"""Обёртка над Qt (PySide6). Остальной код импортирует всё отсюда."""
from PySide6.QtCore import *      # noqa: F401,F403
from PySide6.QtGui import *       # noqa: F401,F403
from PySide6.QtWidgets import *   # noqa: F401,F403
from PySide6.QtNetwork import QLocalServer, QLocalSocket  # noqa: F401
QT_API = "PySide6"
