"""Обёртка над Qt: PySide6 (Windows 10/11) или PySide2 (Windows 7, Qt 5.15).
Остальной код импортирует всё отсюда и не зависит от версии Qt."""
try:
    from PySide6.QtCore import *      # noqa: F401,F403
    from PySide6.QtGui import *       # noqa: F401,F403
    from PySide6.QtWidgets import *   # noqa: F401,F403
    from PySide6.QtNetwork import QLocalServer, QLocalSocket  # noqa: F401
    QT_API = "PySide6"
except ImportError:
    from PySide2.QtCore import *      # noqa: F401,F403
    from PySide2.QtGui import *       # noqa: F401,F403
    from PySide2.QtWidgets import *   # noqa: F401,F403
    from PySide2.QtNetwork import QLocalServer, QLocalSocket  # noqa: F401
    QT_API = "PySide2"
