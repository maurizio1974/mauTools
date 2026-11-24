"""Scene edits made from the board. Every public call is one undo chunk.

Plugs are addressed as plain "node.attr" strings (node may be a DAG path), so the module
works from tests and from the command line exactly as from the panel.
"""
import functools
import re

import maya.api.OpenMaya as om
import maya.cmds as cmds

from . import model

_depth = [0]


def undo_chunk(label):
    """Only the outermost decorated call opens a chunk, so ops can call each other."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            outer = _depth[0] == 0
            if outer:
                cmds.undoInfo(openChunk=True, chunkName="NodeX: " + label)
            _depth[0] += 1
            try:
                return fn(*args, **kwargs)
            finally:
                _depth[0] -= 1
                if outer:
                    cmds.undoInfo(closeChunk=True)
        return wrapper
    return deco


# ---------------------------------------------------------------------------- helpers

def split(plug):
    node, attr = plug.split(".", 1)
    return node, attr


def plug_exists(plug):
    sl = om.MSelectionList()
    try:
        sl.add(plug)
        sl.getPlug(0)
        return True
    except (RuntimeError, TypeError):
        return False


def _mplug(plug):
    sl = om.MSelectionList()
    sl.add(plug)
    return sl.getPlug(0)


def source_of(plug, skip_conversion=True):
    """'node.attr' feeding `plug`, or None."""
    src = cmds.listConnections(plug, source=True, destination=False, plugs=True,
                               skipConversionNodes=skip_conversion) or []
    return _long(src[0]) if src else None


def _long(plug):
    """Canonical 'node.longAttrPath' for any plug string."""
    p = _mplug(plug)
    obj = p.node()
    return model.node_path(obj) + "." + model.plug_path(p)


def _is_readable(plug):
    return om.MFnAttribute(_mplug(plug).attribute()).readable


def _is_writable(plug):
    return om.MFnAttribute(_mplug(plug).attribute()).writable


def _node_of(plug):
    return _mplug(plug).node()


# ---------------------------------------------------------------------------- connect / disconnect

@undo_chunk("connect")
def connect(src, dst):
    """connectAttr -f. Returns '' or the error text Maya gave."""
    try:
        cmds.connectAttr(src, dst, force=True)
    except RuntimeError as e:
        return str(e).strip()
    return ""


@undo_chunk("disconnect")
def disconnect_inputs(dsts):
    """Cut whatever feeds each destination plug, conversion nodes included."""
    cut = []
    for dst in dsts:
        raw = source_of(dst, skip_conversion=False)
        if not raw:
            continue
        cmds.disconnectAttr(raw, dst)
        conv = split(raw)[0]
        if cmds.objExists(conv) and cmds.nodeType(conv) in model.CONVERSION_TYPES:
            if not cmds.listConnections(conv + ".output", source=False, destination=True):
                _drop_conversion(conv)
        cut.append(dst)
    return cut


@undo_chunk("reroute")
def reroute_input(old_dst, new_dst):
    """Move the connection feeding old_dst onto new_dst (drag a wire off an input)."""
    src = source_of(old_dst)
    if not src:
        return "nothing feeds " + old_dst
    disconnect_inputs([old_dst])
    if new_dst:
        return connect(src, new_dst)
    return ""


# ---------------------------------------------------------------------------- transfer / swap

def _inputs_of(node):
    """[(node.attr, source)] for every connected input of a node, conversions skipped."""
    pairs = cmds.listConnections(node, source=True, destination=False, connections=True,
                                 plugs=True, skipConversionNodes=True) or []
    return [(_long(pairs[i]), pairs[i + 1]) for i in range(0, len(pairs), 2)]


def _outputs_of(node):
    pairs = cmds.listConnections(node, source=False, destination=True, connections=True,
                                 plugs=True, skipConversionNodes=True) or []
    return [(_long(pairs[i]), pairs[i + 1]) for i in range(0, len(pairs), 2)]


def _same_node(a, b):
    return cmds.ls(a, long=True) == cmds.ls(b, long=True)


@undo_chunk("transfer connections")
def transfer(src_node, targets, which="all"):
    """Move connections from src_node to targets, matching attributes by name.

    which: 'in' | 'out' | 'all'. Inputs are given to every target; an output can only feed
    one destination, so outputs go to the first target. src_node ends up disconnected on
    the moved side. Returns {'moved': [(old, new)], 'skipped': [(plug, reason)]}.
    """
    report = {"moved": [], "skipped": []}
    targets = [t for t in targets if not _same_node(t, src_node)]
    if not targets:
        return report
    if which in ("in", "all"):
        for plug, src in _inputs_of(src_node):
            attr = split(plug)[1]
            if any(_same_node(split(src)[0], t) for t in targets):
                report["skipped"].append((plug, "comes from a target"))
                continue
            done = False
            for t in targets:
                new = t + "." + attr
                if not plug_exists(new) or not _is_writable(new):
                    report["skipped"].append((plug, "no %s on %s" % (attr, t)))
                    continue
                err = connect(src, new)
                if err:
                    report["skipped"].append((plug, err))
                    continue
                report["moved"].append((plug, new))
                done = True
            if done:
                disconnect_inputs([plug])
    if which in ("out", "all"):
        t = targets[0]
        for plug, dst in _outputs_of(src_node):
            attr = split(plug)[1]
            if any(_same_node(split(dst)[0], x) for x in targets):
                report["skipped"].append((plug, "feeds a target"))
                continue
            new = t + "." + attr
            if not plug_exists(new) or not _is_readable(new):
                report["skipped"].append((plug, "no %s on %s" % (attr, t)))
                continue
            err = connect(new, dst)
            if err:
                report["skipped"].append((plug, err))
                continue
            report["moved"].append((plug, new))
        _prune_conversions(src_node)
    return report


def _prune_conversions(node):
    """Delete conversion nodes left hanging off a node's outputs by a forced reconnect."""
    for conv in set(cmds.listConnections(node, source=False, destination=True) or []):
        if cmds.objExists(conv) and cmds.nodeType(conv) in model.CONVERSION_TYPES:
            if not cmds.listConnections(conv + ".output", source=False, destination=True):
                _drop_conversion(conv)


