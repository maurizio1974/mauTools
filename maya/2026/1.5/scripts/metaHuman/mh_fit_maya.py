#  -*- coding: utf-8 -*-
"""
MetaHuman face fit, interactive, inside Maya 2026.

    import mh_fit_maya
    mh_fit_maya.show()

Steps in the window:
  1. Mesh        select your character and press "Load". It is read in world space (Y up, cm).
  2. Landmarks   13 locators (LM_*) placed automatically, or from a topology profile. A reference
                 MetaHuman head with the same points stands beside your character. Move the locators by
                 hand where needed (hold V to snap to vertices), then "Snap to mesh".
  3. Fit         wraps the MetaHuman head onto your mesh: MHFIT_fittedHead appears on top of it.
                 Edit it by hand if you want (move vertices, soft selection, sculpt), then
                 "Snap to surface" puts the selected (or all) vertices back on your surface.
  4. Build       writes <name>_fitted.dna, <name>_usermesh.npz and <name>_topology.json, then builds
                 the rig in a new scene and saves <name>_rig.ma.

Needs numpy (ships with Maya) and scipy (once: mayapy -m pip install --user scipy; the window offers it).
"""
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import mh_paths  # noqa: E402

ROOT = mh_paths.root()
TOOLS = os.path.join(ROOT, "tools")
LIB = mh_paths.lib_dir()
for _p in (TOOLS, LIB):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402
from maya import cmds  # noqa: E402
import maya.api.OpenMaya as om  # noqa: E402

GRP = "MHFIT_grp"
LM_GRP = "MHFIT_landmarks_grp"
REF_GRP = "MHFIT_reference_grp"
FIT_MESH = "MHFIT_fittedHead"
REF_MESH = "MHFIT_referenceHead"
LM_PREFIX = "LM_"
REF_PREFIX = "REF_"
WIN = "MHFitWin"

LABELS = [("FACIAL_L_EyeCornerInner", "Left eye, inner corner"),
          ("FACIAL_L_EyeCornerOuter", "Left eye, outer corner"),
          ("FACIAL_L_EyelidUpperA", "Left eye, upper lid (middle)"),
          ("FACIAL_L_EyelidLowerA", "Left eye, lower lid (middle)"),
          ("FACIAL_R_EyeCornerInner", "Right eye, inner corner"),
          ("FACIAL_R_EyeCornerOuter", "Right eye, outer corner"),
          ("FACIAL_R_EyelidUpperA", "Right eye, upper lid (middle)"),
          ("FACIAL_R_EyelidLowerA", "Right eye, lower lid (middle)"),
          ("FACIAL_L_LipCorner", "Mouth, left corner"),
          ("FACIAL_R_LipCorner", "Mouth, right corner"),
          ("FACIAL_C_LipUpper", "Upper lip, where the lips meet"),
          ("FACIAL_C_LipLower", "Lower lip, where the lips meet"),
          ("FACIAL_C_NoseTip", "Nose tip")]
LABEL = dict(LABELS)
NAMES = [n for n, _ in LABELS]

_state = {"ctx": None, "ui": {}}


# =========================================================================== helpers
def _short(n):
    return n.replace("FACIAL_", "")


def _lm(n):
    return LM_PREFIX + _short(n)


def _ref(n):
    return REF_PREFIX + _short(n)


def _log(msg):
    print("MH fit: " + msg)
    try:
        cmds.progressWindow(e=True, status=msg.strip()[:80])
    except RuntimeError:
        pass


class _Progress(object):
    def __init__(self, title):
        self.title = title

    def __enter__(self):
        try:
            cmds.progressWindow(title=self.title, status="working...", isInterruptable=False, progress=0)
        except RuntimeError:
            pass
        return self

    def __exit__(self, *a):
        try:
            cmds.progressWindow(endProgress=True)
        except RuntimeError:
            pass


