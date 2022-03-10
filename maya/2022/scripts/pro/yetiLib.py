'''----------------------------------------------------------------------

MAU YETI LIB

Date = 26-02-2015
User = Maurizio Giglioli
Update =
    (10-12-2014)
    First release

----------------------------------------------------------------------'''
import maya.cmds as cmds
import maya.mel as mel
import math
import os


# BASE YETI SET UP
def yetiBase():
    sel, mesh = cmds.ls(sl=True), ''
    if not sel:
        cmds.confirmDialog(t='Error', m='Please select a mesh')
        return
    for s in sel:
        sh = cmds.listRelatives(s, s=True)
        if sh:
            mesh = sh[0]
    check = cmds.nodeType(mesh)
    if not check == 'mesh':
        cmds.confirmDialog(t='Error', m='Please select a mesh')
        return
    mel.eval('pgYetiCreateOnMesh()')
    YT = cmds.ls(sl=True)
    cmds.select(sel[0], r=True)
    mel.eval('pgYetiCreateGroomOnMesh()')
    GR = cmds.ls(sl=True)
    cmds.select(cl=True)
    mel.eval('pgYetiAddGroom("' + GR[0] + '", "' + YT[0] + '")')


# YETI EXPORT ALL THE ATTRIBUTE MAPS OF THE GROOM FOR ALL THE UV TILES
def yetiGroomExport(mesh, groom, path, shells, v, resolution, maxValue, attrs=None):
    res = str(resolution)
    maxV = str(maxValue)
    cmds.constructionHistory(toggle=False)
    vn = v * 1000
    paint = cmds.pgYetiCommand(groom, listAttributes=True)
    for i in range(1, shells + 1):
        if not attrs:
            for p in paint:
                file = os.path.join(
                    path,
                    mesh.replace('Shape', '') + '_' + p + '_' + str((1000 + vn) + i) + '.tif').replace('\\', '/')
                cmd = 'pgYetiCommand -exportTexture "' + file + '" "tif" ' + res
                cmd += ' ' + res + ' -uvrange 0 1 0 1 -attribute "' + p + '" 0 '
                cmd += maxV + ' "' + groom + '"'
                mel.eval(cmd)
        else:
            for a in attrs:
                file = os.path.join(
                    path,
                    mesh.replace('Shape', '') + '_' + a + '_' + str((1000 + vn) + i) + '.tif').replace('\\', '/')
                cmd = 'pgYetiCommand -exportTexture "' + file + '" "tif" ' + res + ' '
                cmd += res + ' -uvrange 0 1 0 1 -attribute "' + a + '" 0 '
                cmd += maxV + ' "' + groom + '"'
                mel.eval(cmd)
        uvs = cmds.polyEvaluate(mesh, uv=True)
        # print uvs
        cmds.select(cl=True)
        cmds.select(mesh + '.map[0:' + str(int(uvs) - 1) + ']')
        cmds.polyEditUV(u=-1, v=-1 * v)

    cmds.select(mesh + '.map[0:' + str(int(uvs) - 1) + ']')
    cmds.polyEditUV(u=shells, v=v)
    cmds.select(cl=True)
    cmds.constructionHistory(toggle=True)
    print 'ALL DONE'


# CREATE A PROXY MESH OF THE HAIR
def yetiProxtHairVol():
    shapes, curves = [], []
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(t='Error', m='Please select a yeti node')
        return
    check = cmds.nodeType(cmds.listRelatives(sel[0], s=True)[0])
    if not check == 'pgYetiMaya':
        cmds.confirmDialog(t='Error', m='Please select a yeti node')
        return
    YT = cmds.listRelatives(sel[0], s=True)
    cmds.pgYetiCommand(generateMayaObjects=True)
    grp = cmds.listRelatives(YT[0] + '_generated_')
    for g in grp:
        shapes = cmds.listRelatives(g, type='nurbsCurve')
        for s in shapes:
            curves.append(s)
    cmds.select(cl=True)
    tta = cmds.createNode('transformsToArrays')
    cvx = cmds.createNode('convexHull')
    mesh = cmds.createNode('mesh')
    mt = cmds.listRelatives(mesh, p=True)
    cmds.connectAttr(tta + '.outPositionPP', cvx + '.inGeometry')
    cmds.connectAttr(cvx + '.outMesh', mesh + '.inMesh')
    i = 0
    for s in curves:
        spans = cmds.getAttr(s + '.spans')
        pos = cmds.pointPosition(s + '.cv[' + str(spans) + ']')
        grp = cmds.createNode('transform')
        cmds.move(pos[0], pos[1], pos[2], grp, a=True)
        if not cmds.objExists('temp_wolrd_null'):
            cmds.group(em=True, n='temp_wolrd_null')
        cmds.parent(grp, 'temp_wolrd_null')
        cmds.connectAttr(
            grp + '.worldMatrix[0]',
            tta + '.inTransforms[' + str(i) + '].inMatrix'
        )
        i = i + 1
        # print 'Working on hair '+s
    cmds.duplicate(mesh, n=sel[0] + '_PROXY')
    cmds.delete(tta, cvx, mt, YT[0] + '_generated_', 'temp_wolrd_null')


