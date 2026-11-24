'''----------------------------------------------------------------------

OUTPOST MATRIX UTILITY

Date = 15/10/2019
User = Maurizio Giglioli
Update =
        15/10/2019 Initial Commit

----------------------------------------------------------------------'''

import os
import math
# import sgtk
import json
import pprint as pp
import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMaya as om
# from utilsTools import geoTagTool
from . import geoTagTool


def cleanScene():
    sel = cmds.ls('*')
    for s in sel:
        if cmds.nodeType(s) == 'unknown':
            cmds.lockNode(s, lock=False)
            cmds.delete(s)
            print('deleting:' + s)
    sel = cmds.ls('*urtle*')
    for s in sel:
        cmds.lockNode(s, l=False)
        cmds.delete(s)
        print('deleting:' + s)
    print('ALL CLEAN')


def layoutExport():
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(
            t='error', m='Select the top node of the whole layout\nor all the assets you want to export')
        return
    assetN = ''
    info = cmds.promptDialog(
        t='Layout Asset Name', m='Enter Name:',
        b=['OK', 'Cancel'], db='OK', cb='Cancel', ds='Cancel')
    if info != 'OK':
        return
    assetN = cmds.promptDialog(q=True, text=True)
    # MAKE MASTER GROUP
    grp = assetN + '_layout_grp'
    if cmds.objExists(grp):
        cmds.lockNode(grp, lock=False)
        children = cmds.listRelatives(grp, c=True)
        if children:
            for c in children:
                cmds.parent(c, w=True)
        cmds.delete(grp)
    cmds.group(em=True, n=grp)
    cmds.select(grp, r=True)
    geoTagTool.attrAdd(assetN, 'layout')
    cmds.lockNode(grp, lock=True)
    for s in sel:
        for a in ['assetName', 'assetType']:
            if cmds.attributeQuery(a, n=s, ex=True):
                cmds.setAttr(s + '.' + a, '', type='string')
        fa = cmds.listRelatives(s, p=True)
        if fa:
            if fa != grp:
                cmds.parent(s, grp)
        else:
            cmds.parent(s, grp)
    # MAKE SET
    ex = 'out_layout_set'
    if cmds.objExists(ex):
        cmds.delete(ex)
    cmds.sets(em=True, n=ex)
    cmds.select(ex, r=True, ne=True)
    geoTagTool.attrAdd(assetN, 'layout')
    for a in ['assetName', 'assetType']:
        cmds.addAttr(ex, ln=a, dt='string')
    cmds.setAttr(ex + '.assetType', 'layout', type='string')
    cmds.setAttr(ex + '.assetName', assetN, type='string')

    cmds.sets(grp, add=ex)
    cmds.select(cl=True)


def removeLayoutExport():
    sel = cmds.ls('|*', type='transform')
    for s in sel:
        if s.endswith('_grp'):
            an = cmds.attributeQuery('assetName', n=s, ex=True)
            at = cmds.attributeQuery('assetType', n=s, ex=True)
            if an or at:
                children = cmds.listRelatives(s, c=True)
                for c in children:
                    cmds.parent(c, w=True)
                cmds.lockNode(s, lock=False)
                cmds.delete(s)
                ex = 'out_layout_set'
                if cmds.objExists(ex):
                    cmds.delete(ex)
    cmds.select(cl=True)


