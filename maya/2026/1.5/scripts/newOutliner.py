# --MAYA-----------------------------------------------------------------------
#   Maurizio Giglioli September 09, 2016
#   Cleaned up / dockable version for Maya 2026.
# -----------------------------------------------------------------------------
#  Description:
#   Opens an extra Outliner with quick type filters in its top bar
#   (Geometry, nDynamics, Sets, animCurves, Cameras, Textures, Shaders,
#   plus Shapes / Hierarchy toggles and a Plugins menu).
#
#   - Each call opens a new outliner in a workspaceControl, so it floats or
#     docks like any Maya panel. The Dock / Float button in the top bar docks
#     it next to the viewport.
#   - Each outliner owns at most ONE set of filter nodes. They are replaced
#     when the filter changes, never saved into the scene file, and deleted
#     when the outliner is closed.
#
#  Usage:
#   import newOutliner
#   newOutliner.do_newOutliner()             # floating
#   newOutliner.do_newOutliner(docked=True)  # docked next to the viewport
#
#   newOutliner.purge_unused_filters()       # report filter nodes left by old versions
#   newOutliner.purge_unused_filters(False)  # ...and delete them
# -----------------------------------------------------------------------------
from contextlib import contextmanager

import maya.cmds as cmds
import maya.api.OpenMaya as om

LABEL = "New Outliner"
_PREFIX = "mgNewOutliner"

# (annotation, icon)
TYPE_BUTTONS = (
    ("Geometry", "Shaded.png"),
    ("nDynamics", "nClothCreate.png"),
    ("Sets", "menuIconEdit.png"),
    ("animCurves", "setKeyframe.png"),
    ("Cameras", "view.png"),
    ("Textures", "Textured.png"),
    ("Shaders", "render_layeredTexture.png"),
)

# Loaded plugins whose name contains one of these show up in the Plugins menu.
PLUGINS = ("SOuP", "mtoa", "Mayatomr", "Substance", "redshift4maya")

_sessions = {}     # workspaceControl name -> _Session
_type_cache = {}   # category -> [node types], built once per Maya session


class _Session(object):
    def __init__(self, ctrl, panel, editor):
        self.ctrl = ctrl
        self.panel = panel
        self.editor = editor
        self.categories = set()   # active type buttons
        self.plugins = set()      # active plugin filters
        self.shapes = False
        self.hierarchy = True
        self.filter_nodes = set() # filter nodes this outliner created and owns
        self.dock_button = None


# --------------------------------------------------------------------------- helpers

@contextmanager
def _no_undo():
    state = cmds.undoInfo(query=True, stateWithoutFlush=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=state)


def _filter_nodes():
    return set(cmds.ls(type="objectFilter") or [])


def _do_not_write(node):
    """Keeps a node out of saved scene files."""
    try:
        sel = om.MSelectionList()
        sel.add(node)
        om.MFnDependencyNode(sel.getDependNode(0)).setDoNotWrite(True)
    except RuntimeError:
        pass


def _delete_nodes(nodes):
    nodes = [n for n in nodes if cmds.objExists(n)]
    if not nodes:
        return
    with _no_undo():
        for n in nodes:
            try:
                cmds.lockNode(n, lock=False)
            except RuntimeError:
                pass
        try:
            cmds.delete(nodes)
        except RuntimeError as err:
            cmds.warning("New Outliner: could not delete filter nodes: {}".format(err))


def _types_for(category):
    if category in _type_cache:
        return _type_cache[category]

    all_types = _type_cache.get("_all")
    if all_types is None:
        all_types = _type_cache["_all"] = cmds.allNodeTypes() or []

    if category == "Geometry":
        types = ["mesh", "subdiv", "nurbsSurface", "nurbsCurve"]
    elif category == "nDynamics":
        types = [t for t in all_types if len(t) > 1 and t[0] == "n" and t[1].isupper()] + ["nucleus"]
    elif category == "Sets":
        types = [t for t in all_types if "Set" in t]
    elif category == "animCurves":
        types = [t for t in all_types if "animCurve" in t]
    elif category == "Cameras":
        types = [t for t in all_types if "camera" in t] + ["imagePlane"]
    elif category == "Textures":
        types = cmds.listNodeTypes("texture") or []
    elif category == "Shaders":
        types = cmds.listNodeTypes("shader") or []
    else:
        types = []

    _type_cache[category] = types
    return types


