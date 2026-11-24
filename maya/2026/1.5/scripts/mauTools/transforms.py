"""Transform tools: match, step rotate, flip, centroid, world-space copy,
animation transfer and motion curves.

Replaces mnmMatcher.py, transformTools.py, transAnim.py, curveMG.py,
refPlane.py, centroidFast.mel and the world-position half of
readWriteAttr.mel.
"""
import json
import math
import os

from maya import cmds
import maya.api.OpenMaya as om

from . import selected, warn, shapes, tmp_file, remap_namespace

WORLD_FILE = 'mauTools_worldPos.json'
REF_PLANE = 'frpTMP'


# ---------------------------------------------------------------------------
# match
# ---------------------------------------------------------------------------
def match(translate=None, rotate=None, scale=None, to_first=False):
    """Match the selected nodes to the last selected one.

    translate / rotate / scale are None (leave alone) or three booleans, one
    per axis. With to_first=True everything is matched to the first selected
    node instead.
    """
    sel = selected()
    if len(sel) < 2:
        return warn('select the nodes to move, then the node to match to.')
    if to_first:
        sel.reverse()
    flags = {}
    for prefix, axes in (('p', translate), ('r', rotate), ('s', scale)):
        if axes and any(axes):
            for axis, state in zip('xyz', axes):
                flags[prefix + axis] = bool(state)
    if not flags:
        return warn('nothing to match, tick at least one axis.')
    cmds.matchTransform(*sel, **flags)


def rotate_step(angle, axes=(False, True, False), world=False):
    """Rotate the selection by `angle` degrees around every ticked axis."""
    for node in selected():
        for index, state in enumerate(axes):
            if state:
                value = [0.0, 0.0, 0.0]
                value[index] = angle
                cmds.rotate(
                    value[0], value[1], value[2], node, relative=True,
                    worldSpace=world, objectSpace=not world)


# ---------------------------------------------------------------------------
# flip
# ---------------------------------------------------------------------------
def mirror(axis=0, translate=True, rotate=True):
    """Mirror world position / rotation across the plane of `axis` (0 1 2).

    One node selected: a locator named <node>_FLIP receives the mirror.
    An even number selected: the first half is mirrored onto the second half.
    """
    nodes = selected()
    if not nodes:
        return warn('select something to flip.')
    if len(nodes) == 1:
        short = nodes[0].split('|')[-1].rpartition(':')[2]
        nodes.append(cmds.spaceLocator(n=short + '_FLIP')[0])
    if len(nodes) % 2:
        return warn('select one node, or the sources followed by the same '
                    'number of destinations.')
    half = len(nodes) // 2
    for source, dest in zip(nodes[:half], nodes[half:]):
        pos = cmds.xform(source, q=True, ws=True, rp=True)
        rot = cmds.xform(source, q=True, ws=True, ro=True)
        if translate:
            pos[axis] *= -1
            cmds.move(pos[0], pos[1], pos[2], dest, absolute=True,
                      worldSpace=True, rotatePivotRelative=True)
        if rotate:
            if axis == 0:
                rot = (rot[0], -rot[1], -rot[2])
            elif axis == 1:
                rot = (rot[0], -rot[1], -rot[2] + 180)
            else:
                rot = (-rot[0], -rot[1], rot[2])
            cmds.xform(dest, ws=True, ro=rot)
    cmds.select(nodes[half:], r=True)
    return nodes[half:]


def reference_plane(axis=0, show=True):
    """Show or hide a template plane on the mirror plane of `axis`."""
    sel = selected()
    if cmds.objExists(REF_PLANE):
        cmds.delete(REF_PLANE)
    if show:
        plane = cmds.polyPlane(n=REF_PLANE, w=1, h=1, sx=1, sy=1,
                               ax=(0, 0, 1), cuv=2, ch=False)[0]
        cmds.setAttr(plane + ('.rotateY', '.rotateX', '.rotateZ')[axis], 90)
        for shape in shapes(plane):
            cmds.setAttr(shape + '.overrideEnabled', 1)
            cmds.setAttr(shape + '.overrideLevelOfDetail', 1)
    if sel:
        cmds.select(sel, r=True)
    else:
        cmds.select(cl=True)


# ---------------------------------------------------------------------------
# centroid / average
# ---------------------------------------------------------------------------
def _chunks(flat):
    return [flat[i:i + 3] for i in range(0, len(flat), 3)]


