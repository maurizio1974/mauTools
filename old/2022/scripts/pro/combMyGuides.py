# uncompyle6 version 3.7.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: C:/Users/Abhishek/Documents/maya/2018/scripts\combMyGuides.py
# Compiled at: 2021-05-20 22:50:16
import maya.cmds as cmds, maya.mel as mel
from functools import partial
from compiler.ast import flatten
import random as rand
from math import *
import time, maya.api.OpenMaya as om, pymel.core as pm, colorsys, json, urllib2, threading, time, os

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


def tuts(*args):
    import webbrowser
    webbrowser.open('https://www.youtube.com/playlist?list=PLjdbFNyrLnM0wqvtJGj0y3xWkdIE3J7lx')


def aboutUs(*args):
    import webbrowser
    webbrowser.open('https://www.facebook.com/UnPlugTools')


def otherProducts(*args):
    import webbrowser
    webbrowser.open('https://gumroad.com/unplugtools')


def switches(*args):
    global switch1
    global switch2
    global switch3
    global switch4
    global switch5
    switch1 = 0
    switch2 = 0
    switch3 = 0
    switch4 = 0
    switch5 = 0


def toolsHelp(*args):
    windowID = 'toolsHelpUI'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Comb my Guides Tools Help', sizeable=1, resizeToFitChildren=1, h=300, w=300)
    cmds.scrollLayout('scrollLayout')
    cmds.columnLayout(adjustableColumn=1)
    cmds.separator(h=20)
    cmds.text(label=' --- CREATE TOOL WINDOW UI --- ', al='left')
    cmds.text(label=' ')
    cmds.text(label='    CREATE GUIDES FROM MESH - These Toolsets work on Poly or Nurbs Meshes', al='left')
    cmds.text(label='        Create From Poly Tubes - Selection Order - 1st Select the Poly Tubes, Then Select the Scalp mesh ', al='left')
    cmds.text(label='            - Converts Poly-tubes Edges to Guides, all at one single Click ', al='left')
    cmds.text(label='            - Selection Order - 1st Select the Poly Tubes, Then Select the Scalp mesh ', al='left')
    cmds.text(label='        Create From Multi Loop ', al='left')
    cmds.text(label='        Create Volume Guides - works on Nurbs Tubes ', al='left')
    cmds.text(label='        Create Twisty Guides - works on Nurbs Tubes ', al='left')
    cmds.text(label=' ')
    cmds.text(label='    CREATE GUIDES FROM CURVES - These Toolsets work on Existing Guide-Curves', al='left')
    cmds.text(label='        Create Steppy Guides - works on Nurbs curves ', al='left')
    cmds.text(label='        Create Curly Guides - works on Nurbs curves ', al='left')
    cmds.text(label='        Create Interpolated Guides - works on scalp mesh vertices ', al='left')
    cmds.text(label=' ')
    cmds.text(label='    Create Length Map based on guide-lengths - ', al='left')
    cmds.separator(h=10)
    cmds.text(label=' ')
    cmds.text(label=' --- MODIFY TOOL  --- ', al='left')
    cmds.text(label='        SoftsSnap Guides with Falloff Diatance', al='left')
    cmds.text(label='        Rebuild guide-curves based on input units value', al='left')
    cmds.text(label='        Randomize guides lengths based on input % value  ', al='left')
    cmds.text(label='        Smooth guide-curves based on smooth value', al='left')
    cmds.text(label='        Standard Rebuild guide-curves based on input segments-count', al='left')
    cmds.text(label='        Remove Penetrations on guide cvs based on input offset value', al='left')
    cmds.text(label='        Select random elements from input elements based on input percentage value', al='left')
    cmds.text(label='        Create skinned-joints on guide-curves for tweaking their shapes', al='left')
    cmds.text(label='        Select First & Last CV on guide-curves', al='left')
    cmds.text(label='        Grow CV selections', al='left')
    cmds.text(label='        Trim scalp-penetrated guide-curves from roots', al='left')
    cmds.text(label='        Move guide-curves Pivots to their roots', al='left')
    cmds.text(label='        Maya Standard: Freeze Transform', al='left')
    cmds.text(label='        Maya Standard: Delete History', al='left')
    cmds.text(label='        Relax-smooth guide-curves', al='left')
    cmds.text(label='        Maya Standard: Nurbs Loft', al='left')
    cmds.text(label='        Maya Standard: Reverse guide-curves direction', al='left')
    cmds.text(label='        Snap whole guides cvs on to Scalp surface', al='left')
    cmds.separator(h=10)
    cmds.text(label=' ')
    cmds.text(label=' --- DISPLAY GUIDES  --- ', al='left')
    cmds.text(label='        Change guide-curves display colors based on input color', al='left')
    cmds.text(label='        Change guide-curves display colors based on input scalp-texture-map', al='left')
    cmds.text(label='        Show/Hide guide-curves CVs  ', al='left')
    cmds.text(label='        Viewport Selection Filters -', al='left')
    cmds.text(label='        Toggle between Object & Sub-object mode', al='left')
    cmds.text(label='            Filter - Mesh only viewport selection', al='left')
    cmds.text(label='            Filter - Mesh only viewport selection', al='left')
    cmds.text(label='            Filter - Curves only viewport selection', al='left')
    cmds.separator(h=10)
    cmds.text(label=' ')
    cmds.text(label=' --- DEFORM GUIDES  --- ', al='left')
    cmds.text(label='        Transfer Skinning from input-mesh to guide-curves', al='left')
    cmds.text(label='        Blend deform guide-curves from Root-to-Tip based on input graph', al='left')
    cmds.text(label='        Stick/constraint guide-curves to Scalp mesh', al='left')
    cmds.text(label='        Maya Standard: apply FFD', al='left')
    cmds.separator(h=10)
    cmds.text(label=' ')
    cmds.text(label=' --- MISCELLANEOUS TOOLS  --- ', al='left')
    cmds.text(label='        Export & Import Face Selection Sets from one mesh to another mesh (ideal for meshes with same Topologies & face count)', al='left')
    cmds.text(label='        Transfer Face Selection Sets from one mesh to another mesh, based on Face Proximities (for meshes with different Topologies)', al='left')
    cmds.text(label='        Remove / Clean Scene NameSpaces')
    cmds.separator(h=20)
    cmds.showWindow(windowID)


def HairSystemOutliner(*args):
    window = cmds.window('window', wh=(400, 300))
    cmds.paneLayout(configuration='vertical2')
    editor1 = cmds.outlinerEditor(shp=True)
    editor2 = cmds.outlinerEditor(shp=True)
    hs = cmds.ls(type='hairSystem')
    inputList1 = cmds.selectionConnection(connectionList=True)
    for e in hs:
        cmds.selectionConnection(inputList1, e=True, obj=e)

    dc = cmds.ls(type='dynamicConstraint')
    inputList2 = cmds.selectionConnection(connectionList=True)
    for e in dc:
        cmds.selectionConnection(inputList2, e=True, obj=e)

    fromEditor1 = cmds.selectionConnection(activeList=True)
    fromEditor2 = cmds.selectionConnection(activeList=True)
    cmds.editor(editor1, edit=True, mainListConnection=inputList1)
    cmds.editor(editor1, edit=True, selectionConnection=fromEditor1)
    cmds.editor(editor2, edit=True, mainListConnection=inputList2)
    cmds.editor(editor2, edit=True, selectionConnection=fromEditor2)
    cmds.showWindow(window)


def vtxToGuide(*args):
    sel = cmds.ls(sl=1)
    if len(sel) == 2:
        selTp = sel[0].split('[')[0]
        selType = selTp.split('.')[1]
        objName = selTp.split('.')[0]
        if selType == 'vtx':
            pnt = sel[0].split('[')[1]
            pnt1 = int(pnt.split(']')[0])
            pnt = sel[1].split('[')[1]
            pnt2 = int(pnt.split(']')[0])
            cmds.polySelect(objName, shortestEdgePath=(pnt1, pnt2))
            cmds.polyToCurve(ch=0, form=2, degree=2, conformToSmoothMeshPreview=1)
            cmds.SmoothHairCurves()
            cmds.SmoothHairCurves()
        else:
            cmds.warning('Please select 2 vertices')
    else:
        cmds.warning('Please select 2 vertices')


def drawPfx(*args):
    cmds.PaintEffectsTool()
    mel.eval('MakePaintable;')


def pfxToCrv(*args):
    sel = cmds.ls(sl=1)
    for e in sel:
        try:
            pm.select(guideGrp)
        except:
            guideGrp = pm.group(w=1, n='pfxGuidesGrp_01')

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
        pm.parent(cu[0], guideGrp)
        pm.delete(cu4, strk, delGrp, c)

    pm.select(guideGrp)


def stepCrvs(unitField, subCuLenField, *args):
    cus = cmds.ls(sl=1)
    unit = cmds.floatField(unitField, q=1, v=1)
    subCuLen = cmds.floatField(subCuLenField, q=1, v=1)
    for cu in cus:
        seg = cmds.getAttr(cu + '.spans') + 3
        cmds.rebuildCurve(cu, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=seg, d=3, tol=0.01)
        leng = cmds.arclen(cu)
        count = int(leng / unit)
        incr = 1.0 / count
        val = 0
        ps = []
        subCus = []
        for e in range(count):
            p = cmds.pointOnCurve(cu, pr=val, p=1)
            ps.append(p)
            val2 = val
            ps2 = []
            for f in range(6):
                p2 = cmds.pointOnCurve(cu, pr=val2, p=1)
                if p2 != [0.0, 0.0, 0.0]:
                    ps2.append(p2)
                val2 += incr * subCuLen / 5

            val += incr
            if len(ps2) > 4:
                subCu = cmds.curve(d=3, p=ps2)
                subCus.append(subCu)

        cmds.group(subCus)
        pivotToRoot()


def GuidesGrpToTubesWIP(*args):
    sel = cmds.ls(sl=1)
    cmds.SelectHierarchy(cmds.select(sel[0]))
    cmds.SelectHierarchy()
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='up')
    cus = cmds.ls(sl=1, fl=1)
    msh = sel[1]
    meshShape = cmds.listRelatives(msh, s=1)
    clsPntNode = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(meshShape[0] + '.worldMatrix', clsPntNode + '.inputMatrix')
    cmds.connectAttr(meshShape[0] + '.worldMesh', clsPntNode + '.inMesh')
    vtxs = []
    cuPs = []
    units = 7
    for i in cus:
        p = cmds.xform(i + '.cv[0]', q=1, ws=1, t=1)
        cmds.setAttr(clsPntNode + '.ip', p[0], p[1], p[2], type='double3')
        vtx = cmds.getAttr(clsPntNode + '.vt')
        vtx = msh + '.vtx[' + str(vtx) + ']'
        vtxs.append(vtx)
        vtxP = cmds.xform(vtx, q=1, ws=1, t=1)
        cmds.xform(i + '.cv[0]', ws=1, t=vtxP)
        p = cmds.xform(i + '.cv[0]', q=1, ws=1, t=1)
        p2 = ([str(p[0])[0:units], str(p[1])[0:units], str(p[2])[0:units]], [i])
        cuPs.append(p2)

    cmds.select(vtxs)
    cmds.ConvertSelectionToEdgePerimeter()
    cmds.polyToCurve(ch=0, form=1, degree=1)
    borderCu = cmds.ls(sl=1, fl=1)[0]
    cmds.select(borderCu + '.cv[*]')
    borderCvs = cmds.ls(sl=1, fl=1)
    loftCrvs = []
    for e in borderCvs:
        p = cmds.xform(e, q=1, ws=1, t=1)
        p2 = [str(p[0])[0:units], str(p[1])[0:units], str(p[2])[0:units]]
        for f in cuPs:
            if p2 == f[0]:
                loftCrvs.append(f[1][0])

    cmds.delete(clsPntNode, borderCu)
    cmds.select(loftCrvs)
    cmds.sets()
    lft = cmds.loft(ch=0, u=1, c=1, ar=1, d=3, ss=1, rn=0, po=0, rsn=1)[0]
    cmds.reverseSurface(lft, d=1, ch=0, rpo=1)
    cmds.select(lft)


def createTiedBunchGuides(*arg):
    sel = cmds.ls(sl=1, fl=1)
    pole = sel[0]
    cmds.select(pole + '.cv[*]')
    poles = cmds.ls(sl=1, fl=1)
    poss = []
    for e in poles:
        pos = cmds.xform(e, q=1, t=1, a=1, ws=1)
        poss.append(pos)

    if cmds.objectType(sel[1]) == 'objectSet':
        cmds.select(sel[1])
        vtx = cmds.ls(sl=1, fl=1)
    else:
        cmds.select(sel[1])
        cmds.SelectHierarchy()
        cmds.pickWalk(d='down')
        cmds.pickWalk(d='down')
        cmds.pickWalk(d='up')
        cmds.SelectCurveCVsFirst()
        cmds.pickWalk(d='up')
        vtx = cmds.ls(sl=1, fl=1)
    cus = []
    for e in vtx:
        vpos = cmds.xform(e, q=1, t=1, a=1, ws=1)
        poss.insert(0, vpos)
        cu = cmds.curve(d=3, p=poss)
        poss.remove(vpos)
        cus.append(cu)

    cmds.group(cus, n='guidesBunch_01')


def joinGuideSets(*args):
    sel = cmds.ls(sl=1, fl=1)
    cmds.select(sel[0])
    cmds.SelectHierarchy()
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='up')
    cus1 = cmds.ls(sl=1, fl=1)
    cmds.select(sel[1])
    cmds.SelectHierarchy()
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='up')
    cus2 = cmds.ls(sl=1, fl=1)
    attachedCus = []
    for e, f in zip(cus1, cus2):
        cu = cmds.attachCurve(e, f, ch=0, rpo=0, p=0.1)[0]
        attachedCus.append(cu)

    cmds.group(attachedCus)


def attachMultiCurves():
    cmds.duplicate()
    try:
        cmds.parent(w=1)
    except:
        pass

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


def bunchSetup(*args):
    sel = pm.ls(sl=1)
    centerCu = sel[1]
    cuOrig = sel[0]
    centerCu2 = pm.duplicate(centerCu)
    cuBaseG = pm.duplicate(cuOrig, n='cuBase')
    pm.select(cuBaseG)
    cmds.SelectHierarchy()
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='up')
    cusBase = pm.ls(sl=1)
    segs = []
    for e in cusBase:
        seg = pm.getAttr(e + '.spans') + 3
        segs.append(seg)

    segs.sort()
    segs.reverse()
    maxSegs = segs[0]
    pm.rebuildCurve(centerCu2, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=maxSegs, d=3, tol=0.01)
    for e in cusBase:
        pm.rebuildCurve(e, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=maxSegs, d=3, tol=0.01)

    cuCollapseG = pm.duplicate(cuBaseG, n='cuTarget')
    pm.select(cuCollapseG)
    cmds.SelectHierarchy()
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='up')
    cuCollapse = pm.ls(sl=1)
    cuDefG = pm.duplicate(cuBaseG, n='cuDef')
    pm.select(cuDefG)
    cmds.SelectHierarchy()
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='up')
    cuDef = pm.ls(sl=1)
    for e in cuCollapse:
        pm.blendShape(centerCu2, e, origin='world', w=[0, 1])
        pm.delete(e, ch=1)

    pm.hide(cuOrig)
    pm.select(cuBaseG, cuCollapseG, cuDefG)
    createBlends()
    pm.select(cuDefG)
    loadBlends()
    graphBlendCUs()
    pm.delete(cuBaseG, cuCollapseG, centerCu2)


def randPercSel(percField, *args):
    percentage = cmds.intField(percField, q=1, v=1)
    sel = cmds.ls(sl=1, fl=1)
    rand.shuffle(sel)
    no = len(sel)
    perc = 100.0 / percentage
    sel2 = sel[0:int(no / perc)]
    cmds.select(sel2)


