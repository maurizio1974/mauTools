"""Attribute tools: add / remove, lock preferences, copy / paste values.

Replaces mLockAttr.py, lockAttrMG.mel, the attribute half of
readWriteAttr.mel and the attrTools / attrLH procedures of flipper.mel.

Lock preferences are stored on each transform in a locked string attribute
("mLocker"). Tags written by the old MEL tool ("lockAttrMG") are still read.
"""
import fnmatch
import json
import os

from maya import cmds

from . import selected, warn, tmp_file, remap_namespace, Progress

TYPES = ('float', 'int', 'bool', 'enum', 'string', 'vector')
LOCK_TAG = 'mLocker'
OLD_LOCK_TAG = 'lockAttrMG'
ATTR_FILE = 'mauTools_attrs.json'
TRANSFORM_ATTRS = ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v')


def _has(node, attr):
    return cmds.attributeQuery(attr, node=node, exists=True)


# ---------------------------------------------------------------------------
# add / remove
# ---------------------------------------------------------------------------
def add_attribute(name, kind='float', keyable=True, channel_box=True,
                  minimum=None, maximum=None, enum_names=None, nodes=None):
    """Add an attribute to the selected nodes.

    kind         one of TYPES
    channel_box  for non-keyable attributes: still show it in the channel box
    minimum / maximum   limits for float and int (None = no limit)
    enum_names   list of names for an enum
    """
    nodes = nodes or selected()
    if not nodes:
        return warn('select something to add the attribute to.')
    if not name:
        return warn('type a name for the attribute.')
    if kind == 'enum' and not enum_names:
        return warn('an enum needs at least one name.')

    flags = {'longName': name, 'keyable': keyable}
    if kind == 'string':
        flags['dataType'] = 'string'
    elif kind == 'vector':
        flags['attributeType'] = 'double3'
    elif kind == 'enum':
        flags['attributeType'] = 'enum'
        flags['enumName'] = ':'.join(enum_names) + ':'
    else:
        flags['attributeType'] = {
            'float': 'double', 'int': 'long', 'bool': 'bool'}[kind]
        if kind in ('float', 'int'):
            if minimum is not None:
                flags['minValue'] = minimum
            if maximum is not None:
                flags['maxValue'] = maximum

    for node in nodes:
        if _has(node, name):
            warn('%s already has an attribute "%s".' % (node, name))
            continue
        cmds.addAttr(node, **flags)
        plugs = [node + '.' + name]
        if kind == 'vector':
            for axis in 'XYZ':
                cmds.addAttr(node, longName=name + axis, parent=name,
                             attributeType='double', keyable=keyable)
            plugs = [node + '.' + name + axis for axis in 'XYZ']
        if not keyable:
            for plug in plugs:
                cmds.setAttr(plug, channelBox=channel_box)


def remove_attribute(name, nodes=None):
    nodes = nodes or selected()
    if not nodes:
        return warn('select the nodes to remove the attribute from.')
    for node in nodes:
        if not _has(node, name):
            warn('%s has no attribute "%s".' % (node, name))
            continue
        cmds.setAttr(node + '.' + name, lock=False)
        cmds.deleteAttr(node, attribute=name)


# ---------------------------------------------------------------------------
# lock preferences
# ---------------------------------------------------------------------------
def lock_pref(node):
    """Attributes this node is tagged to lock (empty list if not tagged)."""
    for tag in (LOCK_TAG, OLD_LOCK_TAG):
        if _has(node, tag):
            return (cmds.getAttr(node + '.' + tag) or '').split()
    return []


def _write_pref(node, attrs):
    for tag in (LOCK_TAG, OLD_LOCK_TAG):
        if _has(node, tag):
            cmds.setAttr(node + '.' + tag, lock=False)
            cmds.deleteAttr(node, attribute=tag)
    if attrs:
        cmds.addAttr(node, longName=LOCK_TAG, dataType='string')
        cmds.setAttr(node + '.' + LOCK_TAG, ' '.join(attrs), type='string')
        cmds.setAttr(node + '.' + LOCK_TAG, lock=True)


def set_lock_pref(translate=(True, True, True), rotate=(True, True, True),
                  scale=(True, True, True), visibility=False,
                  user_defined=False, nodes=None):
    """Tag the selected transforms with the attributes to lock later.

    Nothing is locked yet: apply_lock() reads the tags."""
    nodes = nodes or selected(transforms=True)
    if not nodes:
        return warn('select the transforms to tag.')
    attrs = []
    for prefix, axes in (('t', translate), ('r', rotate), ('s', scale)):
        attrs += [prefix + a for a, on in zip('xyz', axes) if on]
    if visibility:
        attrs.append('v')
    for node in nodes:
        extra = []
        if user_defined:
            extra = [a for a in cmds.listAttr(
                node, userDefined=True, settable=True) or []
                if a not in (LOCK_TAG, OLD_LOCK_TAG)]
        _write_pref(node, attrs + extra)


