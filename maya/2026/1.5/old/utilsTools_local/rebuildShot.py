'''
USAGE
import cachepipeline
reload(cachepipeline)
from cachepipeline import *
reload(rebuildShot)
rebuildShot.do_rebuildShot()
'''

import os
import json
import maya.mel as mel
import maya.cmds as cmds
from pprint import pprint


def cleanUnknown():
    sel = cmds.ls('*')
    for s in sel:
        if cmds.objExists(s):
            if cmds.nodeType(s) == 'unknown':
                print(s + ' is a unknown node')
                if cmds.objExists(s):
                    cmds.lockNode(s, l=False)
                    cmds.delete(s)
    # CLEAN TURTLE NODES
    cleanTurtle()
    # CLEAN BAD REFERENCE NODES
    cleanBadRefs()

def cleanTurtle():
    sel = cmds.ls('*urtle*')
    for s in sel:
        if cmds.objExists(s):
            cmds.lockNode(s, l=False)
            cmds.delete(s)
    if cmds.shelfTabLayout("TURTLE", q=True, ex=True):
        mel.eval('deleteShelfTab("TURTLE")')

def cleanBadRefs():
    refs = cmds.ls(type='reference')
    for r in refs:
        if 'sharedReference' not in r and 'UI' not in r and 'Camera' not in r:
            if 'UNKNOWN' in r:
                print('Deleted broken reference node: ' + r)
                cmds.delete(r)
    # CLEAN EXTRA REFERENCE NODES
    bad = cmds.ls('tmpOfflineForAtomRN*')
    for b in bad:
        cmds.lockNode(b, l=False)
        cmds.delete(b)

# CHECK IF ALL NEEDED PLUGINS ARE LOADED
def plugInCheck():
    plugs = ['AbcExport', 'AbcImport', 'gpuCache', 'atomImportExport']
    for p in plugs:
        state = cmds.pluginInfo(p, q=True, l=True)
        if not state:
            try:
                cmds.loadPlugin(p)
                print('Loaded plugin: ' + p)
            except:
                continue

# FIX MISSING NAMESPACES IN THE SCENE
def fixNameSpaces():
    topRef = cmds.file(q=True, r=True)
    for t in topRef:
        ns = cmds.file(t, q=True, ns=True)
        if not cmds.namespace(ex=ns):
            cmds.namespace(add=ns)
            print('Added missing namespace: ' + ns)

def cleanExtra():
    if cmds.optionVar(ex='scOpt_saveAndClearOptionVars'):
        mel.eval('scOpt_saveAndClearOptionVars(1);')

    # OPTIONS NOT TO CLEAN UP
    options = [
        'nurbsSrfOption', 'setsOption', 'partitionOption',
        'transformOption', 'displayLayerOption', 'renderLayerOption',
        'clipOption', 'poseOption', 'nurbsCrvOption',
        'unusedNurbsSrfOption', 'cachedOption', 'unusedSkinInfsOption',
        'expressionOption', 'shaderOption', 'locatorOption',
        'ptConOption', 'pbOption', 'snapshotOption',
        'unitConversionOption', 'referencedOption', 'brushOption',
        'unknownNodesOption', 'shadingNetworksOption']
    for o in options:
        mel.eval('optionVar -intValue ' + o + ' false;')

    # OPTIONS TO CLEAN UP
    mel.eval('optionVar -intValue groupIDnOption true;')
    mel.eval('optionVar -intValue deformerOption true;')
    mel.eval('optionVar -intValue animationCurveOption true;')

    mel.eval('cleanUpScene(1);')

