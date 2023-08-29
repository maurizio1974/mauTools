'''----------------------------------------------------------------------

SOME MATRIX UTILITY COOL STUFF

Date = 28/10/2017
User = Maurizio Giglioli
Update =
        28/10/2017 Initial Commit

----------------------------------------------------------------------'''

import maya.cmds as cmds
import maya.OpenMaya as om


def getDagPath(node=None):
    sel = om.MSelectionList()
    sel.add(node)
    d = om.MDagPath()
    sel.getDagPath(0, d)
    return d

def getLocalOffset(parent, child):
    parentWorldMatrix = getDagPath(parent).inclusiveMatrix()
    childWorldMatrix = getDagPath(child).inclusiveMatrix()

    return childWorldMatrix * parentWorldMatrix.inverse()

def matrixBlend(drivers, obj, offset):
    # SOME CHECKS
    if not drivers:
        cmds.confirmDialog(t='Error', m='No parent transforms Passed')
        return
    if not obj:
        cmds.confirmDialog(t='Error', m='No end Transform Passed')
        return
    # MANTAIN OFFSET
    out = []
    if offset == 1:
        for x, p in enumerate(drivers):
            mmo = cmds.createNode('multMatrix', n=p + '_mm')
            localOffset = getLocalOffset(p, obj)
            cmds.setAttr(
                mmo + '.matrixIn[0]',
                [localOffset(i, j) for i in range(4) for j in range(4)],
                type="matrix")
            cmds.connectAttr(p + '.worldMatrix[0]', mmo + '.matrixIn[1]')
            out.append(mmo)
    # CREATE AND CONNECT THE WEIGTH MATRIX
    wt = cmds.createNode('wtAddMatrix', n=obj + '_wt')
    if offset == 0:
        for x, p in enumerate(drivers):
            cmds.connectAttr(p + '.worldMatrix[0]', wt + '.wtMatrix[' + str(x) + '].matrixIn')
            cmds.addAttr(obj, ln=p, at='double', min=0, max=1, dv=1.0 / len(drivers), k=True)
            cmds.connectAttr(obj + '.' + p, wt + '.wtMatrix[' + str(x) + '].weightIn')
    elif offset == 1:
        for x, p in enumerate(out):
            cmds.connectAttr(p + '.matrixSum', wt + '.wtMatrix[' + str(x) + '].matrixIn')
            cmds.addAttr(obj, ln=drivers[x], at='double', min=0, max=1, dv=1.0 / len(drivers), k=True)
            cmds.connectAttr(obj + '.' + drivers[x], wt + '.wtMatrix[' + str(x) + '].weightIn')

    # CONNECT TO A MULTI MATRIX
    mm = cmds.createNode('multMatrix', n=obj + '_mm')
    cmds.connectAttr(wt + '.matrixSum', mm + '.matrixIn[0]')

    # MANTAIN PARENT OFFSET
    above = cmds.listRelatives(obj, p=True)
    if above:
        if offset == 1:
            cmds.connectAttr(above[0] + '.worldInverseMatrix[0]', mm + '.matrixIn[1]')
        elif offset == 0:
            cmds.connectAttr(above[0] + '.parentMatrix[0]', mm + '.matrixIn[1]')

    # DECOMPOSE THE MATRIX
    dm = cmds.createNode('decomposeMatrix', n=obj + '_DM')
    cmds.connectAttr(mm + '.matrixSum', dm + '.inputMatrix')

    # CONNECT THE RESUL
    cmds.connectAttr(dm + '.outputTranslate', obj + '.translate')
    cmds.connectAttr(dm + '.outputRotate', obj + '.rotate')


# drivers = ['locator1', 'locator2', 'locator3', 'locator4']
# obj = 'pSphere1'
# offset = 0
# matrixUtil.matrixBlend(drivers, obj, offset)

