# -*- coding: utf-8 -*-

__author__ = "James.N"
__version__ = "1.0.0"


import sys
import math
import traceback

import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as om

kPluginNodeName = 'quadsphere'
kPluginNodeId = om.MTypeId(0xBE8AC)


def lerp(v1, v2, amount):
    """
    linear interpolation
    """
    return amount * v2 + (1.0 - amount) * v1

def createSpherePoint(radius, initX, initY, initZ, interp=1.0):
    """
    evenly project points of unit cube onto spherical surface
    """

    if interp <= 0.0:
        return om.MPoint(initX * radius, initY * radius, initZ * radius)
    else:
        xx = initX * initX
        yy = initY * initY
        zz = initZ * initZ

        nx = initX * math.sqrt(1.0 - (yy / 2.0) - (zz / 2.0) + (yy * zz / 3.0))
        ny = initY * math.sqrt(1.0 - (xx / 2.0) - (zz / 2.0) + (xx * zz / 3.0))
        nz = initZ * math.sqrt(1.0 - (xx / 2.0) - (yy / 2.0) + (xx * yy / 3.0))

        if interp >= 1.0:
            return om.MPoint(nx * radius, ny * radius, nz * radius)
        else:
            return om.MPoint(
                lerp(initX, nx, interp) * radius, lerp(initY, ny, interp) * radius, lerp(initZ, nz, interp) * radius
            )


class QuadSphereParams(object):
    def __init__(self):
        self.division = 0
        self.radius = 0.0
        self.spherical = 0.0


