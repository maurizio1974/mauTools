'''----------------------------------------------------------------------

OUPOST MESH TAG UTILITY

Date = 18/03/2019
User = Maurizio Giglioli
Update =
        18/03/2019 First Release
        19/07/2019 Reworked where to add attributes for pipeline
                   Changed set creation
        20/08/2019 Added tab UI for different tagging and shading
                   assignment
        22/08/2018 Refactor the json export format
----------------------------------------------------------------------'''
import os, sys
import json
import string
import maya.mel as mel
import maya.cmds as cmds
import maya.api.OpenMaya as om
from . import outGeneralUtil
from pprint import pprint, pformat


def do_tag(asset, tipo, id=None):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(t='error', m='Please select the mesh to be tagged')
        return
    for s in sel:
        cmds.select(s, r=True)
        # attrAdd(tipo.lower(), asset.upper(), id)
        attrAdd(tipo, asset, id)
    cmds.select(cl=True)
    cmds.select(sel, r=True)

def attrAdd(asset, tipo, id=None):
    if not id:
        id = 0
    base = {
        'assetName': asset, 'assetType': tipo,
        'mtoa_constant_type': 'type',
        'id': id, 'res': 0 }
    nodes = cmds.ls(sl=True, l=True)
    if not nodes:
        cmds.warning('Select the transforms to add attributes to')
        return
    for s in nodes:
        s = extChecker(s)
        if s:
            # CLEAN ATTRIBUTES
            # attrClean([s], base)
            # ADD ATTRIBUTES
            value, dir, sh= '', '', []
            sh = cmds.listRelatives(s, s=True, ni=True, f=True)
            for b in list(base.keys()):
                if s.endswith('_grp'):
                    if 'asset' in b:
                        if cmds.attributeQuery(b, n=s, ex=True):
                            # cmds.deleteAttr(s + '.' + b)
                            cmds.setAttr(s + '.' + b, base[b], type='string')
                        else:
                            cmds.addAttr(s, ln=b, dt='string')
                            cmds.setAttr(s + '.' + b, base[b], type='string')
                if sh:
                    if cmds.attributeQuery(b, n=sh[0], ex=True):
                        # cmds.deleteAttr(sh[0] + '.' + b)
                        try:
                            cmds.setAttr(sh[0] + '.' + b, base[b], type='string')
                        except:
                            cmds.setAttr(sh[0] + '.' + b, base[b])
                    else:
                        cmds.addAttr(sh[0], ln=b, dt="string")
                        cmds.setAttr(sh[0] + '.' + b, base[b], type='string')

def attrCustAdd(ui):
    sel = cmds.ls(sl=True, l=True)
    if not sel:
        cmds.warning('Select the mesh to add attributes to')
        return
    attr = cmds.optionMenu(ui[0], q=True, v=True)
    for s in sel:
        sh = cmds.listRelatives(s, s=True, ni=True, f=True)
        if sh:
            if cmds.nodeType(sh[0]) == 'mesh' or cmds.nodeType(sh[0]) == 'nurbsCurve' or cmds.nodeType(sh[0]) == 'nurbsSurface' :
                if cmds.attributeQuery(attr, n=sh[0], ex=True):
                    cmds.deleteAttr(sh[0] + '.' + attr)
                val = cmds.textField(ui[1], q=True, tx=True)
                cmds.addAttr(sh[0], ln=attr, dt='string')
                cmds.setAttr(sh[0] + '.' + attr, val, type='string')
                print(attr + ' added on this mesh ' + s + ' with this value ' + val)
            else:
                cmds.warning('Please select a mesh , curve or nubSurface')
    cmds.select(cl=True)
    cmds.select(sel, r=True)

def setDefaulAttr(ui):
    sel = cmds.ls(sl=True, l=True)
    if not sel:
        cmds.warning('Select the mesh to add attributes to')
        return
    for s in sel:
        sh = cmds.listRelatives(s, s=True, ni=True, f=True)
        val = cmds.textField(ui[0], q=True, tx=True)
        if not val:
            cmds.warning('Please set a shader name to add to the attribute')
            return
        attr = 'mtoa_constant_type'
        # if cmds.attributeQuery(attr, n=sh[0], ex=True):
        #     cmds.deleteAttr(sh[0] + '.' + attr)
        # cmds.addAttr(sh[0], ln=attr, dt='string')
        if not sh:
            cmds.warning('The object you selected has no Shapes')
            return
        if cmds.attributeQuery(attr, n=sh[0], ex=True):
            cmds.setAttr(sh[0] + '.' + attr, val, type='string')
            print(attr + ' set on this mesh ' + s + ' with this value ' + val)
        else:
            print(attr + ' missing on this mesh ' + s + ', make sure this mesh is tagged correctly')

