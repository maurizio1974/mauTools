"""Rigging tools: joints, IK helpers, utility nodes, rivets and follicles.

Replaces the joint / IK / node procedures of flipper.mel, mgOrientJNT.mel
and mRivet.py.
"""
import math
import re

from maya import cmds

from . import selected, warn, shapes, parent_of

UTILITY_NODES = [
    'multiplyDivide', 'reverse', 'plusMinusAverage', 'nearestPointOnMesh',
    'closestPointOnMesh', 'closestPointOnSurface', 'curveInfo',
    'vectorProduct', 'samplerInfo', 'condition', 'distanceBetween',
    'setRange', 'clamp', 'blendColors', 'arrayMapper', 'ramp',
    'singleShadingSwitch', 'doubleShadingSwitch', 'tripleShadingSwitch',
    'quadShadingSwitch']

HOME_SUFFIXES = (
    'jnt', 'null', 'HmNull', 'NULL', 'JNT', 'env', 'ENV', 'FK', 'ctrl')

ORIENT_ORDERS = ('xyz', 'yzx', 'zxy', 'zyx', 'yxz', 'xzy', 'none')
SECONDARY_AXES = ('xup', 'xdown', 'yup', 'ydown', 'zup', 'zdown', 'none')


def _prompt(title, text=''):
    """Ask for a name; returns '' when cancelled."""
    result = cmds.promptDialog(
        title=title, message='Enter Name:', text=text,
        button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel',
        dismissString='Cancel')
    return cmds.promptDialog(q=True, text=True) if result == 'OK' else ''


def _short(node):
    return node.split('|')[-1]


# ---------------------------------------------------------------------------
# utility nodes
# ---------------------------------------------------------------------------
def create_node(node_type, name=''):
    if name:
        return cmds.createNode(node_type, n=name)
    return cmds.createNode(node_type)


def lock_nodes(lock=True):
    sel = selected()
    if sel:
        cmds.lockNode(sel, lock=lock)


def clean_unknown_nodes():
    """Unlock and delete every unknown node in the scene."""
    count = 0
    for node in cmds.ls(type=('unknown', 'unknownDag', 'unknownTransform')):
        if not cmds.objExists(node):
            continue
        cmds.lockNode(node, lock=False)
        cmds.delete(node)
        count += 1
    print('mauTools: %d unknown node(s) deleted.' % count)
    return count


# ---------------------------------------------------------------------------
# joints
# ---------------------------------------------------------------------------
def joints_on_vertices():
    """A joint on every selected vertex, or on every vertex of the selected
    meshes."""
    sel = selected(fl=True)
    if not sel:
        return warn('select a mesh or some vertices.')
    verts = cmds.filterExpand(sel, sm=31, ex=True) or []
    if not verts:
        for node in sel:
            verts += cmds.ls(node + '.vtx[*]', fl=True) or []
    made = []
    for vert in verts:
        cmds.select(cl=True)
        made.append(cmds.joint(p=cmds.pointPosition(vert, world=True)))
    cmds.select(made, r=True)
    return made


def home_null(nodes=None):
    """Put every selected node under a locator ("Hm_null") that takes its
    transform, leaving the node itself with zero rotation."""
    made = []
    for node in nodes or selected():
        short = _short(node)
        name = short + 'Hm_null'
        for suffix in HOME_SUFFIXES:
            if short.endswith(suffix):
                name = short[:-len(suffix)] + 'Hm_null'
        if cmds.objExists(name):
            name = _prompt('Name for the home null of ' + short, name)
        if not name or cmds.objExists(name):
            warn('skipped %s, the home null name is taken.' % short)
            continue
        parent = parent_of(node)
        loc = cmds.spaceLocator(n=name)[0]
        cmds.matchTransform(loc, node)
        node = cmds.parent(node, loc)[0]
        if cmds.attributeQuery('jointOrient', node=node, exists=True):
            cmds.setAttr(node + '.jointOrient', 0, 0, 0)
        cmds.setAttr(node + '.rotate', 0, 0, 0)
        if parent:
            loc = cmds.parent(loc, parent)[0]
        made.append(loc)
    return made


