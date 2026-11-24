'''----------------------------------------------------------------------

SOME MATRIX UTILITY COOL STUFF

Date = 28/10/2017
User = Maurizio Giglioli
Update =
        19/01/2026 Code Clean-up
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
    if len(drivers) == 1:
        cmds.connectAttr(f'{drivers[0]}.worldMatrix', f'{obj}.offsetParentMatrix')
        if offset == 0:
            # mat = cmds.xform(drivers[0], q=True, m=True)
            # cmds.xform(obj, m=mat)
            pos = cmds.xform(drivers[0], q=True, ws=True, t=True)
            rot = cmds.xform(drivers[0], q=True, ws=True, ro=True)
            sca = cmds.xform(drivers[0], q=True, ws=True, s=True)
            cmds.xform(obj, ws=True, t=(pos[0], pos[1], pos[2]))
            cmds.xform(obj, ro=(rot[0], rot[1], rot[2]))
            cmds.xform(obj, s=(sca[0], sca[1], sca[2]))
    else:
        if offset == 1:
            for x, p in enumerate(drivers):
                mmo = cmds.createNode('multMatrix', n=p + '_mm')
                localOffset = getLocalOffset(p, obj)
                cmds.setAttr(
                    mmo + '.matrixIn[0]',
                    [localOffset(i, j) for i in range(4) for j in range(4)],
                    type="matrix")
                cmds.connectAttr(f'{p}.worldMatrix[0]', f'{mmo}.matrixIn[1]')
                out.append(mmo)
        # CREATE AND CONNECT THE WEIGTH MATRIX
        wt = cmds.createNode('wtAddMatrix', n=f'{obj}_wt')
        if offset == 0:
            for x, p in enumerate(drivers):
                cmds.connectAttr(f'{p}.worldMatrix[0]', f'{wt}.wtMatrix[{str(x)}].matrixIn')
                cmds.addAttr(obj, ln=p, at='double', min=0, max=1, dv=1.0 / len(drivers), k=True)
                cmds.connectAttr(f'{obj}.{p}', f'{wt}.wtMatrix[{str(x)}].weightIn')
        elif offset == 1:
            for x, p in enumerate(out):
                cmds.connectAttr(f'{p}.matrixSum', f'{wt}.wtMatrix[{str(x)}].matrixIn')
                cmds.addAttr(obj, ln=drivers[x], at='double', min=0, max=1, dv=1.0 / len(drivers), k=True)
                cmds.connectAttr(f'{obj}.{drivers[x]}', f'{wt}.wtMatrix[{str(x)}].weightIn')

        # CONNECT TO A MULTI MATRIX
        mm = cmds.createNode('multMatrix', n=f'{obj}_mm')
        cmds.connectAttr(f'{wt}.matrixSum', f'{mm}.matrixIn[0]')

        # MANTAIN PARENT OFFSET
        above = cmds.listRelatives(obj, p=True)
        if above:
            if offset == 1:
                cmds.connectAttr(f'{above[0]}.worldInverseMatrix[0]', f'{mm}.matrixIn[1]')
            elif offset == 0:
                cmds.connectAttr(f'{above[0]}.parentMatrix[0]', f'{mm}.matrixIn[1]')

        # DECOMPOSE THE MATRIX
        dm = cmds.createNode('decomposeMatrix', n=f'{obj}_DM')
        cmds.connectAttr(f'{mm}.matrixSum', f'{dm}.inputMatrix')

        # CONNECT THE RESUL
        for ax in ['X', 'Y', 'Z']:
            cmds.connectAttr(f'{dm}.outputTranslate{ax}', f'{obj}.translate{ax}')
            cmds.connectAttr(f'{dm}.outputRotate{ax}', f'{obj}.rotate{ax}')


# drivers = ['locator1', 'locator2', 'locator3', 'locator4']
# obj = 'pSphere1'
# offset = 0
# matrixUtil.matrixBlend(drivers, obj, offset)

def matrixRivet(surface, locs):
    print(surface, locs)
    sh = cmds.listRelatives(surface, s=True)
    if not cmds.nodeType(sh[0]) == 'nurbsSurface':
        cmds.confirmDialog(t='Error', m='Make sure you pass a Nurbs surface in the first argument')
        return

    # LOOP OVER ALL THE LOCATORS
    for l in locs:
        cpos = cmds.createNode('pointOnSurfaceInfo', n=l + '_cpos')
        dm = cmds.createNode('decomposeMatrix', n=l + '_dm')
        fbf = cmds.createNode('fourByFourMatrix', n=l + '_fbf')

        # GET SURFACE INFO
        cmds.connectAttr(sh[0] + '.worldSpace[0]', f'{cpos}.inputSurface')

        # CREATE THE MATRIX INFORMATION
        attrs = ['x', 'y', 'z']
        for x, a in enumerate(attrs):
            cmds.connectAttr(f'{cpos}.position' + a.upper(), f'{fbf}.in3' + str(x))

        for x, a in enumerate(attrs):
            cmds.connectAttr(f'{cpos}.tangentV' + a, f'{fbf}.in1' + str(x))

        for x, a in enumerate(attrs):
            cmds.connectAttr(f'{cpos}.normal' + a.upper(), f'{fbf}.in0' + str(x))

        # DECOMPOSE THE MATRIX
        cmds.connectAttr(f'{fbf}.output', f'{dm}.inputMatrix')

        # ADD CONTROLLING ATTRIBUTES
        attrs = ['parameterU', 'parameterV']
        for a in attrs:
            cmds.addAttr(l, ln=a, at='double', min=0, max=1, dv=0.5, k=True)
            cmds.connectAttr(f'{l}.{a}', f'{cpos}.{a}')

        # GET FINAL RESULT
        cmds.connectAttr(f'{dm}.outputTranslate', f'{l}.t')
        cmds.connectAttr(f'{dm}.outputRotate', f'{l}.r')

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
                geo.append(f'{o}.vtx[{str(x)}]')
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
            print(f'Skipped {o}')
    return out

# AIM MATRIX VECTOR
def createVctorDir():
    md = cmds.createNode('multiplyDivide', n='vecto_MD')
    cmds.setAttr(f'{md}.input1Y', -2)
    vp1 = cmds.createNode('vectorProduct', n='vecto1_VP')
    cmds.setAttr(f'{vp1}.operation', 4)
    cmds.setAttr(f'{vp1}.normalizeOutput', 1)
    pma = cmds.createNode('plusMinusAverage', n='vecto_PMA')
    cmds.setAttr(f'{pma}.operation', 2)
    vp2 = cmds.createNode('vectorProduct', n='vecto2_CP')
    cmds.setAttr(f'{vp2}.operation', 0)
    cmds.setAttr(f'{vp2}.normalizeOutput', 1)
    dm = cmds.createNode('decomposeMatrix', n='vecto_DM')
    sl = cmds.spaceLocator(n='director_LOC')
    slR = cmds.spaceLocator(n='director_reference_LOC')


    cmds.connectAttr(slR[0] + '.worldMatrix[0]', f'{vp1}.matrix')
    cmds.connectAttr(slR[0] + '.worldMatrix[0]', f'{dm}.inputMatrix')
    cmds.connectAttr(f'{md}.output', f'{vp1}.input1')
    cmds.connectAttr(f'{dm}.outputTranslate', f'{pma}.input3D[0]')
    cmds.connectAttr(f'{vp1}.output', f'{pma}.input3D[1]')
    cmds.connectAttr(f'{pma}.output3D', f'{vp2}.input1')
    cmds.connectAttr(f'{vp2}.output', f'{sl[0]}.r')
