'''-------------------------------------------------------------------

    MIMMO TRASFER SHADERS UTILITY

    Date = 12-09-2014
    User = Maurizio Giglioli
    Update = (12-09-2014)
            First release

----------------------------------------------------------------------'''

import maya.cmds as cmds


def mTshaders_UI():
    win = cmds.window(t='Mimmo Shader Transfer', s=True)
    # create ui pieces
    fr = cmds.formLayout()
    btP = cmds.button(l='source -->', p=fr, w=60)
    tfP = cmds.textField(p=fr)
    btI = cmds.button(l='destin -->', p=fr, w=60)
    tfI = cmds.textField()
    btB = cmds.button(
        l='Transfer',
        c='mTs.mTshadersGet('
        'cmds.textField(\'' + tfP + '\', q=True, tx=True),'  # source
        'cmds.textField(\'' + tfI + '\', q=True, tx=True))'  # destination
    )
    # ADD UI COMMANDS
    cmds.button(
        btP,
        e=True,
        c='cmds.textField(\'{0}\', e=True, tx=cmds.ls(sl=True)[0])'.format(tfP)
    )
    cmds.button(
        btI,
        e=True,
        c='cmds.textField(\'{0}\', e=True, tx=cmds.ls(sl=True)[0])'.format(tfI)
    )
    # FORMLAYOUT ARRANGMENT
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (btP, 'top', 5), (btP, 'left', 5),
            (tfP, 'top', 5), (tfP, 'right', 5),
            (btI, 'left', 5), (tfI, 'right', 5),
            (btB, 'left', 5), (btB, 'right', 5)],
        ap=[
            (btP, 'right', 5, 25),
            (btI, 'right', 5, 25)],
        ac=[
            (tfP, 'left', 5, btP),
            (btI, 'top', 5, btP),
            (tfI, 'top', 10, tfP), (tfI, 'left', 5, btI),
            (btB, 'top', 15, tfI)]
    )
    # show window and size it
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[240, 100])


def mTshadersGet(node1, node2):
    ns1, ns2, out = '', '', []
    if not node1:
        cmds.confirmDialog(t='Error', m='Need a source object')
        return
    if not node2:
        cmds.confirmDialog(t='Error', m='Need a destination object')
        return
    all = cmds.ls(
        node1,
        dag=True,
        type='transform',
        l=False
    )  # Get the hierarchy of the asset
    for t in node1.split(':')[0:-1]:  # source nameSpace
        ns1 += t + ':'
    for t in node2.split(':')[0:-1]:  # destination nameSpace
        ns2 += t + ':'
    for a in all:
        sh = cmds.listRelatives(a, s=True, f=True)
        if sh:
            if cmds.nodeType(sh[0]) == 'mesh':  # check if the node is a mesh
                if cmds.objExists(a.replace(ns1, ns2)):
                    mTshaders(a, a.replace(ns1, ns2))
                else:
                    out.append(a)
    if out:
        cmds.select(out)
    cmds.confirmDialog(t='tadaaa', m='All DONE')


def mTshaders(obj1, obj2):
    cmds.select(cl=True)  # Clear current selection
    ns1, ns2 = '', ''
    for t in obj1.split(':')[0:-1]:  # source nameSpace
        ns1 += t + ':'
    if not len(ns1):
        cmds.confirmDialog(t='Error', m='Need namespaces on the source asset')
        return
    for t1 in obj2.split(':')[0:-1]:  # destination nameSpace
        ns2 += t1 + ':'

    # print ns1, ns2

    if not len(ns2):
        cmds.confirmDialog(
            t='Error',
            m='Need namespaces on the destination asset'
        )
        return
    shrd = cmds.listSets(ets=True, type=1, o=obj1)  # Get the shaders
    if len(shrd) > 1:
        for s in shrd:
            sgMembers = cmds.sets(s, q=True)
            if s != 'initialShadingGroup':  # Check if default lambert
                if not cmds.objExists(s.replace(ns1, ns2)):
                    shrdD = cmds.duplicate(s, un=True, n=s.replace(ns1, ns2))
                    for sh in shrdD:
                        if sh != shrdD[0]:
                            cmds.rename(sh, ns2 + sh)
                    s = shrdD[0]
                else:
                    s = s.replace(ns1, ns2)
            for sg in sgMembers:
                if cmds.objExists(sg.replace(obj1, obj2)):
                    cmds.sets(sg.replace(obj1, obj2), e=True, fe=s)
                else:
                    print(sg.replace(obj1, obj2) + ' doens\'t exists')
    else:
        cmds.select(obj2)
        shrd = cmds.listConnections(shrd[0] + '.surfaceShader')
        if shrd[0] != 'lambert1':  # Check if default lambert
            print(ns1, ns2, shrd[0].replace(ns1, ns2))
            if not cmds.objExists(shrd[0].replace(ns1, ns2)):
                shrdD = cmds.duplicate(
                    shrd,
                    un=True,
                    n=shrd[0].replace(ns1, ns2))
                cmds.hyperShade(a=shrdD[0])
            else:
                cmds.hyperShade(a=shrd[0].replace(ns1, ns2))
        else:
            cmds.hyperShade(a=shrd[0])
    cmds.select(cl=True)

# -------------------------   ALTERNATIVE ---------------------------------


def transferSHRD():
    se, out = cmds.ls('SHD:*', type='shadingEngine'), []
    for s in se:
        meshes = cmds.sets(s, q=True)
        if not meshes:
            continue
        for m in meshes:
            if cmds.objExists(m.replace('SHD:', '')):
                try:
                    print(m.replace('SHD:', ''))
                    cmds.sets(m.replace('SHD:', ''), e=True, fe=s)
                    # cmds.delete(m)
                except:
                    print('not this one ' + m)
            else:
                out.append(m)
    if out:
        cmds.select(out, r=True)

    se = cmds.ls(sl=True, type='shadingEngine')
    for s in se:
        meshes = cmds.sets(s, q=True)
        if not meshes:
            continue
        for m in meshes:
            if cmds.objExists(m.replace('ASS:', 'MOD:')):
                cmds.sets(m.replace('ASS:', 'MOD:'), e=True, fe=s)
            else:
                print(m.replace('MOD:', ''))
