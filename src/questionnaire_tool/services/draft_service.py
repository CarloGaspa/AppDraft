import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from questionnaire_tool.models.answers import Draft
from questionnaire_tool.models.template import Answer, QuestionnaireTemplate


class DraftError(ValueError):
    pass


class DraftService:
    def __init__(self, directory: Path):
        self.directory = directory

    def load(self, template: QuestionnaireTemplate) -> dict[str, Answer] | None:
        path = self.directory / f"{template.id}.json"
        try:
            if not path.exists():
                return None
            draft = Draft.model_validate_json(path.read_text(encoding="utf-8"))
            if draft.template_id != template.id or draft.template_version != template.version:
                raise DraftError("Bozza incompatibile con ID/versione del template. Il file è stato conservato.")
            questions = {q.id: q for q in template.questions}
            for key, value in draft.answers.items():
                if key not in questions:
                    raise DraftError(f"La bozza contiene una domanda sconosciuta: {key}")
                questions[key].validate_answer(value)
            return draft.answers
        except (OSError, UnicodeError, ValidationError, ValueError) as exc:
            raise DraftError(f"Impossibile caricare {path.name}: {exc}") from exc

    def save(self, template: QuestionnaireTemplate, answers: dict[str, Answer]) -> Path:
        temporary = None
        try:
            unknown = answers.keys() - {q.id for q in template.questions}
            if unknown:
                raise ValueError(f"Domande sconosciute: {', '.join(sorted(unknown))}")
            for q in template.questions:
                q.validate_answer(answers.get(q.id))
            self.directory.mkdir(parents=True, exist_ok=True)
            draft = Draft(template_id=template.id, template_version=template.version,
                          updated_at=datetime.now(timezone.utc), answers=answers)
            path = self.directory / f"{template.id}.json"
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.directory,
                                             suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(draft.model_dump_json(indent=2))
            os.replace(temporary, path)
            return path
        except (OSError, ValueError) as exc:
            raise DraftError(f"Impossibile salvare la bozza: {exc}") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass  # Un residuo .tmp non compromette la bozza precedente.
