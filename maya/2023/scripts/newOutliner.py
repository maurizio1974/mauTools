# --MAYA-----------------------------------------------------------------------
#   Maurizio Giglioli September 09, 2016
# -----------------------------------------------------------------------------
#  Description:
#  Modifications:
# -----------------------------------------------------------------------------
#  GLOBAL PROC TO CREATE A NEW OUTLINER
# -----------------------------------------------------------------------------
import maya.cmds as cmds
import maya.mel as mel
import random
import os


def newOutliner():
    cmds.window(
        'outliner' + str(random.randint(0, 10000)),
        t='New Outliner',
        wh=(300, 750)
    )
    fr = cmds.formLayout()
    panel = cmds.outlinerPanel(mbv=False, p=fr)
    outliner = cmds.outlinerPanel(panel, q=True, oe=True)
    cmds.outlinerEditor(
        outliner, e=True,
        mlc="worldList", slc="modelList",
        shp=False, atr=False, con=False,
        aco=False, xpd=False, dag=True,
        hir=False, xc=False, cmp=True,
        num=False, ha=True,
        autoSelectNewObjects=False,
        dns=False, tf=False, ssm=True,
        sn=1, sf='defaultSetFilter', p=fr
    )
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (panel, 'left', 0),
            (panel, 'right', 0),
            (panel, 'bottom', 0)
        ]
    )
    # ADD UI COMMANDS
    newBuildUI([outliner])
    cmds.showWindow()

    for s in os.getenv('MAYA_MODULE_PATH').split(':'):
        if '/nfs/dev/software/' in s:
            if 'MayaBonusTools' not in s and 'minimo' not in s:
                print(s)


def newBuildUI(ui):
    out, outliner = [], ''
    fr = cmds.menuBarLayout(ui[0], q=True, p=True)
    # Get current outliner
    outliner = ui[0]
    # Standards Maya
    buttons = []
    default = [
        ['Geometry', 'Shaded.png'],
        ['nDynamics', 'nClothCreate.png'],
        ['Sets', 'menuIconEdit.png'],
        ['animCurves', 'setKeyframe.png'],
        ['Cameras', 'view.png'],
        ['Textures', 'Textured.png'],
        ['Shaders', 'render_layeredTexture.png'],
        ['Shapes', 'pickGeometryObj.png'],
        ['Hirearchy', 'menuIconGraph.png'],
        ['Plugins', 'unmuted.png']
    ]
    for d in default:
        out.append(d[0])
        bttn = cmds.iconTextCheckBox(
            p=fr, image1=d[1], style='iconOnly', w=20, h=20, ann=d[0]
        )
        cmdON = 'newOutliner.newOutIsolate("' + outliner + '")'
        cmdOFF = 'newOutliner.newOutIsolate("' + outliner + '")'
        if d[0] == 'Plugins':
            plugins = [
                'SOuP', 'mtoa', 'Mayatomr', 'Substance', 'redshift4maya'
            ]
            pm = cmds.popupMenu(p=bttn)
            cmd = 'newOutliner.newOutIsolate("' + outliner + '")'
            cmdON = 'print "Right click please"'
            cmdOFF = 'print "Right click please"'
            for p in plugins:
                plugs = newCheckPlugs(p)
                if plugs[0]:
                    cmds.menuItem(p, p=pm, cb=False, c=cmd)
        if d[0] == 'Shapes':
             cmdON = 'cmds.outlinerEditor("' + outliner + '", e=True, shp=True)'
             cmdOFF = 'cmds.outlinerEditor("' + outliner + '", e=True, shp=False)'
        elif d[0] == 'Hirearchy':
            cmds.iconTextCheckBox(bttn, e=True, v=1)

        cmds.iconTextCheckBox(bttn, e=True, onc=cmdON, ofc=cmdOFF)
        buttons.append(bttn)
    # Rearrange formLayout
    for x in range(0, len(buttons)):
        if x == 0:
            cmds.formLayout(
                fr,
                e=True,
                af=[
                    (buttons[x], 'left', 10),
                    (buttons[x], 'top', 10)
                ]
            )
        elif x == len(buttons) - 1:
            cmds.formLayout(
                fr,
                e=True,
                af=[
                    (buttons[x], 'right', 10),
                    (buttons[x], 'top', 10)
                ]
            )
        elif x == len(buttons) - 2:
            cmds.formLayout(
                fr,
                e=True,
                af=[(buttons[x], 'top', 10)],
                ac=[
                    (buttons[x], 'right', 2, buttons[x + 1])
                ]
            )
        elif x == len(buttons) - 3:
            cmds.formLayout(
                fr,
                e=True,
                af=[(buttons[x], 'top', 10)],
                ac=[
                    (buttons[x], 'right', 2, buttons[x + 1])
                ]
            )
        else:
            cmds.formLayout(
                fr,
                e=True,
                af=[(buttons[x], 'top', 10)],
                ac=[
                    (buttons[x], 'left', 2, buttons[x - 1])
                ]
            )
    cmds.formLayout(fr, e=True, ac=[(outliner, 'top', 10, buttons[0])])