def attrClean(nodes, dir=None, attrs=None):
    if not dir:
        if not attrs:
            attrs = {
                'assetName': '', 'assetType': '',
                'mtoa_constant_type': '',
                'id': 0, 'res': 0 }
        if not nodes:
            nodes = cmds.ls(sl=True, l=True)
            if not nodes:
                cmds.warning('Please select the nodes to be cleaned')
                return
        for a in list(attrs.keys()):
            snodes = []
            for n in nodes:
                if cmds.attributeQuery(a, n=n, ex=True):
                    cmds.setAttr(n + '.' + a, l=False)
                    cmds.deleteAttr(n, at=a)
                    print(a + ' on ' + n + ' has been removed')
                cur = cmds.listRelatives(n, s=True, ni=True, f=True)
                if cur:
                    for cc in cur:
                        snodes.append(cc)
            if snodes:
                for sn in snodes:
                    if cmds.attributeQuery(a, n=sn, ex=True):
                        if cmds.attributeQuery(a, n=sn, ex=True):
                            cmds.setAttr(sn + '.' + a, l=False)
                            cmds.deleteAttr(sn, at=a)
                            print(a + ' on ' + sn + ' has been removed')
                # CLEAN MTOA_SHADER ASSIGNMENT
                for sn in snodes:
                    attrs = cmds.listAttr(sn, ud=True)
                    if attrs:
                        for a in attrs:
                            if 'mtoa_constant' in a and not 'mtoa_constant_type' in a:
                                cmds.deleteAttr(sn + '.' + a)
                                print(a + ' on ' + sn + ' has been removed')
    else:
        # CLEAN ONLY MTOA_SHADER ASSIGNMENT
        if not nodes:
            nodes = cmds.ls(sl=True)
            if not nodes:
                cmds.warning('Please select the nodes to be cleaned')
                return
        for n in nodes:
            if nodes:
                snodes = cmds.listRelatives(n, s=True, ni=True, f=True)
                if snodes:
                    for sn in snodes:
                        attrs = cmds.listAttr(sn, ud=True)
                        if attrs:
                            for a in attrs:
                                if 'mtoa_constant' in a:
                                    cmds.deleteAttr(sn + '.' + a)
                                    print(a + ' on ' + sn + ' has been removed')
    cmds.select(cl=True)
    cmds.select(nodes, r=True)

def makeExportSet(tipo, asset):
    tag = []
    all_trans = cmds.ls(type='transform')
    all_sets = cmds.ls(type='objectSet')
    for a in all_sets:
        if cmds.attributeQuery('assetName', n=a, ex=True):
            cmds.delete(a)
    for a in all_trans:
        if a.endswith('_grp'):
            if cmds.attributeQuery('assetName', n=a, ex=True):
                tag.append(a)
    if not tag:
        cmds.warning('There are no transforms with extension "_grp" tagged')
        return
    attrs = {'assetName': asset, 'assetType': tipo}
    name = 'out_' + tipo.lower() + '_set'
    cmds.sets(em=True, n=name)
    cmds.select(name, ne=True, r=True)
    for a in list(attrs.keys()):
        cmds.addAttr(name, ln=a, dt='string')
        cmds.setAttr(name + '.' + a, attrs[a], type='string')
    for t in tag:
        cmds.sets(t, add=name)

# ---------------------------------------------------------------------------------------------
# SCRIPT JOBS STUFF
# ---------------------------------------------------------------------------------------------

# CLEAN ALL SCRIPT JOBS
def cleanScriptJobs():
    jobs = cmds.scriptJob(lj=True)
    if jobs:
        for s in jobs:
            if 'geoTag' in s or 'tagTools' in s:
                id = int(s.split(':')[0])
                cmds.scriptJob(k=id, f=True)
                # print 'Cleaned scriptJob: ' + str(id)

# KILL SCRIPT JOBS WHEN WE CLOSE THE UI
def killScriptJobTagger(job, ui):
    cmds.scriptJob(
        uiDeleted=(ui, 'cmds.scriptJob(kill=' + str(job) + ', f=True)'))

# SCRIPT JOBS TO LIST ATTRIBUTE AND IDS ON SELECTION
def makeScriptJobAT(ui):
    job = cmds.scriptJob(
        e=("SelectionChanged", 'geoTagTool.tagCheckValueUI(["' + ui[0] + '"])'),
        protected=True
    )
    return job

def makeScriptJobID(ui):
    job = cmds.scriptJob(
        e=("SelectionChanged", 'geoTagTool.getIndex("' + ui + '")'),
        protected=True
    )
    return job

def makeScriptJobNAME(ui):
    job = cmds.scriptJob(
        e=("SelectionChanged", 'geoTagTool.getAssName(["' + ui[0] + '", "' + ui[1] + '"])'),
        protected=True
    )
    return job

def makeScriptJobExport(ui):
    job = cmds.scriptJob(
        e=("SelectionChanged", 'geoTagTool.getBasePath("' + ui + '")'),
        protected=True
    )
    return job

def makeScriptJobSubD(ui):
    job = cmds.scriptJob(
        e=("SelectionChanged", 'geoTagTool.getSubD(["' + ui[0] + '", "' + ui[1] + '"])'),
        protected=True
    )
    return job

# SCRIPJOB FUNCTION TO RUN
def tagCheckValueUI(ui):
    sel = cmds.ls(sl=True, l=True)
    inf = 'mtoa_constant_type'
    if sel:
        sh = cmds.listRelatives(sel[0], s=True, ni=True, f=True)
        if sh:
            if cmds.attributeQuery(inf, n=sh[0], ex=True):
                val = cmds.getAttr(sh[0] + '.' + inf)
                cmds.textField(ui[0], e=True, tx=val)
    else:
        cmds.textField(ui[0], e=True, tx='')

# ---------------------------------------------------------------------------------------------
# ATTRIBUTES SET/GET STUFF
# ---------------------------------------------------------------------------------------------

