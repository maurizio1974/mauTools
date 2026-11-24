"""Graph model: what a board node looks like, read from the scene through OpenMaya 2.

Pure data in, pure data out: describe() turns a node into the dict the QML Node delegate
draws (rows, ports, fields, anchors), wires() lists the connections between board nodes.
No Qt here, so everything is testable in mayapy.

Nodes are identified by Maya UUID strings: stable across renames and save/reopen.
Plugs are identified by their path below the node, e.g. "target[0].targetMatrix".
"""
import os
import re
import xml.etree.ElementTree as ET

import maya.api.OpenMaya as om
import maya.cmds as cmds

from . import theme

# Nodes Maya inserts on its own; the board draws through them.
CONVERSION_TYPES = {"unitConversion", "unitToTimeConversion", "timeToUnitConversion"}

HEADER_H = 28
ROW_H = 20
KID_H = 18
FIELD_H = 24
FILTER_H = 26
FOOT_H = 20
ROWS_PAD_TOP = 4
ROWS_PAD_BOTTOM = 3
MAX_ELEMENTS = 16          # multi elements listed before the rest is summarised
MIN_W, MAX_W = 180, 320
USER_MIN_W, USER_MAX_W = 120, 900   # a width dragged by hand

MODES = ("simple", "connected", "full", "custom")
# Per-node only (node RMB "Show all attributes", the "+N more" foot): every visible attribute.
ALL = "all"
TRS_FIRST = ("translate", "rotate", "scale", "visibility")

# Node category mapping; anything not matched below falls back by kind.
UTILITY_TYPES = {
    "decomposeMatrix", "composeMatrix", "multMatrix", "blendMatrix", "plusMinusAverage",
    "multiplyDivide", "distanceBetween", "condition", "reverse", "clamp", "remapValue",
    "blendColors",
}


# ---------------------------------------------------------------------------- names

def nice_name(name):
    """camelCase attribute name -> Maya-like nice name ("input3D" -> "Input 3D")."""
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
    s = re.sub(r"(?<=[A-Za-z])(?=[0-9])", " ", s)
    return s[:1].upper() + s[1:]


def fmt_num(v):
    s = "%.3f" % v
    s = s.rstrip("0")
    if s.endswith("."):
        s += "0"
    if s in ("-0.0",):
        s = "0.0"
    return s


# ---------------------------------------------------------------------------- nodes

def obj_from_uuid(uuid):
    sl = om.MSelectionList()
    try:
        sl.add(om.MUuid(uuid))
    except (RuntimeError, ValueError):
        return None
    if sl.length() == 0:
        return None
    return sl.getDependNode(0)


def uuid_of(obj):
    return om.MFnDependencyNode(obj).uuid().asString()


def node_path(obj):
    """Shortest unique name usable in cmds (partial DAG path for DAG nodes)."""
    if obj.hasFn(om.MFn.kDagNode):
        return om.MDagPath.getAPathTo(obj).partialPathName()
    return om.MFnDependencyNode(obj).name()


def full_path(obj):
    """Full DAG path ('|grp|node') for DAG nodes, the plain name otherwise."""
    if obj.hasFn(om.MFn.kDagNode):
        return om.MDagPath.getAPathTo(obj).fullPathName()
    return om.MFnDependencyNode(obj).name()


def path_of(uuid):
    obj = obj_from_uuid(uuid)
    return node_path(obj) if obj is not None else None


def uuids_of(names):
    out = []
    for n in names or []:
        u = cmds.ls(n, uuid=True)
        if u:
            out.append(u[0])
    return out


def is_board_candidate(obj):
    """Nodes worth drawing: not Maya's hidden conversion nodes, not default/shared nodes."""
    fn = om.MFnDependencyNode(obj)
    if fn.typeName in CONVERSION_TYPES:
        return False
    if fn.isDefaultNode or fn.isShared:
        return False
    if fn.name().startswith("nodexBoard"):
        return False
    return True


_cat_cache = {}


def is_matrix_type(type_name, inherited=()):
    """DG nodes whose job is matrix math (multMatrix, pickMatrix, mgear_mulMatrix...); render
    plug-in nodes (aiMatrix*) stay shading utilities, DAG nodes keep their own category."""
    if "dagNode" in inherited or type_name.startswith(("ai", "Redshift")):
        return False
    return "Matrix" in type_name or type_name.startswith("matrix")


def category(type_name, is_dag):
    key = (type_name, is_dag)
    if key in _cat_cache:
        return _cat_cache[key]
    try:
        inh = set(cmds.nodeType(type_name, inherited=True, isTypeName=True) or [])
    except RuntimeError:
        inh = set()
    try:
        cls = " ".join(cmds.getClassification(type_name) or [])
    except RuntimeError:
        cls = ""
    if "joint" in inh:
        cat = "Joint"
    elif is_matrix_type(type_name, inh):
        cat = "Matrix"
    elif type_name in UTILITY_TYPES:
        cat = "Utility"
    elif "animCurve" in inh or type_name.startswith("animBlend"):
        cat = "Animation"
    elif "geometryFilter" in inh:
        cat = "Deformer"
    elif "camera" in inh:
        cat = "Camera"
    elif "light" in inh or "renderLight" in inh:
        cat = "Lighting"
    elif type_name == "time":
        cat = "Time"
    elif "dynBase" in inh or "nucleus" in inh:
        cat = "Dynamic"
    elif "cacheBase" in inh or type_name == "cacheFile":
        cat = "Cache"
    elif "containerBase" in inh and "dagNode" not in inh:
        cat = "Asset"
    elif "shape" in inh or "geometryShape" in inh:
        cat = "Geometry"
    elif cls.startswith("shader") or "texture" in cls:
        cat = "Shader"
    elif is_dag:
        cat = "Other"
    else:
        cat = "Utility"
    _cat_cache[key] = cat
    return cat


# ---------------------------------------------------------------------------- attribute types

NT = om.MFnNumericData