def guideToLenMap(*args):
    CuList = []
    inMesh = []
    sel = []
    try:
        sel = myList = cmds.ls(sl=1)
        cmds.SelectHierarchy()
        cmds.pickWalk(d='down')
        myList = cmds.ls(sl=1)
        cmds.pickWalk(d='up')
        myList2 = cmds.ls(sl=1)
        for e, f in zip(myList, myList2):
            typ = cmds.objectType(e)
            if typ == 'nurbsCurve':
                CuList.append(f)
            if typ == 'mesh':
                inMesh.append(f)

        inMesh = [
         inMesh[0]]
    except:
        pass

    print CuList
    print inMesh
    if len(CuList) < 4 or len(inMesh) < 1:
        cmds.warning('Please select valid inputs : Minimum 4 Curves and a Scalp Mesh')
        CuList = []
        inMesh = []
    else:
        cmds.select(inMesh)
        cmds.makeIdentity(a=1)
        QC = cmds.polyColorSet(q=1, acs=1)
        if QC == None:
            pass
        else:
            for i in QC:
                cmds.polyColorSet(d=1, cs=i)

            meshh = cmds.duplicate(inMesh, n='colScalp')
            CPOM = cmds.createNode('closestPointOnMesh')
            cmds.connectAttr(meshh[0] + '.outMesh', CPOM + '.inMesh')
            x = CuList
            window = cmds.window(t='Transfer Progress')
            cmds.columnLayout()
            progressControl = cmds.progressBar(maxValue=len(x) * 3, width=300)
            cmds.showWindow(window)
            initialTime = time.time()
            p = 0
            rpAll = []
            for each in CuList:
                RootCU = cmds.xform(each + '.cv[0]', t=1, q=1, ws=1)
                cmds.polyPlane(sx=1, sy=1, h=0.001, w=0.001, n='RP_01')
                RootPl = cmds.ls(sl=1)
                rpAll.append(RootPl)
                cmds.move(RootCU[0], RootCU[1], RootCU[2], a=1)
                progressInc = cmds.progressBar(progressControl, edit=True, pr=p + 1)
                p = p + 1

            rpAll = [ val for sublist in rpAll for val in sublist ]
            cmds.transferAttributes(rpAll, meshh, transferPositions=1)
            cmds.select(meshh)
            cmds.polyMergeVertex()
            cmds.DeleteHistory()
            cmds.select(clear=1)
            cmds.delete(rpAll)
            CULenList = []
            for myobj in CuList:
                cmds.select(myobj)
                ArcLen2 = cmds.arclen(myobj)
                ArcLen = round(ArcLen2, 1)
                CULenList.append(ArcLen)
                cmds.select(clear=1)

            baap = max(CULenList)
            VTList = []
            for each in CuList:
                RootP = cmds.pointPosition(each + '.cv[0]')
                cmds.setAttr(CPOM + '.inPositionX', RootP[0])
                cmds.setAttr(CPOM + '.inPositionY', RootP[1])
                cmds.setAttr(CPOM + '.inPositionZ', RootP[2])
                VT = cmds.getAttr(CPOM + '.vt')
                VTList.append(VT)
                progressInc = cmds.progressBar(progressControl, edit=True, pr=p + 1)
                p = p + 1

            VTColVal = []
            for i in CULenList:
                cVal = i / baap
                VTColVal.append(cVal)

            for i, j in map(None, VTList, VTColVal):
                cmds.polyColorPerVertex(meshh[0] + '.vtx[%d]' % i, rgb=(j, j, j))
                progressInc = cmds.progressBar(progressControl, edit=True, pr=p + 1)
                p = p + 1

        cmds.select(meshh, inMesh)
        cmds.transferAttributes(pos=0, nml=0, uvs=0, col=2, spa=0, sus='map1', tus='map1', sm=3, fuv=0, clb=1)
        cmds.DeleteHistory()
        cmds.delete(meshh)
        cmds.select(inMesh)
        cmds.polyColorSet(currentColorSet=1, colorSet='colorSet1')
        cmds.polyColorSet(rename=1, colorSet='colorSet1', newColorSet='Guides_Len_Map')
        cmds.select(CuList, inMesh)
        cmds.deleteUI(window)
        finalTime = time.time()
        TotalTime = finalTime - initialTime
        TotalTime = round(TotalTime, 2)
        cmds.warning('Total time Taken: ' + str(TotalTime) + ' secs')
    return


def BlurMap(*args):
    sm = mel.eval('PaintVertexColorTool; artAttrPaintVertexCtx -e -clear `currentCtx`; objectDetailsBackfaces(); objectDetailsSmoothness(); dR_moveRelease;')


def MapSave(*args):
    sm = mel.eval('PaintVertexColorTool; artExportMapDialog "artAttrPaintVertexCtx"; artExportFileTypeValue "TIFF" artAttrPaintVertexCtx; dR_moveRelease;')
    maya.cmds.setToolTo('Move')
    mel.eval('colorSetDisplay 0"-colorShadedDisplay" 0;')


def loadScalpGuides(*args):
    global CuList
    global inMesh
    CuList = []
    inMesh = []
    sel = []
    try:
        sel = myList = cmds.ls(sl=1)
        cmds.SelectHierarchy()
        cmds.pickWalk(d='down')
        myList = cmds.ls(sl=1)
        cmds.pickWalk(d='up')
        myList2 = cmds.ls(sl=1)
        for e, f in zip(myList, myList2):
            typ = cmds.objectType(e)
            if typ == 'nurbsCurve':
                CuList.append(f)
            if typ == 'mesh':
                inMesh.append(f)

        inMesh = [
         inMesh[0]]
    except:
        pass

    if len(CuList) < 4 or len(inMesh) < 1:
        cmds.warning('Please select valid inputs : Minimum 4 Curves and a Scalp Mesh')
        CuList = []
        inMesh = []
    else:
        cmds.warning('Input Loaded')
    cmds.select(sel)


def iPolSsetup(*args):
    global CuList2
    global cusSet
    global fcs
    global ipolMesh
    global vtxs
    cmds.select(inMesh)
    cmds.duplicate(n='wholeScalp')
    ipolMesh = cmds.ls(sl=1)
    CPOM = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(ipolMesh[0] + '.outMesh', CPOM + '.inMesh')
    CuList2 = cmds.duplicate(CuList)
    rpAll = []
    for each in CuList2:
        RootCU = cmds.xform(each + '.cv[0]', t=1, q=1, ws=1)
        cmds.xform(each + '.scalePivot', ws=1, t=RootCU)
        cmds.xform(each + '.rotatePivot', ws=1, t=RootCU)
        cmds.polyPlane(sx=1, sy=1, h=0.001, w=0.001, n='RP_01')
        RootPl = cmds.ls(sl=1)
        rpAll.append(RootPl)
        cmds.move(RootCU[0], RootCU[1], RootCU[2], a=1)

    rpAll = [ val for sublist in rpAll for val in sublist ]
    cmds.transferAttributes(rpAll, ipolMesh, transferPositions=1)
    cmds.select(ipolMesh)
    cmds.polyMergeVertex()
    cmds.DeleteHistory()
    cmds.select(clear=1)
    cmds.delete(rpAll)
    VTList = []
    for each in CuList2:
        RootP = cmds.pointPosition(each + '.cv[0]')
        cmds.setAttr(CPOM + '.inPositionX', RootP[0])
        cmds.setAttr(CPOM + '.inPositionY', RootP[1])
        cmds.setAttr(CPOM + '.inPositionZ', RootP[2])
        VT = cmds.getAttr(CPOM + '.vt')
        VT2 = (ipolMesh[0] + '.vtx[' + str(VT) + ']', each)
        VTList.append(VT2)

    cmds.select(ipolMesh, inMesh)
    cmds.transferAttributes(pos=0, nml=0, uvs=0, col=1, spa=0, sus='map1', tus='map1', sm=3, fuv=0, clb=1)
    cmds.DeleteHistory()
    cmds.polyTriangulate(ipolMesh)
    cmds.select(ipolMesh)
    cmds.ConvertSelectionToFaces()
    fcs = cmds.ls(sl=1, fl=1)
    cusSet = []
    vtxs = []
    for e in fcs:
        vtx = cmds.polyListComponentConversion(e, tv=1)
        cmds.select(vtx)
        vt = cmds.ls(sl=1, fl=1)
        vtxs.append(vt)
        cus = []
        for f in vt:
            for x in VTList:
                if f == x[0]:
                    cus.append(x[1])

        cusSet.append(cus)

    cmds.select(cl=1)


def interpolateGuides(*args):
    if len(CuList) > 4 or len(inMesh) > 1:
        initialTime = time.time()
        pnts = cmds.ls(sl=1, fl=1)
        if len(pnts) < 1000:
            try:
                pnt = pnts[0].split('[')[0]
                pnt = pnt.split('.')
                if pnt[1] == 'vtx':
                    if pnt[0] == inMesh[0]:
                        window = cmds.window(t='Interpolation Progress')
                        cmds.columnLayout()
                        progressControl = cmds.progressBar(maxValue=len(pnts), width=300)
                        cmds.showWindow(window)
                        e = cmds.ls(sl=1)
                        iPolSsetup()
                        CPOM = cmds.createNode('closestPointOnMesh')
                        cmds.connectAttr(ipolMesh[0] + '.outMesh', CPOM + '.inMesh')
                        cmds.polyColorPerVertex(inMesh, r=0.5, g=0.5, b=0.5, cdo=1)
                        spns = []
                        for e in CuList2:
                            spn = cmds.getAttr(e + '.spans')
                            spns.append(spn)

                        spns.sort()
                        spns.reverse()
                        spns = spns[0]
                        for e in CuList2:
                            cmds.rebuildCurve(e, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=spns, d=3, tol=0.01)

                        cvcnt = spns
                        cvcnt = cvcnt + 3
                        ap = []
                        for e in range(cvcnt):
                            x = [
                             0, 0, 0]
                            ap.append(x)

                        pos = []
                        for e in pnts:
                            p = cmds.xform(e, t=1, q=1, ws=1)
                            pos.append(p)

                        cus = []
                        p = 0
                        for e, ee in zip(pos, pnts):
                            cmds.setAttr(CPOM + '.inPositionX', e[0])
                            cmds.setAttr(CPOM + '.inPositionY', e[1])
                            cmds.setAttr(CPOM + '.inPositionZ', e[2])
                            fac = cmds.getAttr(CPOM + '.f')
                            for f, g, i in zip(fcs, cusSet, vtxs):
                                ff = f.split('[')[1]
                                ff = int(ff.split(']')[0])
                                if fac == ff:
                                    cmds.polyColorPerVertex(i[0], rgb=(1, 0, 0))
                                    cmds.polyColorPerVertex(i[1], rgb=(0, 1, 0))
                                    cmds.polyColorPerVertex(i[2], rgb=(0, 0, 1))
                                    cmds.transferAttributes(ipolMesh[0], inMesh, pos=0, nml=0, tuv=0, col=1, sampleSpace=0, sourceUvSpace='map1', targetUvSpace='map1', searchMethod=3, flipUVs=0, colorBorders=1)
                                    cmds.delete(inMesh, ch=1)
                                    ipol = cmds.curve(d=3, p=ap)
                                    cus.append(ipol)
                                    bs = cmds.blendShape(g, ipol, origin='world')
                                    rgb = cmds.polyColorPerVertex(ee, q=1, rgb=1)
                                    cmds.blendShape(bs, edit=1, w=[(0, rgb[0])])
                                    cmds.blendShape(bs, edit=1, w=[(1, rgb[1])])
                                    cmds.blendShape(bs, edit=1, w=[(2, rgb[2])])
                                    cmds.delete(ipol, ch=1)
                                    Pos = cmds.xform(ipol + '.cv[0]', t=1, q=1, ws=1)
                                    cmds.xform(ipol + '.scalePivot', ws=1, t=Pos)
                                    cmds.xform(ipol + '.rotatePivot', ws=1, t=Pos)
                                    cmds.xform(ipol, t=[-Pos[0], -Pos[1], -Pos[2]], ws=1, a=1)
                                    cmds.xform(ipol, t=e, r=1)
                                    progressInc = cmds.progressBar(progressControl, edit=True, pr=p + 1)
                                    p = p + 1

                        cmds.delete(ipolMesh, CuList2)
                        cmds.polyColorSet(inMesh, d=1, cs='colorSet1')
                        cmds.group(cus, n='ipol_guides_01')
                        finalTime = time.time()
                        TotalTime = finalTime - initialTime
                        TotalTime = round(TotalTime, 2)
                        cmds.deleteUI(window)
                        cmds.warning('Total time Taken: ' + str(TotalTime) + ' secs')
                    else:
                        cmds.warning('Please select Correct Scalp Mesh Vertices')
                else:
                    cmds.warning('Please select Correct Scalp Mesh Vertices')
            except:
                cmds.warning('Please select Correct Scalp Mesh Vertices')

        else:
            cmds.warning('Please select less than 1000 Vertices')
    else:
        cmds.warning('Please Load valid inputs : Minimum 4 Curves and a Scalp Mesh')


def transferSelSets(*args):
    selected = cmds.ls(selection=True)
    a = len(selected)
    if a > 1:
        fullMesh = selected[(-1)]
        set = selected[0:len(selected) - 1]
        typs = []
        for e in set:
            typ = cmds.objectType(e)
            if typ == 'objectSet':
                typs.append(typ)

        if len(typs) == len(set):
            shp = cmds.listRelatives(fullMesh)
            if shp != None:
                typ = cmds.objectType(shp)
                if typ == 'mesh':
                    setNew = []
                    for e in set:
                        st = []
                        cmds.select(e)
                        fcs = cmds.ls(sl=1, fl=1)
                        mshName = fcs[0].split('.')[0]
                        for f in fcs:
                            a = f.split(']')
                            b = a[0].split('[')[1]
                            st.append(b)

                        c = (
                         st, [e])
                        setNew.append(c)

                    cmds.select(mshName)
                    cmds.duplicate()
                    mesh = cmds.ls(sl=1)[0]
                    mesh = cmds.ls(sl=1)[0]
                    mshShp = cmds.listRelatives(mesh, c=1)
                    pieces = []
                    for e in setNew:
                        fcs = []
                        for f in e[0]:
                            fc = mesh + '.f[' + f + ']'
                            fcs.append(fc)

                        cmds.polyChipOff(fcs, ch=1, kft=1, dup=1, off=0)
                        cmds.polySeparate(mshShp, rs=1, ch=1)
                        meshes = cmds.ls(sl=1)
                        cmds.parent(meshes, w=1)
                        cmds.DeleteHistory()
                        cmds.select(meshes[1])
                        cmds.rename(e[1][0] + '_new')
                        ps = cmds.ls(sl=1)[0]
                        pieces.append(ps)
                        mesh = meshes[0]
                        mshShp = cmds.listRelatives(mesh, c=1)
                        cmds.select(mesh)

                    cmds.delete()
                    for ee, ff in zip(pieces, setNew):
                        meshName = ee
                        meshShape = cmds.listRelatives(meshName, shapes=True)
                        cmds.select(fullMesh)
                        cmds.ConvertSelectionToVertices()
                        vtxList = cmds.ls(sl=1, fl=1)
                        clsPntNode = cmds.createNode('closestPointOnMesh')
                        cmds.connectAttr(meshShape[0] + '.worldMatrix', clsPntNode + '.inputMatrix')
                        cmds.connectAttr(meshShape[0] + '.worldMesh', clsPntNode + '.inMesh')
                        bb = cmds.xform(ee, q=1, bb=1)
                        xRange = (bb[0], bb[3])
                        yRange = (bb[1], bb[4])
                        zRange = (bb[2], bb[5])
                        CUs = []
                        for e in vtxList:
                            endPos = cmds.xform(e, query=True, worldSpace=True, translation=True)
                            if xRange[0] <= endPos[0] <= xRange[1] and yRange[0] <= endPos[1] <= yRange[1] and zRange[0] <= endPos[2] <= zRange[1]:
                                cmds.setAttr(clsPntNode + '.ip', endPos[0], endPos[1], endPos[2], type='double3')
                                newPos = cmds.getAttr(clsPntNode + '.p')
                                newPosF = flatten(newPos)
                                distance = sqrt(pow(endPos[0] - newPosF[0], 2) + pow(endPos[1] - newPosF[1], 2) + pow(endPos[2] - newPosF[2], 2))
                                if distance < 0.03:
                                    CU = cmds.ls(e)
                                    CUs.append(CU)

                        CUsF = flatten(CUs)
                        cmds.select(CUsF)
                        cmds.ConvertSelectionToFaces()
                        cmds.GrowPolygonSelectionRegion()
                        cmds.ShrinkPolygonSelectionRegion()
                        cmds.ShrinkPolygonSelectionRegion()
                        nm = ee.split('_')[0]
                        cmds.delete(ee)
                        cmds.sets(n=nm + '_new')
                        cmds.select(fullMesh)

            else:
                cmds.warning('Please Select Valid Source Face-Selection-Sets & a Target Mesh')
        else:
            cmds.warning('Please Select Valid Source Face-Selection-Sets & a Target Mesh')
    else:
        cmds.warning('Please Select atleast 1 Face-Selection-Set & 1 Target Mesh')
    return


def createCuOnTips(*args):
    cuList = cmds.ls(sl=1)
    cmds.makeIdentity(apply=1, t=1, r=1, s=1, n=0, pn=1)
    cmds.select(cl=1)
    ps = []
    for e in cuList:
        spans = cmds.getAttr(e + '.spans')
        spans = spans + 3
        p = cmds.xform(e + '.cv[' + str(spans) + ']', ws=1, t=1, q=1)
        ps.append(p)

    cmds.curve(d=3, p=ps)


def clumpTips(*args):
    cmds.softSelect(e=1, softSelectEnabled=1, softSelectFalloff=1)
    cuList = cmds.ls(sl=1)
    cmds.makeIdentity(apply=1, t=1, r=1, s=1, n=0, pn=1)
    cmds.select(cl=1)
    x = []
    y = []
    z = []
    for e in cuList:
        spans = cmds.getAttr(e + '.spans')
        spans = spans + 3
        p = cmds.xform(e + '.cv[' + str(spans) + ']', ws=1, t=1, q=1)
        x.append(p[0])
        y.append(p[1])
        z.append(p[2])

    avgXYZ = [sum(x) / len(x), sum(y) / len(y), sum(z) / len(z)]
    for e in cuList:
        spans = cmds.getAttr(e + '.spans')
        spans = spans + 3
        TFM = cmds.xform(e + '.cv[' + str(spans) + ']', ws=1, t=1, q=1)
        cmds.move(TFM[0], TFM[1], TFM[2], e + '.scalePivot', e + '.rotatePivot', absolute=1)
        newPos2 = [
         avgXYZ]
        newPos = (newPos2[0][0] - TFM[0], newPos2[0][1] - TFM[1], newPos2[0][2] - TFM[2])
        length = cmds.arclen(e)
        cmds.softSelect(softSelectDistance=length, softSelectCurve='0,1,2,1,0,2')
        spans = cmds.getAttr(e + '.spans')
        spans = spans + 3
        cmds.select(e + '.cv[' + str(spans) + ']')
        cmds.move(newPos[0], newPos[1], newPos[2], r=1)
        TM = cmds.xform(e + '.cv[0]', t=1, q=1)
        cmds.move(TM[0], TM[1], TM[2], e + '.scalePivot', e + '.rotatePivot', absolute=1)
        cmds.select(cl=1)

    cmds.softSelect(softSelectReset=1)


