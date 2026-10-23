import os
import struct
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG = os.path.join(ROOT, "assets", "logo.svg")
SIZES = [16, 24, 32, 48, 64, 128, 256]


def render(renderer, size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    renderer.render(p)
    p.end()
    return img


def png_bytes(img):
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    buf.close()
    return bytes(ba)


def write_ico(path, entries):
    header = struct.pack("<HHH", 0, 1, len(entries))
    offset = 6 + 16 * len(entries)
    directory = b""
    blobs = b""
    for size, data in entries:
        dim = 0 if size >= 256 else size
        directory += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
        blobs += data
        offset += len(data)
    with open(path, "wb") as f:
        f.write(header + directory + blobs)


def main():
    app = QGuiApplication(sys.argv)
    renderer = QSvgRenderer(SVG)
    if not renderer.isValid():
        raise SystemExit("invalid svg")
    big = render(renderer, 512)
    big.save(os.path.join(ROOT, "assets", "icon.png"), "PNG")
    entries = [(s, png_bytes(render(renderer, s))) for s in SIZES]
    write_ico(os.path.join(ROOT, "assets", "icon.ico"), entries)
    print("icons written")
    del app


if __name__ == "__main__":
    main()
