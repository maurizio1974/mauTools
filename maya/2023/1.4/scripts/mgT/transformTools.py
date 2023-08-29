
import math
import maya.cmds as mc

# MIRROR WORLD SPACE POSITION OF SELECTED NODES


def mirrorTrans(dir, t, r):
    nodeList = mc.ls(selection=True)
    if len(nodeList) == 1:
        newLoc = mc.spaceLocator(n=(nodeList[0] + "_FLIP"))
        mc.select(nodeList[0], newLoc)
        nodeList = mc.ls(sl=True)
    if len(nodeList) % 2 == 1:
        raise Exception

    half = len(nodeList) / 2
    counter = 0
    while counter < half:
        sourceNode = nodeList[counter]
        destNode = nodeList[half + counter]
        counter = counter + 1
        sourcePos = mc.pointPosition((sourceNode + ".rotatePivot"), world=True)
        sourceRot = mc.xform(sourceNode, q=True, ws=True, ro=True)
        if dir == 0:
            if t == 1:
                mc.move((sourcePos[0] * -1), sourcePos[1], sourcePos[2], destNode,
                        absolute=True, worldSpace=True, rotatePivotRelative=True)
            if r == 1:
                mc.xform(destNode, ws=True, ro=(
                    sourceRot[0], (sourceRot[1] * -1), (sourceRot[2] * -1)))
            print("Finished World XY Mirror")
            info = [newLoc[0], (sourcePos[0] * -1), sourcePos[1], sourcePos[2]]
        if dir == 1:
            if t == 1:
                mc.move(sourcePos[0], (sourcePos[1] * -1), sourcePos[2], destNode,
                        absolute=True, worldSpace=True, rotatePivotRelative=True)
            if r == 1:
                mc.xform(destNode, ws=True, ro=(
                    sourceRot[0], (sourceRot[1] * -1), ((sourceRot[2] * -1) + 180)))
            print("Finished World XZ Mirror")
            info = [newLoc[0], sourcePos[0], (sourcePos[1] * -1), sourcePos[2]]
        if dir == 2:
            if t == 1:
                mc.move(sourcePos[0], sourcePos[1], (sourcePos[2] * -1), destNode,
                        absolute=True, worldSpace=True, rotatePivotRelative=True)
            if r == 1:
                mc.xform(destNode, ws=True, ro=(
                    (sourceRot[0] * -1), (sourceRot[1] * -1), sourceRot[2]))
            print("Finished World YZ Mirror")
            info = [newLoc[0], sourcePos[0], sourcePos[1], (sourcePos[2] * -1)]

    return info


# FIND AVERAGE POSITION OF MULTIPLE TRASNFORMS
def average(*args):
    # find the average of any number of passed in values
    val = 0
    # print args
    for a in args:
        val += a
    return val / len(args)


def middleLoc():
    avgT = list(map(average, *[mc.pointPosition(p + ".rotatePivot",
                                           world=True) for p in mc.ls(selection=True)]))
    avgR = list(map(average, *[mc.xform(p, q=True, ro=True, ws=True)
                          for p in mc.ls(selection=True)]))
    loc = mc.spaceLocator(n='centerLoc')
    mc.xform(loc, ws=True, t=(avgT[0], avgT[1], avgT[2]))
    mc.xform(loc, ws=True, ro=(avgR[0], avgR[1], avgR[2]))

# RECREATE PARENTCONSTRAINT WITH NODES IN MAYA


def mParentConstraint():
    import maya.api.OpenMaya as om
    sel = mc.ls(sl=True)

    mStart = om.MMatrix(mc.getAttr(sel[0] + '.wm[0]'))
    mEnd = om.MMatrix(mc.getAttr(sel[1] + '.wm[0]'))
    mOutputMatrix = om.MTransformationMatrix(
        mEnd * mStart.inverse()).asMatrix()

    mMatrix = mc.createNode('multMatrix')
    dMatrix = mc.createNode('decomposeMatrix')

    mc.connectAttr((mMatrix + '.matrixSum'), (dMatrix + '.inputMatrix'))
    mc.setAttr(mMatrix + '.i[0]', mOutputMatrix, type='matrix')
    mc.connectAttr(sel[0] + '.matrix', (mMatrix + '.matrixIn[1]'))
    mc.connectAttr((dMatrix + '.outputTranslate'), sel[1] + '.translate')
    mc.connectAttr((dMatrix + '.outputRotate'), sel[1] + '.rotate')


