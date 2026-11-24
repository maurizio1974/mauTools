import maya.cmds as mc


def mauRibbon(rad=None, axis=None):
    sel = mc.ls(sl=True)
    if not sel:
        mc.confirmDialog(t='Error', m='Please selct a Nurb Surface to Start')
        return
    for s in sel:
        sh = mc.listRelatives(s, s=True)
        if mc.nodeType(sh[0]) != 'nurbsSurface':
            mc.confirmDialog(
                t='Error', m='Please selct a Nurb Surface to Start')
            return
        spans = mc.getAttr(f'{sh[0]}.spansV')
        current = (1 / float(spans)) / 2
        grp = s + '_GRP'
        if not mc.objExists(grp):
            mc.group(em=True, n=f'{s}_GRP')
        grpH = s + '_clusters_HGRP'
        if not mc.objExists(grpH):
            mc.group(em=True, n=f'{s}_clusters_HGRP')
        for x in range(0, spans):
            name = s + '_' + str(x).zfill(2) + '_FOL'
            fol = mc.createNode('follicle', n=f'{name}Shape')
            tr = mc.listRelatives(fol, p=True)
            mc.scaleConstraint(grpH, tr[0], mo=True)
            mc.select(cl=True)
            if not rad:
                rad = 1
            jnt = mc.joint(n=f'{s}_' + str(x).zfill(2) + '_JNT', rad=rad)
            mc.parent(jnt, tr[0])
            mc.connectAttr(
                f'{sh[0]}.worldSpace[0]', f'{fol}.inputSurface', f=True)
            mc.connectAttr(
                sh[0] + '.worldMatrix', f'{fol}.inputWorldMatrix', f=True)
            mc.connectAttr(fol + '.outTranslate', tr[0] + '.t')
            mc.connectAttr(fol + '.outRotate', tr[0] + '.r')
            mc.setAttr(fol + '.parameterU', 0.5)
            mc.setAttr(fol + '.parameterV', current)
            current = current + (1 / float(spans))
            mc.parent(tr[0], grp)
            mc.rename(tr[0], name)
        for i in range(0, spans + 2):
            if i != 1 and i != spans + 2:
                grpN = mc.group(
                    em=True, n=s + '_' + str(i).zfill(2) + '_cls_GRP')
                if i == 0:
                    mc.select(s + '.cv[0:3][' + str(i) + ':1]', r=True)
                elif i == spans + 1:
                    mc.select(
                        s + '.cv[0:3][' + str(i) + ':' + str(spans + 2) + ']',
                        r=True)
                else:
                    mc.select(s + '.cv[0:3][' + str(i) + ']', r=True)
                mc.refresh()
                clh = mc.cluster(n=f'{s}_' + str(i).zfill(2) + '_CLH')
                pc = mc.parentConstraint(clh[1], grpN)
                mc.refresh()
                mc.delete(pc)
                mc.parent(clh[1], grpN)
                mc.parent(grpN, grpH)
                if not rad:
                    rad = 1
                x, y, z = 0, 1, 0
                if axis == 'x':
                    x, y, z = 1, 0, 0
                elif axis == 'y':
                    x, y, z = 0, 1, 0
                elif axis == 'z':
                    x, y, z = 0, 0, 1
                circle = mc.circle(
                    n=f'{s}_' + str(i).zfill(2) + '_CTRL', r=rad, nr=(x, y, z))
                mc.parent(circle[0], grpN)
                mc.setAttr(circle[0] + '.t', 0, 0, 0)
                mc.setAttr(circle[0] + '.r', 0, 0, 0)
                mc.parentConstraint(circle[0], clh[1], mo=True)
