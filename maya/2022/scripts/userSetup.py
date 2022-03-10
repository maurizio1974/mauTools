import os
import sys
import fixUndo
import mWild as mW
# import mauUtility as mU
from maya import mel, cmds, utils


def plugInCheck():
    plugs = ['MMtoKey', 'AbcImport', 'gpuCache', 'mtoa']
    for p in plugs:
        state = cmds.pluginInfo(p, q=True, l=True)
        if not state:
            try:
                cmds.loadPlugin(p)
                print 'Loaded plugin: ' + p
            except:
                continue


utils.executeDeferred(mW.mSetWild)
utils.executeDeferred(fixUndo.check_undo)
'''
from SEAutoSave import AutoSave, AutoSaveCallback
utils.executeDeferred(AutoSaveCallback().register)
'''


# print '=' * 500
# print 'Mau Environment Loaded'
# print '=' * 500
