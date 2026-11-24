'''----------------------------------------------------------------------

OUPOST MESH TWEAK UTILITY

Date = 03/12/2018
User = Maurizio Giglioli
Update =
        11/12/2018 Added saving set up and reload
        10/12/2018 Added transfer of animation as well
        10/12/2018 Added transfer set up form one cow to the other
        03/12/2018 First Release

----------------------------------------------------------------------'''
import json
import maya.mel as mel
import maya.cmds as cmds
import maya.api.OpenMaya as om

def makeControl(name):
    out = []
    mel.eval('createImplicitVolume sphere;')
    sel = cmds.ls(sl=True)
    selT = cmds.listRelatives(sel[0], p=True)[0]
    cmds.rename(sel[0], name + 'Shape')
    cmds.rename(selT, name)
    out.append(name)
    return out

def do_tweak(nameC=None):
    grpM, deformMT, newCls, clss = '', '', '', []
    list = cmds.ls(sl=True, fl=True)
    if not list:
        cmds.confirmDialog(t='Error', m="Select a Mesh Face")
        return
    if len(list) > 1:
        cmds.confirmDialog(t='Error', m="Select only a Mesh Face at the time")
        return
    for l in list:
        if 'f[' not in l:
            cmds.confirmDialog(t='Error', m="Select a Mesh Face")
            return
        ns1 = l.replace(l.split(':')[-1], '')
        nObj = l.split('.')
        if '_geo' not in nObj[0]:
            cmds.confirmDialog(t='Oops', m='Please make sure to select a face on the rig mesh\nnot the deform mesh')
            return
        # NAME CLUSTERS
        if not nameC:
            nameC = ''
            result = cmds.promptDialog(
                t='Set tweak name', m='Enter Name:',
                b=['OK', 'Cancel'], db='OK', cb='Cancel', ds='Cancel')
            if result == 'OK':
                current = cmds.promptDialog(q=True, text=True)
                if current:
                    nameC = ns1 + current
                else:
                    cmds.warning('Add a name to the text')
                    return
            else:
                cmds.warning('Tweak Tool Stopped')
                return
        # MASTER GROUP
        name = nObj[0].replace('_geo', '_')
        grpM = name + 'tweak_grp'
        if not cmds.objExists(grpM):
            cmds.group(em=True, n=grpM)
        cmp = nObj[1].split('[')
        cmpIn = l.split('[')[1].split(']')
        sh = cmds.listRelatives(nObj[0], s=True, ni=True)
        startD = cmds.listConnections(sh[0] + '.inMesh', s=True, d=False, p=True)
        # PART FOR MESH OBJECTS
        if cmds.nodeType(sh[0]) == 'mesh' and cmp[0] == 'f':
            edges = []
            cmds.select(l)
            face = str(l.split('[')[-1].split(']')[0])
            mel.eval('PolySelectConvert 2')
            cur = [
                cmds.ls(sl=True, fl=True)[0],
                cmds.ls(sl=True, fl=True)[3]]
            ns = cur[0].split('.')[0].replace(cur[0].split(':')[-1], '')
            # PASS MESHES
            followM = name + 'follow_meshShape'
            followMT = name + 'follow_mesh'
            deformM = name + 'deform_meshShape'
            deformMT = name + 'deform_mesh'
            for m in [followM, deformM]:
                if not cmds.objExists(m):
                    cmds.createNode('mesh', n=m)
                    if m == followM:
                        cmds.connectAttr(startD[0], followM + '.inMesh')
                    elif m == deformM:
                        cmds.connectAttr(followM + '.worldMesh', deformM + '.inMesh')
                        cmds.connectAttr(deformM + '.worldMesh', sh[0] + '.inMesh', f=True)
                        cmds.parent(deformMT, grpM)
                        cmds.setAttr(followM + '.intermediateObject', 1)
                        cmds.parent(followM, deformMT, s=True, r=True)
                        cmds.delete(followMT)
            for c in cur:
                edges.append(c.replace(nObj[0], followMT))
            # MAKE FOLLICLE AND CLUSTER HANDLE)
            fol = tweakFol(edges, grpM, followM, nameC, face)
            index = len(cmds.ls(nameC + '*_grp')) + 1
            grpCtrl = cmds.group(em=True, n=nameC + str(index).zfill(3) + '_grp')
            ctrl = makeControl(nameC + str(index).zfill(3) + '_clh')
            # ADD EXTRA ATTRIBUTE TO CLUSTER
            cmds.addAttr(ctrl[0], ln='deformerName', dt='string')
            cmds.setAttr(ctrl[0] + '.deformerName', nameC + str(index).zfill(3) + '_cls', type='string')
            cmds.setAttr(ctrl[0] + '.deformerName', l=True)
            cmds.addAttr(ctrl[0], ln='deformerType', dt='string')
            cmds.setAttr(ctrl[0] + '.deformerType', 'cluster', type='string')
            cmds.setAttr(ctrl[0] + '.deformerType', l=True)
            cmds.addAttr(ctrl[0], ln='faceIndex', dt='string')
            cmds.setAttr(ctrl[0] + '.faceIndex', face, type='string')
            cmds.setAttr(ctrl[0] + '.faceIndex', l=True)
            # ORGANIZING
            cmds.parent(ctrl[0], grpCtrl)
            pc = cmds.parentConstraint(fol, grpCtrl)
            cmds.refresh()
            cmds.delete(pc)
            # REPARENTING
            cmds.parent(grpCtrl, fol)
            cmds.parent(fol, grpM)
            # MAKE CLUSTER
            cmds.select(deformMT, r=True)
            mel.eval('performCluster false;')
            cur = cmds.ls(sl=True)
            cls = cmds.listConnections(cur[0] + '.worldMatrix[0]', s=False, d=True)[0]
            clsS = cmds.listRelatives(cur[0], s=True, ni=True)[0]
            # MAKE INVERSE MATRIX
            cmds.connectAttr(ctrl[0] + '.worldMatrix[0]', cls + '.matrix', f=True)
            cmds.connectAttr(grpCtrl + '.worldInverseMatrix[0]', cls + '.bindPreMatrix', f=True)
            cmds.parent(clsS, ctrl[0], r=True, s=True)
            cmds.delete(cur[0])
            cmds.setAttr(clsS + '.v', 0)
            newCls = nameC + str(index).zfill(3) + '_cls'
            cmds.rename(cls, newCls)
            clss.append(newCls)
    # ISOLATE VIEW
    cmds.select(grpM, r=True)
    isolateView()
    # ACTIVATE ARTISAN
    context = 'artCowCtx'
    if not cmds.artAttrCtx(context, q=True, ex=True):
        cmds.artAttrCtx(context)
    cmds.setToolTo(context)
    cmds.refresh()
    mel.eval('artSetToolAndSelectAttr("artAttrCtx", "cluster.' + newCls + '.weights")')
    mel.eval('toolPropertyShow;')
    cmds.select(deformMT, r=True)
    # SET CLUSTER WEIGHT TO ZERO
    vtx = cmds.polyEvaluate(deformM, v=1) -1
    inweight = cmds.getAttr('{0}.weightList[0].weights[0:{1}]'.format(newCls, vtx))
    weight = []
    for w in inweight:
        weight.append(0.0)
    cmds.setAttr('{0}.weightList[0].weights[0:{1}]'.format(newCls, vtx), *weight, size=len(weight))
    cmds.select(deformMT, r=True)
    return ctrl[0]

