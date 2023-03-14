import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.mel as mel

# check maya version
support = 0
ver = int(cmds.about(file=True, version=True))
if 2010 < ver:# < 2014:
    support = 1#version OK
else:
    cmds.error('Maya version not support. Use 2011<')

#try import PyQt or PySide
qt = 0
try:
    import PyQt4
    qt = 1
except ImportError:
    try:
        import PySide2
        qt = 2
    except ImportError:
        print('ERRRRRORRRR '* 10)

if not qt:
    cmds.error('NO PYQT or PYSIDE')
elif qt ==1:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
    from sip import wrapinstance as wrp
    qtsignal = pyqtSignal
    def getMayaWindow():
        ptr = omui.MQtUtil.mainWindow()
        if ptr is not None:
            return wrp(int(ptr), QObject)

elif qt ==2:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance as wrp
    qtsignal = Signal
    def getMayaWindow():
        ptr = omui.MQtUtil.mainWindow()
        if ptr is not None:
            return wrp(int(ptr), QMainWindow)

def qControl(mayaName, qobj=None):
    if not qobj:
        qobj = QObject
    ptr = omui.MQtUtil.findControl(mayaName)
    if ptr is None:
        ptr = omui.MQtUtil.findLayout(mayaName)
    if ptr is None:
        ptr = omui.MQtUtil.findMenuItem(mayaName)
    return wrp(int(ptr), qobj)

qMaya = getMayaWindow()
qApp = QApplication.instance()
