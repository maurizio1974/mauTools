import maya.cmds as cmds
import maya.mel as mel

def isolateMG(dir):
    sel = ['']
    sel = cmds.ls(sl=True)
    # GET THE VIEW IN FOCUS AND THE TIPE OF PANEL
    currentPanel = cmds.getPanel(vis=True)
    for eP in currentPanel:
        panelType = cmds.getPanel(to=eP)
        if panelType == 'modelPanel':
            # ISOLATE THE CURRENT SELECTION
            if dir == 0:
                if cmds.isolateSelect(eP, q=True, s=True) == 0:
                    mel.eval('enableIsolateSelect ' + eP + ' 1')
                    cmds.isolateSelect(eP, s=1)
                    #mel.eval( 'isoSelectAutoAddNewObjs '+currentPanel+' 1' )
                else:
                    if len(sel) == 0:
                        cmds.isolateSelect(eP, s=0)
                    else:
                        cmds.isolateSelect(eP, s=0)
                        mel.eval('enableIsolateSelect ' + eP + ' 1')
                        cmds.isolateSelect(eP, s=1)
            # ADD THE CURRENT SELECTION TO THE ACTIVE ISOLATION
            if dir == 1:
                if cmds.isolateSelect(eP, q=True, s=True) == 1:
                    cmds.isolateSelect(eP, addSelected=True)
            # REMOVE THE CURRENT SELECTION TO THE ACTIVE ISOLATION
            if dir == 2:
                if cmds.isolateSelect(eP, q=True, s=True) == 1:
                    cmds.isolateSelect(eP, rs=True )
