# Created by Zagoruyko Alexander (C)

import pymel.core as core
import maya.cmds as cmds

from maya.OpenMaya import *
from maya.OpenMayaMPx import *

import time

try:
    mirrorWeights_parameters
except:
    mirrorWeights_parameters = {}
    mirrorWeights_parameters["mirror"] = True
    mirrorWeights_parameters["srcAttr"] = "weightList[0].weights"
    mirrorWeights_parameters["destAttr"] = "weightList[0].weights"
    mirrorWeights_parameters["srcMesh"] = ""
    mirrorWeights_parameters["destMesh"] = ""
    mirrorWeights_parameters["srcDeformer"] = ""
    mirrorWeights_parameters["destDeformer"] = ""
#===========================================================
def getDagByName(name):
    selList = MSelectionList()
    MGlobal.getSelectionListByName(name, selList)

    if selList.length()>0:
        obj = MDagPath()
        selList.getDagPath(0, obj)

        return obj
    else:
        return -1
#===========================================================
def mirrorWeights(srcMesh, destMesh, srcDeformer, destDeformer, mirror, srcAttr="weightList[0].weights", destAttr="weightList[0].weights"):
    if srcDeformer==destDeformer and srcMesh==destMesh and not mirror: # do nothing when copy to itself
        return

    print("%s from '%s.%s' to '%s.%s'"%("Mirror" if mirror else "Copy",srcDeformer, srcAttr, destDeformer, destAttr))

    destPoints = MPointArray()
    destMeshFn = MFnMesh(getDagByName(destMesh))
    destMeshFn.getPoints(destPoints, MSpace.kWorld)

    srcMeshFn = MFnMesh(getDagByName(srcMesh))
    meshIntersector = MMeshIntersector()

    srcMeshPath = getDagByName(srcMesh)
    srcMeshPath.extendToShape()

    meshIntersector.create(srcMeshPath.node(), srcMeshPath.inclusiveMatrix())

    srcAttr_py = core.PyNode("%s.%s"%(srcDeformer, srcAttr))
    srcAttrValues = [0] * srcMeshFn.numVertices()
    for i, k in zip(srcAttr_py.getArrayIndices(), srcAttr_py.get()):
        srcAttrValues[i] = k

    scriptUtil = MScriptUtil()

    weights = [0] * destPoints.length()
    startTime = time.time()
    for i in range(destPoints.length()):
        mirrorPoint = MPoint(destPoints[i])

        if mirror:
            if destPoints[i].x > 0:
                continue

            mirrorPoint.x *= -1

        pm = MPointOnMesh()
        meshIntersector.getClosestPoint(mirrorPoint, pm)

        scriptUtil.createFromInt(0,0,0,0)
        vertices3 = scriptUtil.asIntPtr()

        srcMeshFn.getPolygonTriangleVertices(pm.faceIndex(), pm.triangleIndex(), vertices3)

        u = floatPtr()
        v = floatPtr()
        pm.getBarycentricCoords(u,v)
        u = u.value()
        v = v.value()

        w = 1 - u - v
        # -----------
        v1 = scriptUtil.getIntArrayItem(vertices3, 0)
        v2 = scriptUtil.getIntArrayItem(vertices3, 1)
        v3 = scriptUtil.getIntArrayItem(vertices3, 2)

        weights[i] = srcAttrValues[v1]*u + srcAttrValues[v2]*v + srcAttrValues[v3]*w

    # destAttr = core.PyNode("%s.%s"%(destDeformer, destAttr))
    # destAttrPlug = destAttr.__apimplug__()
    for i in range(destPoints.length()):
        if mirror and srcDeformer == destDeformer and destPoints[i].x > 0:
            continue

        cmds.setAttr("%s.%s[%s]"%(destDeformer, destAttr, i), weights[i])
        # destAttrElementPlug = destAttrPlug.elementByLogicalIndex(i)
        # destAttrElementPlug.setDouble(weights[i])

    print("MirrorWeights time: %s"%(time.time() - startTime))
