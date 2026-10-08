from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget)

from questionnaire_tool.models.template import Answer, Question
from .widgets.scroll_safe import FormComboBox, FormDoubleSpinBox, FormSlider, FormTextEdit


class FormRenderer:
    """Ogni editor comunica soltanto valori Python al contenitore del form."""

    def render(self, question: Question, value: Answer, on_change: Callable[[Answer], None]) -> QWidget:
        q = question
        if q.type == "text":
            widget = QLineEdit()
            widget.setPlaceholderText(q.placeholder or "")
            widget.setText(value if isinstance(value, str) else "")
            widget.textChanged.connect(on_change)
        elif q.type == "textarea":
            widget = FormTextEdit()
            widget.setAcceptRichText(False)
            widget.setPlaceholderText(q.placeholder or "")
            widget.setPlainText(value if isinstance(value, str) else "")
            widget.setMinimumHeight(100)
            widget.setMaximumHeight(160)
            widget.textChanged.connect(lambda: on_change(widget.toPlainText()))
        elif q.type == "select":
            widget = FormComboBox()
            widget.addItem("— Seleziona —", None)
            for option in q.options:
                widget.addItem(option, option)
            widget.setCurrentIndex(widget.findData(value) if value is not None else 0)
            widget.currentIndexChanged.connect(lambda _: on_change(widget.currentData()))
        elif q.type == "multi_select":
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            boxes = []
            for option in q.options:
                box = QCheckBox(option)
                box.setChecked(isinstance(value, list) and option in value)
                layout.addWidget(box)
                boxes.append(box)
            for box in boxes:
                box.toggled.connect(lambda _: on_change([b.text() for b in boxes if b.isChecked()]))
        elif q.type == "boolean":
            widget = QCheckBox("Sì / No (nessuna risposta: stato intermedio)")
            widget.setTristate(True)
            widget.setCheckState(Qt.CheckState.PartiallyChecked if value is None else
                                 Qt.CheckState.Checked if value else Qt.CheckState.Unchecked)
            widget.checkStateChanged.connect(lambda state: on_change(
                None if state == Qt.CheckState.PartiallyChecked else state == Qt.CheckState.Checked))
        else:
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            enabled = QCheckBox("Risposta")
            enabled.setChecked(value is not None)
            layout.addWidget(enabled)
            if q.type == "scale":
                editor = FormSlider(Qt.Orientation.Horizontal)
                editor.setRange(q.min, q.max)
                editor.setValue(value if value is not None else q.min)
                editor.setSingleStep(1)
                label = QLabel(str(editor.value()) if value is not None else "—")
                editor.valueChanged.connect(lambda v: label.setText(str(v)))
                layout.addWidget(editor, 1)
                layout.addWidget(label)
                enabled.toggled.connect(lambda active: label.setText(str(editor.value()) if active else "—"))
            else:
                editor = FormDoubleSpinBox()
                editor.setDecimals(6)
                editor.setRange(q.min if q.min is not None else -1e12, q.max if q.max is not None else 1e12)
                editor.setValue(value if value is not None else max(editor.minimum(), min(0, editor.maximum())))
                layout.addWidget(editor, 1)
            editor.setEnabled(enabled.isChecked())
            enabled.toggled.connect(editor.setEnabled)
            enabled.toggled.connect(lambda active: on_change(editor.value() if active else None))
            editor.valueChanged.connect(lambda v: on_change(v) if enabled.isChecked() else None)
        widget.setObjectName(q.id)
        widget.setAccessibleName(q.label)
        if q.help:
            widget.setToolTip(q.help)
        return widget
