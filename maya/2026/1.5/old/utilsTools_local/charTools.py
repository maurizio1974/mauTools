'''----------------------------------------------------------------------
OUTPOST SIM UTILITY

Date = 30-08-2018
User = Maurizio Giglioli
Usage:
    from utilsTools import *
    reload(charTools)

Update =
    (30-08-2018) First Release
    (07-08-2019) added import of default bipeds geoemtry
    (07-08-2019) added fix for Nan Camera adn menu separators
----------------------------------------------------------------------'''
import os
import json
import maya.cmds as cmds
from pprint import pprint
import maya.api.OpenMaya as om
import maya.app.renderSetup.model.renderSetup as renderSetup


def attrAdd(asset, tipo):
    base = {'assetName': asset, 'assetType': tipo, 'mtoa_constant_type': asset}
    nodes = cmds.ls(sl=True)
    if not nodes:
        print('Select the transforms to add attributes to')
    for s in nodes:
        # CLEAN ATTRIBUTES
        attrClean([s])
        value, dir, sh = '', '', []
        for b in list(base.keys()):
            cmds.addAttr(s, ln=b, dt='string')
            cmds.setAttr(s + '.' + b, base[b], type='string')
            sh = cmds.listRelatives(s, s=True, ni=True)
            if sh:
                if cmds.nodeType(s) != 'objectSet':
                    # CHECK IF THE ATTRIBUTE EXISTS
                    if cmds.attributeQuery(b, n=sh[0], ex=True):
                        # cmds.setAttr(sh[0] + '.' + b, l=False)
                        cmds.deleteAttr(sh[0], at=b)
                        print('Deleted existing Shape Attr: ' + b, sh)
                    cmds.addAttr(sh[0], ln=b, dt="string")
                    cmds.setAttr(sh[0] + '.' + b, base[b], type='string')
                    # cmds.setAttr(sh[0] + '.' + b, l=True)
        # CHECK IF THE ATTRIBUTE EXISTS
        cmds.addAttr(s, ln="id", at='long', dv=0)
        cmds.addAttr(s, ln="res", at="enum", en="0:1:2:")
        if s.endswith('_grp'):
            dir = 'out'
            if cmds.attributeQuery(dir, n=s, ex=True):
                cmds.deleteAttr(s, at=dir)
                print('Deleted existing Attr: ' + dir, s)
            cmds.addAttr(s, ln=dir, dt="string")
        if sh:
            # ATTR CREATE OF IN AND OUT
            if s.endswith('_in'):
                dir = 'in'
            elif s.endswith('_geo'):
                dir = 'out'
            elif s.endswith('_crv'):
                dir = 'out'
            elif s.endswith('_mesh'):
                dir = 'out'
            if cmds.nodeType(sh[0]) == 'mesh' or cmds.nodeType(sh[0]) == 'nurbsCurve':
                if dir == 'out':
                    repl = s.rsplit('_', 1)
                    value = repl[0].split(':')[-1] + '_in'
                elif dir == 'in':
                    repl = s.rsplit('_', 1)
                    if cmds.nodeType(sh[0]) == 'mesh':
                        value = repl[0] + '_geo'
                    elif cmds.nodeType(sh[0]) == 'nurbsCurve':
                        value = repl[0] + '_crv'
                if dir:
                    # CHECK IF THE ATTRIBUTE EXISTS
                    if cmds.attributeQuery(dir, n=s, ex=True):
                        # cmds.setAttr(s + '.' + dir, l=False)
                        cmds.deleteAttr(s, at=dir)
                        print('Deleted existing Attr: ' + dir, s)
                    cmds.addAttr(s, ln=dir, dt="string")
                    cmds.setAttr(s + '.' + dir, value, type='string')
                    # cmds.setAttr(s + '.' + dir, l=True)
                    # CHECK IF THE ATTRIBUTE EXISTS
                    if cmds.nodeType(s) != 'objectSet':
                        if cmds.attributeQuery(dir, n=sh[0], ex=True):
                            # cmds.setAttr(sh[0] + '.' + dir, l=False)
                            cmds.deleteAttr(sh[0], at=dir)
                            print('Deleted existing Shape Attr: ' + dir, sh)
                        cmds.addAttr(sh[0], ln=dir, dt="string")
                        cmds.setAttr(sh[0] + '.' + dir, value, type='string')
                        # cmds.setAttr(sh[0] + '.' + dir, l=True)
            for at in ['id', 'res']:
                if cmds.attributeQuery(at, n=sh[0], ex=True):
                    # cmds.setAttr(sh[0] + '.' + at, l=False)
                    cmds.deleteAttr(sh[0], at=at)
                    print('Deleted existing Attr: ' + at, sh)
            cmds.addAttr(sh[0], ln="id", at='long', dv=0)
            cmds.addAttr(sh[0], ln="res", at="enum", en="0:1:2:")


