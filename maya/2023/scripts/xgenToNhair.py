import time
import maya.mel as mel
import maya.cmds as cmds


'''
LAUNCH UI

import xgenToNhair
xgenToNhair.xUI()

'''


def xgConvert(mesh, radius, guide, jnts, dyn=None, mode=None):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(t='Not Kick Ass', m='Nothing Selected !"')
        return
    for s in sel:
        start = time.time()  # START TIME EXECUTION
        cmds.xgmGeoRender(
            s, pb=True, convertSelected=0, combineMesh=0, useWidthRamp=1, insertWidthSpan=0,
            uvInTiles=1, uvLayoutType=0, uvTileSeparation=0.0, createStripJoints=0, createGuideJoints=guide)
        cur = s + '_convert'
        cmds.setAttr(cur + '.v', 0)
        grpJ = s + '_joints_grp'
        if guide:
            hairJ = cmds.ls(cur, dag=True, type='joint')
            if not cmds.objExists(grpJ):
                cmds.group(em=True, n=grpJ)
                cmds.refresh()
            cmds.parent(hairJ, grpJ)
            for j in hairJ:
                cmds.setAttr(j + '.radius', 0.005)
        hair = cmds.ls(cur, dag=True, type='transform')
        cmds.select(cl=True)
        # RENAME AND PARENT JOINTS IN CHAINS
        hairC = []
        if guide:
            chain = int(cmds.polyEvaluate(hair[1], v=True) / 4)
            out = jointChain(grpJ, chain)
            if not jnts:
                cmds.delete(grpJ)
            for o in out[1]:
                hairC.append(o)
        if not guide:
            # MAKE PROGRESS BAR
            gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
            # SET PROGRESS BAR
            cmds.progressBar(
                gMainProgressBar, e=True, bp=True, ii=True, st='Working on (' + s + ')', max=len(hair))
            grp = s.replace('convert', 'crv_grp') + '_grp'
            if not cmds.objExists(grp):
                cmds.group(em=True, n=grp)
            for z, h in enumerate(hair):
                if cmds.progressBar(gMainProgressBar, q=True, ic=True):
                    break
                if h != hair[0]:
                    vtx = cmds.polyEvaluate(h, v=True)
                    pos1 = cmds.pointPosition(h + '.vtx[0]')
                    pos2 = cmds.pointPosition(h + '.vtx[1]')
                    avg = [
                        (pos1[0] + pos2[0]) / 2,
                        (pos1[1] + pos2[1]) / 2,
                        (pos1[2] + pos2[2]) / 2]
                    crv = cmds.curve(
                        d=3, n=s + '_' + str(z).zfill(3) + '_crv', p=(avg[0], avg[1], avg[2]))
                    hairC.append(crv)
                    for x in range(0, vtx, 2):
                        pos1 = cmds.pointPosition(h + '.vtx[' + str(x) + ']')
                        pos2 = cmds.pointPosition(
                            h + '.vtx[' + str(x + 1) + ']')
                        avg = [
                            (pos1[0] + pos2[0]) / 2,
                            (pos1[1] + pos2[1]) / 2,
                            (pos1[2] + pos2[2]) / 2]
                        cmds.curve(crv, a=True, p=(avg[0], avg[1], avg[2]))
                    cmds.parent(crv, grp)
                cmds.progressBar(
                    gMainProgressBar, e=True, s=1, st='Working on ( ' + s + ' ) Left to do: ' + str(len(hair) - z))
            cmds.select(cl=True)
            cmds.progressBar(gMainProgressBar, e=True, ep=True)
        if mode:
            if dyn:
                makeDynamic(hairC, mesh)
            else:
                makeStatic(hairC, mesh)
        cmds.delete(cur)

        curveOptions(hairC, radius)
        # curveExport(grp, radius)

        cmds.select(cl=True)
        end = time.time()
        result = round(end - start, 3)
        print('-' * 150)
        msg = 'Groom :'
        if guide:
            msg = 'Guide :'
        print('Done with this ' + msg + '\n' + '\t' * 10 + s + '\n' +
              '\t' * 7 + 'execution time: ' + str(result) + ' seconds')
        print('-' * 150)


