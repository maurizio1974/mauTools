'''----------------------------------------------------------------------

DEFORMER VERTEX EXPORT/IMPORT UTILITY

Date = 28/10/2018
User = Maurizio Giglioli
Update =
        28/10/2018 Initial Commit

----------------------------------------------------------------------'''

import os
import json
import maya.cmds as cmds
from pprint import pprint

# VERTEX MAP -------------------------------------------------------------------
'''
USAGE
vertexDefUtil.nExportVtx('muscle_nCloth', ['inputAttractPerVertex'], 'nuscleus', 'Daisy', 'v003')
vertexDefUtil.nImportVtx('muscle_nCloth', ['inputAttractPerVertex'], 'nuscleus', 'Daisy', 'v003')
'''
# EXPORT
def nExportVtx(objS, vtxm, asset, mapType, version):
    # ACTIVE DIRECTORY
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(ws, 'export', mapType, asset, version)
    if not os.path.isdir(export):
        os.makedirs(export)
        cmds.warning('Created this directory ' + export)
    map = {}
    for v in vtxm:
        info = {}
        node = objS + '.' + v
        ia = str(cmds.getAttr(node))
        if ia:
            info[len(ia)] = ia
            map[node] = info
    # JASON FILE
    jFile = os.path.join(export, objS + '.json').replace('\\', '/')
    # SAVE TO FILE
    with open(jFile, 'w') as outF:
        json.dump(map, outF)
    print 'Data saved to this file: ' + jFile

def nImportVtx(objS, vtxm, asset, mapType, version):
    # ACTIVE DIRECTORY
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(ws, 'export', mapType, asset, version)
    # JASON FILE
    jFile = os.path.join(export, objS + '.json').replace('\\', '/')
    # LOAD THE DATA
    data = {}
    if os.path.isfile(jFile):
        with open(jFile) as jf:
            data = json.load(jf)
        for d in data.keys():
            cmd = 'cmds.setAttr('
            if cmds.objExists(d):
                for dd in data[d].keys():
                    cmd += '\'' + d + '\', ' + data[d][dd] + ', ' + str(dd) + ', type=\'doubleArray\')'
                    exec(cmd)
        print 'Data loaded from this file: ' + jFile

# DEFORMER WEIGHTS -------------------------------------------------------------
# EXPORT
def exportDeform(deform, version):
    nodes = []
    # GET CURRENT SELECTION
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    for s in sel:
        his = cmds.listHistory()
        for h in his:
            if cmds.nodeType(h) == deform:
                nodes.append(h)
    if not nodes:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    # CLEAN DUPLICATES
    nodes = list(set(nodes))
    # MAKE EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(
        ws, 'export/weights/', deform, version).replace('\\', '/')
    if not os.path.isdir(export):
        os.makedirs(export)
        cmds.warning('Created this directory ' + export)
    for n in nodes:
        current = os.path.join(export, n + ".xml")
        if os.path.isfile(current):
            result = cmds.confirmDialog(
                t='Watch it', m='This file already exists:\n' + current,
                b=['Over Write', 'Skip'], db='Skip', cb='Skip', ds='Skip')
            if result == 'Over Write':
                print 'Exported deformer weights for ' + n + ' of type ' + deform
                cmds.deformerWeights(n + ".xml", export=True, deformer=n, path=export)
            else:
                # index = 'v' + str(int(version.split('v')[-1]) + 1).zfill(3)
                # export = export.replace(version, index)
                # exportDeform(deform, index)
                # if not os.path.isdir(export):
                #     os.makedirs(export)
                #     cmds.warning('Made this directory: ' + export)
                # cmds.deformerWeights(n + ".xml", export=True, deformer=n, path=export)
                # cmds.warning(
                #     n + ' Upped version from \n'+ version + ' to ' + index)
                cmds.warning(
                    n + ' Skipped because \n'+ deform + ' file is there already')
        else:
            print 'Exported deformer weights for ' + n + ' of type ' + deform
            cmds.deformerWeights(n + ".xml", export=True, deformer=n, path=export)

