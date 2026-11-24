"""
Move a reference from one namespace to another.

Usage: run this file in the Script Editor (Python), select any node that
belongs to the reference (or the RN node itself), click "Get from selection",
type the destination namespace, check the preview, click "Move".

Destination = the exact namespace the reference will end up with.
    current  char01        destination  shot010:char01   ->  shot010:char01
    current  char01        destination  hero             ->  hero
If "current" is a PARENT of the reference's namespace, only that part of the
path is replaced:
    reference set:char01, current  set, destination  shot010  ->  shot010:char01

Missing parent namespaces are created. Old namespaces left empty can be
removed (checkbox). Everything is done with ABSOLUTE names from the root
namespace, so the scene's current namespace can't nest the result.
"""
import maya.cmds as cmds


# --------------------------------------------------------------------------- utils
def _abs(ns):
    """'A:B' / ':A:B' / '' -> ':A:B' / ':'"""
    ns = (ns or "").strip().strip(":")
    return ":" + ns if ns else ":"


def _join(a, b):
    parts = [p for p in (a.strip(":"), b.strip(":")) if p]
    return _abs(":".join(parts))


def _parent(ns):
    return _abs(ns.rsplit(":", 1)[0])


def _leaf(ns):
    return ns.rsplit(":", 1)[-1]


def _ensure(ns):
    """Create absolute namespace ns and any missing parents."""
    if ns == ":" or cmds.namespace(exists=ns):
        return
    _ensure(_parent(ns))
    cmds.namespace(add=ns)  # absolute name -> parent/current namespace ignored


def _is_empty(ns):
    nodes = cmds.namespaceInfo(ns, listOnlyDependencyNodes=True) or []
    kids = cmds.namespaceInfo(ns, listOnlyNamespaces=True) or []
    return not nodes and not kids


def reference_of(node):
    """Top-level reference node that owns `node`."""
    try:
        if cmds.nodeType(node) == "reference":
            ref = node
        else:
            ref = cmds.referenceQuery(node, referenceNode=True, topReference=True)
    except RuntimeError:
        cmds.error("{} is not part of a reference.".format(node))
    if cmds.referenceQuery(ref, referenceNode=True, parent=True):
        cmds.error("{} is a nested reference; change it in the parent file.".format(ref))
    return ref


def ref_ns(ref):
    return _abs(cmds.referenceQuery(ref, namespace=True))


def target_namespace(ref, current, destination):
    """Work out the final absolute namespace (no scene changes)."""
    old = ref_ns(ref)
    cur, dst = _abs(current), _abs(destination)
    if cur == ":":
        cmds.error("Current namespace can't be the root.")
    if dst == ":":
        cmds.error("Destination can't be the root.")
    if not (old == cur or old.startswith(cur + ":")):
        cmds.error("Reference {} is in '{}', not inside '{}'.".format(ref, old, cur))
    remainder = old[len(cur):].strip(":")
    return old, (_join(dst, remainder) if remainder else dst)


# --------------------------------------------------------------------------- core
def move_reference(node, current, destination, remove_empty=True):
    ref = reference_of(node)
    old, new = target_namespace(ref, current, destination)

    if new == old:
        cmds.warning("Reference is already in '{}'.".format(new))
        return new
    if new.startswith(old + ":"):
        cmds.error("Can't move '{}' inside itself.".format(old))
    merge = False
    if cmds.namespace(exists=new) and not _is_empty(new):
        n = len(cmds.namespaceInfo(new, listOnlyDependencyNodes=True) or [])
        answer = cmds.confirmDialog(
            title="Namespace exists",
            message="'{}' already contains {} node(s).\n\nMerge the reference into it?\n"
                    "Clashing node names get a number added.".format(new, n),
            button=["Merge", "Cancel"], defaultButton="Merge",
            cancelButton="Cancel", dismissString="Cancel")
        if answer != "Merge":
            return old
        merge = True

    ref_file = cmds.referenceQuery(ref, filename=True)
    prev_current = cmds.namespaceInfo(currentNamespace=True, absoluteName=True)
    cmds.undoInfo(openChunk=True)
    try:
        cmds.namespace(set=":")
        if cmds.namespace(exists=new) and not merge:
            cmds.namespace(removeNamespace=new)   # empty leftover namespace
        _ensure(_parent(new))

        if _parent(old) != _parent(new):
            # move under the new parent first (absolute name -> current ns ignored);
            # use a temp name if the final one is taken and we're merging
            step = new if not merge else _join(_parent(new), _leaf(old) + "_moveTmp")
            cmds.namespace(rename=(old, step))

        # final name, same parent: what the Reference Editor does
        if ref_ns(ref) != new:
            cmds.file(ref_file, edit=True, namespace=_leaf(new), mergeNamespacesOnClash=merge)

        if ref_ns(ref) != new:
            raise RuntimeError("Reference ended up in '{}' instead of '{}'.".format(ref_ns(ref), new))

        if remove_empty:
            ns = _parent(old)
            while ns != ":" and cmds.namespace(exists=ns) and _is_empty(ns):
                up = _parent(ns)
                cmds.namespace(removeNamespace=ns)
                ns = up
    except Exception:
        cmds.undoInfo(closeChunk=True)
        cmds.undo()
        raise
    else:
        cmds.undoInfo(closeChunk=True)
    finally:
        if cmds.namespace(exists=prev_current):
            cmds.namespace(set=prev_current)

    print("Moved reference {}:  {}  ->  {}".format(ref, old, new))
    return new


# --------------------------------------------------------------------------- UI
def ui():
    win = "moveRefNsWin"
    if cmds.window(win, exists=True):
        cmds.deleteUI(win)
    cmds.window(win, title="Move Reference Namespace", widthHeight=(320, 190))
    cmds.columnLayout(adj=True, rs=6, co=("both", 8))
    cmds.text(l="Select a node of the reference:", al="left")
    cur = cmds.textFieldButtonGrp(l="Current", bl="Get from selection", cw3=(70, 130, 110), adj=2)
    dst = cmds.textFieldGrp(l="Destination", cw2=(70, 230), adj=2)
    preview = cmds.text(l="Result: -", al="left")
    clean = cmds.checkBox(l="Remove old namespace if empty", v=True)

    def _selected():
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.error("Select a node of the reference.")
        return sel[0]

    def _update(*_):
        try:
            ref = reference_of(_selected())
            old, new = target_namespace(ref,
                                        cmds.textFieldButtonGrp(cur, q=True, tx=True),
                                        cmds.textFieldGrp(dst, q=True, tx=True))
            cmds.text(preview, e=True, l="Result:  {}  ->  {}".format(old, new))
        except RuntimeError:
            cmds.text(preview, e=True, l="Result: -")

    def _fill(*_):
        cmds.textFieldButtonGrp(cur, e=True, tx=ref_ns(reference_of(_selected())).lstrip(":"))
        _update()

    def _move(*_):
        new = move_reference(_selected(),
                             cmds.textFieldButtonGrp(cur, q=True, tx=True),
                             cmds.textFieldGrp(dst, q=True, tx=True),
                             cmds.checkBox(clean, q=True, v=True))
        cmds.textFieldButtonGrp(cur, e=True, tx=new.lstrip(":"))
        _update()

    cmds.textFieldButtonGrp(cur, e=True, bc=_fill, cc=_update)
    cmds.textFieldGrp(dst, e=True, cc=_update)
    cmds.button(l="Move", h=34, c=_move)
    cmds.showWindow(win)


def main():
    ui()