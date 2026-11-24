'''----------------------------------------------------------------------

OUTPOST MATRIX UTILITY

Date = 26/01/2019
User = Maurizio Giglioli
Update =
        26/01/2019 Initial Commit

----------------------------------------------------------------------'''

import math
import pprint as pp
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

# FIND OPPOSITE EDGES OF A QUAD POLY FACE
def findEdges():
    sel = cmds.ls(sl=True)
    cmds.select(sel[0], r=True)
    edges = cmds.polyListComponentConversion(sel[0], ff=True, te=True)
    cmds.select(edges, r=True)
    sel = cmds.ls(sl=True, fl=True)
    master, exit = [], []
    for x, s in enumerate(sel):
        out = []
        vtx = cmds.polyListComponentConversion(sel[x], fe=True, tv=True)
        cmds.select(vtx, r=True)
        vtx = cmds.ls(sl=True, fl=True)
        cmds.select(cl=True)
        master = cmds.polyListComponentConversion(sel[0], fe=True, tv=True)
        cmds.select(master, r=True)
        master = cmds.ls(sl=True, fl=True)
        cmds.select(cl=True)
        if x != 0:
            if not set(master).intersection(vtx):
                exit = s

    # cmds.select(sel[0], exit, r=True)
    return sel[0], exit

# MAKE A PARENTCONTRAINT WITH MATRIXES BLENDABLE
def matrixBlend(offset):
    drivers = cmds.ls(sl=True)
    # SOME CHECKS
    if not drivers:
        cmds.confirmDialog(t='Error', m='No transforms selected')
        return
    if len(drivers) < 2:
        cmds.confirmDialog(t='Error', m='Please select at least two transforms')
        return
    obj = drivers[-1]
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

# MAKE A RIVET WITH MATRIX
def matrixSurface(offset):
    sel = cmds.ls(sl=True)
    # SOME CHECKS
    if not sel:
        cmds.confirmDialog(t='Error', m='Please select a transform at least and one nurbSurface last')
        return
    if len(sel) < 2:
        cmds.confirmDialog(t='Error', m='Please select a transform at least and one nurbSurface last')
        return
    locs = sel[:-1]
    surface = sel[-1]
    # CHECK NURBSURFACE
    sh = cmds.listRelatives(surface, s=True)
    if sh:
        if not cmds.nodeType(sh[0]) == 'nurbsSurface':
            cmds.confirmDialog(t='Error', m='Make sure you select a Nurbs surface at the end')
            return
    else:
        cmds.confirmDialog(t='Error', m='Make sure you select a Nurbs surface at the end')
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

        for x, a in enumerate(attrs):
            cmds.connectAttr(cpos + '.tangentV' + a, fbf + '.in1' + str(x))

        for x, a in enumerate(attrs):
            cmds.connectAttr(cpos + '.normal' + a.upper(), fbf + '.in0' + str(x))

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
            if not cmds.attributeQuery(a, n=l, ex=True):
                cmds.addAttr(l, ln=a, at='double', min=0, dv=0, k=True)
            cmds.connectAttr(l + '.' + a, cpos + '.' + a, f=True)

        # GET UV VALUE ON THE SURFACE
        pos = cmds.xform(l, q=True, ws=True, t=True)
        cps = cmds.createNode('closestPointOnSurface')
        cmds.connectAttr(sh[0] + '.worldSpace[0]', cps + '.inputSurface')
        cmds.setAttr(cps + '.inPosition', pos[0], pos[1], pos[2])
        u = cmds.getAttr(cps + '.parameterU')
        v = cmds.getAttr(cps + '.parameterV')
        cmds.setAttr(l + '.parameterU', u)
        cmds.setAttr(l + '.parameterV', v)
        cmds.delete(cps)
        print(u, v)

        # PLUGIN FINAL RESULT
        if offset == 0:
            cmds.connectAttr(dm + '.outputTranslate', l + '.t')
            cmds.connectAttr(dm + '.outputRotate', l + '.r')
        elif offset == 1:
            loc = cmds.group(em=True, n=l + '_offset')
            cmds.connectAttr(dm + '.outputTranslate', loc + '.t')
            cmds.connectAttr(dm + '.outputRotate', loc + '.r')
            cmds.parent(l, loc)