def attr_class(attr):
    """Maya Node Editor attribute class (palette key) for an attribute MObject."""
    if attr.hasFn(om.MFn.kCompoundAttribute):
        fn = om.MFnCompoundAttribute(attr)
        kids = [attr_class(fn.child(i)) for i in range(fn.numChildren())]
        if attr.hasFn(om.MFn.kNumericAttribute) and om.MFnNumericAttribute(attr).usedAsColor:
            return "Color"
        if kids and all(k == "Rotation" for k in kids):
            return "Rotation"
        if len(kids) in (2, 3, 4) and all(k in ("Numeric", "Integer") for k in kids):
            ints = all(k == "Integer" for k in kids)
            return {2: "TwoD", 3: "ThreeD", 4: "FourD"}[len(kids)] + ("IntegerVector" if ints else "NumericVector")
        return "MultiAmbiguous"
    if attr.hasFn(om.MFn.kNumericAttribute):
        t = om.MFnNumericAttribute(attr).numericType()
        if t == NT.kBoolean:
            return "Boolean"
        if t in (NT.kInt, NT.kShort, NT.kLong, NT.kByte, NT.kChar, NT.kInt64, NT.kAddr):
            return "Integer"
        return "Numeric"
    if attr.hasFn(om.MFn.kUnitAttribute):
        u = om.MFnUnitAttribute(attr).unitType()
        return "Rotation" if u == om.MFnUnitAttribute.kAngle else "Numeric"
    if attr.hasFn(om.MFn.kEnumAttribute):
        return "Integer"
    if attr.hasFn(om.MFn.kMatrixAttribute) or attr.hasFn(om.MFn.kFloatMatrixAttribute):
        return "Matrix"
    if attr.hasFn(om.MFn.kMessageAttribute):
        return "message"
    if attr.hasFn(om.MFn.kTypedAttribute):
        d = om.MFnTypedAttribute(attr).attrType()
        D = om.MFnData
        if d == D.kString:
            return "String"
        if d == D.kMatrix:
            return "Matrix"
        if d in (D.kMesh, D.kNurbsSurface, D.kSubdSurface, D.kLattice):
            return "InOutMesh"
        if d == D.kNurbsCurve:
            return "Curve"
        if d in (D.kDoubleArray, D.kIntArray, D.kPointArray, D.kVectorArray, D.kStringArray,
                 D.kFloatArray, D.kMatrixArray):
            return "Array"
    return "MultiAmbiguous"


def class_color(cls):
    return theme.attr_color("MultiAmbiguous" if cls == "message" else cls)


def value_kind(attr):
    if attr.hasFn(om.MFn.kCompoundAttribute):
        return ""
    if attr.hasFn(om.MFn.kEnumAttribute):
        return "enum"
    if attr.hasFn(om.MFn.kNumericAttribute):
        t = om.MFnNumericAttribute(attr).numericType()
        return "bool" if t == NT.kBoolean else "num"
    if attr.hasFn(om.MFn.kUnitAttribute):
        return "num"
    return ""


def read_value(plug):
    """UI value of a leaf plug as a string (angles in UI units, as the Channel Box shows)."""
    attr = plug.attribute()
    try:
        if attr.hasFn(om.MFn.kEnumAttribute):
            v = plug.asShort()
            try:
                return om.MFnEnumAttribute(attr).fieldName(v)
            except RuntimeError:
                return str(v)
        if attr.hasFn(om.MFn.kUnitAttribute):
            u = om.MFnUnitAttribute(attr).unitType()
            if u == om.MFnUnitAttribute.kAngle:
                return fmt_num(plug.asMAngle().asUnits(om.MAngle.uiUnit()))
            if u == om.MFnUnitAttribute.kDistance:
                return fmt_num(plug.asMDistance().asUnits(om.MDistance.uiUnit()))
            if u == om.MFnUnitAttribute.kTime:
                return fmt_num(plug.asMTime().asUnits(om.MTime.uiUnit()))
            return fmt_num(plug.asDouble())
        if attr.hasFn(om.MFn.kNumericAttribute):
            t = om.MFnNumericAttribute(attr).numericType()
            if t == NT.kBoolean:
                return "on" if plug.asBool() else "off"
            if t in (NT.kInt, NT.kShort, NT.kLong, NT.kByte, NT.kChar, NT.kInt64):
                return str(plug.asInt())
            return fmt_num(plug.asDouble())
    except RuntimeError:
        return ""
    return ""


def enum_options(attr):
    fn = om.MFnEnumAttribute(attr)
    lo, hi = fn.getMin(), fn.getMax()
    out = []
    for i in range(lo, hi + 1):
        try:
            out.append((i, fn.fieldName(i)))
        except RuntimeError:
            pass
    return out


def plug_path(plug):
    """Path of a plug below its node: 'translateX', 'worldMatrix[0]', 'target[0].targetMatrix'."""
    return plug.partialName(useLongNames=True, includeNonMandatoryIndices=True,
                            includeInstancedIndices=True)


def find_plug(uuid, path):
    obj = obj_from_uuid(uuid)
    if obj is None:
        return None
    sl = om.MSelectionList()
    try:
        sl.add(node_path(obj) + "." + path)
        return sl.getPlug(0)
    except RuntimeError:
        return None


# ---------------------------------------------------------------------------- per-type cache

_type_attrs = {}


def top_attrs(fn):
    """Top-level attributes of a node: [(name, attrObj, hidden, keyable)] in declaration order."""
    type_name = fn.typeName
    count = fn.attributeCount()
    # Static attributes are shared by every node of a type; a node carrying dynamic
    # attributes (count differs from the class) is listed fresh.
    try:
        static = om.MNodeClass(type_name).attributeCount
    except (RuntimeError, AttributeError):
        static = -1
    cacheable = count == static
    if cacheable and type_name in _type_attrs:
        return _type_attrs[type_name]
    out = []
    for i in range(count):
        a = fn.attribute(i)
        fa = om.MFnAttribute(a)
        if not fa.parent.isNull():
            continue
        out.append((fa.name, a, fa.hidden, _keyable(a)))
    if cacheable:
        _type_attrs[type_name] = out
    return out


