import sys
import os
import ctypes
import threading

import numpy as np
from PySide6.QtCore import Qt, QThread, Signal, QRectF, QPointF, QEvent
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QKeySequence, QShortcut, QFont, QPalette, QIntValidator, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QSlider, QComboBox, QProgressBar, QFileDialog,
    QButtonGroup, QMessageBox, QFormLayout, QStyledItemDelegate,
)

import carving


def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)

STYLE = """
* {
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
    color: #e4e4e7;
}
QMainWindow, QWidget#root {
    background: #09090b;
}
QWidget#sidebar {
    background: #111113;
    border-right: 1px solid #1f1f23;
}
QLabel {
    background: transparent;
}
QLabel#title {
    font-size: 20px;
    font-weight: 700;
    color: #fafafa;
}
QLabel#section {
    font-size: 11px;
    font-weight: 600;
    color: #71717a;
}
QLabel#hint {
    color: #71717a;
}
QPushButton {
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 8px 12px;
}
QPushButton:hover {
    background: #1f1f23;
    border-color: #3f3f46;
}
QPushButton:pressed {
    background: #27272a;
}
QPushButton:checked {
    background: #6366f1;
    border-color: #6366f1;
    color: #ffffff;
}
QPushButton:disabled {
    background: #111113;
    border-color: #1f1f23;
    color: #52525b;
}
QPushButton#primary {
    background: #6366f1;
    border-color: #6366f1;
    color: #ffffff;
    font-weight: 600;
    padding: 11px;
}
QPushButton#primary:hover {
    background: #7476f3;
    border-color: #7476f3;
}
QPushButton#primary:disabled {
    background: #23234a;
    border-color: #23234a;
    color: #7a7aa8;
}
QLineEdit {
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 0px 12px;
    min-height: 34px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}
QLineEdit:hover {
    border-color: #3f3f46;
}
QLineEdit:focus {
    border-color: #6366f1;
}
QComboBox {
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 0px 10px;
    min-height: 34px;
}
QComboBox:hover {
    border-color: #3f3f46;
}
QComboBox:focus, QComboBox:on {
    border-color: #6366f1;
}
QComboBox::drop-down {
    border: none;
    width: 26px;
}
QComboBoxPrivateContainer {
    background: #18181b;
    border: 1px solid #27272a;
    padding: 0px;
}
QComboBox QAbstractItemView {
    background: #18181b;
    border: none;
    outline: 0;
    padding: 4px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}
QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 0px 8px;
    border-radius: 6px;
}
QComboBox QAbstractItemView::item:hover {
    background: #27272a;
}
QComboBox QAbstractItemView::item:selected {
    background: #6366f1;
}
QSlider::groove:horizontal {
    height: 4px;
    background: #27272a;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #6366f1;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #fafafa;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QProgressBar {
    background: #18181b;
    border: none;
    border-radius: 3px;
    max-height: 6px;
    min-height: 6px;
    color: transparent;
}
QProgressBar::chunk {
    background: #6366f1;
    border-radius: 3px;
}
QWidget#frame {
    background: #09090b;
}
QWidget#titlebar {
    background: #111113;
    border-bottom: 1px solid #1f1f23;
}
QLabel#wintitle {
    font-size: 13px;
    font-weight: 700;
    color: #fafafa;
}
QLabel#winfile {
    font-size: 12px;
    color: #71717a;
}
QPushButton#winbtn {
    background: transparent;
    border: none;
    border-radius: 0px;
    padding: 0px;
    font-family: "Segoe MDL2 Assets";
    font-size: 10px;
    color: #e4e4e7;
    min-width: 46px;
    max-width: 46px;
    min-height: 40px;
    max-height: 40px;
}
QPushButton#winbtn:hover {
    background: #1f1f23;
}
QPushButton#winbtn[danger="true"]:hover {
    background: #e81123;
    color: #ffffff;
}
QToolTip {
    background: #18181b;
    border: 1px solid #27272a;
    color: #e4e4e7;
}
QMessageBox {
    background: #111113;
}
"""


class IntField(QLineEdit):
    def __init__(self):
        super().__init__()
        self._min = 1
        self._max = 1
        self.setValidator(QIntValidator(1, 1, self))
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setMinimumHeight(36)

    def setRange(self, lo, hi):
        self._min, self._max = lo, hi
        self.validator().setRange(lo, hi)

    def setValue(self, v):
        self.setText(str(int(v)))

    def value(self):
        try:
            v = int(self.text())
        except ValueError:
            v = self._max
        return max(self._min, min(self._max, v))

    def focusOutEvent(self, e):
        self.setText(str(self.value()))
        super().focusOutEvent(e)


