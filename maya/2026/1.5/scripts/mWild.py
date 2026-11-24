# ---------------------------------------------------------------------------
# PERSONAL WILD CARD POPUP ITEM MAKER FOR MAU
# ADDS FUNCTION TO REFERENCE EDITOR
# ---------------------------------------------------------------------------
# What it does
#   * Takes over Maya's status-line "select by name" field when the 'off/on'
#     checkbox is on.
#   * 'NS' checkbox + option menu: every pattern you type (or pick from the
#     popup) is resolved inside the chosen namespace before selecting.
#       - "* (any)"  -> searches every namespace (ls -recursive)
#       - "char01"   -> "L_*" becomes "char01:L_*"
#       - a pattern that already contains ':' (or a '|' DAG path) is used as is
#   * 'presets' checkbox: shows the preset patterns in the right-click popup,
#     already resolved with the current namespace and with a match count.
#   * Right-click the field for history + presets. The popup is rebuilt every
#     time it opens, so it always reflects the current namespace / toggles.
#   * Selection modifiers (Maya convention):
#       Shift = toggle, Ctrl = deselect, Ctrl+Shift = add
#   * Toggles, chosen namespace and history persist between sessions.
#
# Usage (e.g. in userSetup.py):
#   import mWild
#   cmds.evalDeferred(mWild.mSetWild, lowestPriority=True)
# ---------------------------------------------------------------------------
from functools import partial

import maya.mel as mel
import maya.cmds as cmds


# --------------------------------------------------------------------------- config
PRESETS = [
    'L_*', 'R_*', 'C_*', '*_CLS', '*_CLH',
    '*_MESH', '*_GEO', '*_COL',
    '*_GRP', '*_NULL', '*_LOC', '*_RIV',
]
HISTORY_MAX = 20
ANY_NS = '* (any)'
SKIP_NS = ('UI', 'shared')

# UI names
CB_ON = 'mnmWildCB'
CB_PRESET = 'mnmWildCB1'
CB_NS = 'mnmWildNSCB'
OM_NS = 'mnmWildOM'
POPUP = 'mnmWildPopup'

# optionVars
OV_ON = 'mnmWild_on'
OV_PRESET = 'mnmWild_presets'
OV_NS = 'mnmWild_ns'
OV_NS_NAME = 'mnmWild_nsName'
OV_HISTORY = 'mnmWild_history'


# --------------------------------------------------------------------------- small helpers
def _field():
    return mel.eval('$tempVar = $gTextualInputField')


def _noop(*_):
    pass


def _opt_get(key, default=None):
    if cmds.optionVar(exists=key):
        return cmds.optionVar(q=key)
    return default


def _opt_set_int(key, value):
    cmds.optionVar(iv=(key, int(bool(value))))


def _cb(name):
    """Checkbox value, False if the UI doesn't exist."""
    return cmds.checkBox(name, exists=True) and cmds.checkBox(name, q=True, v=True)


# --------------------------------------------------------------------------- history
def _load_history():
    hist = _opt_get(OV_HISTORY, [])
    if not isinstance(hist, (list, tuple)):   # optionVar returns 0 / str when odd
        hist = [hist] if hist else []
    return [h for h in hist if h][:HISTORY_MAX]


def _save_history(hist):
    cmds.optionVar(clearArray=OV_HISTORY)
    for h in hist:
        cmds.optionVar(stringValueAppend=(OV_HISTORY, h))


def _remember(pattern):
    hist = [h for h in _load_history() if h != pattern]
    hist.insert(0, pattern)
    _save_history(hist[:HISTORY_MAX])


def _clear_history(*_):
    _save_history([])


# --------------------------------------------------------------------------- namespaces
def _list_namespaces():
    """All namespaces, nested ones included, without the leading ':'."""
    found = cmds.namespaceInfo(':', listOnlyNamespaces=True, recurse=True) or []
    names = {n.lstrip(':') for n in found}
    return sorted(n for n in names if n and n not in SKIP_NS)


