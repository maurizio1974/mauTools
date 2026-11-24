import re
from maya import mel
from maya import cmds
from utilsTools import geoTagTool, vertexDefUtil


def makeMasterCtrl():
    name = 'main_ctrl'
    cmds.curve(
        d=1, p=[
            (0.2, 0.0, 0.2), (0.6, 0.0, 0.2), (0.6, 0.0, 0.4),
            (1.0, 0.0, 0.0), (0.6, 0.0, -0.4), (0.6, 0.0, -0.2),
            (0.2, 0.0, -0.2), (0.2, 0.0, -0.6), (0.4, 0.0, -0.6),
            (0.0, 0.0, -1.0), (-0.4, 0.0, -0.6), (-0.2, 0.0, -0.6),
            (-0.2, 0.0, -0.2), (-0.6, 0.0, -0.2), (-0.6, 0.0, -0.4),
            (-1.0, 0.0, 0.0), (-0.6, 0.0, 0.4), (-0.6, 0.0, 0.2),
            (-0.2, 0.0, 0.2), (-0.2, 0.0, 0.6), (-0.4, 0.0, 0.6),
            (0.0, 0.0, 1.0), (0.4, 0.0, 0.6), (0.2, 0.0, 0.6),
            (0.2, 0.0, 0.2), (0.2, 0.0, 0.2), (0.2, 0.0, 0.2)],
        n=name)
    cmds.rename(cmds.listRelatives(name, s=True)[0], name + 'Shape')
    return name


def colorCtrl(ctrl):
    cmds.setAttr(ctrl + '.overrideEnabled', 1)
    cmds.setAttr(ctrl + ".overrideColor", 17)
    if 'L' in ctrl:
        cmds.setAttr(ctrl + '.overrideEnabled', 1)
        cmds.setAttr(ctrl + ".overrideColor", 6)
    elif 'R' in ctrl:
        cmds.setAttr(ctrl + '.overrideEnabled', 1)
        cmds.setAttr(ctrl + ".overrideColor", 13)


def makeBaseAsset(tipo, id, assetN=None):
    if not assetN:
        info = cmds.promptDialog(
            t='Asset Name', m='Enter Name:',
            b=['OK', 'Cancel'], db='OK', cb='Cancel', ds='Cancel')
        if info != 'OK':
            return
        assetN = cmds.promptDialog(q=True, text=True)
        assetN = re.sub('[^a-zA-Z0-9 \n\.]', '_', assetN)
    else:
        assetN = re.sub('[^a-zA-Z0-9 \n\.]', '_', assetN)

    base = tipo + '_root'
    geom = assetN + '_grp'
    rig = 'rig_grp'
    ctrls = 'controls_grp'

    assets = {
        'model': [base, geom],
        'rig': [base, rig, ctrls, geom]}
    for asset in list(assets.keys()):
        if asset == tipo:
            for node in assets[asset]:
                if not cmds.objExists(node):
                    cmds.group(em=True, n=node)
                    cmds.select(node, r=True)
                    vertexDefUtil.mSetLockAttr([True, True, True], [True, True, True], [
                                               True, True, True], [False])
                    cmds.select(node, r=True)
                    vertexDefUtil.mDoLockAttr(True, 'on')
                    cmds.select(cl=True)
    fa = cmds.listRelatives(geom, p=True)
    if fa:
        if fa[0] != base:
            cmds.parent(geom, base)
    else:
        cmds.parent(geom, base)

    if tipo == 'rig':
        for cur in [rig, ctrls]:
            fa = cmds.listRelatives(cur, p=True)
            if fa:
                if fa[0] != base:
                    cmds.parent(cur, base)
            else:
                cmds.parent(cur, base)
        master = makeMasterCtrl()
        colorCtrl(master)
        cmds.parent(master, ctrls)
        makeRigBaseVis(master, geom, rig)
    cmds.select(geom, r=True)
    geoTagTool.do_tag(assetN, tipo, id)
    geoTagTool.makeExportSet(tipo, assetN)
    cmds.select(cl=True)


def makeRigBaseVis(master, geo_grp, jnt_grp):
    cmds.addAttr(
        master, ln='geoVis', at='enum',
        en='off:on:')
    cmds.setAttr(master + '.geoVis', 1)
    cmds.setAttr(master + '.geoVis', cb=True)
    cmds.connectAttr(master + '.geoVis', geo_grp + '.v')
    cmds.addAttr(master, ln='overEn', at='bool')
    cmds.setAttr(master + '.overEn', 1)
    cmds.addAttr(
        master, ln='geoState', at='enum',
        en='normal:template:reference:')
    cmds.setAttr(master + '.geoState', cb=True)
    cmds.setAttr(master + '.geoState', 2)
    cmds.connectAttr(master + '.geoState', geo_grp + '.overrideDisplayType')
    cmds.connectAttr(master + '.overEn', geo_grp + '.overrideEnabled', f=True)

    cmds.addAttr(
        master, ln='jntVis', at='enum',
        en='off:on:')
    cmds.setAttr(master + '.jntVis', 1)
    cmds.setAttr(master + '.jntVis', cb=True)
    cmds.connectAttr(master + '.jntVis', jnt_grp + '.v')
    cmds.addAttr(
        master, ln='jntState', at='enum',
        en='normal:template:reference:')
    cmds.setAttr(master + '.jntState', cb=True)
    cmds.setAttr(master + '.jntState', 1)

    cmds.connectAttr(master + '.jntState', jnt_grp + '.overrideDisplayType')
    cmds.connectAttr(master + '.overEn', jnt_grp + '.overrideEnabled', f=True)