# MESH ARNOLD VALUES
def getSubD(ui):
    sel = cmds.ls(sl=True, l=True)
    if sel:
        sh = cmds.listRelatives(sel[0], s=True, ni=True, f=True)
        if sh:
            if cmds.attributeQuery('aiSubdivType', n=sh[0], ex=True):
                val1 = cmds.getAttr(sh[0] + '.aiSubdivType')
                cmds.optionMenu(ui[0], e=True, sl=val1 + 1)
                val2 = cmds.getAttr(sh[0] + '.aiSubdivIterations')
                cmds.intField(ui[1], e=True, v=val2)
    else:
        cmds.optionMenu(ui[0], e=True, sl=1)
        cmds.intField(ui[1], e=True, v=0)

def setSubD(subT, subL):
    sel = cmds.ls(sl=True, l=True)
    if sel:
        sh = cmds.listRelatives(sel[0], s=True, ni=True, f=True)
        if sh:
            if cmds.attributeQuery('aiSubdivType', n=sh[0], ex=True):
                cmds.setAttr(sh[0] + '.aiSubdivType', subT - 1)
                cmds.setAttr(sh[0] + '.aiSubdivIterations', subL)

# IDs PRESETS
def readIDs():
    IDs = [
        'brick', 'cement', 'ceramic', 'clay', 'clearcoat',
        'decal', 'glass', 'grass', 'ice', 'leaf', 'leather',
        'marble', 'moss', 'paint', 'paper', 'plaster', 'plastic',
        'rock', 'rubber', 'sand', 'snow', 'soil', 'stone',
        'textile', 'tile', 'water', 'wood', 'woodPolished',
        'darkMetal', 'lightMetal', 'metal', 'paintedMetal',
        'polishedMetal', 'rustyMetal', 'blood', 'bone', 'eyeCornea',
        'eyeIris', 'eyeScalera', 'feather', 'fur', 'hair', 'skin',
        'incandescent', 'transparent', 'volume', 'collector',
        'red', 'green', 'blue', 'unique1', 'unique2', 'unique3']
    return sorted(IDs)

def addCustomIDsList(ui):
    ids = readIDs()
    items = cmds.optionMenu(ui, q=True, ill=True)
    if items:
        for i in items:
            cmds.deleteUI(i)
    for i in ids:
        # cmds.menuItem(l='mtoa_constant_' + i, p=ui)
        cmds.menuItem(l=i, p=ui)

def addCustomIDsListVal(ui):
    val = cmds.optionMenu(ui[0], q=True, v=True)
    cur = val.split('_')[-1]
    if cur:
        # if 'hair' in val or 'fur' in val or 'feather' in val:
        #     cmds.textField(ui[1], e=True, tx=cur + '_aiStandardHair')
        # elif 'volume' in val:
        #     cmds.textField(ui[1], e=True, tx=cur + '_aiStandardVolume')
        # else:
        #     cmds.textField(ui[1], e=True, tx=cur + '_aiStandardSurface')
        cmds.textField(ui[1], e=True, tx=cur)

# ASSET NAMES PART
def getAssName(ui):
    out, out1, dir = '', '', 0
    sel = cmds.ls(sl=True)
    for s in sel:
        sh = cmds.listRelatives(s, s=True, ni=True, f=True)
        if sh:
            for ss in sh:
                if cmds.nodeType(ss) == 'mesh' or cmds.nodeType(ss) == 'nurbsCurve' or cmds.nodeType(ss) == 'nurbsSurface' :
                    if cmds.attributeQuery('assetName', n=ss, ex=True):
                        out = cmds.getAttr(ss + '.assetName')
                    if cmds.attributeQuery('assetType', n=ss, ex=True):
                        out1 = cmds.getAttr(ss + '.assetType')
                    dir = 1
    if dir == 1:
        infos = {ui[0]: out, ui[1]: out1}
        for i in list(infos.keys()):
            if cmds.textField(i, q=True, ex=True):
                cmds.textField(i, e=True, tx=infos[i])

def getAssetsInfo():
    sel, out, ids, asset = [], {}, [], ''
    # GET ALL TRANSFORMS
    sel = cmds.ls(type='transform')
    # GET ASSETS
    for s in sel:
        sh = cmds.listRelatives(s, s=True, ni=True, f=True)
        if sh:
            for ss in sh:
                nt = cmds.nodeType(ss)
                if nt =='mesh' or nt == 'nurbsCurve' or nt == 'nurbsSurface':
                    if cmds.attributeQuery('assetName', n=ss, ex=True) and cmds.attributeQuery('id', n=ss, ex=True):
                        asset = cmds.getAttr(ss + '.assetName')
                        id = cmds.getAttr(ss + '.id')
                        ids.append(int(id))
            if asset:
                out[asset] = sorted(list(set(ids)))
    return out

# INDEX FUNCTIONS
def getIndex(ui):
    out, dir = 0, 0
    sel = cmds.ls(sl=True)
    for s in sel:
        sh = cmds.listRelatives(s, s=True, ni=True, f=True)
        if sh:
            for ss in sh:
                if cmds.nodeType(ss) == 'mesh' or cmds.nodeType(ss) == 'nurbsCurve' or cmds.nodeType(ss) == 'nurbsSurface' :
                    if cmds.attributeQuery('id', n=ss, ex=True):
                        out = cmds.getAttr(ss + '.id')
                        dir = 1
    if dir == 1:
        cmds.intField(ui, e=True, v=int(out))