def _refresh_namespaces(*_):
    """Rebuild the namespace option menu, keeping the current choice if it still exists."""
    if not cmds.optionMenu(OM_NS, exists=True):
        return
    current = None
    if cmds.optionMenu(OM_NS, q=True, ni=True):
        current = cmds.optionMenu(OM_NS, q=True, v=True)
    current = current or _opt_get(OV_NS_NAME)

    for item in cmds.optionMenu(OM_NS, q=True, ill=True) or []:
        cmds.deleteUI(item)

    items = [ANY_NS] + _list_namespaces()
    for n in items:
        cmds.menuItem(label=n, p=OM_NS)
    if current in items:
        cmds.optionMenu(OM_NS, e=True, v=current)


def _current_ns():
    """Active namespace, or None when the NS checkbox is off."""
    if not _cb(CB_NS) or not cmds.optionMenu(OM_NS, exists=True):
        return None
    if not cmds.optionMenu(OM_NS, q=True, ni=True):
        return None
    return cmds.optionMenu(OM_NS, q=True, v=True) or None


def _resolve(pattern):
    """Return (pattern_for_ls, recursive) with the active namespace applied."""
    pattern = pattern.strip()
    ns = _current_ns()
    if not ns or ':' in pattern or '|' in pattern:
        return pattern, False
    if ns == ANY_NS:
        return pattern, True
    return '{}:{}'.format(ns, pattern), False


def _display(pattern):
    resolved, recursive = _resolve(pattern)
    return '{}   [any NS]'.format(resolved) if recursive else resolved


def _matches(pattern):
    resolved, recursive = _resolve(pattern)
    try:
        found = cmds.ls(resolved, recursive=recursive) or []
    except RuntimeError:
        found = []
    return resolved, found


# --------------------------------------------------------------------------- selection
def _select_pattern(pattern, remember=True):
    pattern = (pattern or '').strip()
    if not pattern:
        return
    resolved, found = _matches(pattern)
    if not found:
        cmds.warning('mWild: nothing matches "{}"'.format(resolved))
        return

    mods = cmds.getModifiers()
    shift, ctrl = bool(mods & 1), bool(mods & 4)
    if shift and ctrl:
        cmds.select(found, add=True)
    elif ctrl:
        cmds.select(found, deselect=True)
    elif shift:
        cmds.select(found, toggle=True)
    else:
        cmds.select(found, replace=True)

    if remember:
        _remember(pattern)
    print('mWild: {} match(es) for "{}"'.format(len(found), resolved))


def _on_enter(*_):
    _select_pattern(cmds.textField(_field(), q=True, tx=True))


def _pick(pattern, *_):
    cmds.textField(_field(), e=True, tx=pattern)
    _select_pattern(pattern)


# --------------------------------------------------------------------------- popup
def _build_popup(*_):
    """Called every time the popup opens: history + presets, resolved with the current NS."""
    cmds.popupMenu(POPUP, e=True, deleteAllItems=True)

    ns = _current_ns()
    if ns:
        cmds.menuItem(label='Namespace: {}'.format(ns), en=False, p=POPUP)
        cmds.menuItem(divider=True, p=POPUP)

    hist = _load_history()
    if hist:
        for h in hist:
            cmds.menuItem(label=_display(h), p=POPUP, c=partial(_pick, h))
    else:
        cmds.menuItem(label='(no history yet)', en=False, p=POPUP)

    if _cb(CB_PRESET):
        cmds.menuItem(divider=True, dividerLabel='Presets', p=POPUP)
        for p in PRESETS:
            count = len(_matches(p)[1])
            cmds.menuItem(label='{}   ({})'.format(_display(p), count),
                          en=bool(count), p=POPUP, c=partial(_pick, p))

    cmds.menuItem(divider=True, p=POPUP)
    cmds.menuItem(label='Clear history', p=POPUP, c=_clear_history)


def _ensure_popup():
    if not cmds.popupMenu(POPUP, exists=True):
        cmds.popupMenu(POPUP, p=_field(), postMenuCommand=_build_popup)


def mCleanWild():
    if cmds.popupMenu(POPUP, exists=True):
        cmds.deleteUI(POPUP)