def EnableSoftEdit(*args):
    sel = cmds.ls('*', type=('mesh', 'nurbsCurve', 'nurbsSurface', 'joint'))
    for e in sel:
        try:
            cmds.setAttr(e + '.overrideEnabled', 1)
            cmds.setAttr(e + '.overrideDisplayType', 2)
        except:
            pass

    cmds.SelectHierarchy()
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='down')
    cus = cmds.ls(sl=1, fl=1)
    for e in cus:
        try:
            cmds.setAttr(e + '.overrideEnabled', 1)
            cmds.setAttr(e + '.overrideDisplayType', 0)
        except:
            pass

    cmds.softSelect(e=1, softSelectEnabled=1, ssf=3, softSelectColorCurve='0,.8,.8, 1,1, .2,.2,.2,0,1', softSelectDistance=5, softSelectCurve='0,1,2,1,0,2')
    mel.eval('manipMoveContext -e -mode 0 Move')
    mel.eval('manipRotateContext -e -useManipPivot 0 -useObjectPivot 1 Rotate')
    mel.eval('manipScaleContext -e -useManipPivot 0 -useObjectPivot 1 Scale')
    cmds.ScaleTool()
    cmds.RotateTool()
    cmds.select(cl=1)


def DisableSoftEdit(*args):
    sel = cmds.ls('*', type=('mesh', 'nurbsCurve', 'nurbsSurface', 'joint'))
    for e in sel:
        try:
            cmds.setAttr(e + '.overrideEnabled', 0)
            cmds.setAttr(e + '.overrideDisplayType', 0)
        except:
            pass

    cmds.softSelect(e=1, softSelectReset=1, softSelectEnabled=0)
    mel.eval('manipMoveContext -e -mode 2 Move')
    mel.eval('manipRotateContext -e -useManipPivot 0 -useObjectPivot 0 Rotate')
    cmds.RotateTool()
    mel.eval('manipScaleContext -e -useManipPivot 0 -useObjectPivot 0 Scale')
    cmds.ScaleTool()
    cmds.MoveTool()


def softSnap(tip, ssScaleField, *args):
    mel.eval('reflectionSetMode none;')
    cmds.softSelect(e=1, softSelectEnabled=1, softSelectFalloff=1)
    myList = cmds.ls(sl=1)
    cuList = myList[0:len(myList) - 1]
    mesh = myList[(len(myList) - 1)]
    cmds.makeIdentity(cuList, apply=1, t=1, r=1, s=1, n=0, pn=1)
    tip = cmds.checkBox(tip, q=1, v=0)
    ssScale = cmds.floatField(ssScaleField, q=1, v=1)
    if ssScale < 0:
        ssScale = 0
    if ssScale > 1:
        ssScale = 1
    cmds.select(cl=1)
    CPOM = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(mesh + '.worldMatrix', CPOM + '.inputMatrix')
    cmds.connectAttr(mesh + '.worldMesh', CPOM + '.inMesh')
    x = cuList
    window = cmds.window(t='Snap Progress')
    cmds.columnLayout()
    progressControl = cmds.progressBar(maxValue=len(x), width=300)
    cmds.showWindow(window)
    initialTime = time.time()
    p = 0
    for e in cuList:
        if tip == True:
            cmds.reverseCurve(e, ch=0, rpo=1)
        TFM = cmds.xform(e + '.cv[0]', ws=1, t=1, q=1)
        cmds.move(TFM[0], TFM[1], TFM[2], e + '.scalePivot', e + '.rotatePivot', absolute=1)
        cmds.setAttr(CPOM + '.inPositionX', TFM[0])
        cmds.setAttr(CPOM + '.inPositionY', TFM[1])
        cmds.setAttr(CPOM + '.inPositionZ', TFM[2])
        progressInc = cmds.progressBar(progressControl, edit=True, pr=p)
        p = p + 1
        newPos2 = cmds.getAttr(CPOM + '.p')
        newPos = (newPos2[0][0] - TFM[0], newPos2[0][1] - TFM[1], newPos2[0][2] - TFM[2])
        length = cmds.arclen(e)
        cmds.softSelect(softSelectDistance=length * ssScale, softSelectCurve='0,1,2,1,0,2')
        cmds.select(e + '.cv[0]')
        cmds.move(newPos[0], newPos[1], newPos[2], r=1)
        TM = cmds.xform(e + '.cv[0]', t=1, q=1)
        cmds.move(TM[0], TM[1], TM[2], e + '.scalePivot', e + '.rotatePivot', absolute=1)
        if tip == True:
            cmds.reverseCurve(e, ch=0, rpo=1)
            CP = cmds.xform(e + '.cv[0]', t=1, q=1, ws=1)
            cmds.xform(e + '.scalePivot', ws=1, t=CP)
            cmds.xform(e + '.rotatePivot', ws=1, t=CP)

    cmds.deleteUI(window)
    cmds.softSelect(softSelectReset=1)
    cmds.delete(CPOM)
    cmds.select(myList)


def growCVSel(*args):
    sel = cmds.ls(sl=1, fl=1)
    newCVs = []
    for e in sel:
        sl = e.split('[')[1]
        sl = int(sl.split(']')[0])
        new1 = sl + 1
        new2 = sl - 1
        if sl < 0:
            new2 = sl
        newCVnos = (
         sl, new1, new2)
        for n in newCVnos:
            c = e.split('.')[0]
            cv = c + '.cv[' + str(n) + ']'
            newCVs.append(cv)

    cmds.select(newCVs)


def createHairStrips(*args):
    sel = cmds.ls(sl=1)
    Cus = sel[0:len(sel) - 1]
    meshh = [sel[(len(sel) - 1)]]
    meshShape = cmds.listRelatives(meshh, s=1)[0]
    clsPntNode = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(meshShape + '.worldMatrix', clsPntNode + '.inputMatrix')
    cmds.connectAttr(meshShape + '.worldMesh', clsPntNode + '.inMesh')
    grps = []
    for e in Cus:
        posT = cmds.pointOnCurve(e, pr=0, t=1)
        posP = cmds.pointOnCurve(e, pr=0, p=1)
        tan = om.MVector(posT).normal()
        endPos = cmds.xform(e + '.cv[0]', query=True, worldSpace=True, translation=True)
        cmds.setAttr(clsPntNode + '.ip', endPos[0], endPos[1], endPos[2], type='double3')
        posN = cmds.getAttr(clsPntNode + '.n')[0]
        nor = om.MVector(posN).normal()
        biNor = tan ^ nor
        y = [
         tan.x, tan.y, tan.z, 0.0, nor.x, nor.y, nor.z, 0.0, biNor.x, biNor.y, biNor.z, 0.0, 0.0, 0.0, 0.0, 1.0]
        cmds.polyCube()
        cmds.xform(m=y)
        ro = cmds.xform(q=1, ro=1)
        cmds.delete()
        mel.eval('curve -d 3 -p 0 0 -1 -p 0 0 -0.333333 -p 0 0 0.333333 -p 0 0 1 -k 0 -k 0 -k 0 -k 1 -k 1 -k 1')
        baseCU = cmds.ls(sl=1)
        cmds.rebuildCurve(baseCU, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=5, d=3, tol=0.01)
        cmds.xform(baseCU, t=posP, ro=ro, s=(0.4, 0.4, 0.4), ws=1)
        cmds.select(baseCU)
        cmds.nonLinear(type='bend', lowBound=-1, highBound=1, curvature=0)
        bnd = cmds.ls(sl=1)
        cmds.rotate(90, 0, 90, os=1, r=1)
        cmds.hide(bnd)
        strp = cmds.extrude(baseCU, e, rn=1, po=1, et=2, ucp=0, fpt=1, upn=1, rotation=0, scale=1, rsp=1, n='hairStripMesh_01')
        strip = cmds.ls(sl=1)
        extrud = strp[1]
        polyTesselate = cmds.listConnections(extrud)[0]
        cmds.setAttr(polyTesselate + '.polygonType', 1)
        cmds.setAttr(polyTesselate + '.format', 2)
        cmds.hide(baseCU)
        grp = cmds.group(strip, baseCU, bnd, n='hairStrip_grp_01')
        grps.append(grp)

    cmds.group(grps, n='hairStrips_01')


def selCards(*args):
    global UCount
    global VCount
    global baseCUs
    global bends
    global cards
    global rotts
    global scls
    sel = cmds.ls(sl=1)
    baseCUs = []
    UCount = []
    VCount = []
    cards = []
    bends = []
    rotts = []
    scls = []
    for e in sel:
        try:
            shp = pm.listRelatives(e)
            tess = pm.listConnections(shp)[1]
            typ = pm.objectType(tess)
            if typ == 'nurbsTessellate':
                u = tess + '.uNumber'
                UCount.append(u)
                v = tess + '.vNumber'
                cards.append(e)
                VCount.append(v)
            extrd = pm.listConnections(tess)[1]
            typ = pm.objectType(extrd)
            if typ == 'extrude':
                scl = extrd + '.scale'
                rott = extrd + '.rotation'
                rotts.append(rott)
                scls.append(scl)
            base = pm.listConnections(extrd)[1]
            baseCU = pm.listConnections(base)[1]
            baseCUshp = pm.listRelatives(baseCU)
            bendd = pm.listConnections(baseCUshp)[0]
            bendC = bendd + '.curvature'
            bends.append(bendC)
            shp = pm.listRelatives(baseCU)[0]
            typ = pm.objectType(shp)
            if typ == 'nurbsCurve':
                baseCUScale = baseCU + '.scaleZ'
                baseCUs.append(baseCUScale)
        except:
            pass


def FKIK(*args):
    cu = cmds.ls(sl=1)
    cmds.select(cl=1)
    jnts = 10
    crSplIK = 0
    jntRad = 0.001
    for e in cu:
        shp = cmds.listRelatives(e, s=1)[0]
        uParam = cmds.getAttr(shp + '.minMaxValue')[0][1] - 0.0001
        incr = uParam / jnts
        v = 0
        ts = []
        for f in range(jnts + 1):
            t = cmds.pointOnCurve(e, p=1, pr=v)
            ts.append(t)
            v += incr

        cnt = 0
        allJnts = []
        for g in ts:
            jnt = cmds.joint(p=g)
            allJnts.append(jnt)
            cmds.setAttr(jnt + '.radius', jntRad)
            if cnt == 0:
                Fjnt = jnt
            if cnt == jnts:
                Ljnt = jnt
            cnt += 1

        if crSplIK == 1:
            cmds.select(Fjnt, Ljnt, e)
            cmds.ikHandle(sol='ikSplineSolver', ccv=0)
        cmds.skinCluster(allJnts, e, tsb=1)
        cmds.select(cl=1)


def delFK(*args):
    sel = cmds.ls(sl=1)
    try:
        for cu in sel:
            cmds.select(cu)
            cmds.setAttr(cu + '.tx', lock=0)
            cmds.setAttr(cu + '.ty', lock=0)
            cmds.setAttr(cu + '.tz', lock=0)
            cmds.setAttr(cu + '.rx', lock=0)
            cmds.setAttr(cu + '.ry', lock=0)
            cmds.setAttr(cu + '.rz', lock=0)
            cmds.setAttr(cu + '.sx', lock=0)
            cmds.setAttr(cu + '.sy', lock=0)
            cmds.setAttr(cu + '.sz', lock=0)
            cmds.pickWalk(d='down')
            Shp = cmds.ls(sl=1)
            list = cmds.listConnections(Shp)
            skin = []
            for e in list:
                type = cmds.objectType(e)
                if type == 'skinCluster':
                    skin.append(e)

            list = cmds.listConnections(skin[0])
            jnts = []
            for e in list:
                type = cmds.objectType(e)
                if type == 'joint':
                    jnts.append(e)

            cmds.select(cu)
            cmds.DeleteHistory()
            cmds.delete(jnts)

        cmds.select(sel)
    except:
        pass


def createCurl(*args):
    sels = cmds.ls(sl=1)
    cmds.duplicate()
    try:
        cmds.parent(w=1)
    except:
        pass

    sels = cmds.ls(sl=1)
    for e in sels:
        gate = []
        try:
            gate = cmds.getAttr(e + '.HS')
        except:
            pass

        if len(gate) > 0:
            cmds.warning('Curl curve selected, please select a regular curve')
        if len(gate) == 0:
            cmds.select(e)
            mel.eval('makeCurvesDynamic 2 { "1", "1", "1", "1", "0"};')
            sel = cmds.ls(sl=1)
            neu = cmds.listConnections(sel)[1]
            cmds.delete(neu)
            cmds.pickWalk(d='up')
            Hsys = cmds.ls(sl=1)
            cmds.select(sel)
            cmds.setAttr(sel[0] + '.simulationMethod', 1)
            cmds.setAttr(sel[0] + '.subSegments', 3)
            mel.eval('assignBrushToHairSystem')
            cmds.pickWalk(d='up')
            cmds.rename(e + 'brsh')
            pfx = cmds.ls(sl=1)
            test = mel.eval('doPaintEffectsToCurve( 1)')
            cmds.select(sel)
            mel.eval('convertHairSelection "follicles";')
            Foll = cmds.ls(sl=1)
            cmds.pickWalk(d='up')
            HsysFoll = cmds.ls(sl=1)
            cmds.select(Foll)
            mel.eval('convertHairSelection "current"')
            cmds.pickWalk(d='up')
            add = cmds.ls(sl=1)
            cmds.select(pfx[0] + 'ShapeMainCurves')
            cmds.pickWalk(d='down')
            cmds.parent(w=1)
            crv = cmds.ls(sl=1)
            cmds.delete(pfx[0] + 'ShapeCurves')
            RP = json.dumps(sel)
            cmds.addAttr(crv[0], ln='HS', dt='string')
            cmds.setAttr(crv[0] + '.HS', l=0)
            cmds.setAttr(crv[0] + '.HS', RP, type='string', l=1)
            cmds.select(Hsys, pfx, HsysFoll, add)
            Grp = cmds.group(n=e + 'miscSet')
            cmds.hide(Grp)
            cmds.select(crv, Grp)
            Grp2 = cmds.group(n='curlyGuide_01')
            cmds.select(Hsys)
            cmds.setAttr(sel[0] + '.clumpWidth', 1)
            cmds.setAttr(sel[0] + '.clumpCurl[0].clumpCurl_Position', 0)
            rnd = rand.uniform(0, 1)
            cmds.setAttr(sel[0] + '.clumpCurl[0].clumpCurl_FloatValue', rnd)
            cmds.select(crv)
            baseCol = (0, 1, 0)
            for e in crv:
                cmds.setAttr(e + '.overrideEnabled', 1)
                cmds.setAttr(e + '.overrideRGBColors', 1)
                cmds.setAttr(e + '.overrideColorRGB', baseCol[0], baseCol[1], baseCol[2])


def selectHS(*args):
    sel = cmds.ls(sl=1)
    if len(sel) == 0 or len(sel) > 1:
        cmds.warning('Please select one Curl Curve')
    if len(sel) == 1:
        selShp = cmds.listRelatives(sel[0])
        type = cmds.objectType(selShp[0])
        if type != 'nurbsCurve':
            cmds.warning('Please select a Curl Curve')
        if type == 'nurbsCurve':
            try:
                RPattr = cmds.getAttr(sel[0] + '.HS')
                RP = json.loads(RPattr)
            except:
                cmds.warning('Invalid Curl Curve selected')


def freezeCurve(*args):
    crv = cmds.ls(sl=1)
    if len(crv) == 0:
        cmds.warning('Please select one Curl Curve')
    if len(crv) > 0:
        try:
            for e in crv:
                RPattr = cmds.getAttr(e + '.HS')
                cmds.setAttr(e + '.HS', l=0)
                cmds.deleteAttr(e + '.HS')
                cmds.select(e)
                cmds.pickWalk(d='up')
                grp = cmds.ls(sl=1)
                cmds.select(e)
                cmds.parent(w=1)
                cmds.delete(grp)
                cmds.warning('Curl Curve freeze done')

        except:
            cmds.warning('Invalid Curl Curve selected')

    cmds.select(cl=1)


def createSelSet(*args):
    sel = cmds.ls(sl=1, fl=1)
    cmds.sets(sel, n='selSet_01')


def snapWholeCU(snapOffsetField, *args):
    snapPush = cmds.floatField(snapOffsetField, q=1, v=1)
    selected = cmds.ls(sl=1)
    baseMesh = selected[(-1)]
    cmds.select(baseMesh)
    dupMesh = cmds.duplicate()
    meshShape = cmds.listRelatives(dupMesh, s=1)
    cmds.SmoothPolygon()
    cmds.select(dupMesh)
    cmds.textureDeformer(en=1, s=1, o=snapPush, vs=(1, 1, 1), vo=(0, 0, 0), vsp='Object', d='Normal', ps='Local', ex='')
    cmds.delete(dupMesh, ch=1)
    curveList = selected[0:len(selected) - 1]
    x = curveList
    window = cmds.window(t='Snap Progress')
    cmds.columnLayout()
    progressControl = cmds.progressBar(maxValue=len(x), width=300)
    cmds.showWindow(window)
    initialTime = time.time()
    p = 0
    clsPntNode = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(meshShape[0] + '.worldMatrix', clsPntNode + '.inputMatrix')
    cmds.connectAttr(meshShape[0] + '.worldMesh', clsPntNode + '.inMesh')
    for i in curveList:
        progressInc = cmds.progressBar(progressControl, edit=True, pr=p)
        p = p + 1
        spans = cmds.getAttr(i + '.spans')
        spans = spans + 3
        CVs = []
        for cvv in range(spans):
            cv = i + '.cv[%d]' % cvv
            CVs.append(cv)

        for e in CVs:
            endPos = cmds.xform(e, query=True, worldSpace=True, translation=True)
            cmds.setAttr(clsPntNode + '.ip', endPos[0], endPos[1], endPos[2], type='double3')
            pos = cmds.getAttr(clsPntNode + '.p')[0]
            cmds.xform(e, t=pos, ws=1, a=1)

    cmds.delete(dupMesh, clsPntNode)
    cmds.deleteUI(window)
    cmds.select(curveList)