def jointChain(base, chain):
    jnts = cmds.ls(base, dag=True, type='joint')
    dict = {}
    for x in range(0, int(len(jnts) / chain)):
        if x == 0:
            dict[x] = jnts[x:chain]
        else:
            dict[x] = jnts[chain * x:chain * x + chain]
    out = []
    for d in dict.keys():
        for x, j in enumerate(dict[d]):
            if x > 0:
                cmds.parent(dict[d][x], dict[d][x - 1])
                if dict[d][x] == dict[d][0]:
                    cmds.setAttr(dict[d][x] + '.jointOrient', 0, 0, 0)
        out.append(dict[d][0])
    grpC = base.split('_')[0] + '_guides_grp'
    if not cmds.objExists(grpC):
        cmds.group(em=True, n=grpC)
    # MAKE MAIN PROGRESS BAR
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    # SET PROGRESS BAR
    cmds.progressBar(
        gMainProgressBar, e=True, bp=True, ii=True, st='Makign Guideses', max=len(out))
    crvs, outj = [], []
    for y, o in enumerate(out):
        cmds.progressBar(
            gMainProgressBar, e=True, s=1, st='Making Guide ( ' + o + ' ) Left to do: ' + str(len(out) - y))
        pos = cmds.xform(o, q=True, ws=True, t=True)
        crv = cmds.curve(
            d=3,
            n=base.split('_')[0] + '_' + str(y + 1).zfill(2) + '_guide_crv',
            p=(pos[0], pos[1], pos[2]))
        cmds.parent(crv, grpC)
        crvs.append(crv)
        jnts = cmds.ls(o, dag=True, type='joint')
        for x, j in enumerate(jnts):
            pos = cmds.xform(j, q=True, ws=True, t=True)
            cmds.curve(crv, a=True, p=(pos[0], pos[1], pos[2]))
            name = base.split(
                '_')[0] + '_' + str(y + 1).zfill(2) + '_' + str(x + 1).zfill(3) + '_jnt'
            cmds.rename(j, name)
            outj.append(name)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)
    return outj, crvs


def curveOptions(hair, radius):
    for tr in hair:
        s = cmds.listRelatives(tr, s=True)[0]
        cmds.setAttr(s + '.aiRenderCurve', 1)
        cmds.setAttr(s + '.aiCurveWidth', radius)
        if tr != s.replace('Shape', ''):
            name = tr + 'Shape'
            cmds.rename(s, name)


def curveExport(base, radius):
    name = base.replace('_grp', '')
    grp = cmds.group(em=True, n=name + '_curves')
    hair = cmds.ls(base, dag=True, type='nurbsCurve')
    # MAKE PROGRESS BAR
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    cmds.progressBar(
        gMainProgressBar, e=True, bp=True, ii=True, st='Working on (' + base + ')', max=len(hair))
    for z, h in enumerate(hair):
        if cmds.progressBar(gMainProgressBar, q=True, ic=True):
            break
        nameC = h.replace('_crv', '_ex_crv')
        crv = cmds.createNode('nurbsCurve', n=nameC)
        tr = cmds.listRelatives(crv, p=True)[0]
        cmds.connectAttr(h + '.worldSpace', crv + '.create', f=True)
        cmds.parent(crv, grp, s=True, r=True)
        cmds.setAttr(crv + '.aiRenderCurve', 1)
        cmds.setAttr(crv + '.aiCurveWidth', radius)
        cmds.delete(tr)
        cmds.progressBar(gMainProgressBar, e=True, s=1,
                         st='Working on ( ' + base + ' ) Left to do: ' + str(len(hair) - z))
    cmds.select(cl=True)
    cmds.setAttr(base + '.v', 0)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)


