import maya.cmds as cmds, maya.mel as mel
from functools import partial
# from compiler.ast import flatten
import random as rand
from math import *
import time, maya.api.OpenMaya as om, pymel.core as pm, colorsys, json

def Func1(mode='cust'):
    networkNodes = cmds.ls(type='network')
    if networkNodes:
        for node in networkNodes:
            if cmds.attributeQuery('isAtrapStripNode', node=node, exists=True):
                if cmds.getAttr(node + '.isAtrapStripNode'):
                    if mode == 'all':
                        trapStripNodes.append(node)
                    elif mode == 'tras':
                        if cmds.attributeQuery('connectedtrasNode', node=node, exists=True):
                            trapStripNodes.append(node)
                    elif not cmds.attributeQuery('connectedtrasNode', node=node, exists=True):
                        trapStripNodes.append(node)


def Func2():
    return 10
    currMSNode = cmds.getAttr('trapGentrasNode.currenttrapStripNode')
    stripMaxCount = cmds.getAttr(currMSNode + '.stripMaxCount')


def aboutUs(*args):
    import webbrowser
    webbrowser.open('https://www.facebook.com/UnPlugTools')


def otherProducts(*args):
    import webbrowser
    webbrowser.open('https://gumroad.com/unplugtools')


def smooHairCUs(*args):
    cmds.SmoothHairCurves()


def rebuildCrvsUnitBased(spacingField, *args):
    spacing = cmds.floatField(spacingField, q=1, v=1)
    Crvs = cmds.ls(sl=1)
    PLs = []
    for e in Crvs:
        crvLen = int(cmds.arclen(e) / spacing)
        cmds.rebuildCurve(e, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=crvLen, d=3, tol=0.01)
        cmds.select(Crvs)


def showCVss(*args):
    sel = cmds.ls(sl=1)
    cmds.SelectHierarchy()
    CUs = cmds.ls(sl=1)
    if len(CUs) == 0:
        cmds.warning('Please select Curves')
    if len(CUs) > 0:
        for e in CUs:
            try:
                cmds.setAttr(e + '.dispCV', 1)
            except:
                pass

    cmds.select(sel)


def hideCVss(*args):
    sel = cmds.ls(sl=1)
    cmds.SelectHierarchy()
    CUs = cmds.ls(sl=1)
    if len(CUs) == 0:
        cmds.warning('Please select Curves')
    if len(CUs) > 0:
        for e in CUs:
            try:
                cmds.setAttr(e + '.dispCV', 0)
            except:
                pass

    cmds.select(sel)


def drawPfx(*args):
    cmds.PaintEffectsTool()
    mel.eval('MakePaintable;')


def pfxToCrv(*args):
    sel = cmds.ls(sl=1)
    guideGrp = []
    for e in sel:
        cmds.select(e)
        a = pm.listRelatives()[0]
        b = pm.listConnections(a)[1]
        c = pm.listConnections(b)[2]
        mel.eval('doPaintEffectsToCurve( 0)')
        shp = pm.listRelatives(e, s=1)
        cu = pm.listConnections(shp, t='nurbsCurve')
        pm.rename(cu, 'guide_01')
        strk = pm.listConnections(shp, t='brush')[0]
        cu4 = pm.listConnections(strk)[0]
        pm.select(cu[0])
        delGrp = pm.listRelatives(cu[0], p=1)
        delGrp = pm.listRelatives(delGrp, p=1)
        pm.delete(cu[0], ch=1)
        pm.parent(cu[0], w=1)
        pm.delete(cu4, strk, delGrp, c)
        guideGrp.append(cu[0])

    pm.group(guideGrp, n='pfxGuidesGrp_01')


def switchTool(*args):
    cmds.setToolTo('Move')


def attachMultiCurves(*args):
    sel = cmds.ls(sl=1)
    for e in sel:
        cmds.rebuildCurve(e, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=0, kt=0, s=0, d=1, tol=0.01)

    x = 0
    for e in range(len(sel) - 1):
        a = sel[x]
        b = sel[(x + 1)]
        subSel = (a, b)
        vals = []
        xx = 0
        for f in subSel:
            CUShape = cmds.listRelatives(f, s=1)
            CPOC = cmds.createNode('nearestPointOnCurve')
            cmds.connectAttr(CUShape[0] + '.worldSpace', CPOC + '.inputCurve')
            cmds.setAttr(CPOC + '.inPosition', 1, 2, 3, type='double3')
            if xx == 0:
                pos = cmds.xform(subSel[(xx + 1)] + '.cv[0]', t=1, q=1, ws=1)
            if xx == 1:
                cmds.select(subSel[(xx - 1)] + '.cv[200]')
                pos = cmds.xform(subSel[(xx - 1)] + '.cv[200]', t=1, q=1, ws=1)
            cmds.setAttr(CPOC + '.inPositionX', pos[0])
            cmds.setAttr(CPOC + '.inPositionY', pos[1])
            cmds.setAttr(CPOC + '.inPositionZ', pos[2])
            pos2 = cmds.getAttr(CPOC + '.position')[0]
            uParam = cmds.getAttr(CPOC + '.parameter')
            dist = sqrt(pow(pos[0] - pos2[0], 2) + pow(pos[1] - pos2[1], 2) + pow(pos[2] - pos2[2], 2))
            val = (dist, uParam, f)
            vals.append(val)
            xx += 1

        vals.sort()
        pr = vals[0][1]
        Dcrv = cmds.detachCurve(vals[0][2], ch=0, p=pr, rpo=1)
        if vals[0][2] == b:
            cmds.delete(Dcrv[1])
            b = Dcrv[0]
        else:
            cmds.delete(Dcrv[0])
        ac = cmds.attachCurve(b, a, ch=0, rpo=0, kmk=0, m=1, bb=0.5, bki=0, p=1, n='newCU_01')
        cmds.reverseCurve(ac, ch=0, rpo=1)
        sel[x + 1] = ac[0]
        cmds.delete(a, b)
        x += 1

    cmds.select(ac)
    cmds.SmoothHairCurves()


def toCurrent(*args):
    sell = pm.ls(sl=1)
    vol = pm.getAttr(innerMesh + '.sv')
    if vol == 'a':
        pm.setAttr(innerMesh + '.sv', l=0)
        pm.setAttr(innerMesh + '.sv', 'b', type='string', l=1)
    sel = pm.listRelatives(guides, c=1)
    for e in sel:
        pm.select(e)
        lJb()
        graphblendGuides()

    rootPntScaleUp()
    rootPntScaleDown()
    pm.select(sell)


