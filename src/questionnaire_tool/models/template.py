import math
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Answer = str | int | float | bool | list[str] | None
Identifier = str


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: Identifier = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    label: str = Field(min_length=1)
    type: Literal["text", "textarea", "number", "select", "multi_select", "boolean", "scale"]
    required: bool = False
    placeholder: str | None = None
    help: str | None = None
    default: Answer = None
    options: list[str] = Field(default_factory=list)
    min: int | float | None = None
    max: int | float | None = None

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        if not self.label.strip():
            raise ValueError("La label non può essere vuota")
        if self.type in {"select", "multi_select"}:
            if not self.options or any(not x.strip() for x in self.options):
                raise ValueError("Le domande a scelta richiedono opzioni non vuote")
            if len(set(self.options)) != len(self.options):
                raise ValueError("Le opzioni devono essere uniche")
        elif self.options:
            raise ValueError("options è consentito solo per select e multi_select")
        if self.type not in {"number", "scale"} and (self.min is not None or self.max is not None):
            raise ValueError("min/max sono consentiti solo per number e scale")
        for bound in (self.min, self.max):
            if bound is not None and (isinstance(bound, bool) or not math.isfinite(bound) or abs(bound) > 1e12):
                raise ValueError("Limiti numerici non validi (massimo assoluto 10^12)")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min deve essere minore o uguale a max")
        if self.type == "scale":
            if type(self.min) is not int or type(self.max) is not int:
                raise ValueError("scale richiede min e max interi")
            if self.min < -2147483648 or self.max > 2147483647:
                raise ValueError("Limiti scale fuori intervallo")
        if self.default is not None:
            self.validate_answer(self.default)
        return self

    def validate_answer(self, value: Answer) -> None:
        if value is None:
            return
        valid = False
        if self.type in {"text", "textarea"}:
            valid = isinstance(value, str)
        elif self.type == "boolean":
            valid = type(value) is bool
        elif self.type == "select":
            valid = isinstance(value, str) and value in self.options
        elif self.type == "multi_select":
            valid = isinstance(value, list) and all(x in self.options for x in value) and len(value) == len(set(value))
        elif self.type in {"number", "scale"}:
            valid = type(value) in {int, float} and math.isfinite(value)
            valid = valid and (self.type != "scale" or type(value) is int)
            valid = valid and (self.min is None or value >= self.min) and (self.max is None or value <= self.max)
            valid = valid and abs(value) <= 1e12
        if not valid:
            raise ValueError(f"Risposta non valida per «{self.label}»")


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: Identifier = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    description: str | None = None
    questions: list[Question] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Il titolo non può essere vuoto")
        return value


class QuestionnaireTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: Identifier = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    name: str = Field(min_length=1)
    version: int = Field(ge=1)
    description: str = ""
    sections: list[Section] = Field(min_length=1)
    introduction: str = ""

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Il nome non può essere vuoto")
        return value

    @model_validator(mode="after")
    def unique_ids(self) -> Self:
        sections = [s.id for s in self.sections]
        questions = [q.id for q in self.questions]
        if len(sections) != len(set(sections)) or len(questions) != len(set(questions)):
            raise ValueError("Gli ID di sezioni e domande devono essere unici nel questionario")
        return self

    @property
    def questions(self) -> list[Question]:
        return [q for s in self.sections for q in s.questions]
