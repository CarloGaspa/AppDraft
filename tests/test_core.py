import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from questionnaire_tool.models.answers import completion, initial_answers
from questionnaire_tool.models.template import Question, QuestionnaireTemplate
from questionnaire_tool.parser.markdown_template import TemplateError, TemplateParser
from questionnaire_tool.services.draft_service import DraftError, DraftService
from questionnaire_tool.services.export_service import ExportService
from questionnaire_tool.services.template_service import TemplateService


@pytest.fixture
def template():
    return QuestionnaireTemplate.model_validate({
        "id": "sample", "name": "Esempio", "version": 1,
        "sections": [{"id": "main", "title": "Prodotto", "questions": [
            {"id": "project_name", "label": "Nome", "type": "text", "required": True},
            {"id": "enabled", "label": "Attivo", "type": "boolean", "required": True},
            {"id": "targets", "label": "Piattaforme", "type": "multi_select", "options": ["Windows", "macOS"]},
            {"id": "priority", "label": "Priorità", "type": "scale", "min": 1, "max": 5, "default": 3},
            {"id": "description", "label": "Descrizione", "type": "textarea"},
        ]}]
    })


def test_real_template():
    result = TemplateParser().parse_file(Path(__file__).parents[1] / "src" / "questionnaire_tool" / "resources" / "templates" / "tech-stack.md")
    assert result.name == "Technology Stack Assessment"
    assert len(result.sections) == 20
    assert len(result.questions) > 30
    assert result.introduction.startswith("# Technology")


@pytest.mark.parametrize("text", ["No frontmatter", "---\nid: a", "---\n[broken\n---", "---\n[]\n---",
                                     "---\nid: a\nid: b\n---", "---\nname: Incompleto\n---"])
def test_parser_errors(text):
    with pytest.raises(TemplateError):
        TemplateParser().parse(text)


@pytest.mark.parametrize("settings", [
    {"type": "unknown"}, {"type": "select"}, {"type": "scale", "min": 5, "max": 1},
    {"type": "scale", "min": 1.0, "max": 5}, {"type": "boolean", "default": "yes"},
    {"type": "select", "options": ["A"], "default": "B"},
    {"type": "multi_select", "options": ["A", "A"]},
    {"type": "number", "min": 0, "default": -1}, {"type": "text", "max": 3},
    {"type": "number", "default": float("nan")}, {"type": "text", "id": "../escape"},
])
def test_invalid_questions(settings):
    with pytest.raises(ValidationError):
        Question.model_validate({"id": "q", "label": "Domanda", **settings})


def test_unique_question_ids(template):
    data = template.model_dump()
    data["sections"][0]["questions"].append(data["sections"][0]["questions"][0].copy())
    with pytest.raises(ValidationError):
        QuestionnaireTemplate.model_validate(data)


def test_discovery_isolates_invalid_and_duplicate(tmp_path):
    source = (Path(__file__).parents[1] / "src" / "questionnaire_tool" / "resources" / "templates" / "tech-stack.md").read_text(encoding="utf-8")
    (tmp_path / "a.md").write_text(source, encoding="utf-8")
    (tmp_path / "b.MD").write_text(source, encoding="utf-8")
    (tmp_path / "broken.md").write_text("broken", encoding="utf-8")
    templates, errors = TemplateService(tmp_path).discover()
    assert len(templates) == 1
    assert len(errors) == 2
    assert TemplateService(tmp_path / "missing").discover()[1]


def test_draft_round_trip(tmp_path, template):
    service = DraftService(tmp_path / "drafts")
    assert service.load(template) is None
    answers = initial_answers(template)
    answers.update(project_name="Città", enabled=False, targets=["macOS"])
    path = service.save(template, answers)
    assert service.load(template) == answers
    assert json.loads(path.read_text(encoding="utf-8"))["updated_at"].endswith("Z")
    assert not list(path.parent.glob("*.tmp"))


@pytest.mark.parametrize("contents", ["{broken", '{"template_id":"sample"}',
    '{"template_id":"sample","template_version":1,"updated_at":"2026-10-08T12:00:00Z","answers":{"enabled":"false"}}',
    '{"template_id":"sample","template_version":2,"updated_at":"2026-10-08T12:00:00Z","answers":{}}'])
def test_draft_errors_preserve_file(tmp_path, template, contents):
    path = tmp_path / "sample.json"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(DraftError):
        DraftService(tmp_path).load(template)
    assert path.read_text(encoding="utf-8") == contents


def test_progress_explicit_false_and_zero(template):
    assert completion(template, {}) == (0, 2, 0)
    assert completion(template, {"project_name": "  ", "enabled": False}) == (1, 2, 50)
    assert completion(template, {"project_name": "App", "enabled": False}) == (2, 2, 100)
    template.sections[0].questions[0].required = False
    template.sections[0].questions[1].required = False
    assert completion(template, {}) == (0, 0, 100)


def test_export_and_filename(template, tmp_path):
    service = ExportService()
    answers = {"project_name": "App", "enabled": False, "targets": ["Windows", "macOS"],
               "priority": 4, "description": "Prima riga\nSeconda riga"}
    output = service.generate(template, answers, datetime(2026, 10, 8, 12, tzinfo=timezone.utc))
    assert "questionnaire: sample" in output
    assert "2026-10-08T12:00:00+00:00" in output
    assert "### Attivo\n\nNo" in output
    assert "- Windows\n- macOS" in output
    assert "**4 / 5**" in output
    assert "Prima riga\nSeconda riga" in output
    assert output.index("### Nome") < output.index("### Attivo")
    assert output.count("# Istruzioni per AI") == 1
    assert "_Non compilato._" in service.generate(template, {})
    assert service.suggested_filename(template, answers) == "App - Esempio.md"
    assert "/" not in service.suggested_filename(template, {"project_name": "a/b"})
    path = tmp_path / "export.md"
    service.save(path, output)
    assert path.read_text(encoding="utf-8") == output