def orient_joints(order='xyz', secondary='yup', children=True,
                  zero_scale=True):
    """Orient the selected joints to the given axis order.

    order      one of ORIENT_ORDERS
    secondary  one of SECONDARY_AXES, the world direction of the second axis
    """
    joints = selected(type='joint')
    if not joints:
        return warn('select the joints to orient.')
    flags = {'orientJoint': order, 'children': children,
             'zeroScaleOrient': zero_scale}
    if secondary != 'none' and order != 'none':
        flags['secondaryAxisOrient'] = secondary
    for joint in joints:
        cmds.joint(joint, e=True, **flags)
    cmds.select(joints, r=True)


def orient_joint_like(target):
    """Orient the selected joint chain as if `target` were the world."""
    joints = selected(type='joint')
    if not joints:
        return warn('select the joint to orient.')
    if not target or not cmds.objExists(target):
        return warn('pick the transform the chain should be oriented like.')
    joint = joints[0]
    pos = cmds.xform(target, q=True, ws=True, t=True)
    rot = cmds.xform(target, q=True, ws=True, ro=True)
    target_parent = parent_of(target)
    joint_parent = parent_of(joint)

    joint = cmds.parent(joint, target)[0]
    if target_parent:
        target = cmds.parent(target, world=True)[0]
    cmds.setAttr(target + '.t', 0, 0, 0)
    cmds.setAttr(target + '.r', 0, 0, 0)
    cmds.joint(joint, e=True, orientJoint='xyz', secondaryAxisOrient='yup',
               children=True, zeroScaleOrient=True)
    cmds.setAttr(target + '.t', *pos)
    cmds.setAttr(target + '.r', *rot)
    if joint_parent:
        joint = cmds.parent(joint, joint_parent)[0]
    else:
        joint = cmds.parent(joint, world=True)[0]
    if target_parent:
        cmds.parent(target, target_parent)

    # the last joint of the chain has nothing to aim at
    tail = cmds.ls(joint, dag=True, type='joint', long=True) or []
    if len(tail) > 1:
        cmds.setAttr(tail[-1] + '.jointOrient', 0, 0, 0)
    cmds.select(joint, r=True)


def shape_to_joints():
    """Give every joint in the selected hierarchies a copy of the shape of
    the last selected object, so the joints can be picked as controls."""
    sel = selected(long=True)
    if len(sel) < 2:
        return warn('select the joints, then the curve to use as shape.')
    control = sel[-1]
    if not shapes(control):
        return warn('the last selected object has no shape.')
    for joint in cmds.ls(sel[:-1], dag=True, type='joint', long=True) or []:
        copy = cmds.duplicate(control)[0]
        for shape in shapes(copy):
            shape = cmds.parent(shape, joint, relative=True, shape=True)[0]
            cmds.rename(shape, _short(joint) + 'Shape')
        cmds.delete(copy)
    cmds.select(sel, r=True)


# ---------------------------------------------------------------------------
# IK
# ---------------------------------------------------------------------------
def pole_vector(constrain=False):
    """Locator (with offset groups) on the pole-vector plane of each selected
    IK handle; constrain=True also adds the poleVectorConstraint."""
    handles = selected(type='ikHandle')
    if not handles:
        return warn('select an IK handle first.')
    made = []
    for ik in handles:
        ik_pos = cmds.xform(ik, q=True, ws=True, t=True)
        pole = cmds.getAttr(ik + '.poleVector')[0]
        start = cmds.listConnections(ik + '.startJoint', s=True, d=False)[0]
        start_pos = cmds.xform(start, q=True, ws=True, t=True)
        name = _short(ik).replace('ikHandle', '', 1)

        loc = cmds.spaceLocator(n=name + '_upv_null')[0]
        rotate_grp = cmds.group(loc, n=name + '_upv_mc_null')
        orient_grp = cmds.group(rotate_grp, n=name + '_upv_hm_null')
        cmds.setAttr(orient_grp + '.t', *start_pos)
        cmds.setAttr(loc + '.tz', math.dist(ik_pos, start_pos) / 2.0)
        cmds.delete(cmds.aimConstraint(
            ik, orient_grp, aimVector=(0, -1, 0), upVector=(0, 0, 1),
            worldUpType='vector', worldUpVector=pole))
        if constrain:
            cmds.poleVectorConstraint(loc, ik)
        made.append(loc)
    return made


