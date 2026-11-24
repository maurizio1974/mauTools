"""Mesh tools: skin weights, bind poses, per-vertex maps, proxies and
component selection.

Replaces mg_skinLib.mel, readWriteVtxData.mel, vertexLib.py, nodeLib.py,
mProxy.py, n_mirrorComponents.py, transferSelection.py and the mesh
procedures of mgUtility.mel.
"""
import json
import os
import time

from maya import cmds, mel
import maya.api.OpenMaya as om

from . import selected, warn, shapes, parent_of, tmp_file, Progress
from .transforms import centroid

MAP_FILE = 'mauTools_vtxData.vdt'
DEFORMER_WEIGHTS = 'weightList[0].weights'
PROXY_SUFFIXES = ('geo', 'mesh', 'sdm', 'nul', 'ply',
                  '_geo', '_mesh', '_sdm', '_nul', '_ply')
_copied = {'vertex': None}


# ---------------------------------------------------------------------------
# skin
# ---------------------------------------------------------------------------
def skin_cluster(node):
    """skinCluster deforming a mesh (or the mesh of a component)."""
    history = cmds.listHistory(node.split('.')[0], pruneDagObjects=True) or []
    found = cmds.ls(history, type='skinCluster')
    return found[0] if found else None


def influences(node=None):
    node = node or (selected() or [None])[0]
    skin = node and skin_cluster(node)
    return cmds.skinCluster(skin, q=True, influence=True) if skin else []


def deformers(mesh):
    """Every deformer in the history of a mesh."""
    return [n for n in cmds.listHistory(mesh) or []
            if 'geometryFilter' in cmds.nodeType(n, inherited=True)]


def average_weights(tolerance=0.0, iterations=2, radius=1):
    """Smooth the skin weights around each selected vertex.

    tolerance   weight change tolerance in percent
    iterations  maximum smoothing iterations
    radius      how many times the selection is grown around each vertex
    """
    points = selected(fl=True)
    if not points or not all('.vtx[' in p or '.cv[' in p for p in points):
        return warn('select one or more vertices only.')
    with Progress(len(points), 'Averaging weights ...') as bar:
        for point in points:
            if bar.cancelled():
                break
            skin = skin_cluster(point)
            if not skin:
                warn('%s is not skinned.' % point)
                break
            cmds.select(point, r=True)
            for _ in range(int(radius) - 1):
                mel.eval('PolySelectTraverse 1')
            cmds.skinCluster(skin, e=True, smoothWeights=tolerance / 100.0,
                             smoothWeightsMaxIterations=int(iterations))
            bar.step()
    cmds.select(points, r=True)


def copy_vertex_weights():
    """Remember the first selected vertex for paste_vertex_weights()."""
    sel = selected(fl=True)
    if not sel or '.' not in sel[0]:
        return warn('select the vertex to copy the weights from.')
    _copied['vertex'] = sel[0]
    print('mauTools: stored the weights of ' + sel[0])


def _swap_side(name):
    for a, b in (('L_', 'R_'), ('R_', 'L_')):
        if name.startswith(a):
            return b + name[2:]
    return name


def transfer_vertex_weights(source, dest, mirror=False):
    """Copy the skin weights of one vertex to another (also across meshes).

    mirror=True reads each L_ influence from its R_ twin and vice versa."""
    source_skin = skin_cluster(source)
    dest_skin = skin_cluster(dest)
    if not source_skin or not dest_skin:
        return warn('both vertices must belong to a skinned mesh.')
    weights = dict(zip(
        cmds.skinPercent(source_skin, source, q=True, transform=None) or [],
        cmds.skinPercent(source_skin, source, q=True, value=True) or []))
    values = []
    for inf in cmds.skinCluster(dest_skin, q=True, influence=True) or []:
        twin = _swap_side(inf) if mirror else inf
        if twin in weights:
            values.append((inf, weights[twin]))
    if values:
        cmds.skinPercent(dest_skin, dest, normalize=True,
                         transformValue=values)


def paste_vertex_weights(mirror=False):
    """Paste the stored vertex weights on every selected vertex."""
    source = _copied['vertex']
    if not source or not cmds.objExists(source):
        return warn('copy a vertex first.')
    sel = selected(fl=True)
    for vertex in sel:
        transfer_vertex_weights(source, vertex, mirror)
    print('mauTools: pasted the weights of %s on %d vertices.'
          % (source, len(sel)))


