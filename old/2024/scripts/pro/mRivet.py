'''-------------------------------------------------------------------------

    MAU Rivet Utility

    Date = 07-08-2014
    User = Maurizio Giglioli
    info = Make either Rivets on edjes selected
    or follicles on both mesh and nurbs
    Update = (07-08-2014)
            First Relase
    Update = (02-09-2016)
            Removed multiple rivet
            Added possibility to connect to incoming mesh or deformer
    Update = (07-10-2017)
            Added follicle to loft surface like rivets for meshes without UVs
----------------------------------------------------------------------------'''

import maya.cmds as cmds
import maya.mel as mel
import directionalBB as BB


def mRivet_do(ed1, ed2, mode=None):
    nameObject = ed1.split('.')
    e1 = ed1.split('[')[1].split(']')
    e2 = ed2.split('[')[1].split(']')

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

    # Check if there is something else before
    if mode:
        if mode == 1:
            conn = cmds.listConnections(
                nameObject[0] + '.inMesh', s=True, d=False, p=True
            )
            if conn:
                cmds.connectAttr(conn[0], nameCFME1 + '.im')
                cmds.connectAttr(conn[0], nameCFME2 + '.im')
            else:
                cmds.connectAttr(nameObject[0] + '.w', nameCFME1 + '.im')
                cmds.connectAttr(nameObject[0] + '.w', nameCFME2 + '.im')
        elif mode == 0:
            cmds.connectAttr(nameObject[0] + '.w', nameCFME1 + '.im')
            cmds.connectAttr(nameObject[0] + '.w', nameCFME2 + '.im')
    else:
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


def mRivet(mode):
    list = cmds.filterExpand(sm=32)
    if not list:
        cmds.confirmDialog(t='Error', m="Select a pair number of edges")
        return
    if mode == 0:  # multiple rivets
        for x in range(0, len(list) - 1):
            mRivet_do(list[x], list[x + 1], mode)
    elif mode == 1:  # pair rivets
        for x in range(0, len(list) - 1, 2):
            mRivet_do(list[x], list[x + 1])
    elif mode == 2:  # multiple follicle
        for x in range(0, len(list) - 1):
            rivetFollicleNoUV_do(list[x], list[x + 1])
    elif mode == 3:  # pair follicle
        for x in range(0, len(list) - 1, 2):
            rivetFollicleNoUV_do(list[x], list[x + 1])


def rivetFollicle():
    list = cmds.ls(sl=True, fl=True)
    if not list:
        cmds.confirmDialog(
            t='Error',
            m="Select a Mesh Face or a Nurbs Surface Point"
        )
        return
    for l in list:
        nObj = l.split('.')
        cmp = nObj[1].split('[')
        cmpIn = l.split('[')[1].split(']')
        sh = cmds.listRelatives(nObj[0], s=True)

        # PART FOR NURBS OBJECTS
        if cmds.nodeType(sh[0]) == 'nurbsSurface' and cmp[0] == 'uv':
            rangeU = cmds.getAttr(sh[0] + '.minMaxRangeU')[0]
            rangeV = cmds.getAttr(sh[0] + '.minMaxRangeV')[0]
            U = cmpIn[0]
            V = l.split('[')[2].split(']')[0]
            cond = [
                rangeU[0] == 0,
                rangeU[1] == 1,
                rangeV[0] == 0,
                rangeV[1] == 1
            ]
            if all(cond):
                # MAKE FOLLICLE
                folN = cmds.createNode('follicle')
                folT = cmds.listRelatives(folN, p=True)
                cmds.connectAttr(
                    nObj[0] + '.worldSpace[0]',
                    folN + '.inputSurface'
                )
                cmds.connectAttr(
                    nObj[0] + '.worldMatrix[0]',
                    folN + '.inputWorldMatrix'
                )
                cmds.connectAttr(
                    folN + '.outTranslate',
                    folT[0] + '.translate'
                )
                cmds.connectAttr(folN + '.outRotate', folT[0] + '.rotate')
                cmds.setAttr(folN + '.parameterU', float(U))
                cmds.setAttr(folN + '.parameterV', float(V))

        # PART FOR MESH OBJECTS
        if cmds.nodeType(sh[0]) == 'mesh' and cmp[0] == 'f':
            cmds.select(l)
            mel.eval('PolySelectConvert 3')

            # GET MESH UV VALUE
            loco = BB.directionalBB(0)
            poso = cmds.xform(loco[0], q=True, ws=True, t=True)
            cmds.delete(loco[0])

            # GET MESH UV VALUE
            CPM = cmds.createNode('closestPointOnMesh')
            cmds.connectAttr(sh[0] + '.outMesh', CPM + '.inMesh')
            cmds.setAttr(CPM + ".inPosition", poso[0], poso[1], poso[2])
            U = cmds.getAttr(CPM + ".parameterU")
            V = cmds.getAttr(CPM + ".parameterV")
            cmds.delete(CPM)

            # MAKE FOLLICLE
            folN = cmds.createNode('follicle')
            folT = cmds.listRelatives(folN, p=True)
            cmds.connectAttr(nObj[0] + '.worldMesh', folN + '.inputMesh')
            cmds.connectAttr(
                nObj[0] + '.worldMatrix[0]',
                folN + '.inputWorldMatrix'
            )
            cmds.connectAttr(folN + '.outTranslate', folT[0] + '.translate')
            cmds.connectAttr(folN + '.outRotate', folT[0] + '.rotate')

            folT = cmds.listRelatives(folN, p=True)
            cmds.addAttr(
                folT[0], ln='U', at='double', k=True, min=0, max=1, dv=U)
            cmds.addAttr(
                folT[0], ln='V', at='double', k=True, min=0, max=1, dv=V)
            cmds.connectAttr(folT[0] + '.U', folN + '.parameterU')
            cmds.connectAttr(folT[0] + '.V', folN + '.parameterV')


