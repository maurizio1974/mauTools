"""Scene callbacks for the board.

Callbacks only queue; a short Qt timer flushes the queue on the main loop, so the board
never touches the scene from inside a Maya callback and one burst of edits becomes one
refresh. Every callback id is also kept in a registry that survives a module reload, so a
reloaded or crashed panel can never leave callbacks behind.
"""
import __main__

import maya.api.OpenMaya as om
from .qt import QtCore

from . import model

_REGISTRY_KEY = "_nodex_callback_ids"


def registry():
    return __main__.__dict__.setdefault(_REGISTRY_KEY, set())


def remove_stale():
    """Remove callbacks left by an earlier copy of the module. Returns how many."""
    reg = registry()
    n = 0
    for cid in list(reg):
        try:
            om.MMessage.removeCallback(cid)
        except (RuntimeError, ValueError):
            pass
        reg.discard(cid)
        n += 1
    return n


_ATTR_MSGS = (om.MNodeMessage.kConnectionMade | om.MNodeMessage.kConnectionBroken |
              om.MNodeMessage.kAttributeSet | om.MNodeMessage.kAttributeArrayAdded |
              om.MNodeMessage.kAttributeArrayRemoved | om.MNodeMessage.kAttributeAdded |
              om.MNodeMessage.kAttributeRemoved)


class SceneSync(QtCore.QObject):
    """Owns every callback of one panel. The owner gets `flushed(events)` with:

    added: [uuid], removed: [uuid], renamed: [uuid], changed: [uuid] (connections or
    attributes changed: rows and wires), values: [uuid] (only a value was set: fields),
    selection: bool, scene: 'open' | 'new' | None, history: bool (Undo or Redo)
    """
    flushed = QtCore.Signal(dict)
    beforeSave = QtCore.Signal()

    def __init__(self, parent=None):
        super(SceneSync, self).__init__(parent)
        self._ids = []
        self._node_ids = {}          # uuid -> callback id
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self.flush)
        self._reset_queue()

    def _reset_queue(self):
        self._added = []
        self._removed = []
        self._renamed = set()
        self._changed = set()
        self._values = set()
        self._selection = False
        self._scene = None
        self._history = False

    # ------------------------------------------------------------------ lifetime

    def start(self):
        self.stop()
        add = self._keep
        add(om.MDGMessage.addNodeAddedCallback(self._on_added, "dependNode"))
        add(om.MDGMessage.addNodeRemovedCallback(self._on_removed, "dependNode"))
        add(om.MNodeMessage.addNameChangedCallback(om.MObject(), self._on_renamed))
        add(om.MEventMessage.addEventCallback("SelectionChanged", self._on_selection))
        add(om.MEventMessage.addEventCallback("Undo", self._on_history))
        add(om.MEventMessage.addEventCallback("Redo", self._on_history))
        add(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, self._on_opened))
        add(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, self._on_new))
        add(om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeSave, self._on_before_save))

    def stop(self):
        self._timer.stop()
        reg = registry()
        for cid in self._ids + list(self._node_ids.values()):
            try:
                om.MMessage.removeCallback(cid)
            except (RuntimeError, ValueError):
                pass
            reg.discard(cid)
        self._ids = []
        self._node_ids = {}
        self._reset_queue()

    def count(self):
        return len(self._ids) + len(self._node_ids)

    def _keep(self, cid):
        self._ids.append(cid)
        registry().add(cid)

    def watch(self, uuids):
        """Per-node attribute callbacks for exactly the nodes on the board."""
        want = set(uuids)
        reg = registry()
        for u in list(self._node_ids):
            if u not in want:
                cid = self._node_ids.pop(u)
                try:
                    om.MMessage.removeCallback(cid)
                except (RuntimeError, ValueError):
                    pass
                reg.discard(cid)
        for u in want:
            if u in self._node_ids:
                continue
            obj = model.obj_from_uuid(u)
            if obj is None:
                continue
            try:
                cid = om.MNodeMessage.addAttributeChangedCallback(obj, self._on_attr, u)
            except RuntimeError:
                continue
            self._node_ids[u] = cid
            reg.add(cid)

    # ------------------------------------------------------------------ callbacks (queue only)

    def _kick(self):
        if not self._timer.isActive():
            self._timer.start()

    def _on_added(self, obj, _data):
        try:
            if om.MFileIO.isReadingFile() or om.MFileIO.isOpeningFile():
                return
            self._added.append(om.MObjectHandle(obj))
            self._kick()
        except Exception:
            pass

    def _on_removed(self, obj, _data):
        try:
            self._removed.append(model.uuid_of(obj))
            self._kick()
        except Exception:
            pass

    def _on_renamed(self, obj, _prev, _data):
        try:
            if om.MFileIO.isReadingFile():
                return
            self._renamed.add(model.uuid_of(obj))
            self._kick()
        except Exception:
            pass

    def _on_attr(self, msg, plug, other, uuid):
        try:
            if not msg & _ATTR_MSGS:
                return
            if not msg & (_ATTR_MSGS & ~om.MNodeMessage.kAttributeSet):
                self._values.add(uuid)
                self._kick()
                return
            self._changed.add(uuid)
            if msg & (om.MNodeMessage.kConnectionMade | om.MNodeMessage.kConnectionBroken):
                if not other.isNull:
                    self._changed.add(model.uuid_of(other.node()))
            self._kick()
        except Exception:
            pass

    def _on_selection(self, _data):
        self._selection = True
        self._kick()

    def _on_history(self, _data):
        self._history = True
        self._kick()

    def _on_opened(self, _data):
        self._scene = "open"
        self._kick()

    def _on_new(self, _data):
        self._scene = "new"
        self._kick()

    def _on_before_save(self, _data):
        # Synchronous on purpose: the board must be in the file being written.
        try:
            self.beforeSave.emit()
        except Exception:
            pass

    # ------------------------------------------------------------------ flush

    def flush(self):
        added = []
        for h in self._added:
            if h.isValid() and h.isAlive():
                obj = h.object()
                try:
                    if model.is_board_candidate(obj):
                        added.append(model.uuid_of(obj))
                except RuntimeError:
                    pass
        removed = [u for u in self._removed if model.obj_from_uuid(u) is None]
        events = {
            "added": list(dict.fromkeys(added)),
            "removed": list(dict.fromkeys(removed)),
            "renamed": sorted(self._renamed),
            "changed": sorted(self._changed),
            "values": sorted(self._values - self._changed),
            "selection": self._selection,
            "scene": self._scene,
            "history": self._history,
        }
        self._reset_queue()
        self.flushed.emit(events)
