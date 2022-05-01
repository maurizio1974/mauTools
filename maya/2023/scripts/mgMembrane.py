import maya.cmds as cmds
import maya.mel as mel

mel.eval('source "createMembrane.mel"')
def mgMembrane(geo):
    for f in geo:
        sh = cmds.listRelatives(f, f = True, s = True)
        cmds.select(cl = True)
        cmds.select(f)
        mem = mel.eval('createMembrane')
        cmds.setAttr(mem[0]+'.gravity', 0)
        cmds.setAttr(mem[0]+'.collide', 0)
        baseSh = cmds.listConnections(mem[0]+'.inputMesh')
        shM = cmds.listRelatives(baseSh[0], f = True, s = True)
        cmds.parent(shM[0],f, r = True, s = True)
        cmds.delete(baseSh)
 