# surface = 'nurbsPlane2'
# obj = ['locator2', 'locator3']
# matrixUtil.matrixRivet(surface, obj)

# FOLLICLE FROM A NURBS SURFACE POINT SELECTION
def rivFolSP():
    sel = cmds.ls(sl=True)
    for s in sel:
        if '.uv[' not in s:
            cmds.warning('Please Select a surface point on a nurb surface, skipping this selection:' + s)
        else:
            u = float(s.split('.uv[')[-1].split(']')[0])
            v = float(s.split('.uv[')[-1].split('[')[-1].replace(']', ''))
            surfT = s.split('.uv[')[0]
            surf = cmds.listRelatives(surfT, s=True, ni=True)[0]
            # NORMALIZE UV VALUES
            rangeU = cmds.getAttr(surf + '.minMaxRangeU')[0][1]
            rangeV = cmds.getAttr(surf + '.minMaxRangeV')[0][1]
            un = u / rangeU
            vn = v / rangeV
            # MAKE FOLLICLE
            folN = cmds.createNode('follicle')
            folT = cmds.listRelatives(folN, p=True)
            cmds.connectAttr(surf + '.worldSpace', folN + '.inputSurface')
            # cmds.connectAttr(surfT + '.worldMatrix[0]', folN + '.inputWorldMatrix')
            # FINAL CONNECTIONS
            cmds.addAttr(
                folT[0], ln='U', at='double', k=True, min=0, max=1, dv=un)
            cmds.addAttr(
                folT[0], ln='V', at='double', k=True, min=0, max=1, dv=vn)
            cmds.connectAttr(folT[0] + '.U', folN + '.parameterU')
            cmds.connectAttr(folT[0] + '.V', folN + '.parameterV')
            cmds.connectAttr(folN + '.outTranslate', folT[0] + '.translate')
            cmds.connectAttr(folN + '.outRotate', folT[0] + '.rotate')
            return(folT[0])

def matrixSurfaceSP():
    locs, uvs = [], []
    sel = cmds.ls(sl=True)
    # SOME CHECKS
    if not sel:
        cmds.confirmDialog(t='Error', m='Please select a surface point in on the surface')
        return
    if '.uv' not in sel[0]:
        cmds.confirmDialog(t='Error', m='Please select a surface point in on the Nurb surface')
        return
    # CHECK NURBSURFACE
    surf = sel[0].split('.')[0]
    sh = cmds.listRelatives(surf, s=True)
    if not sh:
        cmds.confirmDialog(t='Error', m='Please select a surface point in on the surface')
        return
    if not cmds.nodeType(sh[0]) == 'nurbsSurface':
        cmds.confirmDialog(t='Error', m='Please select a surface point in on the surface')
        return
    surface = sel[0].split('.')[0]
    uvs = sel[0].split('uv')[-1].replace('[', '').split(']')[0:2]
    loc = cmds.spaceLocator(n='nurbs_rivet')[0]
    # START THE SETUP
    cpos = cmds.createNode('pointOnSurfaceInfo', n=loc + '_cpos')
    dm = cmds.createNode('decomposeMatrix', n=loc + '_dm')
    fbf = cmds.createNode('fourByFourMatrix', n=loc + '_fbf')
    # GET SURFACE INFO
    cmds.connectAttr(sh[0] + '.worldSpace[0]', cpos + '.inputSurface')
    # CREATE THE MATRIX INFORMATION
    attrs = ['x', 'y', 'z']
    for x, a in enumerate(attrs):
        cmds.connectAttr(cpos + '.position' + a.upper(), fbf + '.in3' + str(x))
    for x, a in enumerate(attrs):
        cmds.connectAttr(cpos + '.tangentV' + a, fbf + '.in1' + str(x))
    for x, a in enumerate(attrs):
        cmds.connectAttr(cpos + '.normal' + a.upper(), fbf + '.in0' + str(x))
    # DECOMPOSE THE MATRIX
    cmds.connectAttr(fbf + '.output', dm + '.inputMatrix')
    # ADD CONTROLLING ATTRIBUTES
    attrs = {'parameterU': uvs[0], 'parameterV': uvs[1]}
    for a in list(attrs.keys()):
        cmds.addAttr(l, ln=a, at='double', min=0, dv=float(attrs[a]), k=True)
        cmds.connectAttr(l + '.' + a, cpos + '.' + a)
    # GET FINAL RESULT
    cmds.connectAttr(dm + '.outputTranslate', loc + '.t')
    cmds.connectAttr(dm + '.outputRotate', loc + '.r')

