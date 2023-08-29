from pprint import pprint
from importlib import reload
import atelier_utils
reload(atelier_utils)
import lookdev_utils
reload(lookdev_utils)
from maya import mel, cmds
import os, json, tempfile, time
from datetime import timedelta

# MAKE A POPUP FOR ASSET TO BE REFERENCED

def getShrd(abc, disc):
    shrd = ''
    new = os.path.join(abc.split(disc)[0], 'surfacing/scripts/maya/scenes')
    if os.path.isdir(new):
        shrd = atelier_utils.getLast(new, 'ma')
    return(shrd).replace('\\', '/')


def get_Asset():
    out = {}
    start = time.time()
    base = 'Z:/jobs/GEX/'
    modes = ['assets']
    for m in modes:
        info = {}
        cur = os.path.join(base, m)
        for root, dirs, files in os.walk(cur, topdown=False):
            data = []
            for d in dirs:
                if d == 'maya':
                    maya_cur = atelier_utils.unixifyPath(os.path.join(root, d))
                    abc_cur = atelier_utils.unixifyPath(os.path.join(root, d, 'cache/alembic'))
                    shot = maya_cur.split('/')[-4]
                    disc = maya_cur.split('/')[-3]
                    if os.path.isdir(abc_cur):
                        if disc in maya_cur:
                            abc = atelier_utils.getLast(abc_cur, 'abc', '_proxy_')
                            shrd = getShrd(abc, disc)
                            if abc:
                                if shot not in info:
                                    info[shot] = []
                                    info[shot].append(abc)
                                    if shrd:
                                        info[shot].append(shrd)
                                else:
                                    info[shot].append(abc)
                                    if shrd:
                                        info[shot].append(shrd)
        out[m] = info
    pprint(out)
    end = time.time()
    result = str(end - start)
    print(result.format(str(timedelta(seconds=66))))
    return(out)



def assets_UI():
    gToolBox = mel.eval('$tempVar = $gToolBox')
    # ASSET PICKER BUTTON
    if cmds.iconTextButton('mnmMauAssets', ex=True):
        cmds.deleteUI('mnmMauAssets')
    btt = cmds.iconTextButton(
        'mnmMauAssets',
        label='Asset Picker', w=33, h=30,
        i='asset.png',
        p=gToolBox)
    # UPDATE BUTTON
    if cmds.iconTextButton('mnmMauSwitchAssets', ex=True):
        cmds.deleteUI('mnmMauSwitchAssets')
    btp = cmds.iconTextButton(
        'mnmMauSwitchAssets',
        label='Proxy Switch', w=33, h=30,
        i='proxySwitch.png',
        p=gToolBox)
    pps = cmds.popupMenu('mnmAssBttm', p=btp)
    cmds.menuItem(label='Proxy Mode', p=pps, c='mayaAssets.proxySwitch(0)')
    cmds.menuItem(label='High Res', p=pps, c='mayaAssets.proxySwitch(1)')
    # UPDATE BUTTON
    if cmds.iconTextButton('mnmMauUpAssets', ex=True):
        cmds.deleteUI('mnmMauUpAssets')
    bta = cmds.iconTextButton(
        'mnmMauUpAssets',
        label='Asset Update', w=33, h=30,
        i='update_1.png',
        c='mayaAssets.checkUpdate()',
        p=gToolBox)
    # HERE WE GO
    data = get_Asset()
    ppc = cmds.popupMenu('mnmAssBttm', p=btt)
    for t in data.keys():
        mt = cmds.menuItem(label=t, p=ppc, subMenu=True)
        for s in data[t]:
            ms = cmds.menuItem(label=s, p=mt, subMenu=True)
            asset = data[t][s][0].split('/')[-1].split('_modeling')[0]
            name = 'FULL ASSET - ' + asset
            cmd = ''
            for d in data[t][s]:
                ns = d.split('/')[-1].replace('.', '_')
                tipo = 'Alembic'
                if d.endswith('ma'):
                    tipo = 'mayaAscii'
                cmd += 'cmds.file("' + d + '", r=True, type="' + tipo + '", ignoreVersion=True, gl=True, mergeNamespacesOnClash=False, namespace="' + ns + '");'
                # PART FOR LOOPING ALEMBIC OCEAN NODE
                if not d.endswith('ma'):
                    if s == 'ocean':
                        cmd += 'cmds.setAttr("' + ns + ':water_setup_v001_AlembicNode.cycleType", 1);'
            cmd += 'import lookdev_utils;lookdev_utils.setShaderForShot();'
            cmd += 'print(\'Referenced asset:    ' + name + '\')'
            cmds.menuItem(label=name, p=ms, c=cmd)
            cmds.menuItem(d=True, p=ms)
            for d in data[t][s]:
                name = d.split('/')[-1]
                ns = d.split('/')[-1].replace('.', '_')
                tipo = 'Alembic'
                disc = d.split('/')[-6]
                if d.endswith('ma'):
                    tipo = 'mayaAscii'
                    disc = d.split('/')[-5]
                cmd = 'cmds.file("' + d + '", r=True, type="' + tipo + '", ignoreVersion=True, gl=True, mergeNamespacesOnClash=False, namespace="' + ns + '")'
                # PART FOR LOOPING ALEMBIC OCEAN NODE
                if not d.endswith('ma'):
                    if s == 'ocean':
                        cmd += ';cmds.setAttr("' + ns + ':water_setup_v001_AlembicNode.cycleType", 1)'
                if disc == 'surfacing':
                    cmd += ';import lookdev_utils;lookdev_utils.setShaderForShot()'
                cmd += ';print(\'Referenced asset:    ' + d + '\')'
                cmds.menuItem(label=disc + ' - ' + name, p=ms, c=cmd)


