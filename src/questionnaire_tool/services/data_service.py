import shutil
from pathlib import Path


def prepare_data_directory(directory: Path, legacy_directory: Path | None = None) -> None:
    """Crea lo spazio personale; al primo uso copia i dati della vecchia V1."""
    for name, suffix in (("drafts", ".json"), ("templates", ".md")):
        destination = directory / name
        first_use = not destination.exists()
        destination.mkdir(parents=True, exist_ok=True)
        source = legacy_directory / name if legacy_directory else None
        if first_use and source and source.is_dir() and source.resolve() != destination.resolve():
            for path in source.iterdir():
                if path.is_file() and path.suffix.lower() == suffix:
                    shutil.copy2(path, destination / path.name)
