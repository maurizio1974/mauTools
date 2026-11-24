'''----------------------------------------------------------------------

DEFORMER VERTEX EXPORT/IMPORT UTILITY

Date = 28/10/2018
User = Maurizio Giglioli
Update =
        28/10/2018 Initial Commit

----------------------------------------------------------------------'''

import os
import json
import maya.mel as mel
import maya.cmds as cmds
from pprint import pprint

# VERTEX MAP -------------------------------------------------------------------
'''
USAGE
vertexDefUtil.nExportVtx('muscle_nCloth', ['inputAttractPerVertex'], 'nuscleus', 'Daisy', 'v003')
vertexDefUtil.nImportVtx('muscle_nCloth', ['inputAttractPerVertex'], 'nuscleus', 'Daisy', 'v003')
'''
# EXPORT


def nExportVtx(objS, vtxm, asset, mapType, version):
    # ACTIVE DIRECTORY
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(ws, 'export', mapType, asset, version)
    if not os.path.isdir(export):
        os.makedirs(export)
        cmds.warning('Created this directory ' + export)
    map = {}
    for v in vtxm:
        info = {}
        node = objS + '.' + v
        ia = str(cmds.getAttr(node))
        if ia:
            info[len(ia)] = ia
            map[node] = info
    # JASON FILE
    jFile = os.path.join(export, objS + '.json').replace('\\', '/')
    # SAVE TO FILE
    with open(jFile, 'w') as outF:
        json.dump(map, outF)
    print('Data saved to this file: ' + jFile)


def nImportVtx(objS, vtxm, asset, mapType, version):
    # ACTIVE DIRECTORY
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(ws, 'export', mapType, asset, version)
    # JASON FILE
    jFile = os.path.join(export, objS + '.json').replace('\\', '/')
    # LOAD THE DATA
    data = {}
    if os.path.isfile(jFile):
        with open(jFile) as jf:
            data = json.load(jf)
        for d in list(data.keys()):
            cmd = 'cmds.setAttr('
            if cmds.objExists(d):
                for dd in list(data[d].keys()):
                    cmd += '\'' + d + '\', ' + \
                        data[d][dd] + ', ' + \
                        str(dd) + ', type=\'doubleArray\')'
                    exec(cmd)
        print('Data loaded from this file: ' + jFile)

# DEFORMER WEIGHTS -------------------------------------------------------------
# EXPORT