class QuadSphereNode(OpenMayaMPx.MPxNode):
    # division
    divisionAttribute = om.MObject()
    # radius
    radiusAttribute = om.MObject()
    # spherical
    sphericalAttribute = om.MObject()

    # output mesh
    outputMeshAttribute = om.MObject()

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)

    def compute(self, pPlug, pDataBlock):
        if pPlug == QuadSphereNode.outputMeshAttribute:
            # get input attributes
            params = QuadSphereParams()
            params.division = pDataBlock.inputValue(QuadSphereNode.divisionAttribute).asInt()
            params.radius = pDataBlock.inputValue(QuadSphereNode.radiusAttribute).asFloat()
            params.spherical = pDataBlock.inputValue(QuadSphereNode.sphericalAttribute).asFloat()

            # generate mesh data
            outMeshData = om.MFnMeshData().create()
            try:
                self._createMesh(params, outMeshData)
            except Exception:
                traceback.print_exc()

            # set output
            outMeshHandle = pDataBlock.outputValue(QuadSphereNode.outputMeshAttribute)
            outMeshHandle.setMObject(outMeshData)
            pDataBlock.setClean(QuadSphereNode.outputMeshAttribute)

    def _createMesh(self, params, meshData):
        """
        vtx count:
        n := division + 1
        vtx for one side: V := n^2
        vtx shared by three sides: 8 [16 merged]
        vtx shared by two sides: (n - 2) * 12 [12 edges]
        vtx count = V * 6 - ((n - 2) * 12) / 2 - 16
                  = 6n^2 - 6n -4

              a
          *********
        d *  top  * b
          *       *
          *********
              c
        """

        # basic params
        division = params.division
        pc = division + 1
        step = 2.0 / division

        division2 = division * division

        vtxCount = 6 * pc * division - 4
        polyCount = division2 * 6

        # mesh component containers
        vtxArr = om.MPointArray(vtxCount)
        vtxCountArr = om.MIntArray(polyCount, 4)
        connectionArr = om.MIntArray(polyCount * 4)

        # side a
        start = om.MPoint(-1.0, -1.0, -1.0)
        for row in range(pc):
            for col in range(pc):
                np = createSpherePoint(
                    params.radius,
                    start.x + col * step,
                    start.y + row * step,
                    start.z,
                    params.spherical
                )

                vtxIndex = row * pc + col
                vtxArr.set(np, vtxIndex)

                if row > 0 and col > 0:
                    QuadSphereNode._addQuadConnection(
                        connectionArr,
                        (row - 1) * division + col - 1,
                        vtxIndex - pc,
                        vtxIndex - pc - 1,
                        vtxIndex - 1,
                        vtxIndex
                    )

        # side b
        start = om.MPoint(1.0, -1.0, -1.0)
        startVtxIndex = pc * pc
        startPolyIndex = division2
        for row in range(pc):
            for col in range(1, pc):
                np = createSpherePoint(
                    params.radius,
                    start.x,
                    start.y + row * step,
                    start.z + col * step,
                    params.spherical
                )

                vtxIndex = startVtxIndex + row * division + col - 1
                vtxArr.set(np, vtxIndex)

                if row > 0:
                    polyIndex = startPolyIndex + (row - 1) * division + col - 1
                    if col == 1:
                        QuadSphereNode._addQuadConnection(
                            connectionArr,
                            polyIndex,
                            vtxIndex - division,
                            row * pc - 1,
                            (row + 1) * pc - 1,
                            vtxIndex
                        )
                    else:
                        QuadSphereNode._addQuadConnection(
                            connectionArr,
                            polyIndex,
                            vtxIndex - division,
                            vtxIndex - division - 1,
                            vtxIndex - 1,
                            vtxIndex
                        )

        # side c
        start = om.MPoint(1.0, -1.0, 1.0)
        prevStartVtxIndex = startVtxIndex
        startVtxIndex += (pc * division)
        startPolyIndex += division2
        for row in range(pc):
            for col in range(1, pc):
                np = createSpherePoint(
                    params.radius,
                    start.x - col * step,
                    start.y + row * step,
                    start.z,
                    params.spherical
                )

                vtxIndex = startVtxIndex + row * division + col - 1
                vtxArr.set(np, vtxIndex)

                if row > 0:
                    polyIndex = startPolyIndex + (row - 1) * division + col - 1
                    if col == 1:
                        QuadSphereNode._addQuadConnection(
                            connectionArr,
                            polyIndex,
                            vtxIndex - division,
                            prevStartVtxIndex + row * division - 1,
                            prevStartVtxIndex + (row + 1) * division - 1,
                            vtxIndex
                        )
                    else:
                        QuadSphereNode._addQuadConnection(
                            connectionArr,
                            polyIndex,
                            vtxIndex - division,
                            vtxIndex - division - 1,
                            vtxIndex - 1,
                            vtxIndex
                        )

        # side d
        start = om.MPoint(-1.0, -1.0, 1.0)
        prevStartVtxIndex = startVtxIndex
        startVtxIndex += (pc * division)
        startPolyIndex += division2
        for row in range(pc):
            for col in range(1, division):
                np = createSpherePoint(
                    params.radius,
                    start.x,
                    start.y + row * step,
                    start.z - col * step,
                    params.spherical
                )

                vtxIndex = startVtxIndex + row * (division - 1) + col - 1
                vtxArr.set(np, vtxIndex)

                if row > 0:
                    polyIndex = startPolyIndex + (row - 1) * division + col - 1
                    if col == 1:
                        QuadSphereNode._addQuadConnection(
                            connectionArr,
                            polyIndex,
                            vtxIndex - division + 1,
                            prevStartVtxIndex + row * division - 1,
                            prevStartVtxIndex + (row + 1) * division - 1,
                            vtxIndex
                        )
                    else:
                        QuadSphereNode._addQuadConnection(
                            connectionArr,
                            polyIndex,
                            vtxIndex - division + 1,
                            vtxIndex - division,
                            vtxIndex - 1,
                            vtxIndex
                        )

            # add gap polygon
            if row > 0:
                QuadSphereNode._addQuadConnection(
                    connectionArr,
                    polyIndex + 1,
                    (row - 1) * pc,
                    vtxIndex - division + 1,
                    vtxIndex,
                    row * pc
                )

        # side top
        start = om.MPoint(-1.0, 1.0, -1.0)
        startVtxIndex += ((division - 1) * pc)
        startPolyIndex += division2
        topRim = QuadSphereNode._generateTopRimArr(division)

        QuadSphereNode._generatePlaneFaces(
            params, step, connectionArr, vtxArr, start, startVtxIndex, startPolyIndex, topRim
        )

        # side bottom
        start = om.MPoint(-1.0, -1.0, -1.0)
        startVtxIndex += ((division - 1) * (division - 1))
        startPolyIndex += division2
        bottomRim = QuadSphereNode._generateBottomRimArr(division)

        QuadSphereNode._generatePlaneFaces(
            params, step, connectionArr, vtxArr, start, startVtxIndex, startPolyIndex, bottomRim, reverse=True
        )

        # output mesh
        meshFn = om.MFnMesh(meshData)
        meshFn.create(
            vtxCount,
            polyCount,
            vtxArr,
            vtxCountArr,
            connectionArr,
            meshData
        )

    @staticmethod
    def _addQuadConnection(connectionArr, polyIndex, *points):
        polyOffset = polyIndex * 4
        connectionArr.set(points[0], polyOffset)
        connectionArr.set(points[1], polyOffset + 1)
        connectionArr.set(points[2], polyOffset + 2)
        connectionArr.set(points[3], polyOffset + 3)

    @staticmethod
    def _generatePlaneFaces(params, step, connectionArr, vtxArr, startPos, startVtxIndex, startPolyIndex, rim, reverse=False):
        division = params.division

        left = leftFront = front = 0
        vtxIndex = 0
        polyIndex = 0

        for row in range(1, division):
            for col in range(1, division):
                np = createSpherePoint(
                    params.radius,
                    startPos.x + col * step,
                    startPos.y,
                    startPos.z + row * step,
                    params.spherical
                )

                vtxIndex = startVtxIndex + (row - 1) * (division - 1) + col - 1
                vtxArr.set(np, vtxIndex)

                polyIndex = startPolyIndex + (row - 1) * division + col - 1
                left = rim[3][row] if col == 1 else (vtxIndex - 1)

                if row == 1:
                    leftFront = rim[0][col - 1]
                else:
                    if col == 1:
                        leftFront = rim[3][row - 1]
                    else:
                        leftFront = startVtxIndex + (row - 2) * (division - 1) + col - 2

                if row == 1:
                    front = rim[0][col]
                else:
                    front = startVtxIndex + (row - 2) * (division - 1) + col - 1

                if reverse:
                    QuadSphereNode._addQuadConnection(connectionArr, polyIndex, vtxIndex, left, leftFront, front)
                else:
                    QuadSphereNode._addQuadConnection(connectionArr, polyIndex, vtxIndex, front, leftFront, left)

            # right gap
            if reverse:
                QuadSphereNode._addQuadConnection(
                    connectionArr,
                    polyIndex + 1,
                    rim[1][row],
                    vtxIndex,
                    front,
                    rim[1][row - 1]
                )
            else:
                QuadSphereNode._addQuadConnection(
                    connectionArr,
                    polyIndex + 1,
                    rim[1][row],
                    rim[1][row - 1],
                    front,
                    vtxIndex
                )

        # back gaps
        polyIndex += 1
        if reverse:
            for i in range(1, division + 1):
                QuadSphereNode._addQuadConnection(
                    connectionArr,
                    polyIndex + i,
                    rim[2][i],
                    rim[2][i - 1],
                    rim[3][division - 1] if i == 1 else (startVtxIndex + (division - 2) * (division - 1) + i - 2),
                    rim[1][-2] if i == division else (startVtxIndex + (division - 2) * (division - 1) + i - 1)
                )
        else:
            for i in range(1, division + 1):
                QuadSphereNode._addQuadConnection(
                    connectionArr,
                    polyIndex + i,
                    rim[2][i],
                    rim[1][-2] if i == division else (startVtxIndex + (division - 2) * (division - 1) + i - 1),
                    rim[3][division - 1] if i == 1 else (startVtxIndex + (division - 2) * (division - 1) + i - 2),
                    rim[2][i - 1]
                )

    @staticmethod
    def _generateTopRimArr(division):
        """
            →
          ******
        ↓ *    * ↓
          ******
            →
        """

        pc = division + 1
        arr = [[0] * pc for _ in range(4)]

        # front side
        start = division * pc
        for i in range(pc):
            arr[0][i] = start + i

        # right side
        arr[1][0] = arr[0][-1]
        start = arr[0][-1] + division * division
        for i in range(1, pc):
            arr[1][i] = start + i

        # back side
        arr[2][-1] = arr[1][-1]
        start = arr[1][-1] + division * division
        for i in range(1, pc):
            arr[2][division - i] = start + i

        # left side
        arr[3][0] = arr[0][0]
        arr[3][-1] = arr[2][0]
        start = arr[2][0] + (division - 1) * division
        for i in range(1, division):
            arr[3][division - i] = start + i

        return arr

    @staticmethod
    def _generateBottomRimArr(division):
        pc = division + 1
        arr = [[0] * pc for _ in range(4)]

        # front side
        for i in range(pc):
            arr[0][i] = i

        # right side
        arr[1][0] = arr[0][-1]
        start = pc * pc - 1
        for i in range(1, pc):
            arr[1][i] = start + i

        # back side
        arr[2][-1] = arr[1][-1]
        start = arr[1][-1] + division * division
        for i in range(1, pc):
            arr[2][division - i] = start + i

        # left side
        arr[3][0] = arr[0][0]
        arr[3][-1] = arr[2][0]
        start = arr[2][0] + division * division
        for i in range(1, division):
            arr[3][division - i] = start + i

        return arr



