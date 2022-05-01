import os
import sys
import mWild as mW
import mSuperCB
import mFixUndo
# import mauUtility as mU
from maya import mel, cmds, utils


def plugInCheck(plugs=None):
    if not plugs:
        plugs = ['MMtoKey', 'AbcImport', 'AbcEmport', 'gpuCache', 'mtoa']
    for p in plugs:
        state = cmds.pluginInfo(p, q=True, l=True)
        if not state:
            try:
                cmds.loadPlugin(p)
                print('Loaded plugin: ' + p)
            except:
                continue


utils.executeDeferred(mW.mSetWild)
# EXTRA CHANNEL BOX TOOLS
utils.executeDeferred(mSuperCB.superCB)
# FIX UNDO
utils.executeDeferred(mFixUndo.check_undo)


'''
from SEAutoSave import AutoSave, AutoSaveCallback
utils.executeDeferred(AutoSaveCallback().register)
'''


# print '=' * 500
# print 'Mau Environment Loaded'
# print '=' * 500
