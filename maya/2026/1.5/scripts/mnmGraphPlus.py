''' -----------------------------------------------------------------------

                        NODE EDITOR PLUS TOOLS

-------------------------------------------------------------------------'''

import os
import time
import __main__

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om2

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
        from shiboken2 import wrapInstance
    except ImportError:          # batch / no GUI
        QtCore = QtGui = QtWidgets = wrapInstance = None


# GET UNIQUE NAME
def mauGetName(node):
    all = cmds.ls(node + '*')
    return len(all)


# TURN THE SELECTED NODES STATE ON OR OFF
def mauState(dir, ui):
    sel = cmds.ls(sl=True)
    for s in sel:
        cmds.setAttr(s + '.nodeState', dir)
    mauStateCheckUI(ui)


# TURN THE SELECTED NODES INTERMEDIATE
def mauInter(dir, ui):
    sel = cmds.ls(sl=True)
    for s in sel:
        if cmds.attributeQuery('intermediateObject', n=s, ex=True):
            cmds.setAttr(s + '.intermediateObject', dir)
    mauInterCheckUI(ui)


# TOGGLE AN ATTRIBUTE ON OR OFF OF THE SELCTED NODES
def mauTattr(attr, ui):
    sel = cmds.ls(sl=True)
    for s in sel:
        if cmds.attributeQuery(attr, n=s, ex=True):
            if cmds.getAttr(s + '.' + attr) == 1:
                cmds.setAttr(s + '.' + attr, 0)
            else:
                cmds.setAttr(s + '.' + attr, 1)
    if attr == 'intermediateObject':
        mauInterCheckUI(ui)
    elif attr == 'nodeState':
        mauStateCheckUI(ui)


# --------------------------------------------------------------------------- shared helpers
def _aq(node, attr, **kw):
    """attributeQuery that returns None instead of raising."""
    try:
        return cmds.attributeQuery(attr, node=node, **kw)
    except (RuntimeError, TypeError, ValueError):
        return None


def _driver_and_targets(node1, node2, what):
    """First node drives, every other node is a target. Works from args or selection."""
    if node1 and node2:
        return node1, [node2] if isinstance(node2, str) else list(node2)
    sel = cmds.ls(sl=True)
    if len(sel) < 2:
        cmds.warning('{}: select the source first, then one or more targets'.format(what))
        return None, []
    return sel[0], sel[1:]


def _report(title, report):
    """Print a readable summary and show a short in-view message."""
    print('\n// ---- {} ----'.format(title))
    for src, dst in report['connected']:
        print('   {}  --->>>  {}'.format(src, dst))
    for src, dst, old in report['replaced']:
        print('   {}  --->>>  {}   (replaced {})'.format(src, dst, old))
    for plug, why in report['skipped']:
        print('   skipped {}: {}'.format(plug, why))
    done = len(report['connected']) + len(report['replaced'])
    msg = '<hl>{}</hl> connected'.format(done)
    if report['replaced']:
        msg += ' ({} replaced)'.format(len(report['replaced']))
    if report['skipped']:
        msg += ', {} skipped (see Script Editor)'.format(len(report['skipped']))
    cmds.inViewMessage(amg='{}: {}'.format(title, msg), pos='botCenter', fade=True)
    if not done:
        cmds.warning('{}: nothing connected, see the Script Editor for why'.format(title))


def _new_report():
    return {'connected': [], 'replaced': [], 'skipped': []}


def _connect(src, dst, report, force=True):
    """Connect src -> dst, filling the report. Returns True when connected."""
    try:
        if cmds.isConnected(src, dst):
            report['skipped'].append((dst, 'already connected to ' + src))
            return False
    except RuntimeError:
        pass
    old = cmds.listConnections(dst, s=True, d=False, p=True, scn=True) or []
    if old and not force:
        report['skipped'].append((dst, 'already driven by ' + old[0]))
        return False
    try:
        cmds.connectAttr(src, dst, f=True)
    except RuntimeError as e:
        report['skipped'].append((dst, str(e).strip() or 'connection refused'))
        return False
    if old:
        report['replaced'].append((src, dst, old[0]))
    else:
        report['connected'].append((src, dst))
    return True


def _channelbox_attrs():
    """Attributes selected in any section of the Channel Box."""
    try:
        cb = mel.eval('global string $gChannelBoxName; $temp=$gChannelBoxName;')
    except RuntimeError:
        return []
    out = []
    for flag in ('sma', 'ssa', 'sha', 'soa'):
        try:
            out += cmds.channelBox(cb, q=True, **{flag: True}) or []
        except (RuntimeError, TypeError):
            pass
    return out


# CONNECT MATCHING ATTRIBUTES FROM ONE NODE TO OTHERS
def mauAttrConnector(node1=None, node2=None, attrs=None, force=True, unlock=False):
    """Connect same-named attributes from a driver node to one or more targets.

    Select the driver first, then one or more targets (or pass node1 / node2;
    node2 can be a list). Attributes, first match wins:
      1. 'attrs' argument
      2. attributes selected in the Channel Box (any section)
      3. every keyable attribute of the driver

    Nodes don't need to be the same type: attributes are matched by name, and
    anything the target doesn't have is skipped and reported.
      force=True   replace an existing incoming connection on the target
      unlock=True  unlock locked target attributes instead of skipping them
    Returns a report dict: connected / replaced / skipped.
    """
    driver, targets = _driver_and_targets(node1, node2, 'Attr Connector')
    if not driver:
        return _new_report()

    wanted = attrs or _channelbox_attrs() or cmds.listAttr(driver, k=True) or []
    report = _new_report()

    # long names, valid on the driver, no duplicates (tx + translateX)
    names = []
    for a in wanted:
        long_name = _aq(driver, a, longName=True)
        if not long_name:
            report['skipped'].append(('{}.{}'.format(driver, a), 'not on the driver'))
        elif long_name not in names:
            names.append(long_name)
    # a connected compound already drives its children
    listed = set(names)
    names = [a for a in names
             if not (_aq(driver, a, listParent=True) or [None])[0] in listed]

    cmds.undoInfo(openChunk=True, chunkName='mauAttrConnector')
    try:
        for target in targets:
            if cmds.ls(target, long=True) == cmds.ls(driver, long=True):
                report['skipped'].append((target, 'same node as the driver'))
                continue
            if cmds.nodeType(target) != cmds.nodeType(driver):
                print('// Attr Connector: {} ({}) -> {} ({}), matching by name'.format(
                    driver, cmds.nodeType(driver), target, cmds.nodeType(target)))
            for a in names:
                src, dst = '{}.{}'.format(driver, a), '{}.{}'.format(target, a)
                if not _aq(driver, a, readable=True):
                    report['skipped'].append((src, 'not readable'))
                    continue
                if _aq(driver, a, multi=True):
                    report['skipped'].append((src, 'array attribute, connect it by index'))
                    continue
                if not _aq(target, a, exists=True):
                    report['skipped'].append((dst, 'missing on target'))
                    continue
                if not _aq(target, a, writable=True):
                    report['skipped'].append((dst, 'not writable'))
                    continue
                if cmds.getAttr(dst, lock=True):
                    if not unlock:
                        report['skipped'].append((dst, 'locked (use unlock=True)'))
                        continue
                    cmds.setAttr(dst, lock=False)
                _connect(src, dst, report, force)
    finally:
        cmds.undoInfo(closeChunk=True)

    _report('Attr Connector', report)
    return report


# CONNECT THE GEOMETRY (OR COMPONENTS) OF ONE NODE TO OTHERS
GEO_OUT = ['worldMesh', 'outMesh', 'worldSpace', 'local', 'outputGeometry', 'outGeometry',
           'outputMesh', 'outMeshes', 'outputCurve', 'outCurve', 'outputSurface', 'output']
GEO_IN = ['inMesh', 'create', 'inputPolymesh', 'inputGeometry', 'inGeometry', 'inputMesh',
          'inputCurve', 'inputSurface', 'inputPoly', 'input']
GEO_TYPES = {'mesh', 'nurbsCurve', 'nurbsSurface', 'subdiv', 'lattice',
             'geometry', 'Nothing', 'TdataCompound', ''}
COMP_PAIRS = [('outComponents', ['inComponents', 'inputComponents']),
              ('groupId', ['groupId', 'inGroupId'])]


def _geo_shape(node):
    """Transforms are replaced by their first visible (non-intermediate) shape."""
    if 'transform' in (cmds.nodeType(node, inherited=True) or []):
        shapes = cmds.listRelatives(node, s=True, ni=True, pa=True) or []
        if shapes:
            return shapes[0]
    return node


def _is_deformer(node):
    return 'geometryFilter' in (cmds.nodeType(node, inherited=True) or [])


def _plug_type(plug):
    try:
        return cmds.getAttr(plug, type=True) or ''
    except (RuntimeError, ValueError):
        return ''


def _multi_indices(plug):
    try:
        return cmds.getAttr(plug, multiIndices=True) or []
    except (RuntimeError, ValueError):
        return []


def _free_index(node, attr, child=None):
    """First index whose plug (or child plug) has no incoming connection."""
    idx = _multi_indices('{}.{}'.format(node, attr))
    for i in idx:
        plug = '{}.{}[{}]'.format(node, attr, i) + ('.' + child if child else '')
        if not cmds.listConnections(plug, s=True, d=False):
            return i
    return max(idx) + 1 if idx else 0


def _geo_out_plugs(node):
    """Geometry output plugs of a node, best first."""
    plugs = []
    for a in GEO_OUT:
        if not _aq(node, a, exists=True) or not _aq(node, a, readable=True):
            continue
        if _aq(node, a, multi=True):
            idx = _multi_indices('{}.{}'.format(node, a)) or [0]
            plug = '{}.{}[{}]'.format(node, a, idx[0])
        else:
            plug = '{}.{}'.format(node, a)
        if _plug_type(plug) in GEO_TYPES:
            plugs.append(plug)
    return plugs


