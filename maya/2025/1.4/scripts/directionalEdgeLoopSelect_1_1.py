##--------------------------------------------------------------------------
## ScriptName : directional Edge Loop Select
## Contents   : edge loop select with direction and number
## Author     : Joe Wu
## URL        : https://www.youtube.com/@Im3dJoe
## Since      : 2022/12
## Version    : 1.0 public release
## Version    : 1.1 add multi loops function, bug fix
## Install    : copy and paste script into a python tab in maya script editor
##--------------------------------------------------------------------------

import re
import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.mel as mel
from maya.OpenMaya import MGlobal
import math


def directionalEdgeLoopSelect():
    if mc.window("edgeLoopAdvUI", exists = True):
        mc.deleteUI("edgeLoopAdvUI")
    edgeLoopAdvUI = mc.window('edgeLoopAdvUI', t = 'DELS v1.1', h =90, w = 150, s = 0 ,mxb = False,mnb = False)
    mc.columnLayout(adj=1)
    mc.rowColumnLayout(nc=2, cw=[(1, 40), (2, 90)] )
    mc.textField('edgeLoopNumnerRecord',ed=0,en=0, tx = '1')
    mc.gridLayout( numberOfColumns=3, cellWidthHeight=(30, 30) )
    mc.text(l='')
    mc.iconTextButton( style='iconOnly', rpt =1, image1='UVTkNudgeUp.png', c = 'edgeLoopAdvGo("U")' )
    mc.text(l='')
    mc.iconTextButton( style='iconOnly', rpt =1, image1='UVTkNudgeLeft.png',  c = 'edgeLoopAdvGo("L")' )
    mc.iconTextButton('eeIconState', style='iconOnly', rpt =1, image1='polyConvertToEdgeLoop.png',  c = 'eeIconSwitch()' )
    mc.iconTextButton( style='iconOnly', rpt =1, image1='UVTkNudgeRight.png', c = 'edgeLoopAdvGo("R")' )
    mc.text(l='')
    mc.iconTextButton( style='iconOnly', rpt =1, image1='UVTkNudgeDown.png', c = 'edgeLoopAdvGo("D")' )
    mc.iconTextButton('mPlusIconState', style='iconOnly',en=0, rpt =1, image1='pickHandlesObjPartial.png', c = 'mPlusIconSwitch()' )
    #mc.text(l='')
    mc.setParent( '..' )
    mc.showWindow(edgeLoopAdvUI)


def mPlusIconSwitch():
    checkState = mc.iconTextButton('mPlusIconState', q=1 ,image1= 1)
    if checkState == 'pickHandlesObjPartial.png':
        checkState = mc.iconTextButton('mPlusIconState', e=1 , image1 ='pickHandlesObj.png')
    else:
        checkState = mc.iconTextButton('mPlusIconState', e=1 ,en=1, image1 ='pickHandlesObjPartial.png')

def eeIconSwitch():
    checkState = mc.iconTextButton('eeIconState', q=1 ,image1= 1)
    if checkState == 'polyConvertToEdgeLoop.png':
        checkState = mc.iconTextButton('eeIconState', e=1 , image1 ='polyMoveEdge.png')
        checkState = mc.iconTextButton('mPlusIconState', e=1,en=1, image1 ='pickHandlesObjPartial.png')
    else:
        checkState = mc.iconTextButton('eeIconState', e=1 , image1 ='polyConvertToEdgeLoop.png')
        checkState = mc.iconTextButton('mPlusIconState', e=1 ,en=0, image1 ='pickHandlesObj.png')
        

