# MAKE SET PROJECT MAYA SHIT
import atelier_utils
from maya import mel, cmds
import os, json, tempfile, time
from datetime import timedelta
from pprint import pprint



def get_Prjs(force=False):
    start = time.time()
    # tmp = tempfile.gettempdir().replace('\\', '/')
    # jFile = os.path.join(tmp, 'structure.json')
    jFile = 'Z:/jobs/GEX/rnd/configs/structure.json'
    out = {}
    base = 'Z:/jobs/GEX/'
    if force:
        modes = ['assets', 'shots']
        for m in modes:
            info = {}
            cur = os.path.join(base, m)
            for root, dirs, files in os.walk(cur, topdown=False):
                for d in dirs:
                    if d == 'maya':
                        maya_cur = atelier_utils.unixifyPath(os.path.join(root, d))
                        shot = maya_cur.split('/')[-4]
                        disc = maya_cur.split('/')[-3]
                        print(shot, disc, maya_cur)
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


def prjs_UI(force=False):
    gToolBox = mel.eval('$tempVar = $gToolBox')
    if cmds.iconTextButton('mnmMauPrjs', ex=True):
        cmds.deleteUI('mnmMauPrjs')
    btt = cmds.iconTextButton(
        'mnmMauPrjs',
        label='Prjs', w=33, h=30,
        i='Atelier_Logo.png',
        p=gToolBox)
    data = get_Prjs(force)
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
                    disc = d.split('/')[-3]
                    cmds.menuItem(label=disc, p=ms, c=cmd)
        # Add rebuilding Database menu
        # mr = cmds.menuItem(label='Rebuild Tatabase ( Pretty Slow 2-5 min )', p=ppc, c='mayaProjects.get_Prjs(True)')
    else:
        cmds.warning('There is not project structure config file ask your sup to make one')