def _geo_in_plugs(node):
    """Geometry input plugs of a node, best first (next free index for multis)."""
    if _is_deformer(node):
        return ['{}.input[{}].inputGeometry'.format(node, _free_index(node, 'input', 'inputGeometry'))]
    plugs = []
    for a in GEO_IN:
        if not _aq(node, a, exists=True) or not _aq(node, a, writable=True):
            continue
        if _aq(node, a, multi=True):
            plug = '{}.{}[{}]'.format(node, a, _free_index(node, a))
        else:
            plug = '{}.{}'.format(node, a)
        if _plug_type(plug) in GEO_TYPES:
            plugs.append(plug)
    return plugs


def _comp_in_plugs(node, out_attr, in_attrs):
    if out_attr == 'groupId' and _is_deformer(node):
        return ['{}.input[{}].groupId'.format(node, _free_index(node, 'input', 'groupId'))]
    plugs = []
    for a in in_attrs:
        if _aq(node, a, exists=True) and _aq(node, a, writable=True):
            if _aq(node, a, multi=True):
                plugs.append('{}.{}[{}]'.format(node, a, _free_index(node, a)))
            else:
                plugs.append('{}.{}'.format(node, a))
    return plugs


def mauMeshConnector(node1=None, node2=None, dir=0, force=True):
    """Connect geometry (dir=0) or components / groupId (dir=1) from one node to others.

    Select the source first, then one or more targets (or pass node1 / node2;
    node2 can be a list). Transforms are replaced by their visible shape.

    dir=0  finds the best geometry output on the source (worldMesh, outMesh,
           worldSpace, outputGeometry[i], output...) and the first input on the
           target that accepts it (inMesh, create, inputPolymesh, deformer
           input[next free].inputGeometry, inputPoly[next free]...). Data types
           are checked, so a mesh never goes into a curve's create.
    dir=1  outComponents -> inComponents / inputComponents,
           groupId -> groupId / inGroupId / deformer input[next free].groupId
    Returns a report dict: connected / replaced / skipped.
    """
    title = 'Mesh Connector' if dir == 0 else 'Component Connector'
    source, targets = _driver_and_targets(node1, node2, title)
    if not source:
        return _new_report()
    source = _geo_shape(source)
    report = _new_report()

    cmds.undoInfo(openChunk=True, chunkName='mauMeshConnector')
    try:
        for target in targets:
            target = _geo_shape(target)
            if target == source:
                report['skipped'].append((target, 'same node as the source'))
                continue

            if dir == 0:
                outs, ins = _geo_out_plugs(source), _geo_in_plugs(target)
                if not outs:
                    report['skipped'].append((source, 'no geometry output found'))
                    break
                if not ins:
                    report['skipped'].append((target, 'no geometry input found'))
                    continue
                if any(cmds.isConnected(o, i) for o in outs for i in ins):
                    report['skipped'].append((target, 'already connected to ' + source))
                    continue
                done, errors = False, []
                for out_plug in outs:
                    for in_plug in ins:
                        trial = _new_report()
                        if _connect(out_plug, in_plug, trial, force):
                            report['connected'] += trial['connected']
                            report['replaced'] += trial['replaced']
                            done = True
                            break
                        errors += trial['skipped']
                    if done:
                        break
                if not done:
                    report['skipped'].append(
                        (target, 'no compatible geometry plugs ({})'.format(
                            errors[-1][1] if errors else 'unknown')))
            else:
                found = False
                for out_attr, in_attrs in COMP_PAIRS:
                    if not _aq(source, out_attr, exists=True):
                        continue
                    found = True
                    src_plug = '{}.{}'.format(source, out_attr)
                    ins = _comp_in_plugs(target, out_attr, in_attrs)
                    if not ins:
                        report['skipped'].append((target, 'no input for ' + out_attr))
                        continue
                    for in_plug in ins:
                        if _connect(src_plug, in_plug, report, force):
                            break
                if not found:
                    report['skipped'].append((source, 'no outComponents / groupId'))
    finally:
        cmds.undoInfo(closeChunk=True)

    _report(title, report)
    return report


# SWAP CONNECTED NODES FROM THE FIRST TO THE LAST NODE
def _long_name(node):
    found = cmds.ls(node, long=True)
    return found[0] if found else node


def swapConnections(src=None, swap=None, dest=None, clean=False):
    """Move the connections between the middle nodes and the FIRST node to the LAST node.

    Select: first node, one or more middle nodes, last node.
    First and last must be the same node type (e.g. two meshes, two skinClusters).

      first.attr  -> middle.plug   becomes   last.attr -> middle.plug
      middle.plug -> first.attr    also gets middle.plug -> last.attr
                                   (clean=True removes the old link to the first node)

    Can also be called directly: swapConnections('oldMesh', ['skinCluster1'], 'newMesh')
    """
    if src and dest:
        middles = [swap] if isinstance(swap, str) else list(swap or [])
    else:
        sel = cmds.ls(sl=True)
        if len(sel) < 3:
            cmds.warning('Select at least 3 nodes: first, middle node(s), last. '
                         'First and last must be the same type')
            return 0
        src, middles, dest = sel[0], sel[1:-1], sel[-1]

    if not middles:
        cmds.warning('swapConnections: no middle node to remap')
        return 0
    if cmds.nodeType(src) != cmds.nodeType(dest):
        cmds.warning('The first and last selection need to be the same node type '
                     '({} vs {})'.format(cmds.nodeType(src), cmds.nodeType(dest)))
        return 0

    src_long = _long_name(src)
    moved = 0
    cmds.undoInfo(openChunk=True, chunkName='swapConnections')
    try:
        for mid in middles:
            # ---- inputs of the middle node coming from the first node
            conns = cmds.listConnections(mid, s=True, d=False, p=True, c=True,
                                         scn=True) or []
            for mid_plug, src_plug in zip(conns[::2], conns[1::2]):
                node, attr = src_plug.split('.', 1)
                if _long_name(node) != src_long:
                    continue
                new_plug = '{}.{}'.format(dest, attr)
                try:
                    # an input can only have one source: forcing replaces the old link
                    cmds.connectAttr(new_plug, mid_plug, f=True)
                except RuntimeError as e:
                    cmds.warning('Skipped {} -> {}: {}'.format(new_plug, mid_plug, e))
                    continue
                print('{}  <<<---  {}   (was {})'.format(mid_plug, new_plug, src_plug))
                moved += 1

            # ---- outputs of the middle node going into the first node
            conns = cmds.listConnections(mid, s=False, d=True, p=True, c=True,
                                         scn=True) or []
            for mid_plug, src_plug in zip(conns[::2], conns[1::2]):
                node, attr = src_plug.split('.', 1)
                if _long_name(node) != src_long:
                    continue
                new_plug = '{}.{}'.format(dest, attr)
                try:
                    if not cmds.isConnected(mid_plug, new_plug):
                        cmds.connectAttr(mid_plug, new_plug, f=True)
                except RuntimeError as e:
                    cmds.warning('Skipped {} -> {}: {}'.format(mid_plug, new_plug, e))
                    continue
                print('{}  --->>>  {}'.format(mid_plug, new_plug))
                moved += 1
                if clean:
                    # the real source may be a unitConversion between the two nodes
                    for real_src in cmds.listConnections(src_plug, s=True, d=False, p=True) or []:
                        try:
                            cmds.disconnectAttr(real_src, src_plug)
                            print('   disconnected {} -> {}'.format(real_src, src_plug))
                        except RuntimeError:
                            pass
    finally:
        cmds.undoInfo(closeChunk=True)

    if moved:
        cmds.inViewMessage(
            amg='Swapped <hl>{}</hl> connection(s): {} → {}'.format(moved, src, dest),
            pos='botCenter', fade=True)
    else:
        cmds.warning('No connections between {} and {} found to swap'.format(
            ', '.join(middles), src))
    return moved


# CLEAN THE GRAPH WITH MY PERSONAL SETTINGS
def mauCleanNE():
    list = []
    current = cmds.ls(sl=True)
    cmds.select(cl=True)
    remove = [
        'shadingEngine',
        'objectSet',
        'hyperLayout',
        'hyperView',
        'hyperGraphInfo',
        'renderLayer',
        'renderLayerManager',
        'displayLayer',
        'displayLayerManager',
        'script',
        'nodeGraphEditorInfo',
        'time',
        'timeToUnitConversion',
        'colorManagementGlobals'
    ]
    # ned = cmds.getPanel(wf=True) + 'NodeEditorEd'
    ned = ''
    for p in cmds.getPanel(all=True):
        if 'nodeEditorPane' in p:
            ned = p + 'NodeEditorEd'
            if ned:
                nodes = cmds.nodeEditor(ned, q=True, gnl=True)
                if nodes:
                    for n in nodes:
                        for rem in remove:
                            if cmds.nodeType(n) == rem:
                                list.append(n)
                    for l in list:
                        cmds.nodeEditor(ned, e=True, rem=l)
                    cmds.nodeEditor(ned, e=True, fa=True, lay=True)
    cmds.select(cl=True)
    if current:
        cmds.select(current)


# CLEAN ALL THE UPSTREAM OR DOWNSTREAM NODES FROM SELECTED ONE
def mauForBackNed(dir):
    ned = ''
    current = cmds.ls(sl=True)
    for p in cmds.getPanel(all=True):
        if 'nodeEditorPane' in p:
            ned = p + 'NodeEditorEd'
            if ned:
                if dir == 0:
                    cmds.nodeEditor(ned, e=True, ru=True)
                elif dir == 1:
                    cmds.nodeEditor(ned, e=True, rd=True)
    if current:
        cmds.select(current, r=True)


