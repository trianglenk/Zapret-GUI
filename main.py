from __future__ import annotations

import ctypes
import math
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from qt import (  # PySide6 (Windows 10/11) или PySide2 (Windows 7)
    QT_API, QAbstractButton, QAction, QApplication, QBoxLayout, QButtonGroup, QCheckBox,
    QColor, QColorDialog, QComboBox, QEasingCurve, QFileDialog, QFont, QFrame, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QIcon, QInputDialog, QLabel, QLineEdit, QLinearGradient, QListWidget, QListWidgetItem,
    QLocalServer, QLocalSocket, QMainWindow, QMenu, QMessageBox, QObject, QPainter, QPainterPath, QPen, QPixmap,
    QPlainTextEdit, QPointF, QPropertyAnimation, QPushButton, QRectF, QScrollArea, QSize, QSlider, QStackedWidget,
    QSystemTrayIcon, Qt, QTimer, QVariantAnimation, QVBoxLayout, QWidget,
    Signal,
)

import core
import look
from look import (ACCENT_PRESETS, CORNER_KEYS, DENSITY_KEYS, FONT_KEYS, LEGACY_THEMES, THEME_KEYS, THEMES)

SERVER_NAME = "ZapretGUI.single"
COMPACT_WIDTH = 720

P = look.compute_palette({}, "violet")  # текущая палитра (тема + акцент + шрифт + углы + плотность)


def anim_on() -> bool:
    return bool(core.CFG.get("animations", True))


def build_style() -> str:
    c = P
    return f"""
* {{ font-family: 'Segoe UI'; font-size: {c['FS']}pt; color: {c['TEXT']}; }}
QMainWindow, QWidget#page, QScrollArea, QWidget#scrollbody {{ background: {c['BG']}; border: none; }}
QFrame#card {{ background: {c['SURFACE']}; border: 1px solid {c['BORDER']}; border-radius: {c['R1']}px; }}
QFrame#sectionBody {{ background: transparent; border: none; }}
QLabel#cardTitle {{ color: {c['MUTED']}; font-weight: 600; }}
QLabel#status {{ font-size: 20pt; font-weight: 700; }}
QLabel#h1 {{ font-size: 17pt; font-weight: 700; }}
QLabel#caption {{ color: {c['MUTED']}; font-size: 9pt; font-weight: 600; }}
QLabel#muted {{ color: {c['MUTED']}; }}
QLabel#mono {{ font-family: Consolas; color: {c['MONO']}; }}
QPushButton {{ background: {c['BTN']}; border: 1px solid {c['BORDER']}; padding: {c['PAD']}px 14px; border-radius: {c['R2']}px; }}
QPushButton:hover {{ background: {c['HOVER']}; border-color: {c['ACC1']}; }}
QPushButton:pressed {{ padding-top: {c['PAD'] + 1}px; }}
QPushButton:focus {{ border: 1px solid {c['ACC1']}; }}
QPushButton#sectionHeader {{ background: transparent; border: none; text-align: left; font-weight: 650;
    padding: 7px 4px; color: {c['TEXT']}; }}
QPushButton#sectionHeader:hover {{ background: {c['HOVER']}; border-radius: {c['R2']}px; }}
QPushButton:disabled {{ color: {c['DIS']}; background: {c['SURFACE']}; }}
QPushButton#accent {{ border: none; font-weight: 600; color: {c['ONACC']};
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c['ACC1']}, stop:1 {c['ACC2']}); }}
QPushButton#accent:disabled {{ background: {c['HOVER']}; color: {c['DIS']}; }}
QPushButton#iconbtn {{ background: transparent; border: none; padding: 6px; border-radius: 9px; }}
QPushButton#iconbtn:hover {{ background: {c['HOVER']}; }}
QPushButton#chip {{ background: transparent; border: 1px dashed {c['DIS']}; color: {c['MUTED']};
    padding: 5px 10px; border-radius: 14px; }}
QPushButton#chip:hover {{ color: {c['TEXT']}; border-color: {c['ACC1']}; }}
QPushButton#ghost {{ background: transparent; border: none; color: {c['MUTED']}; padding: 4px 8px; }}
QPushButton#ghost:hover {{ color: {c['BAD']}; }}
QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTableWidget {{
    background: {c['SURFACE']}; border: 1px solid {c['BORDER']}; border-radius: {c['R2']}px; padding: {c['PADI']}px; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {c['ACC1']}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{ background: {c['SURFACE']}; border: 1px solid {c['BORDER']};
    selection-background-color: {c['ACC1']}; selection-color: #ffffff; outline: 0; }}
QListWidget::item {{ padding: {c['PADI'] - 1}px; border-radius: 6px; }}
QListWidget::item:selected {{ background: {c['SEL']}; color: {c['TEXT']}; }}
QListWidget::indicator {{ width: 16px; height: 16px; border-radius: 5px; border: 1px solid {c['DIS']};
    background: {c['BG']}; }}
QListWidget::indicator:checked {{ background: {c['ACC1']}; border-color: {c['ACC1']}; }}
QHeaderView::section {{ background: {c['SURFACE']}; border: none; color: {c['MUTED']}; padding: 6px; }}
QTableWidget {{ gridline-color: transparent; }}
QCheckBox {{ spacing: 10px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 6px; border: 1px solid {c['DIS']};
    background: {c['BG']}; }}
QCheckBox::indicator:checked {{ background: {c['ACC1']}; border-color: {c['ACC1']}; }}
QScrollBar:vertical {{ background: transparent; width: 6px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {c['OFF']}; border-radius: 3px; min-height: 32px; }}
QScrollBar::handle:vertical:hover {{ background: {c['DIS']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; width: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 6px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {c['OFF']}; border-radius: 3px; min-width: 32px; }}
QScrollBar::handle:horizontal:hover {{ background: {c['DIS']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ height: 0; width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}
QSlider::groove:horizontal {{ height: 6px; background: {c['OFF']}; border-radius: 3px; }}
QSlider::handle:horizontal {{ width: 18px; height: 18px; margin: -6px 0; background: {c['ACC1']};
    border-radius: 9px; border: 2px solid {c['SURFACE']}; }}
QSlider::sub-page:horizontal {{ background: {c['ACC1']}; border-radius: 3px; }}
QSlider::add-page:horizontal {{ background: {c['OFF']}; border-radius: 3px; }}
QToolTip {{ background: {c['SURFACE']}; color: {c['TEXT']}; border: 1px solid {c['BORDER']}; }}
"""


def system_is_light() -> bool:
    try:
        return QApplication.styleHints().colorScheme() == Qt.ColorScheme.Light
    except Exception:  # Qt 5 / старый Qt 6: определить тему системы нельзя
        return False


def mix(c1: str, c2: str, t: float) -> str:
    return look.mix_hex(c1, c2, t)


def set_palette(name: str | None = None) -> None:
    P.update(look.compute_palette(core.CFG, name, system_is_light()))


# ---------- служебное ----------
def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> None:
    args = " ".join(f'"{a}"' for a in sys.argv[1:])
    if getattr(sys, "frozen", False):
        exe, params = sys.executable, args
    else:
        pyw = Path(sys.executable).with_name("pythonw.exe")  # без окна консоли
        exe = str(pyw) if pyw.exists() else sys.executable
        params = f'"{sys.argv[0]}" {args}'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)


def resource_path(name: str) -> str:
    base = getattr(sys, "_MEIPASS", None) or Path(__file__).parent
    return str(Path(base) / name)


def app_icon() -> QIcon:
    return QIcon(resource_path("icon.ico"))


def status_icon(on: bool) -> QIcon:
    """Значок в трее: зелёный круг, когда обход запущен, красный, когда отключён."""
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#22c55e" if on else "#ef4444"))
    p.setPen(QPen(QColor("#14532d" if on else "#7f1d1d"), 4))
    p.drawEllipse(6, 6, 52, 52)
    p.end()
    return QIcon(pm)


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(str(path))  # Windows


def card(title: str | None = None):
    f = QFrame()
    f.setObjectName("card")
    f.setProperty("dens", True)  # отступы подстраиваются под выбранную плотность (apply_density)
    lay = QVBoxLayout(f)
    lay.setContentsMargins(P["MARG"], P["MARG"] - 2, P["MARG"], P["MARG"] - 2)
    lay.setSpacing(P["GAP"] - 2)
    if title:
        t = QLabel(title)
        t.setObjectName("cardTitle")
        lay.addWidget(t)
    return f, lay


def page(title: str | None = None) -> tuple[QWidget, QVBoxLayout]:
    w = QWidget()
    w.setObjectName("page")
    w.setProperty("pagebody", True)
    lay = QVBoxLayout(w)
    lay.setContentsMargins(24, 18, 24, 12)
    lay.setSpacing(P["GAP"])
    if title:
        h = QLabel(title)
        h.setObjectName("h1")
        lay.addWidget(h)
    return w, lay


def path_row(title: str, getter) -> QHBoxLayout:
    row = QHBoxLayout()
    box = QVBoxLayout()
    box.setSpacing(2)
    v = QLabel(str(getter()))
    v.setObjectName("mono")
    v.setWordWrap(True)
    v.setTextInteractionFlags(Qt.TextSelectableByMouse)
    box.addWidget(QLabel(title))
    box.addWidget(v)
    row.addLayout(box, 1)
    b = QPushButton("Открыть")
    b.clicked.connect(lambda: open_folder(getter()))
    row.addWidget(b)
    row.value_label, row.getter = v, getter
    return row


def draw_icon(p: QPainter, kind: str, c: QPointF, col: QColor) -> None:
    """Иконки рисуются кодом на сетке 24x24, без внешних файлов."""
    p.save()
    p.translate(c.x() - 12, c.y() - 12)
    p.setPen(QPen(col, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    if kind == "power":
        p.drawArc(QRectF(5, 6, 14, 14), 130 * 16, 280 * 16)
        p.drawLine(QPointF(12, 3), QPointF(12, 12))
    elif kind == "globe":
        p.drawEllipse(QRectF(3, 3, 18, 18))
        p.drawEllipse(QRectF(8, 3, 8, 18))
        p.drawLine(QPointF(3, 12), QPointF(21, 12))
    elif kind == "list":
        for y in (6, 12, 18):
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(10, y), QPointF(20, y))
            p.setBrush(col)
            p.drawEllipse(QPointF(5, y), 1.3, 1.3)
    elif kind == "restart":
        p.drawArc(QRectF(5, 5, 14, 14), 100 * 16, 280 * 16)
        tip = QPointF(12 + 7 * math.cos(math.radians(20)), 12 - 7 * math.sin(math.radians(20)))
        dx, dy = -math.sin(math.radians(20)), -math.cos(math.radians(20))  # направление движения в конце дуги
        for ang in (150, -150):
            a_ = math.radians(ang)
            bx, by = dx * math.cos(a_) - dy * math.sin(a_), dx * math.sin(a_) + dy * math.cos(a_)
            p.drawLine(tip, QPointF(tip.x() + 4.5 * bx, tip.y() + 4.5 * by))
    elif kind == "close":
        p.drawLine(QPointF(6, 6), QPointF(18, 18))
        p.drawLine(QPointF(18, 6), QPointF(6, 18))
    elif kind == "link":
        p.drawPolyline([QPointF(14, 4), QPointF(20, 4), QPointF(20, 10)])
        p.drawLine(QPointF(20, 4), QPointF(11, 13))
        p.drawPolyline([QPointF(17, 14), QPointF(17, 19), QPointF(5, 19), QPointF(5, 7), QPointF(10, 7)])
    elif kind == "layers":
        p.drawPolygon([QPointF(12, 4), QPointF(21, 9), QPointF(12, 14), QPointF(3, 9)])
        p.drawPolyline([QPointF(3, 13), QPointF(12, 18), QPointF(21, 13)])
        p.drawPolyline([QPointF(3, 17), QPointF(12, 22), QPointF(21, 17)])
    elif kind == "more":
        for y, x in ((7, 15), (17, 9)):
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(4, y), QPointF(20, y))
            p.setBrush(QColor(P["SURFACE"]))
            p.drawEllipse(QPointF(x, y), 2.6, 2.6)
    p.restore()


class NavButton(QAbstractButton):
    """Кнопка вкладки: иконка, название в подсказке. Выбранная вкладка подсвечивается градиентной плашкой
    с индикатором, всё это плавно анимируется."""

    def __init__(self, kind: str, tip: str):
        super().__init__()
        self.kind, self.hover, self.vertical = kind, False, False
        self.setCheckable(True)
        self.setToolTip(tip)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(56, 48)
        self._lv = 0.0  # 0 = ничего, 1 = наведено, 2 = выбрано
        self.anim = QVariantAnimation(self)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.valueChanged.connect(self._set_lv)
        self.toggled.connect(lambda _=False: self._retarget())

    def _set_lv(self, v):
        self._lv = float(v)
        self.update()

    def _retarget(self):
        target = 2.0 if self.isChecked() else (1.0 if self.hover else 0.0)
        self.anim.stop()
        if not anim_on():  # без анимаций: сразу в конечное состояние
            self._lv = target
            self.update()
            return
        self.anim.setDuration(200)
        self.anim.setStartValue(self._lv)
        self.anim.setEndValue(target)
        self.anim.start()

    def enterEvent(self, e):
        self.hover = True
        self._retarget()

    def leaveEvent(self, e):
        self.hover = False
        self._retarget()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        lv = self._lv
        sel = max(0.0, min(1.0, lv - 1.0))
        p.setPen(Qt.NoPen)
        if lv > 0.01:
            p.setBrush(QColor(P["HOVER"]))
            p.setOpacity(min(lv, 1.0))
            p.drawRoundedRect(r, 15, 15)
            p.setOpacity(1.0)
        if sel > 0.01:
            g = QLinearGradient(r.topLeft(), r.bottomRight())
            c1, c2 = QColor(P["ACC1"]), QColor(P["ACC2"])
            c1.setAlpha(int(70 * sel))
            c2.setAlpha(int(45 * sel))
            g.setColorAt(0, c1)
            g.setColorAt(1, c2)
            p.setBrush(g)
            edge = QColor(P["ACC1"])
            edge.setAlpha(int(110 * sel))
            p.setPen(QPen(edge, 1.2))
            p.drawRoundedRect(r, 15, 15)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(P["ACC1"]))  # индикатор: полоска снизу (панель внизу) или слева (панель слева)
            if self.vertical:
                h = 20 * sel
                p.drawRoundedRect(QRectF(0.5, self.height() / 2 - h / 2, 3, h), 1.5, 1.5)
            else:
                w = 18 * sel
                p.drawRoundedRect(QRectF(self.width() / 2 - w / 2, self.height() - 4.5, w, 3), 1.5, 1.5)
        draw_icon(p, self.kind, r.center(), QColor(mix(P["MUTED"], P["ACC_FG"], sel)))


