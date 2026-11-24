''' ---------------------------------------------------------------------------

 PROJECT THE VOLUME OF A MESH TO ANOTHER ONE
 CREATING A SET OR JUST SELECT THE POLYS
 usage:
    select the full object you want to get the selection transfer on ,
    then the smaller object we want to use to create  the selection.
    finaly run the procedure
----------------------------------------------------------------------------'''

import maya.cmds as cmds
import time


def transferSelection(radius):
    start = time.clock()
    sel = cmds.ls(sl=True)
    if cmds.pluginInfo('SOuP.so', q=True, l=False):
        cmds.loadPlugin('SOuP.so')

    if len(sel) == 2:
        cmds.select(cl=True)
        sh1 = cmds.listRelatives(sel[0], s=True)
        sh2 = cmds.listRelatives(sel[1], s=True)
        outSel = []
        groupN = cmds.createNode('group')
        boundN = cmds.createNode('boundingObject')
        boundNs = cmds.listRelatives(boundN, p=True)
        cond = [
            len(sh1[0]) > 0,
            cmds.nodeType(sh1[0]) == 'mesh',
            len(sh2[0]) > 0,
            cmds.nodeType(sh2[0]) == 'mesh',
        ]
        if all(cond):
            cmds.connectAttr(sel[0] + '.worldMesh', groupN + '.inGeometry')
            cmds.connectAttr(
                boundN + '.outData', groupN + '.boundingObjects[0]'
            )
            cmds.connectAttr(
                boundN + '.outParentMatrix',
                groupN + '.boundingObjects[0].boundParentMatrix'
            )
            cmds.connectAttr(sel[1] + '.worldMesh', boundN + '.inMesh')
            cmds.setAttr(boundN + '.type', 3)
            cmds.setAttr(boundN + '.pointRadius', radius)

            transfer = cmds.getAttr(groupN + '.outComponents')
            for t in transfer:
                outSel.append(sel[0] + '.' + t)
            cmds.delete(groupN, boundN, boundNs)
            if len(outSel) > 0:
                cmds.select(outSel)
            elapsed = (time.clock() - start)
            print(elapsed)
            return outSel
        else:
            raise Exception
    else:
        raise Exception
