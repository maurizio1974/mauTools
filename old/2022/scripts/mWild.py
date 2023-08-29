# ---------------------------------------------------------------------------
# PERSONAL WILD CARD POPUP ITEM MAKER FOR MAU
# ADDE FUNCTION TO REFERENCE EDITOR
# ---------------------------------------------------------------------------
import maya.mel as mel
import maya.cmds as cmds


def fixOutliner2017():
    outs = cmds.getPanel(type='outlinerPanel')
    for out in outs:
        cmds.outlinerEditor(
            out, e=True, setFilter='defaultSetFilter')


def mReferenceEditor():
    cmds.ReferenceEditor()
    # REFERENCE EDITOR PART
    formRef = cmds.iconTextButton('createRefButton', q=True, p=True)
    btt = cmds.button('NE', w=26, h=26, p=formRef, c='cmds.NamespaceEditor()')
    bttF = cmds.button('FIX', w=26, h=26, p=formRef, c='mW.fixNameSpaces()')
    cmds.formLayout(
        formRef,
        e=True,
        ac=[
            (btt, 'left', 10, 'refEdViewportButton'),
            (bttF, 'left', 5, btt)
        ]
    )


def fixNameSpaces():
    topRef = cmds.file(q=True, r=True)
    for t in topRef:
        ns = cmds.file(t, q=True, ns=True)
        if not cmds.namespace(ex=ns):
            cmds.namespace(add=ns)
            cmds.warning('Added missing namespace: ' + ns)
    cmds.confirmDialog(t='Ole\'', m='Recreated missing Namespaces')


def getNameSpaces(ui, dir):
    topRef = cmds.namespaceInfo(lon=True)
    for t in topRef:
        if t != 'UI' and t != 'shared':
            if dir == 1:
                cmds.menuItem(t, p=ui)
            elif dir == 0:
                all = cmds.optionMenu(ui, q=True, ill=True)
                if all:
                    for a in all:
                        cmds.deleteUI(a)


