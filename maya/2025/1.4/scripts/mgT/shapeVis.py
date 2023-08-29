import maya.cmds as cmds
import maya.mel as mel

def shapeVis():
    
    sel = cmds.ls( sl = True )
    for e in sel:
        shape = cmds.listRelatives( e, s = True )
        if cmds.getAttr( shape[0]+'.visibility' ) == 0:
            cmds.setAttr( shape[0]+'.visibility', 1 )
        else:
            cmds.setAttr( shape[0]+'.visibility', 0 )
    
    cmds.select( sel )