def _drop_conversion(conv):
    """Remove a conversion node that feeds nothing.

    Its connections are broken first: cmds.delete on a still-connected node cascades
    upstream and can take the source node with it (global leaf maya-dg-cascade-delete).
    """
    pairs = cmds.listConnections(conv, connections=True, plugs=True, source=True,
                                 destination=False) or []
    for i in range(0, len(pairs), 2):
        cmds.disconnectAttr(pairs[i + 1], pairs[i])
    pairs = cmds.listConnections(conv, connections=True, plugs=True, source=False,
                                 destination=True) or []
    for i in range(0, len(pairs), 2):
        cmds.disconnectAttr(pairs[i], pairs[i + 1])
    if cmds.objExists(conv):
        cmds.delete(conv)


@undo_chunk("swap links")
def swap_inputs(a, b):
    """Swap what feeds two input plugs (Node Wrangler Alt+S)."""
    sa, sb = source_of(a), source_of(b)
    disconnect_inputs([p for p, s in ((a, sa), (b, sb)) if s])
    errs = []
    if sb:
        errs.append(connect(sb, a))
    if sa:
        errs.append(connect(sa, b))
    return [e for e in errs if e]


# ---------------------------------------------------------------------------- link by name

def socket_options(node, output):
    """Visible, meaningful sockets independent of the board's current display mode."""
    obj = model.obj_from_uuid(model.uuids_of([node])[0])
    fn = om.MFnDependencyNode(obj)
    base = model.base_attr_names()
    options = []

    def visit(plug):
        attr = plug.attribute()
        fa = om.MFnAttribute(attr)
        if fa.hidden or attr.hasFn(om.MFn.kMessageAttribute):
            return
        sides = model.port_sides(attr, obj.hasFn(om.MFn.kDagNode))
        if not sides[1 if output else 0]:
            return
        if plug.isArray:
            indices = list(plug.getExistingArrayAttributeIndices())
            if not output:
                index = 0
                while index in indices and plug.elementByLogicalIndex(index).isDestination:
                    index += 1
                if index not in indices:
                    indices.append(index)
            for index in sorted(indices):
                visit(plug.elementByLogicalIndex(index))
            return
        path = model.plug_path(plug)
        if plug_exists(node + '.' + path):
            options.append((path, model.attr_class(attr)))
        if plug.isCompound:
            for i in range(plug.numChildren()):
                visit(plug.child(i))

    for name, attr, hidden, keyable in model.top_attrs(fn):
        if name not in base and not hidden:
            visit(fn.findPlug(name, False))
    return options