# CALCULATE CENTROID OF AN OBJECT
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
            print('Skipped {0}'.format(o))
    return out

# AIM MATRIX VECTOR
def createVctorDir_old():
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
    sl = cmds.spaceLocator(n='director_loc')
    slR = cmds.spaceLocator(n='director_reference_loc')


    cmds.connectAttr(slR[0] + '.worldMatrix[0]', vp1 + '.matrix')
    cmds.connectAttr(slR[0] + '.worldMatrix[0]', dm + '.inputMatrix')
    cmds.connectAttr(md + '.output', vp1 + '.input1')
    cmds.connectAttr(dm + '.outputTranslate', pma + '.input3D[0]')
    cmds.connectAttr(vp1 + '.output', pma + '.input3D[1]')
    cmds.connectAttr(pma + '.output3D', vp2 + '.input1')
    cmds.connectAttr(vp2 + '.output', sl[0] + '.r')

def createVctorDir():
    ctrl = cmds.curve(
        d=1, p=[
            (0.0, 2.227629192219638e-16, -1.003235), (0.668823, 0.0, 0.0),
            (0.334412, 0.0, 0.0), (0.334412, -3.7127190211094783e-17, 0.167206),
            (0.334412, -1.1138134858867943e-16, 0.501617), (0.334412, -2.227629192219638e-16, 1.003235),
            (-0.334412, -2.227629192219638e-16, 1.003235), (-0.334412, -1.1138134858867943e-16, 0.501617),
            (-0.334412, -3.7127190211094783e-17, 0.167206), (-0.334412, 0.0, 0.0), (-0.668823, 0.0, 0.0),
            (0.0, 2.227629192219638e-16, -1.003235)
            ],
        k=[0,1,2,3,4,5,6,7,8,9,10,11],
        n='directionalVector_ctrl')

    vp = cmds.createNode('vectorProduct', n='directional_vp')
    cmds.connectAttr(ctrl + '.worldMatrix', vp + '.matrix', f=True)
    cmds.setAttr(vp + '.input1Z', -1)
    cmds.setAttr(vp + '.operation', 3)
    cmds.addAttr(ctrl, ln='vectorDir', at='double3',)
    cmds.addAttr(ctrl, ln='vectorDirX', at='double', p='vectorDir', k=True, dv=0)
    cmds.addAttr(ctrl, ln='vectorDirY', at='double', p='vectorDir', k=True, dv=0)
    cmds.addAttr(ctrl, ln='vectorDirZ', at='double', p='vectorDir', k=True, dv=0)
    cmds.connectAttr(vp + '.output', ctrl + '.vectorDir', f=True)

''' -------------------------------------------------   MATRIX   -------------------------------------------------- '''

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
    return listToMMatrix(mc.getAttr(node + "." + matrixType))

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