def matrixRivet(surface, locs):
    print surface, locs
    sh = cmds.listRelatives(surface, s=True)
    if not cmds.nodeType(sh[0]) == 'nurbsSurface':
        cmds.confirmDialog(t='Error', m='Make sure you pass a Nurbs surface in the first argument')
        return

    # LOOP OVER ALL THE LOCATORS
    for l in locs:
        cpos = cmds.createNode('pointOnSurfaceInfo', n=l + '_cpos')
        dm = cmds.createNode('decomposeMatrix', n=l + '_dm')
        # vp = cmds.createNode('vectorProduct', n=l + '_cp')
        fbf = cmds.createNode('fourByFourMatrix', n=l + '_fbf')

        # GET SURFACE INFO
        cmds.connectAttr(sh[0] + '.worldSpace[0]', cpos + '.inputSurface')

        # CREATE THE MATRIX INFORMATION
        attrs = ['x', 'y', 'z']
        for x, a in enumerate(attrs):
            cmds.connectAttr(cpos + '.position' + a.upper(), fbf + '.in3' + str(x))
        # cmds.connectAttr(cpos + '.positionX', fbf + '.in30')
        # cmds.connectAttr(cpos + '.positionY', fbf + '.in31')
        # cmds.connectAttr(cpos + '.positionZ', fbf + '.in32')

        for x, a in enumerate(attrs):
            cmds.connectAttr(cpos + '.tangentV' + a, fbf + '.in1' + str(x))
        # cmds.connectAttr(cpos + '.tangentVx', fbf + '.in10')
        # cmds.connectAttr(cpos + '.tangentVy', fbf + '.in11')
        # cmds.connectAttr(cpos + '.tangentVz', fbf + '.in12')

        for x, a in enumerate(attrs):
            cmds.connectAttr(cpos + '.normal' + a.upper(), fbf + '.in0' + str(x))
        # cmds.connectAttr(cpos + '.normalX', fbf + '.in00')
        # cmds.connectAttr(cpos + '.normalY', fbf + '.in01')
        # cmds.connectAttr(cpos + '.normalZ', fbf + '.in02')

        # # VECTOR PRODUCT, NORMAL AND TANGENT
        # cmds.connectAttr(cpos + '.normal', vp + '.input1')
        # cmds.connectAttr(cpos + '.tangentV', vp + '.input2')
        # cmds.connectAttr(vp + '.outputX', fbf + '.in20')
        # cmds.connectAttr(vp + '.outputY', fbf + '.in21')
        # cmds.connectAttr(vp + '.outputZ', fbf + '.in22')

        # DECOMPOSE THE MATRIX
        cmds.connectAttr(fbf + '.output', dm + '.inputMatrix')

        # ADD CONTROLLING ATTRIBUTES
        attrs = ['parameterU', 'parameterV']
        for a in attrs:
            cmds.addAttr(l, ln=a, at='double', min=0, max=1, dv=0.5, k=True)
            cmds.connectAttr(l + '.' + a, cpos + '.' + a)

        # GET FINAL RESULT
        cmds.connectAttr(dm + '.outputTranslate', l + '.t')
        cmds.connectAttr(dm + '.outputRotate', l + '.r')

# surface = 'nurbsPlane2'
# obj = ['locator2', 'locator3']
# matrixUtil.matrixRivet(surface, obj)

def mCentroid(obj=None):
    out = {}
    if not obj:
        obj = cmds.ls(sl=True)
    if not obj:
        cmds.confirmDialog(t='error', m='Please select a mesh object')
        return
    for o in obj:
        if cmds.nodeType(cmds.listRelatives(o, s=True)[0]) == 'mesh':
            geo, p = [], [[], [], []]
            vtxs = cmds.polyEvaluate(o, v=True)
            for x in range(vtxs):
                geo.append(o + '.vtx[' + str(x) + ']')
            for i in geo:
                po = cmds.xform(i, q=True, ws=True, t=True)
                p[0].append(po[0])
                p[1].append(po[1])
                p[2].append(po[2])

            length = len(p[0])
            centroid = ([
                sum(p[0]) / length,
                sum(p[1]) / length,
                sum(p[2]) / length])
            loc = cmds.spaceLocator()
            cmds.xform(loc[0], t=(centroid[0], centroid[1], centroid[2]))
            out[loc[0]] = centroid
        else:
            print 'Skipped {0}'.format(o)
    return out

# AIM MATRIX VECTOR
def createVctorDir():
    md = cmds.createNode('multiplyDivide', n='vecto_MD')
    cmds.setAttr(md + '.input1Y', -2)
    vp1 = cmds.createNode('vectorProduct', n='vecto1_VP')
    cmds.setAttr(vp1 + '.operation', 4)
    cmds.setAttr(vp1 + '.normalizeOutput', 1)
    pma = cmds.createNode('plusMinusAverage', n='vecto_PMA')
    cmds.setAttr(pma + '.operation', 2)
    vp2 = cmds.createNode('vectorProduct', n='vecto2_CP')
    cmds.setAttr(vp2 + '.operation', 0)
    cmds.setAttr(vp2 + '.normalizeOutput', 1)
    dm = cmds.createNode('decomposeMatrix', n='vecto_DM')
    sl = cmds.spaceLocator(n='director_LOC')
    slR = cmds.spaceLocator(n='director_reference_LOC')


    cmds.connectAttr(slR[0] + '.worldMatrix[0]', vp1 + '.matrix')
    cmds.connectAttr(slR[0] + '.worldMatrix[0]', dm + '.inputMatrix')
    cmds.connectAttr(md + '.output', vp1 + '.input1')
    cmds.connectAttr(dm + '.outputTranslate', pma + '.input3D[0]')
    cmds.connectAttr(vp1 + '.output', pma + '.input3D[1]')
    cmds.connectAttr(pma + '.output3D', vp2 + '.input1')
    cmds.connectAttr(vp2 + '.output', sl[0] + '.r')
