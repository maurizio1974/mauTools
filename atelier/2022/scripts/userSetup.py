import os
import sys
# mp = 'C:/Users/mgiglioli/Documents/maya/extra/mauTools/1.4/scripts'
# pp = [ 'mgT', 'pro', 'extra_Libs' ]
# for p in pp:
#     cur = os.path.join(mp, p)
#     if cur not in sys.path:
#         sys.path.append(cur)
import mWild as mW
import mSuperCB
import mFixUndo
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


utils.executeDeferred(mW.mSetWild)
# mW.mSetWild()
# EXTRA CHANNEL BOX TOOLS
utils.executeDeferred(mSuperCB.superCB)
# mSuperCB.superCB()
# FIX UNDO
# utils.executeDeferred(mFixUndo.check_undo)
# mFixUndo.check_undo()

# plugInCheck()


'''
from SEAutoSave import AutoSave, AutoSaveCallback
utils.executeDeferred(AutoSaveCallback().register)
'''


print('=' * 500)
print('Mau Environment Loaded')
print('=' * 500)