def deformersWgt_UI():
    win = 'deformerWeigths_WIN'
    if cmds.window(win, q=True, ex=True):
        cmds.deleteUI(win)

    win = cmds.window('deformerWeigths_WIN', t='Deformer Weigths Utility')
    fr = cmds.formLayout(p=win)
    txL = cmds.text(l='version', w=100, p=fr)
    txV = cmds.textField(tx='v001', w=100, p=fr)
    cb = cmds.checkBox(v=False, l='Force over write', p=fr)
    btM = cmds.button(l='Select Mesh', w=100)
    txM = cmds.textField(p=fr)
    om = cmds.optionMenu(p=fr, w=100)
    tx = cmds.textField(p=fr)
    bt = cmds.button(l='Save weigths', p=fr)
    btCEP = cmds.button(l='Set Export Custom Path', w=100, p=fr)
    omI = cmds.optionMenu(p=fr, w=100)
    txI = cmds.textField(p=fr)
    btI = cmds.button(l='Load weigths', p=fr)
    btCIP = cmds.button(l='Set Import Custom Path', w=100, p=fr)

    cmds.formLayout(
        fr,
        e=True,
        af=[
            (txL, 'top', 10), (txL, 'left', 5),
            (txV, 'top', 10),
            (cb, 'top', 10),
            (btM, 'left', 5),
            (txM, 'right', 5),
            (om, 'left', 5),
            (tx, 'right', 5),
            (bt, 'left', 5), (bt, 'right', 5),
            (btCEP, 'left', 5), (btCEP, 'right', 5),
            (omI, 'left', 5),
            (txI, 'right', 5),
            (btI, 'left', 5), (btI, 'right', 5),
            (btCIP, 'left', 5), (btCIP, 'right', 5)],
        ac=[
            (txV, 'left', 5, txL),
            (cb, 'left', 5, txV),
            (btM, 'top', 5, txV),
            (txM, 'top', 5, txV), (txM, 'left', 5, btM),
            (tx, 'top', 5, txM), (tx, 'left', 5, om),
            (om, 'top', 5, btM),
            (bt, 'top', 5, tx),
            (btCEP, 'top', 5, bt),
            (omI, 'top', 10, btCEP),
            (txI, 'top', 10, btCEP), (txI, 'left', 5, omI),
            (btI, 'top', 5, txI),
            (btCIP, 'top', 5, btI)])

    # ADD COMMANDS TO UI
    cmdE = 'vertexDefUtil.showExportPath(["' + tx + \
        '", "' + txI + '"], "' + txV + '", "' + om + '")'
    cmdO = 'vertexDefUtil.getDeformers("' + txM + '", "' + omI + \
        '", cmds.optionMenu("' + om + '", q=True, v=True));' + cmdE
    cmdI = 'vertexDefUtil.populateDeformers("' + om + \
        '", vertexDefUtil.getDeformerSel("' + txV + '"))'
    cmdB = 'cmds.textField("' + txM + '", e=True, tx=vertexDefUtil.getDeformerSel("' + \
        txV + '"));' + cmdI + ';' + cmdO
    cmds.button(btM, e=True, c=cmdB)
    cmds.optionMenu(om, e=True, cc=cmdO)

    cmds.textField(txV, e=True, cc=cmdE)

    cmdExport = 'vertexDefUtil.exportDeform(cmds.optionMenu("' + \
        om + '", q=True, v=True), '
    cmdExport += 'cmds.textField("' + txV + \
        '", q=True, tx=True), cmds.checkBox("' + cb + '", q=True, v=True))'
    cmds.button(bt, e=True, c=cmdExport)
    cmdImport = 'vertexDefUtil.importDeform(cmds.optionMenu("' + \
        om + '", q=True, v=True), '
    cmdImport += 'cmds.textField("' + txV + '", q=True, tx=True))'
    cmds.button(btI, e=True, c=cmdImport)

    cmdEC = 'cmds.textField("' + tx + \
        '", e=True, tx=vertexDefUtil.outBrowser(3))'
    cmds.button(btCEP, e=True, c=cmdEC)
    cmdIC = 'cmds.textField("' + txI + \
        '", e=True, tx=vertexDefUtil.outBrowser(3))'
    cmds.button(btCIP, e=True, c=cmdIC)

    # ADD PRESETS TO UI
    pp = cmds.popupMenu('versionPP', p=txV)
    uiVC = '"' + tx + '", "' + txI + '", "' + txV + '", "' + om + '"'
    cmdVD = 'vertexDefUtil.versionFromDir("' + tx + '", "' + txI + '", "' + txV + '", "' + om + '")'
    cmds.menuItem(l='+5', p=pp, c='vertexDefUtil.versioningCtrl(' + uiVC + ', "+", 5)')
    cmds.menuItem(l='+2', p=pp, c='vertexDefUtil.versioningCtrl(' + uiVC + ', "+", 2)')
    cmds.menuItem(l='+1', p=pp, c='vertexDefUtil.versioningCtrl(' + uiVC + ', "+", 1)')
    cmds.menuItem(l='Get From directory', p=pp, c=cmdVD)
    cmds.menuItem(l='-1', p=pp, c='vertexDefUtil.versioningCtrl(' + uiVC + ', "-", 1)')
    cmds.menuItem(l='-2', p=pp, c='vertexDefUtil.versioningCtrl(' + uiVC + ', "-", 2)')
    cmds.menuItem(l='-5', p=pp, c='vertexDefUtil.versioningCtrl(' + uiVC + ', "-", 5)')

    cmds.showWindow(win)
    cmds.window(win, e=True, w=600, h=240)
    showExportPath([tx, txI], txV, om)

def versionFromDir(tx, txI, txV, om):
    idxs = []
    loc = cmds.textField(tx, q=True, tx=True)
    if not os.path.isdir(loc):
        cmds.warning('directory doesn\'t exists:' + loc)
        return
    loc = loc.replace('/' + loc.split('/')[-1], '')
    files = os.listdir(loc)
    if not files:
        cmds.warning('No version in this directory:' + loc)
        return
    for f in files:
        index = int(list(filter(str.isdigit, str(f))))
        idxs.append(index)
    out = 'v' + str(max(idxs)).zfill(3)
    cmds.textField(txV, e=True, tx=out)
    showExportPath([tx, txI], txV, om)


def versioningCtrl(tx, txI, txV, om, mode, val):
    info = str(cmds.textField(txV, q=True, tx=True))
    index = int(list(filter(str.isdigit, info)))
    if mode == '+':
        index = index + val
    elif mode == '-':
        index = index - val
    out = 'v' + str(index).zfill(3)
    cmds.textField(txV, e=True, tx=out)
    showExportPath([tx, txI], txV, om)


def outBrowser(mode):
    out = ''
    filter = "Maya ASCII (*.xml);;"
    r = cmds.fileDialog2(
        ff=filter,
        cap='Deformer Weight Destination',
        dir=cmds.workspace(q=True, act=True),
        fm=mode,
        ds=True)
    if r:
        out = r[0]
    return out