def compatible_sockets(a, b):
    scalars = {'Numeric', 'Integer', 'Boolean', 'Rotation'}
    vectors = {'ThreeDNumericVector', 'ThreeDIntegerVector', 'Color'}
    return a == b and a not in {'MultiAmbiguous', 'Array'} or (
        a in scalars and b in scalars) or (a in vectors and b in vectors)


def type_socket_options(type_name, output):
    """Inspect static sockets without creating a node; new multi inputs start at index zero."""
    node_class = om.MNodeClass(type_name)
    base, options = model.base_attr_names(), []

    def visit(attr, prefix=''):
        fa = om.MFnAttribute(attr)
        if fa.hidden or not fa.connectable or attr.hasFn(om.MFn.kMessageAttribute):
            return
        if not model.port_sides(attr, False)[1 if output else 0]:
            return
        path = prefix + fa.name + ('[0]' if fa.array else '')
        options.append((path, model.attr_class(attr)))
        if attr.hasFn(om.MFn.kCompoundAttribute):
            fn = om.MFnCompoundAttribute(attr)
            for i in range(fn.numChildren()):
                visit(fn.child(i), path + '.')

    for i in range(node_class.attributeCount):
        attr = node_class.attribute(i)
        fa = om.MFnAttribute(attr)
        if fa.parent.isNull() and fa.name not in base:
            visit(attr)
    return options


def utility_types():
    """Maya utilities, including classified utilities from currently loaded plug-ins."""
    result = []
    for name in sorted(set(cmds.allNodeTypes() or []), key=str.lower):
        classification = ':'.join(cmds.getClassification(name) or [])
        if name in model.UTILITY_TYPES or any('utility' in part.split('/') for part in classification.split(':')):
            result.append(name)
    return result


def utility_options(source, destination):
    """Only utilities that can accept this source and feed this destination, without creating nodes."""
    sc = model.attr_class(_mplug(source).attribute())
    dc = model.attr_class(_mplug(destination).attribute())
    result = {}
    for type_name in utility_types():
        try:
            inputs = [(p, c) for p, c in type_socket_options(type_name, False) if compatible_sockets(sc, c)]
            outputs = [(p, c) for p, c in type_socket_options(type_name, True) if compatible_sockets(c, dc)]
        except RuntimeError:
            continue
        if inputs and outputs:
            result[type_name] = (inputs, outputs)
    return result


@undo_chunk('insert utility')
def insert_utility(source, destination, type_name, input_attr, output_attr):
    """Insert into a still-existing wire, preserving its raw conversion source and rolling back failure."""
    if source_of(destination) != _long(source):
        raise ValueError('The original wire changed; choose it again')
    if _mplug(destination).isLocked:
        raise ValueError('The destination attribute is locked')
    ins, outs = dict(type_socket_options(type_name, False)), dict(type_socket_options(type_name, True))
    if input_attr not in ins or output_attr not in outs:
        raise ValueError('Choose valid input and output attributes')
    if not compatible_sockets(model.attr_class(_mplug(source).attribute()), ins[input_attr]) or not compatible_sockets(
            outs[output_attr], model.attr_class(_mplug(destination).attribute())):
        raise ValueError('Choose compatible input and output attributes')
    raw = source_of(destination, skip_conversion=False)
    conversions = set(model.uuids_of(cmds.ls(type='unitConversion')))
    node = create_node(type_name)
    try:
        error = connect(raw, node + '.' + input_attr)
        if error:
            raise RuntimeError(error)
        error = connect(node + '.' + output_attr, destination)
        if error:
            raise RuntimeError(error)
    except Exception:
        if source_of(destination, skip_conversion=False) != raw:
            cmds.connectAttr(raw, destination, force=True)
        new = set(model.uuids_of(cmds.ls(type='unitConversion'))) - conversions
        cleanup = [node] + [model.path_of(u) for u in new if model.path_of(u)]
        for item in cleanup:
            for dst, _ in _inputs_of(item):
                current = source_of(dst, skip_conversion=False)
                if current:
                    cmds.disconnectAttr(current, dst)
        cmds.delete(cleanup)
        raise
    return node


