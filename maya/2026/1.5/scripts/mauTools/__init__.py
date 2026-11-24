"""mauTools - rigging / animation utilities for Maya 2026 (Python 3, Qt 6).

    import mauTools
    mauTools.show()

Author : Maurizio Giglioli (maurizio1974@gmail.com)
History: started 2007 as flipper.mel, rewritten in Python as mauTools 2.0.

Modules
    naming      rename / replace / renumber
    transforms  match, flip, centroid, world-space copy, animation transfer
    rigging     joints, IK helpers, utility nodes, rivets and follicles
    attributes  add / remove attributes, lock preferences, copy / paste values
    mesh        skin weights, per-vertex data, proxies, component tools
    scene       viewport display, selection helpers, scene info
    ui          the mauTools window
"""
import contextlib

from maya import cmds, mel

__version__ = '2.0'


def show():
    """Open the mauTools window."""
    from . import ui
    return ui.show()


def forget():
    """Forget the remembered window layout and field values."""
    from . import ui
    return ui.forget()


def reload_all():
    """Forget every mauTools module so the next import reads the files from
    disk again, and return the freshly imported package."""
    import importlib
    import sys
    for name in [m for m in sys.modules
                 if m == __name__ or m.startswith(__name__ + '.')]:
        del sys.modules[name]
    return importlib.import_module(__name__)


def restart():
    """Reload mauTools from disk and open a new window:

        import mauTools
        mauTools.restart()

    `reload(mauTools)` on its own is not enough. It re-runs this file only
    and leaves the submodules (ui, naming, transforms ...) in memory as they
    were, so the window you get is still the old one.
    """
    return reload_all().show()


# ---------------------------------------------------------------------------
# helpers shared by every module
# ---------------------------------------------------------------------------
def selected(**kwargs):
    """Current selection as a list (never None)."""
    return cmds.ls(sl=True, **kwargs) or []


def warn(message):
    cmds.warning('mauTools: ' + message)


def shapes(node):
    return cmds.listRelatives(node, shapes=True, fullPath=True) or []


def parent_of(node):
    parents = cmds.listRelatives(node, parent=True, fullPath=True)
    return parents[0] if parents else None


def tmp_file(name):
    return cmds.internalVar(userTmpDir=True) + name


def remap_namespace(name, reference=None):
    """Move a stored node name into the namespace of `reference`.

    The namespace saved with the name is dropped, so data stored from one
    reference of a rig can be applied to another one (or to no namespace).
    """
    base = name.split('|')[-1].rpartition(':')[2]
    if reference and ':' in reference:
        return reference.split('|')[-1].rpartition(':')[0] + ':' + base
    return base


@contextlib.contextmanager
def undo_chunk(name='mauTools'):
    cmds.undoInfo(openChunk=True, chunkName=name)
    try:
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


@contextlib.contextmanager
def keep_selection():
    sel = selected()
    try:
        yield sel
    finally:
        sel = [s for s in sel if cmds.objExists(s)]
        if sel:
            cmds.select(sel, r=True)
        else:
            cmds.select(cl=True)


class Progress(object):
    """Main-window progress bar, interruptible with Esc.

        with Progress(len(nodes), 'Locking') as bar:
            for n in nodes:
                if bar.cancelled():
                    break
                ...
                bar.step()
    """

    def __init__(self, total, status='Working ...'):
        self.total = max(int(total), 1)
        self.status = status
        self.bar = None

    def __enter__(self):
        try:
            self.bar = mel.eval('$mauToolsTmp = $gMainProgressBar')
            cmds.progressBar(
                self.bar, e=True, beginProgress=True, isInterruptable=True,
                status=self.status, maxValue=self.total)
        except Exception:
            self.bar = None
        return self

    def __exit__(self, *exc):
        if self.bar:
            cmds.progressBar(self.bar, e=True, endProgress=True)
        return False

    def cancelled(self):
        return bool(self.bar) and bool(
            cmds.progressBar(self.bar, q=True, isCancelled=True))

    def step(self, amount=1):
        if self.bar:
            cmds.progressBar(self.bar, e=True, step=amount)