def toScalp(*args):
    sell = pm.ls(sl=1)
    vol = pm.getAttr(innerMesh + '.sv')
    if vol != 'a':
        pm.setAttr(innerMesh + '.sv', l=0)
        pm.setAttr(innerMesh + '.sv', 'a', type='string', l=1)
    sel = pm.listRelatives(guides, c=1)
    Crvs = pm.listRelatives(guides, c=1)
    crvvs = []
    for e in sel:
        try:
            sh = pm.listRelatives(e, s=1, typ='nurbsCurve')[0]
            crvvs.append(e)
        except:
            pass

    try:
        vall = 0
        for e in Crvs:
            lr = pm.listRelatives(e, s=1)
            lc = pm.listConnections(lr[0])
            bss = []
            for b in lc:
                typ = pm.objectType(b)
                if typ == 'blendShape':
                    bss.append(b)

            cmds.select(bss)
            bss = cmds.ls(sl=1)
            cvNo = pm.getAttr(e + '.spans') + 3
            incr = 1.0 / (cvNo - 1)
            for i in range(cvNo):
                grphVal = cmds.gradientControlNoAttr('graphCrv2', q=True, valueAtPoint=vall)
                if grphVal > 1:
                    grphVal = 1
                if grphVal < 0:
                    grphVal = 0
                grphValB = 1 - grphVal
                cmds.setAttr(bss[0] + '.inputTarget[' + str(0) + '].inputTargetGroup[0].targetWeights' + '[' + str(i) + ']', grphValB)
                cmds.setAttr(bss[0] + '.inputTarget[' + str(0) + '].inputTargetGroup[1].targetWeights' + '[' + str(i) + ']', grphVal)
                vall += incr

            vall = 0

    except:
        pass

    rootPntScaleUp()
    rootPntScaleDown()
    pm.select(sell)


def delGuides(*args):
    sel = pm.ls(sl=1)
    cmds.select(cl=1)
    try:
        for e in sel:
            a = pm.listRelatives(e)[0]
            typ = pm.objectType(a)
            if typ == 'nurbsCurve':
                shp = pm.listRelatives(e)[0]
                b = pm.listConnections(shp)[0]
                c = pm.listConnections(b, t='nurbsCurve')[1]
                d = pm.listConnections(b, t='nurbsCurve')[2]
                e1 = pm.listRelatives(c)[1]
                f1 = pm.listRelatives(d)[1]
                g = pm.listConnections(e1)
                h = pm.listConnections(f1)
                a1 = pm.listRelatives(e)[0]
                b1 = pm.listConnections(a1)[1]
                c1 = pm.listConnections(b1, t='nurbsCurve')[0]
                d1 = pm.listConnections(c1, t='follicle')
                e1 = pm.listRelatives(d1)[0]
                f1 = pm.listConnections(e1, t='nurbsCurve')
                pm.delete(g, h, d1, f1, e)
                rootPntScaleDown()
                rootPntScaleUp()

    except:
        pass


def attachGuides(*args):
    sel = cmds.ls(sl=1)
    pony = sel[0]
    base = sel[1]
    pony = cmds.listRelatives(pony, c=1, f=1)
    base = cmds.listRelatives(base, c=1, f=1)
    grp = []
    for e in pony:
        try:
            p1 = cmds.xform(e + '.cv[0]', q=1, t=1, ws=1, a=1)
            dists = []
            for f in base:
                p2 = cmds.xform(f + '.cv[200]', q=1, t=1, ws=1, a=1)
                dist = sqrt(pow(p1[0] - p2[0], 2) + pow(p1[1] - p2[1], 2) + pow(p1[2] - p2[2], 2))
                dist2 = (dist, f)
                dists.append(dist2)

            dists = sorted(dists)
            mindist = dists[0]
            base.remove(mindist[1])
            c = pm.attachCurve(e, mindist[1], ch=0, rpo=0, kmk=1, m=1, bb=0.8, bki=0, p=0.1)
            pm.rename(c, 'curveBlend_01')
            grp.append(c[0])
        except:
            pass

    pm.group(grp, n='curveBlend_Grp')


def hairMeshScaleUp(*args):
    pfxShp = pm.listRelatives(pfxHair, c=1)
    brsh = pm.listConnections(pfxShp)[1]
    val = pm.getAttr(brsh + '.globalScale')
    pm.setAttr(brsh + '.globalScale', val + 4)


def hairMeshScaleDown(*args):
    pfxShp = pm.listRelatives(pfxHair, c=1)
    brsh = pm.listConnections(pfxShp)[1]
    val = pm.getAttr(brsh + '.globalScale')
    pm.setAttr(brsh + '.globalScale', val - 4)


def rootPntScaleUp(*args):
    gds = pm.listRelatives(guides, c=1)
    roots = pm.listRelatives(rootLocs, c=1)
    x = 0.1
    scl = pm.getAttr(roots[0] + '.sx')
    gdlen = len(gds)
    rootslen = len(roots)
    diff = rootslen - gdlen
    if diff > 0:
        pm.delete(roots[0:diff])
    roots = pm.listRelatives(rootLocs, c=1)
    for e, f in zip(roots, gds):
        ss = scl + x
        tr = pm.xform(f + '.cv[0]', q=1, t=1)
        pm.xform(e, t=tr, s=(ss, ss, ss), a=1)


def rootPntScaleDown(*args):
    gds = pm.listRelatives(guides, c=1)
    roots = pm.listRelatives(rootLocs, c=1)
    x = 0.1
    scl = pm.getAttr(roots[0] + '.sx')
    gdlen = len(gds)
    rootslen = len(roots)
    diff = rootslen - gdlen
    if diff > 0:
        pm.delete(roots[0:diff])
    roots = pm.listRelatives(rootLocs, c=1)
    for e, f in zip(roots, gds):
        ss = scl - x
        tr = pm.xform(f + '.cv[0]', q=1, t=1)
        pm.xform(e, t=tr, s=(ss, ss, ss), a=1)


