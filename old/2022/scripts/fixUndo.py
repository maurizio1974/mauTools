from maya import cmds
from PySide2 import QtCore
# from pymel import core as pm
from maya import OpenMaya as om


def switchUndo():
    if not cmds.undoInfo(q=True, state=True):
        cmds.undoInfo(state=True)
        print('Undo Turned back on')


def check_undo():
    # om.MGlobal.executeCommandOnIdle('''if(!`undoInfo -q -state`) warning("Undo is turned off");''')
    om.MGlobal.executeCommandOnIdle('''if(!`undoInfo -q -state`) python("fixUndo.switchUndo()");''')
    QtCore.QTimer.singleShot(500, check_undo)


# check_undo()