def edgeLoopAdvGo(LoopDir):
    view = omui.M3dView.active3dView()
    cam = om.MDagPath()
    view.getCamera(cam)
    camPath = cam.fullPathName()
    cameraTrans = mc.listRelatives(camPath,type='transform',p=True)
    CurrentCam = cameraTrans[0]
    intSel = []
    intSel = mc.filterExpand(sm=32)
    checkState = mc.iconTextButton('eeIconState', q=1 ,image1= 1)
    if checkState == 'polyMoveEdge.png':
        if intSel:
            toCV= mc.polyListComponentConversion(intSel, fe=1, tv=1)
            toCV = mc.ls(toCV,fl=1)
            toEdge= mc.polyListComponentConversion(toCV, fv=1, te=1)
            toEdge = mc.ls(toEdge,fl=1)
            newFace= mc.polyListComponentConversion(intSel, fe=1, tf=1)
            newFace = mc.ls(newFace,fl=1)
            newEdges= mc.polyListComponentConversion(newFace, ff=1, te=1)
            newEdges = mc.ls(newEdges,fl=1)
            getEdges = list(set(newEdges) - set(toEdge))
            sortData = []
            if getEdges:
                sortData =  sortEdgeLoopGroup(getEdges,0,'')
            if len(sortData) == 1:
                checkEndAA = mc.polyListComponentConversion(sortData[0][0], tv=True)
                checkEndAA = mc.ls(checkEndAA,fl=1)
                crossEdge= mc.polyListComponentConversion(checkEndAA[0], fv=1, te=1)
                crossCV= mc.polyListComponentConversion(crossEdge, fe=1, tv=1)
                crossCV = mc.ls(crossCV,fl=1)
                commonCV = list(set(toCV)&set(crossCV))
                xAA, yAA, zAA = mc.pointPosition(checkEndAA[0], w=1)
                A2DD = worldSpaceToImageSpace(cameraTrans[0], (xAA,yAA,zAA))
                xBB, yBB, zBB = mc.pointPosition(commonCV[0], w=1)
                B2DD = worldSpaceToImageSpace(cameraTrans[0], (xBB,yBB,zBB))
                if LoopDir == 'R':
                    if A2DD[0] > B2DD[0]:
                        mc.select(getEdges)
                elif LoopDir == 'L':
                    if A2DD[0] < B2DD[0]:
                        mc.select(getEdges)
                
                if LoopDir == 'U':
                    if A2DD[1]>B2DD[1]:
                        mc.select(getEdges)

                elif LoopDir == 'D':
                    if A2DD[1] < B2DD[1]:
                        mc.select(getEdges)
            elif len(sortData) == 2:
                crossCV= mc.polyListComponentConversion(intSel[0], fe=1, tv=1)
                crossCV = mc.ls(crossCV,fl=1)
                crossEdge= mc.polyListComponentConversion(crossCV[0], fv=1, te=1)
                loopList = mc.polySelectSp(crossEdge, q= 1, loop=1)
                crossCV= mc.polyListComponentConversion(loopList, fe=1, tv=1)
                crossCV = mc.ls(crossCV,fl=1)
                checkEndAA = mc.polyListComponentConversion(sortData[0], tv=True)
                checkEndAA = mc.ls(checkEndAA,fl=1)
                commonCVAA = list(set(checkEndAA)&set(crossCV))
                checkEndBB = mc.polyListComponentConversion(sortData[1], tv=True)
                checkEndBB = mc.ls(checkEndBB,fl=1)
                commonCVBB = list(set(checkEndBB)&set(crossCV))
                xAA, yAA, zAA = mc.pointPosition(commonCVAA, w=1)
                A2DD = worldSpaceToImageSpace(cameraTrans[0], (xAA,yAA,zAA))
                xBB, yBB, zBB = mc.pointPosition(commonCVBB, w=1)
                B2DD = worldSpaceToImageSpace(cameraTrans[0], (xBB,yBB,zBB))
                if LoopDir == 'R':
                    if A2DD[0]>B2DD[0]:
                        mc.select(sortData[0])
                    else:
                        mc.select(sortData[1])
                elif LoopDir == 'L':
                    if A2DD[0] > B2DD[0]:
                        mc.select(sortData[1])
                    else:
                        mc.select(sortData[0])
                elif LoopDir == 'U':
                    if A2DD[1]>B2DD[1]:
                        mc.select(sortData[0])
                    else:
                        mc.select(sortData[1])
                elif LoopDir == 'D':
                    if A2DD[1] > B2DD[1]:
                        mc.select(sortData[1])
                    else:
                        mc.select(sortData[0])
            checkState = mc.iconTextButton('mPlusIconState', q=1 ,image1= 1)
            if checkState == 'pickHandlesObjPartial.png':
                mc.select(intSel ,add=1)
    else:
        global ctx
        global loopData
        loopData = []
        global fullLoop
        global numberSel
        if 'numberSel' in globals():
            pass
        else:
            numberSel = 1
        fullLoop = 0
        ctx = 'edgeLoopCtx'
        if mc.draggerContext(ctx, exists=True):
            mc.deleteUI(ctx)
        firstCV = ''
        secCV = ''
        shortList = []
        getEdgeLoop=[]
        if len(intSel) == 1:
            geoSel = mc.ls(hl=1)
            storeMeshNode=mc.listRelatives(geoSel,type='transform',p=True)
            if storeMeshNode:
                geoSel[0] = storeMeshNode[0]
            intSelCV = mc.polyListComponentConversion(intSel[0], tv=True)
            intSelCV = mc.ls(intSelCV,fl=1)
            getFace = mc.polyListComponentConversion(intSel[0], tf=True)
            getFace = mc.ls(getFace,fl=1)
            toCV = mc.polyInfo(getFace[0],faceToVertex=1)
            cvOrder = toCV[0].split(':')[1].split('\n')[0].split(' ')
            cvOrder = [x for x in cvOrder if x != '']
            cvOrderList = []
            for c in cvOrder:
                name = geoSel[0] +'.vtx[' + str(c) + ']'
                cvOrderList.append(name)
            for d in cvOrderList:
                if d in intSelCV:
                    shortList.append(d)
            firstCV = shortList[0]
            secCV = shortList[1]
            if shortList[0] == cvOrderList[0] and shortList[1] == cvOrderList[1]:
                pass
            elif shortList[0] == cvOrderList[0] and shortList[1] == cvOrderList[-1]:
                firstCV = shortList[1]
                secCV = shortList[0]
            xA, yA, zA = mc.pointPosition(firstCV, w=1)
            A2D = worldSpaceToImageSpace(cameraTrans[0], (xA,yA,zA))
            xB, yB, zB = mc.pointPosition(secCV, w=1)
            B2D = worldSpaceToImageSpace(cameraTrans[0], (xB,yB,zB))
            #screen space
            if LoopDir == 'L':
                if A2D[0] > B2D[0]:
                    pass
                else:
                    tempFoo = firstCV 
                    firstCV = secCV
                    secCV = tempFoo
            elif LoopDir == 'R':
                if A2D[0] < B2D[0]:
                    pass
                else:
                    tempFoo = firstCV 
                    firstCV = secCV
                    secCV = tempFoo
            elif LoopDir == 'U':
                if A2D[1] < B2D[1]:
                    pass
                else:
                    tempFoo = firstCV 
                    firstCV = secCV
                    secCV = tempFoo
            elif LoopDir == 'D':
                if A2D[1] > B2D[1]:
                    pass
                else:
                    tempFoo = firstCV 
                    firstCV = secCV
                    secCV = tempFoo
            #mc.select(firstCV)
            #mc.select(secCV)
            # for L side -> secCV
            # for R side -> firstCV
            loopList = mc.polySelectSp(intSel, q= 1, loop=1)
            loopList = mc.ls(loopList,fl=1)
            loopList.remove(intSel[0])
            sortData =  sortEdgeLoopGroup(loopList,0,'')
            if len(sortData)>1:
                for s in sortData:
                    checkCV = mc.polyListComponentConversion(s, tv=True)
                    checkCV = mc.ls(checkCV,fl=1)
                    for c in checkCV:
                        if c == secCV:
                            getEdgeLoop = s
            
                getEdgeLoop.append(intSel[0])
            else:
                getEdgeLoop =sortData[0]
                mc.select(intSel)
                mc.polySelectConstraint(m=2,w=1,t=0x8000)
                checkType = mc.ls(sl=1)
                mc.polySelectConstraint(m=0,w=0)
                if len(checkType) > 0:
                    tempFoo = firstCV 
                    firstCV = secCV
                    secCV = tempFoo
                    fullLoop = 1
                else:
                    loopEdgeCount = mc.polySelectSp(intSel, q= 1, loop=1)
                    loopEdgeCount = mc.ls(loopEdgeCount,fl=1)
                    loopCVCount = mc.polyListComponentConversion(loopEdgeCount, tv=True)
                    loopCVCount = mc.ls(loopCVCount,fl=1)
                    if len(loopEdgeCount) == len(loopCVCount):
                        fullLoop = 1
                    else:
                        fullLoop = 0
                        getEdgeLoop.append(intSel[0])
            loopData = edgeLoopOrder(getEdgeLoop)
            if fullLoop == 0:
                mc.select(secCV)
                mc.polySelectConstraint(m=2,w=1,t=0x0001)
                checkType = mc.ls(sl=1)
                mc.polySelectConstraint(m=0,w=0)
                if checkType:
                    mc.select(intSel)
                else:
                    if intSel[0] != loopData[0]:
                        loopData.reverse()
                    mc.select(loopData[0:numberSel])
            else:
                checkEndAA = mc.polyListComponentConversion(loopData[0], tv=True)
                checkEndAA = mc.ls(checkEndAA,fl=1)
                checkEndBB = mc.polyListComponentConversion(loopData[-1], tv=True)
                checkEndBB = mc.ls(checkEndBB,fl=1)
                xAA, yAA, zAA = mc.pointPosition(checkEndAA[0], w=1)
                A2DD = worldSpaceToImageSpace(cameraTrans[0], (xAA,yAA,zAA))
                xBB, yBB, zBB = mc.pointPosition(checkEndBB[0], w=1)
                B2DD = worldSpaceToImageSpace(cameraTrans[0], (xBB,yBB,zBB))
                if LoopDir == 'R':
                    if A2DD[0] < B2DD[0]:
                        loopData.reverse()
                elif LoopDir == 'U':
                    if A2DD[1] < B2DD[1]:
                        loopData.reverse()
                loopData.insert(0, intSel[0])
                mc.select(loopData[0:numberSel])
            mc.draggerContext(ctx, pressCommand = edgeLoopADVPress, rc = edgeLoopADVOff, dragCommand = edgeLoopADVDrag, name=ctx, cursor='crossHair',undoMode='step')
            mc.setToolTo(ctx)

