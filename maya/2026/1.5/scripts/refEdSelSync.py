# -*- coding: utf-8 -*-
"""
refEdSelSync.py - two-way selection sync between the Reference Editor and the scene.

  * Select an entry in the Reference Editor  -> the top node(s) of that
    reference get selected in Maya.
  * Select the top node of a reference in Maya -> the matching entry gets
    selected in the Reference Editor.
  * A "Sel Sync" toggle button is added to the Reference Editor menu bar.
    Turning it off kills the scriptJob; the on/off state is stored in an
    optionVar, so it is remembered between openings (and Maya sessions).

HOW IT WORKS (v3, Maya 2026 friendly)
    The Reference Editor is not a scripted panel any more, so there is no
    callback to hook when it opens.  install() starts one small watcher timer
    (4 times a second, one cheap query) that:
      - notices the Reference Editor opening  -> adds the button and, if the
        feature is on, creates the SelectionChanged scriptJob (scene -> editor)
      - notices the editor selection changing -> selects the top nodes
      - notices the editor closing            -> kills the scriptJob

INSTALL
    Put this file in your Maya scripts folder and add to userSetup.py:

        import maya.cmds as cmds
        cmds.evalDeferred("import refEdSelSync; refEdSelSync.install()",
                          lowestPriority=True)

    Or just run once per session:

        import refEdSelSync
        refEdSelSync.install()

OTHER CALLS
    refEdSelSync.toggle()      # flip on/off from a shelf button / hotkey
    refEdSelSync.show()        # install + open the Reference Editor
    refEdSelSync.uninstall()   # remove everything
    refEdSelSync.diagnose()    # print what the tool can see
"""
import time
import traceback

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui

try:                                    # Maya 2025+
    from PySide6 import QtCore, QtWidgets
    from shiboken6 import wrapInstance
except ImportError:                     # Maya 2017 - 2024
    from PySide2 import QtCore, QtWidgets
    from shiboken2 import wrapInstance

try:
    try:
        from PySide6.QtTest import QTest
    except ImportError:
        from PySide2.QtTest import QTest
except ImportError:
    QTest = None

OPT_VAR = 'refEdSelSync_enabled'
BTN_NAME = 'refEdSelSyncButton'
MENU_NAME = 'refEdSelSyncMenu'
TIMER_NAME = 'refEdSelSyncTimer'
INTERVAL_MS = 250

_state = {
    'timer': None,      # watcher QTimer
    'job': None,        # SelectionChanged scriptJob id
    'ed': None,         # sceneEditor name
    'win': None,        # window the editor currently lives in (None = closed)
    'last_refs': (),    # last seen editor selection
    'no_button': None,  # window for which button creation already failed
    'warned': False,
}


# --------------------------------------------------------------------------
# saved state
# --------------------------------------------------------------------------
def is_enabled():
    if not cmds.optionVar(exists=OPT_VAR):
        return True
    return bool(cmds.optionVar(q=OPT_VAR))


def set_enabled(state):
    """Turn the feature on/off, remember it, create/kill the scriptJob."""
    state = bool(state)
    cmds.optionVar(iv=(OPT_VAR, int(state)))
    if state and _window():
        _start_job()
    else:
        _stop_job()
    _refresh_button()


def toggle():
    set_enabled(not is_enabled())


# --------------------------------------------------------------------------
# finding the Reference Editor UI
# --------------------------------------------------------------------------
def _is_scene_editor(name):
    try:
        return bool(name) and bool(cmds.sceneEditor(name, exists=True))
    except RuntimeError:
        return False


def _editor_name():
    """Name of the sceneEditor used by the Reference Editor (cached)."""
    if _is_scene_editor(_state['ed']):
        return _state['ed']
    name = None
    try:
        name = mel.eval('global string $gReferenceEditorPanel; '
                        '$refEdSelSyncTmp = $gReferenceEditorPanel;')
    except RuntimeError:
        pass
    if not _is_scene_editor(name):
        name = None
        for ed in cmds.lsUI(editors=True) or []:
            if _is_scene_editor(ed):
                name = ed
                break
    _state['ed'] = name
    return name


def _window():
    """Name of the window showing the Reference Editor, None if closed."""
    ed = _editor_name()
    if not ed:
        return None
    try:
        ctl = cmds.sceneEditor(ed, q=True, control=True)
    except RuntimeError:
        return None
    if not ctl or ctl == 'NONE':
        return None
    win = ctl.split('|')[0]
    try:
        if cmds.window(win, exists=True):
            return win if cmds.window(win, q=True, visible=True) else None
        return win if cmds.control(ctl, exists=True) else None
    except RuntimeError:
        return None