def points_of(nodes):
    """World-space points of the given components, meshes, surfaces or
    transforms."""
    points = []
    components = cmds.filterExpand(nodes, ex=True, sm=(28, 31)) or []
    for comp in components:
        points.append(cmds.xform(comp, q=True, ws=True, t=True)[:3])
    if components:
        return points
    for node in nodes:
        node_shapes = shapes(node) or (
            [node] if cmds.objectType(node, isAType='shape') else [])
        shape = node_shapes[0] if node_shapes else None
        kind = cmds.nodeType(shape) if shape else ''
        if kind == 'mesh':
            points += _chunks(
                cmds.xform(shape + '.vtx[*]', q=True, ws=True, t=True))
        elif kind == 'nurbsSurface':
            max_u = cmds.getAttr(shape + '.maxValueU')
            max_v = cmds.getAttr(shape + '.maxValueV')
            for i in range(10):
                for j in range(10):
                    points.append(cmds.pointOnSurface(
                        shape, u=max_u * i / 10.0, v=max_v * j / 10.0,
                        position=True))
        elif kind == 'nurbsCurve':
            points += _chunks(
                cmds.xform(shape + '.cv[*]', q=True, ws=True, t=True))
        else:
            points.append(cmds.xform(node, q=True, ws=True, rp=True))
    return points


def centroid(nodes=None, locator=True):
    """Average position of the selected components / objects.

    Returns the new locator, or the position itself when locator=False.
    """
    nodes = nodes or selected()
    if not nodes:
        return warn('select components or objects to find the centroid of.')
    points = points_of(nodes)
    if not points:
        return warn('no points found in the selection.')
    center = [sum(p[i] for p in points) / len(points) for i in range(3)]
    if not locator:
        return center
    loc = cmds.spaceLocator()[0]
    cmds.xform(loc, ws=True, t=center)
    return loc


def average_locator():
    """Locator at the average position and rotation of the selection."""
    sel = selected()
    if not sel:
        return warn('select the transforms to average.')
    pos = [cmds.xform(n, q=True, ws=True, rp=True) for n in sel]
    rot = [cmds.xform(n, q=True, ws=True, ro=True) for n in sel]
    loc = cmds.spaceLocator(n='centerLoc')[0]
    cmds.xform(loc, ws=True, t=[sum(p[i] for p in pos) / len(sel)
                                for i in range(3)])
    cmds.xform(loc, ws=True, ro=[sum(r[i] for r in rot) / len(sel)
                                 for i in range(3)])
    return loc


def closest_transform(farthest=False):
    """Of the selected transforms, the one closest to (or farthest from) the
    last selected. Returns (node, distance)."""
    sel = selected(type='transform')
    if len(sel) < 2:
        return warn('select at least two transforms, the reference last.')
    center = cmds.xform(sel[-1], q=True, ws=True, rp=True)
    found = []
    for node in sel[:-1]:
        found.append(
            (math.dist(center, cmds.xform(node, q=True, ws=True, rp=True)),
             node))
    distance, node = max(found) if farthest else min(found)
    return node, distance


def matrix_constraint():
    """Parent-constraint the second selected node to the first with matrix
    nodes (multMatrix + decomposeMatrix), keeping the current offset."""
    sel = selected()
    if len(sel) != 2:
        return warn('select the driver, then the driven node.')
    driver, driven = sel
    offset = (om.MMatrix(cmds.getAttr(driven + '.worldMatrix[0]')) *
              om.MMatrix(cmds.getAttr(driver + '.worldMatrix[0]')).inverse())
    mult = cmds.createNode('multMatrix')
    decompose = cmds.createNode('decomposeMatrix')
    cmds.setAttr(mult + '.matrixIn[0]', list(offset), type='matrix')
    cmds.connectAttr(driver + '.matrix', mult + '.matrixIn[1]')
    cmds.connectAttr(mult + '.matrixSum', decompose + '.inputMatrix')
    cmds.connectAttr(decompose + '.outputTranslate', driven + '.translate')
    cmds.connectAttr(decompose + '.outputRotate', driven + '.rotate')
    return mult, decompose


# ---------------------------------------------------------------------------
# world position copy / paste (through a temp file, so it works between
# Maya sessions)
# ---------------------------------------------------------------------------
def store_world(nodes=None):
    nodes = nodes or selected()
    if not nodes:
        return warn('select the nodes to store.')
    data = []
    for node in nodes:
        data.append({
            'node': node,
            't': cmds.xform(node, q=True, ws=True, t=True),
            'ro': cmds.xform(node, q=True, ws=True, ro=True),
            's': cmds.xform(node, q=True, r=True, s=True)})
    path = tmp_file(WORLD_FILE)
    with open(path, 'w') as handle:
        json.dump(data, handle, indent=1)
    print('mauTools: world transforms of %d node(s) stored in %s'
          % (len(data), path))