# --------------------------------------------------------------------------- field takeover
def mChangeWild(state):
    """1 = mWild drives the select-by-name field, 0 = back to Maya's default."""
    f = _field()
    if state:
        # enterCommand does the work; changeCommand silenced so it doesn't
        # also fire Maya's own select (or ours twice) on Enter / focus-out.
        cmds.textField(f, e=True, cc=_noop, ec=_on_enter)
        _ensure_popup()
    else:
        cmds.textField(
            f, e=True,
            cc=lambda *_: mel.eval('quickWildcardSelect'),
            ec=lambda *_: mel.eval('quickWildcardSelect'),
        )
        mCleanWild()


# --------------------------------------------------------------------------- toggle callbacks
def _on_toggle(state, *_):
    state = bool(state)
    _opt_set_int(OV_ON, state)
    cmds.checkBox(CB_ON, e=True, l='on' if state else 'off')
    cmds.checkBox(CB_PRESET, e=True, en=state)
    cmds.checkBox(CB_NS, e=True, en=state)
    cmds.optionMenu(OM_NS, e=True, en=state and _cb(CB_NS))
    if state:
        _refresh_namespaces()
    mChangeWild(1 if state else 0)


def _on_ns_toggle(state, *_):
    _opt_set_int(OV_NS, state)
    cmds.optionMenu(OM_NS, e=True, en=bool(state))
    if state:
        _refresh_namespaces()


def _on_preset_toggle(state, *_):
    _opt_set_int(OV_PRESET, state)


def _on_ns_change(value, *_):
    cmds.optionVar(sv=(OV_NS_NAME, value))


# --------------------------------------------------------------------------- outliner / references
def fixOutliner2017():
    for out in cmds.getPanel(type='outlinerPanel') or []:
        cmds.outlinerEditor(out, e=True, setFilter='defaultSetFilter')


def mReferenceEditor():
    cmds.ReferenceEditor()
    formRef = cmds.iconTextButton('createRefButton', q=True, p=True)
    btt, bttF = 'NE', 'FIX'
    if not cmds.button(btt, q=True, ex=True):
        cmds.button(btt, w=26, h=26, p=formRef, c=lambda *_: cmds.NamespaceEditor())
    if not cmds.button(bttF, q=True, ex=True):
        cmds.button(bttF, w=26, h=26, p=formRef, c=lambda *_: fixNameSpaces())
    cmds.formLayout(
        formRef, e=True,
        ac=[(btt, 'left', 10, 'refEdViewportButton'),
            (bttF, 'left', 5, btt)],
    )


def fixNameSpaces():
    added = []
    for ref in cmds.file(q=True, r=True) or []:
        ns = (cmds.file(ref, q=True, ns=True) or '').lstrip(':')
        if ns and not cmds.namespace(ex=':' + ns):
            cmds.namespace(add=ns, parent=':')
            cmds.warning('Added missing namespace: ' + ns)
            added.append(ns)
    _refresh_namespaces()
    msg = 'Recreated {} missing namespace(s)'.format(len(added)) if added else 'No missing namespaces'
    cmds.confirmDialog(t='Ole\'', m=msg)


