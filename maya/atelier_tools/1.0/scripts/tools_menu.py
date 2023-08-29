'''----------------------------------------------------------------------

ATELIER MAYA MENU

Date = 23/01/2023
User = Maurizio Giglioli
Update =
        23/01/2023 Initial Commit
----------------------------------------------------------------------'''

import os
import sys
import maya.mel as mel
import maya.cmds as cmds



def sourceMel(script, command=None):
    cmd = ''
    dirname, filename = os.path.split(os.path.abspath(__file__))
    melLoc = os.path.join(dirname, 'mel', script)
    melLoc = r"{}".format(melLoc).replace('\\', '/').replace('//', '/')
    if command:
        cmd = 'source "' + melLoc + '";' + command + '();'
    else:
        cmd = 'source "' + melLoc + '";'
    # print cmd
    mel.eval(cmd)


def atelierMayaMenu():
    # main_window = pm.language.melGlobals['gMainWindow']
    main_window = mel.eval('$tempVar = $gMainWindow')

    menu_obj = 'Atelier'
    menu_label = 'Atelier Tools'

    # CHECK MENU
    if cmds.menu(menu_obj, l=menu_label, exists=True, p=main_window):
        cmds.deleteUI(cmds.menu(menu_obj, e=True, deleteAllItems=True))

    # MAIN MENU
    custom_tools_nemu = cmds.menu(
        menu_obj, l=menu_label, p=main_window, tearOff=True)
    # MODEL CHECKER
    cmds.menuItem(
        l='VFX Model Check List',
        c='from modelChecker import modelChecker_UI;import importlib;importlib.reload(modelChecker_UI);modelChecker_UI.UI.show_UI()',
        p=custom_tools_nemu)
    # MAIN QUALITY CHECK
    cmds.menuItem(
        l='VFX Quality Assurance',
        c='import qualityAssurance.ui;import importlib;importlib.reload(qualityAssurance.ui);qualityAssurance.ui.show("atelier")',
        p=custom_tools_nemu)

    # SCENE MANAGER
    cmds.menuItem(
        l='Atelier SCENE TOOLS',
        c='import atelier_Scene;import importlib;importlib.reload(atelier_Scene);atelier_Scene.tlAvfxTools(True)',
        p=custom_tools_nemu)

    # SUBMENUS
    ass = cmds.menuItem(l='--- ASSETS ---', subMenu=True,
                        p=custom_tools_nemu, tearOff=True)
    model = cmds.menuItem(l='Model', subMenu=True,
                          p=custom_tools_nemu, tearOff=True)
    anim = cmds.menuItem(l='Animation', subMenu=True,
                         p=custom_tools_nemu, tearOff=True)
    look = cmds.menuItem(l='Look-Dev', subMenu=True,
                         p=custom_tools_nemu, tearOff=True)
    utility = cmds.menuItem(l='Utility', subMenu=True,
                            p=custom_tools_nemu, tearOff=True)
    about = cmds.menuItem(l='About', subMenu=False,
                          p=custom_tools_nemu, tearOff=False)
    # MAKE TOOL MENUS
    assetTools(ass)
    modelTools(model)
    animTools(anim)
    lookDevTools(look)
    utilityTools(utility)
    # ADD COMMANDS TO UI
    cmds.menuItem(about, e=True, c='tools_menu.aboutTool()')


def aboutTool():
    msg = 'Version 1.0'
    msg += '''
-------------------------------------------------------------------------
    1.0: 23/01/2023
    - First Release
-------------------------------------------------------------------------
    '''
    cmds.confirmDialog(t='Atelier Tools', b=['Cool'], m=msg)

def assetTools(parent):
    user = os.getlogin()
    cmds.menuItem(
        l='Update Assets',
        c='import mayaAssets;import importlib;importlib.reload(mayaAssets);mayaAssets.checkUpdate()',
        p=parent)
    cmds.menuItem(d=True, p=parent)
    cmds.menuItem(
        l='Switch Assets to Proxy',
        c='import mayaAssets;import importlib;importlib.reload(mayaAssets);mayaAssets.proxySwitch(0)',
        p=parent)
    cmds.menuItem(
        l='Switch Assets to High',
        c='import mayaAssets;import importlib;importlib.reload(mayaAssets);mayaAssets.proxySwitch(1)',
        p=parent)
    # ASSETS MENU ITEMS
    cmds.menuItem(d=True, p=parent)
    cmds.menuItem(
        l='Project Switcher',
        c='import mayaProjects;import importlib;importlib.reload(mayaProjects);mayaProjects.prjs_UI()',
        p=parent)
    if user == 'mgiglioli' or user == 'tlhomme':
        cmds.menuItem(
            l='RE-Build Project Switcher',
            c='import mayaProjects;import importlib;importlib.reload(mayaProjects);mayaProjects.prjs_UI(True)',
            p=parent)
    cmds.menuItem(
        l='Asset Picker',
        c='import mayaAssets;import importlib;importlib.reload(mayaAssets);mayaAssets.assets_UI()',
        p=parent)


def utilityTools(parent):
    # UTILITY MENU ITEMS
    cmds.menuItem(
        l='VFX Renamer',
        c='import atelier_Renamer;import importlib;importlib.reload(atelier_Renamer);atelier_Renamer.atelier_UI()',
        p=parent)

def modelTools(parent):
    # MODEL MENU ITEMS
    cmds.menuItem(
        l='Make Model Export Set',
        c='import atelier_utils;import importlib;importlib.reload(atelier_utils);atelier_utils.makeExportSet()',
        p=parent)
    cmds.menuItem(d=True, p=parent)
    cmds.menuItem(
        l='Rock Gen 1.0',
        c='import tools_menu;import importlib;importlib.reload(tools_menu);tools_menu.sourceMel("rockGen.mel", "rockGen")', p=parent)


def lookDevTools(parent):
    cam = cmds.menuItem(l='Camera', subMenu=True, p=parent, tearOff=True)
    # CAMERA MENU ITEMS
    cmds.menuItem(
        l='Full Camera Res',
        c='import atelier_utils;import importlib;importlib.reload(atelier_utils);atelier_utils.setCameraRes(True)',
        p=cam)
    cmds.menuItem(
        l='Half Camera Res',
        c='import atelier_utils;import importlib;importlib.reload(atelier_utils);atelier_utils.setCameraRes(False)',
        p=cam)
    # LOOK-DEV MENU ITEMS
    cmds.menuItem(
        l='Build/Update Operator setup in Shot',
        c='import lookdev_utils;import importlib;importlib.reload(lookdev_utils);lookdev_utils.operatorShot_setup()',
        p=parent)
    cmds.menuItem(
        l='Set operators for Namespace in shot',
        c='import lookdev_utils;import importlib;importlib.reload(lookdev_utils);lookdev_utils.setShaderForShot()',
        p=parent)
    cmds.menuItem(d=True, p=parent)
    cmds.menuItem(
        l='Fix Cryptomatte AOVs in this shot',
        c='import lookdev_utils;import importlib;importlib.reload(lookdev_utils);lookdev_utils.fixCryptomatte()',
        p=parent)


def animTools(parent):
    cmds.menuItem(
        l='Key Frame Reduction',
        c='import keyframeReduction.ui;keyframeReduction.ui.show()', p=parent)
    cmds.menuItem(l='Cache Tool',
                  c='import atelier_cacheTools;import importlib;importlib.reload(atelier_cacheTools);atelier_cacheTools.atelier_ToolsUI()', p=parent)