def createSetup(*args):
    global lam
    sel = cmds.ls(sl=1)
    if len(sel) == 2:
        innerMesh = [
         sel[0]]
        try:
            cmds.addAttr(innerMesh[0], ln='sv', dt='string')
            cmds.setAttr(innerMesh[0] + '.sv', l=0)
            cmds.setAttr(innerMesh[0] + '.sv', 'a', type='string', l=1)
        except:
            pass

        outerMesh = [
         sel[1]]
        cmds.polyAutoProjection(outerMesh, lm=0, pb=0, ibd=1, cm=0, l=2, sc=1, o=1, p=6, ps=0.2, ws=0)
        cmds.delete(outerMesh, ch=1)
        cmds.select(cl=1)
        a = pm.group(em=1, n='guides_01')
        b = pm.group(em=1, n='rootLocs_01')
        c = pm.group(em=1, n='snaps_01')
        d = pm.group(em=1, n='guidesBase_01')
        e = pm.group(em=1, n='hairMeshG_01')
        msc = pm.group(b, c, d, e, n='misc')
        setupGrp = pm.group(innerMesh, outerMesh, a, msc, n='drawGuides_01')
        lam = cmds.shadingNode('lambert', asShader=1, n='rootPointColor')
        cmds.setAttr(lam + '.color', 1, 1, 0, type='double3')
        lam2 = cmds.shadingNode('lambert', asShader=1, n='volumeColor')
        cmds.setAttr(lam2 + '.transparency', 0.9, 0.9, 0.9, type='double3')
        cmds.select(outerMesh[0])
        cmds.hyperShade(assign=lam2)
        pm.select(setupGrp)
        cu = cmds.curve(d=3, p=((0, 0, 1), (1, 0, 1), (2, 0, 1), (3, 0, 1)))
        cmds.pickWalk(d='down')
        cuShp = cmds.ls(sl=1)[0]
        mel.eval('makeCurvesDynamic 2 { "1", "0", "1", "1", "0"};')
        hsShp = cmds.ls(sl=1)[0]
        hsT = cmds.listRelatives(hsShp, p=1)
        hsAll = cmds.listConnections(hsShp)
        follGrp = cmds.listRelatives(hsAll[6], p=1)
        xx = cmds.listRelatives(hsAll[6], s=1)
        xx2 = cmds.listConnections(xx)[4]
        hOutputGrp = cmds.listRelatives(xx2, p=1)
        cmds.delete(xx2, hsAll[6])
        cmds.setAttr(hsShp + '.hairWidthScale[0].hairWidthScale_Interp', 1)
        cmds.setAttr(hsShp + '.hairWidthScale[1].hairWidthScale_Interp', 1)
        cmds.setAttr(hsShp + '.clumpWidth', 0.001)
        cmds.setAttr(hsShp + '.hairWidthScale[0].hairWidthScale_Position', 0)
        cmds.setAttr(hsShp + '.hairWidthScale[0].hairWidthScale_FloatValue', 1)
        cmds.setAttr(hsShp + '.simulationMethod', 1)
        cmds.select(hsShp)
        mel.eval('assignBrushToHairSystem;')
        pfxShp = cmds.ls(sl=1)[0]
        pfxT = cmds.listRelatives(pfxShp, p=1)
        brsh = cmds.listConnections(pfxShp)[1]
        cmds.setAttr(brsh + '.globalScale', 30)
        cmds.setAttr(brsh + '.flatness1', 0.1)
        cmds.hide(hOutputGrp, follGrp, hsT, pfxT)
        cmds.select(pfxShp)
        mel.eval('doPaintEffectsToPoly( 1,0,0,1,100000);')
        meshA = cmds.ls(sl=1)[0]
        meshB = cmds.listRelatives(meshA, p=1)
        meshC = cmds.listRelatives(meshB, p=1)
        cmds.select(meshB)
        cmds.rename('hairMesh_01')
        meshB = pm.ls(sl=1)
        msc = pm.group(follGrp, hOutputGrp, hsT, pfxT, n='hairMisc')
        pm.parent(msc, meshB, e)
        cmds.delete(meshC)
        cmds.setAttr(pfxShp + '.meshQuadOutput', 1)
        lam = cmds.shadingNode('lambert', asShader=1, n='hairDispMeshColor')
        pm.select(meshB)
        cmds.hyperShade(assign=lam)
        mel.eval('createRenderNodeCB -as2DTexture "" ramp ""')
        rmp = cmds.ls(sl=1)[0]
        cmds.connectAttr(rmp + '.outColor', lam + '.color', force=1)
        pm.setAttr(rmp + '.colorEntryList[1].position', 1)
        cmds.setAttr(rmp + '.colorEntryList[0].color', 0, 0, 1, type='double3')
        cmds.setAttr(rmp + '.colorEntryList[1].color', 0, 1, 0, type='double3')
        cmds.delete(hsAll[1])
        pm.select(setupGrp)
        loadSetup()
        cmds.scriptEditorInfo(ch=1)
        cmds.warning('GroomGuide Setup Created')
        cmds.frameLayout('gaga', vis=1, e=1, collapse=0)
        cmds.window('blendGuides', e=1, h=150, w=350)
        try:
            cmds.button('btn01', e=1, vis=0)
            cmds.button('btn02', e=1, vis=0)
        except:
            pass

    else:
        cmds.warning('Please select 2 meshes - 1st the Scalp mesh, then the Hair Volume mesh')


def loadSetup(*args):
    global guides
    global guidesBase
    global hairMesh
    global hs
    global innerMesh
    global lam
    global outerMesh
    global pfxHair
    global rootLocs
    global snaps
    sell = cmds.ls(sl=1)
    if len(sell) == 1:
        sell = cmds.listRelatives(sell, c=1, f=1)
        if len(sell) == 4:
            lam = cmds.ls('rootPointColor*')[0]
            sel = cmds.listRelatives(c=1, f=1)
            sel2 = cmds.listRelatives(sel[3], c=1, f=1)
            hm = cmds.listRelatives(sel2[3], c=1, f=1)[0]
            hs = cmds.listRelatives(hm, c=1, f=1)[2]
            pfxHair = cmds.listRelatives(hm, c=1, f=1)[3]
            hairMesh = cmds.listRelatives(sel2[3], c=1, f=1)[1]
            innerMesh = sel[0]
            outerMesh = sel[1]
            guides = sel[2]
            rootLocs = sel2[0]
            snaps = sel2[1]
            guidesBase = sel2[2]
            cmds.warning('GroomGuide Setup Loaded')
            cmds.frameLayout('gaga', vis=1, e=1, collapse=0)
            try:
                cmds.button('btn01', e=1, vis=0)
                cmds.button('btn02', e=1, vis=0)
            except:
                pass

        else:
            cmds.warning('Please select a Valid GroomGuide Setup')
    else:
        cmds.warning('Nothing selected, Please select a GroomGuide Setup')


def lJb(*args):
    sel = pm.ls(sl=1)
    for e in sel:
        try:
            val = pm.getAttr(e + '.gr')
            cmds.gradientControlNoAttr('graphCrv', e=True, asString=val)
        except:
            pass


def klPJb(*args):
    cmds.button('drawBtn', e=1, bgc=(0.1, 0.4, 0.5), label='    Draw Guide Curves    ')
    all = cmds.scriptJob(lj=True)
    for a in all:
        if 'pTCr' in a:
            b = int(a.split(':')[0])
            cmds.scriptJob(kill=int(a.split(':')[0]))