def populateDeformers(om, mesh=None):
    if mesh:
        menuI = []
        deformers = [
            'blendShape', 'skinCluster', 'deltaMush',
            'tension', 'cluster', 'ffd', 'shrinkWrap',
            'wire']
        # CLEAN OPTION MENU
        mi = cmds.optionMenu(om, q=True, ill=True)
        if mi:
            for m in mi:
                if cmds.menuItem(m, q=True, ex=True):
                    cmds.deleteUI(mi)

        # GET DEFORMERS TYPE ON THE OBJECT
        his = cmds.listHistory(mesh)
        if his:
            for h in sorted(his):
                for df in deformers:
                    if cmds.nodeType(h) == df:
                        menuI.append(df)
        # POPULATE OPTION MENU
        if menuI:
            menuI = list(set(menuI))
            for m in menuI:
                cmds.menuItem(l=m, p=om)


def getDeformerSel(txV):
    version = cmds.textField(txV, q=True, tx=True)
    if not version:
        cmds.confirmDialog(
            t='error', m='please make sure there is a version on the field')
        return
    out = ''
    sel = cmds.ls(sl=True)
    if sel:
        sh = cmds.listRelatives(sel[0], s=True)
        if sh:
            if cmds.nodeType(sh[0]) == 'mesh':
                return sel[0]


def getDeformers(txM, omI, df):
    menuI, his = [], []
    mesh = cmds.textField(txM, q=True, tx=True)
    if not mesh:
        cmds.confirmDialog(t=Error, m='No Mesh in the ui, skipping ....')
        return
    his = cmds.listHistory(mesh)
    # CLEAN OPTION MENU
    mi = cmds.optionMenu(omI, q=True, ill=True)
    if mi:
        for m in mi:
            if cmds.menuItem(m, q=True, ex=True):
                cmds.deleteUI(mi)
    # GET DEFORMERS TYPE ON THE OBJECT
    if his:
        for h in sorted(his):
            if cmds.nodeType(h) == df:
                menuI.append(h)
    # POPULATE OPTION MENU
    if menuI:
        cmds.menuItem(l='All', p=omI)
        for m in menuI:
            cmds.menuItem(l=m, p=omI)


def showExportPath(tx, txV, om):
    export = ''
    version = cmds.textField(txV, q=True, tx=True)
    deform = cmds.optionMenu(om, q=True, v=True)
    if not deform:
        deform = 'default'
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(ws, 'export/weights/', deform, version).replace('\\', '/')
    for t in tx:
        cmds.textField(t, e=True, tx=export)
    return export


# EXPORT
def exportDeform(deform, version, f=None):
    nodes = []
    # GET CURRENT SELECTION
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    for s in sel:
        his = cmds.listHistory()
        for h in his:
            if cmds.nodeType(h) == deform:
                nodes.append(h)
    if not nodes:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    # CLEAN DUPLICATES
    nodes = list(set(nodes))
    # MAKE EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(
        ws, 'export/weights/', deform, version).replace('\\', '/')
    if not os.path.isdir(export):
        os.makedirs(export)
        cmds.warning('Created this directory ' + export)
    for n in nodes:
        nex = n.replace(':', '_')
        current = os.path.join(export, nex + ".xml")
        if f:
            print('Exported deformer weights for ' + n + ' of type ' + deform)
            cmds.deformerWeights(nex + ".xml", export=True,
                                 deformer=n, path=export)
        else:
            if os.path.isfile(current):
                result = cmds.confirmDialog(
                    t='Watch it', m='This file already exists:\n' + current,
                    b=['Over Write', 'Skip'], db='Skip', cb='Skip', ds='Skip')
                if result == 'Over Write':
                    print('Exported deformer weights for ' + n + ' of type ' + deform)
                    cmds.deformerWeights(
                        nex + ".xml", export=True, deformer=n, path=export)
                else:
                    cmds.warning(
                        n + ' Skipped because \n' + deform + ' file is there already')
            else:
                print('Exported deformer weights for ' + n + ' of type ' + deform)
                cmds.deformerWeights(
                    nex + ".xml", export=True, deformer=n, path=export)


# IMPORT
def importDeform(deform, version):
    nodes = []
    # GET CURRENT SELECTION
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    for s in sel:
        his = cmds.listHistory()
        for h in his:
            if cmds.nodeType(h) == deform:
                nodes.append(h)
    if not nodes:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    # CLEAN DUPLICATES
    nodes = list(set(nodes))
    # GET EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    imp = os.path.join(
        ws, 'export/weights/', deform, version).replace('\\', '/')
    for n in nodes:
        nFile = n.replace(':', '_') + '.xml'
        if not os.path.isfile(os.path.join(imp, nFile)):
            cmds.warning('This deformer ' + n + ' doesn\'t exist ' + nFile)
            return
        cmds.deformerWeights(
            nFile, im=True, deformer=n, method='index', path=imp)
        print('Imported deformer weights for ' + n + ' of type ' + deform)