def copy_weights_by_position(source_vertices, dest_mesh):
    """Copy each source vertex to the closest vertex of another mesh."""
    dest_vertices = cmds.ls(dest_mesh + '.vtx[*]', fl=True)
    positions = [cmds.pointPosition(v, world=True) for v in dest_vertices]
    for source in source_vertices:
        pos = om.MPoint(cmds.pointPosition(source, world=True))
        closest = min(range(len(positions)),
                      key=lambda i: pos.distanceTo(om.MPoint(positions[i])))
        transfer_vertex_weights(source, dest_vertices[closest])


def weights_between_joints(joint1, joint2, weight1=0.5, weight2=0.5):
    """Give the selected vertices the two weights on the two joints."""
    verts = cmds.filterExpand(sm=(31, 28, 36)) or []
    if not verts:
        return warn('select the vertices to weight.')
    if not joint1 or not joint2:
        return warn('pick the two joints first.')
    skin = skin_cluster(verts[0])
    if not skin:
        return warn('the selected vertices are not skinned.')
    cmds.waitCursor(state=True)
    try:
        cmds.skinPercent(skin, verts, transformValue=[
            (joint1, weight1), (joint2, weight2)])
    finally:
        cmds.waitCursor(state=False)


def select_influenced_vertices(minimum=0.0, maximum=1.0):
    """Select the vertices of the last selected mesh that the first selected
    joint influences with a weight inside the given range."""
    sel = selected()
    if len(sel) < 2:
        return warn('select the joint, then the skinned mesh.')
    joint, mesh = sel[0], sel[-1]
    skin = skin_cluster(mesh)
    if not skin:
        return warn('%s is not skinned.' % mesh)
    found = []
    count = cmds.polyEvaluate(mesh, vertex=True)
    with Progress(count, 'Getting vertices ...') as bar:
        for i in range(count):
            if bar.cancelled():
                break
            vertex = '%s.vtx[%d]' % (mesh, i)
            weight = cmds.skinPercent(skin, vertex, q=True, transform=joint)
            if weight > 0 and minimum <= weight <= maximum:
                found.append(vertex)
            bar.step()
    cmds.select(found, r=True)
    return found


def _root_influences():
    roots = []
    for skin in cmds.ls(type='skinCluster'):
        for joint in cmds.listConnections(
                skin, s=True, d=False, type='joint') or []:
            parent = parent_of(joint)
            is_root = not parent or cmds.nodeType(parent) != 'joint'
            if is_root and joint not in roots:
                roots.append(joint)
    return roots


def set_bind_pose(everything=False):
    """Replace the bind pose of the selected joints (or of the root joint of
    every skin in the scene) with the current pose."""
    joints = _root_influences() if everything else selected(type='joint')
    if not joints:
        return warn('select a joint.')
    for joint in joints:
        old = cmds.listConnections(joint, type='dagPose') or []
        if old and cmds.getAttr(old[0] + '.bindPose'):
            cmds.delete(old[0])
        pose = cmds.dagPose(joint, save=True, g=True, name='bindPose')
        cmds.setAttr(pose + '.bindPose', 1)
        print('mauTools: new bind pose "%s" for %s' % (pose, joint))


def reset_bind_pose(everything=False):
    """Update the existing bind poses of the selected joints (or of every
    skin influence in the scene) to the current pose."""
    if everything:
        joints = []
        for skin in cmds.ls(type='skinCluster'):
            joints += cmds.listConnections(
                skin, s=True, d=False, type='joint') or []
    else:
        joints = selected(type='joint')
    for joint in dict.fromkeys(joints):
        for pose in cmds.dagPose(joint, q=True, bindPose=True) or []:
            cmds.dagPose(joint, reset=True, name=pose)
            print('mauTools: bind pose %s reset for %s' % (pose, joint))


# ---------------------------------------------------------------------------
# per-vertex maps (deformer weights, nCloth maps)
# ---------------------------------------------------------------------------
def map_node(node):
    """The node that owns the maps: an nCloth shape below a transform, or
    the node itself."""
    for shape in shapes(node) if cmds.objExists(node) else []:
        if cmds.nodeType(shape) == 'nCloth':
            return shape
    return node


