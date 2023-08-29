import os
import sys
import mWild as mW
import mSuperCB
import mFixUndo
import mayaProjects
import mauUtility as mU
from importlib import reload
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


def setPaths():
    base = os.path.join(os.getenv('MIMMO_SW'), 'mauTools/WIN', os.getenv('MAYA_VERSION'), os.getenv('mt_V'), 'scripts')
    # print(base)
    locs = ['mgT', 'pro', 'extra_Libs']
    for l in locs:
        cur = os.path.join(base, l).replace('\\', '/')
        # print(cur)
        if cur not in sys.path:
            os.sys.path.append(cur)



# CREATE PROJECT SWITCHER
utils.executeDeferred(mayaProjects.prjs_UI)
# MAIN UI TWEAKS
utils.executeDeferred(plugInCheck)
utils.executeDeferred(mW.mSetWild)
# EXTRA CHANNEL BOX TOOLS
utils.executeDeferred(mSuperCB.superCB)
# FIX UNDO
# utils.executeDeferred(mFixUndo.check_undo)


# from SEAutoSave import AutoSave, AutoSaveCallback
# utils.executeDeferred(AutoSaveCallback().register)
# print('=' * 500)
# print('Mau Environment Loaded')
# print('=' * 500)