def rivetFollicleNoUV_do(ed1, ed2):
    nObj = ed1.split('.')
    sh = cmds.listRelatives(nObj[0], s=True)

    # PART FOR MESH OBJECTS
    if cmds.nodeType(sh[0]) == 'mesh':
        e1 = ed1.split('[')[1].split(']')
        e2 = ed2.split('[')[1].split(']')

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

# FOLLICLE ON A NURB SURFACE FROM A SURFACE POINT SELECTION


def folRivetSP():
    sel = cmds.ls(sl=True)
    for s in sel:
        if '.uv[' not in s:
            cmds.warning(
                'Please Select a surface point on a nurb surface, skipping this selection:' + s)
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
            cmds.connectAttr(
                surfT + '.worldMatrix[0]', folN + '.inputWorldMatrix')
            # FINAL CONNECTIONS
            cmds.addAttr(
                folT[0], ln='U', at='double', k=True, min=0, max=1, dv=un)
            cmds.addAttr(
                folT[0], ln='V', at='double', k=True, min=0, max=1, dv=vn)
            cmds.connectAttr(folT[0] + '.U', folN + '.parameterU')
            cmds.connectAttr(folT[0] + '.V', folN + '.parameterV')
            cmds.connectAttr(folN + '.outTranslate', folT[0] + '.translate')
            cmds.connectAttr(folN + '.outRotate', folT[0] + '.rotate')