def _add_attr(node, name, **flags):
    if not cmds.attributeQuery(name, node=node, exists=True):
        cmds.addAttr(node, longName=name, attributeType='double',
                     keyable=True, **flags)


def _chain(start, end):
    """Joints from start to end, or None if end is not below start."""
    start = cmds.ls(start, long=True)[0]
    node = cmds.ls(end, long=True)[0]
    chain = [node]
    while node != start:
        node = parent_of(node)
        if not node:
            return None
        chain.append(node)
    return chain[::-1]


def _hide_shape(node):
    for shape in shapes(node):
        cmds.setAttr(shape + '.visibility', 0)


def _world_position(node):
    return shapes(node)[0] + '.worldPosition[0]'


def stretchy_ik():
    """Make the selected IK handles stretchy.

    Adds two attributes to each handle: "stretchy" (0-1 switch) and "lenght"
    (extra rest length). Spline IK handles scale their joints along X with
    the length of the curve instead.
    """
    handles = selected()
    if not handles:
        return warn('select one or more IK handles.')
    for ik in handles:
        if cmds.nodeType(ik) != 'ikHandle':
            warn('%s is not an IK handle, skipped.' % ik)
            continue
        _add_attr(ik, 'stretchy', defaultValue=1, minValue=0, maxValue=1)
        _add_attr(ik, 'lenght', defaultValue=0)
        if cmds.ikHandle(ik, q=True, solver=True) == 'ikSplineSolver':
            _stretchy_spline(ik)
        else:
            _stretchy_chain(ik)