''' --------------------------------------------------  RIVETS ------------------------------------------------------ '''
def mRivet():
    list = cmds.filterExpand(sm=32)
    if not list:
        cmds.confirmDialog(t='Error', m="Select a pair number of edges")
        return
    nameObject = list[0].split('.')
    e1 = list[0].split('[')[1].split(']')
    e2 = list[1].split('[')[1].split(']')

    nameCFME1 = cmds.createNode(
        'curveFromMeshEdge',
        n='rCFME1'
    )
    cmds.setAttr(nameCFME1 + '.ihi', 1)
    cmds.setAttr(nameCFME1 + '.ei[0]', int(e1[0]))
    nameCFME2 = cmds.createNode(
        'curveFromMeshEdge',
        n='rCFME2'
    )
    cmds.setAttr(nameCFME2 + '.ihi', 1)
    cmds.setAttr(nameCFME2 + '.ei[0]', int(e2[0]))
    nameLoft = cmds.createNode('loft', n='rivetLoft1')
    cmds.setAttr(nameLoft + '.ic', s=2)
    cmds.setAttr(nameLoft + '.u', 1)
    cmds.setAttr(nameLoft + '.rsn', 1)

    namePOSI = cmds.createNode(
        'pointOnSurfaceInfo',
        n='rPOSI1'
    )
    cmds.setAttr(namePOSI + '.turnOnPercentage', 1)
    cmds.setAttr(namePOSI + '.parameterU', 0.5)
    cmds.setAttr(namePOSI + '.parameterV', 0.5)

    cmds.connectAttr(nameLoft + '.os', namePOSI + '.is', f=True)
    cmds.connectAttr(nameCFME1 + '.oc', nameLoft + '.ic[0]')
    cmds.connectAttr(nameCFME2 + '.oc', nameLoft + '.ic[1]')

    cmds.connectAttr(nameObject[0] + '.w', nameCFME1 + '.im')
    cmds.connectAttr(nameObject[0] + '.w', nameCFME2 + '.im')

    nameLocator = cmds.createNode('transform', n='mRivet1')
    cmds.createNode('locator', n=nameLocator + 'Shape', p=nameLocator)
    cmds.addAttr(nameLocator, ln='U', at='double', k=True, min=0, max=1)
    cmds.addAttr(nameLocator, ln='V', at='double', k=True, min=0, max=1)
    cmds.connectAttr(nameLocator + '.U', namePOSI + '.parameterU')
    cmds.connectAttr(nameLocator + '.V', namePOSI + '.parameterV')
    cmds.setAttr(nameLocator + '.U', 0.5)
    cmds.setAttr(nameLocator + '.V', 0.5)

    nameAC = cmds.createNode(
        'aimConstraint',
        p=nameLocator,
        n=nameLocator + '_rAC1'
    )
    cmds.setAttr(nameAC + '.tg[0].tw', 1)
    cmds.setAttr(nameAC + '.a', 0, 1, 0, type='double3')
    cmds.setAttr(nameAC + '.u', 0, 0, 1, type='double3')

    attrs = [
        '.tx', '.ty', '.tz',
        '.rx', '.ry', '.rz',
        '.sx', '.sy', '.sz', '.v'
    ]
    for a in attrs:
        cmds.setAttr(nameAC + a, k=0)

    cmds.connectAttr(namePOSI + '.position', nameLocator + '.t')
    cmds.connectAttr(namePOSI + '.n', nameAC + '.tg[0].tt')
    cmds.connectAttr(namePOSI + '.tv', nameAC + '.wu')
    cmds.connectAttr(nameAC + '.crx', nameLocator + '.rx')
    cmds.connectAttr(nameAC + '.cry', nameLocator + '.ry')
    cmds.connectAttr(nameAC + '.crz', nameLocator + '.rz')

    cmds.select(nameLocator, r=True)
    return nameLocator


