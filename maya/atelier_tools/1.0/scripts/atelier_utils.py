import os
import sys
import glob
import maya.mel as mel
import maya.cmds as cmds


def unixifyPath(path):
    path = path.replace('\\', '/')
    return path


def getSceneType(scene):
    ext = scene.split('.')[-1]
    tipo = 'Alembic'
    if ext == 'ma':
        tipo = 'mayaAscii'
    return tipo


def getNs(node):
    ns = ''
    check = node.split(':')
    if len(check) > 1:
        for s in check:
            if s != check[-1]:
                ns += s + ':'
    if ns:
        return ns


def getLast_old(loc, ext, exclude=None):
    latest_file = ''
    list_of_files = glob.glob(loc + '/*.' + ext)
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getmtime)
    return(unixifyPath(latest_file))


def getLast(loc, ext, exclude=None):
    out = []
    latest_file = ''
    list_of_files = os.listdir(loc)
    if list_of_files:
        for f in list_of_files:
            if os.path.isfile(os.path.join(loc, f)):
                if f.endswith(ext):
                    if exclude:
                        for e in exclude:
                            if e not in f:
                                out.append(os.path.join(loc, f))
                    else:
                        out.append(os.path.join(loc, f))
    if out:
        latest_file = max(out, key=os.path.getmtime)
    return(unixifyPath(latest_file))


def makeExportSet(obj=None):
    if not obj:
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.confirmDialog(t='Selection Error', m='Please select the top group of the asset to be exported')
            return
        obj = sel[0]
    name = obj.split('_grp')[0]
    exp = 'export_model_set'
    if not cmds.objExists(exp):
        cmds.sets(em=True, n=exp)
        cmds.addAttr(exp, ln='assetName', dt='string')
        cmds.addAttr(exp, ln='assetType', dt='string')
    cmds.setAttr(exp + '.assetName', name, type='string')
    cmds.setAttr(exp + '.assetType', 'model', type='string')
    cmds.sets(obj, add=exp)
    cmds.select(cl=True)


def setCameraRes(full=False):
    mode = 'Half Res'
    resolution = '2224 x 1548'
    if cmds.objExists('defaultResolution'):
        if full:
            mode = 'Full Res'
            resolution = '4448 x 3096'
            cmds.setAttr("defaultResolution.width", 4448)
            cmds.setAttr("defaultResolution.height", 3096)
        else:
            cmds.setAttr("defaultResolution.width", 2224)
            cmds.setAttr("defaultResolution.height", 1548)
        cmds.confirmDialog(t='Camera resolutioin set            ', m='"' + mode + '"\t'  + resolution)


def setSceneGroups(shotName=""):
    result = cmds.promptDialog(
                    title='SHOT NAME',
                    message='Enter Name:',
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel',
                    text = shotName)

    if result == 'OK':
        shotName = cmds.promptDialog(query=True, text=True)
        
        #create scene structure
        rootNode = cmds.createNode("transform",n=shotName)
        layerNode = cmds.createNode("transform",n="fg01",p=rootNode)
        conesNode = cmds.createNode("transform",n="Cones",p=layerNode)
        objTrackNode = cmds.createNode("transform",n="ObjTrack",p=layerNode)
        geoNode = cmds.createNode("transform",n="Geo",p=layerNode)
        refNode = cmds.createNode("transform",n="Ref",p=layerNode)