# BLEND SHAPE IMPORT EXPORT
def mirrorBS(objSet, geo, deformer, index, axe, dir, clear):
    orig = geo
    his = cmds.listHistory(geo)
    for h in his:
        if 'Orig' in h:
            orig = h
    print('-' * 50 ,'\n', orig)

    check = cmds.sets('mirror', q=True)
    cmds.select(check, r=True)
    temp = cmds.ls(sl=True, fl=True)
    mir = []
    for t in temp:
        pos = cmds.pointPosition(t)
        if axe == 'x':
            if dir == '+':
                if pos[0] > 0:
                    mir.append(t)
            else:
                if pos[0] < 0:
                    mir.append(t)
        elif axe == 'y':
            if dir == '+':
                if pos[1] > 0:
                    mir.append(t)
            else:
                if pos[1] < 0:
                    mir.append(t)
        elif axe == 'z':
            if dir == '+':
                if pos[2] > 0:
                    mir.append(t)
            else:
                if pos[2] < 0:
                    mir.append(t)
    cmds.select(cl=True)
    lista = []
    for l in mir:
        cur = l.split('[')[-1].replace(']', '')
        lista.append(cur)

    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    # vtx = cmds.polyEvaluate(geo, v=True)
    cpm = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(orig + '.worldMesh', cpm + '.inMesh', f=True)
    cmds.progressBar(
        gMainProgressBar, e=True, bp=True,
        ii=True, st='Vertexes Left to mirror from ' + orig, max=len(lista))
    weights = cmds.getAttr(deformer + '.inputTarget[0].inputTargetGroup[' + str(index) + '].targetWeights')[0]
    for x in lista:
        x = int(x)
        cw = round(weights[x], 2)
        if cw > 1:
            print(cw)
        pos = cmds.pointPosition(orig + '.vtx[' + str(x) + ']')
        mir = [pos[0] * -1, pos[1], pos[2]]
        if axe == 'y':
            mir = [pos[0], pos[1] * -1, pos[2]]
        elif axe == 'z':
            mir = [pos[0], pos[1], pos[2] * -1]
        if clear:
            cmds.setAttr(deformer + '.inputTarget[0].inputTargetGroup[' + str(index) + '].targetWeights[' + str(x) + ']', 0)
        cmds.setAttr(cpm + '.inPosition', mir[0], mir[1], mir[2])
        out = cmds.getAttr(cpm + '.closestVertexIndex')
        cmds.setAttr(deformer + '.inputTarget[0].inputTargetGroup[' + str(index) + '].targetWeights[' + str(out) + ']', cw)
        cmds.progressBar(gMainProgressBar, e=True, s=1)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)
    cmds.delete(cpm)

# from pprint import pprint

# mesh = 'pSphere1'
# master, out = {}, {}
# defo = 'blendShape1'
# weights = cmds.getAttr(defo + '.inputTarget[0].inputTargetGroup[0].targetWeights')[0]
# vtx = cmds.polyEvaluate(mesh, v=True)
# for x in range(0, vtx):
#     out[x] = weights[x]
# master[mesh] = out

# cmd = 'cmds.setAttr("' + defo + '.inputTarget[0].inputTargetGroup[0].targetWeights[0:' + str(vtx-1) + ']", '
# for m in master.keys():
#     for w in master[m].keys():
#         cmd += str(master[m][w]) + ', '
# cmd += 'size=' + str(vtx) + ')'
# print cmd
# eval(cmd)

