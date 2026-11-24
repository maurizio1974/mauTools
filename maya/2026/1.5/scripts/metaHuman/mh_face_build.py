#  -*- coding: utf-8 -*-
"""
Build a MetaHuman face rig in Maya from a DNA, with no Epic plug-in.

Uses only:
  * `dna` Python module compiled from Epic's OpenRigLogic (lib/linux/py311), to read the DNA
  * gui.ma, analog_gui.ma, additional_assemble_script.py from Epic's MetaHuman-DNA-Calibration
  * native_riglogic.py: the face's Rig Logic as ordinary Maya nodes (instead of embeddedRL4)
  * numpy (ships with Maya)

Same scene layout and names as Epic's dna_viewer (head_grp, geometry_grp, headRig_grp, <mesh>_blendShapes,
<mesh>_skinCluster, CTRL_expressions, FRM_WMmultipliers, ...), so Epic's assemble script runs unchanged.

    import mh_face_build
    mh_face_build.build("/path/character_fitted.dna", user_mesh="/path/character_usermesh.npz")
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import mh_paths  # noqa: E402

ROOT = mh_paths.root()
DATA = mh_paths.data_dir()
LIB = mh_paths.lib_dir()
if LIB not in sys.path:
    sys.path.insert(0, LIB)

import mh_dna_geo as G  # noqa: E402

TOP, GEO, RIG, LOD0_GRP, LOD0_LAYER = "head_grp", "geometry_grp", "headRig_grp", "head_lod0_grp", "head_lod0_layer"
GUI_TRANSLATE_X = 10.0
NECK_RAW = ("headTurnUp", "headTurnDown", "headTurnLeft", "headTurnRight", "headTiltLeft", "headTiltRight")


def _cmds():
    from maya import cmds
    return cmds


def _om():
    import maya.api.OpenMaya as om
    return om


def _mobject(name):
    om = _om()
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDependNode(0)


def _dagpath(name):
    om = _om()
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDagPath(0)


# --------------------------------------------------------------------------- scene parts
def create_groups():
    cmds = _cmds()
    cmds.group(world=True, empty=True, name=TOP)
    cmds.group(parent=TOP, empty=True, name=GEO)
    cmds.group(parent=TOP, empty=True, name=RIG)
    cmds.group(parent=GEO, empty=True, name=LOD0_GRP)
    cmds.select(LOD0_GRP, replace=True)
    cmds.createDisplayLayer(name=LOD0_LAYER, noRecurse=True)
    cmds.select(clear=True)


def create_joints(joints):
    """Same result as dna_viewer: translate = neutral translation, jointOrient = neutral rotation."""
    cmds = _cmds()
    names, parents = joints["names"], joints["parents"]
    for i, n in enumerate(names):
        p = parents[i]
        parent = TOP if p == i else names[p]
        j = cmds.createNode("joint", name=n, parent=parent, skipSelect=True)
        cmds.setAttr(j + ".translate", *[float(v) for v in joints["t"][i]])
        cmds.setAttr(j + ".jointOrient", *[float(v) for v in joints["r"][i]])
        cmds.setAttr(j + ".segmentScaleCompensate", 0)
    return names


def create_mesh(mesh, parent=LOD0_GRP, name=None):
    """MFnMesh from DNA-style data: pos (V,3), counts, connects, uv (U,2), uv_ids (per face-vertex)."""
    om = _om()
    cmds = _cmds()
    name = name or mesh["name"]
    pts = om.MPointArray([om.MPoint(*map(float, p)) for p in mesh["pos"]])
    fn = om.MFnMesh()
    obj = fn.create(pts, [int(c) for c in mesh["counts"]], [int(c) for c in mesh["connects"]])
    if mesh.get("uv") is not None and len(mesh["uv"]):
        fn.setUVs([float(u) for u in mesh["uv"][:, 0]], [float(v) for v in mesh["uv"][:, 1]])
        fn.assignUVs([int(c) for c in mesh["counts"]], [int(i) for i in mesh["uv_ids"]])
    tr = om.MFnDagNode(obj).fullPathName()
    tr = cmds.rename(tr, name)
    shape = cmds.listRelatives(tr, shapes=True, fullPath=False)[0]
    cmds.rename(shape, name + "Shape")
    cmds.parent(tr, parent)
    cmds.sets(tr, edit=True, forceElement="initialShadingGroup")
    if cmds.objExists(LOD0_LAYER):
        cmds.editDisplayLayerMembers(LOD0_LAYER, tr, noRecurse=True)
    return tr


def add_blendshapes(mesh_name, targets, channel_names, alias_prefix=None):
    """targets: [{"channel": c, "idx": (k,), "delta": (k,3)}]. Creates <mesh>_blendShapes with one
    sparse target per entry, weights aliased <mesh>__<channel> like dna_viewer."""
    om = _om()
    cmds = _cmds()
    if not targets:
        return None
    alias_prefix = alias_prefix or mesh_name
    bs = cmds.blendShape(mesh_name, name=mesh_name + "_blendShapes", origin="local")[0]
    for t, tg in enumerate(targets):
        alias = "%s__%s" % (alias_prefix, channel_names[tg["channel"]])
        cmds.setAttr("%s.weight[%d]" % (bs, t), 0.0)
        cmds.aliasAttr(alias, "%s.weight[%d]" % (bs, t))
        if not len(tg["idx"]):
            continue
        item = "%s.inputTarget[0].inputTargetGroup[%d].inputTargetItem[6000]" % (bs, t)
        sel = om.MSelectionList()
        sel.add(item + ".inputPointsTarget")
        sel.add(item + ".inputComponentsTarget")
        pts = om.MPointArray([om.MPoint(float(d[0]), float(d[1]), float(d[2]), 1.0) for d in tg["delta"]])
        sel.getPlug(0).setMObject(om.MFnPointArrayData().create(pts))
        cf = om.MFnSingleIndexedComponent()
        comp = cf.create(om.MFn.kMeshVertComponent)
        cf.addElements([int(i) for i in tg["idx"]])
        lf = om.MFnComponentListData()
        lobj = lf.create()
        lf.add(comp)
        sel.getPlug(1).setMObject(lobj)
    return bs


def add_skin(mesh_name, joint_names, skin_joints, skin_weights, max_influence):
    """skinCluster with exactly the DNA weights (set through the API in one call)."""
    import maya.api.OpenMayaAnim as oma
    om = _om()
    cmds = _cmds()
    used = sorted({int(j) for js in skin_joints for j in js})
    if not used:
        return None
    infl = [joint_names[j] for j in used]
    sc = cmds.skinCluster(infl, mesh_name, toSelectedBones=True, name=mesh_name + "_skinCluster",
                          maximumInfluences=max(1, int(max_influence)), skinMethod=0, obeyMaxInfluences=False,
                          normalizeWeights=1)[0]
    fn = oma.MFnSkinCluster(_mobject(sc))
    order = [p.partialPathName() for p in fn.influenceObjects()]
    col = {n: k for k, n in enumerate(order)}
    nv = len(skin_joints)
    W = np.zeros((nv, len(order)))
    for v in range(nv):
        for j, w in zip(skin_joints[v], skin_weights[v]):
            W[v, col[joint_names[int(j)]]] += float(w)
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.setCompleteData(nv)
    infl_idx = om.MIntArray([int(fn.indexForInfluenceObject(_dagpath(n))) for n in order])
    shape = _dagpath(mesh_name)
    shape.extendToShape()
    fn.setWeights(shape, comp, infl_idx, om.MDoubleArray(W.ravel().tolist()), False)
    return sc


def add_attribute(node, long_name):
    cmds = _cmds()
    if not cmds.attributeQuery(long_name, node=node, exists=True):
        cmds.addAttr(node, longName=long_name, keyable=True, attributeType="float", minValue=0.0, maxValue=1.0)


def import_gui(path, group):
    cmds = _cmds()
    cmds.file(path, i=True, groupReference=True, groupName=group)


def _local_t(node):
    return list(_cmds().getAttr(node + ".translate")[0])


def position_gui(group="gui"):
    """dna_viewer: move the GUI so CTRL_C_eye lines up with FACIAL_L_Eye (object-space y) and +10 in x."""
    cmds = _cmds()
    if not (cmds.objExists("CTRL_C_eye") and cmds.objExists("FACIAL_L_Eye")):
        return
    dy = _local_t("FACIAL_L_Eye")[1] - _local_t("CTRL_C_eye")[1]
    cmds.move(GUI_TRANSLATE_X, dy, 0, group, relative=True, objectSpace=True)


def place_analog_gui():
    """dna_viewer's add_eyes + add_eye_locators (object-space translations, as in Epic's code)."""
    cmds = _cmds()
    need = ("FACIAL_L_Eye", "FACIAL_R_Eye", "FACIAL_C_FacialRoot", "LOC_C_eyeDriver", "LOC_L_eyeDriver",
            "LOC_R_eyeDriver", "LOC_L_eyeAimUp", "LOC_R_eyeAimUp", "GRP_C_eyesAim", "GRP_L_eyeAim", "GRP_R_eyeAim")
    if not all(cmds.objExists(n) for n in need):
        return
    el, er = np.array(_local_t("FACIAL_L_Eye")), np.array(_local_t("FACIAL_R_Eye"))
    cmds.setAttr("LOC_C_eyeDriver.translate", *_local_t("FACIAL_C_FacialRoot"))
    dl = np.array(_local_t("LOC_L_eyeAimUp")) - np.array(_local_t("LOC_L_eyeDriver"))
    dr = np.array(_local_t("LOC_R_eyeAimUp")) - np.array(_local_t("LOC_R_eyeDriver"))
    cmds.setAttr("LOC_L_eyeDriver.translate", *el)
    cmds.setAttr("LOC_R_eyeDriver.translate", *er)
    cmds.setAttr("LOC_L_eyeAimUp.translate", *(el + dl))
    cmds.setAttr("LOC_R_eyeAimUp.translate", *(er + dr))
    mid = er + (el - er) / 2
    c = _local_t("GRP_C_eyesAim")
    cmds.setAttr("GRP_C_eyesAim.translate", mid[0], mid[1], c[2])
    lz, rz = _local_t("GRP_L_eyeAim")[2], _local_t("GRP_R_eyeAim")[2]
    cmds.setAttr("GRP_L_eyeAim.translate", el[0], el[1], lz)
    cmds.setAttr("GRP_R_eyeAim.translate", er[0], er[1], rz)


def run_assemble_script(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("additional_assemble_script", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run_after_assemble(TOP, RIG, {})


# --------------------------------------------------------------------------- user mesh
def load_user_mesh(path):
    if not str(path).lower().endswith(".npz"):
        raise ValueError("user_mesh must be the <name>_usermesh.npz written by the fitting step, not %s.\n"
                         "For a character that is in a Maya scene: open the scene, run mh_fit_maya.show(), select the "
                         "head/body mesh and go through steps 1-4 (Build writes the .npz and builds the rig)."
                         % os.path.basename(str(path)))
    z = np.load(path, allow_pickle=True)
    d = {k: z[k] for k in z.files}
    d["name"] = str(d["name"])
    d["skin_joints"] = list(d["skin_joints"])
    d["skin_weights"] = list(d["skin_weights"])
    d["targets"] = list(d["targets"])
    return d


def add_user_mesh(um, joint_names, channel_names, head_name):
    """The user's own mesh: skinned and blend-shaped with weights / deltas transferred from the fitted
    MetaHuman head; its blendshape weights follow the head's."""
    cmds = _cmds()
    tr = create_mesh(um, name=um["name"])
    bs = add_blendshapes(tr, um["targets"], channel_names)
    add_skin(tr, joint_names, um["skin_joints"], um["skin_weights"], int(um["max_influence"]))
    if bs:
        for t, tg in enumerate(um["targets"]):
            ch = channel_names[tg["channel"]]
            src = "%s_blendShapes.%s__%s" % (head_name, head_name, ch)
            if cmds.objExists(src):
                cmds.connectAttr(src, "%s.%s__%s" % (bs, tr, ch), force=True)
    return tr


