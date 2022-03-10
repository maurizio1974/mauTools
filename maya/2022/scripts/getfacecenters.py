# script that returns the center point of selected polygon faces. 
# owen burgess 2009

import maya.OpenMaya as OpenMaya
import math

def faceCenter():

    faceCenter = []

    selection = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(selection)
    print ("Number of objects in selection: %s " % selection.length())

    iter = OpenMaya.MItSelectionList (selection, OpenMaya.MFn.kMeshPolygonComponent)

    while not iter.isDone():
        status = OpenMaya.MStatus
        dagPath = OpenMaya.MDagPath()
        component = OpenMaya.MObject()

        iter.getDagPath(dagPath, component)

        polyIter = OpenMaya.MItMeshPolygon(dagPath, component)

        while not polyIter.isDone():
            i = 0
            i = polyIter.index()
            faceInfo = [0]
            faceInfo[0] = ("The center point of face %s is:" %i)
            faceCenter+=faceInfo

            center = OpenMaya.MPoint
            center = polyIter.center(OpenMaya.MSpace.kWorld)
            point = [0.0,0.0,0.0]
            point[0] = center.x
            point[1] = center.y
            point[2] = center.z
            faceCenter += point
            
            polyIter.next()
            
        iter.next()
        
    return faceCenter
# end of script
