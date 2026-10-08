from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .template import Answer, QuestionnaireTemplate


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    template_id: str
    template_version: int
    updated_at: datetime
    answers: dict[str, Answer]


def is_filled(value: Answer) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return True


def completion(template: QuestionnaireTemplate, answers: dict[str, Answer]) -> tuple[int, int, int]:
    required = [q for q in template.questions if q.required]
    done = sum(is_filled(answers.get(q.id)) for q in required)
    return done, len(required), round(100 * done / len(required)) if required else 100


def initial_answers(template: QuestionnaireTemplate) -> dict[str, Answer]:
    return {q.id: q.default.copy() if isinstance(q.default, list) else q.default for q in template.questions}
