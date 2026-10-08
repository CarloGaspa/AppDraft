from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from questionnaire_tool.models.template import QuestionnaireTemplate


class TemplateSidebar(QWidget):
    selected = Signal(str)
    reload_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(190)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Questionari"))
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._selected)
        layout.addWidget(self.list)
        refresh = QPushButton("Ricarica template")
        refresh.clicked.connect(self.reload_requested)
        layout.addWidget(refresh)

    def _selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current:
            self.selected.emit(current.data(Qt.ItemDataRole.UserRole))

    def populate(self, templates: list[QuestionnaireTemplate], selected: str | None) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        target = 0
        for index, template in enumerate(templates):
            item = QListWidgetItem(template.name)
            item.setData(Qt.ItemDataRole.UserRole, template.id)
            item.setToolTip(template.description)
            self.list.addItem(item)
            if template.id == selected:
                target = index
        self.list.blockSignals(False)
        if templates:
            self.list.setCurrentRow(target)