# CLEAN ALL THE NODES PASSED TO THE FUCTION IN THE GRAPH
def mauNodeCleanNE(node):
    list = []
    ned = cmds.getPanel(wf=True) + 'NodeEditorEd'
    if ned:
        nodes = cmds.nodeEditor(ned, q=True, gnl=True)
        if nodes:
            for n in nodes:
                if cmds.nodeType(n) == node:
                    list.append(n)
                    if node == 'follicle':
                        tr = cmds.listConnections(
                            n + '.outTranslate', d=True, s=False)
                        if tr:
                            list.append(tr[0])
            for l in list:
                cmds.nodeEditor(ned, e=True, rem=l)


# CLEAN ALL THE GROUPIDS IN THE GRAPH
def mauGroupIdNE():
    list = []
    ned = cmds.getPanel(wf=True) + 'NodeEditorEd'
    if ned:
        nodes = cmds.nodeEditor(ned, q=True, gnl=True)
        if nodes:
            for n in nodes:
                if cmds.nodeType(n) == 'groupId':
                    list.append(n)
            for l in list:
                cmds.nodeEditor(ned, e=True, rem=l)


def mauSelSkJnts():
    allJ = []
    sel = cmds.ls(sl=True)
    if sel:
        for s in sel:
            if cmds.nodeType(s) == 'skinCluster':
                jnts = cmds.skinCluster(s, q=True, inf=True)
                for j in jnts:
                    allJ.append(j)
    if allJ:
        cmds.select(allJ, r=True)


# CLEAN ALL THE JOINTS ATTACHED TO A SKINCLUSTER IN THE GRAPH
def mauCleanSkinNE():
    list = []
    ned = cmds.getPanel(wf=True) + 'NodeEditorEd'
    if ned:
        nodes = cmds.nodeEditor(ned, q=True, gnl=True)
        if nodes:
            for n in nodes:
                if cmds.nodeType(n) == 'skinCluster':
                    maj = cmds.listConnections(n + '.matrix')
                    coj = cmds.listConnections(n + '.influenceColor')
                    for m in maj:
                        list.append(m)
                    if coj:
                        for c in coj:
                            list.append(c)
            for l in list:
                cmds.nodeEditor(ned, e=True, rem=l)


# CLEAN ALL THE JOINTS ATTACHED TO THE SELECTED SKINCLUSTER
def mauSkinClusterClean():
    # Select the skinCluster to that has the vidible joints in the nodeEditor
    list = []
    sel = cmds.ls(sl=True)
    cmds.select(cl=True)
    if not sel:
        cmds.confirmDialog(t='Error', m='Select a skinCluster node')
        return
    for s in sel:
        if cmds.nodeType(s) == 'skinCluster':
            maj = cmds.listConnections(s + '.matrix')
            coj = cmds.listConnections(s + '.influenceColor')
            for m in maj:
                list.append(m)
            for c in coj:
                list.append(c)
        else:
            print(
                'Skipping {0} because it is not a skinCluster node'.format(s))
    ned = cmds.getPanel(wf=True) + 'NodeEditorEd'
    if ned:
        for l in list:
            cmds.nodeEditor(ned, e=True, rem=l)


# MAKE A CLEAN SEPARATION OF A MESH
def mauSeaparate(dir):
    sel = cmds.ls(type='mesh', sl=True)
    if not sel:
        cmds.confirmDialog(m='please Select a mesh shape')
        return
    top = cmds.listRelatives(sel[0], p=True)
    sepa = cmds.polySeparate(sel[0])
    if not sepa:
        cmds.confirmDialog(m='This mesh is not separated')
        return
    for s in sepa:
        sh = cmds.listRelatives(s, s=True)
        if sh:
            topN = cmds.listRelatives(sh[0], p=True)
            cmds.setAttr(sh[0] + '.intermediateObject', 0)
            if dir == 1:
                index = cmds.ls(sh[0].replace('Shape', '_NULL') + '*')
                tr = cmds.createNode(
                    'transform',
                    n=sh[0] + '_NULL' + str(len(index)))
                top.append(tr)
            cmds.parent(sh[0], top[-1], r=True, s=True)
            cmds.delete(topN)
    cmds.setAttr(sel[0] + '.intermediateObject', 0)
    # CLEAN NEW TRANSFORM FORM THE ORIG MESH
    topN = cmds.listRelatives(sel[0], p=True)
    cmds.parent(sel[0], top[0], r=True, s=True)
    cmds.delete(topN)
    # CLEAN UP
    conn = cmds.listConnections(sepa[-1] + '.output')
    # cmds.rename(sepa[-1], sel[0].replace('Shape'+sel[0][-1], '_PS'))
    if conn:
        for c in conn:
            if cmds.nodeType(c) == 'groupParts':
                cmds.delete(c)
    return sepa


# UNITE ONE OR MORE MESH SHAPE TO A SINGLE ONE WITH THE POLYUNITE NODE
def mauUnite(dir):
    sel = cmds.ls(type='mesh', sl=True)
    if not sel:
        cmds.confirmDialog(m='please Select at least one mesh shape')
        return
    fath = cmds.listRelatives(sel[0], p=True)
    unite = cmds.createNode(
        'polyUnite',
        n=sel[0].replace('Shape' + sel[0][-1], '_UNI')
    )
    i = 0
    for s in sel:
        cmds.connectAttr(
            s + '.worldMatrix[0]', unite + '.inputMat[' + str(i) + ']')
        cmds.connectAttr(
            s + '.worldMesh[0]', unite + '.inputPoly[' + str(i) + ']')
        i = i + 1
    endMesh = cmds.createNode('mesh')
    endMeshT = cmds.listRelatives(endMesh, p=True)[0]
    cmds.connectAttr(unite + '.output', endMesh + '.inMesh')
    if dir == 1:
        fathN = cmds.listRelatives(endMesh, p=True)
        cmds.parent(endMesh, fath[0], r=True, s=True)
        cmds.delete(fathN)
    return unite, endMesh, endMeshT


# BRANCH OFF A NEW SHAPE FROM THE SELECTED NODES
def mauSh(node, kind):
    # Select the node to outPut from
    # and then optionally the transform to parent the shape under
    attr = [
        'outMesh',
        'outGeometry',
        'output',
        'outputGeometry',
        'outputCurve',
        'worldSpace'
    ]
    sel = cmds.ls(sl=True)
    if sel:
        if cmds.nodeType(sel[-1]) != 'transform':
            # index = mauGetName(sel[0].replace('Shape', ''))
            # tr = cmds.createNode(
            #     'transform',
            #     n=sel[0].replace('Shape', '') + str(index) + '_null')
            tr = cmds.createNode('transform')
            sel.append(tr)
    for n in node:
        for a in attr:
            if cmds.attributeQuery(a, n=n, ex=True):
                # index = mauGetName(n)
                # shape = cmds.createNode(
                #     kind,
                #     n=n.replace('Shape', '') + str(index) + 'Shape'
                # )
                shape = cmds.createNode(kind)
                father = cmds.listRelatives(shape, p=True)
                if a == 'outputGeometry' or a == 'worldSpace':
                    if kind == 'mesh':
                        cmds.connectAttr(
                            n + '.' + a + '[0]', shape + '.inMesh')
                    elif kind == 'nurbsCurve' or kind == 'nurbsSurface':
                        cmds.connectAttr(
                            n + '.' + a + '[0]', shape + '.create')
                else:
                    if kind == 'mesh':
                        cmds.connectAttr(n + '.' + a, shape + '.inMesh')
                    elif kind == 'nurbsCurve' or kind == 'nurbsSurface':
                        cmds.connectAttr(n + '.' + a, shape + '.create')
                cmds.parent(shape, sel[-1], r=True, s=True)
                cmds.delete(father[0])


def mauCreateSh():
    node = ''
    sel = cmds.ls(sl=True)
    if not sel:
        node = cmds.createNode('mesh')
        print(node + ' created')
    else:
        attrs = ['worldMesh[0]', 'outputGeometry[0]', 'outGeometry']
        node = cmds.createNode('mesh')
        for a in attrs:
            try:
                cmds.connectAttr(sel[0] + '.' + a, node + '.inMesh', f=True)
                print(node + ' created and connected to ' + sel[0])
            except:
                print('Skipping this attribute' + a)

    # ADD IT TO THE GRAPH
    for p in cmds.getPanel(all=True):
        if 'nodeEditorPane' in p:
            ned = p + 'NodeEditorEd'
            if ned:
                cmds.nodeEditor(ned, e=True, addNode=node)


# PARENT TRHE SELECTED SHAPES UPDATE THE LAST SELECTED TRANSFORM
def mParentSh():
    sel = cmds.ls(sl=1)
    if not sel:
        cmds.confirmDialog(
            t='Error',
            m='Please select some shapes and last a transform')
        return
    if cmds.nodeType(sel[-1]) != 'transform':
        cmds.confirmDialog(
            t='Error',
            m='Please select some shapes and last a transform')
        return
    for s in sel:
        if s is not sel[-1]:
            cmds.parent(s, sel[-1], r=True, s=True)
            print('{0} parent to {1}'.format(s, sel[-1]))
    cmds.select(cl=True)


