'''-------------------------------------------------------------------------

        MINIMO ARNOLD AOVS IN RENDER WINDOW

        Date = 24-02-2015
        User = Maurizio Giglioli
        info = Show actives AOVS in the maya render window,
        Update = (24-02-2015)
                First release.

----------------------------------------------------------------------------'''

import maya.cmds as cmds
import mtoa.aovs as aovs
import os


def aovUI():
    if cmds.objExists('defaultArnoldRenderOptions.aovMode'):
        if cmds.getAttr("defaultArnoldRenderOptions.aovMode") == 0:
            cmds.confirmDialog(
                t='Error',
                m='AOVS in the render settings are not enabled')
            return
        if cmds.flowLayout('renderViewToolbar', q=True, ex=True):
            if cmds.optionMenu('aovsListMenu', q=True, ex=True):
                if cmds.optionMenu('aovsListMenu', q=True, ils=True):
                    for i in cmds.optionMenu('aovsListMenu', q=True, ils=True):
                        cmds.deleteUI(i)
                cmds.deleteUI('aovsListMenu')
            cmds.optionMenu(
                'aovsListMenu',
                h=25,
                l='AOVs',
                cc=loadAOV,
                p='renderViewToolbar'
                )
            activeAOVS, aovsNames = [], []
            ao = aovs.AOVInterface().getAOVNodes(names=True)
            for i in range(0, len(ao)):
                activeAOVS.append(ao[i][1])

            for a in activeAOVS:
                aovsNames.append(a.split('aiAOV_')[-1].replace('1', ''))

            # activeAOVS = cmds.ls(et='aiAOV')
            # aovsNames = [i.split('_', 1)[1] for i in activeAOVS]

            cmds.menuItem(l='beauty')

            for item in aovsNames:
                if item != 'beauty':
                    cmds.menuItem(l=item)


def loadAOV(*args):
    activeAOVS = cmds.ls(et='aiAOV')
    aovsNames = [i.split('_', 1)[1] for i in activeAOVS]

    if activeAOVS == []:
        cmds.warning("No aov's setup")
    else:
        CurrentProject = cmds.workspace(q=1, fullName=1)
        rview = cmds.getPanel(sty='renderWindowPanel')
        selectedAOV = cmds.optionMenu('aovsListMenu', q=1, v=1)

        ImgTempPath = CurrentProject + '/images/tmp/'
        latest_file = max(all_files_under(ImgTempPath), key=os.path.getmtime)
        # splitPath = latest_file.replace('/', '\\')
        splitPath = latest_file.replace('/', '/')

        splitPath = splitPath.split(os.sep)

        for n, i in enumerate(splitPath):
            if i in aovsNames or i == 'beauty':
                splitPath[n] = selectedAOV

        splitPath[0] = splitPath[0] + '\\'
        pathToImg = reduce(os.path.join, splitPath)

        # print pathToImg
        cmds.renderWindowEditor(rview, e=True, li=pathToImg)


def all_files_under(path):
    for cur_path, dirnames, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(cur_path, filename)
