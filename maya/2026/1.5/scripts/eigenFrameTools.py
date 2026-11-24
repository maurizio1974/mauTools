"""
eigenFrameTools.py - create and set up eigenFrame locators (eigenFrame v2, Maya 2026; maya.cmds).

    import eigenFrameTools as eft
    eft.show_window()
    loc = eft.create("headPCA", frame_mode="Tracked PCA", pivot_mode="Bounding Box Center")
    loc = eft.create("headPCA", opm=True)         # drive offsetParentMatrix (clean translate/rotate)
    eft.set_up_object("headCtrl")                 # select eigen locator(s) first, or pass nodes=
    eft.capture_rest()                            # selected locators: rest shape = current pose
    eft.load_plugin("python")                     # use the Python version instead of the C++ plug-in

MEL: eigenFrameWindow;   eigenLocator -n "myPCA";   eigenLocator -n "myPCA" -opm;
     eigenFrameSetUpObject "headCtrl";   eigenFrameCaptureRest;
"""
from maya import cmds

CPP_PLUGIN = "eigenFrame"
PY_PLUGIN = "eigenFramePy"
NODE_TYPE = "eigenFrame"
_WIN = "eigenFrameToolsWin"

FRAME_MODES = ("Tracked PCA", "Best-Fit Rigid", "Raw PCA")
VECTOR_SPACES = ("Object", "World")
UP_TYPES = ("None", "Vector", "Object", "ObjectRotation")
UP_AXIS_MODES = ("Closest Eigen Axis", "Middle Eigen Axis")
PIVOT_MODES = ("Centroid", "Bounding Box Center")


def loaded_plugin():
    """The plug-in that provides the eigenFrame node, or None."""
    for name in (CPP_PLUGIN, PY_PLUGIN):
        if cmds.pluginInfo(name, query=True, loaded=True):
            return name
    return None


def load_plugin(prefer="cpp"):
    """Load the C++ plug-in (prefer="cpp", falls back to Python) or the Python one (prefer="python").
    Does nothing if either is already loaded: only one can provide the node in a session."""
    current = loaded_plugin()
    if current:
        return current
    order = [CPP_PLUGIN, PY_PLUGIN] if prefer != "python" else [PY_PLUGIN, CPP_PLUGIN]
    errors = []
    for name in order:
        try:
            cmds.loadPlugin(name + (".py" if name == PY_PLUGIN else ""), quiet=True)
            return name
        except RuntimeError as exc:
            errors.append("%s: %s" % (name, exc))
    raise RuntimeError("Could not load eigenFrame (%s)" % "; ".join(errors))


def _index(value, names, what):
    if value is None:
        return None
    if isinstance(value, int):
        if not 0 <= value < len(names):
            raise ValueError("eigenFrame: %s must be 0-%d" % (what, len(names) - 1))
        return value
    for i, n in enumerate(names):
        if n.replace(" ", "").lower() == str(value).replace(" ", "").lower():
            return i
    raise ValueError("eigenFrame: unknown %s %r (use one of %s)" % (what, value, ", ".join(names)))


def frame_node(node):
    """The eigenFrame node for a locator made by eigenLocator (or the node itself)."""
    if cmds.nodeType(node) == NODE_TYPE:
        return node
    for candidate in [node] + (cmds.listRelatives(node, parent=True, fullPath=True) or []):
        for attr in ("translate", "offsetParentMatrix"):         # channels, or -opm locators
            if not cmds.objExists(candidate + "." + attr):
                continue
            found = cmds.listConnections(candidate + "." + attr, source=True, destination=False,
                                         type=NODE_TYPE) or []
            if found:
                return found[0]
    return None


def selected_frame_nodes(selection=None):
    """eigenFrame nodes of the selected locators / nodes."""
    nodes = []
    for item in cmds.ls(selection or cmds.ls(selection=True), long=True) or []:
        node = frame_node(item.split(".")[0])
        if node and node not in nodes:
            nodes.append(node)
    return nodes


