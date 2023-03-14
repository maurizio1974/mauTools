# Python code
# matrixutils.py

import maya.cmds as mc
import maya.OpenMaya as om
import math
import pprint as pp

def listToMMatrix(mList):
    """
    Convert a list of 16 floats into a MMatrix object
    Mainly a helper for getMMatrix()
    """
    if len(mList) != 16:
        raise Exception("Argument 'mList' needs to have 16 float elements")
    m = om.MMatrix()
    om.MScriptUtil.createMatrixFromList(mList, m)
    return m

def mMatrixToList(matrix):
    """
    Convert a MMatrix object into a list of 16 floats.
    Mainly a helper for matrixXform()
    """
    return [matrix(i,j) for i in range(4) for j in range(4)]

def getMMatrix(node, matrixType):
    """
    Get matrix data from a node, and return as MMatrix object.
    """
    good = ["matrix", "inverseMatrix", "worldMatrix", "worldInverseMatrix",
            "parentMatrix", "parentInverseMatrix", "xformMatrix"]
    if matrixType not in good:
        raise Exception("Argument 'matrixType' is an invalid matrix attr type."+
                        "  Please choose from: " + ' '.join(good))
    return listToMMatrix(mc.getAttr(node+"."+matrixType))

def matrixXform(node, matrix, spaceType):
    """
    Transform a Maya DAG (transform, joint) object based on a given matrix value,
    via the mel 'xform' command.

    matrix : either a maya.OpenMaya.MMatrix object, or a list with 16 entries.
    spaceType :  either 'worldSpace' or 'objectSpace'
    """
    mList = None
    if type(matrix) is type(om.MMatrix()):
        mList = mMatrixToList(matrix)
    elif type(matrix) is type(list()) and len(matrix) == 16:
        mList = matrix
    else:
        raise TypeError("Arg 'matrix' either needs to be a maya.OpenMaya.MMatrix object, or list with 16 entries")

    if(spaceType == "worldSpace"):
        mc.xform(node, worldSpace=True, matrix=mList)
    elif(spaceType == "objectSpace"):
        mc.xform(node, objectSpace=True, matrix=mList)
    else:
        raise ValueError("spaceType arg is neither 'worldSpace' or 'objectSpace', passed value is '%s'"%spaceType)
        
''' -------------------------------------------------   VECTORS   -------------------------------------------------- '''

# VECTOR DOT PRODUCT BETWEEN TWO VECTORS       
def vctrDot(a,b):
    dot = a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
    return dot

# MANHATTEN DISTANCE
def vctrLength(a):
    mag = a[0]*a[0] + a[1]*a[1] + a[2]*a[2]
    return mag
    
# MAGNITUDE (ABSOLUTE VALUED) LENGTH OF A VECTOR
def vctrMag(a):
    length = vctrLength(a)
    mag = math.sqrt(length)
    return mag

# ADD TWO VECTORS
def vctrAdd(a,b):
    x = a[0] + b[0]
    y = a[1] + b[1]
    z = a[2] + b[2]
    return [x, y, z]

# SUBTRACT TWO VECTORS
def vctrSub(a,b):
    x = a[0] - b[0]
    y = a[1] - b[1]
    z = a[2] - b[2]
    return [x, y, z]