# --------------------------------------------------------------------------- main
def build(dna_path, user_mesh=None, gui=True, neck_correctives=True, new_scene=True, hide_mh_head=True, log=print):
    """Build the face rig. dna_path: LOD0 DNA (e.g. written by the fitting step).
    user_mesh: optional .npz from the fitting step (the user's own mesh, transferred skin + blendshapes)."""
    cmds = _cmds()
    import native_riglogic as nrl
    if not str(dna_path).lower().endswith(".dna"):
        raise ValueError("dna_path must be a .dna file (e.g. <name>_fitted.dna), not %s" % os.path.basename(str(dna_path)))
    if user_mesh:
        load_user_mesh(user_mesh)  # checks the file before anything in the scene changes
    if new_scene:
        if cmds.file(q=True, modified=True) and not cmds.about(batch=True):
            ans = cmds.confirmDialog(title="MetaHuman build", message="The rig is built in a NEW scene.\n"
                                     "The current scene has unsaved changes. Discard them?",
                                     button=["Discard and build", "Cancel"], defaultButton="Cancel", cancelButton="Cancel")
            if ans != "Discard and build":
                log("cancelled")
                return None
        cmds.file(new=True, force=True)
    reader = G.open_dna(dna_path)
    if reader.getTranslationUnit() != 0 or reader.getRotationUnit() != 0:
        raise RuntimeError("Only cm / degree DNAs are supported.")
    cmds.currentUnit(linear="cm", angle="deg")
    meshes = [G.read_mesh(reader, m) for m in reader.getMeshIndicesForLOD(0)]
    joints = G.read_joints(reader)
    channel_names = [reader.getBlendShapeChannelName(i) for i in range(reader.getBlendShapeChannelCount())]
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        log("groups, joints...")
        create_groups()
        names = create_joints(joints)
        for m in meshes:
            log("mesh %s (%d verts, %d blendshape targets)" % (m["name"], len(m["pos"]), len(m["targets"])))
            create_mesh(m)
            add_blendshapes(m["name"], m["targets"], channel_names)
            add_skin(m["name"], names, m["skin_joints"], m["skin_weights"], m["max_influence"])
        um = None
        if user_mesh:
            um = load_user_mesh(user_mesh)
            log("user mesh %s (%d verts)" % (um["name"], len(um["pos"])))
            add_user_mesh(um, names, channel_names, meshes[0]["name"])
        raw_names = [reader.getRawControlName(i) for i in range(reader.getRawControlCount())]
        map_names = [reader.getAnimatedMapName(i) for i in range(reader.getAnimatedMapCount())]
        if gui:
            log("GUI...")
            import_gui(os.path.join(DATA, "gui.ma"), "gui")
            position_gui("gui")
            for n in raw_names:
                node, attr = n.split(".")
                if cmds.objExists(node):
                    add_attribute(node, attr)
            if not cmds.objExists("FRM_WMmultipliers"):
                cmds.createNode("transform", name="FRM_WMmultipliers", parent=RIG)
            for n in map_names:
                add_attribute("FRM_WMmultipliers", n.replace(".", "_"))
            import_gui(os.path.join(DATA, "analog_gui.ma"), "analog_gui")
            place_analog_gui()
        holder = None
        if gui:  # Rig Logic reads the GUI controls
            log("native Rig Logic...")
            holder = nrl.build(source=dna_path, lod=0)
            nrl.switch_to_native(holder=holder)
        if gui:
            log("Epic's additional assemble script...")
            run_assemble_script(os.path.join(DATA, "additional_assemble_script.py"))
            if neck_correctives and holder:
                for base in NECK_RAW:
                    for s in "UMD":
                        src, dst = "CTRL_expressions.%s%s" % (base, s), "%s.raw_%s%s" % (holder, base, s)
                        if cmds.objExists(src) and cmds.objExists(dst):
                            cmds.connectAttr(src, dst, force=True)
        if um is not None and hide_mh_head:
            cmds.setAttr(meshes[0]["name"] + ".visibility", 0)
        cmds.select(clear=True)
    finally:
        cmds.undoInfo(stateWithoutFlush=True)
    log("done: %s" % os.path.basename(dna_path))
    return holder
