try:
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from PySide2.QtUiTools import QUiLoader
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6.QtGui import *
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtUiTools import QUiLoader
    from shiboken6 import wrapInstance