def _channel_key(path):
    """Match input/output families by their leaf name and array indices, never by declaration order."""
    leaf = path.rsplit('.', 1)[-1]
    leaf = re.sub(r'^(?:input|output|in|out)(?=[A-Z_0-9\[]|$)', '', leaf)
    leaf = re.sub(r'(?:Input|Output|_in|_out)$', '', leaf).strip('_')
    leaf = re.sub(r'^\d+(?=[A-Za-z])', '', leaf)
    axis = re.search(r'[XYZRGB]$', leaf)
    if axis:
        leaf = axis[0]
    return tuple(re.findall(r'\[\d+\]', path)), leaf.lower()


def _unique_pairs(inputs, outputs):
    """Require a unique perfect matching, with exact names and channel names before type-only matches."""
    if len(inputs) != len(outputs) or not inputs:
        raise ValueError('Active inputs and outputs must form one-to-one pairs')
    candidates = []
    for output, destinations in outputs:
        def compatible(inp, source):
            sc = model.attr_class(source.attribute())
            if sc == 'MultiAmbiguous':
                sc = model.attr_class(inp.attribute())  # unitConversion's generic socket
            for dst in destinations:
                dc = model.attr_class(dst.attribute())
                if dc == 'MultiAmbiguous':
                    dc = model.attr_class(output.attribute())
                if not compatible_sockets(sc, dc):
                    return False
            return True
        valid = [i for i, (inp, source) in enumerate(inputs)
                 if compatible(inp, source)]
        exact = [i for i in valid if model.plug_path(inputs[i][0]) == model.plug_path(output)]
        named = [i for i in valid if _channel_key(model.plug_path(inputs[i][0])) ==
                 _channel_key(model.plug_path(output))]
        leaf = _channel_key(model.plug_path(output))[1]
        channels = [i for i in valid if leaf and _channel_key(model.plug_path(inputs[i][0]))[1] == leaf]
        candidates.append(exact or named or channels or valid)

    def match(exclude=None):
        assigned = {}
        def visit(out, seen):
            for inp in candidates[out]:
                if (out, inp) == exclude or inp in seen:
                    continue
                seen.add(inp)
                if inp not in assigned or visit(assigned[inp], seen):
                    assigned[inp] = out
                    return True
            return False
        if all(visit(out, set()) for out in range(len(outputs))):
            return {out: inp for inp, out in assigned.items()}
        return None

    pairs = match()
    if pairs is None:
        raise ValueError('Active input/output pairs have incompatible data types or channels')
    if any(match((out, inp)) is not None for out, inp in pairs.items()):
        raise ValueError('Active input/output pairing is ambiguous')
    return pairs


def _leaf_inputs(plug, source):
    if plug.isCompound and source.isCompound and plug.numChildren() == source.numChildren():
        return [pair for i in range(plug.numChildren())
                for pair in _leaf_inputs(plug.child(i), source.child(i))]
    return [(plug, source)]


def _leaf_outputs(plug, destinations):
    if plug.isCompound and all(p.isCompound and p.numChildren() == plug.numChildren() for p in destinations):
        return [pair for i in range(plug.numChildren())
                for pair in _leaf_outputs(plug.child(i), [p.child(i) for p in destinations])]
    return [(plug, destinations)]