def exportBS(mesh, version):
    out, data, vtxs, inv = {}, [], [], []
    # MAKE EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(
        ws, 'export/weights/blendShape', version).replace('\\', '/')
    if not os.path.isdir(export):
        os.makedirs(export)
        cmds.warning('Created this directory ' + export)
    his = cmds.listHistory(mesh)
    for bs in his:
        if cmds.nodeType(bs) == 'blendShape':
            trgs = len(cmds.blendShape(bs, q=True, w=True))
            for index in range(0, trgs):
                attr = [
                    bs,
                    'inputTarget[0]',
                    'inputTargetGroup[' + str(index) + ']',
                    'targetWeights']
                bIN = cmds.getAttr('.'.join(attr))[0]
                vb = cmds.listAttr('.'.join(attr), multi=True)
                tg = cmds.blendShape(bs, q=True, t=True)
                if tg:
                    vCount = cmds.polyEvaluate(tg[0], v=True)
                    if vb:
                        for v in vb:
                            ind = v.split('.')[-1].split('[')[1].split(']')[0]
                            vtxs.append(int(ind))
                    for x in range(vCount):
                        inv.append(x)
                    if len(vtxs) > 0:
                        inv = [x for x in inv if x not in vtxs]
                    for x in range(len(bIN)):
                        data.append("cmds.setAttr('" + '.'.join(attr) +
                                    "[" + str(vtxs[x]) + "]', " + str(bIN[x]) + ")")
                    for x in inv:
                        data.append(
                            "cmds.setAttr('" + '.'.join(attr) + "[" + str(x) + "]', 0)")
                else:
                    print('No target found on this blendShape: ' + bs)
            out[bs] = data
    jFile = os.path.join(export, mesh + '_bsw.json')
    with open(jFile, 'w') as outfile:
        json.dump(out, outfile)
    print(jFile)


def importBS(mesh, version, deb=None):
    data = {}
    # GET EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(
        ws, 'export/weights/blendShape', version).replace('\\', '/')
    jFile = os.path.join(export, mesh + '_bsw.json')
    with open(jFile) as inFile:
        data = json.load(inFile)
    for d in list(data.keys()):
        print('=' * 100)
        print('Importing weights on mesh: ' + mesh + ' for blendShape: ' + d)
        if cmds.objExists(d):
            for cmd in data[d]:
                exec(cmd)
                if deb:
                    print(cmd)
        else:
            'The specified blendShape ' + d + ' is not in the scene'
        print('-' * 100)


# IMPORT AND SWAP TO ANOTHER ASSET ( NAMESPACE BASED )
def importDeformSwap(deform, version, ns1, ns2):
    nodes = []
    # GET CURRENT SELECTION
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    for s in sel:
        his = cmds.listHistory()
        for h in his:
            if cmds.nodeType(h) == deform:
                nodes.append(h)
    if not nodes:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    # CLEAN DUPLICATES
    nodes = list(set(nodes))
    # GET EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    imp = os.path.join(
        ws, 'export/weights/', deform, version).replace('\\', '/')
    for n in nodes:
        nName = n.replace(ns2, ns1)
        nFile = nName.replace(':', '_') + '.xml'
        if not os.path.isfile(os.path.join(imp, nFile)):
            cmds.warning('This deformer ' + n + ' doesn\'t exist ' + nFile)
        else:
            cmds.deformerWeights(
                nFile, im=True, deformer=n, method='index', path=imp)
            print('Imported deformer weights for ' + n + ' of type ' + deform)


def transferDeform(defSrc, defDes, meshSrc, meshDes, set):
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    out = []
    cpm = 'transfer_cpm____temp'
    if not cmds.objExists(cpm):
        cmds.createNode('closestPointOnMesh', n=cpm)
        cmds.connectAttr(meshDes + '.worldMesh', cpm + '.inMesh')
    if set:
        areas = cmds.sets(set, q=True)
        cmds.select(areas, r=True)
        area = cmds.ls(sl=True, fl=True)
        cmds.select(cl=True)
        for a in area:
            index = a.split('[')[-1][:-1]
            out.append(index)
    else:
        vtxs = cmds.polyEvaluate(origMesh, v=True)
        for v in range(0, vtxs):
            index = v.split('[')[-1][:-1]
            out.append(index)
    cmds.progressBar(gMainProgressBar, e=True, bp=True, ii=True, st='Vertex left: ' + str(len(out)), max=len(out))
    for y, x in enumerate(out):
        if cmds.progressBar(gMainProgressBar, q=True, ic=True):
            break
        wg = cmds.getAttr(defSrc + '.weightList[0].weights[' + str(x) + ']')
        if wg > 0:
            pos = cmds.pointPosition(meshSrc + '.vtx[' + str(x) + ']')
            cmds.setAttr(cpm + '.inPosition', pos[0], pos[1], pos[2])
            vtx = cmds.getAttr(cpm + '.closestVertexIndex')
            cmds.setAttr(defDes + '.weightList[0].weights[' + str(vtx) + ']', wg)
            cmds.progressBar(gMainProgressBar, e=True, s=1)
            cmds.progressBar(gMainProgressBar, e=True, st='Vertex left: ' + str(len(out) - y))
        else:
            cmds.progressBar(gMainProgressBar, e=True, s=1)
            cmds.progressBar(gMainProgressBar, e=True, st='Vertex left: ' + str(len(out) - y))
    if cmds.objExists(cpm):
        cmds.delete(cpm)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)


