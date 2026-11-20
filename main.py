import ctypes
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import (QEasingCurve, QObject, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer,
                            QVariantAnimation, Signal)
from PySide6.QtGui import QAction, QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (
    QAbstractButton, QAbstractItemView, QApplication, QBoxLayout, QColorDialog, QGraphicsOpacityEffect, QInputDialog, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QStackedWidget, QSystemTrayIcon, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

import core

THEMES = {
    "violet": dict(NAME="Фиолетовая", SWATCH=("#0c0d12", "#7c5cff", "#e6e8ef"),
                   BG="#0c0d12", SURFACE="#15161d", BORDER="#242530", TEXT="#f2f3f7", MUTED="#7c7f93",
                   ACC1="#7c5cff", ACC2="#b794ff", OK="#34d399", BAD="#ff5c7a", HOVER="#272836",
                   BTN="#1e1f29", SEL="#2a2550", MONO="#b4b7c9", OFF="#2d2e3c", DIS="#565869", ONACC="#ffffff"),
    "green": dict(NAME="Зелёная", SWATCH=("#070b09", "#22c55e", "#14301f"),
                  BG="#070b09", SURFACE="#0e1612", BORDER="#1b2b22", TEXT="#eaf5ee", MUTED="#6f8a7a",
                  ACC1="#16a34a", ACC2="#4ade80", OK="#4ade80", BAD="#ff6b6b", HOVER="#16251d",
                  BTN="#12201a", SEL="#14301f", MONO="#a9c4b4", OFF="#24382c", DIS="#4d6358", ONACC="#04130a"),
    "light": dict(NAME="Светлая", SWATCH=("#ffffff", "#6a4cff", "#c9cbd8"),
                  BG="#f4f5fa", SURFACE="#ffffff", BORDER="#e1e3ee", TEXT="#14151c", MUTED="#6b6f85",
                  ACC1="#6a4cff", ACC2="#a78bfa", OK="#0f9f8a", BAD="#e03e5c", HOVER="#ecedf6",
                  BTN="#f0f1f8", SEL="#e4defe", MONO="#4a4d63", OFF="#d5d7e4", DIS="#a3a6b8", ONACC="#ffffff"),
    "light-green": dict(NAME="Светло-зелёная", SWATCH=("#ffffff", "#16a34a", "#cfe0d5"),
                        BG="#f2f7f4", SURFACE="#ffffff", BORDER="#dbe8df", TEXT="#12201a", MUTED="#5f7a6b",
                        ACC1="#15803d", ACC2="#22c55e", OK="#15803d", BAD="#dc2f4f", HOVER="#e8f1ec",
                        BTN="#ecf3ef", SEL="#d5efdf", MONO="#3f5a4b", OFF="#cfe0d5", DIS="#9db3a6", ONACC="#ffffff"),
}
THEME_KEYS = ["violet", "green", "light", "light-green", "auto"]
LEGACY_THEMES = {"dark": "violet"}
FONT_KEYS, FONT_SIZES = ["small", "normal", "large"], {"small": 9, "normal": 10, "large": 11.5}
CORNER_KEYS, CORNERS = ["soft", "sharp"], {"soft": (14, 10), "sharp": (6, 4)}
SERVER_NAME = "ZapretGUI.single"
COMPACT_WIDTH = 720

P = dict(THEMES["violet"], FS=10, R1=14, R2=10)  # текущая палитра


def build_style() -> str:
    c = P
    return f"""
* {{ font-family: 'Segoe UI'; font-size: {c['FS']}pt; color: {c['TEXT']}; }}
QMainWindow, QWidget#page, QScrollArea, QWidget#scrollbody {{ background: {c['BG']}; border: none; }}
QFrame#card {{ background: {c['SURFACE']}; border: 1px solid {c['BORDER']}; border-radius: {c['R1']}px; }}
QLabel#cardTitle {{ color: {c['MUTED']}; font-weight: 600; }}
QLabel#status {{ font-size: 20pt; font-weight: 700; }}
QLabel#muted {{ color: {c['MUTED']}; }}
QLabel#mono {{ font-family: Consolas; color: {c['MONO']}; }}
QPushButton {{ background: {c['BTN']}; border: 1px solid {c['BORDER']}; padding: 8px 14px; border-radius: {c['R2']}px; }}
QPushButton:hover {{ background: {c['HOVER']}; }}
QPushButton:disabled {{ color: {c['DIS']}; background: {c['SURFACE']}; }}
QPushButton#accent {{ border: none; font-weight: 600; color: {c['ONACC']};
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c['ACC1']}, stop:1 {c['ACC2']}); }}
QPushButton#accent:disabled {{ background: {c['HOVER']}; color: {c['DIS']}; }}
QPushButton#ghost {{ background: transparent; border: none; color: {c['MUTED']}; padding: 4px 8px; }}
QPushButton#ghost:hover {{ color: {c['BAD']}; }}
QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTableWidget {{
    background: {c['SURFACE']}; border: 1px solid {c['BORDER']}; border-radius: {c['R2']}px; padding: 7px; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {c['ACC1']}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{ background: {c['SURFACE']}; border: 1px solid {c['BORDER']};
    selection-background-color: {c['ACC1']}; selection-color: #ffffff; outline: 0; }}
QListWidget::item {{ padding: 6px; border-radius: 6px; }}
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
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: {c['OFF']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{ background: {c['SURFACE']}; color: {c['TEXT']}; border: 1px solid {c['BORDER']}; }}
"""


def resolve_theme(name: str) -> str:
    name = LEGACY_THEMES.get(name, name)
    if name == "auto":
        try:
            return "light" if QApplication.styleHints().colorScheme() == Qt.ColorScheme.Light else "violet"
        except Exception:
            return "violet"
    return name if name in THEMES else "violet"


def mix(c1: str, c2: str, t: float) -> str:
    a, b = QColor(c1), QColor(c2)
    return QColor(int(a.red() * (1 - t) + b.red() * t), int(a.green() * (1 - t) + b.green() * t),
                  int(a.blue() * (1 - t) + b.blue() * t)).name()


def set_palette(name: str) -> None:
    P.update(THEMES[resolve_theme(name)])
    acc = core.CFG.get("accent") or ""
    if acc and QColor(acc).isValid():  # свой цвет акцента перекрывает цвета выбранной темы
        P["ACC1"], P["ACC2"] = acc, QColor(acc).lighter(135).name()
        P["SEL"] = mix(P["BG"], acc, 0.25)
        P["ONACC"] = "#ffffff" if QColor(acc).lightness() < 125 else "#0c0d12"
    P["FS"] = FONT_SIZES.get(core.CFG.get("font_size"), 10)
    P["R1"], P["R2"] = CORNERS.get(core.CFG.get("corners"), (14, 10))


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
    lay = QVBoxLayout(f)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(10)
    if title:
        t = QLabel(title)
        t.setObjectName("cardTitle")
        lay.addWidget(t)
    return f, lay


def page() -> tuple[QWidget, QVBoxLayout]:
    w = QWidget()
    w.setObjectName("page")
    lay = QVBoxLayout(w)
    lay.setContentsMargins(24, 10, 24, 20)
    lay.setSpacing(12)
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
    """Кнопка вкладки: только иконка, название в подсказке."""

    def __init__(self, kind: str, tip: str):
        super().__init__()
        self.kind, self.hover = kind, False
        self.setCheckable(True)
        self.setToolTip(tip)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(52, 46)

    def enterEvent(self, e):
        self.hover = True
        self.update()

    def leaveEvent(self, e):
        self.hover = False
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        if self.isChecked():
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(P["SEL"]))
            p.drawRoundedRect(r, 14, 14)
        elif self.hover:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(P["HOVER"]))
            p.drawRoundedRect(r, 14, 14)
        draw_icon(p, self.kind, r.center(), QColor(P["ACC1"] if self.isChecked() else P["MUTED"]))


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
            p.setPen(QPen(QColor(P["ACC1"]), 2.5))
            p.drawEllipse(QRectF(self.rect()).adjusted(2, 2, -2, -2))
        else:
            p.setPen(QPen(QColor(P["BORDER"]), 1.5))
            p.drawEllipse(r)


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
        if changed:
            self.anim.stop()
            self.anim.setStartValue(self._level)
            self.anim.setEndValue(1.0 if on else 0.0)
            self.anim.start()
            if on and self.isVisible():
                self.pulse.start()
            elif not on:
                self.pulse.stop()
                self._pulse = 0.0
        self.update()

    def showEvent(self, e):
        if self.on:
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
        self._cur_profile = ""
        self.log_history = []
        self.app_rels = []
        self.app_buttons = []
        self._app_manual = False
        self.running = False
        self._run_since = None
        self._page_anim = None
        self._fade = None
        self.swatches = []
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

        root = QWidget()
        root.setObjectName("page")
        self.setCentralWidget(root)
        self.root_lay = QBoxLayout(QBoxLayout.LeftToRight, root)
        self.root_lay.setContentsMargins(0, 0, 0, 0)
        self.root_lay.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setMaximumWidth(920)
        self.content = QWidget()
        self.content.setObjectName("page")
        cl = QHBoxLayout(self.content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addStretch(1)
        cl.addWidget(self.stack, 100)
        cl.addStretch(1)

        self.nav = QWidget()
        self.nav.setObjectName("nav")
        self.nav.setAttribute(Qt.WA_StyledBackground, True)
        self.nav_lay = QBoxLayout(QBoxLayout.LeftToRight, self.nav)
        self.nav_buttons = []
        group = QButtonGroup(self)
        for i, (kind, tip, builder) in enumerate([
            ("power", "Главная", self.build_home), ("globe", "Сайты", self.build_sites),
            ("list", "Списки", self.build_lists), ("layers", "Профили", self.build_profiles),
            ("more", "Ещё", self.build_more),
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
        v.addSpacing(14)
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
        w, v = page()
        row = QHBoxLayout()
        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("example.com")
        self.site_input.returnPressed.connect(self.add_site)
        add = QPushButton("Добавить")
        add.clicked.connect(self.add_site)
        row.addWidget(self.site_input, 1)
        row.addWidget(add)
        v.addLayout(row)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Сайт", "Статус", "Ответ", ""])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 110)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setShowGrid(False)
        v.addWidget(self.table, 1)
        self.sites_btn = QPushButton("Проверить все")
        self.sites_btn.setObjectName("accent")
        self.sites_btn.clicked.connect(self.check_all)
        v.addWidget(self.sites_btn)
        self.fill_sites()
        return w

    def build_lists(self):
        w, v = page()
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
        b = QPushButton("Сохранить и применить")
        b.setObjectName("accent")
        b.clicked.connect(self.save_list)
        v.addWidget(b)
        return w

    def build_profiles(self):
        w, v = page()
        hint = QLabel("Профили: наборы доменов для обхода (Telegram, Discord и свои). Галочка включает профиль, "
                      "сервис перезапускается сам.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        v.addWidget(hint)
        self.prof_list = QListWidget()
        self.prof_list.setMaximumHeight(170)
        self.prof_list.currentItemChanged.connect(self.on_profile_selected)
        self.prof_list.itemChanged.connect(self.on_profile_toggled)
        v.addWidget(self.prof_list)
        lab = QLabel("Домены выбранного профиля")
        lab.setObjectName("cardTitle")
        v.addWidget(lab)
        self.prof_editor = QPlainTextEdit()
        self.prof_editor.setPlaceholderText("Один домен на строку, например: example.com")
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
        for b in (b_new, b_save, b_del, b_imp):
            row.addWidget(b)
        v.addLayout(row)
        return w

    def build_more(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        body.setObjectName("scrollbody")
        v = QVBoxLayout(body)
        v.setContentsMargins(24, 10, 24, 20)
        v.setSpacing(12)
        scroll.setWidget(body)

        c, cl = card("О приложении")
        t = QLabel("Zapret GUI")
        t.setStyleSheet("font-size: 16pt; font-weight: 700;")
        cl.addWidget(t)
        ver = QLabel(f"Версия {core.VERSION}")
        cl.addWidget(ver)
        repo = core.app_repo()
        if repo:
            link = QLabel(f'<a href="https://github.com/{repo}">github.com/{repo}</a>')
            link.setOpenExternalLinks(True)
            cl.addWidget(link)
        v.addWidget(c)

        c, cl = card("zapret")
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
        self.busy_buttons += [self.btn_check, self.btn_install]
        v.addWidget(c)

        c, cl = card("Приложение")
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
        v.addWidget(c)

        c, cl = card("Папки")
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
        v.addWidget(c)

        c, cl = card("Бэкапы и своя версия")
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
        v.addWidget(c)

        c, cl = card("Журнал")
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
        v.addWidget(c)

        c, cl = card("Оформление")
        row = QHBoxLayout()
        row.setSpacing(6)
        grp = QButtonGroup(self)
        cur = LEGACY_THEMES.get(core.CFG["theme"], core.CFG["theme"])
        self.swatches = []
        for key in THEME_KEYS:
            sw = ThemeSwatch(key)
            sw.setChecked(key == cur)
            sw.clicked.connect(lambda _=False, k=key: self.on_theme_pick(k))
            grp.addButton(sw)
            self.swatches.append(sw)
            row.addWidget(sw)
        row.addStretch(1)
        cl.addLayout(row)
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Мелкий шрифт", "Обычный шрифт", "Крупный шрифт"])
        self.font_combo.setCurrentIndex(FONT_KEYS.index(core.CFG["font_size"]) if core.CFG["font_size"] in FONT_KEYS else 1)
        self.font_combo.currentIndexChanged.connect(lambda i: self.set_look("font_size", FONT_KEYS[i]))
        self.corner_combo = QComboBox()
        self.corner_combo.addItems(["Мягкие углы", "Строгие углы"])
        self.corner_combo.setCurrentIndex(CORNER_KEYS.index(core.CFG["corners"]) if core.CFG["corners"] in CORNER_KEYS else 0)
        self.corner_combo.currentIndexChanged.connect(lambda i: self.set_look("corners", CORNER_KEYS[i]))
        cl.addWidget(self.font_combo)
        cl.addWidget(self.corner_combo)
        arow = QHBoxLayout()
        b_acc = QPushButton("Свой цвет акцента…")
        b_acc.clicked.connect(self.pick_accent)
        b_reset = QPushButton("Сбросить")
        b_reset.clicked.connect(lambda: self.set_look("accent", ""))
        arow.addWidget(b_acc, 1)
        arow.addWidget(b_reset)
        cl.addLayout(arow)
        v.addWidget(c)

        c, cl = card("Поведение")
        self.opts = {}
        for key, text in [
            ("auto_update", "Обновлять zapret автоматически"),
            ("auto_start_bypass", "Включать обход при запуске программы"),
            ("close_to_tray", "Крестик сворачивает в трей"),
            ("stop_on_exit", "Выключать обход при выходе из программы"),
            ("game_filter", "Игровой фильтр (порты выше 1023)"),
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
        v.addWidget(c)
        v.addStretch()
        return scroll

    def build_tray(self):
        self.tray = QSystemTrayIcon(status_icon(False), self)
        self.tray.setToolTip("Zapret GUI")
        menu = QMenu()
        self.tray_toggle = QAction("Включить", self, triggered=self.toggle)
        menu.addAction(QAction("Открыть", self, triggered=self.show_window))
        menu.addAction(self.tray_toggle)
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
        """Узкое окно: вкладки-иконки снизу (как в телефоне). Широкое: колонка иконок слева."""
        self.compact = compact
        lay, nl = self.root_lay, self.nav_lay
        lay.removeWidget(self.nav)
        lay.removeWidget(self.content)
        while nl.count():
            nl.takeAt(0)
        if compact:
            lay.setDirection(QBoxLayout.TopToBottom)
            lay.addWidget(self.content, 1)
            lay.addWidget(self.nav)
            nl.setDirection(QBoxLayout.LeftToRight)
            nl.setContentsMargins(8, 6, 8, 6)
            for b in self.nav_buttons:
                nl.addStretch(1)
                nl.addWidget(b)
            nl.addStretch(1)
            self.nav.setMinimumSize(0, 62)
            self.nav.setMaximumSize(16777215, 62)
        else:
            lay.setDirection(QBoxLayout.LeftToRight)
            lay.addWidget(self.nav)
            lay.addWidget(self.content, 1)
            nl.setDirection(QBoxLayout.TopToBottom)
            nl.setContentsMargins(10, 18, 10, 18)
            nl.setSpacing(8)
            for b in self.nav_buttons:
                nl.addWidget(b, alignment=Qt.AlignHCenter)
            nl.addStretch(1)
            self.nav.setMinimumSize(72, 0)
            self.nav.setMaximumSize(72, 16777215)
        self.style_nav()

    def style_nav(self):
        edge = "border-top" if self.compact else "border-right"
        self.nav.setStyleSheet(f"QWidget#nav {{ background: {P['SURFACE']}; {edge}: 1px solid {P['BORDER']}; }}")

    def apply_theme(self, name: str):
        set_palette(name)
        QApplication.instance().setStyleSheet(build_style())
        self.style_nav()
        self.power.update()
        self.restart_btn.setIcon(make_icon("restart", P["TEXT"]))
        for b in self.nav_buttons + self.swatches:
            b.update()
        self.refresh_status()

    def on_theme_pick(self, key: str):
        core.CFG["theme"] = key
        core.save()
        self.apply_theme(key)

    def set_look(self, key: str, value: str):
        core.CFG[key] = value
        core.save()
        self.apply_theme(core.CFG["theme"])

    def pick_accent(self):
        col = QColorDialog.getColor(QColor(P["ACC1"]), self, "Цвет акцента")
        if col.isValid():
            self.set_look("accent", col.name())

    # ---------- состояние ----------
    def fade_in(self):
        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(220)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._fade.start()

    def switch_page(self, i: int):
        """Плавное появление страницы при переключении вкладки."""
        if i == self.stack.currentIndex():
            return
        self.stack.setCurrentIndex(i)
        w = self.stack.currentWidget()
        eff = QGraphicsOpacityEffect(w)
        w.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", w)
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
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
        self.tray.showMessage("Zapret GUI", text, QSystemTrayIcon.NoIcon, 1800)

    def on_log(self, text: str):
        line = f"{time.strftime('%H:%M:%S')}  {text}"
        self.log_history = (self.log_history + [line])[-300:]
        self.log_line.setText(text)
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
        self.tray.setToolTip("Zapret GUI: " + ("включено" if running else "выключено"))

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
        name = core.CFG["strategy"]
        if not name:
            return
        mode = core.start(name)
        self.bus.log.emit(f"Запущено: {name} ({mode})")
        QTimer.singleShot(1500, self.after_start)

    def after_start(self):
        err = core.start_error()
        if err and not self._bat_tried:  # прямой запуск не удался -> пробуем через .bat
            self._bat_tried = True
            self.bus.log.emit("Прямой запуск не удался, пробую через .bat…")
            core.start(core.CFG["strategy"], force_bat=True)
            QTimer.singleShot(2500, self.after_start)
            return
        self._bat_tried = False
        if err or not core.is_running():
            self.bus.log.emit("Обход не запустился: " + (err.replace("\n", " ") or "winws.exe не появился"))
            self.notify("Не удалось включить обход, подробности в окне")
        else:
            self.notify("Обход включён")
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

    # ---------- обновление приложения ----------
    def on_channel_changed(self, i: int):
        core.CFG["app_channel"] = "pre" if i == 1 else "stable"
        core.save()
        self.check_app_updates(manual=True)

    def save_app_repo(self):
        core.CFG["app_repo"] = self.app_repo_edit.text().strip()
        core.save()

    def set_app_busy(self, busy: bool):
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
                    self.bus.failed.emit(f"Не удалось проверить обновления приложения: {e}")
        core.bg(work)

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
            if core.CFG["app_auto_update"] and core.can_self_update():
                self.install_app(latest)
            else:
                self.bus.log.emit(f"Доступна новая версия приложения: {latest['version']}")
                self.notify(f"Доступна новая версия приложения: {latest['version']}")
        elif self._app_manual:
            self.bus.log.emit("Новых версий приложения нет" if not newer else f"Доступна версия {latest['version']}")

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
        core.CFG["resume_after_update"] = core.is_running()  # после перезапуска сам включим обход
        core.save()
        self.bus.log.emit("Перезапускаю приложение…")
        core.launch_updater(Path(path))
        self.quit_app()

    # ---------- профили ----------
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

    def on_profile_selected(self, cur, _prev):
        if cur is not None:
            self._cur_profile = cur.text()
            self.prof_editor.setPlainText(core.read_profile(cur.text()))

    def on_profile_toggled(self, item):
        core.set_enabled(item.text(), item.checkState() == Qt.Checked)
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
    def fill_sites(self):
        sites = core.CFG["sites"]
        self.table.setRowCount(len(sites))
        for i, s in enumerate(sites):
            self.table.setItem(i, 0, QTableWidgetItem(s["name"]))
            self.table.setItem(i, 1, QTableWidgetItem("—"))
            self.table.setItem(i, 2, QTableWidgetItem(""))
            b = QPushButton("✕")
            b.setObjectName("ghost")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, u=s["url"]: self.remove_site(u))
            self.table.setCellWidget(i, 3, b)

    def add_site(self):
        if core.add_site(self.site_input.text()):
            self.site_input.clear()
            self.fill_sites()
        else:
            self.bus.log.emit("Сайт пустой или уже есть в списке")

    def remove_site(self, url: str):
        core.remove_site(url)
        self.fill_sites()

    def check_all(self):
        sites = list(core.CFG["sites"])
        self.sites_btn.setEnabled(False)
        for i in range(len(sites)):
            self.table.item(i, 1).setText("проверяю…")
            self.table.item(i, 1).setForeground(QColor(P["MUTED"]))
            self.table.item(i, 2).setText("")

        def work():
            with ThreadPoolExecutor(max_workers=6) as ex:
                futs = [ex.submit(core.probe, s["url"]) for s in sites]
                for i, f in enumerate(futs):
                    self.bus.site.emit(i, sites[i]["url"], f.result())
            self.bus.sites_done.emit()
        core.bg(work)

    def on_site_result(self, i: int, url: str, res: dict):
        if i >= self.table.rowCount() or core.CFG["sites"][i]["url"] != url:
            return
        st, info = self.table.item(i, 1), self.table.item(i, 2)
        st.setText("Доступен" if res["ok"] else "Недоступен")
        st.setForeground(QColor(P["OK"] if res["ok"] else P["BAD"]))
        info.setText(f"{res['code']} · {res['ms']} мс" if res["ok"] else "нет ответа")

    # ---------- обновления / бэкапы / импорт ----------
    def set_busy(self, busy: bool):
        self.busy = busy
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

    def on_changed(self):
        self.set_busy(False)
        self.reload_all()

    def on_failed(self, msg: str):
        self.bus.log.emit(msg)
        self.btn_check.setEnabled(True)
        self.set_app_busy(False)
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
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