def setIndex(id):
    sel = cmds.ls(sl=True, dag=True, l=True)
    if not sel:
        cmds.warning('Please select a mesh or a group to be tagged')
        return
    for s in sel:
        sh = cmds.listRelatives(s, s=True, ni=True, f=True)
        if sh:
            for ss in sh:
                if cmds.nodeType(ss) == 'mesh' or cmds.nodeType(ss) == 'nurbsCurve' or cmds.nodeType(ss) == 'nurbsSurface' :
                    if cmds.attributeQuery('id', n=ss, ex=True):
                        try:
                            cmds.setAttr(ss + '.id', id, type='string')
                        except:
                            cmds.setAttr(ss + '.id', id)
                        print('ID set to ' + str(id) + ' for this node ' + ss.split('|')[-1])

# GET INFO OF STRUCTURE
def getShadingInfo(debug, dir=None):
    infoAST = {}
    assets = getAssetsInfo()
    if not assets:
        cmds.warning('No tagged assets in this scene')
        return
    for asset in list(assets.keys()):
        index = {}
        # GET ALL TRANSFORMS
        for i in assets[asset]:
            sel = cmds.ls(type='transform')
            coll = []
            for s in sel:
                sh = cmds.listRelatives(s, s=True, ni=True, f=True)
                if sh:
                    for ss in sh:
                        nt = cmds.nodeType(ss)
                        if nt =='mesh' or nt == 'nurbsCurve' or nt == 'nurbsSurface':
                            if cmds.attributeQuery('assetName', n=ss, ex=True) and cmds.attributeQuery('id', n=ss, ex=True):
                                cur = cmds.getAttr(ss + '.assetName')
                                id = cmds.getAttr(ss + '.id')
                                if cur == asset:
                                    if str(i) == str(id):
                                        out = {}
                                        # attrs = cmds.listAttr(ss, ud=True)
                                        attrs = cmds.listAttr(ss)
                                        if attrs:
                                            shady = {}
                                            for a in attrs:
                                                # if 'mtoa_constant' in a:
                                                if 'mtoa_constant' in a or a.startswith('ai') and a != 'aiFilters':
                                                    value = cmds.getAttr(ss + '.' + a)
                                                    if type(value) == list:
                                                        shady[a] = value[0]
                                                    else:
                                                        shady[a] = value
                                            ssC = ss.split('|')[-1].split(':')[-1]
                                            out[ssC] = shady
                                            coll.append(out)
                                        index[id] = coll
        infoAST[asset] = index
    # for i in infoAST.keys():
    #     if i:
    #         for ii in infoAST[i].keys():
    #             exportShaingInfo(i, infoAST[i][ii], ii, debug, dir)
    exportShaingInfo(infoAST, debug, dir)

def exportShaingInfo(data, debug=None, dir=None):
    cur, out = {}, {}
    path = getBasePath()[0]
    sceneNC = getBasePath()[1]
    # DEBUG MODE
    if debug:
        pprint(data)
        return
    # JSON FILE
    jFile = os.path.join(path, sceneNC + '.json').replace('\\', '/').replace('//', '/')
    if dir:
        if not os.path.isdir(dir):
            cmds.warning('The selected location doesn\'t exist')
            return
        jFile = os.path.join(dir, sceneNC + '.json').replace('\\', '/').replace('//', '/')
    if not os.path.isdir(dir):
        os.makedirs(dir)
        cmds.warning('Created new directory\n' + dir)
    with open(jFile, 'w') as jf:
        data = json.dump(data, jf, indent=4)
        print('File saved here ' + jFile)

def exportShaingInfo_old(asset, data, id, debug=None, dir=None):
    cur, out = {}, {}
    path = getBasePath()[0]
    sceneNC = getBasePath()[1]
    # DATA
    cur[id] = data
    out[asset] = cur
    if debug:
        # cmds.confirmDialog(t='Asset Shading info', m=pformat(out))
        pprint(out)
        return
    # JSON FILE
    # dir = os.path.join(path, sceneNC)
    # jFile = os.path.join(path, asset + str(id) + '.json').replace('\\', '/').replace('//', '/')
    jFile = os.path.join(path, sceneNC + '.json').replace('\\', '/').replace('//', '/')
    if dir:
        jFile = os.path.join(dir, sceneNC + '.json').replace('\\', '/').replace('//', '/')
    if not os.path.isdir(dir):
        os.makedirs(dir)
        cmds.warning('Created new directory\n' + dir)
    with open(jFile, 'w') as jf:
        data = json.dump(out, jf, indent=4)
        print('File saved here ' + jFile)

# EXTENSIONS CHECK
def extChecker(node):
    out = ''
    exts = ['_grp', '_geo', '_mesh', '_crv', '_surf']
    match = {
        'transform': ['_grp'],
        'mesh': ['_mesh', '_geo'],
        'nurbsCurve': ['_crv'],
        'nurbsSurface': ['_surf']}
    for e in exts:
        if e in node:
            out = node
    if out:
        return out
    else:
        type = ''
        sh = cmds.listRelatives(node, s=True)
        if sh:
            type = cmds.nodeType(sh[0])
        else:
            type = cmds.nodeType(node)
        if type:
            print('Skipping ' + node + ' of type ' + type + ' because missing right extension "' + '" "'.join(match[type]) + '"')
        else:
            print('Skipping ' + node + ' because missing right extension')

