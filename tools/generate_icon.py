"""Render the shared vector mark for the window, taskbar, and Windows EXE."""

from __future__ import annotations

import os
import struct
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QByteArray, QIODevice  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "docs" / "assets" / "icon.svg"
ASSETS = ROOT / "src" / "dubua" / "assets"


def render(renderer: QSvgRenderer, size: int) -> bytes:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    payload = QByteArray()
    buffer = QBuffer(payload)
    buffer.open(QIODevice.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError(f"Could not render icon at {size}px")
    return bytes(payload)


def main() -> None:
    app = QGuiApplication([])
    renderer = QSvgRenderer(str(SVG))
    if not renderer.isValid():
        raise RuntimeError(f"Invalid logo SVG: {SVG}")
    sizes = (16, 32, 48, 64, 128, 256)
    frames = [render(renderer, size) for size in sizes]
    (ASSETS / "app.png").write_bytes(frames[-1])
    offset = 6 + 16 * len(frames)
    directory = bytearray(struct.pack("<HHH", 0, 1, len(frames)))
    for size, frame in zip(sizes, frames):
        directory.extend(struct.pack("<BBBBHHII", size % 256, size % 256,
                                     0, 0, 1, 32, len(frame), offset))
        offset += len(frame)
    (ASSETS / "app.ico").write_bytes(directory + b"".join(frames))
    del app


if __name__ == "__main__":
    main()