def _supported_loaded_plugins():
    loaded = cmds.pluginInfo(query=True, listPlugins=True) or []
    keys = [k.lower() for k in PLUGINS]
    return sorted(p for p in loaded if any(k in p.lower() for k in keys))


def _plugin_types(plugin):
    if not cmds.pluginInfo(plugin, query=True, loaded=True):
        return []
    return cmds.pluginInfo(plugin, query=True, dependNode=True) or []


# --------------------------------------------------------------------------- filtering

def _apply(ctrl):
    """Rebuilds this outliner's filter from the button states."""
    s = _sessions.get(ctrl)
    if s is None or not cmds.outlinerEditor(s.editor, exists=True):
        return

    types = []
    for category, _ in TYPE_BUTTONS:
        if category in s.categories:
            types.extend(_types_for(category))
    for plugin in sorted(s.plugins):
        types.extend(_plugin_types(plugin))
    types = list(dict.fromkeys(types))  # unique, keep order

    filtering = bool(s.categories or s.plugins)
    filter_name, new_nodes = "", set()

    if types:
        with _no_undo():
            before = _filter_nodes()
            filter_name = cmds.itemFilter(byType=types)
            new_nodes = _filter_nodes() - before
        for n in new_nodes:
            _do_not_write(n)

    # Apply the new filter first, then remove the old one the editor no longer uses.
    cmds.outlinerEditor(
        s.editor, edit=True,
        showDagOnly=not filtering,
        showShapes=s.shapes,
        ignoreDagHierarchy=not s.hierarchy,
        filter=filter_name,
    )
    _delete_nodes(s.filter_nodes - new_nodes)
    s.filter_nodes = new_nodes


def _toggle_category(ctrl, category, value):
    s = _sessions.get(ctrl)
    if s is None:
        return
    (s.categories.add if value else s.categories.discard)(category)
    _apply(ctrl)


def _toggle_plugin(ctrl, plugin, value):
    s = _sessions.get(ctrl)
    if s is None:
        return
    (s.plugins.add if value else s.plugins.discard)(plugin)
    _apply(ctrl)


def _clear_plugins(ctrl):
    s = _sessions.get(ctrl)
    if s is not None and s.plugins:
        s.plugins.clear()
        _apply(ctrl)


def _set_shapes(ctrl, value):
    s = _sessions.get(ctrl)
    if s is not None:
        s.shapes = bool(value)
        cmds.outlinerEditor(s.editor, edit=True, showShapes=s.shapes)


def _set_hierarchy(ctrl, value):
    s = _sessions.get(ctrl)
    if s is not None:
        s.hierarchy = bool(value)
        cmds.outlinerEditor(s.editor, edit=True, ignoreDagHierarchy=not s.hierarchy)


def _fill_plugin_menu(ctrl, menu):
    s = _sessions.get(ctrl)
    cmds.popupMenu(menu, edit=True, deleteAllItems=True)
    if s is None:
        return

    plugins = _supported_loaded_plugins()
    if not plugins:
        cmds.menuItem(label="No supported plugins loaded", enable=False, parent=menu)
        return

    for plugin in plugins:
        cmds.menuItem(label=plugin, checkBox=plugin in s.plugins, parent=menu,
                      command=lambda value, p=plugin: _toggle_plugin(ctrl, p, value))
    cmds.menuItem(divider=True, parent=menu)
    cmds.menuItem(label="Clear plugin filters", parent=menu,
                  command=lambda *_: _clear_plugins(ctrl))


def _on_scene_changed(ctrl):
    # A new / opened scene wipes our filter nodes; rebuild them.
    s = _sessions.get(ctrl)
    if s is not None:
        s.filter_nodes = {n for n in s.filter_nodes if cmds.objExists(n)}
        _apply(ctrl)