# -----------------------------------------------------------------------------
# SCENE RELATED STUFF
# -----------------------------------------------------------------------------
def getSceneAssets():
    data = {}
    for sel in cmds.ls(type='transform'):
        if cmds.attributeQuery('assetName', n=sel, ex=True):
            children = cmds.ls(sel, dag=True)
            if children:
                for child in children:
                    nt = cmds.nodeType(child)
                    if nt != 'transform':
                        if cmds.attributeQuery('assetName', n=child, ex=True):
                            asset = str(cmds.getAttr(child + '.assetName'))
                            if cmds.attributeQuery('id', n=child, ex=True):
                                id = int(cmds.getAttr(child + '.id'))
                                ns = child.split(':')[0].split('|')[-1]
                                if asset not in data:
                                    data[asset] = {}
                                if id not in data[asset]:
                                    data[asset][id] = []
                                if ns not in data[asset][id]:
                                    data[asset][id].append(ns)
    return data

def getAllJson(jsonD, ui, latest):
    outD, outT = {}, {}
    if jsonD:
        if not os.path.isdir(jsonD):
            cmds.confirmDialog(t='error', m='The chosen location doesn\'t exists')
            return
        jsons = os.listdir(jsonD)
        if latest:
            for j in sorted(jsons):
                if j.endswith('.json'):
                    version = j.split('_v')[-1].split('.')[0]
                    outT[j.split('_v')[0]] = version
                    if '.v' in j:
                        version = j.split('.v')[-1].split('.')[0]
                        outT[j.split('.v')[0]] = version
            for o in list(outT.keys()):
                outD[o + '_v' + str(outT[o]) + '.json'] = outT[o]
        else:
            for j in sorted(jsons):
                if j.endswith('.json'):
                    version = j.split('_v')[-1].split('.')[0]
                    if '.v' in j:
                        version = j.split('.v')[-1].split('.')[0]
                    outD[j] = version

        cmds.textScrollList(ui, e=True, ra=True)
        for o in sorted(outD.keys()):
            cmds.textScrollList(ui, e=True, a=o)
        # pprint(outD)

def applyShadingInfo(jsonD, ui):
    if not os.path.isdir(jsonD):
        cmds.confirmDialog(t='error', m='The chosen location doesn\'t exists')
        return
    jsons = cmds.textScrollList(ui, q=True, si=True)
    if not jsons:
        cmds.confirmDialog(t='error', m='Please select some files in the list')
        return
    for j in jsons:
        data = {}
        jsonF = os.path.join(jsonD, j)
        with open(jsonF, 'r') as f:
            data = json.load(f)
        if not data:
            cmds.confirmDailog(t='Error', m='This json ' + j + ' file has no data')
            pass
        assets = getSceneAssets()
        for asset in list(assets.keys()):
            for i in assets[asset]:
                id = i
                if data.get(asset):
                    result = False
                    if data[asset].get(str(i)):
                        nss = assets[asset][id]
                        if nss:
                            for ns in nss:
                                for ii in data[asset][str(i)]:
                                    for shape in list(ii.keys()):
                                        obj = ns + ':' + shape
                                        if cmds.objExists(obj):
                                            for attr in list(ii[shape].keys()):
                                                if cmds.attributeQuery(attr, n=obj, ex=True):
                                                    curV = cmds.getAttr(obj + '.' + attr)
                                                    val = ii[shape][attr]
                                                    if type(val) == list:
                                                        # print obj + '.' + attr, 'array = ', val[0], val[1], val[2]
                                                        cmds.setAttr(obj + '.' + attr, val[0], val[1], val[2])
                                                    elif type(val) == str:
                                                        # print obj + '.' + attr, 'string = ', val
                                                        cmds.setAttr(obj + '.' + attr, val, type='string')
                                                    else:
                                                        # print obj + '.' + attr, val
                                                        cmds.setAttr(obj + '.' + attr, val)
                                                    result = True
                                if result:
                                    print('\n')
                                    print('=' * len(jsonF))
                                    print('Data from this file:\n' +  jsonF + '\nhas read into\nasset: "' + asset + '"\nid: ' + str(id) + '\nnamespace: "' + ns + '"')
                                    print('-' * len(jsonF))
                    if not result:
                        cmds.warning('nothing to read from this file ' +  j  + ' onto this scene')
    print('\n', '*' * len(jsonF), '\n\n', (' ' * (len(jsonF)/2 - len('All Done')/2) ) + 'All Done', '\n\n', '*' * len(jsonF))

def operatorNSAdd(debug):
    result = False
    counter = 0
    ops = cmds.ls(type='aiSetParameter')
    if not ops:
        cmds.warning('There are no \'aiSetParameter\' nodes in the scene')
        return
    for o in ops:
        tipo = cmds.nodeType(o)
        if tipo == 'aiSetParameter':
            if len(o.split(':')) == 1 :
                print('-*' * 75)
                print('skipping this node becasue doesn\'t have a namespace\n\t' + o)
            else:
                ns = o.replace(':' + o.split(':')[-1], '')
                if ns:
                    attrs = cmds.listAttr(o + '.assignment', m=True)
                    if attrs:
                        outI, info = {}, []
                        for a in attrs:
                            val = cmds.getAttr(o + '.' + a)
                            if val:
                                data = checkNS(ns, o, val)
                                if data:
                                    if debug:
                                        info.append(['From:', str(val), 'To:', str(data)])
                                    else:
                                        cmds.setAttr(o + '.' + a, data, type='string')
                                        result = True
                                        counter = counter + 1
                        if debug:
                            print('-' * 150)
                            outI[str(o)] = info
                            pprint(outI)
    if result:
        print('All DONE WHAT WE COULD :D')
        print(str(counter) + ' aiSetParameter nodes set to their relative namespace in the scene')

