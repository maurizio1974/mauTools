'''menuData
act={name:Export Channels to Houdini,action:show()}
'''
'''moduleInfo
Export channels to Houdini *.clip file
'''
'''
Maya to Houdini Channel exporter
author: paulWinex
sile: paulwinex.ru

This script save maya animation channels to houdini .clip file.
You can load .clip file via fileCHOP.

Usage
import pw_MayaToHoudiniChannelExport
pw_MayaToHoudiniChannelExport.show()
'''
from .mayaqtimport import *
# import mayaqtimport 

from . import channelExportWindow
import importlib
importlib.reload(channelExportWindow)

def getMayaWindow():
    ptr = mayaqtimport.omui.MQtUtil.mainWindow()
    if ptr is not None:
        return wrp(int(ptr), QMainWindow)

wind = channelExportWindow.channelExporterWindowClass(getMayaWindow())
def show():
    wind.show()