# --------------------------------------------------------------------------- main UI
def mSetWild():
    gStatusLine = mel.eval('$tempVar = $gStatusLine')
    gToolBox = mel.eval('$tempVar = $gToolBox')

    uiP = [
        CB_ON, CB_PRESET, CB_NS, OM_NS,
        'mnmMauTools', 'mnmSetsManager', 'mnmPK', 'mnmPlugs', 'mnmPipe',
        'mnmMauRef', 'mnmMauRen',
    ]
    for u in uiP:
        if cmds.control(u, exists=True):
            cmds.deleteUI(u)
    mCleanWild()

    # ---- wildcard controls (status line)
    cmds.checkBox(CB_ON, v=False, label='off', p=gStatusLine, cc=_on_toggle,
                  ann='Use mWild for the select-by-name field')
    cmds.checkBox(CB_PRESET, en=False, label='presets', p=gStatusLine,
                  v=bool(_opt_get(OV_PRESET, 0)), cc=_on_preset_toggle,
                  ann='Show preset patterns in the right-click popup')
    cmds.checkBox(CB_NS, en=False, label='NS', p=gStatusLine,
                  v=bool(_opt_get(OV_NS, 0)), cc=_on_ns_toggle,
                  ann='Resolve patterns inside the chosen namespace')
    cmds.optionMenu(OM_NS, en=False, p=gStatusLine, cc=_on_ns_change,
                    ann='Namespace used for selection ("* (any)" = all namespaces)')
    try:  # Maya 2018+: refresh the namespace list right before the menu opens
        cmds.optionMenu(OM_NS, e=True, beforeShowPopup=_refresh_namespaces)
    except TypeError:
        pass
    _refresh_namespaces()
    for ev in ('SceneOpened', 'NewSceneOpened'):
        cmds.scriptJob(e=[ev, _refresh_namespaces], parent=OM_NS)

    # ---- toolbox buttons
    cmds.iconTextButton(
        'mnmPipe', label='', w=33, h=33, i='pipeline2.png',
        c='import toolLauncher;import importlib;importlib.reload(toolLauncher);toolLauncher.main()',
        p=gToolBox)
    cmds.button(
        'mnmMauTools', label='Mau', w=33, h=20,
        c='import mauTools;reload(mauTools);mauTools.restart()',
        p=gToolBox)
    cmds.iconTextButton(
        'mnmMauRen', label='Set', w=33, h=33, i='rigging_toolkit.png',
        c='import mauRenamer;import importlib;importlib.reload(mauRenamer);mauRenamer.mauRenamer_UI();',
        p=gToolBox)
    cmds.iconTextButton(
        'mnmSetsManager', label='Set', w=33, h=33, i='mSET.png',
        c='import mSetManager as ms;import importlib;importlib.reload(ms);ms.mSetManager_UI()',
        p=gToolBox)
    cmds.iconTextButton(
        'mnmPK', label='PK', w=33, h=33, i='mAssetPack.png',
        c='import mAssetPack as mA;import importlib;importlib.reload(mA);mA.mAssetPackUI()',
        p=gToolBox)
    cmds.button(
        'mnmMauRef', label='mRef', w=33, h=20,
        c='import mWild as mW;import importlib;importlib.reload(mW);mW.mReferenceEditor();',
        p=gToolBox)
    cmds.button(
        'mnmPlugs', label='PLUG', w=33, h=20,
        c=lambda *_: mel.eval('PluginManager'),
        p=gStatusLine)

    # ---- restore last state
    on = bool(_opt_get(OV_ON, 0))
    cmds.checkBox(CB_ON, e=True, v=on)
    _on_toggle(on)

    # EXTRA MENUBAR UI
    mMenuBarPlus()


# ===========================================================================
# Viewport camera button
# Adds a camera button to every viewport's icon bar. Left-click it to get the
# cameras in the scene; picking one looks through it in that viewport. The list
# is rebuilt every time the menu opens.
# ===========================================================================
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


def mMenuItemBar(camera, panel):
    """Look through the chosen camera in the given viewport."""
    if cmds.objExists(camera) and cmds.modelPanel(panel, exists=True):
        cmds.modelPanel(panel, e=True, camera=camera)


def _fill_camera_menu(menu, panel):
    cmds.popupMenu(menu, e=True, deleteAllItems=True)
    current = cmds.modelPanel(panel, q=True, camera=True) if cmds.modelPanel(panel, exists=True) else None
    for shape in sorted(cmds.ls(type='camera') or []):
        tr = cmds.listRelatives(shape, p=True)[0]
        cmds.menuItem(
            label=tr, p=menu,
            checkBox=(tr == current),
            c=lambda *_, t=tr, p=panel: mMenuItemBar(t, p),
        )


def mMenuBarPlus():
    for b in cmds.lsUI(type='iconTextButton', long=True) or []:
        if b.split('|')[-1].startswith('mBarBttm_'):
            cmds.deleteUI(b)

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
        menu = cmds.popupMenu(p=btn, button=1)
        cmds.popupMenu(
            menu, e=True,
            postMenuCommand=lambda *_, m=menu, p=panel: _fill_camera_menu(m, p),
        )


def install():
    """Run once Maya is idle, so the status line and viewport bars are fully built."""
    cmds.evalDeferred(mSetWild, lowestPriority=True)