# SELECTIONS -------------------------------------------------------------------
# IMPORT
def importSel(version, name):
    data = {}
    sel = cmds.ls(sl=True, fl=True)
    if not sel:
        cmds.warning('Please select the mesh to import the selection to')
        return
    if len(sel[0].split('.')) > 1:
        obj = sel[0].split('.')[0]
    else:
        obj = sel[0]
    # GET IMPORT PATH
    ws = cmds.workspace(q=True, act=True)
    imp = os.path.join(
        ws, 'export/selections', version).replace('\\', '/')
    # READ FILE
    jFile = os.path.join(imp, name + '.' + version +
                         '.json').replace('\\', '/')
    if not os.path.isfile(jFile):
        cmds.warning('This file doesn\'t exists check your project\n' + jFile)
        return
    with open(jFile, 'r') as inF:
        data = json.load(inF)
    cmds.select(cl=True)
    if cmds.objExists(name):
        if cmds.nodeType(name) == 'objectSet':
            cmds.delete(name)
    cmds.sets(em=True, n=name)
    cmds.addAttr(name, ln='mSet', dt='string')
    for d in list(data.keys()):
        for t in list(data[d].keys()):
            for index in data[d][t]:
                current = obj + '.' + t + '[' + str(index) + ']'
                cmds.select(current, add=True)
                cmds.sets(current, add=name)
    cmds.select(sel[0])


# EXPORT
def exportSel(version, name):
    data, out, info, obj = {}, [], {}, ''
    sel = cmds.ls(sl=True, fl=True)
    if sel:
        if len(sel[0].split('.')) > 1:
            obj = sel[0].split('.')[0]
            tipo = sel[0].split('.')[-1].split('[')[0]
            for s in sel:
                index = s.split('.')[-1].replace(tipo,
                                                 '').replace('[', '').replace(']', '')
                out.append(index)
            data[tipo] = out
            info[obj] = data
    # pprint(info)
    # MAKE EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(
        ws, 'export/selections', version).replace('\\', '/')
    if not os.path.isdir(export):
        os.makedirs(export)
        cmds.warning('Created this directory ' + export)
    # SAVE TO FILE
    jFile = os.path.join(export, name + '.' + version + '.json')
    with open(jFile, 'w') as outF:
        json.dump(info, outF)


# GEO --------------------------------------------------------------------------
# EXPORT
def exportObjs(asset, version):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning(
            'Please select one or more geoemtry meshes to be exported')
        return
    # MAKE EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    out = os.path.join(
        ws, 'export/objs', asset,  version).replace('\\', '/')
    if not os.path.isdir(out):
        os.makedirs(out)
    for s in sel:
        sh = cmds.listRelatives(s, s=True, ni=True)
        if sh:
            if cmds.nodeType(sh[0]) == 'mesh':
                cmds.select(s, r=True)
                name = s + '_' + version + '.obj'
                exp = os.path.join(out, name).replace('\\', '/')
                cmds.file(
                    exp, force=True,
                    options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
                    typ="OBJexport", pr=True, es=True)
            else:
                cmds.warning('Skipping this node ' + s +
                             ' because it is not a mesh')
    cmds.select(sel, r=True)
    cmds.warning('ALL MESHES EXPORTED HERE:\n' + out)