# --------------------------------------------------------------------------- dock / float

def _update_dock_button(ctrl):
    s = _sessions.get(ctrl)
    if s is None or not cmds.workspaceControl(ctrl, exists=True):
        return
    if s.dock_button and cmds.button(s.dock_button, exists=True):
        floating = cmds.workspaceControl(ctrl, query=True, floating=True)
        cmds.button(s.dock_button, edit=True,
                    label="Dock" if floating else "Float",
                    annotation="Dock next to the viewport" if floating else "Undock into a floating window")


def _toggle_dock(ctrl):
    if not cmds.workspaceControl(ctrl, exists=True):
        return
    if cmds.workspaceControl(ctrl, query=True, floating=True):
        try:
            cmds.workspaceControl(ctrl, edit=True, dockToControl=("MainPane", "right"))
        except RuntimeError:
            cmds.workspaceControl(ctrl, edit=True, dockToMainWindow=("right", False))
    else:
        cmds.workspaceControl(ctrl, edit=True, floating=True)
    cmds.evalDeferred(lambda: _update_dock_button(ctrl))


# --------------------------------------------------------------------------- build / close

def _unique_names():
    i = 1
    while (cmds.workspaceControl("{}{}".format(_PREFIX, i), exists=True)
           or cmds.panel("{}Panel{}".format(_PREFIX, i), exists=True)):
        i += 1
    return "{}{}".format(_PREFIX, i), "{}Panel{}".format(_PREFIX, i)


def _icon_check(ann, icon, command, value=False):
    return cmds.iconTextCheckBox(style="iconOnly", image1=icon, width=22, height=22,
                                 annotation=ann, value=value, changeCommand=command)


def _build(ctrl, panel_name):
    cmds.setParent(ctrl)
    form = cmds.formLayout()

    n_types = len(TYPE_BUTTONS)
    bar = cmds.rowLayout(numberOfColumns=n_types + 5, adjustableColumn=n_types + 1,
                         height=26, columnAttach=(1, "left", 4))
    for category, icon in TYPE_BUTTONS:
        _icon_check(category, icon, lambda v, c=category: _toggle_category(ctrl, c, v))

    cmds.separator(style="none")

    _icon_check("Shapes", "pickGeometryObj.png", lambda v: _set_shapes(ctrl, v))
    _icon_check("Hierarchy", "menuIconGraph.png", lambda v: _set_hierarchy(ctrl, v), value=True)

    plug_btn = cmds.iconTextButton(style="iconOnly", image1="unmuted.png", width=22, height=22,
                                   annotation="Plugins (click for menu)")
    for mouse_button in (1, 3):
        menu = cmds.popupMenu(parent=plug_btn, button=mouse_button)
        cmds.popupMenu(menu, edit=True,
                       postMenuCommand=lambda *_, m=menu: _fill_plugin_menu(ctrl, m))

    dock_btn = cmds.button(label="Dock", height=20, width=46,
                           command=lambda *_: _toggle_dock(ctrl))
    cmds.setParent(form)

    pane = cmds.paneLayout(configuration="single")
    panel = cmds.outlinerPanel(panel_name, menuBarVisible=False, label=LABEL)
    editor = cmds.outlinerPanel(panel, query=True, outlinerEditor=True)
    cmds.outlinerEditor(
        editor, edit=True,
        mainListConnection="worldList",
        selectionConnection="modelList",
        showShapes=False,
        showAttributes=False,
        showConnected=False,
        showAnimCurvesOnly=False,
        autoExpand=False,
        showDagOnly=True,
        ignoreDagHierarchy=False,
        expandConnections=False,
        showCompounds=True,
        showNumericAttrsOnly=False,
        highlightActive=True,
        autoSelectNewObjects=False,
        doNotSelectNewObjects=False,
        transmitFilters=False,
        showSetMembers=True,
        showNamespace=True,
        setFilter="defaultSetFilter",
    )
    cmds.setParent(form)

    cmds.formLayout(form, edit=True,
                    attachForm=[(bar, "top", 2), (bar, "left", 2), (bar, "right", 2),
                                (pane, "left", 0), (pane, "right", 0), (pane, "bottom", 0)],
                    attachControl=[(pane, "top", 2, bar)])

    for event in ("SceneOpened", "NewSceneOpened"):
        cmds.scriptJob(event=[event, lambda: _on_scene_changed(ctrl)], parent=form)

    return panel, editor, dock_btn


