"""
-------------------------------------------------------------------------
 Author : Maurizio Giglioli
 Date   : 03/05/2010
 Python port for Maya 2026.
 update : 17/11/2026
        - ported to python

 Notes :
     Fixes local space values on the selected transform nodes:
     freezes translate / scale and moves the translation onto the pivot,
     so the transform's translate values show where its pivot is.

 Usage :
     Select the offending transforms and run:

         import localSpaceFix
         localSpaceFix.fixLocSpace()
-------------------------------------------------------------------------
"""

from maya import cmds


def _freeze(node):
    cmds.makeIdentity(node, apply=True, t=True, r=False, s=True, n=0)


def _fix(node):
    # Work with the UUID so we keep track of the node when parent() renames its path.
    uuid = cmds.ls(node, uuid=True)[0]

    def current():
        return cmds.ls(uuid, long=True)[0]

    parents = cmds.listRelatives(node, parent=True, fullPath=True)
    if parents:
        cmds.parent(current(), world=True, absolute=True)
        _freeze(current())

    _freeze(current())

    piv = cmds.getAttr(current() + ".scalePivot")[0]
    cmds.setAttr(current() + ".translate", -piv[0], -piv[1], -piv[2])
    _freeze(current())
    cmds.setAttr(current() + ".translate", piv[0], piv[1], piv[2])

    if parents:
        cmds.parent(current(), parents[0])

    return current()


def fixLocSpace():
    sel = cmds.ls(sl=True, type="transform", long=True)
    if not sel:
        cmds.warning("Please select a transform to fix")
        return []

    fixed = []
    cmds.undoInfo(openChunk=True, chunkName="fixLocSpace")
    try:
        for node in sel:
            try:
                fixed.append(_fix(node))
                print("Local space values fixed for " + fixed[-1].split("|")[-1])
            except RuntimeError as err:
                cmds.warning("Could not fix {}: {}".format(node, err))
    finally:
        cmds.undoInfo(closeChunk=True)

    if fixed:
        cmds.select(fixed, r=True)
        cmds.headsUpMessage("Local Space Values fixed.", time=5.0)
    return fixed