def map_attributes(node):
    """Per-vertex attributes that can be saved / copied on a node."""
    if not node or not cmds.objExists(node):
        return []
    node = map_node(node)
    if cmds.nodeType(node) == 'nCloth':
        return sorted(a for a in cmds.listAttr(node) or []
                      if a.endswith('PerVertex'))
    if 'geometryFilter' in cmds.nodeType(node, inherited=True):
        return [DEFORMER_WEIGHTS]
    return []


def _is_array(plug):
    return cmds.getAttr(plug, type=True) == 'doubleArray'


def read_map(node, attr):
    """Values of a map: a list (nCloth maps) or {index: weight} (deformers)."""
    plug = map_node(node) + '.' + attr
    if _is_array(plug):
        return list(cmds.getAttr(plug) or [])
    indices = cmds.getAttr(plug, multiIndices=True) or []
    return dict((i, cmds.getAttr('%s[%d]' % (plug, i))) for i in indices)


def write_map(node, attr, values, invert=False):
    plug = map_node(node) + '.' + attr
    items = (values.items() if isinstance(values, dict)
             else enumerate(values))
    items = [(int(i), 1.0 - v if invert else v) for i, v in items]
    if _is_array(plug):
        size = max(i for i, _ in items) + 1 if items else 0
        array = [0.0] * size
        for i, value in items:
            array[i] = value
        cmds.setAttr(plug, array, type='doubleArray')
    else:
        for i, value in items:
            cmds.setAttr('%s[%d]' % (plug, i), value)


def save_maps(node='', directory=''):
    """Save every map of a node to <directory>/<node>.vdt (or to a temp file
    when no directory is given). Returns the file path."""
    node = node or (selected() or [''])[0]
    attrs = map_attributes(node)
    if not attrs:
        return warn('pick a deformer (cluster ...) or an nCloth node.')
    data = {'node': node,
            'maps': dict((a, read_map(node, a)) for a in attrs)}
    short = node.split('|')[-1].replace(':', '_')
    path = (os.path.join(directory, short + '.vdt') if directory
            else tmp_file(MAP_FILE))
    with open(path, 'w') as handle:
        json.dump(data, handle)
    print('mauTools: vertex data of %s saved in %s' % (node, path))
    return path


def _read_map_file(path):
    with open(path) as handle:
        text = handle.read()
    if text.lstrip().startswith('{'):
        return json.loads(text)['maps']
    # files written by the old MEL tool: "attribute count value value ..."
    maps = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) > 2:
            maps[parts[0]] = [float(v) for v in parts[2:]]
    return maps


def load_maps(node='', path=''):
    """Load a .vdt file on a node (the temp file when no path is given)."""
    node = node or (selected() or [''])[0]
    path = path or tmp_file(MAP_FILE)
    if not node or not cmds.objExists(node):
        return warn('pick the node to load the vertex data on.')
    if not os.path.isfile(path):
        return warn('file not found: ' + path)
    known = map_attributes(node)
    done = []
    for attr, values in _read_map_file(path).items():
        if attr not in known:
            warn('%s has no map "%s", skipped.' % (node, attr))
            continue
        write_map(node, attr, values)
        done.append(attr)
    print('mauTools: %d map(s) loaded on %s' % (len(done), node))
    return done


def copy_map(source, source_attr, dest, dest_attr='', invert=False):
    """Copy a map from one node to another, optionally inverted (1 - w)."""
    if not source or not dest or not source_attr:
        return warn('pick the source and destination nodes and maps.')
    write_map(dest, dest_attr or source_attr, read_map(source, source_attr),
              invert)
    print('mauTools: %s.%s copied to %s.%s' % (
        source, source_attr, dest, dest_attr or source_attr))


