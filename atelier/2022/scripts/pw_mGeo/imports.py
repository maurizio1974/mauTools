import maya.cmds as cmds

from functools import partial
import maya.OpenMaya as om
import maya.OpenMayaFX as omx
import maya.utils as utils
from time import gmtime, strftime
import time, datetime, sys, os, subprocess, shutil, re, getpass
import maya.OpenMayaUI as omui
import maya.mel as mel
import gc
import platform

# check maya version
support = 0
ver = int(cmds.about(file=True))
if 2010 < ver:# < 2014:
    support = 1#version OK
else:
    cmds.error('Maya version not support. Use 2011-2013')

#try import pyqt
qt = ''
try:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
    qt = 'qt'
except ImportError:
    try:
        from PySide.QtGui import *
        from PySide.QtCore import *
        qt = 'side'
    except ImportError:
        cmds.error('PyQt or PySide not found!!!')
#Load modules
#get maya window
def getMayaWindow(qt):
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        if qt: #PyQt
            return wrp(int(ptr), QObject)
        else: #PySide
            return wrp(int(ptr), QMainWindow)

if qt:
    if qt == 'qt':
        from . import mGeo_UI as ui
        from sip import wrapinstance as wrp
        qMayaWindow = getMayaWindow(True)
        from PyQt4.QtCore import QSettings as qset
    elif qt == 'side':
        from . import mGeo_UIs as ui
        from shiboken import wrapInstance as wrp
        qMayaWindow = getMayaWindow(False)
        from  PySide.QtCore import QSettings as qset
