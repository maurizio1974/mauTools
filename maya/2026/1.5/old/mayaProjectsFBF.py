from maya import mel, cmds
import os, json, tempfile, time, getpass
from datetime import timedelta
from pprint import pprint


# MAKE SET PROJECT MAYA SHIT

def unixifyPath(path):
    path = path.replace('\\', '/')
    return path


def get_Prjs(force=False):
    start = time.time()
    user = getpass.getuser()
    # user = 'm.panci'
    out = {}
    base = '/mnt/projects/tmsviz/01_assets'
    if force:
        info = {}
        for root, dirs, files in os.walk(base, topdown=False):
            for d in dirs:
                if d == user:
                    maya_cur = os.path.join(root, d)
                    shot = maya_cur.split('/')[-6]
                    disc = maya_cur.split('/')[-2]
                    # print(shot, disc, maya_cur)
                    if disc in maya_cur:
                        if shot not in info:
                            info[shot] = []
                            info[shot].append(maya_cur)
                        else:
                            info[shot].append(maya_cur)
        pprint(info)
    end = time.time()
    result = str(end - start)
    print(result.format(str(timedelta(seconds=66))))
    return(info)


def prjs_UI():
    gToolBox = mel.eval('$tempVar = $gToolBox')
    if cmds.iconTextButton('mnmFBFprjs', ex=True):
        cmds.deleteUI('mnmFBFprjs')
    btt = cmds.iconTextButton(
        'mnmFBFprjs',
        label='Prjs', w=33, h=30,
        i='jobs.png',
        p=gToolBox)
    data = get_Prjs(True)
    if data:
        ppc = cmds.popupMenu('mnmCamBttm', p=btt)
        for t in data.keys():
            mt = cmds.menuItem(label=t, p=ppc, subMenu=True)
            for s in data[t]:
                cmd = 'cmds.workspace("' + s + '", openWorkspace=True);'
                cmd += 'cmds.workspace(dir="' + s + '");'
                cmd += 'print(\'Workspace set to:    ' + s + '\')'
                disc = s.split('/')[-2]
                cmds.menuItem(label=disc, p=mt, c=cmd)
    else:
        cmds.warning('There is not project structure config file ask your sup to make one')