def yetiProxtHair(res, mesh=None, twod=None, decimate=None):
    pi = math.pi
    shapes, curves = [], []
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(t='Error', m='Please select a yeti node')
        return
    check = cmds.nodeType(cmds.listRelatives(sel[0], s=True)[0])
    if not check == 'pgYetiMaya':
        cmds.confirmDialog(t='Error', m='Please select a yeti node')
        return
    YT = cmds.listRelatives(sel[0], s=True)
    if not decimate:
        decimate = 2
    sca = mel.eval('pgYetiGraph -listNodes -type "scatter" ' + YT[0])
    for s in sca:
        cmd = 'pgYetiGraph -node "' + s + '" -param "densityMultiplier"'
        cmd += ' -getParamValue ' + YT[0]
        attr = mel.eval(cmd)
        cmd = 'pgYetiGraph -node "' + s + '" -param "densityMultiplier" '
        cmd += '-setParamValueScalar ' + str(attr / decimate) + ' ' + YT[0]
        mel.eval(cmd)
    cmds.pgYetiCommand(generateMayaObjects=True)
    # RESTORE SCATTER INITIAL VALUES
    for s in sca:
        cmd = 'pgYetiGraph -node "' + s + '" -param "densityMultiplier"'
        cmd += ' -getParamValue ' + YT[0]
        attr = mel.eval(cmd)
        cmd = 'pgYetiGraph -node "' + s + '" -param "densityMultiplier" '
        cmd += '-setParamValueScalar ' + str(attr * decimate) + ' ' + YT[0]
        mel.eval(cmd)
    grp = cmds.listRelatives(YT[0] + '_generated_')
    for g in grp:
        shapes = cmds.listRelatives(g, type='nurbsCurve')
        for s in shapes:
            curves.append(s)
    dist, maxs = [], 0
    # GET MAX LENGHT OF CURVES
    for c in curves:
        dist.append(cmds.arclen(c))
        maxs = max(dist)
    cmds.select(cl=True)
    if mesh:
        cpos = cmds.createNode('closestPointOnMesh', n='CPOS')
        cmds.connectAttr(mesh + '.worldMesh[0]', cpos + '.inMesh')
    for s in curves:
        pos = cmds.pointPosition(s + '.cv[0]')
        plane = cmds.polyPlane(sx=1, sy=1, o=True, ch=False, w=0.01, h=0.01)
        cmds.xform(plane, ws=True, t=(pos[0], pos[1], pos[2]))
        # GET ORIENTATION BASED ON GROTH SURFACE
        if mesh:
            posc = cmds.pointPosition(s + '.cv[0]')
            cmds.setAttr(cpos + '.inPosition', posc[0], posc[1], posc[2])
            normal = cmds.getAttr(cpos + '.normal')[0]
            rot = []
            for x in range(0, 3):
                rot.append(normal[x] * (180 / pi))
            cmds.setAttr(plane[0] + '.r', rot[0], rot[1], rot[2])
            # CLEAR ROTATION VALUE ON TRANSFORM
            cmds.select(plane, r=True)
            cmds.makeIdentity(
                apply=True, t=False, r=True, s=False, n=False, pn=True)
        cmds.select(plane, s, r=True)
        multi = int(res / (maxs / cmds.arclen(s)))
        if multi < 2:
            multi = 3
        cmds.polyExtrudeFacet(
            ch=True,
            keepFacesTogether=True,
            divisions=multi,
            twist=0,
            taper=0.01,
            off=0,
            thickness=0,
            smoothingAngle=30,
            inputCurve=s
        )
        if not cmds.objExists(sel[0] + '_proxy_Hair_GRP'):
            cmds.group(em=True, n=sel[0] + '_proxy_Hair_GRP')
        cmds.parent(plane, sel[0] + '_proxy_Hair_GRP')
        if twod == 1:
            ammount = int(cmds.polyEvaluate(plane[0], f=True))
            cmds.delete(plane[0] + '.f[0:' + str(ammount - (multi + 1)) + ']')
        cmds.select(plane, s, r=True)
        mel.eval('DeleteHistory')
        cmds.select(cl=True)
    # CLEANUP
    cmds.delete(YT[0] + '_generated_')


# SWAP GEOMETRY
def yetiSwapGeo():
    sel, state = cmds.ls(sl=True), 0
    if len(sel) != 2:
        cmds.confirmDialog(
            t='Error',
            m='Please select the yeti mesh and the one to transfer to'
        )
        return
    check = cmds.nodeType(cmds.listRelatives(sel[0], s=True)[0])
    check1 = cmds.nodeType(cmds.listRelatives(sel[1], s=True)[0])
    if check:
        if not check == 'mesh':
            cmds.confirmDialog(
                t='Error',
                m='The first selection is not a mesh'
            )
            return
    if check1:
        if not check1 == 'mesh':
            cmds.confirmDialog(
                t='Error',
                m='The second selection is not a mesh'
            )
            return
    conn = cmds.listConnections(sel[0] + '.worldMesh[0]', s=False, d=True)
    if conn:
        for c in conn:
            if cmds.nodeType(cmds.listRelatives(c, s=True)[0]) == 'pgYetiMaya':
                state = 1
        if state == 0:
            cmds.confirmDialog(
                t='Error',
                m='The first mesh doesn\'t not have a yetiNode assigned to it'
            )
            return
        else:
            cmd = 'pgYetiSwapGeometry("'
            cmd += cmds.listRelatives(sel[0], s=True)[0] + '", "'
            cmd += cmds.listRelatives(sel[1], s=True)[0] + '")'
            mel.eval(cmd)
    else:
        cmds.confirmDialog(
            t='Error',
            m='The first mesh doesn\'t not have a yetiNode assigned to it'
        )