def _ensure_scipy():
    try:
        import scipy.sparse.linalg  # noqa: F401
        import scipy.ndimage  # noqa: F401
        import scipy.interpolate  # noqa: F401
        return True
    except ImportError:
        pass
    mayapy = find_mayapy()
    how = ("%s -m pip install --user scipy" % mayapy) if mayapy else "pip, inside this Maya session"
    ans = cmds.confirmDialog(title="MH fit", message="The fit needs scipy in Maya's Python.\n\nInstall it now with\n%s ?" % how,
                             button=["Install", "Cancel"], defaultButton="Install", cancelButton="Cancel")
    if ans != "Install":
        return False
    import site
    import importlib
    with _Progress("Installing scipy"):
        if mayapy:
            import subprocess
            r = subprocess.run([mayapy, "-m", "pip", "install", "--user", "scipy"], capture_output=True, text=True)
            print(r.stdout[-2000:], r.stderr[-2000:])
        else:  # no mayapy on disk: run pip in this Maya's own Python
            try:
                from pip._internal.cli.main import main as pip_main
            except ImportError:
                import ensurepip
                ensurepip.bootstrap(user=True)
                from pip._internal.cli.main import main as pip_main
            pip_main(["install", "--user", "scipy"])
    user_site = site.getusersitepackages()
    if user_site not in sys.path:
        sys.path.append(user_site)
    importlib.invalidate_caches()
    try:
        import scipy.sparse.linalg  # noqa: F401,F811
        return True
    except ImportError:
        cmds.confirmDialog(title="MH fit", message="scipy could not be installed (see the Script Editor).\n"
                           "Install it from a terminal with mayapy -m pip install --user scipy, then restart Maya.", button=["OK"])
        return False


def find_mayapy():
    """mayapy of this Maya, or None. Looks next to the running executable and in MAYA_LOCATION/bin."""
    dirs = [os.path.dirname(sys.executable)]
    if os.environ.get("MAYA_LOCATION"):
        dirs.append(os.path.join(os.environ["MAYA_LOCATION"], "bin"))
    for d in dirs:
        for n in ("mayapy", "mayapy.exe"):
            p = os.path.join(d, n)
            if os.path.isfile(p):
                return p
    return None


def _pipeline():
    import mh_fit_pipeline as P
    return P


def _mesh_shape(name):
    if cmds.objectType(name) == "mesh":
        return name
    shapes = cmds.listRelatives(name, shapes=True, noIntermediate=True, type="mesh", fullPath=True) or []
    if not shapes:
        raise RuntimeError("'%s' is not a polygon mesh" % name)
    return shapes[0]


def pick_face_mesh(name):
    """A mesh, or a group: then the mesh inside it that holds the face (the one with the highest point
    among the big ones). Returns the transform's name."""
    if cmds.objectType(name) == "mesh":
        name = cmds.listRelatives(name, parent=True, fullPath=True)[0]
    if cmds.listRelatives(name, shapes=True, noIntermediate=True, type="mesh"):
        return name
    shapes = cmds.listRelatives(name, allDescendents=True, noIntermediate=True, type="mesh", fullPath=True) or []
    if not shapes:
        raise RuntimeError("'%s' has no polygon meshes inside" % name)
    cand = []
    for sh in shapes:
        tr = cmds.listRelatives(sh, parent=True, fullPath=True)[0]
        n = cmds.polyEvaluate(sh, vertex=True)
        top = cmds.exactWorldBoundingBox(tr)[4]
        cand.append((n, top, tr))
    big = max(c[0] for c in cand)
    cand = [c for c in cand if c[0] >= 0.25 * big]      # skip eyes, teeth, lashes, props
    best = max(cand, key=lambda c: c[1])
    others = [c[2].split("|")[-1] for c in cand if c is not best]
    print("MH fit: using '%s' (%d vertices) from group '%s'%s" % (best[2].split("|")[-1], best[0], name.split("|")[-1],
          ("; other big meshes: " + ", ".join(others)) if others else ""))
    return best[2]


def _fn_mesh(name):
    sel = om.MSelectionList()
    sel.add(_mesh_shape(name))
    return om.MFnMesh(sel.getDagPath(0))


def _points(name):
    pts = _fn_mesh(name).getPoints(om.MSpace.kWorld)
    return np.array([(p.x, p.y, p.z) for p in pts], np.float64)


def _set_points(name, P):
    _fn_mesh(name).setPoints(om.MPointArray([om.MPoint(*map(float, p)) for p in P]), om.MSpace.kWorld)


def read_maya_mesh(name):
    """Your mesh, as the fitting code wants it (world space, cm)."""
    fn = _fn_mesh(name)
    counts, connects = fn.getVertices()
    counts, connects = np.array(counts, np.int64), np.array(connects, np.int64)
    m = {"pos": _points(name), "counts": counts, "connects": connects, "uv": np.zeros((0, 2)), "uv_ids": np.zeros(0, np.int64)}
    try:
        uvc, uvids = fn.getAssignedUVs()
        if len(uvids) == len(connects) and np.array_equal(np.array(uvc), counts):
            us, vs = fn.getUVs()
            m["uv"] = np.stack([np.array(us), np.array(vs)], 1)
            m["uv_ids"] = np.array(uvids, np.int64)
    except RuntimeError:
        pass
    return m


