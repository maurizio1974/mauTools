import maya.cmds as cmds

'''-------------------------------------------------------------------------
    Author :
        Maurizio Giglioli
    Date :
        03/05/2010
    Update:
        18/11/2015 Converted to Python
    Notes :
        This script fixes local space values on selected transform node.s
    Usage :
        Just select the needed offending trasnform and call the script.

--------------------------------------------------------------------------'''


def fixLocSpace():
    sel = cmds.ls(sl=True, typ='transform')
    if sel:
        for s in sel:
            f = cmds.listRelatives(s, p=True)
            print f
            child = cmds.listRelatives(s, c=True, type='transform')
            if child:
                for c in child:
                    if c != s:
                        cmds.parent(c, w=True)
            if f:
                cmds.parent(s, w=True)
                cmds.makeIdentity(s, apply=True, t=1, r=0, s=1, n=0)
            cmds.makeIdentity(s, apply=True, t=1, r=0, s=1, n=0)
            cmds.CenterPivot()
            piv = cmds.getAttr(s + '.scalePivot')[0]
            cmds.setAttr(s + '.t', -1 * piv[0], -1 * piv[1], -1 * piv[2])
            cmds.select(s, r=True)
            cmds.makeIdentity(s, apply=True, t=1, r=0, s=1, n=0)
            cmds.setAttr(s + '.t', piv[0], piv[1], piv[2])
            if f:
                cmds.parent(s, f[0])
            if child:
                for c in child:
                    cmds.parent(c, s)
            print 'Local space values fired for ' + s
            cmds.select(s, r=True)
    else:
        cmds.warning('Please select a trasnform to fix')
    cmds.headsUpMessage('Local Space Values fixed for' + s, time=5.0)


def fixLocSpace2():
    sel = cmds.ls(sl=True)
    for s in sel:
        fa = cmds.listRelatives(s, p=True)
        chi = cmds.listRelatives(s, c=True, type='transform')
        print chi
        grp = cmds.group(em=True)
        if chi:
            for c in chi:
                cmds.parent(c, w=True)
        pc = cmds.pointConstraint(s, grp)
        cmds.refresh()
        cmds.delete(pc)
        cmds.parent(s, grp)
        cmds.makeIdentity(s, apply=True, t=1, r=0, s=1, n=0)
        if fa:
            cmds.parent(s, fa[0])
        else:
            cmds.parent(s, w=True)
        if chi:
            for c in chi:
                cmds.parent(c, s)
        cmds.delete(grp)