def _on_close(ctrl):
    # The control is still being torn down here; clean up on the next idle.
    cmds.evalDeferred(lambda: _cleanup(ctrl))


def _cleanup(ctrl):
    s = _sessions.pop(ctrl, None)
    if s is None:
        return

    if cmds.outlinerEditor(s.editor, exists=True):
        cmds.outlinerEditor(s.editor, edit=True, filter="")
    if cmds.panel(s.panel, exists=True):
        cmds.deleteUI(s.panel, panel=True)
    if cmds.workspaceControl(ctrl, exists=True):
        cmds.deleteUI(ctrl, control=True)
    if cmds.workspaceControlState(ctrl, exists=True):
        cmds.workspaceControlState(ctrl, remove=True)

    _delete_nodes(s.filter_nodes)


def newOutliner(docked=False):
    ctrl, panel_name = _unique_names()

    cmds.workspaceControl(
        ctrl,
        label=LABEL,
        retain=False,
        floating=True,
        initialWidth=300,
        initialHeight=750,
        minimumWidth=150,
        closeCommand=lambda: _on_close(ctrl),
        visibleChangeCommand=lambda *_: cmds.evalDeferred(lambda: _update_dock_button(ctrl)),
    )

    panel, editor, dock_btn = _build(ctrl, panel_name)
    session = _Session(ctrl, panel, editor)
    session.dock_button = dock_btn
    _sessions[ctrl] = session

    if docked:
        _toggle_dock(ctrl)
    return ctrl


def do_newOutliner(docked=False):
    return newOutliner(docked=docked)


def cleanup_all():
    """Closes every New Outliner and deletes their panels and filter nodes."""
    for ctrl in list(_sessions):
        if cmds.workspaceControl(ctrl, exists=True):
            cmds.workspaceControl(ctrl, edit=True, close=True)
        _cleanup(ctrl)


# --------------------------------------------------------------------------- old scenes

def _filters_in_use():
    used = set()
    for editor in cmds.lsUI(editors=True) or []:
        try:
            f = cmds.outlinerEditor(editor, query=True, filter=True)
        except (RuntimeError, TypeError):
            continue
        if f and cmds.objExists(f):
            used.add(f)
    for f in list(used):
        used.update(cmds.listHistory(f) or [])
    return used


def purge_unused_filters(dry_run=True):
    """
    Finds filter nodes left behind by the old version of this tool (or anything
    else): not used by any open outliner, not built-in, not saved by the user,
    not referenced. With dry_run=False they are deleted.
    """
    candidates = set()
    for f in _filter_nodes() - _filters_in_use():
        if f.startswith("default") or cmds.referenceQuery(f, isNodeReferenced=True):
            continue
        try:
            if cmds.itemFilter(f, query=True, classification=True) in ("builtIn", "user"):
                continue
        except (RuntimeError, TypeError):
            pass
        candidates.add(f)

    # Keep anything that still feeds a node we are not deleting.
    changed = True
    while changed:
        changed = False
        for f in list(candidates):
            outputs = set(cmds.listConnections(f, source=False, destination=True) or [])
            if outputs - candidates:
                candidates.discard(f)
                changed = True

    candidates = sorted(candidates)
    if dry_run:
        print("New Outliner: {} unused filter nodes found (run purge_unused_filters(False) to delete):"
              .format(len(candidates)))
        for f in candidates:
            print("    " + f)
    else:
        _delete_nodes(candidates)
        print("New Outliner: deleted {} unused filter nodes.".format(len(candidates)))
    return candidates


if __name__ == "__main__":
    do_newOutliner()