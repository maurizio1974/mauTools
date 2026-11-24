"""Scene tools: viewport display, selection helpers, scene info, shelves.

Replaces shapeVis.py, xrayer.py, isolateMG.py, visUI.py, mgInfo.mel, the
selection half of readWriteAttr.mel and the display / selection procedures
of flipper.mel and mgUtility.mel.
"""
import json
import os
import re

from maya import cmds, mel

from . import selected, warn, shapes, tmp_file, keep_selection

SELECTION_FILE = 'mauTools_selection.json'

MENU_SETS = (
    ('anim', 'animationMenuSet'), ('model', 'modelingMenuSet'),
    ('rig', 'riggingMenuSet'), ('dyn', 'dynamicsMenuSet'),
    ('render', 'renderingMenuSet'))

# modelEditor flag, label
SHOW_FLAGS = (
    ('nurbsCurves', 'Curves'), ('nurbsSurfaces', 'Surfaces'),
    ('subdivSurfaces', 'SubD'), ('polymeshes', 'Polygons'),
    ('planes', 'Planes'), ('lights', 'Lights'),
    ('joints', 'Joints'), ('ikHandles', 'IK Handles'),
    ('deformers', 'Deformers'), ('dynamics', 'Dynamics'),
    ('fluids', 'Fluids'), ('hairSystems', 'Hair'),
    ('follicles', 'Follicles'), ('nCloths', 'nCloths'),
    ('nRigids', 'nRigids'), ('dynamicConstraints', 'Dyn Constraints'),
    ('locators', 'Locators'), ('dimensions', 'Distance'),
    ('pivots', 'Pivots'), ('handles', 'Handles'),
    ('textures', 'Textures'), ('strokes', 'Strokes'),
    ('manipulators', 'Manipulators'), ('cameras', 'Cameras'),
    ('cv', 'CVs'), ('hulls', 'Hulls'),
    ('grid', 'Grid'), ('hud', 'HUD'),
    ('sel', 'Selection'))

INFO_TYPES = (
    'camera', 'locator', 'cluster', 'lattice', 'wire', 'joint', 'nucleus',
    'nCloth', 'nParticle', 'nRigid', 'follicle', 'mesh', 'nurbsSurface',
    'wrap', 'attributeTransfer', 'textureToArray', 'multiAttributeTransfer',
    'point', 'group', 'scatter', 'shatter', 'instancer')


def menu_set(name):
    """Switch the main menu set (animationMenuSet, riggingMenuSet ...)."""
    try:
        mel.eval('workingMode %s' % name)
    except RuntimeError:
        cmds.setMenuMode(name)


# ---------------------------------------------------------------------------
# viewport
# ---------------------------------------------------------------------------
def model_panels(visible=True):
    panels = cmds.getPanel(type='modelPanel') or []
    if visible:
        shown = cmds.getPanel(visiblePanels=True) or []
        panels = [p for p in panels if p in shown]
    return panels


def active_model_panel():
    panel = cmds.getPanel(withFocus=True)
    if panel and cmds.getPanel(typeOf=panel) == 'modelPanel':
        return panel
    panels = model_panels()
    return panels[0] if panels else None


def toggle_template():
    """Toggle template on the selection, or on every mesh if nothing is
    selected."""
    for node in selected() or cmds.ls(type='mesh'):
        plug = node + '.template'
        if cmds.objExists(plug):
            cmds.setAttr(plug, not cmds.getAttr(plug))


def toggle_shape_visibility():
    for node in selected():
        for shape in shapes(node)[:1]:
            plug = shape + '.visibility'
            cmds.setAttr(plug, not cmds.getAttr(plug))


def toggle_xray():
    """Toggle x-ray on the selected objects, or on the active viewport if
    nothing is selected."""
    sel = selected()
    if sel:
        for node in sel:
            state = cmds.displaySurface(node, q=True, xRay=True)[0]
            cmds.displaySurface(node, xRay=not state)
        cmds.select(sel, r=True)
        return
    panel = active_model_panel()
    if panel:
        cmds.modelEditor(panel, e=True, xray=not cmds.modelEditor(
            panel, q=True, xray=True))


def reset_xray():
    """X-ray off on every mesh and every viewport."""
    with keep_selection():
        for mesh in cmds.ls(type='mesh'):
            cmds.displaySurface(mesh, xRay=False)
    for panel in model_panels(visible=False):
        cmds.modelEditor(panel, e=True, xray=False)


def isolate(mode='toggle'):
    """Isolate select in every visible viewport.

    mode: 'toggle' (isolate the selection, or leave isolation when nothing
    is selected), 'add' or 'remove' the selection from the isolated set."""
    sel = selected()
    for panel in model_panels():
        on = cmds.isolateSelect(panel, q=True, state=True)
        if mode == 'toggle':
            if on:
                cmds.isolateSelect(panel, state=False)
            if not on or sel:
                mel.eval('enableIsolateSelect %s 1' % panel)
                cmds.isolateSelect(panel, state=True)
        elif on and mode == 'add':
            cmds.isolateSelect(panel, addSelected=True)
        elif on and mode == 'remove':
            cmds.isolateSelect(panel, removeSelected=True)