_nice = {}


def attr_nice(fn, node, attr):
    """Maya's own nice name of an attribute: the type's definition or an addAttr -niceName,
    else Maya's rule for dynamic names ("ik_fk_blender" -> "Ik Fk Blender", "_worldW2" ->
    "World W2"). Static attributes are cached per type; dynamic ones asked every time."""
    fa = om.MFnAttribute(attr)
    key = None if fa.dynamic else (fn.typeName, fa.name)
    hit = _nice.get(key) if key else None
    if hit is None:
        try:
            hit = cmds.attributeQuery(fa.name, node=node, niceName=True) or nice_name(fa.name)
        except (RuntimeError, TypeError):
            hit = nice_name(fa.name)
        if key:
            _nice[key] = hit
    return hit


def aliases(fn):
    """plug path -> alias of a node (blendShape weight[0] -> "open_mouth", any aliasAttr)."""
    try:
        return dict((plug, alias) for alias, plug in fn.getAliasList())
    except RuntimeError:
        return {}


class _Names(object):
    """What labels a node's rows: the node, its path for cmds, its aliases."""
    __slots__ = ("fn", "node", "alias")

    def __init__(self, fn, node):
        self.fn = fn
        self.node = node
        self.alias = aliases(fn)

    def nice(self, attr):
        return attr_nice(self.fn, self.node, attr)


_type_search = {}
_node_search = {}


def _terms_of(fn, node, attr, names):
    fa = om.MFnAttribute(attr)
    names.add(fa.name.lower())
    names.add(fa.shortName.lower())
    names.add(attr_nice(fn, node, attr).lower())


def search_terms(fn, node=None, alias=None):
    """Lower-case names a node is found by: EVERY attribute of the node -- hidden,
    dynamic, plug-in, children of compounds -- by long, short and nice name, and its aliases.
    Static attributes are listed once per type; dynamic ones and aliases per node."""
    node = node or node_path(fn.object())
    alias = aliases(fn) if alias is None else alias
    # Per node, until its attribute count or aliases change (an addAttr, a new target).
    nkey = (fn.uuid().asString(), fn.attributeCount(), tuple(sorted(alias.values())))
    hit = _node_search.get(nkey[0])
    if hit is not None and hit[0] == nkey:
        return hit[1]
    t = fn.typeName
    static = _type_search.get(t)
    if static is None:
        names = set()
        try:
            for a in om.MNodeClass(t).getAttributes():
                _terms_of(fn, node, a, names)
            static = " ".join(sorted(names))
        except (RuntimeError, AttributeError):
            static = ""                    # no class info: every attribute is listed below
        _type_search[t] = static
    extra = set()
    try:
        n_static = om.MNodeClass(t).attributeCount if static else -1
    except (RuntimeError, AttributeError):
        n_static = -1
    if not static:
        for i in range(fn.attributeCount()):
            _terms_of(fn, node, fn.attribute(i), extra)
    elif fn.attributeCount() != n_static:
        for i in range(fn.attributeCount()):
            a = fn.attribute(i)
            if om.MFnAttribute(a).dynamic:
                _terms_of(fn, node, a, extra)
    for a in alias.values():
        extra.add(a.lower())
    s = static + (" " + " ".join(sorted(extra)) if extra else "")
    _node_search[nkey[0]] = (nkey, s)
    return s


def _strict_keyable(attr):
    fa = om.MFnAttribute(attr)
    if fa.keyable:
        return True
    if attr.hasFn(om.MFn.kCompoundAttribute):
        fc = om.MFnCompoundAttribute(attr)
        return any(_strict_keyable(fc.child(i)) for i in range(fc.numChildren()))
    return False


def _cb_first(tops):
    """Channel Box order: keyable attributes with visibility closing them, then the
    non-keyable channel-box ones (joint radius), then everything else."""
    key, vis, cb, rest = [], [], [], []
    for t in tops:
        name, a, hidden, keyable = t
        if not keyable or hidden:
            rest.append(t)
        elif name == "visibility":
            vis.append(t)
        elif _strict_keyable(a):
            key.append(t)
        else:
            cb.append(t)
    return key + vis + cb + rest


_base_names = []


def base_attr_names():
    """Attributes every DG node has (caching, nodeState, frozen ...)."""
    if not _base_names:
        try:
            for a in om.MNodeClass("node").getAttributes():
                _base_names.append(om.MFnAttribute(a).name)
        except (RuntimeError, AttributeError):
            _base_names.extend(["message", "caching", "frozen", "isHistoricallyInteresting",
                                "nodeState", "binMembership"])
    return _base_names


def _keyable(attr):
    """Keyable or in the channel box; a compound counts when a child does (translate)."""
    fa = om.MFnAttribute(attr)
    if fa.keyable or fa.channelBox:
        return True
    if attr.hasFn(om.MFn.kCompoundAttribute):
        fc = om.MFnCompoundAttribute(attr)
        return any(_keyable(fc.child(i)) for i in range(fc.numChildren()))
    return False


def port_sides(attr, is_dag):
    """(input port, output port) for an attribute.

    DAG nodes: readable + writable attributes get a port on both sides (translate). DG
    compute nodes: a writable attribute is an input, a read-only one an output, which is how
    their attributes are meant to be used (input1 -> output).
    """
    fa = om.MFnAttribute(attr)
    has_in = fa.writable
    has_out = fa.readable and (not fa.writable or is_dag)
    return bool(has_in), bool(has_out)


# ---------------------------------------------------------------------------- display modes

_affected = {}


def _keyable_input(attr):
    """Keyable, or a compound with a keyable direct child (translate). Deeper descendants
    do not count: blendShape's inputTarget is an output in Maya's Full mode."""
    if om.MFnAttribute(attr).keyable:
        return True
    if attr.hasFn(om.MFn.kCompoundAttribute):
        fc = om.MFnCompoundAttribute(attr)
        return any(om.MFnAttribute(fc.child(i)).keyable for i in range(fc.numChildren()))
    return False