def layoutExport_old():
    sceneN = cmds.file(q=True, sn=True, shn=True).split('.')[
        0].replace('-', '_')
    trs = cmds.ls(type='transform')
    master = sceneN + '_layout_grp'
    if not cmds.objExists(master):
        cmds.group(em=True, n=master)
        cmds.setAttr(master + '.v', 0)
        cmds.lockNode(master, lock=True)
    constrs = sceneN + '_constraints_grp'
    geom = sceneN + '_geometry_grp'
    for cur in [geom, constrs]:
        if not cmds.objExists(cur):
            cmds.group(em=True, n=cur)
            cmds.setAttr(cur + '.v', 0)
            cmds.parent(cur, master)
            if cur == geom:
                cmds.setAttr(cur + '.v', 1)
                cmds.select(cur, r=True)
                geoTagTool.do_tag('LAYOUT', sceneN)
                geoTagTool.makeExportSet('LAYOUT', sceneN, cur)
    for t in trs:
        if t.endswith('_grp'):
            if cmds.attributeQuery('assetName', n=t, ex=True):
                assetName = cmds.getAttr(t + '.assetName')
                assetG = t.replace('_grp', '_lay_grp')
                if not cmds.objExists(assetG):
                    cmds.group(em=True, n=assetG)
                    cmds.select(assetG, r=True)
                    geoTagTool.do_tag(assetName, 'LAYOUT')
                    cmds.parent(assetG, geom)
                nodes = cmds.ls(t, dag=True, type='transform')
                for n in nodes:
                    if n != t:
                        sh = cmds.listRelatives(n, s=True, ni=True)
                        if sh:
                            if cmds.attributeQuery('assetName', n=sh[0], ex=True):
                                ns = n.split(':')[0].replace(
                                    '_grp', '_lay_grp')
                                dd = cmds.duplicate(n, rr=True)
                                cmds.parent(dd[0], assetG)
                                cmds.connectAttr(
                                    n + '.worldMesh', dd[0] + '.inMesh')
                                pc = cmds.parentConstraint(n, dd[0], mo=True)
                                sc = cmds.scaleConstraint(n, dd[0], mo=True)
                                cmds.rename(dd[0], ns + ':' + dd[0])
                                for cur in [pc[0], sc[0]]:
                                    cmds.parent(cur, constrs)
    cmds.select(cl=True)


def removeLayoutExport_old():
    nss = []
    sceneN = cmds.file(q=True, sn=True, shn=True).split('.')[
        0].replace('-', '_')
    master = sceneN + '_layout_grp'
    cmds.lockNode(master, lock=False)
    sel = cmds.ls(master, dag=True, type='transform')
    for s in sel:
        test = s.split(':')
        if len(test) > 1:
            name = s.split(':')[-1]
            ns = s.replace(name, '')
            nss.append(ns)
    nss = list(set(nss))
    for n in nss:
        try:
            cmds.namespace(f=True, rm=n, dnc=True)
        except:
            print('')
    cmds.delete(master)


def readRenderSettings(show, mode=None):
    jfile = '/mnt/jobs/' + show + '/tools/maya/Presets/renderSettings.json'
    if os.path.isfile(jfile):
        with open(jfile, 'r') as f:
            data = json.load(f)
    if data:
        if mode == 'high' or mode == 'low':
            width = data[mode][0][0]
            height = data[mode][0][1]
            ratio = data[mode][1]
            if cmds.objExists('defaultResolution'):
                cmds.setAttr('defaultResolution.aspectLock', 0)
                # cmds.setAttr('defaultResolution.lockDeviceAspectRatio', 0)
                cmds.setAttr('defaultResolution.width', width)
                cmds.setAttr('defaultResolution.height', height)
                cmds.setAttr('defaultResolution.deviceAspectRatio', ratio)
                # cmds.setAttr('defaultResolution.lockDeviceAspectRatio', 1)
                cmds.setAttr('defaultResolution.aspectLock', 1)
        elif mode == 'overscan':
            over = data[mode]
            cmds.setAttr(
                'defaultArnoldRenderOptions.outputOverscan', over, type='string')
        elif not mode:
            cmds.setAttr(
                'defaultArnoldRenderOptions.outputOverscan', '', type='string')


# MAKE DEFAULT SCRIPT JOB FOR ADDING NAMESPACE TO OPERATORS
def setOperatorsNS():
    jobs = cmds.scriptJob(listJobs=True)
    if jobs:
        for j in jobs:
            if 'operatorNSAdd' in j and 'PostSceneRead' in j:
                id = int(j.split(':')[0])
                cmds.scriptJob(kill=id)
    cmds.scriptJob(
        event=['PostSceneRead', 'from utilsTools import geoTagTool;geoTagTool.operatorNSAdd(False)'])


