import maya.cmds as cmds
import maya.mel as mel

def xrayer(value):
    
    # GET THE VIEW WITH FOCUS AND THE TYPE OF PANEL
    currentPanel = cmds.getPanel(wf=True)
    panelType = cmds.getPanel(to=currentPanel)
    
    # GET SELECTION
    sel = cmds.ls(sl = True)
    
    if value == 1:
        if len(sel) == 0:
            if cmds.modelEditor (currentPanel, q = True, xray = True ) == 0:
                cmds.modelEditor ( currentPanel, e = True, xray =  1 )
            else:
                cmds.modelEditor ( currentPanel, e = True, xray =  0 )
        else:
            for eP in sel:
                dispInf = cmds.displaySurface ( eP, q = True, xRay = True )
                if dispInf[0] == 0:
                    cmds.displaySurface ( eP, xRay = 1 )
                else:
                    cmds.displaySurface ( eP, xRay = 0 )
    
    # RESET THE xRAY VALUES
    if value == 2:
        cmds.select( cl = True )
        sels = cmds.ls( typ = 'mesh')
                
        for eS in sels:
            cmds.displaySurface ( eS, xRay = 0 )
            
    cmds.modelEditor( currentPanel, e = True,xray = 0 )

        
    # RESTORE SELECTION
    if len(sel) != 0 :
        cmds.select( sel )
    