# DRIVE ISOLATE VIEWPORT FROM NODE EDITOR
def mauIsolate(dir):
    sel = cmds.ls(sl=True)
    cPanel = cmds.getPanel(vis=True)
    for eP in cPanel:
        # eP = cmds.paneLayout('viewPanes', q=True, pane1=True)
        panelType = cmds.getPanel(to=eP)
        if panelType == 'modelPanel':
            # ISOLATE THE CURRENT SELECTION
            if dir == 0:
                if cmds.isolateSelect(eP, q=True, s=True) == 0:
                    cmds.isolateSelect(eP, s=1)
                    cmds.isolateSelect(eP, addSelected=True)
                else:
                    if len(sel) == 0:
                        cmds.isolateSelect(eP, s=0)
                    else:
                        cmds.isolateSelect(eP, s=1)
                        cmds.isolateSelect(eP, addSelected=True)

            # ADD THE CURRENT SELECTION TO THE ACTIVE ISOLATION
            if dir == 1:
                if cmds.isolateSelect(eP, q=True, s=True) == 1:
                    cmds.isolateSelect(eP, addSelected=True)

            # REMOVE THE CURRENT SELECTION TO THE ACTIVE ISOLATION
            if dir == 2:
                if cmds.isolateSelect(eP, q=True, s=True) == 1:
                    cmds.isolateSelect(eP, rs=True)


# ADD SELECTION TO SELECTED GROUP NODE
def mauGroupAddSel():
    out = ''
    sel = cmds.ls(sl=True, fl=True)
    if cmds.nodeType(sel[0]) == 'group':
        for s in sel:
            name = s.split('[')[-1].replace(']', '')
            if s != sel[0]:
                if s != sel[-1]:
                    out += name + ' '
                else:
                    out += name
        print(out)
        cmds.setAttr(sel[0] + '.pattern', out, type='string')
    else:
        cmds.warning(
            'Make sure to select a group node first, then some components')


def mauGroupCreate():
    node = ''
    sel = cmds.ls(sl=True, fl=True)
    if not sel:
        node = cmds.createNode('group')
        print('Made Group ' + node)
    else:
        if cmds.nodeType(sel[0]) == 'mesh':
            node = cmds.createNode('group')
            cmds.connectAttr(
                sel[0] + '.worldMesh[0]', node + '.inGeometry', f=True)
            print('Made Group ' + node + ' and connected to ' + sel[0])
        else:
            node = cmds.createNode('group')
            print('Made Group ' + node)

    # ADD IT TO THE GRAPH
    for p in cmds.getPanel(all=True):
        if 'nodeEditorPane' in p:
            ned = p + 'NodeEditorEd'
            if ned:
                cmds.nodeEditor(ned, e=True, addNode=node)

# GET SELECTION OF SELECTED GROUP NODE


def mauGetPatterSelection():
    sel = cmds.ls(sl=True, fl=True)
    if cmds.nodeType(sel[0]) == 'group':
        comp, mesh = '', []
        tipo = cmds.getAttr(sel[0] + '.componentType')
        if tipo == 0:
            comp = 'vtx'
        elif tipo == 1:
            comp = 'e'
        try:
            if not sel[1]:
                mesh = cmds.listConnections(sel[0] + '.inGeometry')
            else:
                if cmds.nodeType(sel[1]) == 'mesh':
                    mesh.append(sel[1])
                else:
                    cmds.warning(
                        'Please make sure the secon selecion is a meshShape')
        except:
            mesh = cmds.listConnections(sel[0] + '.inGeometry')
        components = cmds.getAttr(sel[0] + '.pattern').split(' ')
        cmds.select(sel[0], r=True)
        for c in components:
            cmds.select(mesh[0] + '.' + comp + '[' + str(c) + ']', add=True)
    else:
        cmds.warning('Make sure to select a group node first')

# MAKE A SOUP GROUP TO THE DEFORMER AND CLEAN THE MAYA ONE


def mauGRP():
    # select the orig mesh and then the deformer
    nodes = cmds.ls(sl=True)
    if len(nodes) < 1:
        cmds.confirmDialog(
            m='please Select the orig mesh and the deformer node')
        return
    grp = cmds.createNode('group')
    if cmds.attributeQuery('worldMesh', n=nodes[0], ex=True):
        cmds.connectAttr(
            nodes[0] + '.worldMesh[0]', grp + '.inGeometry', f=True
        )
    elif cmds.attributeQuery('output', n=nodes[0], ex=True):
        cmds.connectAttr(nodes[0] + '.output', grp + '.inGeometry', f=True)
    elif cmds.attributeQuery('outMesh', n=nodes[0], ex=True):
        cmds.connectAttr(nodes[0] + '.outMesh[0]', grp + '.inGeometry', f=True)
    cmds.refresh()

    cmds.setAttr(grp + '.invert', 1)
    cmds.setAttr(grp + '.outputObjectGroup', 1)
    grpID = cmds.createNode('groupId')
    cmds.connectAttr(grpID + '.groupId', grp + '.groupId', f=True)
    cmds.refresh()
    cmds.select(grpID)
    # CLEAN UP
    headMesh = cmds.listConnections(nodes[1] + '.outputGeometry[0]', p=1)
    cmds.delete(
        cmds.listConnections(headMesh[0].split('.')[0] + '.tweakLocation'))
    cmds.delete(
        cmds.listConnections(
            headMesh[0].split('.')[0] + '.instObjGroups[0].objectGroups[0]'))
    cmds.refresh()
    cmds.connectAttr(
        grp + '.outGeometry',
        nodes[1] + '.input[0].inputGeometry',
        f=True)
    cmds.refresh()
    cmds.connectAttr(
        grpID + '.groupId',
        nodes[1] + '.input[0].groupId',
        f=True)


# DUPLICATE THE GRAP H AND SPLIT IT AT THE BEGINNING
def mauDupChain():
    sel = cmds.ls(sl=True)  # Selected shape
    if cmds.nodeType(sel[0]) != 'mesh':
        cmds.warning('Select a mesh shape')
        return
    dup = cmds.duplicate(sel[0], un=True)  # duplicate the structure
    trans = cmds.listRelatives(sel[0], p=True)  # get transform of the shape
    sh = cmds.listRelatives(trans[0], s=True)  # get all the shapes of the node
    # get all the shapes of the duplicate node
    sh2 = cmds.listRelatives(dup[0], s=True)
    # get orig shape of the duplicated node
    conn = cmds.listConnections(sh2[-1], s=False, d=True)
    # connect the orig mesh to the duplicated deformation stack
    cmds.connectAttr(
        sh[-1] + '.worldMesh[0]', conn[0] + '.inputGeometry', f=True)
    # parent the duplicated shape to the original transform
    cmds.parent(sh2[0], trans[0], r=True, s=True)
    cmds.delete(dup[0])  # delete the original transform


''' --------------------------------------------------------------------------

                        COMMAND HELPERS
    Buttons and menus use Python callables instead of command strings, so they
    don't depend on 'mnmGraphPlus' being imported in the Script Editor, and they
    always call the latest version of the module after a reload.

----------------------------------------------------------------------------'''


def _call(func, *args):
    import mnmGraphPlus as m
    return getattr(m, func)(*args)


def _cmd(func, *args):
    return lambda *_: _call(func, *args)


def _with_selection(func, *extra):
    return lambda *_: _call(func, cmds.ls(sl=True), *extra)


def _with_two(func, *extra):
    def run(*_):
        sel = cmds.ls(sl=True)
        if len(sel) < 2:
            cmds.warning('Select two nodes')
            return
        _call(func, sel[0], sel[1], *extra)
    return run


def _main_exec(code):
    """Run code in the Script Editor namespace (for external tools like SOuP)."""
    return lambda *_: exec(code, __import__('__main__').__dict__)


def _connector(*_):
    import mnmConnectPopUP
    mnmConnectPopUP.show()


def _clean_constraints(*_):
    for t in ('parentConstraint', 'pointConstraint', 'orientConstraint', 'scaleConstraint'):
        _call('mauNodeCleanNE', t)


''' --------------------------------------------------------------------------

                        GRAPH TOOLS
    Select connected nodes and pan the graph to them.

----------------------------------------------------------------------------'''


def _remove_old_auto_space():
    """Earlier versions had an auto-spacing feature with scene callbacks: make sure
    nothing from it is left running after this version is loaded or reloaded."""
    for key in ('_mnmGraphPlus_spaceCallbacks', '_mnmGraphPlus_connectionCb'):
        ids = __main__.__dict__.pop(key, None)
        if ids is None:
            continue
        for cb in (ids if isinstance(ids, (list, tuple)) else [ids]):
            try:
                om2.MMessage.removeCallback(cb)
            except Exception:
                pass
    for key in ('_mnmGraphPlus_spaceQueue', '_mnmGraphPlus_spaceRunner'):
        __main__.__dict__.pop(key, None)
    try:
        if cmds.optionVar(exists='mnmGraphPlus_autoSpace'):
            cmds.optionVar(remove='mnmGraphPlus_autoSpace')
    except Exception:
        pass


_remove_old_auto_space()


def _shown_nodes(ned):
    return set(cmds.ls(cmds.nodeEditor(ned, q=True, getNodeList=True) or []))


def _visible_editors():
    visible = set(cmds.getPanel(vis=True) or [])
    return [p + 'NodeEditorEd' for p in (cmds.getPanel(scriptType='nodeEditorPanel') or [])
            if p in visible and cmds.nodeEditor(p + 'NodeEditorEd', exists=True)]


def _graph_nodes():
    """Nodes shown in the visible Node Editor(s), or None when no editor is open."""
    editors = _visible_editors()
    if not editors:
        return None
    shown = set()
    for ned in editors:
        shown |= _shown_nodes(ned)
    return shown