def newCheckPlugs(plug):
    current, out = [], []
    for ps in cmds.pluginInfo(q=True, listPlugins=True):
        if ps in plug:
            # Check if plugin is loaded
            if not cmds.pluginInfo(ps, q=True, loaded=True):
                cmds.loadPlugin(ps)
                out.append(ps)
            else:
                out.append(ps)
            # Get nodes of current plugin
            inP = cmds.pluginInfo(ps, q=True, dn=True)
            if inP:
                current = {plug: cmds.pluginInfo(plug, q=True, dn=True)}
    return out, current


def newOutIsolate(outliner):
    current, filtro, allVar = [], [], []
    # Clean existing Filters
    if cmds.itemFilter(outliner + '_tempObjectFilter', q=True, ex=True):
        cmds.delete(outliner + '_tempObjectFilter')
        print('deleted ' + outliner + '_tempObjectFilter')
    # Get All the UI values
    buttons = newGetUI(outliner)[0]
    shState = newGetUI(outliner)[1]
    hrState = newGetUI(outliner)[2]
    mnItems = newGetUI(outliner)[3]
    mnState = newGetUI(outliner)[4]
    dgState = 0
    if not buttons and not mnState:
        dgState = 1
    # Plugins Section
    for p in mnItems:
        if cmds.menuItem(p, q=True, cb=True):
            plug = newCheckPlugs(p)
            allVar.append(plug[1])
    # Maya standard Section
    Geometry = {
        'Geometry': ['mesh', 'subdiv', 'nurbsSurface', 'nurbsCurve']
    }
    nDynamics = {'nDynamics': getStrandards('n', 1) + ['nucleus']}
    Sets = {'Sets': getStrandards('Set', 0)}
    animCurves = {'animCurves': getStrandards('animCurve', 0)}
    Cameras = {'Cameras': getStrandards('camera', 0) + ['imagePlane']}
    Textures = {'Textures': cmds.listNodeTypes('texture')}
    Shaders = {'Shaders': cmds.listNodeTypes('shader')}
    # Standards Maya
    standard = [
        Geometry, nDynamics, Sets, animCurves, Cameras, Textures, Shaders
    ]
    for s in standard:
        allVar.append(s)
    # Create Filters
    for a in allVar:
        for b in buttons:
            if b in a:
                for key in a:
                    for al in a[key]:
                        current.append(al)
        for m in mnItems:
            if m in a:
                for key in a:
                    for al in a[key]:
                        current.append(al)
    # Apply Filter
    if current:
        filtro = cmds.itemFilter(
            outliner + '_tempObjectFilter', byType=current
        )
    else:
        filtro = cmds.itemFilter(outliner + '_tempObjectFilter', byName='*')

    cmds.outlinerEditor(
        outliner, e=True, dag=dgState, shp=shState, hir=hrState, f=filtro
    )


def getStrandards(nodo, switch):
    allN = cmds.allNodeTypes()
    tm = []
    if switch == 0:
        for c in allN:
            if nodo in c:
                tm.append(c)
    elif switch == 1:
        for c in allN:
            if nodo in c[0] and c[1].istitle():
                tm.append(c)
    return tm


def newGetUI(outliner):
    buttons, shState, hrState, mi, mis = [], 0, 0, [], []
    fr = cmds.outlinerEditor(outliner, q=True, p=True).split('|')[1]
    for b in cmds.formLayout(fr, q=True, ca=True):
        if 'iconTextCheckBox' in b:
            ann = cmds.iconTextCheckBox(b, q=True, ann=True)
            if ann == 'Shapes':
                if cmds.iconTextCheckBox(b, q=True, v=True):
                    shState = 1
                else:
                    shState = 0
            elif ann == 'Hirearchy':
                if cmds.iconTextCheckBox(b, q=True, v=True):
                    hrState = 0
                else:
                    hrState = 1
            elif ann == 'Plugins':
                pm = cmds.iconTextCheckBox(b, q=True, pma=True)
                pma = cmds.popupMenu(pm, q=True, ia=True)
                if pma:
                    for i in pma:
                        mi.append(i)
                        if cmds.menuItem(i, q=True, cb=True):
                            mis.append(1)
            else:
                if cmds.iconTextCheckBox(b, q=True, v=True):
                    buttons.append(ann)

    return buttons, shState, hrState, mi, mis


def mfilterUIGetField(outliner):
    gFilterUIViewListMau = mel.eval("$tempVar = $gFilterUIViewList")
    gFilterUIFieldListMau = mel.eval("$tempVar = $gFilterUIFieldList")
    field, index = "", 0
    for index in range(0, len(gFilterUIViewListMau)):
        if outliner == gFilterUIViewListMau[index]:
            field = gFilterUIFieldListMau[index]
            if not cmds.textField(field, ex=True) == "":
                break
    return field


# -----------------------------------------------------------------------------
#  GLOBAL DO
# -----------------------------------------------------------------------------
def do_newOutliner():
    newOutliner()