def apply_dark_palette(app):
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor("#09090b"))
    pal.setColor(QPalette.WindowText, QColor("#e4e4e7"))
    pal.setColor(QPalette.Base, QColor("#18181b"))
    pal.setColor(QPalette.AlternateBase, QColor("#111113"))
    pal.setColor(QPalette.Text, QColor("#e4e4e7"))
    pal.setColor(QPalette.Button, QColor("#18181b"))
    pal.setColor(QPalette.ButtonText, QColor("#e4e4e7"))
    pal.setColor(QPalette.BrightText, QColor("#ffffff"))
    pal.setColor(QPalette.Highlight, QColor("#6366f1"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ToolTipBase, QColor("#18181b"))
    pal.setColor(QPalette.ToolTipText, QColor("#e4e4e7"))
    pal.setColor(QPalette.PlaceholderText, QColor("#71717a"))
    pal.setColor(QPalette.Light, QColor("#27272a"))
    pal.setColor(QPalette.Midlight, QColor("#1f1f23"))
    pal.setColor(QPalette.Mid, QColor("#27272a"))
    pal.setColor(QPalette.Dark, QColor("#09090b"))
    pal.setColor(QPalette.Shadow, QColor("#000000"))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        pal.setColor(QPalette.Disabled, role, QColor("#52525b"))
    app.setPalette(pal)


def style_combo(combo):
    combo.setItemDelegate(QStyledItemDelegate(combo))
    popup = combo.view().window()
    popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
    popup.setAttribute(Qt.WA_TranslucentBackground, False)
    combo.setCursor(Qt.PointingHandCursor)


def qimage_to_rgb(q):
    q = q.convertToFormat(QImage.Format_RGB888)
    w, h, bpl = q.width(), q.height(), q.bytesPerLine()
    buf = np.frombuffer(q.constBits(), dtype=np.uint8).reshape(h, bpl)
    return buf[:, : w * 3].reshape(h, w, 3).copy()


def rgb_to_qimage(a):
    a = np.ascontiguousarray(a)
    h, w, _ = a.shape
    return QImage(a.data, w, h, w * 3, QImage.Format_RGB888).copy()


def mask_to_np(q):
    w, h, bpl = q.width(), q.height(), q.bytesPerLine()
    arr = np.frombuffer(q.constBits(), dtype=np.uint8).reshape(h, bpl)
    arr = arr[:, : w * 4].reshape(h, w, 4)
    ok = arr[..., 3] > 64
    red = arr[..., 2] > 128
    green = arr[..., 1] > 128
    m = np.zeros((h, w), dtype=np.int8)
    m[ok & red] = 1
    m[ok & green & ~red] = -1
    return m


class Worker(QThread):
    progress = Signal(float)
    done = Signal(object, object)
    failed = Signal(str)

    def __init__(self, rgb, mask, tw, th):
        super().__init__()
        self.rgb, self.mask, self.tw, self.th = rgb, mask, tw, th
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            out, removed = carving.carve(
                self.rgb, self.mask, self.tw, self.th,
                progress=self.progress.emit, cancelled=lambda: self._cancel,
            )
            self.done.emit(out, removed)
        except carving.Cancelled:
            self.failed.emit("Cancelled")
        except Exception as ex:
            self.failed.emit(str(ex))


class Canvas(QWidget):
    PAD = 14

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setMinimumSize(480, 360)
        self.base = None
        self.mask = None
        self.show_mask = True
        self.mode = "protect"
        self.brush = 24
        self._last = None
        self._hover = None
        self._button = None

    def fit_rect(self):
        if self.base is None:
            return QRectF()
        area = QRectF(self.rect()).adjusted(self.PAD, self.PAD, -self.PAD, -self.PAD)
        iw, ih = self.base.width(), self.base.height()
        s = min(area.width() / iw, area.height() / ih)
        w, h = iw * s, ih * s
        return QRectF(area.x() + (area.width() - w) / 2, area.y() + (area.height() - h) / 2, w, h)

    def _img_pt(self, pos):
        r = self.fit_rect()
        s = r.width() / self.base.width()
        return QPointF((pos.x() - r.x()) / s, (pos.y() - r.y()) / s), s

    def _stroke(self, a, b, s):
        p = QPainter(self.mask)
        p.setRenderHint(QPainter.Antialiasing)
        erase = self._button == Qt.RightButton or self.mode == "erase"
        if erase:
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            pen = QPen(QColor(0, 0, 0, 255))
        else:
            pen = QPen(QColor(255, 0, 0) if self.mode == "protect" else QColor(0, 255, 0))
        pen.setWidthF(max(1.0, self.brush / s))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.drawLine(a, b)
        p.end()
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        frame = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor("#1f1f23"), 1))
        p.setBrush(QColor("#0c0c0e"))
        p.drawRoundedRect(frame, 14, 14)
        if self.base is None:
            p.setPen(QColor("#52525b"))
            p.setFont(QFont("Segoe UI", 11))
            p.drawText(self.rect(), Qt.AlignCenter, "Open an image, drag one in, or paste with Ctrl+V")
            return
        r = self.fit_rect()
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawImage(r, self.base)
        if self.show_mask and self.mask is not None:
            p.setOpacity(0.6)
            p.drawImage(r, self.mask)
            p.setOpacity(1.0)
        if self.show_mask and self._hover is not None:
            p.setPen(QPen(QColor(255, 255, 255, 200), 1))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(self._hover, self.brush / 2, self.brush / 2)

    def _can_paint(self):
        return self.base is not None and self.mask is not None and self.show_mask

    def mousePressEvent(self, e):
        if self._can_paint() and e.button() in (Qt.LeftButton, Qt.RightButton):
            self._button = e.button()
            pt, s = self._img_pt(e.position())
            self._last = pt
            self._stroke(pt, pt, s)

    def mouseMoveEvent(self, e):
        self._hover = e.position()
        if self._can_paint() and self._last is not None:
            pt, s = self._img_pt(e.position())
            self._stroke(self._last, pt, s)
            self._last = pt
        else:
            self.update()

    def mouseReleaseEvent(self, e):
        self._last = None
        self._button = None

    def leaveEvent(self, _):
        self._hover = None
        self.update()


