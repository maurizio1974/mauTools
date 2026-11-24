import os
from .UtilsPyside import *
from maya import cmds, OpenMayaUI as omui


version = "1.3"
parent = cmds.columnLayout(p=cmds.window())		# empty hidden layout for temp parenting
location = os.path.dirname(__file__)


def wrapWidget(name="MayaWindow"):
    """wrap maya widget into QWidget shell"""
    return wrapInstance(int(omui.MQtUtil.findControl(name)), QWidget)


def wrapWidgetType(name="MayaWindow", widget_type=QMainWindow):
    """wrap maya widget into QWidget shell"""
    return wrapInstance(int(omui.MQtUtil.findControl(name)), widget_type)


def createWidget(function, *args, **kwargs):
    """create maya widget as QWidget"""
    return wrapInstance(int(omui.MQtUtil.findControl(function(*args, **kwargs))), QWidget)


def createWidgetType(function, widget_type=QMainWindow, *args, **kwargs):
    """create maya widget as QWidget"""
    return wrapInstance(int(omui.MQtUtil.findControl(function(*args, **kwargs))), widget_type)


def loadUI(ui_file, directory=None, parent_widget=None):
    """load .ui file as a QWidget"""
    loader = QUiLoader()
    directory = directory or os.path.dirname(ui_file)
    loader.setWorkingDirectory(QDir(directory))
    return loader.load(ui_file, parent_widget)      # parent widget are good for QMainWindow only


def reloadWidget(widget_name, widget=None):
    """remove copies of widget with similar names"""
    while cmds.control(widget_name, q=True, ex=True):
        cmds.deleteUI(widget_name)
    if widget:
        widget.setObjectName(widget_name)


def removeWidgets(*widget_names):
    """remove all widgets by selected names"""
    for widget_name in widget_names:
        while cmds.control(widget_name, q=True, ex=True):
            cmds.deleteUI(widget_name)


def about(version):
    """show parent info"""
    window = QMainWindow(wrapWidget())
    reloadWidget(version.name + "About", window)
    window.setWindowTitle("About")
    window.setWindowFlags(Qt.Tool)
    window.setFixedSize(180, 160)
    title = QTextEdit(window)
    title.setGeometry(10, 10, 160, 110)
    title.setText("%s\nv%s\n\n%s" % (version.name, version.version, version.vendor))
    title.setReadOnly(True)
    button = QPushButton(window)
    button.setText("apply")
    button.setGeometry(50, 130, 80, 20)
    button.released.connect(lambda: cmds.deleteUI(window.objectName()))
    window.show()