def makeStatic(hair, mesh):
    name = hair[0].split('_')[0]
    # MAKE PROGRESS BAR
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    cmds.progressBar(
        gMainProgressBar, e=True, bp=True, ii=True, st='Making static hair follicle ( ' + name + ' )', max=len(hair))
    for x, h in enumerate(hair):
        if cmds.progressBar(gMainProgressBar, q=True, ic=True):
            break
        fa = cmds.listRelatives(h, p=True)[0]
        pos = cmds.pointPosition(h + '.cv[0]')
        ID = getClosestFace(mesh, pos=[pos[0], pos[1], pos[2]])
        curF = mesh + '_' + str(ID) + '_fol'
        cmds.progressBar(gMainProgressBar, e=True, s=1,
                         st='Making static hair follicle ( ' + name + ' ) Left to do: ' + str(len(hair) - x))
        if cmds.objExists(curF):
            cmds.parent(h, curF)
            continue
        cmds.select(mesh + '.f[' + str(ID) + ']', r=True)
        fol = rivetFollNoUV()
        cmds.parent(fol, fa)
        cmds.parent(h, fol)
        cmds.rename(fol, curF)
        cmds.select(cl=True)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)


def makeDynamic(hair, mesh):
    name = hair[0].split('_')[0]
    # GET ALL THE EXISTING HAIRSYSTEMS
    hss1 = cmds.ls(type='hairSystem')
    cmds.select(hair, r=True)
    cmds.select(mesh, add=True)
    mel.eval('makeCurvesDynamic 2 { "1", "0", "1", "1", "0"}')
    # CLEAN UP AND RENAME
    sel = cmds.ls('hairSystem1OutputCurves', dag=True, type='transform')[1:]
    for s in sel:
        fol = cmds.listConnections(s + '.create', s=True, d=False)[0]
        folS = cmds.listRelatives(fol, s=True)[0]
        cmds.setAttr(folS + '.v', 0)
        crv = cmds.listConnections(fol + '.startPosition', s=True, d=False)[0]
        nameC = crv.replace('_crv', '')
        cmds.rename(fol, nameC + '_fol')
        cmds.rename(s, nameC + '_dyn_crv')
    # GET CURRENT HAIR SYSTEM
    hs = getCurrentHS(hss1, name)
    cmds.rename('hairSystem1OutputCurves', name + '_OutputCurves_grp')


def getCurrentHS(hss1, name):
    hss2 = cmds.ls(type='hairSystem')
    hss = []
    if hss1 != hss2:
        hss = list(set(hss2) - set(hss1))
    if not hss:
        hss = hss1
    hssT = cmds.listRelatives(hss[0], p=True)[0]
    cmds.rename(hssT, name + '_hairSystem')
    return name + '_hairSystem'

# FIND OPPOSITE EDGES OF A QUAD POLY FACE


def findEdges():
    sel = cmds.ls(sl=True)
    cmds.select(sel[0], r=True)
    edges = cmds.polyListComponentConversion(sel[0], ff=True, te=True)
    cmds.select(edges, r=True)
    sel = cmds.ls(sl=True, fl=True)
    master, exit = [], []
    for x, s in enumerate(sel):
        vtx = cmds.polyListComponentConversion(sel[x], fe=True, tv=True)
        cmds.select(vtx, r=True)
        vtx = cmds.ls(sl=True, fl=True)
        cmds.select(cl=True)
        master = cmds.polyListComponentConversion(sel[0], fe=True, tv=True)
        cmds.select(master, r=True)
        master = cmds.ls(sl=True, fl=True)
        cmds.select(cl=True)
        if x != 0:
            if not set(master).intersection(vtx):
                exit = s
    return sel[0], exit


def getClosestFace(mesh, pos):
    if not cmds.pluginInfo('nearestPointOnMesh', query=True, l=True):
        cmds.loadPlugin('nearestPointOnMesh')
    npm = 'nearestPointOnMesh_TEMP'
    if not cmds.objExists(npm):
        cmds.createNode('nearestPointOnMesh', n=npm)
    cmds.connectAttr(mesh + '.worldMesh[0]', npm + '.inMesh', f=True)
    cmds.setAttr(npm + '.inPosition', pos[0], pos[1], pos[2])
    ID = cmds.getAttr(npm + '.nearestFaceIndex')
    cmds.delete(npm)
    return ID


