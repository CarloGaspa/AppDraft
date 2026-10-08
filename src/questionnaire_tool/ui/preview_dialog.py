from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QPushButton, QTextEdit, QVBoxLayout


class PreviewDialog(QDialog):
    def __init__(self, markdown: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preview Markdown — AppDraft")
        self.resize(800, 650)
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(markdown)
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        copy = QPushButton("Copia negli appunti")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(markdown))
        buttons.addButton(copy, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