def _make_mesh(name, pos, counts, connects, parent):
    if cmds.objExists(name):
        cmds.delete(name)
    fn = om.MFnMesh()
    obj = fn.create(om.MPointArray([om.MPoint(*map(float, p)) for p in pos]), [int(c) for c in counts],
                    [int(c) for c in connects])
    tr = cmds.rename(om.MFnDagNode(obj).fullPathName(), name)
    tr = cmds.parent(tr, parent)[0]
    cmds.sets(tr, edit=True, forceElement="initialShadingGroup")
    return tr


def _shader(mesh, name, rgb, transparency):
    sg = name + "SG"
    if not cmds.objExists(name):
        cmds.shadingNode("lambert", asShader=True, name=name)
        cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
        cmds.connectAttr(name + ".outColor", sg + ".surfaceShader", force=True)
    cmds.setAttr(name + ".color", *rgb, type="double3")
    cmds.setAttr(name + ".transparency", transparency, transparency, transparency, type="double3")
    cmds.sets(mesh, edit=True, forceElement=sg)


def _color(node, index):
    for s in cmds.listRelatives(node, shapes=True, fullPath=True) or [node]:
        cmds.setAttr(s + ".overrideEnabled", 1)
        cmds.setAttr(s + ".overrideColor", index)


def _group(name, parent=None):
    if not cmds.objExists(name):
        if parent:
            cmds.group(empty=True, name=name, parent=parent)
        else:
            cmds.group(empty=True, name=name, world=True)
    return name


def _head_size(ctx):
    return float(np.ptp(ctx["head"]["pos"][:, 1]) / ctx["s"])


def _ctx():
    if _state["ctx"] is None:
        raise RuntimeError("Load your mesh first (step 1).")
    return _state["ctx"]


# =========================================================================== steps
def load_mesh(name=None):
    """Step 1: read the mesh and align the MetaHuman template roughly."""
    if not _ensure_scipy():
        return None
    name = name or (cmds.ls(selection=True, long=False) or [None])[0]
    if not name:
        raise RuntimeError("Select your character's mesh.")
    name = pick_face_mesh(name.split(".")[0])
    if cmds.upAxis(q=True, axis=True) != "y":
        cmds.warning("MH fit: the scene is Z-up; the fit expects Y-up with the face looking along +Z.")
    P = _pipeline()
    with _Progress("MH fit: loading"):
        user = read_maya_mesh(name)
        _log("reading the base DNA and aligning...")
        ctx = P.prepare(user, log=_log)
    ctx["mesh_name"] = name
    _state["ctx"] = ctx
    _group(GRP)
    if not cmds.attributeQuery("mhfitMesh", node=GRP, exists=True):
        cmds.addAttr(GRP, longName="mhfitMesh", dataType="string")
    cmds.setAttr(GRP + ".mhfitMesh", name, type="string")
    show_reference()
    _log("loaded %s: %d vertices, scale MetaHuman/yours %.4f" % (name, len(user["pos"]), ctx["s"]))
    _refresh_ui()
    return ctx


def show_reference(offset=True):
    """The MetaHuman template head (roughly scaled to yours) beside your character, with grey
    markers where each landmark goes."""
    ctx = _ctx()
    P = _pipeline()
    if cmds.objExists(REF_GRP):
        cmds.delete(REF_GRP)
    _group(REF_GRP, GRP)
    head = ctx["head"]
    shift = np.array([1.35 * float(np.ptp(head["pos"][:, 0])) / ctx["s"] if offset else 0.0, 0.0, 0.0])
    ref = _make_mesh(REF_MESH, P.to_user(ctx, head["pos"]) + shift, head["counts"], head["connects"], REF_GRP)
    _shader(ref, "MHFIT_reference_mat", (0.55, 0.62, 0.72), 0.0)
    cmds.setAttr(ref + ".overrideEnabled", 1)
    cmds.setAttr(ref + ".overrideDisplayType", 2)          # reference: visible, not selectable
    size = _head_size(ctx) * 0.012
    for n in NAMES:
        if n in ctx["f_mh"]:
            p = P.to_user(ctx, ctx["f_mh"][n]) + shift
            loc = cmds.spaceLocator(name=_ref(n))[0]
            cmds.setAttr(loc + ".localScale", size, size, size)
            cmds.xform(loc, worldSpace=True, translation=list(map(float, p)))
            _color(loc, 3)
            cmds.parent(loc, REF_GRP)
    return ref