def rivetFollNoUV():
    list = cmds.ls(sl=True, fl=True)
    if not list:
        cmds.confirmDialog(
            t='Error', m="Select a single Mesh Face")
        return
    if not '.f[':
        cmds.confirmDialog(
            t='Error', m="Select a single Mesh Face")
        return
    nObj = list[0].split('.')
    sh = cmds.listRelatives(nObj[0], s=True)
    if not sh:
        sh = []
        if cmds.nodeType(nObj[0]) == 'mesh':
            sh.append(nObj[0])
    # PART FOR MESH OBJECTS
    if cmds.nodeType(sh[0]) == 'mesh':
        list = findEdges()

        e1 = list[0].split('[')[1].split(']')
        e2 = list[1].split('[')[1].split(']')

        nameCFME1 = cmds.createNode(
            'curveFromMeshEdge', n='rCFME1')
        cmds.setAttr(nameCFME1 + '.ihi', 1)
        cmds.setAttr(nameCFME1 + '.ei[0]', int(e1[0]))
        nameCFME2 = cmds.createNode(
            'curveFromMeshEdge', n='rCFME2')
        cmds.setAttr(nameCFME2 + '.ihi', 1)
        cmds.setAttr(nameCFME2 + '.ei[0]', int(e2[0]))
        cmds.connectAttr(sh[0] + '.w', nameCFME1 + '.im')
        cmds.connectAttr(sh[0] + '.w', nameCFME2 + '.im')

        lofty = cmds.createNode('loft', n='rivetLoft1')
        cmds.setAttr(lofty + '.ic', s=2)
        cmds.setAttr(lofty + '.u', 1)
        cmds.setAttr(lofty + '.rsn', 1)

        cmds.connectAttr(nameCFME1 + '.oc', lofty + '.ic[0]')
        cmds.connectAttr(nameCFME2 + '.oc', lofty + '.ic[1]')

        # MAKE FOLLICLE
        folN = cmds.createNode('follicle')
        folT = cmds.listRelatives(folN, p=True)
        cmds.connectAttr(
            lofty + '.outputSurface', folN + '.inputSurface')
        cmds.connectAttr(
            nObj[0] + '.worldMatrix[0]', folN + '.inputWorldMatrix')
        # FINAL CONNECTIONS
        folT = cmds.listRelatives(folN, p=True)
        cmds.addAttr(
            folT[0], ln='U', at='double', k=True, min=0, max=1, dv=0.5)
        cmds.addAttr(
            folT[0], ln='V', at='double', k=True, min=0, max=1, dv=0.5)
        cmds.connectAttr(folT[0] + '.U', folN + '.parameterU')
        cmds.connectAttr(folT[0] + '.V', folN + '.parameterV')
        cmds.connectAttr(folN + '.outTranslate', folT[0] + '.translate')
        cmds.connectAttr(folN + '.outRotate', folT[0] + '.rotate')
        cmds.setAttr(folN + '.v', 0)
        return folT


def getMesh(ui):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning('Please select a mesh shape')
        return
    sh = cmds.listRelatives(sel[0], s=True)
    if sh:
        if cmds.nodeType(sh[0]) == 'mesh':
            cmds.textField(ui, e=True, tx=sel[0])
        else:
            cmds.warning('Please select a mesh shape')


def getGrooms(ui):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning('Please select one or more Groom Descriptions')
        return
    cmds.textScrollList(ui, e=True, ra=True)
    for s in sel:
        sh = cmds.listRelatives(s, s=True)
        if sh:
            if cmds.nodeType(sh[0]) == 'xgmDescription':
                cmds.textScrollList(ui, e=True, a=s)
            else:
                cmds.warning(
                    'Skipping ' + s + ' because it is not a xgen fur description')


