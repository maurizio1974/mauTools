# uncompyle6 version 3.7.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.17 (default, Sep 30 2020, 13:38:04) 
# [GCC 7.5.0]
# Embedded file name: D:/My Documents/maya/2020/scripts\weight_utils.py
# Compiled at: 2021-12-11 10:18:04
try:
    del om
    del om2
except:
    pass

import maya.cmds as cmds, maya.OpenMaya as om, maya.OpenMayaAnim as omAnim, maya.api.OpenMaya as om2, maya.api.OpenMayaAnim as omAnim2, json, re, xml.etree.ElementTree as ET, time
try:
    import numpy as np
except:
    cmds.warning('numpy is not installed: This will affect the speed of some functions')

try:
    import weight_utils_cmds
    if not cmds.pluginInfo('weight_utils_cmds', q=True, loaded=True):
        cmds.loadPlugin(weight_utils_cmds.__file__)
except:
    cmds.warning('Could not load the weight_utils_cmds plugin. Undo may not work for all functions')

def convert_transform_to_shape(transform):
    """
    Checks if the given node is a shape node, and if it isn't it will return the first shape node child. This exists so that the individual utils don't have to and therefore they run more quickly.
    
    transform = The node you want to test.
    
    Returns the given node if it is a shape node, and returns the first c
    """
    if not cmds.objExists(transform):
        cmds.error(('"{}" does not exist').format(transform))
    if cmds.nodeType(transform) == 'transform':
        shape_list = cmds.listRelatives(transform, s=True)
        if shape_list:
            return shape_list[0]
        cmds.error(('{} has no shapes').format(transform))
    else:
        if cmds.nodeType(transform) in ('mesh', 'nurbsSurface', 'nurbsCurve', 'lattice'):
            return transform
        cmds.error(('"{}" is not a valid shape').format(transform))


def get_component_list(shape):
    """ 
    Generates a list of all the components on the given shape.

    shape = The shape node whose components you want a list of. Example: "cubeShape1"
    
    Returns a list of all the components on the given shape as strings.
    """
    if cmds.nodeType(shape) == 'mesh':
        return [ ('{}.vtx[{}]').format(shape, index) for index in range(cmds.polyEvaluate(shape, v=True)) ]
    if cmds.nodeType(shape) == 'nurbsSurface':
        u_div = cmds.getAttr(shape + '.spansU') + cmds.getAttr(shape + '.degreeU')
        v_div = cmds.getAttr(shape + '.spansV') + cmds.getAttr(shape + '.degreeV')
        return [ ('{}.cv[{}][{}]').format(shape, u_index, v_index) for v_index in range(v_div) for u_index in range(u_div) ]
    if cmds.nodeType(shape) == 'nurbsCurve':
        curve_len = cmds.getAttr(shape + '.degree') + cmds.getAttr(shape + '.spans')
        if cmds.getAttr(shape + '.f') == 2:
            curve_len -= cmds.getAttr(shape + '.degree')
        return [ ('{}.cv[{}]').format(shape, index) for index in range(curve_len) ]
    if cmds.nodeType(shape) == 'lattice':
        s_div, t_div, u_div = cmds.lattice(shape, q=True, dv=True)
        return [ ('{}.pt[{}][{}][{}]').format(shape, s_index, t_index, u_index) for u_index in range(u_div) for t_index in range(t_div) for s_index in range(s_div) ]
    cmds.error(('"{}" is not a valid shape').format(shape))


def get_position_list(shape, prePose=True, object_space=True):
    """ 
    Generates a list of world space positions for all the components on the given shape.

    shape = The shape whose components you want the positions for. Example: "cubeShape1"
    prePose = When True, this function will return the list of positions for the shape prior to any deformations. 
    object_space = When True, this function will return the list of positions in object space.
    
    Returns a list of all the positions as tuples.
    """
    shape_type = cmds.nodeType(shape)
    if shape_type == 'transform':
        shape = convert_transform_to_shape(shape)
        shape_type = cmds.nodeType(shape)
    if prePose == True:
        transform = cmds.listRelatives(shape, p=True, f=True)[0]
        shape = cmds.listRelatives(transform, s=True, f=True)[(-1)]
    position_list = []
    if shape_type == 'mesh':
        mSelectionList = om2.MSelectionList()
        mSelectionList.add(shape)
        mObject = om2.MObject()
        mObject = mSelectionList.getDependNode(0)
        mDagPath = om2.MDagPath()
        mDagPath = mSelectionList.getDagPath(0)
        worldMatrix = mDagPath.inclusiveMatrix()
        position_list = om2.MFnMesh(mDagPath).getPoints()
        if not object_space:
            position_list = [ position * worldMatrix for position in position_list ]
        return [ tuple(pos)[0:3] for pos in position_list ]
    if shape_type == 'nurbsSurface':
        mSelectionList = om2.MSelectionList()
        mSelectionList.add(shape)
        mObject = om2.MObject()
        mObject = mSelectionList.getDependNode(0)
        mDagPath = om2.MDagPath()
        mDagPath = mSelectionList.getDagPath(0)
        worldMatrix = mDagPath.inclusiveMatrix()
        position_list = om2.MFnNurbsSurface(mDagPath).cvPositions()
        u_div = cmds.getAttr(shape + '.spansU') + cmds.getAttr(shape + '.degreeU')
        if cmds.getAttr(shape + '.fu') == 2:
            u_div -= cmds.getAttr(shape + '.degreeU')
        v_div = cmds.getAttr(shape + '.spansV') + cmds.getAttr(shape + '.degreeV')
        if cmds.getAttr(shape + '.fv') == 2:
            v_div -= cmds.getAttr(shape + '.degreeV')
        if not object_space:
            position_list = [ position * worldMatrix for position in position_list ]
        return [ tuple(pos)[0:3] for pos in position_list ]
    if shape_type == 'nurbsCurve':
        mSelectionList = om2.MSelectionList()
        mSelectionList.add(shape)
        mObject = om2.MObject()
        mObject = mSelectionList.getDependNode(0)
        mDagPath = om2.MDagPath()
        mDagPath = mSelectionList.getDagPath(0)
        worldMatrix = mDagPath.inclusiveMatrix()
        position_list = om2.MFnNurbsCurve(mDagPath).cvPositions()
        degreeU = cmds.getAttr(shape + '.degree')
        position_list = position_list[0:len(position_list) - degreeU]
        if not object_space:
            position_list = [ position * worldMatrix for position in position_list ]
        return [ tuple(pos)[0:3] for pos in position_list ]
    if shape_type == 'lattice':
        mSelectionList = om.MSelectionList()
        mSelectionList.add(shape)
        mDagPath = om.MDagPath()
        mSelectionList.getDagPath(0, mDagPath)
        worldMatrix = mDagPath.inclusiveMatrix()
        s_div = cmds.getAttr(shape + '.sDivisions')
        t_div = cmds.getAttr(shape + '.tDivisions')
        u_div = cmds.getAttr(shape + '.uDivisions')
        mFnLattice = omAnim.MFnLattice(mDagPath)
        position_list = []
        for u in range(u_div):
            for t in range(t_div):
                for s in range(s_div):
                    position_list.append(mFnLattice.point(s, t, u))

        if not object_space:
            position_list = [ position * worldMatrix for position in position_list ]
        return [ (pos[0], pos[1], pos[2]) for pos in position_list ]
    cmds.error(('"{}" is not a valid shape').format(shape))


def get_ordered_deformer_list(shape):
    """
    Finds the deformation order of the given shape.
    
    shape = The shape whose deformation order you are querying.
    
    Returns a list containing the names of the deformers from first to last in order of evaluation.
    """
    if not cmds.objExists(shape):
        cmds.error(('"{}" does not exist').format(shape))
    if cmds.nodeType(shape) == 'mesh':
        input_attr = 'inMesh'
    else:
        if cmds.nodeType(shape) == 'nurbsCurve':
            input_attr = 'create'
        elif cmds.nodeType(shape) == 'nurbsSurface':
            input_attr = 'create'
        elif cmds.nodeType(shape) == 'lattice':
            input_attr = 'latticeInput'
        else:
            return []
        deformer_list = []
        first_deformer = cmds.connectionInfo(shape + '.' + input_attr, sfd=True)
        if not first_deformer:
            return []

    def get_the_upstream_deformer(output_attr):
        deformer_node = output_attr.split('.')[0]
        if cmds.nodeType(deformer_node) == 'groupParts':
            source_attr = cmds.connectionInfo(('{}.inputGeometry').format(deformer_node), sfd=True)
        else:
            if cmds.nodeType(deformer_node) in ('mesh', 'nurbsCurve', 'nurbsSurface',
                                                'lattice'):
                return
            if 'geometryFilter' in cmds.nodeType(deformer_node, inherited=True):
                deformer_attr = ('.').join(output_attr.split('.')[1:])
                index_split = deformer_attr.split('[')
                if len(index_split) > 1:
                    indexless_attr = index_split[0]
                else:
                    cmds.error(('"{}" has no index to remove').format(output_attr))
                if indexless_attr == 'outputGeometry':
                    deformer_index = int(deformer_attr.split('[')[1][:-1])
                else:
                    cmds.error(deformer_attr)
                if cmds.getAttr(('{}.input[{}].groupId').format(deformer_node, deformer_index)) != 0:
                    deformer_list.append(deformer_node)
                source_attr = cmds.connectionInfo(('{}.input[{}].inputGeometry').format(deformer_node, deformer_index), sfd=True)
                if not source_attr:
                    cmds.error(('"{}" has no source').format(deformer_node))
            elif cmds.nodeType(deformer_node) == 'createColorSet':
                source_attr = cmds.connectionInfo(('{}.inputGeometry').format(deformer_node), sfd=True)
            elif 'polyModifier' in cmds.nodeType(deformer_node, inherited=True):
                source_attr = cmds.connectionInfo(('{}.inputPolymesh').format(deformer_node), sfd=True)
            else:
                cmds.error(('"{}" is not a deformer, shape, groupParts, or polyModifier').format(deformer_node))
                return
        get_the_upstream_deformer(source_attr)

    get_the_upstream_deformer(first_deformer)
    return list(reversed(deformer_list))


def get_index_list(component_list):
    """
    Gets the index for each component in a list of components.
    
    component_list = A list components you want get the index for. This list must be flat. Example: ["cubeShape1.vtx[0]","cubeShape1.vtx[1]",...] 
                     The components need to be in the scene because there is data on the shape node that is required.
                     The command will not flatten it for you because it is slow.
    
    Returns the component indices as a list of integers.
    
    NOTE:While it would be faster to use an API component-based function, converting from strings to components is very costly.
         To keep the utils more user friendly the input has to be strings, so we use the fastest string-based method.
    """
    if type(component_list) is not list:
        cmds.error(('component_list:"{}" is not a list').format(component_list))
    if component_list == []:
        cmds.error(('component list:"{}" is an empty list').format(component_list))
    shape = component_list[0].split('.')[0]
    if not cmds.objExists(shape):
        cmds.error(('"{}" does not exist').format(shape))
    shape_type = cmds.nodeType(shape)
    if shape_type == 'transform':
        shape_list = cmds.listRelatives(shape, s=True, f=True)
        if shape_list != []:
            shape = shape_list[0]
            shape_type = cmds.nodeType(shape)
    if shape_type in ('mesh', 'nurbsCurve'):
        index_list = [ int(comp.split('[')[(-1)][0:-1]) for comp in component_list ]
    elif shape_type == 'lattice':
        s_div, t_div, u_div = cmds.lattice(shape, q=True, dv=True)
        s_index_list = [ int(component.split('[')[(-3)][0:-1]) for component in component_list ]
        t_index_list = [ int(component.split('[')[(-2)][0:-1]) for component in component_list ]
        u_index_list = [ int(component.split('[')[(-1)][0:-1]) for component in component_list ]
        index_list = [ s_index + t_index * s_div + u_index * t_div * s_div for s_index, t_index, u_index in zip(s_index_list, t_index_list, u_index_list) ]
    elif shape_type == 'nurbsSurface':
        sel = om2.MSelectionList()
        sel.add(shape)
        shape_dagPath = om2.MDagPath()
        comp_mObject = om2.MObject()
        shape_dagPath, comp_mObject = sel.getComponent(0)
        mFn_surface = om2.MFnNurbsSurface(shape_dagPath)
        u_div = mFn_surface.numCVsInU
        v_div = mFn_surface.numCVsInV
        u_index_list = [ int(component.split('[')[(-2)][0:-1]) for component in component_list ]
        v_index_list = [ int(component.split('[')[(-1)][0:-1]) for component in component_list ]
        index_list = [ int(v_index + u_index * v_div) for u_index, v_index in zip(u_index_list, v_index_list) ]
    else:
        cmds.error(('"{}" is not a valid shape').format(shape))
    return index_list


def convert_indices_to_components(index_list, shape):
    if cmds.nodeType(shape) == 'mesh':
        component_list = [ 'vtx[' + str(index) + ']' for index in index_list ]
    elif cmds.nodeType(shape) == 'nurbsCurve':
        component_list = [ ('cv[{}]').format(index) for index in index_list ]
    elif cmds.nodeType(shape) == 'nurbsSurface':
        u_div = cmds.getAttr(shape + '.spansU')
        v_div = cmds.getAttr(shape + '.spansV')
        if cmds.getAttr(shape + '.formU') == 0:
            u_div += cmds.getAttr(shape + '.degreeU')
        if cmds.getAttr(shape + '.formV') == 0:
            v_div += cmds.getAttr(shape + '.degreeV')
        component_list = [ ('cv[{}][{}]').format(int(index / v_div), index % v_div) for index in index_list ]
    elif cmds.nodeType(shape) == 'lattice':
        s_div, t_div, u_div = cmds.lattice(shape, q=True, dv=True)
        s_index_list = [ index % s_div for index in index_list ]
        t_index_list = [ int(index / s_div) % t_div for index in index_list ]
        u_index_list = [ int(index / (s_div * t_div)) % u_div for index in index_list ]
        component_list = [ ('pt[{}][{}][{}]').format(s_index, t_index, u_index) for s_index, t_index, u_index in zip(s_index_list, t_index_list, u_index_list) ]
    else:
        cmds.error(('"{}" is not a valid shape').format(shape))
    return [ shape + '.' + comp for comp in component_list ]


def set_deformer_components(deformer_node, shape, deformerSet_ids):
    old_component_ids = get_deformer_component_ids(deformer_node, shape)
    old_component_list = convert_indices_to_components(old_component_ids, shape)
    new_component_list = convert_indices_to_components(deformerSet_ids, shape)
    sel = om2.MSelectionList()
    sel.add(deformer_node)
    deformer_mObj = sel.getDependNode(0)
    mfn = omAnim2.MFnGeometryFilter(deformer_mObj)
    deformerSet_mObj = mfn.deformerSet
    deformerSet = om2.MFnDependencyNode(deformerSet_mObj).name()
    cmds.sets(new_component_list, add=deformerSet)
    unused_components = [ x for x in old_component_list if x not in new_component_list ]
    if unused_components:
        cmds.sets(unused_components, remove=deformerSet)


