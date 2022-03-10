'''----------------------------------------------------

    MINIMO Proxy Maker

    Date = 15-09-2014
    User = Maurizio Giglioli
    info = Make a proxy mesh of the selected geometry
    Update = (15-09-2014)
            First Relase

----------------------------------------------------'''

import maya.cmds as cmds
import numpy as np


def makeProxy_UI():
    win = cmds.window(t='Minimo Proxy Maker', s=True)
    # create ui pieces
    fr = cmds.formLayout()
    btP = cmds.button(l='source -->', p=fr, w=60)
    tfP = cmds.textField(w=120, p=fr)
    om = cmds.optionMenu(w=60, en=False)
    btV = cmds.button(l='AVG Vol', p=fr, w=60, en=False)
    ffv = cmds.floatField(p=fr, w=60, en=False)
    cbE = cmds.checkBox(l='Exclude', en=False)
    ffE = cmds.floatField(p=fr, w=25, en=False, v=0)
    ifg = cmds.intFieldGrp(
        nf=3,
        l='Resolution',
        value1=1,
        value2=2,
        value3=4,
        cat=[1, 'left', 0],
        cw4=[65, 35, 35, 35],
        en=False
    )
    btB = cmds.button(
        l='Make Proxy',
        c='mP.makeProxy('
        'cmds.textField(\'' + tfP + '\', q = True, tx = True),'  # asset
        'cmds.optionMenu(\'' + om + '\', q = True, v = True),'  # extension
        'cmds.intFieldGrp(\'' + ifg + '\', q = True, v1 = True),'  # low
        'cmds.intFieldGrp(\'' + ifg + '\', q = True, v2 = True),'  # med
        'cmds.intFieldGrp(\'' + ifg + '\', q = True, v3 = True),'  # high
        'cmds.floatField(\'' + ffE + '\', q = True, v = True))'  # Exclude
    )
    # ADD UI COMMANDS
    cmds.button(
        btP,
        e=True,
        c='cmds.textField(\'' + tfP + '\',e = True, tx = cmds.ls(sl=True)[0]);'
        'cmds.optionMenu(\'' + om + '\',e = True, en = True);'
        'cmds.button(\'' + btV + '\',e = True, en = True);'
        'cmds.floatField(\'' + ffv + '\',e = True, en = True);'
        'cmds.checkBox(\'' + cbE + '\',e = True, en = True);'
        'cmds.intFieldGrp(\'' + ifg + '\',e = True, en = True);'
    )
    cmds.textField(
        tfP,
        e=True,
        ec='cmds.button(\'' + btV + '\',e = True, en = False);'
        'cmds.optionMenu(\'' + om + '\',e = True, en = False);'
        'cmds.floatField(\'' + ffv + '\',e = True, en = False);'
        'cmds.checkBox(\'' + cbE + '\',e = True, en = False);'
        'cmds.intFieldGrp(\'' + ifg + '\',e = True, en = False);'
    )
    cmd = (
        'cmds.floatField(\'{0}\', e=True,'
        'v=mP.getAverageVolume(cmds.textField(\'{1}\', q=True, tx=True), cmds.optionMenu(\'{2}\', q=True, v=True)))'
    ).format(ffv, tfP, om)
    cmds.button(
        btV,
        e=True,
        c=cmd
    )
    cmds.checkBox(
        cbE,
        e=True,
        onc='cmds.floatField(\'{0}\', e=True, en=True, v=10)'.format(ffE),
        ofc='cmds.floatField(\'{0}\', e=True, en=False, v=0)'.format(ffE)
    )
    ext = [
        'GEO', 'MESH', 'SDM', 'NUL', 'PLY',
        '_GEO', '_MESH', '_SDM', '_NUL', '_PLY'
    ]
    for e in ext:
        cmds.menuItem(l=e.lower(), p=om)
    # FORMLAYOUT ARRANGMENT
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (btP, 'top', 5), (btP, 'left', 5),
            (tfP, 'top', 5),
            (om, 'top', 5),
            (btV, 'left', 5),
            (btB, 'left', 5),
            (ffv, 'left', 5),
            (ifg, 'left', 5), (ifg, 'right', 5),
            (ffE, 'right', 5),
            (btB, 'right', 5)
        ],
        ap=[
            (btP, 'right', 5, 25),
            (btV, 'right', 5, 25)
        ],
        ac=[
            (tfP, 'left', 5, btP),
            (om, 'left', 5, tfP),
            (btV, 'top', 5, btP),
            (ffv, 'top', 10, tfP),
            (ffv, 'left', 5, btV),
            (cbE, 'left', 5, ffv),
            (cbE, 'top', 10, tfP),
            (ffE, 'left', 5, cbE),
            (ffE, 'top', 10, tfP),
            (ifg, 'top', 10, ffv),
            (btB, 'top', 15, ifg)
        ]
    )
    # show window and size it
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[260, 140])