def convCmd(ui):
    val = cmds.optionMenu(ui[1], q=True, v=True)
    grms = cmds.textScrollList(ui[2], q=True, ai=True)
    guide = cmds.checkBox(ui[4], q=True, v=True)
    jnts = cmds.checkBox(ui[5], q=True, v=True)
    if not grms:
        cmds.warning(
            'Please make sure to add one or more Groom Description to the UI')
        return
    if 'groom' not in val:
        radius = cmds.floatField(ui[3], q=True, v=True)
        dict = {
            'Only Curves not connected': 'False, False',
            'Static Curves connected to Mesh': 'False, True',
            'Dynamic Curves connected to Mesh': 'True, True'}
        if guide:
            dict = {
                'Only Guide Curves not connected': 'False, False',
                'Static Guide Curves connected to Mesh': 'False, True',
                'Dynamic Guide Curves connected to Mesh': 'True, True'}
        mesh = cmds.textField(ui[0], q=True, tx=True)
        if 'Only' not in val:
            if not mesh:
                cmds.warning(
                    'Please Make sure to add the mesh to connect the hair too')
                return
            sh = cmds.listRelatives(mesh, s=True)
            if not sh:
                cmds.warning(
                    'Please Make sure to add a mesh to connect the hair too')
                return
            if cmds.nodeType(sh[0]) != 'mesh':
                cmds.warning(
                    'Please Make sure to add a mesh to connect the hair too')
                return
        cmds.select(grms, r=True)
        exec(
            'import xgenToNhair;xgenToNhair.xgConvert("' + mesh + '", ' + str(radius) + ', ' + str(guide) + ', ' + str(jnts) + ', ' + dict[val] + ')')
    else:
        jnt = 0
        if guide:
            if jnts:
                jnt = 1
        mesh = 1
        if 'Single' not in val:
            mesh = 0
        for g in grms:
            cmds.xgmGeoRender(
                g, pb=True, convertSelected=0, combineMesh=mesh, useWidthRamp=1, insertWidthSpan=0,
                uvInTiles=1, uvLayoutType=0, uvTileSeparation=0.0, createStripJoints=0, createGuideJoints=jnts)
            cur = g + '_grp'
            cmds.rename(g + '_convert', cur)
            if jnts == 1:
                grpJ = g + '_joints_grp'
                if jnts:
                    hairJ = cmds.ls(cur, dag=True, type='joint')
                    if not cmds.objExists(grpJ):
                        cmds.group(em=True, n=grpJ)
                    cmds.parent(hairJ, grpJ)
                    for j in hairJ:
                        cmds.setAttr(j + '.radius', 0.005)
            # RENAME AND PARENT JOINTS IN CHAINS
            if jnts:
                cmds.xgmGeoRender(
                    g, pb=True, convertSelected=0, combineMesh=0, useWidthRamp=1, insertWidthSpan=0,
                    uvInTiles=1, uvLayoutType=0, uvTileSeparation=0.0, createStripJoints=0, createGuideJoints=0)
                hair = cmds.ls(g + '_convert', dag=True, type='transform')
                chain = int(cmds.polyEvaluate(hair[1], v=True) / 4)
                cmds.delete(g + '_convert')
                jointChain(grpJ, chain)
            if mesh == 1:
                resultM = cmds.listRelatives(cur, c=True)[0]
                cmds.parent(resultM, w=True)
                cmds.rename(resultM, g + '_mesh')
                cmds.delete(cur)
            else:
                resultM = cmds.listRelatives(cur, c=True)
                for x, r in enumerate(resultM):
                    cmds.rename(r, g + '_' + str(x + 1).zfill(3) + '_mesh')

    cmds.select(cl=True)


def changeOptionMenu(ui):
    mode = 1
    # CLEAN MENU
    mi = cmds.optionMenu(ui[0], q=True, ill=True)
    if mi:
        check = cmds.menuItem(mi[0], q=True, label=True)
        if 'Guide' in check:
            mode = 0
        for m in mi:
            cmds.deleteUI(m, mi=True)
    # POPULATE OPTIONMENUS
    modes = [
        'Only Curves not connected', 'Static Curves connected to Mesh',
        'Dynamic Curves connected to Mesh', 'Single Mesh for the groom',
        'Mesh for each Hair for the groom']
    if mode == 1:
        modes = [
            'Only Guide Curves not connected', 'Static Guide Curves connected to Mesh',
            'Dynamic Guide Curves connected to Mesh']
    for m in modes:
        cmds.menuItem(label=m, p=ui[0])
        cmds.checkBox(ui[1], e=True, en=mode)
        cmds.text(ui[2], e=True, en=mode)


