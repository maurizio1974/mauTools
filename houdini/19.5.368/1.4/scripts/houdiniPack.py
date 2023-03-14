import os, hou, json, shutil, time
from pprint import pprint

'''PACKAGE A SCENE IN A NEW DIRECTORY

-   INFO

    Get everything in a scene and move it to a new directory
    with all dependecies

-   EXAMPLE

import assetPackagerH
loc = '/mnt/jobs/fallout_81222/concept/mau'
assetPackagerH.sceneMover(loc)

'''

def path_checker(loc_file):
    out = loc_file.replace('\\', '/')
    return out


def sceneSaver(loc_path, debug):
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


def lister():
    out, hdas = {}, []
    # get all contexts
    contexts = hou.node('/').children()
    for c in contexts:
        # get all top level nodes in a context
        nodes = hou.node('/' + c.name()).children()
        for x, node in enumerate(nodes):
            # get all children of a node
            all_children = node.allSubChildren()
            if not all_children:
                continue
            hdas.append(node)
            info = {}
            for child in all_children:
                hdas.append(child)
                # Continue making the list of assets to copy
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
                        # Check if the result is a valid file
                        checkV = val.split('/')[-1].split('.')
                        if len(checkV) > 1 :
                            # print child.name(), child.type().name(), attr.name(), len(checkV), val
                            vals[attr.name()] = val
                if vals:
                    info[child] = vals
            out[node.name()] = info
    return(out, hdas)


def copyShotHda(data, loc_path):
    show = os.getenv('HIP')
    hda_loc = os.path.join(
        show.split('jobs')[0],
        'jobs',
        show.split('jobs/')[-1].split('/')[0],
        'tools/houdini/otls')
    for dt in data:
        # Check if it is a show hda and in case copyi it
        hda_definition = dt.type().definition()
        if hda_definition:
            hda = hda_definition.libraryFilePath()
            if hda != 'Embedded':
                if hda_loc in hda:
                    # print hda, hda_loc, loc_path
                    new_path = os.path.join(loc_path, 'otls')
                    hda_name = hda.split('/')[-1]
                    if not os.path.isdir(new_path):
                        os.makedirs(new_path)
                        print('Made missing directory:\n' + new_path)
                    end_file = os.path.join(new_path, hda_name)
                    if not os.path.isfile(end_file):
                        shutil.copy2(hda, end_file)
                        print('Copied Hda: ' + end_file)


def getExtLocation(val):
    ext = val.split('.')[-1]
    token = 'images'
    exts = {
        'abc': ['abc'],
        'geo': ['obj', 'sc', 'bgeo', 'stl'],
        'vdb': ['vdb'],
        'ass': ['ass', 'gzip']}
    for e in exts.keys():
        if ext in exts[e]:
            token = e
    return(token)


def getSeq(val, nameC, name):
    out = []
    path = val.replace('/' + name, '')
    files = os.listdir(path)
    for f in files:
        if nameC in f:
            out.append(os.path.join(path, f).replace('\\', '/'))
    return(sorted(out))


def moveAllData(loc_path, data):
    ms = len(data.keys())
    for x, d in enumerate(data.keys()):
        sc = len(data[d])
        for y, child in enumerate(data[d]):
            for attr in data[d][child].keys():
                val = data[d][child][attr]
                name = val.split('/')[-1]
                node_name = val.split('/')[-1]
                token = getExtLocation(node_name)
                new_path = os.path.join(loc_path, token, d)
                if not os.path.isdir(new_path):
                    os.makedirs(new_path)
                    print('Made missing directory:\n' + new_path)
                # CHECK IF SEQUENCE
                index = None
                for n in name.split('.'):
                    if len(n) == len(''.join(filter(str.isdigit, n))):
                        index = n
                if index:
                    nameC = name.split(index)[0]
                    vals = getSeq(val, nameC, name)
                    for v in vals:
                        node_seq_name = v.split('/')[-1]
                        end_file = os.path.join(new_path, node_seq_name).replace('\\', '/')
                        if not os.path.isfile(end_file):
                            shutil.copy2(v, end_file)
                            print('Copied ' + end_file)
                else:
                    end_file = os.path.join(new_path, node_name).replace('\\', '/')
                    if not os.path.isfile(end_file):
                        shutil.copy2(val, end_file)
                        print('Copied ' + end_file)
            print('Left to do: ' + str(ms - x) + ' (' + d + '): ' + str(sc - y))


def sceneMover(loc_path=None):
    startTime = time.time()
    show = os.getenv('HIP')
    shot = os.getenv('HIPNAME')
    if not loc_path:
        loc_path = os.path.join(show, shot)
    else:
        loc_path = os.path.join(loc_path, shot)
    if not os.path.isdir(loc_path):
        os.makedirs(loc_path)
        print('Made missing directory:\n' + loc_path)
    # for contest in ['obj', 'out', 'img', 'mat', 'shop']:
    # GET FILES INFO AND LOCATIONS
    data = lister()
    # COPY ALL THE SHOW HDAS IN THE SHOT
    copyShotHda(data[1], loc_path)
    # COPY ALL THE PATH AND FILES FOUND
    moveAllData(loc_path, data[0])
    # COPY SCENE
    sceneSaver(loc_path, False)
    executionTime = (time.time() - startTime)
    print '*' * 30, '\n' * 3, "\tPackaging Time:\t", '\n\n\tminutes: ' + str(round(executionTime / 60, 1)) + '\n\tseconds: ' + str(round(executionTime, 1)), '\n' * 3, '*' * 30