def RemovePenetration(pushOffset2Field, *args):
    global baseMesh
    global curveList
    global meshShape
    selected = cmds.ls(selection=True)
    baseMesh = selected[(-1)]
    meshShape = cmds.listRelatives(baseMesh, shapes=True)
    curveList = selected[0:len(selected) - 1]
    pushy = cmds.floatField(pushOffset2Field, q=1, v=1)
    RemovePene(pushy)


def RemovePene(push, *args):
    cmds.select(baseMesh)
    meshName = cmds.duplicate()
    meshShape = cmds.listRelatives(meshName, s=1)
    cmds.SmoothPolygon()
    cmds.select(meshName)
    mesh2 = cmds.duplicate()
    cmds.textureDeformer(en=1, s=1, o=push, vs=(1, 1, 1), vo=(0, 0, 0), vsp='Object', d='Normal', ps='Local', ex='')
    cmds.delete(mesh2, ch=1)
    clsPntNode = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(meshShape[0] + '.worldMatrix', clsPntNode + '.inputMatrix')
    cmds.connectAttr(meshShape[0] + '.worldMesh', clsPntNode + '.inMesh')
    mesh2Shape = cmds.listRelatives(mesh2, shapes=True)
    clsPntNode2 = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(mesh2Shape[0] + '.worldMatrix', clsPntNode2 + '.inputMatrix')
    cmds.connectAttr(mesh2Shape[0] + '.worldMesh', clsPntNode2 + '.inMesh')
    x = curveList
    window = cmds.window(t='Progress')
    cmds.columnLayout()
    progressControl = cmds.progressBar(maxValue=len(x), width=300)
    cmds.showWindow(window)
    initialTime = time.time()
    p = 0
    for i in curveList:
        progressInc = cmds.progressBar(progressControl, edit=True, pr=p)
        p = p + 1
        spans = cmds.getAttr(i + '.spans')
        spans = spans + 3
        CVs = []
        for cvv in range(spans):
            cv = i + '.cv[%d]' % cvv
            CVs.append(cv)

        for e in CVs:
            endPos = cmds.xform(e, query=True, worldSpace=True, translation=True)
            cmds.setAttr(clsPntNode + '.ip', endPos[0], endPos[1], endPos[2], type='double3')
            newPos = cmds.getAttr(clsPntNode + '.p')
            newPos = [ val for sublist in newPos for val in sublist ]
            cmds.setAttr(clsPntNode2 + '.ip', endPos[0], endPos[1], endPos[2], type='double3')
            NPos = cmds.getAttr(clsPntNode2 + '.p')
            NPos = [ val for sublist in NPos for val in sublist ]
            t1x = endPos[0] - newPos[0]
            t1y = endPos[1] - newPos[1]
            t1z = endPos[2] - newPos[2]
            t1 = [t1x, t1y, t1z]
            Pnormal = om.MVector(t1).normal()
            t2x = NPos[0] - newPos[0]
            t2y = NPos[1] - newPos[1]
            t2z = NPos[2] - newPos[2]
            t2 = [t2x, t2y, t2z]
            Fnormal = om.MVector(t2).normal()
            dot = Fnormal * Pnormal
            if dot < 0:
                cmds.xform(e, worldSpace=True, translation=NPos)

    cmds.delete(mesh2, meshName, clsPntNode)
    cmds.deleteUI(window)
    cmds.select(curveList)


def autoMultiEdge2(*args):
    sel = cmds.ls(sl=1)
    cmds.SelectEdgeRingSp()
    edges = cmds.ls(sl=1, fl=1)
    cus = []
    for e in edges:
        cmds.select(e)
        cmds.SelectEdgeLoopSp()
        cu = cmds.polyToCurve(form=2, degree=3, n='edgCu_01')[0]
        cuShp = cmds.listRelatives(cu, s=1)[0]
        frm = cmds.getAttr(cuShp + '.f')
        cus.append(cu)
        if frm == 2:
            cmds.delete(cu)
            cus.remove(cu)

    cmds.group(cus, n='edgeCurves_01')


def autoMultiEdge(genTube, *args):
    genTube = cmds.checkBox(genTube, q=1, v=0)
    sell = cmds.ls(sl=1)
    if len(sell) > 1:
        cmds.displaySmoothness(divisionsU=0, divisionsV=0, pointsWire=4, pointsShaded=1, polygonObject=1)
        scalp = sell[(len(sell) - 1)]
        sel = sell[0:len(sell) - 1]
        CPOM = cmds.createNode('closestPointOnMesh')
        cmds.connectAttr(scalp + '.outMesh', CPOM + '.inMesh')
        sclp = 1
        for e in sel:
            svtx = cmds.polyEvaluate(e, v=1) / 2
            cmds.select(e + '.vtx[' + str(svtx) + ']')
            cmds.ConvertSelectionToEdges()
            eds = cmds.ls(sl=1, fl=1)
            lns = []
            for f in eds:
                cmds.select(f)
                cmds.SelectEdgeLoopSp()
                pc = (cmds.polyToCurve(form=2, degree=1, n='edgeCu_01')[0], f)
                pcShp = cmds.listRelatives(pc[0], s=1)[0]
                frm = cmds.getAttr(pcShp + '.f')
                if frm == 2:
                    cmds.select(pc[0] + '.cv[*]')
                    cvp = cmds.ls(sl=1, fl=1)
                    cvps = []
                    for cv in cvp:
                        p = cmds.pointPosition(cv)
                        cvps.append(p)

                if frm != 2:
                    lns.append(pc)
                cmds.delete(pc[0])

            cmds.select(lns[0][1])
            cmds.SelectEdgeRingSp()
            cues = cmds.ls(sl=1, fl=1)
            order = []
            for xx in cvps:
                for yy in cues:
                    cmds.select(yy)
                    cmds.ConvertSelectionToVertices()
                    vtx = cmds.ls(sl=1, fl=1)
                    for vt in vtx:
                        pp = cmds.pointPosition(vt)
                        if pp == xx:
                            order.append(yy)

            cus = []
            for g in order:
                cmds.select(g)
                cmds.SelectEdgeLoopSp()
                cu = cmds.polyToCurve(form=2, degree=3, n='edgCu_01')[0]
                cus.append(cu)
                if sclp == 1:
                    lastCV = cmds.getAttr(cu + '.spans') + 2
                    cvs = (cu + '.cv[0]', cu + '.cv[' + str(lastCV) + ']')
                    dsts = []
                    for h in cvs:
                        p = cmds.pointPosition(h)
                        cmds.setAttr(CPOM + '.inPositionX', p[0])
                        cmds.setAttr(CPOM + '.inPositionY', p[1])
                        cmds.setAttr(CPOM + '.inPositionZ', p[2])
                        ps = cmds.getAttr(CPOM + '.p')[0]
                        dist = sqrt(pow(p[0] - ps[0], 2) + pow(p[1] - ps[1], 2) + pow(p[2] - ps[2], 2))
                        dsts.append(dist)

                    if dsts[0] > dsts[1]:
                        cmds.reverseCurve(cu, ch=0, rpo=1)
                    else:
                        continue

            grp = cmds.group(cus, n='cus_grp_01')
            if genTube == 1:
                cmds.loft(ch=1, u=1, c=1, ar=1, d=3, ss=1, rn=0, po=0, rsn=1, n='nurbsTube_01')
                cmds.select(grp)

        print 'done'
        cmds.scriptEditorInfo(clearHistory=1)
    else:
        cmds.warning('Please Select atleast Poly Tube & Scalp')


def extractMultiEdgeLoops(*args):
    sel = cmds.ls(sl=1, fl=1)
    cus = []
    for e in sel:
        cmds.select(e)
        cmds.SelectEdgeLoopSp()
        cmds.polyToCurve(form=2, degree=3)
        cu = cmds.ls(sl=1)[0]
        cus.append(cu)

    cmds.group(cus, n='guide_cus')
    cmds.DeleteHistory()


def nameSpaceRemover(*args):
    sel = cmds.ls()
    for e in sel:
        try:
            n = e.split(':')
            cmds.rename(e, n[1])
        except:
            pass


def applyFFD(*args):
    cmds.lattice(divisions=(3, 3, 3), objectCentered=1, ldv=(2, 2, 2))


def transferSkinWeights(*args):
    sel = cmds.ls(sl=1)
    Cus = sel[0:len(sel) - 1]
    msh = [sel[(len(sel) - 1)]]
    cmds.select(msh)
    cmds.pickWalk(d='down')
    mshShp = cmds.ls(sl=1)
    list = cmds.listConnections(mshShp)
    skin = []
    for e in list:
        type = cmds.objectType(e)
        if type == 'skinCluster':
            skin.append(e)

    list = cmds.listConnections(skin[0])
    jnts = []
    for e in list:
        type = cmds.objectType(e)
        if type == 'joint':
            jnts.append(e)

    for e in Cus:
        try:
            cmds.skinCluster(jnts, e, tsb=1)
            cmds.select(msh, e)
            cmds.copySkinWeights(noMirror=1, surfaceAssociation='closestPoint', influenceAssociation='closestJoint')
        except:
            pass

    cmds.select(Cus)


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


def loadBlends(*args):
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


def graphBlendCUs(*args):
    try:
        sel = cmds.ls(sl=1)
        cmds.SelectHierarchy()
        for x in range(10):
            cmds.pickWalk(d='down')

        cmds.pickWalk(d='up')
        Crvs = pm.ls(sl=1)
        cmds.select(sel)
        indx = []
        for e in Crvs:
            for f in CrvsIndex:
                if e == f[0]:
                    indx.append(f[1])

        vall = 0
        for e, f in zip(Crvs, indx):
            pm.select(e + '.cv[*]')
            cvNo = cmds.ls(sl=1, fl=1)
            cvNo = len(cvNo)
            incr = 1.0 / (cvNo - 1)
            for i in range(cvNo):
                GraphVal = cmds.gradientControlNoAttr('falloffCurv', q=True, valueAtPoint=vall)
                if GraphVal > 1:
                    GraphVal = 1
                if GraphVal < 0:
                    GraphVal = 0
                GraphVal2 = 1 - GraphVal
                cmds.setAttr(bss[0] + '.inputTarget[' + str(f) + '].inputTargetGroup[0].targetWeights' + '[' + str(i) + ']', GraphVal2)
                cmds.setAttr(bss[0] + '.inputTarget[' + str(f) + '].inputTargetGroup[1].targetWeights' + '[' + str(i) + ']', GraphVal)
                vall += incr

            vall = 0
            pm.select(sel)

    except:
        cmds.warning('Please 1st load or create Blends')


def export(*args):
    sel = cmds.ls(sl=1)
    allFaces = []
    for e in sel:
        lst = cmds.select(e)
        fcs = cmds.ls(sl=1, fl=1)
        faces = []
        for f in fcs:
            token1 = f.split('[')[1]
            token2 = token1.split(']')[0]
            faces.append(token2)

        faces2 = (
         faces, e)
        allFaces.append(faces2)

    cmds.select(sel, ne=1)
    allFaces = json.dumps(allFaces)
    savePath = cmds.fileDialog2(fileFilter='*.sel', dialogStyle=2)
    f = open(savePath[0], 'w+')
    f.write(allFaces)
    f.close()


def emport(*args):
    loadPath = cmds.fileDialog()
    load = open(loadPath, 'r')
    allFaces = load.read()
    allFaces = json.loads(allFaces)
    sel = cmds.ls(sl=1)
    for e in allFaces:
        fcs = []
        for f in e[0]:
            ff = sel[0] + '.f[' + f + ']'
            fcs.append(ff)

        cmds.sets(fcs, name=e[1])


def rivetCurves(*args):
    sel = cmds.ls(sl=1)
    CusA = sel[0:len(sel) - 1]
    meshh = [sel[(len(sel) - 1)]]
    cmds.select(CusA)
    cmds.SelectHierarchy()
    for r in range(4):
        cmds.pickWalk(d='down')

    cmds.pickWalk(d='up')
    CusAs = cmds.ls(sl=1, l=1)

    def rivet():
        cuMode = 1
        snap = 1
        meshhShp = cmds.listRelatives(meshh, c=1)
        CPOM = cmds.createNode('closestPointOnMesh')
        cmds.connectAttr(meshhShp[0] + '.worldMatrix', CPOM + '.inputMatrix')
        cmds.connectAttr(meshhShp[0] + '.worldMesh', CPOM + '.inMesh')
        folls = []
        for e in CusAs:
            cmds.xform(e, cp=1, ws=1)
            cmds.makeIdentity(e, apply=1, t=1, r=1, s=1, n=0, pn=1)
            CP = cmds.xform(e + '.scalePivot', q=1, ws=1, t=1)
            cmds.setAttr(CPOM + '.ip', CP[0], CP[1], CP[2], type='double3')
            pos = cmds.getAttr(CPOM + '.p')[0]
            if cuMode == 1:
                CP = cmds.xform(e + '.cv[0]', t=1, q=1, ws=1)
                cmds.xform(e + '.scalePivot', ws=1, t=CP)
                cmds.xform(e + '.rotatePivot', ws=1, t=CP)
                cmds.setAttr(CPOM + '.ip', CP[0], CP[1], CP[2], type='double3')
            if snap == 1:
                cmds.makeIdentity(e, apply=1, t=1, r=1, s=1, n=0, pn=1)
                CP = cmds.xform(e + '.scalePivot', q=1, ws=1, t=1)
                cmds.setAttr(CPOM + '.ip', CP[0], CP[1], CP[2], type='double3')
                pos = cmds.getAttr(CPOM + '.p')[0]
                op = (-CP[0], -CP[1], -CP[2])
                cmds.xform(e, t=op, r=1, os=1)
                cmds.makeIdentity(e, apply=1, t=1, r=1, s=1, n=0, pn=1)
                cmds.xform(e, t=pos, r=1, os=1)
                cmds.makeIdentity(e, apply=1, t=1, r=1, s=1, n=0, pn=1)
            Upos = cmds.getAttr(CPOM + '.u')
            Vpos = cmds.getAttr(CPOM + '.v')
            cmds.createNode('follicle')
            FollmainShp = cmds.ls(sl=1)
            mel.eval('pickWalk -d up')
            FollmainT = cmds.ls(sl=1)[0]
            folls.append(FollmainT)
            cmds.connectAttr(meshhShp[0] + '.outMesh', FollmainShp[0] + '.inputMesh')
            cmds.connectAttr(meshhShp[0] + '.worldMatrix[0]', FollmainShp[0] + '.inputWorldMatrix')
            cmds.connectAttr(FollmainShp[0] + '.outRotate', FollmainT + '.rotate')
            cmds.connectAttr(FollmainShp[0] + '.outTranslate', FollmainT + '.translate')
            cmds.setAttr(FollmainShp[0] + '.parameterU', Upos)
            cmds.setAttr(FollmainShp[0] + '.parameterV', Vpos)
            cmds.select(FollmainT, e)
            mel.eval('doCreateParentConstraintArgList 1 { "1","0","0","0","0","0","0","0","1","","1" }')

        folls = cmds.group(folls, n='follicles_01')
        cmds.delete(CPOM)

    rivet()


def listTexturePaths(*args):
    sel = cmds.ls(sl=1)
    for e in sel:
        try:
            path = cmds.getAttr(e + '.fileTextureName')
        except:
            pass


def pivotToRoot(*args):
    cmds.SelectHierarchy()
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='down')
    cmds.pickWalk(d='up')
    sel = cmds.ls(sl=1)
    for e in sel:
        CP = cmds.xform(e + '.cv[0]', t=1, q=1, ws=1)
        cmds.xform(e + '.scalePivot', ws=1, t=CP)
        cmds.xform(e + '.rotatePivot', ws=1, t=CP)


def curvesColorOverride(baseColField, *args):
    baseCol = cmds.colorSliderGrp(baseColField, q=1, rgb=1)
    print baseCol
    cmds.pickWalk(d='down')
    sel = cmds.ls(sl=1)
    for e in sel:
        cmds.setAttr(e + '.overrideEnabled', 1)
        cmds.setAttr(e + '.overrideRGBColors', 1)
        cmds.setAttr(e + '.overrideColorRGB', baseCol[0], baseCol[1], baseCol[2])


def curvesColorScalp(*args):
    try:
        cmds.pickWalk(d='down')
        sel = cmds.ls(sl=1)
        scalp = sel[(len(sel) - 1)]
        lm = cmds.listConnections(scalp)[0]
        lam = cmds.listConnections(lm, t='lambert')[0]
        tex = cmds.listConnections(lam)
        tex = tex[(len(tex) - 1)]
        CPOM = cmds.createNode('closestPointOnMesh')
        cmds.connectAttr(scalp + '.worldMatrix', CPOM + '.inputMatrix')
        cmds.connectAttr(scalp + '.worldMesh', CPOM + '.inMesh')
        cus = sel[0:len(sel) - 1]
        for e in cus:
            p = cmds.xform(e + '.cv[0]', ws=1, t=1, q=1)
            cmds.setAttr(CPOM + '.inPositionX', p[0])
            cmds.setAttr(CPOM + '.inPositionY', p[1])
            cmds.setAttr(CPOM + '.inPositionZ', p[2])
            u = cmds.getAttr(CPOM + '.u')
            v = cmds.getAttr(CPOM + '.v')
            cap = cmds.colorAtPoint(tex, u=u, v=v, o='RGB')
            cmds.setAttr(e + '.overrideEnabled', 1)
            cmds.setAttr(e + '.overrideRGBColors', 1)
            cmds.setAttr(e + '.overrideColorRGB', cap[0] - 0.3, cap[1] - 0.3, cap[2] - 0.3)

        cmds.delete(CPOM)
    except:
        pass