def drawCurves(DepthField, redrow, *args):
    global drwGd
    global drwGd2
    global redraw
    global unit
    cmds.button('drawBtn', e=1, bgc=(1, 0.9, 0.2), l='      Drawing Guides      ')
    unit = cmds.floatFieldGrp(DepthField, q=1, v=1)[0]
    redraw = cmds.checkBox(redrow, q=1, v=0)
    if unit < 0.01:
        unit = 0.01
    if unit > 2.0:
        unit = 2.0
    if redraw == 1:
        drwGd = cmds.ls(sl=1)
        drwGd2 = cmds.ls(sl=1)
        if len(drwGd) == 1:
            drwGdShp = cmds.listRelatives(drwGd[0], s=1)[0]
            typ = cmds.objectType(drwGdShp)
            if typ == 'nurbsCurve':
                sel = pm.ls(sl=1)
                cmds.select(cl=1)
                for e in sel:
                    a = pm.listRelatives(e)[0]
                    typ = pm.objectType(a)
                    if typ == 'nurbsCurve':
                        shp = pm.listRelatives(e)[0]
                        b = pm.listConnections(shp)[0]
                        c = pm.listConnections(b, t='nurbsCurve')[1]
                        d = pm.listConnections(b, t='nurbsCurve')[2]
                        e1 = pm.listRelatives(c)[1]
                        f1 = pm.listRelatives(d)[1]
                        g = pm.listConnections(e1)
                        drwGd = [pm.listConnections(f1)[0]]

                cmds.PaintEffectsTool()
                pm.select(outerMesh)
                mel.eval('MakePaintable;')
                if redraw == 1:
                    pm.select(drwGd2)
                cmds.scriptJob(event=['DagObjectCreated', 'pTCr()'], compressUndo=True)
                cmds.scriptJob(event=['ToolChanged', 'klPJb()'], runOnce=True)
            else:
                cmds.warning('Please Select One CrawCurve for Re-draw')
        if len(drwGd) == 0:
            cmds.warning('Please Select One CrawCurve for Re-draw')
    if redraw == 0:
        cmds.PaintEffectsTool()
        pm.select(outerMesh)
        mel.eval('MakePaintable;')
        cmds.select(cl=1)
        if redraw == 1:
            pm.select(drwGd)
        cmds.scriptJob(event=['DagObjectCreated', 'pTCr()'], compressUndo=True)
        cmds.scriptJob(event=['ToolChanged', 'klPJb()'], runOnce=True)


def cuToGuides(*args):
    global redraw
    redraw = 2
    selCu = pm.ls(sl=1)
    for e in selCu:
        try:
            pm.setAttr(e + '.gr', l=0)
            pm.deleteAttr(e + '.gr')
        except:
            pass

    pTCr()