def _connected_nodes(direction, only_graph=True):
    """Nodes connected to the selection. direction: 'in' = upstream, 'out' = downstream.
    only_graph: keep only the nodes shown in the Node Editor (all of them when no
    editor is open)."""
    sel = cmds.ls(sl=True) or []
    shown = _graph_nodes() if only_graph else None
    found = []
    for s in sel:
        for n in cmds.listConnections(s, s=(direction == 'in'), d=(direction == 'out'),
                                      scn=True) or []:
            name = (cmds.ls(n) or [n])[0]
            if name in found or name in sel:
                continue
            if shown is not None and name not in shown:
                continue
            found.append(name)
    return found


def _ned_view(ned):
    """QGraphicsView of the CURRENT tab of a Node Editor (pane > QStackedLayout > tab > view)."""
    if wrapInstance is None:
        return None
    ptr = omui.MQtUtil.findControl(ned)
    if not ptr:
        return None
    pane = wrapInstance(int(ptr), QtWidgets.QWidget)
    stack = pane.findChild(QtWidgets.QStackedLayout)
    if stack is not None and stack.currentWidget() is not None:
        view = stack.currentWidget().findChild(QtWidgets.QGraphicsView)
        if view is not None and view.scene() is not None:
            return view
    views = [v for v in pane.findChildren(QtWidgets.QGraphicsView)
             if v.scene() is not None and v.isVisible()]
    return views[0] if views else None


PAN_MS = 220        # length of the pan animation (0 = jump)
_PAN_KEY = '_mnmGraphPlus_panAnims'


def _pan_to(view, point):
    """Slide the view so 'point' (scene coords) ends up in the middle. Zoom is untouched."""
    start = view.mapToScene(view.viewport().rect().center())
    start = QtCore.QPointF(start)
    if PAN_MS <= 0:
        view.centerOn(point)
        return
    anim = QtCore.QVariantAnimation(view)
    anim.setStartValue(start)
    anim.setEndValue(QtCore.QPointF(point))
    anim.setDuration(PAN_MS)
    anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
    anim.valueChanged.connect(lambda v, w=view: w.centerOn(v))
    anims = __main__.__dict__.setdefault(_PAN_KEY, [])
    anims.append(anim)                                   # keep it alive while it runs
    anim.finished.connect(lambda a=anim: anims.remove(a) if a in anims else None)
    anim.start()


def _center_on_selected(ned, tries=3):
    """Once the graph shows the new selection, pan so it sits in the middle of the view.
    Maya pushes a selection into the graph on the next event-loop pass, hence the timer."""
    def do(left=tries):
        view = _ned_view(ned)
        if view is None:
            return
        items = list(view.scene().selectedItems())
        if not items:
            if left > 1:
                QtCore.QTimer.singleShot(80, lambda: do(left - 1))
            return
        rect = items[0].sceneBoundingRect()
        for it in items[1:]:
            rect = rect.united(it.sceneBoundingRect())
        _pan_to(view, rect.center())
    QtCore.QTimer.singleShot(60, do)


def mauSelectConnected(direction='out', center=True, frame=None):
    """Select the nodes connected to the selection that are SHOWN in the Node Editor,
    and pan the graph so they are in the middle. The graph is not rebuilt, no nodes
    are added and the zoom is kept.
    direction: 'out' = downstream (nodes receiving our outputs), 'in' = upstream.
    ('frame' is the old name of 'center' and is still accepted.)"""
    if frame is not None:
        center = frame
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning('Select a node first')
        return []
    found = _connected_nodes(direction)
    if not found:
        cmds.warning('No {} connections on {} in the Node Editor'.format(
            'outgoing' if direction == 'out' else 'incoming', ', '.join(sel)))
        return []
    cmds.select(found, r=True)
    if center and QtCore is not None:
        for ned in _visible_editors():
            _center_on_selected(ned)
    return found


''' --------------------------------------------------------------------------

                NODE EDITOR PLUS MENU ( CTRL + RIGHT CLICK )
    A styled popup at the mouse:  INPUTS on the left, OUTPUTS on the right,
    the preset tools in the middle.

----------------------------------------------------------------------------'''
MENU_TRANSPARENCY = 6        # 0 = solid ... 90
_MENU_KEY = '_mnmGraphPlus_presetMenu'
_FILTER_KEY = '_mnmGraphPlus_menuFilters'

MENU_STYLE = """
QFrame#panel { background: #24262b; border: 1px solid #3a3d44; border-radius: 12px; }
QLabel { color: #d7d9dd; }
QLabel#title { color: #7c828c; font-size: 10px; font-weight: bold; letter-spacing: 2px; }
QLabel#sel { color: #e6e6e6; font-weight: 600; }
QLabel#hint { color: #6f757e; font-size: 10px; }
QFrame#section { background: #1e2024; border: 1px solid #2f3238; border-radius: 8px; }
QLabel#secTitle { font-size: 10px; font-weight: bold; letter-spacing: 1px; padding: 2px 6px; }
QPushButton#item {
    background: transparent; border: none; color: #d7d9dd;
    text-align: left; padding: 4px 8px; border-radius: 5px;
}
QPushButton#item:hover { background: #2f3440; color: #ffffff; }
QPushButton#item[hot="true"] { background: #355bb8; color: #ffffff; }
QPushButton#item[running="true"] { background: #2f9e5b; color: #ffffff; }
QPushButton#sideIn, QPushButton#sideOut {
    border: none; border-radius: 10px; color: #ffffff;
    font-weight: bold; font-size: 12px; padding: 10px 6px;
}
QPushButton#sideIn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3566e0, stop:1 #26334f);
}
QPushButton#sideIn:hover { background: #3f74f5; }
QPushButton#sideOut {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f3420, stop:1 #db7d30);
}
QPushButton#sideOut:hover { background: #f08c3c; }
QPushButton#sideIn[hot="true"] { background: #4d82ff; }
QPushButton#sideOut[hot="true"] { background: #ff9a4a; }
QPushButton#sideIn[running="true"], QPushButton#sideOut[running="true"] { background: #2f9e5b; }
QPushButton#sideIn:disabled, QPushButton#sideOut:disabled { background: #2a2c31; color: #5b6068; }
QToolTip { background: #1b1d21; color: #e6e6e6; border: 1px solid #3a3d44; padding: 4px; }
"""


def _preset_sections():
    """(title, colour, [(label, command, tooltip), ...])"""
    return [
        ('Connect', '#4a7cf0', [
            ('Connector popup', _connector, 'Pick an output, then an input'),
            ('Connect Attributes', _cmd('mauAttrConnector'),
             'Driver first, then targets: Channel Box selection or all keyable'),
            ('Connect Shapes', _cmd('mauMeshConnector'),
             'Geometry from the first node into the others'),
            ('Connect Components', _cmd('mauMeshConnector', None, None, 1),
             'outComponents / groupId from the first node into the others'),
            ('Swap Connections', _cmd('swapConnections'),
             'Select first, middle node(s), last'),
            ('Swap + Disconnect First', _cmd('swapConnections', None, None, None, True),
             'Swap, then remove the old links into the first node'),
        ]),
        ('Clean', '#e8a45a', [
            ('Clean Up', _cmd('mauCleanNE'), 'Remove sets, layers and other clutter'),
            ('Clean + Joints', _cmd('mauCleanSkinNE'), 'Also remove skinCluster joints'),
            ('Clean + BindPose', _cmd('mauNodeCleanNE', 'dagPose'), 'Remove dagPose nodes'),
            ('Clean Constraints', _clean_constraints, 'Remove parent/point/orient/scale constraints'),
            ('Clean GroupId', _cmd('mauNodeCleanNE', 'groupId'), 'Remove groupId nodes'),
            ('Clean Follicles', _cmd('mauNodeCleanNE', 'follicle'), 'Remove follicles + their transforms'),
            ('Select SkinCluster Joints', _cmd('mauSelSkJnts'), 'Joints of the selected skinCluster'),
        ]),
        ('Shapes', '#6fcf97', [
            ('Mesh Shape', _with_selection('mauSh', 'mesh'), 'New mesh shape from the selected node'),
            ('NurbsCurve Shape', _with_selection('mauSh', 'nurbsCurve'), 'New curve shape from the selected node'),
            ('NurbsSurface Shape', _with_selection('mauSh', 'nurbsSurface'), 'New surface shape from the selected node'),
            ('Shape After Node', _cmd('mauCreateSh'), 'Extra mesh after the selected node'),
            ('Parent Shapes', _cmd('mParentSh'), 'Shapes first, then the transform'),
        ]),
        ('Mesh', '#b48cf2', [
            ('Clean Separate', _cmd('mauSeaparate', 0), 'Separate a mesh cleanly'),
            ('Separate + Transform', _cmd('mauSeaparate', 1), 'Separate, each piece with its own transform'),
            ('Clean Unite', _cmd('mauUnite', 1), 'Unite meshes into one'),
            ('Unite + Transform', _cmd('mauUnite', 0), 'Unite under a new transform'),
            ('Duplicate Chain', _cmd('mauDupChain'), 'Duplicate the selected mesh hierarchy'),
        ]),
    ]


def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


def _run_safely(fn):
    try:
        fn()
    except Exception as e:
        cmds.warning('Node Editor Plus: {}'.format(e))


