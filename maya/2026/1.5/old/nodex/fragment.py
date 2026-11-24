"""Native Maya snapshots of an induced subgraph, independent of the source scene."""
import contextlib
import os
import re
import tempfile
import uuid

import maya.api.OpenMaya as om
import maya.cmds as cmds

from . import model, ops


@contextlib.contextmanager
def _selection():
    previous = om.MGlobal.getActiveSelectionList()
    try:
        yield
    finally:
        om.MGlobal.setActiveSelectionList(previous)


def _internal_conversions(nodes):
    """Include hidden conversion chains only when both visible endpoints are selected."""
    selected = set(model.uuids_of(nodes))
    extra = set()
    for node in nodes:
        fn = om.MFnDependencyNode(ops._node_of(node + '.message'))
        for plug in fn.getConnections():
            if not plug.isDestination:
                continue
            source = plug.sourceWithConversion()
            chain, seen = [], set()
            while not source.isNull:
                sf = om.MFnDependencyNode(source.node())
                uid = sf.uuid().asString()
                if uid in selected:
                    extra.update(chain)
                    break
                if sf.typeName not in model.CONVERSION_TYPES or uid in seen:
                    break
                seen.add(uid)
                chain.append(uid)
                source = sf.findPlug('input', False).sourceWithConversion()
    return [model.path_of(u) for u in sorted(extra - selected)]


def _commands(text):
    """Split MEL statements without splitting quoted strings, escaped quotes or comments."""
    start, quoted, escaped, comment = 0, False, False, False
    for i, char in enumerate(text):
        if comment:
            if char == '\n':
                comment = False
                start = i + 1
            continue
        if escaped:
            escaped = False
            continue
        if quoted and char == '\\':
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted and text[i:i + 2] == '//':
            comment = True
        elif not quoted and char == ';':
            yield text[start:i + 1].strip()
            start = i + 1


def _clean_scene(text, tag, exported, codeset):
    """Drop Maya's implicit default-node edits and any link to a node outside the fragment."""
    statements = list(_commands(text))
    names = set()
    for stmt in statements:
        if stmt.startswith('createNode '):
            match = re.search(r'-n "([^"]+)"', stmt)
            if match:
                names.add(match[1])
    def internal(plug):
        node = plug.split('.', 1)[0].lstrip(':')
        return node in names or node.rsplit('|', 1)[-1] in names

    out, local = ['//Maya ASCII fragment\n//Codeset: ' + codeset], False
    tagged = set()
    for stmt in statements:
        command = stmt.split(None, 1)[0]
        if command in ('requires', 'currentUnit'):
            out.append(stmt)
        elif command == 'createNode':
            local = True
            out.append(stmt)
        elif command == 'select':
            local = False              # default/shared nodes are emitted as select -ne
        elif command == 'rename' and local:
            match = re.fullmatch(r'rename -uid "([^"]+)";', stmt)
            if match and match[1] in exported:
                uid = match[1]
                tagged.add(uid)
                out.extend(['addAttr -ln "%s" -dt "string";' % tag,
                            'setAttr ".%s" -type "string" "%s";' % (tag, uid)])
        elif command in ('setAttr', 'addAttr', 'aliasAttr', 'lockNode') and local:
            out.append(stmt)
        elif command == 'connectAttr':
            plugs = re.findall(r'"((?:\\.|[^"\\])*)"', stmt)
            if len(plugs) == 2 and all(internal(p) for p in plugs):
                out.append(stmt)
        elif command == 'parent':
            paths = re.findall(r'"([^"]+)"', stmt)
            if paths and all(internal(p) for p in paths):
                out.append(stmt)
    missing = exported - tagged
    if missing:
        raise RuntimeError('Maya could not serialize every selected node')
    return '\n'.join(out) + '\n'


def capture(nodes):
    """Read-only snapshot: native attributes and only internal links; no undo entries."""
    nodes = list(dict.fromkeys(nodes))
    if not nodes:
        raise ValueError('Select nodes to copy')
    ids = model.uuids_of(nodes)
    if len(ids) != len(nodes):
        raise ValueError('Some selected nodes no longer exist')
    # A transform's geometry is part of the object, even when its shape is not on the board.
    shapes = []
    for node in nodes:
        if cmds.objectType(node, isAType='transform'):
            shapes.extend(cmds.listRelatives(node, shapes=True, fullPath=True) or [])
    nodes = [model.path_of(u) for u in dict.fromkeys(ids + model.uuids_of(shapes))]
    nodes += _internal_conversions(nodes)
    exported = set(model.uuids_of(nodes))
    tag = '_nodexFragment_' + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='nodex_') as folder, _selection():
        selection = om.MSelectionList()
        for node in nodes:
            selection.add(node)
        om.MGlobal.setActiveSelectionList(selection)
        path = os.path.join(folder, 'fragment.ma')
        cmds.file(path, force=True, type='mayaAscii', exportSelectedStrict=True,
                  preserveReferences=False)
        with open(path, 'rb') as stream:
            raw = stream.read()
        code = re.search(br'//Codeset:\s*([^\r\n]+)', raw)
        codeset = code[1].decode('ascii').strip() if code else 'UTF-8'
        encoding = codeset
        if encoding.isdigit():
            encoding = 'cp' + encoding
        scene = _clean_scene(raw.decode(encoding), tag, exported, codeset)
    return {'version': 1, 'scene': scene, 'encoding': encoding, 'tag': tag, 'selected': ids}


def _import_snapshot(snapshot):
    """Native import used only inside the undoable plug-in command."""
    if snapshot.get('version') != 1 or not snapshot.get('selected'):
        raise ValueError('Unsupported NodeX fragment')
    tag = snapshot['tag']
    namespace = 'nodexPaste_' + uuid.uuid4().hex
    mapping = {}
    with tempfile.TemporaryDirectory(prefix='nodex_') as folder, _selection():
        path = os.path.join(folder, 'fragment.ma')
        with open(path, 'w', encoding=snapshot.get('encoding', 'utf-8')) as stream:
            stream.write(snapshot['scene'])
        try:
            created = cmds.file(path, i=True, type='mayaAscii', namespace=':' + namespace,
                                returnNewNodes=True, executeScriptNodes=False,
                                importFrameRate=False, importTimeRange='keep') or []
            all_created = model.uuids_of(created)
            for node in created:
                plug = node + '.' + tag
                if not cmds.objExists(plug):
                    continue
                key = cmds.getAttr(plug)
                mapping[key] = model.uuids_of([node])[0]
                cmds.deleteAttr(plug)
            if any(u not in mapping for u in snapshot['selected']):
                raise RuntimeError('Maya could not restore every copied node')
            cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
        except Exception:
            if cmds.namespace(exists=namespace):
                cmds.namespace(removeNamespace=namespace, deleteNamespaceContent=True)
            raise
    return {u: mapping[u] for u in snapshot['selected']}, all_created


_requests = {}


def paste(snapshot):
    """Return old UUID -> new UUID; the custom command makes native file import undoable."""
    import json
    command_path = os.path.join(os.path.dirname(__file__), 'fragment_command.py')
    if not cmds.pluginInfo(command_path, q=True, loaded=True):
        cmds.loadPlugin(command_path, quiet=True)
    token = uuid.uuid4().hex
    _requests[token] = snapshot
    try:
        result = cmds.nodexPasteFragment(token)
        return json.loads(result[0] if isinstance(result, list) else result)
    finally:
        _requests.pop(token, None)