def makeSceneVersion(mode, add=None):
    user = os.getlogin()
    scene_dir = cmds.workspace(q=True, sn=True)
    cur_scene = cmds.file(q=True, sn=True, shn=True)
    ext = cur_scene.split('.')[-1]
    disc = scene_dir.split('/')[-3]
    name = scene_dir.split('/')[-4]
    prio = scene_dir.split('/')[-5]
    # CREATE SCENE PATH BASED ON THE MODE
    scene_render_path = unixifyPath(os.path.join(scene_dir, 'scenes'))
    if mode == 'user':
        scene_user_path = unixifyPath(os.path.join(scene_dir, 'scenes', user))
        if not os.path.isdir(scene_user_path):
            info  = '.... ' + scene_user_path.split(prio)[-1]
            result = cmds.confirmDialog(
                t='Make Dir', b=['Yes','No'], db='No', cb='No', ds='No',
                m='Do you want to make your user directory?\n\n' + info)
            if result == 'Yes':
                os.makedirs(scene_user_path)
                print('Made this directory:\n\t' + scene_user_path)
    if os.path.isdir(scene_render_path):           
        # GET THE VERSION BASED ON THE PROPER NAMING THE SCENE SHOULD HAVE
        idx, vers, match = 0, [], []
        scene_name = name + '_' + disc + '_v'
        files = os.listdir(scene_render_path)
        for f in files:
            cur = unixifyPath(os.path.join(scene_render_path, f))
            if os.path.isfile(cur):
                if scene_name in f and f.endswith(ext):
                    match.append(f)
                    ver = int(f.split('v')[-1].split('.')[0])
                    vers.append(ver)
                    print(f, ver)
        idx = len(match) + 1
        if vers:
            idx = max(vers) + 1
        if add:
            idx = idx + add
        scene_name = name + '_' + disc + '_v' + str(idx).zfill(3) + '.' + ext
    # WRITE SCENE
    full_scene = unixifyPath(os.path.join(scene_render_path, scene_name))
    if mode == 'user':
        full_scene = unixifyPath(os.path.join(scene_user_path, scene_name))
    if os.path.isfile(full_scene):
        makeSceneVersion('user', 1)
        print('Versioning up: ' + str(idx))
    info =  '.... ' + full_scene.split(prio)[-1]
    tipo = 'mayaAscii'
    if ext == 'mb':
        tipo = 'mayaBinary'
    cmds.file(rename=full_scene)
    cmds.file(save=True, type='mayaAscii', f=True)
    cmds.confirmDialog(t='Atelier Save Mode: ' + mode, m=info, b=['Fuck Yeah'])
    print ('result: ' + full_scene)


def atelierMayaFileMenu():
    main_window = mel.eval('$tempVar = $gMainWindow')
    file_menu = cmds.window(main_window, q=True, ma=True)
    items = cmds.menu(file_menu[0], q=True, ia=True)
    for i in items:
        if 'save' in i:
            cmds.menuItem(i, e=True, vis=False)
    extra = []
    for i in items:
        if 'menuItem' in i:
            extra.append(i)
    sepa = extra[0]
    for x in range(1, 4):
        cmds.menuItem(extra[x], e=True, vis=False)
    # cmds.iconTextButton('saveSceneButton', e=True, en=False)
    menus = ['atelierUser', 'atelierRender', 'atelierSepa']
    for m in menus:
        if cmds.menuItem(m, q=True, ex=True):
            print('Clean menu: ' + m)
            cmds.deleteUI(m)
    cmds.menuItem(
        menus[0], l='Atelier User Save',
        p='mainFileMenu', ia=sepa, bld=True,
        c='atelier_utils.makeSceneVersion("user")')
    cmds.menuItem(
        menus[1], l='Atelier Render Save',
        p='mainFileMenu', ia=menus[0], bld=True,
        c='atelier_utils.makeSceneVersion("render")')
    cmds.menuItem(menus[2], d=True, ia=menus[1], bld=True)


def restoreMayaFileMenu():
    extra = []
    main_window = mel.eval('$tempVar = $gMainWindow')
    file_menu = cmds.window(main_window, q=True, ma=True)
    items = cmds.menu(file_menu[0], q=True, ia=True)
    for i in items:
        if 'save' in i:
            cmds.menuItem(i, e=True, vis=True)
    for i in items:
        if 'menuItem' in i:
            extra.append(i)

    menus = ['atelierUser', 'atelierRender', 'atelierSepa']
    for m in menus:
        if cmds.menuItem(m, q=True, ex=True):
            cmds.deleteUI(m)
    for x in range(1, 4):
        cmds.menuItem(extra[x], e=True, vis=True)
    # cmds.iconTextButton('saveSceneButton', e=True, en=True)