def _computed(fn, a, fa):
    """True when a visible attribute affects `a` (an output Maya computes; blendShape's
    targetParentVisibility, driven only by the hidden parentDirectory, is not one).
    Static attributes are cached per type; dynamic ones are asked every time."""
    key = None if fa.dynamic else (fn.typeName, fa.name)
    hit = _affected.get(key) if key else None
    if hit is None:
        try:
            hit = any(not om.MFnAttribute(x).hidden for x in fn.getAffectingAttributes(a))
        except RuntimeError:
            hit = False
        if key:
            _affected[key] = hit
    return hit


def maya_full(fn, tops, conn_tops):
    """The tops Maya's Full mode ("all interesting attributes") shows, in Maya's order.

    conn_tops: top name -> connection bits (1 input, 2 output) of it and its descendants.
    The set: keyable inputs, visible computed outputs, visible dynamic attributes, and any
    connected attribute, hidden included. The order (measured against Maya's own Node
    Editor on a set of real nodes) goes by the side Maya draws the ports
    on: translate / rotate / scale / visibility first; then output-only rows (computed or
    read-only attributes, and static ones connected only as a source: rotateOrder,
    message); then rows with ports on both sides (dynamic, keyable, connected both ways);
    then input-only rows (connected only as a destination: rotatePivot). Each group after
    the first is sorted by long name, case-sensitively ("HeadSupport" < "ik_fk_blender").
    """
    first = {}
    outs, both, ins = [], [], []
    for t in tops:
        name, a, hidden = t[0], t[1], t[2]
        fa = om.MFnAttribute(a)
        keyable = not hidden and _keyable_input(a)
        dynamic = fa.dynamic and not hidden
        computed = not hidden and not keyable and _computed(fn, a, fa)
        bits = conn_tops.get(name, 0) & 3
        if not (keyable or dynamic or computed or bits):
            continue
        if name in TRS_FIRST and keyable:
            first[name] = t
        elif computed or (not fa.writable and not dynamic):
            outs.append(t)
        elif keyable or dynamic or bits == 3 or not bits:
            both.append(t)
        elif bits == 2:
            outs.append(t)
        else:
            ins.append(t)
    out = [first[n] for n in TRS_FIRST if n in first]
    for g in (outs, both, ins):
        out.extend(sorted(g, key=lambda t: t[0]))
    return out


_templates = {}


def template_dirs():
    """Where Maya looks for Node Editor templates, in its order."""
    dirs = []
    try:
        dirs.append(os.path.join(cmds.internalVar(userPrefDir=True), "viewTemplates"))
    except RuntimeError:
        pass
    for p in (os.environ.get("MAYA_CUSTOM_TEMPLATE_PATH") or "").split(os.pathsep):
        if p.strip():
            dirs.append(p.strip())
    loc = os.environ.get("MAYA_LOCATION")
    if loc:
        dirs.append(os.path.join(loc, "scripts", "NETemplates"))
    return dirs


def _read_template(path):
    """Attribute names of the NEDefault view of a template file, in file order."""
    try:
        with open(path, "rb") as f:
            # Maya's own files open with a blank line before <?xml ...?>.
            root = ET.fromstring(f.read().lstrip(b"\xef\xbb\xbf \t\r\n"))
    except (ET.ParseError, OSError):
        return None
    for v in root.iter("view"):
        if v.get("name") == "NEDefault":
            return [p.get("name") for p in v.iter("property") if p.get("name")]
    return None


def template_attrs(type_name, node_name=""):
    """Names in Maya's custom-mode template for a node, or None when it has none.

    A node-specific NE<type>.<name>Template.xml wins over NE<type>Template.xml; the first
    directory holding a file wins. No inheritance: a joint does not take transform's."""
    short = node_name.rsplit(":", 1)[-1] if node_name else ""
    files = (["NE%s.%sTemplate.xml" % (type_name, short)] if short else []) + \
            ["NE%sTemplate.xml" % type_name]
    for f in files:
        key = f
        if key not in _templates:
            _templates[key] = None
            for d in template_dirs():
                p = os.path.join(d, f)
                if os.path.isfile(p):
                    _templates[key] = _read_template(p)
                    break
        if _templates[key] is not None:
            return _templates[key]
    return None


def custom_tops(fn, tops, conn_tops):
    """Custom mode: Maya's template view plus every connected attribute (the user's choice
    over Maya's template-only); no template -> Full."""
    names = template_attrs(fn.typeName, fn.name())
    if names is None:
        return maya_full(fn, tops, conn_tops)
    by_name = dict((t[0], t) for t in tops)
    out, seen = [], set()
    for n in names:
        if n not in by_name and fn.hasAttribute(n):
            # A template may name a child (translateX): show its top-level attribute.
            fa = om.MFnAttribute(fn.attribute(n))
            while not fa.parent.isNull():
                fa = om.MFnAttribute(fa.parent)
            n = fa.name
        if n in by_name and n not in seen:
            seen.add(n)
            out.append(by_name[n])
    out.extend(sorted((t for t in tops if t[0] in conn_tops and t[0] not in seen),
                      key=lambda t: t[0]))
    return out


# ---------------------------------------------------------------------------- rows

class _P(object):
    """One plug in a row tree."""
    __slots__ = ("plug", "path", "label", "attr", "cls", "kids", "parent", "slot", "readable",
                 "writable", "in_conn", "out_conn", "desc_conn", "hidden", "keyable", "more")

    def __init__(self, plug, label, parent=None, slot=False):
        self.plug = plug
        self.path = plug_path(plug)
        self.label = label
        self.attr = plug.attribute()
        fa = om.MFnAttribute(self.attr)
        self.cls = attr_class(self.attr)
        self.readable = fa.readable
        self.writable = fa.writable
        self.hidden = fa.hidden
        self.keyable = fa.keyable or fa.channelBox
        self.kids = []
        self.parent = parent
        self.slot = slot
        self.in_conn = False
        self.out_conn = False
        self.desc_conn = False
        self.more = 0