def set_landmarks(points):
    """Create or move the LM_* locators. points: {name: xyz}."""
    ctx = _ctx()
    _group(LM_GRP, GRP)
    size = _head_size(ctx) * 0.015
    for n in NAMES:
        if n not in points:
            continue
        loc = _lm(n)
        if not cmds.objExists(loc):
            loc = cmds.spaceLocator(name=loc)[0]
            cmds.setAttr(loc + ".localScale", size, size, size)
            _color(loc, 13 if "_L_" in n else (6 if "_R_" in n else 17))
            loc = cmds.parent(loc, LM_GRP)[0]
        cmds.xform(_lm(n), worldSpace=True, translation=list(map(float, points[n])))


def read_landmarks():
    return {n: np.array(cmds.xform(_lm(n), q=True, worldSpace=True, translation=True)) for n in NAMES if cmds.objExists(_lm(n))}


def auto_landmarks():
    """Step 2: find the 13 landmarks on your mesh."""
    ctx = _ctx()
    with _Progress("MH fit: landmarks"):
        pts, guessed = _pipeline().detect_landmarks(ctx, log=_log)
    set_landmarks(pts)
    if guessed:
        cmds.warning("MH fit: not found automatically, placed from the rough alignment only: %s. Check them."
                     % ", ".join(LABEL[g] for g in guessed))
    cmds.select([_lm(n) for n in NAMES if cmds.objExists(_lm(n))], replace=True)
    _refresh_ui()
    return pts


def load_profile(path=None):
    path = path or _pick_file("Topology profile (*.json)", mode=1)
    if not path:
        return None
    pts = _pipeline().landmarks_from_profile(_ctx(), path)
    set_landmarks(pts)
    _refresh_ui()
    return pts


def save_profile(path=None):
    path = path or _pick_file("Topology profile (*.json)", mode=0)
    if not path:
        return None
    _pipeline().save_profile(_ctx(), read_landmarks(), path)
    _log("profile saved: %s" % path)
    return path


def snap_landmarks():
    """Put every locator on the closest point of your mesh."""
    fn = _fn_mesh(_ctx()["mesh_name"])
    for n in NAMES:
        if cmds.objExists(_lm(n)):
            p = om.MPoint(*cmds.xform(_lm(n), q=True, worldSpace=True, translation=True))
            q, _ = fn.getClosestPoint(p, om.MSpace.kWorld)
            cmds.xform(_lm(n), worldSpace=True, translation=(q.x, q.y, q.z))


def mirror_landmarks(left_to_right=True):
    """Mirror the left locators onto the right ones (or back) across your mesh's middle (x of the nose tip)."""
    lm = read_landmarks()
    cx = lm["FACIAL_C_NoseTip"][0] if "FACIAL_C_NoseTip" in lm else 0.0
    a, b = ("_L_", "_R_") if left_to_right else ("_R_", "_L_")
    out = {}
    for n, p in lm.items():
        if a in n and n.replace(a, b) in NAMES:
            out[n.replace(a, b)] = np.array([2 * cx - p[0], p[1], p[2]])
    set_landmarks(out)
    snap_landmarks()


def select_landmark(n):
    if cmds.objExists(_lm(n)):
        cmds.select(_lm(n), replace=True)
    for m in NAMES:
        if cmds.objExists(_ref(m)):
            _color(_ref(m), 17 if m == n else 3)


def run_fit():
    """Step 3: wrap the MetaHuman head onto your mesh."""
    ctx = _ctx()
    lm = read_landmarks()
    missing = [LABEL[n] for n in NAMES if n not in lm]
    if len(lm) < 6:
        raise RuntimeError("Place the landmarks first (step 2).")
    if missing:
        cmds.warning("MH fit: fitting without %s" % ", ".join(missing))
    P = _pipeline()
    with _Progress("MH fit: fitting (about 30 s)"):
        X = P.fit(ctx, lm, log=_log)
    head = ctx["head"]
    mesh = _make_mesh(FIT_MESH, P.to_user(ctx, X), head["counts"], head["connects"], GRP)
    _shader(mesh, "MHFIT_fitted_mat", (0.9, 0.55, 0.25), 0.35)
    ctx["X"] = X
    mean, p95 = ctx["fit_error"]
    _log("fitted: %.2f mm mean from your surface, 95%% within %.2f mm (MetaHuman scale)" % (mean * 10, p95 * 10))
    _refresh_ui()
    return mesh