def _stretchy_chain(ik):
    start = cmds.ikHandle(ik, q=True, startJoint=True)
    effector = cmds.ikHandle(ik, q=True, endEffector=True)
    ends = cmds.listConnections(
        effector + '.translateX', s=True, d=False, type='joint')
    if not ends:
        return warn('could not find the end joint of %s.' % ik)
    end = ends[0]
    chain = _chain(start, end)
    if not chain:
        return warn('%s is not below %s.' % (end, start))
    start_parent = parent_of(start)
    ik_parent = parent_of(ik)

    short = _short(start)
    name = short[:-3] if short.endswith('jnt') else _prompt(
        'Stretchy Name', short)
    if not name:
        return

    # rest length of the chain
    length = 0.0
    for joint in chain[1:]:
        length += cmds.getAttr(joint + '.tx')
        length -= length * 0.001

    # locators measuring the current distance ...
    start_loc = cmds.spaceLocator(n=name + 'SD')[0]
    end_loc = cmds.spaceLocator(n=name + 'ED')[0]
    _hide_shape(start_loc)
    cmds.setAttr(shapes(end_loc)[0] + '.localScale', 0.25, 0.25, 0.25)
    cmds.matchTransform(start_loc, start, pos=True, rot=True)
    cmds.matchTransform(end_loc, end, pos=True, rot=True)

    # ... and the rest distance, which follows the scale of the rig
    start_rest = cmds.spaceLocator(n=name + 'SDS')[0]
    end_rest = cmds.spaceLocator(n=name + 'EDS')[0]
    _hide_shape(start_rest)
    _hide_shape(end_rest)
    cmds.matchTransform(start_rest, start, pos=True, rot=True)
    aim = cmds.spaceLocator(n='TempAimLocStretch_null')[0]
    cmds.matchTransform(aim, start, pos=True, rot=True)
    cmds.delete(cmds.aimConstraint(end, aim))
    end_rest = cmds.parent(end_rest, aim)[0]
    cmds.setAttr(end_rest + '.t', length, 0, 0)
    cmds.setAttr(end_rest + '.r', 0, 0, 0)
    end_rest = cmds.parent(end_rest, world=True)[0]
    cmds.delete(aim)

    distance = cmds.shadingNode('distanceBetween', asUtility=True,
                                n=name + 'DD')
    rest = cmds.shadingNode('distanceBetween', asUtility=True,
                            n=name + 'DDS')
    cmds.connectAttr(_world_position(start_loc), distance + '.point1', f=True)
    cmds.connectAttr(_world_position(end_loc), distance + '.point2', f=True)
    cmds.connectAttr(_world_position(start_rest), rest + '.point1', f=True)
    cmds.connectAttr(_world_position(end_rest), rest + '.point2', f=True)

    ratio = cmds.createNode('multiplyDivide', n=name + 'MD')
    cmds.setAttr(ratio + '.operation', 2)                     # divide
    longer = cmds.shadingNode('condition', asUtility=True, n=name + 'CND')
    cmds.setAttr(longer + '.operation', 4)                    # less than
    switch = cmds.shadingNode('condition', asUtility=True,
                              n=name + 'SwitchCND')
    cmds.setAttr(switch + '.operation', 1)                    # not equal
    cmds.connectAttr(ik + '.stretchy', switch + '.firstTerm', f=True)
    cmds.connectAttr(rest + '.distance', longer + '.firstTerm', f=True)
    cmds.connectAttr(distance + '.distance', longer + '.secondTerm', f=True)

    rest_grp = cmds.group(em=True, n=_short(end_rest) + '_grp')
    cmds.matchTransform(rest_grp, end_rest, pos=True, rot=True)
    end_rest = cmds.parent(end_rest, rest_grp)[0]
    cmds.connectAttr(ik + '.lenght', end_rest + '.tx', f=True)

    cmds.connectAttr(distance + '.distance', ratio + '.input1X', f=True)
    cmds.connectAttr(rest + '.distance', ratio + '.input2X', f=True)
    cmds.connectAttr(ratio + '.outputX', longer + '.colorIfTrueR', f=True)
    cmds.connectAttr(longer + '.outColorR', switch + '.colorIfTrueR', f=True)

    # multDoubleLinear is called multDL from Maya 2026
    mult_type = ('multDL' if 'multDL' in cmds.allNodeTypes()
                 else 'multDoubleLinear')
    for joint in chain[1:]:
        mult = cmds.createNode(mult_type, n=name + 'MDL')
        cmds.setAttr(mult + '.input1', cmds.getAttr(joint + '.tx'))
        cmds.connectAttr(switch + '.outColorR', mult + '.input2', f=True)
        cmds.connectAttr(mult + '.output', joint + '.tx', f=True)

    if ik_parent:
        end_loc = cmds.parent(end_loc, ik_parent)[0]
    if start_parent:
        cmds.parent(rest_grp, start_rest, start_loc, start_parent)
    cmds.parent(ik, end_loc)


def _stretchy_spline(ik):
    curve = cmds.ikHandle(ik, q=True, curve=True)
    if not curve:
        return warn('could not find the curve of %s.' % ik)
    name = _short(ik)
    info = cmds.createNode('curveInfo', n=name + 'CINFO')
    ratio = cmds.createNode('multiplyDivide', n=name + 'MD')
    cmds.connectAttr(curve + '.worldSpace[0]', info + '.inputCurve', f=True)
    cmds.connectAttr(info + '.arcLength', ratio + '.input1X', f=True)
    cmds.setAttr(ratio + '.input2X', cmds.getAttr(info + '.arcLength'))
    cmds.setAttr(ratio + '.operation', 2)
    joints = cmds.ikHandle(ik, q=True, jointList=True) or cmds.ls(
        cmds.ikHandle(ik, q=True, startJoint=True), dag=True, type='joint')
    for joint in joints:
        cmds.connectAttr(ratio + '.outputX', joint + '.scaleX', f=True)


# ---------------------------------------------------------------------------
# rivets and follicles
# ---------------------------------------------------------------------------
def _edge_index(edge):
    return int(re.findall(r'\[(\d+)\]', edge)[-1])