def mSetWild():
    gStatusLine = mel.eval('$tempVar = $gStatusLine')
    gToolBox = mel.eval('$tempVar = $gToolBox')
    # ADD UI COMPONENTS IF NEEDED
    # 'mnmCH',
    uiP = [
        'mnmWildCB', 'mnmWildCB1', 'mnmWildNSCB', 'mnmWildOM',
        'mnmMauTools', 'mnmSetsManager', 'mnmPK', 'mnmPlugs',
        'mnmMauRef'
    ]
    for u in uiP:
        if cmds.checkBox(u, ex=True) == 1:
            cmds.deleteUI(u)
        elif cmds.optionMenu(u, ex=True) == 1:
            cmds.deleteUI(u)
        elif cmds.button(u, ex=True) == 1:
            cmds.deleteUI(u)
        elif cmds.iconTextButton(u, ex=True) == 1:
            cmds.deleteUI(u)

    cmds.checkBox(
        'mnmWildCB',
        v=0,
        label='off',
        p=gStatusLine,
        onc='mW.mChangeWild(1);'
        'cmds.checkBox(\'mnmWildCB\', e=True, l=\'on\');'
        'cmds.checkBox(\'mnmWildCB1\', e=True, en=True);'
        'cmds.checkBox(\'mnmWildNSCB\', e=True, en=True);',
        ofc='mW.mCleanWild();'
        'cmds.checkBox(\'mnmWildCB\', e=True, l=\'off\');'
        'cmds.checkBox(\'mnmWildCB1\', e=True, en=False, v=False);'
        'cmds.checkBox(\'mnmWildNSCB\', e=True, en=False);'
        'cmds.checkBox(\'mnmWildNSCB\', e=True, v=False);'
        'cmds.optionMenu(\'mnmWildOM\', e=True, en=False);'
        'mW.getNameSpaces(\'mnmWildOM\', 0);'
    )
    cmds.checkBox(
        'mnmWildCB1',
        en=False,
        label='presets',
        p=gStatusLine,
        onc='mW.mPresetWild(0)',
        ofc='mW.mPresetWild(1)'
    )
    cmds.checkBox(
        'mnmWildNSCB',
        en=False,
        label='NS',
        p=gStatusLine,
        onc='cmds.optionMenu(\'mnmWildOM\', e=True, en=True);'
        'mW.getNameSpaces(\'mnmWildOM\', 1);',
        ofc='cmds.optionMenu(\'mnmWildOM\', e=True, en=False);'
        'mW.getNameSpaces(\'mnmWildOM\', 0);'
    )
    cmds.optionMenu(
        'mnmWildOM',
        en=False,
        p=gStatusLine,
        cc='mW.mPresetWild(0)'
    )
    cmd = 'source "flipper.mel";mauTools();'
    cmds.button(
        'mnmMauTools',
        label='Mau', w=33, h=20,
        c='mel.eval(\'' + cmd + '\')',
        p=gToolBox
    )
    cmds.iconTextButton(
        'mnmSetsManager',
        label='Set', w=33, h=33,
        i='mSET.png',
        c='import mSetManager as ms;reload(ms);ms.mSetManager_UI()',
        p=gToolBox
    )
    cmds.iconTextButton(
        'mnmPK',
        label='PK', w=33, h=33,
        i='mAssetPack.png',
        c='import mAssetPack as mA;reload(mA);mA.mAssetPackUI()',
        p=gToolBox
    )
    # cmds.iconTextButton(
    #     'mnmCH',
    #     l='PK', w=33, h=33,
    #     i='LOGO_rebrand.ico',
    #     c='import charPipeline;reload(charPipeline);import cachePipeline;reload(cachePipeline);cachePipeline.aToolsUI()',
    #     p=gToolBox
    # )
    cmds.button(
        'mnmMauRef',
        label='mRef', w=33, h=20,
        c='import mWild as mW;reload(mW);mW.mReferenceEditor();',
        p=gToolBox
    )
    cmds.button(
        'mnmPlugs',
        label='PLUG', w=33, h=20,
        c='mel.eval("PluginManager")',
        p=gStatusLine
    )
    if cmds.checkBox('mnmWildNSCB', q=True, v=True) == 1:
        mChangeWild(1)
    else:
        mChangeWild(0)

    # EXTRA MENUBAR UI
    mMenuBarPlus()


def mChangeWild(dir):
    gTInField = mel.eval('$tempVar = $gTextualInputField')
    # CHANGE THE DEFAULT MAYA WILDCARD TEXTFIELD COMMAND
    if dir == 0:
        cmds.textField(
            gTInField,
            e=True,
            cc='mel.eval(\'quickWildcardSelect\')',
            ec='mel.eval(\'quickWildcardSelect\')'
        )
    elif dir == 1:
        cmds.textField(
            gTInField,
            e=True,
            cc='mW.mItemWild('
            'cmds.optionMenu(\'mnmWildOM\', q=True, v=True),'
            'cmds.textField(\'' + gTInField + '\',q=True, tx=True));',
            ec='mW.mItemWild('
            'cmds.optionMenu(\'mnmWildOM\', q=True, v=True),'
            'cmds.textField(\'' + gTInField + '\',q=True, tx=True));'
        )