def restore_world():
    """Apply the stored transforms. If something is selected, its namespace
    is used to find the nodes."""
    path = tmp_file(WORLD_FILE)
    if not os.path.isfile(path):
        return warn('nothing stored yet.')
    with open(path) as handle:
        data = json.load(handle)
    sel = selected()
    done = 0
    for item in data:
        node = remap_namespace(item['node'], sel[0]) if sel else item['node']
        if not cmds.objExists(node):
            warn('%s not found, skipped.' % node)
            continue
        cmds.xform(node, ws=True, t=item['t'])
        cmds.xform(node, ws=True, ro=item['ro'])
        cmds.xform(node, s=item['s'])
        done += 1
    print('mauTools: world transforms applied to %d node(s).' % done)


# ---------------------------------------------------------------------------
# animation
# ---------------------------------------------------------------------------
def transfer_anim(world=False, offset=0.0, simplify=False):
    """Copy the animation curves of the first selected node to the second.

    world     re-key translate / rotate / scale so the second node follows
              the first one in world space on every frame
    offset    shift the copied keys in time
    simplify  run Maya's simplify filter on the copied curves
    """
    sel = selected()
    if len(sel) != 2:
        return warn('select the animated node, then the node to copy to.')
    source, dest = sel
    curves = cmds.listConnections(
        source, s=True, d=False, type='animCurve') or []
    if not curves:
        return warn('%s has no animation to copy.' % source)
    old = cmds.listConnections(dest, s=True, d=False, type='animCurve') or []
    if old:
        cmds.delete(old)

    source_path = cmds.ls(source, long=True)
    copies, attrs = [], []
    for curve in curves:
        for plug in cmds.listConnections(
                curve + '.output', s=False, d=True, plugs=True) or []:
            node, attr = plug.split('.', 1)
            if cmds.ls(node, long=True) != source_path:
                continue
            if not cmds.objExists(dest + '.' + attr):
                continue
            copy = cmds.duplicate(curve)[0]
            cmds.connectAttr(copy + '.output', dest + '.' + attr, force=True)
            copies.append(copy)
            attrs.append(attr)
    if not copies:
        return warn('no matching attributes on %s.' % dest)

    if world:
        groups = {'position': 'translate', 'rotation': 'rotate',
                  'scale': 'scale'}
        flags = {flag: any(a.startswith(name) for a in attrs)
                 for flag, name in groups.items()}
        keyed = [a for a in attrs if a.startswith(tuple(groups.values()))]
        times = cmds.keyframe(copies, q=True, timeChange=True) or []
        if keyed and times:
            auto = cmds.autoKeyframe(q=True, state=True)
            now = cmds.currentTime(q=True)
            cmds.autoKeyframe(state=False)
            try:
                for frame in range(int(min(times)), int(max(times)) + 1):
                    cmds.currentTime(frame)
                    cmds.matchTransform(dest, source, **flags)
                    cmds.setKeyframe(dest, attribute=keyed)
            finally:
                cmds.autoKeyframe(state=auto)
                cmds.currentTime(now)

    if offset:
        cmds.keyframe(copies, e=True, includeUpperBound=True, relative=True,
                      option='move', timeChange=offset)
    if simplify:
        for copy in copies:
            cmds.filterCurve(copy, filter='simplify', timeTolerance=0.05)
    cmds.select(sel, r=True)
    return copies


def motion_curve(nodes=None):
    """Draw a curve through the world position of each selected node over
    the playback range."""
    nodes = nodes or selected(type='transform')
    if not nodes:
        return warn('select the animated transforms.')
    start = int(cmds.playbackOptions(q=True, min=True))
    end = int(cmds.playbackOptions(q=True, max=True))
    now = cmds.currentTime(q=True)
    points = dict((n, []) for n in nodes)
    try:
        for frame in range(start, end + 1):
            cmds.currentTime(frame)
            for node in nodes:
                points[node].append(
                    tuple(cmds.xform(node, q=True, ws=True, rp=True)))
    finally:
        cmds.currentTime(now)
    curves = []
    for node in nodes:
        short = node.split('|')[-1].rpartition(':')[2]
        curves.append(cmds.curve(n=short + 'CRV', d=1, p=points[node]))
    cmds.select(nodes, r=True)
    return curves
