#  -*- coding: utf-8 -*-
"""
Bake the facial Rig Logic of a MetaHuman DNA into native Maya nodes.

After switching, the face rig no longer needs Epic's embeddedRL4 plug-in or the DNA file:
everything the DNA's behaviour layer does is stored in ordinary Maya nodes.

What Rig Logic computes, and the native node for each part
---------------------------------------------------------
GUI controls -> raw controls      piecewise-linear "conditional table"   -> animCurveUU (linear keys)
raw controls -> correctives (PSD)  product of 2..6 raw controls, 0..1      -> multDoubleLinear chain + clamp
inputs -> joints (~5000 channels)  one big linear matrix (~850k numbers)   -> ONE blendShape on a hidden
                                                                              degree-1 curve: one target per
                                                                              input, each CV holds 3 channels;
                                                                              curveInfo reads the CVs out
                                                                              (rotations in degrees, converted
                                                                              by Maya's own unitConversion)
inputs -> blendshape weights       direct copy                             -> connections
inputs -> wrinkle maps             conditional table, 0..1                 -> animCurveUU + sum + clamp

Joint outputs follow Epic's node exactly: translate = DNA neutral + delta, rotate = delta (the rest
orientation is in the joint orient), scale = 1 + delta.

Checked offline against Epic's own Rig Logic (libembeddedRL4) on random and boundary poses:
see README "Native facial rig". Two known differences, both outside normal use:
  * a GUI control pushed beyond its range keeps its end value (Epic's node drops to 0);
    the GUI controls are limited to their range, so this doesn't happen with the stock GUI;
  * at exactly 0.33 / 0.66 on the two multi-step mouth controls, Epic's node adds both
    neighbouring steps (a one-value spike to 2x); the native curve stays continuous.

Usage (in Maya, scene with a MetaHuman face rig open):
    import native_riglogic as nrl
    nrl.show()                       # small window
    # or
    nrl.build()                      # reads the DNA path from the rl4Embedded node, LOD 0
    nrl.verify()                     # compares with the Epic node on random poses (plug-in loaded)
    nrl.switch_to_native()           # disconnects (and deletes) the Epic node, connects the native one
    nrl.switch_to_rl4()              # back, as long as the Epic node wasn't deleted
    nrl.cleanup_epic_nodes()         # optional: delete the Epic node and the (unused) neck RBF nodes

Without Epic's `dna` Python module in this Maya, export the DNA once with tools/dna_behavior_export.py
(any Python that can import `dna`) and pass the JSON:  nrl.build(source="/path/character_behavior.json")
"""
import json
import math
import os
import random

NATIVE_NODE = "MH_nativeRL"
NATIVE_GROUP = "MH_nativeRL_GRP"
EPS_KEY = 1e-5
JOINT_ATTRS = ("translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ",
               "scaleX", "scaleY", "scaleZ")
_SHORT_TO_LONG = {"tx": "translateX", "ty": "translateY", "tz": "translateZ", "rx": "rotateX",
                  "ry": "rotateY", "rz": "rotateZ", "sx": "scaleX", "sy": "scaleY", "sz": "scaleZ"}


# =========================================================================== DNA data
def behavior_from_reader(r):
    """Behaviour layer of a dna reader as plain Python data (same layout as the JSON export)."""
    def L(x):
        return [float(v) for v in x]

    def I(x):
        return [int(v) for v in x]
    d = {"format": "native-riglogic", "version": 1,
         "translationUnit": int(r.getTranslationUnit()), "rotationUnit": int(r.getRotationUnit()),
         "lodCount": int(r.getLODCount()),
         "guiControls": [r.getGUIControlName(i) for i in range(r.getGUIControlCount())],
         "rawControls": [r.getRawControlName(i) for i in range(r.getRawControlCount())],
         "guiToRaw": {"input": I(r.getGUIToRawInputIndices()), "output": I(r.getGUIToRawOutputIndices()),
                      "from": L(r.getGUIToRawFromValues()), "to": L(r.getGUIToRawToValues()),
                      "slope": L(r.getGUIToRawSlopeValues()), "cut": L(r.getGUIToRawCutValues())},
         "psd": {"count": int(r.getPSDCount()), "rows": I(r.getPSDRowIndices()),
                 "cols": I(r.getPSDColumnIndices()), "values": L(r.getPSDValues())}}
    jn = r.getJointCount()
    d["joints"] = [r.getJointName(i) for i in range(jn)]
    d["neutralTranslation"] = [list(r.getNeutralJointTranslation(i)) for i in range(jn)]
    d["neutralRotation"] = [list(r.getNeutralJointRotation(i)) for i in range(jn)]
    d["jointGroups"] = [{"lods": I(r.getJointGroupLODs(g)), "inputs": I(r.getJointGroupInputIndices(g)),
                         "outputs": I(r.getJointGroupOutputIndices(g)), "values": L(r.getJointGroupValues(g)),
                         "joints": I(r.getJointGroupJointIndices(g))}
                        for g in range(r.getJointGroupCount())]
    d["blendShapeChannels"] = [r.getBlendShapeChannelName(i) for i in range(r.getBlendShapeChannelCount())]
    d["blendShapes"] = {"lods": I(r.getBlendShapeChannelLODs()), "input": I(r.getBlendShapeChannelInputIndices()),
                        "output": I(r.getBlendShapeChannelOutputIndices())}
    d["meshes"] = [r.getMeshName(i) for i in range(r.getMeshCount())]
    d["meshBlendShapeMapping"] = [[int(r.getMeshBlendShapeChannelMapping(i).meshIndex),
                                   int(r.getMeshBlendShapeChannelMapping(i).blendShapeChannelIndex)]
                                  for i in range(r.getMeshBlendShapeChannelMappingCount())]
    d["meshesPerLOD"] = [I(r.getMeshIndicesForLOD(l)) for l in range(r.getLODCount())]
    d["animatedMaps"] = [r.getAnimatedMapName(i) for i in range(r.getAnimatedMapCount())]
    d["animatedMapTable"] = {"lods": I(r.getAnimatedMapLODs()), "input": I(r.getAnimatedMapInputIndices()),
                             "output": I(r.getAnimatedMapOutputIndices()), "from": L(r.getAnimatedMapFromValues()),
                             "to": L(r.getAnimatedMapToValues()), "slope": L(r.getAnimatedMapSlopeValues()),
                             "cut": L(r.getAnimatedMapCutValues())}
    return d


