"""Qt binding shim: PySide6 (Maya 2025+) or PySide2 (Maya 2022-2024).

    from .qt import QtCore, QtGui, QtWidgets, QtQuickWidgets, QtQml

Everything else in the package imports Qt through here, so the rest of the code is binding
agnostic. The handful of API differences that matter to NodeX are wrapped below.
"""
try:
    from PySide6 import QtCore, QtGui, QtQml, QtQuickWidgets, QtWidgets
    from shiboken6 import wrapInstance, isValid
    QT6 = True
except ImportError:
    from PySide2 import QtCore, QtGui, QtQml, QtQuickWidgets, QtWidgets
    from shiboken2 import wrapInstance, isValid
    QT6 = False

QT_MAJOR = 6 if QT6 else 5

# Classes Qt 6 moved from QtWidgets to QtGui.
QAction = QtGui.QAction if QT6 else QtWidgets.QAction
QActionGroup = QtGui.QActionGroup if QT6 else QtWidgets.QActionGroup
QShortcut = QtGui.QShortcut if QT6 else QtWidgets.QShortcut


def ival(v):
    """An enum / flag as a plain int. PySide6 enums are Python enums: int() fails on flags
    (Qt.KeyboardModifier, Qt.MouseButton...), `.value` works on both bindings' enums."""
    if isinstance(v, int):
        return int(v)
    value = getattr(v, "value", None)
    if isinstance(value, int):
        return value
    return int(v)


def exec_(obj, *args):
    """QDialog / QMenu / QEventLoop exec: `exec` in PySide6, `exec_` in PySide2."""
    fn = getattr(obj, "exec", None) or getattr(obj, "exec_")
    return fn(*args)