'''
def cMau:
        sel =cmds.ls(loc[1], fl = True, sl = True)
        x,y,z = [], [], []
        xSum,ySum,zSum=0,0,0
        pos, endPos = [], []
        u = len(sel)
        for s in sel:
                pos =cmds.pointPosition(s)
                x.append(pos[0])
                y.append(pos[1])
                z.append(pos[2])

        loc =cmds.spaceLocator("centroid_NULL");
        for $x in range(len(x)):
                xSum += x[a]
                ySum += y[a]
                zSum += z[a]
        endPos[0] = xSum/u;
        endPos[1] = ySum/u;
        endPos[2] = zSum/u;

        cmds.xform(loc[0], ws=True,t=True, endPos[0] endPos[1] endPos[2])
        print 'Centroid of '+loc[0]+' is...\nX: endPos[0]\nY: endPos[1]\nZ: endPos[2]'
'''


def _addParentConstTarget(driver, driven, parentConst, wtsIndex):
    # calculate offset - this same as creating parent constraint with maintain offset
    trans = _getTransformOffset(
        driver, driven, 'translate', cmds.getAttr('%s.rotateOrder' % driven))
    rotation = _getTransformOffset(
        driver, driven, 'rotate', cmds.getAttr('%s.rotateOrder' % driven))
    # connect required target index inputs
    cmds.addAttr(parentConst, ln='%sW%s' % (driver, wtsIndex),
                 sn='w%s' % wtsIndex, at='double', min=0, max=1, dv=1, k=1)
    cmds.connectAttr('%s.parentMatrix[0]' % driver, '%s.target[%s].targetParentMatrix' % (
        parentConst, wtsIndex))
    cmds.connectAttr('%s.scale' % driver,
                     '%s.target[%s].targetScale' % (parentConst, wtsIndex))
    cmds.connectAttr('%s.rotateOrder' % driver,
                     '%s.target[%s].targetRotateOrder' % (parentConst, wtsIndex))
    cmds.connectAttr('%s.rotate' % driver,
                     '%s.target[%s].targetRotate' % (parentConst, wtsIndex))
    cmds.connectAttr('%s.rotatePivotTranslate' % driver,
                     '%s.target[%s].targetRotateTranslate' % (parentConst, wtsIndex))
    cmds.connectAttr('%s.rotatePivot' % driver,
                     '%s.target[%s].targetRotatePivot' % (parentConst, wtsIndex))
    cmds.connectAttr('%s.translate' % driver,
                     '%s.target[%s].targetTranslate' % (parentConst, wtsIndex))
    cmds.connectAttr('%s.%sW%s' % (parentConst, driver, wtsIndex),
                     '%s.target[%s].targetWeight' % (parentConst, wtsIndex))
    # setting offset value
    cmds.setAttr('%s.target[%s].targetOffsetTranslateX' %
                 (parentConst, wtsIndex), trans[0])
    cmds.setAttr('%s.target[%s].targetOffsetTranslateY' %
                 (parentConst, wtsIndex), trans[1])
    cmds.setAttr('%s.target[%s].targetOffsetTranslateZ' %
                 (parentConst, wtsIndex), trans[2])
    cmds.setAttr('%s.target[%s].targetOffsetRotateX' %
                 (parentConst, wtsIndex), rotation[0])
    cmds.setAttr('%s.target[%s].targetOffsetRotateY' %
                 (parentConst, wtsIndex), rotation[1])
    cmds.setAttr('%s.target[%s].targetOffsetRotateZ' %
                 (parentConst, wtsIndex), rotation[2])


def _getTransformOffset(startObj, endObj, type, rotateOrder):
    mStart = om.MMatrix()
    mEnd = om.MMatrix()
    start = cmds.getAttr('%s.wm[0]' % startObj)
    end = cmds.getAttr('%s.wm[0]' % endObj)
    om.MScriptUtil().createMatrixFromList(start, mStart)
    om.MScriptUtil().createMatrixFromList(end, mEnd)
    mOutputMatrix = om.MTransformationMatrix(mEnd * mStart.inverse())
    if type == 'translate':
        vTrans = om.MVector(mOutputMatrix.getTranslation(om.MSpace.kTransform))
        return vTrans.x, vTrans.y, vTrans.z
    if type == 'rotate':
        vRotation = om.MEulerRotation(
            mOutputMatrix.eulerRotation().reorder(rotateOrder))
        return math.degrees(vRotation.x), math.degrees(vRotation.y), math.degrees(vRotation.z)