def mirror_map(source, dest='', axis=0, attr=DEFORMER_WEIGHTS):
    """Mirror deformer weights across an axis (0 1 2 = X Y Z), in world
    space, for the selected vertices. `dest` defaults to the same deformer."""
    verts = cmds.filterExpand(sm=31) or []
    if not verts:
        return warn('select the vertices to mirror.')
    if not source:
        return warn('pick the deformer to mirror.')
    dest = dest or source
    mesh = cmds.listRelatives(verts[0].split('.')[0], shapes=True,
                              noIntermediate=True, fullPath=True)[0]
    closest = cmds.createNode('closestPointOnMesh', n='tempCPM')
    cmds.connectAttr(mesh + '.worldMesh[0]', closest + '.inMesh')
    try:
        for vertex in verts:
            index = int(vertex.split('[')[-1].rstrip(']'))
            value = cmds.getAttr('%s.%s[%d]' % (source, attr, index))
            pos = cmds.pointPosition(vertex, world=True)
            pos[axis] *= -1
            cmds.setAttr(closest + '.inPosition', *pos)
            twin = cmds.getAttr(closest + '.closestVertexIndex')
            cmds.setAttr('%s.%s[%d]' % (dest, attr, twin), value)
    finally:
        cmds.delete(closest)


# ---------------------------------------------------------------------------
# proxy meshes
# ---------------------------------------------------------------------------
def volume(node):
    box = cmds.exactWorldBoundingBox(node)
    return (box[3] - box[0]) * (box[4] - box[1]) * (box[5] - box[2])


def _proxy_sources(top, suffix):
    return [n for n in cmds.ls(top, dag=True, type='transform') or []
            if suffix in n]


def average_volume(top, suffix):
    """Average bounding-box volume of the meshes below `top` whose name
    contains `suffix`."""
    volumes = [volume(n) for n in _proxy_sources(top, suffix)]
    if not volumes:
        warn('no "%s" meshes found under %s.' % (suffix, top))
        return 0.0
    return sum(volumes) / len(volumes)


def make_proxy(top, suffix, low=1, mid=2, high=4, exclude=0.0):
    """Shrink-wrapped cube proxies for every mesh below `top` whose name
    contains `suffix`.

    Small, average and big meshes (by bounding-box volume) get cubes with
    low / mid / high subdivisions. Meshes smaller than `exclude` are skipped.
    """
    if not top or not cmds.objExists(top):
        return warn('pick the top node of the asset.')
    if low <= 0:
        return warn('the low resolution must be at least 1.')
    average = average_volume(top, suffix)
    resolution = low
    made = []
    for node in _proxy_sources(top, suffix):
        size = volume(node)
        if size <= exclude:
            continue
        if size < average:
            resolution = mid if size > average - average % 25 else low
        elif size > average:
            resolution = high if size > average + average % 25 else mid
        node_shapes = shapes(node)
        if not node_shapes or cmds.nodeType(node_shapes[0]) != 'mesh':
            continue
        tail = '_proxy' if '_' in suffix else 'proxy'
        name = node.replace(suffix, tail)
        if cmds.objExists(name):
            name = node.replace(
                suffix, '_%d%s' % (len(cmds.ls(name)), tail))
        cube = cmds.polyCube(w=100000, h=100000, d=100000, sx=resolution,
                             sy=resolution, sz=resolution, n=name)[0]
        cmds.setAttr(cube + '.t', *centroid([node], locator=False))
        parent = parent_of(node)
        if parent:
            cube = cmds.parent(cube, parent)[0]
        cmds.refresh()
        cmds.transferAttributes(
            node, cube, transferPositions=True, transferNormals=False,
            transferUVs=False, transferColors=False, searchMethod=3)
        cmds.delete(cube, constructionHistory=True)
        cmds.setAttr(cube + '.v', cmds.getAttr(node + '.v'))
        cmds.refresh()
        made.append(cube)
    print('mauTools: %d proxy mesh(es) made.' % len(made))
    return made


def wrap_out():
    """Duplicate each selected mesh as <name>_OUT, wrap-deformed by the
    original, and hide the original."""
    made = []
    for node in selected():
        copy = cmds.duplicate(node, rr=True)[0]
        cmds.select(copy, node, r=True)
        wrap = cmds.deformer(copy, type='wrap')[0]
        cmds.setAttr(node + '.v', 0)
        cmds.setAttr(wrap + '.exclusiveBind', 1)
        cmds.setAttr(wrap + '.autoWeightThreshold', 1)
        if parent_of(copy):
            copy = cmds.parent(copy, world=True)[0]
        made.append(cmds.rename(
            copy, node.split('|')[-1].replace('_geo', '_OUT', 1)))
    return made


# ---------------------------------------------------------------------------
# component selection
# ---------------------------------------------------------------------------
def invert_components():
    """Invert the vertex / edge / face selection on its mesh."""
    sel = selected(fl=True)
    if not sel or '.' not in sel[0]:
        return warn('select some mesh components.')
    node, comp = sel[0].split('.', 1)
    cmds.select('%s.%s[*]' % (node, comp.split('[')[0]), toggle=True)
    return selected(fl=True)