def tweakFol(list, grpM, shape, nameC, face):
    ns = grpM.replace(grpM.split(':')[-1], '')
    nObj = list[0].split('.')
    # START PROCESS
    e1 = list[0].split('[')[1].split(']')
    e2 = list[1].split('[')[1].split(']')

    nameCFME1 = cmds.createNode(
        'curveFromMeshEdge',
        n='rCFME1')
    cmds.setAttr(nameCFME1 + '.ihi', 1)
    cmds.setAttr(nameCFME1 + '.ei[0]', int(e1[0]))
    nameCFME2 = cmds.createNode(
        'curveFromMeshEdge',
        n='rCFME2'
    )
    cmds.setAttr(nameCFME2 + '.ihi', 1)
    cmds.setAttr(nameCFME2 + '.ei[0]', int(e2[0]))
    cmds.connectAttr(shape + '.worldMesh', nameCFME1 + '.im')
    cmds.connectAttr(shape + '.worldMesh', nameCFME2 + '.im')

    lofty = cmds.createNode('loft', n='rivetLoft1')
    cmds.setAttr(lofty + '.ic', s=2)
    cmds.setAttr(lofty + '.u', 1)
    cmds.setAttr(lofty + '.rsn', 1)

    cmds.connectAttr(nameCFME1 + '.oc', lofty + '.ic[0]')
    cmds.connectAttr(nameCFME2 + '.oc', lofty + '.ic[1]')

    # MAKE FOLLICLE
    index = len(cmds.ls(nameC + '*_folShape*')) + 1

    folN = cmds.createNode('follicle', n=nameC + str(index).zfill(3) + '_folShape')
    folT = cmds.listRelatives(folN, p=True)
    cmds.connectAttr(
        lofty + '.outputSurface', folN + '.inputSurface')
    cmds.connectAttr(
        shape + '.worldMatrix[0]',
        folN + '.inputWorldMatrix'
    )
    cmds.setAttr(folN + '.v', 0)
    # FINAL CONNECTIONS
    folT = cmds.listRelatives(folN, p=True)
    cmds.addAttr(
        folT[0], ln='U', at='double', k=True, min=0, max=1, dv=0.5)
    cmds.addAttr(
        folT[0], ln='V', at='double', k=True, min=0, max=1, dv=0.5)
    cmds.connectAttr(folT[0] + '.U', folN + '.parameterU')
    cmds.connectAttr(folT[0] + '.V', folN + '.parameterV')
    cmds.connectAttr(folN + '.outTranslate', folT[0] + '.translate')
    mesh = ''
    cmds.connectAttr(folN + '.outRotate', folT[0] + '.rotate')
    return folT[0]