def snap_fit_to_surface(selected_only=True):
    """Put vertices of the fitted head back on your surface (the selected ones, or all the outer
    ones), e.g. after moving them by hand."""
    ctx = _ctx()
    import transfer as TR
    if not cmds.objExists(FIT_MESH):
        raise RuntimeError("Run the fit first (step 3).")
    Pu = _points(FIT_MESH)
    ids = []
    if selected_only:
        sel = cmds.ls(selection=True, flatten=True) or []
        sel = cmds.filterExpand(sel, selectionMask=31) or []          # vertices
        ids = [int(s.rsplit("[", 1)[1][:-1]) for s in sel if s.split(".")[0].split("|")[-1] == FIT_MESH]
    if not ids:
        ids = list(np.where(ctx["ext"])[0])
    ids = np.array(ids)
    V, T = ctx["V"], ctx["ut"]
    tri, bary = TR.closest_on_triangles(Pu[ids], V, T)
    Pu[ids] = np.einsum("ij,ijk->ik", bary, V[T[tri]])
    _set_points(FIT_MESH, Pu)
    _log("%d vertices snapped to your surface" % len(ids))


def fitted_head_metahuman_space():
    ctx = _ctx()
    if not cmds.objExists(FIT_MESH):
        raise RuntimeError("Run the fit first (step 3).")
    Pu = _points(FIT_MESH)
    if len(Pu) != len(ctx["head"]["pos"]):
        raise RuntimeError("%s has %d vertices, not %d: don't add or delete vertices on it." % (FIT_MESH, len(Pu), len(ctx["head"]["pos"])))
    return _pipeline().to_metahuman(ctx, Pu)


def build(out_dir, name, make_scene=True):
    """Step 4: DNA + your mesh's weights, then the rig in a new scene, saved as <name>_rig.ma."""
    ctx = _ctx()
    P = _pipeline()
    name = P.clean_name(name)
    X = fitted_head_metahuman_space()
    os.makedirs(out_dir, exist_ok=True)
    with _Progress("MH fit: writing the DNA"):
        P.save_profile(ctx, read_landmarks(), os.path.join(out_dir, name + "_topology.json"))
        dna_path, npz = P.finish(ctx, X, out_dir, name, previews=False, log=_log)
    _log("wrote %s and %s" % (dna_path, npz))
    if not make_scene:
        return dna_path, npz, None
    if cmds.file(q=True, modified=True):
        ans = cmds.confirmDialog(title="MH fit", message="The rig is built in a new scene.\nSave this fitting scene first?",
                                 button=["Save", "Don't save", "Cancel"], defaultButton="Save", cancelButton="Cancel")
        if ans == "Cancel":
            return dna_path, npz, None
        if ans == "Save":
            if not cmds.file(q=True, sceneName=True):
                p = _pick_file("Maya ASCII (*.ma)", mode=0, start=os.path.join(out_dir, name + "_fitting.ma"))
                if not p:
                    return dna_path, npz, None
                cmds.file(rename=p)
            cmds.file(save=True, type="mayaAscii")
    import mh_face_build as B
    with _Progress("MH fit: building the rig"):
        B.build(dna_path, user_mesh=npz, log=_log)
    ma = os.path.join(out_dir, name + "_rig.ma")
    cmds.file(rename=ma)
    cmds.file(save=True, type="mayaAscii", force=True)
    _state["ctx"] = None
    _log("rig saved: %s" % ma)
    return dna_path, npz, ma


def resume():
    """After reopening a fitting scene: reload the mesh named on MHFIT_grp, keeping the locators and the fitted head."""
    if not cmds.objExists(GRP) or not cmds.attributeQuery("mhfitMesh", node=GRP, exists=True):
        return None
    name = cmds.getAttr(GRP + ".mhfitMesh")
    if not cmds.objExists(name):
        return None
    lm = read_landmarks()
    fitted = _points(FIT_MESH) if cmds.objExists(FIT_MESH) else None
    ctx = load_mesh(name)
    if ctx is None:
        return None
    if lm:
        set_landmarks(lm)
    if fitted is not None:
        _set_points(FIT_MESH, fitted)
        ctx["X"] = _pipeline().to_metahuman(ctx, fitted)
    _refresh_ui()
    return ctx


