from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QSlider, QTextEdit


class FormComboBox(QComboBox):
    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()  # Qt inoltra la rotella al contenitore scrollabile.


class FormDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()


class FormSlider(QSlider):
    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()


class FormTextEdit(QTextEdit):
    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()
