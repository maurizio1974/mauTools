import sys
import maya.cmds as cmds
import maya.mel as mel

if '/mpc/people/maurizio-g/maya/scripts/utility/' is not (sys.path):sys.path.append('/mpc/people/maurizio-g/maya/scripts/utility/')
if '/mpc/people/maurizio-g/maya/scripts/flipper/' is not (sys.path):sys.path.append('/mpc/people/maurizio-g/maya/scripts/flipper/')  

import mgTireAnimCRV
reload(mgTireAnimCRV)
import curveMG
reload(curveMG)


def allTirePlot():
    asset = cmds.optionMenu('tireAnimOM', q = True, v = True)
    transforms = mel.eval('mgGetTire("'+asset+'")')
    
    for t in transforms:
        path = curveMG.curveMG(t)
        rollP = mgTireAnimCRV.makeTireRoll(path)
        moveR = mgTireAnimCRV.makeMP(rollP)
        mgTireAnimCRV.bakeTireRoll(moveR)
    