def remove_lock_pref(nodes=None):
    for node in nodes or selected(transforms=True):
        _write_pref(node, [])


def lock_pref_from_scene():
    """Tag every transform below the selection with the attributes that are
    locked on it right now."""
    sel = selected()
    if not sel:
        return warn('select the top node of the hierarchy to read.')
    nodes = cmds.ls(sel, dag=True, type='transform', long=True) or []
    with Progress(len(nodes), 'Reading locked attributes') as bar:
        for node in nodes:
            if bar.cancelled():
                break
            _write_pref(node, [a for a in TRANSFORM_ATTRS
                               if cmds.getAttr(node + '.' + a, lock=True)])
            bar.step()
    print('mauTools: locking preferences stored on %d node(s).' % len(nodes))


def apply_lock(lock=True, hide=False, hierarchy=True):
    """Lock (and optionally hide) or unlock the tagged attributes of the
    selection, or of everything below it when hierarchy=True."""
    nodes = cmds.ls(sl=True, dag=hierarchy, type='transform', long=True) or []
    if not nodes:
        return warn('nothing selected.')
    with Progress(len(nodes), 'Locking' if lock else 'Unlocking') as bar:
        for node in nodes:
            if bar.cancelled():
                break
            for attr in lock_pref(node):
                if not _has(node, attr):
                    continue
                plug = node + '.' + attr
                cmds.setAttr(plug, lock=lock)
                cmds.setAttr(plug, keyable=not (lock and hide))
            bar.step()
    print('mauTools: structure %s.' % ('locked' if lock else 'unlocked'))


def lock_hide_by_pattern(pattern, lock=True, hide=True):
    """Lock / hide translate, rotate, scale and visibility of every node
    below the selection whose name matches `pattern` (for example "*_jnt")."""
    count = 0
    nodes = cmds.ls(sl=True, dag=True, allPaths=True, long=True) or []
    with Progress(len(nodes)) as bar:
        for node in nodes:
            if bar.cancelled():
                break
            bar.step()
            short = node.split('|')[-1]
            if 'Shape' in short or not fnmatch.fnmatchcase(short, pattern):
                continue
            for attr in TRANSFORM_ATTRS:
                if _has(node, attr):
                    cmds.setAttr(node + '.' + attr, lock=lock,
                                 keyable=not hide)
            count += 1
    print('mauTools: %d node(s) %s.' % (
        count, 'locked' if lock else 'unlocked'))
    return count


# ---------------------------------------------------------------------------
# copy / paste values (through a temp file, so it works between sessions)
# ---------------------------------------------------------------------------
def store_attributes(nodes=None):
    """Store the keyable attribute values of the selection."""
    nodes = nodes or selected()
    if not nodes:
        return warn('select the nodes to store.')
    data = {}
    for node in nodes:
        values = {}
        for attr in cmds.listAttr(node, keyable=True, scalar=True) or []:
            try:
                values[attr] = cmds.getAttr(node + '.' + attr)
            except (RuntimeError, ValueError):
                pass
        data[node] = values
    path = tmp_file(ATTR_FILE)
    with open(path, 'w') as handle:
        json.dump(data, handle, indent=1)
    print('mauTools: attributes of %d node(s) stored in %s'
          % (len(data), path))


def restore_attributes():
    """Apply the stored values. If something is selected its namespace is
    used to find the nodes. Locked and connected attributes are skipped."""
    path = tmp_file(ATTR_FILE)
    if not os.path.isfile(path):
        return warn('nothing stored yet.')
    with open(path) as handle:
        data = json.load(handle)
    sel = selected()
    done = 0
    for stored, values in data.items():
        node = remap_namespace(stored, sel[0]) if sel else stored
        if not cmds.objExists(node):
            warn('%s not found, skipped.' % node)
            continue
        for attr, value in values.items():
            plug = node + '.' + attr
            if not cmds.objExists(plug) or cmds.getAttr(plug, lock=True):
                continue
            if cmds.connectionInfo(plug, sourceFromDestination=True):
                continue
            cmds.setAttr(plug, value)
        done += 1
    print('mauTools: attributes applied to %d node(s).' % done)