def checkNS(ns, node, val):
    exp, exns, out = '', '', ''
    # CLEAN WHITESPACES
    val = val.translate({ord(c): None for c in string.whitespace})
    token = val.split('\'')[0]
    if token == 'shader=' or token == 'disp_map=':
        exp = val.split('\'')[1]
        if len(exp.split(':')) > 1:
            # exns = exp.replace(exp.split(':')[-1], '')[:-1]
            exns = ns
            exp = exp.split(':')[-1]
        else:
            exns = ns
            exp = val.split('\'')[1]
        out = token + '\'' + exns  + ':' + exp + '\''
    else:
        out = val
    return out

# -----------------------------------------------------------------------------
# UI UTILITIES
# -----------------------------------------------------------------------------
def getBasePath(ui=None, dir=None):
    scene = cmds.file(q=True, sn=True, sh=True)
    sceneN = cmds.file(q=True, sn=True, shn=True)
    sceneNC = ('.').join(sceneN.split('.')[:-1])
    out = 'Export Location to be set by open scene ( Might need Relaunch UI )'
    if sceneN and 'untitled' not in sceneN:
        # out = (scene.split('work')[0] + 'publish/maya').replace('\\', '/')
        out = (scene.split('scenes')[0] + 'data').replace('\\', '/')
    if dir:
        out = dir
    if ui:
        if cmds.text(ui, q=True, ex=True):
            cmds.text(ui, e=True, l=out)
    return out, sceneNC

def setUiInfo(ui, tsl=None, last=None, data=None):
    base = cmds.textField(ui, q=True, tx=True)
    if not os.path.isdir(base):
        base = cmds.workspace(q=True, act=True).split('assets')[0].split('sequences')[0][:-1]
    loc = outGeneralUtil.oBrowser(2, base)
    if not loc:
        loc = cmds.textField(ui, q=True, tx=True)
        cmds.textField(ui, e=True, tx=loc)
    if data:
        if os.path.isdir(loc):
            getAllJson(loc, tsl, last)
    cmds.textField(ui, e=True, tx=loc)

# -----------------------------------------------------------------------------
# UI TOOLS
# -----------------------------------------------------------------------------
# MAIN UI
def geoTag_UI(mode=None):
    winN = 'tagTools_win'
    if cmds.window(winN, q=True, ex=True):
        cmds.deleteUI(winN)
    win = cmds.window(winN, t='TAG Tools', rtf=True)
    frb = cmds.formLayout(p=winN)
    tl = cmds.tabLayout(p=frb)
    frc = cmds.formLayout(p=tl)  # TAG UI
    frcc = cmds.formLayout(p=tl)  # SHADING UI
    frccc = cmds.formLayout(p=tl)  # OPERATORS UI
    cmds.tabLayout(
        tl,
        e=True,
        tl=(
            (frc, 'Tagging Geo'),
            (frcc, 'Tagging Shading'),
            (frccc, 'Operators')))
    cmds.formLayout(
        frb,
        e=True,
        af=[
            (tl, 'top', 0),
            (tl, 'left', 0),
            (tl, 'right', 0),
            (tl, 'bottom', 0)])

    # CLEAN SCRIPTJOBS
    cleanScriptJobs()
    # MAKE SCRIPJOBS
    jobID = tag_tools_UI(frc, mode)
    jobAT = shade_tools_UI(frcc)
    jobOp = operators_tools_UI(frccc)
    # SHOW WINDOW AND SIZE IT
    cmds.showWindow(win)
    cmds.window(win, e=True, w=300, h=260)
    # KILL FOR SCRIPTJOBS
    for jj in [jobID, jobAT, jobOp]:
        for j in jj:
            killScriptJobTagger(j, winN)