def _wrap(ptr):
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


def _win_widget(win):
    if not win:
        return None
    w = _wrap(omui.MQtUtil.findWindow(win) or omui.MQtUtil.findControl(win) or
              omui.MQtUtil.findLayout(win))
    if w is None:
        for top in QtWidgets.QApplication.topLevelWidgets():
            if top.objectName() == win:
                return top
    return w


def _main_window():
    return _wrap(omui.MQtUtil.mainWindow())


# --------------------------------------------------------------------------
# the toggle button
# --------------------------------------------------------------------------
def _find_button(win=None):
    w = _win_widget(win or _state['win'])
    if w is None:
        return None
    return w.findChild(QtWidgets.QPushButton, BTN_NAME)


def _has_menu_fallback():
    try:
        return bool(cmds.menu(MENU_NAME, exists=True))
    except RuntimeError:
        return False


def _build_button(win):
    if _find_button(win) is not None or _has_menu_fallback():
        _refresh_button()
        return
    if _state['no_button'] == win:
        return
    w = _win_widget(win)
    bars = w.findChildren(QtWidgets.QMenuBar) if w is not None else []
    if bars:
        bar = bars[0]
        btn = QtWidgets.QPushButton(bar)
        btn.setObjectName(BTN_NAME)
        btn.setCheckable(True)
        btn.setToolTip('Sync selection between the Reference Editor and the '
                       'scene (reference entry <-> reference top node).')
        btn.toggled.connect(set_enabled)
        bar.setCornerWidget(btn, QtCore.Qt.TopRightCorner)
        btn.show()
    else:
        # no Qt menu bar found: add a small menu with a check box instead
        try:
            cmds.menu(MENU_NAME, parent=win, label='Sel Sync')
            cmds.menuItem(MENU_NAME + 'Item', parent=MENU_NAME,
                          label='Sync selection with scene', checkBox=True,
                          command=lambda value, *_: set_enabled(value))
        except RuntimeError:
            _state['no_button'] = win
            cmds.warning('refEdSelSync: could not add the button to the '
                         'Reference Editor (use refEdSelSync.toggle()).')
            return
    _refresh_button()


def _refresh_button():
    on = is_enabled()
    btn = _find_button()
    if btn is not None:
        btn.blockSignals(True)
        btn.setChecked(on)
        btn.blockSignals(False)
        btn.setText('Sel Sync: ON' if on else 'Sel Sync: OFF')
        btn.setStyleSheet('QPushButton{padding:2px 8px;%s}' %
                          ('background-color:#5a8a5a;color:white;' if on else ''))
    if _has_menu_fallback():
        try:
            cmds.menu(MENU_NAME, e=True,
                      label='Sel Sync: ON' if on else 'Sel Sync: OFF')
            cmds.menuItem(MENU_NAME + 'Item', e=True, checkBox=on)
        except RuntimeError:
            pass


def _remove_button():
    btn = _find_button()
    if btn is not None:
        btn.setParent(None)
        btn.deleteLater()
    if _has_menu_fallback():
        try:
            cmds.deleteUI(MENU_NAME, menu=True)
        except RuntimeError:
            pass


# --------------------------------------------------------------------------
# scriptJob (scene -> editor)
# --------------------------------------------------------------------------
def _start_job():
    _stop_job()
    win = _window()
    if not win:
        return
    ed = _editor_name()
    _state['last_refs'] = tuple(_selected_refs(ed))   # no jump on start
    try:
        _state['job'] = cmds.scriptJob(
            event=['SelectionChanged', _scene_to_editor], parent=win)
    except RuntimeError:
        _state['job'] = cmds.scriptJob(
            event=['SelectionChanged', _scene_to_editor])


def _stop_job():
    job = _state['job']
    if job is not None and cmds.scriptJob(exists=job):
        cmds.scriptJob(kill=job, force=True)
    _state['job'] = None


def _kill_stray_jobs():
    """Jobs left behind by a previous import/reload of this module."""
    for entry in cmds.scriptJob(listJobs=True) or []:
        if '_scene_to_editor' in entry:
            try:
                cmds.scriptJob(kill=int(entry.split(':')[0]), force=True)
            except Exception:
                pass


# --------------------------------------------------------------------------
# reference helpers
# --------------------------------------------------------------------------
def _selected_refs(ed):
    try:
        return cmds.sceneEditor(ed, q=True, selectReference=True) or []
    except RuntimeError:
        return []


