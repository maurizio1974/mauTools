import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as OpenMaya


class MeasureNode(OpenMayaMPx.MPxNode):
    kPluginNodeId = OpenMaya.MTypeId(0x00000120)

    pos1 = OpenMaya.MObject()
    pos2 = OpenMaya.MObject()
    midpoint = OpenMaya.MObject()
    distance = OpenMaya.MObject()

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)

    def compute(self, plug, data):
        p1 = data.inputValue(MeasureNode.pos1).asDouble3()
        p2 = data.inputValue(MeasureNode.pos2).asDouble3()

        mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2)
        d = ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2) ** .5

        aOutput = data.outputValue(MeasureNode.midpoint)
        aOutput.set3Double(mid[0], mid[1], mid[2])

        bOutput = data.outputValue(MeasureNode.distance)
        bOutput.setFloat(d)
        data.setClean(plug)


def creator():
    return OpenMayaMPx.asMPxPtr(MeasureNode())


def initialize():
    nAttr = OpenMaya.MFnNumericAttribute()
    MeasureNode.midpoint = nAttr.create(
        "midpoint",
        "mid",
        OpenMaya.MFnNumericData.k3Double,
        0.0
    )
    nAttr.setWritable(True)
    nAttr.setStorable(True)
    MeasureNode.addAttribute(MeasureNode.midpoint)

    MeasureNode.distance = nAttr.create(
        "distance",
        "dist",
        OpenMaya.MFnNumericData.kFloat,
        0.0
    )
    nAttr.setWritable(True)
    nAttr.setStorable(True)
    MeasureNode.addAttribute(MeasureNode.distance)

    MeasureNode.pos1 = nAttr.create(
        "pos1",
        "in1",
        OpenMaya.MFnNumericData.k3Double,
        0.0
    )
    MeasureNode.addAttribute(MeasureNode.pos1)
    MeasureNode.attributeAffects(MeasureNode.pos1, MeasureNode.midpoint)
    MeasureNode.attributeAffects(MeasureNode.pos1, MeasureNode.distance)

    MeasureNode.pos2 = nAttr.create(
        "pos2",
        "in2",
        OpenMaya.MFnNumericData.k3Double,
        0.0
    )
    MeasureNode.addAttribute(MeasureNode.pos2)
    MeasureNode.attributeAffects(MeasureNode.pos2, MeasureNode.midpoint)
    MeasureNode.attributeAffects(MeasureNode.pos2, MeasureNode.distance)


def initializePlugin(obj):
    plugin = OpenMayaMPx.MFnPlugin(obj, 'measureMe', '0.1', 'macka')
    try:
        plugin.registerNode(
            'measureMe',
            MeasureNode.kPluginNodeId,
            creator,
            initialize
        )
    except:
        raise RuntimeError, 'uh oh, initialization fail'


def uninitializePlugin(obj):
    plugin = OpenMayaMPx.MFnPlugin(obj)
    try:
        plugin.deregisterNode(MeasureNode.kPluginNodeId)
    except:
        raise RuntimeError, 'oh dear, this node does not want to unload'