# ATTRIBUTE LOCKER
def outLockAttr_UI():
    if cmds.window('outLockAttr_WIN', ex=1) == 1:
        cmds.deleteUI('outLockAttr_WIN', window=True)

    win = cmds.window('outLockAttr_WIN', t='Outpost Attrs Locker')

    fr = cmds.formLayout()
    btr = cmds.button(l='On', w=40, h=18)
    cbT = cmds.checkBoxGrp(ct4=['left', 'left', 'left', 'left'], cw4=[
                           60, 40, 40, 40], v1=1, v2=1, v3=1, ncb=3, l='Tra ', la3=['X', 'Y', 'Z'])
    brt = cmds.button(l='On', w=40, h=18)
    cbR = cmds.checkBoxGrp(ct4=['left', 'left', 'left', 'left'], cw4=[
                           60, 40, 40, 40], v1=1, v2=1, v3=1, ncb=3, l='Rot ', la3=['X', 'Y', 'Z'])
    bsc = cmds.button(l='On', w=40, h=18)
    cbZ = cmds.checkBoxGrp(ct4=['left', 'left', 'left', 'left'], cw4=[
                           60, 40, 40, 40], v1=1, v2=1, v3=1, ncb=3, l='Sca ', la3=['X', 'Y', 'Z'])
    bv = cmds.button(l='Off', w=40, h=18)
    cbV = cmds.checkBoxGrp(ct2=['left', 'left'], cw2=[60, 40], l='Vis ', v1=0)
    b = cmds.button(
        l='Set lock Pref',
        c='vertexDefUtil.mSetLockAttr('
        '[cmds.checkBoxGrp("' + cbT + '",q = 1, v1 = 1),'
        'cmds.checkBoxGrp("' + cbT + '",q = 1, v2 = 1),'
        'cmds.checkBoxGrp("' + cbT + '",q = 1, v3 = 1)],'
        '[cmds.checkBoxGrp("' + cbR + '",q = 1, v1 = 1),'
        'cmds.checkBoxGrp("' + cbR + '",q = 1, v2 = 1),'
        'cmds.checkBoxGrp("' + cbR + '",q = 1, v3 = 1)],'
        '[cmds.checkBoxGrp("' + cbZ + '",q = 1, v1 = 1),'
        'cmds.checkBoxGrp("' + cbZ + '",q = 1, v2 = 1),'
        'cmds.checkBoxGrp("' + cbZ + '",q = 1, v3 = 1)],'
        '[cmds.checkBoxGrp("' + cbV + '",q = 1, v1 = 1)])'
    )
    br = cmds.button(l='Remove lock Prefs', c='vertexDefUtil.mUnSetLockAttr()')
    bg = cmds.button(l='Create from current selection',
                     c='vertexDefUtil.mBuildLocking()')
    s = cmds.separator()
    cmds.button(
        btr, e=True,
        c='vertexDefUtil.uiSwitch("' + btr + '", "' + cbT + '", "multi")')
    cmds.button(
        brt, e=True,
        c='vertexDefUtil.uiSwitch("' + brt + '", "' + cbR + '", "multi")')
    cmds.button(
        bsc, e=True,
        c='vertexDefUtil.uiSwitch("' + bsc + '", "' + cbZ + '", "multi")')
    cmds.button(
        bv, e=True,
        c='vertexDefUtil.uiSwitch("' + bv + '", "' + cbV + '", "single")')
    cbH = cmds.checkBox(
        'visilock', l='Visible',
        onc='cmds.checkBox("visilock", e=True, l="hidden")',
        ofc='cmds.checkBox("visilock", e=True, l="Visible")')
    bl = cmds.button(
        l='lock',
        c='vertexDefUtil.mDoLockAttr(cmds.checkBox("' + cbH + '",q = 1, v = 1),"on")', w=50)
    bu = cmds.button(
        l='unlock',
        c='vertexDefUtil.mDoLockAttr(cmds.checkBox("' + cbH + '",q = 1, v = 1),"off")', w=50)
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (btr, 'left', 5), (btr, 'top', 10),
            (cbT, 'top', 10),
            (brt, 'left', 5),
            (bsc, 'left', 5),
            (bv, 'left', 5),
            (b, 'left', 5), (b, 'right', 0),
            (br, 'left', 5), (br, 'right', 0),
            (bg, 'left', 5), (bg, 'right', 0),
            (s, 'left', 5), (s, 'right', 0),
            (cbH, 'left', 10),
            (bl, 'left', 10),
            (bu, 'left', 10)],
        ac=[
            (cbT, 'left', 0, btr),
            (brt, 'top', 0, btr),
            (cbR, 'left', 0, brt), (cbR, 'top', 0, cbT),
            (bsc, 'top', 0, brt),
            (cbZ, 'left', 0, bsc), (cbZ, 'top', 0, cbR),
            (bv, 'top', 0, bsc),
            (cbV, 'left', 0, bv), (cbV, 'top', 0, cbZ),
            (b, 'top', 10, cbV),
            (br, 'top', 5, b),
            (bg, 'top', 5, br),
            (s, 'top', 10, bg),
            (cbH, 'top', 10, s),
            (bl, 'left', 10, cbH),
            (bl, 'top', 10, s),
            (bu, 'left', 5, bl),
            (bu, 'top', 10, s)
        ]
    )

    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[280, 225])


def uiSwitch(ui, cb, mode):
    if cmds.button(ui, q=True, l=True) == "Off":
        cmds.button(ui, e=True, l="On")
        cmds.checkBoxGrp(cb, e=True, v1=True)
        if mode == 'multi':
            cmds.checkBoxGrp(cb, e=True, v2=True)
            cmds.checkBoxGrp(cb, e=True, v3=True)
    else:
        cmds.button(ui, e=True, l="Off")
        cmds.checkBoxGrp(cb, e=True, v1=False)
        if mode == 'multi':
            cmds.checkBoxGrp(cb, e=True, v2=False)
            cmds.checkBoxGrp(cb, e=True, v3=False)