def delete_inbetween_plan(node):
    """Read-only bypass plan for any node with unambiguously paired active data sockets."""
    obj = _node_of(node + '.message')
    if cmds.lockNode(node, q=True, lock=True)[0] or cmds.referenceQuery(node, isNodeReferenced=True):
        raise ValueError('The node is locked or referenced')
    if obj.hasFn(om.MFn.kDagNode) and cmds.listRelatives(node, children=True, type='transform'):
        raise ValueError('The node has child transforms; delete them separately')
    inputs, outputs, originals, detach = [], [], [], []
    for plug in om.MFnDependencyNode(obj).getConnections():
        if plug.isDestination:
            detach.append((_long(plug.sourceWithConversion().name()), _long(plug.name())))
        if plug.attribute().hasFn(om.MFn.kMessageAttribute):
            detach.extend((_long(plug.name()), _long(p.name())) for p in plug.connectedTo(False, True))
            continue  # Registration, shading membership and metadata are not data channels.
        if plug.isDestination:
            source = plug.sourceWithConversion()
            if source.node() == obj:
                raise ValueError('The node contains an internal connection')
            inputs.append((plug, source))
        destinations = []
        for dest in plug.connectedTo(False, True):
            top = model.plug_path(dest).split('.', 1)[0].split('[', 1)[0]
            if dest.node().hasFn(om.MFn.kSet) and top in ('dagSetMembers', 'dnSetMembers'):
                detach.append((_long(plug.name()), _long(dest.name())))
            else:
                destinations.append(dest)
        if destinations:
            if any(p.node() == obj for p in destinations):
                raise ValueError('The node contains an internal connection')
            outputs.append((plug, destinations))
            originals.extend((plug, p) for p in destinations)
    if not inputs or not outputs:
        raise ValueError('Connect at least one input and one output first')
    if len(inputs) != 1 or len(outputs) != 1:
        inputs = [pair for plug, source in inputs for pair in _leaf_inputs(plug, source)]
        outputs = [pair for plug, dests in outputs for pair in _leaf_outputs(plug, dests)]
    pairs = _unique_pairs(inputs, outputs)
    routes = []
    for out, inp in sorted(pairs.items()):
        source = inputs[inp][1]
        for destination in outputs[out][1]:
            if destination.isLocked:
                raise ValueError('A destination attribute is locked')
            routes.append((_long(source.name()), _long(destination.name())))
    return {'routes': routes, 'originals': [(_long(s.name()), _long(d.name())) for s, d in originals],
            'detach': detach,
            'pairs': len(pairs)}


@undo_chunk('delete inbetween')
def delete_inbetween(node):
    """Bypass all paired channels and delete the node; rollback all rewiring if any step fails."""
    plan = delete_inbetween_plan(node)
    conversions = set(model.uuids_of(cmds.ls(type='unitConversion')))
    disconnected = []
    try:
        # Disconnect parent compound connections before replacing them with leaf channels.
        for source, destination in plan['originals']:
            cmds.disconnectAttr(source, destination)
        for source, destination in plan['routes']:
            error = connect(source, destination)
            if error:
                raise RuntimeError(error)
        # Disconnect incoming wires before deletion so Maya cannot cascade into upstream nodes.
        # Save names before mutations: disconnecting a multi element can invalidate its MPlug.
        for source, dest in plan['detach']:
            cmds.disconnectAttr(source, dest)
            disconnected.append((source, dest))
        cmds.delete(node)
    except Exception:
        for _, dest in plan['routes']:
            raw = source_of(dest, skip_conversion=False)
            if raw:
                cmds.disconnectAttr(raw, dest)
        for source, dest in plan['originals'] + disconnected:
            if plug_exists(source) and plug_exists(dest):
                cmds.connectAttr(source, dest, force=True)
        new = set(model.uuids_of(cmds.ls(type='unitConversion'))) - conversions
        for uid in new:
            path = model.path_of(uid)
            if path:
                for dst, _ in _inputs_of(path):
                    raw = source_of(dst, skip_conversion=False)
                    if raw:
                        cmds.disconnectAttr(raw, dst)
                cmds.delete(path)
        raise
    return plan


def lazy_pairs(source, target):
    """Rank compatible output/input pairs, preferring name matches and primary outputs."""
    outputs, inputs = socket_options(source, True), socket_options(target, False)
    named = set(link_pairs(source, target))
    ranked = []
    for sp, sc in outputs:
        for dp, dc in inputs:
            dst = target + '.' + dp
            if not compatible_sockets(sc, dc) or source_of(dst, skip_conversion=False):
                continue
            if _mplug(dst).isLocked:
                continue
            score = (100 if (sp, dp) in named else 0) + (20 if sp.startswith(_OUT_PREFIX) else 0)
            score += 10 if sc == dc else 0
            ranked.append((score, sp, dp))
    ranked.sort(key=lambda p: -p[0])  # declaration order resolves equal scores predictably
    return [(sp, dp) for _, sp, dp in ranked]