'''
import maya.cmds as cmds
import maya.mel as mel
from rig import directionalBB as BB


def mRivet_do(ed1, ed2):
    nameObject = ed1.split('.')
    e1 = ed1.split('[')[1].split(']')
    e2 = ed2.split('[')[1].split(']')

    nameCFME1 = cmds.createNode(
        'curveFromMeshEdge',
        n='rivetCurveFromMeshEdge1'
    )
    cmds.setAttr(nameCFME1 + '.ihi', 1)
    cmds.setAttr(nameCFME1 + '.ei[0]', int(e1[0]))
    nameCFME2 = cmds.createNode(
        'curveFromMeshEdge',
        n='rivetCurveFromMeshEdge2'
    )
    cmds.setAttr(nameCFME2 + '.ihi', 1)
    cmds.setAttr(nameCFME2 + '.ei[0]', int(e2[0]))
    nameLoft = cmds.createNode('loft', n='rivetLoft1')
    cmds.setAttr(nameLoft + '.ic', s=2)
    cmds.setAttr(nameLoft + '.u', 1)
    cmds.setAttr(nameLoft + '.rsn', 1)

    namePOSI = cmds.createNode(
        'pointOnSurfaceInfo',
        n='rivetPointOnSurfaceInfo1'
    )
    cmds.setAttr(namePOSI + '.turnOnPercentage', 1)
    cmds.setAttr(namePOSI + '.parameterU', 0.5)
    cmds.setAttr(namePOSI + '.parameterV', 0.5)

    cmds.connectAttr(nameLoft + '.os', namePOSI + '.is', f=True)
    cmds.connectAttr(nameCFME1 + '.oc', nameLoft + '.ic[0]')
    cmds.connectAttr(nameCFME2 + '.oc', nameLoft + '.ic[1]')
    cmds.connectAttr(nameObject[0] + '.w', nameCFME1 + '.im')
    cmds.connectAttr(nameObject[0] + '.w', nameCFME2 + '.im')

    nameLocator = cmds.createNode('transform', n='rivet1')
    cmds.createNode('locator', n=nameLocator + 'Shape', p=nameLocator)
    cmds.addAttr(nameLocator, ln='U', at='double', k=True)
    cmds.addAttr(nameLocator, ln='V', at='double', k=True)
    cmds.connectAttr(nameLocator + '.U', namePOSI + '.parameterU')
    cmds.connectAttr(nameLocator + '.V', namePOSI + '.parameterV')
    cmds.setAttr(nameLocator + '.U', 0.5)
    cmds.setAttr(nameLocator + '.V', 0.5)

    nameAC = cmds.createNode(
        'aimConstraint',
        p=nameLocator,
        n=nameLocator + '_rivetAimConstraint1'
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


def mRivet(mode):
    list = cmds.filterExpand(sm=32)
    if not list:
        cmds.confirmDialog(t='Error', m="Select a pair number of edges")
        return
    if mode is 0:  # sequencial rivets
        for s in range(1, len(list), 1):
            mRivet_do(list[s], list[s - 1])
    if mode is 1:  # pair rivets
        for s in range(1, len(list), 2):
            mRivet_do(list[s], list[s - 1])


def rivetFollicle():
    list = cmds.ls(sl=True, fl=True)
    if not list:
        cmds.confirmDialog(
            t='Error',
            m="Select a Mesh Face or a Nurbs Surface Point"
        )
        return
    for l in list:
        nObj = l.split('.')
        cmp = nObj[1].split('[')
        cmpIn = l.split('[')[1].split(']')
        sh = cmds.listRelatives(nObj[0], s=True)

        # PART FOR NURBS OBJECTS
        if cmds.nodeType(sh[0]) == 'nurbsSurface' and cmp[0] == 'uv':
            rangeU = cmds.getAttr(sh[0] + '.minMaxRangeU')[0]
            rangeV = cmds.getAttr(sh[0] + '.minMaxRangeV')[0]
            U = cmpIn[0]
            V = l.split('[')[2].split(']')[0]
            cond = [
                rangeU[0] == 0,
                rangeU[1] == 1,
                rangeV[0] == 0,
                rangeV[1] == 1
            ]
            if all(cond):
                # MAKE FOLLICLE
                    folN = cmds.createNode('follicle')
                    folT = cmds.listRelatives(folN, p=True)
                    cmds.connectAttr(
                        nObj[0] + '.worldSpace[0]',
                        folN + '.inputSurface'
                    )
                    cmds.connectAttr(
                        nObj[0] + '.worldMatrix[0]',
                        folN + '.inputWorldMatrix'
                    )
                    cmds.connectAttr(
                        folN + '.outTranslate',
                        folT[0] + '.translate'
                    )
                    cmds.connectAttr(folN + '.outRotate', folT[0] + '.rotate')
                    cmds.setAttr(folN + '.parameterU', float(U))
                    cmds.setAttr(folN + '.parameterV', float(V))

        # PART FOR MESH OBJECTS
        if cmds.nodeType(sh[0]) == 'mesh' and cmp[0] == 'f':
            cmds.select(l)
            mel.eval('PolySelectConvert 3')

            # GET MESH UV VALUE
            loco = BB.directionalBB(0)
            poso = cmds.xform(loco[0], q=True, ws=True, t=True)
            cmds.delete(loco[0])

            # GET MESH UV VALUE
            CPM = cmds.createNode('closestPointOnMesh')
            cmds.connectAttr(sh[0] + '.outMesh', CPM + '.inMesh')
            cmds.setAttr(CPM + ".inPosition", poso[0], poso[1], poso[2])
            U = cmds.getAttr(CPM + ".parameterU")
            V = cmds.getAttr(CPM + ".parameterV")
            cmds.delete(CPM)

            # MAKE FOLLICLE
            folN = cmds.createNode('follicle')
            folT = cmds.listRelatives(folN, p=True)
            cmds.connectAttr(nObj[0] + '.worldMesh', folN + '.inputMesh')
            cmds.connectAttr(
                nObj[0] + '.worldMatrix[0]',
                folN + '.inputWorldMatrix'
            )
            cmds.connectAttr(folN + '.outTranslate', folT[0] + '.translate')
            cmds.connectAttr(folN + '.outRotate', folT[0] + '.rotate')
            cmds.setAttr(folN + '.parameterU', U)
            cmds.setAttr(folN + '.parameterV', V)
'''