def show_states():
    """{flag: state} of the active viewport for every flag in SHOW_FLAGS."""
    panel = active_model_panel()
    if not panel:
        return {}
    return dict((flag, bool(cmds.modelEditor(panel, q=True, **{flag: True})))
                for flag, _ in SHOW_FLAGS)


def set_show(flag, state):
    """Show / hide one object type in every visible viewport."""
    for panel in model_panels():
        cmds.modelEditor(panel, e=True, **{flag: bool(state)})


def set_show_all(state):
    for panel in model_panels():
        cmds.modelEditor(panel, e=True, allObjects=bool(state))


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------
def select_opposite(add=False, first_letter=False):
    """Select the other side of the selection by swapping L and R.

    first_letter  only names that start with L or R (default: the first L or
                  R anywhere in the name)
    add           keep the current selection
    """
    found = []
    for item in selected():
        namespace, _, name = item.rpartition(':')
        prefix = namespace + ':' if namespace else ''
        for a, b in (('L', 'R'), ('R', 'L')):
            if name.startswith(a) if first_letter else a in name:
                twin = prefix + name.replace(a, b, 1)
                if cmds.objExists(twin):
                    found.append(twin)
    if found:
        cmds.select(found, add=add, replace=not add)
    elif not add:
        cmds.select(cl=True)
    return found


def swap_selection(search, replace):
    """Select the nodes named like the selection with `search` replaced."""
    if not search:
        return warn('type the text to swap from.')
    found = []
    for item in selected():
        twin = item.replace(search, replace, 1)
        if cmds.objExists(twin):
            found.append(twin)
    cmds.select(found, r=True) if found else cmds.select(cl=True)
    return found


def store_selection():
    sel = selected(fl=True)
    path = tmp_file(SELECTION_FILE)
    with open(path, 'w') as handle:
        json.dump(sel, handle)
    print('mauTools: selection of %d item(s) stored in %s' % (len(sel), path))


def restore_selection():
    path = tmp_file(SELECTION_FILE)
    if not os.path.isfile(path):
        return warn('nothing stored yet.')
    with open(path) as handle:
        found = [n for n in json.load(handle) if cmds.objExists(n)]
    cmds.select(found, r=True) if found else cmds.select(cl=True)
    return found


def selection_as_text(python=True):
    """Print (and return) the selection as a Python list or a MEL array."""
    sel = selected(fl=True)
    if python:
        text = repr(sel)
    else:
        text = '{' + ', '.join('"%s"' % s for s in sel) + '};'
    print(text)
    return text


def namespaces():
    """Every namespace in the scene, except Maya's own."""
    found = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) or []
    return [n for n in found if n not in ('UI', 'shared')]


# ---------------------------------------------------------------------------
# scene
# ---------------------------------------------------------------------------
def scene_counts(types=INFO_TYPES):
    """[(node type, count)] for the node types present in the scene."""
    known = set(cmds.allNodeTypes())
    out = []
    for node_type in types:
        if node_type in known:
            count = len(cmds.ls(type=node_type))
            if count:
                out.append((node_type, count))
    return out


def next_version_name(path):
    """scene_v07.ma -> scene_v08.ma ; scene.ma -> scenev01.ma"""
    base, ext = os.path.splitext(path)
    found = re.search(r'(\d+)$', base)
    if not found:
        return base + 'v01' + ext
    digits = found.group(1)
    return base[:-len(digits)] + str(int(digits) + 1).zfill(len(digits)) + ext


def save_new_version():
    """Save the scene under the next version number, after confirmation."""
    scene = cmds.file(q=True, sceneName=True)
    if not scene:
        return warn('save the scene once before versioning it.')
    new = next_version_name(scene)
    question = 'Save the scene as\n%s ?' % new
    if os.path.exists(new):
        question = '%s already exists.\nOverwrite it?' % new
    if cmds.confirmDialog(title='New Version', message=question,
                          button=['Save', 'Cancel'], defaultButton='Save',
                          cancelButton='Cancel',
                          dismissString='Cancel') != 'Save':
        return None
    cmds.file(rename=new)
    cmds.file(save=True,
              type='mayaBinary' if new.endswith('.mb') else 'mayaAscii')
    return new


def step_main_shelf(where):
    """Change tab on Maya's main shelf: 'first', 'previous', 'next', 'last'."""
    shelf = mel.eval('$mauToolsTmp = $gShelfTopLevel')
    count = cmds.shelfTabLayout(shelf, q=True, numberOfChildren=True)
    index = cmds.shelfTabLayout(shelf, q=True, selectTabIndex=True)
    index = {'first': 1, 'last': count, 'previous': max(index - 1, 1),
             'next': min(index + 1, count)}[where]
    cmds.shelfTabLayout(shelf, e=True, selectTabIndex=index)
