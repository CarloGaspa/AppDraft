from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from questionnaire_tool.models.template import Answer, QuestionnaireTemplate
from questionnaire_tool.renderer.form_renderer import FormRenderer


class QuestionnaireView(QScrollArea):
    answer_changed = Signal(str, object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.renderer = FormRenderer()
        self.editors: dict[str, QWidget] = {}

    def load(self, template: QuestionnaireTemplate, answers: dict[str, Answer]) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(12)
        title = QLabel(template.name)
        title.setWordWrap(True)
        font = title.font()
        font.setPointSize(font.pointSize() + 5)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        if template.description:
            description = QLabel(template.description)
            description.setWordWrap(True)
            layout.addWidget(description)
        hint = QLabel("* Campo obbligatorio · Risposta: abilita un numero o una scala prima di compilarli.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.editors.clear()
        for section in template.sections:
            layout.addSpacing(16)
            heading = QLabel(section.title)
            font = heading.font()
            font.setPointSize(font.pointSize() + 2)
            font.setBold(True)
            heading.setFont(font)
            layout.addWidget(heading)
            if section.description:
                description = QLabel(section.description)
                description.setWordWrap(True)
                layout.addWidget(description)
            for question in section.questions:
                label = QLabel(question.label + (" *" if question.required else ""))
                label.setWordWrap(True)
                layout.addWidget(label)
                editor = self.renderer.render(question, answers.get(question.id),
                                              lambda value, key=question.id: self.answer_changed.emit(key, value))
                self.editors[question.id] = editor
                label.setBuddy(editor)
                layout.addWidget(editor)
                if question.help:
                    help_label = QLabel(question.help)
                    help_label.setWordWrap(True)
                    font = help_label.font()
                    font.setPointSize(max(8, font.pointSize() - 1))
                    help_label.setFont(font)
                    layout.addWidget(help_label)
                layout.addSpacing(6)
        layout.addStretch()
        previous = self.takeWidget()
        if previous:
            previous.deleteLater()
        self.setWidget(container)
        self.verticalScrollBar().setValue(0)