def _loft(mesh_plug, edge1, edge2):
    """Loft a surface between two edges of a mesh; returns the loft node."""
    curves = []
    for i, edge in enumerate((edge1, edge2)):
        curve = cmds.createNode('curveFromMeshEdge', n='rCFME%d' % (i + 1))
        cmds.setAttr(curve + '.isHistoricallyInteresting', 1)
        cmds.setAttr(curve + '.edgeIndex[0]', _edge_index(edge))
        cmds.connectAttr(mesh_plug, curve + '.inputMesh')
        curves.append(curve)
    loft = cmds.createNode('loft', n='rivetLoft1')
    cmds.setAttr(loft + '.inputCurve', size=2)
    cmds.setAttr(loft + '.uniform', 1)
    cmds.setAttr(loft + '.reverseSurfaceNormals', 1)
    cmds.connectAttr(curves[0] + '.outputCurve', loft + '.inputCurve[0]')
    cmds.connectAttr(curves[1] + '.outputCurve', loft + '.inputCurve[1]')
    return loft


def _mesh_shape(component):
    node = component.split('.')[0]
    found = cmds.listRelatives(
        node, shapes=True, noIntermediate=True, fullPath=True)
    return found[0] if found else node


def _opposite_edges(face):
    """Two edges of a face that do not share a vertex."""
    def verts(edge):
        return set(cmds.ls(cmds.polyListComponentConversion(
            edge, fromEdge=True, toVertex=True), fl=True))

    edges = cmds.ls(cmds.polyListComponentConversion(
        face, fromFace=True, toEdge=True), fl=True)
    first = verts(edges[0])
    for edge in edges[1:]:
        if not first & verts(edge):
            return edges[0], edge
    return None


def _rivet_locator(edge1, edge2, use_input=False):
    shape = _mesh_shape(edge1)
    mesh_plug = shape + '.worldMesh[0]'
    if use_input:
        incoming = cmds.listConnections(
            shape + '.inMesh', s=True, d=False, plugs=True)
        if incoming:
            mesh_plug = incoming[0]
    loft = _loft(mesh_plug, edge1, edge2)
    info = cmds.createNode('pointOnSurfaceInfo', n='rPOSI1')
    cmds.setAttr(info + '.turnOnPercentage', 1)
    cmds.connectAttr(loft + '.outputSurface', info + '.inputSurface', f=True)

    loc = cmds.createNode('transform', n='mRivet1')
    cmds.createNode('locator', n=loc + 'Shape', p=loc)
    for attr in 'UV':
        cmds.addAttr(loc, ln=attr, at='double', k=True, min=0, max=1, dv=0.5)
        cmds.connectAttr(loc + '.' + attr, info + '.parameter' + attr)

    aim = cmds.createNode('aimConstraint', p=loc, n=loc + '_rAC1')
    cmds.setAttr(aim + '.target[0].targetWeight', 1)
    cmds.setAttr(aim + '.aimVector', 0, 1, 0, type='double3')
    cmds.setAttr(aim + '.upVector', 0, 0, 1, type='double3')
    for attr in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v'):
        cmds.setAttr(aim + '.' + attr, k=False)
    cmds.connectAttr(info + '.position', loc + '.translate')
    cmds.connectAttr(info + '.normal', aim + '.target[0].targetTranslate')
    cmds.connectAttr(info + '.tangentV', aim + '.worldUpVector')
    for axis in 'XYZ':
        cmds.connectAttr(aim + '.constraintRotate' + axis,
                         loc + '.rotate' + axis)
    return loc


def _follicle(u, v, matrix_node, surface=None, mesh=None):
    """Follicle transform with keyable U / V attributes."""
    shape = cmds.createNode('follicle')
    xform = cmds.listRelatives(shape, parent=True)[0]
    if surface:
        cmds.connectAttr(surface, shape + '.inputSurface')
    if mesh:
        cmds.connectAttr(mesh, shape + '.inputMesh')
    if matrix_node:
        cmds.connectAttr(matrix_node + '.worldMatrix[0]',
                         shape + '.inputWorldMatrix')
    for attr, value in (('U', u), ('V', v)):
        cmds.addAttr(xform, ln=attr, at='double', k=True, min=0, max=1,
                     dv=value)
        cmds.connectAttr(xform + '.' + attr, shape + '.parameter' + attr)
    cmds.connectAttr(shape + '.outTranslate', xform + '.translate')
    cmds.connectAttr(shape + '.outRotate', xform + '.rotate')
    return xform


