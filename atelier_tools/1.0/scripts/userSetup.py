import sys
import maya.cmds as cmds


def plugInCheck():
    plugs = ['AbcExport', 'AbcImport', 'gpuCache', 'mtoa']
    for p in plugs:
        state = cmds.pluginInfo(p, q=True, l=True)
        if not state:
            try:
                cmds.loadPlugin(p)
                print('Loaded plugin: ' + p)
            except:
                continue


cmds.evalDeferred("plugInCheck()")
cmds.evalDeferred(
    "import tools_menu;import importlib;importlib.reload(tools_menu);tools_menu.atelierMayaMenu()")
cmds.evalDeferred(
    "import mayaProjects;import importlib;importlib.reload(mayaProjects);mayaProjects.prjs_UI()")
