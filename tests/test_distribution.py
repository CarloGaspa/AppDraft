import shutil
from pathlib import Path

import pytest

from questionnaire_tool.application import bundled_templates_directory
from questionnaire_tool.parser.markdown_template import TemplateError
from questionnaire_tool.services.data_service import prepare_data_directory
from questionnaire_tool.services.template_service import TemplateService


def test_bundled_template_without_external_directory(tmp_path):
    templates, errors = TemplateService(tmp_path / "missing", bundled_templates_directory()).discover()
    assert not errors
    assert [t.id for t in templates] == ["tech-stack"]
    assert not (tmp_path / "missing").exists()


def test_user_template_overrides_bundled_without_modifying_it(tmp_path):
    builtin = bundled_templates_directory() / "tech-stack.md"
    original = builtin.read_text(encoding="utf-8")
    imported = tmp_path / "personal.md"
    imported.write_text(original.replace('name: "Technology Stack Assessment"', 'name: "Personalizzato"'), encoding="utf-8")
    service = TemplateService(tmp_path / "templates", bundled_templates_directory())
    service.import_template(imported)
    templates, errors = service.discover()
    assert not errors
    assert len(templates) == 1
    assert templates[0].name == "Personalizzato"
    assert builtin.read_text(encoding="utf-8") == original
    with pytest.raises(FileExistsError):
        service.import_template(builtin)
    service.import_template(builtin, overwrite=True)
    assert service.discover()[0][0].name == "Technology Stack Assessment"


def test_invalid_import_preserves_previous_template(tmp_path):
    service = TemplateService(tmp_path / "templates")
    builtin = bundled_templates_directory() / "tech-stack.md"
    service.import_template(builtin)
    before = (service.directory / "tech-stack.md").read_bytes()
    broken = tmp_path / "broken.md"
    broken.write_text("---\nid: tech-stack\n---", encoding="utf-8")
    with pytest.raises(TemplateError):
        service.import_template(broken, overwrite=True)
    assert (service.directory / "tech-stack.md").read_bytes() == before


def test_first_run_copies_legacy_data_without_overwriting_or_reimporting(tmp_path):
    legacy = tmp_path / "old"
    (legacy / "drafts").mkdir(parents=True)
    (legacy / "templates").mkdir()
    (legacy / "drafts" / "tech-stack.json").write_text('{"old":true}', encoding="utf-8")
    shutil.copy2(bundled_templates_directory() / "tech-stack.md", legacy / "templates" / "tech-stack.md")
    destination = tmp_path / "user"
    prepare_data_directory(destination, legacy)
    copied = destination / "drafts" / "tech-stack.json"
    assert copied.read_text(encoding="utf-8") == '{"old":true}'
    copied.write_text('{"new":true}', encoding="utf-8")
    (destination / "templates" / "tech-stack.md").unlink()
    prepare_data_directory(destination, legacy)
    assert copied.read_text(encoding="utf-8") == '{"new":true}'
    assert not (destination / "templates" / "tech-stack.md").exists()
    assert (legacy / "drafts" / "tech-stack.json").is_file()


def test_data_directory_without_legacy_files(tmp_path):
    directory = tmp_path / "data"
    prepare_data_directory(directory)
    assert (directory / "drafts").is_dir()
    assert (directory / "templates").is_dir()
    assert not (directory / "exports").exists()