def _loft_follicle(edge1, edge2):
    shape = _mesh_shape(edge1)
    loft = _loft(shape + '.outMesh', edge1, edge2)
    return _follicle(0.5, 0.5, cmds.listRelatives(shape, parent=True,
                                                  fullPath=True)[0],
                     surface=loft + '.outputSurface')


def rivet(pairs=True, follicles=False, use_input=False):
    """Rivets between the selected mesh edges.

    pairs      True: edges 1-2, 3-4 ...   False: edges 1-2, 2-3, 3-4 ...
    follicles  build follicles on the lofted surface instead of locators
    use_input  (locators only) read the mesh from what feeds its inMesh, so
               the rivet ignores later deformers
    """
    edges = cmds.filterExpand(sm=32) or []
    if len(edges) < 2:
        return warn('select at least two mesh edges.')
    made = []
    for i in range(0, len(edges) - 1, 2 if pairs else 1):
        if follicles:
            made.append(_loft_follicle(edges[i], edges[i + 1]))
        else:
            made.append(_rivet_locator(edges[i], edges[i + 1], use_input))
    cmds.select(made, r=True)
    return made


def follicle():
    """A follicle on every selected mesh face (needs UVs) or NURBS surface
    point."""
    sel = selected(fl=True)
    made = []
    for item in sel:
        if '.' not in item:
            continue
        node, comp = item.split('.', 1)
        shape = _mesh_shape(item)
        kind = cmds.nodeType(shape)
        owner = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
        if kind == 'nurbsSurface' and comp.startswith('uv['):
            u, v = [float(x) for x in re.findall(r'\[([^\]]+)\]', comp)]
            min_u, max_u = cmds.getAttr(shape + '.minMaxRangeU')[0]
            min_v, max_v = cmds.getAttr(shape + '.minMaxRangeV')[0]
            made.append(_follicle(
                (u - min_u) / (max_u - min_u), (v - min_v) / (max_v - min_v),
                owner, surface=shape + '.local'))
        elif kind == 'mesh' and comp.startswith('f['):
            flat = cmds.xform(item, q=True, ws=True, t=True)
            count = len(flat) // 3
            center = [sum(flat[i::3]) / count for i in range(3)]
            closest = cmds.createNode('closestPointOnMesh')
            cmds.connectAttr(shape + '.worldMesh[0]', closest + '.inMesh')
            cmds.setAttr(closest + '.inPosition', *center)
            u = cmds.getAttr(closest + '.parameterU')
            v = cmds.getAttr(closest + '.parameterV')
            cmds.delete(closest)
            made.append(_follicle(u, v, owner, mesh=shape + '.outMesh'))
    if not made:
        return warn('select mesh faces or NURBS surface points.')
    cmds.select(made, r=True)
    return made


def follicle_no_uv():
    """A follicle in the middle of every selected mesh face, built on a loft
    between two opposite edges, so the mesh does not need UVs."""
    faces = cmds.filterExpand(sm=34) or []
    if not faces:
        return warn('select one or more mesh faces.')
    made = []
    for face in faces:
        edges = _opposite_edges(face)
        if not edges:
            warn('%s has no opposite edges, skipped.' % face)
            continue
        made.append(_loft_follicle(*edges))
    if made:
        cmds.select(made, r=True)
    return made


def reverse_follicle():
    """Flip the selected loft follicles by swapping the two loft curves."""
    sel = selected()
    if not sel:
        return warn('select a follicle.')
    for node in sel:
        fol = [s for s in shapes(node) if cmds.nodeType(s) == 'follicle']
        lofts = fol and cmds.listConnections(
            fol[0] + '.inputSurface', s=True, d=False, type='loft')
        if not lofts:
            warn('skipped %s, it is not a loft follicle.' % node)
            continue
        loft = lofts[0]
        first = cmds.listConnections(
            loft + '.inputCurve[0]', s=True, d=False, plugs=True)[0]
        second = cmds.listConnections(
            loft + '.inputCurve[1]', s=True, d=False, plugs=True)[0]
        cmds.connectAttr(first, loft + '.inputCurve[1]', f=True)
        cmds.connectAttr(second, loft + '.inputCurve[0]', f=True)
