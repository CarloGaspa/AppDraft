import argparse
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication, QMessageBox

from questionnaire_tool.services.data_service import prepare_data_directory
from questionnaire_tool.ui.main_window import MainWindow


def default_data_directory() -> Path:
    """Chiamare dopo aver impostato nome/organizzazione di QApplication."""
    directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    if not directory:
        raise OSError("Il sistema non ha fornito una cartella dati personale")
    return Path(directory)


def bundled_templates_directory() -> Path:
    # PyInstaller mantiene __file__ relativo alle risorse estratte o al bundle.
    return Path(__file__).resolve().parent / "resources" / "templates"


def legacy_data_directory() -> Path:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        for parent in executable.parents:
            if parent.suffix == ".app":
                return parent.parent
        return executable.parent
    return Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="AppDraft — questionari desktop locali")
    parser.add_argument("--data-dir", type=Path,
                        help="Cartella dati alternativa (predefinita: cartella personale del sistema)")
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("AppDraft")
    app.setOrganizationName("AppDraft")

    try:
        directory = (arguments.data_dir or default_data_directory()).resolve()
        prepare_data_directory(directory, legacy_data_directory() if arguments.data_dir is None else None)
        logging.basicConfig(level=logging.INFO, filename=directory / "appdraft.log", encoding="utf-8", force=True)
    except OSError as exc:
        QMessageBox.critical(None, "Cartella dati non disponibile", f"Impossibile preparare i dati personali: {exc}")
        return 1

    def report_exception(exc_type, value, traceback):
        logging.error("Errore non gestito", exc_info=(exc_type, value, traceback))
        QMessageBox.critical(None, "Errore AppDraft", f"Operazione non riuscita. I dettagli sono nel log:\n{directory / 'appdraft.log'}")

    sys.excepthook = report_exception
    window = MainWindow(directory, bundled_templates_directory())
    window.show()
    return app.exec()