def rivetFollicleNoUV():
    list = cmds.ls(sl=True, fl=True)
    if not list:
        cmds.confirmDialog(
            t='Error',
            m="Select a single Mesh Face"
        )
        return
    if not '.f[':
        cmds.confirmDialog(
            t='Error',
            m="Select a single Mesh Face"
        )
        return
    nObj = list[0].split('.')
    sh = cmds.listRelatives(nObj[0], s=True)
    if not sh:
        sh = []
        if cmds.nodeType(nObj[0]) == 'mesh':
            sh.append(nObj[0])
    # print list, nObj, sh, '-' * 100
    # PART FOR MESH OBJECTS
    if cmds.nodeType(sh[0]) == 'mesh':
        # list = cmds.filterExpand(sm=32)
        # if not list:
        #     cmds.confirmDialog(
        #         t='Error', m="Select a pair number of edges")
        #     return

        list = findEdges()

        e1 = list[0].split('[')[1].split(']')
        e2 = list[1].split('[')[1].split(']')

        nameCFME1 = cmds.createNode(
            'curveFromMeshEdge',
            n='rCFME1')
        cmds.setAttr(nameCFME1 + '.ihi', 1)
        cmds.setAttr(nameCFME1 + '.ei[0]', int(e1[0]))
        nameCFME2 = cmds.createNode(
            'curveFromMeshEdge',
            n='rCFME2'
        )
        cmds.setAttr(nameCFME2 + '.ihi', 1)
        cmds.setAttr(nameCFME2 + '.ei[0]', int(e2[0]))
        cmds.connectAttr(sh[0] + '.w', nameCFME1 + '.im')
        cmds.connectAttr(sh[0] + '.w', nameCFME2 + '.im')

        lofty = cmds.createNode('loft', n='rivetLoft1')
        cmds.setAttr(lofty + '.ic', s=2)
        cmds.setAttr(lofty + '.u', 1)
        cmds.setAttr(lofty + '.rsn', 1)

        cmds.connectAttr(nameCFME1 + '.oc', lofty + '.ic[0]')
        cmds.connectAttr(nameCFME2 + '.oc', lofty + '.ic[1]')

        # MAKE FOLLICLE
        folN = cmds.createNode('follicle')
        folT = cmds.listRelatives(folN, p=True)
        cmds.connectAttr(
            lofty + '.outputSurface', folN + '.inputSurface')
        cmds.connectAttr(
            nObj[0] + '.worldMatrix[0]',
            folN + '.inputWorldMatrix'
        )
        # FINAL CONNECTIONS
        folT = cmds.listRelatives(folN, p=True)
        cmds.addAttr(
            folT[0], ln='U', at='double', k=True, min=0, max=1, dv=0.5)
        cmds.addAttr(
            folT[0], ln='V', at='double', k=True, min=0, max=1, dv=0.5)
        cmds.connectAttr(folT[0] + '.U', folN + '.parameterU')
        cmds.connectAttr(folT[0] + '.V', folN + '.parameterV')
        cmds.connectAttr(folN + '.outTranslate', folT[0] + '.translate')
        cmds.connectAttr(folN + '.outRotate', folT[0] + '.rotate')
        return folT

''' --------------------------------------------------  UTILITIES ------------------------------------------------------ '''
def getClosestVertex(mayaMesh, pos=[0, 0, 0]):
	mVector = om.MVector(pos)
	selectionList = om.MSelectionList()
	selectionList.add(mayaMesh)
	dPath = selectionList.getDagPath(0)
	mMesh = om.MFnMesh(dPath)
	ID = mMesh.getClosestPoint(om.MPoint(mVector),space=om.MSpace.kWorld)[1]
	list = cmds.ls(cmds.polyListComponentConversion(mayaMesh + '.f[' + str(ID) + ']', ff=True, tv=True), flatten=True)
	d = mVector - om.MVector(cmds.xform(list[0], t=True, ws=True, q=True))
	smallestDist2 = d.x * d.x + d.y * d.y + d.z * d.z
	closest = list[0]

	for i in range(1,len(list)) :
		d = mVector - om.MVector(cmds.xform(list[i], t=True, ws=True, q=True))
		d2 = d.x * d.x + d.y * d.y + d.z * d.z
		if d2 < smallestDist2:
			smallestDist2 = d2
			closest = list[i]
	return closest

def getClosestFace(mayaMesh, pos=[0, 0, 0]):
    mVector = om.MVector(pos)
    selectionList = om.MSelectionList()
    selectionList.add(mayaMesh)
    dPath = selectionList.getDagPath(0)
    mMesh=om.MFnMesh(dPath)
    ID = mMesh.getClosestPoint(om.MPoint(mVector),space=om.MSpace.kWorld)[1]
    return ID