def load_behavior(source):
    """source: a .json written by tools/dna_behavior_export.py, or a .dna (needs Epic's `dna` module)."""
    if source.lower().endswith(".json"):
        with open(source, "r", encoding="utf-8") as f:
            return json.load(f)
    try:
        from mh_paths import ensure_dna
        dna = ensure_dna()
    except ImportError:
        try:
            import dna
        except ImportError as e:
            raise RuntimeError("Can't import the `dna` module (%s). Pass a behaviour .json instead of the .dna, "
                               "or set MH_NODEPS_ROOT to the mh_nodeps folder." % e)
    stream = dna.FileStream(source, dna.FileStream.AccessMode_Read, dna.FileStream.OpenMode_Binary)
    reader = dna.BinaryStreamReader(stream, dna.DataLayer_All)
    reader.read()
    if not dna.Status.isOk():
        raise RuntimeError("Error loading DNA %s: %s" % (source, dna.Status.get().message))
    return behavior_from_reader(reader)


# =========================================================================== plan (pure Python)
def piecewise_keys(segments, eps=EPS_KEY):
    """Keys (x, y) of a linear curve equal to the sum of conditional-table rows for one
    input/output pair. Rows are (from, to, slope, cut), active for from <= x <= to.
    Jumps get two keys eps apart. Outside all rows the curve keeps its end values."""
    pts = sorted({s[0] for s in segments} | {s[1] for s in segments})

    def left(x):
        return sum(s * x + c for f, t, s, c in segments if f < x <= t)

    def right(x):
        return sum(s * x + c for f, t, s, c in segments if f <= x < t)
    if len(pts) == 1:  # degenerate single point row
        x = pts[0]
        return [(x, sum(s * x + c for f, t, s, c in segments))]
    keys = []
    last = len(pts) - 1
    for k, x in enumerate(pts):
        lv, rv = left(x), right(x)
        if k == 0:
            keys.append((x, rv))
        elif k == last:
            keys.append((x, lv))
        elif abs(lv - rv) <= 1e-5:  # float32 data: treat as continuous
            keys.append((x, lv))
        else:
            keys.append((x, lv))
            keys.append((x + eps, rv))
    return keys


def eval_keys(keys, x):
    """Linear interpolation with constant extrapolation (what the animCurveUU does)."""
    if x <= keys[0][0]:
        return keys[0][1]
    if x >= keys[-1][0]:
        return keys[-1][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x0 <= x <= x1:
            return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return keys[-1][1]


def _group_segments(table, rows=None):
    n = len(table["input"]) if rows is None else rows
    pairs = {}
    for k in range(n):
        key = (table["input"][k], table["output"][k])
        pairs.setdefault(key, []).append((table["from"][k], table["to"][k], table["slope"][k], table["cut"][k]))
    return pairs


def _safe(name):
    out = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in name)
    return out if out and not out[0].isdigit() else "_" + out


