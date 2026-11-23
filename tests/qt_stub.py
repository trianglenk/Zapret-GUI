"""Заглушка Qt: позволяет проверять Python-логику приложения без настоящего Qt (см. test_ui_logic.py)."""
import sys


class DMeta(type):
    def __getattr__(cls, n):
        if n.startswith("__"):
            raise AttributeError(n)
        return D()


class D(metaclass=DMeta):
    def __init__(self, *a, **k): pass
    def __getattr__(self, n):
        if n.startswith("__"):
            raise AttributeError(n)
        if n == "count":          # циклы вида while layout.count() должны заканчиваться
            return lambda: 0
        return D()
    def __call__(self, *a, **k): return D()
    def __iter__(self): return iter(())
    def __bool__(self): return True
    def __lt__(self, o): return False
    __le__ = __gt__ = __ge__ = __lt__
    def __mul__(self, o): return D()
    __rmul__ = __add__ = __radd__ = __sub__ = __rsub__ = __truediv__ = __rtruediv__ = __mul__
    def __neg__(self): return D()
    def __or__(self, o): return D()
    def __int__(self): return 0
    def __float__(self): return 0.0
    def __index__(self): return 0
    def __format__(self, spec): return "D"
    def __str__(self): return "D"


class Signal:
    def __init__(self, *a): self.cbs = []
    def connect(self, f): self.cbs.append(f)
    def emit(self, *a):
        for f in list(self.cbs):
            f(*a)


class _QTimer(D):
    @staticmethod
    def singleShot(ms, fn): pass


NAMES = """QAbstractButton QAction QApplication QBoxLayout QButtonGroup QCheckBox QColor QColorDialog QComboBox
QEasingCurve QFileDialog QFrame QGraphicsDropShadowEffect QGraphicsOpacityEffect QGridLayout QHBoxLayout QIcon
QInputDialog QLabel QLineEdit QLinearGradient QListWidget QListWidgetItem QLocalServer QLocalSocket QMainWindow
QMenu QMessageBox QObject QPainter QPainterPath QPen QPixmap QPlainTextEdit QPointF QPropertyAnimation QPushButton QRectF
QScrollArea QSize QSlider QStackedWidget QSystemTrayIcon QVariantAnimation QVBoxLayout QWidget QFont""".split()
mod = sys.modules[__name__]
for n in NAMES:
    setattr(mod, n, type(n, (D,), {}))
Qt = D()
QTimer = _QTimer
QT_API = "stub"

def __getattr__(name):
    if name.startswith('__'):
        raise AttributeError(name)
    obj = type(name, (D,), {})
    globals()[name] = obj
    return obj