class TitleBar(QWidget):
    def __init__(self, host):
        super().__init__()
        self.host = host
        self.setObjectName("titlebar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(40)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 0, 0)
        lay.setSpacing(0)
        logo = QLabel()
        logo.setPixmap(
            QPixmap(resource_path("assets/icon.png")).scaled(
                22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        lay.addWidget(logo)
        lay.addSpacing(10)
        brand = QLabel("seam<span style='color:#6366f1'>cut</span>")
        brand.setTextFormat(Qt.RichText)
        brand.setObjectName("wintitle")
        self.file = QLabel("")
        self.file.setObjectName("winfile")
        lay.addWidget(brand)
        lay.addSpacing(12)
        lay.addWidget(self.file)
        lay.addStretch(1)
        self.b_min = self._button("\uE921", self.host.showMinimized)
        self.b_max = self._button("\uE922", self.toggle_max)
        self.b_close = self._button("\uE8BB", self.host.close)
        self.b_close.setProperty("danger", True)
        for b in (self.b_min, self.b_max, self.b_close):
            lay.addWidget(b)

    def _button(self, glyph, slot):
        b = QPushButton(glyph)
        b.setObjectName("winbtn")
        b.setFocusPolicy(Qt.NoFocus)
        b.clicked.connect(slot)
        return b

    def toggle_max(self):
        if self.host.isMaximized():
            self.host.showNormal()
        else:
            self.host.showMaximized()

    def sync(self):
        self.b_max.setText("\uE923" if self.host.isMaximized() else "\uE922")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.host.windowHandle():
            self.host.windowHandle().startSystemMove()

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.toggle_max()


class ResizeFrame(QWidget):
    MARGIN = 6

    def __init__(self, host):
        super().__init__()
        self.host = host
        self.setObjectName("frame")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMouseTracking(True)

    def _edges(self, pos):
        m = self.MARGIN
        flags = []
        if pos.x() < m:
            flags.append(Qt.LeftEdge)
        if pos.x() > self.width() - m:
            flags.append(Qt.RightEdge)
        if pos.y() < m:
            flags.append(Qt.TopEdge)
        if pos.y() > self.height() - m:
            flags.append(Qt.BottomEdge)
        if not flags:
            return None
        edges = flags[0]
        for f in flags[1:]:
            edges |= f
        return edges

    def _cursor(self, edges):
        l = bool(edges & Qt.LeftEdge)
        r = bool(edges & Qt.RightEdge)
        t = bool(edges & Qt.TopEdge)
        b = bool(edges & Qt.BottomEdge)
        if (l and t) or (r and b):
            return Qt.SizeFDiagCursor
        if (r and t) or (l and b):
            return Qt.SizeBDiagCursor
        if l or r:
            return Qt.SizeHorCursor
        return Qt.SizeVerCursor

    def mouseMoveEvent(self, e):
        edges = None if self.host.isMaximized() else self._edges(e.position())
        if edges is None:
            self.unsetCursor()
        else:
            self.setCursor(self._cursor(edges))

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton or self.host.isMaximized():
            return
        edges = self._edges(e.position())
        if edges is not None and self.host.windowHandle():
            self.host.windowHandle().startSystemResize(edges)


def section_label(text):
    lbl = QLabel(text.upper())
    lbl.setObjectName("section")
    return lbl


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("seamcut")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.resize(1240, 800)
        self.setAcceptDrops(True)

        self.src_q = None
        self.rgb = None
        self.orig_q = None
        self.result = None
        self.result_q = None
        self.seams_q = None
        self.removed = None
        self.worker = None

        self.canvas = Canvas()

        panel = QWidget()
        panel.setObjectName("sidebar")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setFixedWidth(300)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(20, 20, 20, 20)
        pl.setSpacing(10)

        self.btn_open = QPushButton("Open image")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_dialog)
        pl.addWidget(self.btn_open)
        pl.addSpacing(8)

        pl.addWidget(section_label("Target size"))
        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.sw = IntField()
        self.sh = IntField()
        self.max_side = QComboBox()
        for label, val in (("600 px", 600), ("900 px", 900), ("1200 px", 1200), ("1600 px", 1600), ("Full size", 0)):
            self.max_side.addItem(label, val)
        self.max_side.setCurrentIndex(2)
        self.max_side.setMinimumHeight(36)
        style_combo(self.max_side)
        self.max_side.currentIndexChanged.connect(self.reload_scaled)
        form.addRow("Width (px)", self.sw)
        form.addRow("Height (px)", self.sh)
        form.addRow("Max side", self.max_side)
        pl.addLayout(form)
        pl.addSpacing(8)

        pl.addWidget(section_label("Mask brush"))
        row = QHBoxLayout()
        row.setSpacing(6)
        self.tool_group = QButtonGroup(self)
        for key, label in (("protect", "Protect"), ("remove", "Remove"), ("erase", "Erase")):
            b = QPushButton(label)
            b.setCheckable(True)
            b.setChecked(key == "protect")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self.set_tool(k))
            self.tool_group.addButton(b)
            row.addWidget(b)
        pl.addLayout(row)
        self.brush = QSlider(Qt.Horizontal)
        self.brush.setRange(3, 120)
        self.brush.setValue(24)
        self.brush.valueChanged.connect(self.set_brush)
        pl.addWidget(self.brush)
        clear = QPushButton("Clear mask")
        clear.setCursor(Qt.PointingHandCursor)
        clear.clicked.connect(self.clear_mask)
        pl.addWidget(clear)
        hint = QLabel("Red keeps pixels, green removes them.\nRight-click erases.")
        hint.setObjectName("hint")
        pl.addWidget(hint)
        pl.addSpacing(8)

        pl.addWidget(section_label("View"))
        self.view = QComboBox()
        self.view.addItem("Original + mask", "original")
        self.view.addItem("Result", "result")
        self.view.addItem("Seams", "seams")
        self.view.setMinimumHeight(36)
        style_combo(self.view)
        self.view.currentIndexChanged.connect(self.update_view)
        pl.addWidget(self.view)
        pl.addStretch(1)

        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        self.bar.setVisible(False)
        pl.addWidget(self.bar)

        self.status = QLabel("Open an image to get started.")
        self.status.setObjectName("hint")
        self.status.setWordWrap(True)
        pl.addWidget(self.status)

        self.btn_run = QPushButton("Cut")
        self.btn_run.setObjectName("primary")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_cut)
        pl.addWidget(self.btn_run)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self.cancel_cut)
        pl.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save result")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save)
        pl.addWidget(self.btn_save)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(16, 16, 16, 16)
        rl.addWidget(self.canvas)

        body = QWidget()
        bl = QHBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)
        bl.addWidget(panel)
        bl.addWidget(right, 1)

        self.titlebar = TitleBar(self)

        inner = QWidget()
        inner.setObjectName("root")
        inner.setAttribute(Qt.WA_StyledBackground, True)
        inner.setCursor(Qt.ArrowCursor)
        il = QVBoxLayout(inner)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(0)
        il.addWidget(self.titlebar)
        il.addWidget(body, 1)

        self.frame = ResizeFrame(self)
        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(6, 6, 6, 6)
        self.frame_layout.addWidget(inner)
        self.setCentralWidget(self.frame)

        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_dialog)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save)
        QShortcut(QKeySequence("Ctrl+V"), self, activated=self.paste)

    def changeEvent(self, e):
        if e.type() == QEvent.WindowStateChange and hasattr(self, "frame_layout"):
            m = 0 if self.isMaximized() else 6
            self.frame_layout.setContentsMargins(m, m, m, m)
            self.titlebar.sync()
        super().changeEvent(e)

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)"
        )
        if path:
            self.open_path(path)

    def open_path(self, path):
        q = QImage(path)
        if q.isNull():
            QMessageBox.warning(self, "seamcut", "Could not open the image.")
            return
        self.src_q = q
        self.setWindowTitle(f"seamcut - {os.path.basename(path)}")
        self.titlebar.file.setText(os.path.basename(path))
        self.reload_scaled()

    def paste(self):
        q = QApplication.clipboard().image()
        if not q.isNull():
            self.src_q = q
            self.reload_scaled()

    def reload_scaled(self):
        if self.src_q is None or (self.worker and self.worker.isRunning()):
            return
        q = self.src_q
        ms = self.max_side.currentData()
        if ms and max(q.width(), q.height()) > ms:
            q = q.scaled(ms, ms, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.rgb = qimage_to_rgb(q)
        self.orig_q = rgb_to_qimage(self.rgb)
        h, w = self.rgb.shape[:2]
        mask = QImage(w, h, QImage.Format_ARGB32)
        mask.fill(0)
        self.canvas.mask = mask
        self.result = self.result_q = self.seams_q = self.removed = None
        self.sw.setRange(1, w)
        self.sh.setRange(1, h)
        self.sw.setValue(w)
        self.sh.setValue(h)
        self.view.setCurrentIndex(0)
        self.btn_run.setEnabled(True)
        self.btn_save.setEnabled(False)
        self.status.setText(f"{w}x{h} loaded. Set a target size and press Cut.")
        self.update_view()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            self.open_path(urls[0].toLocalFile())

    def set_tool(self, key):
        self.canvas.mode = key

    def set_brush(self, v):
        self.canvas.brush = v

    def clear_mask(self):
        if self.canvas.mask is not None:
            self.canvas.mask.fill(0)
            self.canvas.update()

    def update_view(self):
        if self.orig_q is None:
            return
        mode = self.view.currentData()
        if mode == "result" and self.result_q is not None:
            self.canvas.base, self.canvas.show_mask = self.result_q, False
        elif mode == "seams" and self.seams_q is not None:
            self.canvas.base, self.canvas.show_mask = self.seams_q, False
        else:
            self.canvas.base, self.canvas.show_mask = self.orig_q, True
        self.canvas.update()

    def run_cut(self):
        if self.rgb is None or (self.worker and self.worker.isRunning()):
            return
        h, w = self.rgb.shape[:2]
        tw, th = self.sw.value(), self.sh.value()
        if tw == w and th == h:
            self.status.setText("Target size matches the original.")
            return
        mask = mask_to_np(self.canvas.mask)
        self.worker = Worker(self.rgb, mask, tw, th)
        self.worker.progress.connect(lambda v: self.bar.setValue(int(v * 1000)))
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.bar.setValue(0)
        self.bar.setVisible(True)
        self.btn_run.setEnabled(False)
        self.btn_cancel.setVisible(True)
        self.btn_save.setEnabled(False)
        self.status.setText("Cutting... the first run compiles kernels and may take a few seconds.")
        self.worker.start()

    def cancel_cut(self):
        if self.worker:
            self.worker.cancel()

    def finish_ui(self):
        self.bar.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_run.setEnabled(True)

    def on_done(self, out, removed):
        self.finish_ui()
        self.result, self.removed = out, removed
        self.result_q = rgb_to_qimage(out)
        seams = self.rgb.copy()
        seams[removed] = (255, 40, 70)
        self.seams_q = rgb_to_qimage(seams)
        h, w = self.rgb.shape[:2]
        self.status.setText(f"{w}x{h} -> {out.shape[1]}x{out.shape[0]}")
        self.btn_save.setEnabled(True)
        self.view.setCurrentIndex(1)
        self.update_view()

    def on_failed(self, msg):
        self.finish_ui()
        self.status.setText(msg)

    def save(self):
        if self.result_q is None:
            return
        name = f"seamcut-{self.result_q.width()}x{self.result_q.height()}.png"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save image", name, "PNG (*.png);;JPEG (*.jpg);;WebP (*.webp)"
        )
        if path:
            if self.result_q.save(path):
                self.status.setText(f"Saved: {os.path.basename(path)}")
            else:
                QMessageBox.warning(self, "seamcut", "Could not save the file.")


def main():
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("seamcut.desktop.app")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
    apply_dark_palette(app)
    app.setStyleSheet(STYLE)
    threading.Thread(target=carving.warmup, daemon=True).start()
    win = MainWindow()
    win.show()
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        win.open_path(sys.argv[1])
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