# REBUILD SHOT
def do_rebuildShot(new=None):
    # CLEAN SCENE
    cleanUnknown()
    cleanExtra()
    # CHECK PLUGINS
    plugInCheck()
    # CREATE DATA STRUCTURE
    sc = cmds.file(q=True, sn=True)
    scn = cmds.file(q=True, sn=True, shn=True)
    loc = sc.replace(scn, '')
    ext = scn.split('.')[-1]
    ws = cmds.workspace(q=True, act=True)
    outD = os.path.join(ws, 'data', scn)
    if not os.path.isdir(outD):
        print('Making missing directory: ' + outD)
        os.makedirs(outD)
    # NEW SCENE
    nsc = os.path.join(loc, scn.replace('.' + ext, '.REBUILT.' + ext))
    tipo = 'mayaAscii'
    if ext ==  'mb':
        tipo = 'mayaBinary'
    # FIX MISSING NAMESPACES
    fixNameSpaces()
    # GET REFERENCE INFORMATION
    refs = cmds.ls(type='reference')
    for r in refs:
        if 'shared' not in r:
            try:
                cur = cmds.referenceQuery(r, f=True)
                if 'Rig' in cur:
                    if cmds.referenceQuery(r, il=True):
                        cmds.file(cmds.referenceQuery(r, f=True), ur=True)
                    cmds.referenceEdit(r, scs=True, r=True, ec='disconnectAttr')
                    cmds.referenceEdit(r, fld=True, r=True)
                    print('-' * 50)
                    print('Cleaned reference: ' + r)
                    print('-' * 50)
                elif 'cmm' in cur:
                    edits = cmds.referenceQuery(r, es=True)
                    if cmds.referenceQuery(r, il=True):
                        cmds.file(cmds.referenceQuery(r, f=True), ur=True)
                    cmds.file(cmds.referenceQuery(r, f=True), cr=r)
                    cmds.file(cmds.referenceQuery(r, f=True), lr=True)
                    for et in edits:
                        try:
                            exec('mel.eval(\'' + et + '\')')
                        except:
                            print('Skipping this command ' + et)
                    print('-' * 50)
                    print('Cleaned and rebuilt reference: ' + r)
                    print('-' * 50)
            except:
                cmds.warning('Skipped ' + r + ' because not associated to any reference file')
    # SAVE NEW SCENE
    msg = 'The scene has been rebuild but not saved'
    if new:
        if new == 1:
            # RENAME SCENE
            cmds.file(rename=nsc)
            # SAVE NEW SCENE
            cmds.file(s=True, type=tipo)
            msg = 'Shot Rebuilt and saved as :\n' + nsc
    # CONFRIM DIALOG
    result = cmds.confirmDialog(
        t='Tadaa', m=msg,
        b=['Reload References', 'Don\'t reload References'],
        db='Don\'t reload References', cb='Don\'t reload References', ds='Reload References')
    if result == 'Reload References':
        for r in refs:
            cmds.file(cmds.referenceQuery(r, f=True), lr=True)

