import maya.cmds as cmds
import maya.mel as mel
import shutil


def mSaveVertexMaps_UI():
    mel.eval('PaintVertexColorTool')
    cmds.setToolTo('selectSuperContext')
    win = cmds.window(t='Minimo ColorVertex Exporter', s=False, rtf=True)
    # UI
    frT = cmds.formLayout()
    mbt = cmds.button(label='Get Mesh')
    mtf = cmds.textField()
    lbt = cmds.button(label='Set Location')
    ltf = cmds.textField()
    ntf = cmds.textFieldGrp(
        label='Name', cw2=(97, 190), cl2=('center', 'left'))
    ffg = cmds.floatFieldGrp(
        nf=2, cw4=(97, 60, 60, 97),
        cl4=('center', 'center', 'center', 'right'),
        label='start', el='end',
        v1=cmds.playbackOptions(q=True, min=True),
        v2=cmds.playbackOptions(q=True, max=True)
    )
    auto = cmds.checkBox(label='ALL', v=True)
    opU = cmds.optionMenu(label='U', en=False)
    opV = cmds.optionMenu(label='V', en=False)
    obt = cmds.button(label='Write Out')
    # ORGANIZE UI
    cmds.formLayout(
        frT,
        e=True,
        af=[
            (mbt, 'left', 5),
            (mbt, 'top', 5),
            (mtf, 'top', 5),
            (mtf, 'right', 5),
            (lbt, 'left', 5),
            (ltf, 'right', 5),
            (ntf, 'left', 5),
            (ntf, 'right', 5),
            (ffg, 'left', 5),
            (ffg, 'right', 5),
            (auto, 'left', 5),
            (opV, 'right', 5),
            (obt, 'left', 5),
            (obt, 'right', 5)
        ],
        ap=[
            (mbt, 'right', 5, 35),
            (lbt, 'right', 5, 35),
            (auto, 'right', 55, 15),
            (opU, 'right', 25, 65)
        ],
        ac=[
            (mtf, 'left', 5, mbt),
            (lbt, 'top', 5, mbt),
            (ltf, 'top', 5, mtf),
            (ltf, 'left', 5, lbt),
            (ntf, 'top', 5, ltf),
            (ffg, 'top', 5, ntf),
            (auto, 'top', 12, ffg),
            (opU, 'top', 10, ffg), (opU, 'left', 5, auto),
            (opV, 'top', 10, ffg), (opV, 'left', 10, opU),
            (obt, 'top', 10, opU)
        ]
    )
    # ADD UI COMMANDS
    cmds.button(
        mbt,
        e=True,
        c='cmds.textField("' + mtf + '", e=True, tx=cmds.ls(sl=True)[0])'
    )
    cmd = 'cmds.textField("' + ltf
    cmd += '", e=True, tx=mVertexColorExport.mBrowser(3))'
    cmds.button(
        lbt,
        e=True,
        c=cmd
    )
    cmds.checkBox(
        auto,
        e=True,
        onc='cmds.optionMenu("' + opU + '", e=True, en=False);'
        'cmds.optionMenu("' + opV + '", e=True, en=False)',
        ofc='cmds.optionMenu("' + opU + '", e=True, en=True);'
        'cmds.optionMenu("' + opV + '", e=True, en=True)'
    )
    cmd = '''
    cmds.textField(\'{0}\', q=True, tx=True),
    cmds.textField(\'{1}\', q=True, tx=True),
    cmds.floatFieldGrp(\'{2}\', q=True, v1=True),
    cmds.floatFieldGrp(\'{2}\', q=True, v2=True),
    cmds.textFieldGrp(\'{3}\', q=True, tx=True),
    cmds.optionMenu(\'{4}\', q=True, sl=True),
    cmds.optionMenu(\'{5}\', q=True, sl=True),
    cmds.checkBox(\'{6}\', q=True, v=True)
    '''.format(mtf, ltf, ffg, ntf, opU, opV, auto)
    # OPTION MENU
    for o in [opU, opV]:
        for x in range(1, 10):
            cmds.menuItem(str(x), p=o)
    # FINAL BUTTON
    cmds.button(
        obt,
        e=True,
        c='mVertexColorExport.mSaveVertexMap(' + cmd + ')'
    )
    # presets for scene name
    prst = [
        'tension', 'stretch', 'compress', 'color'
    ]
    pps = cmds.popupMenu('namesPP', p=ntf)
    for p in prst:
        cmds.menuItem(
            label=p,
            p=pps,
            c="cmds.textFieldGrp('" + ntf + "', e=True, tx=\'" + p + "\')"
        )
    # show window and size it
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[300, 200])


def mSaveVertexMap(mesh, path, start, end, name, u, v, auto):
    if not mesh:
        cmds.confirmDialog(
            t='Error', m='Set a mesh to get the vertex map from'
        )
        return
    if not path:
        cmds.confirmDialog(
            t='Error', m='Set a path where to save the images'
        )
        return
    if not name:
        cmds.confirmDialog(
            t='Error', m='Set a name for the images'
        )
        return
    cmds.currentTime(start)
    if auto:  # GET THE FULL UV LAYOUT RANGE AUTOMATICALLY
        uPos, vPos = [], []
        uv = cmds.polyEvaluate(mesh, uv=True)
        for x in range(0, uv):
            uPos.append(
                cmds.polyEditUV("{0}.map[{1}]".format(mesh, x), q=1)[0]
            )
            vPos.append(
                cmds.polyEditUV("{0}.map[{1}]".format(mesh, x), q=1)[1]
            )
        u = int(round(max(uPos)))
        v = int(round(max(vPos)))
    # START EXPORTING THE VERTEX MAP
    for x in range(0, u):
        for y in range(0, v):
            mUVmover(mesh, x * -1, y * -1, 0)
            for i in range(int(start), int(end + 1)):
                cmds.select(cl=True)
                nameout = name + '_' + str(x) + '_' + str(y)
                nameout += '.' + str("%04d" % (i, ))
                file = shutil.os.path.join(path, nameout) + '.tiff'
                cmds.setToolTo('artAttrColorPerVertexContext')
                cmds.select(mesh)
                cmds.artAttrPaintVertexCtx(
                    'artAttrColorPerVertexContext',
                    e=True,
                    exportfilesave=file
                )
                cmds.select(cl=True)
                cmds.currentTime(i + 1)
            mUVmover(mesh, x * -1, y * -1, 1)
    cmds.setToolTo('selectSuperContext')
    cmds.select(cl=True)
    print 'ALL DONE'
    cmds.currentTime(start)


def mUVmover(mesh, u, v, dir):
    vtx = cmds.polyEvaluate(mesh, uv=True)
    cmds.select(mesh + '.map[0:' + str(vtx) + ']', r=True)
    if dir == 0:
        cmds.polyEditUV(r=True, u=u, v=v)
    elif dir == 1:
        cmds.polyEditUV(r=True, u=u * -1, v=v * -1)


def mBrowser(mode):
    ws = cmds.workspace(q=True, act=True)  # active directory
    out = ''
    filter = "Maya ASCII (*.ma);;Maya Binary (*.mb)"
    r = cmds.fileDialog2(
        ff=filter,
        cap='Asset Package Destination',
        dir=ws,
        fm=mode,
        ds=True
    )
    if r:
        out = r[0]
    return out
