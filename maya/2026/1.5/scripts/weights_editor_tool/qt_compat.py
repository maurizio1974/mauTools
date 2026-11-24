"""
Qt compatibility layer.

Maya 2025+ (including 2026.x) ships PySide6 / Qt6, older versions ship PySide2 / Qt5.
Every module in the tool imports Qt from here so the same code runs on both.
"""

try:
    from PySide6 import QtCore, QtGui, QtWidgets, QtNetwork
    import shiboken6 as shiboken
    QT_VERSION = 6
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets, QtNetwork
    import shiboken2 as shiboken
    QT_VERSION = 5


if QT_VERSION == 6:
    # These classes moved from QtWidgets to QtGui in Qt6.
    # Alias them back so existing `QtWidgets.QAction` style calls keep working.
    for _name in ("QAction", "QActionGroup", "QShortcut", "QUndoStack", "QUndoCommand", "QUndoGroup"):
        if not hasattr(QtWidgets, _name) and hasattr(QtGui, _name):
            setattr(QtWidgets, _name, getattr(QtGui, _name))


def to_int(value):
    """
    Converts Qt enums, flags and key combinations to a plain int.
    PySide6 uses real Python enums which no longer behave like ints.
    """
    if value is None:
        return 0
    if isinstance(value, int):
        return int(value)
    if hasattr(value, "toCombined"):  # QKeyCombination (Qt6)
        return int(value.toCombined())
    if hasattr(value, "value"):  # Python enum (PySide6)
        return int(value.value)
    return int(value)


def key_event_code(event):
    """
    Returns key | modifiers of a QKeyEvent as an int.
    """
    return to_int(event.key()) | to_int(event.modifiers())


def mouse_event_pos(event):
    """
    Returns a QMouseEvent's local position as a QPoint.
    QMouseEvent.pos()/x()/y() are deprecated in Qt6.
    """
    if hasattr(event, "position"):
        return event.position().toPoint()
    return event.pos()


def wrap_instance(ptr, base=None):
    return shiboken.wrapInstance(int(ptr), base or QtWidgets.QWidget)


def is_valid(obj):
    return shiboken.isValid(obj)


def exec_dialog(obj, *args):
    """
    Calls exec() on dialogs and menus (exec_ is deprecated in PySide6).
    """
    if hasattr(obj, "exec"):
        return obj.exec(*args)
    return obj.exec_(*args)


def text_width(font_metrics, text):
    if hasattr(font_metrics, "horizontalAdvance"):
        return font_metrics.horizontalAdvance(text)
    return font_metrics.width(text)