@undo_chunk('lazy connect')
def lazy_connect(source, target):
    pairs = lazy_pairs(source, target)
    if not pairs:
        return '', '', 'No compatible free input; use Alt+Shift+RMB to choose sockets'
    sp, dp = pairs[0]
    error = connect(source + '.' + sp, target + '.' + dp)
    return sp, dp, error

_OUT_PREFIX = ("output", "out")
_IN_PREFIX = ("input", "in")


def _strip(name, prefixes):
    for p in prefixes:
        if name.startswith(p) and len(name) > len(p) and name[len(p)].isupper():
            rest = name[len(p):]
            return rest[0].lower() + rest[1:]
    return None


def _tops(node):
    obj = model.obj_from_uuid(model.uuids_of([node])[0])
    fn = om.MFnDependencyNode(obj)
    out = []
    for name, attr, hidden, keyable in model.top_attrs(fn):
        if hidden or name == "message":
            continue
        fa = om.MFnAttribute(attr)
        out.append((name, fa.readable, fa.writable, keyable, fa.array))
    return out


def link_pairs(active, target):
    """Attribute pairs active.X -> target.Y matched by name.

    outputTranslate -> translate, outColor -> inColor (prefix stripped), and same-name links
    for keyable attributes (translate -> translate). One source per destination.
    """
    src_attrs = _tops(active)
    dst_attrs = {n: (r, w, k, arr) for n, r, w, k, arr in _tops(target) if w}
    dst_stripped = {}
    for n in dst_attrs:
        s = _strip(n, _IN_PREFIX)
        if s:
            dst_stripped.setdefault(s, n)
    pairs, used = [], set()
    # Pass 1: prefix-stripped outputs.
    for n, readable, writable, keyable, arr in src_attrs:
        if not readable:
            continue
        s = _strip(n, _OUT_PREFIX)
        if not s:
            continue
        d = s if s in dst_attrs else dst_stripped.get(s)
        if d and d not in used:
            pairs.append((n, d))
            used.add(d)
    # Pass 2: same name, keyable attributes only (otherwise every internal attr would link).
    for n, readable, writable, keyable, arr in src_attrs:
        if not (readable and keyable) or n not in dst_attrs or n in used:
            continue
        if not dst_attrs[n][2]:
            continue
        pairs.append((n, n))
        used.add(n)
    return pairs


@undo_chunk("link by name")
def link_by_name(active, targets, replace=False):
    """Connect active -> each target by attribute name (Node Wrangler K / Shift+K)."""
    made, skipped = [], []
    for t in targets:
        if _same_node(t, active):
            continue
        for s, d in link_pairs(active, t):
            sp, dp = active + "." + s, t + "." + d
            if source_of(dp) and not replace:
                skipped.append((dp, "already connected"))
                continue
            err = connect(sp, dp)
            if err:
                skipped.append((dp, err))
            else:
                made.append((sp, dp))
    return {"made": made, "skipped": skipped}


@undo_chunk("connect to multi")
def connect_many_to_multi(sources, multi):
    """Several source plugs into a multi input (target[i], input3D[i]) in the given order."""
    made = []
    p = _mplug(multi)
    idx = list(p.getExistingArrayAttributeIndices())
    nxt = (max(idx) + 1) if idx else 0
    for s in sources:
        dst = "%s[%d]" % (multi, nxt)
        err = connect(s, dst)
        if not err:
            made.append((s, dst))
            nxt += 1
    return made


# ---------------------------------------------------------------------------- names

def copy_forms(plug):
    """The three strings the port menu copies: attr path, node.attr, full DAG path."""
    p = _mplug(plug)
    obj = p.node()
    path = model.plug_path(p)
    short = om.MFnDependencyNode(obj).name()
    return {"attr": path, "node": short + "." + path, "dag": model.full_path(obj) + "." + path}


# ---------------------------------------------------------------------------- values

@undo_chunk("set value")
def set_value(plug, text):
    """Set a numeric / bool / enum attribute from the text typed into a node field."""
    p = _mplug(plug)
    attr = p.attribute()
    text = (text or "").strip()
    try:
        if attr.hasFn(om.MFn.kEnumAttribute):
            fn = om.MFnEnumAttribute(attr)
            if re.match(r"^-?\d+$", text):
                v = int(text)
            else:
                v = fn.fieldValue(text)
            cmds.setAttr(plug, v)
        elif model.value_kind(attr) == "bool":
            v = text.lower() in ("1", "on", "true", "yes")
            cmds.setAttr(plug, v)
        else:
            cmds.setAttr(plug, float(text))
    except (RuntimeError, ValueError) as e:
        return str(e).strip()
    return ""