def edgeLoopADVOff():
    global newNumberSel
    global numberSel
    numberSel = newNumberSel
    mc.setToolTo('selectSuperContext')

def edgeLoopADVPress():
    global ctx
    global screenX,screenY
    global numberSel
    vpX, vpY, _ = mc.draggerContext(ctx, query=True, anchorPoint=True)
    screenX = vpX
    screenY = vpY
    if numberSel > 0:
        mc.select(loopData[0:numberSel])
        
def edgeLoopADVDrag():
    global ctx
    global screenX,screenY
    global numberSel
    global loopData
    global newNumberSel
    vpX, vpY, _ = mc.draggerContext(ctx, query=True, dragPoint=True)                
    newNumberSel = int((vpX - screenX) / 50 ) + numberSel
    
    if newNumberSel > 0:
        mc.select(loopData[0:newNumberSel])
        mc.textField('edgeLoopNumnerRecord', e=1, tx = str(newNumberSel))
    mc.refresh(f=True)

def edgeLoopOrder(edgeLoopList):
    loopCV = mc.polyListComponentConversion(edgeLoopList, tv=True)
    loopCV = mc.ls(loopCV,fl=1)
    headEndCV = []
    checkEdge = []
    edgeLoopOrder = [] 
    secP = []  
    for l in loopCV:
        checkEdges = mc.polyListComponentConversion(l, te=True)
        checkEdges = mc.ls(checkEdges,fl=1)
        checkCommon = list(set(edgeLoopList) & set(checkEdges))
        if len(checkCommon) == 1:
            twoP = mc.polyListComponentConversion(checkCommon, tv=True)
            twoP = mc.ls(twoP,fl=1)
            headEndCV.append(l)
            twoP.remove(l)
            secP = twoP
            checkEdge.append(checkCommon[0])
            break
    edgeLoopOrder.append(checkEdge[0])
    edgeLoopList.remove(checkEdge[0])
    while len(edgeLoopList) > 0:
        checkCV = mc.polyListComponentConversion(checkEdge[0], tv=True)
        diff = list(set(checkCV) - set(headEndCV))
        newEdge = mc.polyListComponentConversion(diff, te=True)
        newEdge = mc.ls(newEdge,fl=1)
        checkEdge = list(set(edgeLoopList) & set(newEdge))
        edgeLoopOrder.append(checkEdge[0])
        edgeLoopList.remove(checkEdge[0])
    return edgeLoopOrder

