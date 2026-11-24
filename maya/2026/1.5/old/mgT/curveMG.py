import maya.cmds as cmds, maya.mel as mel

def curveMG(transform):
    cmds.select(transform)
    all = cmds.ls(sl=True)
    time = 0

    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    cmds.currentTime(start, e=True)

    for cur in all:
        l = cmds.spaceLocator(n=(cur+'_LOC'))
        cmds.parentConstraint(cur, l, w=.1)

        pos = cmds.xform(l[0], q=True, ws=True, t=True)
        name = cur+'CRV'
        curve = cmds.curve(n=name, d=1, p=[(pos[0], pos[1], pos[2])])

        for e in range(start, end):
            cmds.currentTime(e, e=True)
            pos = cmds.xform(l[0], q=True, t=True)
            cmds.curve(curve, os=True, a=True, p=[(pos[0], pos[1], pos[2])])

    cmds.currentTime(start, e=True)
    cmds.select(l[0])
    cmds.delete(l)

    return[curve, all[0]]