def _label(names, plug, label):
    """an aliased plug is labelled by its alias (blendShape weight[3] -> its target name)."""
    if names is not None and names.alias:
        a = names.alias.get(plug_path(plug))
        if a:
            return a
    return label


def _build_tree(plug, label, conn, parent=None, full=False, names=None):
    """Row tree below a plug. Multi attributes expand straight into their elements.
    names: a _Names for Maya's nice names and aliases (None: the plain camelCase split)."""
    nodes = []
    if plug.isArray:
        idx = list(plug.getExistingArrayAttributeIndices())
        shown = idx
        if not full:
            shown = [i for i in idx if _elem_connected(plug, i, conn)]
        more = max(0, len(shown) - MAX_ELEMENTS)
        for i in shown[:MAX_ELEMENTS]:
            el = plug.elementByLogicalIndex(i)
            nodes.extend(_build_tree(el, _label(names, el, "%s [%d]" % (label, i)), conn, parent,
                                     full, names))
        fa = om.MFnAttribute(plug.attribute())
        if fa.writable and not fa.hidden:
            nxt = (max(idx) + 1) if idx else 0
            el = plug.elementByLogicalIndex(nxt)
            s = _P(el, "%s [%d]" % (label, nxt), parent, slot=True)
            s.more = more
            nodes.append(s)
        elif not idx and full:
            # An output multi with no element yet (parentMatrix before it is evaluated):
            # one row for the multi itself, as Maya shows it; wires climb to it.
            nodes.append(_P(plug, label, parent))
        return nodes
    p = _P(plug, label, parent)
    path = p.path
    p.in_conn = conn.get(path, 0) & 1 != 0
    p.out_conn = conn.get(path, 0) & 2 != 0
    p.desc_conn = conn.get(path, 0) & 4 != 0
    if plug.isCompound:
        for k in range(plug.numChildren()):
            c = plug.child(k)
            ca = c.attribute()
            lab = names.nice(ca) if names is not None else nice_name(om.MFnAttribute(ca).name)
            p.kids.extend(_build_tree(c, _label(names, c, lab), conn, p, full, names))
    return [p]


def _elem_connected(plug, i, conn):
    prefix = "%s[%d]" % (plug_path(plug), i)
    for k in conn:
        if k == prefix or k.startswith(prefix + "."):
            return True
    return False


def _connection_map(fn):
    """path -> bits: 1 input connected, 2 output connected, 4 a descendant is connected."""
    conn = {}
    for p in fn.getConnections():
        bits = (1 if p.isDestination else 0) | (2 if p.isSource else 0)
        if not bits:
            continue
        path = plug_path(p)
        conn[path] = conn.get(path, 0) | bits
        # Mark ancestors: compound parents and array parents.
        q = p
        while True:
            if q.isChild:
                q = q.parent()
            elif q.isElement:
                q = q.array()
            else:
                break
            ap = plug_path(q)
            conn[ap] = conn.get(ap, 0) | 4
    return conn


def _top_of(path):
    return re.split(r"[.\[]", path, 1)[0]


class NodeView(object):
    """UI state of one node on one board tab (kept by the bridge, not by the scene)."""

    def __init__(self, mode=None, expanded=None, filter_text="", filter_open=False, pinned=None):
        self.mode = mode                      # None = follow the board's mode
        self.expanded = set(expanded or [])   # plug paths opened with the chevron
        self.filter_text = filter_text
        self.filter_open = filter_open
        self.pinned = set(pinned or [])