def selectWeights():
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(t='Oops', m='Please select a tweak controller')
        return
    if '_clh' not in sel[0]:
        cmds.confirmDialog(t='Oops', m='Please select a tweak controller')
        return
    ns = sel[0].replace(sel[0].split(':')[-1], '')
    clh = sel[0]
    cls = clh.replace('_clh', '_cls')
    mesh = []
    his = cmds.listHistory(cls + '.outputGeometry', f=True)
    for h in his:
        if cmds.nodeType(h) == 'mesh' and '_geo' in h:
            mesh.append(h.replace('Shape', ''))
    deformT = mesh[0].replace('_geo', '_deform_mesh')
    grpM = deformT.replace('_deform_mesh', '_tweak_grp')
    # ISOLATE VIEW
    cmds.select(grpM, r=True)
    isolateView()
    # ACTIVATE ARTISAN
    context = 'artCowCtx'
    if not cmds.artAttrCtx(context, q=True, ex=True):
        cmds.artAttrCtx(context)
    cmds.setToolTo(context)
    cmds.refresh()
    mel.eval('artSetToolAndSelectAttr("artAttrCtx", "cluster.' + cls + '.weights");')
    mel.eval('artAttrInitPaintableAttr;')
    mel.eval('artAttrPaintMenu( "artAttrListPopupMenu" );')
    mel.eval('artAttrValues artAttrContext;')
    mel.eval('toolPropertyShow;')
    mel.eval('editMenuUpdate MayaWindow|mainEditMenu;')
    mel.eval('changeToolIcon;')
    mel.eval('dR_contextChanged;')
    mel.eval('currentCtx;')
    mel.eval('dR_updateToolSettings;')
    cmds.select(deformT, r=True)

