"""Rigenera gli asset dell'app da Icon.png, usando Qt e la libreria standard."""
import struct
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage


def png_at_size(source: QImage, size: int) -> bytes:
    resized = source.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not resized.save(buffer, "PNG"):
        raise RuntimeError(f"Conversione PNG non riuscita: {size}px")
    return bytes(buffer.data())


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source = QImage(str(root / "Icon.png"))
    if source.isNull():
        raise ValueError("Impossibile leggere Icon.png nella radice della repo")
    if source.width() != source.height():
        raise ValueError("L'icona sorgente deve essere quadrata")
    directory = root / "src" / "questionnaire_tool" / "resources" / "icons"
    directory.mkdir(parents=True, exist_ok=True)
    directory.joinpath("appdraft.png").write_bytes(png_at_size(source, 512))

    # ICO multi-risoluzione con immagini PNG e canale alpha (Windows moderno).
    sizes = (16, 24, 32, 48, 64, 128, 256)
    images = [png_at_size(source, size) for size in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = []
    for size, data in zip(sizes, images):
        entries.append(struct.pack("<BBBBHHII", size if size < 256 else 0,
                                   size if size < 256 else 0, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    directory.joinpath("appdraft.ico").write_bytes(header + b"".join(entries) + b"".join(images))

    # ICNS con rappresentazioni PNG, fino alla risoluzione Retina di 1024px.
    representations = ((b"icp4", 16), (b"icp5", 32), (b"icp6", 64),
                       (b"ic07", 128), (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024))
    chunks = []
    for kind, size in representations:
        data = png_at_size(source, size)
        chunks.append(kind + struct.pack(">I", 8 + len(data)) + data)
    body = b"".join(chunks)
    directory.joinpath("appdraft.icns").write_bytes(b"icns" + struct.pack(">I", 8 + len(body)) + body)
    print(f"Icone PNG, ICO e ICNS generate in {directory}")


if __name__ == "__main__":
    main()