def pTCr(*args):
    doHairMesh = 1

    def blendCurves():
        global drwGd
        global drwGd2

        def rivet():
            snap = 1
            meshhShp = pm.listRelatives(meshh, c=1)
            CPOM = cmds.createNode('closestPointOnMesh')
            pm.connectAttr(meshhShp[0] + '.worldMatrix', CPOM + '.inputMatrix')
            pm.connectAttr(meshhShp[0] + '.worldMesh', CPOM + '.inMesh')
            folls = []
            for e in cu:
                CP = cmds.xform(e + '.cv[' + str(cv) + ']', t=1, q=1, ws=1)
                cmds.xform(e + '.scalePivot', ws=1, t=CP)
                cmds.xform(e + '.rotatePivot', ws=1, t=CP)
                pm.setAttr(CPOM + '.ip', CP[0], CP[1], CP[2], type='double3')
                cmds.makeIdentity(e, apply=1, t=1, r=1, s=1, n=0, pn=1)
                CP = cmds.xform(e + '.scalePivot', q=1, ws=1, t=1)
                pm.setAttr(CPOM + '.ip', CP[0], CP[1], CP[2], type='double3')
                pos = cmds.getAttr(CPOM + '.p')[0]
                op = (-CP[0], -CP[1], -CP[2])
                cmds.xform(e, t=op, r=1, os=1)
                cmds.makeIdentity(e, apply=1, t=1, r=1, s=1, n=0, pn=1)
                cmds.xform(e, t=pos, r=1, os=1)
                cmds.makeIdentity(e, apply=1, t=1, r=1, s=1, n=0, pn=1)
                Upos = pm.getAttr(CPOM + '.u')
                Vpos = pm.getAttr(CPOM + '.v')
                cmds.createNode('follicle')
                mel.eval('pickWalk -d up')
                Tr = cmds.ls(sl=1)[0]
                pm.parent(Tr, snaps)
                cmds.select(Tr)
                cmds.rename('snap_01')
                FollmainT = cmds.ls(sl=1)[0]
                no = FollmainT.split('_')[1]
                mel.eval('pickWalk -d down')
                cmds.rename('snapShp_' + str(no))
                FollmainShp = cmds.ls(sl=1)
                folls.append(FollmainT)
                cmds.hide(FollmainT)
                pm.connectAttr(meshhShp[0] + '.outMesh', FollmainShp[0] + '.inputMesh')
                pm.connectAttr(meshhShp[0] + '.worldMatrix[0]', FollmainShp[0] + '.inputWorldMatrix')
                pm.connectAttr(FollmainShp[0] + '.outRotate', FollmainT + '.rotate')
                pm.connectAttr(FollmainShp[0] + '.outTranslate', FollmainT + '.translate')
                pm.setAttr(FollmainShp[0] + '.parameterU', Upos)
                pm.setAttr(FollmainShp[0] + '.parameterV', Vpos)
                cmds.select(FollmainT, e)
                mel.eval('doCreateParentConstraintArgList 1 { "1","0","0","0","0","0","0","0","1","","1" }')

            pm.delete(CPOM)

        cmds.rename('guideA_01')
        cu1 = cmds.ls(sl=1)
        cmds.parent(cu1, guides)
        cu1 = cmds.ls(sl=1)
        cu2 = cmds.duplicate(cu1, n='guideB_01')
        cu3 = cmds.duplicate(cu1, n='drawGuide_01')
        cvNo = pm.getAttr(cu3[0] + '.spans') + 3
        meshh = innerMesh
        cu = cu1
        cv = 0
        rivet()
        meshh = outerMesh
        cu = cu2
        cv = cvNo - 1
        rivet()
        bs = cmds.blendShape(cu1, cu2, cu3, origin='world', tc=0, n='gbs')
        cmds.blendShape(bs, edit=True, w=[(0, 1), (1, 1)])
        vol = pm.getAttr(innerMesh + '.sv')
        vall = 0
        incr = 1.0 / (cvNo - 1)
        for i in range(cvNo):
            if vol == 'a':
                grphVal = cmds.gradientControlNoAttr('graphCrv2', q=True, valueAtPoint=vall)
            if vol == 'b':
                grphVal = cmds.gradientControlNoAttr('graphCrv', q=True, valueAtPoint=vall)
            if grphVal > 1:
                grphVal = 1
            if grphVal < 0:
                grphVal = 0
            grphValB = 1 - grphVal
            cmds.setAttr(bs[0] + '.inputTarget[' + str(0) + '].inputTargetGroup[0].targetWeights' + '[' + str(i) + ']', grphValB)
            cmds.setAttr(bs[0] + '.inputTarget[' + str(0) + '].inputTargetGroup[1].targetWeights' + '[' + str(i) + ']', grphVal)
            vall += incr

        vall = 0
        cmds.select(cu3)
        cmds.hide(cu1, cu2)
        pm.parent(cu1, guidesBase)
        pm.parent(cu2, guidesBase)
        cud = cmds.ls('*drawGuide*')[0]
        cd = cmds.getAttr(cud + '.dispCV')
        cmds.setAttr(cu3[0] + '.dispCV', cd)
        if doHairMesh == 1:
            cu4 = pm.duplicate(cu3)
            bs = pm.blendShape(cu3, cu4, origin='world', tc=0)
            pm.blendShape(bs, edit=True, w=[0, 1])
            pm.hide(cu4)
            pm.select(hs)
            hc = cmds.ls(sl=1, l=1)
            pm.select(cu4)
            pm.parent(w=1)
            pm.select(cu4)
            cmds.pickWalk(d='down')
            mel.eval('assignHairSystem ' + hc[0])
        if redraw == 1:
            pm.select(drwGd2)
            delGuides()
            cmds.select(cu3[0])
            cmds.rename('drawGuide_01')
            cu3 = cmds.ls(sl=1)
        drwGd = cu3[0]
        drwGd2 = cu3[0]
        pos = pm.xform(drwGd + '.cv[0]', q=1, t=1, ws=1, a=1)
        sph = pm.polySphere(sx=10, sy=6, r=0.1, n='root_pnt_01')[0]
        pm.hyperShade(assign=lam)
        cmds.DeleteHistory()
        pm.xform(t=pos, ws=1)
        pm.parent(sph, rootLocs)
        roots = cmds.ls('root_pnt*', type='transform')
        ss = cmds.getAttr(roots[0] + '.sx')
        pm.xform(sph, s=(ss, ss, ss), a=1)
        cmds.select(drwGd)
        shp = pm.listRelatives(drwGd)[0]
        b = pm.listConnections(shp)[0]
        c = pm.listConnections(b, t='nurbsCurve')[1]
        d = pm.listConnections(b, t='nurbsCurve')[2]
        e1 = pm.listRelatives(c)[1]
        f1 = pm.listRelatives(d)[1]
        g = pm.listConnections(e1)
        try:
            drwGd = [
             pm.listConnections(f1)[0]]
        except:
            pass

    if redraw == 1:
        try:
            sel = cmds.ls(sl=1)
            pm.select(cl=1)
            try:
                pm.select(drwGd)
            except:
                pass

            testSel = cmds.ls(sl=1)
            if len(testSel) == 0:
                cmds.setToolTo('Move')
                cmds.scriptEditorInfo(ch=1)
                cmds.warning('Exiting Draw Mode')
            cmds.select(sel)
            mel.eval('doPaintEffectsToCurve( 0)')
            recu = pm.duplicate(drwGd)
            shp = pm.listRelatives(sel[0], s=1)
            cu2 = pm.listConnections(shp, t='nurbsCurve')
            cu = pm.attachCurve(recu, cu2, ch=0, rpo=0, kmk=0, m=1, bb=1, bki=0, p=1)
            pm.rename(cu, 'guideA_01')
            strk = pm.listConnections(shp, t='brush')[0]
            cu4 = pm.listConnections(strk)[0]
            pm.addAttr(cu[0], ln='gr', dt='string')
            pm.setAttr(cu[0] + '.gr', l=0)
            grph = cmds.gradientControlNoAttr('graphCrv', q=True, asString=True)
            pm.setAttr(cu[0] + '.gr', grph, type='string', l=1)
            ln = pm.arclen(cu[0])
            segs = int(ln / unit)
            pm.rebuildCurve(cu[0], ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=segs, d=3, tol=0.01)
            pm.select(cu[0] + '.cv[0:200]')
            mel.eval('smoothCurve -ch 1 -rpo 1 -s 10')
            pm.select(cu[0])
            delGrp = pm.listRelatives(cu2[0], p=1)
            delGrp = pm.listRelatives(delGrp, p=1)
            pm.select(cu[0])
            doHairMesh = 1
            blendCurves()
            pm.delete(cu4, strk, delGrp)
            shp = pm.listRelatives(outerMesh, s=1, f=1)
            shpCU = pm.listRelatives(shp, c=1, f=1)
            pm.delete(shpCU, recu)
            cmds.scriptEditorInfo(ch=1)
        except:
            pass

    if redraw == 0:
        sel = cmds.ls(sl=1)
        mel.eval('doPaintEffectsToCurve( 0)')
        shp = pm.listRelatives(sel[0], s=1)
        cu = pm.listConnections(shp, t='nurbsCurve')
        strk = pm.listConnections(shp, t='brush')[0]
        cu4 = pm.listConnections(strk)[0]
        pm.addAttr(cu[0], ln='gr', dt='string')
        pm.setAttr(cu[0] + '.gr', l=0)
        grph = cmds.gradientControlNoAttr('graphCrv', q=True, asString=True)
        pm.setAttr(cu[0] + '.gr', grph, type='string', l=1)
        ln = pm.arclen(cu[0])
        segs = int(ln / unit)
        pm.rebuildCurve(cu[0], ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=segs, d=3, tol=0.01)
        pm.select(cu[0] + '.cv[0:200]')
        mel.eval('smoothCurve -ch 1 -rpo 1 -s 10')
        pm.select(cu[0])
        delGrp = pm.listRelatives(cu[0], p=1)
        delGrp = pm.listRelatives(delGrp, p=1)
        pm.select(cu[0])
        doHairMesh = 1
        blendCurves()
        pm.delete(cu4, strk, delGrp)
        shp = pm.listRelatives(outerMesh, s=1, f=1)
        shpCU = pm.listRelatives(shp, c=1, f=1)
        pm.delete(shpCU)
        cmds.scriptEditorInfo(ch=1)
    if redraw == 2:
        sel = pm.ls(sl=1)
        for e in sel:
            pm.addAttr(e, ln='gr', dt='string')
            pm.setAttr(e + '.gr', l=0)
            grph = cmds.gradientControlNoAttr('graphCrv', q=True, asString=True)
            pm.setAttr(e + '.gr', grph, type='string', l=1)
            pm.select(e)
            doHairMesh = 1
            blendCurves()


def showCVs(*args):
    CUs = cmds.ls('*drawGuide*')
    if len(CUs) == 0:
        cmds.warning('Please select Curves')
    if len(CUs) > 0:
        for e in CUs:
            try:
                cmds.setAttr(e + '.dispCV', 1)
            except:
                pass


def hideCVs(*args):
    CUs = cmds.ls('*drawGuide*')
    if len(CUs) == 0:
        cmds.warning('Please select Curves')
    if len(CUs) > 0:
        for e in CUs:
            try:
                cmds.setAttr(e + '.dispCV', 0)
            except:
                pass


def hideMesh(*args):
    pm.hide(hairMesh)


def showMesh(*args):
    pm.showHidden(hairMesh)


def createBlends(*args):
    global CUsA
    global CUsB
    global CUsC
    global bs
    sel = cmds.ls(sl=1)
    CUsA = sel[0]
    CUsB = sel[1]
    CUsC = sel[2]
    bs = cmds.blendShape(CUsA, CUsB, CUsC, origin='world', tc=0)
    cmds.blendShape(bs, edit=True, w=[(0, 1), (1, 1)])