# =========================================================================== window
def _pick_file(filt, mode=1, start=None):
    kw = {"fileFilter": filt, "fileMode": mode}
    if start:
        kw["startingDirectory"] = start
    res = cmds.fileDialog2(**kw)
    return res[0] if res else None


def _safe(fn):
    def wrapped(*_):
        try:
            fn()
        except Exception as e:  # show it in Maya, keep the window alive
            import traceback
            traceback.print_exc()
            cmds.warning("MH fit: %s" % e)
    return wrapped


def _refresh_ui():
    ui = _state["ui"]
    if not ui or not cmds.window(WIN, exists=True):
        return
    ctx = _state["ctx"]
    if ctx:
        cmds.textFieldGrp(ui["mesh"], e=True, text=ctx["mesh_name"])
        if not cmds.textFieldGrp(ui["name"], q=True, text=True):
            cmds.textFieldGrp(ui["name"], e=True, text=_pipeline().clean_name(ctx["mesh_name"].split("|")[-1].split(":")[-1]))
    items = []
    for n, label in LABELS:
        items.append(("[x] " if cmds.objExists(_lm(n)) else "[ ] ") + label)
    cmds.textScrollList(ui["list"], e=True, removeAll=True, append=items)
    status = "no mesh loaded"
    if ctx:
        status = "mesh: %s  |  landmarks: %d / 13" % (ctx["mesh_name"], len(read_landmarks()))
        if "fit_error" in ctx:
            status += "  |  fit: %.2f mm mean" % (ctx["fit_error"][0] * 10)
    cmds.text(ui["status"], e=True, label=status)


def _list_selected(*_):
    idx = cmds.textScrollList(_state["ui"]["list"], q=True, selectIndexedItem=True) or []
    if idx:
        select_landmark(NAMES[idx[0] - 1])


FONT_VAR = "MHFitFontSize"
BASE_FONT = 10
BASE_WIDTH = 450


def _btn(label, command, height=24):
    b = cmds.button(label=label, height=height, command=command)
    _state["sized"].append(("button", b, height))
    return b


def _grp_text(cmd, name, widths):
    _state["sized"].append((cmd, name, widths))
    return name


def _qt_window():
    try:
        import maya.OpenMayaUI as omui
        try:
            from PySide6 import QtWidgets
            from shiboken6 import wrapInstance
        except ImportError:
            from PySide2 import QtWidgets
            from shiboken2 import wrapInstance
        ptr = omui.MQtUtil.findWindow(WIN)
        return (wrapInstance(int(ptr), QtWidgets.QWidget), QtWidgets) if ptr else (None, None)
    except Exception:
        return None, None


def set_font_size(size):
    """Text size of the whole window (points); buttons, fields and the window grow with it."""
    size = int(max(8, min(32, size)))
    cmds.optionVar(intValue=(FONT_VAR, size))
    k = size / float(BASE_FONT)
    win, QtWidgets = _qt_window()
    if win is not None:
        win.setStyleSheet("QWidget { font-size: %dpt; }" % size)
        for w in [win] + win.findChildren(QtWidgets.QWidget):
            f = w.font()
            f.setPointSize(size)
            w.setFont(f)
    for kind, name, base in _state.get("sized", []):
        try:
            if kind == "button":
                cmds.button(name, e=True, height=int(round(base * max(1.0, k))))
            elif kind == "textFieldGrp":
                cmds.textFieldGrp(name, e=True, columnWidth2=tuple(int(round(b * k)) for b in base))
            elif kind == "textFieldButtonGrp":
                cmds.textFieldButtonGrp(name, e=True, columnWidth3=tuple(int(round(b * k)) for b in base))
            elif kind == "intSliderGrp":
                cmds.intSliderGrp(name, e=True, columnWidth3=tuple(int(round(b * k)) for b in base))
        except RuntimeError:
            pass
    try:
        cmds.window(WIN, e=True, width=int(round(BASE_WIDTH * max(1.0, k))))
    except RuntimeError:
        pass


