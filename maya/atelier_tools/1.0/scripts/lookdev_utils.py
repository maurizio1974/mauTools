import os
import sys
import maya.mel as mel
import maya.cmds as cmds
import atelier_utils



def operatorShot_setup():
    # clean previos operator master setup 
    ops = cmds.ls('*_OPERATOR_SETUP', type='aiMerge')
    if ops:
        for o in ops:
            cmds.delete(o)
            print('Cleaned previous setup ' + o)
    filepath = cmds.file(q=True, sn=True)
    filename = os.path.basename(filepath).split('_v')[0]
    setP = cmds.ls(type='aiMerge')
    if setP:
        nodes = []
        master = 'SCENE_' + filename + '_OPERATOR_SETUP'
        if not cmds.objExists(master):
            cmds.createNode('aiMerge', n=master)
            if cmds.objExists('defaultArnoldRenderOptions'):
                cmds.connectAttr(master + '.message', 'defaultArnoldRenderOptions.operator', f=True)
            else:
                cmds.confirmDialog(t='error', m='PLease open the arnold render settings one and then re-run the tool')
        for s in setP:
            if s != master:
                nodes.append(s)

        for x, n in enumerate(nodes):
            print('Connecting', n, 'to plug:', x)
            try:
                cmds.connectAttr(n + '.out', master + '.inputs[' + str(x) + ']', f=True)
            except:
                print(n + '.out', master + '.inputs[' + str(x) + ']' + ' is Already Connected')
        setShaderForShot()
    else:
        cmds.confirmDialog(
            t='error', m='Not aiSetParameters for shader assignement in the shot')


def getAssignPlug(node, assign):
    idx = ''
    for x in range(0, 10):
        val = cmds.getAttr(node + '.assignment[' + str(x) + ']')
        if assign + '=' not in val:
            continue
        idx = str(x)
    if idx:
        return idx
        

def setShaderForShot():
    # Assign in shot
    sel = cmds.ls(type='aiSetParameter')
    if not sel:
        cmds.confirmDialog(
            t='error', m='Not aiSetParameters for shader assignement in the shot')
        return
    for s in sel:
        ns = atelier_utils.getNs(s)
        if not ns:
            print('Skipping ' + s + ' because it doesn\'t have a namespace so no changes needed')
            continue
        # attrs = cmds.listAttr(s)
        idx = getAssignPlug(s, 'shader')
        if idx:
            if ns:
                curA = 'assignment[' + idx + ']'
                val = cmds.getAttr(s + '.' + curA)
                shrd = val.split('=')[-1].replace('\'', '')
                if len(val.split(':')) > 1:
                    shrd = val.split('=')[-1].replace('\'', '').split(':')[-1]
                new = "shader='" + ns + shrd + "'"
                print('Changed: ' + val)
                print('To:      ' + new)
                cmds.setAttr(s + '.' + curA, new, type='string')


def fixCryptomatte():
    out = []
    aovs = cmds.ls(type='aiAOV')
    if aovs:
        for a in aovs:
            if 'crypto' in a:
                out.append(a)
        if out:
            crypto = ''
            sel = cmds.ls(type='cryptomatte')
            if not sel:
                crypto = cmds.createNode('cryptomatte', n='_aov_cryptomatte')
            else:
                crypto = sel[0]
            for o in out:
                cmds.connectAttr(crypto + '.outColor', o + '.defaultValue', f=True)
            cmds.confirmDialog(t='Ta Da !!!', m='Fixed Cryptomatte on this shot')
        else:
            cmds.confirmDialog(t='Yo Yo Yo Dude !!!', m='There are not cryptomatte AOVs in this shot, make some please')
    else:
        cmds.confirmDialog(t='Da Fuck !!!', m='There are not AOVs at all in this scene, make some please')