def recreateTweaks(anim):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(t='Ooops', m='Please select the source cow and\nthe destination cow top nodes in the outliner')
        return
    if len(sel) > 2 or len(sel) < 2:
        cmds.confirmDialog(t='Ooops', m='Please Two cows top nodes only and only two')
        return
    # GET NAMESPACES
    ns1 = sel[0].replace(sel[0].split(':')[-1], '')
    ns2 = sel[1].replace(sel[1].split(':')[-1], '')
    grp = cmds.ls(ns1 + '*_tweak_grp')[0]
    grp1 = grp.replace(ns1, ns2)
    if cmds.objExists(grp1):
        nodesTemp = cmds.ls(grp1, dag=True, type='transform')
        if len(nodesTemp) != 2:
            cmds.confirmDialog(t='Ooops', m='Sorry the destination cow has already some tweak nodes,\ndelete them ( NOT THE MESH ) and re-launch the tool')
            return
    nodes = cmds.ls(grp, dag=True, type='transform')
    # GET CLUSTERS INFO
    clss, cls, df = [], '', ''
    deform = ''
    for r in nodes:
        if '_clh' in r:
            if cmds.attributeQuery('deformerName', n=r, ex=True) and cmds.attributeQuery('deformerType', n=r, ex=True):
                cls = cmds.getAttr(r + '.deformerName')
                df = cmds.getAttr(r + '.deformerType')
            else:
                cls = cmds.listConnections(r + '.worldMatrix[0]', s=False, d=True)[0]
                df = 'cluster'
        if cmds.objExists(cls) and cmds.nodeType(cls) == df:
            clss.append(cls)
            if not deform:
                # deform = cmds.listConnections(cls + '.outputGeometry', s=False, d=True)[0].split(':')[-1]
                hi = cmds.listHistory(cls + '.outputGeometry', f=True)
                for h in hi:
                    if cmds.nodeType(h) == 'mesh' and 'deform' in h:
                        deform = h.split(':')[-1]
                print(deform, '-' * 10, cls)
    if not clss:
        cmds.confirmDialog(t='Ooops', m='There are no Tweak nodes on the first cow selected')
        return
    # SAVE MAPS
    # cmds.select(ns1 + 'cowBasemesh_geo', r=True)
    cmds.select(ns1 + deform.replace('_deform_mesh', '_geo'), r=True)
    vertexDefUtil.exportDeform('cluster', 'v001', f=True)
    # CLEAN DUPLICATES ON THE LIST
    clss = list(set(clss))
    # START THE RIBUILD
    geo = deform.replace('_deform_mesh', '_geo')
    print(geo)
    for c in clss:
        face = ''
        clh = cmds.listConnections(c + '.matrix', s=True, d=False)[0]
        nameC = clh.replace('_clh', '')
        nameC = nameC.replace(ns1, ns2)
        nameC = ns2 + nameC.split(':')[-1].replace(list(filter(str.isdigit, str(nameC.split(':')[-1]))), '')
        # cow = ns1 + 'cowBasemesh_geo'
        cow = ns1 + geo
        # newCow = ns2 + 'cowBasemesh_geo'
        newCow = ns2 + geo
        if cmds.attributeQuery('faceIndex', n=clh, ex=True):
            face = cmds.getAttr(clh + '.faceIndex')
        if not face:
            pos = cmds.xform(clh, q=True, ws=True, t=True)
            face = getFaceID(cow, pos)
        nFace = newCow + '.f[' + str(face) + ']'
        print(cow, newCow, nFace)
        cmds.select(nFace, r=True)
        outCtrl = do_tweak(nameC)
        if anim:
            transferAnim(clh, ns2)
    # IMPORT CLUSTER WEIGTHS
    # cmds.select(ns2 + 'cowBasemesh_geo', r=True)
    cmds.select(ns2 + geo, r=True)
    vertexDefUtil.importDeformSwap('cluster', 'v001', ns1, ns2)
    cmds.setToolTo('selectSuperContext')
    cmds.select(cl=True)
    isolateView()
    cmds.refresh()
    isolateView()

def transferAnim(ctrl, ns2):
    attrs = ['t', 'r', 's']
    axes = ['x', 'y', 'z']
    ns1 = ctrl.replace(ctrl.split(':')[-1], '')
    ctrlT = ctrl.replace(ns1, ns2)
    info = 0
    print('=' * 100)
    print(' ' * 25, 'ANIMATION TRANSFER')
    print('=' * 100)
    for a in attrs:
        for x in axes:
            attr = a + x
            conn = cmds.listConnections(ctrl + '.' + attr, s=True, d=False, p=True)
            if conn:
                if cmds.objExists(ctrlT):
                    node = conn[0].split('.')[0]
                    dd = cmds.duplicate(node)
                    cmds.connectAttr(dd[0] + '.output', ctrlT + '.' + attr)
                    print('Animation transfered:\n' + ctrl + '  --->>>   ' + ctrlT)
                else:
                    print('Skipping ' + ctrlT + ' because not in the scene')

def restoreAsset():
    current = cmds.ls(sl=True)
    if not current:
        cmds.confirmDialog(t='Ooops', m='Please select group nodes with tweaks and the mesh of the assets you want to restore')
        return
    for s in current:
        if '_tweak_grp' not in s:
            cmds.confirmDialog(t='Ooops', m='Please select only group nodes with tweaks and the mesh of the assets you want to restore')
            return
        chi = cmds.listRelatives(s, c=True)
        if chi:
            for c in chi:
                if 'deform_mesh' in c:
                    sh = cmds.listRelatives(c, s=True, ni=True)
                    startM = sh[0].replace('_deform_mesh', '_follow_mesh')
                    start = cmds.listConnections(startM + '.inMesh', s=True, d=False, p=True)
                    end = cmds.listConnections(c + '.worldMesh[0]', s=False, d=True, p=True)
                    # RECONNECT ORIGINAL DEFORMER STACK
                    cmds.connectAttr(start[0], end[0], f=True)
                    cmds.delete(s)
                    print('-' * 100)
                    print('Asset ' + s + ' Cleaned')
                    print('-' * 100)