def mItemWild(ns, name):
    gTInField = mel.eval('$tempVar = $gTextualInputField')
    pop, pM, mI, items, item, itemN, itemR = [], '', '', [], '', [], []
    if name:
        if ns:
            name = ns + ':' + name
        if cmds.objExists(name) == 1:
            # CHECK IF THE POPUPMENU EXISTS IF NOT CREATE IT
            pop = cmds.textField(gTInField, q=True, pma=True)
            if not pop:
                pM = cmds.popupMenu(p=gTInField)
                mI = cmds.menuItem(l=name, p=pM)
                cmds.menuItem(
                    mI,
                    e=True,
                    c='cmds.textField('
                    '\'' + gTInField + '\', e=True, tx=\'' + name + '\');'
                    'mel.eval(\'quickWildcardSelect\')'
                )
                mel.eval('quickWildcardSelect')
            else:
                # CREATE NEW MENUITEMS ARRAY FOR THE POPUPMENU
                items = cmds.popupMenu(pop[0], q=True, ia=True)
                if items:
                    for i in items:
                        item = cmds.menuItem(i, q=True, l=True)
                        if cmds.objExists(item):
                            itemN.append(item)
                    # CLEAN THE POPUP
                    cmds.popupMenu(pop[0], e=True, dai=True)
                # REPOPULATE POPUPMENU WITH NEW ARRAY
                itemN.append(name)
                itemR = set(itemN)
                itemR = list(set(itemN))
                for iR in itemR:
                    mI = cmds.menuItem(l=iR, p=pop[0])
                    cmds.menuItem(
                        mI,
                        e=True,
                        c='cmds.textField('
                        '\'' + gTInField + '\', e=True, tx=\'' + iR + '\');'
                        'mel.eval(\'quickWildcardSelect\')'
                    )
                cmds.textField(gTInField, e=True, tx=name)
                mel.eval('quickWildcardSelect')


def mPresetWild(dir):
    gTInField = mel.eval('$tempVar = $gTextualInputField')
    pop = cmds.textField(gTInField, q=True, pma=True)
    presets = [
        'L_*', 'R_*', 'C_*', '*_CLS', '*_CLH',
        '*_MESH', '*_GEO', '*_COL',
        '*_GRP', '*_NULL', '*_LOC', '*_RIV'
    ]

    ns = ''
    if dir == 0:
        if not pop:
            popm = cmds.popupMenu(p=gTInField)
            pop = [popm]
        if cmds.checkBox('mnmWildNSCB', q=True, v=True):
            ns = cmds.optionMenu('mnmWildOM', q=True, v=True)
        mis = cmds.popupMenu(pop[0], q=True, ia=True)
        for p in presets:
            if ns:
                p = ns + ':' + p
            if mis:
                for ms in mis:
                    label = cmds.menuItem(ms, q=True, label=True)
                    if label not in p:
                        mI = cmds.menuItem(label=p, p=pop[0])
                        cmds.menuItem(
                            mI,
                            e=True,
                            c='cmds.textField('
                            '\'' + gTInField + '\', e=True, tx=\'' + p + '\');'
                            'mel.eval(\'quickWildcardSelect\')'
                        )
            else:
                mI = cmds.menuItem(label=p, p=pop[0])
                cmds.menuItem(
                    mI,
                    e=True,
                    c='cmds.textField('
                    '\'' + gTInField + '\', e=True, tx=\'' + p + '\');'
                    'mel.eval(\'quickWildcardSelect\')'
                )
    if dir == 1:
        mis = cmds.popupMenu(pop[0], q=True, ia=True)
        if cmds.checkBox('mnmWildNSCB', q=True, v=True):
            ns = cmds.optionMenu('mnmWildOM', q=True, v=True)
        for ms in mis:
            label = cmds.menuItem(ms, q=True, label=True)
            for p in presets:
                if ns:
                    p = ns + ':' + p
                if label in p:
                    # print '2:  ', p, label, ms
                    cmds.deleteUI(ms)


def mCleanWild():
    gTInField = mel.eval('$tempVar = $gTextualInputField')
    pop = cmds.textField(gTInField, q=True, pma=True)
    if pop:
        cmds.deleteUI(pop)