# TAG MESH UI
def tag_tools_UI(parent, tipo=None):
    if not tipo:
        tipo = ''
    fl = cmds.formLayout(p=parent)
    assN = cmds.text('Asset Name', p=fl)
    assNF = cmds.textField(p=fl)
    assINT = cmds.text('Asset ID', p=fl)
    assIN = cmds.intField(p=fl, w=50)
    idSet = cmds.button(l='Set ID', p=fl)
    assT = cmds.text('Asset Type', p=fl)
    assTF = cmds.textField(tx=tipo, p=fl)
    btTag = cmds.button(l='Tag Asset', p=fl)
    btUnTag = cmds.button(l='unTag Asset', p=fl)
    assTS = cmds.text('Set name', p=fl)
    assTFS = cmds.textField(tx='', p=fl)
    btSet = cmds.button(l='Make Export Set', p=fl)
    # ORGANIZE UI
    cmds.formLayout(
        parent, e=True,
        af=[
            (fl, 'top', 5),
            (fl, 'left', 5),
            (fl, 'right', 5),
            (fl, 'bottom', 5)
        ]
    )
    cmds.formLayout(
        fl,
        e=True,
        af=[
            (assN, 'left', 5), (assN, 'top', 5), (assN, 'right', 5),
            (assNF, 'left', 5), (assNF, 'right', 5),
            (assINT, 'left', 5), (assINT, 'right', 5),
            (assIN, 'left', 5),
            (idSet, 'right', 5),
            (assT, 'left', 5), (assT, 'right', 5),
            (assTF, 'left', 5), (assTF, 'right', 5),
            (btTag, 'left', 5), (btTag, 'right', 5),
            (btUnTag, 'left', 5), (btUnTag, 'right', 5),
            (assTS, 'left', 5), (assTS, 'right', 5),
            (assTFS, 'left', 5), (assTFS, 'right', 5),
            (btSet, 'left', 5), (btSet, 'right', 5)
        ],
        ac=[
            (assNF, 'top', 0, assN),
            (assINT, 'top', 5, assNF),
            (assIN, 'top', 5, assINT),
            (idSet, 'top', 5, assINT), (idSet, 'left', 5, assIN),
            (assT, 'top', 10, assIN),
            (assTF, 'top', 0, assT),
            (btTag, 'top', 15, assTF),
            (btUnTag, 'top', 15, btTag),
            (assTS, 'top', 5, btUnTag),
            (assTFS, 'top', 0, assTS),
            (btSet, 'top', 5, assTFS),
        ]
    )
    # ADD COMMANDS TO BUTTONS
    cmds.button(
        btTag,
        e=True,
        c='geoTagTool.do_tag(cmds.textField("' + assTF + '",q=True, tx=True), cmds.textField("' + assNF + '",q=True, tx=True), cmds.intField("' + assIN + '",q=True, v=True))')
    cmds.button(
        btUnTag,
        e=True,
        c='geoTagTool.attrClean(None, None)')
    cmds.button(
        btSet,
        e=True,
        c='geoTagTool.makeExportSet(cmds.textField("' + assTF + '",q=True, tx=True), cmds.textField("' + assNF + '",q=True, tx=True))')
    cmds.button(
        idSet,
        e=True,
        c='geoTagTool.setIndex(cmds.intField("' + assIN + '",q=True, v=True))')
    # ADD DISCIPLINES PRESETS
    pp1 = cmds.popupMenu('assetDisciplines', p=assTF)
    disciplines = ['MODEL', 'RIG', 'TEX', 'LOOKDEV']
    for d in sorted(disciplines):
        cmds.menuItem(
            l=d,
            p=pp1,
            c='cmds.textField("' + assTF + '", e=True, tx="' + d + '");cmds.textField("' + assTFS + '", e=True, tx="out_' + d.lower() + '_set")')
    # ADD ASSETS PRESETS
    pp2 = cmds.popupMenu('assetNames', p=assNF)
    assets = ['Biped', 'Bison', 'shark', 'Male', 'Female', 'Lion', 'dolphin', 'Cow', 'Horse', 'Prop']
    for a in sorted(assets):
        cmds.menuItem(
            l=a,
            p=pp2,
            c='cmds.textField("' + assNF + '", e=True, tx="' + a + '");')
    # ADD ASSETS PRESETS
    pp3 = cmds.popupMenu('assetNames', p=assIN)
    for x in range(0, 11):
        cmds.menuItem(
            l=str(x),
            p=pp3,
            c='cmds.intField("' + assIN + '", e=True, v=' + str(x) + ')')
    # ADD SCRIPTJOB
    job = makeScriptJobID(assIN)
    jobN = makeScriptJobNAME([assNF, assTF])
    # jobEx = makeScriptJobExport()
    # CHECK FOR ID AND NAME ON SELECTION
    getIndex(assIN)
    getAssName(assNF)

    return job, jobN

# SHADING TAG UI
def shade_tools_UI(parent):
    fl = cmds.formLayout(p=parent)
    oma = cmds.optionMenu(l='Shaders Tags              ')
    sepa = cmds.separator()
    shN = cmds.text('Shader Name', p=fl)
    shV = cmds.textField(p=fl)
    btEE = cmds.button(l='Edit Shader ID on mesh', p=fl)
    btSD = cmds.button(l='Set SUB-D on mesh', p=fl)
    omSD = cmds.optionMenu()
    inSD = cmds.intField(v=0)
    # ORGANIZE UI
    cmds.formLayout(
        parent, e=True,
        af=[
            (fl, 'top', 5),
            (fl, 'left', 5),
            (fl, 'right', 5),
            (fl, 'bottom', 5)
        ]
    )
    cmds.formLayout(
        fl, e=True,
        af=[
            (oma, 'left', 5), (oma, 'top', 5), (oma, 'right', 5),
            (sepa, 'left', 5), (sepa, 'right', 5),
            (shN, 'left', 5), (shN, 'right', 5),
            (shV, 'left', 5), (shV, 'right', 5),
            (btEE, 'left', 5), (btEE, 'right', 5),
            (btSD, 'left', 5),
            (omSD, 'left', 5)
            ],
        ap=[
            (btSD, 'right', 5, 50)
            ],
        ac=[
            (sepa, 'top', 5, oma),
            (shN, 'top', 5, sepa),
            (shV, 'top', 5, shN),
            (btEE, 'top', 5, shV),
            (btSD, 'top', 5, btEE),
            (omSD, 'top', 5, btEE), (omSD, 'left', 15, btSD),
            (inSD, 'top', 5, btEE), (inSD, 'left', 15, omSD),
        ]
    )
    # ADD UI COMMANDS
    cmds.optionMenu(
        oma, e=True,
        cc='geoTagTool.addCustomIDsListVal(["' + oma + '", "' + shV + '"])')
    cmds.button(
        btEE, e=True,
        c='geoTagTool.setDefaulAttr(["' + shV + '"])')
    cmds.button(
        btSD, e=True,
        c='geoTagTool.setSubD(cmds.optionMenu("' + omSD + '",q=True, sl=True), cmds.intField("' + inSD + '", q=True, v=True))')
    # ADD SUB-D STATES TO OPTION MENU
    states = ['none', 'catclark', 'linear']
    for s in states:
        cmds.menuItem(l=s, p=omSD)
    # ADD SCRIPTJOB
    job = makeScriptJobAT([shV])
    jobSD = makeScriptJobSubD([omSD, inSD])
    # CHECK FOR ATTRIBUTES ON SELECTION
    # ADD CUSTOM IDs TYPE TO UI
    addCustomIDsList(oma)
    return job, jobSD

