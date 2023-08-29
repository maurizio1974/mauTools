import maya.cmds as cmds


def run(parent):
    """requires amTinyTools"""
    try:
        import amTinyTools
        amTinyTools.menuSelect(parent)
    except ImportError:
        cmds.confirmDialog(m="this module requires amTinyTools")