def mirror_components(components=None, tolerance=0.001, axis=0, world=False,
                      select=True, add=False):
    """Find the mirrored twins of mesh vertices, edges, faces or UVs.

    components  list of components (default: the selection)
    tolerance   how far a vertex may be from the exact mirrored position
    axis        0 1 2 = X Y Z
    world       mirror in world space instead of object space
    add         keep the original components in the result

    After n_mirrorComponents by Catalin Niculescu
    (3desque.wordpress.com/2011/03/23/n_mirrorcomponents).
    """
    components = components or selected()
    if not components:
        return warn('select some mesh components.')
    flat = cmds.ls(components, fl=True)
    kind = flat[0].split('.')[-1].split('[')[0] if '.' in flat[0] else ''
    convert = {'e': 'fromEdge', 'f': 'fromFace', 'map': 'fromUV'}
    if kind not in convert and kind != 'vtx':
        return warn('the first selected item is not a mesh component.')
    verts = components
    if kind in convert:
        verts = cmds.polyListComponentConversion(
            components, toVertex=True, **{convert[kind]: True})

    space = om.MSpace.kWorld if world else om.MSpace.kObject
    sel = om.MSelectionList()
    for item in verts:
        sel.add(item)
    mirrored = []
    for i in range(sel.length()):
        path, comp = sel.getComponent(i)
        if comp.isNull():
            continue
        mesh = om.MFnMesh(path)
        it = om.MItMeshVertex(path, comp)
        while not it.isDone():
            point = it.position(space)
            setattr(point, 'xyz'[axis], -getattr(point, 'xyz'[axis]))
            face = mesh.getClosestPoint(point, space)[1]
            for vertex in mesh.getPolygonVertices(face):
                if mesh.getPoint(vertex, space).isEquivalent(
                        point, tolerance):
                    mirrored.append(
                        '%s.vtx[%d]' % (path.fullPathName(), vertex))
                    break
            it.next()

    back = {'e': 'toEdge', 'f': 'toFace', 'map': 'toUV'}
    if kind in back and mirrored:
        flags = {'fromVertex': True, back[kind]: True}
        if kind != 'map':
            flags['internal'] = True
        mirrored = cmds.polyListComponentConversion(mirrored, **flags)
    if add:
        mirrored = list(mirrored) + list(components)
    if select and mirrored:
        cmds.select(mirrored, r=True)
    return mirrored


def transfer_selection(radius=0.1):
    """Select the components of the first mesh that fall inside the volume
    of the second one. Needs the SOuP plug-in."""
    sel = selected()
    if len(sel) != 2:
        return warn('select the mesh to pick on, then the volume mesh.')
    start = time.perf_counter()
    try:
        if not cmds.pluginInfo('SOuP', q=True, loaded=True):
            cmds.loadPlugin('SOuP')
    except RuntimeError:
        return warn('the SOuP plug-in is needed for this tool.')
    for node in sel:
        node_shapes = shapes(node)
        if not node_shapes or cmds.nodeType(node_shapes[0]) != 'mesh':
            return warn('%s is not a mesh.' % node)
    group = cmds.createNode('group')
    bound = cmds.createNode('boundingObject')
    bound_parent = cmds.listRelatives(bound, parent=True)
    try:
        cmds.connectAttr(sel[0] + '.worldMesh', group + '.inGeometry')
        cmds.connectAttr(bound + '.outData', group + '.boundingObjects[0]')
        cmds.connectAttr(
            bound + '.outParentMatrix',
            group + '.boundingObjects[0].boundParentMatrix')
        cmds.connectAttr(sel[1] + '.worldMesh', bound + '.inMesh')
        cmds.setAttr(bound + '.type', 3)
        cmds.setAttr(bound + '.pointRadius', radius)
        found = [sel[0] + '.' + c
                 for c in cmds.getAttr(group + '.outComponents') or []]
    finally:
        cmds.delete([group, bound] + (bound_parent or []))
    if found:
        cmds.select(found, r=True)
    print('mauTools: %d component(s) in %.2fs'
          % (len(found), time.perf_counter() - start))
    return found