def attrClean(nodes=None):
    snodes = []
    if not nodes:
        nodes = cmds.ls(sl=True)
    if not nodes:
        print('Select the transforms to add attributes to')
    attrs = [
        'assetName', 'assetType', 'res', 'id',
        'in', 'out', 'mtoa_constant_type', 'mtoa_constant_cowtype']
    # LEGACY BROOKLYN ATTRIBUTS
    for a in attrs:
        for n in nodes:
            if cmds.attributeQuery(a, n=n, ex=True):
                cmds.setAttr(n + '.' + a, l=False)
                cmds.deleteAttr(n, at=a)
                print(a + ' on ' + n + ' has been removed')
            cur = cmds.listRelatives(n, s=True, ni=True)
            if cur:
                for cc in cur:
                    snodes.append(cc)
        for sn in snodes:
            if cmds.attributeQuery(a, n=sn, ex=True):
                if cmds.attributeQuery(a, n=sn, ex=True):
                    cmds.setAttr(sn + '.' + a, l=False)
                    cmds.deleteAttr(sn, at=a)
                    print(a + ' on ' + sn + ' has been removed')


def saveAssetInfo(out, nodes, attrs):
    asset, value = {}, 0
    for n in nodes:
        info = {}
        for a in attrs:
            if cmds.attributeQuery(a, n=n, ex=True):
                value = cmds.getAttr(n + '.' + a)
                info[a] = value
        asset[n] = info
    # SAVE DATA
    with open(out, 'w') as outfile:
        json.dump(asset, outfile, indent=4)
    print('Asset data saved to ' + out)


def importRig(ns, rig):
    if not os.path.isfile(rig):
        cmds.confirmDialog(t='Error', m='The file doesn\'t exists:\n' + rig)
        return
    cmds.file(
        rig, r=True, type="mayaAscii",
        ignoreVersion=True, gl=True,
        mergeNamespacesOnClash=False,
        namespace=ns, options="v=0;")
    cmds.refresh()


def setIDandRES(stage, cam=None):
    if stage == 'RIG':
        if not cam:
            sel = cmds.ls(sl=True)
            if not sel:
                cmds.warning('Please select the render Camera')
                return
            if cmds.nodeType(sel[0]) == 'transform':
                sh = cmds.listRelatives(sel[0], s=True)[0]
                if sh:
                    if cmds.nodeType(sh) != 'camera':
                        cmds.warning('Please select the render Camera')
                        return
            else:
                cmds.warning('Please select the render Camera')
                return
            sel[0] = cam
        camSelected = cmds.xform(cam, q=True, ws=True, t=True)
        cam = om.MVector(camSelected)
        assets, id = {}, None
        # FIRST NAMESPACE DECLARATION TO CHECK FOR BAD ONES
        ns = cmds.namespaceInfo(lon=True, r=True)
        for n in ns:
            if 'EXPORTNS' in n:
                if cmds.namespace(ex=n):
                    cmds.namespace(rm=n, dnc=True)
        # REDECLARE THE NAMESPACES VARIABLE CLEANED UP
        ns = cmds.namespaceInfo(lon=True, r=True)
        for x, n in enumerate(ns):
            nodes = cmds.namespaceInfo(n, lod=True)
            if 'UI' not in n and 'shared' not in n:
                if nodes:
                    sets = cmds.ls(n + ':*out_set')
                    if sets:
                        geo = sets[0].replace(sets[0].split(
                            ':')[-1], '') + 'cowBasemesh_geo'
                        if cmds.objExists(geo):
                            space = cmds.objectCenter(geo)
                            asset = om.MVector(space)
                            dist = om.MVector(asset - cam).length()
                            assets[dist] = sets[0]
        for i, a in enumerate(sorted(assets.keys())):
            res, id = 0, i
            if a <= 100:
                res = 2
            elif a <= 300:
                res = 1
            print(a, assets[a], res, id)
            nodes = cmds.sets(assets[a], q=True)
            cmds.setAttr(assets[a] + '.res', res)
            cmds.setAttr(assets[a] + '.id', id)
            for node in nodes:
                cmds.setAttr(node + '.res', res)
                cmds.setAttr(node + '.id', id)
                sh = cmds.listRelatives(node, s=True, ni=True)[0]
                if sh:
                    if cmds.attributeQuery('res', n=sh, ex=True) and cmds.attributeQuery('id', n=sh, ex=True):
                        cmds.setAttr(sh + '.res', res)
                        cmds.setAttr(sh + '.id', id)
                    else:
                        cmds.warning('Skipping this node: ' + sh +
                                     ' Doens\'t have the right attributes to be set')
        cmds.warning('IDs and LOD set for this shot')


