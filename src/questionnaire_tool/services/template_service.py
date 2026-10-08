from pathlib import Path
import os
import tempfile

from questionnaire_tool.models.template import QuestionnaireTemplate
from questionnaire_tool.parser.markdown_template import TemplateError, TemplateParser


class TemplateService:
    def __init__(self, directory: Path, bundled_directory: Path | None = None):
        self.directory = directory
        self.bundled_directory = bundled_directory
        self.parser = TemplateParser()

    def discover(self) -> tuple[list[QuestionnaireTemplate], list[str]]:
        templates: dict[str, QuestionnaireTemplate] = {}
        errors = []
        if self.bundled_directory is not None:
            builtin, issues = self._discover_directory(self.bundled_directory)
            templates.update((t.id, t) for t in builtin)
            errors.extend(issues)
        if self.directory.is_dir() or self.bundled_directory is None:
            personal, issues = self._discover_directory(self.directory)
            templates.update((t.id, t) for t in personal)
            errors.extend(issues)
        return list(templates.values()), errors

    def _discover_directory(self, directory: Path) -> tuple[list[QuestionnaireTemplate], list[str]]:
        templates, errors = [], []
        if not directory.is_dir():
            return [], [f"Cartella template mancante: {directory}"]
        seen = set()
        try:
            paths = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".md")
        except OSError as exc:
            return [], [f"Impossibile leggere la cartella template: {exc}"]
        for path in paths:
            try:
                template = self.parser.parse_file(path)
                if template.id in seen:
                    raise TemplateError(f"ID template duplicato: {template.id}")
                seen.add(template.id)
                templates.append(template)
            except TemplateError as exc:
                errors.append(f"{path.name}: {exc}")
        return templates, errors

    def import_template(self, source: Path, overwrite: bool = False) -> QuestionnaireTemplate:
        text = source.read_text(encoding="utf-8-sig")
        template = self.parser.parse(text)
        self.directory.mkdir(parents=True, exist_ok=True)
        destination = self.directory / f"{template.id}.md"
        if destination.exists() and not overwrite:
            raise FileExistsError(f"Esiste già un template personale con ID «{template.id}»")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.directory,
                                             suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(text)
            os.replace(temporary, destination)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
        return template