class BusyBar(QWidget):
    """Тонкая бегущая полоска: показывает, что программа что-то делает (скачивание, подбор, обновление)."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(240, 5)
        self._t, self._run = 0.0, False
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(1300)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setLoopCount(-1)
        self.anim.valueChanged.connect(self._tick)

    def _tick(self, v):
        self._t = float(v)
        self.update()

    def run(self, on: bool):
        if on == self._run:
            return
        self._run = on
        if on and self.isVisible() and anim_on():
            self.anim.start()
        elif not on:
            self.anim.stop()
        self.update()

    def showEvent(self, e):
        if self._run and anim_on():
            self.anim.start()

    def hideEvent(self, e):
        self.anim.stop()

    def paintEvent(self, _):
        if not self._run:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(P["OFF"]))
        p.drawRoundedRect(r, 2.5, 2.5)
        w = r.width() * 0.35
        x = -w + (r.width() + w) * self._t
        if not anim_on():  # без анимаций: неподвижная полоска «идёт работа»
            w, x = r.width() * 0.5, r.width() * 0.25
        p.setClipRect(r)
        grad = QLinearGradient(x, 0, x + w, 0)
        grad.setColorAt(0, QColor(P["ACC1"]))
        grad.setColorAt(1, QColor(P["ACC2"]))
        p.setBrush(grad)
        p.drawRoundedRect(QRectF(x, 0, w, r.height()), 2.5, 2.5)


SITE_PRESETS = [("YouTube", "https://www.youtube.com"), ("Discord", "https://discord.com"),
                ("Telegram", "https://web.telegram.org"), ("Instagram", "https://www.instagram.com"),
                ("X (Twitter)", "https://x.com"), ("Spotify", "https://open.spotify.com"),
                ("Twitch", "https://www.twitch.tv"), ("GitHub", "https://github.com")]
AVATAR_COLORS = ["#7c5cff", "#3b82f6", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444", "#ec4899", "#8b5cf6"]


def rgba(color: str, alpha: int) -> str:
    c = QColor(color)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


class RatioBar(QWidget):
    """Полоска «сколько сайтов доступно»: плавно заполняется, цвет от красного к зелёному."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(8)
        self._v = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.valueChanged.connect(self._set)

    def _set(self, v):
        self._v = float(v)
        self.update()

    def set_ratio(self, r: float):
        self.anim.stop()
        if not anim_on():
            self._v = max(0.0, min(1.0, r))
            self.update()
            return
        self.anim.setDuration(380)
        self.anim.setStartValue(self._v)
        self.anim.setEndValue(max(0.0, min(1.0, r)))
        self.anim.start()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(P["OFF"]))
        p.drawRoundedRect(r, 4, 4)
        if self._v > 0.001:
            p.setBrush(QColor(mix(P["BAD"], P["OK"], self._v)))
            p.drawRoundedRect(QRectF(0, 0, max(8.0, r.width() * self._v), r.height()), 4, 4)


class SiteRow(QFrame):
    """Строка сайта: иконка (favicon) или буква, название, адрес, статус и кнопки."""

    def __init__(self, name: str, url: str):
        super().__init__()
        self.url = url
        self.setObjectName("card")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 8, 10)
        lay.setSpacing(12)
        col = AVATAR_COLORS[sum(map(ord, name)) % len(AVATAR_COLORS)]
        self._avatar_col = col
        self.avatar = QLabel((name[:1] or "?").upper())
        self.avatar.setFixedSize(40, 40)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet(f"background: {col}; color: #ffffff; border-radius: 20px; "
                                  "font-size: 13pt; font-weight: 700;")
        lay.addWidget(self.avatar, alignment=Qt.AlignVCenter)
        mid = QVBoxLayout()
        mid.setSpacing(2)
        self.name_lbl = QLabel(name)
        self.name_lbl.setStyleSheet("font-weight: 700;")
        self.url_lbl = QLabel(core.site_name(url))
        self.url_lbl.setObjectName("muted")
        status = QHBoxLayout()
        status.setSpacing(8)
        self.pill = QLabel()
        self.ms_lbl = QLabel()
        self.ms_lbl.setObjectName("muted")
        status.addWidget(self.pill)
        status.addWidget(self.ms_lbl)
        status.addStretch(1)
        mid.addWidget(self.name_lbl)
        mid.addWidget(self.url_lbl)
        mid.addLayout(status)
        lay.addLayout(mid, 1)
        self.check_btn = self._icon_btn("restart", "Проверить этот сайт")
        self.open_btn = self._icon_btn("link", "Открыть в браузере")
        self.del_btn = self._icon_btn("close", "Удалить из списка")
        for b in (self.check_btn, self.open_btn, self.del_btn):
            lay.addWidget(b, alignment=Qt.AlignVCenter)
        self.fx = QGraphicsOpacityEffect(self.pill)
        self.pill.setGraphicsEffect(self.fx)
        self.pulse = QPropertyAnimation(self.fx, b"opacity", self)  # «дыхание» пока идёт проверка
        self.pulse.setDuration(900)
        self.pulse.setKeyValueAt(0.0, 1.0)
        self.pulse.setKeyValueAt(0.5, 0.35)
        self.pulse.setKeyValueAt(1.0, 1.0)
        self.pulse.setLoopCount(-1)
        self.pop = QPropertyAnimation(self.fx, b"opacity", self)    # появление результата
        self.pop.setDuration(260)
        self.pop.setStartValue(0.2)
        self.pop.setEndValue(1.0)
        self.set_result(None, animate=False)

    @staticmethod
    def _icon_btn(kind: str, tip: str) -> QPushButton:
        b = QPushButton()
        b.setObjectName("iconbtn")
        b.setIcon(make_icon(kind, P["MUTED"], 18))
        b.setIconSize(QSize(18, 18))
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        return b

    def _pill(self, text: str, color: str):
        self.pill.setText(text)
        self.pill.setStyleSheet(f"color: {color}; background: {rgba(color, 40)}; border-radius: 10px; "
                                "padding: 2px 10px; font-weight: 600;")

    def set_checking(self):
        self._pill("Проверяю…", P["ACC_FG"])
        self.ms_lbl.setText("")
        self.pop.stop()
        if anim_on():
            self.pulse.start()

    def set_favicon(self, data: bytes):
        """Иконка внутри скруглённой рамки 40×40, без выхода за края."""
        src = QPixmap()
        if not data or not src.loadFromData(data):
            return
        box = 40
        inner = 32
        src = src.scaled(inner, inner, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        canvas = QPixmap(box, box)
        canvas.fill(Qt.transparent)
        p = QPainter(canvas)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        # фон и обводка
        p.setPen(QPen(QColor(P["BORDER"]), 1))
        p.setBrush(QColor(P["SURFACE"]))
        p.drawRoundedRect(QRectF(0.5, 0.5, box - 1, box - 1), 10, 10)
        # клип по скруглению, иконка по центру
        path = QPainterPath()
        path.addRoundedRect(QRectF(2, 2, box - 4, box - 4), 8, 8)
        p.setClipPath(path)
        x = (box - src.width()) // 2
        y = (box - src.height()) // 2
        p.drawPixmap(x, y, src)
        p.end()
        self.avatar.setText("")
        self.avatar.setPixmap(canvas)
        self.avatar.setStyleSheet("background: transparent; border: none;")

    def set_result(self, res, animate: bool = True):
        self.pulse.stop()
        self.fx.setOpacity(1.0)
        if res is None:
            self._pill("Не проверен", P["MUTED"])
            self.ms_lbl.setText("")
            return
        if res["ok"]:
            self._pill("Доступен", P["OK"])
            ms = res["ms"]
            color = P["OK"] if ms < 400 else ("#f59e0b" if ms < 1200 else P["BAD"])
            self.ms_lbl.setStyleSheet(f"color: {color};")
            self.ms_lbl.setText(f"{ms} мс  ·  HTTP {res['code']}")
        else:
            self._pill("Недоступен", P["BAD"])
            self.ms_lbl.setStyleSheet(f"color: {P['MUTED']};")
            self.ms_lbl.setText("нет ответа")
        if animate and anim_on():
            self.pop.start()


def make_icon(kind: str, color: str, size: int = 22) -> QIcon:
    """Иконка из тех же рисунков, что и во вкладках, для текстовых кнопок."""
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size * 2 / 24, size * 2 / 24)
    draw_icon(p, kind, QPointF(12, 12), QColor(color))
    p.end()
    return QIcon(pm)


class ThemeSwatch(QAbstractButton):
    """Круглый образец темы из трёх цветов."""

    def __init__(self, key: str):
        super().__init__()
        self.key = key
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(40, 40)
        self.setToolTip("Как в системе" if key == "auto" else THEMES[key]["NAME"])
        self.hover_cb = None  # вызывается с {"theme": key} при наведении и с None, когда мышь ушла

    def enterEvent(self, e):
        if self.hover_cb:
            self.hover_cb({"theme": self.key})

    def leaveEvent(self, e):
        if self.hover_cb:
            self.hover_cb(None)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        p.setPen(Qt.NoPen)
        if self.key == "auto":  # половина тёмная, половина светлая
            p.setBrush(QColor("#0c0d12"))
            p.drawPie(r, 90 * 16, 180 * 16)
            p.setBrush(QColor("#ffffff"))
            p.drawPie(r, 270 * 16, 180 * 16)
            p.setBrush(QColor("#7c5cff"))
            p.drawEllipse(r.center(), 4, 4)
        else:
            for i, col in enumerate(THEMES[self.key]["SWATCH"]):
                p.setBrush(QColor(col))
                p.drawPie(r, (90 + 120 * i) * 16, 120 * 16)
        p.setBrush(Qt.NoBrush)
        if self.isChecked():
            p.setPen(QPen(QColor(P["ACC_FG"]), 2.5))
            p.drawEllipse(QRectF(self.rect()).adjusted(2, 2, -2, -2))
        else:
            p.setPen(QPen(QColor(P["BORDER"]), 1.5))
            p.drawEllipse(r)


class ColorDot(QAbstractButton):
    """Круглый образец цвета акцента. color=None: цвет берётся из темы."""

    def __init__(self, color):
        super().__init__()
        self.color = color
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(30, 30)
        self.setToolTip("Цвет из темы" if color is None else color)
        self.hover_cb = None

    def enterEvent(self, e):
        if self.hover_cb:
            self.hover_cb({"accent": self.color or ""})

    def leaveEvent(self, e):
        if self.hover_cb:
            self.hover_cb(None)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(5, 5, -5, -5)
        if self.color is None:  # «по теме»: кружок с косой чертой
            p.setPen(QPen(QColor(P["DIS"]), 1.6))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(r)
            p.drawLine(QPointF(r.left() + 3, r.bottom() - 3), QPointF(r.right() - 3, r.top() + 3))
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(self.color))
            p.drawEllipse(r)
        if self.isChecked():
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(P["TEXT"]), 2))
            p.drawEllipse(QRectF(self.rect()).adjusted(2, 2, -2, -2))


class FontSizeSlider(QWidget):
    """Плавная непрерывная настройка размера шрифта (9–16 pt, шаг 0,5)."""
    changed = Signal(float)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(58)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(18, 32)  # половины пунктов: 9.0–16.0 pt
        self.slider.setPageStep(2)
        self.slider.setSingleStep(1)
        self.slider.setTracking(True)
        self.slider.setTickPosition(QSlider.NoTicks)
        self.slider.valueChanged.connect(self._on_value)
        lay.addWidget(self.slider)
        labels = QHBoxLayout()
        labels.setContentsMargins(0, 0, 0, 0)
        for text in ("Мелкий", "Обычный", "Крупный"):
            lab = QLabel(text)
            lab.setObjectName("muted")
            lab.setAlignment(Qt.AlignCenter)
            labels.addWidget(lab, 1)
        lay.addLayout(labels)

    def set_key(self, key):
        legacy = {"small": 9.0, "normal": 10.0, "large": 11.5}
        value = legacy.get(key, key)
        try:
            value = max(9.0, min(16.0, float(value)))
        except (TypeError, ValueError):
            value = 10.0
        self.slider.blockSignals(True)
        self.slider.setValue(round(value * 2))
        self.slider.blockSignals(False)

    def _on_value(self, value: int):
        self.changed.emit(value / 2.0)