def loadBlends():
    global Crvs
    global CrvsIndex
    global bss
    sel = cmds.ls(sl=1)
    cmds.SelectHierarchy()
    for x in range(10):
        cmds.pickWalk(d='down')

    cmds.pickWalk(d='up')
    Crvs = pm.ls(sl=1)
    cmds.select(sel)
    x = 0
    CrvsIndex = []
    for e in Crvs:
        ci = (
         e, x)
        x += 1
        CrvsIndex.append(ci)

    lr = pm.listRelatives(Crvs[0], s=1)
    lc = pm.listConnections(lr[0])
    bss = []
    for b in lc:
        typ = pm.objectType(b)
        if typ == 'blendShape':
            bss.append(b)

    cmds.select(bss)
    bss = cmds.ls(sl=1)
    cmds.select(sel)


def graphblendGuides(*args):
    sel = pm.ls(sl=1)
    Crvs = pm.ls(sl=1)
    crvvs = []
    for e in sel:
        try:
            sh = pm.listRelatives(e, s=1, typ='nurbsCurve')[0]
            crvvs.append(e)
        except:
            pass

    try:
        vall = 0
        for e in Crvs:
            lr = pm.listRelatives(e, s=1)
            lc = pm.listConnections(lr[0])
            bss = []
            for b in lc:
                typ = pm.objectType(b)
                if typ == 'blendShape':
                    bss.append(b)

            cmds.select(bss)
            bss = cmds.ls(sl=1)
            cvNo = pm.getAttr(e + '.spans') + 3
            incr = 1.0 / (cvNo - 1)
            for i in range(cvNo):
                grphVal = cmds.gradientControlNoAttr('graphCrv', q=True, valueAtPoint=vall)
                if grphVal > 1:
                    grphVal = 1
                if grphVal < 0:
                    grphVal = 0
                grphValB = 1 - grphVal
                cmds.setAttr(bss[0] + '.inputTarget[' + str(0) + '].inputTargetGroup[0].targetWeights' + '[' + str(i) + ']', grphValB)
                cmds.setAttr(bss[0] + '.inputTarget[' + str(0) + '].inputTargetGroup[1].targetWeights' + '[' + str(i) + ']', grphVal)
                vall += incr

            vall = 0
            pm.select(sel)
            grph = cmds.gradientControlNoAttr('graphCrv', q=True, asString=True)
            pm.setAttr(e + '.gr', l=0)
            pm.setAttr(e + '.gr', grph, type='string', l=1)

    except:
        pm.select(crvvs)


def onn(*args):
    gds = pm.listRelatives(guides, c=1)
    roots = pm.listRelatives(rootLocs, c=1)
    pm.hide(roots)


def off(*args):
    gds = pm.listRelatives(guides, c=1)
    roots = pm.listRelatives(rootLocs, c=1)
    pm.showHidden(roots)


def bakeGuides(*args):
    gd = pm.duplicate(guides, n='bakeGuides_01')
    pm.parent(gd, w=1)
    gds = pm.listRelatives(gd)
    for e in gds:
        pm.rename(e, 'bakeCU_01')
        cmds.setAttr(e + '.gr', l=0)
        cmds.deleteAttr(e + '.gr')
        CP = pm.xform(e + '.cv[0]', t=1, q=1, ws=1)
        pm.xform(e + '.scalePivot', ws=1, t=CP)
        pm.xform(e + '.rotatePivot', ws=1, t=CP)