def _top_nodes(ref_node):
    """DAG nodes of a reference whose parent is not part of that reference."""
    try:
        nodes = cmds.referenceQuery(ref_node, nodes=True, dagPath=True) or []
    except RuntimeError:            # unloaded reference
        return []
    dag = cmds.ls(nodes, long=True, type='transform') or []
    dag_set = set(dag)
    tops = [n for n in dag if n.rsplit('|', 1)[0] not in dag_set]
    if not tops:
        # file that only contains other references: use their top nodes
        try:
            children = cmds.referenceQuery(ref_node, referenceNode=True,
                                           child=True) or []
        except RuntimeError:
            children = []
        for child in children:
            tops.extend(_top_nodes(child))
    return tops


def _ref_of_top_node(node):
    """Reference node if `node` is the top node of a reference, else None."""
    try:
        if not cmds.referenceQuery(node, isNodeReferenced=True):
            return None
        rn = cmds.referenceQuery(node, referenceNode=True)
        parent = cmds.listRelatives(node, parent=True, fullPath=True)
        if (parent and cmds.referenceQuery(parent[0], isNodeReferenced=True) and
                cmds.referenceQuery(parent[0], referenceNode=True) == rn):
            return None             # parent is in the same reference: not a top
        return rn
    except RuntimeError:
        return None


# --------------------------------------------------------------------------
# editor -> scene (called by the watcher when the editor selection changes)
# --------------------------------------------------------------------------
def _editor_to_scene(ed):
    refs = tuple(_selected_refs(ed))
    if refs == _state['last_refs']:
        return
    _state['last_refs'] = refs
    tops = []
    for rn in refs:
        for n in _top_nodes(rn):
            if n not in tops:
                tops.append(n)
    if not tops:
        return
    if set(tops) == set(cmds.ls(selection=True, long=True) or []):
        return
    cmds.select(tops, replace=True)


# --------------------------------------------------------------------------
# scene -> editor (scriptJob callback)
# --------------------------------------------------------------------------
def _scene_to_editor():
    if not is_enabled():
        return
    ed = _editor_name()
    if not ed or not _window():
        return
    targets = []
    for node in cmds.ls(selection=True, long=True, type='transform') or []:
        rn = _ref_of_top_node(node)
        if rn and rn not in targets:
            targets.append(rn)
    if not targets or set(targets) == set(_selected_refs(ed)):
        return
    # ignore the editor's own selection change for a moment, so the watcher
    # does not echo it back to the scene and drop the user's selection
    _state['mute_until'] = time.time() + 0.75
    _select_refs(ed, targets)
    _state['last_refs'] = tuple(_selected_refs(ed))


def _item_views(win):
    """List/tree widgets inside the Reference Editor (minus combo popups)."""
    w = _win_widget(win)
    if w is None:
        return []
    views = []
    for v in w.findChildren(QtWidgets.QAbstractItemView):
        p, in_combo = v.parentWidget(), False
        while p is not None and p != w:
            if p.inherits('QComboBox'):
                in_combo = True
                break
            p = p.parentWidget()
        if not in_combo:
            views.append(v)
    return views


def _iter_rows(model, parent=None):
    parent = parent if parent is not None else QtCore.QModelIndex()
    for row in range(model.rowCount(parent)):
        idx = model.index(row, 0, parent)
        yield idx
        for child in _iter_rows(model, idx):
            yield child


def _ref_labels(rn):
    """Texts the Reference Editor may show for a reference node."""
    labels = set([rn])
    try:
        ns = (cmds.referenceQuery(rn, namespace=True) or '').lstrip(':')
        if ns:
            labels.update([ns, ns.split(':')[-1]])
    except RuntimeError:
        pass
    for kw in ({}, {'unresolvedName': True}, {'withoutCopyNumber': True}):
        try:
            f = cmds.referenceQuery(rn, filename=True, **kw)
        except RuntimeError:
            continue
        if f:
            labels.update([f, f.replace('\\', '/').rsplit('/', 1)[-1]])
    return labels


def _index_by_text(view, rn):
    """Row of `rn` found by comparing the row texts with its labels."""
    model = view.model()
    if model is None:
        return None
    labels = _ref_labels(rn)
    for idx in _iter_rows(model):
        for col in range(max(1, model.columnCount(idx.parent()))):
            data = model.data(idx.sibling(idx.row(), col),
                              QtCore.Qt.DisplayRole)
            if data and (u'%s' % data).strip() in labels:
                return idx
    return None


