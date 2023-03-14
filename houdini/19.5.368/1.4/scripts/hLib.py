import os
import hou
import glob
import shutil
from pprint import pprint
from random import randint
# from PySide2 import QtCore, QtUiTools, QtWidgets
# from Qt import QtCore, QtWidgets, QtCompat , QtGui



def path_checker(loc_file):
    out = loc_file.replace('\\', '/')
    return out


def alembicMover(loc_path, debug):
    node_type = hou.nodeType(hou.sopNodeTypeCategory(), 'alembic')
    abcs = node_type.instances()
    for node in list(abcs):
        abc_path = node.parm('fileName').eval()
        abc_name = abc_path.split('/')[-1].split('\\')[-1]
        ast = node.parent().name()
        out = os.path.join(loc_path, ast)
        if not os.path.isdir(out):
            os.makedirs(out)
        new_path = path_checker(os.path.join(out, abc_name))
        if abc_path != new_path:
            if not os.path.isfile(new_path):
                if not debug:
                    shutil.copy2(abc_path, new_path)
                print('Copying this alembic:\n\t' + node.name() + '\nHere:\n\t' + new_path)
            else:
                print('Alembic is there already:\n' + new_path)
            if not debug:
                node.setParms({'fileName': new_path})
        else:
            print('Skipping this alembic:\n\t' + abc_path + '\n\tbecause there already')


def materialMover(loc_path, debug):
    node_type = hou.nodeType(hou.vopNodeTypeCategory(), 'arnold::image')
    mats = node_type.instances()
    for node in list(mats):
        tex_path = node.parm('filename').eval()
        tex_name = tex_path.split('/')[-1].split('\\')[-1]
        mat = node.parent().name()
        out = os.path.join(loc_path, mat)
        if not os.path.isdir(out):
            os.makedirs(out)
        new_path = path_checker(os.path.join(out, tex_name))
        if tex_path != new_path:
            if not os.path.isfile(new_path):
                if not debug:
                    shutil.copy2(tex_path, new_path)
                print('Copying this texture:\n\t' + node.name() + '\nHere:\n\t' + new_path)
            else:
                print('Texture is there already:\n' + new_path)
            node.setParms({'filename': new_path})
        else:
            print('Skipping this texture:\n\t' + tex_path + '\n\tbecause there already')


def sceneMover(loc_path, debug):
    cur_scene = hou.hipFile.name()
    scene_path = os.getenv('HIP')
    scene_name = hou.hipFile.basename()
    new_scene = path_checker(os.path.join(loc_path, scene_name))
    if cur_scene != new_scene:
        if not os.path.isfile(new_scene):
            if not debug:
                # shutil.copy2(scene, new_scene)
                hou.hipFile.save(file_name=str(new_scene), save_to_recent_files=False)
            print('Copying scene :\n\t' + scene_name + '\nHere:\n\t' + new_scene)
        else:
            print('Skipping this scene:\n\t' + scene_name + '\n\tbecause there already')
    else:
        print('Skipping this scene:\n\t' + scene_name + '\n\tbecause there already')


def assetMover(loc_path=None):
    show = os.getenv('HIP')
    shot = os.getenv('HIPNAME')
    if not loc_path:
        loc_path = os.path.join(show, shot)
    else:
        loc_path = os.path.join(loc_path, shot)
    if not os.path.isdir(loc_path):
        os.makedirs(loc_path)
        print('Made missing directory:\n' + loc_path)
    # COPY ALEMBIC NODES
    cur_path = os.path.join(loc_path, 'abc')
    alembicMover(cur_path, False)
    # COPY IMAGES
    cur_path = os.path.join(loc_path, 'images')
    materialMover(cur_path, False)
    # COPY SCENE
    sceneMover(loc_path, False)
    print('*' * 30, '\n' * 3, "\tALL DONE\t", '\n' * 3, '*' * 30)


def saveToDesk(mode=None):
    # nodes = hou.selectedNodes()
    # if not nodes:
    #     if mode:
    #         hou.ui.displayMessage('Select one or more nodes in the ' + mode + ' context')
    #     else:
    #         hou.ui.displayMessage('Select one or more nodes in the context')
    #     return
    command = 'opscript -r /* > C:/Users/mauri/Desktop/mover.cmd'
    if mode:
        command = 'opscript -r /' + mode + '/* > C:/Users/mauri/Desktop/mover.cmd'
    print(command)
    hou.hscript(command)


def loadFromDesk():
    desk = 'C:/Users/mauri/Desktop/mover.cmd'
    if not os.path.isfile(desk):
        hou.ui.displayMessage('nothing found to be imported here:\n' + desk)
        return
    command = 'cmdread ' + desk
    hou.hscript(command)
    os.remove(desk)

# ---------------------------------------------------------------------------------------------
# REPATH IMAGES

def repath(contest):
    nodes = hou.node('/' + contest).children()
    for x, node in enumerate(nodes):
        if node.type().name() == 'matnet':
            # print(node)
            mats = node.children()
            for mat in mats:
                img = mat.children()
                for i in img:
                    check = ['arnold::image', 'filename']
                    # check = ['alembic', 'fileName']
                    if i.type().name() == check[0]:
                        i_path = i.parm(check[1]).eval()
                        i_name = i_path.split('/')[-1]
                        out = '$HIP/images/' + node.name() + '/' + i_name
                        try:
                            i.setParms({check[1]: out}).setexpressions()
                            print(out)
                        except:
                            print(i.path())

def repathAbc2():
    nodes = hou.node('/obj').children()
    for x, node in enumerate(nodes):
        if node.type().name() == 'geo':
            img = node.children()
            for i in img:
                check = ['alembic', 'fileName']
                if i.type().name() == check[0]:
                    i_path = i.parm(check[1]).eval()
                    i_name = i_path.split('/')[-1]
                    out = '$HIP/abc/' + node.name() + '/' + i_name
                    try:
                        i.setParms({check[1]: out}).setexpressions()
                        print(out)
                    except:
                        print(i.path())



def repathAbc():
    node_type = hou.nodeType(hou.sopNodeTypeCategory(), 'alembic')
    abcs = node_type.instances()
    for node in list(abcs):
        abc_path = node.parm('fileName').eval()
        abc_node = abc_path.split('/')[-2]
        abc_name = abc_path.split('/')[-1]
        out = '$HIP/abc/generatorroomenv/' + abc_name
        check = os.path.isfile(out.replace('$HIP', 'G:/jobs/Houdini/mech_103_043_1000_fx_steam_v008'))
        if '$HIP' not in abc_path:
            if check:
                print(out)
                print(abc_path)
                node.setParms({'fileName': out})
        # try:
        #     node.setParms({'fileName': out}).setexpressions()
        # except:
        #     print(node.path())
        


def lister(contest):
    out = {}
    # get all top level nodes in a context
    nodes = hou.node('/' + contest).children()
    for x, node in enumerate(nodes):
        # get all children of a node
        all_children = node.allSubChildren()
        if not all_children:
            continue
        info = {}
        for child in all_children:
            attrs = child.parms()
            if not attrs:
                continue
            vals = {}
            for attr in attrs:
                val = child.parm(attr.name()).eval()
                if not 'str' in str(type(val)):
                    continue
                # Check if the path exists
                if os.path.isfile(val):
                    # print(node.name(), child.path(), attr.name(), val)
                    vals[attr.name()] = val
            if vals:
                info[child] = vals
        out[node.name()] = info
    return(out)




# target = hou.node('../Target')

# world = target.worldTransform()
# pos = world.extractTranslates('srt')


# return pos[0]