# IMPORT
def importDeform(deform, version):
    nodes = []
    # GET CURRENT SELECTION
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    for s in sel:
        his = cmds.listHistory()
        for h in his:
            if cmds.nodeType(h) == deform:
                nodes.append(h)
    if not nodes:
        cmds.warning(
            'Plesase select geometry with this tipe of deformer: ' + deform)
        return
    # CLEAN DUPLICATES
    nodes = list(set(nodes))
    # GET EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    imp = os.path.join(
        ws, 'export/weights/', deform, version).replace('\\', '/')
    for n in nodes:
        skinfile = n + '.xml'
        if not os.path.isfile(os.path.join(imp, skinfile)):
            cmds.warning('This skin cluster doesn\'t exist ' + skinfile)
            return
        cmds.deformerWeights(
            skinfile, im=True, deformer=n, method='index', path=imp)
        print 'Imported deformer weights for ' + n + ' of type ' + deform

# SELECTIONS -------------------------------------------------------------------
# IMPORT
def importSel(version):
    data, name = {}, ''
    sel = cmds.ls(sl=True, fl=True)
    if not sel:
        cmds.warning('Please select eh mesh to import the selection to')
        return
    if len(sel[0].split('.')) > 1:
        name = sel[0].split('.')[0]
    else:
        name = sel[0]
    # GET IMPORT PATH
    ws = cmds.workspace(q=True, act=True)
    imp = os.path.join(
        ws, 'export/selections', version).replace('\\', '/')
    # READ FILE
    jFile = os.path.join(imp, name + '.' + version + '.json').replace('\\', '/')
    if not os.path.isfile(jFile):
        cmds.warning('This file doesn\'t exists check your project\n' + jFile)
        return
    with open(jFile, 'r') as inF:
        data = json.load(inF)
    cmds.select(cl=True)
    for d in data.keys():
        for t in data[d].keys():
            for index in data[d][t]:
                current = name + '.' + t + '[' + str(index) + ']'
                cmds.select(current, add=True)

# EXPORT
def exportSel(version):
    data, name, out, info = {}, '', [], {}
    sel = cmds.ls(sl=True, fl=True)
    if sel:
        if len(sel[0].split('.')) > 1:
            name = sel[0].split('.')[0]
            tipo = sel[0].split('.')[-1].split('[')[0]
            for s in sel:
                index = s.split('.')[-1].replace(tipo, '').replace('[', '').replace(']', '')
                out.append(index)
            data[tipo] = out
            info[name] = data
    # pprint(info)
    # MAKE EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    export = os.path.join(
        ws, 'export/selections', version).replace('\\', '/')
    if not os.path.isdir(export):
        os.makedirs(export)
        cmds.warning('Created this directory ' + export)
    # SAVE TO FILE
    jFile = os.path.join(export, name + '.' + version + '.json')
    with open(jFile, 'w') as outF:
        json.dump(info, outF)

# GEO --------------------------------------------------------------------------
# EXPORT
def exportObjs(prefix, version):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning('Please select one or more geoemtry meshes to be exported')
        return
    # MAKE EXPORT PATH
    ws = cmds.workspace(q=True, act=True)
    out = os.path.join(
        ws, 'export/objs', version).replace('\\', '/')
    for s in sel:
        sh = cmds.listRelatives(s, s=True, ni=True)
        if sh:
            if cmds.nodeType(sh[0]) == 'mesh':
                name = prefix + '_' + s + '_' + version + '.obj'
                exp = os.path.join(out, name).replace('\\', '/')
                cmds.file(
                    exp, force=True,
                    options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
                    typ="OBJexport", pr=True, es=True)
            else:
                cmds.warning('Skipping this node ' + s + ' because it is not a mesh')
    cmds.warning('ALL MESHES EXPORTED HERE:\n' + out)