def loadAssetTweaks():
    current = cmds.ls(sl=True, l=True)
    if not current:
        cmds.confirmDialog(t='Ooops', m='Please select The top node of the rig you want to save\nsomething like "namespace:root_grp"')
        return
    if len(current[0].split('|')) != 2:
        cmds.confirmDialog(t='Ooops', m='Please select The top node of the rig you want to save\nsomething like "namespace:root_grp"')
        return
    asset = current[0].split('|')[-1]
    ns2 = asset.replace(asset.split(':')[-1], '')
    # mesh = ns2 + 'cowBasemesh_geo'
    grpTw = cmds.ls(ns2 + '*_tweak_grp')
    mesh, grp = '', ''
    for g in grpTw:
        current = g.replace('_tweak_grp', '_geo')
        if cmds.objExists(current):
            mesh = current
            grp = mesh.replace('_geo', '_tweak_grp')
            print(mesh, 'LOAD STEP')
    # grp = ns2 + 'baseMesh_tweak_grp'
    if cmds.objExists(grp):
        cmds.confirmDialog(t='Oooops', m='this selected asset has already some tweaks , remove the set up with the UI tool please')
        return
    inFile = cmds.fileDialog2(fileMode=1, caption='Save Asset Tweaks', ff='*.json', sff='*.json')
    data = {}
    with open(inFile[0], 'r') as inData:
        data = json.load(inData)
    for d in list(data.keys()):
        ns1 = d.replace(d.split(':')[-1], '')
        mesh = d
        for dd in list(data[mesh].keys()):
            name = dd
            for id in list(data[mesh][name].keys()):
                face = id
                weights = data[mesh][name][face]
                destM = d.replace(ns1, ns2)
                cmds.select(destM + '.f[' + str(face) + ']', r=True)
                nameO = str(name.split(':')[-1])
                digit = list(filter(str.isdigit, nameO))
                nameC = ns2 + nameO.replace(digit, '')
                clh = do_tweak(nameC)
                # IMPORT TWEAK WEIGHTS
                deformM = destM.replace('_geo', '_deform_mesh')
                cls = clh.replace('_clh', '_cls')
                vtx = cmds.polyEvaluate(deformM, v=1) -1
                cmds.setAttr('{0}.weightList[0].weights[0:{1}]'.format(cls, vtx), *weights, size=len(weights))
    cmds.select(cl=True)
    cmds.evalDeferred("cmds.setToolTo('selectSuperContext')")
    isolateView()
    cmds.refresh()
    isolateView()

def saveAssetTweaks():
    current = cmds.ls(sl=True, l=True)
    if not current:
        cmds.confirmDialog(t='Ooops', m='Please select The top node of the rig you want to save\nsomething like "namespace:Character"')
        return
    if len(current[0].split('|')) != 2:
        cmds.confirmDialog(t='Ooops', m='Please select The top node of the rig you want to save\nsomething like "namespace:Character"')
        return
    asset = current[0].split('|')[-1]
    ns = asset.replace(asset.split(':')[-1], '')
    # mesh = ns + 'cowBasemesh_geo'
    grpTw = cmds.ls(ns + '*_tweak_grp')
    mesh, grp = '', ''
    for g in grpTw:
        current = g.replace('_tweak_grp', '_geo')
        if cmds.objExists(current):
            mesh = current
            grp = mesh.replace('_geo', '_tweak_grp')
            print(mesh, 'SAVE STEP')
    deformM = mesh.replace('_geo', '_deform_mesh')
    # grp = ns + 'baseMesh_tweak_grp'
    if not cmds.objExists(grp):
        cmds.confirmDialog(t='Ooops', m='There aren\'t any tweaks on this asset:\n' + asset)
        return
    info, folI, fol, faces = {}, {}, [], []
    chi = cmds.listRelatives(grp, c=True)
    for c in chi:
        if '_fol' in c:
            details, weights = {}, []
            name = c.replace('_fol', '')
            clh = c.replace('_fol', '_clh')
            cls = c.replace('_fol', '_cls')
            vtx = cmds.polyEvaluate(deformM, v=1) -1
            for w in cmds.getAttr('{0}.weightList[0].weights[0:{1}]'.format(cls, vtx)):
                weights.append(w)
            face = str(cmds.getAttr(clh + '.faceIndex'))
            details[face] = weights
            folI[name] = details
    info[mesh] = folI
    outFile = cmds.fileDialog2(fileMode=0, caption='Save Asset Tweaks', ff='*.json', sff='*.json')
    if outFile:
        jFile = outFile[0]
        with open(jFile, 'w') as outData:
            json.dump(info, outData)