def _expand_to(view, idx):
    if hasattr(view, 'expand'):
        parent = idx.parent()
        while parent.isValid():
            view.expand(parent)
            parent = parent.parent()


def _apply_selection_model(view, indexes):
    sm = view.selectionModel()
    if sm is None:
        return
    sel = QtCore.QItemSelection()
    for idx in indexes:
        _expand_to(view, idx)
        sel.select(idx, idx)
    sm.select(sel, QtCore.QItemSelectionModel.ClearAndSelect |
              QtCore.QItemSelectionModel.Rows)
    sm.setCurrentIndex(indexes[0], QtCore.QItemSelectionModel.NoUpdate)
    view.scrollTo(indexes[0])


def _apply_clicks(view, indexes):
    """Click the first row, Ctrl+click the others, like a user would."""
    if QTest is None:
        return False
    model = view.model()
    for i, idx in enumerate(indexes):
        _expand_to(view, idx)
        view.scrollTo(idx)
        rect = None
        for col in range(max(1, model.columnCount(idx.parent()))):
            r = view.visualRect(idx.sibling(idx.row(), col))
            if r.isValid() and r.width() > 4:
                rect = r
                break
        if rect is None:
            continue
        mod = QtCore.Qt.ControlModifier if i else QtCore.Qt.NoModifier
        QTest.mouseClick(view.viewport(), QtCore.Qt.LeftButton, mod,
                         rect.center())
    view.scrollTo(indexes[0])
    return True


def _select_refs(ed, targets):
    """Select one or several reference entries in the Reference Editor."""
    if len(targets) == 1:
        ok = _select_ref(ed, targets[0])
        _state['multi'] = 'single'
        return ok
    # 1) maybe the flag takes several names at once
    try:
        cmds.sceneEditor(ed, e=True, selectReference=targets)
    except Exception:
        pass
    if set(targets) <= set(_selected_refs(ed)):
        _state['multi'] = 'flag'
        return True

    # 2) find the row of every reference in the editor list
    views = _item_views(_state['win'] or _window())
    found = dict((v, []) for v in views)
    expected = set()
    for rn in targets:
        if _select_ref(ed, rn):
            expected.update(_selected_refs(ed))     # rn, or its parent
        for v in views:
            idx = None
            sm = v.selectionModel()
            if sm is not None:
                rows = sm.selectedRows() or sm.selectedIndexes()
                if rows:
                    idx = rows[0]
                elif sm.currentIndex().isValid():
                    idx = sm.currentIndex()
            if idx is None:
                idx = _index_by_text(v, rn)
            if idx is not None:
                idx = idx.sibling(idx.row(), 0)
                if idx not in found[v]:
                    found[v].append(idx)

    # 3) select all those rows together
    for v in sorted(views, key=lambda x: -len(found[x])):
        indexes = found[v]
        if len(indexes) < 2:
            continue
        _apply_selection_model(v, indexes)
        if expected and expected <= set(_selected_refs(ed)):
            _state['multi'] = 'selectionModel'
            return True
        if _apply_clicks(v, indexes) and expected <= set(_selected_refs(ed)):
            _state['multi'] = 'ctrlClick'
            return True
        _state['multi'] = 'rows selected (editor query disagrees)'
        return True

    _state['multi'] = 'failed: views=%d rows=%s' % (
        len(views), [len(found[v]) for v in views])
    if not _state.get('multi_warned'):
        _state['multi_warned'] = True
        cmds.warning('refEdSelSync: could not select several entries in the '
                     'Reference Editor. Run refEdSelSync.diagnose() and send '
                     'the output.')
    return False


def _select_ref(ed, ref_node):
    """Select the entry of `ref_node` in the Reference Editor."""
    try:
        cmds.sceneEditor(ed, e=True, selectReference=ref_node)
    except Exception:
        pass
    if ref_node in _selected_refs(ed):
        return True
    # fallback: walk the entries by index until the wanted one is selected
    count = len(cmds.ls(type='reference') or []) + 2
    for index in range(count):
        try:
            cmds.sceneEditor(ed, e=True, selectItem=index)
        except Exception:
            continue
        if ref_node in _selected_refs(ed):
            return True
    # nested reference that is not listed: fall back to its parent reference
    try:
        parent = cmds.referenceQuery(ref_node, referenceNode=True, parent=True)
    except RuntimeError:
        parent = None
    return _select_ref(ed, parent) if parent else False