def symmetrize_deformerSet(deformerSet_ids, shape, ii_dict=None, axis='x', direction='+ to -', symm_coordinate=0):
    ip_dictionary = convert_shape_to_index_position_dictionary(shape)
    axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
    if not ii_dict:
        if direction == '+ to -':
            non_symm_ip_dict = {index:position for index, position in list(ip_dictionary.items()) if position[axis_index] >= symm_coordinate + 0.001}
            symm_ip_dict = {index:position for index, position in list(ip_dictionary.items()) if position[axis_index] < symm_coordinate - 0.001}
        elif direction == '- to +':
            non_symm_ip_dict = {index:position for index, position in list(ip_dictionary.items()) if position[axis_index] >= symm_coordinate + 0.001}
            symm_ip_dict = {index:position for index, position in list(ip_dictionary.items()) if position[axis_index] < symm_coordinate - 0.001}
        else:
            cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
            return
        if axis == 'x':
            symm_ip_dict = {comp_index:(2 * symm_coordinate - x, y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
        elif axis == 'y':
            symm_ip_dict = {comp_index:(x, 2 * symm_coordinate - y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
        elif axis == 'z':
            symm_ip_dict = {comp_index:(x, y, 2 * symm_coordinate - z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
        ii_dict = match_points_to_closest_point(non_symm_ip_dict, symm_ip_dict)
    new_ids = deformerSet_ids[:]
    for destination_id, source_id in list(ii_dict.items()):
        if source_id in deformerSet_ids:
            new_ids.append(destination_id)

    return (
     new_ids, ii_dict)


def flip_deformerSet():
    pass


def get_member_index(deformer_node, shape):
    """
    Gets the index of the plug that the shape is being connected through.
    It returns a lot of other data that is useful for deformer set stuff too.
    
    deformer_node = The deformer you want to get the member index on.
    shape = The shape you want to get the member index of.
    
    Returns
    the member index as an integer, 
    the given shape as an mObject, 
    the given deformer as an MObject, 
    the MSelectionList of members for the deformer, 
    and the MFnGeometryFilter for the deformer.
    """
    mSelectionList = om.MSelectionList()
    mSelectionList.add(deformer_node)
    mSelectionList.add(shape)
    mObject_deformer = om.MObject()
    mSelectionList.getDependNode(0, mObject_deformer)
    mObject_shape = om.MObject()
    mSelectionList.getDependNode(1, mObject_shape)
    mFnGeometryFilter = omAnim.MFnGeometryFilter(mObject_deformer)
    mFnSet = om.MFnSet(mFnGeometryFilter.deformerSet())
    members = om.MSelectionList()
    member_index = 0
    mFnSet.getMembers(members, False)
    for i in range(members.length()):
        mObject = om.MObject()
        members.getDependNode(i, mObject)
        if mObject_shape == mObject:
            member_index = i

    return [
     member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter]


def get_blendShape_target_index(blendShape_node, blendShape_target):
    """
    Gets the index of the given target on the given blendShape node.
    
    blendShape_node = The blendShape node the target is on.
    blendShape_target = The target you want to get the index for.
    
    Returns the target index as an integer.
    """
    if not cmds.objExists(blendShape_node):
        cmds.error(('"{}" does not exist').format(blendShape_node))
    if cmds.nodeType(blendShape_node) != 'blendShape':
        cmds.error(('"{}" is not a blendShape node').format(blendShape_node))
    target_attr_list = cmds.aliasAttr(blendShape_node, query=True)
    if not target_attr_list:
        cmds.error(('"{}" has no targets').format(blendShape_node))
    target_list = target_attr_list[::2]
    target_index_list = [ int(attr[7:-1]) for attr in target_attr_list[1::2] ]
    target_index_dict = dict(list(zip(target_list, target_index_list)))
    if blendShape_target in target_list:
        target_index = target_index_dict[blendShape_target]
    else:
        cmds.error(('"{}" has no target "{}"').format(blendShape_node, blendShape_target))
    return target_index


def apply_ii_dictionary_to_weight_dictionary(weight_dictionary, source_dictionary, ii_dict):
    """
    !!!
    """
    new_weight_dictionary = weight_dictionary.copy()
    for new, old in list(ii_dict.items()):
        new_weight_dictionary[new] = [(0, 0, 0), source_dictionary[old][1]]

    return new_weight_dictionary


def apply_ibw_dictionary_to_weight_dictionary(weight_dictionary, source_dictionary, ibw_dict):
    """
    Takes a source dictionary and uses an ibw to update another weight dictionary.
    This should be used after you have gotten an ibw dict using "match_points_to_closest_point_on_surface()".
    The "weight dictionary" input can be empty, but in cases where the ibw dict was created using only part of 
    the destination shapes ip dict (liked when symmetrisizing data) then the weight dictionary should contain 
    the data from the unmodified components.
    WARNING: The positions for any components in the resulting dictionary whose weights are modified by the will be 0,0,0.#!!!
    
    weight_dictionary = The weight dictionary you want to modify.
    source_dictionary = The weight dictionary you want to get the data from.
    ibw_dict = The dictionary that contains the "closestPointOnSurface" mapping data between the weight_dictionary and the source dictionary.
    
    Returns a weight dictionary
    """
    new_weight_dictionary = weight_dictionary.copy()
    for new_id, (comp_ids, barycentric_weights) in list(ibw_dict.items()):
        new_weight_dictionary[new_id] = [(0, 0, 0), sum([ source_dictionary[id][1] * bary for id, bary in zip(comp_ids, barycentric_weights) ])]

    return new_weight_dictionary


def apply_ibw_dictionary_to_delta_dictionary(deltas_dictionary, source_dictionary, ibw_dict):
    matched_dictionary = deltas_dictionary.copy()
    for new_id, (comp_ids, barycentric_weights) in list(ibw_dict.items()):
        weighted_delta = [ [ x * bary for x in source_dictionary[comp_id][1] ] for comp_id, bary in zip(comp_ids, barycentric_weights) ]
        sum_delta = [ sum(x) for x in zip(*weighted_delta) ]
        matched_dictionary[new_id] = [
         (0, 0, 0), sum_delta]

    return matched_dictionary


def apply_ibw_dict_to_ng_data(data, ibw):
    """
    !!!
    """
    for each_layer in data['layers']:
        mask_wts = each_layer['mask']
        if mask_wts:
            new_wts = []
            for i in range(len(ibw)):
                indices, barycentric_wts = ibw[i]
                new_wts.append(sum([ mask_wts[index] * bw for index, bw in zip(indices, barycentric_wts) ]))

            each_layer['mask'] = new_wts
        for each_influence in each_layer['influences']:
            influence_wts = each_influence['weights']
            new_wts = []
            for i in range(len(ibw)):
                indices, barycentric_wts = ibw[i]
                new_wts.append(sum([ influence_wts[index] * bw for index, bw in zip(indices, barycentric_wts) ]))

            each_influence['weights'] = new_wts

    return data


def add_weightMap(node, attr_name, defaultWeight=1):
    cmds.addAttr(node, ln=('{}_weightList').format(attr_name), at='compound', numberOfChildren=1, multi=True)
    cmds.addAttr(node, ln=('{}_weights').format(attr_name), at='float', dv=defaultWeight, parent=('{}_weightList').format(attr_name), multi=True)
    cmds.makePaintable(cmds.nodeType(node), ('{}_weights').format(attr_name), at='multiFloat', sm='deformer')


def listPaintableAttributes(deformerNode):
    """
    Returns a list of attributes that "could" be paintable. It may return attributes that do not appear in the paint weights menu.
    
    deformerNode = The deformer node you want to get the paintable attributes for.
    """
    paintableAttributes = []
    for attr in cmds.listAttr(deformerNode):
        if not cmds.attributeQuery(attr.split('.')[(-1)], multi=True, node=deformerNode):
            continue
        children = cmds.attributeQuery(attr.split('.')[(-1)], listChildren=True, node=deformerNode)
        if not children:
            continue
        if len(children) > 1:
            continue
        parents = cmds.attributeQuery(attr.split('.')[(-1)], listParent=True, node=deformerNode)
        if parents:
            continue
        for child in children:
            if not cmds.attributeQuery(child, multi=True, node=deformerNode):
                continue
            grandchildren = cmds.attributeQuery(child, listChildren=True, node=deformerNode)
            if grandchildren:
                continue
            paintableAttributes.append(attr + '.' + child)

    return paintableAttributes


def convert_weightDelta_positions_to_matrix_space(input_dictionary, space_MMatrix):
    """ 
    Takes a weight or delta dictionary and converts the position information from worldSpace to the positions relative to the space_MMatrix.
    
    input_dictionary = The weight or delta dictionary you want to convert.
    space_MMatrix = The worldMatrix (not worldInverseMatrix) of the transform node whose local space you want to get the positions in.
    
    Returns a weight or delta dictionary (the same as the input).
    """
    return {index:(list(om2.MPoint(position) * space_MMatrix.inverse())[0:3], weight) for index, (position, weight) in list(input_dictionary.items())}


def convert_weightDelta_positions_to_UV_coordinates(input_dictionary, shape):
    """ 
    Takes a weight or delta dictionary and converts its positions to UV's
    in the form (U coordinate, V coordinate, 0) in place of (X position, Y position, Z position).
    
    input_dictionary = The weight or delta dictionary you want to convert.
    shape = The mesh shape node whose UV's you want to use in the conversion.
    
    Returns a weight or delta dictionary (the same as the input).
    """
    if not shape:
        cmds.error(('shape:"{}" does not exist').format(shape))
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    items = list(input_dictionary.items())
    comp_index_list = [ x[0] for x in items ]
    position_list = [ x[1][0] for x in items ]
    weight_list = [ x[1][1] for x in items ]
    sel = om2.MSelectionList()
    sel.add(shape)
    obj = sel.getDependNode(0)
    mFnMesh = om2.MFnMesh(obj)
    U_list, V_list = mFnMesh.getUVs()
    return {index:[[U, V, 0], weight] for index, U, V, weight in zip(comp_index_list, U_list, V_list, weight_list)}


def convert_weightDelta_positions_to_surface_uvn(weight_dictionary, nurbsSurface):
    """ 
    Takes a weight or delta dictionary and converts its positions to the coordinates of the nearest point on the given in nurbs surface 
    in the form (U coordinate, V coordinate, Distance To Surface) in place of (X position, Y position, Z position).
    
    weight_dictionary = The weight dictionary you want to convert.
    nurbsSurface = The nurbs surface that is used to convert the weight dictionary. Example: "nurbsPlane1"
    
    Returns a weight or delta dictionary (the same as the input).
    """
    if not cmds.objExists(nurbsSurface):
        cmds.error(('nurbsSurface: "{}" does not exist').format(nurbsSurface))
    nurbsSurfaceShape = ''
    if cmds.nodeType(nurbsSurface) == 'nurbsSurface':
        nurbsSurfaceShape = nurbsSurface
    else:
        cmds.error(('"{}" is not a nurbs surface').format(nurbsSurface))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(nurbsSurfaceShape)
    mObject = om2.MObject()
    mObject = mSelectionList.getDependNode(0)
    mDagPath = om2.MDagPath()
    mDagPath = mSelectionList.getDagPath(0)
    mFnNurbsSurface = om2.MFnNurbsSurface(mObject)
    objMatrix = mDagPath.inclusiveMatrixInverse()
    converted_weight_dictionary = {}
    for index, (position, weight) in list(weight_dictionary.items()):
        close_pos, u_coordinate, v_coordinate = mFnNurbsSurface.closestPoint(om2.MPoint(position) * objMatrix)
        distance_to_surface = close_pos.distanceTo(om2.MPoint(position) * objMatrix)
        converted_weight_dictionary[index] = ((u_coordinate, v_coordinate, distance_to_surface), weight)

    return converted_weight_dictionary


def convert_weightDelta_positions_to_curve_parameters(weight_dictionary, nurbsCurve):
    """ 
    Takes a weight or delta dictionary and converts its positions to the nearest point on the given in nurbs curve 
    in the form (U parameter, distance along curve, distance to curve) in place of (X position, Y position, Z position).
    
    weight_dictionary = The weight or delta dictionary you want to convert.
    nurbsCurve = The nurbs curve that is used to convert the weight dictionary. Example: "curve1"
    
    Returns a weight or delta dictionary (the same as the input).
    """
    if not cmds.objExists(nurbsCurve):
        cmds.error(('nurbsCurve: "{}" does not exist').format(nurbsCurve))
    nurbsCurveShape = ''
    if cmds.nodeType(nurbsCurve) == 'nurbsCurve':
        nurbsCurveShape = nurbsCurve
    else:
        cmds.error(('"{}" is not a nurbs curve').format(nurbsCurve))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(nurbsCurve)
    mObject = om2.MObject()
    mObject = mSelectionList.getDependNode(0)
    mDagPath = om2.MDagPath()
    mDagPath = mSelectionList.getDagPath(0)
    mFnNurbsCurve = om2.MFnNurbsCurve(mObject)
    objMatrix = mDagPath.inclusiveMatrixInverse()
    converted_weight_dictionary = {}
    for index, (position, weight) in list(weight_dictionary.items()):
        close_pos, u_param = mFnNurbsCurve.closestPoint(om2.MPoint(position) * objMatrix)
        distance_along_curve = mFnNurbsCurve.findLengthFromParam(u_param)
        distance_to_curve = close_pos.distanceTo(om2.MPoint(position) * objMatrix)
        converted_weight_dictionary[index] = ((u_param, distance_along_curve, distance_to_curve), weight)

    return converted_weight_dictionary


def convert_weightDeltas_UV_coordinates_to_positions(input_dictionary, shape):
    """ 
    Takes a weight or delta dictionary that has been converted to use UV coordinates and converts it back into a dictionary that uses world position.
    Converting to UV and back again will return the original dictionary, unless there are overlapping UVs.
    
    input_dictionary = The weight or delta dictionary you want to convert.
    shape = The mesh shape node whose UV's you want to use in the conversion.
    
    Returns a weight or delta dictionary (the same as the input).
    """
    if not shape:
        cmds.error(('shape:"{}" does not exist').format(shape))
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    sel = om2.MSelectionList()
    sel.add(shape)
    obj = sel.getDependNode(0)
    mFnMesh = om2.MFnMesh(shape)
    result_dictionary = {}
    for comp_index, ((U, V, N), weight) in list(input_dictionary.items()):
        closest_id = mFnMesh.getClosestUVs(U, V)
        new_pos = tuple(getPoint(closest_id))
        result_dictionary[index] = [new_pos, weight]

    return result_dictionary


def convert_weightDelta_curve_parameters_to_positions(weight_dictionary, nurbsCurve):
    """ 
    Takes a weight or delta dictionary that has been converted to use parameter and converts it back into a dictionary that uses world position.
    Note: Converting to parameters and back again will not return the original dictionary because this function gives the positions directly on the curve.
    
    weight_dictionary = The weight or delta dictionary you want to convert.
    nurbsCurve = The nurbs curve that is used to convert the weight dictionary. Example: "curve1"
    
    Returns a weight or delta dictionary (the same as the input).
    """
    if not cmds.objExists(nurbsCurve):
        cmds.error(('nurbsCurve: "{}" does not exist').format(nurbsSurface))
    nurbsCurveShape = ''
    if cmds.nodeType(nurbsCurve) == 'nurbsCurve':
        nurbsCurveShape = nurbsCurve
    else:
        cmds.error(('"{}" is not a nurbs curve').format(nurbsSurface))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(nurbsSurfaceShape)
    mObject = om2.MObject()
    mObject = mSelectionList.getDependNode(0)
    mDagPath = om2.MDagPath()
    mDagPath = mSelectionList.getDagPath(0)
    mFnNurbsCurve = om2.MFnNurbCurve(mObject)
    objMatrix = mDagPath.inclusiveMatrixInverse()
    converted_weight_dictionary = {}
    for index, (position, weight) in list(weight_dictionary.items()):
        new_position = MFnNurbCurve.getPointAtParam(position[0])
        converted_weight_dictionary[index] = (tuple(position)[0:3], weight)

    return converted_weight_dictionary


def convert_weightDelta_surface_uvn_to_positions(weight_dictionary, nurbsSurface):
    """ 
    Takes a weight or delta dictionary that has been converted to use surface UVN coordinates and converts it back into a dictionary that uses world position.
    
    weight_dictionary = The weight or delta dictionary you want to convert.
    nurbsSurface = The nurbs surface that is used to convert the weight dictionary. Example: "nurbsPlane1"
    
    Returns a weight or delta dictionary (the same as the input).
    """
    if not cmds.objExists(nurbsSurface):
        cmds.error(('nurbsSurface: "{}" does not exist').format(nurbsSurface))
    nurbsSurfaceShape = ''
    if cmds.nodeType(nurbsSurface) == 'nurbsSurface':
        nurbsSurfaceShape = nurbsSurface
    else:
        cmds.error(('"{}" is not a nurbs surface').format(nurbsSurface))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(nurbsSurfaceShape)
    mObject = mSelectionList.getDependNode(0)
    mDagPath = mSelectionList.getDagPath(0)
    mFnNurbsSurface = om2.MFnNurbsSurface(mObject)
    objMatrix = mDagPath.inclusiveMatrix()
    converted_weight_dictionary = {}
    for index, (position, weight) in list(weight_dictionary.items()):
        point_on_surface = MFnNurbsSurface.getPointAtParam(position[0], position[1])
        normal_at_point = MFnNurbsSurface.normal(position[0], position[1])
        new_position = (point_on_surface + normal_at_point) * objMatrix
        converted_weight_dictionary[index] = (tuple(new_position)[0:3], weight)

    return converted_weight_dictionary


def convert_ip_dict_positions_to_UV_coordinates(ip_dictionary, shape):
    """
    Takes an index:position dictionary and converts its positions to UV's
    in the form (U coordinate, V coordinate, 0) in place of (X position, Y position, Z position).

    ip_dictionary = The index:position dictionary you want to convert.
    shape = The mesh shape node whose UV's you want to use in the conversion.

    Returns an index:position dictionary.
    """
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    comp_index_list = list(ip_dictionary.keys())
    sel = om2.MSelectionList()
    sel.add(shape)
    obj = sel.getDependNode(0)
    mFnMesh = om2.MFnMesh(obj)
    U_list, V_list = mFnMesh.getUVs()
    return {index:(U_list[index], V_list[index], 0) for index in comp_index_list}


def convert_ip_dict_positions_to_surface_uvn(ip_dictionary, nurbsSurface):
    """
    Takes an index:position dictionary and converts its positions to the coordinates of the nearest point on the given in nurbs surface
    in the form (U coordinate, V coordinate, Distance To Surface) in place of (X position, Y position, Z position).

    ip_dictionary = The index:position dictionary you want to convert.
    nurbsSurface = The nurbs surface that is used to convert the weight dictionary. Example: "nurbsPlane1"

    Returns an index:position dictionary.
    """
    if not cmds.objExists(nurbsSurface):
        cmds.error(('nurbsSurface: "{}" does not exist').format(nurbsSurface))
    nurbsSurfaceShape = ''
    if cmds.nodeType(nurbsSurface) == 'nurbsSurface':
        nurbsSurfaceShape = nurbsSurface
    else:
        cmds.error(('"{}" is not a nurbs surface').format(nurbsSurface))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(nurbsSurfaceShape)
    mObject = om2.MObject()
    mObject = mSelectionList.getDependNode(0)
    mDagPath = om2.MDagPath()
    mDagPath = mSelectionList.getDagPath(0)
    mFnNurbsSurface = om2.MFnNurbsSurface(mObject)
    objMatrix = mDagPath.inclusiveMatrixInverse()
    converted_weight_dictionary = {}
    for index, (position, weight) in list(ip_dictionary.items()):
        close_pos, u_coordinate, v_coordinate = mFnNurbsSurface.closestPoint(om2.MPoint(position) * objMatrix)
        distance_to_surface = close_pos.distanceTo(om2.MPoint(position) * objMatrix)
        converted_weight_dictionary[index] = (u_coordinate, v_coordinate, distance_to_surface)

    return converted_weight_dictionary


def convert_ip_dict_positions_to_curve_parameters(ip_dictionary, nurbsCurve):
    """
    Takes an index:position dictionary and converts its positions to the nearest point on the given in nurbs curve
    in the form (U parameter, distance along curve, distance to curve) in place of (X position, Y position, Z position).

    ip_dictionary = The index:position dictionary you want to convert.
    nurbsCurve = The nurbs curve that is used to convert the weight dictionary. Example: "curve1"

    Returns an index:position dictionary.
    """
    if not cmds.objExists(nurbsCurve):
        cmds.error(('nurbsCurve: "{}" does not exist').format(nurbsCurve))
    nurbsCurveShape = ''
    if cmds.nodeType(nurbsCurve) == 'nurbsCurve':
        nurbsCurveShape = nurbsCurve
    else:
        cmds.error(('"{}" is not a nurbs curve').format(nurbsCurve))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(nurbsCurve)
    mObject = om2.MObject()
    mObject = mSelectionList.getDependNode(0)
    mDagPath = om2.MDagPath()
    mDagPath = mSelectionList.getDagPath(0)
    mFnNurbsCurve = om2.MFnNurbsCurve(mObject)
    objMatrix = mDagPath.inclusiveMatrixInverse()
    converted_weight_dictionary = {}
    for index, (position, weight) in list(ip_dictionary.items()):
        close_pos, u_param = mFnNurbsCurve.closestPoint(om2.MPoint(position) * objMatrix)
        distance_along_curve = mFnNurbsCurve.findLengthFromParam(u_param)
        distance_to_curve = close_pos.distanceTo(om2.MPoint(position) * objMatrix)
        converted_weight_dictionary[index] = (u_param, distance_along_curve, distance_to_curve)

    return converted_weight_dictionary


def convert_ip_dict_parameters_to_positions(ip_dictionary, nurbsCurve):
    """
    Takes an index:position dictionary that has been converted to use parameter and converts it back into a dictionary that uses world position.
    Note: Converting to parameters and back again will not return the original dictionary because this function gives the positions directly on the curve.

    ip_dictionary = The index:position dictionary you want to convert.
    nurbsCurve = The nurbs curve that is used to convert the weight dictionary. Example: "curve1"

    Returns a weight or delta dictionary (the same as the input).
    """
    if not cmds.objExists(nurbsCurve):
        cmds.error(('nurbsCurve: "{}" does not exist').format(nurbsSurface))
    nurbsCurveShape = ''
    if cmds.nodeType(nurbsCurve) == 'nurbsCurve':
        nurbsCurveShape = nurbsCurve
    else:
        cmds.error(('"{}" is not a nurbs curve').format(nurbsSurface))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(nurbsSurfaceShape)
    mObject = om2.MObject()
    mObject = mSelectionList.getDependNode(0)
    mDagPath = om2.MDagPath()
    mDagPath = mSelectionList.getDagPath(0)
    mFnNurbsCurve = om2.MFnNurbCurve(mObject)
    objMatrix = mDagPath.inclusiveMatrixInverse()
    converted_weight_dictionary = {}
    for index, (position, weight) in list(ip_dictionary.items()):
        new_position = MFnNurbCurve.getPointAtParam(position[0])
        converted_weight_dictionary[index] = tuple(position)[0:3]

    return converted_weight_dictionary


def convert_ip_dict_surface_uvn_to_positions(ip_dictionary, nurbsSurface):
    """
    Takes an index:position dictionary that has been converted to use surface UVN coordinates and converts it back into a dictionary that uses world position.

    ip_dictionary = The index:position dictionary you want to convert.
    nurbsSurface = The nurbs surface that is used to convert the weight dictionary. Example: "nurbsPlane1"

    Returns a weight or delta dictionary (the same as the input).
    """
    if not cmds.objExists(nurbsSurface):
        cmds.error(('nurbsSurface: "{}" does not exist').format(nurbsSurface))
    nurbsSurfaceShape = ''
    if cmds.nodeType(nurbsSurface) == 'nurbsSurface':
        nurbsSurfaceShape = nurbsSurface
    else:
        cmds.error(('"{}" is not a nurbs surface').format(nurbsSurface))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(nurbsSurfaceShape)
    mObject = mSelectionList.getDependNode(0)
    mDagPath = mSelectionList.getDagPath(0)
    mFnNurbsSurface = om2.MFnNurbsSurface(mObject)
    objMatrix = mDagPath.inclusiveMatrix()
    converted_weight_dictionary = {}
    for index, (position, weight) in list(ip_dictionary.items()):
        point_on_surface = MFnNurbsSurface.getPointAtParam(position[0], position[1])
        normal_at_point = MFnNurbsSurface.normal(position[0], position[1])
        new_position = (point_on_surface + normal_at_point) * objMatrix
        converted_weight_dictionary[index] = tuple(new_position)[0:3]

    return converted_weight_dictionary


def get_deformer_component_ids(deformer_node, shape):
    """ 
    Returns a list of the indices that are part of the deformer set for the given shape

    deformer_node = The deformer whose component set you want to get. Example: "cluster1" 
    shape = The shape node whose components you want to query. Example: "cubeShape1"

    Returns a list of integers
    !!!
    """
    mSelectionList = om.MSelectionList()
    mSelectionList.add(deformer_node)
    mSelectionList.add(shape)
    mObject_deformer = om.MObject()
    mSelectionList.getDependNode(0, mObject_deformer)
    mObject_shape = om.MObject()
    mSelectionList.getDependNode(1, mObject_shape)
    mFnGeometryFilter = omAnim.MFnGeometryFilter(mObject_deformer)
    mFnSet = om.MFnSet(mFnGeometryFilter.deformerSet())
    members = om.MSelectionList()
    member_index = 0
    mFnSet.getMembers(members, False)
    for i in range(members.length()):
        mObject = om.MObject()
        members.getDependNode(i, mObject)
        if mObject_shape == mObject:
            member_index = i

    components = om.MObject()
    dagPath = om.MDagPath()
    members.getDagPath(member_index, dagPath, components)
    mFnComponent = om.MFnComponent(components)
    component_type = components.apiType()
    if component_type in [om.MFn.kMeshVertComponent, om.MFn.kCurveCVComponent]:
        index_array = om.MIntArray()
        om.MFnSingleIndexedComponent(components).getElements(index_array)
        return [ int(x) for x in index_array ]
    if component_type == om.MFn.ksurfaceCVComponent:
        u_index_list = om.MIntArray()
        v_index_list = om.MIntArray()
        om.MFnDoubleIndexedComponent(components).getElements(u_index_list, v_index_list)
        return [ int(v_index + u_index * v_div) for u_index, v_index in zip(u_index_list, v_index_list) ]
    if component_type == om.MFn.kLatticeComponent:
        s_index_list = om.MIntArray()
        t_index_list = om.MIntArray()
        u_index_list = om.MIntArray()
        om.MFnTripleIndexedComponent(components).getElements(s_index_list, t_index_list, u_index_list)
        return [ int(s_index + t_index * s_div + u_index * t_div * s_div) for s_index, t_index, u_index in zip(s_index_list, t_index_list, u_index_list) ]


def get_deformer_weights(deformer_node, shape, position_list=None, component_list=None):
    """ 
    Generates a weight dictionary for the given deformer on the given shape. 

    deformer_node = The deformer whose weights you want to get. Example: "cluster1" 
    shape = The shape node whose weights you want to query. Example: "cubeShape1"
    positition_list: The list of positions for the given shape (if you already have them it is faster to give them as inputs than to get them again)

    Returns a weight dictionary
    """
    if not cmds.objExists(deformer_node):
        cmds.error(('deformer:"{}" does not exist').format(deformer_node))
    if shape == None:
        shape = component_list[0].split('.')[0]
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    if not position_list:
        position_list = get_position_list(shape)
    shape = cmds.ls(shape, l=True)[0]
    geo_list = cmds.deformer(deformer_node, q=True, g=True)
    geo_list = [ cmds.ls(x, l=True)[0] for x in geo_list ]
    if not geo_list:
        cmds.error(('"{}" does not affect any geo').format(deformer_node))
    if shape not in geo_list:
        cmds.error(('"{}" is not affected by "{}"').format(shape, deformer_node))
    node_type = cmds.nodeType(deformer_node)
    if node_type in ('ffd', 'nonLinear', 'repulsor'):
        member_index, mObject_shape, mObject_lattice, members, mFnGeometryFilter = get_member_index(deformer_node, shape)
        components = om.MObject()
        dagPath = om.MDagPath()
        members.getDagPath(member_index, dagPath, components)
        mit = om.MItGeometry(dagPath, components)
        logical_index = mFnGeometryFilter.indexForOutputShape(mObject_shape)
        mFnDependencyNode = om.MFnDependencyNode(mObject_lattice)
        weights_mPlug = mFnDependencyNode.findPlug('weightList', False).elementByLogicalIndex(logical_index).child(0)
        if not component_list:
            weight_list = [ 0 for x in range(len(position_list)) ]
            while not mit.isDone():
                comp_index = mit.index()
                weight_list[comp_index] = weights_mPlug.elementByLogicalIndex(comp_index).asFloat()
                next(mit)

            return {key:value for key, value in enumerate(zip(position_list, weight_list))}
        comp_index_list = get_index_list(component_list)
        res_dict = {comp_index:(position_list[comp_index], 0) for comp_index in comp_index_list}
        while not mit.isDone():
            comp_index = mit.index()
            if comp_index in comp_index_list:
                res_dict[comp_index] = (position_list[comp_index], weights_mPlug.elementByLogicalIndex(comp_index).asFloat())
            next(mit)

        return res_dict
    if node_type in ('cluster', 'wire', 'softMod'):
        member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(deformer_node, shape)
        components = om.MObject()
        dagPath = om.MDagPath()
        members.getDagPath(member_index, dagPath, components)
        shape_logical_index = mFnGeometryFilter.indexForOutputShape(mObject_shape)
        mFnWeight = omAnim.MFnWeightGeometryFilter(mObject_deformer)
        mFloatArray = om.MFloatArray()
        mFnWeight.getWeights(shape_logical_index, components, mFloatArray)
        weight_list = [ 0 for x in range(len(position_list)) ]
        mit = om.MItGeometry(dagPath, components)
        i = 0
        if not component_list:
            weight_list = [ 0 for x in range(len(position_list)) ]
            while not mit.isDone():
                comp_index = mit.index()
                weight_list[comp_index] = mFloatArray[i]
                i += 1
                next(mit)

            return {index:(pos, weight) for index, (pos, weight) in enumerate(zip(position_list, weight_list))}
        comp_index_list = get_index_list(component_list)
        res_dict = {comp_index:(position_list[comp_index], 0) for comp_index in comp_index_list}
        while not mit.isDone():
            comp_index = mit.index()
            if comp_index in comp_index_list:
                res_dict[comp_index] = (position_list[comp_index], mFloatArray[i])
            i += 1
            next(mit)

        return res_dict
    cmds.error(('"{}" is not a valid deformer type').format(deformer_node))
    return


def get_ngSkin_influence_weights(layer_ID, influence_name, shape, position_list=None):
    """ 
    Generates a weight dictionary from the given ngSkin influence and layer on the given shape. 
    (if you are not familiar with the ngSkinTools API you can use the convert_layer_name_to_layer_ID function to get the layer ID)

    layer_ID = The layer ID you want to query weights from. 
    influence_name = The name of the influence you want to query weights from. Example: "joint1" 
    shape = The shape node whose weights you want to query. Example: "cubeShape1"
    positition_list: The list of positions for the given shape (if you already have them it is faster to give them as inputs than to get them again)

    Returns a weight dictionary
    """
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    set_list = cmds.listSets(object=shape)
    for set in set_list:
        used_by_list = cmds.listConnections(set + '.usedBy[0]')
        if used_by_list:
            if cmds.nodeType(used_by_list[0]) == 'skinCluster':
                break
    else:
        cmds.error(('{} has no skinCluster').format(shape))

    transform_node = cmds.listRelatives(shape, p=True)[0]
    from ngSkinTools.mllInterface import MllInterface
    mll = MllInterface()
    mll.setCurrentMesh(transform_node)
    layer_dictionary = {x[0]:x[1] for x in mll.listLayers()}
    if layer_ID not in layer_dictionary:
        cmds.error(('Layer with ID {} does not exist.').format(layer_ID))
    long_influence_name = cmds.ls(influence_name, int=True)[0]
    influence_index_list = [ int(index) for index in mll.listInfluenceIndexes() ]
    influence_dictionary = dict(list(zip(mll.listInfluencePaths(), influence_index_list)))
    if long_influence_name in influence_dictionary:
        influenceId = influence_dictionary[long_influence_name]
    else:
        cmds.error(('"{}" does not affect "{}"').format(influence_name, shape))
    if not position_list:
        position_list = get_position_list(shape)
    index_list = list(range(len(position_list)))
    full_weight_list = mll.getInfluenceWeights(layer_ID, influenceId)
    if full_weight_list == []:
        full_weight_list = [
         0] * len(position_list)
    return {index:(pos, weight) for index, pos, weight in zip(index_list, position_list, full_weight_list)}


def convert_layer_name_to_layer_ID(layer_name, shape):
    """
    Finds the ID for the given layer name on the given shape.
    
    layer_name = The name of the layer you want to get the ID for.
    shape = The shape node the layer is for.
    positition_list: The list of positions for the given shape (if you already have them it is faster to give them as inputs than to get them again)

    If the the layer name is unique returns the layer ID as an integer, otherwise returns a list of integers and gives a warning.
    """
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    set_list = cmds.listSets(object=shape)
    for set in set_list:
        used_by_list = cmds.listConnections(set + '.usedBy[0]')
        if used_by_list:
            if cmds.nodeType(used_by_list[0]) == 'skinCluster':
                break
    else:
        cmds.error(('{} has no skinCluster').format(shape))

    transform_node = cmds.listRelatives(shape, p=True)[0]
    from ngSkinTools.mllInterface import MllInterface
    mll = MllInterface()
    mll.setCurrentMesh(transform_node)
    layer_tuple_list = list(mll.listLayers())
    indices = [ ID for ID, name, parent_ID in layer_tuple_list if name == layer_name ]
    if len(indices) == 0:
        cmds.error(('Layer "{}" does not exist.').format(layer_name))
    else:
        if len(indices) == 1:
            return indices[0]
        else:
            cmds.warning(('Multiple Layers named "{}"').format(layer_name))
            return indices


def get_ngSkin_mask_weights(layer_ID, shape, position_list=None, component_list=None):
    """ 
    Generates a weight dictionary from the given ngSkin layers mask on the given shape. 
    (if you are not familiar with the ngSkinTools API you can use the convert_layer_name_to_layer_ID function to get the layer ID)

    layer_ID = The ID of the layer you want to query weights for. 
    shape = The shape node whose weights you want to query. Example: "cubeShape1"
    positition_list: The list of positions for the given shape (if you already have them it is faster to give them as inputs than to get them again)
  
    Returns a weight dictionary
    """
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    set_list = cmds.listSets(object=shape)
    for set in set_list:
        used_by_list = cmds.listConnections(set + '.usedBy[0]')
        if used_by_list:
            if cmds.nodeType(used_by_list[0]) == 'skinCluster':
                break
    else:
        cmds.error(('{} has no skinCluster').format(shape))

    transform_node = cmds.listRelatives(shape, p=True)[0]
    from ngSkinTools.mllInterface import MllInterface
    mll = MllInterface()
    mll.setCurrentMesh(transform_node)
    layer_dictionary = {x[0]:x[1] for x in mll.listLayers()}
    if layer_ID not in layer_dictionary:
        cmds.error(('Layer with ID {} does not exist.').format(layer_ID))
    if not position_list:
        position_list = get_position_list(shape)
    index_list = list(range(len(position_list)))
    full_weight_list = mll.getLayerMask(layer_ID)
    if full_weight_list == []:
        full_weight_list = [
         1] * len(index_list)
    if not component_list:
        return {index:(pos, weight) for index, pos, weight in zip(index_list, position_list, full_weight_list)}
    else:
        comp_ids = get_index_list(component_list)
        return {index:(pos, weight) for index, pos, weight in zip(index_list, position_list, full_weight_list) if index in comp_ids}


def get_ngSkin_DQ_weights(layer_ID, shape, position_list=None):
    """ 
    Generates a weight dictionary from the given ngSkin layers dual quaternions on the given shape. 
    (if you are not familiar with the ngSkinTools API you can use the convert_layer_name_to_layer_ID function to get the layer ID)

    layer_ID = The layer ID you want to query weights from. 
    shape = The shape node whose weights you want to query. Example: "cubeShape1"
    positition_list: The list of positions for the given shape (if you already have them it is faster to give them as inputs than to get them again)

    Returns a weight dictionary
    """
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    set_list = cmds.listSets(object=shape)
    for set in set_list:
        used_by_list = cmds.listConnections(set + '.usedBy[0]')
        if used_by_list:
            if cmds.nodeType(used_by_list[0]) == 'skinCluster':
                break
    else:
        cmds.error(('{} has no skinCluster').format(shape))

    transform_node = cmds.listRelatives(shape, p=True)[0]
    from ngSkinTools.mllInterface import MllInterface
    mll = MllInterface()
    mll.setCurrentMesh(transform_node)
    layer_dictionary = {x[0]:x[1] for x in mll.listLayers()}
    if layer_ID not in layer_dictionary:
        cmds.error(('Layer with ID {} does not exist.').format(layer_ID))
    full_weight_list = mll.getDualQuaternionWeights(layer_ID)
    if full_weight_list == []:
        full_weight_list = [
         0] * len(index_list)
    if not position_list:
        position_list = get_position_list(shape)
    index_list = list(range(len(full_weight_list)))
    return {index:(pos, weight) for index, pos, weight in zip(index_list, position_list, full_weight_list)}


def get_blendShape_target_weights(blendShape_node, blendShape_target, position_list=None, shape=None):
    """ 
    Generates a weight dictionary from the given blendShape target on the given blendShape node.
    
    blendShape_node: The blendShape node you want to query the weights from.
    blendShape_target: The blendShape target you want to query the weights from.
    positition_list: The list of positions for the given shape (if you already have them it is faster to give them as inputs than to get them again)
    shape: The shape whose weights you want to get for this deformer (this is only required if you have two shapes deformed by the same blendShape node)
    
    Returns a weight dictionary
    """
    target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    if shape:
        shape = cmds.ls(shape, l=True)[0]
        geo_list = cmds.deformer(blendShape_node, q=True, g=True)
        geo_list = [ cmds.ls(x, l=True)[0] for x in geo_list ]
        if shape not in geo_list:
            cmds.error(('"{}" is not affected by "{}"').format(shape, blendShape_node))
        member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(blendShape_node, shape)
    else:
        member_index = 0
        shape = cmds.blendShape(blendShape_node, q=True, g=True)
        if not shape:
            cmds.error(('"{}" does not affect any geometry').format(blendShape_node))
            return
        shape = shape[0]
    if not position_list:
        position_list = get_position_list(shape)
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(blendShape_node)
    mObject_blendShape_node = mSelectionList.getDependNode(0)
    mFnDependencyNode = om2.MFnDependencyNode(mObject_blendShape_node)
    weights_mPlug = mFnDependencyNode.findPlug('inputTarget', False).elementByLogicalIndex(member_index).child(0).elementByLogicalIndex(target_index).child(1)
    weight_list = [ 1 for x in range(len(position_list)) ]
    for comp_index in weights_mPlug.getExistingArrayAttributeIndices():
        if comp_index < len(position_list):
            weight_list[comp_index] = weights_mPlug.elementByLogicalIndex(comp_index).asFloat()

    return {index:(pos, weight) for index, pos, weight in zip(list(range(len(position_list))), position_list, weight_list)}


def get_blendShape_base_weights(blendShape_node, position_list=None, shape=None):
    """ 
    Generates a weight dictionary from the given blendShape nodes base weights.
    
    blendShape_node: The blendShape node you want to query the weights from.
    positition_list: The list of positions for the given shape (if you already have them it is faster to give them as inputs than to get them again)
    shape: The shape whose weights you want to get for this deformer (this is only required if you have two shapes deformed by the same blendShape node)

    Returns a weight dictionary
    """
    if cmds.nodeType(blendShape_node) != 'blendShape':
        cmds.error('"{}" is not a blendShape node')
    if not shape:
        shape = cmds.blendShape(blendShape_node, q=True, g=True)
        if shape == []:
            cmds.error('"{}" does not affect any geometry')
        else:
            shape = shape[0]
    member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(blendShape_node, shape)
    if not position_list:
        position_list = get_position_list(shape)
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(blendShape_node)
    mObject_lattice = mSelectionList.getDependNode(0)
    mFnDependencyNode = om2.MFnDependencyNode(mObject_lattice)
    weights_mPlug = mFnDependencyNode.findPlug('inputTarget', False).elementByLogicalIndex(member_index).child(1)
    weight_list = [ 1 for x in range(len(position_list)) ]
    for comp_index in weights_mPlug.getExistingArrayAttributeIndices():
        weight_list[comp_index] = weights_mPlug.elementByLogicalIndex(comp_index).asFloat()

    return {index:(pos, weight) for index, pos, weight in zip(list(range(len(position_list))), position_list, weight_list)}


def get_weightList_weights(deformer_node, shape, weightListPlug, position_list=None, component_list=None):
    """ 
    Generates a weight dictionary from the given weightList on the given shape.
    
    deformer_node: The deformer node you want to query the weights from.
    shape: The shape whose weights you want to get for this deformer.
    weightListPlug: The weightList plug you want to query the weights from.
    position_list: The list of positions for the given shape (if you already have them it is faster to give them as inputs than to get them again)
    
    Returns a weight dictionary
    """
    if not cmds.objExists(deformer_node):
        cmds.error(('deformer node "{}" does not exist').format(deformer_node))
    sel = om2.MSelectionList()
    sel.add(deformer_node)
    mObj_deformer_node = sel.getDependNode(0)
    if not mObj_deformer_node.hasFn(om2.MFn.kWeightGeometryFilt):
        cmds.error(('"{}" is not a deformer node').format(deformer_node))
    if not cmds.objExists(shape):
        cmds.error(('shape: "{}" does not exists').format(deformer_node))
    shape = cmds.ls(shape, l=True)[0]
    geo_list = cmds.deformer(deformer_node, q=True, g=True)
    geo_list = [ cmds.ls(x, l=True)[0] for x in geo_list ]
    if shape not in geo_list:
        cmds.error(('"{}" is not affected by "{}"').format(shape, deformer_node))
    member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(deformer_node, shape)
    shape_logical_index = mFnGeometryFilter.indexForOutputShape(mObject_shape)
    if not position_list:
        position_list = get_position_list(shape)
    weights_mPlug = weightListPlug.elementByLogicalIndex(shape_logical_index).child(0)
    weights_name = weights_mPlug.elementByLogicalIndex(0).name()
    default_wt = cmds.attributeQuery(weights_name.split('.')[(-1)].split('[')[0], node=weights_name.split('.')[0], listDefault=True)[0]
    components = om.MObject()
    dagPath = om.MDagPath()
    members.getDagPath(member_index, dagPath, components)
    mit = om.MItGeometry(dagPath, components)
    if not component_list:
        weight_list = [ default_wt for x in range(len(position_list)) ]
        while not mit.isDone():
            comp_index = mit.index()
            weight_list[comp_index] = weights_mPlug.elementByLogicalIndex(comp_index).asFloat()
            next(mit)

        return {key:value for key, value in enumerate(zip(position_list, weight_list))}
    else:
        comp_index_list = get_index_list(component_list)
        res_dict = {comp_index:(position_list[comp_index], default_wt) for comp_index in comp_index_list}
        while not mit.isDone():
            comp_index = mit.index()
            if comp_index in comp_index_list:
                res_dict[comp_index] = (position_list[comp_index], weights_mPlug.elementByLogicalIndex(comp_index).asFloat())
            next(mit)

        return res_dict


def get_skinCluster_influence_weights(influence_name, shape, position_list=None):
    """ 
    Generates a weight dictionary from the given skinCluster influence on the given shape. 

    influence_name = The name of the influence whose weights you want to query. Example: "joint1' 
    shape = The shape node whose weights you want to query. Example: "cubeShape1"
        
    Returns a weight dictionary
    """
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    set_list = cmds.listSets(object=shape)
    for set in set_list:
        used_by_list = cmds.listConnections(set + '.usedBy[0]')
        if used_by_list:
            if cmds.nodeType(used_by_list[0]) == 'skinCluster':
                break
    else:
        cmds.error(('{} has no skinCluster').format(shape))

    if influence_name not in cmds.skinCluster(skinCluster_node, q=True, influence=True):
        cmds.error(('"{}" not an influence on {}').format(influence_name, shape))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(skinCluster_node)
    mSelectionList.add(influence_name)
    mSelectionList.add(shape)
    mObject_skinCluster = mSelectionList.getDependNode(0)
    mDagPath_influence = mSelectionList.getDagPath(1)
    mDagPath_shape = mSelectionList.getDagPath(2)
    mObject_shape_components = mSelectionList.getComponent(2)[1]
    mFnSkinCluster = omAnim2.MFnSkinCluster(mObject_skinCluster)
    influence_index = mFnSkinCluster.indexForInfluenceObject(mDagPath_influence)
    weight_list = mFnSkinCluster.getWeights(mDagPath_shape, mObject_shape_components, influence_index)
    if not position_list:
        position_list = get_position_list(shape)
    return {index:(pos, weight) for index, pos, weight in zip(list(range(len(weight_list))), position_list, weight_list)}


def get_skinCluster_DQ_weights(shape):
    """ 
    Generates a weight dictionary from the given skinCluster influence on the given shape. 

    shape = The shape node whose weights you want to query. Example: "cubeShape1"
        
    Returns a weight dictionary
    """
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    set_list = cmds.listSets(object=shape)
    for set in set_list:
        if cmds.objExists(set):
            used_by_list = cmds.listConnections(set + '.usedBy[0]')
            if used_by_list:
                if cmds.nodeType(used_by_list[0]) == 'skinCluster':
                    skinCluster_node = used_by_list[0]
                    break
    else:
        cmds.error(('{} has no skinCluster').format(shape))

    mSelectionList = om2.MSelectionList()
    mSelectionList.add(skinCluster_node)
    mSelectionList.add(shape)
    mObject_skinCluster = mSelectionList.getDependNode(0)
    mDagPath_shape, mObject_shape_components = mSelectionList.getComponent(1)
    mFnSkinCluster = omAnim2.MFnSkinCluster(mObject_skinCluster)
    if cmds.nodeType(shape) == 'mesh':
        meshVerItFn = om2.MItMeshVertex(mDagPath_shape)
        indices = list(range(meshVerItFn.count()))
        singleIdComp = om2.MFnSingleIndexedComponent()
        comp_list = singleIdComp.create(om2.MFn.kMeshVertComponent)
        singleIdComp.addElements(indices)
    elif cmds.nodeType(shape) == 'nurbsCurve':
        curveItFn = om2.MItCurveCV(mDagPath_shape)
        indices = om2.MIntArray()
        while not curveItFn.isDone():
            indices.append(index)
            next(curveItFn)

        singleIdComp = om2.MFnSingleIndexedComponent()
        comp_list = singleIdComp.create(om2.MFn.kCurveCVComponent)
        singleIdComp.addElements(indices)
    elif cmds.nodeType(shape) == 'nurbsSurface':
        surfaceItFn = om2.MItSurfaceCV(mDagPath_shape)
        doubleIdComp = om2.MFnDoubleIndexedComponent()
        comp_list = doubleIdComp.create(om2.MFn.kSurfaceCVComponent)
        sizeInV = om2.MFnNurbsSurface(mDagPath_shape).numCVsInV
        while not surfaceItFn.isDone():
            index = surfaceItFn.index()
            indexU = index / sizeInV
            indexU = index % sizeInV
            doubleIdComp.addElement(indexU, indexU)
            next(surfaceItFn)

    else:
        cmds.error(('DQ weights cannot be queried for "{}"').format(shape))
    weight_list = mFnSkinCluster.getBlendWeights(mDagPath_shape, comp_list)
    return {index:(pos, weight) for index, pos, weight in zip(list(range(len(weight_list))), get_position_list(shape), weight_list)}


def symmetrisize_weights(weight_dictionary, symm_coordinate=0, axis='x', uv_axis='u', direction='+ to -', matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None):
    """ 
    Makes a weight dictionary symmetrical. 

    weight_dictionary = The weight dictionary you want to symmetrisize
    symm_coordinate = The coordinate at which the weights will be symmetrisized
    axis = The axis you want to symmetrisize the weights over ("x" "y" or "z") when using closestComponent or closestPointOnSurface ("u" or "v") when using closestComponentUV. 
    uv_axis = The axis in UV space you want to to symmetrisize the points over.
    direction: The direction in which you symmetrisize the weights, can be "+ to -" or "- to +"
    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the weights from the components that influence that point.
            When the source_shape input is a lattice the closest point on surface is actually based on volume.
        closestComponentUV = 
            Matches to the closest compoennt on the other side in UV space.
            The returned dictionary will not UV coordinate information instead of worldspace position information.
            Note: You will probably want to set the symm_coordinate to .5 when using this method.

    source_shape = The shape the weight dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentrix weight information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.
            
    If the matching method is "closestComponent" or "closestComponentUV" it returns weight dictionary and an ii_dict so that the operation can be performed faster next time [weight_dictionary,ii_dict]
    If the matching_method is "closestPointOnSurface" it returns a weight dictionary and an ibw dict so that the operation can be performed faster next time [weight_dictionary,dict].
    """
    if matching_method == 'closestComponent':
        if axis not in ('x', 'y', 'z'):
            cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
        axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
        if not ii_dict:
            if direction == '+ to -':
                non_symm_weight_dict = {key:value for key, value in list(weight_dictionary.items()) if value[0][axis_index] >= symm_coordinate - 0.001}
                non_symm_ip_dict = {index:position for index, (position, weight) in list(non_symm_weight_dict.items())}
                symm_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items()) if position[axis_index] < symm_coordinate - 0.001}
            elif direction == '- to +':
                non_symm_weight_dict = {key:value for key, value in list(weight_dictionary.items()) if value[0][axis_index] <= symm_coordinate + 0.001}
                non_symm_ip_dict = {index:position for index, (position, weight) in list(non_symm_weight_dict.items())}
                symm_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items()) if position[axis_index] > symm_coordinate + 0.001}
            else:
                cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                return
            if axis == 'x':
                symm_ip_dict = {comp_index:(2 * symm_coordinate - x, y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
            elif axis == 'y':
                symm_ip_dict = {comp_index:(x, 2 * symm_coordinate - y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
            elif axis == 'z':
                symm_ip_dict = {comp_index:(x, y, 2 * symm_coordinate - z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
            ii_dict = match_points_to_closest_point(non_symm_ip_dict, symm_ip_dict)
        new_weight_dictionary = weight_dictionary.copy()
        for new, old in list(ii_dict.items()):
            new_weight_dictionary[new] = [
             weight_dictionary[new][0], weight_dictionary[old][1]]

        return [
         new_weight_dictionary, ii_dict]
    if matching_method == 'closestComponentUV':
        if uv_axis not in ('u', 'v'):
            cmds.error(('"{}" is not a valid axis ("u" or "v")').format(uv_axis))
        axis_index = {'u': 0, 'v': 1}[uv_axis]
        if not ii_dict:
            weight_dictionary = convert_weightDelta_positions_to_UV_coordinates(weight_dictionary, source_shape)
            if direction == '+ to -':
                non_symm_weight_dict = {key:value for key, value in list(weight_dictionary.items()) if value[0][axis_index] >= symm_coordinate - 0.001}
                non_symm_ip_dict = {index:position for index, (position, weight) in list(non_symm_weight_dict.items())}
                symm_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items()) if position[axis_index] < symm_coordinate - 0.001}
            elif direction == '- to +':
                non_symm_weight_dict = {key:value for key, value in list(weight_dictionary.items()) if value[0][axis_index] <= symm_coordinate + 0.001}
                non_symm_ip_dict = {index:position for index, (position, weight) in list(non_symm_weight_dict.items())}
                symm_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items()) if position[axis_index] > symm_coordinate + 0.001}
            else:
                cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                return
            if uv_axis == 'u':
                symm_ip_dict = {comp_index:(2 * symm_coordinate - x, y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
            else:
                if uv_axis == 'v':
                    symm_ip_dict = {comp_index:(x, 2 * symm_coordinate - y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
                ii_dict = match_points_to_closest_point(non_symm_ip_dict, symm_ip_dict)
                for new, old in list(ii_dict.items()):
                    non_symm_weight_dict[new] = [
                     weight_dictionary[new][0], weight_dictionary[old][1]]

            return [non_symm_weight_dict, ii_dict]
        new_weight_dictionary = weight_dictionary.copy()
        for new, old in list(ii_dict.items()):
            new_weight_dictionary[new] = [
             weight_dictionary[new][0], weight_dictionary[old][1]]

        return [
         new_weight_dictionary, ii_dict]
    if matching_method == 'closestPointOnSurface':
        if axis not in ('x', 'y', 'z'):
            cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
        axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
        if not ibw_dict:
            if direction == '+ to -':
                non_symm_weight_dict = {key:value for key, value in list(weight_dictionary.items()) if value[0][axis_index] >= symm_coordinate - 0.001}
                non_symm_ip_dict = {index:position for index, (position, weight) in list(non_symm_weight_dict.items())}
                symm_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items()) if position[axis_index] < symm_coordinate - 0.001}
            elif direction == '- to +':
                non_symm_weight_dict = {key:value for key, value in list(weight_dictionary.items()) if value[0][axis_index] <= symm_coordinate + 0.001}
                non_symm_ip_dict = {index:position for index, (position, weight) in list(non_symm_weight_dict.items())}
                symm_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items()) if position[axis_index] > symm_coordinate + 0.001}
            else:
                cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                return
            if axis == 'x':
                symm_ip_dict = {comp_index:(2 * symm_coordinate - x, y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
            elif axis == 'y':
                symm_ip_dict = {comp_index:(x, 2 * symm_coordinate - y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
            elif axis == 'z':
                symm_ip_dict = {comp_index:(x, y, 2 * symm_coordinate - z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
            orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
            ibw_dict = match_points_to_closest_point_on_surface(orig_shape, symm_ip_dict)
            non_symm_weight_dict = apply_ibw_dictionary_to_weight_dictionary(non_symm_weight_dict, weight_dictionary, ibw_dict)
            return [
             non_symm_weight_dict, ibw_dict]
        new_weight_dictionary = apply_ibw_dictionary_to_weight_dictionary(weight_dictionary, weight_dictionary, ibw_dict)
        return [new_weight_dictionary, ibw_dict]
    else:
        cmds.error(('"{}" is not a valid matching method ("closestComponent","closestComponentUV","closestPointOnSurface")').format(matching_method))


def flip_weights(weight_dictionary, flip_coordinate=0, axis='x', uv_axis='u', matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None):
    """ 
    Flips the given weight dictionary over the given axis at the given flip coordinate.

    weight_dictionary = The weight dictionary you want to flip.
    flip_coordinate: The coordinate you want to flip the weight dictionary at.
    axis: The axis you want to flip the weights over ("x" "y" or "z") when using closestComponent or closestPointOnSurface.
    uv_axis = The axis in UV space you want to to flip the points over ("u" or "v").

    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the weights from the components that influence that point.
            When the source_shape input is a lattice the closest point on surface is actually based on volume.
        closestComponentUV = 
            Matches to the closest compoennt on the other side in UV space.
            The returned dictionary will not UV coordinate information instead of worldspace position information.
            Note: You will probably want to set the symm_coordinate to .5 when using this method.

    source_shape = The shape the weight dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentrix weight information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.
            
    If the matching method is "closestComponent" or "closestComponentUV" it returns weight dictionary and an ii_dict so that the operation can be performed faster next time [weight_dictionary,ii_dict]
    If the matching_method is "closestPointOnSurface" it returns a weight dictionary and an ibw dict so that the operation can be performed faster next time [weight_dictionary,dict].
    """
    if matching_method == 'closestComponent':
        if not ii_dict:
            original_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items())}
            if axis == 'x':
                flipped_ip_dict = {comp_index:(2 * flip_coordinate - x, y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
            elif axis == 'y':
                flipped_ip_dict = {comp_index:(x, 2 * flip_coordinate - y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
            elif axis == 'z':
                flipped_ip_dict = {comp_index:(x, y, 2 * flip_coordinate - z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
            else:
                cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
            ii_dict = match_points_to_closest_point(flipped_ip_dict, original_ip_dict)
            flipped_weight_dictionary = {new:[weight_dictionary[new][0], weight_dictionary[old][1]] for new, old in list(ii_dict.items())}
            return [
             flipped_weight_dictionary, ii_dict]
        else:
            flipped_weight_dictionary = {new:[weight_dictionary[new][0], weight_dictionary[old][1]] for new, old in list(ii_dict.items())}
            return [
             flipped_weight_dictionary, ii_dict]

    elif matching_method == 'closestComponentUV':
        if not ii_dict:
            weight_dictionary = convert_weightDelta_positions_to_UV_coordinates(weight_dictionary, source_shape)
            original_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items())}
            if uv_axis == 'u':
                flipped_ip_dict = {comp_index:(2 * flip_coordinate - x, y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
            elif uv_axis == 'v':
                flipped_ip_dict = {comp_index:(x, 2 * flip_coordinate - y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
            else:
                cmds.error(('"{}" is not a valid uv_axis ("x","y", or "z")').format(axis))
            ii_dict = match_points_to_closest_point(flipped_ip_dict, original_ip_dict)
            flipped_weight_dictionary = {new:[weight_dictionary[new][0], weight_dictionary[old][1]] for new, old in list(ii_dict.items())}
            return [
             flipped_weight_dictionary, ii_dict]
        else:
            flipped_weight_dictionary = {new:[weight_dictionary[new][0], weight_dictionary[old][1]] for new, old in list(ii_dict.items())}
            return [
             flipped_weight_dictionary, ii_dict]

    elif matching_method == 'closestPointOnSurface':
        if not ibw_dict:
            if axis == 'x':
                flipped_ip_dict = {comp_index:(2 * flip_coordinate - x, y, z) for comp_index, ((x, y, z), weight) in list(weight_dictionary.items())}
            elif axis == 'y':
                flipped_ip_dict = {comp_index:(x, 2 * flip_coordinate - y, z) for comp_index, ((x, y, z), weight) in list(weight_dictionary.items())}
            elif axis == 'z':
                flipped_ip_dict = {comp_index:(x, y, 2 * flip_coordinate - z) for comp_index, ((x, y, z), weight) in list(weight_dictionary.items())}
            else:
                cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
            orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
            ibw_dict = match_points_to_closest_point_on_surface(orig_shape, flipped_ip_dict)
            flipped_weight_dictionary = apply_ibw_dictionary_to_weight_dictionary(weight_dictionary, weight_dictionary, ibw_dict)
            return [
             flipped_weight_dictionary, ibw_dict]
        else:
            flipped_weight_dictionary = apply_ibw_dictionary_to_weight_dictionary(weight_dictionary, weight_dictionary, ibw_dict)
            return [flipped_weight_dictionary, ibw_dict]

    else:
        cmds.error(('"{}" is not a valid matching method ("closestComponent","closestComponentUV","closestPointOnSurface")').format(matching_method))


def invert_weights(weight_dictionary):
    """
    Inverts the weights in a weight dictionary so 0 becomes 1, .25 becomes .75 etc.
    
    weight_dictionary = The weight dictionary you want to flip.
    
    Returns a weight dictionary.
    """
    return {comp_index:((x, y, z), 1 - weight) for comp_index, ((x, y, z), weight) in list(weight_dictionary.items())}


def split_weights(weight_dictionary, split_coordinate=0, axis='x', falloff_distance=0):
    """
    Splits a weight dictionary into two weight dictionaries one for each side of the split_coordinate along the given axis.
    
    weight_dictionary = The weight dictionary you want to split.
    split_coordinate = The coordinate you want to split the weights above and below.
    axis: The axis you want to mirror the deformations over ("x" "y" or "z"). 
    falloff_distance = The distance around the coordinate that smooths the split weights.
    
    Returns a list containing two weight dictionaries one for each side of the split coordinate, as well as a pair of "mask" weight dictionaries. 
    [[weight_dict1, weight_dict2],[mask_dict1,mask_dict2]]
    """
    if axis not in ('x', 'y', 'z'):
        cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
    axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
    positive_weight_dictionary = {}
    negative_weight_dictionary = {}
    positive_mask_dictionary = {}
    negative_mask_dictionary = {}
    for comp_index, (position, weight) in list(weight_dictionary.items()):
        axis_position = position[axis_index]
        if axis_position > split_coordinate + falloff_distance:
            positive_weight_dictionary[comp_index] = (
             position, weight)
            negative_weight_dictionary[comp_index] = (position, 0)
            positive_mask_dictionary[comp_index] = (position, 1)
            negative_mask_dictionary[comp_index] = (position, 0)
        elif axis_position < split_coordinate - falloff_distance:
            negative_weight_dictionary[comp_index] = (
             position, weight)
            positive_weight_dictionary[comp_index] = (position, 0)
            positive_mask_dictionary[comp_index] = (position, 0)
            negative_mask_dictionary[comp_index] = (position, 1)
        elif falloff_distance == 0:
            negative_weight_dictionary[comp_index] = (
             position, 0)
            positive_weight_dictionary[comp_index] = (position, weight)
            positive_mask_dictionary[comp_index] = (position, 1)
            negative_mask_dictionary[comp_index] = (position, 0)
        else:
            scaled_distance = (axis_position - split_coordinate + falloff_distance) / (falloff_distance * 2)
            positive_weight = 3 * scaled_distance ** 2 - 2 * scaled_distance ** 3
            negative_weight = 1 - positive_weight
            negative_weight_dictionary[comp_index] = (
             position, weight * negative_weight)
            positive_weight_dictionary[comp_index] = (position, weight * positive_weight)
            positive_mask_dictionary[comp_index] = (position, positive_weight)
            negative_mask_dictionary[comp_index] = (position, negative_weight)

    return [
     [
      positive_weight_dictionary, negative_weight_dictionary], [positive_mask_dictionary, negative_mask_dictionary]]


def split_weights_radially(weight_dictionary, split_MMatrix, number_of_sections=4, falloff_angle=0):
    """
    Splits a weight dictionary into two weight dictionaries one for each side of the split_coordinate along the given axis.
    
    weight_dictionary = The weight dictionary you want to split radially.
    split_matrix = The matrix whose position and orientation are going to be used to split the weights. It will split as if creating a wedge and rotating it around the objects y axis. Example: om2.MMatrix
    number_of_sections = The number of sectors the weights will be split into.
    falloff_angle = The angle range over which the weights are smoothed.
    
    Returns a list of weight dictionaries and a list of "mask" weights.
    [[weight_dict1, weight_dict2...],[mask_dict1,mask_dict2...]]
    """
    full_angle = 180 / number_of_sections
    items = list(weight_dictionary.items())
    comp_index_list = [ x[0] for x in items ]
    position_list = [ x[1][0] for x in items ]
    weight_list = [ x[1][1] for x in items ]
    full_mask_weight_list = []
    for i in range(number_of_sections):
        mTransformationMatrix_rotation = om2.MTransformationMatrix()
        mTransformationMatrix_rotation.setRotation(om2.MEulerRotation(0, 6.283185 / number_of_sections * i, 0))
        rotated_matrix = mTransformationMatrix_rotation.asMatrix() * split_MMatrix
        inverse_matrix = rotated_matrix.inverse()
        mask_weight_list = []
        for j in range(len(position_list)):
            position_vector = om2.MVector(*position_list[j])
            local_vector = position_vector * inverse_matrix
            local_vector.y = 0
            angle = local_vector.angle(om2.MVector(0, 0, 1)) * 360 / 6.28318531
            if angle > full_angle + falloff_angle:
                mask_weight_list.append(0)
            elif angle <= full_angle - falloff_angle:
                mask_weight_list.append(1)
            else:
                if falloff_angle == 0:
                    mask_weight_list.append(1)
                weight_proportion = 1 - (angle - (full_angle - falloff_angle)) / (falloff_angle * 2)
                weight_proportion = 3 * weight_proportion ** 2 - 2 * weight_proportion ** 3
                mask_weight_list.append(weight_proportion)

        full_mask_weight_list.append(mask_weight_list)

    zipped_weight_list = list(zip(*full_mask_weight_list))
    weight_sums = [ float(sum(x)) for x in zipped_weight_list ]
    weight_sums = [ x if x > 0 else 1 for x in weight_sums ]
    normalized_weights = [ [ per_index_weight / weight_sum for per_index_weight in per_index_weight_list ] for weight_sum, per_index_weight_list in zip(weight_sums, zipped_weight_list) ]
    unzipped_weight_list = list(zip(*normalized_weights))
    mask_weight_dict_list = [ {index:(position, weight) for index, position, weight in zip(comp_index_list, position_list, each_weight_list)} for each_weight_list in unzipped_weight_list ]
    split_weight_dict_list = [ multiply_weights(weight_dictionary, mask_weight_dict) for mask_weight_dict in mask_weight_dict_list ]
    return [
     split_weight_dict_list, mask_weight_dict_list]


def split_weights_with_surface(weight_dictionary, nurbsSurface, falloff_distance):
    """
    Splits a weight dictionary into two weight dictionaries on for each side of the surface.
    
    weight_dictionary = The weight dictionary you want to split.
    nurbsSurface = The nurbs surface that is used to split the weight dictionary.
    falloff_distance = The distance around the surface that smooths the split weights.
    
    Returns a list containing two weight dictionaries one for each side of the surface and a list of mask weights.
    [[weight_dict1, weight_dict2],[mask_dict1,mask_dict2]]
    """
    if not cmds.objExists(nurbsSurface):
        return
    if cmds.nodeType(nurbsSurface) == 'nurbsSurface':
        nurbsSurfaceShape = nurbsSurface
    else:
        shape_list = cmds.listRelatives(nurbsSurface, f=True, s=True)
        shape_list = [ shape for shape in shape_list if cmds.nodeType(shape) == 'nurbsSurface' ]
        if shape_list != []:
            nurbsSurfaceShape = shape_list[0]
        else:
            cmds.error(('{} is not a nurbsSurface').format(nurbsSurface))
        items = list(weight_dictionary.items())
        index_list = [ x[0] for x in items ]
        position_list = [ x[1][0] for x in items ]
        weight_list = [ x[1][1] for x in items ]
        sel = om2.MSelectionList()
        sel.add(nurbsSurfaceShape)
        mFn = om2.MFnNurbsSurface(sel.getDependNode(0))
        mDagPath = sel.getDagPath(0)
        objMatrixInverse = mDagPath.inclusiveMatrixInverse()
        objMatrix = mDagPath.inclusiveMatrix()
        mPointArray = om2.MPointArray(position_list)
        closest_pnt_list = [ mFn.closestPoint(mPoint * objMatrixInverse) for mPoint in mPointArray ]
        mVector_list = [ mPoint - closest_pnt[0] * objMatrix for mPoint, closest_pnt in zip(mPointArray, closest_pnt_list) ]
        normal_list = [ mFn.normal(U, V) * objMatrix for pnt, U, V in closest_pnt_list ]
        dot_product_list = [ normal.normalize() * vector for normal, vector in zip(normal_list, mVector_list) ]
        dot_product_list = [ 1 if dot_product > 0 else -1 for dot_product in dot_product_list ]
        distance_scalar_list = [ dot_product * vector.length() for dot_product, vector in zip(dot_product_list, mVector_list) ]
        inside_weight_dictionary = {}
        outside_weight_dictionary = {}
        inside_mask_dictionary = {}
        outside_mask_dictionary = {}
        for comp_index, position, weight, distance_scalar in zip(index_list, position_list, weight_list, distance_scalar_list):
            if distance_scalar > falloff_distance:
                outside_weight_dictionary[comp_index] = (
                 position, weight)
                inside_weight_dictionary[comp_index] = (position, 0)
                inside_mask_dictionary[comp_index] = (position, 0)
                outside_mask_dictionary[comp_index] = (position, 1)
            elif distance_scalar < -falloff_distance:
                inside_weight_dictionary[comp_index] = (
                 position, weight)
                outside_weight_dictionary[comp_index] = (position, 0)
                inside_mask_dictionary[comp_index] = (position, 1)
                outside_mask_dictionary[comp_index] = (position, 0)
            else:
                scaled_distance = (distance_scalar + falloff_distance) / (2 * falloff_distance)
                cubic_hermite = lambda x: 1 - (3 * x ** 2 - 2 * x ** 3)
                inner_weight = cubic_hermite(scaled_distance)
                outer_weight = 1 - inner_weight
                inside_weight_dictionary[comp_index] = (
                 position, weight * inner_weight)
                outside_weight_dictionary[comp_index] = (position, weight * outer_weight)
                inside_mask_dictionary[comp_index] = (position, inner_weight)
                outside_mask_dictionary[comp_index] = (position, outer_weight)

    return [
     [
      inside_weight_dictionary, outside_weight_dictionary], [inside_mask_dictionary, outside_mask_dictionary]]


def split_weights_along_axis(weight_dictionary, start_position=0, end_position=1, falloff_distance=1, split_number=2, axis='x', closed=False):
    """ 
    Takes a weight dictionary and splits it along the given axis into multiple weight dictionaries. 
    
    weight_dictionary = The weight dictionary you want to split.
    start_position: The starting position for the splitting. Any points below this position along the given axis will be assigned to the first weight dictionary.
    end_position: The end position for the splitting. Any points above this position along the given axis will be assigned to the last weight dictionary.
    falloff_distance: The distance over which the returned weigh dictionaries are smoothed.
    split_number: The number of weight dictionaries you want to split the weight dictionary into.
    axis: The axis you want to mirror the deformations over ("x" "y" or "z"). 
    closed: Whether or not you want the first and last weight dictionaries to wrap around. (used for when spliiting along a closed curve or surface)

    Returns a list of weight dictionaries and a list of mask weight dictionaries.
    [[weight_dict1, weight_dict2...],[mask_dict1,mask_dict2...]]
    """
    if axis not in ('x', 'y', 'z'):
        cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
    axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
    item_list = list(weight_dictionary.items())
    index_list = [ x[0] for x in item_list ]
    position_list = [ x[1][0] for x in item_list ]
    weight_list = [ x[1][1] for x in item_list ]
    axis_position_list = [ position[axis_index] for position in position_list ]
    mask_weight_list = []
    cubic_hermite = lambda x: 1 - (3 * x ** 2 - 2 * x ** 3)
    if closed == False:
        segment_length = (end_position - start_position) / max(1, split_number - 1)
        for number in range(split_number):
            split_center = start_position + segment_length * number
            short_weight_list = []
            for x, axis_position in enumerate(axis_position_list):
                distance_to_center = abs(axis_position - split_center)
                if distance_to_center > 0.5 * segment_length + 0.5 * falloff_distance:
                    short_weight_list.append(0)
                elif distance_to_center <= 0.5 * segment_length - 0.5 * falloff_distance:
                    short_weight_list.append(1)
                else:
                    weight = (distance_to_center - (0.5 * segment_length - 0.5 * falloff_distance)) / falloff_distance
                    short_weight_list.append(cubic_hermite(weight))

            mask_weight_list.append(short_weight_list)

    else:
        segment_length = (end_position - start_position) / max(1, split_number)
        for number in range(split_number):
            split_center = start_position + segment_length * number
            short_weight_list = []
            for axis_position in axis_position_list:
                distance_to_center = abs(split_center - axis_position)
                wrapped_distance = end_position - start_position - distance_to_center
                distance = min(distance_to_center, wrapped_distance)
                if distance > 0.5 * segment_length + 0.5 * falloff_distance:
                    short_weight_list.append(0)
                elif distance <= 0.5 * segment_length - 0.5 * falloff_distance:
                    short_weight_list.append(1)
                elif falloff_distance == 0:
                    short_weight_list.append(1)
                else:
                    weight = (distance - (0.5 * segment_length - 0.5 * falloff_distance)) / falloff_distance
                    short_weight_list.append(cubic_hermite(weight))

            mask_weight_list.append(short_weight_list)

    zipped_weight_list = list(zip(*mask_weight_list))
    weight_sums = [ float(sum(x)) for x in zipped_weight_list ]
    weight_sums = [ x if x > 0 else 1.0 for x in weight_sums ]
    normalized_weights = [ [ per_index_weight / weight_sum for per_index_weight in per_index_weight_list ] for weight_sum, per_index_weight_list in zip(weight_sums, zipped_weight_list) ]
    mask_weight_list = list(zip(*normalized_weights))
    mask_weight_dict_list = [ {index:(position, weight) for index, position, weight in zip(index_list, position_list, each_weight_list)} for each_weight_list in mask_weight_list ]
    dict_list = [ multiply_weights(weight_dictionary, mask_wt) for mask_wt in mask_weight_dict_list ]
    return [
     dict_list, mask_weight_dict_list]


def split_weights_along_curve(weight_dictionary, nurbsCurve, falloff_distance=1, split_number=2, mode=0):
    """ 
    Takes a weight dictionary and splits it along the given nurbsCurve into multiple weight dictionaries. 
    
    weight_dictionary = The weight dictionary you want to split.
    falloff_distance: The distance over which the returned weigh dictionaries are smoothed.
    split_number: The number of weight dictionaries you want to split the weight dictionary into.
    mode: Which coordinate (relative to the curve) you want to use to split the curve. 

    parameter = Splits based on closest parameter 
    distanceAlong = Splits based on closest points distance along the curve 
    distanceFrom  = Splits based on the distance from the curve
            
    Returns a list of weight dictionaries and a list of mask weight dictionaries.
    [[weight_dict1, weight_dict2...],[mask_dict1,mask_dict2...]]
    """
    converted_weight_dict = convert_weightDelta_positions_to_curve_parameters(weight_dictionary, nurbsCurve)
    mode_axis = {'parameter': 'x', 'distanceAlong': 'y', 'distanceFrom': 'z'}[mode]
    if mode_axis == 'x':
        max_position = cmds.getAttr(nurbsCurve + '.minMaxValue.maxValue')
    elif mode_axis == 'y':
        max_position = cmds.arclen(nurbsCurve)
    elif mode_axis == 'z':
        distance_to_curve_list = [ x[1][0][2] for x in list(converted_weight_dict.items()) ]
        max_position = max(distance_to_curve_list)
    else:
        cmds.error(('Invalid Mode "{}"').format(mode))
    closed = cmds.getAttr(nurbsCurve + '.form')
    return split_weights_along_axis(converted_weight_dict, start_position=0, end_position=max_position, falloff_distance=falloff_distance, split_number=split_number, axis=mode_axis, closed=closed)


def split_weights_along_surface(weight_dictionary, nurbsSurface, falloff_distance=1, split_number=2, mode=0):
    """ 
    Takes a weight dictionary and splits it along the given nurbsSurface into multiple weight dictionaries. 
    
    weight_dictionary = The weight dictionary you want to split.
    nurbsSurface = The surface you want to use to split the given weight dictionary.
    falloff_distance: The distance over which the returned weigh dictionaries are smoothed.
    split_number = The number of weight dictionaries you want to split the weight dictionary into.
    mode = Which coordinate (relative to the surface) you want to use to split the curve.
    
    0 = U Parameter
    1 = V Parameter
    2 = Distance From The Surface
            
    Returns a list of weight dictionaries and a list of mask weight dictionaries.
    [[weight_dict1, weight_dict2...],[mask_dict1,mask_dict2...]]
    """
    converted_weight_dict = convert_weightDelta_positions_to_surface_uvn(weight_dictionary, nurbsSurface)
    if mode not in (0, 1, 2):
        cmds.error(('"{}" is not a valid mode').format(mode))
    mode_axis = ['x', 'y', 'z'][mode]
    if mode == 0:
        max_position = cmds.getAttr(nurbsSurface + '.minMaxRangeU.maxValueU')
    elif mode == 1:
        max_position = cmds.getAttr(nurbsSurface + '.minMaxRangeV.maxValueV')
    else:
        distance_to_surface_list = [ x[1][0][2] for x in list(converted_weight_dict.items()) ]
        max_position = max(distance_to_surface_list)
    if mode == 0:
        closed = cmds.getAttr(nurbsSurface + '.formU')
    elif mode == 1:
        closed = cmds.getAttr(nurbsSurface + '.formV')
    else:
        close = False
    return split_weights_along_axis(converted_weight_dict, start_position=0, end_position=max_position, falloff_distance=falloff_distance, split_number=split_number, axis=mode_axis, closed=closed)


def split_weights_with_plane(weight_dictionary, plane_position, plane_normal, falloff_distance):
    """
    Splits a weight dictionary into two weight dictionaries one for each side of a plane. This functions is faster than splitting with a nurbsSurface.
    
    weight_dictionary = The weight dictionary you want to split.
    plane_position = The position of the plane.
    plane_normal = The normal of the plane.
    falloff_distance = The distance from the plane over which you want to smooth the split weights.
    
    Returns a list containing two weight dictionaries one for each side of the plane.
    """
    positive_weight_dictionary = {}
    negative_weight_dictionary = {}
    planePosition = om2.MVector(*plane_position)
    planeNormal = om2.MVector(*plane_normal)
    mPlane = om2.MPlane()
    mPlane.setPlane(planeNormal, 0)
    offset_distance = mPlane.distanceToPoint(planePosition, True)
    mPlane.setPlane(planeNormal, -offset_distance)
    for comp_index, (position, weight) in list(weight_dictionary.items()):
        distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
        if distance_to_plane > falloff_distance:
            positive_weight_dictionary[comp_index] = (
             position, weight)
            negative_weight_dictionary[comp_index] = (position, 0)
        elif distance_to_plane < falloff_distance:
            negative_weight_dictionary[comp_index] = (
             position, weight)
            positive_weight_dictionary[comp_index] = (position, 0)
        elif falloff_distance == 0:
            negative_weight_dictionary[comp_index] = (
             position, 0)
            positive_weight_dictionary[comp_index] = (position, weight)
        else:
            scaled_distance = (axis_position - split_coordinate + falloff_distance) / (falloff_distance * 2)
            positive_weight = 3 * scaled_distance ** 2 - 2 * scaled_distance ** 3
            negative_weight = 1 - positive_weight
            negative_weight_dictionary[comp_index] = (
             position, weight * negative_weight)
            positive_weight_dictionary[comp_index] = (position, weight * positive_weight)

    return [
     positive_weight_dictionary, negative_weight_dictionary]


def split_weights_with_animCurve(weight_dictionary, animCurve, axis='x'):
    """
    This function will assign each component a coordinate based on it's axis component.
    Then the weight for each component will be multiplied by the value associated with that coordinate on the animCurve.
    
    weight_dictionary = The weight dictionary you want to split.
    animCurve = The animCurve you want to split the weights with.
    axis = The axis you are splitting along.

    Returns a weight dictionary.
    """
    if axis in ('x', 'y', 'z'):
        axis_int = [
         'x', 'y', 'z'].index(axis)
    else:
        cmds.error(('{} is not a valid axis "x","y","z"').format(axis))
    sel = om2.MSelectionList()
    sel.add(animCurve)
    splitter_dependNode = sel.getDependNode(0)
    mFnAnimCurve = omAnim2.MFnAnimCurve(splitter_dependNode)
    type = cmds.nodeType(animCurve)
    if type in ('animCurveTL', 'animCurveTA', 'animCurveTT', 'animCurveTU'):
        return {index:(position, mFnAnimCurve.evaluate(om2.MTime(position[axis_int])) * weight) for index, (position, weight) in list(weight_dictionary.items())}
    else:
        return {index:(position, mFnAnimCurve.evaluate(position[axis_int]) * weight) for index, (position, weight) in list(weight_dictionary.items())}


def symmetrisize_weights_with_plane(weight_dictionary, plane_position, plane_normal, direction='+ to -', matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None, max_distance=None):
    """
    Symmetrisize a weight dictionary over a plane. (faster than using a nurbsSurface)
    
    weight_dictionary = The weight dictionary you want to symmetrisize.
    plane_position = The position of the plane.
    plane_normal = The normal of the plane.
    direction: The direction in which you symmetrisize the weights, can be "+ to -" or "- to +"
    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the weights from the components that influence that point.
            When the source_shape input is a lattice the closest point on surface is actually based on volume.
        
    source_shape = The shape the weight dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentrix weight information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.
        
    max_distance = When this value is not None any components whose matching component is farther away than this distance will have their deltas remain unchanged.
    
    If the matching method is "closestComponent" it returns weight dictionary and an ii_dict so that the operation can be performed faster next time [weight_dictionary,ii_dict]
    If the matching_method is "closestPointOnSurface" it returns a weight dictionary and an ibw dict so that the operation can be performed faster next time [weight_dictionary,dict].
    """
    planePosition = om2.MVector(*plane_position)
    planeNormal = om2.MVector(*plane_normal).normalize() * -1
    mPlane = om2.MPlane()
    mPlane.setPlane(planeNormal, 0)
    offset_distance = mPlane.distanceToPoint(planePosition, True)
    mPlane.setPlane(planeNormal, -offset_distance)
    if matching_method == 'closestComponent':
        if not ii_dict:
            non_symm_ip_dict = {}
            symm_ip_dict = {}
            if direction == '+ to -':
                for index, (position, weight) in list(weight_dictionary.items()):
                    distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                    if distance_to_plane <= 0.001:
                        non_symm_ip_dict[index] = position
                    else:
                        symm_ip_dict[index] = om2.MVector(position) - 2.0 * distance_to_plane * planeNormal

            else:
                if direction == '- to +':
                    for index, (position, weight) in list(weight_dictionary.items()):
                        distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                        if distance_to_plane >= -0.001:
                            non_symm_ip_dict[index] = position
                        else:
                            symm_ip_dict[index] = om2.MVector(position) - 2.0 * distance_to_plane * planeNormal

                else:
                    cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                ii_dict = match_points_to_closest_point(symm_ip_dict, non_symm_ip_dict, max_distance=max_distance)
                symm_weght_dict = weight_dictionary.copy()
                for new, old in list(ii_dict.items()):
                    symm_weght_dict[new] = [
                     weight_dictionary[new][0], weight_dictionary[old][1]]

            return [symm_weght_dict, ii_dict]
        else:
            symm_weght_dict = weight_dictionary.copy()
            for new, old in list(ii_dict.items()):
                symm_weght_dict[new] = [
                 weight_dictionary[new][0], weight_dictionary[old][1]]

            return [symm_weght_dict, ii_dict]

    if matching_method == 'closestPointOnSurface':
        if not ibw_dict:
            non_symm_ip_dict = {}
            symm_ip_dict = {}
            if direction == '+ to -':
                for index, (position, weight) in list(weight_dictionary.items()):
                    distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                    if distance_to_plane <= 0.001:
                        non_symm_ip_dict[index] = position
                    else:
                        symm_ip_dict[index] = om2.MVector(position) - 2.0 * distance_to_plane * planeNormal

            elif direction == '- to +':
                for index, (position, weight) in list(weight_dictionary.items()):
                    distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                    if distance_to_plane >= -0.001:
                        non_symm_ip_dict[index] = position
                    else:
                        symm_ip_dict[index] = om2.MVector(position) - 2.0 * distance_to_plane * planeNormal

            else:
                cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
            orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
            ibw_dict = match_points_to_closest_point_on_surface(orig_shape, symm_ip_dict, max_distance=max_distance)
            symm_weght_dict = apply_ibw_dictionary_to_weight_dictionary(weight_dictionary, weight_dictionary, ibw_dict)
            return [
             symm_weght_dict, ibw_dict]
        else:
            symm_weght_dict = apply_ibw_dictionary_to_weight_dictionary(weight_dictionary, weight_dictionary, ibw_dict)
            return [symm_weght_dict, ibw_dict]

    else:
        cmds.error(('"{}" is not a valid matching method ("closestComponent","closestPointOnSurface")').format(matching_method))


def flip_weights_with_plane(weight_dictionary, plane_position, plane_normal, matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None, max_distance=None):
    """
    Flip a weight dictionary over a plane. (faster than using a nurbsSurface)
    
    weight_dictionary = The weight dictionary you want to symmetrisize.
    plane_position = The position of the plane.
    plane_normal = The normal of the plane.
    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the weights from the components that influence that point.
            When the source_shape input is a lattice the closest point on surface is actually based on volume.
        
    source_shape = The shape the weight dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentrix weight information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.
        
    max_distance = When this value is not None any components whose matching component is farther away than this distance will have their weights remain unchanged.
    
    If the matching method is "closestComponent" it returns weight dictionary and an ii_dict so that the operation can be performed faster next time [weight_dictionary,ii_dict]
    If the matching_method is "closestPointOnSurface" it returns a weight dictionary and an ibw dict so that the operation can be performed faster next time [weight_dictionary,dict].
    """
    planePosition = om2.MVector(plane_position)
    planeNormal = om2.MVector(plane_normal).normalize()
    mPlane = om2.MPlane()
    mPlane.setPlane(planeNormal, 0)
    offset_distance = mPlane.distanceToPoint(planePosition, True)
    mPlane.setPlane(planeNormal, -offset_distance)
    if matching_method == 'closestComponent':
        if not ii_dict:
            original_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items())}
            flipped_ip_dict = {index:om2.MVector(position) - 2.0 * mPlane.distanceToPoint(om2.MVector(*position), True) * planeNormal for index, position in list(original_ip_dict.items())}
            ii_dict = match_points_to_closest_point(flipped_ip_dict, original_ip_dict, max_distance=max_distance)
            flipped_weight_dict = {new:[weight_dictionary[new][0], weight_dictionary[old][1]] for new, old in list(ii_dict.items())}
            return [
             flipped_weight_dict, ii_dict]
        else:
            flipped_weight_dict = {new:[weight_dictionary[new][0], weight_dictionary[old][1]] for new, old in list(ii_dict.items())}
            return [
             symm_weght_dict, ii_dict]

    if matching_method == 'closestPointOnSurface':
        if not ibw_dict:
            original_ip_dict = {index:position for index, (position, weight) in list(weight_dictionary.items())}
            flipped_ip_dict = {index:om2.MVector(position) - 2.0 * mPlane.distanceToPoint(om2.MVector(*position), True) * planeNormal for index, position in list(original_ip_dict.items())}
            orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
            ibw_dict = match_points_to_closest_point_on_surface(orig_shape, flipped_ip_dict, max_distance=max_distance)
        flipped_weight_dict = apply_ibw_dictionary_to_weight_dictionary(weight_dictionary, weight_dictionary, ibw_dict)
        return [
         flipped_weight_dict, ibw_dict]
    cmds.error(('"{}" is not a valid matching method ("closestComponent","closestPointOnSurface")').format(matching_method))


def multiply_weights(weight_dictionary_01, weight_dictionary_02):
    """ 
    Takes two weight dictionaries and matches them by index and multiplies them. If the second dictionary has indexes not in 
    the first dictionary they will be skipped. If the first dictionary has indexes not in the second they will be assigned 0 weight.
    
    weight_dictionary_01: The first weight dictionary whose weights you want to multiply. This dictionary will be the source for the positions. 
    weight_dictionary_02: The second weight dictionary whose weights you want to multiply. 

    Returns a weight dictionary.
    """
    return_weights = weight_dictionary_01.copy()
    index_list_02 = list(weight_dictionary_02.keys())
    for index in list(weight_dictionary_01.keys()):
        if index in index_list_02:
            return_weights[index] = (
             weight_dictionary_01[index][0], weight_dictionary_01[index][1] * weight_dictionary_02[index][1])
        else:
            return_weights[index] = (
             weight_dictionary_01[index][0], 0)

    return return_weights


def subtract_weights(weight_dictionary_01, weight_dictionary_02, minimum=None, maximum=None):
    """ 
    Takes two weight dictionaries and matches them by index and subtracts the second from the first. If the second dictionary has indexes not in 
    the first dictionary they will be skipped. If the first dictionary has indexes not in the second they will remain unchanged.
    
    weight_dictionary_01: The first weight dictionary whose weights you want to subtract from. This dictionary will be the source for the positions. 
    weight_dictionary_02: The second weight dictionary whose weights you want to subtract. 

    Returns a weight dictionary.
    """
    index_list_02 = list(weight_dictionary_02.keys())
    for index in list(weight_dictionary_01.keys()):
        if index in index_list_02:
            weight_dictionary_01[index] = (
             weight_dictionary_01[index][0], weight_dictionary_01[index][1] - weight_dictionary_02[index][1])

    if minimum:
        weight_dictionary_01 = {index:(position, max(minimum, weight)) for index, (position, weight) in list(weight_dictionary_01.items())}
    if maximum:
        weight_dictionary_01 = {index:(position, min(maximum, weight)) for index, (position, weight) in list(weight_dictionary_01.items())}
    return weight_dictionary_01


def add_weights(weight_dictionary_01, weight_dictionary_02, minimum=None, maximum=None):
    """ 
    Takes two weight dictionaries and matches them by index and ass the second to the first.
    
    weight_dictionary_01: The first weight dictionary whose weights you want to add. This dictionary will be the source for the positions. 
    weight_dictionary_02: The second weight dictionary whose weights you want to add. 
    minimum: The lower bound for the resulting weights. Any weights lower than this value will be set to this value.
    maximum: The upper bound for the resulting weights. Any weights higher than this value will be set to this value.

    Returns a weight dictionary.
    """
    sum_weight_dictionary = weight_dictionary_01.copy()
    for index, (position, weight) in list(weight_dictionary_02.items()):
        if index in sum_weight_dictionary:
            sum_weight_dictionary[index] = (
             weight_dictionary_01[index][0], weight_dictionary_01[index][1] + weight_dictionary_02[index][1])

    if minimum:
        sum_weight_dictionary = {index:(position, max(minimum, weight)) for index, (position, weight) in list(sum_weight_dictionary.items())}
    if maximum:
        sum_weight_dictionary = {index:(position, min(maximum, weight)) for index, (position, weight) in list(sum_weight_dictionary.items())}
    return sum_weight_dictionary


def clamp_weights(weight_dictionary, minimum_weight, maximum_weight):
    """ 
    Takes a weight dictionary and clamps the weights between the minimum_weight and the maximum_weight.
    
    weight_dictionary = The weight dictionary you want to clamp
    minimum_weight: The minimum weight used for the clamping.
    maximum_weight: The maximum weight used for the clamping.

    Returns a weight dictionaries. 
    """
    return {comp_index:(pos, min(maximum_weight, max(minimum_weight, weight))) for comp_index, (pos, weight) in list(weight_dictionary.items())}


def normalize_weights(weight_dictionary_list):
    """ 
    Takes a list of weight dictionaries and normalizes them so that for each index the weights add up to 1
    
    weight_dictionary_list: The list of weight dictionaries whose weights you want to normalize. 

    Returns a list of weight dictionaries. 
    """
    if len(weight_dictionary_list) == 1:
        return weight_dictionary_list
    long_index_list = [ max(weight_dictionary.keys()) for weight_dictionary in weight_dictionary_list ]
    sum_weight_list = [ 0 for index in range(max(long_index_list) + 1) ]
    for weight_dictionary in weight_dictionary_list:
        for index, (position, weight) in list(weight_dictionary.items()):
            sum_weight_list[index] += weight

    return_weight_dict_list = []
    for weight_dictionary in weight_dictionary_list:
        weight_dict = {}
        for index, (pos, wt) in list(weight_dictionary.items()):
            if sum_weight_list[index] != 0:
                weight_dict[index] = (
                 pos, wt / sum_weight_list[index])
            else:
                weight_dict[index] = (
                 pos, 0)

        return_weight_dict_list.append(weight_dict)

    return return_weight_dict_list


def transform_weights(weight_dictionary, mMatrix):
    return {key:[tuple(om2.MPoint(position) * mMatrix)[0:3], wt] for key, (position, wt) in list(weight_dictionary.items())}


def set_deformer_weights(deformer_node, weight_dictionary, shape=None, component_list=None, undoable=False):
    """ 
    Assign the weights from the given weight dictionary to the given deformer on the given shape.

    deformer_node: The deformer you want to load the weights onto. Example: "cluster2" 
    component_list = The list of components you want to set the weights for. 
                     If set to None, the function will default to using the shape input and apply the weights to the entire shape. Example: ["cubeShape1.vtx[0]","cubeShape1.vtx[1]",...]
    weight_dictionary = The weight dictionary you want to apply.
    shape = The shape you want to apply the weights to. If component list is not None, the weights will only be applied to the components in the component_list.
    """
    if shape == None:
        shape = component_list[0].split('.')[0]
    if not cmds.objExists(shape):
        cmds.error(('The given shape "{}" does not exist').format(shape))
    shape = cmds.ls(shape)[0]
    shape = cmds.ls(shape, l=True)[0]
    geo_list = cmds.deformer(deformer_node, q=True, g=True)
    geo_list = [ cmds.ls(x, l=True)[0] for x in geo_list ]
    if not geo_list:
        cmds.error(('"{}" does not affect any geo').format(deformer_node))
    if shape not in geo_list:
        cmds.error(('"{}" is not affected by "{}"').format(shape, deformer_node))
    else:
        deformer_type = cmds.nodeType(deformer_node)
        if deformer_type in ('ffd', 'nonLinear', 'repulsor'):
            if component_list == None:
                component_list = get_component_list(shape)
            if cmds.pluginInfo('weight_utils_cmds.py', q=True, loaded=True) and undoable:
                mSelectionList = om2.MSelectionList()
                mSelectionList.add(deformer_node)
                mSelectionList.add(shape)
                mObject_lattice = mSelectionList.getDependNode(0)
                mObject_shape = mSelectionList.getDependNode(1)
                mFnGeometryFilter = omAnim2.MFnGeometryFilter(mObject_lattice)
                shape_logical_index = mFnGeometryFilter.indexForOutputShape(mObject_shape)
                mFnDependencyNode = om2.MFnDependencyNode(mObject_lattice)
                weights_mPlug = mFnDependencyNode.findPlug('weightList', False).elementByLogicalIndex(shape_logical_index).child(0)
                index_list = get_index_list(component_list)
                if component_list != None:
                    index_list = get_index_list(component_list)
                mFloatArray_oldWeights = om.MFloatArray()
                shared_index_set = set(get_index_list(component_list)) & set(weight_dictionary.keys())
                while not mit.isDone():
                    comp_index = mit.index()
                    if comp_index in shared_index_set:
                        mFloatArray_oldWeights.append(weight_dictionary[comp_index][1])
                    else:
                        mFloatArray_oldWeights.append(weights_mPlug.elementByLogicalIndex(comp_index))
                    next(mit)

                cmds.setDeformerWeights(deformer_node, shape, list(mFloatArray_oldWeights))
            else:
                mSelectionList = om2.MSelectionList()
                mSelectionList.add(deformer_node)
                mSelectionList.add(shape)
                mObject_lattice = mSelectionList.getDependNode(0)
                mObject_shape = mSelectionList.getDependNode(1)
                mFnGeometryFilter = omAnim2.MFnGeometryFilter(mObject_lattice)
                shape_logical_index = mFnGeometryFilter.indexForOutputShape(mObject_shape)
                mFnDependencyNode = om2.MFnDependencyNode(mObject_lattice)
                weights_mPlug = mFnDependencyNode.findPlug('weightList', False).elementByLogicalIndex(shape_logical_index).child(0)
                index_list = get_index_list(component_list)
                mdg = om2.MDGModifier()
                for index in list(weight_dictionary.keys()):
                    mdg.newPlugValueFloat(weights_mPlug.elementByLogicalIndex(int(index)), weight_dictionary[index][1])

                mdg.doIt()
        elif deformer_type in ('cluster', 'wire', 'softMod'):
            member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(deformer_node, shape)
            shape_logical_index = mFnGeometryFilter.indexForOutputShape(mObject_shape)
            components = om.MObject()
            dagPath = om.MDagPath()
            members.getDagPath(member_index, dagPath, components)
            mFnWeight = omAnim.MFnWeightGeometryFilter(mObject_deformer)
            mFloatArray_oldWeights = om.MFloatArray()
            mFnWeight.getWeights(shape_logical_index, components, mFloatArray_oldWeights)
            mFloatArray_index = 0
            mit = om.MItGeometry(dagPath, components)
            if component_list != None:
                shared_index_set = set(get_index_list(component_list)) & set(weight_dictionary.keys())
                while not mit.isDone():
                    comp_index = mit.index()
                    if comp_index in shared_index_set:
                        mFloatArray_oldWeights[mFloatArray_index] = weight_dictionary[comp_index][1]
                    mFloatArray_index += 1
                    next(mit)

            else:
                valid_keys = list(weight_dictionary.keys())
                while not mit.isDone():
                    comp_index = mit.index()
                    if comp_index in valid_keys:
                        mFloatArray_oldWeights.set(weight_dictionary[comp_index][1], mFloatArray_index)
                    mFloatArray_index += 1
                    next(mit)

            if cmds.pluginInfo('weight_utils_cmds.py', q=True, loaded=True) and undoable:
                cmds.setDeformerWeights(deformer_node, shape, list(mFloatArray_oldWeights))
            else:
                mFnWeight.setWeight(dagPath, shape_logical_index, components, mFloatArray_oldWeights)
        else:
            cmds.error(('"{}" is not a valid deformer type').format(deformer_node))
    return


def set_ngSkin_influence_weights(layer_ID, influence_name, weight_dictionary, component_list=None, shape=None):
    """ 
    Assign the weights from the given weight dictionary to the given influence on the given layer on the given shape.

    layer_ID = The ID of the layer you want to query weights from. 
    influence_name = The name of the influence you want to query weights from. Example: "joint1" 
    weight_dictionary = The weight dictionary you want to apply.
    component_list = The list components you want get the weights for. Example: ["cubeShape1.vtx[0]","cubeShape1.vtx[1]",...] 
    shape = The shape you want to apply the weights to. If component list is not None, the weights will only be applied to the components in the component_list.
    """
    if shape == None:
        shape = component_list[0].split('.')[0]
    if not cmds.objExists(shape):
        cmds.error(('The given shape "{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    set_list = cmds.listSets(object=shape)
    for set in set_list:
        used_by_list = cmds.listConnections(set + '.usedBy[0]')
        if used_by_list:
            if cmds.nodeType(used_by_list[0]) == 'skinCluster':
                break
    else:
        cmds.error(('{} has no skinCluster').format(shape))

    transform_node = cmds.listRelatives(shape, p=True)[0]
    from ngSkinTools.mllInterface import MllInterface
    mll = MllInterface()
    mll.setCurrentMesh(transform_node)
    layer_dictionary = {x[0]:x[1] for x in mll.listLayers()}
    if layer_ID not in layer_dictionary:
        cmds.error(('Layer with ID {} does not exist.').format(layer_ID))
    long_influence_name = cmds.ls(influence_name, int=True)[0]
    influence_name_list = mll.listInfluencePaths()
    influence_index_list = mll.listInfluenceIndexes()
    influence_index_list = [ int(str(index).replace('L', '')) for index in influence_index_list ]
    influence_dictionary = dict(list(zip(influence_name_list, influence_index_list)))
    if long_influence_name in influence_dictionary:
        influenceId = influence_dictionary[long_influence_name]
    else:
        cmds.error(('"{}" does not affect "{}"').format(influence_name, shape))
    full_weight_list = mll.getInfluenceWeights(layer_ID, influenceId)
    if full_weight_list == []:
        full_weight_list = [
         1.0] * mll.getVertCount()
    if component_list:
        comp_index_list = get_index_list(component_list)
        for index in comp_index_list:
            if index in weight_dictionary:
                full_weight_list[index] = weight_dictionary[index][1]

    else:
        for index, (position, weight) in list(weight_dictionary.items()):
            full_weight_list[index] = weight

    mll.setInfluenceWeights(layer_ID, influenceId, full_weight_list, undoEnabled=True)
    return


def set_ngSkin_mask_weights(layer_ID, weight_dictionary, shape=None, component_list=None):
    """ 
    Assign the weights from the given weight dictionary to the given layer mask on the given shape.

    layer_ID = The ID of the layer whose mask you want to assign the weights to. 
    weight_dictionary = The weight dictionary you want to apply.
    component_list = The list components you want get the weights for. Example: ["cubeShape1.vtx[0]","cubeShape1.vtx[1]",...] 
    shape = The shape you want to apply the weights to. If component list is not None, the weights will only be applied to the components in the component_list.
    """
    if shape == None:
        shape = component_list[0].split('.')[0]
    if not cmds.objExists(shape):
        cmds.error(('The given shape "{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    set_list = cmds.listSets(object=shape)
    for set in set_list:
        used_by_list = cmds.listConnections(set + '.usedBy[0]')
        if used_by_list:
            if cmds.nodeType(used_by_list[0]) == 'skinCluster':
                break
    else:
        cmds.error(('{} has no skinCluster').format(shape))

    transform_node = cmds.listRelatives(shape, p=True)[0]
    from ngSkinTools.mllInterface import MllInterface
    mll = MllInterface()
    mll.setCurrentMesh(transform_node)
    layer_dictionary = {x[0]:x[1] for x in mll.listLayers()}
    if layer_ID not in layer_dictionary:
        cmds.error(('Layer with ID {} does not exist.').format(layer_ID))
    full_weight_list = mll.getLayerMask(layer_ID)
    if full_weight_list == []:
        full_weight_list = [
         1.0] * mll.getVertCount()
    if component_list is not None:
        comp_index_list = get_index_list(component_list)
        for index in comp_index_list:
            if index in weight_dictionary:
                full_weight_list[index] = weight_dictionary[index][1]

    else:
        for index, (position, weight) in list(weight_dictionary.items()):
            full_weight_list[index] = weight

    mll.setLayerMask(layer_ID, full_weight_list)
    return


def set_ngSkin_DQ_weights(layer_ID, weight_dictionary, shape=None, component_list=None):
    """ 
    Assign the weights from the given weight dictionary to the dual Quaterion weights for the given layer on the given shape.

    layer_ID = The ID of the layer whose mask you want to assign the weights to. 
    weight_dictionary = The weight dictionary you want to apply.
    component_list = The list components you want get the weights for. Example: ["cubeShape1.vtx[0]","cubeShape1.vtx[1]",...] 
    shape = The shape you want to apply the weights to. If component list is not None, the weights will only be applied to the components in the component_list.
    """
    if not cmds.objExists(shape):
        cmds.error(('shape:"{}" does not exist').format(shape))
    if cmds.nodeType(shape) != 'mesh':
        cmds.error(('shape:"{}" is not a mesh').format(shape))
    set_list = cmds.listSets(object=shape)
    for set in set_list:
        used_by_list = cmds.listConnections(set + '.usedBy[0]')
        if used_by_list:
            if cmds.nodeType(used_by_list[0]) == 'skinCluster':
                break
    else:
        cmds.error(('{} has no skinCluster').format(shape))

    transform_node = cmds.listRelatives(shape, p=True)[0]
    from ngSkinTools.mllInterface import MllInterface
    mll = MllInterface()
    mll.setCurrentMesh(transform_node)
    layer_dictionary = {x[0]:x[1] for x in mll.listLayers()}
    if layer_ID not in layer_dictionary:
        cmds.error(('Layer with ID {} does not exist.').format(layer_ID))
    full_weight_list = mll.getDualQuaternionWeights(layer_ID)
    if full_weight_list == []:
        full_weight_list = [
         1.0] * mll.getVertCount()
    if component_list is not None:
        comp_index_list = get_index_list(component_list)
        for index in comp_index_list:
            if index in weight_dictionary:
                full_weight_list[index] = weight_dictionary[index][1]

    else:
        for index, (position, weight) in list(weight_dictionary.items()):
            full_weight_list[index] = weight

    mll.setDualQuaternionWeights(layer_ID, full_weight_list)
    return


def set_blendShape_target_weights(blendShape_node, blendShape_target, weight_dictionary, component_list=None, shape=None):
    """ 
    Assign the weights from the given weight dictionary to the given blendShape target on the given blendShape node.

    blendShape_node: The blendShape node you want to load the weights onto. Example: "blendShape1" 
    blendShape_target: The blendShape target you want to load the weights onto. Example: "target1" 
    weight_dictionary = The weight dictionary you want to apply.
    component_list = The list components you want get the weights for. Example: ["cubeShape1.vtx[0]","cubeShape1.vtx[1]",...]    
    shape = The shape you want to apply the weights to. If component list is not None, the weights will only be applied to the components in the component_list. (this is only required if you have two shapes deformed by the same blendShape node)
    """
    target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    geo_list = cmds.blendShape(blendShape_node, q=True, g=True)
    if not geo_list:
        cmds.error(('{} does not affect any geometry').format(blendShape_node))
    if not shape:
        if component_list:
            shape = component_list[0].split('.')[0]
            shape = cmds.ls(shape, l=True)[0]
        else:
            shape = geo_list[0]
    geo_list = [ cmds.ls(x, l=True)[0] for x in geo_list ]
    if cmds.ls(shape, l=True)[0] not in geo_list:
        cmds.error(('"{}" is not affected by "{}"').format(shape, blendShape_node))
    if component_list is None:
        component_list = get_component_list(shape)
    member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(blendShape_node, shape)
    mFnDependencyNode = om.MFnDependencyNode(mObject_deformer)
    mPlug = mFnDependencyNode.findPlug('inputTarget').elementByLogicalIndex(member_index).child(0).elementByLogicalIndex(target_index).child(1)
    for comp_index in get_index_list(component_list):
        if comp_index in weight_dictionary:
            mPlug.elementByLogicalIndex(comp_index).setFloat(weight_dictionary[comp_index][1])
        else:
            mPlug.elementByLogicalIndex(comp_index).setFloat(0)

    return


def set_blendShape_base_weights(blendShape_node, weight_dictionary, component_list=None, shape=None):
    """ 
    Assign the weights from the given weight dictionary to the given blendShape nodes base weights.

    blendShape_node: The blendShape node you want to load the weights onto. Example: "blendShape1" 
    blendShape_target: The blendShape target you want to load the weights onto. Example: "target1" 
    weight_dictionary = The weight dictionary you want to apply.
    component_list = A list components you want get the weights for. Example: ["cubeShape1.vtx[0]","cubeShape1.vtx[1]",...] 
    shape = The shape you want to apply the weights to. If component list is not None, the weights will only be applied to the components in the component_list. (this is only required if you have two shapes deformed by the same blendShape node)s
    """
    if not cmds.objExists(blendShape_node):
        cmds.error(('"{}" does not exist').format(blendShape_node))
    if not shape:
        if component_list:
            shape = component_list[0].split('.')[0]
            shape = cmds.ls(shape, l=True)[0]
        else:
            geo_list = cmds.blendShape(blendShape_node, q=True, g=True)
            if not geo_list:
                cmds.error(('{} does not affect any geometry').format(blendShape_node))
            shape = geo_list[0]
    geo_list = cmds.blendShape(blendShape_node, q=True, g=True)
    if not geo_list:
        cmds.error(('{} does not affect any geometry').format(blendShape_node))
    if shape not in geo_list:
        cmds.error(('"{}" is not affected by "{}"').format(shape, blendShape_node))
    component_list = get_component_list(shape)
    index_list = get_index_list(component_list)
    member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(blendShape_node, shape)
    mFnDependencyNode = om.MFnDependencyNode(mObject_deformer)
    mPlug = mFnDependencyNode.findPlug('inputTarget').elementByLogicalIndex(member_index).child(1)
    for comp_index in get_index_list(component_list):
        if comp_index in weight_dictionary:
            mPlug.elementByLogicalIndex(comp_index).setFloat(weight_dictionary[comp_index][1])
        else:
            mPlug.elementByLogicalIndex(comp_index).setFloat(0)


def set_weightList_weights(deformer_node, shape, weightListPlug, weight_dictionary, component_list=None):
    """ 
    Applies a weight dictionary to the given weightList on the given shape.
    
    deformer_node: The deformer node you want to put the weights on.
    shape: The shape whose weights you want to change.
    weightListPlug: The weightList plug you want to put the weights on.
    """
    if not cmds.objExists(deformer_node):
        cmds.error(('deformer node "{}" does not exist').format(deformer_node))
    sel = om2.MSelectionList()
    sel.add(deformer_node)
    mObj_deformer_node = sel.getDependNode(0)
    if not mObj_deformer_node.hasFn(om2.MFn.kWeightGeometryFilt):
        cmds.error(('"{}" is not a deformer node').format(deformer_node))
    if not cmds.objExists(shape):
        cmds.error(('shape: "{}" does not exists').format(deformer_node))
    shape = cmds.ls(shape, l=True)[0]
    geo_list = cmds.deformer(deformer_node, q=True, g=True)
    geo_list = [ cmds.ls(x, l=True)[0] for x in geo_list ]
    if shape not in geo_list:
        cmds.error(('"{}" is not affected by "{}"').format(shape, deformer_node))
    member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(deformer_node, shape)
    shape_logical_index = mFnGeometryFilter.indexForOutputShape(mObject_shape)
    weights_mPlug = weightListPlug.elementByLogicalIndex(shape_logical_index).child(0)
    weights_name = weights_mPlug.elementByLogicalIndex(0).name()
    default_wt = cmds.attributeQuery(weights_name.split('.')[(-1)].split('[')[0], node=weights_name.split('.')[0], listDefault=True)[0]
    components = om.MObject()
    dagPath = om.MDagPath()
    members.getDagPath(member_index, dagPath, components)
    mit = om.MItGeometry(dagPath, components)
    i = 0
    if component_list:
        component_index_list = get_index_list(component_list)
        while not mit.isDone():
            comp_index = mit.index()
            if comp_index in weight_dictionary and comp_index in component_index_list:
                weights_mPlug.elementByLogicalIndex(comp_index).setFloat(weight_dictionary[comp_index][1])
            next(mit)

    else:
        while not mit.isDone():
            comp_index = mit.index()
            if comp_index in weight_dictionary:
                weights_mPlug.elementByLogicalIndex(comp_index).setFloat(weight_dictionary[comp_index][1])
            else:
                weights_mPlug.elementByLogicalIndex(comp_index).setFloat(default_wt)
            next(mit)


def set_skinCluster_DQ_weights(skinCluster_node, weight_dictionary):
    """ 
    Sets the weightBlended weights on the given skinCluster

    skinCluster_node = the skinCluster you are setting weights for
    """
    if not cmds.objExists(skinCluster_node):
        cmds.error(('skinCluster_node:"{}" does not exist').format(skinCluster_node))
    if not cmds.nodeType(skinCluster_node) == 'skinCluster':
        cmds.error(('skinCluster_node:"{}" is not a skinCluster').format(skinCluster_node))
    deformed_shapes = cmds.deformer(skinCluster_node, q=True, g=True)
    if deformed_shapes:
        shape = deformed_shapes[0]
    else:
        cmds.error(('"{}" does not deformer any geometry').format(skinCluster_node))
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(skinCluster_node)
    mSelectionList.add(shape)
    mObject_skinCluster = mSelectionList.getDependNode(0)
    mDagPath_shape, mObject_shape_components = mSelectionList.getComponent(1)
    mFnSkinCluster = omAnim2.MFnSkinCluster(mObject_skinCluster)
    if cmds.nodeType(shape) == 'mesh':
        meshVerItFn = om2.MItMeshVertex(mDagPath_shape)
        indices = list(range(meshVerItFn.count()))
        singleIdComp = om2.MFnSingleIndexedComponent()
        comp_list = singleIdComp.create(om2.MFn.kMeshVertComponent)
        singleIdComp.addElements(indices)
    elif cmds.nodeType(shape) == 'nurbsCurve':
        curveItFn = om2.MItCurveCV(mDagPath_shape)
        indices = om2.MIntArray()
        while not curveItFn.isDone():
            indices.append(index)
            next(curveItFn)

        singleIdComp = om2.MFnSingleIndexedComponent()
        comp_list = singleIdComp.create(om2.MFn.kCurveCVComponent)
        doubleIdComp.addElements(indices)
    elif cmds.nodeType(shape) == 'nurbsSurface':
        surfaceItFn = om2.MItSurfaceCV(mDagPath_shape)
        doubleIdComp = om2.MFnDoubleIndexedComponent()
        comp_list = doubleIdComp.create(om2.MFn.kSurfaceCVComponent)
        sizeInV = om2.MFnNurbsSurface(mDagPath_shape).numCVsInV
        while not surfaceItFn.isDone():
            index = surfaceItFn.index()
            indexU = index / sizeInV
            indexU = index % sizeInV
            doubleIdComp.addElement(indexU, indexU)
            next(surfaceItFn)

    else:
        cmds.error(('DQ weights cannot be queried for "{}"').format(shape))
    weight_MDoubleArray = om2.MDoubleArray([ w for i, (p, w) in list(weight_dictionary.items()) ])
    mFnSkinCluster.setBlendWeights(mDagPath_shape, comp_list, weight_MDoubleArray)


def get_shape_data(shape, prePose=True):
    """
    Gets the required data to recreate a shape node. This function is intended to be used when exporting weights or deltas to a json file 
    so that "closestPointOnSurface" or "closestComponentUV" matching can be used when loading the weights or deltas.
    
    shape = The shape node you want to export the data for.
    prePose = When True, this function will return the list of positions for the shape prior to any deformations. 
    
    When the input shape is a mesh type object returns a list containing:
    *A list of the objectSpace positions of the vertices of the given shape.
    *A list of the number of verts each polygonal face has].
    *A list of the vertex indices for each polygonal face contains (this list is flat, it is not a list of tuples).
    *A list of tuples containing the UV coordinates of each vertex.
    *The type of shape you are exporting data for.
    
    When the input shape is a nurbsSurface type object returns a list containing:
    *A list of the objectSpace positions of the cvs of the given shape.
    *Parameter values for the knots in the U direction.
    *Parameter values for the knots in the V direction.
    *The degree of the surface in U.
    *The degree of the surface in V.
    *The form of the surface in U.
    *The form of th surface in V.
    *Whether or not the surface is rational.
    *The type of shape you are exporting data for.
    
    When the input shape is a nurbsCurve type object returns a list containing:
    *A list of the objectSpace positions of the cvs of the given shape.
    *Parameter values for the knots in the U direction.
    *The degree of the curve.
    *The form of the curve.
    *Whether or not the surface is 2D in the Z axis.
    *Whether or not the surface is rational.
    *The type of shape you are exporting data for.
    
    When the input shape is a lattice type object returns a list containing:
    *A list of the objectSpace positions of the pnts of the given shape.
    *The number of division in S
    *The number of division in T
    *The number of division in U
    *The type of shape you are exporting data for.
    """
    used_shape = shape
    if prePose == True:
        transform = cmds.listRelatives(shape, p=True, f=True)[0]
        used_shape = cmds.listRelatives(transform, s=True, f=True)[(-1)]
    if cmds.nodeType(used_shape) == 'mesh':
        sel = om2.MSelectionList()
        sel.add(used_shape)
        dagNode = sel.getDependNode(0)
        mFn = om2.MFnMesh(dagNode)
        points = mFn.getPoints()
        points = [ tuple(x) for x in points ]
        verts, vert_connects = mFn.getVertices()
        UVs = mFn.getUVs()
        UVs = [ tuple(x) for x in UVs ]
        return [
         points, list(verts), list(vert_connects), UVs, 'mesh']
    else:
        if cmds.nodeType(used_shape) == 'nurbsSurface':
            sel = om2.MSelectionList()
            sel.add(used_shape)
            dagNode = sel.getDependNode(0)
            mFn = om2.MFnNurbsSurface(dagNode)
            points = mFn.cvPositions()
            points = [ tuple(x) for x in points ]
            knotsInU = [ x for x in mFn.knotsInU() ]
            knotsInV = [ x for x in mFn.knotsInV() ]
            degU = mFn.degreeInU
            degV = mFn.degreeInV
            formU = mFn.formInU
            formV = mFn.formInV
            rational = True
            return [
             points, knotsInU, knotsInV, degU, degV, formU, formV, rational, 'nurbsSurface']
        if cmds.nodeType(used_shape) == 'nurbsCurve':
            sel = om2.MSelectionList()
            sel.add(used_shape)
            dagNode = sel.getDependNode(0)
            mFn = om2.MFnNurbsCurve(dagNode)
            points = mFn.cvPositions()
            knotsInU = [ float(x) for x in mFn.knots() ]
            points = [ tuple(x) for x in points ]
            degree = mFn.degree
            form = mFn.form
            is2D = False
            rational = True
            return [
             points, knotsInU, degree, form, is2D, rational, 'nurbsCurve']
        if cmds.nodeType(used_shape) == 'lattice':
            pnts = get_position_list(used_shape)
            sDiv = cmds.getAttr(used_shape + '.sDivisions')
            tDiv = cmds.getAttr(used_shape + '.tDivisions')
            uDiv = cmds.getAttr(used_shape + '.uDivisions')
            return [
             pnts, sDiv, tDiv, uDiv, 'lattice']
        cmds.error(('shape data can not be queried for {} objects').format(cmds.nodeType(used_shape)))
        return


def create_shape_from_data(shape_data):
    """
    Takes shape data (see the description for get_shape_data) and uses it to create a shape in the scene). 
    Be careful, if the data has been modified improperly by hand this command may cause Maya to crash.
    
    shape_data = The shape data you want to use to generate a new shape.
    
    Returns the name of the shape node that was created.
    """
    shape_type = shape_data[(-1)]
    if shape_type == 'mesh':
        points, verts, vert_connects, UVs, shape_type = shape_data
        mPointArray_points = om2.MPointArray(points)
        mIntArray_verts = om2.MIntArray(verts)
        mIntArray_vert_connects = om2.MIntArray(vert_connects)
        mFloatArray_U = om2.MFloatArray(UVs[0])
        mFloatArray_V = om2.MFloatArray(UVs[1])
        newMesh = om2.MFnMesh()
        shape_mObject = newMesh.create(mPointArray_points, mIntArray_verts, mIntArray_vert_connects)
        shape_dagPath = om2.MDagPath()
        newMesh.clearUVs()
        newMesh.setUVs(mFloatArray_U, mFloatArray_V)
        newMesh.assignUVs(mIntArray_verts, mIntArray_vert_connects)
        if shape_mObject.hasFn(om2.MFn.kDagNode):
            transform_name = om2.MDagPath.getAPathTo(shape_mObject)
            shape_name = cmds.listRelatives(transform_name, s=True)[0]
        return shape_name
    if shape_type == 'nurbsSurface':
        points, uKnots, vKnots, degU, degV, formU, formV, rational, shape_type = shape_data
        mPointArray_points = om2.MPointArray(points)
        newSurface = om2.MFnNurbsSurface()
        shape_mObject = newSurface.create(points, uKnots, vKnots, degU, degV, formU, formV, rational)
        shape_dagPath = om2.MDagPath()
        if shape_mObject.hasFn(om2.MFn.kDagNode):
            transform_name = om2.MDagPath.getAPathTo(shape_mObject)
            shape_name = cmds.listRelatives(transform_name, s=True)[0]
        return shape_name
    if shape_type == 'nurbsCurve':
        points, knotsInU, degree, form, is2D, rational, shape_type = shape_data
        mPointArray_points = om2.MPointArray(points)
        newCurve = om2.MFnNurbsCurve()
        shape_mObject = newCurve.create(mPointArray_points, knotsInU, degree, form, is2D, rational)
        shape_dagPath = om2.MDagPath()
        if shape_mObject.hasFn(om2.MFn.kDagNode):
            transform_name = om2.MDagPath.getAPathTo(shape_mObject)
            shape_name = cmds.listRelatives(transform_name, s=True)[0]
        return shape_name
    if shape_type == 'lattice':
        points, sDiv, tDiv, uDiv, shape_type = shape_data
        newLattice = omAnim.MFnLattice()
        shape_mObject = newLattice.create(sDiv, tDiv, uDiv)
        if shape_mObject.hasFn(om.MFn.kDagNode):
            shape_dagPath = om.MDagPath()
            om.MDagPath.getAPathTo(shape_mObject, shape_dagPath)
            transform_name = shape_dagPath.fullPathName()
            shape_name = cmds.listRelatives(transform_name, s=True)[0]
        for pos, pnt in zip(points, cmds.ls(shape_name + '.pt[*][*][*]', fl=True)):
            cmds.move(pos[0], pos[1], pos[2], pnt, a=True)

        return shape_name
    return
    return


def save_dictionary(save_path, dictionary, shape_data=None):
    """ 
    Saves the weight or delta dictionary to a JSON file 

    save_path: The full path name of the JSON file you want to save your deformer weights to, Example: "/desktop/lip_weights.json" 
    dictionary = The dictionary you want to save.
    shape_data = The shape data you want to save.
    """
    with open(save_path, 'w') as (wf):
        json.dump([dictionary, shape_data], wf, sort_keys=True, indent=4, ensure_ascii=False)


def load_dictionary(load_path):
    """ 
    Loads the weight or delta dictionary and shape data from a JSON file. 

    load_path: The full path name of the JSON file you want to load your dictionary from, Example: "/desktop/lip_weights.json" 
    
    Returns a list containing a dictionary representing a set of  weights or deltas, and list representing the shape data. 
    """
    try:
        open(load_path, 'r')
    except:
        return {}

    with open(load_path, 'r') as (rf):
        x = json.load(rf)
        loaded_dictionary = x[0]
        shape_data = x[1]
    return ({int(key):value for key, value in list(loaded_dictionary.items())}, shape_data)


def load_weights_only_dictionary(load_path):
    """ 
    Loads the weight or delta dictionary from a JSON file. 

    load_path: The full path name of the JSON file you want to load your dictionary from, Example: "/desktop/lip_weights.json" 
    
    Returns a dictionary representing a set of  weights or deltas.
    """
    try:
        open(load_path, 'r')
    except:
        return {}

    with open(load_path, 'r') as (rf):
        loaded_dictionary = json.load(rf)
    return {int(key):value for key, value in list(loaded_dictionary.items())}


def load_xml(load_path):
    """ 
    Loads the weight or delta dictionary from an xml file that has exported by maya. 

    load_path: The full path name of the xml file you want to load your dictionary from, Example: "/desktop/lip_weights.xml" 
    
    Returns a list of weight dictionaries.
    """
    try:
        root = ET.parse(load_path).getroot()
    except:
        return {}

    ip_dict = {}
    for component in root[2]:
        ip_dict[int(component.attrib['index'])] = [ float(x) for x in component.attrib['value'].split(' ')[1:] ]

    return_dict_list = []
    for weight_list in root[3:]:
        index_weight_dict = {}
        for component in weight_list:
            index_weight_dict[int(component.attrib['index'])] = float(component.attrib['value'])

        weight_dictionary = {index:(ip_dict[index], weight) for index, weight in list(index_weight_dict.items())}
        return_dict_list.append(weight_dictionary)

    if return_dict_list == []:
        weight_dictionary = {index:(position, 1.0) for index, position in list(ip_dict.items())}
        return_dict_list.append(weight_dictionary)
    return return_dict_list


def convert_shape_to_index_position_dictionary(shape=None, component_list=None, prePose=True, object_space=True):
    """
    Takes a list of components and returns a dictionary containing the components index and their positions in the form {index:position}.
    This is useful, because the dictionary can be stored and used again for another point matching without recalculating it.
    
    shape = The shape whose components you want to convert to an index:position dictionary. "pSphereSphape1"
    component_list = A list of components you want to create a dictionary for. Example: ["cubeShape1.vtx[0]","cubeShape1.vtx[1]",...] 
    prePose = When True the positions of in the returned dictionary will be from the shape before any deformations.
    object_space = When True, the positions of in the returned dictionary will be in object space.
    
    Returns a dictionary containing the components index and their positions in the form {index:position}.       
    """
    if component_list:
        shape = component_list[0].split('.')[0]
    elif shape:
        component_list = get_component_list(shape)
    else:
        return
    index_list = get_index_list(component_list)
    position_list = get_position_list(shape, prePose=prePose, object_space=object_space)
    return {index:position_list[index] for index in index_list}


def convert_weightDelta_dictionary_to_index_position_dictionary(input_dictionary):
    """
    Takes a weight dictionary and converts it into an index:position dictionary. 
    Using this function allows you to save and use position data without having the shape in the scene.
    
    Returns an index:position dictionary.
    """
    return {index:position for index, (position, weight) in list(input_dictionary.items())}


def match_weights_to_shape(weight_dictionary, target_shape, matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None, target_object_space=False):
    """
    Takes a weight dictionary and matches each point on the dictionary to the closest point on the input shape.
    
    weight_dictionary = The weight dictionary you want to match to the given shape.
    target_shape = The shape node you want to match the weight dictionary to.
    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the deltas from the components that influence that point.
            When the source_shape input is a lattice the closest point on surface is actually based on volume.
        closestComponentUV = 
            Matches to the closest compoennt on the other side in UV space.
            The returned dictionary will not UV coordinate information instead of worldspace position information.
            Note: You will probably want to set the symm_coordinate to .5 when using this method.
    
    source_shape = The shape the weight dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentrix delta information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.

    If the matching_method is "closestComponent" or "closestComponentUV" this command will return a weight dictionary and an ii_dict in a list.
    If the matching_method is "closestPointOnSurface" this command will return a weight dictionary and an ibw_dict in a list. 
    """
    if matching_method == 'closestComponent':
        if not ii_dict:
            source_ip_dictionary = convert_weightDelta_dictionary_to_index_position_dictionary(weight_dictionary)
            target_ip_dictionary = convert_shape_to_index_position_dictionary(shape=target_shape, object_space=target_object_space)
            ii_dict = match_points_to_closest_point(source_ip_dictionary, target_ip_dictionary)
        matched_dictionary = {new_index:weight_dictionary[old_index] for new_index, old_index in list(ii_dict.items())}
        return [
         matched_dictionary, ii_dict]
    if matching_method == 'closestComponentUV':
        if not ii_dict:
            source_ip_dictionary = convert_weightDelta_dictionary_to_index_position_dictionary(weight_dictionary)
            source_ip_dictionary = convert_ipDict_positions_to_UV_coordinates(source_ip_dictionary, target_shape)
            target_ip_dictionary = convert_shape_to_index_position_dictionary(shape=target_shape, object_space=target_object_space)
            target_ip_dictionary = convert_ipDict_positions_to_UV_coordinates(target_ip_dictionary, target_shape)
            ii_dict = match_points_to_closest_point(source_ip_dictionary, target_ip_dictionary)
        matched_dictionary = {new_index:weight_dictionary[old_index] for new_index, old_index in list(ii_dict.items())}
        return [
         matched_dictionary, ii_dict]
    if matching_method == 'closestPointOnSurface':
        if cmds.nodeType(source_shape) == 'mesh':
            if not ibw_dict:
                target_ip_dictionary = convert_shape_to_index_position_dictionary(shape=target_shape, object_space=target_object_space)
                orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
                ibw_dict = match_points_to_closest_point_on_surface(orig_shape, target_ip_dictionary)
            matched_dictionary = apply_ibw_dictionary_to_weight_dictionary(weight_dictionary, weight_dictionary, ibw_dict)
            return [
             matched_dictionary, ibw_dict]
        cmds.error('"closestPointOnSurface" matching_method only works when the source_shape is a mesh')


def match_deltas_to_shape(delta_dictionary, target_shape, matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None, target_object_space=False):
    """
    Takes a delta dictionary and matches each point on the dictionary to the closest point on the input shape.
    
    delta_dictionary = The delta dictionary you want to match to the given shape.
    target_shape = The shape node you want to match the delta dictionary to.
    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the deltas from the components that influence that point.
            When the source_shape input is a lattice the closest point on surface is actually based on volume.
        closestComponentUV = 
            Matches to the closest compoennt on the other side in UV space.
            The returned dictionary will not UV coordinate information instead of worldspace position information.
            Note: You will probably want to set the symm_coordinate to .5 when using this method.
    
    source_shape = The shape the delta dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentrix delta information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.

    If the matching_method is "closestComponent" or "closestComponentUV" this command will return a delta dictionary and an ii_dict in a list.
    If the matching_method is "closestPointOnSurface" this command will return a delta dictionary and an ibw_dict in a list. 
    """
    if matching_method == 'closestComponent':
        if not ii_dict:
            source_ip_dictionary = convert_weightDelta_dictionary_to_index_position_dictionary(delta_dictionary)
            target_ip_dictionary = convert_shape_to_index_position_dictionary(shape=target_shape, object_space=target_object_space)
            ii_dict = match_points_to_closest_point(source_ip_dictionary, target_ip_dictionary)
        matched_dictionary = {new_index:delta_dictionary[old_index] for new_index, old_index in list(ii_dict.items())}
        return [
         matched_dictionary, ii_dict]
    if matching_method == 'closestComponentUV':
        if not ii_dict:
            source_ip_dictionary = convert_weightDelta_dictionary_to_index_position_dictionary(delta_dictionary)
            source_ip_dictionary = convert_ipDict_positions_to_UV_coordinates(source_ip_dictionary, target_shape)
            target_ip_dictionary = convert_shape_to_index_position_dictionary(shape=target_shape, object_space=target_object_space)
            target_ip_dictionary = convert_ipDict_positions_to_UV_coordinates(target_ip_dictionary, target_shape)
            ii_dict = match_points_to_closest_point(source_ip_dictionary, target_ip_dictionary)
        matched_dictionary = {new_index:delta_dictionary[old_index] for new_index, old_index in list(ii_dict.items())}
        return [
         matched_dictionary, ii_dict]
    if matching_method == 'closestPointOnSurface':
        target_ip_dictionary = convert_shape_to_index_position_dictionary(shape=target_shape, object_space=target_object_space)
        if not ibw_dict:
            orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
            ibw_dict = match_points_to_closest_point_on_surface(orig_shape, target_ip_dictionary)
        matched_dictionary = {}
        matched_dictionary = apply_ibw_dictionary_to_delta_dictionary({}, source_dictionary, ibw_dict)
        return [
         matched_dictionary, ibw_dict]


def match_points_to_closest_point(source_index_position_dictionary, target_index_position_dictionary, max_distance=None):
    """ 
    Takes a index:position dictionary that represents the target shape and finds the closest point in the index:position dictionary that represents the source shape (analogues to the Maya's "closestComponent" matching). 

    source_index_position_dictionary = A dictionary in the form {component index: component position,...} that comes from the source shape. These  are the components the target components will try to match to.
    target_index_position_dictionary = A dictionary in the form {component index: component position,...} that comes from the target shape. These are the components you need to find pairs for.
    
    one_destination = If this option is turned on, each source position will be matched to one and only one target position. This means some points will not have a matching source posiition and will therefore have a value of None in the return index:index dictionary.
    
    Returns an index:index dictionary. This dictionary will have the indices of the target components as keys and indices of the source components as values.
    This output is useful because it lets you convert multiple deformers from one shape to another with minimal calculations.
    """
    items = list(source_index_position_dictionary.items())
    source_comp_index_list = [ x[0] for x in items ]
    source_position_list = [ x[1] for x in items ]
    items = list(target_index_position_dictionary.items())
    target_comp_index_list = [ x[0] for x in items ]
    target_position_list = [ x[1] for x in items ]
    np_imported = True
    try:
        import numpy as np
    except:
        np_imported = False

    index_index_dict = {}
    if max_distance:
        if np_imported:
            source_position_array = np.asarray(source_position_list)
            for target_index, target_position in zip(target_comp_index_list, np.asarray(target_position_list)):
                distance_list = np.sum((source_position_array - target_position) ** 2, axis=1)
                shortest_distance = distance_list.min()
                if shortest_distance < max_distance ** 2:
                    shortest_distance_index = distance_list.argmin()
                    source_comp_index = source_comp_index_list[shortest_distance_index]
                    index_index_dict[target_index] = source_comp_index

        else:
            source_position_array = [ om.MPoint(*pnt) for pnt in source_position_list ]
            target_position_array = [ om.MPoint(*pnt) for pnt in target_position_list ]
            for target_index, target_position in zip(target_comp_index_list, target_position_array):
                distance_list = [ pnt.distanceTo(target_position) for source_position in source_position_array ]
                shortest_distance = min(distance_list)
                if shortest_distance < max_distance:
                    shortest_distance_index = distance_list.index(shortest_distance)
                    source_comp_index = source_comp_index_list[shortest_distance_index]
                    index_index_dict[target_index] = source_comp_index

    elif np_imported:
        source_position_array = np.asarray(source_position_list)
        for target_index, target_position in zip(target_comp_index_list, np.asarray(target_position_list)):
            distance_list = np.sum((source_position_array - target_position) ** 2, axis=1)
            shortest_distance_index = distance_list.argmin()
            source_comp_index = source_comp_index_list[shortest_distance_index]
            index_index_dict[target_index] = source_comp_index

    else:
        source_position_array = [ om.MPoint(*pnt) for pnt in source_position_list ]
        target_position_array = [ om.MPoint(*pnt) for pnt in target_position_list ]
        for target_index, target_position in zip(target_comp_index_list, target_position_array):
            distance_list = [ source_position.distanceTo(target_position) for source_position in source_position_array ]
            shortest_distance_index = distance_list.index(min(distance_list))
            source_comp_index = source_comp_index_list[shortest_distance_index]
            index_index_dict[target_index] = source_comp_index

    return index_index_dict


def match_points_to_closest_point_on_surface(source_shape, target_index_position_dictionary, max_distance=None):
    """
    Matches the points in the target_index_position_dictionary to the closest point on the given source_shape.
    
    source_shape = 
        The shape that you will matching to. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    target_index_position_dictionary =  
        A dictionary of the index and position for each component that represents the shape you want to transfer the weight onto.
        
    Returns an ibw dictionary which is a dictionary with each item being index:[[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
    !!!
    """
    if cmds.nodeType(source_shape) == 'mesh':
        sel = om2.MSelectionList()
        sel.add(source_shape)
        source_shape_dagPath = sel.getDagPath(0)
        source_mFnMesh = om2.MFnMesh(source_shape_dagPath)
        source_position_list = source_mFnMesh.getPoints()

        def get_area(a, b, c):
            l0 = om2.MPoint(a) - om2.MPoint(b)
            l1 = om2.MPoint(b) - om2.MPoint(c)
            l2 = om2.MPoint(c) - om2.MPoint(a)
            A = l0.length()
            B = l1.length()
            C = l2.length()
            p = (A + B + C) / 2
            area = (p * (p - A) * (p - B) * (p - C)) ** 0.5
            return area

        ibw_dict = {}
        if max_distance:
            for index, position in list(target_index_position_dictionary.items()):
                pos = om2.MPoint(position)
                closest_pos, poly_index = source_mFnMesh.getClosestPoint(pos)
                ray_vector = om2.MVector(closest_pos) - om2.MVector(pos)
                if ray_vector.length() < max_distance:
                    hitPoint, hitRayParam, hitFace, hitTriangle, hitBary1, hitBary2 = source_mFnMesh.closestIntersection(om2.MFloatPoint(pos), om2.MFloatVector(ray_vector), om2.MSpace.kWorld, ray_vector.length() * 1.1, True, faceIds=[
                     poly_index])
                    if hitTriangle == -1:
                        closest_pos, normal_vector, poly_index = source_mFnMesh.getClosestPointAndNormal(pos)
                        hitPoint, hitRayParam, hitFace, hitTriangle, hitBary1, hitBary2 = source_mFnMesh.closestIntersection(om2.MFloatPoint(closest_pos - normal_vector), om2.MFloatVector(normal_vector), om2.MSpace.kWorld, normal_vector.length() * 1.1, True, faceIds=[
                         poly_index])
                    triangle_vert_list = source_mFnMesh.getPolygonTriangleVertices(poly_index, hitTriangle)
                    bary_weights = [hitBary1, hitBary2, 1 - hitBary1 - hitBary2]
                    ibw_dict[index] = [triangle_vert_list, bary_weights]

        else:
            for index, position in list(target_index_position_dictionary.items()):
                pos = om2.MPoint(position)
                closest_pos, poly_index = source_mFnMesh.getClosestPoint(pos)
                foundTriangle = False
                for triangleNum in range(len(source_mFnMesh.getPolygonVertices(poly_index)) - 1):
                    tri_vert_ids = source_mFnMesh.getPolygonTriangleVertices(poly_index, triangleNum)
                    a = source_position_list[tri_vert_ids[0]]
                    b = source_position_list[tri_vert_ids[1]]
                    c = source_position_list[tri_vert_ids[2]]
                    full_area = get_area(a, b, c)
                    sum_area = get_area(a, b, closest_pos) + get_area(a, c, closest_pos) + get_area(b, c, closest_pos)
                    if abs(full_area - sum_area) < 0.001:
                        foundTriangle = True
                        v0 = b - a
                        v1 = c - a
                        v2 = closest_pos - a
                        d00 = v0 * v0
                        d01 = v0 * v1
                        d11 = v1 * v1
                        d20 = v2 * v0
                        d21 = v2 * v1
                        denom = d00 * d11 - d01 * d01
                        v = (d11 * d20 - d01 * d21) / denom
                        w = (d00 * d21 - d01 * d20) / denom
                        u = 1.0 - v - w
                        ibw_dict[index] = [
                         tri_vert_ids[:3], [u, v, w]]
                        break

                if not foundTriangle:
                    cmds.error('Closest Point On Surface Matching Failed')

        return ibw_dict
    else:
        if cmds.nodeType(source_shape) == 'nurbsCurve':
            cmds.error('This function does not work with nurbsCurve shapes yet')
            return
        if cmds.nodeType(source_shape) == 'nurbsSurface':
            cmds.error('This function does not work with nurbsSurface shapes yet')
            return
        if cmds.nodeType(source_shape) == 'lattice':
            cmds.error('This function does not work with lattice shapes yet')
            return
        cmds.error(('"{}"" is not a valid shape').format(source_shape))
        return


def convert_wire_to_weights(wire_deformer, shape):
    """ 
    Turns the falloff and weight mask of the given wire deformer on the given shape into a weight dictionary.

    wire_deformer = The wire deformer whose weights you want to get. Example: "wire1" 
    shape = The shape you want to get the weights from.
    
    Returns a weight dictionary.
    """
    if not cmds.objExists(wire_deformer):
        cmds.error(('"{}" does not exist').format(wire_deformer))
    if cmds.nodeType(wire_deformer) != 'wire':
        cmds.error(('{} is not a wire').format(wire_deformer))
    if not cmds.objExists(shape):
        cmds.error(('"{}" does not exist').format(shape))
    shape = cmds.ls(shape, l=True)[0]
    geo_list = cmds.wire(wire_deformer, q=True, g=True)
    geo_list = [ cmds.ls(x, l=True)[0] for x in geo_list ]
    if shape not in geo_list:
        cmds.error(('"{}" is not affected by "{}"').format(shape, blendShape_node))
    rotate_value = cmds.getAttr(wire_deformer + '.rotation')
    cmds.setAttr(wire_deformer + '.rotation', 0)
    start_pos_list = get_position_list(shape, prePose=False)
    deformedWire_index_list = cmds.getAttr(('{}.deformedWire').format(wire_deformer), multiIndices=True)
    deformedWire_attr_list = [ ('{}.deformedWire[{}]').format(wire_deformer, int(x)) for x in deformedWire_index_list ]
    wire_shape_list = []
    for attr in deformedWire_attr_list:
        wire_shape = cmds.connectionInfo(attr, sfd=True)
        if wire_shape != []:
            wire_shape_list.append(wire_shape.split('.')[0])

    for wire_shape in wire_shape_list:
        cmds.move(1, 0, 0, wire_shape, ws=True, r=True)

    end_pos_list = get_position_list(shape, prePose=False)
    for wire_shape in wire_shape_list:
        cmds.move(-1, 0, 0, wire_shape, ws=True, r=True)

    cmds.setAttr(wire_deformer + '.rotation', rotate_value)
    weight_list = [ om2.MPoint(end).distanceTo(om2.MPoint(start)) for end, start in zip(end_pos_list, start_pos_list) ]
    comp_index_list = get_index_list(get_component_list(shape))
    position_list = get_position_list(shape, prePose=True)
    return {index:(pos, weight) for index, pos, weight in zip(comp_index_list, position_list, weight_list)}


def convert_softSelect_to_weights():
    """ 
    Turns the falloff of the softSelection into a weight dictionary.
    
    Returns a list containing a list of weight dictionaries (one per shape) and a list of the corresponding shapes.
    """
    if not cmds.softSelect(q=True, sse=True):
        cmds.warning('SoftSelect is not on. No weights were returned.')
        return {}
    symm = cmds.symmetricModelling(q=True, symmetry=True)
    richSel = om.MRichSelection()
    try:
        om.MGlobal.getRichSelection(richSel)
    except:
        cmds.warning('Could Not Get Softselection')
        return {}

    richSelList = om.MSelectionList()
    richSel.getSelection(richSelList)
    if symm:
        symm_richSelList = om.MSelectionList()
        richSel.getSymmetry(symm_richSelList)
    selCount = richSelList.length()
    if selCount == 0:
        cmds.warning('No valid selection. No weights were returned.')
        return {}
    return_list = [[], []]
    for object_index in range(selCount):
        shapeDag = om.MDagPath()
        shapeComp = om.MObject()
        symm_shapeDag = om.MDagPath()
        symm_shapeComp = om.MObject()
        try:
            richSelList.getDagPath(object_index, shapeDag, shapeComp)
            if symm:
                symm_richSelList.getDagPath(object_index, symm_shapeDag, symm_shapeComp)
        except:
            cmds.error('Error Getting Softselection')

        selected_shape = str(shapeDag.fullPathName())
        pos_list = get_position_list(selected_shape)
        weight_dict = {index:[position, 0.0] for index, position in enumerate(pos_list)}
        if shapeComp.hasFn(om.MFn.kSingleIndexedComponent):
            compFn = om.MFnSingleIndexedComponent(shapeComp)
            try:
                for i in range(compFn.elementCount()):
                    comp_index = compFn.element(i)
                    weight = compFn.weight(i).influence()
                    weight_dict[comp_index] = [pos_list[comp_index], weight]

            except:
                cmds.error('Error Getting Softselection')

            if symm:
                symm_compFn = om.MFnSingleIndexedComponent(symm_shapeComp)
                try:
                    for i in range(symm_compFn.elementCount()):
                        comp_index = symm_compFn.element(i)
                        weight = symm_compFn.weight(i).influence()
                        weight_dict[comp_index] = [pos_list[comp_index], weight]

                except:
                    cmds.error('Error Getting Softselection')

        if shapeComp.hasFn(om.MFn.kDoubleIndexedComponent):
            compFn = om.MFnDoubleIndexedComponent(shapeComp)
            mFn_surface = om.MFnNurbsSurface(shapeDag)
            maxU = mFn_surface.numCVsInU()
            maxV = mFn_surface.numCVsInV()
            U_util = om.MScriptUtil()
            V_util = om.MScriptUtil()
            U_pntr = U_util.asIntPtr()
            V_pntr = V_util.asIntPtr()
            for i in range(compFn.elementCount()):
                compFn.getElement(i, U_pntr, V_pntr)
                U = U_util.getInt(U_pntr)
                V = V_util.getInt(V_pntr)
                comp_index = V + U * maxV
                weight = compFn.weight(i).influence()
                weight_dict[comp_index] = [pos_list[comp_index], weight]

            if symm:
                symm_compFn = om.MFnDoubleIndexedComponent(symm_shapeComp)
                try:
                    for i in range(symm_compFn.elementCount()):
                        symm_compFn.getElement(i, U_pntr, V_pntr)
                        U = U_util.getInt(U_pntr)
                        V = V_util.getInt(V_pntr)
                        comp_index = V + u_U * maxV
                        weight = symm_compFn.weight(i).influence()

                except:
                    cmds.error('Error Getting Softselection')
                    continue

        if shapeComp.hasFn(om.MFn.kTripleIndexedComponent):
            compFn = om.MFnTripleIndexedComponent(shapeComp)
            maxS_util = om.MScriptUtil()
            maxT_util = om.MScriptUtil()
            maxU_util = om.MScriptUtil()
            maxS_pntr = maxS_util.asUintPtr()
            maxT_pntr = maxT_util.asUintPtr()
            maxU_pntr = maxU_util.asUintPtr()
            mFn_lattice = omAnim.MFnLattice(shapeDag)
            mFn_lattice.getDivisions(maxS_pntr, maxT_pntr, maxU_pntr)
            maxS = maxS_util.getUint(maxS_pntr)
            maxT = maxT_util.getUint(maxT_pntr)
            maxU = maxU_util.getUint(maxU_pntr)
            S_util = om.MScriptUtil()
            T_util = om.MScriptUtil()
            U_util = om.MScriptUtil()
            S_pntr = S_util.asIntPtr()
            T_pntr = T_util.asIntPtr()
            U_pntr = U_util.asIntPtr()
            try:
                for i in range(compFn.elementCount()):
                    compFn.getElement(i, S_pntr, T_pntr, U_pntr)
                    S = S_util.getInt(S_pntr)
                    T = T_util.getInt(T_pntr)
                    U = U_util.getInt(U_pntr)
                    comp_index = S + T * maxS + U * maxT * maxS
                    weight = compFn.weight(i).influence()
                    weight_dict[comp_index] = [pos_list[comp_index], weight]

            except:
                cmds.error('Error Getting Softselection')
                continue

            if symm:
                symm_compFn = om.MFnTripleIndexedComponent(symm_shapeComp)
                try:
                    for i in range(symm_compFn.elementCount()):
                        symm_compFn.getElement(i, S_pntr, T_pntr, U_pntr)
                        S = util.getInt(S_pntr)
                        T = util.getInt(T_pntr)
                        U = util.getInt(U_pntr)
                        comp_index = S + T * maxS + U * maxT * maxS
                        weight = compFn.weight(i).influence()
                        weight_dict[comp_index] = [pos_list[comp_index], weight]

                except:
                    cmds.error('Error Getting Softselection')
                    continue

        return_list[0].append(weight_dict)
        return_list[1].append(selected_shape)

    return return_list


def convert_softMod_to_weights(softMod_node, shape):
    """ 
    Turns the falloff and weight mask of a softMod deformer into a weight dictionary.

    softMod_node = The softMod deformer whose weights you want to get. Example: "softMod1" 
    shape = The shape you want to get the weights from.
    
    Returns a weight dictionary
    """
    index_list = get_index_list(get_component_list(shape))
    matrix_input = cmds.connectionInfo(softMod_node + '.matrix', sourceFromDestination=True)
    softModXforms_input = cmds.connectionInfo(softMod_node + '.softModXforms', sourceFromDestination=True)
    weightedMatrix_input = cmds.connectionInfo(softMod_node + '.weightedMatrix', sourceFromDestination=True)
    if not cmds.isConnected(weightedMatrix_input, softMod_node + '.weightedMatrix'):
        weightedMatrix_input = ''
    if matrix_input:
        cmds.disconnectAttr(matrix_input, softMod_node + '.matrix')
    if softModXforms_input:
        cmds.disconnectAttr(softModXforms_input, softMod_node + '.softModXforms')
    if weightedMatrix_input:
        cmds.disconnectAttr(weightedMatrix_input, softMod_node + '.weightedMatrix')
    start_pos_list = get_position_list(shape, prePose=False)
    position_list = start_pos_list[:]
    array_matrix = cmds.getAttr(softMod_node + '.matrix')
    array_matrix[12] += 1.0
    cmds.setAttr(softMod_node + '.matrix', array_matrix, type='matrix')
    cmds.getAttr(softMod_node + '.weightedMatrix')
    array_matrix[12] += 1.0
    cmds.setAttr(softMod_node + '.weightedMatrix', array_matrix, type='matrix')
    end_pos_list = get_position_list(shape, prePose=False)
    array_matrix = cmds.getAttr(softMod_node + '.matrix')
    array_matrix[12] -= 1.0
    cmds.setAttr(softMod_node + '.matrix', array_matrix, type='matrix')
    array_matrix = cmds.getAttr(softMod_node + '.weightedMatrix')
    array_matrix[12] -= 1.0
    cmds.setAttr(softMod_node + '.weightedMatrix', array_matrix, type='matrix')
    if matrix_input:
        cmds.connectAttr(matrix_input, softMod_node + '.matrix')
    if softModXforms_input:
        cmds.connectAttr(softModXforms_input, softMod_node + '.softModXforms')
    if weightedMatrix_input:
        cmds.disconnectAttr(weightedMatrix_input, softMod_node + '.weightedMatrix')
    weight_list = [ om2.MPoint(end).distanceTo(om2.MPoint(start)) for end, start in zip(end_pos_list, start_pos_list) ]
    return {index:(pos, weight) for index, pos, weight in zip(index_list, position_list, weight_list)}


def convert_deltas_to_weights_via_vector(delta_dictionary, translate_vector):
    """ 
    Turns a delta dictionary into a weight dictionary by finding the magnitude of the component of the delta that is aligned with given vector.
    
    delta_dictionary = The delta dictionary you want to convert.
    translate_vector = The vector that will be used to convert the deltas to weights, the magnitude and direction of this vector will affect the results. Example: (0,1,0)
    
    Returns a weight dictionary. 
    """
    items = list(delta_dictionary.items())
    index_list = [ x[0] for x in items ]
    position_list = [ x[1][0] for x in items ]
    deltas = [ x[1][1] for x in items ]
    tVector = om.MVector(*translate_vector)
    weight_list = [ om.MVector(*delta[0:3]) * tVector for delta in deltas ]
    return {index:(position, weight) for index, position, weight in zip(index_list, position_list, weight_list)}


def convert_blendShape_deltas_to_weights_via_matrix(deltas_dictionary, preMMatrix, postMMatrix):
    """ 
    Turns a delta dictionary into a weight dictionary by finding the weight that would get the deformation as close to the given deltas as possible using the given matrix transformation.
    
    delta_dictionary = The delta dictionary you want to convert to a weight dictionary.
    preMMatrix = The worldMatrix that represents the pivot pre-transformation. Example: om2.MMatrix()
    postMMatrix = The worldMatrix that represents the pivot post-transformation. Example: om2.MMatrix()
    
    Returns a weight dictionary.
    """
    items = list(deltas_dictionary.items())
    index_list = [ x[0] for x in items ]
    position_list = [ x[1][0] for x, deltas in items ]
    deltas = [ x[1][1] for x in items ]
    mVector_position_list = [ om2.MVector(*position) for position in position_list ]
    mVector_delta_list = [ om2.MVector(*delta) for delta in deltas ]
    post_position_list = [ position * preMMatrix.inverse() * postMMatrix for position in mVector_position_list ]
    matrix_deltas = [ post - pre for post, pre in zip(post_position_list, mVector_position_list) ]
    weight_list = [ delta * matrix_deltas for delta, matrix_deltas in zip(matrix_deltas, matrix_deltas) ]
    return {index:(position, weight) for index, position, weight in zip(index_list, position_list, weight_list)}


def convert_blendShape_deltas_to_single_axis_rotate_weights(delta_dictionary, rotMMatrix, rotation_angle):
    """ 
    Turns a delta dictionary into a weight dictionary by finding the weight that would get the deformation as close to the given deltas as possible using the given matrix transformation.
    
    delta_dictionary = The delta dictionary you want to convert to a weight dictionary.
    preMMatrix = The worldMatrix that represents the pivot pre-transformation. Example: om2.MMatrix()
    postMMatrix = The worldMatrix that represents the pivot post-transformation. Example: om2.MMatrix()
    
    Returns a weight dictionary.
    """
    items = list(delta_dictionary.items())
    index_list = [ x[0] for x in items ]
    position_list = [ position for x, (position, deltas) in items ]
    deltas = [ deltas for x, (position, deltas) in items ]
    mVector_position_list = [ om2.MVector(*position) for position in position_list ]
    mVector_delta_list = [ om2.MVector(*delta) for delta in deltas ]
    mVector_end_list = [ pos + delta for pos, delta in zip(mVector_position_list, mVector_delta_list) ]
    local_position_list = [ om2.MPoint(pos) * rotMMatrix.inverse() for pos in mVector_position_list ]
    local_end_list = [ om2.MPoint(pos) * rotMMatrix.inverse() for pos in mVector_end_list ]
    local_position_list = [ om2.MVector(0, y, z) for x, y, z, w in local_position_list ]
    local_end_list = [ om2.MVector(0, y, z) for x, y, z, w in local_end_list ]
    cross_product_list = [ start ^ end for start, end in zip(local_position_list, local_end_list) ]
    cross_product_list = [ cross * om2.MVector(1, 0, 0) for cross in cross_product_list ]
    sign_list = []
    for cross in cross_product_list:
        if cross > 0:
            sign_list.append(-1)
        else:
            sign_list.append(1)

    angle_list = [ start.angle(end) * 57.2958 * cross for start, end, cross in zip(local_position_list, local_end_list, sign_list) ]
    weight_list = [ angle / rotation_angle for angle in angle_list ]
    return {index:(position, weight) for index, position, weight in zip(index_list, position_list, weight_list)}


def transfer_blendShapes_via_wrap(source_blendShape_node, destination_shape, falloffMode='volume', connect_targets=True, skip_existing=True, skip_live_targets=True, transfer_only=[], empty_target_threshold=0.05, targets_not_to_skip=[], targets_to_skip=[]):
    """
    Transfers blendShape deltas from one shape to another using a wrap deformer. The script assumes the blendShape node is at the front of the chain.
    
    source_blendShape_node = The blendShape node you want to the transfer the blendShape targets from.
    destination_shape = The shape you want to transfer the blendShape targets to.
    falloffMode = The falloffMode value you want the wrap deformer to use 'volume' or 'surface'.
    connect_targets = Controls whether the weight for the blendShape targets on the source shape will drive the weights for the blendShape targets on the target shape.
    skip_existing = Targets that already exist on the target shapes blendShape node will not be transferred as new duplicate targets.
    skip_live_target = Controls whether targets that are connected to another existing shape are transferred.
    transfer_only = If this list is not [] then only the given targets will be transferred. Otherwisde the following parameters will determine which target is transferred.
    
    empty_target_threshold = Any transferred blendShapes whoses deltas have a magnitude less than this number will not be transferred.
    targets_not_to_skip = These targets will NOT be skipped regardless of the empty threshold (this list take precedence over the targets_to_skip list).
    targets_to_skip = These targets will be skipped regardless of the empty threshold.
    
    return a the blendShape node for the target shape.
    """
    if not cmds.objExists(source_blendShape_node):
        cmds.error(('source_blendShape_node:{} does not exist').format(source_blendShape_node))
    if cmds.nodeType(source_blendShape_node) != 'blendShape':
        cmds.error(('{} is not a blendShape node').format(source_blendShape_node))
    geo_list = cmds.blendShape(source_blendShape_node, q=True, g=True)
    if geo_list == []:
        cmds.error(('source_blendShape_node:"{}" doest not affect any geometry').format(source_blendShape_node))
    else:
        source_shape = geo_list[0]
    if falloffMode not in ('volume', 'surface'):
        cmds.error(('"{}" is not a valid falloffMode value ["volume","surface"]').format(falloffMode))
    destination_blendShape_node = ''
    set_list = cmds.listSets(object=destination_shape)
    if set_list:
        for set in set_list:
            if cmds.objExists(set):
                if cmds.attributeQuery('usedBy', node=set, exists=True):
                    used_by_list = cmds.listConnections(set + '.usedBy[0]')
                    if used_by_list:
                        if cmds.nodeType(used_by_list[0]) == 'blendShape':
                            destination_blendShape_node = used_by_list[0]

    if destination_blendShape_node == '':
        cmds.select(cl=True)
        destination_blendShape_node = cmds.blendShape(destination_shape, foc=True)[0]
    target_index_list = cmds.aliasAttr(source_blendShape_node, q=True)
    if target_index_list == None:
        return destination_blendShape_node
    else:
        target_list = target_index_list[0::2]
        index_list = target_index_list[1::2]
        index_list = [ int(index.split('[')[1].split(']')[0]) for index in index_list ]
        target_index_dict = dict(list(zip(target_list, index_list)))
        target_source_dict = {}
        for target in target_list:
            dest_attribute = source_blendShape_node + '.' + target
            source = cmds.connectionInfo(source_blendShape_node + '.' + target, sourceFromDestination=True)
            weight = cmds.getAttr(source_blendShape_node + '.' + target)
            target_source_dict[dest_attribute] = [source, weight]
            if source != '':
                cmds.disconnectAttr(source, dest_attribute)
            cmds.blendShape(source_blendShape_node, e=True, w=(target_index_dict[target], 0))

        if transfer_only:
            target_list = [ target for target in target_list if target in transfer_only ]
        else:
            if targets_to_skip != []:
                for target in target_list[:]:
                    if target in targets_to_skip and target not in targets_not_to_skip:
                        target_list.remove(target)

            if skip_live_targets:
                for target, index in list(target_index_dict.items()):
                    if cmds.listConnections(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[6000].inputGeomTarget').format(source_blendShape_node, index)):
                        if target in target_list:
                            target_list.remove(target)

            if skip_existing:
                destination_target_index_list = cmds.aliasAttr(destination_blendShape_node, q=True)
                if destination_target_index_list:
                    for existing_target in destination_target_index_list[0::2]:
                        if existing_target in target_list[:]:
                            target_list.remove(existing_target)

            wrap_node = cmds.deformer(destination_shape, type='wrap')[0]
            cmds.setAttr(wrap_node + '.autoWeightThreshold', 1)
            cmds.setAttr(wrap_node + '.maxDistance', 1)
            cmds.setAttr(wrap_node + '.falloffMode', {'volume': 0, 'surface': 1}[falloffMode])
            cmds.connectAttr(destination_shape + '.worldMatrix[0]', wrap_node + '.geomMatrix')
            source_base_shape = cmds.duplicate(source_shape, name=source_shape)[0]
            if cmds.nodeType(source_shape) == 'mesh':
                cmds.connectAttr(source_shape + '.worldMesh', wrap_node + '.driverPoints[0]')
                cmds.connectAttr(source_base_shape + '.worldMesh', wrap_node + '.basePoints[0]')
                cmds.setAttr(wrap_node + '.inflType[0]', 2)
                cmds.setAttr(wrap_node + '.dropoff[0]', 4)
            if cmds.nodeType(source_shape) == 'nurbsCurve' or cmds.nodeType(source_shape) == 'nurbsSurface':
                cmds.connectAttr(source_shape + '.ws', wrap_node + '.driverPoints[0]')
                cmds.connectAttr(source_base_shape + '.ws', wrap_node + '.basePoints[0]')
                cmds.setAttr(wrap_node + '.nurbsSamples[0]', 10)
            source_target_mesh_dict = {}
            for target in target_list[:]:
                index = target_index_dict[target]
                cmds.blendShape(source_blendShape_node, e=True, w=(index, 1))
                new_mesh = cmds.duplicate(destination_shape, n=target)[0]
                cmds.blendShape(source_blendShape_node, e=True, w=(index, 0))
                source_target_mesh_dict[target] = new_mesh

            cmds.delete('|' + source_base_shape)
            cmds.delete(wrap_node)
            if empty_target_threshold is not None:
                starting_position_list = get_position_list(destination_shape)
                for target in target_list[:]:
                    new_mesh = source_target_mesh_dict[target]
                    new_position_list = get_position_list(cmds.listRelatives(new_mesh, s=True, f=True)[0], prePose=False)
                    delta_magnitude_list = [ (om2.MVector(start_position) - om2.MVector(new_position)).length() for start_position, new_position in zip(starting_position_list, new_position_list) ]
                    if max(delta_magnitude_list) < empty_target_threshold:
                        if target not in targets_not_to_skip:
                            cmds.delete(new_mesh)
                            target_list.remove(target)

            index_list = cmds.aliasAttr(destination_blendShape_node, q=True)
            if not index_list:
                max_index = 0
            else:
                index_list = [ int(x.split('[')[(-1)][:-1]) for x in index_list[1::2] ]
                max_index = max(index_list) + 1
            target_attr_list = [ [destination_shape, int(i) + int(max_index), source_target_mesh_dict[target], 1] for i, target in enumerate(target_list) ]
            cmds.blendShape(destination_blendShape_node, e=True, t=target_attr_list)
            alias_list = cmds.aliasAttr(destination_blendShape_node, q=True)
            if not alias_list:
                for blendShape_attribute, (source_attribute, weight) in list(target_source_dict.items()):
                    if source_attribute != '':
                        cmds.connectAttr(source_attribute, blendShape_attribute, f=True)
                    else:
                        cmds.setAttr(blendShape_attribute, weight)

                cmds.warning('No targets were transferred. If this was not the expected result try saving and re-opening the file to resolve the issue')
                return destination_blendShape_node
            destination_target_list = alias_list[0::2]
            destination_index_list = [ int(x.split('[')[(-1)][:-1]) for x in alias_list[1::2] ]
            index_target_dict = dict(list(zip(destination_index_list, destination_target_list)))
            old_target_new_target_dict = {}
            for i, target in enumerate(target_list):
                current_target_name = index_target_dict[(max_index + i)]
                if current_target_name == target:
                    old_target_new_target_dict[target] = target
                    continue
                if not cmds.attributeQuery(target, node=destination_blendShape_node, exists=True):
                    cmds.aliasAttr(target, ('{}.w[{}]').format(destination_blendShape_node, max_index + i))
                    old_target_new_target_dict[target] = target
                    continue
                else:
                    ending_enumeration = re.findall('\\d+$', target)
                    if ending_enumeration:
                        numberless_target = target_name[:-len(ending_enumeration[0])]
                        ending_enumeration = int(ending_enumeration[0])
                    else:
                        numberless_target = target
                        ending_enumeration = 1
                    while cmds.attributeQuery(('{}{}').format(numberless_target, ending_enumeration), node=destination_blendShape_node, exists=True):
                        ending_enumeration += 1

                    cmds.aliasAttr(numberless_target + str(ending_enumeration), ('{}.w[{}]').format(destination_blendShape_node, max_index + i))
                    old_target_new_target_dict[target] = numberless_target + str(ending_enumeration)

            for blendShape_attribute, (source_attribute, weight) in list(target_source_dict.items()):
                if source_attribute != '':
                    cmds.connectAttr(source_attribute, blendShape_attribute, f=True)
                else:
                    cmds.setAttr(blendShape_attribute, weight)

        if connect_targets:
            for old_target, new_target in list(old_target_new_target_dict.items()):
                try:
                    cmds.connectAttr(('{}.{}').format(source_blendShape_node, old_target), ('{}.{}').format(destination_blendShape_node, new_target), f=True)
                except:
                    cmds.warning(('hey you found an issue with this target {}:{}').format(old_target, new_target))

        cmds.delete(*[ source_target_mesh_dict[target] for target in target_list ])
        return destination_blendShape_node


def get_blendShape_target_deltas(blendShape_node, blendShape_target, position_list=None, inBetween_weight=1, shape=None, scarce=False):
    """
    Generates a delta dictionary from the given target on the given blendShape node.
    
    blendShape_node = The blendShape node the blendShape_target is on.
    blendShape_target = The blendShape target you want to get the deltas from
    positition_list: The list of positions for the given shape (if you already have them it is faster to give them as inputs than to get them again)
    inBetween_weight = The inbetween weight you want to set the deltas at.
    shape = The shape you want to get the deltas from.(this is only required if you have two shapes deformed by the same blendShape node)

    Returns a delta dictionary.
    """
    target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    geo_list = cmds.blendShape(blendShape_node, q=True, g=True)
    geo_list = [ cmds.ls(x, l=True)[0] for x in geo_list ]
    if not shape:
        if not geo_list:
            cmds.error(('"{}" does not affect any geometry').format(shape))
        else:
            shape = geo_list[0]
    else:
        shape = cmds.ls(shape, l=True)[0]
        if shape not in geo_list:
            cmds.error(('"{}" does not affect {}').format(blendShape_node, shape))
        member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(blendShape_node, shape)
        mFnDependencyNode = om.MFnDependencyNode(mObject_deformer)
        item_index = int(5000 + 1000 * inBetween_weight)
        if cmds.connectionInfo(('{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(blendShape_node, member_index, target_index, item_index), sfd=True):
            cmds.error('Deltas can not be queried for targets that use a "live" mesh')
        if not position_list:
            full_position_list = get_position_list(shape)
        else:
            full_position_list = position_list
        full_index_list = list(range(len(full_position_list)))
        empty_delta_dict = {index:(position, (0, 0, 0)) for index, position in zip(full_index_list, full_position_list)}
        delta_component_ids = cmds.getAttr(('{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[{}].inputComponentsTarget').format(blendShape_node, member_index, target_index, item_index))
        if not delta_component_ids:
            return empty_delta_dict
        delta_components = cmds.ls([ shape + '.' + id for id in delta_component_ids ], fl=True)
        delta_components = [ shape + '.' + component.split('.')[(-1)] for component in delta_components ]
        delta_indices = get_index_list(delta_components)
        deltas = cmds.getAttr(('{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[{}].inputPointsTarget').format(blendShape_node, member_index, target_index, item_index))
        if not deltas:
            return {index:(position, (0, 0, 0)) for index, position in enumerate(positfull_position_listion_list)}
        delta_indices = [ x for x in delta_indices if x < len(full_position_list) ]
        if scarce:
            return {index:(full_position_list[index], delta[0:3]) for index, delta in zip(delta_indices, deltas)}
    empty_delta_dict = {index:(position, (0, 0, 0)) for index, position in enumerate(full_position_list)}
    delta_dict = {index:(full_position_list[index], delta[0:3]) for index, delta in zip(delta_indices, deltas)}
    empty_delta_dict.update(delta_dict)
    return empty_delta_dict


def set_blendShape_target_deltas(blendShape_node, blendShape_target, delta_dictionary, inBetween_weight=1, shape=None, clean=False):
    """
    Generates a delta dictionary from the given target on the given blendShape node.
    
    blendShape_node = The blendShape node the blendShape_target is on.
    blendShape_target = The blendShape target you want to set the deltas for.
    inBetween_weight = If you are setting deltas for an inbetween on a target set the weight for the inBetween with this input.
    shape = The shape you want to set the deltas for.(this is only required if you have two shapes deformed by the same blendShape node)
    clean = This will filter out any deltas of 0 length
    """
    target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    geo_list = cmds.blendShape(blendShape_node, q=True, g=True)
    geo_list = [ cmds.ls(x, l=True)[0] for x in geo_list ]
    if not shape:
        if not geo_list:
            cmds.error(('"{}" does not affect any geometry').format(shape))
        else:
            shape = geo_list[0]
    else:
        shape = cmds.ls(shape, l=True)[0]
        if shape not in geo_list:
            cmds.error(('"{}" does not affect {}').format(blendShape_node, shape))
        member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(blendShape_node, shape)
        mFnDependencyNode = om.MFnDependencyNode(mObject_deformer)
        item_index = int(5000 + 1000 * inBetween_weight)
        if cmds.connectionInfo(('{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(blendShape_node, member_index, target_index, item_index), sfd=True):
            cmds.error('Deltas can not be queried for targets that use a "live" mesh')
        items = list(delta_dictionary.items())
        set_delta_component_ids = [ x[0] for x in items ]
        set_deltas = [ x[1][1] for x in items ]
        if cmds.nodeType(shape) == 'mesh':
            set_delta_component_ids = [ ('vtx[{}]').format(index) for index in set_delta_component_ids ]
        elif cmds.nodeType(shape) == 'nurbsCurve':
            set_delta_component_ids = [ ('cv[{}]').format(index) for index in set_delta_component_ids ]
        elif cmds.nodeType(shape) == 'nurbsSurface':
            u_div = cmds.getAttr(shape + '.spansU')
            v_div = cmds.getAttr(shape + '.spansV')
            if cmds.getAttr(shape + '.formU') == 0:
                u_div += cmds.getAttr(shape + '.degreeU')
            if cmds.getAttr(shape + '.formV') == 0:
                v_div += cmds.getAttr(shape + '.degreeV')
            set_delta_component_ids = [ ('cv[{}][{}]').format(int(index / v_div), index % v_div) for index in set_delta_component_ids ]
        elif cmds.nodeType(shape) == 'lattice':
            s_div, t_div, u_div = cmds.lattice(shape, q=True, dv=True)
            s_index_list = [ index % s_div for index in set_delta_component_ids ]
            t_index_list = [ int(index / s_div) % t_div for index in set_delta_component_ids ]
            u_index_list = [ int(index / (s_div * t_div)) % u_div for index in set_delta_component_ids ]
            set_delta_component_ids = [ ('pt[{}][{}][{}]').format(s_index, t_index, u_index) for s_index, t_index, u_index in zip(s_index_list, t_index_list, u_index_list) ]
        else:
            cmds.error(('"{}" is not a valid shape').format(shape))
        if clean:
            clean_deltas = []
            clean_components = []
            for delta, component in zip(set_deltas, set_delta_component_ids):
                if sum([ abs(x) for x in delta ]) > 0.001:
                    clean_components.append(component)
                    clean_deltas.append(delta)

            set_delta_component_ids = clean_components
            set_deltas = clean_deltas
        if not set_deltas:
            component_prefix = 'vtx'
            cmds.setAttr(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputComponentsTarget').format(blendShape_node, target_index, item_index), 1, type='componentList', *[component_prefix + '[0]'])
            cmds.setAttr(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputPointsTarget').format(blendShape_node, target_index, item_index), 1, type='pointArray', *[(0.0, 0.0, 0.0, 1.0)])
            return
    cmds.setAttr(('{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[{}].inputComponentsTarget').format(blendShape_node, member_index, target_index, item_index), len(set_delta_component_ids), type='componentList', *set_delta_component_ids)
    cmds.setAttr(('{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[{}].inputPointsTarget').format(blendShape_node, member_index, target_index, item_index), len(set_deltas), type='pointArray', *set_deltas)


def symmetrisize_deltas(delta_dictionary, symm_coordinate=0, axis='x', uv_axis='u', direction='+ to -', matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None):
    """ 
    Makes a delta dictionary symmetrical. 

    delta_dictionary = The delta dictionary you want to symmetrisize
    symm_coordinate = The coordinate at which the deltas will be symmetrisized
    axis = The axis you want to symmetrisize the deltas over ("x" "y" or "z"). 
    uv_axis = The axis in UV space you want to to symmetrisize the points over.
    direction: The direction in which you symmetrisize the deltas, can be "+ to -" or "- to +"
    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the deltas from the components that influence that point.
            When the source_shape input is a lattice the closest point on surface is actually based on volume.
        closestComponentUV = 
            Matches to the closest compoennt on the other side in UV space.
            The returned dictionary will not UV coordinate information instead of worldspace position information.
            Note: You will probably want to set the symm_coordinate to .5 when using this method.
    
    source_shape = The shape the delta dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentrix delta information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.
            
    If the matching method is "closestComponent" or "closestComponentUV" it returns delta dictionary and an ii_dict so that the operation can be performed faster next time [delta_dictionary,ii_dict]
    If the matching_method is "closestPointOnSurface" it returns a delta dictionary and an ibw dict so that the operation can be performed faster next time [delta_dictionary,dict].
    """
    if matching_method == 'closestComponent':
        if axis not in ('x', 'y', 'z'):
            cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
        axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
        if direction == '+ to -':
            non_symm_delta_dict = {key:value for key, value in list(delta_dictionary.items()) if value[0][axis_index] >= symm_coordinate - 0.001}
            non_symm_ip_dict = {index:position for index, (position, delta) in list(non_symm_delta_dict.items())}
            symm_ip_dict = {index:position for index, (position, delta) in list(delta_dictionary.items()) if position[axis_index] < symm_coordinate - 0.001}
        else:
            if direction == '- to +':
                non_symm_delta_dict = {key:value for key, value in list(delta_dictionary.items()) if value[0][axis_index] <= symm_coordinate + 0.001}
                non_symm_ip_dict = {index:position for index, (position, delta) in list(non_symm_delta_dict.items())}
                symm_ip_dict = {index:position for index, (position, delta) in list(delta_dictionary.items()) if position[axis_index] > symm_coordinate + 0.001}
            else:
                cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                return
            if axis == 'x':
                symmed_deltas = {comp_index:(-a, b, c) for comp_index, (position, (a, b, c)) in list(non_symm_delta_dict.items())}
                symm_ip_dict = {comp_index:(2 * symm_coordinate - x, y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
                seam_dict = {key:(position, (0, b, c)) for key, (position, (a, b, c)) in list(non_symm_delta_dict.items()) if position[axis_index] > symm_coordinate - 0.001 and position[axis_index] < symm_coordinate + 0.001}
            elif axis == 'y':
                symmed_deltas = {comp_index:(a, -b, c) for comp_index, (position, (a, b, c)) in list(non_symm_delta_dict.items())}
                symm_ip_dict = {comp_index:(x, 2 * symm_coordinate - y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
                seam_dict = {key:(position, (a, 0, c)) for key, (position, (a, b, c)) in list(non_symm_delta_dict.items()) if position[axis_index] > symm_coordinate - 0.001 and position[axis_index] < symm_coordinate + 0.001}
            elif axis == 'z':
                symmed_deltas = {comp_index:(a, b, -c) for comp_index, (position, (a, b, c)) in list(non_symm_delta_dict.items())}
                symm_ip_dict = {comp_index:(x, y, 2 * symm_coordinate - z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
                seam_dict = {key:(position, (a, b, 0)) for key, (position, (a, b, c)) in list(non_symm_delta_dict.items()) if position[axis_index] > symm_coordinate - 0.001 and position[axis_index] < symm_coordinate + 0.001}
            non_symm_delta_dict.update(seam_dict)
            if not ii_dict:
                ii_dict = match_points_to_closest_point(non_symm_ip_dict, symm_ip_dict)
            for new, old in list(ii_dict.items()):
                non_symm_delta_dict[new] = [
                 delta_dictionary[new][0], symmed_deltas[old]]

        return [non_symm_delta_dict, ii_dict]
    if matching_method == 'closestComponentUV':
        if not ii_dict:
            delta_dictionary = convert_weightDelta_positions_to_UV_coordinates(delta_dictionary, source_shape)
        if axis not in ('x', 'y', 'z'):
            cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
        axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
        if uv_axis in ('u', 'v'):
            UV_index = {'u': 0, 'v': 1}[uv_axis]
        else:
            cmds.error(('"{}" is not a valid UV axis ("u" or "v")').format(uv_axis))
        if direction == '+ to -':
            non_symm_delta_dict = {key:value for key, value in list(delta_dictionary.items()) if value[0][UV_index] >= symm_coordinate - 0.001}
            non_symm_ip_dict = {index:position for index, (position, delta) in list(non_symm_delta_dict.items())}
            symm_ip_dict = {index:position for index, (position, delta) in list(delta_dictionary.items()) if position[UV_index] < symm_coordinate - 0.001}
        elif direction == '- to +':
            non_symm_delta_dict = {key:value for key, value in list(delta_dictionary.items()) if value[0][UV_index] <= symm_coordinate + 0.001}
            non_symm_ip_dict = {index:position for index, (position, delta) in list(non_symm_delta_dict.items())}
            symm_ip_dict = {index:position for index, (position, delta) in list(delta_dictionary.items()) if position[UV_index] > symm_coordinate + 0.001}
        else:
            cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
            return
        if uv_axis == 'u':
            symm_ip_dict = {comp_index:(2 * symm_coordinate - x, y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
        else:
            if uv_axis == 'v':
                symm_ip_dict = {comp_index:(x, 2 * symm_coordinate - y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
            if axis == 'x':
                symmed_deltas = {comp_index:(-a, b, c) for comp_index, (position, (a, b, c)) in list(non_symm_delta_dict.items())}
                seam_dict = {key:(position, (0, b, c)) for key, (position, (a, b, c)) in list(non_symm_delta_dict.items()) if position[UV_index] > symm_coordinate - 0.001 and position[UV_index] < symm_coordinate + 0.001}
            elif axis == 'y':
                symmed_deltas = {comp_index:(a, -b, c) for comp_index, (position, (a, b, c)) in list(non_symm_delta_dict.items())}
                seam_dict = {key:(position, (a, 0, c)) for key, (position, (a, b, c)) in list(non_symm_delta_dict.items()) if position[UV_index] > symm_coordinate - 0.001 and position[UV_index] < symm_coordinate + 0.001}
            elif axis == 'z':
                symmed_deltas = {comp_index:(a, b, -c) for comp_index, (position, (a, b, c)) in list(non_symm_delta_dict.items())}
                seam_dict = {key:(position, (a, b, 0)) for key, (position, (a, b, c)) in list(non_symm_delta_dict.items()) if position[UV_index] > symm_coordinate - 0.001 and position[UV_index] < symm_coordinate + 0.001}
            non_symm_delta_dict.update(seam_dict)
            if not ii_dict:
                ii_dict = match_points_to_closest_point(symm_ip_dict, non_symm_ip_dict)
                for new, old in list(ii_dict.items()):
                    non_symm_delta_dict[new] = [
                     delta_dictionary[new][0], symmed_deltas[old]]

                return [
                 delta_dictionary, ii_dict]
    if matching_method == 'closestPointOnSurface':
        axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
        if not ibw_dict:
            if direction == '+ to -':
                non_symm_delta_dict = {key:value for key, value in list(delta_dictionary.items()) if value[0][axis_index] >= symm_coordinate - 0.001}
                symm_ip_dict = {index:position for index, (position, delta) in list(delta_dictionary.items()) if position[axis_index] < symm_coordinate - 0.001}
            elif direction == '- to +':
                non_symm_delta_dict = {key:value for key, value in list(delta_dictionary.items()) if value[0][axis_index] <= symm_coordinate + 0.001}
                symm_ip_dict = {index:position for index, (position, delta) in list(delta_dictionary.items()) if position[axis_index] > symm_coordinate + 0.001}
            else:
                cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                return
            if axis == 'x':
                symmed_deltas = {comp_index:(-a, b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
                symm_ip_dict = {comp_index:(2 * symm_coordinate - x, y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
                seam_dict = {key:(position, (0, b, c)) for key, (position, (a, b, c)) in list(non_symm_delta_dict.items()) if position[axis_index] > symm_coordinate - 0.001 and position[axis_index] < symm_coordinate + 0.001}
            elif axis == 'y':
                symmed_deltas = {comp_index:(a, -b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
                symm_ip_dict = {comp_index:(x, 2 * symm_coordinate - y, z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
                seam_dict = {key:(position, (a, 0, c)) for key, (position, (a, b, c)) in list(non_symm_delta_dict.items()) if position[axis_index] > symm_coordinate - 0.001 and position[axis_index] < symm_coordinate + 0.001}
            elif axis == 'z':
                symmed_deltas = {comp_index:(a, b, -c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
                symm_ip_dict = {comp_index:(x, y, 2 * symm_coordinate - z) for comp_index, (x, y, z) in list(symm_ip_dict.items())}
                seam_dict = {key:(position, (a, b, 0)) for key, (position, (a, b, c)) in list(non_symm_delta_dict.items()) if position[axis_index] > symm_coordinate - 0.001 and position[axis_index] < symm_coordinate + 0.001}
            non_symm_delta_dict.update(seam_dict)
            orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
            ibw_dict = match_points_to_closest_point_on_surface(orig_shape, symm_ip_dict)
            non_symm_delta_dict = apply_ibw_dictionary_to_delta_dictionary(non_symm_delta_dict, symmed_deltas, ibw_dict)
            return [
             non_symm_delta_dict, ibw_dict]
        if axis == 'x':
            symmed_deltas = {comp_index:(-a, b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
            seam_dict = {key:(position, (0, b, c)) for key, (position, (a, b, c)) in list(delta_dictionary.items()) if position[axis_index] > symm_coordinate - 0.001 and position[axis_index] < symm_coordinate + 0.001}
        elif axis == 'y':
            symmed_deltas = {comp_index:(a, -b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
            seam_dict = {key:(position, (a, 0, c)) for key, (position, (a, b, c)) in list(delta_dictionary.items()) if position[axis_index] > symm_coordinate - 0.001 and position[axis_index] < symm_coordinate + 0.001}
        elif axis == 'z':
            symmed_deltas = {comp_index:(a, b, -c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
            seam_dict = {key:(position, (a, b, 0)) for key, (position, (a, b, c)) in list(delta_dictionary.items()) if position[axis_index] > symm_coordinate - 0.001 and position[axis_index] < symm_coordinate + 0.001}
        delta_dictionary.update(seam_dict)
        delta_dictionary = apply_ibw_dictionary_to_delta_dictionary(delta_dictionary, symmed_deltas, ibw_dict)
        return [
         delta_dictionary, ibw_dict]
    else:
        cmds.error(('"{}" is not a valid matching method ("closestComponent","closestComponentUV","closestPointOnSurface")').format(matching_method))


def symmetrisize_deltas_with_plane(delta_dictionary, plane_position, plane_normal, direction='+ to -', matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None, max_distance=0.01):
    """
    Symmetrisize a delta dictionary over a plane. (faster than using a nurbsSurface)
    
    delta_dictionary = The delta dictionary you want to symmetrisize.
    plane_position = The position of the plane.
    plane_normal = The normal of the plane.
    direction = The direction in which the delta dictionary is mirrored.
    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the weights from the components that influence that point.
            When the source_shape input is a lattice the closest point on surface is actually based on volume.
        
    source_shape = The shape the delta dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentrix weight information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.
        
    max_distance = When this value is not None any components whose matching component is farther away than this distance will have their deltas remain unchanged.
        
    If the matching method is "closestComponent" or "closestComponentUV" it returns delta dictionary and an ii_dict so that the operation can be performed faster next time [delta_dictionary,ii_dict]
    If the matching_method is "closestPointOnSurface" it returns a delta dictionary and an ibw dict so that the operation can be performed faster next time [delta_dictionary,dict].
    """
    planePosition = om2.MVector(*plane_position)
    planeNormal = om2.MVector(*plane_normal)
    planeNormal.normalize()
    mPlane = om2.MPlane()
    mPlane.setPlane(planeNormal, 0)
    offset_distance = mPlane.distanceToPoint(planePosition, True)
    mPlane.setPlane(planeNormal, -offset_distance)
    if matching_method == 'closestComponent':
        if not ii_dict:
            non_symm_ip_dict = {}
            symm_ip_dict = {}
            symmed_deltas = {}
            seam_dict = {}
            if direction == '+ to -':
                value1, value2 = (0.001, -0.001)
            else:
                if direction == '- to +':
                    value1, value2 = (-0.001, 0.001)
                else:
                    cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                for index, (position, delta) in list(delta_dictionary.items()):
                    distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                    if distance_to_plane <= value1:
                        non_symm_ip_dict[index] = position
                        mVector_delta = om2.MVector(*delta)
                        parallel_vector = planeNormal * mVector_delta * planeNormal
                        perpendicular_vector = mVector_delta - parallel_vector
                        new_delta = perpendicular_vector - parallel_vector
                        symmed_deltas[index] = tuple(new_delta)[0:3]
                    elif distance_to_plane >= value2:
                        symm_ip_dict[index] = tuple(om2.MVector(position) - 2.0 * distance_to_plane * planeNormal)
                    else:
                        mVector_delta = om2.MVector(*delta)
                        parallel_vector = planeNormal * mVector_delta * planeNormal
                        perpendicular_vector = mVector_delta - parallel_vector
                        seam_dict[index] = [position, tuple(perpendicular_vector)[0:3]]

            delta_dictionary.update(seam_dict)
            ii_dict = match_points_to_closest_point(non_symm_ip_dict, symm_ip_dict, max_distance=max_distance)
        else:
            symmed_deltas = {}
            seam_dict = {}
            if direction == '+ to -':
                value1, value2 = (0.001, -0.001)
            else:
                if direction == '- to +':
                    value1, value2 = (-0.001, 0.001)
                else:
                    cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                for index, (position, delta) in list(delta_dictionary.items()):
                    distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                    if distance_to_plane <= value1:
                        mVector_delta = om2.MVector(*delta)
                        parallel_vector = planeNormal * mVector_delta * planeNormal
                        perpendicular_vector = mVector_delta - parallel_vector
                        new_delta = perpendicular_vector - parallel_vector
                        symmed_deltas[index] = tuple(new_delta)[0:3]
                    else:
                        mVector_delta = om2.MVector(*delta)
                        parallel_vector = planeNormal * mVector_delta * planeNormal
                        perpendicular_vector = mVector_delta - parallel_vector
                        seam_dict[index] = [
                         position, tuple(perpendicular_vector)[0:3]]

                delta_dictionary.update(seam_dict)
            symmed_deltas_dict = delta_dictionary.copy()
            for new, old in list(ii_dict.items()):
                symmed_deltas_dict[new] = [delta_dictionary[new][0], symmed_deltas[old]]

        return [symmed_deltas_dict, ii_dict]
    if matching_method == 'closestPointOnSurface':
        if not ibw_dict:
            non_symm_ip_dict = {}
            symm_ip_dict = {}
            symmed_deltas = {}
            seam_dict = {}
            if direction == '+ to -':
                value1, value2 = (0.001, -0.001)
            else:
                if direction == '- to +':
                    value1, value2 = (-0.001, 0.001)
                else:
                    cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                for index, (position, delta) in list(delta_dictionary.items()):
                    distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                    if distance_to_plane <= value1:
                        non_symm_ip_dict[index] = position
                        mVector_delta = om2.MVector(*delta)
                        parallel_vector = planeNormal * mVector_delta * planeNormal
                        perpendicular_vector = mVector_delta - parallel_vector
                        new_delta = perpendicular_vector - parallel_vector
                        symmed_deltas[index] = tuple(new_delta)[0:3]
                    elif distance_to_plane >= value2:
                        symm_ip_dict[index] = om2.MVector(position) - 2.0 * distance_to_plane * planeNormal
                        symmed_deltas[index] = delta
                    else:
                        mVector_delta = om2.MVector(*delta)
                        parallel_vector = planeNormal * mVector_delta * planeNormal
                        perpendicular_vector = mVector_delta - parallel_vector
                        seam_dict[index] = [position, tuple(perpendicular_vector)[0:3]]
                        symmed_deltas[index] = tuple(perpendicular_vector)[0:3]

            delta_dictionary.update(seam_dict)
            orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
            ibw_dict = match_points_to_closest_point_on_surface(orig_shape, symm_ip_dict)
        else:
            symmed_deltas = {}
            seam_dict = {}
            if direction == '+ to -':
                value1, value2 = (0.001, -0.001)
            else:
                if direction == '- to +':
                    value1, value2 = (-0.001, 0.001)
                else:
                    cmds.error(('"{}" is not a valid direction ("+ to -" or "- to +")').format(direction))
                for index, (position, delta) in list(delta_dictionary.items()):
                    distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                    if distance_to_plane <= value1:
                        mVector_delta = om2.MVector(*delta)
                        parallel_vector = planeNormal * mVector_delta * planeNormal
                        perpendicular_vector = mVector_delta - parallel_vector
                        new_delta = perpendicular_vector - parallel_vector
                        symmed_deltas[index] = tuple(new_delta)[0:3]
                        symmed_deltas[index] = delta
                    else:
                        mVector_delta = om2.MVector(*delta)
                        parallel_vector = planeNormal * mVector_delta * planeNormal
                        perpendicular_vector = mVector_delta - parallel_vector
                        seam_dict[index] = [position, tuple(perpendicular_vector)[0:3]]
                        symmed_deltas[index] = tuple(perpendicular_vector)[0:3]

        delta_dictionary.update(seam_dict)
        symmed_deltas_dict = delta_dictionary.copy()
        symmed_deltas_dict = apply_ibw_dictionary_to_delta_dictionary(symmed_deltas_dict, symmed_deltas, ibw_dict)
        return [
         symmed_deltas_dict, ibw_dict]


def flip_deltas(delta_dictionary, flip_coordinate=0, axis='x', uv_axis='u', matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None):
    """ 
    Flips the given delta dictionary over the given axis at the given flip coordinate. 

    delta_dictionary = The delta dictionary you want to flip.
    flip_coordinate: The coordinate you want to flip the delta dictionary at.
    axis: The axis you want to flip the deformations over ("x" "y" or "z"). 
    uv_axis = The axis in UV space you want to to flip the deltas over.

    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the deltas from the components that influence that point.
            When the source_shape input is a lattice the closest point on surface is actually based on volume.
        closestComponentUV = 
            Matches to the closest component on the other side in UV space.
            The returned dictionary will not UV coordinate information instead of worldspace position information.
            Note: You will probably want to set the flip_coordinate to .5 when using this method.

    source_shape = The shape the delta dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentrix delta information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.
            
    If the matching method is "closestComponent" or "closestComponentUV" it returns delta dictionary and an ii_dict so that the operation can be performed faster next time [delta_dictionary,ii_dict]
    If the matching_method is "closestPointOnSurface" it returns a delta dictionary and an ibw dict so that the operation can be performed faster next time [delta_dictionary,dict].
    """
    if matching_method == 'closestComponent':
        original_ip_dict = {index:position for index, (position, delta) in list(delta_dictionary.items())}
        if axis == 'x':
            flipped_deltas = {comp_index:(-a, b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
            flipped_ip_dict = {comp_index:(2 * flip_coordinate - x, y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
        else:
            if axis == 'y':
                flipped_deltas = {comp_index:(a, -b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
                flipped_ip_dict = {comp_index:(x, 2 * flip_coordinate - y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
            elif axis == 'z':
                flipped_deltas = {comp_index:(a, b, -c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
                flipped_ip_dict = {comp_index:(x, y, 2 * flip_coordinate - z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
            else:
                cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
            if not ii_dict:
                ii_dict = match_points_to_closest_point(flipped_ip_dict, original_ip_dict)
                flipped_delta_dictionary = {old:[original_ip_dict[old], flipped_deltas[new]] for old, new in list(ii_dict.items())}
                return [
                 flipped_delta_dictionary, ii_dict]
        flipped_delta_dictionary = {old:[original_ip_dict[old], flipped_deltas[new]] for old, new in list(ii_dict.items())}
        return [flipped_delta_dictionary, ii_dict]
    if matching_method == 'closestComponentUV':
        delta_dictionary = convert_weightDelta_positions_to_UV_coordinates(delta_dictionary, source_shape)
        if not ii_dict:
            original_ip_dict = {index:position for index, (position, delta) in list(delta_dictionary.items())}
            if axis == 'x':
                flipped_deltas = {comp_index:(-a, b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
            elif axis == 'y':
                flipped_deltas = {comp_index:(a, -b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
            elif axis == 'z':
                flipped_deltas = {comp_index:(a, b, -c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
            else:
                cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
            if uv_axis == 'u':
                flipped_ip_dict = {comp_index:(2 * flip_coordinate - x, y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
            elif uv_axis == 'v':
                flipped_ip_dict = {comp_index:(x, 2 * flip_coordinate - y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
            else:
                cmds.error(('"{}" is not a valid UV axis ("u" or "v")').format(axis))
            ii_dict = match_points_to_closest_point(flipped_ip_dict, original_ip_dict)
            flipped_delta_dictionary = {old:[original_ip_dict[old], flipped_deltas[new]] for old, new in list(ii_dict.items())}
            return [
             flipped_delta_dictionary, ii_dict]
        flipped_delta_dictionary = {old:[original_ip_dict[old], flipped_deltas[new]] for old, new in list(ii_dict.items())}
        return [
         flipped_delta_dictionary, ii_dict]
    else:
        if matching_method == 'closestPointOnSurface':
            if not ibw_dict:
                original_ip_dict = {index:position for index, (position, delta) in list(delta_dictionary.items())}
                if axis == 'x':
                    flipped_deltas = {comp_index:(-a, b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
                    flipped_ip_dict = {comp_index:(2 * flip_coordinate - x, y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
                elif axis == 'y':
                    flipped_deltas = {comp_index:(a, -b, c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
                    flipped_ip_dict = {comp_index:(x, 2 * flip_coordinate - y, z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
                elif axis == 'z':
                    flipped_deltas = {comp_index:(a, b, -c) for comp_index, (position, (a, b, c)) in list(delta_dictionary.items())}
                    flipped_ip_dict = {comp_index:(x, y, 2 * flip_coordinate - z) for comp_index, (x, y, z) in list(original_ip_dict.items())}
                else:
                    cmds.error(('"{}" is not a valid axis ("x","y", or "z")').format(axis))
                orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
                ibw_dict = match_points_to_closest_point_on_surface(orig_shape, flipped_ip_dict)
            flipped_delta_dictionary = {}
            flipped_delta_dictionary = apply_ibw_dictionary_to_delta_dictionary(flipped_delta_dictionary, flipped_deltas, ibw_dict)
            return [
             flipped_delta_dictionary, ibw_dict]
        cmds.error(('"{}" is not a valid matching method ("closestComponent","closestComponentUV","closestPointOnSurface")').format(matching_method))


def flip_deltas_with_plane(delta_dictionary, plane_position, plane_normal, matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None, max_distance=None):
    """
    Flip a delta dictionary over a plane. (faster than using a nurbsSurface)
    
    delta_dictionary = The delta dictionary you want to flip.
    plane_position = The position of the plane.
    plane_normal = The normal of the plane.
    matching_method = The method you want to use to find the matching points on each side.

        closestComponent = 
            Matches to the closest compoennt on the other side.
        closestPointOnSurface = 
            Finds the closest point on the surface and interpolates the deltas from the components that influence that point.

    source_shape = The shape that the delta dictionary came from. This is only a required input when you are using the "closestPointOnSurface" or "closestComponentUV" matching methods.
    ii_dict = An dictionary that matches component indices. Giving this value will speed up the function when using the  "closestComponent" match method.
    ibw_dict = 
        
        A dictionary that matches component indices to barycentric weight  information. 
        Each entry will look like this index = [[component_index_0, component_index_1, component_index_2...],[barcentric_weight_0, barcentric_weight_1, barcentric_weight_2...]]
        Giving this value will speed up the function when using the "closestPointOnSurface" match method.
        
    max_distance = When this value is not None any components whose matching component is farther away than this distance will have their deltas remain unchanged.

    If the matching method is "closestComponent" or "closestComponentUV" it returns delta dictionary and an ii_dict so that the operation can be performed faster next time [delta_dictionary,ii_dict]
    """
    start_dict = delta_dictionary
    mPlane = om2.MPlane()
    mVector_normal = om2.MVector(*plane_normal)
    mVector_normal.normalize()
    mPlane.setPlane(mVector_normal, 0)
    offset_distance = mPlane.distanceToPoint(om2.MVector(*plane_position), True)
    mPlane.setPlane(mVector_normal, -offset_distance)
    if matching_method == 'closestComponent':
        if not ii_dict:
            original_ip_dict = {index:position for index, (position, weight) in list(delta_dictionary.items())}
            flipped_ip_dict = {}
            flipped_deltas = {}
            for index, (position, delta) in list(delta_dictionary.items()):
                distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                flipped_ip_dict[index] = om2.MVector(position) - 2.0 * distance_to_plane * mVector_normal
                mVector_delta = om2.MVector(*delta)
                parallel_vector = mVector_normal * mVector_delta * mVector_normal
                perpendicular_vector = mVector_delta - parallel_vector
                new_delta = perpendicular_vector - parallel_vector
                flipped_deltas[index] = list(new_delta)[0:3]

            ii_dict = match_points_to_closest_point(flipped_ip_dict, original_ip_dict, max_distance=max_distance)
        else:
            flipped_deltas = {}
            for index, (position, delta) in list(delta_dictionary.items()):
                distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                mVector_delta = om2.MVector(*delta)
                parallel_vector = mVector_normal * mVector_delta * mVector_normal
                perpendicular_vector = mVector_delta - parallel_vector
                new_delta = perpendicular_vector - parallel_vector
                flipped_deltas[index] = list(new_delta)[0:3]

            result_dictionary = delta_dictionary.copy()
            for old, new in list(ii_dict.items()):
                result_dictionary[old] = [
                 delta_dictionary[old][0], flipped_deltas[new]]

        return [result_dictionary, ii_dict]
    if matching_method == 'closestPointOnSurface':
        if not ibw_dict:
            original_ip_dict = {index:position for index, (position, weight) in list(delta_dictionary.items())}
            flipped_ip_dict = {}
            flipped_deltas = {}
            for index, (position, delta) in list(delta_dictionary.items()):
                distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                flipped_ip_dict[index] = om2.MVector(position) - 2.0 * distance_to_plane * mVector_normal
                mVector_delta = om2.MVector(*delta)
                parallel_vector = mVector_normal * mVector_delta * mVector_normal
                perpendicular_vector = mVector_delta - parallel_vector
                new_delta = perpendicular_vector - parallel_vector
                flipped_deltas[index] = list(new_delta)[0:3]

            orig_shape = cmds.listRelatives(cmds.listRelatives(source_shape, p=True)[0], s=True)[(-1)]
            ibw_dict = match_points_to_closest_point_on_surface(orig_shape, flipped_ip_dict)
        else:
            flipped_deltas = {}
            for index, (position, delta) in list(delta_dictionary.items()):
                distance_to_plane = mPlane.distanceToPoint(om2.MVector(*position), True)
                flipped_ip_dict[index] = om2.MVector(position) - 2.0 * distance_to_plane * mVector_normal
                mVector_delta = om2.MVector(*delta)
                parallel_vector = mVector_normal * mVector_delta * mVector_normal
                perpendicular_vector = mVector_delta - parallel_vector
                new_delta = perpendicular_vector - parallel_vector
                flipped_deltas[index] = list(new_delta)[0:3]

        result_dictionary = delta_dictionary.copy()
        result_dictionary = apply_ibw_dictionary_to_delta_dictionary(result_dictionary, flipped_deltas, ibw_dict)
        return [
         result_dictionary, ibw_dict]
    cmds.error('"{}" is not a valid matching_method ("closestComponent","closestPointOnSurface")')


def split_deltas(delta_dictionary, split_coordinate=0, axis='x', falloff_distance=0):
    """
    Splits a delta dictionary into two weight dictionaries one for each side of the split_coordinate along the given axis.
    
    delta_dictionary = The weight dictionary you want to split.
    split_coordinate = The coordinate you want to split the weights above and below.
    axis: The axis you want to mirror the deformations over ("x" "y" or "z"). 
    falloff_distance = The distance around the coordinate that smooths the split weights.
    
    Returns a list containing two delta dictionaries one for each side of the split coordinate and a list of two mask weight dictionaries.
    [[delta_dictionary1,delta_dictionary2],[mask_dictionary1,mask_dictionary2]]
    """
    weight_dictionary = {index:[position, 1] for index, (position, delta) in list(delta_dictionary.items())}
    split_weight_dict_list, mask_weight_dict_list = split_weights(weight_dictionary, split_coordinate=split_coordinate, axis=axis, falloff_distance=falloff_distance)
    split_deltas_dict_list = [ multiply_deltas_by_weights(weight_dict, delta_dictionary) for weight_dict in split_weight_dict_list ]
    return [
     split_deltas_dict_list, mask_weight_dict_list]


def split_deltas_with_surface(delta_dictionary, nurbsSurface, falloff_distance):
    """
    Splits a delta dictionary into two delta dictionaries on for each side of the surface.
    
    delta_dictionary = The delta dictionary you want to split.
    nurbsSurface = The nurbs surface that is used to split the delta dictionary.
    falloff_distance = The distance around the surface that smooths the split deltas.
    
    Returns a list containing two delta dictionaries one for each side of the surface, and a list containing two mask weight dictionaries.
    """
    weight_dictionary = {index:[position, 1] for index, (position, delta) in list(delta_dictionary.items())}
    split_weight_dict_list, mask_weight_dict_list = split_weights_with_surface(weight_dictionary, nurbsSurface, falloff_distance)
    split_deltas_dict_list = [ multiply_deltas_by_weights(weight_dict, delta_dictionary) for weight_dict in split_weight_dict_list ]
    return [
     split_deltas_dict_list, mask_weight_dict_list]


def split_deltas_with_plane(delta_dictionary, plane_position, plane_normal, falloff_distance):
    """
    Splits a delta dictionary into two delta dictionaries one for each side of a plane. (faster than using a nurbsSurface)
    
    delta_dictionary = The delta dictionary you want to split.
    plane_position = The position of the plane.
    plane_normal = The normal of the plane.
    falloff_distance = The distance from the plane over which you want to smooth the split deltas.
    
    Returns a list containing two delta dictionaries one for each side of the plane, and a list containing two mask weight dictionaries.
    [[delta_dictionary1,delta_dictionary2],[mask_dictionary1,mask_dictionary2]]
    """
    weight_dictionary = {index:[position, 1] for index, (position, delta) in list(delta_dictionary.items())}
    split_weight_dict_list, mask_weight_dict_list = split_deltas_with_plane(weight_dictionary, plane_position, plane_normal, falloff_distance)
    split_deltas_dict_list = [ multiply_deltas_by_weights(weight_dict, delta_dictionary) for weight_dict in split_weight_dict_list ]
    return [
     split_deltas_dict_list, mask_weight_dict_list]


def split_deltas_radially(delta_dictionary, split_MMatrix, number_of_sections=4, falloff_angle=0):
    """
    Splits a delta dictionary into two delta dictionaries one for each side of the split_coordinate along the given axis.
    
    delta_dictionary = The delta dictionary you want to split radially.
    split_matrix = The matrix whose position and orientation are going to be used to split the deltas. It will split as if creating a wedge and rotating it around the objects y axis. Example: om2.MMatrix
    number_of_sections = The number of sectors the deltas will be split into.
    falloff_angle = The angle range over which the deltas are smoothed.
    
    Returns a list of delta dictionaries and list of mask weight dictionaries.
    [[delta_dictionary1,delta_dictionary2...],[mask_dictionary1,mask_dictionary2...]]
    """
    weight_dictionary = {index:[position, 1] for index, (position, delta) in list(delta_dictionary.items())}
    split_weight_dict_list, mask_weight_dict_list = split_weights_radially(weight_dictionary, split_MMatrix, number_of_sections, falloff_angle)
    split_deltas_dict_list = [ multiply_deltas_by_weights(weight_dict, delta_dictionary) for weight_dict in split_weight_dict_list ]
    return [
     split_deltas_dict_list, mask_weight_dict_list]


def split_deltas_along_curve(delta_dictionary, nurbsCurve, falloff_distance=1, split_number=2, mode=0):
    """ 
    Takes a delta dictionary and splits it along the given nurbsCurve into multiple delta dictionaries. 
    
    delta_dictionary = The weight dictionary you want to split.
    falloff_distance: The distance over which the returned delta dictionaries are smoothed.
    split_number: The number of delta dictionaries you want to split the weight dictionary into.
    mode: Which coordinate (relative to the curve) you want to use to split the curve. 
    
    0 = Parameter
    1 = Distance Along The Curve
    2 = Distance To Curve
            
    Returns a list of deltas dictionaries and a list of mask weight dictionaries.
    [[delta_dictionary1,delta_dictionary2...],[mask_dictionary1,mask_dictionary2...]]
    """
    weight_dictionary = {index:[position, 1] for index, (position, delta) in list(delta_dictionary.items())}
    split_weight_dict_list, mask_weight_dict_list = split_weights_along_curve(weight_dictionary, nurbsCurve, falloff_distance=falloff_distance, split_number=split_number, mode=mode)
    split_deltas_dict_list = [ multiply_deltas_by_weights(weight_dict, delta_dictionary) for weight_dict in split_weight_dict_list ]
    return [
     split_deltas_dict_list, mask_weight_dict_list]


def split_deltas_along_surface(delta_dictionary, nurbsSurface, falloff_distance=1, split_number=2, mode=0):
    """ 
    Takes a delta dictionary and splits it along the given nurbsSurface into multiple deltas dictionaries. 
    
    deltas_dictionary = The deltas dictionary you want to split.
    nurbsSurface = The surface you want to use to split the given deltas dictionary.
    falloff_distance: The distance over which the returned weigh dictionaries are smoothed.
    split_number: The number of deltas dictionaries you want to split the deltas dictionary into.
    mode: Which coordinate (relative to the surface) you want to use to split the curve.
    
    0 = U Parameter
    1 = V Parameter
    2 = Distance From The Surface
            
    Returns a list of deltas dictionaries and a list of mask weight dictionaries.
    [[delta_dictionary1,delta_dictionary2...],[mask_dictionary1,mask_dictionary2...]]
    """
    weight_dictionary = {index:[position, 1] for index, (position, delta) in list(delta_dictionary.items())}
    split_weight_dict_list, mask_weight_dict_list = split_weights_along_surface(weight_dictionary, nurbsSurface, falloff_distance=1, split_number=2, mode=0)
    split_deltas_dict_list = [ multiply_deltas_by_weights(weight_dict, delta_dictionary) for weight_dict in split_weight_dict_list ]
    return [
     split_deltas_dict_list, mask_weight_dict_list]


def add_deltas(delta_dictionary_01, delta_dictionary_02):
    """ 
    Takes two delta dictionaries and matches them by index and ass the second to the first.
    
    delta_dictionary_01 = The first delta dictionary whose deltas you want to add. This dictionary will be the source for the positions. 
    dtla_dictionary_02 = The second delta dictionary whose deltas you want to add. 

    Returns a delta dictionary.
    """
    sum_delta_dictionary = delta_dictionary_01.copy()
    for index, (position, delta) in list(delta_dictionary_02.items()):
        if index in sum_delta_dictionary:
            sum_delta_dictionary[index] = (
             delta_dictionary_01[index][0], [ a + b for a, b in zip(delta_dictionary_01[index][1], delta_dictionary_02[index][1]) ])
        else:
            sum_delta_dictionary[index] = (
             position, delta)

    return sum_delta_dictionary


def subtract_deltas(delta_dictionary_01, delta_dictionary_02):
    """ 
    Takes two delta dictionaries and matches them by index and subtracts the second from the first. If the second dictionary has indexes not in 
    the first dictionary they will be skipped. If the first dictionary has indexes not in the second they will remain unchanged.
    
    delta_dictionary_01 = The first delta dictionary whose deltas you want to subtract from. This dictionary will be the source for the positions. 
    delta_dictionary_02 = The second delta dictionary whose deltas you want to subtract. 

    Returns a delta dictionary.
    """
    sum_delta_dictionary = delta_dictionary_01.copy()
    for index, (position, delta) in list(delta_dictionary_02.items()):
        if index in sum_delta_dictionary:
            sum_delta_dictionary[index] = (
             delta_dictionary_01[index][0], [ a - b for a, b in zip(delta_dictionary_01[index][1], delta_dictionary_02[index][1]) ])

    return sum_delta_dictionary


def multiply_deltas(delta_dictionary_01, scalar):
    """ 
    Takes a deltas dictionary and scales the deltas by the given scalar.
    
    delta_dictionary = The deltas dictionary you want to scale
    scalar = The value the deltas will be scaled by

    Returns a delta dictionary.
    """
    return {index:[position, [ x * scalar for x in delta ]] for index, (position, delta) in list(delta_dictionary_01.items())}


def clear_deltas(blendShape_node, blendShape_target, inBetween_weight=1, component_list=None):
    """
    Generates a delta dictionary from the given target on the given blendShape node.
    
    blendShape_node = The blendShape node the blendShape_target is on.
    blendShape_target = The blendShape target you want to set the deltas for.
    """
    target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    shape = cmds.blendShape(blendShape_node, q=True, g=True)
    if shape == []:
        cmds.error(('"{}" does not affect any geometry').format(shape))
    else:
        shape = shape[0]
    item_index = int(5000 + 1000 * inBetween_weight)
    if component_list:
        delta_components = cmds.getAttr(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputComponentsTarget').format(blendShape_node, target_index, item_index))
        delta_points = cmds.getAttr(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputPointsTarget').format(blendShape_node, target_index, item_index))
        component_prefix = delta_components[0].split('[')[0]
        delta_index_list = []
        for element in delta_components:
            if ':' in element:
                slice_start, slice_end = element.split(':')
                slice_start = int(slice_start.split('[')[(-1)])
                slice_end = int(slice_end[:-1]) + 1
                delta_index_list += list(range(slice_start, slice_end))
            else:
                delta_index_list.append(int(element.split('[')[(-1)][:-1]))

        component_index_list = get_index_list(component_list)
        new_delta_components = []
        new_delta_points = []
        for delta_point, delta_index in zip(delta_points, delta_index_list):
            if delta_index not in component_index_list:
                new_delta_points.append(delta_point)
                new_delta_components.append(('{}[{}]').format(component_prefix, delta_index))

        list_size = len(new_delta_components)
        cmds.setAttr(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputComponentsTarget').format(blendShape_node, target_index, item_index), list_size, type='componentList', *new_delta_components)
        cmds.setAttr(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputPointsTarget').format(blendShape_node, target_index, item_index), list_size, type='pointArray', *new_delta_points)
    else:
        shape = cmds.blendShape(blendShape_node, q=True, g=True)[0]
        if cmds.nodeType(shape) == 'mesh':
            component_prefix = 'vtx'
        if cmds.nodeType(shape) == 'nurbsCurve':
            component_prefix = 'cv'
        cmds.setAttr(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputComponentsTarget').format(blendShape_node, target_index, item_index), 1, type='componentList', *[component_prefix + '[0]'])
        cmds.setAttr(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputPointsTarget').format(blendShape_node, target_index, item_index), 1, type='pointArray', *[(0.0, 0.0, 0.0, 1.0)])


def multiply_deltas_by_weights(weight_dictionary, delta_dictionary):
    """
    Scale the deltas in delta dictionary by the weights in a weight dictionary. The deltas and weights are matched by index.
    
    weight_dictionary = The weight dictionary whose weights you want to scale the given delta dictionary by.
    delta_dictionary = The deltas dictionary whose deltas you want to scale.
    """
    scaled_dictionary = {}
    for index, (position, delta) in list(delta_dictionary.items()):
        if index in weight_dictionary:
            scaled_dictionary[index] = [
             position, [ axis_delta * weight_dictionary[index][1] for axis_delta in delta ]]
        else:
            scaled_dictionary[index] = [
             position, (0, 0, 0)]

    return scaled_dictionary


def average_deltas(delta_dictionary):
    """
    Averages the deltas in a delta dictionary. Useful when using the transfer_blendShapes_via_wrap to create a riveted patch on the mesh.
    The deltas direction are averaged, and then their lengths.
    
    delta_dictionary: The deltas you want to average.
    
    Returns a delta dictionary containing the averaged deltas.
    """
    items = list(delta_dictionary.items())
    index_list = [ key for key, value in items ]
    position_list = [ om2.MVector(*value[0]) for key, value in items ]
    vector_list = [ om2.MVector(*value[1]) for key, value in items ]
    magnitude = [ vector.length() for vector in vector_list ]
    avg_magnitude = sum(magnitude) / len(magnitude)
    sum_vector = om2.MVector(0, 0, 0)
    for vector in vector_list:
        sum_vector += vector

    single_vector = om2.MVector(sum_vector).normalize() * avg_magnitude
    return {key:(pos, single_vector) for key, pos in zip(index_list, position_list)}


def extract_deltas(shape, target_index_position_dict, post_deformation=False, post_deformation_blendShape=None, safeMode=True):
    """
    Calculated the pre-deformation deltas that need to be applied to the given shape in order to match the positions in the given index position dictionary
    Can handle shapes being deformed by skinClusters and clusters.
    
    shape: The shape that you want to apply the deltas to (this function does not apply the deltas though, it just calculates them).
    target_index_position_dictionary = A dictionary in the form {component index: component position,...} that comes from the target shape. This lets you extract deltas without needing the actually target shape in the scene.
    
    Returns  a deltas dictionary.
    """
    transform = cmds.listRelatives(shape, p=True, f=True)[0]
    original_shape = cmds.listRelatives(transform, s=True, f=True)[(-1)]
    sel = om2.MSelectionList()
    sel.add(shape)
    sel.add(original_shape)
    shape_dagPath = sel.getDagPath(0)
    original_shape_dagPath = sel.getDagPath(1)
    if cmds.nodeType(shape) == 'mesh':
        mFn_original = om2.MFnMesh(original_shape_dagPath)
        start_original_position_list = mFn_original.getPoints(1)
        start_original_global_position_list = mFn_original.getPoints(1)
        mFn_rigged = om2.MFnMesh(shape_dagPath)
        start_rigged_position_list = mFn_rigged.getPoints(1)
    else:
        if cmds.nodeType(shape) == 'nurbsCurve':
            mFn_original = om2.MFnNurbsCurve(original_shape_dagPath)
            start_original_position_list = mFn_original.cvPositions(1)
            start_original_global_position_list = mFn_original.cvPositions(1)
            mFn_rigged = om2.MFnNurbsCurve(shape_dagPath)
            start_rigged_position_list = mFn_rigged.cvPositions(1)
        else:
            if cmds.nodeType(shape) == 'nurbsSurface':
                mFn_original = om2.MFnNurbsSurface(original_shape_dagPath)
                start_original_position_list = mFn_original.cvPositions(1)
                start_original_global_position_list = mFn_original.cvPositions(1)
                mFn_rigged = om2.MFnNurbsSurface(shape_dagPath)
                start_rigged_position_list = mFn_rigged.cvPositions(1)
            else:
                if cmds.nodeType(shape) == 'lattice':
                    cmds.warning('Extract deltas for lattices has not been implemented')
                    return
                else:
                    return

            if post_deformation or safeMode:
                if not post_deformation_blendShape:
                    cmds.error('post_deformation_blendShape is a required input when post_deformation = True or safeMode = True')
                temp_target, temp_index = add_empty_blendShape_target(post_deformation_blendShape, target_name='emptyTarget', tangent_space=post_deformation)
                cmds.setAttr(('{}.{}').format(post_deformation_blendShape, temp_target), 1)
                vector_list = []
                for i in range(3):
                    offset_vector = [
                     0, 0, 0]
                    offset_vector[i] = 1
                    delta_dict = {index:((0, 0, 0), offset_vector) for index in range(len(start_rigged_position_list))}
                    set_blendShape_target_deltas(post_deformation_blendShape, temp_target, delta_dict, inBetween_weight=1)
                    if cmds.nodeType(shape) == 'mesh':
                        offset_rigged_position_list = mFn_rigged.getPoints(1)
                    elif cmds.nodeType(shape) == 'nurbsCurve':
                        offset_rigged_position_list = mFn_rigged.cvPositions(1)
                    elif cmds.nodeType(original_shape) == 'nurbsSurface':
                        offset_rigged_position_list = mFn_rigged.cvPositions(1)
                    elif cmds.nodeType(shape) == 'lattice':
                        return
                    axis_vector_list = [ om2.MVector(offset_pos - pos) for offset_pos, pos in zip(offset_rigged_position_list, start_rigged_position_list) ]
                    vector_list.append(axis_vector_list)

                delete_blendShape_target(post_deformation_blendShape, temp_target)
            else:
                vector_list = []
                for i in range(3):
                    offset_vector = [0, 0, 0]
                    offset_vector[i] = 1
                    offset_vector = om2.MVector(offset_vector)
                    offset_position_list = [ pos + offset_vector for pos in start_original_position_list ]
                    if cmds.nodeType(shape) == 'mesh':
                        mFn_original.setPoints(offset_position_list, 1)
                        mFn_original.updateSurface()
                        offset_rigged_position_list = mFn_rigged.getPoints(1)
                    elif cmds.nodeType(shape) == 'nurbsCurve':
                        mFn_original.setCVPositions(offset_position_list, 1)
                        mFn_original.updateCurve()
                        offset_rigged_position_list = mFn_rigged.cvPositions(1)
                    elif cmds.nodeType(original_shape) == 'nurbsSurface':
                        mFn_original.setCVPositions(offset_position_list, 1)
                        mFn_original.updateSurface()
                        offset_rigged_position_list = mFn_rigged.cvPositions(1)
                    elif cmds.nodeType(shape) == 'lattice':
                        return
                    axis_vector_list = [ om2.MVector(offset_pos - pos) for offset_pos, pos in zip(offset_rigged_position_list, start_rigged_position_list) ]
                    vector_list.append(axis_vector_list)

                if cmds.nodeType(shape) == 'mesh':
                    mFn_original.setPoints(start_original_position_list, 1)
                    mFn_original.updateSurface()
                elif cmds.nodeType(shape) == 'nurbsCurve':
                    mFn_original.setCVPositions(start_original_position_list, 1)
                    mFn_original.updateCurve()
                elif cmds.nodeType(original_shape) == 'nurbsSurface':
                    mFn_original.setCVPositions(start_original_position_list, 1)
                    mFn_original.updateSurface()
                elif cmds.nodeType(shape) == 'lattice':
                    return
        local_matrix_list = []
        for each_component in zip(*vector_list):
            local_matrix = om2.MMatrix()
            for row, each_vector in enumerate(each_component):
                for column, each_axis in enumerate(each_vector):
                    local_matrix.setElement(row, column, each_axis)

            local_matrix_list.append(local_matrix)

    target_positions = [ x[1] for x in list(target_index_position_dict.items()) ]
    target_positions = [ om2.MPoint(pos) for pos in target_positions ]
    deltas = [ target_pos - start_pos for target_pos, start_pos in zip(target_positions, start_rigged_position_list) ]
    localized_deltas = [ delta * matrix.inverse() for delta, matrix in zip(deltas, local_matrix_list) ]
    localized_deltas = [ tuple(x)[0:3] for x in localized_deltas ]
    start_original_global_position_list = [ tuple(x)[0:3] for x in start_original_global_position_list ]
    delta_dictionary = {index:(pos, delta) for index, pos, delta in zip(list(range(len(localized_deltas))), start_original_global_position_list, localized_deltas)}
    return delta_dictionary


def getVertexTangents(shape, normalize=True):
    """ Prototype/Snippet to get vertex tangents from a mesh """
    selList = om2.MSelectionList()
    selList.add(shape)
    path = selList.getDagPath(0)
    fnMesh = om2.MFnMesh(path)
    tangents = fnMesh.getTangents()
    itMeshVertex = om2.MItMeshVertex(path)
    vertId = 0
    connectedFaceIds = om2.MIntArray()
    vertTangents = []
    while not itMeshVertex.isDone():
        connectedFaceIds = itMeshVertex.getConnectedFaces()
        tangent = om2.MFloatVector()
        for faceId in connectedFaceIds:
            tangentId = fnMesh.getTangentId(faceId, vertId)
            tangent += tangents[tangentId]


def extract_blendShape_target(blendShape_node, blendShape_target):
    """
    Takes the given blendShape target on the given blendShape node and extracts it as a mesh
    
    blendShape_node = The blendShape node that contains the target you want to extract.
    blendShape_target = The blendShape target that you want to extract
    
    Returns the name of the extracted shape
    """
    target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    if cmds.objExists(blendShape_target):
        dup_shape = cmds.duplicate(blendShape_target)[0]
    else:
        live_shape = cmds.sculptTarget(blendShape_node, e=True, regenerate=True, target=target_index)[0]
        dup_shape = cmds.duplicate(live_shape)[0]
        cmds.delete(live_shape)
    cmds.select(cmds.listRelatives(dup_shape, c=True, f=True))
    cmds.select(cmds.listRelatives(dup_shape, s=True, f=True), d=True)
    cmds.delete()
    try:
        dup_shape = cmds.parent(dup_shape, w=True)[0]
    except:
        pass

    return dup_shape


def add_empty_blendShape_target(blendShape_node, target_name='emptyTarget', tangent_space=False):
    """
    Adds a new target to the given blendshape node. The new target will have no deltas.
    
    blendShape_node = The blendShape node that contains the target you want to extract.
    target_name = The name you want to be assigned to the new target.
    
    Returns the name of the new target (which may change to avoid conflicting names) and the index of the new target.
    """
    if not cmds.objExists(blendShape_node):
        cmds.error('"{}" does not exist')
    if cmds.nodeType(blendShape_node) != 'blendShape':
        cmds.error('"{}" is not a blendShape node')
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(blendShape_node)
    mObject_blendShape_node = mSelectionList.getDependNode(0)
    mFnDependencyNode = om2.MFnDependencyNode(mObject_blendShape_node)
    target_mPlug = mFnDependencyNode.findPlug('inputTarget', False).elementByLogicalIndex(0).child(0)
    used_index_list = list(target_mPlug.getExistingArrayAttributeIndices())
    if used_index_list == []:
        max_index = -1
    else:
        max_index = max(used_index_list)
    target_mPlug.elementByLogicalIndex(max_index + 1).asMObject()
    target_mPlug.evaluateNumElements()
    input_target_item_mPlug = target_mPlug.elementByLogicalIndex(max_index + 1).child(0)
    input_target_item_mPlug.elementByLogicalIndex(6000)
    input_target_item_mPlug.evaluateNumElements()
    weight_mPlug = mFnDependencyNode.findPlug('weight', False)
    weight_mPlug.elementByLogicalIndex(max_index + 1).asFloat()
    weight_mPlug.evaluateNumElements()
    if tangent_space:
        base_obj = cmds.blendShape(blendShape_node, q=True, g=True)
        if not base_obj:
            cmds.error(('"{}" does not affect any geometry and therefore there is no tangent space').format(blendShape_node))
        temp_obj = cmds.duplicate(base_obj[0])[0]
        cmds.blendShape(blendShape_node, e=True, target=[base_obj[0], max_index + 1, temp_obj, 1.0], tangentSpace=True)
        cmds.delete(temp_obj)
    if not cmds.attributeQuery(target_name, node=blendShape_node, exists=True):
        cmds.aliasAttr(target_name, ('{}.w[{}]').format(blendShape_node, max_index + 1))
        return (
         target_name, max_index + 1)
    else:
        ending_enumeration = re.findall('\\d+$', target_name)
        if ending_enumeration:
            numberless_target = target_name[:-len(ending_enumeration[0])]
            ending_enumeration = int(ending_enumeration[0])
        else:
            ending_enumeration = 1
            numberless_target = target_name
        while cmds.attributeQuery(('{}{}').format(numberless_target, ending_enumeration), node=blendShape_node, exists=True):
            ending_enumeration += 1

        cmds.aliasAttr(numberless_target + str(ending_enumeration), ('{}.w[{}]').format(blendShape_node, max_index + 1))
        return (numberless_target + str(ending_enumeration), max_index + 1)


def duplicate_blendShape_target(blendShape_node, blendShape_target, include_inBetweens=False):
    """
    Creates a duplicate of the given blendShape target on the given blendShape node
    
    blendShape_node = The blendShape node that contains the target you want to duplicate.
    blendShape_target = The blendShape target that you want to duplicate.
    include_inBetweens = When true, all the inBetweens for the given blendShape target will also be duplicated 
    
    If include inBetweens is False returns the name of the new target the index of the new target as a list, and an empty list. [target name, target index, []]
    If include inBetweens is True returns the name of the new target, the index of the new target. and a list with an element for each duplicated inBetween containing their name and weight. [target name, target index, [[inBetween0_name, inBetween0_weight],...]]
    """
    target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    dup_target, dup_index = add_empty_blendShape_target(blendShape_node, target_name=blendShape_target)
    delta_dictionary = get_blendShape_target_deltas(blendShape_node, blendShape_target)
    set_blendShape_target_deltas(blendShape_node, dup_target, delta_dictionary)
    return_list = []
    if include_inBetweens:
        sel = om2.MSelectionList()
        sel.add(blendShape_node)
        mFn = om2.MFnDependencyNode(sel.getDependNode(0))
        inBetweenInfo_mPlug = mFn.findPlug('inbetweenInfoGroup', False).elementByLogicalIndex(target_index).child(0)
        ib_target_indices = inBetweenInfo_mPlug.getExistingArrayAttributeIndices()
        for index in ib_target_indices:
            inBetween_name = inBetweenInfo_mPlug.elementByLogicalIndex(index).child(1).asString()
            inBetween_weight = float(index - 5000.0) / 1000.0
            add_inBetween_blendShape_target(blendShape_node, dup_target, inBetween_weight, inBetween_target_name=inBetween_name)
            deltas = get_blendShape_target_deltas(blendShape_node, blendShape_target, inBetween_weight=inBetween_weight)
            set_blendShape_target_deltas(blendShape_node, dup_target, deltas, inBetween_weight=inBetween_weight)
            return_list.append([inBetween_name, inBetween_weight])

    return [
     dup_target, dup_index, return_list]


def add_inBetween_blendShape_target(blendShape_node, blendShape_target, inBetween_weight, inBetween_target_name='emptyInbetween'):
    """
    Adds a new target to the given blendshape node. The new target will have no deltas.
    
    blendShape_node = The blendShape node that contains the target you want to extract.
    target_name = The name of the target you want to add an inBetween target to.
    inBetween_target_name = The name you want to assign to the new inBetween target.
    """
    given_target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    item_index = int(5000 + 1000 * inBetween_weight)
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(blendShape_node)
    mObject_blendShape_node = mSelectionList.getDependNode(0)
    mFnDependencyNode = om2.MFnDependencyNode(mObject_blendShape_node)
    target_mPlug = mFnDependencyNode.findPlug('inputTarget', False).elementByLogicalIndex(0).child(0).elementByLogicalIndex(given_target_index).child(0)
    used_index_list = list(target_mPlug.getExistingArrayAttributeIndices())
    if item_index in used_index_list:
        cmds.error(('An inbetween already exists for the weight {} on {}.{}').format(inBetween_weight, blendShape_node, blendShape_target))
    target_mPlug.elementByLogicalIndex(item_index).asMObject()
    target_mPlug.evaluateNumElements()
    ibInfo_mPlug = mFnDependencyNode.findPlug('inbetweenInfoGroup', False)
    ib_target_indices = ibInfo_mPlug.getExistingArrayAttributeIndices()
    ib_weight_indices = ibInfo_mPlug.elementByLogicalIndex(given_target_index).child(0).elementByLogicalIndex(item_index).child(1).setString(inBetween_target_name)


def delete_blendShape_target(blendShape_node, blendShape_target):
    """
    Deletes the given blendShape_target from the given blendShape_node
    
    blendShape_node = The blendShape node that contains the target you want to delete.
    blendShape_target = The blendShape target that you want to delete.
    """
    target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    incoming_connection = cmds.connectionInfo(('{}.{}').format(blendShape_node, blendShape_target), sfd=True)
    if incoming_connection:
        cmds.disconnectAttr(incoming_connection, ('{}.{}').format(blendShape_node, blendShape_target))
    cmds.setAttr(('{}.{}').format(blendShape_node, blendShape_target), 0)
    cmds.aliasAttr(('{}.{}').format(blendShape_node, blendShape_target), remove=True)
    cmds.removeMultiInstance(('{}.weight[{}]').format(blendShape_node, target_index), b=True)
    cmds.removeMultiInstance(('{}.inputTarget[0].inputTargetGroup[{}]').format(blendShape_node, target_index), b=True)
    cmds.setAttr(('{}.inputTarget[0].sculptInbetweenWeight').format(blendShape_node), -1)
    cmds.setAttr(('{}.pndr[0]').format(blendShape_node), -1)
    cmds.setAttr(('{}.targetVisibility[{}]').format(blendShape_node, target_index), 1)
    cmds.setAttr(('{}.targetParentVisibility[{}]').format(blendShape_node, target_index), 1)
    cmds.removeMultiInstance(('{}.targetVisibility[{}]').format(blendShape_node, target_index), b=True)
    cmds.removeMultiInstance(('{}.targetParentVisibility[{}]').format(blendShape_node, target_index), b=True)


def delete_inBetween_blendShape_target(blendShape_node, blendShape_target, inBetween_weight):
    """
    Deletes the given blendShape_target from the given blendShape_node
    
    blendShape_node = The blendShape node that contains the target you want to delete.
    blendShape_target = The blendShape target that you want to delete.
    inBetween_weight = The weight of the inBetween you want to add.
    """
    target_index = get_blendShape_target_index(blendShape_node, blendShape_target)
    item_index = int(5000 + 1000 * inBetween_weight)
    mSelectionList = om2.MSelectionList()
    mSelectionList.add(blendShape_node)
    mObject_blendShape_node = mSelectionList.getDependNode(0)
    mFnDependencyNode = om2.MFnDependencyNode(mObject_blendShape_node)
    target_mPlug = mFnDependencyNode.findPlug('inputTarget', False).elementByLogicalIndex(0).child(0).elementByLogicalIndex(target_index).child(0)
    used_index_list = list(target_mPlug.getExistingArrayAttributeIndices())
    if item_index not in used_index_list:
        cmds.error(('An inbetween does not exist for the weight {} on {}.{}').format(inBetween_weight, blendShape_node, blendShape_target))
    cmds.removeMultiInstance(('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}]').format(blendShape_node, target_index, item_index), b=True)
    cmds.removeMultiInstance(('{}.inbetweenInfoGroup[{}].inbetweenInfo[{}]').format(blendShape_node, target_index, item_index), b=True)


def bake_weights_onto_blendShape_target(blendShape_node, blendShape_target):
    """
    Takes the painted weights on the given blendShape target and bakes them onto the actual target deltas.
    
    blendShape_node = The blendShape node that contains the target you want to bake.
    blendShape_target = The blendShape target that you want to bake
    """
    shape = cmds.blendShape(blendShape_node, q=True, g=True)
    if not shape:
        return
    shape = shape[0]
    delta_dictionary = get_blendShape_target_deltas(blendShape_node, blendShape_target)
    weight_dictionary = get_blendShape_target_weights(blendShape_node, blendShape_target)
    product_dictionary = multiply_deltas_by_weights(weight_dictionary, delta_dictionary)
    set_blendShape_target_deltas(blendShape_node, blendShape_target, product_dictionary)
    full_weight_dictionary = {index:(pos, 1) for index, (pos, wt) in list(weight_dictionary.items())}
    set_blendShape_target_weights(blendShape_node, blendShape_target, full_weight_dictionary, shape=shape)


def make_blendShape_target_radial(blendShape_node, blendShape_target, center_point, rotation_vector=None):
    """
    Takes the given blendShape target on the given blendShape node and makes it follow a quadratic spline path that closesly approximates a radial path areound the given center point.
    It accomplishes this by splitting the given target into two targets and varying the weight of those two targets according to the following functions found below.
    The rotation vector is the vector around which the radial "rotation" takes place. 
    When the rotation vector is set to None the spline path is the shortest distance on the surface of a sphere between the two points (plus the offset distance from the "sphere").
    
    blendShape_node = The blendShape node that contains the target you want to make radial
    blendShape_target = The blendShape target that you want to make radial
    center_point = The center point of the rotation. Example: (0,0,0)
    rotation_vector = The approximated radial motion will use this is the axis of rotation. Example: (0,1,0)
    """
    delta_dictionary = get_blendShape_target_deltas(blendShape_node, blendShape_target)
    midPoint_deltas = {}
    center_vector = om2.MVector(*center_point)
    if rotation_vector:
        rotation_vector = om2.MVector(*rotation_vector)
    for index, (position, delta) in list(delta_dictionary.items()):
        position_vector = om2.MVector(position)
        delta_vector = om2.MVector(delta)
        vector1 = position_vector - center_vector
        vector2 = position_vector + delta_vector - center_vector
        if rotation_vector:
            rotation_vector = om2.MVector(*rotation_vector)
            vector1_parallel_scalar = vector1 * rotation_vector
            vector2_parallel_scalar = vector2 * rotation_vector
            average_length = (vector1_parallel_scalar + vector2_parallel_scalar) / 2.0
            parallel_component = rotation_vector.normalize() * average_length
            vector1_perpendicular_component = vector1 - rotation_vector * vector1_parallel_scalar
            vector2_perpendicular_component = vector2 - rotation_vector * vector2_parallel_scalar
            average_vector = (vector1_perpendicular_component + vector2_perpendicular_component) / 2.0
            average_length = (vector1_perpendicular_component.length() + vector2_perpendicular_component.length()) / 2.0
            perpendicular_component = om2.MVector(average_vector).normalize() * average_length
            perpendicular_component = perpendicular_component - average_vector + perpendicular_component
            midPoint_delta = tuple(perpendicular_component + parallel_component - position_vector)[0:3]
        else:
            average_vector = (vector1 + vector2) / 2.0
            average_length = (vector1.length() + vector2.length()) / 2.0
            midPoint_vector = om2.MVector(average_vector).normalize() * average_length
            midPoint_vector = midPoint_vector - average_vector + midPoint_vector
            midPoint_delta = tuple(midPoint_vector - position_vector)[0:3]
        midPoint_deltas[index] = [position, midPoint_delta]

    endTarget, endTarget_index = duplicate_blendShape_target(blendShape_node, blendShape_target)
    midTarget, midTarget_index = duplicate_blendShape_target(blendShape_node, blendShape_target)
    set_blendShape_target_deltas(blendShape_node, midTarget, midPoint_deltas)
    clear_deltas(blendShape_node, blendShape_target)
    cmds.expression(s=('{}.{} = - 2*pow({}.{},2) + 2*{}.{}').format(blendShape_node, midTarget, blendShape_node, blendShape_target, blendShape_node, blendShape_target))
    cmds.expression(s=('{}.{} = pow({}.{},2)').format(blendShape_node, endTarget, blendShape_node, blendShape_target))
    cmds.aliasAttr(blendShape_target + '_radial_part1', ('{}.w[{}]').format(blendShape_node, midTarget_index))
    cmds.aliasAttr(blendShape_target + '_radial_part2', ('{}.w[{}]').format(blendShape_node, endTarget_index))


def get_blendShape_target_weight_list(mObject_blendShape_node, target_index, member_index, componentCount):
    """
    This functions gets the weights for the a blendShape target.
    """
    mFnDependencyNode = om2.MFnDependencyNode(mObject_blendShape_node)
    weights_mPlug = mFnDependencyNode.findPlug('inputTarget', False).elementByLogicalIndex(member_index).child(0).elementByLogicalIndex(target_index).child(1)
    weight_list = [ 1 for x in range(componentCount) ]
    for comp_index in weights_mPlug.getExistingArrayAttributeIndices():
        if comp_index < componentCount:
            weight_list[comp_index] = weights_mPlug.elementByLogicalIndex(comp_index).asFloat()
        else:
            break


def set_deformer_order(shape, deformer_list):
    """
    Puts the deformers in the given order.
    
    shape = The shape whose deformation order you are setting.
    deformer_list = The ordered list of deformers from first to last in order of evaluation.
    """
    if not deformer_list:
        return
    connections = {}
    for x in cmds.listHistory(shape):
        if x in cmds.ls(type='geometryFilter'):
            x_connections = cmds.listConnections(x, s=True, d=True, p=True, c=True)
            sources = x_connections[1::2]
            destinations = x_connections[::2]
            for s, d in zip(sources, destinations):
                if 'inputGeometry' in s:
                    continue
                if 'outputGeometry' in s:
                    continue
                if 'inputGeometry' in d:
                    continue
                if 'outputGeometry' in d:
                    continue
                if 'groupId' in s:
                    continue
                if 'usedBy' in s:
                    continue
                if 'usedBy' in d:
                    continue
                if 'message' in d:
                    continue
                if 'message' in s:
                    continue
                if cmds.isConnected(s, d):
                    connections[s] = d
                elif cmds.isConnected(d, s):
                    connections[d] = s

    for s, d in list(connections.items()):
        try:
            if 'interactiveBindInterface' not in d:
                if cmds.isConnected(s, d):
                    cmds.disconnectAttr(s, d)
        except:
            pass

    current_order = get_ordered_deformer_list(shape)
    current_order_list = list(reversed(current_order))
    deformer_list = [ x for x in deformer_list if x in current_order ]
    cmds.select(shape)
    flipped_list = list(reversed(deformer_list))
    for i, each_deformer in enumerate(flipped_list[:-1]):
        previous_deformer = flipped_list[(i + 1)]
        deformer_index = current_order_list.index(each_deformer)
        previous_deformer_index = current_order_list.index(previous_deformer)
        if deformer_index > previous_deformer_index:
            current_order_list.pop(previous_deformer_index)
            current_order_list.insert(current_order_list.index(each_deformer) + 1, previous_deformer)
            try:
                cmds.reorderDeformers(each_deformer, previous_deformer)
            except:
                pass

    for s, d in list(connections.items()):
        try:
            if 'interactiveBindInterface' not in d:
                cmds.connectAttr(s, d)
        except:
            pass


def get_blendShape_target_deltas_list(blendShape_node, target_index, member_index, item_index, componentCount, shape):
    """
    This functions gets a list of deltas for the specified target on a specified blendShape node.
    No Checks are performed.
    """
    delta_component_ids = cmds.getAttr(('{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[{}].inputComponentsTarget').format(blendShape_node, member_index, target_index, item_index))
    if not delta_component_ids:
        return [[0, 0, 0]] * componentCount
    delta_indices = []
    for delta_component_id in delta_component_ids:
        id_slice = delta_component_id.split('[')[(-1)][:-1]
        if ':' in id_slice:
            slice_start, slice_end = id_slice.split(':')
            delta_indices += list(range(int(slice_start), int(slice_end) + 1))
        else:
            delta_indices.append(int(id_slice))

    deltas = cmds.getAttr(('{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[{}].inputPointsTarget').format(blendShape_node, member_index, target_index, item_index))
    if not deltas:
        return [[0, 0, 0]] * componentCount
    delta_list = [[0, 0, 0]] * componentCount
    for i, d in zip(delta_indices, deltas):
        delta_list[i] = d[:3]

    return delta_list


def set_blendShape_target_weightList(mObject_blendShape_node, target_index, member_index, weight_list):
    """
    This functions sets the weights on the a blendShape target.
    This method is slow, use the connectionSetter node if you can.
    """
    mFnDependencyNode = om2.MFnDependencyNode(mObject_blendShape_node)
    mPlug = mFnDependencyNode.findPlug('inputTarget', False).elementByLogicalIndex(member_index).child(0).elementByLogicalIndex(target_index).child(1)
    for i, w in enumerate(weight_list):
        mPlug.elementByLogicalIndex(i).setFloat(w)


def set_deformer_weightList(deformer_node, shape, weightList):
    """
    This sets a scarce list of weight value used by the given shape on the given deformer.
    This function will only work properly if the contents of the deformer set in the scene
    is the same size as the weightList. 
    No checks are performed.
    """
    member_index, mObject_shape, mObject_deformer, members, mFnGeometryFilter = get_member_index(deformer_node, shape)
    shape_logical_index = mFnGeometryFilter.indexForOutputShape(mObject_shape)
    components = om.MObject()
    dagPath = om.MDagPath()
    members.getDagPath(member_index, dagPath, components)
    mFnWeight = omAnim.MFnWeightGeometryFilter(mObject_deformer)
    mFloatArray_oldWeights = om.MFloatArray()
    for wt in weightList:
        mFloatArray_oldWeights.append(wt)

    mFnWeight.setWeight(dagPath, shape_logical_index, components, mFloatArray_oldWeights)


def get_deformer_weightList(mObject_deformer, mObject_shape, shape_logical_index):
    """
    This gets a scarce list of weight value used by the given shape on the given deformer.
    Only the components that are part of the deformer set will have their weights included in this list.
    """
    mFnGeometryFilter = omAnim.MFnGeometryFilter(mObject_deformer)
    mFnSet = om.MFnSet(mFnGeometryFilter.deformerSet())
    members = om.MSelectionList()
    components = om.MObject()
    dagPath = om.MDagPath()
    mFnSet.getMembers(members, False)
    for i in range(members.length()):
        mObject = om.MObject()
        members.getDependNode(i, mObject)
        if mObject_shape == mObject:
            members.getDagPath(i, dagPath, components)

    mFnWeight = omAnim.MFnWeightGeometryFilter(mObject_deformer)
    mFloatArray = om.MFloatArray()
    mFnWeight.getWeights(shape_logical_index, components, mFloatArray)
    return mFloatArray


def get_deformer_indexWeight_dictionary(mObject_deformer, mObject_shape, shape_logical_index):
    """
    This gets a scarce dictonary of component indices and associated weight value used by the given shape for the given deformer.
    """
    mFnGeometryFilter = omAnim.MFnGeometryFilter(mObject_deformer)
    mFnSet = om.MFnSet(mFnGeometryFilter.deformerSet())
    members = om.MSelectionList()
    components = om.MObject()
    dagPath = om.MDagPath()
    mFnSet.getMembers(members, False)
    for i in range(members.length()):
        mObject = om.MObject()
        members.getDependNode(i, mObject)
        if mObject_shape == mObject:
            members.getDagPath(i, dagPath, components)
            break

    mit = om.MItGeometry(dagPath, components)
    index_list = []
    while not mit.isDone():
        index_list.append(mit.index())
        next(mit)

    mFnWeight = omAnim.MFnWeightGeometryFilter(mObject_deformer)
    mFloatArray = om.MFloatArray()
    mFnWeight.getWeights(shape_logical_index, components, mFloatArray)
    return {i:w for i, w in zip(index_list, mFloatArray)}


def get_weightList(mObj_deformer_node, mObject_shape, weightListPlug, componentCount=None):
    """
    This gets a non-scarce list of weight value used by the given shape for the given weight plug on the given deformer.
    """
    mFnGeometryFilter = om2Anim.mFnGeometryFilter(mObj_deformer_node)
    shape_logical_index = mFnGeometryFilter.indexForOutputShape(mObject_shape)
    weights_mPlug = weightListPlug.elementByLogicalIndex(shape_logical_index).child(0)
    return [ weights_mPlug.elementByLogicalIndex(comp_index).asFloat() for comp_index in range(componentCount) ]