def tubesToVolCurves(DensityField, flip, centrCU, *args):

    def VolGuides():
        HSS = []
        for each in Tubes:
            each = cmds.duplicate(each)[0]
            dcu = cmds.duplicateCurve(each + '.v[0]', ch=0, rn=0, local=0)
            ctype = cmds.getAttr(dcu[0] + '.form')
            if ctype == 2 or ctype == 1:
                cmds.reverseSurface(each, d=3, ch=0, rpo=1)
            cmds.delete(dcu)
            spnU = cmds.getAttr(each + '.spansU')
            spnV = cmds.getAttr(each + '.spansV')
            cmds.rebuildSurface(each, rpo=1, rt=0, end=1, kr=0, kcp=0, kc=0, su=spnU, du=3, sv=spnV * 3, dv=3, tol=0.01, fr=0, dir=2)
            sU = cmds.getAttr(each + '.spansU')
            sV = cmds.getAttr(each + '.spansV')
            K = sU + 3
            L = sV - 1
            DiscVtxall = []
            sells = []
            Dscs = []
            while K >= 0:
                cmds.select(each + '.cv[%d]' % K + '[0:%d]' % L)
                NLoopcvs = cmds.ls(sl=1, fl=1)
                NgonPts = []
                for i in NLoopcvs:
                    Ptp = cmds.pointPosition(i)
                    NgonPts.append(Ptp)

                cmds.polyCreateFacet(tx=2, p=NgonPts, n='LoopFace')
                sell = cmds.ls(sl=1)
                cmds.polySmooth(dv=2)
                if centrCU == 0:
                    cmds.polyPlane(w=1, h=1, sx=Density, sy=Density, n='disc')
                if centrCU == 1:
                    cmds.polyPlane(w=1, h=1, sx=2, sy=2, n='disc')
                Dsc = cmds.ls(sl=1)
                cmds.transferAttributes(sell, Dsc, pos=1, nml=0, uvs=0, col=0, spa=3, sm=3, fuv=0, clb=1)
                cmds.ConvertSelectionToVertices()
                DiscVtx = cmds.ls(sl=1, fl=1)
                cmds.hide(Dsc)
                cmds.hide(sell)
                cmds.select(cl=1)
                K = K - 1
                DiscVtxall.append(DiscVtx)
                Dscs.append(Dsc)
                sells.append(sell)
                Dscss = [ x[0] for x in Dscs ]
                sellss = [ x[0] for x in sells ]

            sortXYZ = []
            length = len(DiscVtxall[0])
            for x in range(length):
                sortXYZ.append([])
                for y in range(len(DiscVtxall)):
                    sortXYZ[x].append(DiscVtxall[y][x])

            cuG = []
            cc = 0
            for j in sortXYZ:
                ppp = []
                for z in j:
                    kk = currPos = cmds.xform(z, q=True, ws=True, t=True)
                    ppp.append(kk)

                if centrCU == 1:
                    if cc == 4:
                        my_curve = pm.curve(p=ppp, n='Centre_CU_01')
                if centrCU == 0:
                    my_curve = pm.curve(p=ppp, n='Centre_CU_01')
                    cuG.append(my_curve)
                cc = cc + 1

            if centrCU == 0:
                pm.group(cuG, n='Clump_CUs_01')
            cmds.group(Dscss, n='Dscs_01')
            cmds.group(sellss, n='sells_01')
            cmds.delete(each)

        cmds.select('sells*', 'Dscs*')
        AllData = cmds.group(n='AllData')
        cmds.delete(AllData)
        if flip == 1:
            for cr in cuG:
                pm.reverseCurve(cr, ch=0, rpo=1)

        pm.select(cuG)
        cmds.SelectCurveCVsFirst()

    Density = cmds.intField(DensityField, q=1, v=1)
    flip = cmds.checkBox(flip, q=1, v=0)
    centrCU = cmds.checkBox(centrCU, q=1, v=1)
    Tubes = cmds.ls(sl=1)
    meshshape = cmds.listRelatives(Tubes)
    MeshType = cmds.objectType(meshshape[0])
    if MeshType == 'nurbsSurface':
        VolGuides()


def rebuildCrvs(segsField, *args):
    sel = cmds.ls(sl=1)
    segs = cmds.intField(segsField, q=1, v=1)
    for e in sel:
        cmds.rebuildCurve(e, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=segs, d=3, tol=0.01)

    cmds.select(sel)


def smoothCVs(smooField, *args):
    smoo = cmds.floatField(smooField, q=1, v=1)
    sel1 = cmds.ls(sl=1)
    cmds.SelectHierarchy()
    cmds.pickWalk(d='up')
    sel = cmds.ls(sl=1)
    for e in sel:
        cvs = e.split('cv')
        if len(cvs) == 1:
            selshape = cmds.listRelatives(e)
            selType = cmds.objectType(selshape[0])
            if selType == 'nurbsCurve':
                cmds.select(e + '.cv[*]')
                cmds.smoothCurve(ch=1, rpo=1, s=smoo)
        if len(cvs) == 2:
            cmds.smoothCurve(e, ch=1, rpo=1, s=smoo)

    cmds.select(sel1)


def smooHairCUs(*args):
    cmds.SmoothHairCurves()


def nurbsLoft(*args):
    cmds.loft(ch=1, u=1, c=1, ar=1, d=3, ss=1, rn=0, po=0, rsn=1)


def reverseCUrv(*args):
    cmds.ReverseCurve()


def randomizeCULen(percField, *args):
    CUlist = cmds.ls(sl=1)
    perc = cmds.floatField(percField, q=1, v=1)
    perc = 1 - perc
    CUs = []
    rand.seed(0)
    for each in CUlist:
        pts = [
         0]
        cmds.rebuildCurve(each, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=1, kt=0, s=8, d=3, tol=0.01)
        spans = cmds.getAttr(each + '.spans')
        RandLen = rand.uniform(1.0, perc)
        iterr = spans
        div = 1.0 / iterr
        div2 = 1.0 / iterr
        while iterr > 0 and div < 1:
            pt = RandLen * div
            div = div + div2
            iterr = iterr - 1
            pts.append(pt)

        CPP = []
        for i in pts:
            CP = cmds.pointOnCurve(each, pr=i, p=1)
            CPP.append(CP)

        cmds.curve(p=CPP)
        CU = cmds.ls(sl=1)
        cmds.rebuildCurve(s=spans)
        CUs.append(CU)

    CUss = [ x[0] for x in CUs ]
    cmds.group(CUss, n='New_CUs')


def rebuildCrvsUnitBased(spacingField, *args):
    spacing = cmds.floatField(spacingField, q=1, v=1)
    Crvs = cmds.ls(sl=1)
    PLs = []
    for e in Crvs:
        crvLen = int(cmds.arclen(e) / spacing)
        cmds.rebuildCurve(e, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=crvLen, d=3, tol=0.01)
        cmds.select(Crvs)


def cuSelFilterON(*args):
    mel.eval('setObjectPickMask "Curve" true')
    mel.eval('setObjectPickMask "Surface" false')
    mel.eval('setObjectPickMask "Marker" false')
    mel.eval('setObjectPickMask "Joint" false')
    mel.eval('setObjectPickMask "Deformer" false')
    mel.eval('setObjectPickMask "Dynamic" false')
    mel.eval('setObjectPickMask "Rendering" false')
    mel.eval('setObjectPickMask "Other" false')


def cuSelFilterOFF(*args):
    mel.eval('setObjectPickMask "Surface" true')
    mel.eval('setObjectPickMask "Curve" false')
    mel.eval('setObjectPickMask "Marker" false')
    mel.eval('setObjectPickMask "Joint" false')
    mel.eval('setObjectPickMask "Deformer" false')
    mel.eval('setObjectPickMask "Dynamic" false')
    mel.eval('setObjectPickMask "Rendering" false')
    mel.eval('setObjectPickMask "Other" false')


def allSelFilterON(*args):
    mel.eval('setObjectPickMask "Surface" true')
    mel.eval('setObjectPickMask "Curve" true')
    mel.eval('setObjectPickMask "Marker" true')
    mel.eval('setObjectPickMask "Joint" true')
    mel.eval('setObjectPickMask "Deformer" true')
    mel.eval('setObjectPickMask "Dynamic" true')
    mel.eval('setObjectPickMask "Rendering" true')
    mel.eval('setObjectPickMask "Other" true')


def CVMode(*args):
    cmds.SelectToggleMode()


def selectFirstCV(*args):
    cmds.SelectHierarchy()
    sel = cmds.ls(sl=1, l=1, type='nurbsCurve')
    fcvs = []
    for e in sel:
        cv = e + '.cv[0]'
        fcvs.append(cv)

    cmds.select(fcvs)


def selectLastCV(*args):
    cmds.SelectHierarchy()
    sel = cmds.ls(sl=1, l=1, type='nurbsCurve')
    fcvs = []
    for e in sel:
        cv = e + '.cv[0]'
        fcvs.append(cv)

    cmds.select(fcvs)


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


def deleteHist(*args):
    cmds.DeleteHistory()


def freezeTrans(*args):
    cmds.makeIdentity(apply=1, t=1, r=1, s=1, n=0, pn=1)


def Tubes_to_twisted_curves(flipp, CountField, segsField, twistField, randuField, *args):
    flip = cmds.checkBox(flipp, q=1, v=1)
    Count = cmds.intField(CountField, q=1, v=1)
    segs = cmds.intField(segsField, q=1, v=1)
    twist = cmds.floatField(twistField, q=1, v=1)
    randu = cmds.floatField(randuField, q=1, v=1)
    Tubes = cmds.ls(sl=1)
    meshShape = cmds.listRelatives(Tubes)
    MeshType = cmds.objectType(meshShape[0])

    def Nurbs_twisted_curves():
        mesh = cmds.ls(sl=1)
        ScalpShape = cmds.listRelatives(mesh, s=1)[0]
        FollC = cmds.createNode('follicle')
        FollTransf = cmds.listRelatives(FollC, allParents=1)[0]
        cmds.connectAttr(ScalpShape + '.local', FollC + '.inputSurface')
        cmds.connectAttr(ScalpShape + '.worldMatrix[0]', FollC + '.inputWorldMatrix')
        cmds.connectAttr(FollC + '.outRotate', FollTransf + '.rotate')
        cmds.connectAttr(FollC + '.outTranslate', FollTransf + '.translate')
        twi = twist
        if twist < 0:
            twi = -twist
        segsMulti = abs(twist) + 1
        X = segs * segsMulti
        X = int(X)
        incU = 1.0 / X
        incV = 1.0 / X * twist
        incY = 1.0 / Count
        Uu = 0
        Vv = 0
        Vvv = 0
        Vvs = []
        cBB = []
        for i in range(Count):
            FolTranzAll = []
            Fst = 0
            for e in range(X + 1):
                randa = rand.uniform(-randu, randu)
                U = Uu
                if Fst == 0:
                    V = Vv
                if Fst > 0:
                    V = Vv + randa
                cmds.setAttr(FollC + '.parameterU', U)
                cmds.setAttr(FollC + '.parameterV', V)
                Uu = Uu + incU
                Vv = Vv + incV
                if Vv >= 1:
                    Vv = Vv - 1
                if Vv <= 0:
                    Vv = 1 + Vv
                Vvs.append(Vv)
                FollX = cmds.getAttr(FollTransf + '.translateX')
                FollY = cmds.getAttr(FollTransf + '.translateY')
                FollZ = cmds.getAttr(FollTransf + '.translateZ')
                FolTranz = (FollX, FollY, FollZ)
                FolTranzAll.append(FolTranz)
                Fst = Fst + 1

            cB = cmds.curve(p=FolTranzAll, d=3)
            cBB.append(cB)
            Uu = 0
            Vvv = Vvv + incY
            Vv = Vvv
            Vvs.append(Vvv)

        cmds.select(cBB)
        cmds.group(n='guides_01')
        cmds.delete(FollTransf)

    if MeshType == 'nurbsSurface':
        if flip == 1:
            cmds.reverseSurface(d=2)
        Nurbs_twisted_curves()
    if MeshType == 'mesh':
        cmds.warning('Please Select a Nurbs Tube')


def trim_Guides_Scalp(*args):
    ST = time.time()
    sel = cmds.ls(sl=1)
    mesh = sel[(-1)]
    FixRootCVs()
    CPOM = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(mesh + '.worldMatrix', CPOM + '.inputMatrix')
    cmds.connectAttr(mesh + '.worldMesh', CPOM + '.inMesh')
    cmds.select(cl=1)
    x = Crvs
    window = cmds.window(t='Progress')
    cmds.columnLayout()
    progressControl = cmds.progressBar(maxValue=len(x) * 4, width=300)
    cmds.showWindow(window)
    initialTime = time.time()
    p = 0
    uParams = []
    for e, f in zip(Crvs, peneCVsAll):
        progressInc = cmds.progressBar(progressControl, edit=True, pr=p)
        p = p + 1
        cmds.rebuildCurve(e, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=0, kt=0, s=1, d=3, tol=0.01)
        RootCV = cmds.ls(f)
        RootCVp = cmds.xform(RootCV, t=1, q=1, ws=1)
        CUShape = cmds.listRelatives(e, s=1)
        CPOC = cmds.createNode('nearestPointOnCurve')
        cmds.connectAttr(CUShape[0] + '.worldSpace', CPOC + '.inputCurve')
        cmds.setAttr(CPOC + '.inPosition', 1, 2, 3, type='double3')
        uParam2 = 0
        cnt = 0
        for x in range(100):
            cmds.setAttr(CPOM + '.inPositionX', RootCVp[0])
            cmds.setAttr(CPOM + '.inPositionY', RootCVp[1])
            cmds.setAttr(CPOM + '.inPositionZ', RootCVp[2])
            RootP1 = cmds.getAttr(CPOM + '.p')
            RootP1 = [ val for sublist in RootP1 for val in sublist ]
            cmds.setAttr(CPOC + '.inPositionX', RootP1[0])
            cmds.setAttr(CPOC + '.inPositionY', RootP1[1])
            cmds.setAttr(CPOC + '.inPositionZ', RootP1[2])
            RootCVp = cmds.getAttr(CPOC + '.position')[0]
            uParam = cmds.getAttr(CPOC + '.parameter')
            cnt += 1
            uParamStr = str(uParam)
            uParamStr = uParamStr[0:5]
            uParam = float(uParamStr)
            if uParam == uParam2:
                break
            uParam2 = uParam

        uParam = 1 - uParam
        uParams.append(uParam)
        cmds.delete(CPOC)

    for e in Crvs:
        progressInc = cmds.progressBar(progressControl, edit=True, pr=p)
        p = p + 1
        cmds.reverseCurve(e, ch=0)

    for e, f in zip(Crvs, uParams):
        progressInc = cmds.progressBar(progressControl, edit=True, pr=p)
        p = p + 1
        Dcrv = cmds.detachCurve(e, ch=0, p=f, rpo=1)
        cmds.delete(Dcrv[0])

    for e in Crvs:
        progressInc = cmds.progressBar(progressControl, edit=True, pr=p)
        p = p + 1
        cmds.reverseCurve(e, ch=0)

    cmds.delete(CPOM)
    cmds.select(Crvs)
    cmds.SelectCurveCVsFirst()
    cmds.deleteUI(window)
    ET = time.time()
    TT = ET - ST
    TT = str(TT)
    TT = TT[0:4]
    cmds.warning('Totoal time taken = ' + TT + ' Seconds')


def FixRootCVs(*args):
    global Crvs
    global peneCVsAll
    sel = cmds.ls(sl=1)
    meshName = sel[(-1)]
    curveList = sel[0:len(sel) - 1]
    cmds.select(meshName)
    meshName = cmds.duplicate()
    meshShape = cmds.listRelatives(meshName, s=1)
    cmds.SmoothPolygon()
    cmds.select(meshName)
    mesh2 = cmds.duplicate()
    cmds.textureDeformer(en=1, s=1, o=0.05, vs=(1, 1, 1), vo=(0, 0, 0), vsp='Object', d='Normal', ps='Local', ex='')
    cmds.delete(mesh2, ch=1)
    CPOM = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(meshShape[0] + '.worldMatrix', CPOM + '.inputMatrix')
    cmds.connectAttr(meshShape[0] + '.worldMesh', CPOM + '.inMesh')
    mesh2Shape = cmds.listRelatives(mesh2, s=1)
    CPOM2 = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(mesh2Shape[0] + '.worldMatrix', CPOM2 + '.inputMatrix')
    cmds.connectAttr(mesh2Shape[0] + '.worldMesh', CPOM2 + '.inMesh')

    def inCVs():
        global peneCVs
        spans = cmds.getAttr(i + '.spans')
        spans = spans + 3
        vtxs = []
        for cvv in range(spans):
            cv = i + '.cv[%d]' % cvv
            vtxs.append(cv)

        peneCVs = []
        for e in vtxs:
            endPos = cmds.xform(e, q=1, ws=1, t=1)
            cmds.setAttr(CPOM + '.ip', endPos[0], endPos[1], endPos[2], type='double3')
            newPos = cmds.getAttr(CPOM + '.p')
            newPos = [ val for sublist in newPos for val in sublist ]
            cmds.setAttr(CPOM2 + '.ip', endPos[0], endPos[1], endPos[2], type='double3')
            NPos = cmds.getAttr(CPOM2 + '.p')
            NPos = [ val for sublist in NPos for val in sublist ]
            t1x = endPos[0] - newPos[0]
            t1y = endPos[1] - newPos[1]
            t1z = endPos[2] - newPos[2]
            t1 = [t1x, t1y, t1z]
            Pnormal = om.MVector(t1).normal()
            t2x = NPos[0] - newPos[0]
            t2y = NPos[1] - newPos[1]
            t2z = NPos[2] - newPos[2]
            t2 = [t2x, t2y, t2z]
            Fnormal = om.MVector(t2).normal()
            dot = Fnormal * Pnormal
            if dot < 0:
                peneCVs.append(e)

    x = curveList
    window = cmds.window(t='Progress')
    cmds.columnLayout()
    progressControl = cmds.progressBar(maxValue=len(x), width=300)
    cmds.showWindow(window)
    initialTime = time.time()
    p = 0
    peneCVsAll = []
    Crvs = []
    for i in curveList:
        progressInc = cmds.progressBar(progressControl, edit=True, pr=p)
        p = p + 1
        inCVs()
        if len(peneCVs) > 0:
            peneCVs.sort()
            sml = peneCVs[0].split('[')
            sml = sml[1].split(']')[0]
            sml = int(sml)
            cmds.select(peneCVs)
            if sml != 0:
                cmds.reverseCurve(i, ch=0)
            inCVs()
            peneCVs.reverse()
            peneCVsAll.append(peneCVs[0])
            Crvs.append(i)

    cmds.delete(mesh2, meshName, CPOM, CPOM2)
    cmds.deleteUI(window)