def checkUpdate():
    out = {}
    refs = cmds.ls(type='reference')
    if refs:
        for r in refs:
            if 'shared' in r:
                continue
            cur = ''
            try:
                cur = cmds.referenceQuery(r, f=True).split('{')[0]
            except:
                cmds.lockNode(r, l=False)
                cmds.delete(r)
                cmds.warning('Deleted dirty reference node: ' + r)
            if cur:
                path = cur.replace('/' + cur.split('/')[-1], '')
                if 'camera' not in path:
                    ext = cur.split('.')[-1]
                    up = atelier_utils.getLast(path, ext, ['_proxy_'])
                    if up != cur:
                        out[r] = up
    if not out:
        cmds.confirmDialog(t='Coolio !!!', m='Everything is up to date, references wise')
    else:
        msg = 'Here what is needed to be updated:\n\n'
        for o in out.keys():
            msg += o + ':\n\t' + out[o].split('/')[-1] + '\n'
        result = cmds.confirmDialog(t='Watch out !!!', m=msg, b=['Update', 'Leave it alone'], db='Update')
        if result == 'Update':
            upAssets()


def upAssets():
    out = {}
    refs = cmds.ls(type='reference')
    if refs:
        for r in refs:
            if 'shared' in r:
                continue
            cur = cmds.referenceQuery(r, f=True).split('{')[0]
            if cur:
                path = cur.replace('/' + cur.split('/')[-1], '')
                ext = cur.split('.')[-1]
                up = atelier_utils.getLast(path, ext, '_proxy_')
                tipo = 'Alembic'
                if ext == 'ma':
                    tipo = 'mayaAscii'
                if up != cur:
                    out[r] = up
                    ns = cmds.referenceQuery(r, ns=True)
                    cmds.file(up, loadReference=r, type=tipo)
                    lookdev_utils.setShaderForShot()
                    if 'water' in ns:
                        if cmds.objExists(ns + ':water_setup_v001_AlembicNode'):
                            cmds.setAttr(ns + ':water_setup_v001_AlembicNode.cycleType', 1)



def proxySwitch(mode):
    tag = 'Proxy'
    refs = cmds.ls(type='reference')
    if refs:
        for r in refs:
            if 'shared' in  r:
                continue
            cur = cmds.referenceQuery(r, f=True).split('{')[0]
            path = cur.replace('/' + cur.split('/')[-1], '')
            name = cur.split('/')[-1]
            if '_modeling_' in name:
                new_name = name.replace('_v', '_proxy_v')
                if mode == 1:
                    tag = 'High'
                    new_name = name.replace('_proxy_v', '_v')
                proxy = atelier_utils.unixifyPath(os.path.join(path, new_name))
                if cur != proxy:
                    if os.path.isfile(proxy):
                        tipo = atelier_utils.getSceneType(proxy)
                        print(proxy)
                        cmds.file(proxy, loadReference=r, type=tipo)
                    else:
                        print('Missing ' + tag + ' for ' + name)
                else:
                    print('Proxy and High res are the same for ' + name)
        cmds.confirmDialog(t=tag + ' !!!', m='Everything is set to ' + tag + '                                 ')
    else:
        cmds.confirmDialog(t='Oopps !!!', m='There are no references in this shot')