def sortEdgeLoopGroup(selEdges,listSort,listInput):
    trans = selEdges[0].split(".")[0]
    e2vInfos = mc.polyInfo(selEdges, ev=True)
    e2vDict = {}
    fEdges = []
    for info in e2vInfos:
        evList = [ int(i) for i in re.findall('\\d+', info) ]
        e2vDict.update(dict([(evList[0], evList[1:])]))
    while True:
        try:
            startEdge, startVtxs = e2vDict.popitem()
        except:
            break
        edgesGrp = [startEdge]
        num = 0
        for vtx in startVtxs:
            curVtx = vtx
            while True:

                nextEdges = []
                for k in e2vDict:
                    if curVtx in e2vDict[k]:
                        nextEdges.append(k)
                if nextEdges:
                    if len(nextEdges) == 1:
                        if num == 0:
                            edgesGrp.append(nextEdges[0])
                        else:
                            edgesGrp.insert(0, nextEdges[0])
                        nextVtxs = e2vDict[nextEdges[0]]
                        curVtx = [ vtx for vtx in nextVtxs if vtx != curVtx ][0]
                        e2vDict.pop(nextEdges[0])
                    else:
                        break
                else:
                    break
            num += 1
        fEdges.append(edgesGrp)
    retEdges =[]
    for f in fEdges:
        f= list(map(lambda x: (trans +".e["+ str(x) +"]"), f))
        retEdges.append(f)
    if listSort == 1:
        sortEdgeLoopOrder=[]
        getCircleState,listVtx = vtxLoopOrderCheck(listInput)
        for l in listVtx:
            for r in retEdges:
                checkCvList = mc.ls(mc.polyListComponentConversion( r,fe=True, tv=True), fl=True,l=True)
                if l in checkCvList:
                    sortEdgeLoopOrder.append(r)
        return sortEdgeLoopOrder
    else:
        return retEdges