def setLoadOperatorsNS():
    jobs = cmds.scriptJob(listJobs=True)
    if jobs:
        for j in jobs:
            if 'operatorNSAdd' in j and 'SceneOpened' in j:
                id = int(j.split(':')[0])
                cmds.scriptJob(kill=id)
    cmds.scriptJob(
        event=['SceneOpened', 'from utilsTools import geoTagTool;geoTagTool.operatorNSAdd(False)'])


# MAKE DEFAULT SCRIPT JOB FOR SETTIGN SHOTGUN FRAMERANGE
def makeFrameRangerSJ():
    jobs = cmds.scriptJob(listJobs=True)
    if jobs:
        for j in jobs:
            if 'getShotInfo' in j:
                id = int(j.split(':')[0])
                cmds.scriptJob(kill=id)
                # print id, j
    cmds.scriptJob(event=['SceneOpened', 'outGeneralUtil.getShotInfo()'])


# SET MAYA SHOT FRAMERANGE
def getShotInfo():
    ws = cmds.workspace(q=True, act=True)
    sceneN = cmds.file(q=True, sn=True, shn=True)
    if not sceneN:
        cmds.warning('This scene hasn\'t been saved yet , please save')
        return
    path = os.path.join(ws, sceneN)
    tk = sgtk.sgtk_from_path(path)
    ctx = tk.context_from_path(path)
    engine = sgtk.platform.current_engine()

    filters = [['id', 'is', int(ctx.entity["id"])]]
    result = engine.shotgun.find_one(
        'Shot', filters=filters, fields=["sg_head_in", "sg_tail_out"])
    if result:
        start = result['sg_head_in']
        end = result['sg_tail_out']
        if start and end:
            cmds.setAttr('defaultRenderGlobals.startFrame', start)
            cmds.setAttr('defaultRenderGlobals.endFrame', end)
            cmds.playbackOptions(min=start, max=end)
            print('=' * 50)
            print('SET SHOTGUN SHOT FRAMERANGE INFO\nSTART:' + str(start) + ' END:' + str(end))
            print('=' * 50)


# DEFAULT MAYA FILE BROWSER
def oBrowser(mode, loc=None, tipo=None):
    defPath = loc
    if not loc:
        defPath = cmds.workspace(q=True, act=True)
    out = ''
    filter = "Operators Desciption (*.json);;"
    if tipo:
        filter = "Operators Desciption (*" + tipo + ");;"
    r = cmds.fileDialog2(
        ff=filter, cap='Shading Information',
        dir=defPath, fm=mode, ds=True)
    if r:
        out = r[0]
    return out


# CHECK EXTENSION OF NODES
def checkNode(node, ext):
    print(node, ext)


def extLib():
    lib = {
        'spaceLocator': ['loc'], 'mesh': ['geo', 'mesh'],
        'transform': ['grp', 'hgrp'], 'light': ['ltg']}

    print(lib)


# FIX OFF SETS IN MESHES
def findMeshOffset():
    sel = cmds.ls(type='mesh')
    out = {}
    for s in sel:
        vtx = cmds.polyEvaluate(s, v=True)
        idx = {}
        for x in range(0, vtx):
            val = {}
            for a in ['x', 'y', 'z']:
                cur = cmds.getAttr(s + '.pnts[' + str(x) + '].pnt' + a)
                if cur != 0:
                    val[a] = cur
                    idx[str(x)] = val
        out[s] = idx
        if len(out[s]) > 0:
            result = cmds.confirmDialog(
                t='Mesh offset', m='Clean This Mesh ' + s,
                b=['Yes', 'No'], db='Yes', cb='No', ds='No')
            if result == 'Yes':
                fixMeshOffSet(s)