def enterLicense(*args):

    def feedLCK():
        result = cmds.promptDialog(title='Enter your License Key for DrawGroomGuides', message='___________Enter your DrawGroomGuides License Key___________', button=[
         'OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
        if result == 'OK':
            enc = cmds.promptDialog(query=True, text=True)
            enc = str(enc)
        try:

            def getCPK():
                return '744585677675456'

            import base64
            key = getCPK()
            dec = []
            end = base64.urlsafe_b64decode(enc)
            for i in range(len(end)):
                key_c = key[(i % len(key))]
                dec_c = chr((256 + ord(end[i]) - ord(key_c)) % 256)
                dec.append(dec_c)

            Lic = ('').join(dec)
            Lic = Lic.split('_')
            chk1 = cmds.optionVar(q='sphereAxisModeDG')
            chk2 = cmds.optionVar(q='cubeAxisModeDG')
            if chk1 == Lic[0] and chk2 == Lic[1]:
                cmds.optionVar(sv=['sphereAxisModeDMG', Lic[0]])
                cmds.optionVar(sv=['cubeAxisModeDMG', Lic[2]])
                cmds.optionVar(sv=['planeAxisModeDMG', Lic[3]])
                cmds.optionVar(sv=['coneAxisModeDMG', Lic[1]])
                cmds.savePrefs()
                cmds.scriptEditorInfo(clearHistory=1)
                cmds.warning('CONGRATS..!! Your DrawGroomGuides License is Activated.. Kindly relaunch the Tool UI')
            else:
                cmds.warning('License error:' + ' Please Enter Correct License Key')
        except:
            cmds.warning('License error:' + ' Please Enter Correct License Key')

    exs = cmds.optionVar(ex='sphereAxisModeDMG')
    if exs == 1:
        cmds.warning('Your Copy is already Licensed')
    if exs == 0:
        import platform
        OS = platform.system()
        if OS != 'Windows':
            feedLCK()
        if OS == 'Windows':
            import subprocess
            cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            prgs = []
            for line in proc.stdout:
                prg = line.split('.exe')[0]
                if prg == 'maya':
                    prgs.append(prg)

            if len(prgs) > 1:
                cmds.warning('Multiple Maya sessions Open, Please Open only ONE Maya session')
            if len(prgs) == 1:
                feedLCK()


def getActKey(*args):

    def genActKY():
        import uuid, platform
        PCN = platform.node()
        OSnVer = platform.platform()
        MayaVer = cmds.about(version=1)
        ex1 = cmds.optionVar(ex='sphereAxisModeDG')
        ex2 = cmds.optionVar(ex='cubeAxisModeDG')
        ex3 = cmds.optionVar(ex='planeAxisModeDG')
        ex4 = cmds.optionVar(ex='coneAxisModeDG')

        def createKeyWin():
            msgA = cmds.optionVar(q='sphereAxisModeDG')
            msgB = cmds.optionVar(q='cubeAxisModeDG')
            msgC = cmds.optionVar(q='planeAxisModeDG')
            msgD = cmds.optionVar(q='coneAxisModeDG')
            message = msgA + '_' + msgB + '_' + msgC + '_' + msgD + '_' + PCN + '_' + OSnVer + '_' + 'Maya' + MayaVer

            def getCPK():
                return '15031025787585830'

            import base64
            key = getCPK()
            enc = []
            for i in range(len(message)):
                key_c = key[(i % len(key))]
                enc_c = chr((ord(message[i]) + ord(key_c)) % 256)
                enc.append(enc_c)

            enc = base64.urlsafe_b64encode(('').join(enc))
            cmds.warning('Please Copy your `Draw Groom Guides` ACTIVATION KEY and email it to- aka.toools@gmail.com')
            if cmds.window('ETWin', exists=True):
                cmds.deleteUI('ETWin')
            cmds.window('ETWin', title='Activation Key for DrawGroomGuides', h=60, w=600)
            cmds.columnLayout(adj=True)
            cmds.text(label='Please Copy your `Draw Groom Guides` ACTIVATION KEY and email it to- aka.toools@gmail.com')
            cmds.text(label='  ctrl+A then ctrl+C')
            cmds.text(label='')
            cmds.textField('licGBTextField', text=enc, ed=False, annotation='(Ctrl+A) (Ctrl+C)')
            cmds.text(label='')
            cmds.showWindow('ETWin')
            cmds.setFocus('licGBTextField')
            cmds.warning('Your Activation Key is')
            cmds.warning(enc)

        if ex1 != 1 and ex2 != 1 and ex3 != 1 and ex4 != 1:
            loc = str(uuid.uuid4())
            loc = loc.split('-')
            cmds.optionVar(sv=['sphereAxisModeDG', loc[0]])
            cmds.optionVar(sv=['cubeAxisModeDG', loc[2]])
            cmds.optionVar(sv=['planeAxisModeDG', loc[3]])
            cmds.optionVar(sv=['coneAxisModeDG', loc[1]])
            cmds.optionVar(sv=['cylinderAxisModeDG', PCN])
            cmds.savePrefs()
            cmds.scriptEditorInfo(clearHistory=1)
            createKeyWin()
        if ex1 == 1 and ex2 == 1 and ex3 == 1 and ex4 == 1:
            createKeyWin()

    exs = cmds.optionVar(ex='sphereAxisModeDMG')
    if exs == 1:
        cmds.warning('Your DrawGroomGuides Copy is already Licensed')
    if exs == 0:
        import platform
        OS = platform.system()
        if OS != 'Windows':
            genActKY()
        if OS == 'Windows':
            import subprocess
            cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            prgs = []
            for line in proc.stdout:
                prg = line.split('.exe')[0]
                if prg == 'maya':
                    prgs.append(prg)

            if len(prgs) > 1:
                cmds.warning('Multiple Maya sessions Open, Please Open only ONE Maya session')
            if len(prgs) == 1:
                genActKY()


def removeLicense(*args):

    def remLc():
        remConfirm = cmds.confirmDialog(title='Confirm', message='Are you sure you want to remove DrawGroomGuides License?', button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
        if remConfirm == 'No':
            cmds.warning('Relax..Your GroomTools License has NOT been removed')
        if remConfirm == 'Yes':
            reremConfirm = cmds.confirmDialog(title='Confirm', message='Please Re-comfrim..!! Are you sure you want to remove DrawGroomGuides License?', button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
            if reremConfirm == 'No':
                cmds.warning('Relax..Your GroomTools License has NOT been removed')
            if reremConfirm == 'Yes':
                reeremConfirm = cmds.confirmDialog(title='Confirm', message='FINAL RECONFIRM..!! Your FINALLY SURE you want to REMOVE DrawGroomGuides License?', button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
                if reeremConfirm == 'No':
                    cmds.warning('Relax..Your DrawGroomGuides License has NOT been removed')
                if reeremConfirm == 'Yes':
                    cmds.optionVar(sv=['gooh2', 1])
                    cmds.optionVar(remove='sphereAxisModeDG')
                    cmds.optionVar(remove='cubeAxisModeDG')
                    cmds.optionVar(remove='planeAxisModeDG')
                    cmds.optionVar(remove='coneAxisModeDG')
                    cmds.optionVar(remove='sphereAxisModeDMG')
                    cmds.optionVar(remove='cubeAxisModeDMG')
                    cmds.optionVar(remove='planeAxisModeDMG')
                    cmds.optionVar(remove='coneAxisModeDMG')
                    cmds.optionVar(remove='cylinderAxisModeDG')
                    cmds.warning('Your `Draw GroomGuides` License has been successfully REMOVED')
                    cmds.savePrefs()
                    cmds.scriptEditorInfo(clearHistory=1)

    chk1 = cmds.optionVar(ex='sphereAxisModeDMG')
    if chk1 == 0:
        cmds.warning('NO LICENSE FOUND..!! Your Draw GroomGuides Product is not Registered yet..!!')
    if chk1 == 1:
        import platform
        OS = platform.system()
        if OS != 'Windows':
            remLc()
        if OS == 'Windows':
            import subprocess
            cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            prgs = []
            for line in proc.stdout:
                prg = line.split('.exe')[0]
                if prg == 'maya':
                    prgs.append(prg)

            if len(prgs) > 1:
                cmds.warning('Multiple Maya sessions Open, Please Open only ONE Maya session')
            if len(prgs) == 1:
                remLc()


def drawGroomGuidesUI():

    def verifyLic():
        msgA = cmds.optionVar(q='sphereAxisModeDMG')
        msgB = cmds.optionVar(q='cubeAxisModeDMG')
        msgC = cmds.optionVar(q='planeAxisModeDMG')
        msgD = cmds.optionVar(q='coneAxisModeDMG')
        import platform
        PCN = platform.node()
        try:
            userL = str(msgA) + '_' + str(msgB) + '_' + str(msgC) + '_' + str(msgD) + '_' + PCN
        except:
            cmds.warning('License error' + ' Please contact your vendor')

        try:
            msgA = cmds.optionVar(q='sphereAxisModeDG')
            msgB = cmds.optionVar(q='cubeAxisModeDG')
            msgC = cmds.optionVar(q='planeAxisModeDG')
            msgD = cmds.optionVar(q='coneAxisModeDG')
            msgE = cmds.optionVar(q='cylinderAxisModeDG')
            key = str(msgA) + '_' + str(msgC) + '_' + str(msgD) + '_' + str(msgB) + '_' + str(msgE)
        except:
            cmds.warning('License error:' + ' Please contact your vendor')

        userL = key
        return (key, userL)

    cmds.optionVar(remove='GraphGuidesVar')
    cmds.optionVar(remove='GraphGuidesVar2')
    if cmds.window('blendGuides', exists=True):
        cmds.deleteUI('blendGuides')
    cmds.window('blendGuides', title=' Draw Groom Guides V1.5 ', sizeable=1, menuBar=1, resizeToFitChildren=1, h=280, w=320)
    cmds.menu(label=' HELP..!!', tearOff=1)
    cmds.menuItem(label='Get your Activation Key', c=partial(getActKey))
    cmds.menuItem(label='Enter your License Key', c=partial(enterLicense))
    cmds.menuItem(label='About Us', c=partial(aboutUs))
    cmds.menuItem(label='More Products', c=partial(otherProducts))
    cmds.menuItem(label='[Remove License]', c=partial(removeLicense), bld=1)
    cmds.columnLayout('main', adjustableColumn=1)
    cmds.text(label='     Tool developed by - UnPlug Tools         ', bgc=(0.35, 0.4,
                                                                           0.4), h=25)
    cmds.text(label='      ')
    cmds.setParent('main')
    if verifyLic()[0] != verifyLic()[1]:
        cmds.text(label='No License Installed in this PC', h=20)
        cmds.text(label='Click below on <Get your Activation Key>', h=20)
        cmds.button(label='Get your Activation Key', command=partial(getActKey))
        cmds.text(label='Copy your Unique Activation Key', h=20)
        cmds.text(label='and mail it to - aka.toools@gmail.com ', h=20)
        cmds.text(label='along with your Purchase Receipt ', h=20)
        cmds.text(label='OR your Purchase email ID ', h=20)
        cmds.separator(h=10)
        cmds.text(label='Once you recieve your License Key', h=20)
        cmds.text(label=' Enter the Key by clicking below ', h=20)
        cmds.button(label='Enter your License Key', c=partial(enterLicense))
        cmds.showWindow('blendGuides')
    if verifyLic()[0] == verifyLic()[1]:
        cmds.separator(h=10)
        cmds.frameLayout('gaga', label='', collapsable=0, collapse=1)
        cmds.rowColumnLayout(numberOfRows=4, cs=[10, 10])
        cmds.button(label='Create Setup', command=partial(createSetup), w=100)
        cmds.separator(h=10)
        cmds.button(label='Load Setup', command=partial(loadSetup), w=100)
        depthVal = cmds.floatFieldGrp(numberOfFields=1, label='Guide Segments    ', precision=2, value1=0.2, vis=1, step=0.1, cc=partial(switchTool), w=180)
        redrw = cmds.checkBox(l=' Re-Draw Guides', v=0, h=5, onc=partial(switchTool), ofc=partial(switchTool), vis=0)
        cmds.separator(h=10)
        bt = cmds.button('drawBtn', label='    Draw Guide Curves    ', command=partial(drawCurves, depthVal, redrw), bgc=(0.1,
                                                                                                                          0.4,
                                                                                                                          0.5))
        cmds.setParent('gaga')
        cmds.separator(h=10)
        cmds.rowColumnLayout(numberOfRows=3, cs=[10, 10])
        cmds.button(label='Delete Guides', command=partial(delGuides), w=100)
        cmds.text(label='', h=4)
        cmds.button(label='Bake Guides', command=partial(bakeGuides))
        cmds.button(label='Attach multi Curves', command=partial(attachMultiCurves), w=110)
        cmds.text(label='', h=4)
        cmds.button(label='Curves to Guides', command=partial(cuToGuides), w=100)
        cmds.button(label='Draw PFX', command=partial(drawPfx), w=110)
        cmds.text(label='', h=4)
        cmds.button(label='PFX To Curve', command=partial(pfxToCrv), w=110)
        cmds.setParent('gaga')
        cmds.separator(h=15)
        cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
        cmds.text(label=' Rebuild Unit  ', al='left')
        spacingVal = cmds.floatField(minValue=0.1, maxValue=50, precision=2, value=0.3, step=0.1, w=50)
        cmds.text(label='')
        cmds.button(label='Unit Rebuild Curves', c=partial(rebuildCrvsUnitBased, spacingVal), bgc=(0.4,
                                                                                                   0.4,
                                                                                                   0.4), h=20)
        cmds.button(label='Relax Curves', command=partial(smooHairCUs), bgc=(0.4, 0.4,
                                                                             0.4), h=20)
        cmds.setParent('gaga')
        cmds.separator(h=15)
        cmds.setParent('gaga')
        cmds.frameLayout(label='Guides Falloff Shape Graph', collapsable=1, collapse=0)
        cmds.text(label='')
        cmds.optionVar(stringValueAppend=['GraphGuidesVar', '1,1,3'])
        cmds.optionVar(stringValueAppend=['GraphGuidesVar', '0,0,3'])
        cmds.gradientControlNoAttr('graphCrv', h=120, w=280, bgc=(0.2, 0.2, 0.2))
        cmds.gradientControlNoAttr('graphCrv', e=True, optionVar='GraphGuidesVar', cc=partial(graphblendGuides))
        cmds.button(label='Apply Current to All', command=partial(graphblendGuides))
        cmds.text(label='  <-- Root                                                                   Tip -->  ')
        cmds.setParent('gaga')
        cmds.frameLayout(label='Volume Mode Graph', collapsable=1, collapse=1)
        cmds.optionVar(stringValueAppend=['GraphGuidesVar2', '1,1,3'])
        cmds.optionVar(stringValueAppend=['GraphGuidesVar2', '.8,0,3'])
        cmds.gradientControlNoAttr('graphCrv2', h=100, w=280, bgc=(0.2, 0.2, 0.2))
        cmds.gradientControlNoAttr('graphCrv2', e=True, optionVar='GraphGuidesVar2')
        cmds.setParent('gaga')
        cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
        cmds.text(label=' ', h=5)
        cmds.button(label='Set to Volume MODE', command=partial(toScalp), w=145)
        cmds.button(label='Set to Current MODE', command=partial(toCurrent), w=145)
        cmds.setParent('gaga')
        cmds.text(label='       ', h=5)
        cmds.frameLayout(label='Misc Controls', collapsable=1, collapse=0)
        cmds.rowColumnLayout(numberOfColumns=4, cs=[10, 10])
        cmds.text(label='       ')
        cmds.rowColumnLayout(numberOfColumns=5, cs=[10, 10])
        cmds.checkBox(label='Draw-Guide CVs', onc=partial(showCVs), ofc=partial(hideCVs))
        cmds.button(label='   +   ', command=partial(rootPntScaleUp))
        cmds.text(label='  ')
        cmds.checkBox(label='Guide Mesh', onc=partial(showMesh), ofc=partial(hideMesh), v=1)
        cmds.button(label='   +   ', command=partial(hairMeshScaleUp))
        cmds.checkBox(label='Maya-Curve CVs', onc=partial(showCVss), ofc=partial(hideCVss))
        cmds.button(label='   -   ', command=partial(rootPntScaleDown))
        cmds.text(label='')
        cmds.checkBox(label='Root Points', onc=partial(off), ofc=partial(onn), v=1)
        cmds.button(label='   +   ', command=partial(hairMeshScaleDown))
        cmds.rowColumnLayout(numberOfColumns=1, cs=[10, 10])
        cmds.setParent('gaga')
        try:
            cmds.select(guides)
            cmds.select(cl=1)
            cmds.frameLayout('gaga', vis=1, e=1, collapse=0)
            cmds.window('blendGuides', e=1, h=150, w=350)
            cmds.showWindow('blendGuides')
        except:
            cmds.button('btn01', label='Create Setup', command=partial(createSetup), w=100, p='main')
            cmds.separator(h=10)
            cmds.button('btn02', label='Load Setup', command=partial(loadSetup), w=100, p='main')
            cmds.window('blendGuides', e=1, h=150, w=350)
            cmds.frameLayout('gaga', vis=0, e=1, collapse=1)
            cmds.showWindow('blendGuides')
            cmds.text(label='')
            cmds.setParent('gaga')


cmds.scriptJob(event=['SelectionChanged', partial(lJb)], compressUndo=True)