# --------------------------------------------------------------------------
# watcher
# --------------------------------------------------------------------------
def _tick():
    try:
        win = _window()
        if win != _state['win']:            # editor opened or closed
            _stop_job()
            _state['win'] = win
            if win:
                _build_button(win)
                if is_enabled():
                    _start_job()
            return
        if not win:
            return
        if _find_button(win) is None and not _has_menu_fallback():
            _build_button(win)              # window was rebuilt
        if is_enabled():
            if _state['job'] is None or not cmds.scriptJob(exists=_state['job']):
                _start_job()
            if time.time() < _state.get('mute_until', 0):
                _state['last_refs'] = tuple(_selected_refs(_state['ed']))
                return
            _editor_to_scene(_state['ed'])
    except Exception:
        if not _state['warned']:
            _state['warned'] = True
            traceback.print_exc()
            cmds.warning('refEdSelSync: error in watcher (see Script Editor).')


def _kill_timers():
    main = _main_window()
    if main is not None:
        for old in main.findChildren(QtCore.QTimer, TIMER_NAME):
            old.stop()
            old.setParent(None)
            old.deleteLater()
    _state['timer'] = None


def install():
    """Start the watcher. Safe to call again (also after a reload)."""
    _kill_timers()
    _kill_stray_jobs()
    _state.update(job=None, win=None, warned=False, no_button=None)
    timer = QtCore.QTimer(_main_window())
    timer.setObjectName(TIMER_NAME)
    timer.setInterval(INTERVAL_MS)
    timer.timeout.connect(_tick)
    timer.start()
    _state['timer'] = timer
    _tick()                         # attach now if the editor is already open
    return True


def uninstall():
    """Stop the watcher, kill the scriptJob and remove the button."""
    _kill_timers()
    _stop_job()
    _kill_stray_jobs()
    _remove_button()
    _state['win'] = None


def show():
    """Install (if needed) and open the Reference Editor."""
    if _state['timer'] is None:
        install()
    mel.eval('ReferenceEditor')


# --------------------------------------------------------------------------
def diagnose():
    """Print everything the tool can see. Run with the Reference Editor open."""
    out = ['', '===== refEdSelSync diagnose (v5) =====']
    add = out.append
    add('maya version : %s' % cmds.about(version=True))
    add('enabled      : %s' % is_enabled())
    ed = _editor_name()
    add('editor name  : %s' % ed)
    win = _window()
    add('window       : %s (attached to: %s)' % (win, _state['win']))
    timer = _state['timer']
    add('timer        : %s' % (timer.isActive() if timer is not None else None))
    job = _state['job']
    add('scriptJob    : %s (alive: %s)' % (
        job, bool(job is not None and cmds.scriptJob(exists=job))))
    w = _win_widget(win)
    add('window widget: %s' % (w.metaObject().className() if w else None))
    if w is not None:
        add('menu bars    : %d' % len(w.findChildren(QtWidgets.QMenuBar)))
    for v in _item_views(win):
        sm = v.selectionModel()
        add('item view    : %s  selected rows: %s' % (
            v.metaObject().className(),
            len(sm.selectedRows()) if sm is not None else None))
    if w is not None and not _item_views(win):
        names = sorted(set(c.metaObject().className()
                           for c in w.findChildren(QtWidgets.QWidget)))
        add('item view    : none.  widget classes: %s' % names)
    add('multi select : last method used = %s' % _state.get('multi'))
    if ed:
        for v in _item_views(win):
            model = v.model()
            if model is None:
                continue
            for i, idx in enumerate(_iter_rows(model)):
                if i >= 8:
                    add('    ...')
                    break
                cells = [model.data(idx.sibling(idx.row(), c),
                                    QtCore.Qt.DisplayRole)
                         for c in range(model.columnCount(idx.parent()))]
                add('    row: %r' % [c for c in cells if c])
    add('button       : %s   menu fallback: %s' % (
        _find_button(win) is not None, _has_menu_fallback()))
    if ed:
        add('editor sel   : %s' % _selected_refs(ed))
        add('last seen    : %s' % (_state['last_refs'],))
        for rn in _selected_refs(ed):
            add('  top nodes of %s: %s' % (rn, _top_nodes(rn)))
    sel = cmds.ls(selection=True, long=True) or []
    add('scene sel    : %s' % sel)
    for n in sel[:5]:
        add('  %s -> top node of: %s' % (n, _ref_of_top_node(n)))
    add('======================================')
    print('\n'.join(out))


# if __name__ == '__main__':          # pasted / run from the Script Editor
#     install()