"""Rename tools: add / remove text, search and replace, renumber.

Replaces renRelName.py, renuRel.py, mauRenamer.py and mgRenameBox.mel.

Every function works on the selection, on the hierarchy below it
(hierarchy=True) or on every transform in the scene (everything=True).
Nodes are tracked by UUID while renaming, so parents and children can be
renamed in the same pass in any order.
"""
import re

from maya import cmds

from . import selected, warn

PRESETS = [
    'L_', 'R_', '_grp', '_jnt', '_null', '_loc', '_riv', '_fol',
    '_clh', '_cls', '_crv', '_mesh', '_geo', '_surf']


def _startup_cameras():
    out = set()
    for cam in cmds.ls(type='camera', long=True) or []:
        if cmds.camera(cam, q=True, startupCamera=True):
            out.update(cmds.listRelatives(cam, parent=True, fullPath=True) or [])
    return out


def targets(hierarchy=False, everything=False):
    """UUIDs of the nodes to rename, in selection / hierarchy order."""
    if everything:
        skip = _startup_cameras()
        nodes = [n for n in cmds.ls(type='transform', long=True) or []
                 if n not in skip]
    else:
        nodes = selected(long=True)
        if not nodes:
            warn('select at least one node to rename.')
            return []
        if hierarchy:
            nodes = cmds.ls(nodes, dag=True, type='transform', long=True) or []
    seen, uuids = set(), []
    for uuid in cmds.ls(nodes, uuid=True) or []:
        if uuid not in seen:
            seen.add(uuid)
            uuids.append(uuid)
    return uuids


def _rename(uuids, new_name):
    """Rename every node; new_name(short_name, index) returns the new name."""
    count = 0
    for index, uuid in enumerate(uuids):
        path = cmds.ls(uuid, long=True)
        if not path:
            continue
        old = path[0].split('|')[-1]
        new = new_name(old, index)
        if not new or new == old:
            continue
        try:
            cmds.rename(path[0], new)
            count += 1
        except RuntimeError as exc:
            warn('could not rename %s: %s' % (old, str(exc).strip()))
    print('mauTools: renamed %d node(s).' % count)
    return count


def add(text, suffix=False, hierarchy=False, everything=False):
    """Add `text` in front of the name, or after it when suffix=True."""
    if not text:
        return warn('type the text to add.')
    return _rename(
        targets(hierarchy, everything),
        lambda name, i: name + text if suffix else text + name)


def remove(text, last=False, hierarchy=False, everything=False):
    """Remove the first occurrence of `text` (the last one when last=True)."""
    if not text:
        return warn('type the text to remove.')

    def new_name(name, i):
        index = name.rfind(text) if last else name.find(text)
        if index < 0:
            return name
        return name[:index] + name[index + len(text):]

    return _rename(targets(hierarchy, everything), new_name)


def replace(search, replacement='', mode='all', hierarchy=False,
            everything=False):
    """Replace `search` with `replacement`; mode is 'first', 'last' or 'all'."""
    if not search:
        return warn('type the text to search for.')

    def new_name(name, i):
        if mode == 'first':
            return name.replace(search, replacement, 1)
        if mode == 'last':
            return replacement.join(name.rsplit(search, 1))
        return name.replace(search, replacement)

    return _rename(targets(hierarchy, everything), new_name)


def renumber(base, start=1, padding=2, hierarchy=False):
    """Rename to base + number, counting up from `start` in selection order."""
    if not base:
        return warn('type the base name to renumber with.')
    return _rename(
        targets(hierarchy),
        lambda name, i: base + str(start + i).zfill(padding))


def base_name():
    """Base name of the first selected node, without preset suffix or number."""
    sel = selected()
    if not sel:
        return ''
    name = sel[0].split('|')[-1].rpartition(':')[2]
    for preset in PRESETS:
        if preset.startswith('_') and name.endswith(preset):
            name = name[:-len(preset)]
            break
    return re.sub(r'\d+$', '', name)