def getFaceID(cow, pos):
    mVector = om.MVector(pos)
    selectionList = om.MSelectionList()
    selectionList.add(cow)
    dPath= selectionList.getDagPath(0)
    mMesh=om.MFnMesh(dPath)
    ID = mMesh.getClosestPoint(om.MPoint(mVector),space=om.MSpace.kWorld)[1]
    return ID

def isolateView():
    sel = cmds.ls(sl=True)
    # GET THE VIEW IN FOCUS AND THE TIPE OF PANEL
    currentPanel = cmds.getPanel(vis=True)
    for eP in currentPanel:
        panelType = cmds.getPanel(to=eP)
        if panelType == 'modelPanel':
            # ISOLATE THE CURRENT SELECTION
            if cmds.isolateSelect(eP, q=True, s=True) == 0:
                mel.eval('enableIsolateSelect ' + eP + ' 1')
                cmds.isolateSelect(eP, s=1)
            else:
                if len(sel) > 0:
                    cmds.ls(sl=False)
                cmds.isolateSelect(eP, s=0)

def mDefaulShader():
    panels = cmds.getPanel(type='modelPanel')
    for p in panels:
        if cmds.modelEditor(p, q=True, udm=True):
            cmds.modelEditor(p, e=True, udm=False)
        else:
            cmds.modelEditor(p, e=True, udm=True)

def tweak_UI():
    winN = 'tweak_win'
    if cmds.window(winN, q=True, ex=True):
        cmds.deleteUI(winN)
    win = cmds.window(winN, t='Tweak UI', rtf=True)
    fl = cmds.formLayout(p=win)
    btT = cmds.button(l='Make Tweak', p=fl, h=40, w=220)
    btS = cmds.button(l='Paint Weights of selected Tweak', p=fl, h=40, w=220)
    btR = cmds.button(l='Transfer Tweaks', p=fl, h=40, w=220)
    btA = cmds.checkBox(l='Anim', p=fl, v=False)
    btE = cmds.button(l='Remove all Tweaks from asset', p=fl, h=40, w=220)
    sep = cmds.separator()
    btV = cmds.button(l='Save Asset Tweak Preset', p=fl, h=40, w=220)
    btL = cmds.button(l='Load Asset Tweak Preset', p=fl, h=40, w=220)

    cmds.formLayout(
        fl,
        e=True,
        af=[
            (btT, 'left', 5), (btT, 'top', 5), (btT, 'right', 5),
            (btS, 'left', 5), (btS, 'right', 5),
            (btR, 'left', 5),
            (btA, 'right', 5),
            (btE, 'left', 5), (btE, 'right', 5),
            (sep, 'left', 5), (sep, 'right', 5),
            (btV, 'left', 5), (btV, 'right', 5),
            (btL, 'left', 5), (btL, 'right', 5)
        ],
        ap=[
            (btR, 'right', 5, 75),
        ],
        ac=[
            (btS, 'top', 5, btT),
            (btR, 'top', 5, btS),
            (btA, 'top', 15, btS), (btA, 'left', 10, btR),
            (btE, 'top', 5, btR),
            (sep, 'top', 5, btE),
            (btV, 'top', 5, sep),
            (btL, 'top', 5, btV)
        ]
    )
    # ADD COMMANDS TO BUTTONS
    cmds.button(
        btT,
        e=True,
        c='tweakTool.do_tweak()'
    )
    cmds.button(
        btS,
        e=True,
        c='tweakTool.selectWeights()'
    )
    cmds.button(
        btR,
        e=True,
        c='tweakTool.recreateTweaks(cmds.checkBox("' + btA + '", q=True, v=True))'
    )
    cmds.button(
        btE,
        e=True,
        c='tweakTool.restoreAsset()'
    )
    cmds.button(
        btV,
        e=True,
        c='tweakTool.saveAssetTweaks()'
    )
    cmds.button(
        btL,
        e=True,
        c='tweakTool.loadAssetTweaks()'
    )

    cmds.showWindow(win)
    cmds.window(win, e=True, w=140, h=285)