def show():
    if cmds.window(WIN, exists=True):
        cmds.deleteUI(WIN)
    ui = _state["ui"] = {}
    _state["sized"] = []
    cmds.window(WIN, title="MetaHuman face fit", widthHeight=(BASE_WIDTH, 680))
    cmds.scrollLayout(childResizable=True)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4, columnOffset=("both", 6))

    cmds.frameLayout(label="1. Your mesh", collapsable=True, marginWidth=4, marginHeight=4)
    ui["mesh"] = _grp_text("textFieldGrp", cmds.textFieldGrp(label="Mesh", columnWidth2=(50, 290), editable=False), (50, 290))
    _btn("Load selected mesh (or its group)", _safe(lambda: load_mesh()), 28)
    _btn("Resume fitting scene", _safe(lambda: resume()))
    cmds.setParent("..")

    cmds.frameLayout(label="2. Landmarks (move LM_* locators by hand)", collapsable=True, marginWidth=4, marginHeight=4)
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=1)
    _btn("Find automatically", _safe(auto_landmarks), 28)
    _btn("From profile...", _safe(lambda: load_profile()), 28)
    cmds.setParent("..")
    ui["list"] = cmds.textScrollList(numberOfRows=13, allowMultiSelection=False, selectCommand=_safe(_list_selected))
    cmds.text(label="Click a name: its locator is selected and its reference marker turns yellow.\n"
                    "Hold V while moving to snap to vertices.", align="left")
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=1)
    _btn("Snap to mesh", _safe(snap_landmarks))
    _btn("Mirror L > R", _safe(lambda: mirror_landmarks(True)))
    _btn("Mirror R > L", _safe(lambda: mirror_landmarks(False)))
    cmds.setParent("..")
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=1)
    _btn("Save profile...", _safe(lambda: save_profile()))
    _btn("Toggle reference", _safe(lambda: cmds.setAttr(REF_GRP + ".visibility", not cmds.getAttr(REF_GRP + ".visibility"))))
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.frameLayout(label="3. Fit (edit MHFIT_fittedHead by hand after)", collapsable=True, marginWidth=4, marginHeight=4)
    _btn("Fit MetaHuman head", _safe(run_fit), 32)
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=1)
    _btn("Snap selected verts to surface", _safe(lambda: snap_fit_to_surface(True)))
    _btn("Snap all", _safe(lambda: snap_fit_to_surface(False)))
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.frameLayout(label="4. Build the rig", collapsable=True, marginWidth=4, marginHeight=4)
    ui["name"] = _grp_text("textFieldGrp", cmds.textFieldGrp(label="Name", columnWidth2=(50, 290)), (50, 290))
    ui["out"] = _grp_text("textFieldButtonGrp", cmds.textFieldButtonGrp(
        label="Folder", columnWidth3=(50, 250, 40), buttonLabel="...", text=os.path.join(os.path.expanduser("~"), "mh_rigs")),
        (50, 250, 40))
    cmds.textFieldButtonGrp(ui["out"], e=True, buttonCommand=lambda *_: _pick_out())
    ui["scene"] = cmds.checkBox(label="Build the rig in a new scene and save it", value=True)
    _btn("Build", _safe(_build_from_ui), 34)
    cmds.setParent("..")

    ui["status"] = cmds.text(label="", align="left")
    cmds.separator(height=10, style="in")
    size = cmds.optionVar(q=FONT_VAR) if cmds.optionVar(exists=FONT_VAR) else BASE_FONT
    ui["font"] = _grp_text("intSliderGrp", cmds.intSliderGrp(
        label="Text size", field=True, minValue=8, maxValue=24, fieldMinValue=8, fieldMaxValue=32, value=size,
        columnWidth3=(60, 40, 240), dragCommand=lambda v: set_font_size(v), changeCommand=lambda v: set_font_size(v)),
        (60, 40, 240))
    cmds.showWindow(WIN)
    set_font_size(size)
    if _state["ctx"] is None and cmds.objExists(GRP):
        cmds.text(ui["status"], e=True, label="a fitting scene is open: press 'Resume fitting scene'")
    else:
        _refresh_ui()


def _pick_out():
    res = cmds.fileDialog2(fileMode=3, caption="Output folder")
    if res:
        cmds.textFieldButtonGrp(_state["ui"]["out"], e=True, text=res[0])


def _build_from_ui():
    ui = _state["ui"]
    name = cmds.textFieldGrp(ui["name"], q=True, text=True) or "character"
    out = os.path.join(cmds.textFieldButtonGrp(ui["out"], q=True, text=True), name)
    build(out, name, cmds.checkBox(ui["scene"], q=True, value=True))