def screenRes():
    global lastPanelActive
    lastPanelActive =[]
    windowUnder = mc.getPanel(withFocus=True)
    if 'modelPanel' not in windowUnder:
        windowUnder = lastPanelActive
        if 'modelPanel' not in windowUnder:
            windowUnder = 'modelPanel4'
    viewNow = omui.M3dView()
    omui.M3dView.getM3dViewFromModelEditor(windowUnder, viewNow)
    screenW = omui.M3dView.portWidth(viewNow)
    screenH = omui.M3dView.portHeight(viewNow)
    return screenW,screenH

def worldSpaceToImageSpace(cameraName, worldPoint):
    resWidth,resHeight = screenRes()
    selList = om.MSelectionList()
    selList.add(cameraName)
    dagPath = om.MDagPath()
    selList.getDagPath(0,dagPath)
    dagPath.extendToShape()
    camInvMtx = dagPath.inclusiveMatrix().inverse()
    fnCam = om.MFnCamera(dagPath)
    mFloatMtx = fnCam.projectionMatrix()
    projMtx = om.MMatrix(mFloatMtx.matrix)
    mPoint = om.MPoint(worldPoint[0],worldPoint[1],worldPoint[2]) * camInvMtx * projMtx;
    x = (mPoint[0] / mPoint[3] / 2 + .5) * resWidth
    y = (mPoint[1] / mPoint[3] / 2 + .5) * resHeight
    return [x,y]    

directionalEdgeLoopSelect()