def describe(uuid, view=None, board_mode="connected", query=""):
    """Everything the QML Node delegate draws for one node, as plain data.

    query: the board's find field. A node whose attributes match it reveals the
    matching rows on top of its normal ones, the match underlined.
    """
    view = view or NodeView()
    obj = obj_from_uuid(uuid)
    if obj is None:
        return None
    fn = om.MFnDependencyNode(obj)
    type_name = fn.typeName
    is_dag = obj.hasFn(om.MFn.kDagNode)
    mode = view.mode or board_mode
    q = (view.filter_text or "").strip().lower()
    gq = (query or "").strip().lower()
    conn = _connection_map(fn)
    path = node_path(obj)
    names = _Names(fn, path)
    terms = search_terms(fn, path, names.alias)
    reveal = bool(gq) and not q and gq in terms

    info = {
        "id": uuid,
        "name": fn.name(),
        "path": path,
        "type": type_name,
        "category": category(type_name, is_dag),
        "mode": mode,
        "filterOpen": bool(view.filter_open),
        "filterText": view.filter_text or "",
        "dead": False,
        "conv": type_name in CONVERSION_TYPES,
    }
    info["color"] = theme.node_color(info["category"])
    info["hasIn"] = any(v & 1 for v in conn.values())
    info["hasOut"] = any(v & 2 for v in conn.values())

    tops = top_attrs(fn)
    conn_tops = {}
    for k, bits in conn.items():
        t = _top_of(k)
        conn_tops[t] = conn_tops.get(t, 0) | (bits & 3)
    picked = set()
    rule = mode
    if mode == "custom" and template_attrs(type_name, fn.name()) is None:
        rule = "full"                      # no template -> Full, as Maya
    if rule == ALL:
        tops = _cb_first(tops)
    elif rule in ("full", "custom"):
        lead = (maya_full if rule == "full" else custom_tops)(fn, tops, conn_tops)
        picked = set(t[0] for t in lead)
        tops = lead + [t for t in tops if t[0] not in picked]
    full = rule in ("full", ALL) or bool(q)
    rows = []
    anchors = {}
    parents = {}
    hidden_tops = 0

    base = mode != "simple" or bool(q) or view.filter_open
    if base or reveal:
        if view.filter_open:
            rows.append({"kind": "filter", "key": "__filter__", "h": FILTER_H, "depth": 0})
        wanted = set()
        if base:
            wanted = set(conn_tops) | picked
            wanted |= set(_top_of(k) for k in view.expanded)
            wanted |= set(_top_of(k) for k in view.pinned)
        enum_rows, port_rows = [], []
        for name, a, hidden, keyable in tops:
            is_enum = a.hasFn(om.MFn.kEnumAttribute)
            show_top = name in wanted
            # Show all attributes: every visible one. A node filter looks through every
            # attribute, hidden ones too; _emit keeps the matching rows.
            if base and not show_top and ((mode == ALL and not hidden) or q):
                show_top = True
            # Mode switches of compute nodes (operation, interpolation ...) are shown as fields;
            # DAG nodes carry dozens of display enums, those stay in full mode.
            if (base and not show_top and mode == "connected" and is_enum and not is_dag
                    and not hidden and name not in base_attr_names()):
                show_top = True
            trees = None
            if not show_top and not reveal:
                if not hidden:
                    hidden_tops += 1
                continue
            plug = fn.findPlug(a, False)
            label = _label(names, plug, names.nice(a))
            if not show_top and reveal:
                # The find field reaches any attribute: hidden ones, every multi
                # element (an alias names one), not only the connected ones.
                trees = [t for t in _build_tree(plug, label, conn, None, True, names)
                         if _matches(t, gq)]
                show_top = bool(trees)
            if not show_top:
                if not hidden:
                    hidden_tops += 1
                continue
            if trees is None:
                trees = _build_tree(plug, label, conn, None, full, names)
                if reveal and plug.isArray and not full:
                    # A shown multi lists its connected elements; a match among the others
                    # (an alias: a blendShape target) joins them, before the free slot.
                    have = set(t.path for t in trees)
                    more = [t for t in _build_tree(plug, label, conn, None, True, names)
                            if t.path not in have and not t.slot and _matches(t, gq)]
                    if more:
                        slot = [t for t in trees if t.slot]
                        trees = [t for t in trees if not t.slot] + more + slot
            for t in trees:
                # Fields first in connected mode only; full / custom keep the Channel Box order,
                # or a DAG node opens with its display enums (View Mode, UI Treatment ...).
                field = mode == "connected" and is_enum and not t.in_conn and not t.out_conn
                target = enum_rows if field else port_rows
                _emit(t, 0, view, mode, q, target, parents, is_dag, gq if reveal else "")
        body = enum_rows + port_rows
        if q and not body:
            body.append({"kind": "nomatch", "key": "__nomatch__", "h": ROW_H, "depth": 0,
                         "label": 'No attributes match "%s"' % view.filter_text})
        rows.extend(body)

    y = HEADER_H + (ROWS_PAD_TOP if rows else 0)
    for r in rows:
        r["y"] = y
        y += r["h"]
        if r["kind"] in ("port", "enum", "slot"):
            anchors[r["key"]] = r["y"] + r["h"] / 2.0
    foot = ""
    if rows:
        y += ROWS_PAD_BOTTOM
        if not q and mode != "simple":
            if mode == ALL:
                foot = "Show fewer attributes"
            elif hidden_tops:
                foot = "+ %d more attribute%s" % (hidden_tops, "s" if hidden_tops > 1 else "")
        if foot:
            y += FOOT_H
    info["rows"] = rows
    info["foot"] = foot
    info["height"] = y if rows else HEADER_H
    info["anchors"] = anchors
    info["parents"] = parents
    info["width"] = _width(info)
    info["search"] = " ".join([fn.name().lower(), type_name.lower(), terms])
    return info


def _matches(p, q):
    if not q:
        return True
    if q in p.label.lower() or q in p.path.lower():
        return True
    return any(_matches(k, q) for k in p.kids)


def _hit(p, q):
    """Row label as styled text with the match underlined; "" when the row does not match."""
    if not q:
        return ""
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lab = p.label
    i = lab.lower().find(q)
    if i >= 0:
        return esc(lab[:i]) + "<u>" + esc(lab[i:i + len(q)]) + "</u>" + esc(lab[i + len(q):])
    if q in p.path.lower():
        return "<u>" + esc(lab) + "</u>"
    return ""


def _emit(p, depth, view, mode, q, out, parents, is_dag, gq=""):
    """Flatten a row tree into rows, applying the display rules.

    gq: the global find query; kids matching it are shown although folded.
    """
    parents[p.path] = p.parent.path if p.parent is not None else ""
    for k in p.kids:
        _register(k, parents)
    if q and not _matches(p, q):
        return
    if p.slot:
        if mode == "simple":
            return
        out.append(_row(p, depth, view, mode, is_dag, slot=True))
        return
    out.append(_row(p, depth, view, mode, is_dag, hq=q or gq))
    if not p.kids:
        return
    opened = p.path in view.expanded
    for k in p.kids:
        if q:
            if _matches(k, q):
                _emit(k, depth + 1, view, mode, q, out, parents, is_dag)
        elif (opened or k.in_conn or k.out_conn or k.desc_conn or k.path in view.pinned
              or (gq and _matches(k, gq))):
            _emit(k, depth + 1, view, mode, q, out, parents, is_dag, gq)


def _register(p, parents):
    parents[p.path] = p.parent.path if p.parent is not None else ""
    for k in p.kids:
        _register(k, parents)