def paths(*args):
    mayafiles = cmds.file(query=True, sn=True, l=1)
    xgenFiles = []
    for e in mayafiles:
        parts = e.split('.xgen')
        if len(parts) == 2:
            xgenFile = e
            xgenFiles.append(xgenFile)

    projectPath = cmds.workspace(q=1, rd=1)
    xgenPath = projectPath + 'xgen/collections/'
    return (mayafiles, xgenFiles, xgenPath)


def renameScalpAndPtex(name, *args):
    overrite = 1
    xgenFiles = paths()[1]
    xgenPath = paths()[2]
    mayafiles = paths()[0]
    newMeshName = cmds.textField(name, q=1, tx=1)
    sell = cmds.ls(sl=1)
    if len(sell) == 0:
        cmds.warning('pls select a scalp mesh')
    if len(sell) > 1:
        cmds.warning('pls select only one scalp mesh')
    if len(sell) == 1:
        oldMeshName = cmds.ls(sl=1)[0]
        oldMeshName = str(oldMeshName)
        if len(newMeshName) < 2:
            cmds.warning('pls enter a valid scalp name')
        else:
            cmds.rename(newMeshName)
            newMeshName = cmds.ls(sl=1)
            newMeshName = str(newMeshName[0])
            xgenDesc = cmds.listConnections()
            if xgenDesc == None:
                cmds.warning('pls select a valid scalp mesh')
            else:
                xgenDescs = []
                for e in xgenDesc:
                    cmds.select(e)
                    cmds.pickWalk(d='up')
                    cmds.pickWalk(d='down')
                    selTyp = cmds.ls(sl=1)
                    typo = cmds.objectType(selTyp)
                    if typo == 'xgmDescription':
                        xgenD = cmds.listRelatives(e, p=1)[0]
                        xgenC = cmds.listRelatives(xgenD, p=1)[0]
                        xgenDC = (xgenC, xgenD)
                        xgenDescs.append(xgenDC)

                if len(xgenDescs) == None:
                    cmds.warning('pls select a valid scalp mesh')
                else:
                    cmds.select(newMeshName)
                    descPaths = []
                    collPaths = []
                    for e in xgenDescs:
                        descPath = xgenPath + '/' + e[0] + '/' + e[1]
                        descPaths.append(descPath)
                        collPath = xgenPath + '/' + e[0]
                        collPaths.append(collPath)

                    collPaths = list(set(collPaths))
                    linezz = []
                    for xgn in xgenFiles:
                        linez = []
                        F = open(xgn, 'r')
                        x = 0
                        for line in F:
                            a = line.split()
                            if len(a) > 1:
                                if a[0] == 'Patches':
                                    for xgd in xgenDescs:
                                        if a[1] == xgd[1]:
                                            x = 1
                                            linez.append(line)

                            if x == 1:
                                if a[0] == 'name':
                                    x = 0
                                    addLine = 'Patch\tSubd\n'
                                    newLine = '\t' + a[0] + '\t' + newMeshName + '\n'
                                    linez.append(addLine)
                                    linez.append(newLine)
                            else:
                                linez.append(line)

                        linezz.append(linez)
                        if overrite == 1:
                            F = open(xgn, 'w')
                            for e in linez:
                                F.write(e)

                            F.close()
                        if overrite == 1:
                            for ee in descPaths:
                                filess = []
                                for root, dirs, files in os.walk(ee):
                                    for file in files:
                                        if file.endswith('.ptx'):
                                            files = root + '/' + file
                                            fileName = file.split('.')
                                            newFile = root + '/' + newMeshName + '.ptx'
                                            os.rename(files, newFile)
                                            filess.append(files)

                            cmds.file(f=1, save=1)
                            cmds.file(mayafiles[0], f=1, ignoreVersion=1, o=1)

    return


def renameDescriptions(name2, *args):
    overrite = 1
    newName = cmds.textField(name2, q=1, tx=1)
    sel = cmds.ls(sl=1)
    xgenFiles = paths()[1]
    xgenPath = paths()[2]
    mayafiles = paths()[0]
    if len(sel) == 0:
        cmds.warning('pls select an Xgen Description')
    if len(sel) > 1:
        cmds.warning('pls select only one Xgen Description')
    if len(sel) == 1:
        if len(newName) < 2:
            cmds.warning('pls enter a valid Xgen Description name')
        else:
            cmds.polyCube(n=newName)
            newName = cmds.ls(sl=1)[0]
            cmds.delete()
            cmds.select(sel)
            sel = cmds.ls(sl=1)[0]
            try:
                obj = cmds.listRelatives(s=1)[0]
                type = cmds.objectType(obj)
            except:
                type = 'dummy'

            if type != 'xgmDescription':
                cmds.warning('Please select a valid Xgen Description')
            if type == 'xgmDescription':
                xgenC = cmds.listRelatives(sel, p=1)[0]
                oldDescName = xgenPath + xgenC + '/' + sel
                newDescName = xgenPath + xgenC + '/' + newName
                try:
                    if overrite == 1:
                        os.rename(oldDescName, newDescName)
                except:
                    pass

            if type == 'xgmDescription':
                for xgn in xgenFiles:
                    F = open(xgn, 'r')
                    linez = []
                    x = 0
                    for line in F:
                        a = line.split()
                        if len(a) > 0:
                            if a[0] == 'Description':
                                x = 1
                                linez.append(line)
                            if a[0] == 'Patches':
                                if a[1] == sel:
                                    newLine = a[0] + '\t' + newName + '   ' + a[2] + '\n'
                                    linez.append(newLine)
                                else:
                                    linez.append(line)
                        if x == 1:
                            if a[0] == 'name':
                                x = 0
                                if a[1] == sel:
                                    newLine = '\t' + a[0] + '\t\t\t\t' + newName + '\n'
                                    linez.append(newLine)
                                else:
                                    linez.append(line)
                        else:
                            try:
                                if a[0] == 'Patches':
                                    pass
                                else:
                                    linez.append(line)
                            except:
                                pass

                    if overrite == 1:
                        F = open(xgn, 'w')
                        for e in linez:
                            F.write(e)

                        F.close()
                        cmds.file(f=1, new=1)
                        cmds.file(mayafiles[0], f=1, ignoreVersion=1, o=1)