class ScrollToTopArea(QScrollArea):
    """QScrollArea со всплывающей кнопкой возврата к началу."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.top_button = QPushButton("↑", self.viewport())
        self.top_button.setObjectName("accent")
        self.top_button.setToolTip("Наверх")
        self.top_button.setFixedSize(42, 42)
        self.top_button.setCursor(Qt.PointingHandCursor)
        self.top_button.hide()
        self.top_button.clicked.connect(lambda: self.verticalScrollBar().setValue(0))
        self.verticalScrollBar().valueChanged.connect(self._scroll_changed)

    def _scroll_changed(self, value):
        self.top_button.setVisible(value > 120)
        self._position_button()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_button()

    def _position_button(self):
        self.top_button.move(max(8, self.viewport().width() - 56),
                             max(8, self.viewport().height() - 56))
        self.top_button.raise_()


class CornerButton(QAbstractButton):
    """Кнопка выбора углов: рисует прямоугольник с нужным скруглением."""

    def __init__(self, key: str, title: str, radius: float):
        super().__init__()
        self.key = key
        self.title = title
        self.radius = radius
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self.setMinimumWidth(100)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        checked = self.isChecked()
        p.setPen(QPen(QColor(P["ACC1"] if checked else P["BORDER"]), 2 if checked else 1))
        p.setBrush(QColor(P["SEL"] if checked else P["BTN"]))
        p.drawRoundedRect(r, self.radius, self.radius)
        inner = r.adjusted(10, 10, -10, -10)
        p.setPen(QPen(QColor(P["BORDER"]), 1))
        p.setBrush(QColor(P["SURFACE"]))
        ir = max(2.0, self.radius * 0.55)
        p.drawRoundedRect(inner, ir, ir)
        p.setPen(QColor(P["TEXT"] if checked else P["MUTED"]))
        f = QFont(p.font())
        f.setPointSizeF(max(8.0, P.get("FS", 10) * 0.9))
        f.setBold(checked)
        p.setFont(f)
        p.drawText(r, Qt.AlignCenter, self.title)


class CornerPicker(QWidget):
    """Визуальный выбор углов: сразу видно, скруглённые или строгие."""
    changed = Signal(str)  # CORNER_KEYS value

    def __init__(self):
        super().__init__()
        self.setFixedHeight(56)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        self.buttons = []
        grp = QButtonGroup(self)
        for key, title, radius in (("soft", "Мягкие", 14), ("sharp", "Строгие", 4)):
            btn = CornerButton(key, title, radius)
            btn.clicked.connect(lambda _=False, k=key: self.changed.emit(k))
            grp.addButton(btn)
            self.buttons.append(btn)
            lay.addWidget(btn, 1)

    def set_key(self, key: str):
        for btn in self.buttons:
            btn.setChecked(btn.key == key)
            btn.update()


class ThemePreview(QWidget):
    """Мини-окно: сразу показывает, как выглядят тема, акцент, шрифт, углы и плотность.
    При наведении на образец темы или цвета показывает вариант до применения."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(176)
        self.setMinimumWidth(200)
        self.patch = None

    def set_patch(self, patch):
        self.patch = patch
        self.update()

    def paintEvent(self, _):
        pal = look.compute_palette({**core.CFG, **self.patch}, None, system_is_light()) if self.patch else P
        W, H = self.width(), self.height()
        gap, r1, r2 = pal["GAP"], pal["R1"], pal["R2"]
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(pal["BORDER"]), 1))
        p.setBrush(QColor(pal["BG"]))
        p.drawRoundedRect(QRectF(0.5, 0.5, W - 1, H - 1), r1, r1)
        # боковая панель вкладок
        nav = QRectF(10, 10, 34, H - 20)
        p.setBrush(QColor(pal["SURFACE"]))
        p.drawRoundedRect(nav, min(r1, 14), min(r1, 14))
        for i in range(4):
            c = QPointF(nav.center().x(), nav.top() + 22 + i * 32)
            if i == 0:
                sel = QColor(pal["ACC1"])
                sel.setAlpha(70)
                p.setPen(Qt.NoPen)
                p.setBrush(sel)
                p.drawRoundedRect(QRectF(nav.left() + 4, c.y() - 13, nav.width() - 8, 26), 8, 8)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(pal["ACC_FG"] if i == 0 else pal["MUTED"]))
            p.drawEllipse(c, 4, 4)
        # карточка
        card = QRectF(nav.right() + 8, 10, W - nav.right() - 18, H - 20)
        p.setPen(QPen(QColor(pal["BORDER"]), 1))
        p.setBrush(QColor(pal["SURFACE"]))
        p.drawRoundedRect(card, r1, r1)
        p.save()
        p.setClipRect(card.adjusted(1, 1, -1, -1))
        pad = 8 + gap // 2
        x, w = card.left() + pad, card.width() - 2 * pad
        y = card.top() + pad
        f = QFont(p.font())
        f.setPointSizeF(pal["FS"])
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(pal["TEXT"]))
        p.drawText(QRectF(x, y, w, 20), Qt.AlignLeft | Qt.AlignVCenter, "Zapret GUI")
        y += 20
        f.setBold(False)
        f.setPointSizeF(pal["FS"] * 0.85)
        p.setFont(f)
        p.setPen(QColor(pal["MUTED"]))
        p.drawText(QRectF(x, y, w, 16), Qt.AlignLeft | Qt.AlignVCenter, "Обход работает")
        y += 16 + gap // 2
        bh = 18 + pal["PAD"] * 1.4  # высота кнопок зависит от плотности
        bw = max(60.0, min(92.0, (w - 8) / 2))
        g = QLinearGradient(x, y, x + bw, y)
        g.setColorAt(0, QColor(pal["ACC1"]))
        g.setColorAt(1, QColor(pal["ACC2"]))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(QRectF(x, y, bw, bh), r2, r2)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(pal["ONACC"]))
        p.drawText(QRectF(x, y, bw, bh), Qt.AlignCenter, "Включить")
        p.setPen(QPen(QColor(pal["BORDER"]), 1))
        p.setBrush(QColor(pal["BTN"]))
        p.drawRoundedRect(QRectF(x + bw + 8, y, bw, bh), r2, r2)
        f.setBold(False)
        p.setFont(f)
        p.setPen(QColor(pal["TEXT"]))
        p.drawText(QRectF(x + bw + 8, y, bw, bh), Qt.AlignCenter, "Отмена")
        y += bh + gap // 2 + 2
        ok = QColor(pal["OK"])
        ok.setAlpha(45)
        p.setPen(Qt.NoPen)
        p.setBrush(ok)
        p.drawRoundedRect(QRectF(x, y, 78, 18), 9, 9)
        p.setPen(QColor(pal["OK"]))
        p.drawText(QRectF(x, y, 78, 18), Qt.AlignCenter, "Доступен")
        y += 18 + gap // 2 + 2
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(pal["OFF"]))
        p.drawRoundedRect(QRectF(x, y, w, 6), 3, 3)
        g2 = QLinearGradient(x, y, x + w, y)
        g2.setColorAt(0, QColor(pal["ACC1"]))
        g2.setColorAt(1, QColor(pal["ACC2"]))
        p.setBrush(g2)
        p.drawRoundedRect(QRectF(x, y, w * 0.65, 6), 3, 3)
        p.restore()