def fixMeshOffSet(node):
    # sel = cmds.ls(sl=True)
    # conn = cmds.listConnections(node + '.inMesh', s=True, d=False)
    cmds.select(node, r=True)
    # clh = cmds.cluster()
    cmds.cluster()
    cmds.select(node, r=True)
    mel.eval('DeleteHistory')


def outFixLocSpace(center=None):
    sel = cmds.ls(sl=True, typ='transform')
    local = ''
    if sel:
        for s in sel:
            if center:
                cmds.select(s, r=True)
            cmds.CenterPivot()
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
                    c = c.split('|')[-1]
                    if cmds.nodeType(c) == 'transform':
                        cmds.parent(c, s)
            if center:
                print('Local space values fixed and pivot centered for ' + s + '\n')
            else:
                print('Local space values fixed for ' + s + '\n')
            cmds.select(s, r=True)
            cmds.DeleteHistory()
    else:
        cmds.warning('Please select a trasnform to fix')
    cmds.headsUpMessage('Local Space Values fixed.', time=5.0)


# PRINT COMMAND TO CREATE SELECTED CURVE
def printControlCmd():
    sel = cmds.ls(sl=True)
    # CHEKCS
    if not sel:
        cmds.warning('Please select a nurbsCurve')
        return
    for s in sel:
        # CHEKCS
        if not cmds.nodeType(s) == 'nurbsCurve':
            sh = cmds.listRelatives(s, s=True, ni=True)
            if not sh:
                cmds.warning('Please select a nurbsCurve')
                return
            if not cmds.nodeType(sh[0]) == 'nurbsCurve':
                cmds.warning('Please select a nurbsCurve')
                return
            s = sh[0]
        poss, ks = [], []
        deg, spans = cmds.getAttr(s + '.degree'), cmds.getAttr(s + '.spans')
        # CREATE COMMAND
        cmd = 'cmds.curve(d=' + str(deg) + ', p=['
        for x in range(0, spans + 3):
            pos = str(cmds.pointPosition(
                s + '.cv[' + str(x) + ']')).replace('[', '(').replace(']', ')')
            poss.append(pos)
        cmd += (', ').join(poss) + '])'
        # PRINT COMMAND
        print(cmd)


def oneCurveGrid(rezx=10, rezy=10, scalex=1, scaley=1):
    points = []
    sx = 1.0 / (rezx - 1)
    sy = 1.0 / (rezy - 1)
    for i in range(rezx / 2):
        for j in range(rezy):
            points.append([(2.0 * i * sx - .5) * scalex,
                           (j * sy - .5) * scaley, 0])
        for j in reversed(list(range(rezy))):
            points.append([((2.0 * i + 1) * sx - .5) *
                           scalex, (j * sy - .5) * scaley, 0])
    for i in range(rezy / 2):
        for j in reversed(list(range(rezx))):
            points.append(
                [(j * sx - .5) * scalex, (i * 2.0 * sy - .5) * scaley, 0])
        for j in range(rezx):
            points.append(
                [(j * sx - .5) * scalex, ((i * 2.0 + 1) * sy - .5) * scaley, 0])
    for i in reversed(list(range(rezx))):
        points.append([((i * sx - .5) * scalex), ((i * sx - .5) * scaley), 0])

    return points