def make_plan(d, lod=0):
    """Everything the node network needs, computed from the behaviour data."""
    R = len(d["rawControls"])
    P = d["psd"]["count"]
    lod = max(0, min(int(lod), d["lodCount"] - 1))
    plan = {"lod": lod, "rawCount": R, "psdCount": P}
    tscale = 100.0 if d.get("translationUnit", 0) == 1 else 1.0          # m -> cm
    rscale = 180.0 / math.pi if d.get("rotationUnit", 0) == 1 else 1.0   # rad -> deg

    # signal names (one attribute each on the holder node)
    names, used = [], set()
    for n in d["rawControls"]:
        a = "raw_" + _safe(n.split(".")[-1])
        while a in used:
            a += "_"
        used.add(a)
        names.append(a)
    names += ["psd_%03d" % i for i in range(P)]
    plan["signals"] = names

    # GUI -> raw
    raw_curves = []
    for (gi, ro), segs in sorted(_group_segments(d["guiToRaw"]).items(), key=lambda kv: (kv[0][1], kv[0][0])):
        raw_curves.append({"gui": d["guiControls"][gi], "raw": ro, "keys": piecewise_keys(segs)})
    plan["rawCurves"] = raw_curves

    # PSDs (rows are R..R+P-1, columns are raw controls)
    cols, factor = {}, {}
    for r, c, v in zip(d["psd"]["rows"], d["psd"]["cols"], d["psd"]["values"]):
        cols.setdefault(r, []).append(c)
        factor[r] = factor.get(r, 1.0) * v
    psds = []
    for p in range(P):
        r = R + p
        if r in cols:
            if any(c >= R for c in cols[r]):
                raise RuntimeError("PSD %d reads another PSD; not supported" % p)
            psds.append({"psd": p, "inputs": cols[r], "factor": factor[r]})
    plan["psds"] = psds

    # joints: one channel per joint-matrix row of this LOD
    channels = {}   # output index -> {signal: coefficient}
    for g in d["jointGroups"]:
        nrows = g["lods"][lod] if lod < len(g["lods"]) else 0
        C = len(g["inputs"])
        vals = g["values"]
        for r in range(nrows):
            o = g["outputs"][r]
            attr = o % 9
            scale = tscale if attr < 3 else (rscale if attr < 6 else 1.0)
            row = channels.setdefault(o, {})
            base = r * C
            for c in range(C):
                v = vals[base + c]
                if v != 0.0:
                    s = g["inputs"][c]
                    row[s] = row.get(s, 0.0) + v * scale
    order = sorted(channels)
    plan["channels"] = []
    targets = {}
    for slot, o in enumerate(order):
        j, a = divmod(o, 9)
        if a < 3:
            base = d["neutralTranslation"][j][a] * tscale
        elif a < 6:
            base = 0.0
        else:
            base = 1.0
        plan["channels"].append({"output": o, "joint": d["joints"][j], "attr": a, "base": base})
        point, axis = divmod(slot, 3)
        for s, v in channels[o].items():
            targets.setdefault(s, {}).setdefault(point, [0.0, 0.0, 0.0])[axis] += v
    plan["pointCount"] = max(2, (len(order) + 2) // 3)
    plan["targets"] = {s: sorted(t.items()) for s, t in targets.items()}
    # every channel of every joint the DNA drives (for joints/attrs without a row: constant value)
    plan["neutral"] = {d["joints"][j]: [d["neutralTranslation"][j][k] * tscale for k in range(3)]
                       for g in d["jointGroups"] for j in g["joints"]}

    # blendshapes
    bs = d["blendShapes"]
    nb = bs["lods"][lod] if lod < len(bs["lods"]) else 0
    plan["blendShapes"] = [{"input": bs["input"][k], "channel": bs["output"][k]} for k in range(nb)]
    plan["blendShapeChannels"] = d["blendShapeChannels"]
    lod_meshes = set(d["meshesPerLOD"][lod]) if d.get("meshesPerLOD") else set(range(len(d["meshes"])))
    plan["meshChannels"] = [(d["meshes"][m], c) for m, c in d["meshBlendShapeMapping"] if m in lod_meshes]

    # animated maps
    am = d["animatedMapTable"]
    na = am["lods"][lod] if lod < len(am["lods"]) else 0
    maps = {}
    for (i, o), segs in _group_segments(am, na).items():
        maps.setdefault(o, []).append({"input": i, "keys": piecewise_keys(segs)})
    plan["animatedMaps"] = [{"map": o, "name": d["animatedMaps"][o], "curves": maps[o]} for o in sorted(maps)]
    plan["animatedMapNames"] = d["animatedMaps"]
    return plan


def evaluate_plan(plan, gui_values):
    """What the native network computes, in plain Python (for tests).
    gui_values: {gui control name: value}. Returns (signals, joint channels by output, bs, maps)."""
    R, P = plan["rawCount"], plan["psdCount"]
    sig = [0.0] * (R + P)
    for c in plan["rawCurves"]:
        sig[c["raw"]] += eval_keys(c["keys"], gui_values.get(c["gui"], 0.0))
    for p in plan["psds"]:
        v = p["factor"]
        for i in p["inputs"]:
            v *= sig[i]
        sig[R + p["psd"]] = min(1.0, max(0.0, v))
    pts = [[0.0, 0.0, 0.0] for _ in range(plan["pointCount"])]
    for slot, ch in enumerate(plan["channels"]):
        pts[slot // 3][slot % 3] = ch["base"]
    for s, tgt in plan["targets"].items():
        w = sig[s]
        if w:
            for point, dv in tgt:
                for a in range(3):
                    pts[point][a] += w * dv[a]
    joints = {ch["output"]: pts[slot // 3][slot % 3] for slot, ch in enumerate(plan["channels"])}
    bs = {b["channel"]: sig[b["input"]] for b in plan["blendShapes"]}
    maps = {}
    for m in plan["animatedMaps"]:
        maps[m["map"]] = min(1.0, max(0.0, sum(eval_keys(c["keys"], sig[c["input"]]) for c in m["curves"])))
    return sig, joints, bs, maps


# =========================================================================== network builder
def build_network(maya, plan, name=NATIVE_NODE):
    """Create the native nodes through `maya` (an adapter: real Maya below, a fake one in tests).
    Outputs are NOT connected to the rig yet; returns {"holder", "sources"} where sources maps
    each output kind/key to the plug that carries its value."""
    R = plan["rawCount"]
    group = maya.create("transform", NATIVE_GROUP)
    holder = maya.create("network", name)
    maya.add_attrs(holder, plan["signals"])
    sig = ["%s.%s" % (holder, a) for a in plan["signals"]]

    # GUI -> raw
    per_raw = {}
    for c in plan["rawCurves"]:
        per_raw.setdefault(c["raw"], []).append(c)
    for r, curves in per_raw.items():
        outs = []
        for c in curves:
            crv = maya.create("animCurveUU", "nrl_%s_from_%s" % (plan["signals"][r], _safe(c["gui"])))
            maya.set_keys(crv, c["keys"])
            maya.connect(c["gui"], crv + ".input")
            outs.append(crv + ".output")
        maya.connect(_sum(maya, outs, "nrl_%s_sum" % plan["signals"][r]), sig[r])

    # PSDs: product chain, then clamp 0..1 (three per clamp node)
    clamps = []
    for k, p in enumerate(plan["psds"]):
        cur = sig[p["inputs"][0]]
        for n, i in enumerate(p["inputs"][1:]):
            m = maya.create("multDoubleLinear", "nrl_psd%03d_mul%d" % (p["psd"], n))
            maya.connect(cur, m + ".input1")
            maya.connect(sig[i], m + ".input2")
            cur = m + ".output"
        if p["factor"] != 1.0 or len(p["inputs"]) == 1:
            m = maya.create("multDoubleLinear", "nrl_psd%03d_weight" % p["psd"])
            maya.connect(cur, m + ".input1")
            maya.set(m + ".input2", p["factor"])
            cur = m + ".output"
        cl, ch = _clamp_slot(maya, clamps, "nrl_psd_clamp")
        maya.connect(cur, "%s.input%s" % (cl, ch))
        maya.connect("%s.output%s" % (cl, ch), sig[R + p["psd"]])

    # joints: curve + blendShape + curveInfo
    points = [[0.0, 0.0, 0.0] for _ in range(plan["pointCount"])]
    for slot, chn in enumerate(plan["channels"]):
        points[slot // 3][slot % 3] = chn["base"]
    curve, shape = maya.make_curve("nrl_jointValues", points, parent=group)
    bs = maya.make_blendshape(shape, "nrl_jointMatrix")
    for t, (s, tgt) in enumerate(sorted(plan["targets"].items())):
        maya.set_bs_target(bs, t, plan["signals"][s], tgt)
        maya.connect(sig[s], "%s.weight[%d]" % (bs, t))
    info = maya.create("curveInfo", "nrl_jointValues_info")
    maya.connect(shape + ".worldSpace[0]", info + ".inputCurve")
    sources = {"joint": {}, "bs": {}, "map": {}}
    axis_name = ("xValue", "yValue", "zValue")
    for slot, chn in enumerate(plan["channels"]):
        # rotation channels hold degrees: connected directly to rotate while the scene is in
        # cm/deg, Maya inserts the unitConversion (factor pi/180) itself, and removes /
        # re-creates it when switching between the native and the Epic node
        value_plug = "%s.controlPoints[%d].%s" % (info, slot // 3, axis_name[slot % 3])
        sources["joint"][(chn["joint"], chn["attr"])] = {"drive": value_plug, "value": value_plug}

    # blendshape channels
    for b in plan["blendShapes"]:
        sources["bs"][b["channel"]] = {"drive": sig[b["input"]], "value": sig[b["input"]]}

    # animated maps: curves -> sum -> clamp, stored on the holder
    maya.add_attrs(holder, ["map_%03d" % m["map"] for m in plan["animatedMaps"]])
    clamps = []
    for m in plan["animatedMaps"]:
        outs = []
        for n, c in enumerate(m["curves"]):
            crv = maya.create("animCurveUU", "nrl_map%03d_from_%s" % (m["map"], plan["signals"][c["input"]]))
            maya.set_keys(crv, c["keys"])
            maya.connect(sig[c["input"]], crv + ".input")
            outs.append(crv + ".output")
        cl, ch = _clamp_slot(maya, clamps, "nrl_map_clamp")
        maya.connect(_sum(maya, outs, "nrl_map%03d_sum" % m["map"]), "%s.input%s" % (cl, ch))
        plug = "%s.map_%03d" % (holder, m["map"])
        maya.connect("%s.output%s" % (cl, ch), plug)
        sources["map"][m["map"]] = {"drive": plug, "value": plug}
    return {"holder": holder, "group": group, "sources": sources}


def _sum(maya, plugs, name):
    if len(plugs) == 1:
        return plugs[0]
    pma = maya.create("plusMinusAverage", name)
    for k, p in enumerate(plugs):
        maya.connect(p, "%s.input1D[%d]" % (pma, k))
    return pma + ".output1D"


def _clamp_slot(maya, clamps, name):
    """Next free channel (R/G/B) of a clamp node set to 0..1."""
    if not clamps or clamps[-1][1] == 3:
        cl = maya.create("clamp", "%s%d" % (name, len(clamps)))
        for ch in "RGB":
            maya.set("%s.min%s" % (cl, ch), 0.0)
            maya.set("%s.max%s" % (cl, ch), 1.0)
        clamps.append([cl, 0])
    cl = clamps[-1]
    ch = "RGB"[cl[1]]
    cl[1] += 1
    return cl[0], ch


# =========================================================================== Maya side
class MayaAdapter(object):
    """The few Maya operations build_network needs."""

    def __init__(self):
        from maya import cmds
        import maya.api.OpenMaya as om
        import maya.api.OpenMayaAnim as oma
        self.cmds, self.om, self.oma = cmds, om, oma

    def create(self, node_type, name):
        return self.cmds.createNode(node_type, name=name, skipSelect=True)

    def add_attrs(self, node, names):
        for n in names:
            self.cmds.addAttr(node, longName=n, attributeType="double", defaultValue=0.0)

    def set(self, plug, value):
        self.cmds.setAttr(plug, value)

    def connect(self, src, dst):
        self.cmds.connectAttr(src, dst, force=True)

    def _mobject(self, node):
        sel = self.om.MSelectionList()
        sel.add(node)
        return sel.getDependNode(0)

    def set_keys(self, curve, keys):
        try:
            fn = self.oma.MFnAnimCurve(self._mobject(curve))
            lin = self.oma.MFnAnimCurve.kTangentLinear
            for x, y in keys:
                fn.addKey(x, y, tangentInType=lin, tangentOutType=lin)
        except (TypeError, ValueError, RuntimeError):
            # same data as a .ma file: ".ktv" holds (input, value) pairs
            flat = [v for k in keys for v in k]
            self.cmds.setAttr("%s.ktv[0:%d]" % (curve, len(keys) - 1), *flat, size=len(keys))
            self.cmds.keyTangent(curve, edit=True, inTangentType="linear", outTangentType="linear")
        n = self.cmds.keyframe(curve, query=True, keyframeCount=True)
        if n != len(keys):
            raise RuntimeError("%s: %d keys set, %d expected" % (curve, n, len(keys)))

    def make_curve(self, name, points, parent=None):
        tr = self.cmds.curve(degree=1, point=[tuple(p) for p in points], name=name)
        shape = self.cmds.listRelatives(tr, shapes=True, fullPath=False)[0]
        shape = self.cmds.rename(shape, name + "Shape")
        if parent:
            tr = self.cmds.parent(tr, parent)[0]
        for a in ("t", "r", "s"):
            for ax in "xyz":
                self.cmds.setAttr("%s.%s%s" % (tr, a, ax), lock=True)
        return tr, shape

    def make_blendshape(self, shape, name):
        return self.cmds.blendShape(shape, name=name, origin="local")[0]

    def set_bs_target(self, bs, index, alias, target):
        """target: [(cv index, [dx, dy, dz]), ...] stored as a sparse blendShape target."""
        om = self.om
        self.cmds.setAttr("%s.weight[%d]" % (bs, index), 0.0)
        try:
            self.cmds.aliasAttr(alias, "%s.weight[%d]" % (bs, index))
        except RuntimeError:
            pass
        item = "%s.inputTarget[0].inputTargetGroup[%d].inputTargetItem[6000]" % (bs, index)
        sel = om.MSelectionList()
        sel.add(item + ".inputPointsTarget")
        sel.add(item + ".inputComponentsTarget")
        pts_plug, comp_plug = sel.getPlug(0), sel.getPlug(1)
        pts = om.MPointArray()
        ids = []
        for cv, dv in target:
            pts.append(om.MPoint(dv[0], dv[1], dv[2], 1.0))
            ids.append(int(cv))
        pts_plug.setMObject(om.MFnPointArrayData().create(pts))
        comp_fn = om.MFnSingleIndexedComponent()
        comp = comp_fn.create(om.MFn.kCurveCVComponent)
        comp_fn.addElements(ids)
        list_fn = om.MFnComponentListData()
        list_obj = list_fn.create()
        list_fn.add(comp)
        comp_plug.setMObject(list_obj)


def _cmds():
    from maya import cmds
    return cmds


def find_rl4_nodes():
    cmds = _cmds()
    nodes = []
    for t in ("embeddedNodeRL4",):
        try:
            nodes += cmds.ls(type=t) or []
        except RuntimeError:
            pass
    nodes += [n for n in cmds.ls("rl4Embedded_*", type="unknown") or [] if n not in nodes]
    nodes += [n for n in cmds.ls("rl4Embedded_*") or [] if n not in nodes and cmds.objectType(n) != "transform"]
    return nodes


def _rl4_dna_path(rl4):
    cmds = _cmds()
    try:
        return cmds.getAttr(rl4 + ".dnaFilePath")
    except (RuntimeError, ValueError):
        return ""


def _resolve_targets(plan, rl4=None):
    """Destination plugs for every output, keyed like build_network's sources:
    ("joint", (joint, attr)) / ("bs", channel) / ("map", index) -> [plug, ...].
    With an Epic node in the scene its actual connections are used; otherwise names follow
    dna_viewer's naming (<mesh>_blendShapes.<mesh>__<channel>, FRM_WMmultipliers.<map>)."""
    cmds = _cmds()
    targets = {}
    joints = set(plan["neutral"])
    channel_index = {n: i for i, n in enumerate(plan["blendShapeChannels"])}
    map_index = {n.replace(".", "_"): i for i, n in enumerate(plan["animatedMapNames"])}
    unmatched = []
    if rl4 and cmds.objExists(rl4):
        pairs = cmds.listConnections(rl4, source=False, destination=True, plugs=True, connections=True,
                                     skipConversionNodes=True) or []
        for src, dst in zip(pairs[0::2], pairs[1::2]):
            node, attr = dst.split(".", 1)
            base = _base_name(node)
            key = None
            if base in joints:
                long = _SHORT_TO_LONG.get(attr, attr)
                if long in JOINT_ATTRS:
                    key = ("joint", (base, JOINT_ATTRS.index(long)))
            elif cmds.objectType(node) == "blendShape":
                alias = attr
                if alias.startswith("weight[") or alias.startswith("w["):
                    alias = cmds.aliasAttr(dst, q=True) or alias
                ch = alias.split("__", 1)[1] if "__" in alias else alias
                if ch in channel_index:
                    key = ("bs", channel_index[ch])
            elif attr in map_index:
                key = ("map", map_index[attr])
            if key is None:
                unmatched.append(dst)
            else:
                targets.setdefault(key, []).append(dst)
        return targets, unmatched
    # no Epic node: build the names
    for j in joints:
        if cmds.objExists(j):
            for a in range(9):
                targets[("joint", (j, a))] = ["%s.%s" % (j, JOINT_ATTRS[a])]
    for mesh, c in plan["meshChannels"]:
        for plug in ("%s_blendShapes.%s__%s" % (mesh, mesh, plan["blendShapeChannels"][c]),
                     "%s_blendShapes.%s" % (mesh, plan["blendShapeChannels"][c])):
            if cmds.objExists(plug):
                targets.setdefault(("bs", c), []).append(plug)
                break
    for name, i in map_index.items():
        plug = "FRM_WMmultipliers." + name
        if cmds.objExists(plug):
            targets[("map", i)] = [plug]
    return targets, unmatched


def _base_name(node):
    """'|grp|ns:FACIAL_L_Eye' -> 'FACIAL_L_Eye'"""
    return node.split("|")[-1].split(":")[-1]


def _resolve_gui(plan, rl4=None):
    """Scene plug for each DNA GUI control ('CTRL_L_brow_down.ty'). With an Epic node, its own
    input connections are used, so namespaces and long/short attribute names don't matter."""
    cmds = _cmds()
    found = {}
    if rl4 and cmds.objExists(rl4):
        pairs = cmds.listConnections(rl4, source=True, destination=False, plugs=True, connections=True,
                                     skipConversionNodes=True) or []
        by_name = {}
        for dst, src in zip(pairs[0::2], pairs[1::2]):
            node, attr = src.split(".", 1)
            by_name[(_base_name(node), _SHORT_TO_LONG.get(attr, attr))] = src
        for c in plan["rawCurves"]:
            node, attr = c["gui"].split(".", 1)
            plug = by_name.get((node, _SHORT_TO_LONG.get(attr, attr)))
            if plug:
                found[c["gui"]] = plug
    for c in plan["rawCurves"]:
        if c["gui"] not in found and cmds.objExists(c["gui"]):
            found[c["gui"]] = c["gui"]
    return found


def _static_value(plan, joint, attr):
    if attr < 3:
        return plan["neutral"][joint][attr]
    return 0.0 if attr < 6 else 1.0


class _Units(object):
    """Build in centimetres / degrees, like the MetaHuman rig; restore the user's units after."""

    def __enter__(self):
        cmds = _cmds()
        self.lin = cmds.currentUnit(q=True, linear=True)
        self.ang = cmds.currentUnit(q=True, angle=True)
        cmds.currentUnit(linear="cm", angle="deg")

    def __exit__(self, *a):
        cmds = _cmds()
        cmds.currentUnit(linear=self.lin, angle=self.ang)


def build(source=None, lod=0, rl4=None, name=NATIVE_NODE):
    """Build the native network (not yet driving the rig). source: .dna or .json; by default
    the DNA the Epic node points at. Returns the holder node."""
    cmds = _cmds()
    if cmds.objExists(name):
        raise RuntimeError("'%s' already exists. Run remove_native() first." % name)
    rl4 = rl4 or (find_rl4_nodes() or [None])[0]
    if not source:
        source = _rl4_dna_path(rl4) if rl4 else ""
        if not source or not os.path.isfile(source):
            raise RuntimeError("No DNA given and none found on the Rig Logic node.")
    behaviour = load_behavior(source)
    plan = make_plan(behaviour, lod)
    targets, unmatched = _resolve_targets(plan, rl4)
    gui = _resolve_gui(plan, rl4)
    missing_gui = sorted({c["gui"] for c in plan["rawCurves"] if c["gui"] not in gui})
    if missing_gui:
        raise RuntimeError("GUI controls missing in the scene, e.g. %s" % missing_gui[:5])
    for c in plan["rawCurves"]:
        c["gui"] = gui[c["gui"]]

    cmds.undoInfo(openChunk=True, chunkName="native Rig Logic")
    try:
        with _Units():
            net = build_network(MayaAdapter(), plan, name)
        holder = net["holder"]
        cmds.setAttr(net["group"] + ".visibility", 0)
        cmds.setAttr(net["group"] + ".hiddenInOutliner", 1)
        # store the output map so verify / switch work later (also after reopening the scene)
        out_map = []
        static = []
        for key, plugs in targets.items():
            kind, k = key
            src = net["sources"][kind].get(k)
            for plug in plugs:
                if src:
                    out_map.append([kind, list(k) if isinstance(k, tuple) else k, src["drive"], src["value"], plug])
                elif kind == "joint":
                    static.append([plug, _static_value(plan, k[0], k[1])])
                else:
                    static.append([plug, 0.0])
        for attr, value in (("nrlSource", source), ("nrlRL4", rl4 or ""), ("nrlLOD", str(plan["lod"])),
                            ("nrlOutputs", json.dumps(out_map)), ("nrlStatic", json.dumps(static))):
            cmds.addAttr(holder, longName=attr, dataType="string")
            cmds.setAttr(holder + "." + attr, value, type="string")
    finally:
        cmds.undoInfo(closeChunk=True)
    print("native Rig Logic: built '%s' (LOD %d): %d joint channels, %d blendshape targets, "
          "%d correctives, %d maps, %d outputs, %d constant channels."
          % (holder, plan["lod"], len(plan["channels"]), len(plan["targets"]), len(plan["psds"]),
             len(plan["animatedMaps"]), len(out_map), len(static)))
    if unmatched:
        cmds.warning("native Rig Logic: %d Rig Logic outputs not recognised, e.g. %s"
                      % (len(unmatched), unmatched[:5]))
    return holder


def _outputs(holder=NATIVE_NODE):
    cmds = _cmds()
    if not cmds.objExists(holder):
        raise RuntimeError("No native Rig Logic in the scene. Run build() first.")
    return (json.loads(cmds.getAttr(holder + ".nrlOutputs")), json.loads(cmds.getAttr(holder + ".nrlStatic")),
            cmds.getAttr(holder + ".nrlRL4"))


def _gui_ranges(holder=NATIVE_NODE):
    """GUI control plugs and the range of their keys, from the native curves."""
    cmds = _cmds()
    ranges = {}
    for crv in cmds.ls("nrl_*_from_*", type="animCurveUU") or []:
        src = cmds.listConnections(crv + ".input", source=True, destination=False, plugs=True,
                                   skipConversionNodes=True) or []
        if not src or src[0].startswith(holder + "."):
            continue
        xs = cmds.keyframe(crv, q=True, floatChange=True) or [0.0]
        lo, hi = ranges.get(src[0], (0.0, 0.0))
        ranges[src[0]] = (min(lo, min(xs)), max(hi, max(xs)))
    return ranges


def verify(samples=20, tolerance=1e-3, holder=NATIVE_NODE, seed=1):
    """Pose the GUI randomly and compare the native values with what the Epic node writes into the
    rig (it must still be connected, with its plug-in loaded). Returns the largest differences."""
    import maya.api.OpenMaya as om
    cmds = _cmds()
    out_map, static, rl4 = _outputs(holder)
    if not rl4 or not cmds.objExists(rl4) or cmds.objectType(rl4) == "unknown":
        raise RuntimeError("verify() needs the Epic Rig Logic node with its plug-in loaded.")
    driven = [o for o in out_map if (cmds.listConnections(o[4], source=True, destination=False,
                                                          skipConversionNodes=True) or [None])[0] == rl4]
    if not driven:
        raise RuntimeError("The rig isn't driven by the Epic node (already switched?). Use switch_to_rl4() first.")

    def plug(name):
        sel = om.MSelectionList()
        sel.add(name)
        return sel.getPlug(0)
    pairs = [(o[0], o[1], plug(o[3]), plug(o[4]), o[4]) for o in driven]
    ranges = _gui_ranges(holder)
    gui = [g for g in ranges if not cmds.getAttr(g, lock=True)
           and not cmds.listConnections(g, source=True, destination=False)]
    saved = {g: cmds.getAttr(g) for g in gui}
    rng = random.Random(seed)
    worst = {"joint": (0.0, None), "bs": (0.0, None), "map": (0.0, None)}
    poses = [{}]
    for _ in range(samples):
        poses.append({g: (rng.uniform(*ranges[g]) if rng.random() < 0.35 else 0.0) for g in gui})
    for k in range(4):  # boundary values: every control at an end of its range
        poses.append({g: ranges[g][rng.randint(0, 1)] if rng.random() < 0.5 else 0.0 for g in gui})
    try:
        for pose in poses:
            for g in gui:
                cmds.setAttr(g, pose.get(g, 0.0))
            for kind, key, native, rig, name in pairs:
                a = native.asDouble()
                b = rig.asDouble()
                if kind == "joint" and 3 <= key[1] < 6:
                    b = math.degrees(b)
                err = abs(a - b)
                if err > worst[kind][0]:
                    worst[kind] = (err, name)
    finally:
        for g, v in saved.items():
            cmds.setAttr(g, v)
    ok = all(w[0] <= tolerance for w in worst.values())
    print("native Rig Logic vs Epic, %d poses: largest difference joints %.2e (%s), blendshapes "
          "%.2e (%s), maps %.2e (%s) -> %s" % (len(poses), worst["joint"][0], worst["joint"][1], worst["bs"][0],
                                              worst["bs"][1], worst["map"][0], worst["map"][1],
                                              "OK" if ok else "CHECK"))
    return worst


def switch_to_native(delete_rl4=False, holder=NATIVE_NODE):
    """Drive the rig with the native network. delete_rl4=True also deletes the Epic node
    (the scene then no longer needs embeddedRL4 or the DNA file)."""
    cmds = _cmds()
    out_map, static, rl4 = _outputs(holder)
    cmds.undoInfo(openChunk=True, chunkName="switch to native Rig Logic")
    try:
        if rl4 and cmds.objExists(rl4):
            pairs = cmds.listConnections(rl4, source=False, destination=True, plugs=True, connections=True) or []
            saved = list(zip(pairs[0::2], pairs[1::2]))
            if saved:  # keep them so switch_to_rl4() can restore the Epic node
                if not cmds.attributeQuery("nrlRL4Connections", node=holder, exists=True):
                    cmds.addAttr(holder, longName="nrlRL4Connections", dataType="string")
                cmds.setAttr(holder + ".nrlRL4Connections", json.dumps(saved), type="string")
            for src, dst in saved:
                cmds.disconnectAttr(src, dst)
        with _Units():
            for kind, key, drive, value, dst in out_map:
                cmds.connectAttr(drive, dst, force=True)
            for dst, value in static:
                if not cmds.listConnections(dst, source=True, destination=False):
                    try:
                        cmds.setAttr(dst, value)
                    except RuntimeError:
                        pass
        if delete_rl4 and rl4 and cmds.objExists(rl4):
            cmds.lockNode(rl4, lock=False)
            cmds.delete(rl4)
            cmds.setAttr(holder + ".nrlRL4", "", type="string")
    finally:
        cmds.undoInfo(closeChunk=True)
    print("native Rig Logic: face rig now driven by native nodes%s." % (" (Epic node deleted)" if delete_rl4 else ""))


def switch_to_rl4(holder=NATIVE_NODE):
    """Give the rig back to the Epic node (only if it wasn't deleted)."""
    cmds = _cmds()
    out_map, static, rl4 = _outputs(holder)
    if not rl4 or not cmds.objExists(rl4):
        raise RuntimeError("The Epic Rig Logic node is gone; can't switch back.")
    saved = []
    if cmds.attributeQuery("nrlRL4Connections", node=holder, exists=True):
        saved = json.loads(cmds.getAttr(holder + ".nrlRL4Connections") or "[]")
    if not saved:
        raise RuntimeError("No saved Epic connections (the rig was never switched to native).")
    failed = []
    cmds.undoInfo(openChunk=True, chunkName="switch to Epic Rig Logic")
    try:
        for kind, key, drive, value, dst in out_map:
            if cmds.isConnected(drive, dst):
                cmds.disconnectAttr(drive, dst)
        for src, dst in saved:
            try:
                cmds.connectAttr(src, dst, force=True)
            except RuntimeError:
                failed.append(dst)
    finally:
        cmds.undoInfo(closeChunk=True)
    if failed:
        cmds.warning("Could not reconnect %d plugs, e.g. %s" % (len(failed), failed[:3]))
    print("native Rig Logic: face rig driven by the Epic Rig Logic node again.")


def remove_native(holder=NATIVE_NODE, force=False):
    """Delete the native network. Refuses while it drives the rig (switch_to_rl4() first),
    unless force=True."""
    cmds = _cmds()
    if cmds.objExists(holder) and not force:
        out_map = json.loads(cmds.getAttr(holder + ".nrlOutputs") or "[]")
        if any(cmds.isConnected(o[2], o[4]) for o in out_map if cmds.objExists(o[4])):
            raise RuntimeError("The native network drives the face rig. Use switch_to_rl4() first, "
                               "or remove_native(force=True) to delete it anyway.")
    nodes = cmds.ls("nrl_*") or []
    for n in (holder, NATIVE_GROUP):
        if cmds.objExists(n):
            nodes.append(n)
    if nodes:
        cmds.delete(nodes)


def cleanup_epic_nodes(holder=NATIVE_NODE):
    """After switch_to_native(): delete what is left of Epic's plug-ins in the scene, so it opens
    without embeddedRL4 / MayaUERBFPlugin. The neck RBF network (UERBFSolverNode,
    UEPoseBlenderNode) only feeds LOC_expListOutputToRL, which nothing in the Maya face rig reads."""
    cmds = _cmds()
    out_map, static, rl4 = _outputs(holder)
    if not any(cmds.isConnected(o[2], o[4]) for o in out_map if cmds.objExists(o[4])):
        raise RuntimeError("The face isn't driven by the native network yet. Run switch_to_native() first.")
    epic_types = ("embeddedNodeRL4", "UERBFSolverNode", "UEPoseBlenderNode")
    doomed = []
    for t in epic_types:
        try:
            doomed += cmds.ls(type=t) or []
        except RuntimeError:
            pass
    for n in cmds.ls(type="unknown") or []:
        try:
            if cmds.unknownNode(n, q=True, realClassName=True) in epic_types:
                doomed.append(n)
        except RuntimeError:
            pass
    doomed = sorted(set(doomed))
    cmds.undoInfo(openChunk=True, chunkName="remove Epic nodes")
    try:
        for n in doomed:
            if cmds.objExists(n):
                cmds.lockNode(n, lock=False)
                cmds.delete(n)
        if rl4 and not cmds.objExists(rl4):
            cmds.setAttr(holder + ".nrlRL4", "", type="string")
    finally:
        cmds.undoInfo(closeChunk=True)
    removed_plugins = []
    for plugin in cmds.unknownPlugin(q=True, list=True) or []:
        if plugin.split(".")[0] in ("embeddedRL4", "MayaUERBFPlugin"):
            try:
                cmds.unknownPlugin(plugin, remove=True)
                removed_plugins.append(plugin)
            except RuntimeError:
                pass
    print("native Rig Logic: deleted %d Epic nodes%s." % (len(doomed), (", removed plug-in requirements: %s"
                                                               % ", ".join(removed_plugins)) if removed_plugins else ""))
    return doomed


# =========================================================================== window
def show():
    cmds = _cmds()
    win = "MHNativeRLWin"
    if cmds.window(win, exists=True):
        cmds.deleteUI(win)
    cmds.window(win, title="Native facial Rig Logic", widthHeight=(300, 260))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4, columnOffset=("both", 6))
    cmds.text(label="Bake the DNA's facial Rig Logic into native nodes", align="left")
    src = cmds.textFieldButtonGrp(label="DNA / JSON", columnWidth3=(60, 180, 50), buttonLabel="...",
                                  text=_rl4_dna_path((find_rl4_nodes() or [""])[0]) if find_rl4_nodes() else "")
    cmds.textFieldButtonGrp(src, e=True, buttonCommand=lambda *_: _pick(src))
    lod = cmds.intSliderGrp(label="LOD", field=True, minValue=0, maxValue=7, value=0, columnWidth3=(60, 40, 180))
    cmds.button(label="1. Build", height=28,
                command=lambda *_: build(cmds.textFieldButtonGrp(src, q=True, text=True) or None,
                                         cmds.intSliderGrp(lod, q=True, value=True)))
    cmds.button(label="2. Verify against Epic node", height=28, command=lambda *_: verify())
    cmds.button(label="3. Switch rig to native", height=28, command=lambda *_: switch_to_native(False))
    cmds.button(label="Switch + delete Epic node", height=24, command=lambda *_: switch_to_native(True))
    cmds.button(label="4. Remove all Epic nodes (RL4 + neck RBF)", height=24, command=lambda *_: cleanup_epic_nodes())
    cmds.button(label="Remove native network", height=24, command=lambda *_: remove_native())
    cmds.showWindow(win)


def _pick(field):
    cmds = _cmds()
    res = cmds.fileDialog2(fileMode=1, fileFilter="DNA or JSON (*.dna *.json)", caption="DNA or behaviour JSON")
    if res:
        cmds.textFieldButtonGrp(field, e=True, text=res[0])