def _row(p, depth, view, mode, is_dag, slot=False, hq=""):
    is_enum = p.attr.hasFn(om.MFn.kEnumAttribute)
    has_in, has_out = port_sides(p.attr, is_dag)
    if slot:
        has_in, has_out = True, False
    r = {
        "kind": "slot" if slot else ("enum" if is_enum and not p.in_conn else "port"),
        "key": p.path,
        "label": p.label,
        "depth": depth,
        "h": FIELD_H if (is_enum and not p.in_conn and not slot) else (KID_H if depth else ROW_H),
        "inPort": bool(has_in),
        "outPort": bool(has_out),
        "inConn": p.in_conn,
        "outConn": p.out_conn,
        "cls": p.cls,
        "compound": bool(p.kids),
        "color": class_color(p.cls),
        "chev": (2 if p.path in view.expanded else 1) if p.kids else 0,
        "valueKind": "",
        "value": "",
        "more": p.more,
        "hit": "" if slot else _hit(p, hq),
    }
    vk = value_kind(p.attr)
    show_val = (has_in and not p.in_conn and not p.kids and not slot and vk and
                (depth > 0 or mode in ("full", "custom", ALL) or p.path in view.pinned or is_enum))
    if show_val:
        r["valueKind"] = vk
        r["value"] = read_value(p.plug)
    return r


def _width(info):
    w = 8 + 20 + 7 + len(info["name"]) * 7.0 + 48
    for r in info["rows"]:
        if r["kind"] in ("filter", "nomatch"):
            continue
        rw = 24 + r["depth"] * 14 + len(r.get("label", "")) * 6.2 + 14
        if r.get("valueKind"):
            rw += 70 if r["valueKind"] != "enum" else max(70, 34 + len(r["value"]) * 6.4)
        w = max(w, rw)
    return int(max(MIN_W, min(MAX_W, w)))


def anchor_y(info, path):
    """Y (node space) where a wire meets `path`: its row, else the nearest shown ancestor."""
    if info is None:
        return HEADER_H / 2.0
    anchors = info["anchors"]
    parents = info["parents"]
    p = path
    seen = 0
    while p and seen < 16:
        if p in anchors:
            return anchors[p]
        nxt = parents.get(p)
        if nxt is None:
            # Unknown plug (not built): climb the path string.
            m = re.match(r"^(.*)(\.[^.\[\]]+|\[\d+\])$", p)
            nxt = m.group(1) if m else ""
        p = nxt
        seen += 1
    return HEADER_H / 2.0


# ---------------------------------------------------------------------------- wires

def _wire_into(p, u, on_board, infos):
    """The wire ending at destination plug `p` of board node `u`, or None."""
    src = p.source()
    if src.isNull:
        return None
    raw = p.sourceWithConversion()
    uc = (not raw.isNull) and raw.node() != src.node()
    conv = uuid_of(raw.node()) if uc else ""
    if uc and conv in on_board:
        # The conversion node is expanded onto the board: src -> uc -> dst.
        src, uc, conv = raw, False, ""
    su = uuid_of(src.node())
    if su not in on_board:
        return None
    sp, dp = plug_path(src), plug_path(p)
    cls = attr_class(src.attribute())
    w = {
        "id": "%s|%s>%s|%s" % (su, sp, u, dp),
        "src": su, "srcPlug": sp, "dst": u, "dstPlug": dp,
        "uc": bool(uc),
        "conv": conv,
        "cls": cls,
        "compound": bool(src.isCompound),
        "color": theme.attr_color("UnitConversion") if uc else class_color(cls),
    }
    if infos is not None:
        w["srcY"] = anchor_y(infos.get(su), sp)
        w["dstY"] = anchor_y(infos.get(u), dp)
    return w


def wires(uuids, infos=None):
    """Connections between board nodes: [{id, src, srcPlug, dst, dstPlug, color, uc, ...}]."""
    on_board = set(uuids)
    out = []
    for u in uuids:
        obj = obj_from_uuid(u)
        if obj is None:
            continue
        for p in om.MFnDependencyNode(obj).getConnections():
            if p.isDestination:
                w = _wire_into(p, u, on_board, infos)
                if w is not None:
                    out.append(w)
    return out


def wires_touching(touched, uuids, infos=None):
    """The wires of `wires(uuids)` with an end on a node of `touched`, found from those
    nodes alone (their inputs, and the inputs their outputs feed), so a change on a few
    nodes of a big board does not walk every connection."""
    on_board = set(uuids)
    out = {}
    for u in touched:
        if u not in on_board:
            continue
        obj = obj_from_uuid(u)
        if obj is None:
            continue
        for p in om.MFnDependencyNode(obj).getConnections():
            ends = []
            if p.isDestination:
                ends.append((p, u))
            if p.isSource:
                # destinations() looks through conversion nodes, ...WithConversions() stops
                # at them: the second one finds an expanded (on-board) conversion node.
                for d in list(p.destinations()) + list(p.destinationsWithConversions()):
                    du = uuid_of(d.node())
                    if du in on_board:
                        ends.append((d, du))
            for dp, du in ends:
                w = _wire_into(dp, du, on_board, infos)
                if w is not None and (w["src"] in touched or w["dst"] in touched):
                    out[w["id"]] = w
    return list(out.values())


# ---------------------------------------------------------------------------- traversal

def neighbours(uuid, direction):
    """UUIDs directly upstream ('up') or downstream ('down') of a node, through conversions."""
    obj = obj_from_uuid(uuid)
    if obj is None:
        return []
    out = []
    for p in om.MFnDependencyNode(obj).getConnections():
        others = []
        if direction in ("up", "both") and p.isDestination:
            s = p.source()
            if not s.isNull:
                others.append(s.node())
        if direction in ("down", "both") and p.isSource:
            others.extend(d.node() for d in p.destinations())
        for o in others:
            if is_board_candidate(o):
                out.append(uuid_of(o))
    return out