def outpostCentroid(obj=None):
    out = {}
    if not obj:
        obj = cmds.ls(sl=True)
    if not obj:
        cmds.confirmDialog(t='error', m='Please select a mesh object')
    for o in obj:
        sh = cmds.listRelatives(o, s=True, ni=True)[0]
        if sh:
            if cmds.nodeType(cmds.listRelatives(o, s=True, ni=True)[0]) == 'mesh':
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
                centroid = (
                    [sum(p[0]) / length, sum(p[1]) / length, sum(p[2]) / length])
                loc = cmds.spaceLocator()
                cmds.xform(loc[0], t=(centroid[0], centroid[1], centroid[2]))
                out[loc[0]] = centroid
            else:
                print('Skipped {0}'.format(o))
    return out


def importDefaultGeo(gender, mode, stage):
    biped = ''
    dirname, filename = os.path.split(os.path.abspath(__file__))
    if stage == 'Model':
        token = 'default_geo'
    elif stage == 'Rig':
        token = 'default_rigs'
    geoLoc = os.path.join(dirname, token)
    if not os.path.isdir(geoLoc):
        cmds.confirmDialog(
            t='error', m=geoLoc + '\ndoesn\'t exist, please make sure the directory exists')
        return
    geos = os.listdir(geoLoc)
    if geos:
        for g in geos:
            if gender in g:
                biped = g
    geo = os.path.join(geoLoc, biped)
    if not os.path.isfile(geo):
        cmds.confirmDialog(t='Error', m='The file doesn\'t exists:\n' + geo)
        return
    if mode == 'ref':
        cmds.file(
            geo, r=True, type="mayaAscii",
            ignoreVersion=True, gl=True,
            mergeNamespacesOnClash=False,
            namespace=gender, options="v=0;")
    elif mode == 'imp':
        cmds.file(
            geo, i=True, type="mayaAscii",
            ignoreVersion=True, gl=True,
            mergeNamespacesOnClash=False,
            namespace=gender, options="v=0;")
    cmds.refresh()


def importDefaultTurntable(zone, mode):
    setup = ''
    dirname, filename = os.path.split(os.path.abspath(__file__))
    geoLoc = os.path.join(dirname, 'default_scenes')
    if not os.path.isdir(geoLoc):
        cmds.confirmDialog(
            t='error', m=geoLoc + '\ndoesn\'t exist, please make sure the directory exists')
        return
    scenes = os.listdir(geoLoc)
    if scenes:
        for g in scenes:
            if zone in g:
                if g.endswith('.ma'):
                    scene = g
                elif g.endswith('.json'):
                    setup = g
    shot = os.path.join(geoLoc, scene)
    info = os.path.join(geoLoc, setup)
    if not os.path.isfile(shot):
        cmds.confirmDialog(t='Error', m='The file doesn\'t exists:\n' + shot)
        return
    if not os.path.isfile(info):
        cmds.confirmDialog(t='Error', m='The file doesn\'t exists:\n' + info)
        return
    print('scene', shot)
    print('config', info)
    if mode == 'ref':
        cmds.file(
            shot, r=True, type="mayaAscii",
            ignoreVersion=True, gl=True,
            mergeNamespacesOnClash=False,
            namespace=zone, options="v=0;")
    elif mode == 'imp':
        cmds.file(
            shot, i=True, type="mayaAscii",
            ignoreVersion=True, gl=True,
            mergeNamespacesOnClash=False,
            namespace=zone, options="v=0;")
    cmds.refresh()
    # READ THE SCENE SETTINS
    with open(info, 'r') as file:
        print('-' * 50)
        print(info)
        renderSetup.instance().decode(json.load(file), renderSetup.DECODE_AND_OVERWRITE, None)


def fixNaNCam():
    cams = cmds.camera(n='newStartupCam')
    cmds.camera('persp', e=True, sc=False)
    cmds.delete('persp')
    cmds.rename(cams[0], 'persp')
    cmds.camera('persp', e=True, sc=True)
    cmds.reorder('persp', f=True)
    cmds.setAttr('persp.v', 1)
    cmds.optionVar(fv=('defaultFitFactor', 1.0))
