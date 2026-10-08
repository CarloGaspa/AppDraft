import argparse
import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from questionnaire_tool.ui.main_window import MainWindow


def default_data_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="AppDraft — questionari desktop locali")
    parser.add_argument("--data-dir", type=Path, default=default_data_directory(),
                        help="Cartella contenente templates/, drafts/ ed exports/")
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("AppDraft")
    app.setOrganizationName("AppDraft")

    def report_exception(exc_type, value, traceback):
        logging.error("Errore non gestito", exc_info=(exc_type, value, traceback))
        QMessageBox.critical(None, "Errore AppDraft", "Operazione non riuscita. Consulta la console per i dettagli tecnici.")

    sys.excepthook = report_exception
    window = MainWindow(arguments.data_dir.resolve())
    window.show()
    return app.exec()