def configure(nodes, frame_mode=None, vector_space=None, world_up_type=None, up_axis_mode=None,
              pivot_mode=None, up_vector=None, aim_vector=None, tolerance=None):
    """Set options on eigenFrame nodes. Modes take a name ("Bounding Box Center") or an index."""
    fm = _index(frame_mode, FRAME_MODES, "frame mode")
    vs = _index(vector_space, VECTOR_SPACES, "vector space")
    ut = _index(world_up_type, UP_TYPES, "world up type")
    um = _index(up_axis_mode, UP_AXIS_MODES, "up axis mode")
    pm = _index(pivot_mode, PIVOT_MODES, "pivot mode")
    for node in nodes:
        if fm is not None:
            cmds.setAttr(node + ".frameMode", fm)
        if vs is not None:
            cmds.setAttr(node + ".vectorSpace", vs)
        if ut is not None:
            cmds.setAttr(node + ".worldUpType", ut)
        if um is not None:
            cmds.setAttr(node + ".upAxisMode", um)
        if pm is not None:
            cmds.setAttr(node + ".pivotMode", pm)
        if up_vector is not None:
            cmds.setAttr(node + ".worldUpVector", *up_vector)
        if aim_vector is not None:
            cmds.setAttr(node + ".aimVector", *aim_vector)
        if tolerance is not None:
            cmds.setAttr(node + ".degenerateTolerance", max(0.0, float(tolerance)))
    return nodes


def create(name="eigenLocator", selection=None, opm=False, **options):
    """Make an eigenFrame locator from the selection (an object, or its vertices / edges / faces /
    CVs), as the eigenLocator command does, then apply any options (see configure).
    opm=True drives the locator's offsetParentMatrix instead of translate / rotate.
    Returns the locator. One undo step."""
    load_plugin()
    if selection is not None:
        cmds.select(selection, replace=True)
    if not cmds.ls(selection=True):
        raise RuntimeError("eigenFrame: select a mesh, NURBS surface or NURBS curve (or its components).")
    cmds.undoInfo(openChunk=True, chunkName="eigenFrameCreate")
    try:
        loc = cmds.eigenLocator(name=name, useOffsetParentMatrix=bool(opm))
        if isinstance(loc, (list, tuple)):
            loc = loc[0]
        node = frame_node(loc)
        if node and options:
            configure([node], **options)
        cmds.select(loc, replace=True)
    finally:
        cmds.undoInfo(closeChunk=True)
    return loc


def set_up_object(up_object, nodes=None, rotation=False):
    """Drive the up vector from an object: its position (Object) or its rotation applied to
    worldUpVector (ObjectRotation, rotation=True). nodes: eigenFrame nodes or their locators
    (default: the selection, without up_object)."""
    if nodes is None:
        nodes = [n for n in cmds.ls(selection=True, long=True) or []
                 if cmds.ls(n)[0] != cmds.ls(up_object)[0]]
    frames = selected_frame_nodes(nodes)
    if not frames:
        raise RuntimeError("eigenFrame: select eigenFrame locators (then the up object), or pass nodes=.")
    if not cmds.objExists(up_object + ".worldMatrix"):
        raise RuntimeError("eigenFrame: %s isn't a DAG object." % up_object)
    cmds.undoInfo(openChunk=True, chunkName="eigenFrameSetUpObject")
    try:
        for node in frames:
            cmds.connectAttr(up_object + ".worldMatrix[0]", node + ".worldUpMatrix", force=True)
            cmds.setAttr(node + ".worldUpType", 3 if rotation else 2)
    finally:
        cmds.undoInfo(closeChunk=True)
    return frames


def capture_rest(nodes=None):
    """Make the current pose the rest shape of the given (or selected) eigenFrame locators / nodes
    (eigenLocator -captureRest). Use it on geometry without deformer history, or to re-pose the
    rest. Returns the nodes. One undo step each, as the command."""
    frames = selected_frame_nodes(nodes)
    if not frames:
        raise RuntimeError("eigenFrame: select eigenFrame locators (or nodes) to capture.")
    load_plugin()
    for node in frames:
        cmds.eigenLocator(captureRest=node)
    return frames


