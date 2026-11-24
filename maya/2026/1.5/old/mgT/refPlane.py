import maya.cmds as cmds
import maya.mel as mel
import string

def refPl(switch):

    sel = cmds.ls(sl=1)
    aXis = cmds.radioButtonGrp('XYZradioGrp', q=1, sl=1)
    aXe = ''
    value = 0
    plane = 'frpTMP'

    if cmds.objExists(plane):
        cmds.delete(plane)
    if aXis == 1:
        aXe = ".rotateY"
        value = 90
    if aXis == 2:
        aXe = ".rotateX"
        value = 90
    if aXis == 3:
        aXe = ".rotateZ"
        value = 90

    if switch == 0 and not cmds.objExists(plane) and len(aXe) != 0:
        cmds.polyPlane(n=plane, w=1, h=1, sx=1, sy=1,
                       ax=[0, 0, 1], cuv=2, ch=0)
        cmds.setAttr('frpTMP' + aXe, value)
        cmds.setAttr(plane + 'Shape.overrideEnabled', 1)
        cmds.setAttr(plane + 'Shape.overrideLevelOfDetail', 1)
        cmds.select(clear=1)
    if switch == 1 and cmds.objExists(plane):
        cmds.delete(plane)

        cmds.select(clear=1)

        # RESTORE THE ORIGINAL SELECTION
    if type(sel).__name__ != 'NoneType' and len(sel) != 0:
        cmds.select(sel)