def xUI():
    if cmds.window('winXgenUI', q=True, ex=True):
        cmds.deleteUI('winXgenUI')
    win = cmds.window('winXgenUI', t='xGen to nHair', rtf=True)
    # UI
    frT = cmds.formLayout()
    # UI ELEMENTS
    butM = cmds.button(l='Get mesh', p=frT, en=True)
    mTx = cmds.textField(p=frT, en=True)
    butG = cmds.button(l='Get Groom Descriptions', p=frT)
    rtx = cmds.text('Hair default width', p=frT)
    gTx = cmds.text('Make Guide', p=frT)
    cbg = cmds.checkBox(l='', v=True)
    jTx = cmds.text('Make Guide Joints', en=False, p=frT)
    cbj = cmds.checkBox(l='', en=False, v=False, p=frT)
    rf = cmds.floatField(v=0.0025, p=frT)
    omM = cmds.optionMenu(en=True, p=frT)
    tsL = cmds.textScrollList(p=frT)
    butD = cmds.button(l='Let\'s do it', p=frT)
    # FORMALYOUT ARRANGMENT
    cmds.formLayout(
        frT, e=True,
        af=[
            (butM, 'top', 5), (butM, 'left', 5),
            (butG, 'left', 5), (butG, 'right', 5),
            (mTx, 'top', 5), (mTx, 'right', 5),
            (rtx, 'left', 5),
            (gTx, 'left', 5),
            (cbg, 'right', 5),
            (jTx, 'left', 5),
            (cbj, 'right', 5),
            (rf, 'right', 5),
            (omM, 'left', 5), (omM, 'right', 5),
            (tsL, 'left', 10), (tsL, 'right', 10),
            (butD, 'left', 5), (butD, 'bottom', 5), (butD, 'right', 5)],
        ap=[
            (butM, 'right', 0, 50),
            (gTx, 'right', 0, 50),
            (jTx, 'right', 0, 50),
            (rtx, 'right', 0, 50)],
        ac=[
            (butG, 'top', 5, butM),
            (mTx, 'left', 5, butM),
            (tsL, 'top', 10, butG), (tsL, 'bottom', 15, rtx),
            (rtx, 'bottom', 5, gTx),
            (rf, 'bottom', 5, cbg), (rf, 'left', 5, rtx),
            (gTx, 'bottom', 5, jTx),
            (cbg, 'bottom', 5, cbj), (cbg, 'left', 5, gTx),
            (jTx, 'bottom', 5, omM),
            (cbj, 'bottom', 5, omM), (cbj, 'left', 5, jTx),
            (omM, 'bottom', 5, butD)])
    # POPULATE OPTIONMENUS
    changeOptionMenu([omM, cbj, jTx])
    # ADD COMMANDS TO UI
    cmds.checkBox(
        cbg, e=True,
        cc='xgenToNhair.changeOptionMenu(["' + omM + '", "' + cbj + '", "' + jTx + '"])')
    cmds.button(butM, e=True, c='xgenToNhair.getMesh("' + mTx + '")')
    cmds.button(butG, e=True, c='xgenToNhair.getGrooms("' + tsL + '")')
    cmds.textScrollList(
        tsL, e=True,
        dcc='cmds.textScrollList("' + tsL + '", e=True, ri=cmds.textScrollList("' + tsL + '", q=True, si=True)[0])')
    cmds.button(
        butD, e=True,
        c='xgenToNhair.convCmd(["' + mTx + '", "' + omM + '", "' + tsL + '", "' + rf + '", "' + cbg + '", "' + cbj + '"])')
    # show window and size it
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[280, 350])