# node initialization
def nodeCreator():
    return OpenMayaMPx.asMPxPtr(QuadSphereNode())

def nodeInitializer():
    numericAttributeFn = om.MFnNumericAttribute()
    typedAttributeFn = om.MFnTypedAttribute()

    # division attribute
    QuadSphereNode.divisionAttribute = numericAttributeFn.create('division', 'div', om.MFnNumericData.kInt, 10)
    numericAttributeFn.setMin(2)
    numericAttributeFn.setSoftMax(20)
    numericAttributeFn.setStorable(False)
    numericAttributeFn.setWritable(True)
    numericAttributeFn.setReadable(False)
    numericAttributeFn.setKeyable(True)
    QuadSphereNode.addAttribute(QuadSphereNode.divisionAttribute)

    # radius attribute
    QuadSphereNode.radiusAttribute = numericAttributeFn.create('radius', 'rad', om.MFnNumericData.kFloat, 1.0)
    numericAttributeFn.setMin(0.1)
    numericAttributeFn.setSoftMax(5.0)
    numericAttributeFn.setStorable(False)
    numericAttributeFn.setWritable(True)
    numericAttributeFn.setReadable(False)
    numericAttributeFn.setKeyable(True)
    QuadSphereNode.addAttribute(QuadSphereNode.radiusAttribute)

    # spherical attribute
    QuadSphereNode.sphericalAttribute = numericAttributeFn.create('spherical', 'sph', om.MFnNumericData.kFloat, 1.0)
    numericAttributeFn.setMin(0.0)
    numericAttributeFn.setMax(1.0)
    numericAttributeFn.setStorable(False)
    numericAttributeFn.setWritable(True)
    numericAttributeFn.setReadable(False)
    numericAttributeFn.setKeyable(True)
    QuadSphereNode.addAttribute(QuadSphereNode.sphericalAttribute)

    # output mesh attribute
    QuadSphereNode.outputMeshAttribute = typedAttributeFn.create('outputMesh', 'outmesh', om.MFnData.kMesh)
    typedAttributeFn.setStorable(False)
    typedAttributeFn.setReadable(True)
    typedAttributeFn.setWritable(False)
    typedAttributeFn.setHidden(False)
    QuadSphereNode.addAttribute(QuadSphereNode.outputMeshAttribute)

    # affect matrix
    QuadSphereNode.attributeAffects(QuadSphereNode.divisionAttribute, QuadSphereNode.outputMeshAttribute)
    QuadSphereNode.attributeAffects(QuadSphereNode.radiusAttribute, QuadSphereNode.outputMeshAttribute)
    QuadSphereNode.attributeAffects(QuadSphereNode.sphericalAttribute, QuadSphereNode.outputMeshAttribute)

# plugin initialization
def initializePlugin(mObject):
    mplugin = OpenMayaMPx.MFnPlugin(mObject, __author__)
    try:
        mplugin.registerNode(kPluginNodeName, kPluginNodeId, nodeCreator, nodeInitializer)
        mplugin.setVersion(__version__)
    except:
        sys.stderr.write("Failed to register node: %s" % kPluginNodeName)
        raise

def uninitializePlugin(mObject):
    mplugin = OpenMayaMPx.MFnPlugin(mObject)
    try:
        mplugin.deregisterNode(kPluginNodeId)
    except:
        sys.stderr.write("Failed to deregister node: %s" % kPluginNodeName)
        raise