#===========================================================
def doItClicked():
    global mirrorWeights_parameters

    mirror = cmds.checkBox("mirrorWeightsUI_mirror", q=True, v=True)

    srcAttr = cmds.textFieldGrp("mirrorWeightsUI_srcAttr",q=True, text=True)
    destAttr = cmds.textFieldGrp("mirrorWeightsUI_destAttr",q=True, text=True)

    srcMesh = cmds.textFieldButtonGrp("mirrorWeightsUI_srcMesh", q=True, text=True)
    destMesh = cmds.textFieldButtonGrp("mirrorWeightsUI_destMesh", q=True, text=True)

    srcDeformer = cmds.textFieldButtonGrp("mirrorWeightsUI_srcDeformer", q=True, text=True)
    destDeformer = cmds.textFieldButtonGrp("mirrorWeightsUI_destDeformer", q=True, text=True)

    mirrorWeights_parameters["mirror"] = mirror
    mirrorWeights_parameters["srcAttr"] = srcAttr
    mirrorWeights_parameters["destAttr"] = destAttr
    mirrorWeights_parameters["srcMesh"] = srcMesh
    mirrorWeights_parameters["destMesh"] = destMesh
    mirrorWeights_parameters["srcDeformer"] = srcDeformer
    mirrorWeights_parameters["destDeformer"] = destDeformer

    if not srcMesh or not destMesh or not srcDeformer or not destDeformer or not srcAttr or not destAttr:
       MGlobal.displayError("Please fill all the fields")
       return

    if not cmds.objExists(srcMesh) or not cmds.objExists(destMesh) or \
       not cmds.objExists(srcDeformer) or not cmds.objExists(destDeformer):
       MGlobal.displayError("Some of the entered objects don't exist")
       return

    if not cmds.objExists("%s.%s[0]"%(srcDeformer, srcAttr)) or not cmds.objExists("%s.%s[0]"%(destDeformer, destAttr)):
       MGlobal.displayError("Attr patterns must be valid")
       return

    mirrorWeights(srcMesh, destMesh, srcDeformer, destDeformer, mirror, srcAttr, destAttr)
#===========================================================
def getSelected(field):
    ls = cmds.ls(sl=True)
    if ls:
        cmds.textFieldGrp(field, e=True, text=ls[0])
#===========================================================
def mirrorWeightsUI():
    global mirrorWeights_parameters

    if cmds.windowPref("mirrorWeightsUI_window", exists=True):
        cmds.windowPref("mirrorWeightsUI_window", remove=True)

    if cmds.window("mirrorWeightsUI_window", exists=True):
        cmds.deleteUI("mirrorWeightsUI_window", wnd=True)

    cmds.window("mirrorWeightsUI_window", title="Mirror weights", width=280, height=220, sizeable=False)
    cmds.columnLayout(adj=True, rs=5)

    cmds.checkBox("mirrorWeightsUI_mirror", l="Mirror? (from X to -X)", v=mirrorWeights_parameters["mirror"])

    cmds.textFieldGrp("mirrorWeightsUI_srcAttr",cw2=[90, 180], label="Source attr",text=mirrorWeights_parameters["srcAttr"])
    cmds.textFieldGrp("mirrorWeightsUI_destAttr",cw2=[90, 180], label="Destination attr",text=mirrorWeights_parameters["destAttr"])

    cmds.textFieldButtonGrp("mirrorWeightsUI_srcMesh", cw3=[120, 100, 40], label="Source mesh", text=mirrorWeights_parameters["srcMesh"], buttonLabel="<<", bc="getSelected('mirrorWeightsUI_srcMesh')")
    cmds.textFieldButtonGrp("mirrorWeightsUI_destMesh", cw3=[120, 100, 40], label="Destination mesh", text=mirrorWeights_parameters["destMesh"], buttonLabel="<<", bc="getSelected('mirrorWeightsUI_destMesh')")
    cmds.textFieldButtonGrp("mirrorWeightsUI_srcDeformer", cw3=[120, 100, 40], label="Source deformer", text=mirrorWeights_parameters["srcDeformer"], buttonLabel="<<", bc="getSelected('mirrorWeightsUI_srcDeformer')")
    cmds.textFieldButtonGrp("mirrorWeightsUI_destDeformer", cw3=[120, 100, 40], label="Destination deformer", text=mirrorWeights_parameters["destDeformer"], buttonLabel="<<", bc="getSelected('mirrorWeightsUI_destDeformer')")

    cmds.button(l="Do it", c="doItClicked()")
    cmds.showWindow("mirrorWeightsUI_window")

#mirrorWeightsUI()