# --------------------------------------------------------------------------- window
def show_window():
    if cmds.window(_WIN, exists=True):
        cmds.deleteUI(_WIN)
    cmds.window(_WIN, title="eigenFrame", widthHeight=(370, 470), sizeable=True)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=("both", 6))
    backend = cmds.radioButtonGrp(label="Plug-in", labelArray2=("C++", "Python"), numberOfRadioButtons=2,
                                  select=1, columnWidth3=(90, 80, 80))
    status = cmds.text(label="", align="left")
    name = cmds.textFieldGrp(label="Locator name", text="eigenLocator", columnWidth2=(90, 220))

    def menu(label, items, default):
        m = cmds.optionMenuGrp(label=label, columnWidth2=(90, 200))
        for it in items:
            cmds.menuItem(label=it)
        cmds.optionMenuGrp(m, edit=True, select=default + 1)
        return m

    frame_mode = menu("Frame mode", FRAME_MODES, 0)
    vector_space = menu("Up/aim space", VECTOR_SPACES, 0)
    up_type = menu("World up", UP_TYPES, 1)
    up_axis = menu("Up axis", UP_AXIS_MODES, 0)
    pivot = menu("Pivot", PIVOT_MODES, 0)
    up_vec = cmds.floatFieldGrp(label="Up vector", numberOfFields=3, value1=0, value2=1, value3=0,
                                columnWidth4=(90, 70, 70, 70))
    aim_vec = cmds.floatFieldGrp(label="Aim vector", numberOfFields=3, value1=1, value2=0, value3=0,
                                 columnWidth4=(90, 70, 70, 70))
    tol = cmds.floatSliderGrp(label="Degenerate tol.", field=True, minValue=0, maxValue=0.5,
                              fieldMaxValue=1, value=0.05, columnWidth3=(90, 60, 150))
    opm = cmds.checkBoxGrp(label="", label1="Drive offsetParentMatrix", value1=False, columnWidth2=(90, 220))

    def update_status(*_):
        current = loaded_plugin()
        cmds.text(status, edit=True, label="Loaded: %s" % (current or "none"))
        cmds.radioButtonGrp(backend, edit=True, enable=current is None)

    def options():
        return dict(
            frame_mode=cmds.optionMenuGrp(frame_mode, query=True, select=True) - 1,
            vector_space=cmds.optionMenuGrp(vector_space, query=True, select=True) - 1,
            world_up_type=cmds.optionMenuGrp(up_type, query=True, select=True) - 1,
            up_axis_mode=cmds.optionMenuGrp(up_axis, query=True, select=True) - 1,
            pivot_mode=cmds.optionMenuGrp(pivot, query=True, select=True) - 1,
            up_vector=cmds.floatFieldGrp(up_vec, query=True, value=True),
            aim_vector=cmds.floatFieldGrp(aim_vec, query=True, value=True),
            tolerance=cmds.floatSliderGrp(tol, query=True, value=True))

    def make(*_):
        load_plugin("python" if cmds.radioButtonGrp(backend, query=True, select=True) == 2 else "cpp")
        update_status()
        loc = create(cmds.textFieldGrp(name, query=True, text=True) or "eigenLocator",
                     opm=cmds.checkBoxGrp(opm, query=True, value1=True), **options())
        print("eigenFrame: created %s" % loc)

    def apply(*_):
        nodes = selected_frame_nodes()
        if not nodes:
            cmds.warning("eigenFrame: select eigenFrame locators to update.")
            return
        configure(nodes, **options())
        print("eigenFrame: updated %d node(s)" % len(nodes))

    def up_object(rotation):
        def run(*_):
            sel = cmds.ls(selection=True, long=True) or []
            if len(sel) < 2:
                cmds.warning("eigenFrame: select the eigenFrame locator(s), then the up object last.")
                return
            nodes = set_up_object(sel[-1], nodes=sel[:-1], rotation=rotation)
            cmds.optionMenuGrp(up_type, edit=True, select=(4 if rotation else 3))
            print("eigenFrame: %s drives the up vector of %d node(s)" % (sel[-1], len(nodes)))
        return run

    cmds.button(label="Create from Selection (object or components)", height=28, command=make)
    cmds.button(label="Apply Settings to Selected Locators", command=apply)

    def capture(*_):
        if not selected_frame_nodes():
            cmds.warning("eigenFrame: select eigenFrame locators to capture.")
            return
        print("eigenFrame: rest captured for %s" % ", ".join(capture_rest()))

    cmds.button(label="Capture Rest from Current Pose (selected)", command=capture)
    cmds.separator(height=8)
    cmds.text(label="Select eigen locator(s), then the up object last:", align="left")
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAttach2=("both", "both"))
    cmds.button(label="Up = Object Position", command=up_object(False))
    cmds.button(label="Up = Object Rotation", command=up_object(True))
    cmds.setParent("..")
    update_status()
    cmds.showWindow(_WIN)
    return _WIN
