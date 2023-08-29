from maya import mel, cmds
import os, json, tempfile, time
from datetime import timedelta
from pprint import pprint


# MAKE SET PROJECT MAYA SHIT

def unixifyPath(path):
    path = path.replace('\\', '/')
    return path


def get_Prjs(force=False):
    start = time.time()
    out = {}
    base = unixifyPath(os.getenv('MIMMO_PROJECT'))
    jFile = unixifyPath(os.path.join(base, 'config/structure.json'))
    if force:
        modes = ['build', 'shots']
        for m in modes:
            info = {}
            cur = unixifyPath(os.path.join(base, m))
            for root, dirs, files in os.walk(cur, topdown=False):
                for d in dirs:
                    if d == 'maya':
                        maya_cur = unixifyPath(os.path.join(root, d))
                        shot = maya_cur.split('/')[-3]
                        disc = maya_cur.split('/')[-2]
                        # print(shot, disc, maya_cur)
                        if disc in maya_cur:
                            if shot not in info:
                                info[shot] = []
                                info[shot].append(maya_cur)
                            else:
                                info[shot].append(maya_cur)
            out[m] = info
        pprint(out)
        if os.path.isfile(jFile):
            os.remove(jFile)
        with open(jFile, "w") as outfile:
            json.dump(out, outfile, indent=4)
    if os.path.isfile(jFile):
        with open(jFile, 'r') as f:
            out = json.load(f)
    end = time.time()
    result = str(end - start)
    print(result.format(str(timedelta(seconds=66))))
    return(out)


def prjs_UI():
    gToolBox = mel.eval('$tempVar = $gToolBox')
    if cmds.iconTextButton('mnmMauPrjs', ex=True):
        cmds.deleteUI('mnmMauPrjs')
    btt = cmds.iconTextButton(
        'mnmMauPrjs',
        label='Prjs', w=33, h=30,
        i='jobs.png',
        p=gToolBox)
    data = get_Prjs(True)
    if data:
        ppc = cmds.popupMenu('mnmCamBttm', p=btt)
        for t in data.keys():
            mt = cmds.menuItem(label=t, p=ppc, subMenu=True)
            for s in data[t]:
                ms = cmds.menuItem(label=s, p=mt, subMenu=True)
                for d in data[t][s]:
                    # print(t, s, d.split('/')[-3])
                    cmd = 'cmds.workspace("' + d + '", openWorkspace=True);'
                    cmd += 'cmds.workspace(dir="' + d + '");'
                    cmd += 'print(\'Workspace set to:    ' + d + '\')'
                    disc = d.split('/')[-2]
                    cmds.menuItem(label=disc, p=ms, c=cmd)
        # Add rebuilding Database menu
        # mr = cmds.menuItem(label='Rebuild Tatabase ( Pretty Slow 2-5 min )', p=ppc, c='mayaProjects.get_Prjs(True)')
    else:
        cmds.warning('There is not project structure config file ask your sup to make one')

