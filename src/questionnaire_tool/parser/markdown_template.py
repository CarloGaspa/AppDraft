from pathlib import Path

import yaml
from pydantic import ValidationError

from questionnaire_tool.models.template import QuestionnaireTemplate


class TemplateError(ValueError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    """Evita che chiavi YAML duplicate vengano ignorate silenziosamente."""


def unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise TemplateError("Chiave YAML duplicata o non testuale")
        result[key] = loader.construct_object(value_node)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


class TemplateParser:
    def parse(self, text: str) -> QuestionnaireTemplate:
        lines = text.lstrip("\ufeff").splitlines()
        if not lines or lines[0].strip() != "---":
            raise TemplateError("Il file deve iniziare con frontmatter YAML delimitato da ---")
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is None:
            raise TemplateError("Manca il delimitatore finale --- del frontmatter")
        try:
            data = yaml.load("\n".join(lines[1:end]), Loader=UniqueKeyLoader)
            if not isinstance(data, dict):
                raise TemplateError("Il frontmatter deve contenere una mappa YAML")
            data["introduction"] = "\n".join(lines[end + 1:]).strip()
            return QuestionnaireTemplate.model_validate(data)
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            location = f" (riga {mark.line + 2})" if mark else ""
            raise TemplateError(f"YAML non valido{location}: {getattr(exc, 'problem', 'sintassi errata')}") from exc
        except ValidationError as exc:
            details = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
            raise TemplateError(f"Configurazione non valida: {details}") from exc

    def parse_file(self, path: Path) -> QuestionnaireTemplate:
        try:
            return self.parse(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError) as exc:
            raise TemplateError(f"Impossibile leggere {path.name}: {exc}") from exc