def do_rebuildShot_anim(new=None, old=None):
    out = {}
    # CHECK PLUGINS
    plugInCheck()
    # CREATE DATA STRUCTURE
    sc = cmds.file(q=True, sn=True)
    scn = cmds.file(q=True, sn=True, shn=True)
    loc = sc.replace(scn, '')
    ext = scn.split('.')[-1]
    ws = cmds.workspace(q=True, act=True)
    outD = os.path.join(ws, 'data', scn).replace('\\', '/').replace('.ma', '')
    if not os.path.isdir(outD):
        print('Making missing directory: ' + outD)
        os.makedirs(outD)
    # MAIN RIG INFO
    rootRig = 'root_grp'
    ctrlSet = 'rig_controllers_grp'
    if old:
        rootRig = 'Character_COW'
        ctrlSet = 'character_cow_CTRLS'
    # NEW SCENE
    nsc = os.path.join(loc, scn.replace('.' + ext, '.REBUILT.' + ext))
    tipo = 'mayaAscii'
    if ext ==  'mb':
        tipo = 'mayaBinary'
    # FIX MISSING NAMESPACES
    fixNameSpaces()
    # GET REFERENCE INFORMATION
    refs = cmds.ls(type='reference')
    for r in refs:
        if 'shared' not in r and 'UI' not in r:
            try:
                if cmds.referenceQuery(r, il=True):
                    current = cmds.referenceQuery(r, f=True)
                    if 'Rig' in current and 'QPAS' not in r:
                        cur = [
                            cmds.referenceQuery(r, ns=True)[1:],
                            cmds.referenceQuery(r, f=True)]
                        out[r] = cur
                    elif 'cmm' in current:
                        edits = cmds.referenceQuery(r, es=True)
                        if cmds.referenceQuery(r, il=True):
                            cmds.file(cmds.referenceQuery(r, f=True), ur=True)
                        cmds.file(cmds.referenceQuery(r, f=True), cr=r)
                        cmds.file(cmds.referenceQuery(r, f=True), lr=True)
                        for et in edits:
                            try:
                                exec('mel.eval(\'' + et + '\')')
                            except:
                                print('Skipping this command ' + et)
                        msg = 'Cleaned and rebuilt reference: ' + r
                        print('=' * len(msg))
                        print(msg)
                        print('=' * len(msg))
            except:
                cmds.warning('Skipped ' + r + ' because not associated to any reference file')
    pprint(out)
    # SAVE ANIMATION DATA WITH ATOM
    start = str(cmds.playbackOptions(q=True, min=True))
    end = str(cmds.playbackOptions(q=True, max=True))
    for o in list(out.keys()):
        # CHECK IF THE REFERENCE IS LOADED
        if not cmds.referenceQuery(out[o][1], il=True):
            if 'Rig' in out[o][1]:
                # LOAD REFERENCE
                cmds.file(cmds.referenceQuery(o, f=True), lr=True)
        # SELECT ALL CONTROLLERS OF THE RIG TO EXPORT ANIMATION
        if cmds.objExists(out[o][0] + ':' + ctrlSet):
            # CHECK PARENTING LEVEL OF RIG
            fa = cmds.listRelatives(out[o][0] + ':' + rootRig, p=True)
            # GET ALL THE CONTROLERS
            ctrls = cmds.sets(out[o][0] + ':' + ctrlSet, q=True)
            cmds.select(ctrls, r=True)
            # SET WHERE TO SAVE THE ATOM ANIM FILE
            filename = out[o][0].replace(':', '_')
            outAnim = os.path.join(outD, filename).replace('\\', '/')
            msg = 'Exporting animation file here: ' + outAnim
            print('-' * len(msg))
            print(msg)
            print('-' * len(msg))
            cmds.refresh()
            cmds.file(
                outAnim + '.atom',
                force=True,
                options='precision=8;exportEdits=' + outAnim + '.editMA;statics=1;baked=1;sdk=0;constraint=1;animLayers=1;selected=selectedOnly;whichRange=2;range=' + start + ':' + end + ';hierarchy=none;controlPoints=0;useChannelBox=1;options=keys;copyKeyCmd=-animation objects -time >' + start + ':' + end + '> -float >' + start + ':' + end + '> -option keys -hierarchy none -controlPoints 0 ',
                typ='atomExport',
                es=True)
            # UNLOAD REFERENCE
            cmds.file(
                cmds.referenceQuery(o, f=True), ur=True)
            # CLEAN EDITS
            cmds.file(
                cmds.referenceQuery(o, f=True), cr=o)
            # RELOAD REFERENCE
            cmds.file(cmds.referenceQuery(o, f=True), lr=True)
            # SELECT CONTROLLERS OF ASSET
            cmds.select(ctrls, r=True)
            # APPLY ANIMATION BACK
            ns = out[o][0]
            if ns.split(':') > 1:
                ns = out[o][0].split(':')[0]
            cmds.file(
                outAnim + '.atom',
                i=True,
                type="atomImport",
                ra=True,
                namespace=ns,
                options=";;targetTime=3;option=scaleReplace;match=string;;selected=selectedOnly;search=;replace=;prefix=;suffix=;mapFile=;")
            # REPARENT ASSET IF NEEDED
            if fa:
                cmds.parent(out[o][0] + ':' + rootRig, fa[0])
            # UNLOAD REFERENCE
            cmds.file(
                cmds.referenceQuery(o, f=True), ur=True)
        else:
            cmds.warning('Skipping : "' + out[o][0] + ':' + ctrlSet + '" because not in the scene')
    # CLEAN SCENE
    cleanExtra()
    # SAVE NEW SCENE
    msg = 'The scene has been rebuild but not saved'
    if new == 1:
        # RENAME SCENE
        cmds.file(rename=nsc)
        # SAVE NEW SCENE
        cmds.file(s=True, type=tipo)
        msg = 'Shot Rebuilt and saved as ' + nsc
    # CONFRIM DIALOG
    result = cmds.confirmDialog(
        t='Tadaa', m=msg,
        b=['Reload References', 'Don\'t reload References'],
        db='Don\'t reload References', cb='Don\'t reload References', ds='Reload References')
    if result == 'Reload References':
        for r in refs:
            cmds.file(cmds.referenceQuery(r, f=True), lr=True)

# out = {}
# refs = cmds.ls(type='reference')
# for r in refs:
#     if 'shared' not in r:
#         if 'Rig' in cmds.referenceQuery(r, f=True):
#             if not cmds.referenceQuery(r, il=True):
#                 print r
#                 cmds.referenceEdit(r, scs=True, r=True, ec='disconnectAttr')
