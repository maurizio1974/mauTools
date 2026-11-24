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
    btt = 'NE'
    if not cmds.button(btt, q=True, ex=True):
        cmds.button(btt, w=26, h=26, p=formRef, c='cmds.NamespaceEditor()')
    bttF = 'FIX'
    if not cmds.button(bttF, q=True, ex=True):
        cmds.button(bttF, w=26, h=26, p=formRef, c='mW.fixNameSpaces()')
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
        'mnmMauTools', 'mnmSetsManager', 'mnmPK', 'mnmPlugs', 'mnmPipe',
        'mnmMauRef', 'mnmMauRen'
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
    cmds.iconTextButton(
        'mnmPipe',
        label='', w=33, h=33,
        i='pipeline2.png',
        c='import toolLauncher;import importlib;importlib.reload(toolLauncher);toolLauncher.main()',
        p=gToolBox
    )
    cmd = 'source "flipper.mel";mauTools();'
    cmds.button(
        'mnmMauTools',
        label='Mau', w=33, h=20,
        c='from maya import mel;mel.eval(\'' + cmd + '\')',
        p=gToolBox
    )
    cmds.iconTextButton(
        'mnmMauRen',
        label='Set', w=33, h=33,
        i='rigging_toolkit.png',
        c='import mauRenamer;import importlib;importlib.reload(mauRenamer);mauRenamer.mauRenamer_UI();',
        p=gToolBox
    )
    cmds.iconTextButton(
        'mnmSetsManager',
        label='Set', w=33, h=33,
        i='mSET.png',
        c='import mSetManager as ms;import importlib;importlib.reload(ms);ms.mSetManager_UI()',
        p=gToolBox
    )
    cmds.iconTextButton(
        'mnmPK',
        label='PK', w=33, h=33,
        i='mAssetPack.png',
        c='import mAssetPack as mA;import importlib;importlib.reload(mA);mA.mAssetPackUI()',
        p=gToolBox
    )
    cmds.button(
        'mnmMauRef',
        label='mRef', w=33, h=20,
        c='import mWild as mW;import importlib;importlib.reload(mW);mW.mReferenceEditor();',
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


"""
Adds a camera button to every viewport's icon bar.
Left-click the button to get a list of the cameras currently in the scene;
picking one looks through it in that viewport. The list is rebuilt every
time the menu opens, so new / deleted / renamed cameras always show up.

Usage:
    import mMenuBarPlus
    mMenuBarPlus.install()      # e.g. in userSetup.py
"""

# --------------------------------------------------------------------------- helpers
def _panel_from_path(path):
    """Find the modelPanel that owns a UI path."""
    for token in reversed(path.split('|')):
        if token and cmds.modelPanel(token, exists=True):
            return token
    return None


def _has_xray_button(flow):
    """True if this flowLayout is the viewport icon bar (contains the X-Ray button)."""
    for child in cmds.flowLayout(flow, q=True, ca=True) or []:
        child_path = flow + '|' + child
        if cmds.formLayout(child_path, exists=True):
            kids = cmds.formLayout(child_path, q=True, ca=True) or []
            if any('XRayBtn' in k for k in kids):
                return True
    return False


# --------------------------------------------------------------------------- menu
def mMenuItemBar(camera, panel):
    """Look through the chosen camera in the given viewport."""
    if cmds.objExists(camera) and cmds.modelPanel(panel, exists=True):
        cmds.modelPanel(panel, e=True, camera=camera)


def _fill_camera_menu(menu, panel):
    """Rebuild the camera list every time the menu opens."""
    cmds.popupMenu(menu, e=True, deleteAllItems=True)
    current = cmds.modelPanel(panel, q=True, camera=True) if cmds.modelPanel(panel, exists=True) else None

    for shape in sorted(cmds.ls(type='camera') or []):
        tr = cmds.listRelatives(shape, p=True)[0]
        cmds.menuItem(
            label=tr, p=menu,
            checkBox=(tr == current),  # tick the camera this viewport is using
            c=lambda *_, t=tr, p=panel: mMenuItemBar(t, p),
        )


# --------------------------------------------------------------------------- build
def mMenuBarPlus():
    # Remove old buttons
    for b in cmds.lsUI(type='iconTextButton', long=True) or []:
        if b.split('|')[-1].startswith('mBarBttm_'):
            cmds.deleteUI(b)

    # Add a button to every viewport icon bar
    for flow in cmds.lsUI(type='flowLayout', long=True) or []:
        parent = cmds.flowLayout(flow, q=True, p=True) or ''
        if 'modelEditorIconBar' not in parent:
            continue
        if not _has_xray_button(flow):
            continue
        panel = _panel_from_path(flow)
        if not panel:
            continue

        btn = cmds.iconTextButton(
            'mBarBttm_' + panel, p=flow, w=20, h=20,
            label='[r]', i='cameralens.png',
            ann='Click to choose a camera for this viewport',
        )
        menu = cmds.popupMenu(p=btn, button=1)  # 1 = left click, 3 = right click
        cmds.popupMenu(
            menu, e=True,
            postMenuCommand=lambda *_, m=menu, p=panel: _fill_camera_menu(m, p),
        )


def install():
    """Run once Maya is idle, so the viewport bars are fully built first."""
    cmds.evalDeferred(mMenuBarPlus, lowestPriority=True)