def makeProxy(topNode, ext, low, mid, high, exclude):
    meshes, sel, res, name = [], [], 1, ''
    if not topNode:
        cmds.confirmDialog(t='Error', m='Need an asset to work on')
        return
    if low <= 0:
        cmds.confirmDialog(
            t='error',
            m='Make sure the low value is at least 1'
        )
        return
    if topNode:
        sel = cmds.ls(topNode, dag=True, typ='transform')
        for s in sel:
            if ext in s:
                meshes.append(s)
        avg = getAverageVolume(topNode, ext)  # Get Average Poly Volume
        for m in meshes:
            if getVolume(m) > exclude:
                # SET THE RESOLUTION BASED ON THE VOLUME
                if getVolume(m) < avg:
                    if getVolume(m) > avg - avg % 25:
                        res = mid
                    else:
                        res = low
                elif getVolume(m) > avg:
                    if getVolume(m) > avg + avg % 25:
                        res = high
                    else:
                        res = mid
                # MAKE THE PROXY
                sh = cmds.listRelatives(m, s=True)
                vis = cmds.getAttr(m + '.v')
                if sh:
                    if cmds.nodeType(sh[0]) == 'mesh':
                        if '_' in ext:
                            name = m.replace(ext, '_proxy')
                            if cmds.objExists(name):
                                index = len(cmds.ls(name))
                                name = m.replace(ext, '_' + str(index) + '_proxy')
                        else:
                            name = m.replace(ext, 'proxy')
                            if cmds.objExists(name):
                                index = len(cmds.ls(name))
                                name = m.replace(ext, '_' + str(index) + 'proxy')
                        pc = cmds.polyCube(
                            w=100000,
                            h=100000,
                            d=100000,
                            sx=res,
                            sy=res,
                            sz=res,
                            n=name
                        )
                        center = mCentroid(m, 1)
                        cmds.setAttr(
                            pc[0] + '.t',
                            center[0],
                            center[1],
                            center[2]
                        )
                        father = cmds.listRelatives(m, p=True)
                        cmds.parent(pc[0], father[0])
                        cmds.refresh()
                        cmds.transferAttributes(
                            m,
                            pc[0],
                            transferPositions=True,
                            transferNormals=False,
                            transferUVs=False,
                            transferColors=False,
                            sourceUvSpace=False,
                            targetUvSpace='map1',
                            searchMethod=3,
                            flipUVs=0,
                            colorBorders=True
                        )
                        cmds.delete(pc[0], ch=True)
                        cmds.setAttr(pc[0] + '.v', vis)
                        cmds.refresh()
        print 'Proxy DONE'


def getAverageVolume(topNode, ext):
    sel = cmds.ls(topNode, dag=True, typ='transform')
    meshes, sum = [], []
    if topNode:
        for s in sel:
            if ext in s:
                meshes.append(s)
        for s in meshes:
            vol = getVolume(s)
            sum.append(vol)
        print min(sum), max(sum), np.mean(sum)
        return np.mean(sum)
    else:
        cmds.warning('no meshes found !')


def getVolume(mesh):
    bbox = cmds.exactWorldBoundingBox(mesh)
    xLen = bbox[3] - bbox[0]
    yLen = bbox[4] - bbox[1]
    zLen = bbox[5] - bbox[2]
    vol = xLen * yLen * zLen
    return vol


def mCentroid(obj, dir):
    if cmds.nodeType(cmds.listRelatives(obj, s=True)[0]) == 'mesh':
        geo = []
        p = [[], [], []]
        vtxs = cmds.polyEvaluate(obj, v=True)
        for x in range(vtxs):
            geo.append(obj + '.vtx[' + str(x) + ']')
        for i in geo:
            po = cmds.xform(i, q=True, ws=True, t=True)
            p[0].append(po[0])
            p[1].append(po[1])
            p[2].append(po[2])

        length = len(p[0])
        centroid = ([
            sum(p[0]) / length,
            sum(p[1]) / length,
            sum(p[2]) / length
        ])
        loc = cmds.spaceLocator()
        cmds.xform(loc[0], t=(centroid[0], centroid[1], centroid[2]))
        if dir == 1:
            cmds.delete(loc)
        return centroid
    else:
        print 'Skipped {0}'.format(obj)
