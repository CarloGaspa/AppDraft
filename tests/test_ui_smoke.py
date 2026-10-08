"""Verifica operativa Qt in isolamento: nessuna bozza o impostazione dell'utente."""
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QSettings, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QFileDialog, QMessageBox, QTextEdit

from questionnaire_tool.ui.main_window import MainWindow
from questionnaire_tool.renderer.widgets.scroll_safe import FormDoubleSpinBox, FormSlider


def test_edit_autosave_reopen_preview_export_and_discovery(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path / "settings"))
    templates = tmp_path / "templates"
    templates.mkdir()
    source = (Path(__file__).parents[1] / "templates" / "tech-stack.md").read_text(encoding="utf-8")
    (templates / "tech-stack.md").write_text(source, encoding="utf-8")
    window = MainWindow(tmp_path)
    errors = []
    monkeypatch.setattr(window, "error", lambda title, message: errors.append((title, message)))
    window.show()
    QTest.qWait(50)
    assert window.current.id == "tech-stack"
    assert len(window.view.editors) > 30
    window.view.editors["project_name"].setText("Smoke project")
    window.view.editors["product_description"].setPlainText("Desktop locale\nSeconda riga")
    window.view.editors["backend_need"].setCurrentIndex(1)
    box = window.view.editors["open_source_only"]
    box.setCheckState(Qt.CheckState.Unchecked)
    assert window.answers["open_source_only"] is False
    multi = window.view.editors["product_type"].findChildren(QCheckBox)
    multi[3].setChecked(True)
    number = window.view.editors["initial_users"]
    number.findChild(QCheckBox).setChecked(True)
    scale = window.view.editors["native_importance"]
    scale.findChild(QCheckBox).setChecked(True)
    QTest.qWait(750)
    assert (tmp_path / "drafts" / "tech-stack.json").is_file()
    assert not window.dirty
    assert window.progress_bar.value() > 0
    assert not errors
    # Chiudi con una modifica in attesa: deve essere salvata immediatamente.
    window.view.editors["project_name"].setText("AppDraft smoke")
    window.close()
    reopened = MainWindow(tmp_path)
    monkeypatch.setattr(reopened, "error", lambda title, message: errors.append((title, message)))
    reopened.show()
    QTest.qWait(50)
    assert reopened.answers["project_name"] == "AppDraft smoke"
    assert reopened.answers["open_source_only"] is False
    assert reopened.answers["product_type"] == ["Desktop"]
    assert reopened.view.editors["backend_need"].currentText() == "No"

    def inspect_preview():
        dialog = app.activeModalWidget()
        assert isinstance(dialog, QDialog)
        text = dialog.findChild(QTextEdit).toPlainText()
        assert "AppDraft smoke" in text and "# Istruzioni per AI" in text
        dialog.reject()

    QTimer.singleShot(50, inspect_preview)
    reopened.preview()
    exported = tmp_path / "result.md"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(exported), "Markdown (*.md)"))
    reopened.export()
    assert "- Desktop" in exported.read_text(encoding="utf-8")
    assert "### È obbligatorio" in exported.read_text(encoding="utf-8")
    (templates / "new.md").write_text(source.replace("id: tech-stack", "id: second").replace(
        'name: "Technology Stack Assessment"', 'name: "Secondo questionario"'), encoding="utf-8")
    reopened.reload_templates()
    assert reopened.sidebar.list.count() == 2
    assert not errors
    reopened.close()


def test_corrupt_draft_protection_and_export_failure(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path / "settings"))
    templates = tmp_path / "templates"
    templates.mkdir()
    source = Path(__file__).parents[1] / "templates" / "tech-stack.md"
    (templates / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    corrupt = drafts / "tech-stack.json"
    corrupt.write_text("{broken", encoding="utf-8")
    errors = []
    window = MainWindow(tmp_path)
    monkeypatch.setattr(window, "error", lambda title, message: errors.append((title, message)))
    window.show()
    QTest.qWait(50)
    assert window.blocked_draft
    assert len(errors) == 1
    window.view.editors["project_name"].setText("Recuperato")
    QTest.qWait(750)
    assert corrupt.read_text(encoding="utf-8") == "{broken"
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    assert not window.close()
    assert window.isVisible()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    assert window.manual_save()
    assert window.draft_service.load(window.current)["project_name"] == "Recuperato"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(tmp_path / "bad.md"), ""))

    def fail_save(*args):
        raise PermissionError("Accesso negato")

    monkeypatch.setattr(window.export_service, "save", fail_save)
    window.export()
    assert errors[-1] == ("Export non riuscito", "Accesso negato")
    assert window.close()


@pytest.mark.parametrize("question_id", ["domain_complexity", "initial_users", "native_importance", "product_description"])
def test_wheel_scrolls_form_without_changing_answers(tmp_path, monkeypatch, question_id):
    app = QApplication.instance() or QApplication([])
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path / "settings"))
    templates = tmp_path / "templates"
    templates.mkdir()
    source = Path(__file__).parents[1] / "templates" / "tech-stack.md"
    (templates / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    window = MainWindow(tmp_path)
    monkeypatch.setattr(window, "error", lambda *args: pytest.fail(str(args)))
    window.show()
    QTest.qWait(50)
    editor = window.view.editors[question_id]
    if question_id in {"initial_users", "native_importance"}:
        editor.findChild(QCheckBox).setChecked(True)
        editor = editor.findChild(FormDoubleSpinBox if question_id == "initial_users" else FormSlider)
    elif question_id == "domain_complexity":
        editor.setCurrentIndex(2)
    else:
        editor.setPlainText("\n".join(f"Riga {i}" for i in range(40)))
    window.view.ensureWidgetVisible(editor)
    editor.setFocus()
    QTest.qWait(20)
    before_answers = window.answers.copy()
    before_scroll = window.view.verticalScrollBar().value()
    position = editor.mapTo(window, editor.rect().center())
    QTest.wheelEvent(window.windowHandle(), position, QPoint(0, -120))
    QTest.qWait(20)
    assert window.answers == before_answers
    assert window.view.verticalScrollBar().value() > before_scroll
    window.close()