def mSetLockAttr(cbT, cbR, cbZ, cbV):
    sel = cmds.ls(sl=True, tr=True)
    if not len(sel) > 0:
        cmds.confirmDialog(t='Not Kick Ass', m='Nothing Selected !"')
        return
    if cbT[0]:
        cbT[0] = 'tx'
    if cbT[1]:
        cbT[1] = 'ty'
    if cbT[2]:
        cbT[2] = 'tz'

    if cbR[0]:
        cbR[0] = 'rx'
    if cbR[1]:
        cbR[1] = 'ry'
    if cbR[2]:
        cbR[2] = 'rz'

    if cbZ[0]:
        cbZ[0] = 'sx'
    if cbZ[1]:
        cbZ[1] = 'sy'
    if cbZ[2]:
        cbZ[2] = 'sz'

    if cbV[0]:
        cbV[0] = 'v'

    value = [
        cbT[0], cbT[1], cbT[2],
        cbR[0], cbR[1], cbR[2],
        cbZ[0], cbZ[1], cbZ[2],
        cbV[0]
    ]
    out = ''
    for v in value:  # Create the attribute string
        if v:
            out = out + ' ' + v

    for s in sel:
        if cmds.attributeQuery('outLocker', node=s, ex=1) == 0:
            if out:
                cmds.addAttr(s, ln='outLocker', dt='string')
                cmds.setAttr(
                    s + '.outLocker',
                    out.replace('[', '').replace(']', ''),
                    type='string', l=1)
        else:
            cmds.setAttr(s + '.outLocker', lock=0)
            cmds.setAttr(
                s + '.outLocker',
                out.replace('[', '').replace(']', ''),
                type='string')
            cmds.setAttr(s + '.outLocker', lock=1)


def mUnSetLockAttr():
    sel = cmds.ls(sl=True, tr=True)
    for s in sel:
        if not len(sel) > 0:
            cmds.confirmDialog(t='Not Kick Ass', m='Nothing Selected !"')
            return
        if cmds.attributeQuery('outLocker', node=s, ex=1) == 1:
            cmds.setAttr(s + '.outLocker', l=0)
            cmds.deleteAttr(s, at='outLocker')


def mDoLockAttr(state, switch):
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    sel = cmds.ls(sl=True, dag=True, tr=True)
    if not sel:
        cmds.confirmDialog(t='Not Kick Ass', m='Nothing Selected !"')
        return
    cmds.progressBar(gMainProgressBar, e=True, bp=True,
                     ii=True, st='Nodes left to do', max=len(sel))
    msg, attrs = 'locked', ''
    for s in sel:
        if cmds.progressBar(gMainProgressBar, q=True, ic=True):
            break
        if cmds.attributeQuery('outLocker', node=s, ex=1) == 1:
            attrs = cmds.getAttr(s + '.outLocker')
            if switch == 'on':
                for a in attrs.split(' '):
                    if len(a) >= 1:
                        cmds.setAttr(s + '.' + a, l=True)
                        if state == 1:
                            cmds.setAttr(s + '.' + a, k=False)
            elif switch == 'off':
                msg = 'unLocked'
                for a in attrs.split(' '):
                    if len(a) >= 1:
                        cmds.setAttr(s + '.' + a, l=False)
                        cmds.setAttr(s + '.' + a, k=True)
        cmds.progressBar(gMainProgressBar, e=True, s=1)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)
    print('Structure ' + msg)


def mBuildLocking():
    node = cmds.ls(sl=True)
    if not node:
        cmds.confirmDialog(
            t='Not Kick Ass',
            m='Please select the top node of the hierarchy you want to copy locking information from')
        return
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    sel = cmds.ls(node, dag=True, type='transform')
    cmds.progressBar(gMainProgressBar, e=True, bp=True,
                     ii=True, st='Nodes left to do', max=len(sel))
    attrs = ['t', 'r', 's', 'v']
    axes = ['x', 'y', 'z']
    cmd = 'import vertexDefUtil\n'
    for x, s in enumerate(sel):
        if cmds.progressBar(gMainProgressBar, q=True, ic=True):
            break
        cmd += 'cmds.select(\'' + s + '\', r=True)\n'
        cmd += 'vertexDefUtil.mSetLockAttr('
        for a in attrs:
            info = []
            if a != 'v':
                for ax in axes:
                    state = cmds.getAttr(s + '.' + a + ax, lock=True)
                    info.append(state)
            else:
                state = cmds.getAttr(s + '.' + a, lock=True)
                info = [state]
            if a == 'v':
                cmd += str(info)
            else:
                cmd += str(info) + ', '
        cmd += ')\n'
        # print s, len(info), info
        # print cmd
        exec(cmd)
        cmds.progressBar(gMainProgressBar, e=True, s=1)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)
    print('Locking Structure tagged')