class PowerButton(QWidget):
    """Большая круглая кнопка включения: плавная смена состояния и «дыхание» свечения, пока обход работает."""
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(190, 190)
        self.on = False
        self.enabled_ = True
        self._level = 0.0   # 0 = выключено, 1 = включено (анимируется)
        self._pulse = 0.0
        self.setCursor(Qt.PointingHandCursor)
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(280)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.anim.valueChanged.connect(self._set_level)
        self.pulse = QVariantAnimation(self)
        self.pulse.setDuration(2400)
        self.pulse.setStartValue(0.0)
        self.pulse.setEndValue(1.0)
        self.pulse.setLoopCount(-1)
        self.pulse.valueChanged.connect(self._set_pulse)

    def _set_level(self, v):
        self._level = float(v)
        self.update()

    def _set_pulse(self, v):
        self._pulse = float(v)
        self.update()

    def set_state(self, on: bool, enabled: bool):
        changed = on != self.on
        self.on, self.enabled_ = on, enabled
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        if changed and not anim_on():
            self.anim.stop()
            self.pulse.stop()
            self._level, self._pulse = (1.0 if on else 0.0), 0.0
        elif changed:
            self.anim.stop()
            self.anim.setDuration(280)
            self.anim.setStartValue(self._level)
            self.anim.setEndValue(1.0 if on else 0.0)
            self.anim.start()
            if on and self.isVisible() and anim_on():
                self.pulse.start()
            elif not on:
                self.pulse.stop()
                self._pulse = 0.0
        self.update()

    def showEvent(self, e):
        if self.on and anim_on():
            self.pulse.start()

    def hideEvent(self, e):  # скрытое окно не должно тратить процессор на анимацию
        self.pulse.stop()

    def mouseReleaseEvent(self, e):
        if self.enabled_ and e.button() == Qt.LeftButton:
            self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(22, 22, -22, -22)
        c = r.center()
        lv = self._level
        wave = 0.5 - 0.5 * math.cos(2 * math.pi * self._pulse)
        p.setBrush(QColor(P["SURFACE"]))
        p.setPen(QPen(QColor(P["OFF"]), 3))
        p.drawEllipse(r)
        if lv > 0.001:
            p.setOpacity(lv)
            p.setPen(Qt.NoPen)
            for i, a in enumerate((34, 20, 10)):  # свечение, которое «дышит»
                glow = QColor(P["ACC1"])
                glow.setAlpha(a)
                p.setBrush(glow)
                g = 6 * (i + 1) + 5 * wave * (i + 1) / 2
                p.drawEllipse(r.adjusted(-g, -g, g, g))
            grad = QLinearGradient(r.topLeft(), r.bottomRight())
            grad.setColorAt(0, QColor(P["ACC1"]))
            grad.setColorAt(1, QColor(P["ACC2"]))
            p.setBrush(grad)
            p.drawEllipse(r)
            p.setOpacity(1.0)
        col = QColor(mix(P["MUTED"] if self.enabled_ else P["DIS"], P["ONACC"], lv))
        p.setPen(QPen(col, 7, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        rad = r.width() * 0.22
        p.drawArc(QRectF(c.x() - rad, c.y() - rad + 3, 2 * rad, 2 * rad), 130 * 16, 280 * 16)
        p.drawLine(QPointF(c.x(), c.y() - rad - 5), QPointF(c.x(), c.y() + 2))


class Bus(QObject):
    log = Signal(str)
    latest = Signal(str, str)
    changed = Signal()
    failed = Signal(str)
    site = Signal(int, str, dict)
    sites_done = Signal()
    auto_done = Signal(str)
    app_checked = Signal(list)
    app_ready = Signal(str)
    lists_done = Signal(int, bool)
    diag_done = Signal(list)
    favicon = Signal(str, object)       # url, bytes | None
    zapret_releases = Signal(list)      # list[dict] из core.list_zapret_releases


class CollapsibleSection(QFrame):
    """Карточка с независимым состоянием сворачивания и плавным раскрытием."""
    def __init__(self, title: str, key: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setObjectName("card")
        self._anim = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(P["MARG"], P["MARG"] - 2, P["MARG"], P["MARG"] - 2)
        outer.setSpacing(P["GAP"] - 2)
        self.header = QPushButton(title)
        self.header.setObjectName("sectionHeader")
        self.header.setCheckable(True)
        outer.addWidget(self.header)
        self.body = QFrame()
        self.body.setObjectName("sectionBody")
        self.content_layout = QVBoxLayout(self.body)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(P["GAP"] - 2)
        outer.addWidget(self.body)
        collapsed = bool(core.CFG.get("collapsed_sections", {}).get(key, False))
        self.header.setChecked(not collapsed)
        self.body.setVisible(not collapsed)
        self._update_caption(not collapsed)
        self.header.toggled.connect(self.set_expanded)

    def _update_caption(self, expanded: bool):
        self.header.setText(("▾  " if expanded else "▸  ") + self._title())

    def _title(self):
        return self.header.property("sectionTitle") or self.header.text().lstrip("▾▸ ")

    def set_expanded(self, expanded: bool):
        title = self._title()
        self.header.setProperty("sectionTitle", title)
        self._update_caption(expanded)
        states = dict(core.CFG.get("collapsed_sections", {}))
        states[self.key] = not expanded
        core.CFG["collapsed_sections"] = states
        core.save()
        if self._anim is not None:
            self._anim.stop()
        if not anim_on() or core.CFG.get("animation_style") == "subtle":
            self.body.setVisible(expanded)
            self.body.setMaximumHeight(16777215)
            return
        if expanded:
            self.body.setVisible(True)
            self.body.setMaximumHeight(0)
            end = max(1, self.body.sizeHint().height())
            start = 0
        else:
            start = max(1, self.body.height())
            end = 0
        duration = 140 if core.CFG.get("animation_style") == "quick" else 220
        self._anim = QPropertyAnimation(self.body, b"maximumHeight", self)
        self._anim.setDuration(duration)
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        if not expanded:
            self._anim.finished.connect(lambda: self.body.setVisible(False))
        else:
            self._anim.finished.connect(lambda: self.body.setMaximumHeight(16777215))
        self._anim.start()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.compact = None  # None = раскладка ещё не собрана
        self.setWindowTitle(f"Zapret GUI {core.VERSION}")
        self.setWindowIcon(app_icon())
        self.resize(520, 720)
        self.setMinimumSize(380, 560)
        self.latest = ("", "")
        self._force = False
        self.path_rows = []
        self.busy_buttons = []
        self.busy = False
        self._bat_tried = False
        self._first_err = ""
        self._cur_profile = ""
        self.log_history = []
        self.app_rels = []
        self.app_buttons = []
        self._app_manual = False
        self._app_busy = False
        self.running = False
        self._run_since = None
        self._page_anim = None
        self._fade = None
        self.swatches = []
        self.section_widgets = {}
        self.site_rows = {}
        self.site_results = {}
        self.sites_checked_at = ""
        self.bus = Bus()
        self.bus.log.connect(self.on_log)
        self.bus.latest.connect(self.on_latest)
        self.bus.changed.connect(self.on_changed)
        self.bus.failed.connect(self.on_failed)
        self.bus.site.connect(self.on_site_result)
        self.bus.sites_done.connect(lambda: self.sites_btn.setEnabled(True))
        self.bus.auto_done.connect(self.on_auto_done)
        self.bus.app_checked.connect(self.on_app_checked)
        self.bus.app_ready.connect(self.on_app_ready)
        self.bus.lists_done.connect(self.on_lists_done)
        self.bus.diag_done.connect(self.on_diag_done)
        self.bus.favicon.connect(self.on_favicon)
        self.bus.zapret_releases.connect(self.on_zapret_releases)
        self._favicon_cache = {}
        self.zapret_rels = []

        root = QWidget()
        root.setObjectName("page")
        self.setCentralWidget(root)
        self.root_lay = QBoxLayout(QBoxLayout.LeftToRight, root)
        self.root_lay.setContentsMargins(0, 0, 0, 0)
        self.root_lay.setSpacing(0)

        self.stack = QStackedWidget()
        self.content = QWidget()
        self.content.setObjectName("page")
        self.content_lay = QHBoxLayout(self.content)
        self.content_lay.setContentsMargins(0, 0, 0, 0)
        self.content_lay.setSpacing(0)
        # боковые растяжки: в узком окне центрируют, в широком почти исчезают
        self._side_l = QWidget()
        self._side_r = QWidget()
        self._side_l.setMinimumWidth(0)
        self._side_r.setMinimumWidth(0)
        self.content_lay.addWidget(self._side_l, 1)
        self.content_lay.addWidget(self.stack, 20)
        self.content_lay.addWidget(self._side_r, 1)

        self.nav = QWidget()
        self.nav.setObjectName("nav")
        self.nav.setAttribute(Qt.WA_StyledBackground, True)
        self.nav_outer = QBoxLayout(QBoxLayout.LeftToRight, self.nav)
        self.navpanel = QFrame()  # скруглённая «парящая» панель с тенью
        self.navpanel.setObjectName("navpanel")
        self.nav_outer.addWidget(self.navpanel)
        self.nav_lay = QBoxLayout(QBoxLayout.LeftToRight, self.navpanel)
        self.nav_shadow = QGraphicsDropShadowEffect(self.navpanel)
        self.nav_shadow.setBlurRadius(30)
        self.nav_shadow.setOffset(0, 4)
        self.navpanel.setGraphicsEffect(self.nav_shadow)
        self.nav_buttons = []
        group = QButtonGroup(self)
        for i, (kind, tip, builder) in enumerate([
            ("power", "Главная", self.build_home), ("globe", "Сайты", self.build_sites),
            ("list", "Списки", self.build_lists), ("layers", "Профили", self.build_profiles),
            ("more", "Настройки", self.build_more),
        ]):
            b = NavButton(kind, tip)
            group.addButton(b, i)
            self.nav_buttons.append(b)
            self.stack.addWidget(builder())
        group.idClicked.connect(self.switch_page)
        self.nav_buttons[0].setChecked(True)
        self.apply_layout(self.width() < COMPACT_WIDTH)

        self.build_tray()
        self.reload_all()
        try:  # тема «Как в системе» следует за переключением в Windows
            QApplication.styleHints().colorSchemeChanged.connect(
                lambda *_: self.apply_theme("auto") if core.CFG["theme"] == "auto" else None)
        except Exception:
            pass
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(2500)
        self.ticker = QTimer(self)  # раз в секунду обновляет время работы
        self.ticker.timeout.connect(self.tick)
        self.ticker.start(1000)
        self.check_updates()
        QTimer.singleShot(4000, self.check_app_updates)
        QTimer.singleShot(1200, self.maybe_show_whats_new)
        if core.is_installed() and core.lists_due():  # списки подтягиваем в фоне раз в 12 часов
            QTimer.singleShot(2500, lambda: self.update_lists_now(manual=False))
        if core.CFG.get("resume_after_update"):  # только что обновились: возвращаем обход, если он был включён
            core.CFG["resume_after_update"] = False
            core.save()
            if core.is_installed():
                QTimer.singleShot(800, self.restart)
        if core.CFG["auto_start_bypass"] and core.is_installed() and not core.is_running():
            QTimer.singleShot(500, self.toggle)

    # ---------- страницы ----------
    def build_home(self):
        w, v = page()
        # мини-баннер: версия и предложение обновиться / что нового
        self.home_banner = QFrame()
        self.home_banner.setObjectName("card")
        self.home_banner.setVisible(False)
        bl = QVBoxLayout(self.home_banner)
        bl.setContentsMargins(14, 12, 14, 12)
        bl.setSpacing(8)
        self.home_banner_title = QLabel("")
        self.home_banner_title.setStyleSheet("font-weight: 700;")
        self.home_banner_body = QLabel("")
        self.home_banner_body.setObjectName("muted")
        self.home_banner_body.setWordWrap(True)
        bl.addWidget(self.home_banner_title)
        bl.addWidget(self.home_banner_body)
        brow = QHBoxLayout()
        self.home_banner_update = QPushButton("Обновить")
        self.home_banner_update.setObjectName("accent")
        self.home_banner_update.clicked.connect(self.on_home_banner_update)
        self.home_banner_later = QPushButton("Закрыть")
        self.home_banner_later.clicked.connect(self.on_home_banner_later)
        brow.addWidget(self.home_banner_update)
        brow.addWidget(self.home_banner_later)
        brow.addStretch(1)
        bl.addLayout(brow)
        v.addWidget(self.home_banner)
        self.home_ver = QLabel(f"Zapret GUI {core.VERSION}")
        self.home_ver.setObjectName("muted")
        self.home_ver.setAlignment(Qt.AlignHCenter)
        v.addWidget(self.home_ver)
        v.addStretch(2)
        self.power = PowerButton()
        self.power.clicked.connect(self.toggle)
        v.addWidget(self.power, alignment=Qt.AlignHCenter)
        v.addSpacing(8)
        self.status = QLabel("Выключено")
        self.status.setObjectName("status")
        v.addWidget(self.status, alignment=Qt.AlignHCenter)
        self.sub = QLabel("")
        self.sub.setObjectName("muted")
        self.sub.setWordWrap(True)
        self.sub.setAlignment(Qt.AlignHCenter)
        v.addWidget(self.sub)
        self.busybar = BusyBar()
        v.addWidget(self.busybar, alignment=Qt.AlignHCenter)
        v.addSpacing(10)
        self.combo = QComboBox()
        self.combo.setMinimumWidth(280)
        self.combo.currentTextChanged.connect(self.on_strategy_changed)
        v.addWidget(self.combo, alignment=Qt.AlignHCenter)
        self.auto_btn = QPushButton("Подобрать стратегию автоматически")
        self.auto_btn.clicked.connect(self.auto_pick)
        self.busy_buttons.append(self.auto_btn)
        v.addWidget(self.auto_btn, alignment=Qt.AlignHCenter)
        hint = QLabel("Не открывается сайт? Программа сама найдёт рабочую стратегию.")
        hint.setObjectName("muted")
        v.addWidget(hint, alignment=Qt.AlignHCenter)
        v.addStretch(3)
        self.log_line = QLabel("")
        self.log_line.setObjectName("muted")
        self.log_line.setWordWrap(True)
        self.log_line.setAlignment(Qt.AlignHCenter)
        self.log_fx = QGraphicsOpacityEffect(self.log_line)
        self.log_line.setGraphicsEffect(self.log_fx)
        self.log_anim = QPropertyAnimation(self.log_fx, b"opacity", self)
        v.addWidget(self.log_line)
        bar, bl = card()  # нижняя панель с кнопкой перезапуска
        self.restart_btn = QPushButton("Перезапустить")
        self.restart_btn.setIcon(make_icon("restart", P["TEXT"]))
        self.restart_btn.setIconSize(QSize(22, 22))
        self.restart_btn.setMinimumHeight(44)
        self.restart_btn.setCursor(Qt.PointingHandCursor)
        self.restart_btn.setToolTip("Перезапустить сервис с текущей стратегией и профилями")
        self.restart_btn.clicked.connect(self.restart_service)
        bl.addWidget(self.restart_btn)
        v.addWidget(bar)
        return w

    def build_sites(self):
        w, v = page("Сайты")
        c, cl = card()
        top = QHBoxLayout()
        tv = QVBoxLayout()
        tv.setSpacing(2)
        self.sites_title = QLabel("Проверка доступности")
        self.sites_title.setStyleSheet("font-size: 14pt; font-weight: 700;")
        self.sites_sub = QLabel("")
        self.sites_sub.setObjectName("muted")
        self.sites_sub.setWordWrap(True)
        tv.addWidget(self.sites_title)
        tv.addWidget(self.sites_sub)
        top.addLayout(tv, 1)
        self.sites_btn = QPushButton("Проверить все")
        self.sites_btn.setObjectName("accent")
        self.sites_btn.clicked.connect(self.check_all)
        top.addWidget(self.sites_btn, alignment=Qt.AlignTop)
        cl.addLayout(top)
        self.ratio_bar = RatioBar()
        cl.addWidget(self.ratio_bar)
        v.addWidget(c)

        row = QHBoxLayout()
        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("Добавить сайт: example.com")
        self.site_input.returnPressed.connect(self.add_site)
        add = QPushButton("Добавить")
        add.clicked.connect(self.add_site)
        row.addWidget(self.site_input, 1)
        row.addWidget(add)
        v.addLayout(row)

        self.chips_cap = QLabel("БЫСТРО ДОБАВИТЬ")
        self.chips_cap.setObjectName("caption")
        v.addWidget(self.chips_cap)
        self.chips_box = QWidget()
        self.chips_lay = QGridLayout(self.chips_box)
        self.chips_lay.setContentsMargins(0, 0, 0, 0)
        self.chips_lay.setSpacing(8)
        for col in range(3):
            self.chips_lay.setColumnStretch(col, 1)
        v.addWidget(self.chips_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        body = QWidget()
        body.setObjectName("scrollbody")
        self.sites_lay = QVBoxLayout(body)
        self.sites_lay.setContentsMargins(0, 0, 4, 0)
        self.sites_lay.setSpacing(8)
        scroll.setWidget(body)
        v.addWidget(scroll, 1)
        self.rebuild_sites()
        return w

    def build_lists(self):
        w, v = page("Списки")
        self.list_combo = QComboBox()
        self.list_combo.addItems(core.EDITABLE_LISTS)
        self.list_combo.currentTextChanged.connect(self.load_list)
        v.addWidget(self.list_combo)
        hint = QLabel("По одному домену или IP на строку. ipset-all.txt обновляется вместе с релизом, "
                      "остальные файлы при обновлении сохраняются. Домены включённых профилей программа "
                      "дописывает в конец list-general-user.txt между строками # profiles.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        v.addWidget(hint)
        self.editor = QPlainTextEdit()
        v.addWidget(self.editor, 1)
        row = QHBoxLayout()
        b = QPushButton("Сохранить и применить")
        b.setObjectName("accent")
        b.clicked.connect(self.save_list)
        self.lists_btn = QPushButton("Обновить списки с GitHub")
        self.lists_btn.setToolTip("Скачать актуальные списки из официального репозитория Flowseal/zapret-discord-youtube")
        self.lists_btn.clicked.connect(lambda: self.update_lists_now(manual=True))
        row.addWidget(b, 1)
        row.addWidget(self.lists_btn, 1)
        v.addLayout(row)
        self.lists_info = QLabel("")
        self.lists_info.setObjectName("muted")
        self.lists_info.setWordWrap(True)
        v.addWidget(self.lists_info)
        self.refresh_lists_info()
        return w

    def build_profiles(self):
        w, v = page("Профили")
        hint = QLabel("Профили — отдельные наборы доменов для обхода. Включай нужные наборы галочкой; изменения применяются автоматически.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        v.addWidget(hint)
        self.profile_search = QLineEdit()
        self.profile_search.setPlaceholderText("Поиск профиля…")
        self.profile_search.textChanged.connect(self.filter_profiles)
        v.addWidget(self.profile_search)
        self.profile_summary = QLabel("Профили")
        self.profile_summary.setObjectName("caption")
        v.addWidget(self.profile_summary)
        self.prof_list = QListWidget()
        self.prof_list.setMinimumHeight(125)
        self.prof_list.setMaximumHeight(210)
        self.prof_list.currentItemChanged.connect(self.on_profile_selected)
        self.prof_list.itemChanged.connect(self.on_profile_toggled)
        v.addWidget(self.prof_list)
        editor_head = QHBoxLayout()
        lab = QLabel("Домены выбранного профиля")
        lab.setObjectName("cardTitle")
        editor_head.addWidget(lab)
        editor_head.addStretch()
        self.profile_count = QLabel("0 строк")
        self.profile_count.setObjectName("muted")
        editor_head.addWidget(self.profile_count)
        v.addLayout(editor_head)
        self.prof_editor = QPlainTextEdit()
        self.prof_editor.setPlaceholderText("Один домен на строку, например: example.com")
        self.prof_editor.textChanged.connect(self.update_profile_count)
        v.addWidget(self.prof_editor, 1)
        row = QHBoxLayout()
        b_new = QPushButton("Новый")
        b_new.clicked.connect(self.new_profile)
        b_save = QPushButton("Сохранить")
        b_save.setObjectName("accent")
        b_save.clicked.connect(self.save_profile)
        b_del = QPushButton("Удалить")
        b_del.clicked.connect(self.delete_profile)
        b_imp = QPushButton("Импорт…")
        b_imp.clicked.connect(self.import_profile)
        b_exp = QPushButton("Экспорт…")
        b_exp.clicked.connect(self.export_profile)
        for b in (b_new, b_save, b_del, b_imp, b_exp):
            row.addWidget(b)
        v.addLayout(row)
        self.update_profile_count()
        return w

    def section_card(self, key: str, title: str):
        section = CollapsibleSection(title, key, self)
        self.section_widgets[key] = section
        return section, section.content_layout

    def build_more(self):
        scroll = ScrollToTopArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        body = QWidget()
        body.setObjectName("scrollbody")
        body.setProperty("pagebody", True)
        v = QVBoxLayout(body)
        v.setContentsMargins(24, 10, 24, 20)
        v.setSpacing(P["GAP"])
        scroll.setWidget(body)
        head = QLabel("Настройки")
        head.setObjectName("h1")
        v.addWidget(head)

        c, cl = self.section_card("about", "О приложении")
        t = QLabel("Zapret GUI")
        t.setStyleSheet("font-size: 18pt; font-weight: 700; letter-spacing: -0.3px;")
        cl.addWidget(t)
        ver = QLabel(f"Версия {core.VERSION}")
        ver.setObjectName("muted")
        cl.addWidget(ver)
        repo = core.app_repo()
        self.about_link = None
        if repo:
            self.about_link = QLabel(f'<a href="https://github.com/{repo}" style="text-decoration:none;">github.com/{repo}</a>')
            self.about_link.setOpenExternalLinks(True)
            self.about_link.setStyleSheet(f"padding-top: 2px; color: {P['ACC1']};")
            cl.addWidget(self.about_link)
        v.addWidget(c)

        c, cl = self.section_card("appearance", "Оформление")

        def caption(text):
            lab = QLabel(text)
            lab.setObjectName("caption")
            cl.addWidget(lab)

        self.preview = ThemePreview()  # мини-окно: показывает результат сразу
        cl.addWidget(self.preview)

        caption("ТЕМА")
        row = QHBoxLayout()
        row.setSpacing(6)
        grp = QButtonGroup(self)
        cur = LEGACY_THEMES.get(core.CFG["theme"], core.CFG["theme"])
        self.swatches = []
        for key in THEME_KEYS:
            sw = ThemeSwatch(key)
            sw.setChecked(key == cur)
            sw.clicked.connect(lambda _=False, k=key: self.on_theme_pick(k))
            sw.hover_cb = self.preview.set_patch
            grp.addButton(sw)
            self.swatches.append(sw)
            row.addWidget(sw)
        row.addStretch(1)
        cl.addLayout(row)
        self.theme_name = QLabel("")
        self.theme_name.setObjectName("muted")
        cl.addWidget(self.theme_name)

        caption("ЦВЕТ АКЦЕНТА")
        agrid = QGridLayout()
        agrid.setHorizontalSpacing(4)
        agrid.setVerticalSpacing(4)
        self.accent_dots = []
        agrp = QButtonGroup(self)
        for i, col in enumerate([None] + ACCENT_PRESETS):
            d = ColorDot(col)
            d.clicked.connect(lambda _=False, c_=col: self.set_look("accent", c_ or ""))
            d.hover_cb = self.preview.set_patch
            agrp.addButton(d)
            self.accent_dots.append(d)
            agrid.addWidget(d, i // 8, i % 8)  # сетка 8 колонок: умещается и в узком окне
        b_acc = QPushButton("…")
        b_acc.setToolTip("Выбрать любой цвет")
        b_acc.setFixedSize(30, 30)
        b_acc.setStyleSheet("padding: 0; border-radius: 15px;")
        b_acc.clicked.connect(self.pick_accent)
        agrid.addWidget(b_acc, (len(self.accent_dots)) // 8, (len(self.accent_dots)) % 8)
        cl.addLayout(agrid)

        caption("ШРИФТ")
        self.font_slider = FontSizeSlider()
        self.font_slider.set_key(core.CFG.get("font_size", "normal"))
        self.font_slider.changed.connect(lambda value: self.set_look("font_size", value))
        cl.addWidget(self.font_slider)

        caption("УГЛЫ")
        self.corner_picker = CornerPicker()
        self.corner_picker.set_key(core.CFG.get("corners", "soft"))
        self.corner_picker.changed.connect(lambda k: self.set_look("corners", k))
        cl.addWidget(self.corner_picker)

        self.anim_cb = QCheckBox("Анимации интерфейса")
        self.anim_cb.setChecked(core.CFG["animations"])
        self.anim_cb.toggled.connect(self.on_anim_toggled)
        cl.addWidget(self.anim_cb)

        caption("СТИЛЬ АНИМАЦИИ")
        self.animation_style_combo = QComboBox()
        self.animation_style_combo.addItems(["Плавная", "Быстрая", "Ненавязчивая"])
        self.animation_style_combo.setCurrentIndex(
            {"smooth": 0, "quick": 1, "subtle": 2}.get(core.CFG.get("animation_style", "smooth"), 0))
        self.animation_style_combo.currentIndexChanged.connect(self.on_animation_style_changed)
        cl.addWidget(self.animation_style_combo)

        b_def = QPushButton("Сбросить оформление")
        b_def.clicked.connect(self.reset_look)
        cl.addWidget(b_def)
        self.sync_look_controls()
        v.addWidget(c)

        c, cl = self.section_card("zapret", "zapret")
        self.up_installed, self.up_latest = QLabel(), QLabel()
        for k, lab in (("Установлена", self.up_installed), ("Последний релиз", self.up_latest)):
            r = QHBoxLayout()
            r.addWidget(QLabel(k))
            r.addStretch()
            r.addWidget(lab)
            cl.addLayout(r)
        src = QLabel(f"Источник: {core.REPO_URL}")
        src.setObjectName("muted")
        src.setWordWrap(True)
        cl.addWidget(src)
        r = QHBoxLayout()
        self.btn_check = QPushButton("Проверить")
        self.btn_check.clicked.connect(lambda: self.check_updates(force=False))
        self.btn_install = QPushButton("Скачать и установить")
        self.btn_install.setObjectName("accent")
        self.btn_install.clicked.connect(self.install_latest)
        r.addWidget(self.btn_check)
        r.addWidget(self.btn_install)
        cl.addLayout(r)
        lab = QLabel("Другие версии zapret")
        lab.setObjectName("cardTitle")
        cl.addWidget(lab)
        hint = QLabel("Можно поставить не только последний релиз, а любую из списка (например, откат на 1.10.x).")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        cl.addWidget(hint)
        self.zapret_combo = QComboBox()
        self.zapret_combo.setEnabled(False)
        cl.addWidget(self.zapret_combo)
        r = QHBoxLayout()
        self.btn_zapret_list = QPushButton("Загрузить список")
        self.btn_zapret_list.clicked.connect(self.load_zapret_releases)
        self.btn_zapret_install = QPushButton("Установить выбранную")
        self.btn_zapret_install.clicked.connect(self.install_selected_zapret)
        r.addWidget(self.btn_zapret_list)
        r.addWidget(self.btn_zapret_install, 1)
        cl.addLayout(r)
        self.busy_buttons += [self.btn_check, self.btn_install, self.btn_zapret_list, self.btn_zapret_install]
        v.addWidget(c)

        management_card, management_layout = self.section_card("management", "Приложение, папки, версии и журнал")
        cl = management_layout
        sub = QLabel("ПРИЛОЖЕНИЕ")
        sub.setObjectName("cardTitle")
        cl.addWidget(sub)
        r = QHBoxLayout()
        r.addWidget(QLabel("Установленная версия"))
        r.addStretch()
        r.addWidget(QLabel(core.VERSION))
        cl.addLayout(r)
        r = QHBoxLayout()
        r.addWidget(QLabel("Последняя на GitHub"))
        r.addStretch()
        self.app_latest_lbl = QLabel("—")
        r.addWidget(self.app_latest_lbl)
        cl.addLayout(r)
        self.app_repo_edit = QLineEdit(core.app_repo())
        self.app_repo_edit.setPlaceholderText("Репозиторий GitHub: владелец/репозиторий")
        self.app_repo_edit.editingFinished.connect(self.save_app_repo)
        cl.addWidget(self.app_repo_edit)
        r = QHBoxLayout()
        self.app_check_btn = QPushButton("Проверить")
        self.app_check_btn.clicked.connect(lambda: self.check_app_updates(manual=True))
        self.app_update_btn = QPushButton("Обновить приложение")
        self.app_update_btn.setObjectName("accent")
        self.app_update_btn.setEnabled(False)
        self.app_update_btn.clicked.connect(lambda: self.install_app(self.app_rels[0] if self.app_rels else None))
        r.addWidget(self.app_check_btn)
        r.addWidget(self.app_update_btn, 1)
        cl.addLayout(r)
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Стабильные версии", "Пререлизы (бета)"])
        self.channel_combo.setCurrentIndex(1 if core.CFG["app_channel"] == "pre" else 0)
        self.channel_combo.currentIndexChanged.connect(self.on_channel_changed)
        cl.addWidget(self.channel_combo)
        self.app_combo = QComboBox()
        cl.addWidget(self.app_combo)
        b_sel = QPushButton("Установить выбранную версию")
        b_sel.clicked.connect(lambda: self.install_app(self.app_combo.currentData()))
        cl.addWidget(b_sel)
        lab = QLabel("Предыдущие версии (бэкапы)")
        lab.setObjectName("cardTitle")
        cl.addWidget(lab)
        self.app_backup_list = QListWidget()
        self.app_backup_list.setMaximumHeight(90)
        cl.addWidget(self.app_backup_list)
        b_roll = QPushButton("Откатиться на выбранную")
        b_roll.clicked.connect(self.rollback_app)
        cl.addWidget(b_roll)
        self.app_auto_cb = QCheckBox("Обновлять приложение автоматически")
        self.app_auto_cb.setChecked(core.CFG["app_auto_update"])
        self.app_auto_cb.toggled.connect(lambda on: (core.CFG.update(app_auto_update=on), core.save()))
        cl.addWidget(self.app_auto_cb)
        self.app_buttons = [self.app_check_btn, self.app_update_btn, b_sel, b_roll]

        cl = management_layout
        sub = QLabel("ПАПКИ И ВЕРСИИ")
        sub.setObjectName("cardTitle")
        cl.addWidget(sub)
        for title, getter in [("Рабочая версия", core.release_dir),
                              ("Бэкапы старых версий", core.backup_dir),
                              ("Скачанные архивы", core.downloads_dir),
                              ("Профили (наборы доменов)", core.profiles_dir)]:
            r = path_row(title, getter)
            self.path_rows.append(r)
            cl.addLayout(r)
        b = QPushButton("Изменить папку данных…")
        b.clicked.connect(self.change_base)
        cl.addWidget(b)

        cl = management_layout
        sub = QLabel("УПРАВЛЕНИЕ ВЕРСИЯМИ И БЭКАПЫ")
        sub.setObjectName("cardTitle")
        cl.addWidget(sub)
        self.backup_list = QListWidget()
        self.backup_list.setMaximumHeight(96)
        cl.addWidget(self.backup_list)
        b1 = QPushButton("Восстановить выбранный бэкап")
        b1.clicked.connect(self.restore_backup)
        b2 = QPushButton("Указать свою папку zapret…")
        b2.clicked.connect(self.import_folder)
        b3 = QPushButton("Импорт из ZIP…")
        b3.clicked.connect(self.import_zip)
        for b in (b1, b2, b3):
            cl.addWidget(b)
            self.busy_buttons.append(b)
        cl = management_layout
        sub = QLabel("ЖУРНАЛ")
        sub.setObjectName("cardTitle")
        cl.addWidget(sub)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(130)
        self.log_view.setPlainText("\n".join(self.log_history))
        cl.addWidget(self.log_view)
        r = QHBoxLayout()
        b1 = QPushButton("Копировать")
        b1.clicked.connect(self.copy_log)
        b2 = QPushButton("Открыть winws.log")
        b2.clicked.connect(self.open_winws_log)
        r.addWidget(b1)
        r.addWidget(b2)
        cl.addLayout(r)

        v.addWidget(management_card)

        c, cl = self.section_card("diagnostics", "Диагностика")
        self.diag_view = QPlainTextEdit()
        self.diag_view.setReadOnly(True)
        self.diag_view.setMinimumHeight(150)
        self.diag_view.setPlaceholderText("Нажми «Проверить систему»: права, файлы zapret, WinDivert (отдельно), списки, доступ к GitHub, блокировка антивирусом.")
        cl.addWidget(self.diag_view)
        self.diag_btn = QPushButton("Проверить систему")
        self.diag_btn.clicked.connect(self.run_diagnostics)
        cl.addWidget(self.diag_btn)
        auto_l = QCheckBox("Обновлять списки автоматически (раз в 12 часов)")
        auto_l.setChecked(core.CFG["lists_auto_update"])
        auto_l.toggled.connect(lambda on: (core.CFG.update(lists_auto_update=on), core.save()))
        cl.addWidget(auto_l)
        v.addWidget(c)

        c, cl = self.section_card("behavior", "Поведение")
        self.opts = {}
        for key, text in [
            ("auto_update", "Обновлять zapret автоматически"),
            ("auto_start_bypass", "Включать обход при запуске программы"),
            ("close_to_tray", "Крестик сворачивает в трей"),
            ("stop_on_exit", "Выключать обход при выходе из программы"),
            ("game_filter", "Игровой фильтр (порты выше 1023)"),
            ("sites_auto", "Проверять сайты после включения обхода"),
        ]:
            cb = QCheckBox(text)
            cb.setChecked(bool(core.CFG[key]))
            cb.toggled.connect(lambda on, k=key: self.set_opt(k, on))
            cl.addWidget(cb)
            self.opts[key] = cb
        self.autostart_cb = QCheckBox("Запускать вместе с Windows (в трее)")
        self.autostart_cb.setChecked(core.CFG["autostart"])
        self.autostart_cb.clicked.connect(self.toggle_autostart)
        cl.addWidget(self.autostart_cb)
        pref_title = QLabel("СВОРАЧИВАЕМЫЕ РАЗДЕЛЫ")
        pref_title.setObjectName("caption")
        cl.addWidget(pref_title)
        cl.addWidget(QLabel("Выбери, какие блоки настроек будут свёрнуты при следующем открытии."))
        self.collapse_options = {}
        section_names = [("about", "О приложении"), ("appearance", "Оформление"),
                         ("zapret", "zapret"), ("management", "Приложение, папки, версии и журнал"),
                         ("diagnostics", "Диагностика"), ("behavior", "Поведение")]
        collapsed_cfg = core.CFG.get("collapsed_sections", {})
        for skey, label in section_names:
            cb = QCheckBox("Сворачивать: " + label)
            cb.setChecked(bool(collapsed_cfg.get(skey, False)))
            cb.toggled.connect(lambda on, k=skey: self.set_section_default(k, on))
            cl.addWidget(cb)
            self.collapse_options[skey] = cb
        v.addWidget(c)
        v.addStretch()
        return scroll

    def build_tray(self):
        self.tray = QSystemTrayIcon(status_icon(False), self)
        self.tray.setToolTip("Zapret GUI")
        menu = QMenu()
        # Индикатор статуса (некликабельный)
        self.tray_status = QAction("● Выключено", self)
        self.tray_status.setEnabled(False)
        menu.addAction(self.tray_status)
        menu.addSeparator()
        menu.addAction(QAction("Открыть", self, triggered=self.show_window))
        self.tray_toggle = QAction("Включить", self, triggered=self.toggle)
        menu.addAction(self.tray_toggle)
        menu.addAction(QAction("Перезапустить", self, triggered=self.restart))
        menu.addSeparator()
        menu.addAction(QAction("Подобрать стратегию", self, triggered=self.auto_pick))
        menu.addAction(QAction("Проверить систему", self, triggered=self.run_diagnostics_from_tray))
        menu.addSeparator()
        menu.addAction(QAction("Выход", self, triggered=self.quit_app))
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()

    # ---------- адаптивная раскладка и тема ----------
    def resizeEvent(self, e):
        super().resizeEvent(e)
        if getattr(self, "compact", None) is None:  # окно ещё собирается
            return
        compact = self.width() < COMPACT_WIDTH
        if compact != self.compact:
            self.apply_layout(compact)

    def apply_layout(self, compact: bool):
        """Узкое окно: панель вкладок снизу. Широкое: колонка слева, контент растягивается."""
        self.compact = compact
        lay, nl = self.root_lay, self.nav_lay
        lay.removeWidget(self.nav)
        lay.removeWidget(self.content)
        while nl.count():
            nl.takeAt(0)
        for b in self.nav_buttons:
            b.vertical = not compact
            b.update()
        if compact:
            # телефонный вид: контент по центру, ограничение ширины
            self.stack.setMaximumWidth(560)
            self.content_lay.setStretch(0, 1)
            self.content_lay.setStretch(1, 0)
            self.content_lay.setStretch(2, 1)
            lay.setDirection(QBoxLayout.TopToBottom)
            lay.addWidget(self.content, 1)
            lay.addWidget(self.nav)
            self.nav_outer.setContentsMargins(16, 2, 16, 12)
            nl.setDirection(QBoxLayout.LeftToRight)
            nl.setContentsMargins(10, 6, 10, 6)
            nl.setSpacing(0)
            for b in self.nav_buttons:
                nl.addStretch(1)
                nl.addWidget(b)
            nl.addStretch(1)
            self.nav.setMinimumSize(0, 82)
            self.nav.setMaximumSize(16777215, 82)
        else:
            # широкий / полный экран: контент занимает почти всю ширину
            self.stack.setMaximumWidth(16777215)
            self.content_lay.setStretch(0, 1)
            self.content_lay.setStretch(1, 40)
            self.content_lay.setStretch(2, 1)
            lay.setDirection(QBoxLayout.LeftToRight)
            lay.addWidget(self.nav)
            lay.addWidget(self.content, 1)
            self.nav_outer.setContentsMargins(14, 16, 2, 16)
            nl.setDirection(QBoxLayout.TopToBottom)
            nl.setContentsMargins(8, 12, 8, 12)
            nl.setSpacing(8)
            for b in self.nav_buttons:
                nl.addWidget(b, alignment=Qt.AlignHCenter)
            nl.addStretch(1)
            self.nav.setMinimumSize(90, 0)
            self.nav.setMaximumSize(90, 16777215)
        self.style_nav()

    def style_nav(self):
        dark = QColor(P["BG"]).lightness() < 128
        self.nav_shadow.setColor(QColor(0, 0, 0, 130 if dark else 50))
        self.nav.setStyleSheet(
            "QWidget#nav { background: transparent; } "
            f"QFrame#navpanel {{ background: {P['SURFACE']}; border: 1px solid {P['BORDER']}; border-radius: 24px; }}")

    def apply_theme(self, name: str):
        set_palette(name)
        QApplication.instance().setStyleSheet(build_style())
        self.style_nav()
        self.power.update()
        self.restart_btn.setIcon(make_icon("restart", P["TEXT"]))
        for b in self.nav_buttons + self.swatches:
            b.update()
        if getattr(self, "corner_picker", None):
            for b in self.corner_picker.buttons:
                b.update()
        if getattr(self, "about_link", None):
            self.about_link.setStyleSheet(f"padding-top: 2px; color: {P['ACC1']};")
        self.rebuild_sites()
        self.apply_density()
        self.preview.update()
        self.refresh_status()

    def apply_density(self):
        """Меняет отступы уже созданных карточек и страниц под выбранную плотность."""
        gap, marg = P["GAP"], P["MARG"]
        for w in self.findChildren(QWidget):
            lay = w.layout()
            if lay is None:
                continue
            if w.property("dens"):
                lay.setContentsMargins(marg, marg - 2, marg, marg - 2)
                lay.setSpacing(gap - 2)
            elif w.property("pagebody"):
                lay.setSpacing(gap)

    def on_theme_pick(self, key: str):
        core.CFG["theme"] = key
        core.save()
        self.apply_theme(key)
        self.sync_look_controls()

    def set_look(self, key: str, value: str):
        core.CFG[key] = value
        core.save()
        self.apply_theme(core.CFG["theme"])
        self.sync_look_controls()

    def sync_look_controls(self):
        """Отмечает в настройках текущие значения (после смены темы, сброса и т.д.)."""
        acc = core.CFG.get("accent") or ""
        for d in self.accent_dots:
            d.setChecked((d.color or "") == acc)
            d.update()
        cur = LEGACY_THEMES.get(core.CFG["theme"], core.CFG["theme"])
        for sw in self.swatches:
            sw.setChecked(sw.key == cur)
        self.theme_name.setText("Как в системе" if cur == "auto" else THEMES.get(cur, THEMES["violet"])["NAME"])
        if hasattr(self, "font_slider"):
            self.font_slider.set_key(core.CFG.get("font_size", "normal"))
        if hasattr(self, "corner_picker"):
            self.corner_picker.set_key(core.CFG.get("corners", "soft"))
        if hasattr(self, "animation_style_combo"):
            self.animation_style_combo.blockSignals(True)
            self.animation_style_combo.setCurrentIndex(
                {"smooth": 0, "quick": 1, "subtle": 2}.get(core.CFG.get("animation_style", "smooth"), 0))
            self.animation_style_combo.blockSignals(False)
        self.preview.set_patch(None)

    def set_section_default(self, key: str, collapsed: bool):
        states = dict(core.CFG.get("collapsed_sections", {}))
        states[key] = bool(collapsed)
        core.CFG["collapsed_sections"] = states
        core.save()
        section = self.section_widgets.get(key)
        if section is not None:
            section.header.setChecked(not collapsed)

    def on_animation_style_changed(self, index: int):
        core.CFG["animation_style"] = ["smooth", "quick", "subtle"][max(0, min(2, index))]
        core.save()
        # короткая демонстрация выбранного стиля
        if not anim_on():
            return
        style = core.CFG["animation_style"]
        duration = {"quick": 120, "subtle": 90, "smooth": 240}.get(style, 220)
        self._style_demo = QPropertyAnimation(self.preview, b"windowOpacity", self)
        # preview не имеет windowOpacity, поэтому анимируем через временный эффект
        fx = QGraphicsOpacityEffect(self.preview)
        self.preview.setGraphicsEffect(fx)
        self._style_demo = QPropertyAnimation(fx, b"opacity", self)
        self._style_demo.setDuration(duration)
        self._style_demo.setStartValue(0.35)
        self._style_demo.setEndValue(1.0)
        self._style_demo.setEasingCurve(
            QEasingCurve.OutCubic if style == "smooth" else
            QEasingCurve.OutQuad if style == "quick" else QEasingCurve.Linear)
        self._style_demo.finished.connect(lambda: self.preview.setGraphicsEffect(None))
        self._style_demo.start()

    def on_anim_toggled(self, on: bool):
        core.CFG["animations"] = on
        core.save()
        if not on:
            self.power.pulse.stop()
            self.busybar.anim.stop()
            self.power._level = 1.0 if self.running else 0.0
        elif self.running and self.power.isVisible():
            self.power.pulse.start()
        for w in (self.power, self.busybar, *self.nav_buttons):
            w.update()

    def reset_look(self):
        core.CFG.update(theme="violet", accent="", font_size="normal", corners="soft", density="normal",
                        animations=True, animation_style="smooth")
        core.save()
        if hasattr(self, "font_slider"):
            self.font_slider.set_key("normal")
        if hasattr(self, "corner_picker"):
            self.corner_picker.set_key("soft")
        self.anim_cb.setChecked(True)
        if hasattr(self, "animation_style_combo"):
            self.animation_style_combo.setCurrentIndex(0)
        self.apply_theme("violet")
        self.sync_look_controls()

    def pick_accent(self):
        col = QColorDialog.getColor(QColor(P["ACC1"]), self, "Цвет акцента")
        if col.isValid():
            self.set_look("accent", col.name())

    # ---------- состояние ----------
    def fade_in(self):
        if not anim_on():
            self.setWindowOpacity(1.0)
            return
        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(220)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._fade.start()

    def switch_page(self, i: int):
        """Плавное появление страницы: лёгкое затухание + короткий fade-in."""
        if i == self.stack.currentIndex():
            return
        self.stack.setCurrentIndex(i)
        if not anim_on():
            return
        style = core.CFG.get("animation_style", "smooth")
        duration = 120 if style == "quick" else (90 if style == "subtle" else 220)
        w = self.stack.currentWidget()
        eff = QGraphicsOpacityEffect(w)
        w.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", w)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic if style == "smooth" else QEasingCurve.OutQuad)
        anim.finished.connect(lambda w=w: w.setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._page_anim = anim

    def show_window(self):
        was_hidden = not self.isVisible()
        self.showNormal()
        if was_hidden:
            self.fade_in()
        self.raise_()
        self.activateWindow()

    def on_tray_click(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.isVisible() and self.isActiveWindow():
                self.hide()
            else:
                self.show_window()

    def attach_server(self, server: QLocalServer):
        """Второй запуск (например, из закрепа на панели задач) просто открывает это окно."""
        self._server = server
        server.newConnection.connect(self.on_second_launch)

    def on_second_launch(self):
        while self._server.hasPendingConnections():
            self._server.nextPendingConnection().close()
        self.show_window()

    def notify(self, text: str):
        # Используем иконку приложения (Zapret), а не пустую/системную
        try:
            self.tray.showMessage("Zapret GUI", text, app_icon(), 2500)
        except TypeError:
            # Старые Qt: нет перегрузки с QIcon
            self.tray.showMessage("Zapret GUI", text, QSystemTrayIcon.Information, 2500)

    def on_log(self, text: str):
        line = f"{time.strftime('%H:%M:%S')}  {text}"
        self.log_history = (self.log_history + [line])[-300:]
        self.log_line.setText(text)
        if anim_on():  # новая строка мягко проявляется
            self.log_anim.stop()
            self.log_anim.setDuration(240)
            self.log_anim.setStartValue(0.1)
            self.log_anim.setEndValue(1.0)
            self.log_anim.start()
        if hasattr(self, "log_view"):
            self.log_view.appendPlainText(line)

    def copy_log(self):
        QApplication.clipboard().setText("\n".join(self.log_history))
        self.bus.log.emit("Журнал скопирован в буфер обмена")

    def open_winws_log(self):
        p = core.base_dir() / "winws.log"
        if p.exists():
            os.startfile(str(p))
        else:
            self.bus.log.emit("winws.log ещё не создан: обход ни разу не запускался")

    def running_text(self) -> str:
        s = int(time.time() - self._run_since) if self._run_since else 0
        h, rest = divmod(s, 3600)
        mi, sec = divmod(rest, 60)
        return f"{core.CFG['strategy']}  ·  работает {h:02d}:{mi:02d}:{sec:02d}"

    def tick(self):
        if self.running and not self.busy:
            self.sub.setText(self.running_text())

    def reload_all(self):
        core.seed_profiles()
        self.reload_profiles()
        names = core.strategies()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(names)
        if core.CFG["strategy"] in names:
            self.combo.setCurrentText(core.CFG["strategy"])
        elif names:
            core.CFG["strategy"] = names[0]
            core.save()
        self.combo.blockSignals(False)
        self.backup_list.clear()
        self.backup_list.addItems(core.list_backups())
        self.app_backup_list.clear()
        self.app_backup_list.addItems(core.list_app_backups())
        for r in self.path_rows:
            r.value_label.setText(str(r.getter()))
        self.load_list(self.list_combo.currentText())
        self.update_version_labels()
        self.refresh_status()

    def refresh_status(self):
        running = core.is_running()
        installed = core.is_installed()
        self.running = running
        if running and self._run_since is None:
            self._run_since = time.time()
        elif not running:
            self._run_since = None
        self.power.set_state(running, installed and not self.busy)
        self.restart_btn.setEnabled(installed and not self.busy)
        if self.busy:
            self.status.setText("Подожди…")
            self.sub.setText("")
        elif not installed:
            self.status.setText("Нет zapret")
            self.sub.setText("Скачиваю последний релиз с GitHub…")
        else:
            self.status.setText("Включено" if running else "Выключено")
            self.sub.setText(self.running_text() if running else "Нажми на кнопку, чтобы включить обход")
        self.status.setStyleSheet(f"color: {P['OK']};" if running and not self.busy else "")
        self.tray_toggle.setText("Выключить" if running else "Включить")
        self.tray.setIcon(status_icon(running))
        strategy = core.CFG.get("strategy") or "—"
        if not installed:
            tip = "Zapret GUI: zapret не установлен"
            status_text = "● Нет zapret"
        elif self.busy:
            tip = "Zapret GUI: подождите…"
            status_text = "● Подождите…"
        elif running:
            tip = f"Zapret GUI: включено · {strategy}"
            status_text = f"● Включено · {strategy}"
        else:
            tip = "Zapret GUI: выключено"
            status_text = "● Выключено"
        self.tray.setToolTip(tip)
        if hasattr(self, "tray_status"):
            self.tray_status.setText(status_text)

    def update_version_labels(self):
        self.up_installed.setText(core.CFG["version"] or "не установлена")
        self.up_latest.setText(self.latest[0] or "—")

    def set_opt(self, key: str, on: bool):
        core.CFG[key] = on
        core.save()
        if key == "game_filter" and core.is_running():
            self.restart()

    # ---------- запуск ----------
    def toggle(self):
        if self.busy or not core.is_installed():
            return
        if core.is_running():
            self.status.setText("Выключаю…")
            QApplication.processEvents()
            core.stop()  # убивает winws, останавливает службу zapret и драйвер WinDivert
            self.bus.log.emit("Сервис полностью остановлен (winws, zapret, WinDivert)")
            self.notify("Обход выключен полностью")
            self.refresh_status()
        else:
            self.restart()

    def restart(self):
        """Coalesce simultaneous UI changes into one winws restart.

        Strategy selection and profile/list updates can arrive in the same
        event burst. Previously each signal called core.start() independently,
        killing and relaunching winws multiple times in succession.
        """
        if getattr(self, "_restart_pending", False):
            return
        self._restart_pending = True
        QTimer.singleShot(300, self._restart_now)

    def _restart_now(self):
        self._restart_pending = False
        name = core.CFG["strategy"]
        if not name:
            return
        try:
            mode = core.start(name)
        except Exception as exc:
            self.bus.log.emit(f"Не удалось переключить стратегию: {exc}")
            self.notify("Не удалось переключить стратегию, смотри журнал")
            self.refresh_status()
            return
        self.bus.log.emit(f"Запущено: {name} ({mode})")
        # Даём winws до 5 секунд на старт (раньше было 1.5 с — часто не успевал)
        QTimer.singleShot(5000, self.after_start)

    def after_start(self):
        err = core.start_error()
        if err and not self._bat_tried:  # прямой запуск не удался -> пишем причину и пробуем через .bat
            self._bat_tried = True
            self._first_err = err
            rc = core.LAST_PROC.returncode if core.LAST_PROC else None
            hint = core.explain_output(err, rc)
            self.bus.log.emit("Прямой запуск не удался: " + err.replace("\n", " | ") + (f"  →  {hint}" if hint else ""))
            self.bus.log.emit("Пробую запустить через .bat…")
            core.start(core.CFG["strategy"], force_bat=True)
            QTimer.singleShot(5000, self.after_start)
            return
        first, self._first_err, self._bat_tried = self._first_err, "", False
        running = core.is_running()
        if err or not running:
            # Если запуск через BAT тоже завершился ошибкой, его журнал важнее
            # первоначального сообщения прямого запуска.
            raw = err or first
            hint = core.explain_output(raw)
            problems = core.bin_problems()
            reason = " ".join(problems) or hint or (raw.replace("\n", " | ") if raw else
                                                    "winws.exe не появился: запусти «Проверить систему» в настройках")
            self.bus.log.emit("Обход не запустился. " + reason)
            self.notify("Не удалось включить обход, причина в журнале")
        else:
            self.notify("Обход включён")
            if core.CFG.get("sites_auto") and self.site_rows:
                QTimer.singleShot(3500, self.check_all)  # покажем, что обход действительно работает
        self.refresh_status()

    def auto_pick(self):
        if self.busy or not core.is_installed():
            return
        self.set_busy(True)

        def work():
            try:
                best = core.auto_select(self.bus.log.emit)
                if best:
                    core.CFG["strategy"] = best
                    core.save()
                    core.start(best)
                else:
                    core.stop()
                self.bus.auto_done.emit(best or "")
            except Exception as e:
                self.bus.failed.emit(f"Ошибка подбора: {e}")
        core.bg(work)

    def on_auto_done(self, name: str):
        self.set_busy(False)
        self.reload_all()
        if name:
            self.bus.log.emit(f"Подобрана стратегия: {name}")
            self.notify(f"Подобрана стратегия: {name}")
        else:
            self.bus.log.emit("Ни одна стратегия не подошла. Проверь список сайтов и интернет.")
            self.notify("Подобрать стратегию не удалось")

    def on_strategy_changed(self, name: str):
        if not name:
            return
        core.CFG["strategy"] = name
        core.save()
        if core.is_running():
            self.bus.log.emit(f"Стратегия: {name}, перезапускаю сервис…")
            self.restart()
        else:
            self.refresh_status()

    # ---------- списки ----------
    def load_list(self, name: str):
        if name and hasattr(self, "editor"):
            p = core.list_path(name)
            self.editor.setPlainText(p.read_text(encoding="utf-8") if p.exists() else "")

    def save_list(self):
        p = core.list_path(self.list_combo.currentText(), create=True)
        p.write_text(self.editor.toPlainText().strip() + "\n", encoding="utf-8")
        self.bus.log.emit(f"Сохранено: {p.name}")
        if core.is_running():
            self.restart()

    # ---------- официальные списки ----------
    def refresh_lists_info(self):
        when = core.CFG.get("lists_updated") or "ещё не обновлялись"
        self.lists_info.setText(f"Списки берутся из официального репозитория zapret. Последнее обновление: {when}.")

    def update_lists_now(self, manual: bool = False):
        if not core.is_installed():
            if manual:
                self.bus.log.emit("Сначала нужно установить zapret")
            return
        self.lists_btn.setEnabled(False)

        def work():
            try:
                n = core.update_lists(self.bus.log.emit)
                self.bus.lists_done.emit(n, manual)
            except Exception as e:
                self.bus.failed.emit(f"Не удалось обновить списки: {e}")
        core.bg(work)

    def on_lists_done(self, n: int, manual: bool):
        self.lists_btn.setEnabled(True)
        self.refresh_lists_info()
        self.load_list(self.list_combo.currentText())
        if n:
            self.bus.log.emit(f"Списки обновлены: {n} файл(ов)")
            if core.is_running():
                self.restart()
        elif manual:
            self.bus.log.emit("Списки уже актуальны")

    # ---------- диагностика ----------
    def run_diagnostics_from_tray(self):
        """Из трея: открыть окно на вкладке «Настройки» и запустить проверку."""
        self.show_window()
        try:
            self.switch_page(4)  # «Настройки» (build_more)
            if hasattr(self, "nav_buttons") and len(self.nav_buttons) > 4:
                self.nav_buttons[4].setChecked(True)
        except Exception:
            pass
        self.run_diagnostics()

    def run_diagnostics(self):
        self.diag_btn.setEnabled(False)
        self.diag_view.setPlainText("Проверяю…")
        core.bg(lambda: self.bus.diag_done.emit(core.diagnose()))

    def on_diag_done(self, items: list):
        self.diag_btn.setEnabled(True)
        marks = {True: "✓", False: "✗", None: "•"}
        self.diag_view.setPlainText("\n".join(f"{marks[ok]}  {text}" for ok, text in items))

    # ---------- обновление приложения ----------
    def on_channel_changed(self, i: int):
        core.CFG["app_channel"] = "pre" if i == 1 else "stable"
        core.save()
        self.check_app_updates(manual=True)

    def save_app_repo(self):
        core.CFG["app_repo"] = self.app_repo_edit.text().strip()
        core.save()

    def set_app_busy(self, busy: bool):
        self._app_busy = busy
        self.update_busybar()
        for b in self.app_buttons:
            b.setEnabled(not busy)
        if not busy:
            self.app_update_btn.setEnabled(bool(self.app_rels) and
                                           core.parse_ver(self.app_rels[0]["version"]) > core.parse_ver(core.VERSION))

    def check_app_updates(self, manual: bool = False):
        if not core.app_repo():
            if manual:
                self.bus.log.emit("Укажи репозиторий GitHub (владелец/репозиторий) в блоке «Приложение»")
            return
        self._app_manual = manual

        def work():
            try:
                self.bus.app_checked.emit(core.app_releases())
            except Exception as e:
                if manual:
                    self.bus.failed.emit(f"Не удалось проверить обновления приложения.\n{e}")
                else:
                    self.bus.log.emit(f"Проверка обновлений пропущена: {e}")
        core.bg(work)

    def show_home_banner(self, title: str, body: str, show_update: bool):
        if not hasattr(self, "home_banner"):
            return
        self.home_banner_title.setText(title)
        self.home_banner_body.setText(body)
        self.home_banner_update.setVisible(show_update)
        self.home_banner.setVisible(True)

    def hide_home_banner(self):
        if hasattr(self, "home_banner"):
            self.home_banner.setVisible(False)

    def on_home_banner_update(self):
        if self.app_rels:
            self.install_app(self.app_rels[0])
        else:
            self.check_app_updates(manual=True)

    def on_home_banner_later(self):
        # Закрытие баннера не отключает уведомления о версии навсегда.
        self.hide_home_banner()

    def maybe_show_whats_new(self):
        """После обновления один раз показать краткое «что изменилось»."""
        seen = core.CFG.get("changelog_seen") or ""
        if seen == core.VERSION:
            return
        notes = self._changelog_for(core.VERSION)
        core.CFG["changelog_seen"] = core.VERSION
        core.save()
        if notes:
            self.show_home_banner(f"Обновлено до {core.VERSION}", notes, show_update=False)

    def _changelog_for(self, ver: str) -> str:
        try:
            base = Path(getattr(sys, "_MEIPASS", None) or Path(__file__).parent)
            text = (base / "CHANGELOG.md").read_text(encoding="utf-8")
        except Exception:
            return ""
        lines, grab = [], False
        for line in text.splitlines():
            if line.startswith("## ") and ver in line:
                grab = True
                continue
            if grab and line.startswith("## "):
                break
            if grab and line.strip().startswith("-"):
                lines.append(line.strip())
            if grab and len(lines) >= 5:
                break
        return "\n".join(lines) if lines else ""

    def on_app_checked(self, rels: list):
        self.app_rels = rels
        self.app_combo.clear()
        for r in rels:
            self.app_combo.addItem(f"{r['tag']}  ·  {r['date']}" + ("  ·  пререлиз" if r.get("pre") else ""), r)
        latest = rels[0] if rels else None
        self.app_latest_lbl.setText(latest["version"] if latest else "—")
        self.set_app_busy(False)
        newer = bool(latest) and core.parse_ver(latest["version"]) > core.parse_ver(core.VERSION)
        ignored = core.CFG.get("app_ignore", "")
        skip = bool(ignored) and bool(latest) and core.parse_ver(latest["version"]) <= core.parse_ver(ignored)
        if newer and not skip:
            notes = (latest.get("notes") or "").strip()
            if not notes:
                notes = self._changelog_for(latest["version"])
            if not notes:
                notes = f"Доступна версия {latest['version']}. Подробности смотрите в списке изменений релиза."
            notes = re.sub(r"(?m)^#{1,6}\\s*", "", notes)
            notes = re.sub(r"(?m)^[-*]\\s*", "• ", notes)
            self.show_home_banner(
                f"Доступна новая версия: {latest['version']}",
                f"Текущая версия: {core.VERSION}\\n\\nЧто нового:\\n{notes}",
                show_update=True)
            if core.CFG["app_auto_update"] and core.can_self_update():
                self.install_app(latest)
            else:
                self.bus.log.emit(f"Доступна новая версия приложения: {latest['version']}")
                self.notify(f"Доступна новая версия приложения: {latest['version']}")
        elif self._app_manual:
            self.bus.log.emit("Новых версий приложения нет" if not newer else f"Доступна версия {latest['version']}")
            if not newer:
                self.hide_home_banner()
        else:
            self.maybe_show_whats_new()

    def install_app(self, rel):
        if not rel:
            return
        if not core.can_self_update():
            QMessageBox.information(self, "Обновление", "Обновление работает только в собранном ZapretGUI.exe, "
                                    "а не при запуске из исходников.")
            return
        self.set_app_busy(True)

        def work():
            try:
                self.bus.app_ready.emit(str(core.prepare_app_install(rel, self.bus.log.emit)))
            except Exception as e:
                self.bus.failed.emit(f"Ошибка обновления приложения: {e}")
        core.bg(work)

    def rollback_app(self):
        item = self.app_backup_list.currentItem()
        if not item:
            return
        if not core.can_self_update():
            QMessageBox.information(self, "Откат", "Откат работает только в собранном ZapretGUI.exe.")
            return
        ver = item.text()
        if QMessageBox.question(self, "Откат", f"Вернуть версию {ver}? Приложение перезапустится.") != QMessageBox.Yes:
            return
        self.set_app_busy(True)
        prev = core.VERSION

        def work():
            try:
                path = core.prepare_app_rollback(ver, self.bus.log.emit)
                core.CFG["app_ignore"] = prev  # не предлагать снова версию, с которой откатились
                core.save()
                self.bus.app_ready.emit(str(path))
            except Exception as e:
                self.bus.failed.emit(f"Ошибка отката: {e}")
        core.bg(work)

    def on_app_ready(self, path: str):
        # не гасим обход при обновлении — после старта новой версии resume_after_update включит его снова
        core.CFG["resume_after_update"] = core.is_running()
        core.save()
        self.bus.log.emit("Перезапускаю приложение в новой версии…")
        try:
            core.launch_updater(Path(path))
        except Exception as e:
            self.bus.failed.emit(f"Не удалось запустить обновление: {e}")
            self.set_app_busy(False)
            return
        # выход без stop(): иначе обход и файлы могут мешать подмене exe
        self.tray.hide()
        QTimer.singleShot(200, QApplication.quit)

    # ---------- профили ----------
    def filter_profiles(self, query: str):
        query = (query or "").strip().casefold()
        for i in range(self.prof_list.count()):
            item = self.prof_list.item(i)
            item.setHidden(query not in item.text().casefold())

    def update_profile_count(self):
        if not hasattr(self, "prof_editor"):
            return
        lines = [line.strip() for line in self.prof_editor.toPlainText().splitlines() if line.strip()]
        self.profile_count.setText(f"{len(lines)} домен(ов)")

    def export_profile(self):
        if not self._cur_profile:
            self.bus.log.emit("Сначала выбери профиль для экспорта")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт профиля", self._cur_profile + ".txt",
                                               "Текстовые файлы (*.txt);;Все файлы (*.*)")
        if path:
            Path(path).write_text(self.prof_editor.toPlainText(), encoding="utf-8")
            self.bus.log.emit(f"Профиль экспортирован: {path}")

    def reload_profiles(self, select: str = ""):
        names = core.list_profiles()
        self.prof_list.blockSignals(True)
        self.prof_list.clear()
        for n in names:
            it = QListWidgetItem(n)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if core.is_enabled(n) else Qt.Unchecked)
            self.prof_list.addItem(it)
        self.prof_list.blockSignals(False)
        target = select or self._cur_profile
        idx = names.index(target) if target in names else (0 if names else -1)
        if idx >= 0:
            self.prof_list.setCurrentRow(idx)
            self.on_profile_selected(self.prof_list.item(idx), None)
        else:
            self._cur_profile = ""
            self.prof_editor.clear()
        if hasattr(self, "profile_summary"):
            enabled = sum(1 for name in names if core.is_enabled(name))
            self.profile_summary.setText(f"{len(names)} профилей · включено {enabled}")
        if hasattr(self, "profile_search"):
            self.filter_profiles(self.profile_search.text())

    def on_profile_selected(self, cur, _prev):
        if cur is not None:
            self._cur_profile = cur.text()
            self.prof_editor.setPlainText(core.read_profile(cur.text()))

    def on_profile_toggled(self, item):
        core.set_enabled(item.text(), item.checkState() == Qt.Checked)
        if hasattr(self, "profile_summary"):
            names = core.list_profiles()
            enabled = sum(1 for name in names if core.is_enabled(name))
            self.profile_summary.setText(f"{len(names)} профилей · включено {enabled}")
        self.apply_profiles_now()

    def apply_profiles_now(self):
        core.apply_profiles()
        if core.is_running():
            self.bus.log.emit("Профили изменены, перезапускаю сервис…")
            self.restart()

    def new_profile(self):
        name, ok = QInputDialog.getText(self, "Новый профиль", "Название профиля:")
        name = core.safe_name(name) if ok else ""
        if not name:
            return
        if name in core.list_profiles():
            self.bus.log.emit("Профиль с таким названием уже есть")
            return
        core.write_profile(name, "")
        self.reload_profiles(select=name)
        self.prof_editor.setFocus()

    def save_profile(self):
        if not self._cur_profile:
            return
        core.write_profile(self._cur_profile, self.prof_editor.toPlainText())
        self.bus.log.emit(f"Профиль сохранён: {self._cur_profile}")
        if core.is_enabled(self._cur_profile):
            self.apply_profiles_now()

    def delete_profile(self):
        name = self._cur_profile
        if not name:
            return
        if QMessageBox.question(self, "Удалить профиль", f"Удалить профиль «{name}»?") != QMessageBox.Yes:
            return
        was_enabled = core.is_enabled(name)
        core.delete_profile(name)
        self._cur_profile = ""
        self.reload_profiles()
        self.bus.log.emit(f"Профиль удалён: {name}")
        if was_enabled:
            self.apply_profiles_now()

    def import_profile(self):
        f, _ = QFileDialog.getOpenFileName(self, "Файл со списком доменов", "", "Текст (*.txt)")
        if not f:
            return
        name = core.safe_name(Path(f).stem) or "Импорт"
        while name in core.list_profiles():
            name += " (импорт)"
        core.write_profile(name, Path(f).read_text(encoding="utf-8", errors="ignore"))
        self.reload_profiles(select=name)
        self.bus.log.emit(f"Профиль импортирован: {name}")

    def restart_service(self):
        """Мини-кнопка у кнопки включения: перезапуск (если был выключен, просто запустит)."""
        if self.busy or not core.is_installed():
            return
        self.bus.log.emit("Перезапускаю сервис…")
        self.restart()

    # ---------- сайты ----------
    def rebuild_sites(self):
        while self.sites_lay.count():
            item = self.sites_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.site_rows = {}
        sites = core.CFG["sites"]
        for s in sites:
            url = s["url"]
            row = SiteRow(s["name"], url)
            row.check_btn.clicked.connect(lambda _=False, u=url: self.check_one(u))
            row.open_btn.clicked.connect(lambda _=False, u=url: self.open_site(u))
            row.del_btn.clicked.connect(lambda _=False, u=url: self.remove_site(u))
            row.set_result(self.site_results.get(url), animate=False)
            cached = self._favicon_cache.get(url)
            if cached:
                row.set_favicon(cached)
            self.sites_lay.addWidget(row)
            self.site_rows[url] = row
        if not sites:
            empty = QLabel("Список пуст. Добавь сайт строкой выше или выбери из быстрых.")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            self.sites_lay.addWidget(empty)
        self.sites_lay.addStretch(1)
        self.rebuild_chips()
        self.update_sites_summary()
        self.load_missing_favicons()

    def load_missing_favicons(self):
        """В фоне подтянуть иконки для сайтов, у которых ещё нет кэша."""
        need = [u for u in self.site_rows if u not in self._favicon_cache]
        if not need:
            return

        def work():
            for url in need:
                try:
                    data = core.fetch_favicon(url)
                except Exception:
                    data = None
                self.bus.favicon.emit(url, data)

        core.bg(work)

    def on_favicon(self, url: str, data):
        if data:
            self._favicon_cache[url] = data
            row = self.site_rows.get(url)
            if row is not None:
                row.set_favicon(data)
        else:
            self._favicon_cache.setdefault(url, b"")  # не долбить повторно

    def rebuild_chips(self):
        while self.chips_lay.count():
            item = self.chips_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        have = {s["url"] for s in core.CFG["sites"]}
        free = [(n, u) for n, u in SITE_PRESETS if core.normalize_url(u) not in have][:6]
        for i, (n, u) in enumerate(free):
            b = QPushButton(f"+  {n}")
            b.setObjectName("chip")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, n=n, u=u: self.add_preset(n, u))
            self.chips_lay.addWidget(b, i // 3, i % 3)
        self.chips_box.setVisible(bool(free))
        self.chips_cap.setVisible(bool(free))

    def update_sites_summary(self):
        sites = core.CFG["sites"]
        done = [s for s in sites if s["url"] in self.site_results]
        ok = sum(1 for s in done if self.site_results[s["url"]]["ok"])
        if not sites:
            title, sub, ratio = "Список пуст", "Добавь сайты, доступность которых хочешь отслеживать", 0.0
        elif not done:
            title, sub, ratio = f"Сайтов в списке: {len(sites)}", "Нажми «Проверить все»", 0.0
        else:
            title = f"Доступно {ok} из {len(done)}"
            sub = f"Последняя проверка: {self.sites_checked_at}" if self.sites_checked_at else ""
            ratio = ok / len(done)
        self.sites_title.setText(title)
        self.sites_sub.setText(sub)
        self.ratio_bar.set_ratio(ratio)

    def open_site(self, url: str):
        try:
            os.startfile(url)  # откроется в браузере по умолчанию
        except Exception as e:
            self.bus.log.emit(f"Не удалось открыть {url}: {e}")

    def add_site(self):
        text = self.site_input.text()
        url = core.normalize_url(text) if text.strip() else ""
        if url and core.add_site(text):
            self.site_input.clear()
            self.rebuild_sites()
            self.check_one(url)
        else:
            self.bus.log.emit("Сайт пустой или уже есть в списке")

    def add_preset(self, name: str, url: str):
        if core.add_site(url, name):
            self.rebuild_sites()
            self.check_one(core.normalize_url(url))

    def remove_site(self, url: str):
        core.remove_site(url)
        self.site_results.pop(url, None)
        self.rebuild_sites()

    def check_one(self, url: str):
        row = self.site_rows.get(url)
        if row:
            row.set_checking()
        core.bg(lambda: self.bus.site.emit(0, url, core.probe(url)))

    def check_all(self):
        sites = list(core.CFG["sites"])
        if not sites:
            return
        self.sites_btn.setEnabled(False)
        self.sites_sub.setText("Проверяю…")
        for s in sites:
            row = self.site_rows.get(s["url"])
            if row:
                row.set_checking()

        def work():
            with ThreadPoolExecutor(max_workers=6) as ex:
                futs = {ex.submit(core.probe, s["url"]): s["url"] for s in sites}
                for f in as_completed(futs):  # результаты появляются по мере готовности
                    self.bus.site.emit(0, futs[f], f.result())
            self.bus.sites_done.emit()
        core.bg(work)

    def on_site_result(self, _i: int, url: str, res: dict):
        self.site_results[url] = res
        self.sites_checked_at = time.strftime("%H:%M:%S")
        row = self.site_rows.get(url)
        if row:
            row.set_result(res)
        self.update_sites_summary()

    # ---------- обновления / бэкапы / импорт ----------
    def update_busybar(self):
        self.busybar.run(self.busy or self._app_busy)

    def set_busy(self, busy: bool):
        self.busy = busy
        self.update_busybar()
        for b in self.busy_buttons:
            b.setEnabled(not busy)
        self.refresh_status()

    def check_updates(self, force=False):
        self._force = force
        self.btn_check.setEnabled(False)

        def work():
            try:
                self.bus.latest.emit(*core.latest_release())
            except Exception as e:
                self.bus.failed.emit(f"Не удалось проверить обновления: {e}")
        core.bg(work)

    def on_latest(self, tag: str, url: str):
        self.latest = (tag, url)
        self.update_version_labels()
        self.btn_check.setEnabled(not self.busy)
        outdated = tag != core.CFG["version"] and core.CFG["version"] != "своя"
        if outdated and (not core.is_installed() or core.CFG["auto_update"] or self._force):
            self.install_latest()
        else:
            self.bus.log.emit("Обновлений нет" if not outdated else f"Доступна версия {tag}")
            if outdated:
                self.notify(f"Доступна новая версия zapret: {tag}")

    def run_task(self, fn):
        was_running = core.is_running()
        self.set_busy(True)

        def work():
            try:
                fn()
                if was_running:
                    names = core.strategies()
                    if names:
                        saved = core.CFG["strategy"]
                        core.start(saved if saved in names else names[0])
                self.bus.changed.emit()
            except Exception as e:
                self.bus.failed.emit(f"Ошибка: {e}")
        core.bg(work)

    def install_latest(self):
        tag, url = self.latest
        if tag and not self.busy:
            self.run_task(lambda: core.install_release(url, tag, self.bus.log.emit))

    def load_zapret_releases(self):
        self.btn_zapret_list.setEnabled(False)

        def work():
            try:
                self.bus.zapret_releases.emit(core.list_zapret_releases(25))
            except Exception as e:
                self.bus.failed.emit(f"Не удалось загрузить список версий zapret: {e}")

        core.bg(work)

    def on_zapret_releases(self, items: list):
        self.zapret_rels = items or []
        self.zapret_combo.clear()
        for it in self.zapret_rels:
            pre = " (pre)" if it.get("pre") else ""
            date = f" · {it['date']}" if it.get("date") else ""
            self.zapret_combo.addItem(f"{it['tag']}{pre}{date}", it)
        self.zapret_combo.setEnabled(bool(self.zapret_rels))
        self.btn_zapret_list.setEnabled(not self.busy)
        if self.zapret_rels:
            self.bus.log.emit(f"Загружено версий zapret: {len(self.zapret_rels)}")
        else:
            self.bus.log.emit("Список версий zapret пуст")

    def install_selected_zapret(self):
        it = self.zapret_combo.currentData()
        if not it or self.busy:
            if not it:
                self.bus.log.emit("Сначала нажми «Загрузить список» и выбери версию")
            return
        tag, url = it["tag"], it["url"]
        self.run_task(lambda: core.install_release(url, tag, self.bus.log.emit))

    def on_changed(self):
        self.set_busy(False)
        self.reload_all()

    def on_failed(self, msg: str):
        self.bus.log.emit(msg)
        self.btn_check.setEnabled(True)
        self.set_app_busy(False)
        self.lists_btn.setEnabled(True)
        self.diag_btn.setEnabled(True)
        if self.busy:
            self.set_busy(False)

    def restore_backup(self):
        item = self.backup_list.currentItem()
        if item:
            self.run_task(lambda: core.restore_backup(item.text(), self.bus.log.emit))

    def import_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Папка с zapret (где лежат general*.bat и bin)")
        if d:
            self.run_task(lambda: core.import_folder(Path(d), self.bus.log.emit))

    def import_zip(self):
        f, _ = QFileDialog.getOpenFileName(self, "Архив zapret", "", "ZIP (*.zip)")
        if f:
            self.run_task(lambda: core.import_zip(Path(f), self.bus.log.emit))

    def change_base(self):
        d = QFileDialog.getExistingDirectory(self, "Новая папка данных", str(core.base_dir()))
        if not d:
            return
        core.set_base_dir(d)
        self.reload_all()
        self.bus.log.emit(f"Папка данных: {d}. zapret скачается заново.")
        self.check_updates(force=True)

    def toggle_autostart(self, on: bool):
        if not core.set_autostart(on):
            self.autostart_cb.setChecked(not on)
            QMessageBox.warning(self, "Автозапуск", "Не удалось изменить задачу автозапуска.")

    # ---------- окно ----------
    def closeEvent(self, e):
        if core.CFG["close_to_tray"]:
            e.ignore()
            self.hide()
            self.notify("Работает в трее")
        else:
            self.quit_app()

    def quit_app(self):
        if core.CFG["stop_on_exit"]:
            core.stop()
        self.tray.hide()
        QApplication.quit()


def main():
    if sys.platform == "win32" and not is_admin():
        relaunch_as_admin()
        return
    try:  # чтобы значок в панели задач и закреплённый ярлык совпадали
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ZapretGUI.App")
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setWindowIcon(app_icon())
    app.setQuitOnLastWindowClosed(False)
    set_palette(core.CFG["theme"])
    app.setStyleSheet(build_style())
    sock = QLocalSocket()  # уже запущена? тогда просто открываем её окно и выходим
    sock.connectToServer(SERVER_NAME)
    if sock.waitForConnected(400):
        sock.write(b"show")
        sock.waitForBytesWritten(400)
        return
    server = QLocalServer()
    QLocalServer.removeServer(SERVER_NAME)
    server.listen(SERVER_NAME)
    w = MainWindow()
    w.attach_server(server)
    if "--minimized" not in sys.argv:
        w.show()
        w.fade_in()
    sys.exit(app.exec() if hasattr(app, "exec") else app.exec_())


if __name__ == "__main__":
    main()
