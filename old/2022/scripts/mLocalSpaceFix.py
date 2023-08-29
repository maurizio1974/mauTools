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
    local = ''
    if sel:
        for s in sel:
            f = cmds.listRelatives(s, p=True)
            child = cmds.listRelatives(s, c=True, f=True)
            if child:
                for c in child:
                    if cmds.nodeType(c) == 'transform':
                        cmds.parent(c, w=True)
            if f:
                cmds.parent(s, w=True, a=True)
                local = '|' + s.split('|')[-1]
                cmds.makeIdentity(local, apply=True, t=1, r=0, s=1, n=0)
            else:
                local = s
            cmds.makeIdentity(local, apply=True, t=1, r=0, s=1, n=0)
            piv = cmds.getAttr(local + '.scalePivot')[0]
            cmds.setAttr(local + '.t', -1 * piv[0], -1 * piv[1], -1 * piv[2])
            cmds.select(local, r=True)
            cmds.makeIdentity(local, apply=True, t=1, r=0, s=1, n=0)
            cmds.setAttr(local + '.t', piv[0], piv[1], piv[2])
            if f:
                cmds.parent(local, f[0])
            if child:
                for c in child:
                    if cmds.nodeType(c) == 'transform':
                        cmds.parent(c, s)
            print 'Local space values firx for ' + s + '\n'
            cmds.select(s, r=True)
    else:
        cmds.warning('Please select a trasnform to fix')
    cmds.headsUpMessage('Local Space Values fixed.', time=5.0)


fixLocSpace()