def createZDistanceTool():
    '''creates controllers to help with the focus distance.
    Plugs into 'focusDistance' of camera shape'''
    # CHOOSE CAM
    selection = cmds.ls(sl=True)
    if not selection:
        cmds.warning('Please select a camera')
        return
    selShp = (selection[0], cmds.listRelatives(selection[0], s=True))[
        cmds.nodeType(selection[0]) == 'transform']
    if not cmds.nodeType(selShp) == 'camera':
        cmds.warning('Please select a camera')
        return
    chosenCamera = selShp
    camObj = cmds.listRelatives(chosenCamera, p=1)[0]
    camShape = chosenCamera[0]
    floatingZLoc = cmds.group(em=True, n=camObj + '_float_grp')
    # CREATE CURVE TO PROJECT OUR LOCATOR ON
    projCurve = cmds.curve(p=[[0, 0, 0], [0, 0, 1000]],
                           d=1, n=camObj + '_long_crv')
    # CURVE FOLLOW CAMERA
    pc = cmds.parentConstraint(camObj, projCurve, mo=False)[0]
    cmds.setAttr(pc + '.target[0].targetOffsetRotateY', 180)
    # LOCATOR ON CAMERA TO GET WORLD POSITION LATER
    cameraLocator = cmds.spaceLocator(n=camObj + '_cam_loc')[0]
    cmds.pointConstraint(camObj, cameraLocator, mo=False)
    # LOCATOR TO GET FLOATING CONTROLLER WORLD POS
    floatingLocator = cmds.spaceLocator(n=camObj + '_float_loc')[0]
    cmds.parent(floatingLocator, floatingZLoc)
    # LOCATOR TO PROJECT ON CURVE
    projectionLocator = cmds.spaceLocator(n=camObj + '_proj_loc')[0]

    nPoc = cmds.createNode('nearestPointOnCurve')
    cmds.connectAttr(cmds.listRelatives(
        floatingLocator, s=True)[0] + '.worldPosition', nPoc + '.inPosition', f=True)
    cmds.connectAttr(
        cmds.listRelatives(projCurve, s=True)[0] + '.worldSpace', nPoc + '.inputCurve', f=True)
    cmds.connectAttr(
        nPoc + '.position', projectionLocator + '.translate', f=True)

    db = cmds.createNode('distanceBetween')
    cmds.connectAttr(
        cmds.listRelatives(projectionLocator, s=True)[0] + '.worldPosition', db + '.point1')
    cmds.connectAttr(
        cmds.listRelatives(cameraLocator, s=True)[0] + '.worldPosition', db + '.point2')

    # END RESULT LOCATOR AND GRID
    resultLocator = cmds.spaceLocator(n=camObj + 'result_loc')[0]
    resultGrid = cmds.curve(
        p=oneCurveGrid(14, 8, 3.84, 2.16), d=1, n=camObj + '_resultGrid_crv')
    cmds.setAttr(resultGrid + '.tz', keyable=False, channelBox=False)
    cmds.setAttr(resultGrid + '.visibility', keyable=False, channelBox=False)

    # CAMERA BASED SYSTEM
    # CREATE A GRID TO VIZ STANDARD FOCUS DISTANCE Z
    cameraGrid = cmds.curve(
        p=oneCurveGrid(28, 16, 8, 4.5), d=1, n=camObj + '_ctrl')
    cameraGridNull = cmds.group(em=True, n=camObj + '_zero_grp')
    cmds.parent(cameraGrid, cameraGridNull)
    cmds.parent(resultLocator, cameraGridNull)
    cmds.parent(resultGrid, cameraGridNull)
    pc2 = cmds.parentConstraint(projCurve, cameraGridNull, mo=False)[0]

    # GRAB EXISTING ZDEPTH FOCUS
    currentDistance = cmds.getAttr(camShape + '.focusDistance')
    cmds.setAttr(cameraGrid + '.tz', currentDistance)

    # CHOICE SYSTEM
    sr = cmds.createNode('setRange')
    sr2 = cmds.createNode('setRange')
    cmds.setAttr(sr + '.oldMaxX', 1)
    cmds.setAttr(sr + '.oldMaxY', 1)
    cmds.setAttr(sr + '.maxY', 0)
    cmds.setAttr(sr + '.minY', 1)
    cmds.setAttr(sr2 + '.maxX', 1)
    cmds.setAttr(sr2 + '.maxY', 0)
    cmds.setAttr(sr2 + '.minY', 1)
    cmds.setAttr(sr2 + '.oldMaxX', .001)
    cmds.setAttr(sr2 + '.oldMinY', .999)
    cmds.setAttr(sr2 + '.oldMaxY', 1)
    cmds.connectAttr(db + '.distance', sr + '.maxX', f=1)
    cmds.connectAttr(cameraGrid + '.tz', sr + '.minX', f=1)
    cmds.connectAttr(sr + '.outValue.outValueX', resultLocator + '.tz', f=True)
    arrow = cmds.annotate(resultLocator, p=(0, 0, 0))
    arrowObj = cmds.listRelatives(arrow, p=1)[0]
    arrowObj = cmds.rename(arrowObj, camObj + '_z_dd')
    arrow = cmds.listRelatives(arrowObj, s=1)[0]
    cmds.parent(arrowObj, cameraGridNull, r=True)

    # RIDICULUS HACK TO FORCE ANNOTATION UPDATE
    md = cmds.createNode('multiplyDivide')
    cmds.connectAttr(camObj + '.tx', md + '.input2.input2X')
    cmds.connectAttr(sr + '.outValue.outValueX', md + '.input2.input2Y')
    cmds.connectAttr(floatingZLoc + '.tx', md + '.input2.input2Z')
    cmds.connectAttr(
        md + '.output', cmds.listRelatives(arrow, p=1)[0] + '.translate')

    # CONTROLS AND COSMETIC STUFF
    for o in (projCurve, resultLocator, floatingLocator, projectionLocator, cameraLocator, pc2):
        cmds.setAttr(o + '.visibility', False)
    for o in (cameraGrid, arrowObj):
        for p in ('tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'rx', 'ry', 'rz'):
            cmds.setAttr(o + '.' + p, keyable=False, channelBox=False)
    cmds.setAttr(cameraGrid + '.tz', keyable=True, channelBox=False)
    cmds.setAttr(cameraGrid + '.tx', lock=True)
    cmds.setAttr(cameraGrid + '.ty', lock=True)
    cmds.addAttr(arrowObj, ln='focusDistance')
    cmds.setAttr(
        arrowObj + '.focusDistance', e=0, k=False, cb=True)
    cmds.connectAttr(
        sr + '.outValue.outValueX', arrowObj + '.focusDistance', f=True)
    cmds.connectAttr(sr + '.outValue.outValueX', resultGrid + '.tz', f=True)
    cmds.connectAttr(
        sr2 + '.outValue.outValueX', resultGrid + '.v', f=True)
    cmds.connectAttr(
        sr2 + '.outValue.outValueY', cameraGrid + '.v', f=True)
    cmds.setAttr(resultGrid + '.overrideEnabled', 1)
    cmds.setAttr(resultGrid + '.overrideColor', 1)
    cmds.addAttr(arrowObj, ln='useFloatingLocator', dv=0.0, min=0.0, max=1.0)
    cmds.setAttr(
        arrowObj + '.useFloatingLocator', e=1, k=True, cb=False)
    cmds.connectAttr(arrowObj + '.useFloatingLocator', sr + '.valueX', f=True)
    cmds.connectAttr(arrowObj + '.useFloatingLocator', sr + '.valueY', f=True)
    cmds.connectAttr(arrowObj + '.useFloatingLocator', sr + '.valueZ', f=True)
    cmds.connectAttr(arrowObj + '.useFloatingLocator', sr2 + '.valueX', f=True)
    cmds.connectAttr(arrowObj + '.useFloatingLocator', sr2 + '.valueY', f=True)
    cmds.setAttr(arrow + '.overrideEnabled', 1)
    cmds.setAttr(arrow + '.overrideColor', 17)
    cmds.setAttr(cameraGrid + '.overrideEnabled', 1)
    cmds.setAttr(cameraGrid + '.overrideColor', 12)
    cmds.setAttr(floatingZLoc + '.overrideEnabled', 1)
    cmds.setAttr(floatingZLoc + '.overrideColor', 12)
    zFocusGroup = cmds.group(em=True, n=camObj + '_grp')
    cmds.parent(
        cameraGridNull, floatingZLoc, projCurve, projectionLocator, cameraLocator, zFocusGroup)
    cmds.connectAttr(resultLocator + '.tz', camShape + '.focusDistance', f=1)
    cmds.select(arrowObj)