def mMenuBarPlus():
    # CLEAN UI
    bttm = cmds.lsUI(type='iconTextButton')
    for b in bttm:
        if 'mBar' in b:
            cmds.deleteUI(b)
    # CREATE EXTRA UI AND POPULATE MENUS
    fll = cmds.lsUI(type='flowLayout')
    for f in fll:
        if 'modelEditorIconBar' in cmds.flowLayout(f, q=True, p=True):
            mPanel = cmds.flowLayout(
                f, q=True, p=True
            ).split('modelEditorIconBar')[0].split('|')[-2]
        ca = cmds.flowLayout(f, q=True, ca=True)
        for c in ca:
            if 'formLayout' in c:
                new = cmds.formLayout(c, q=True, ca=True)
                for n in new:
                    if 'XRayBtn' in n:
                        # CHECK OF THE REFRESH BUTTON AND CREATE
                        if cmds.objExists('mBarBttm' + f[-1]):
                            cmds.deleteUI('mBarBttm' + f[-1])
                        cmds.iconTextButton(
                            'mBarBttm' + f[-1],
                            label='[r]', p=f,
                            w=20, h=20,
                            i='cameralens.png',
                            c='mW.mMenuBarPlus()')
                        ui = 'mBarBttm' + f[-1]
                        ppc = cmds.popupMenu('mnmCamBttm', p=ui)
                        # FILL OPTION MENU
                        cam = cmds.ls(type='camera')
                        for c in cam:
                            tr = cmds.listRelatives(c, p=True)[0]
                            cmds.menuItem(
                                label=c.replace('Shape', ''),
                                c='mW.mMenuItemBar("' + tr +
                                '", "' + mPanel + '")',
                                p=ppc
                            )


def mMenuItemBar(out, panel):
    print out, panel
    mel.eval('lookThroughModelPanel ' + out + ' "' + panel + '"')
    cmds.renderWindowEditor("renderView", e=True, crc=out)

# def mMenuBarPlus():
#     # CLEAN UI
#     bttm = cmds.lsUI(type='button')
#     for b in bttm:
#         if 'mBar' in b:
#             cmds.deleteUI(b)
#     om = cmds.lsUI(type='optionMenu')
#     for o in om:
#         if 'mBar' in o:
#             cmds.deleteUI(o)
#     # CREATE EXTRA UI AND POPULATE MENUS
#     fll = cmds.lsUI(type='flowLayout')
#     for f in fll:
#         if 'modelEditorIconBar' in cmds.flowLayout(f, q=True, p=True):
#             mPanel = cmds.flowLayout(
#                 f, q=True, p=True
#                 ).split('modelEditorIconBar')[0].split('|')[-2]
#         ca = cmds.flowLayout(f, q=True, ca=True)
#         for c in ca:
#             if 'formLayout' in c:
#                 new = cmds.formLayout(c, q=True, ca=True)
#                 for n in new:
#                     if 'XRayBtn' in n:
#                         if cmds.objExists('mBarOM'+f[-1]):
#                             cmds.deleteUI('mBarOM'+f[-1])
#                         # MAKE THE OPTION MENU CHANGE COMMAND
#                         cmd = 'mel.eval(\'lookThroughModelPanel \'+cmds.optionMenu("mBarOM'+f[-1]+'", q=True, v=True)+\''+' "'+mPanel+'"\');cmds.renderWindowEditor("renderView", e=True, crc=cmds.optionMenu("mBarOM'+f[-1]+'", q=True, v=True))'
#                         # CREATE OPTION MENU
#                         cmds.optionMenu(
#                             'mBarOM'+f[-1],
#                             p=f,
#                             w=90,
#                             h=20,
#                             cc=cmd
#                             )
#                         # CHECK OF THE REFRESH BUTTON AND CREATE
#                         if cmds.objExists('mBarBttm'+f[-1]):
#                             cmds.deleteUI('mBarBttm'+f[-1])
#                         cmds.button(
#                             'mBarBttm'+f[-1],
#                             l='[r]',
#                             p=f,
#                             w=20,
#                             h=20,
#                             c='mW.mMenuBarPlus()'
#                             )
#                         # FILL OPTION MENU
#                         cam = cmds.ls(type='camera')
#                         for c in cam:
#                             cmds.menuItem(
#                                 l=c.replace('Shape', ''),
#                                 p='mBarOM'+f[-1]
#                                 )