def _limits(attr):
    """Soft limits first (what a slider should span), else hard limits; UI units."""
    def conv(v):
        if isinstance(v, om.MAngle):
            return v.asUnits(om.MAngle.uiUnit())
        if isinstance(v, om.MDistance):
            return v.asUnits(om.MDistance.uiUnit())
        if isinstance(v, om.MTime):
            return v.asUnits(om.MTime.uiUnit())
        return float(v)
    lo = hi = slo = shi = None
    try:
        if attr.hasFn(om.MFn.kNumericAttribute):
            fn = om.MFnNumericAttribute(attr)
        elif attr.hasFn(om.MFn.kUnitAttribute):
            fn = om.MFnUnitAttribute(attr)
        else:
            return None, None, None, None
        if fn.hasMin():
            lo = conv(fn.getMin())
        if fn.hasMax():
            hi = conv(fn.getMax())
        if fn.hasSoftMin():
            slo = conv(fn.getSoftMin())
        if fn.hasSoftMax():
            shi = conv(fn.getSoftMax())
    except (RuntimeError, TypeError, ValueError):
        pass
    return lo, hi, slo, shi


def slide_meta(plug):
    """Blender-like drag parameters for one number plug (UI units, as the field shows)."""
    attr = plug.attribute()
    value = float(model.read_value(plug) or 0.0)
    is_int = False
    angle = False
    if attr.hasFn(om.MFn.kNumericAttribute):
        t = om.MFnNumericAttribute(attr).numericType()
        NT = om.MFnNumericData
        is_int = t in (NT.kInt, NT.kShort, NT.kLong, NT.kByte, NT.kChar, NT.kInt64)
    elif attr.hasFn(om.MFn.kUnitAttribute):
        angle = om.MFnUnitAttribute(attr).unitType() == om.MFnUnitAttribute.kAngle
    lo, hi, slo, shi = _limits(attr)
    a = slo if slo is not None else lo
    b = shi if shi is not None else hi
    if is_int:
        step, coarse, fine = 0.1, 1.0, 1.0
    elif angle:
        step, coarse, fine = 0.5, 5.0, 1.0
    elif a is not None and b is not None and 0 < b - a <= 1000:
        span = b - a
        step, coarse, fine = span / 250.0, span / 20.0, span / 100.0
    else:
        step, coarse, fine = 0.02, 1.0, 0.1
    return {"v": value, "isInt": is_int, "step": step, "coarse": coarse, "fine": fine,
            "min": lo, "max": hi}


# ---------------------------------------------------------------------------- nodes

@undo_chunk("delete nodes")
def delete_nodes(nodes):
    nodes = [n for n in nodes if cmds.objExists(n)]
    if nodes:
        cmds.delete(nodes)
    return nodes


@undo_chunk("rename node")
def rename_node(node, text):
    """rename from the board. Returns (new name, error text); Maya may adjust the name
    (a clash gets a number, a bad character an underscore), so the caller shows what came back."""
    text = (text or "").strip()
    if not text:
        return node, "A node name cannot be empty"
    if not cmds.objExists(node):
        return node, "%s no longer exists" % node
    if text == node or text == node.rsplit("|", 1)[-1]:
        return node, ""
    try:
        return cmds.rename(node, text), ""
    except RuntimeError as e:
        return node, str(e).strip()


@undo_chunk("create node")
def create_node(type_name):
    """Create a node the way Maya's Node Editor Tab field does (utilities via shadingNode)."""
    try:
        cls = " ".join(cmds.getClassification(type_name) or [])
    except RuntimeError:
        cls = ""
    if cls.startswith("utility") or "/utility" in cls:
        name = cmds.shadingNode(type_name, asUtility=True)
    elif cls.startswith("shader"):
        name = cmds.shadingNode(type_name, asShader=True)
    elif cls.startswith("texture"):
        name = cmds.shadingNode(type_name, asTexture=True)
    else:
        name = cmds.createNode(type_name, skipSelect=True)
    return name
