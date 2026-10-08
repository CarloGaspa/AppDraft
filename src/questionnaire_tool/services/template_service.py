from pathlib import Path

from questionnaire_tool.models.template import QuestionnaireTemplate
from questionnaire_tool.parser.markdown_template import TemplateError, TemplateParser


class TemplateService:
    def __init__(self, directory: Path):
        self.directory = directory
        self.parser = TemplateParser()

    def discover(self) -> tuple[list[QuestionnaireTemplate], list[str]]:
        templates, errors = [], []
        if not self.directory.is_dir():
            return [], [f"Cartella template mancante: {self.directory}"]
        seen = set()
        try:
            paths = sorted(p for p in self.directory.iterdir() if p.is_file() and p.suffix.lower() == ".md")
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