# OPERATORS TAG UI
def operators_tools_UI(parent):
    fl = cmds.formLayout(p=parent)
    btFB = cmds.button(l='Export Location', p=fl)
    exTx = cmds.textField(tx='Export Location to be set by open scene', p=fl)
    btExp = cmds.button(l='Export Operators Assignment', p=fl)
    cbD = cmds.checkBox(l='Debug', v=True, p=fl)
    sepa = cmds.separator()
    btBF = cmds.button(l='Import Location', p=fl)
    imTx = cmds.textField(tx='Import Operators Assignment', p=fl)
    cbL = cmds.checkBox(l='latest', v=False)
    tsl = cmds.textScrollList(ams=True, p=fl)
    btImp = cmds.button(l='Import Operators Assignment', p=fl)
    btONS = cmds.button(l='Set Namespace for Operators in the Scene', p=fl)
    cbD2 = cmds.checkBox(l='Debug', v=True)

    # ORGANIZE UI
    cmds.formLayout(
        parent, e=True,
        af=[
            (fl, 'top', 5),
            (fl, 'left', 5),
            (fl, 'right', 5),
            (fl, 'bottom', 5)
        ]
    )
    cmds.formLayout(
        fl, e=True,
        af=[
            (btFB, 'left', 5), (btFB, 'top', 5),
            (exTx, 'right', 5), (exTx, 'top', 5),
            (btExp, 'left', 5),
            (cbD, 'right', 5),
            (sepa, 'right', 5), (sepa, 'left', 5),
            (btBF, 'left', 5),
            (imTx, 'right', 5),
            (tsl, 'left', 5), (tsl, 'right', 5),
            (btImp, 'left', 5),
            (btONS, 'left', 5), (btONS, 'bottom', 5),
            (cbD2, 'right', 5), (cbD2, 'bottom', 5)
            ],
        ap=[
            (btFB, 'right', 5, 25),
            (btExp, 'right', 5, 85),
            (btBF, 'right', 5, 25),
            (btImp, 'right', 5, 85),
            (btONS, 'right', 5, 85)
            ],
        ac=[
            (exTx, 'left', 10, btFB),
            (btExp, 'top', 5, btFB),
            (cbD, 'top', 5, btFB),
            (sepa, 'top', 10, btExp),
            (btBF, 'top', 10, sepa),
            (imTx, 'top', 10, sepa), (imTx, 'left', 5, btBF),
            (tsl, 'top', 5, btBF), (tsl, 'bottom', 5, btImp),
            (cbL, 'left', 5, btImp), (cbL, 'top', 5, tsl),
            (btImp, 'bottom', 10, btONS),
        ]
    )
    # ADD UI COMMANDS
    cmds.textField(exTx, e=True, tx=getBasePath()[0])
    cmds.button(
        btExp, e=True,
        c='geoTagTool.getShadingInfo(cmds.checkBox("' + cbD + '",q=True, v=True), cmds.textField("' + exTx + '",q=True, tx=True))')
    cmds.button(
        btFB, e=True,
        c='geoTagTool.setUiInfo("' + exTx + '")')
    cmds.textField(
        exTx, e=True,
        ec='geoTagTool.setUiInfo("' + exTx + '")')
    cmds.button(
        btBF, e=True,
        c='geoTagTool.setUiInfo("' + imTx + '", "' + tsl + '", cmds.checkBox("' + cbL + '", q=True, v=True), True)')
    cmds.textField(
        exTx, e=True,
        ec='geoTagTool.setUiInfo("' + imTx + '", "' + tsl + '", cmds.checkBox("' + cbL + '", q=True, v=True), True)')
    cmds.checkBox(
        cbL, e=True,
        cc='geoTagTool.getAllJson(cmds.textField("' + imTx + '", q=True, tx=True), "' + tsl + '", cmds.checkBox("' + cbL + '", q=True, v=True))')
    cmds.button(
        btImp, e=True,
        c='geoTagTool.applyShadingInfo(cmds.textField("' + imTx + '", q=True, tx=True), "' + tsl + '")')
    cmds.button(
        btONS, e=True,
        c='geoTagTool.operatorNSAdd(cmds.checkBox("' + cbD2 + '", q=True, v=True))')
    # ADD SCRIPTJOB
    jobEx = makeScriptJobExport(exTx)
    return [jobEx]
