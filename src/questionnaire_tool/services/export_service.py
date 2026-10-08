import re
from datetime import datetime
from pathlib import Path

import yaml

from questionnaire_tool.models.answers import is_filled
from questionnaire_tool.models.template import Answer, QuestionnaireTemplate

AI_INSTRUCTIONS = """# Istruzioni per AI

Analizza la specifica precedente come un Principal Software Architect.

Parti dai requisiti e dai vincoli descritti nel documento.

Restituisci:

1. sintesi dei requisiti;
2. architettura consigliata;
3. stack principale;
4. due alternative;
5. vantaggi e svantaggi;
6. rischi tecnici;
7. scalabilità;
8. tecnologie non necessarie inizialmente;
9. verdetto finale.

Non scegliere tecnologie solamente perché popolari.

Preferisci la soluzione più semplice che soddisfa correttamente i requisiti.
"""


def heading(text: str) -> str:
    return " ".join(text.splitlines())


class ExportService:
    def generate(self, template: QuestionnaireTemplate, answers: dict[str, Answer],
                 exported_at: datetime | None = None) -> str:
        timestamp = exported_at or datetime.now().astimezone()
        metadata = {"questionnaire": template.id, "questionnaire_name": template.name,
                    "template_version": template.version, "exported_at": timestamp.isoformat(timespec="seconds")}
        parts = ["---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip() + "\n---",
                 f"# {heading(template.name)}"]
        for section in template.sections:
            parts.append(f"## {heading(section.title)}")
            for q in section.questions:
                value = answers.get(q.id)
                q.validate_answer(value)
                parts.append(f"### {heading(q.label)}")
                if not is_filled(value):
                    rendered = "_Non compilato._"
                elif isinstance(value, list):
                    rendered = "\n".join(f"- {heading(item)}" for item in value)
                elif isinstance(value, bool):
                    rendered = "Sì" if value else "No"
                elif q.type == "scale":
                    rendered = f"**{value} / {q.max}**"
                else:
                    rendered = str(value).strip()
                parts.append(rendered)
            parts.append("---")
        parts.append(AI_INSTRUCTIONS.strip())
        return "\n\n".join(parts) + "\n"

    def suggested_filename(self, template: QuestionnaireTemplate, answers: dict[str, Answer]) -> str:
        project = answers.get("project_name")
        title = f"{project.strip()} - {template.name}" if isinstance(project, str) and project.strip() else f"{template.name} - {datetime.now().astimezone():%Y-%m-%d}"
        title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")[:160]
        if title.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]}:
            title = "_" + title
        return (title or "questionario") + ".md"

    def save(self, path: Path, markdown: str) -> None:
        path.write_text(markdown, encoding="utf-8")
