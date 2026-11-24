# ---------------------------------------------------------------------------
# WrapX Tools for Maya
# ---------------------------------------------------------------------------
import maya.cmds as cmds
import wrap


def mBrowser(mode):
    filter = "Maya ASCII (*.ma);;Maya Binary (*.mb)"
    r = cmds.fileDialog2(
        ff=filter,
        cap='cacheScene',
        dir="data/",
        fm=mode,
        ds=True
    )
    out = r[0]
    return out


def mWrapUI():
    win = cmds.window(t='Minimo mWrap', s=True)
    # create ui pieces
    fr = cmds.formLayout()
    btP = cmds.button(l='Base Geo', p=fr)
    tfP = cmds.textField(p=fr)
    btPP = cmds.button(l='Base Points', p=fr)
    tfPP = cmds.textField(p=fr)
    btI = cmds.button(l='Scan Geo')
    tfI = cmds.textField()
    tfO = cmds.textField()
    txO = cmds.button(
        l='Output Geo',
        c='cmds.textField(\'' + tfO + '\', e=True, tx=mWrap.mBrowser())'
    )
    cmd = 'mWrap.prepareWrap('
    cmd += 'cmds.textField(\'' + tfP + '\', q=True, tx=True), '
    cmd += 'cmds.textField(\'' + tfI + '\', q=True, tx=True))'
    btW = cmds.button(
        l='WrapIt OUT',
        c=cmd
    )
    # ADD UI COMMANDS
    # TEXT FIELD GET NAME
    cmds.button(
        btP,
        e=True,
        c='cmds.textField(\'' + tfP + '\',e = True, tx = cmds.ls(sl=True)[0])'
    )
    cmds.button(
        btI,
        e=True,
        c='cmds.textField(\'' + tfI + '\',e = True, tx = cmds.ls(sl=True)[0])'
    )
    # FORMLAYOUT ARRANGMENT
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (btP, 'top', 5), (btP, 'left', 5),
            (tfP, 'top', 5), (tfP, 'right', 5),
            (btPP, 'top', 5), (btPP, 'left', 5),
            (tfPP, 'top', 5), (tfPP, 'right', 5),
            (btI, 'left', 5),
            (tfI, 'right', 5),
            (txO, 'left', 5),
            (tfO, 'right', 5),
            (btW, 'left', 5),
            (btW, 'right', 5)
        ],
        ap=[
            (btP, 'right', 5, 25),
            (btI, 'right', 5, 25),
            (txO, 'right', 5, 25),
        ],
        ac=[
            (tfP, 'left', 5, btP),
            (btPP, 'top', 5, btP),
            (tfPP, 'top', 10, tfP), (tfPP, 'left', 5, btPP),
            (btI, 'top', 5, btPP),
            (tfI, 'top', 10, tfPP), (tfI, 'left', 5, btI),
            (txO, 'top', 10, btI),
            (tfO, 'top', 10, tfI), (tfO, 'left', 5, txO),
            (btW, 'top', 10, tfO)
        ]
    )
    # show window and size it
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[300, 130])


def prepareWrap(geom, scan):
    cmds.select(cl=True)
    # path = '/tmp/'
    path = '/home/mau/Desktop/'
    cmds.select(geom, r=True)
    cmds.file(
        path + geom + '.obj',
        f=True,
        typ="OBJexport",
        pr=False,
        es=True
    )
    cmds.select(scan, r=True)
    cmds.file(
        path + scan + '.obj',
        f=True,
        typ="OBJexport",
        pr=False,
        es=True
    )
    cmds.select(cl=True)
    mDefineWrap(path + geom + '.obj', 1.0, path + scan + '.obj', 1.0)


def mDefineWrap(base, baseS, scan, scanS):
    geom = wrap.Geom(str(base), scaleFactor=baseS)
    scan = wrap.Geom(str(scan), scaleFactor=scanS)
    return geom, scan


def mRigidWrap(geom, scan, basePoints, scanPoints, out, baseS):
    # Rigid Alignment
    pointsGeom = wrap.loadPoints(basePoints)
    pointsScan = wrap.loadPoints(scanPoints)
    rigidTransformation = wrap.rigidAlignment(
        geom, pointsGeom, scan, pointsScan
    )
    geom.transform(rigidTransformation)
    if out:
        geom.save(out, scaleFactor=1 / baseS)


def mNonRigidWrap(
        geom, scan, basePoints, scanPoints, basePolygons, out, baseS):
    # Non-Rigid Alignment ALL BODY
    controlPointsGeom = wrap.loadPoints(basePoints)
    controlPointsScan = wrap.loadPoints(scanPoints)
    # FREE POLYGONS
    controlPolyGeom = wrap.loadPolygons(basePolygons)
    # Settings non Rigid
    geom = wrap.nonRigidRegistration(
        geom, scan, controlPointsGeom, controlPointsScan, controlPolyGeom
    )
    # 3 Save the result
    if out:
        geom.save(out, scaleFactor=1 / baseS)