def connections_between(a, b, limit=10000):
    """Union of directed connection paths between two nodes, in both directions; no scene edits."""
    endpoints, adjacency = {a, b}, {}
    if a == b or any(obj_from_uuid(u) is None for u in endpoints):
        return []

    def links(uid):
        if uid in adjacency:
            return adjacency[uid]
        if len(adjacency) >= limit:
            raise ValueError('Connection search exceeded %d nodes; choose closer endpoints' % limit)
        obj = obj_from_uuid(uid)
        up, down = [], []
        if obj is not None:
            for plug in om.MFnDependencyNode(obj).getConnections():
                if plug.attribute().hasFn(om.MFn.kMessageAttribute):
                    continue
                top = plug_path(plug).split('.', 1)[0].split('[', 1)[0]
                if obj.hasFn(om.MFn.kSet) and top in ('dagSetMembers', 'dnSetMembers'):
                    continue
                if plug.isDestination:
                    source = plug.sourceWithConversion()
                    if not source.isNull and not source.attribute().hasFn(om.MFn.kMessageAttribute):
                        up.append(source.node())
                for dest in plug.connectedTo(False, True):
                    if dest.attribute().hasFn(om.MFn.kMessageAttribute):
                        continue
                    top = plug_path(dest).split('.', 1)[0].split('[', 1)[0]
                    if dest.node().hasFn(om.MFn.kSet) and top in ('dagSetMembers', 'dnSetMembers'):
                        continue
                    down.append(dest.node())
        def ids(objects):
            return list(dict.fromkeys(uuid_of(o) for o in objects
                        if uuid_of(o) in endpoints or not om.MFnDependencyNode(o).isDefaultNode))
        adjacency[uid] = ids(up), ids(down)
        return adjacency[uid]

    def reachable(start, side):
        seen, queue = {start}, [start]
        for uid in queue:
            for neighbour in links(uid)[side]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        return seen

    forward, reverse = reachable(a, 1), reachable(b, 1)
    found = set()
    if b in forward:
        found.update(forward & reachable(b, 0))
    if a in reverse:
        found.update(reverse & reachable(a, 0))
    return [u for u in (a, b) if u in found] + sorted(found - endpoints)


def traverse(seeds, direction, depth, limit=2000, stop=None):
    """Seeds plus everything within `depth` hops (None = unlimited), nearest first.

    Breadth-first, so cutting the list keeps the network closest to the seeds; the walk stops
    as soon as `limit` nodes are found (None = no limit) instead of walking a whole rig."""
    found = list(dict.fromkeys(seeds))
    seen = set(found)
    front = list(found)
    d = 0
    while front and (depth is None or d < depth):
        nxt = []
        for u in front:
            for v in neighbours(u, direction):
                if v not in seen:
                    seen.add(v)
                    if stop is not None and stop(v):
                        continue        # neither shown nor walked through (Display filter)
                    found.append(v)
                    nxt.append(v)
                    if limit is not None and len(found) >= limit:
                        return found
        front = nxt
        d += 1
    return found


# ---------------------------------------------------------------------------- shapes (Display group)

SHADING_TYPES = {"shadingEngine", "materialInfo", "partition", "groupId"}


def is_shading(uuid):
    """Shading network members, left out by "Graph all shapes except shading networks"."""
    obj = obj_from_uuid(uuid)
    if obj is None:
        return False
    t = om.MFnDependencyNode(obj).typeName
    if t in SHADING_TYPES:
        return True
    try:
        cls = ":".join(cmds.getClassification(t) or [])
    except RuntimeError:
        return False
    return any(part.startswith(("shader/", "texture/")) for part in cls.split(":"))


def shapes_of(uuid):
    """Non-intermediate shapes directly under a transform, as Maya graphs them with it."""
    obj = obj_from_uuid(uuid)
    if obj is None or not obj.hasFn(om.MFn.kTransform):
        return []
    path = om.MDagPath.getAPathTo(obj)
    out = []
    for i in range(path.childCount()):
        c = path.child(i)
        if c.hasFn(om.MFn.kShape) and not om.MFnDagNode(c).isIntermediateObject:
            out.append(uuid_of(c))
    return out


def transform_of(uuid):
    obj = obj_from_uuid(uuid)
    if obj is None or not obj.hasFn(om.MFn.kShape):
        return uuid
    parent = om.MFnDagNode(obj).parent(0)
    return uuid_of(parent) if parent.hasFn(om.MFn.kTransform) else uuid


def apply_shape_filter(uuids, mode, keep=()):
    """Maya's Display group: "all" graphs each transform with its shapes, "except" does the same
    but drops shading networks (except nodes in `keep`, asked for by name), "none" shows the
    transform in place of each shape."""
    out = []
    for u in uuids:
        if mode == "none":
            out.append(transform_of(u))
            continue
        if mode == "except" and u not in keep and is_shading(u):
            continue
        out.append(u)
        out.extend(shapes_of(u))
    return [u for u in dict.fromkeys(out)]


# ---------------------------------------------------------------------------- tooltip

def plug_info(uuid, path):
    """Tooltip content for a port."""
    plug = find_plug(uuid, path)
    if plug is None:
        return None
    attr = plug.attribute()
    fa = om.MFnAttribute(attr)
    obj = plug.node()
    cls = attr_class(attr)
    has_in, has_out = port_sides(attr, obj.hasFn(om.MFn.kDagNode))
    io = "input and output" if (has_in and has_out) else ("input" if has_in else "output")
    fn = om.MFnDependencyNode(obj)
    nice = aliases(fn).get(path) or attr_nice(fn, node_path(obj), attr)
    info = {
        "nice": nice,
        "long": fn.name() + "." + path,
        "cls": cls,
        "color": class_color(cls),
        "io": io,
        "value": "",
        "source": "",
        "via": "",
    }
    vk = value_kind(attr)
    if vk:
        info["value"] = read_value(plug)
    elif plug.isCompound and not plug.isArray:
        vals = []
        for k in range(plug.numChildren()):
            c = plug.child(k)
            if value_kind(c.attribute()) and not c.isCompound:
                vals.append(read_value(c))
        if vals:
            info["value"] = "(" + ", ".join(vals) + ")"
    elif cls == "Matrix":
        info["value"] = "4x4 matrix"
    elif cls == "message":
        info["value"] = "none"
    if plug.isDestination:
        src = plug.source()
        raw = plug.sourceWithConversion()
        if not src.isNull:
            info["source"] = om.MFnDependencyNode(src.node()).name() + "." + plug_path(src)
            if not raw.isNull and raw.node() != src.node():
                info["via"] = om.MFnDependencyNode(raw.node()).typeName
    return info
