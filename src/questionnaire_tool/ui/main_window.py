from pathlib import Path
import logging

from PySide6.QtCore import QSettings, QStandardPaths, Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                               QProgressBar, QPushButton, QSplitter, QVBoxLayout, QWidget)

from questionnaire_tool.models.answers import completion, initial_answers
from questionnaire_tool.models.template import Answer, QuestionnaireTemplate
from questionnaire_tool.services.draft_service import DraftError, DraftService
from questionnaire_tool.services.export_service import ExportService
from questionnaire_tool.services.template_service import TemplateService
from .preview_dialog import PreviewDialog
from .questionnaire_view import QuestionnaireView
from .template_sidebar import TemplateSidebar


class MainWindow(QMainWindow):
    def __init__(self, data_directory: Path, bundled_templates_directory: Path | None = None):
        super().__init__()
        self.data_directory = data_directory
        self.template_service = TemplateService(data_directory / "templates", bundled_templates_directory)
        self.draft_service = DraftService(data_directory / "drafts")
        self.export_service = ExportService()
        self.settings = QSettings("AppDraft", "AppDraft")
        self.templates: dict[str, QuestionnaireTemplate] = {}
        self.current: QuestionnaireTemplate | None = None
        self.answers: dict[str, Answer] = {}
        self.dirty = False
        self.blocked_draft = False
        self.setWindowTitle("AppDraft")
        self.resize(1100, 800)
        self.setMinimumSize(760, 500)
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        central = QWidget()
        layout = QVBoxLayout(central)
        splitter = QSplitter()
        self.sidebar = TemplateSidebar()
        self.view = QuestionnaireView()
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 860])
        layout.addWidget(splitter, 1)
        footer = QHBoxLayout()
        self.progress_label = QLabel("Seleziona un questionario")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(170)
        footer.addWidget(self.progress_label)
        footer.addWidget(self.progress_bar)
        footer.addStretch()
        self.save_button = QPushButton("Salva bozza")
        self.preview_button = QPushButton("Preview")
        self.export_button = QPushButton("Esporta .md")
        for button in (self.save_button, self.preview_button, self.export_button):
            footer.addWidget(button)
            button.setEnabled(False)
        layout.addLayout(footer)
        self.setCentralWidget(central)
        self.autosave = QTimer(self)
        self.autosave.setSingleShot(True)
        self.autosave.setInterval(650)
        self.autosave.timeout.connect(self.save_draft)
        self.sidebar.selected.connect(self.open_template)
        self.sidebar.reload_requested.connect(self.reload_templates)
        self.sidebar.import_requested.connect(self.import_template)
        self.view.answer_changed.connect(self.answer_changed)
        self.save_button.clicked.connect(self.manual_save)
        self.preview_button.clicked.connect(self.preview)
        self.export_button.clicked.connect(self.export)
        QTimer.singleShot(0, self.reload_templates)

    def error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def import_template(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Importa questionario", "", "Markdown (*.md)")
        if not filename or not self.save_draft():
            return
        try:
            try:
                imported = self.template_service.import_template(Path(filename))
            except FileExistsError as exc:
                if QMessageBox.question(self, "Sostituisci template", f"{exc}\nSostituirlo? Le bozze restano conservate.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                    return
                imported = self.template_service.import_template(Path(filename), overwrite=True)
            self.reload_templates()
            for row in range(self.sidebar.list.count()):
                if self.sidebar.list.item(row).data(Qt.ItemDataRole.UserRole) == imported.id:
                    self.sidebar.list.setCurrentRow(row)
                    break
            self.statusBar().showMessage("Template importato", 4000)
        except (OSError, UnicodeError, ValueError) as exc:
            self.error("Importazione non riuscita", str(exc))

    def reload_templates(self) -> None:
        if not self.save_draft():
            return
        selected = self.current.id if self.current else self.settings.value("last_template", "")
        templates, errors = self.template_service.discover()
        logging.getLogger(__name__).info("Template caricati: %s; errori: %d", ", ".join(t.id for t in templates), len(errors))
        self.templates = {t.id: t for t in templates}
        self.current = None
        self.answers = {}
        for button in (self.save_button, self.preview_button, self.export_button):
            button.setEnabled(bool(templates))
        if not templates:
            previous = self.view.takeWidget()
            if previous:
                previous.deleteLater()
            self.view.setWidget(QLabel(f"Nessun questionario valido. Aggiungi un file .md in:\n{self.template_service.directory}"))
            self.progress_label.setText("Nessun questionario")
            self.progress_bar.setValue(0)
        self.sidebar.populate(templates, selected)
        if errors:
            self.error("Problemi nei template", "\n\n".join(errors))

    def open_template(self, template_id: str) -> None:
        previous = self.current
        if not self.save_draft():
            if previous:
                self.sidebar.list.blockSignals(True)
                for row in range(self.sidebar.list.count()):
                    if self.sidebar.list.item(row).text() == previous.name:
                        self.sidebar.list.setCurrentRow(row)
                        break
                self.sidebar.list.blockSignals(False)
            return
        self.current = self.templates[template_id]
        self.answers = initial_answers(self.current)
        self.blocked_draft = False
        try:
            loaded = self.draft_service.load(self.current)
            if loaded is not None:
                self.answers.update(loaded)
        except DraftError as exc:
            self.blocked_draft = True
            self.error("Problema nella bozza", f"{exc}\n\nCompilazione disponibile. Autosalvataggio sospeso per proteggere il file esistente. «Salva bozza» permette di sostituirlo esplicitamente.")
        self.dirty = False
        self.view.load(self.current, self.answers)
        self.settings.setValue("last_template", template_id)
        self.update_progress()
        self.statusBar().showMessage("Bozza protetta: autosalvataggio sospeso" if self.blocked_draft else "Bozza caricata" if loaded is not None else "Nuovo questionario")

    def answer_changed(self, key: str, value: Answer) -> None:
        if self.answers.get(key) == value:
            return
        self.answers[key] = value
        self.dirty = True
        self.update_progress()
        if not self.blocked_draft:
            self.statusBar().showMessage("Modifiche da salvare…")
            self.autosave.start()

    def update_progress(self) -> None:
        if self.current:
            done, total, percent = completion(self.current, self.answers)
            self.progress_label.setText(f"{done} / {total} obbligatorie completate")
            self.progress_bar.setValue(percent)

    def save_draft(self) -> bool:
        self.autosave.stop()
        if not self.current or not self.dirty:
            return True
        if self.blocked_draft:
            return self.manual_save()
        try:
            self.draft_service.save(self.current, self.answers)
            self.dirty = False
            self.statusBar().showMessage("Bozza salvata", 4000)
            return True
        except DraftError as exc:
            self.error("Salvataggio non riuscito", str(exc))
            return False

    def manual_save(self) -> bool:
        if not self.current:
            return True
        if self.blocked_draft:
            choice = QMessageBox.question(self, "Sostituisci bozza", "Sostituire la bozza non leggibile o incompatibile con le risposte attuali?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                          QMessageBox.StandardButton.No)
            if choice != QMessageBox.StandardButton.Yes:
                return False
            self.blocked_draft = False
        self.dirty = True
        return self.save_draft()

    def preview(self) -> None:
        if self.current:
            PreviewDialog(self.export_service.generate(self.current, self.answers), self).exec()

    def export(self) -> None:
        if not self.current:
            return
        try:
            documents = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            directory = Path(self.settings.value("export_directory", documents or str(Path.home())))
            if not directory.is_dir():
                directory = Path(documents or str(Path.home()))
            suggested = directory / self.export_service.suggested_filename(self.current, self.answers)
            filename, _ = QFileDialog.getSaveFileName(self, "Esporta Markdown", str(suggested), "Markdown (*.md)")
            if not filename:
                return
            path = Path(filename)
            if path.suffix.lower() != ".md":
                path = path.with_name(path.name + ".md")
                if path.exists() and QMessageBox.question(self, "Sostituisci file", f"Sostituire {path.name}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                    return
            self.export_service.save(path, self.export_service.generate(self.current, self.answers))
            self.settings.setValue("export_directory", str(path.parent))
            self.statusBar().showMessage(f"Esportato: {path}", 10000)
        except (OSError, ValueError) as exc:
            self.error("Export non riuscito", str(exc))

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self.save_draft():
            event.ignore()
            return
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()