def enterLicense(*args):

    def feedLCK():
        result = cmds.promptDialog(title='Enter your License Key for GuidesTool', message='___________Enter your GuidesTool License Key___________', button=[
         'OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
        if result == 'OK':
            enc = cmds.promptDialog(query=True, text=True)
            enc = str(enc)
        try:

            def getCPK():
                return '514457286756573634'

            import base64
            key = getCPK()
            dec = []
            end = base64.urlsafe_b64decode(enc)
            for i in range(len(end)):
                key_c = key[(i % len(key))]
                dec_c = chr((256 + ord(end[i]) - ord(key_c)) % 256)
                dec.append(dec_c)

            Lic = ('').join(dec)
            print Lic
            Lic = Lic.split('_')
            print Lic
            chk1 = cmds.optionVar(q='sphereAxisModePG')
            chk2 = cmds.optionVar(q='cubeAxisModePG')
            if chk1 == Lic[0] and chk2 == Lic[1]:
                cmds.optionVar(sv=['sphereAxisModePMG', Lic[0]])
                cmds.optionVar(sv=['cubeAxisModePMG', Lic[2]])
                cmds.optionVar(sv=['planeAxisModePMG', Lic[3]])
                cmds.optionVar(sv=['coneAxisModePMG', Lic[1]])
                cmds.savePrefs()
                cmds.scriptEditorInfo(clearHistory=1)
                cmds.warning('CONGRATS..!! Your GroomTools License is Activated.. Kindly relaunch the Tool UI')
            else:
                cmds.warning('License error:' + ' Please Enter Correct License Key')
        except:
            cmds.warning('License error:' + ' Please Enter Correct License Key')

    exs = cmds.optionVar(ex='sphereAxisModePMG')
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
        ex1 = cmds.optionVar(ex='sphereAxisModePG')
        ex2 = cmds.optionVar(ex='cubeAxisModePG')
        ex3 = cmds.optionVar(ex='planeAxisModePG')
        ex4 = cmds.optionVar(ex='coneAxisModePG')

        def createKeyWin():
            msgA = cmds.optionVar(q='sphereAxisModePG')
            msgB = cmds.optionVar(q='cubeAxisModePG')
            msgC = cmds.optionVar(q='planeAxisModePG')
            msgD = cmds.optionVar(q='coneAxisModePG')
            message = msgA + '_' + msgB + '_' + msgC + '_' + msgD + '_' + PCN + '_' + OSnVer + '_' + 'Maya' + MayaVer

            def getCPK():
                return '162503103368735458' + '359'

            import base64
            key = getCPK()
            enc = []
            for i in range(len(message)):
                key_c = key[(i % len(key))]
                enc_c = chr((ord(message[i]) + ord(key_c)) % 256)
                enc.append(enc_c)

            enc = base64.urlsafe_b64encode(('').join(enc))
            cmds.warning('Please Copy your GroomTools ACTIVATION KEY.. and email it to- aka.toools@gmail.com')
            if cmds.window('ETWin', exists=True):
                cmds.deleteUI('ETWin')
            cmds.window('ETWin', title='Activation Key for GuidesTool', h=60, w=600)
            cmds.columnLayout(adj=True)
            cmds.text(label='Please Copy your GroomTools ACTIVATION KEY.. and email it to- aka.toools@gmail.com')
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
            cmds.optionVar(sv=['sphereAxisModePG', loc[0]])
            cmds.optionVar(sv=['cubeAxisModePG', loc[2]])
            cmds.optionVar(sv=['planeAxisModePG', loc[3]])
            cmds.optionVar(sv=['coneAxisModePG', loc[1]])
            cmds.optionVar(sv=['cylinderAxisModePG', PCN])
            cmds.savePrefs()
            cmds.scriptEditorInfo(clearHistory=1)
            createKeyWin()
        if ex1 == 1 and ex2 == 1 and ex3 == 1 and ex4 == 1:
            createKeyWin()

    exs = cmds.optionVar(ex='sphereAxisModePMG')
    if exs == 1:
        cmds.warning('Your GroomTools Copy is already Licensed')
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
        remConfirm = cmds.confirmDialog(title='Confirm', message='Are you sure you want to remove GroomTools License?', button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
        if remConfirm == 'No':
            cmds.warning('Relax..Your GroomTools License has NOT been removed')
        if remConfirm == 'Yes':
            reremConfirm = cmds.confirmDialog(title='Confirm', message='Please Re-comfrim..!! Are you sure you want to remove GroomTools License?', button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
            if reremConfirm == 'No':
                cmds.warning('Relax..Your GroomTools License has NOT been removed')
            if reremConfirm == 'Yes':
                reeremConfirm = cmds.confirmDialog(title='Confirm', message='FINAL RECONFIRM..!! Your FINALLY SURE you want to REMOVE GroomTools License?', button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
                if reeremConfirm == 'No':
                    cmds.warning('Relax..Your GroomTools License has NOT been removed')
                if reeremConfirm == 'Yes':
                    cmds.optionVar(sv=['gooh3', 1])
                    cmds.optionVar(remove='sphereAxisModePG')
                    cmds.optionVar(remove='cubeAxisModePG')
                    cmds.optionVar(remove='planeAxisModePG')
                    cmds.optionVar(remove='coneAxisModePG')
                    cmds.optionVar(remove='sphereAxisModePMG')
                    cmds.optionVar(remove='cubeAxisModePMG')
                    cmds.optionVar(remove='planeAxisModePMG')
                    cmds.optionVar(remove='coneAxisModePMG')
                    cmds.optionVar(remove='cylinderAxisModePG')
                    cmds.warning('Your `GroomTools` License has been successfully REMOVED')
                    cmds.evalDeferred('cmds.quit(f=1)')

    chk1 = cmds.optionVar(ex='sphereAxisModePMG')
    if chk1 == 0:
        cmds.warning('NO LICENSE FOUND..!! Your GroomTools Product is not Registered yet..!!')
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


def XgenRenamerz(*args):
    cmds.commandEcho(state=0)
    windowID = 'xgenRenamer'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Xgen Renamer Tool', sizeable=1, resizeToFitChildren=1, h=300, w=300)
    cmds.scrollLayout('scrollLayout')
    cmds.columnLayout(adjustableColumn=1)
    cmds.text(label='')
    cmds.setParent(top=1)
    cmds.columnLayout(adjustableColumn=1)
    cmds.frameLayout(label='Xgen Renamer Tool', fn='boldLabelFont', bgc=(0.4, 0.45,
                                                                         0.5), collapsable=0, collapse=0)
    cmds.separator(h=10)
    cmds.rowColumnLayout(numberOfRows=4, cs=[10, 10])
    cmds.text(label='Enter New Scalp Name')
    name = cmds.textField()
    cmds.separator(h=20)
    cmds.button(label='Rename Xgen Scalp mesh', command=partial(renameScalpAndPtex, name), bgc=(0.4,
                                                                                                0.4,
                                                                                                0.4), w=250)
    cmds.separator(h=20)
    cmds.separator(h=20)
    cmds.setParent(u=1)
    cmds.separator(h=10)
    cmds.rowColumnLayout(numberOfRows=4, cs=[10, 10])
    cmds.text(label='Enter New Description Name')
    name2 = cmds.textField()
    cmds.separator(h=20)
    cmds.button(label='Rename Xgen Description', command=partial(renameDescriptions, name2), bgc=(0.4,
                                                                                                  0.4,
                                                                                                  0.4), w=250)
    cmds.separator(h=20)
    cmds.separator(h=20)
    cmds.showWindow(windowID)


def stripsEdit(*args):
    windowID = 'stripsEdit'
    if cmds.window(windowID, exists=1):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='HairStrips Editor', menuBar=1, h=300, w=400)
    cmds.columnLayout(adjustableColumn=1)
    cmds.separator(h=20, w=250)
    selCards()
    if len(UCount) > 0 or len(UCount) == None:
        pm.select(cards)
        cmds.floatSliderGrp('stripsWidth', label='Strips Width', field=1, step=0.01, minValue=0.01, maxValue=5, precision=3, w=350)
        cmds.connectControl('stripsWidth', baseCUs)
        cmds.intSliderGrp('U', label='X segments', field=1, minValue=2, maxValue=20, w=350)
        cmds.connectControl('U', UCount)
        cmds.intSliderGrp('V', label='Y segments', field=1, minValue=2, maxValue=20, w=350)
        cmds.connectControl('V', VCount)
        cmds.intSliderGrp('bendz', label='Bend', field=1, minValue=-50, maxValue=50, w=350)
        cmds.connectControl('bendz', bends)
        cmds.intSliderGrp('rotz', label='Twist', field=1, minValue=-360, maxValue=360, w=350)
        cmds.connectControl('rotz', rotts)
        cmds.floatSliderGrp('sclz', label='Scale', field=1, minValue=0, maxValue=3, w=350)
        cmds.connectControl('sclz', scls)
    else:
        cmds.text('no strips selected')
    cmds.showWindow(windowID)
    return


def bakeStrips(*args):
    selCards()
    pm.select(cards)
    cmds.DeleteHistory()
    cmds.pickWalk(d='up')
    sel = cmds.ls(sl=1, l=1)
    pm.select(cards)
    cmds.parent(w=1)
    cmds.group(n='Strips')
    cmds.delete(sel)


def curlShapesUI(*args):
    sel = cmds.ls(sl=1)
    selShp = cmds.listRelatives(sel[0])
    type = cmds.objectType(selShp[0])
    if type != 'nurbsCurve':
        cmds.warning('Please select a Curl Curve')
    if type == 'nurbsCurve':
        hss = []
        for e in sel:
            try:
                RPattr = cmds.getAttr(e + '.HS')
                hs = json.loads(RPattr)[0]
                hss.append(hs)
            except:
                cmds.warning('Invalid Curl Curve selected')

    clumpWdth = []
    for e in hss:
        cw = e + '.clumpWidth'
        clumpWdth.append(cw)

    clumpTwst = []
    for e in hss:
        ctw = e + '.clumpTwist'
        clumpTwst.append(ctw)

    clumpWdthScl = []
    for e in hss:
        cws = e + '.clumpWidthScale'
        clumpWdthScl.append(cws)

    c = 'clumpWidthScale'
    b = 'clumpCurl'
    valc = 0

    def copyGraph(stringo, sele, *args):
        global Fvals
        global Pvals
        global profileNos1
        profiles = cmds.listAttr(sele, m=1, st=stringo)
        profileNos1 = []
        profileNos2 = []
        for e in profiles:
            nm = e.split('[')
            if len(nm) > 1:
                profileNos2.append(e)
                nm2 = e.split(stringo)
                profileNos1.append(nm2[1])

        profileName = profileNos2[0].split('[')[0]
        Fvals = []
        Pvals = []
        for e in profileNos1:
            floatVal = cmds.getAttr(sele + '.' + profileName + e + '.' + profileName + '_FloatValue')
            Fvals.append(floatVal)
            posVal = cmds.getAttr(sele + '.' + profileName + e + '.' + profileName + '_Position')
            Pvals.append(posVal)

    def pasteGraph(stringo2, sele2, x, *args):
        for i in sele2:
            profiles = cmds.listAttr(i, m=1, st=stringo2)
            profileNos = []
            for e in profiles:
                nm = e.split('[')
                if len(nm) > 1:
                    profileNos.append(e)

            profileName = profileNos[0].split('[')[0]
            c = 0
            for e in profileNos:
                if c > 0:
                    cmds.removeMultiInstance(i + '.' + e)
                c += 1

            for a, b, c in zip(Pvals, Fvals, profileNos1):
                cmds.setAttr(i + '.' + profileName + c + '.' + profileName + '_FloatValue', b)
                cmds.setAttr(i + '.' + profileName + c + '.' + profileName + '_Position', a)
                cmds.setAttr(i + '.' + profileName + c + '.' + profileName + '_Interp', 1)

    def updateGraphC(*args):
        copyGraph(c, hss[0])
        pasteGraph(c, hss, valc)

    def updateGraphB(*args):
        copyGraph(b, hss[0])
        pasteGraph(b, hss, valc)

    windowID = 'curlShapes'
    cmds.optionVar(remove='falloffCurvOptionVar')
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Edit Curl Shape Design', sizeable=1, resizeToFitChildren=1, widthHeight=(350,
                                                                                                          400))
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(h=20, w=250)
    cmds.floatSliderGrp('braidBundleWidth', label='Curl Radius   ', field=1, step=0.01, minValue=0, maxValue=10, v=0, precision=2, w=350)
    cmds.connectControl('braidBundleWidth', clumpWdth)
    cmds.separator(h=20, w=250)
    cmds.text(label='    Curl Radius graph', bgc=(0.4, 0.4, 0.4), h=25)
    cmds.gradientControl(at='%s.clumpWidthScale' % hss[0], w=300, h=100)
    cmds.popupMenu()
    cmds.menuItem(l='Update Graphs', c=partial(updateGraphC))
    cmds.separator(h=20, w=250)
    cmds.floatSliderGrp('braidBundleTwist', label='Curl Twist Offset   ', field=1, step=0.01, minValue=0, maxValue=10, v=0, precision=2, w=350)
    cmds.connectControl('braidBundleTwist', clumpTwst)
    cmds.separator(h=20, w=250)
    cmds.text(label='    Curl Twist graph', bgc=(0.4, 0.4, 0.4), h=25)
    cmds.gradientControl(at='%s.clumpCurl' % hss[0], w=300, h=100)
    cmds.popupMenu()
    cmds.menuItem(l='Update Graphs', c=partial(updateGraphB))
    cmds.showWindow(windowID)


def graphBlendCurvesUI(*args):
    windowID = 'blendCUs'
    cmds.optionVar(remove='falloffCurvOptionVar')
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Graph Blend Guides', sizeable=1, resizeToFitChildren=1)
    cmds.columnLayout(adjustableColumn=1)
    cmds.text(label='')
    cmds.setParent(top=1)
    cmds.columnLayout(adjustableColumn=1)
    cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
    cmds.button(label='Create Blends', command=partial(createBlends), bgc=(0.4, 0.4,
                                                                           0.4), w=194)
    cmds.button(label='Load Blends', command=partial(loadBlends), bgc=(0.4, 0.4, 0.4), w=194)
    cmds.setParent('..')
    cmds.separator(h=20, w=250)
    cmds.setParent('..')
    cmds.frameLayout(label='Shape Graph', collapsable=1, collapse=0, bgc=(0.4, 0.45,
                                                                          0.5))
    cmds.optionVar(stringValueAppend=['falloffCurvOptionVar', '1,1,3'])
    cmds.optionVar(stringValueAppend=['falloffCurvOptionVar', '0,0,3'])
    cmds.gradientControlNoAttr('falloffCurv', h=100, w=380, bgc=(0.4, 0.45, 0.5))
    cmds.gradientControlNoAttr('falloffCurv', e=True, optionVar='falloffCurvOptionVar', cc=partial(graphBlendCUs))
    cmds.text(label=' Root <--     Guides Blend Graph        -->  Tip')
    cmds.separator(h=10, w=250)
    cmds.setParent(top=1)
    cmds.button(label='Graph Blend', command=partial(graphBlendCUs), bgc=(0.4, 0.4,
                                                                          0.4), w=194)
    cmds.button(label='Create Hair-Bunch Setep', command=partial(bunchSetup), bgc=(0.4,
                                                                                   0.4,
                                                                                   0.4), w=194)
    cmds.text(label='')
    cmds.text(label='')
    cmds.setParent(top=1)
    cmds.showWindow(windowID)


def CreateGuides(*args):
    cmds.optionVar(remove='falloffCurvTwistOptionVar')
    cmds.rowColumnLayout(numberOfColumns=1, cs=[10, 10])
    cmds.frameLayout(label='CREATE GUIDES FROM MESH', fn='boldLabelFont', bgc=(0.2,
                                                                               0.45,
                                                                               0.5), collapsable=1, collapse=0, w=300)
    cmds.separator(h=7)
    cmds.text(label='----- CREATE MULTI-EDGE GUIDES ( POLY MESH ) -----', bgc=(0.4,
                                                                               0.45,
                                                                               0.5), h=20)
    cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
    genTube = cmds.checkBox(l='NurbsTubes', v=0)
    cmds.button(label='From Poly Tubes', command=partial(autoMultiEdge, genTube), bgc=(0.4,
                                                                                       0.4,
                                                                                       0.4))
    cmds.button(label='From Multi Loop', command=partial(autoMultiEdge2), bgc=(0.4,
                                                                               0.4,
                                                                               0.4))
    cmds.setParent(u=1)
    cmds.separator(h=1)
    cmds.text(label='----- CREATE VOLUME GUIDES ( NURBS TUBES ) -----', bgc=(0.4, 0.45,
                                                                             0.5), h=25)
    cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
    DensityVal = cmds.intField(w=60, value=5, min=2, max=20)
    cmds.text(label='Tube Guides Density   ')
    flip = cmds.checkBox(l=' Flip direction', v=0)
    cmds.setParent(u=1)
    cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
    centrCU = cmds.checkBox(l=' Center Curves Only ', v=0)
    cmds.button(label='      Create Volume Guides      ', c=partial(tubesToVolCurves, DensityVal, flip, centrCU), bgc=(0.4,
                                                                                                                       0.4,
                                                                                                                       0.4))
    cmds.setParent(u=1)
    cmds.separator(h=10)
    cmds.text(label=' ----- CREATE TWISTY GUIDES -----', bgc=(0.4, 0.45, 0.5), h=25)
    cmds.text(label='', h=1)
    cmds.rowColumnLayout(numberOfColumns=4, cs=[10, 10])
    flipp = cmds.checkBox(l=' Flip direction', v=0, h=5)
    cmds.text(label='')
    cmds.text(label='')
    cmds.text(label='')
    cmds.text(label='   Guides Count    ')
    CountVal = cmds.intField(min=4, max=100, value=6, w=50)
    cmds.text(label='   Base Segments  ')
    segsVal = cmds.intField(min=6, max=100, value=15, w=50)
    cmds.text(label='', h=5)
    cmds.text(label='', h=5)
    cmds.text(label='', h=5)
    cmds.text(label='', h=5)
    cmds.text(label='Twist Amount')
    twistVal = cmds.floatField(min=-10, max=10, precision=2, value=0, w=50)
    cmds.text(label='   Randomisation  ')
    randuVal = cmds.floatField(min=0, max=0.1, precision=2, value=0, w=50)
    cmds.setParent(u=1)
    cmds.button(l='Create Twisty guides', command=partial(Tubes_to_twisted_curves, flipp, CountVal, segsVal, twistVal, randuVal), bgc=(0.4,
                                                                                                                                       0.4,
                                                                                                                                       0.4))
    cmds.separator(h=10)
    cmds.setParent(u=1)
    cmds.frameLayout(label=' CREATE GUIDES FROM CURVES ', fn='boldLabelFont', bgc=(0.2,
                                                                                   0.45,
                                                                                   0.5), collapsable=1, collapse=0, w=300)
    cmds.separator(h=10)
    cmds.text(label=' ----- CREATE STEPY GUIDES -----', bgc=(0.4, 0.45, 0.5), h=20)
    cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
    cmds.text(label='Spacing')
    unitVal = cmds.floatField(min=0, max=20, precision=2, value=0.4, w=30)
    cmds.text(label='LRatio')
    subCuLenVal = cmds.floatField(min=0, max=10, precision=2, value=1.0, w=30)
    cmds.button(label=' Create Stepy Guides ', command=partial(stepCrvs, unitVal, subCuLenVal), bgc=(0.4,
                                                                                                     0.4,
                                                                                                     0.4))
    cmds.setParent(u=1)
    cmds.separator(h=10)
    cmds.text(label=' ----- CREATE CURLY GUIDES -----', bgc=(0.4, 0.45, 0.5), h=20)
    cmds.separator(h=1)
    cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
    cmds.button(label=' Create Curly Guides ', command=partial(createCurl), bgc=(0.4,
                                                                                 0.4,
                                                                                 0.4))
    cmds.button(label=' Edit Guides  ', command=partial(curlShapesUI), bgc=(0.4, 0.4,
                                                                            0.4))
    cmds.button(label=' Freeze Guides  ', command=partial(freezeCurve), bgc=(0.4, 0.4,
                                                                             0.4))
    cmds.setParent(u=1)
    cmds.separator(h=10)
    cmds.text(label=' ----- CREATE INTERPOLATED GUIDES -----', bgc=(0.4, 0.45, 0.5), h=20)
    cmds.separator(h=1)
    cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
    cmds.button(label='     Load Scalp and Guides      ', command=partial(loadScalpGuides), bgc=(0.4,
                                                                                                 0.4,
                                                                                                 0.4))
    cmds.button(label='     Interpolate Guides      ', command=partial(interpolateGuides), bgc=(0.4,
                                                                                                0.4,
                                                                                                0.4))
    cmds.setParent(u=1)
    cmds.separator(h=10)
    cmds.setParent(u=1)
    cmds.frameLayout(label='Create Length-Map Based on Guides Length ', fn='boldLabelFont', bgc=(0.2,
                                                                                                 0.45,
                                                                                                 0.5), collapsable=1, collapse=0, w=300)
    cmds.separator(h=10)
    cmds.rowColumnLayout(numberOfRows=1, cs=[10, 10])
    cmds.button(label='     Create Length Map     ', command=partial(guideToLenMap), bgc=(0.4,
                                                                                          0.4,
                                                                                          0.4))
    cmds.button(label='      Save Length Map       ', command=partial(MapSave), bgc=(0.4,
                                                                                     0.4,
                                                                                     0.4))
    cmds.setParent(u=1)
    cmds.separator(h=10)
    cmds.setParent(u=1)


def CreateGuidesUI(*args):
    global switch1
    if switch1 == 0:
        switch1 = 1
    else:
        switch1 = 0
    windowID = 'createGuides'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Create Guides', sizeable=1, resizeToFitChildren=0, vis=1, h=630, w=340)
    cmds.scrollLayout()
    cmds.columnLayout(adjustableColumn=1)
    cmds.setParent(top=1)
    cmds.rowColumnLayout(numberOfColumns=2, cs=[10, 10])
    cmds.text(label='    ')
    CreateGuides()
    cmds.showWindow(windowID)
    if switch1 == 0:
        cmds.deleteUI(windowID)


def ModifyGuides(*args):
    cmds.frameLayout(label='Modify Guides', fn='boldLabelFont', bgc=(0.4, 0.45, 0.5), collapsable=1, collapse=0)
    cmds.separator(h=10)
    cmds.rowColumnLayout(numberOfColumns=5, cs=[10, 10])
    for e in range(6):
        cmds.text(label='     ')

    cmds.rowColumnLayout(numberOfColumns=2, cs=[10, 10])
    tip = cmds.checkBox(l='Tip? ', v=0)
    cmds.text(label='Falloff ', al='left')
    cmds.setParent(u=1)
    ssScaleVal = cmds.floatField(minValue=0, maxValue=1, precision=2, value=1, step=0.1, w=50)
    cmds.text(label='')
    cmds.button(label='SoftSnap Guide Root-Tip', c=partial(softSnap, tip, ssScaleVal), bgc=(0.4,
                                                                                            0.4,
                                                                                            0.4), w=150, h=20)
    for e in range(6):
        cmds.text(label='     ')

    cmds.text(label='Rebuild Unit Val  ', al='left')
    spacingVal = cmds.floatField(minValue=0.1, maxValue=50, precision=2, value=0.3, step=0.1, w=50)
    cmds.text(label='')
    cmds.button(label='Unit Rebuild Guides', c=partial(rebuildCrvsUnitBased, spacingVal), bgc=(0.4,
                                                                                               0.4,
                                                                                               0.4), w=150, h=20)
    for e in range(6):
        cmds.text(label='     ')

    cmds.text(label='Segment Count  ', al='left')
    segsVal = cmds.intField(minValue=5, maxValue=400, value=5, step=1, w=50)
    cmds.text(label='')
    cmds.button(label='Rebuild Guides', command=partial(rebuildCrvs, segsVal), bgc=(0.4,
                                                                                    0.4,
                                                                                    0.4), w=150, h=20)
    for e in range(6):
        cmds.text(label='     ')

    cmds.text(label='Smooth Value  ', al='left')
    smooVal = cmds.floatField(minValue=0.1, maxValue=100, precision=1, value=0.3, step=0.1, w=50)
    cmds.text(label='')
    cmds.button(label='Smooth Guides', command=partial(smoothCVs, smooVal), bgc=(0.4,
                                                                                 0.4,
                                                                                 0.4), w=150, h=20)
    for e in range(6):
        cmds.text(label='     ')

    cmds.text(label='Collision Offset  ', al='left')
    pushOffset2Val = cmds.floatField(minValue=0.001, maxValue=1, precision=3, value=0.01, step=0.1, w=50)
    cmds.text(label='')
    cmds.button(label='Remove Penetrations', command=partial(RemovePenetration, pushOffset2Val), bgc=(0.4,
                                                                                                      0.4,
                                                                                                      0.4))
    for e in range(6):
        cmds.text(label='     ')

    cmds.text(label='Snap Offset  ', al='left')
    snapOffsetVal = cmds.floatField(minValue=0.001, maxValue=1, precision=3, value=0.01, step=0.1, w=50)
    cmds.text(label='')
    cmds.button(label='Snap Whole Guide', command=partial(snapWholeCU, snapOffsetVal), bgc=(0.4,
                                                                                            0.4,
                                                                                            0.4), w=140, h=20)
    for e in range(6):
        cmds.text(label='     ')

    cmds.text(label='Random Value  ', al='left')
    percVal = cmds.floatField(minValue=0.1, maxValue=0.9, precision=2, value=0.3, step=0.1, w=50)
    cmds.text(label='')
    cmds.button(label='Randomize Guide Length', command=partial(randomizeCULen, percVal), bgc=(0.4,
                                                                                               0.4,
                                                                                               0.4), w=150, h=20)
    for e in range(6):
        cmds.text(label='     ')

    cmds.text(label=' Percentage %  ', al='left')
    percVal = cmds.intField(minValue=1, maxValue=99, value=50, step=1, w=50)
    cmds.text(label='')
    cmds.button(label='Select Random Percent', command=partial(randPercSel, percVal), bgc=(0.4,
                                                                                           0.4,
                                                                                           0.4), w=150, h=20)
    cmds.setParent(u=1)
    cmds.separator(h=10)
    cmds.rowColumnLayout(numberOfColumns=4, cs=[10, 10])
    for e in range(4):
        cmds.text(label='', h=3)

    cmds.text(label='')
    cmds.button(label='Create Tweak-Joints', command=partial(FKIK), bgc=(0.4, 0.4,
                                                                         0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='Bake Tweak-Joints', command=partial(delFK), bgc=(0.4, 0.4, 0.4), w=140, h=20)
    for e in range(4):
        cmds.text(label='', h=3)

    cmds.text(label='')
    cmds.button(label='Enable Soft EDIT ', command=partial(EnableSoftEdit), bgc=(0.4,
                                                                                 0.4,
                                                                                 0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='Disable Soft EDIT ', command=partial(DisableSoftEdit), bgc=(0.4,
                                                                                   0.4,
                                                                                   0.4), w=140, h=20)
    cmds.text(label='      ')
    cmds.text(label='  CVs and Selection    ', h=25, al='left')
    cmds.text(label='      ')
    cmds.text(label='      ')
    cmds.text(label='      ')
    cmds.button(label='Select Root CV', command=partial(selectFirstCV), bgc=(0.4, 0.4,
                                                                             0.4), w=124, h=20)
    cmds.text(label='')
    cmds.button(label='Select Tip CV', command=partial(selectLastCV), bgc=(0.4, 0.4,
                                                                           0.4), w=124, h=20)
    for e in range(4):
        cmds.text(label='', h=3)

    cmds.text(label='')
    cmds.button(label='Grow CV Select', command=partial(growCVSel), bgc=(0.4, 0.4,
                                                                         0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='Toggle Sub-Obj Mode', command=partial(CVMode), bgc=(0.4, 0.4,
                                                                           0.4), w=124, h=20)
    cmds.text(label='      ')
    cmds.text(label='  Roots based   ', h=25, al='left')
    cmds.text(label='      ')
    cmds.text(label='      ')
    cmds.text(label='')
    cmds.button(label='Trim Scalp Penetration', command=partial(trim_Guides_Scalp), bgc=(0.4,
                                                                                         0.4,
                                                                                         0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='Move Pivot to Root', command=partial(pivotToRoot), bgc=(0.4,
                                                                               0.4,
                                                                               0.4), w=140, h=20)
    for e in range(4):
        cmds.text(label='', h=3)

    cmds.text(label='')
    cmds.button(label='Relax Guides', command=partial(smooHairCUs), bgc=(0.4, 0.4,
                                                                         0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='Flip Guide Direction', command=partial(reverseCUrv), bgc=(0.4,
                                                                                 0.4,
                                                                                 0.4), w=140, h=20)
    cmds.text(label='      ')
    cmds.text(label='  Maya Standard  ', h=25, al='left')
    cmds.text(label='      ')
    cmds.text(label='      ')
    cmds.text(label='')
    cmds.button(label='Freeze Transform', command=partial(freezeTrans), bgc=(0.4, 0.4,
                                                                             0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='Delete History', command=partial(deleteHist), bgc=(0.4, 0.4,
                                                                          0.4), w=140, h=20)
    for e in range(4):
        cmds.text(label='', h=3)

    cmds.text(label='')
    cmds.button(label='Nurbs Loft', command=partial(nurbsLoft), bgc=(0.4, 0.4, 0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='Create Selection Set  ', command=partial(createSelSet), bgc=(0.4,
                                                                                    0.4,
                                                                                    0.4), w=140, h=20)
    cmds.text(label='      ')
    cmds.text(label='  Add-on Tools ', h=25, al='left')
    cmds.text(label='      ')
    cmds.text(label='      ')
    cmds.text(label='')
    cmds.button(label='Clump Guide Tips', command=partial(clumpTips), bgc=(0.4, 0.4,
                                                                           0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='Create Curve on Tips ', command=partial(createCuOnTips), bgc=(0.4,
                                                                                     0.4,
                                                                                     0.4), w=140, h=20)
    for e in range(4):
        cmds.text(label='', h=3)

    cmds.text(label='')
    cmds.button(label='Draw PFX Guides ', command=partial(drawPfx), bgc=(0.4, 0.4,
                                                                         0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='PFX To Guides ', command=partial(pfxToCrv), bgc=(0.4, 0.4, 0.4), w=140, h=20)
    for e in range(4):
        cmds.text(label='', h=3)

    cmds.text(label='')
    cmds.button(label='Vertex-Pair to Guide ', command=partial(vtxToGuide), bgc=(0.4,
                                                                                 0.4,
                                                                                 0.4), w=140, h=20)
    cmds.text(label='')
    cmds.button(label='', bgc=(0.4, 0.4, 0.4), w=140, h=20)
    cmds.setParent(top=1)
    cmds.separator(h=10)


def ModifyGuidesUI(*args):
    global switch2
    if switch2 == 0:
        switch2 = 1
    else:
        switch2 = 0
    windowID = 'modifyGuides'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Modify Guides', sizeable=1, menuBar=1, resizeToFitChildren=1, h=510, w=340)
    cmds.scrollLayout('scrollLayout')
    cmds.text(label='', h=5)
    ModifyGuides()
    cmds.showWindow(windowID)
    if switch2 == 0:
        cmds.deleteUI(windowID)


def DeformGuides(*args):
    cmds.frameLayout(label='Deform Guides', fn='boldLabelFont', bgc=(0.4, 0.45, 0.5), collapsable=1, collapse=0)
    cmds.separator(h=10)
    cmds.rowColumnLayout(numberOfColumns=2, cs=[10, 10])
    cmds.text(label='      ')
    cmds.rowColumnLayout(numberOfRows=10, cs=[10, 10])
    cmds.button(label='Transfer Skin - Mesh to Curves', command=partial(transferSkinWeights), bgc=(0.4,
                                                                                                   0.4,
                                                                                                   0.4), w=194, h=30)
    cmds.text(label='')
    cmds.button(label='Root-Tip Blend Curves UI', command=partial(graphBlendCurvesUI), bgc=(0.4,
                                                                                            0.4,
                                                                                            0.4), w=194, h=30)
    cmds.text(label='')
    cmds.button(label='Stick curves to Scalp', command=partial(rivetCurves), bgc=(0.4,
                                                                                  0.4,
                                                                                  0.4), w=194, h=30)
    cmds.text(label='')
    cmds.button(label='Apply FFD', command=partial(applyFFD), bgc=(0.4, 0.4, 0.4), w=194, h=30)
    cmds.setParent(top=1)
    cmds.separator(h=10)


def DeformGuidesUI(*args):
    global switch3
    if switch3 == 0:
        switch3 = 1
    else:
        switch3 = 0
    windowID = 'deformGuides'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Deform Guides', sizeable=1, menuBar=1, resizeToFitChildren=1, h=250, w=250)
    cmds.scrollLayout('scrollLayout')
    cmds.text(label='', h=5)
    DeformGuides()
    cmds.showWindow(windowID)
    if switch3 == 0:
        cmds.deleteUI(windowID)


def DisplayGuides(*args):
    cmds.frameLayout(label='Display Guides', fn='boldLabelFont', bgc=(0.4, 0.45, 0.5), collapsable=1, collapse=0, w=290)
    cmds.separator(h=10)
    cmds.rowColumnLayout(numberOfColumns=2, cs=[1, 0])
    cmds.rowColumnLayout(numberOfRows=2, cs=[1, 0])
    cmds.text(label='          ')
    cmds.text(label='    ')
    cmds.rowColumnLayout(numberOfRows=5, cs=[1, 0])
    baseColVal = cmds.colorSliderGrp(l='Color', rgb=(0.15, 0.7, 0.0), w=220)
    cmds.button(label='Curves Color', command=partial(curvesColorOverride, baseColVal), bgc=(0.4,
                                                                                             0.4,
                                                                                             0.4), w=10)
    cmds.separator(h=15)
    cmds.button(label='Curves to Scalp Color', command=partial(curvesColorScalp), bgc=(0.4,
                                                                                       0.4,
                                                                                       0.4), w=10)
    cmds.setParent(top=1)
    cmds.rowColumnLayout(numberOfColumns=2, cs=[1, 0])
    cmds.text(label='     ')
    cmds.rowColumnLayout(numberOfColumns=3, cs=[10, 100])
    cmds.checkBox(label='Show/Hide Guide CVs', onc=partial(showCVss), ofc=partial(hideCVss))
    cmds.text(label='   ', h=5)
    cmds.button(label='', bgc=(0.4, 0.4, 0.4), w=124, h=20)
    cmds.text(label='   ', h=5)
    cmds.text(label='   ', h=5)
    cmds.text(label='   ', h=5)
    cmds.text(label='   ', h=15)
    cmds.text(label='   ', h=15)
    cmds.text(label='   ', h=15)
    cmds.button(label='Filter: Mesh Select', command=partial(cuSelFilterOFF), bgc=(0.4,
                                                                                   0.4,
                                                                                   0.4), w=124, h=20)
    cmds.text(label='   ', h=5)
    cmds.button(label='Filter: All Select', command=partial(allSelFilterON), bgc=(0.4,
                                                                                  0.4,
                                                                                  0.4), w=124, h=20)
    cmds.text(label='   ', h=5)
    cmds.text(label='   ', h=5)
    cmds.text(label='   ', h=5)
    cmds.button(label='', bgc=(0.4, 0.4, 0.4), w=124, h=20)
    cmds.text(label='   ', h=5)
    cmds.button(label='Filter: Curve Select', command=partial(cuSelFilterON), bgc=(0.4,
                                                                                   0.4,
                                                                                   0.4), w=124, h=20)
    cmds.setParent(top=1)
    cmds.separator(h=10)


def DisplayGuidesUI(*args):
    global switch4
    if switch4 == 0:
        switch4 = 1
    else:
        switch4 = 0
    windowID = 'displayGuides'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Display Guides', sizeable=1, menuBar=1, resizeToFitChildren=1, h=300, w=300)
    cmds.scrollLayout('scrollLayout')
    cmds.text(label='', h=5)
    DisplayGuides()
    cmds.showWindow(windowID)
    if switch4 == 0:
        cmds.deleteUI(windowID)


def MiscTools(*args):
    cmds.frameLayout(label='Misc Tools', fn='boldLabelFont', bgc=(0.4, 0.45, 0.5), collapsable=1, collapse=0)
    cmds.separator(h=2)
    cmds.rowColumnLayout(numberOfColumns=2, cs=[10, 5])
    cmds.text(label='     ')
    cmds.rowColumnLayout(numberOfColumns=1, cs=[10, 5])
    cmds.button(label='Import Face-Sel-Sets', command=partial(emport), bgc=(0.4, 0.4,
                                                                            0.4))
    cmds.text(label='', h=5)
    cmds.button(label='Export Face-Sel-Sets', command=partial(export), bgc=(0.4, 0.4,
                                                                            0.4))
    cmds.text(label='', h=5)
    cmds.button(label='Transfer Face-Sel-Sets', command=partial(transferSelSets), bgc=(0.4,
                                                                                       0.4,
                                                                                       0.4))
    cmds.text(label='', h=5)
    cmds.button(label='Remove Scene NameSpaces', command=partial(nameSpaceRemover), bgc=(0.4,
                                                                                         0.4,
                                                                                         0.4))
    cmds.text(label='')
    cmds.setParent(top=1)


def MiscToolsUI(*args):
    global switch5
    if switch5 == 0:
        switch5 = 1
    else:
        switch5 = 0
    windowID = 'miscTools'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Misc Tools', sizeable=1, menuBar=1, resizeToFitChildren=1, h=200, w=200)
    cmds.scrollLayout('scrollLayout')
    cmds.columnLayout(adjustableColumn=1)
    cmds.text(label='')
    cmds.setParent(top=1)
    MiscTools()
    cmds.showWindow(windowID)
    if switch5 == 0:
        cmds.deleteUI(windowID)


def CurlIT(*args):
    windowID = 'CurveCurl'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='CURL IT', sizeable=1, menuBar=1, resizeToFitChildren=1, h=250, w=430)
    cmds.scrollLayout('scrollLayout')
    cmds.columnLayout(adjustableColumn=1)
    cmds.text(label='     Tool developed by - AKA Tools - Abhishek Karmakar - aakaashwa@gmail.com    ', bgc=(0.35,
                                                                                                             0.4,
                                                                                                             0.4), h=25)
    cmds.text(label='')
    cmds.setParent(top=1)
    cmds.columnLayout(adjustableColumn=1)
    cmds.setParent(top=1)
    cmds.frameLayout(label='CURLY CURVES', fn='boldLabelFont', bgc=(0.4, 0.45, 0.5), collapsable=1, collapse=0, w=350)
    cmds.button(label='Create Curly Curves', command=partial(createCurl), bgc=(0.4,
                                                                               0.4,
                                                                               0.4))
    cmds.button(label='Curl Properties', command=partial(selectHS), bgc=(0.4, 0.4,
                                                                         0.4))
    cmds.button(label='Freeze Curl curves', command=partial(freezeCurve), bgc=(0.4,
                                                                               0.4,
                                                                               0.4))
    cmds.setParent(top=1)
    cmds.showWindow(windowID)


def combMyGuidesUI():

    def verifyLic():
        msgA = cmds.optionVar(q='sphereAxisModePMG')
        msgB = cmds.optionVar(q='cubeAxisModePMG')
        msgC = cmds.optionVar(q='planeAxisModePMG')
        msgD = cmds.optionVar(q='coneAxisModePMG')
        import platform
        PCN = platform.node()
        try:
            userL = str(msgA) + '_' + str(msgB) + '_' + str(msgC) + '_' + str(msgD) + '_' + PCN
        except:
            cmds.warning('License error' + ' Please contact your vendor')

        try:
            msgA = cmds.optionVar(q='sphereAxisModePG')
            msgB = cmds.optionVar(q='cubeAxisModePG')
            msgC = cmds.optionVar(q='planeAxisModePG')
            msgD = cmds.optionVar(q='coneAxisModePG')
            msgE = cmds.optionVar(q='cylinderAxisModePG')
            key = str(msgA) + '_' + str(msgC) + '_' + str(msgD) + '_' + str(msgB) + '_' + str(msgE)
        except:
            cmds.warning('License error:' + ' Please contact your vendor')

        return (key, userL)

    switches()
    path = cmds.internalVar(userAppDir=1) + 'UnPlugIcons/'
    iconz = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.jpg'):
                files = root + '/' + file
                iconz.append(files)

    if len(iconz) > 0:
        useIconz = 1
    else:
        useIconz = 0
    cmds.commandEcho(state=0)
    windowID = 'groomTsoolz'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title='Comb-my-Guides 1.0', sizeable=1, menuBar=1, resizeToFitChildren=1, h=330, w=315)
    cmds.window(windowID, e=1, h=330, w=315)
    cmds.menu(label=' HELP..!!', tearOff=1)
    cmds.menuItem(label='Get your Activation Key', c=partial(getActKey))
    cmds.menuItem(label='Enter your License Key', c=partial(enterLicense))
    cmds.menuItem(label='About Us', c=partial(aboutUs))
    cmds.menuItem(label='Tools Help', c=partial(toolsHelp))
    cmds.menuItem(label='More Products', c=partial(otherProducts))
    cmds.menuItem(label='[Remove License]', c=partial(removeLicense), bld=1)
    cmds.columnLayout(adjustableColumn=1)
    cmds.text(label='    Powered by - UNPLUG TOOLS     ', bgc=(0.35, 0.4, 0.4), h=25)
    cmds.text(label='    unplug.tools@gmail.com     ', bgc=(0.35, 0.4, 0.4), h=25)
    cmds.separator(h=10)
    cmds.setParent(top=1)
    cmds.rowColumnLayout(numberOfColumns=2, cs=[10, 5])
    cmds.rowColumnLayout(numberOfRows=2, cs=[10, 5])
    cmds.text(label='          ', h=15)
    cmds.setParent(u=1)
    if verifyLic()[0] != verifyLic()[1]:
        cmds.rowColumnLayout(numberOfRows=15, cs=[5, 2])
        cmds.text(label='NO LICENSE INSTALLED IN THIS PC', h=20)
        if useIconz == 1:
            sym = cmds.image(ann='Wise Monkey', image=path + 'error1.jpg')
        else:
            cmds.button(label=' O.O ', command=partial(ModifyGuidesUI), bgc=(0.4, 0.4,
                                                                             0.4))
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
        cmds.separator(h=15)
        cmds.text(label='')
        cmds.setParent('..')
        cmds.showWindow(windowID)

        def print_every(n=0.5):
            while True:
                try:
                    if img == '/error1':
                        img = '/error2'
                    else:
                        img = '/error1'
                except:
                    img = '/error1'

                if useIconz == 1:
                    try:
                        cmds.image(sym, e=1, ann='Wise Monkey', image=path + img + '.jpg')
                    except:
                        pass

                else:
                    cmds.button(label='Wise Monkey', command=partial(ModifyGuidesUI), bgc=(0.4,
                                                                                           0.4,
                                                                                           0.4))
                time.sleep(n)

        thread = threading.Thread(target=print_every)
        thread.start()
    if verifyLic()[0] == verifyLic()[1]:
        cmds.rowColumnLayout(numberOfRows=4, cs=[5, 2])
        if useIconz == 1:
            cmds.symbolButton(ann='Create Guides UI', image=path + 'create.jpg', command=partial(CreateGuidesUI))
        else:
            cmds.button(label='Create Guides', command=partial(CreateGuidesUI), bgc=(0.4,
                                                                                     0.4,
                                                                                     0.4), w=120, h=70)
        cmds.text(label='', h=2)
        if useIconz == 1:
            cmds.symbolButton(ann='Create Guides UI', image=path + 'display.jpg', command=partial(DisplayGuidesUI))
        else:
            cmds.button(label='Display Guides', command=partial(DisplayGuidesUI), bgc=(0.4,
                                                                                       0.4,
                                                                                       0.4), w=120, h=70)
        cmds.text(label='', h=2)
        if useIconz == 1:
            cmds.symbolButton(ann='Create Guides UI', image=path + 'modify.jpg', command=partial(ModifyGuidesUI))
        else:
            cmds.button(label='Modify Guides', command=partial(ModifyGuidesUI), bgc=(0.4,
                                                                                     0.4,
                                                                                     0.4), w=120, h=70)
        cmds.text(label='', h=2)
        if useIconz == 1:
            cmds.symbolButton(ann='Create Guides UI', image=path + 'deform.jpg', command=partial(DeformGuidesUI))
        else:
            cmds.button(label='Deform Guides', command=partial(DeformGuidesUI), bgc=(0.4,
                                                                                     0.4,
                                                                                     0.4), w=120, h=70)
        cmds.setParent(top=1)
        cmds.rowColumnLayout(numberOfColumns=2, cs=[5, 2])
        cmds.text(label='                         ', h=2)
        if useIconz == 1:
            cmds.symbolButton(ann='Create Guides UI', image=path + 'miscTools.jpg', command=partial(MiscToolsUI))
        else:
            cmds.button(label='Misc Tools', command=partial(MiscToolsUI), bgc=(0.4,
                                                                               0.4,
                                                                               0.4), w=120, h=70)
    cmds.showWindow(windowID)