if QtWidgets is not None:

    class PresetMenu(QtWidgets.QWidget):
        def __init__(self, parent=None, drag=False):
            super(PresetMenu, self).__init__(parent)
            self._actions = {}          # widget -> command
            self._hot = None
            self._busy = False
            self._opened = time.time()
            self.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint
                                | QtCore.Qt.NoDropShadowWindowHint)
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.setStyleSheet(MENU_STYLE)
            self.setWindowOpacity(1.0 - max(0, min(90, MENU_TRANSPARENCY)) / 100.0)
            self._build()
            # marking-menu mode: opened while the right button is held down
            self._poll = QtCore.QTimer(self)
            self._poll.timeout.connect(self._track)
            if drag:
                self._poll.start(15)

        # ---------------------------------------------------------------- layout
        def _build(self):
            outer = QtWidgets.QVBoxLayout(self)
            outer.setContentsMargins(16, 16, 16, 16)
            panel = QtWidgets.QFrame(objectName='panel')
            shadow = QtWidgets.QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(30)
            shadow.setOffset(0, 6)
            shadow.setColor(QtGui.QColor(0, 0, 0, 170))
            panel.setGraphicsEffect(shadow)
            outer.addWidget(panel)

            lay = QtWidgets.QVBoxLayout(panel)
            lay.setContentsMargins(12, 10, 12, 8)
            lay.setSpacing(8)

            # header
            sel = cmds.ls(sl=True) or []
            head = QtWidgets.QHBoxLayout()
            head.addWidget(QtWidgets.QLabel('NODE EDITOR PLUS', objectName='title'))
            head.addStretch(1)
            if sel:
                text = sel[0].split('|')[-1] + ('   +{}'.format(len(sel) - 1) if len(sel) > 1 else '')
            else:
                text = 'nothing selected'
            sel_label = QtWidgets.QLabel(text, objectName='sel')
            sel_label.setToolTip('\n'.join(sel[:20]))
            head.addWidget(sel_label)
            lay.addLayout(head)

            # body: inputs | presets | outputs
            body = QtWidgets.QHBoxLayout()
            body.setSpacing(8)
            self.in_btn = self._side_button('in', _connected_nodes('in'))
            self.out_btn = self._side_button('out', _connected_nodes('out'))

            grid = QtWidgets.QGridLayout()
            grid.setSpacing(8)
            for i, (title, colour, items) in enumerate(_preset_sections()):
                grid.addWidget(self._section(title, colour, items), i // 2, i % 2)

            body.addWidget(self.in_btn)
            body.addLayout(grid, 1)
            body.addWidget(self.out_btn)
            lay.addLayout(body, 1)

            hint = QtWidgets.QLabel(
                'Release the right button on a tool to run it   \u00b7   or click   \u00b7   '
                '\u25c0 \u25b6 keys   \u00b7   Shift keeps it open', objectName='hint')
            hint.setAlignment(QtCore.Qt.AlignCenter)
            lay.addWidget(hint)

        def _side_button(self, direction, nodes):
            incoming = direction == 'in'
            arrow, title = ('◀', 'INPUTS') if incoming else ('▶', 'OUTPUTS')
            count = len(nodes)
            sub = '{} node{}'.format(count, '' if count == 1 else 's') if count else 'none'
            btn = QtWidgets.QPushButton('{}\n\n{}\n{}'.format(arrow, title, sub),
                                        objectName='sideIn' if incoming else 'sideOut')
            btn.setMinimumWidth(96)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            btn.setFocusPolicy(QtCore.Qt.NoFocus)
            btn.setEnabled(bool(count))
            tip = 'Select the {} nodes shown in the graph and centre on them'.format(
                'incoming' if incoming else 'outgoing')
            if nodes:
                tip += ':\n' + '\n'.join(nodes[:15]) + ('\n…' if count > 15 else '')
            btn.setToolTip(tip)
            self._actions[btn] = lambda: _call('mauSelectConnected', direction)
            btn.clicked.connect(lambda *_, b=btn: self._fire(b))
            return btn

        def _section(self, title, colour, items):
            frame = QtWidgets.QFrame(objectName='section')
            v = QtWidgets.QVBoxLayout(frame)
            v.setContentsMargins(6, 6, 6, 6)
            v.setSpacing(1)
            label = QtWidgets.QLabel(title.upper(), objectName='secTitle')
            label.setStyleSheet('color: {0}; border-left: 3px solid {0};'.format(colour))
            v.addWidget(label)
            for text, cmd, tip in items:
                b = QtWidgets.QPushButton(text, objectName='item')
                b.setToolTip(tip)
                b.setCursor(QtCore.Qt.PointingHandCursor)
                b.setFocusPolicy(QtCore.Qt.NoFocus)
                self._actions[b] = cmd
                b.clicked.connect(lambda *_, w=b: self._fire(w))
                v.addWidget(b)
            v.addStretch(1)
            return frame

        # ---------------------------------------------------------------- actions
        @staticmethod
        def _set_state(widget, name, value):
            widget.setProperty(name, 'true' if value else 'false')
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        def _target_at_cursor(self):
            w = self.childAt(self.mapFromGlobal(QtGui.QCursor.pos()))
            while w is not None and w is not self and w not in self._actions:
                w = w.parentWidget()
            if w in self._actions and w.isEnabled():
                return w
            return None

        def _set_hot(self, widget):
            if widget is self._hot:
                return
            if self._hot is not None:
                self._set_state(self._hot, 'hot', False)
            self._hot = widget
            if widget is not None:
                self._set_state(widget, 'hot', True)

        def _track(self):
            """Marking-menu mode: follow the cursor while the right button is held,
            run the highlighted tool when it is released."""
            if self._busy:
                return
            self._set_hot(self._target_at_cursor())
            if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.RightButton:
                return
            self._poll.stop()
            if self._hot is not None:
                self._fire(self._hot)
            elif time.time() - self._opened > 0.35:
                self.close()          # dragged and released on nothing: cancel
            # quick press-release on nothing: stay open and work with clicks

        def _fire(self, widget):
            """Flash the tool green, close (unless Shift) and run it."""
            if self._busy:
                return
            fn = self._actions.get(widget)
            if fn is None:
                return
            keep = QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier
            self._set_hot(None)
            self._set_state(widget, 'running', True)
            if keep:
                _run_safely(fn)
                QtCore.QTimer.singleShot(250, lambda: self._set_state(widget, 'running', False))
                return
            self._busy = True

            def finish():
                self.close()                              # close first: some tools open popups
                QtCore.QTimer.singleShot(0, lambda: _run_safely(fn))
            QtCore.QTimer.singleShot(170, finish)

        def keyPressEvent(self, event):
            if event.key() == QtCore.Qt.Key_Left and self.in_btn.isEnabled():
                self._fire(self.in_btn)
            elif event.key() == QtCore.Qt.Key_Right and self.out_btn.isEnabled():
                self._fire(self.out_btn)
            else:
                super(PresetMenu, self).keyPressEvent(event)

        def place_at_cursor(self):
            self.adjustSize()
            pos = QtGui.QCursor.pos()
            screen = QtGui.QGuiApplication.screenAt(pos) or QtGui.QGuiApplication.primaryScreen()
            geo = screen.availableGeometry()
            w, h = self.width(), self.height()
            x = min(max(pos.x() - w // 2, geo.left()), geo.right() - w)
            y = min(max(pos.y() - h // 2, geo.top()), geo.bottom() - h)
            self.move(x, y)

    class _CtrlRightClick(QtCore.QObject):
        """Event filter on the graph: Ctrl + right-press opens the preset menu in
        marking-menu mode. The rest of that right-button gesture (moves and the
        release) is swallowed so the Node Editor doesn't pan or open its own menu."""
        def __init__(self, parent=None):
            super(_CtrlRightClick, self).__init__(parent)
            self._swallow = False

        def eventFilter(self, obj, event):
            try:
                t = event.type()
                if (t == QtCore.QEvent.MouseButtonPress
                        and event.button() == QtCore.Qt.RightButton
                        and event.modifiers() & QtCore.Qt.ControlModifier):
                    self._swallow = True
                    QtCore.QTimer.singleShot(0, lambda: _call('mauPresetMenu', True))
                    return True
                if self._swallow:
                    if t == QtCore.QEvent.MouseMove:
                        return True
                    if (t == QtCore.QEvent.MouseButtonRelease
                            and event.button() == QtCore.Qt.RightButton):
                        self._swallow = False
                        return True
            except Exception:
                pass
            return False


def mauPresetMenu(drag=False):
    """Open the Node Editor Plus menu at the mouse.
    drag=True: marking-menu mode (release the right button on a tool to run it).
    From a hotkey or shelf it opens in click mode."""
    if QtWidgets is None:
        cmds.warning('Node Editor Plus menu needs a Maya GUI session')
        return None
    old = __main__.__dict__.get(_MENU_KEY)
    try:
        if old is not None:
            old.close()
    except RuntimeError:
        pass
    menu = PresetMenu(_maya_main_window(), drag=drag)
    menu.place_at_cursor()
    menu.show()
    menu.activateWindow()
    __main__.__dict__[_MENU_KEY] = menu
    return menu


def _hook_ctrl_right_click(ned):
    """Install the Ctrl + right-click filter on every graph tab of the editor."""
    if QtWidgets is None:
        return
    store = __main__.__dict__.setdefault(_FILTER_KEY, {})
    for view, flt in store.pop(ned, []):
        try:
            view.viewport().removeEventFilter(flt)
        except RuntimeError:            # editor was closed: Qt objects are gone
            pass
    ptr = omui.MQtUtil.findControl(ned)
    if not ptr:
        return
    pane = wrapInstance(int(ptr), QtWidgets.QWidget)
    hooked = []
    for view in pane.findChildren(QtWidgets.QGraphicsView):
        flt = _CtrlRightClick(view)
        view.viewport().installEventFilter(flt)
        hooked.append((view, flt))
    store[ned] = hooked


def nodePlusMM(panel):
    """Ctrl + right-click in the graph opens the Node Editor Plus menu."""
    # fallback: a one-line Maya menu, only seen on tabs the Qt hook didn't reach
    name = panel + 'MauMM'
    if cmds.popupMenu(name, exists=True):
        cmds.deleteUI(name)
    pm = cmds.popupMenu(name, p=panel, b=3, ctl=True)
    cmds.menuItem(label='Node Editor Plus menu…', p=pm,
                  c=lambda *_: _call('mauPresetMenu'))
    _hook_ctrl_right_click(panel + 'NodeEditorEd')


''' --------------------------------------------------------------------------

                        NODE EDITOR PLUS UI CHANGES
    A toolbar docked on the bottom (or left) edge of the Node Editor graph.

----------------------------------------------------------------------------'''
TOOLBAR_POSITION = 'left'        # 'left' or 'bottom' - or mnmNODEplus(position='bottom')
TOOLBAR_SIZE = 36                # height at the bottom / width on the left
TOOLBAR_SIZE_CLOSED_BOTTOM = 20  # height when collapsed at the bottom
TOOLBAR_SIZE_CLOSED_LEFT = 14    # width when collapsed on the left
ICON_SIZE = 26

# names used by the old horizontal toolbar (removed if still around)
_LEGACY_KEYS = ['MauCollapse', 'LCCLEAN', 'LCALIGN', 'LCSTATE', 'LCINTER', 'LCPSH',
                'LCISO', 'LCSHAPE', 'LCCONNECTOR', 'LCMCONNECTOR', 'LCSWN',
                'LCSEPA', 'LCUNITE', 'LCGRP', 'LCDUP', 'LCSDC']


def _btn(ned, key):
    return '{}MauV_{}'.format(ned, key)


def _toolbar_spec(ned):
    """(key, icon, tooltip, command, [(popup label, command), ...]) - None = separator."""
    state_ui, inter_ui = _btn(ned, 'STATE'), _btn(ned, 'INTER')
    return [
        ('CLEAN', 'cleanerBrush', 'Clean the current Node Editor from extra sets  (right-click: more)',
         _cmd('mauCleanNE'), [
             ('Clean + all Joints', _cmd('mauCleanSkinNE')),
             ('Clean Joints of Selected SkinCluster', _cmd('mauSkinClusterClean')),
             ('Clean + Constraints', _clean_constraints),
             ('Clean + GroupId', _cmd('mauNodeCleanNE', 'groupId')),
             ('Clean + Follicles', _cmd('mauNodeCleanNE', 'follicle')),
             ('Clean + BindPose', _cmd('mauNodeCleanNE', 'dagPose')),
             ('Select joints of selected SkinCluster', _cmd('mauSelSkJnts')),
         ]),
        ('ALIGN', 'aling', 'Open UI to align nodes',
         _main_exec('import nodeAlignDeezUI, importlib; importlib.reload(nodeAlignDeezUI); '
                    'nodeAlignDeezUI.run()'), None),
        None,
        ('STATE', 'refresh', 'Toggle node state Normal / Has No Effect  (right-click: on / off)',
         _cmd('mauTattr', 'nodeState', state_ui), [
             ('On (Normal)', _cmd('mauState', 0, state_ui)),
             ('Off (Has No Effect)', _cmd('mauState', 1, state_ui)),
         ]),
        ('INTER', 'out_polyPlane', 'Toggle intermediate object on the selected shapes',
         _cmd('mauTattr', 'intermediateObject', inter_ui), [
             ('Intermediate On', _cmd('mauInter', 1, inter_ui)),
             ('Intermediate Off', _cmd('mauInter', 0, inter_ui)),
         ]),
        None,
        ('PSH', 'mParentSh', 'Select shapes and then a transform to put them under',
         _cmd('mParentSh'), None),
        ('ISO', 'mISO', 'Isolate selection in the viewport  (right-click: add / remove)',
         _cmd('mauIsolate', 0), [
             ('Add to Isolate', _cmd('mauIsolate', 1)),
             ('Remove from Isolate', _cmd('mauIsolate', 2)),
         ]),
        ('SHAPE', 'mauMesh', 'Make an extra shape after the selected node  (right-click: type)',
         _cmd('mauCreateSh'), [
             ('Mesh Shape', _with_selection('mauSh', 'mesh')),
             ('NurbsCurve Shape', _with_selection('mauSh', 'nurbsCurve')),
             ('NurbsSurface Shape', _with_selection('mauSh', 'nurbsSurface')),
         ]),
        None,
        ('CONNECTOR', 'connectorAttribute', 'Connect matching attributes: driver first, then one or more targets (Channel Box selection or all keyable)',
         _cmd('mauAttrConnector'), None),
        ('MCONNECTOR', 'connectorMesh2', 'Connector popup: pick an output, then an input  (right-click: components)',
         _connector, [
             ('Connect components', _cmd('mauMeshConnector', None, None, 1)),
             ('Connect shape attributes', _cmd('mauMeshConnector', None, None, 0)),
         ]),
        ('SWN', 'Skonverter', 'Swap connections: select first, middle node(s), last  (right-click: + disconnect)',
         _cmd('swapConnections'), [
             ('Swap and disconnect from the first node',
              _cmd('swapConnections', None, None, None, True)),
         ]),
        None,
        ('SEPA', 'polySeparate', 'Clean Separate of a mesh  (right-click: + transform)',
         _cmd('mauSeaparate', 0), [
             ('Separate with new Transform', _cmd('mauSeaparate', 1)),
         ]),
        ('UNITE', 'polyUnite', 'Make a single mesh from multiple meshes  (right-click: + transform)',
         _cmd('mauUnite', 1), [
             ('Unite with new Transform', _cmd('mauUnite', 0)),
         ]),
        # ('GRP', 'mauGRP', 'Create a group node  (right-click: add / get selection)',
        #  _cmd('mauGroupCreate'), [
        #      ('Add Selection to current group node', _cmd('mauGroupAddSel')),
        #      ('Get Selection of current group node', _cmd('mauGetPatterSelection')),
        #  ]),
        # ('DUP', 'mDUP', 'Duplicate the selected mesh hierarchy',
        #  _cmd('mauDupChain'), None),
        # None,
        # ('SDC', 'mdisplayComp', 'SOuP Display Components',
        #  _main_exec("soup().create('displayComponents')"), None),
    ]


# ---------------------------------------------------------------------------- layout helpers
def _full_path(ui):
    """Full Maya UI path of a control or editor."""
    try:
        ptr = omui.MQtUtil.findControl(ui)
        if ptr:
            path = omui.MQtUtil.fullName(ptr)
            if path:
                return path
    except Exception:
        pass
    try:
        parent = cmds.nodeEditor(ui, q=True, parent=True)
        if parent:
            return parent + '|' + ui
    except Exception:
        pass
    return None


def _editor_form(ned):
    """(formLayout, child) - the nearest formLayout around the editor and its
    direct child that contains the editor."""
    path = _full_path(ned)
    if not path:
        return None, None
    tokens = path.split('|')
    for i in range(len(tokens) - 2, -1, -1):
        candidate = '|'.join(tokens[:i + 1])
        if cmds.formLayout(candidate, exists=True):
            return candidate, tokens[i + 1]
    return None, None


def _edge_attach(form, child, edge, keep_missing=False):
    """How 'child' is attached on 'edge': ('form', offset), ('control', offset, other) or None.
    A link to a control that no longer exists counts as None unless keep_missing."""
    def same(a, b):
        return str(a).split('|')[-1] == b

    af = cmds.formLayout(form, q=True, af=True) or []
    for i in range(0, len(af) - 2, 3):
        if same(af[i], child) and af[i + 1] == edge:
            try:
                return 'form', int(float(af[i + 2]))
            except ValueError:
                return 'form', 0

    ac = cmds.formLayout(form, q=True, ac=True) or []
    for i in range(0, len(ac) - 3, 4):
        if same(ac[i], child) and ac[i + 1] == edge:
            a, b = ac[i + 2], ac[i + 3]
            try:
                att = 'control', int(float(a)), str(b).split('|')[-1]
            except ValueError:
                try:
                    att = 'control', int(float(b)), str(a).split('|')[-1]
                except ValueError:
                    return None
            if keep_missing or cmds.control(att[2], exists=True):
                return att
            return None
    return None


def _form_children(form):
    return [str(c).split('|')[-1] for c in (cmds.formLayout(form, q=True, childArray=True) or [])]


def _detach_from(form, child, bar_short):
    """Before removing an old toolbar, glue everything that leaned on it back to the form."""
    fix = []
    for sib in _form_children(form):
        if sib == bar_short:
            continue
        for edge in ('top', 'bottom', 'left', 'right'):
            att = _edge_attach(form, sib, edge, keep_missing=True)
            if att and att[0] == 'control' and att[2] == bar_short:
                fix.append((sib, edge, 0))
    if fix:
        cmds.formLayout(form, e=True, af=fix)


def _qt_rect(form, name):
    """Qt geometry of a child of the form (None when it can't be found / is hidden)."""
    if wrapInstance is None:
        return None
    for path in (form + '|' + name, name):
        ptr = omui.MQtUtil.findControl(path) or omui.MQtUtil.findLayout(path)
        if ptr:
            w = wrapInstance(int(ptr), QtWidgets.QWidget)
            return w.geometry() if w.isVisible() else None
    return None


def _shares_edge(form, child, sib, position):
    """Would 'sib' end up under the toolbar? It must be attached to the same edge as
    the graph and overlap it on the other axis (beside it for 'left', under it for 'bottom')."""
    anchor = 'left' if position == 'left' else 'bottom'
    child_att = _edge_attach(form, child, anchor)
    if child_att is None or _edge_attach(form, sib, anchor) != child_att:
        return False
    g, s = _qt_rect(form, child), _qt_rect(form, sib)
    if s is None:
        return False                      # hidden / not found: nothing to cover
    if g is None:
        return True                       # can't measure the graph: push it to be safe
    if position == 'left':
        return s.top() < g.bottom() and s.bottom() > g.top()
    return s.left() < g.right() and s.right() > g.left()


def _attach_toolbar(form, child, bar, position):
    """Dock the toolbar on the left or bottom edge of the graph.
    The toolbar takes the graph's place on that edge and copies its other two
    edges. The graph AND every other widget sharing that edge in the same range
    are then attached to the toolbar, so the expanded toolbar pushes them over
    instead of covering them (collapsing gives the space back)."""
    bar_short = bar.split('|')[-1]
    anchor = 'left' if position == 'left' else 'bottom'
    sides = ('top', 'bottom') if position == 'left' else ('left', 'right')

    pushed = [child] + [s for s in _form_children(form)
                        if s not in (child, bar_short) and _shares_edge(form, child, s, position)]
    af, ac = [], []
    for edge in (anchor,) + sides:
        att = _edge_attach(form, child, edge)
        if att and att[0] == 'control':
            ac.append((bar_short, edge, att[1], att[2]))
        else:
            af.append((bar_short, edge, att[1] if att else 0))
    for w in pushed:
        ac.append((w, anchor, 0, bar_short))
    cmds.formLayout(form, e=True, af=af, ac=ac)


def _delete_legacy(ned):
    for key in _LEGACY_KEYS:
        name = ned + key
        if cmds.iconTextButton(name, q=True, ex=True):
            cmds.deleteUI(name)


# ---------------------------------------------------------------------------- build
def nodeEdCreateToolbarPy(panelName, fl=None, position=None):
    """Build the Mau toolbar on the panel's Node Editor.
    position: 'bottom' or 'left' (default TOOLBAR_POSITION).
    'fl' is ignored (kept so old calls still work)."""
    position = (position or TOOLBAR_POSITION).lower()
    if position not in ('bottom', 'left'):
        position = 'bottom'
    ned = panelName + 'NodeEditorEd'
    form, child = _editor_form(ned)
    if not form:
        cmds.warning('mnmGraphPlus: could not find the Node Editor layout for ' + panelName)
        return None

    bar_name, box_name = ned + 'MauVBar', ned + 'MauVCol'
    if cmds.layout(bar_name, exists=True):
        _detach_from(form, child, bar_name)
        cmds.deleteUI(bar_name)
    _delete_legacy(ned)

    spec = _toolbar_spec(ned)
    if position == 'left':
        bar = cmds.scrollLayout(
            bar_name, p=form, w=TOOLBAR_SIZE, childResizable=True,
            horizontalScrollBarThickness=0, verticalScrollBarThickness=4)
        box = cmds.columnLayout(box_name, p=bar, adj=True, rowSpacing=2,
                                columnAlign='center')
        cmds.iconTextButton(
            ned + 'MauCollapse', p=box, style='textOnly', label='◂', h=16,
            ann='Collapse / expand the Mau toolbar',
            c=lambda *_: _call('nodeEditorToggleMauIconsPy', 1, ned))
    else:
        bar = cmds.scrollLayout(
            bar_name, p=form, h=TOOLBAR_SIZE, childResizable=False,
            horizontalScrollBarThickness=4, verticalScrollBarThickness=0)
        box = cmds.rowLayout(box_name, p=bar, numberOfColumns=len(spec) + 1,
                             columnAttach=[(i + 1, 'both', 1) for i in range(len(spec) + 1)])
        cmds.iconTextButton(
            ned + 'MauCollapse', p=box, style='textOnly', label='▾', w=14,
            h=ICON_SIZE, ann='Collapse / expand the Mau toolbar',
            c=lambda *_: _call('nodeEditorToggleMauIconsPy', 1, ned))

    sep = 0
    for entry in spec:
        if entry is None:
            sep += 1
            name = '{}MauVSep{}'.format(ned, sep)
            if position == 'left':
                cmds.separator(name, p=box, style='in', h=8)
            else:
                cmds.separator(name, p=box, style='in', horizontal=False, w=8, h=ICON_SIZE)
            continue
        key, icon, ann, cmd, popup = entry
        btn = cmds.iconTextButton(
            _btn(ned, key), p=box, style='iconOnly', image1=icon,
            w=ICON_SIZE, h=ICON_SIZE, ann=ann, c=cmd)
        if popup:
            pm = cmds.popupMenu(p=btn)
            for label, pcmd in popup:
                if label is None:
                    cmds.menuItem(divider=True, p=pm)
                else:
                    cmds.menuItem(label=label, p=pm, c=pcmd)

    # icons follow the selection; jobs die with the toolbar
    state_ui, inter_ui = _btn(ned, 'STATE'), _btn(ned, 'INTER')
    jobS = cmds.scriptJob(e=['SelectionChanged', lambda: _call('mauStateCheckUI', state_ui)],
                          parent=bar)
    jobI = cmds.scriptJob(e=['SelectionChanged', lambda: _call('mauInterCheckUI', inter_ui)],
                          parent=bar)

    _attach_toolbar(form, child, bar, position)
    return jobS, jobI


def nodeEditorToggleMauIconsPy(arg=None, ned=None):
    """Collapse / expand the toolbar (works for both positions)."""
    box, bar, btn = ned + 'MauVCol', ned + 'MauVBar', ned + 'MauCollapse'
    if not cmds.layout(box, exists=True):
        return
    bottom = cmds.rowLayout(box, exists=True)
    kids = [k for k in (cmds.layout(box, q=True, ca=True) or [])
            if k != btn.split('|')[-1]]
    if not kids:
        return
    show = not cmds.control(kids[0], q=True, manage=True)
    for k in kids:
        cmds.control(k, e=True, manage=show)
    if bottom:
        cmds.scrollLayout(bar, e=True, h=TOOLBAR_SIZE if show else TOOLBAR_SIZE_CLOSED_BOTTOM)
        cmds.iconTextButton(btn, e=True, label='▾' if show else '▴',
                            h=ICON_SIZE if show else 16)
    else:
        cmds.scrollLayout(bar, e=True, w=TOOLBAR_SIZE if show else TOOLBAR_SIZE_CLOSED_LEFT)
        cmds.iconTextButton(btn, e=True, label='◂' if show else '▸')


def _node_editor_panels():
    panels = [p for p in (cmds.getPanel(scriptType='nodeEditorPanel') or [])
              if cmds.nodeEditor(p + 'NodeEditorEd', exists=True)]
    visible = set(cmds.getPanel(vis=True) or [])
    return [p for p in panels if p in visible] or panels[:1]


def mnmNODEplus(position=None):
    """Open the Node Editor and add the Mau toolbar + Ctrl+right-click menu.
    position: 'bottom' or 'left' (default TOOLBAR_POSITION)."""
    cmds.NodeEditorWindow()
    for panel in _node_editor_panels():
        nodeEdCreateToolbarPy(panel, position=position)
        nodePlusMM(panel)


# CHANGE THE ICON OF THE NODE EDITOR BASED ON THE NODE STATE
def mauStateCheckUI(ui):
    if not cmds.iconTextButton(ui, q=True, ex=True):
        return
    sel = cmds.ls(sl=True)
    if sel and '.' not in sel[0] and cmds.attributeQuery('nodeState', n=sel[0], ex=True):
        icon = 'refreshGray' if cmds.getAttr(sel[0] + '.nodeState') else 'refresh'
        cmds.iconTextButton(ui, e=True, i=icon)


# CHANGE THE ICON OF THE NODE EDITOR BASED ON THE MESH INTERMEDIATE STATE
def mauInterCheckUI(ui):
    if not cmds.iconTextButton(ui, q=True, ex=True):
        return
    sel = cmds.ls(sl=True)
    if sel and '.' not in sel[0] and cmds.attributeQuery('intermediateObject', n=sel[0], ex=True):
        icon = 'out_mesh' if cmds.getAttr(sel[0] + '.intermediateObject') else 'out_polyPlane'
        cmds.iconTextButton(ui, e=True, i=icon)


# -----------------------------------------------------------------------------
def mTextureViewWindow():
    mel.eval('TextureViewWindow')
    uvTexGlob = mel.eval('string $temp = $gUVTexEditToolBar')

    uiextra = ['outV', 'outU', 'uvVal', 'inU', 'inV']
    for u in uiextra:
        if cmds.objExists(u):
            cmds.deleteUI(u)

    cmds.iconTextButton(
        'outV', w=30, h=20,
        p=uvTexGlob, i='arrowLeft',
        c='cmds.polyEditUV(u=-1*cmds.floatField("uvVal", q=True, v=True), v=0)')
    cmds.iconTextButton(
        'outU', w=30, h=20,
        p=uvTexGlob, i='arrowDown',
        c='cmds.polyEditUV(u=0, v=-1*cmds.floatField("uvVal", q=True, v=True))')
    cmds.floatField('uvVal', pre=1, w=30, p=uvTexGlob, v=1)
    cmds.iconTextButton(
        'inU', w=30, h=20,
        p=uvTexGlob, i='arrowUp',
        c='cmds.polyEditUV(u=0, v=cmds.floatField("uvVal", q=True, v=True))')
    cmds.iconTextButton(
        'inV', w=30, h=20,
        p=uvTexGlob, i='arrowRight',
        c='cmds.polyEditUV(u=cmds.floatField("uvVal", q=True, v=True), v=0)')
    # preset for iterations
    prst = [
        '-1.0', '-0.5', '-0.1', '0.1', '0.5', '1.0']
    pps = cmds.popupMenu('uvValue', p='uvVal')
    for p in prst:
        cmds.menuItem(
            label=p,
            p=pps,
            c="cmds.floatField('uvVal', e=True, v=" + p + ")")