"""The board controller: owns board state, talks to Maya, feeds QML.

QML never touches Maya: it calls the slots below and redraws from the signals. Updates
that rebuild QML delegates (nodeAdded / nodeChanged / nodeRemoved / wiresChanged) are
always emitted from a zero-delay timer, never from inside the QML mouse handler that asked
for them (global leaf qt/qml-in-a-host-app: a Repeater model replaced from a delegate's own
handler destroys the delegate mid-event).
"""
import json

import maya.api.OpenMaya as om
import maya.cmds as cmds
from .qt import QtCore, QtGui, QtWidgets, exec_, ival

from . import catalog, fragment, layout, model, naming, ops, presets, store, sync, theme

FRAGMENT_MIME = 'application/x-nodex-fragment+json'

BURST_LIMIT = 200      # more nodes created at once than this are not auto-added
BULK_RESET = 60        # more nodes added + removed in one flush than this rebuild the board at once
LINKS_AUTO = 1200      # wires on a tab above which "auto" draws node links (one per node pair)
MAX_NODES = 500        # default node limit of a tab, like the limit of Maya's own Node Editor
MAX_NODES_VAR = "nodexMaxNodes"   # optionVar: a preference of the machine, not of the scene
SHAPES_VAR = "nodexShapes"        # optionVar: Display group mode, kept across panel rebuilds
GRID = 22


def max_nodes_pref():
    if cmds.optionVar(exists=MAX_NODES_VAR):
        return max(1, int(cmds.optionVar(q=MAX_NODES_VAR)))
    return MAX_NODES


def shapes_pref():
    if cmds.optionVar(exists=SHAPES_VAR):
        mode = cmds.optionVar(q=SHAPES_VAR)
        if mode in ("all", "except", "none"):
            return mode
    return "except"


def _js(v):
    """A JS array/object passed to a "QVariant" slot arrives as QJSValue, not a list/dict."""
    if hasattr(v, "toVariant"):
        v = v.toVariant()
    return v


class Bridge(QtCore.QObject):
    # --> QML. Every signal a QML handler binds to MUST name its parameters (`arguments=`):
    # a PySide2 signal with 3+ unnamed parameters crashes QQmlBoundSignalExpression while
    # `Connections { function onX(a, b, c) }` is bound (ACCESS_VIOLATION in setSource, ~25%
    # of loads). Guarded by tests/test_qml.py.
    boardReset = QtCore.Signal()
    nodeAdded = QtCore.Signal(str, "QVariant", arguments=["id", "info"])
    nodeChanged = QtCore.Signal(str, "QVariant", arguments=["id", "info"])
    nodeRemoved = QtCore.Signal(str, arguments=["id"])
    nodesMoved = QtCore.Signal("QVariant", bool, arguments=["map", "anim"])
    # Big payloads travel as JSON text: a 7500-wire list or a 600-node snapshot converted
    # through QVariant took ~100-200 ms; json.dumps + JSON.parse take a fraction of it.
    wiresChanged = QtCore.Signal(str, arguments=["list"])
    selectionChanged = QtCore.Signal("QVariant", str, arguments=["ids", "ld"])
    viewRequested = QtCore.Signal(float, float, float, arguments=["x", "y", "z"])
    frameRequested = QtCore.Signal(bool, arguments=["all"])
    renameRequested = QtCore.Signal(str, arguments=["id"])
    # --> panel (named too, so any of them can be bound from QML later)
    tabsChanged = QtCore.Signal()
    statusChanged = QtCore.Signal(str, arguments=["text"])
    countsChanged = QtCore.Signal(int, int, arguments=["nodes", "wires"])
    zoomChanged = QtCore.Signal(float, arguments=["zoom"])
    modeChanged = QtCore.Signal(str, arguments=["mode"])
    syncChanged = QtCore.Signal(bool, arguments=["on"])
    createRequested = QtCore.Signal(float, float, arguments=["x", "y"])
    linksChanged = QtCore.Signal(bool, str, arguments=["on", "mode"])
    connectionsFound = QtCore.Signal('QVariant', 'QVariant', arguments=['nodes', 'wires'])
    framesChanged = QtCore.Signal(str, arguments=["list"])
    frameEditRequested = QtCore.Signal(str, str, arguments=["id", "field"])

    def __init__(self, parent=None):
        super(Bridge, self).__init__(parent)
        self.store = store.Store()
        self.sync = sync.SceneSync(self)
        self.sync.flushed.connect(self._on_scene_events)
        self.sync.beforeSave.connect(self.save_store)
        self.sync_on = True
        self.locked = False
        self.depth = 1
        self.max_nodes = max_nodes_pref()
        self.shapes = shapes_pref()     # all | except | none (Display group)
        self.infos = {}                 # uuid -> node info on the active tab
        self.views = {}                 # uuid -> model.NodeView
        self.dead = set()
        self.wires = []
        self.skipped = 0                # nodes the last add_nodes() left out over max_nodes
        self.sel = []                   # ordered; last is the lead
        self.cursor = None              # world position of the last press / Tab
        self.open_search = None         # panel callback: (provider, on_pick, title, hint, at_cursor)
        self.view_aspect = 1.6          # board width / height, for layouts that fill the view
        self.query = ""                 # find field: matching rows are revealed
        self._revealed = set()
        self._pending = self._no_pending()
        self._flush_timer = QtCore.QTimer(self)
        self._flush_timer.setSingleShot(True)
        self._flush_timer.setInterval(0)
        self._flush_timer.timeout.connect(self._flush_ui)
        self._ignore_selection = 0
        self._connection_result = None

    # ================================================================== lifetime

    def start(self):
        sync.remove_stale()
        self.store.load()
        self.sync.start()
        self._load_tab()

    def shutdown(self):
        try:
            self.save_store()
        except Exception:
            pass
        self.sync.stop()
        self._flush_timer.stop()

    def save_store(self):
        self._sync_tab_views()
        alive = [u for t in self.store.tabs for u in list(t["nodes"]) + list(t["gone"])
                 if model.obj_from_uuid(u) is not None]
        self.store.prune(alive)
        self.store.save()

    # ================================================================== tab loading

    @property
    def tab(self):
        return self.store.tab

    def _view_for(self, u):
        v = self.views.get(u)
        if v is None:
            d = self.tab["views"].get(u) or {}
            v = model.NodeView(mode=d.get("mode"), expanded=d.get("expanded"),
                               pinned=d.get("pinned"))
            self.views[u] = v
        return v

    def _sync_tab_views(self):
        for u, v in self.views.items():
            if u in self.tab["nodes"]:
                self.tab["views"][u] = {"mode": v.mode, "expanded": sorted(v.expanded),
                                        "pinned": sorted(v.pinned)}

    def _load_tab(self):
        self.infos = {}
        self.views = {}
        self.dead = set()
        self.wires = []
        self._connection_result = None
        for u in list(self.tab["nodes"]):
            info = self._describe(u)
            if info is None:
                # Deleted while the scene was closed or the tab was hidden.
                self.store.remove(u)
                continue
            self.infos[u] = info
        self.wires = model.wires(list(self.infos), self.infos)
        self._pull_selection()
        self.sync.watch(list(self.infos))
        self.boardReset.emit()
        v = self.tab.get("view") or {}
        self.viewRequested.emit(float(v.get("x", 60)), float(v.get("y", 60)), float(v.get("z", 1)))
        self.modeChanged.emit(self.tab.get("mode", "connected"))
        self._links_state = None
        self._emit_links()
        self.tabsChanged.emit()
        self._emit_counts()

        if len(self.infos) > self.max_nodes:
            # Never drop a saved board on load; say why it may be slow instead.
            self.status("This tab holds %d nodes, above the limit of %d; Remove some or raise "
                        "Options > Node limit" % (len(self.infos), self.max_nodes))

    def _describe(self, u):
        info = model.describe(u, self._view_for(u), self.tab.get("mode", "connected"), self.query)
        if info is not None:
            p = self.store.pos(u)
            info["x"], info["y"] = (p if p else (60.0, 60.0))
            self._apply_width(u, info)
        return info

    def _apply_width(self, u, info):
        """A width the user dragged the node to wins over the computed one."""
        w = self.store.width(u)
        if w:
            info["width"] = w

    @QtCore.Slot(str, float)
    def setNodeWidth(self, u, w):
        """the node's right edge was dragged; w <= 0 goes back to the computed width."""
        if u not in self.infos:
            return
        self.store.set_width(u, max(model.USER_MIN_W, min(model.USER_MAX_W, w)) if w > 0 else 0)
        self._queue(changed=[u], rewire=False)       # rows (anchors) do not move

    # ================================================================== deferred UI flush

    @staticmethod
    def _no_pending():
        return {"added": [], "changed": set(), "removed": [], "rewire": set(), "all": False}

    def _queue(self, added=(), changed=(), removed=(), wires=False, rewire=True):
        """changed: nodes to describe again; with `rewire` their wires are rebuilt too (rows,
        so anchors, may have moved). Only the wires touching added / changed / removed nodes
        are rebuilt; wires=True rebuilds all of them."""
        p = self._pending
        p["added"].extend(u for u in added if u not in p["added"])
        p["changed"].update(changed)
        p["removed"].extend(removed)
        p["rewire"].update(added)
        if rewire:
            p["rewire"].update(changed)
        p["all"] = p["all"] or wires
        self._flush_timer.start()

    def _flush_ui(self):
        p = self._pending
        self._pending = self._no_pending()
        # Graphing a network adds / removes hundreds of nodes: one board reset is far cheaper
        # than hundreds of delegate inserts and removals (each removal searches the model).
        bulk = len(p["removed"]) + len(p["added"]) > BULK_RESET
        if not bulk:
            for u in p["removed"]:
                self.nodeRemoved.emit(u)
            for u in p["added"]:
                if u in self.infos:
                    self.nodeAdded.emit(u, self.infos[u])
        for u in p["changed"]:
            if u in self.infos and u not in p["added"]:
                if u not in self.dead:
                    info = self._describe(u)
                    if info is None:
                        continue
                    self.infos[u] = info
                if not bulk:
                    self.nodeChanged.emit(u, self.infos[u])
        live = [u for u in self.infos if u not in self.dead]
        drop = set(p["rewire"]) | set(p["removed"])
        if p["all"] or bulk:
            self.wires = model.wires(live, self.infos)
        elif drop:
            keep = [w for w in self.wires if w["src"] not in drop and w["dst"] not in drop]
            touch = [u for u in p["rewire"] if u in self.infos and u not in self.dead]
            self.wires = keep + model.wires_touching(touch, live, self.infos)
        self._emit_links()
        if bulk:
            self.boardReset.emit()
        elif p["all"] or drop:
            self.wiresChanged.emit(json.dumps(self.wires))
        self.sync.watch([u for u in self.infos if u not in self.dead])
        self._emit_counts()

        if self._connection_result is not None:
            nodes = self._connection_result
            self._connection_result = None
            found = set(nodes)
            self.connectionsFound.emit(nodes, [w['id'] for w in self.wires if w['src'] in found and w['dst'] in found])

    # ================================================================== node links (big graphs)

    def links_mode(self):
        return self.tab.get("links", "auto")

    def links_on(self):
        """One wire per node pair: forced on/off, or on above LINKS_AUTO wires ("auto")."""
        m = self.links_mode()
        return m == "on" or (m == "auto" and len(self.wires) > LINKS_AUTO)

    def _emit_links(self):
        st = (self.links_on(), self.links_mode())
        if st != getattr(self, "_links_state", None):
            self._links_state = st
            self.linksChanged.emit(st[0], st[1])

    @QtCore.Slot(str)
    def setLinks(self, mode):
        self.tab["links"] = mode if mode in ("auto", "on", "off") else "auto"
        self._emit_links()

    def _wires_of(self, ids):
        ids = set(_js(ids) or [])
        return [w for w in self.wires if w["id"] in ids]

    def _conn_line(self, w):
        a = self.infos.get(w["src"], {}).get("name", "?")
        b = self.infos.get(w["dst"], {}).get("name", "?")
        return "%s.%s -> %s.%s" % (a, w["srcPlug"], b, w["dstPlug"])

    @QtCore.Slot("QVariant", result=str)
    def bundleTip(self, ids):
        ws = self._wires_of(ids)
        if not ws:
            return ""
        esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        th = theme.CHROME
        a = self.infos.get(ws[0]["src"], {}).get("name", "?")
        b = self.infos.get(ws[0]["dst"], {}).get("name", "?")
        h = ('<b style="color:%s">%d connection%s</b> <span style="color:%s">%s &rarr; %s</span>'
             % (th["ink"], len(ws), "" if len(ws) == 1 else "s", th["faint"], esc(a), esc(b)))
        for w in ws[:14]:
            h += ('<br><span style="color:%s">&#9679;</span> %s <span style="color:%s">&rarr;</span> %s'
                  % (w["color"], esc(w["srcPlug"]), th["faint"], esc(w["dstPlug"])))
        if len(ws) > 14:
            h += '<br><span style="color:%s">+ %d more</span>' % (th["faint"], len(ws) - 14)
        return h

    @QtCore.Slot("QVariant")
    def bundleMenu(self, ids):
        ws = self._wires_of(ids)
        if not ws:
            return
        if len(ws) == 1:
            self.wireMenu(ws[0]['id'])
            return
        menu = QtWidgets.QMenu()
        for w in ws[:12]:
            menu.addAction(self._conn_line(w)).setEnabled(False)
        if len(ws) > 12:
            menu.addAction("+ %d more" % (len(ws) - 12)).setEnabled(False)
        menu.addSeparator()
        wids = [w["id"] for w in ws]
        menu.addAction("Disconnect all %d\tDel" % len(ws), lambda: self.disconnectWires(wids))
        between = menu.addMenu('Inbetween')
        between.setEnabled(not self.locked and len(self.infos) < self.max_nodes)
        for w in ws:
            connection = between.addMenu(self._conn_line(w))
            self._fill_utility_menu(connection, w)
        self._popup(menu)

    def _emit_counts(self):
        self.countsChanged.emit(len(self.infos), len(self.wires))

    def status(self, text):
        self.statusChanged.emit(text)

    def _over(self):
        """Status suffix for an add_nodes() that ran into the limit."""
        if not self.skipped:
            return ""
        return "; %d left out, the tab limit is %d (Options > Node limit)" % (self.skipped, self.max_nodes)

    def set_max_nodes(self, n):
        """The limit only gates adding: a tab already above it keeps its nodes."""
        self.max_nodes = max(1, int(n))
        cmds.optionVar(intValue=(MAX_NODES_VAR, self.max_nodes))
        self._emit_counts()

    # ================================================================== adding / removing nodes

    def _rects(self, exclude=()):
        out = []
        for u, i in self.infos.items():
            if u in exclude:
                continue
            x, y = self.store.pos(u) or (i["x"], i["y"])
            out.append((x, y, i["width"], i["height"]))
        return out

    def add_nodes(self, uuids, cursor=None, arrange_new=True, force=False):
        """Put nodes on the active tab. Existing nodes never move.

        At most `max_nodes` on a tab: the first ones in `uuids` win (callers pass them nearest
        first) and `self.skipped` counts the rest. `force` is for one explicit node (create,
        unit conversion), which the limit never refuses."""
        new = [u for u in dict.fromkeys(uuids) if u not in self.infos]
        self.skipped = 0
        if not force:
            room = max(0, self.max_nodes - len(self.infos))
            self.skipped = max(0, len(new) - room)
            new = new[:room]
        infos = {}
        for u in new:
            info = model.describe(u, self._view_for(u), self.tab.get("mode", "connected"), self.query)
            if info is not None:
                self._apply_width(u, info)
                infos[u] = info
        new = [u for u in new if u in infos]
        if not new:
            return []
        placed = {}
        for u in new:
            known = self.store.pos(u) or self.tab["gone"].pop(u, None)
            if known:
                placed[u] = tuple(known)
        todo = [u for u in new if u not in placed]
        if len(todo) > 1 and arrange_new:
            # A network arrives at once: lay it out as a block, then drop the block in free space.
            sizes = dict((u, (infos[u]["width"], infos[u]["height"])) for u in todo)
            edges = self._edges(todo)
            block = layout.layered(todo, sizes, edges, origin=(0.0, 0.0))
            block = layout.wrap(block, sizes, aspect=getattr(self, "view_aspect", 1.6))
            bw = max(block[u][0] + sizes[u][0] for u in todo)
            bh = max(block[u][1] + sizes[u][1] for u in todo)
            rects = self._rects()
            if cursor is not None:
                bx, by = layout.free_spot(cursor[0], cursor[1], bw, bh, rects)
            elif rects:
                x1 = max(r[0] + r[2] for r in rects)
                y0 = min(r[1] for r in rects)
                bx, by = layout.free_spot(x1 + layout.GAP_X * 2, y0, bw, bh, rects)
            else:
                bx, by = 60.0, 60.0
            for u in todo:
                placed[u] = (bx + block[u][0], by + block[u][1])
        else:
            for u in todo:
                rects = self._rects() + [(placed[v][0], placed[v][1], infos[v]["width"], infos[v]["height"])
                                         for v in placed if v in infos]
                ups = [r for r in self._neighbour_rects(u, "up", placed, infos)]
                downs = [r for r in self._neighbour_rects(u, "down", placed, infos)]
                placed[u] = layout.place((infos[u]["width"], infos[u]["height"]), rects,
                                         cursor=cursor, upstream=ups, downstream=downs)
        for u in new:
            x, y = placed[u]
            if cursor is not None:
                x, y = self._snap(x, y)
            self.store.set_pos(u, x, y)
            infos[u]["x"], infos[u]["y"] = self.store.pos(u)
            self.infos[u] = infos[u]
        self._queue(added=new)
        self._mark_modified()
        return new

    def _snap(self, x, y):
        return round(x, 1), round(y, 1)

    def _edges(self, ids):
        s = set(ids)
        edges = []
        for u in ids:
            for v in model.neighbours(u, "down"):
                if v in s:
                    edges.append((u, v))
        return edges

    def _neighbour_rects(self, u, direction, placed, infos):
        out = []
        for v in model.neighbours(u, direction):
            if v in self.infos and v not in infos:
                i = self.infos[v]
                x, y = self.store.pos(v) or (i["x"], i["y"])
                out.append((x, y, i["width"], i["height"]))
            elif v in placed and v in infos:
                out.append((placed[v][0], placed[v][1], infos[v]["width"], infos[v]["height"]))
        return out

    def remove_nodes(self, uuids, remember=False):
        gone = [u for u in uuids if u in self.infos]
        for u in gone:
            self.infos.pop(u, None)
            self.dead.discard(u)
            self.store.remove(u, remember=remember)
            if not remember:
                self.views.pop(u, None)
        self.sel = [u for u in self.sel if u not in gone]
        if gone:
            self._queue(removed=gone)
            self._emit_selection()
            self._mark_modified()
        return gone

    def _mark_modified(self):
        try:
            cmds.file(modified=True)
        except RuntimeError:
            pass

    # ================================================================== scene events (sync.py)

    def _on_scene_events(self, ev):
        if ev["scene"]:
            self.store.load()
            self.sync.watch([])
            self._load_tab()
            return
        if ev.get('history'):
            self._restore_history_nodes()
        changed = set(u for u in ev["changed"] if u in self.infos)
        if ev["removed"]:
            gone = [u for u in ev["removed"] if u in self.infos]
            if self.sync_on:
                self.remove_nodes(gone, remember=True)
            else:
                for u in gone:
                    self.dead.add(u)
                    self.infos[u]["dead"] = True
                    changed.add(u)
        if ev["added"] and self.sync_on and not self.locked:
            fresh = [u for u in self._filter_shapes(ev["added"]) if u not in self.infos]
            if len(fresh) > BURST_LIMIT:
                self.status("%d nodes created -- too many to add; use Add selected" % len(fresh))
            elif fresh:
                self.add_nodes(fresh, cursor=None, arrange_new=True)
                if self.skipped:
                    self.status("%d new node%s not added: the tab is at its limit of %d"
                                % (self.skipped, "" if self.skipped == 1 else "s", self.max_nodes))
        if ev["renamed"] and self.sync_on:
            changed.update(u for u in ev["renamed"] if u in self.infos)
        if changed:
            self._queue(changed=changed)
        # A value set on its own changes fields only: no rows, no wires.
        vals = [u for u in ev.get("values", ()) if u in self.infos and u not in changed
                and any(r.get("valueKind") for r in self.infos[u]["rows"])]
        if vals:
            self._queue(changed=vals, rewire=False)
        if ev["selection"]:
            self._pull_selection()

    def _restore_history_nodes(self):
        """Undo can revive an existing MObject without a node-added callback; reconcile tracked UUIDs."""
        missing = [u for u in self.infos if model.path_of(u) is None]
        self.remove_nodes(missing, remember=True)
        restored = [u for u in self.tab['gone'] if model.path_of(u) is not None]
        self.add_nodes(restored, arrange_new=False, force=True)
        for u in list(self.dead):
            if model.path_of(u):
                self.dead.discard(u)
        # Callbacks attached before a deletion may no longer belong to the revived node.
        self.sync.watch([])
        self._queue(changed=list(self.infos), wires=True)

    def _pull_selection(self):
        if self._ignore_selection:
            return
        names = cmds.ls(selection=True, long=True) or []
        uu = model.uuids_of(names)
        self.sel = [u for u in uu if u in self.infos]
        self._emit_selection()

    def _emit_selection(self):
        self.selectionChanged.emit(list(self.sel), self.sel[-1] if self.sel else "")

    def _push_selection(self):
        names = [model.path_of(u) for u in self.sel if u not in self.dead]
        names = [n for n in names if n]
        if names:
            cmds.select(names, replace=True)
        else:
            cmds.select(clear=True)

    # ================================================================== slots: data for QML

    @QtCore.Slot(result="QVariant")
    def theme(self):
        return theme.qml_theme()

    @QtCore.Slot(result=str)
    def snapshot(self):
        """The whole active tab for Board.reset(), as JSON text (see wiresChanged)."""
        return json.dumps({"nodes": [self.infos[u] for u in self.infos], "wires": self.wires,
                           "sel": list(self.sel), "lead": self.sel[-1] if self.sel else "",
                           "links": self.links_on(), "frames": self.tab.setdefault("frames", [])})

    @QtCore.Slot(str, result="QVariant")
    def nodeInfo(self, u):
        return self.infos.get(u)

    @QtCore.Slot(str, str, result=str)
    def tooltip(self, u, plug):
        if u in self.dead:
            return ""
        i = model.plug_info(u, plug)
        if not i:
            return ""
        esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        th = theme.CHROME
        h = ('<b style="color:%s">%s</b> <span style="color:%s">%s</span><br>'
             % (th["ink"], esc(i["nice"]), th["faint"], esc(i["long"])))
        h += ('<span style="color:%s">&#9679;</span> %s <span style="color:%s">&middot; %s</span><br>'
              % (i["color"], esc(i["cls"]), th["faint"], esc(i["io"])))
        h += ('<span style="color:%s">value</span> <span style="color:%s;font-family:Consolas">%s</span>'
              % (th["faint"], th["ink"], esc(i["value"] or "-")))
        if i["source"]:
            h += '<br><span style="color:%s">from</span> %s' % (th["faint"], esc(i["source"]))
            if i["via"]:
                h += ' <span style="color:%s">via %s</span>' % (th["faint"], esc(i["via"]))
        return h

    @QtCore.Slot(str, result=str)
    def iconUrl(self, type_name):
        import os
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", type_name + ".png")
        return QtCore.QUrl.fromLocalFile(p).toString() if os.path.exists(p) else ""

    @QtCore.Slot(str, result=str)
    def toolbarIcon(self, name):
        import os
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "toolbar", name + ".png")
        return QtCore.QUrl.fromLocalFile(p).toString()

    # ================================================================== slots: selection & moves

    @QtCore.Slot(str, int)
    def clickNode(self, u, modifiers):
        shift = bool(ival(modifiers) & ival(QtCore.Qt.ShiftModifier))
        ctrl = bool(ival(modifiers) & ival(QtCore.Qt.ControlModifier))
        if shift and u in self.sel:
            if self.sel[-1] == u:
                self.sel.remove(u)
            else:
                self.sel.remove(u)
                self.sel.append(u)          # re-clicking makes it the lead
        elif shift or ctrl and u not in self.sel:
            self.sel.append(u)
        elif ctrl:
            self.sel.remove(u)
        elif u not in self.sel:
            self.sel = [u]
        else:
            self.sel.remove(u)
            self.sel.append(u)
        self._emit_selection()
        self._select_in_maya()

    @QtCore.Slot("QVariant", bool)
    def selectNodes(self, ids, add):
        ids = [u for u in (_js(ids) or []) if u in self.infos]
        if add:
            self.sel = self.sel + [u for u in ids if u not in self.sel]
        else:
            self.sel = ids
        self._emit_selection()
        self._select_in_maya()

    @QtCore.Slot()
    def clearSelection(self):
        if self.sel:
            self.sel = []
            self._emit_selection()
            self._select_in_maya()

    def _select_in_maya(self):
        self._ignore_selection += 1
        try:
            self._push_selection()
        finally:
            QtCore.QTimer.singleShot(60, self._release_selection)

    def _release_selection(self):
        self._ignore_selection = max(0, self._ignore_selection - 1)

    @QtCore.Slot("QVariant")
    def moveNodes(self, positions):
        for u, xy in (_js(positions) or {}).items():
            if u in self.infos:
                self.store.set_pos(u, xy[0], xy[1])
                self.infos[u]["x"], self.infos[u]["y"] = self.store.pos(u)
        self._mark_modified()

    @QtCore.Slot(float, float, float)
    def setView(self, x, y, z):
        self.tab["view"] = {"x": round(x, 1), "y": round(y, 1), "z": round(z, 4)}
        self.zoomChanged.emit(z)

    @QtCore.Slot(float, float)
    def setViewSize(self, w, h):
        if w > 0 and h > 0:
            self.view_aspect = max(0.3, min(4.0, w / h))
            self.view_size = (w, h)

    @QtCore.Slot(float, float)
    def setCursor(self, x, y):
        self.cursor = (x, y)

    # ================================================================== slots: wiring

    def _plug(self, u, path):
        p = model.path_of(u)
        return (p + "." + path) if p else None

    @QtCore.Slot(str, str, str, str, result=str)
    @ops.undo_chunk("connect")
    def connectPlugs(self, su, sp, du, dp):
        a, b = self._plug(su, sp), self._plug(du, dp)
        if not a or not b:
            return "node is gone"
        err = ops.connect(a, b)
        if err:
            self.status(err)
            return err
        extra, how = self._bulk_connect(su, sp, du, dp)
        self.status("Connected %s -> %s%s" % (a, b, " (+%d %s)" % (extra, how) if extra else ""))
        return err

    def _bulk_connect(self, su, sp, du, dp):
        """One dragged wire, many connections (Options > Bulk connect):
        - both ends selected: the pair teaches a name rule (skin_* -> drv_*) and every other
          selected node connects to its renamed partner; selected nodes of the two types are
          paired in selection order when no name follows the rule;
        - only the destination selected: the source feeds the same input on every selected
          node of the destination's type.
        -> (count, description)."""
        if not getattr(self, "bulk", True) or su == du:
            return 0, ""
        live = [u for u in self.sel if u in self.infos and u not in self.dead]
        if du not in live or len(live) < 2:
            return 0, ""
        paths = dict((u, model.path_of(u)) for u in live)
        made = 0
        if su in live:
            names = [paths[u] for u in live if paths[u]]
            found = naming.pairs(paths[su], paths[du], names)
            how = "by similar names"
            if not found:
                ta, tb = cmds.nodeType(paths[su]), cmds.nodeType(paths[du])
                xs = [paths[u] for u in live if u not in (su, du) and cmds.nodeType(paths[u]) == ta]
                ys = [paths[u] for u in live if u not in (su, du) and cmds.nodeType(paths[u]) == tb]
                if ta != tb and xs and len(xs) == len(ys):
                    found = list(zip(xs, ys))
                    how = "by selection order"
            for x, y in found:
                if ops.plug_exists(x + "." + sp) and ops.plug_exists(y + "." + dp) \
                        and not ops.connect(x + "." + sp, y + "." + dp):
                    made += 1
            return made, how
        src = self._plug(su, sp)
        kind = cmds.nodeType(paths[du])
        for u in live:
            if u == du or cmds.nodeType(paths[u]) != kind:
                continue
            if ops.plug_exists(paths[u] + "." + dp) and not ops.connect(src, paths[u] + "." + dp):
                made += 1
        return made, "to the selected %s nodes" % kind

    @QtCore.Slot(str, str, 'QVariant')
    @ops.undo_chunk('distribute wire')
    def distributeWire(self, su, sp, targets):
        source = self._plug(su, sp)
        if not source:
            self.status('Source node is gone')
            return
        connected, errors, seen = 0, [], set()
        for target in _js(targets) or []:
            dest = self._plug(target['nid'], target['key'])
            if not dest or dest in seen:
                continue
            seen.add(dest)
            if ops.source_of(dest) == source:
                continue
            error = ops.connect(source, dest)
            if error:
                errors.append(error)
            else:
                connected += 1
        self.status('Connected %d inputs%s' % (connected,
                    '; ' + errors[0] if errors else ''))

    @QtCore.Slot(str, str, str, str, result=str)
    def rerouteInput(self, du, dp, nu, np_):
        old = self._plug(du, dp)
        new = self._plug(nu, np_) if nu else ""
        err = ops.reroute_input(old, new)
        self.status(err or ("Moved input to %s" % new if new else "Disconnected %s" % old))
        return err

    @QtCore.Slot("QVariant")
    def disconnectWires(self, ids):
        ids = _js(ids) or []
        dsts = []
        for w in self.wires:
            if w["id"] in ids:
                d = self._plug(w["dst"], w["dstPlug"])
                if d:
                    dsts.append(d)
        if dsts:
            cut = ops.disconnect_inputs(dsts)
            self.status("Disconnected %d connection%s" % (len(cut), "" if len(cut) == 1 else "s"))

    # ================================================================== slots: node display

    @QtCore.Slot(str, str)
    def toggleExpand(self, u, path):
        v = self._view_for(u)
        if path in v.expanded:
            v.expanded.discard(path)
        else:
            v.expanded.add(path)
        self._queue(changed=[u])

    @QtCore.Slot(str)
    def toggleFold(self, u):
        v = self._view_for(u)
        cur = v.mode or self.tab.get("mode", "connected")
        v.mode = "connected" if cur == "simple" else "simple"
        self._queue(changed=[u])

    @QtCore.Slot(str)
    def toggleFoot(self, u):
        """The "+N more" foot and node RMB "Show all attributes": every visible attribute
        of this node, and back to the board's mode."""
        v = self._view_for(u)
        v.mode = None if v.mode == model.ALL else model.ALL
        self._queue(changed=[u])

    @QtCore.Slot(str)
    def toggleFilter(self, u):
        v = self._view_for(u)
        v.filter_open = not v.filter_open
        if not v.filter_open:
            v.filter_text = ""
        self._queue(changed=[u])

    @QtCore.Slot(str, str)
    def setFilter(self, u, text):
        v = self._view_for(u)
        v.filter_text = text
        self._queue(changed=[u])

    @QtCore.Slot(bool)
    def setAllFilters(self, on):
        for u in self.infos:
            v = self._view_for(u)
            v.filter_open = on
            if not on:
                v.filter_text = ""
        self._queue(changed=list(self.infos))

    @QtCore.Slot(str)
    def displayMode(self, mode):
        """Keys 1/2/3: the selection, or the whole board when nothing is selected."""
        if self.sel:
            for u in self.sel:
                self._view_for(u).mode = mode
            self._queue(changed=list(self.sel))
        else:
            self.setBoardMode(mode)

    @QtCore.Slot(str)
    def setBoardMode(self, mode):
        self.tab["mode"] = mode
        for u in self.infos:
            self._view_for(u).mode = None
        self.modeChanged.emit(mode)
        self._queue(changed=list(self.infos))

    # ================================================================== slots: values

    @QtCore.Slot(str, str, str)
    def setValue(self, u, path, text):
        plug = self._plug(u, path)
        if not plug:
            return
        err = ops.set_value(plug, text)
        self.status(err or "%s = %s" % (plug, text))
        self._queue(changed=[u])

    @QtCore.Slot(str, str)
    def toggleBool(self, u, path):
        plug = self._plug(u, path)
        if plug:
            ops.set_value(plug, "off" if cmds.getAttr(plug) else "on")
            self._queue(changed=[u])

    @QtCore.Slot(str, str, result="QVariant")
    def enumOptions(self, u, path):
        """Rows of the Blender-style enum list (Board.qml openEnum)."""
        mp = model.find_plug(u, path)
        if mp is None:
            return None
        return {"items": [{"i": i, "name": n} for i, n in model.enum_options(mp.attribute())],
                "cur": mp.asShort(), "label": model.nice_name(path.split(".")[-1].split("[")[0])}

    @QtCore.Slot(str, str, int)
    def stepEnum(self, u, path, step):
        mp = model.find_plug(u, path)
        if mp is None:
            return
        idx = [i for i, _ in model.enum_options(mp.attribute())]
        if mp.asShort() in idx:
            k = idx.index(mp.asShort()) + step
            if 0 <= k < len(idx):
                self.setValue(u, path, str(idx[k]))

    @QtCore.Slot(str, str, result="QVariant")
    def valueMeta(self, u, path):
        """Slide parameters of a number field: current value, pixels-to-units, snaps, limits."""
        mp = model.find_plug(u, path)
        if mp is None or mp.isLocked or (mp.isDestination and not mp.source().isNull):
            return None
        return ops.slide_meta(mp)

    @staticmethod
    def _silently(fn):
        """Live values while dragging: no undo entry per mouse move (commit adds one)."""
        state = cmds.undoInfo(q=True, stateWithoutFlush=True)
        cmds.undoInfo(stateWithoutFlush=False)
        try:
            fn()
        finally:
            cmds.undoInfo(stateWithoutFlush=state)

    def _set_rows(self, rows, col):
        for row in _js(rows) or []:
            plug = self._plug(row[0], row[1])
            if plug:
                ops.set_value(plug, row[col])

    @QtCore.Slot("QVariant")
    def previewValues(self, rows):
        self._silently(lambda: self._set_rows(rows, 2))

    @QtCore.Slot("QVariant")
    def revertValues(self, rows):
        rows = _js(rows) or []
        self._silently(lambda: self._set_rows(rows, 2))
        self._queue(changed=list(set(r[0] for r in rows if r[0] in self.infos)), rewire=False)

    @QtCore.Slot("QVariant")
    def commitValues(self, rows):
        """Back to the start values silently, then the final ones as ONE undo step."""
        rows = [list(r) for r in _js(rows) or []]
        self._silently(lambda: self._set_rows(rows, 2))

        @ops.undo_chunk("set values")
        def commit():
            errs = []
            for u, path, _, text in rows:
                plug = self._plug(u, path)
                err = ops.set_value(plug, text) if plug else "node is gone"
                if err:
                    errs.append(err)
            return errs
        errs = commit()
        if errs:
            self.status(errs[0])
        elif len(rows) == 1:
            self.status("%s = %s" % (self._plug(rows[0][0], rows[0][1]), rows[0][3]))
        else:
            self.status("Set %d values" % len(rows))
        self._queue(changed=list(set(r[0] for r in rows if r[0] in self.infos)), rewire=False)

    def _popup(self, menu):
        self._menu = menu                 # keep a Python reference while it is open
        menu.popup(QtGui.QCursor.pos())

    # ================================================================== slots: menus

    @QtCore.Slot(str, str)
    def portMenu(self, u, path):
        plug = self._plug(u, path)
        if not plug:
            return
        forms = ops.copy_forms(plug)
        menu = QtWidgets.QMenu()
        for key, label in (("attr", "Copy attribute name"), ("node", "Copy node.attr"),
                           ("dag", "Copy full DAG path")):
            act = menu.addAction("%s    %s" % (label, forms[key]))
            act.triggered.connect(lambda _=False, t=forms[key]: self.copyText(t))
        menu.addSeparator()
        dis = menu.addAction("Disconnect input")
        dis.setEnabled(bool(ops.source_of(plug)))
        dis.triggered.connect(lambda _=False: ops.disconnect_inputs([plug]))
        v = self._view_for(u)
        pin = menu.addAction("Pin in connected mode")
        pin.setCheckable(True)
        pin.setChecked(path in v.pinned)
        pin.triggered.connect(lambda _=False: self._toggle_pin(u, path))
        self._popup(menu)

    def _toggle_pin(self, u, path):
        v = self._view_for(u)
        if path in v.pinned:
            v.pinned.discard(path)
        else:
            v.pinned.add(path)
        self._queue(changed=[u])

    @QtCore.Slot(str)
    def copyText(self, text):
        QtWidgets.QApplication.clipboard().setText(text)
        self.status("Copied " + text)

    # ================================================================== graph clipboard

    def _capture_fragment(self):
        ids = [u for u in self.sel if u in self.infos and u not in self.dead
               and model.path_of(u)]
        snapshot = fragment.capture([model.path_of(u) for u in ids])
        self._sync_tab_views()
        x0 = min(self.infos[u]['x'] for u in ids)
        y0 = min(self.infos[u]['y'] for u in ids)
        snapshot['layout'] = {u: {
            'offset': [self.infos[u]['x'] - x0, self.infos[u]['y'] - y0],
            'view': dict(self.tab['views'].get(u) or {},
                         mode=self._view_for(u).mode or self.tab.get('mode', 'connected')),
            'width': self.store.width(u),
        } for u in ids}
        return snapshot

    @QtCore.Slot()
    def copyFragment(self):
        try:
            snapshot = self._capture_fragment()
            mime = QtCore.QMimeData()
            mime.setData(FRAGMENT_MIME, json.dumps(snapshot).encode('utf-8'))
            QtWidgets.QApplication.clipboard().setMimeData(mime)
            self.status('Copied %d nodes with internal connections' % len(snapshot['selected']))
        except (RuntimeError, ValueError, OSError) as e:
            self.status(str(e).strip())

    def _clipboard_fragment(self):
        clipboard = QtWidgets.QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime is None or not mime.hasFormat(FRAGMENT_MIME):
            raise ValueError('Copy a graph fragment in NodeX first')
        snapshot = json.loads(bytes(mime.data(FRAGMENT_MIME)).decode('utf-8'))
        if not isinstance(snapshot, dict) or snapshot.get('version') != 1:
            raise ValueError('Unsupported NodeX fragment')
        return snapshot

    @ops.undo_chunk('paste fragment')
    def _paste_fragment(self, snapshot, x, y):
        if self.locked:
            self.status('Unlock the graph to paste nodes')
            return
        count = len(snapshot['selected'])
        if len(self.infos) + count > self.max_nodes:
            self.status('Paste needs %d free slots; raise Options > Node limit' % count)
            return
        mapping = fragment.paste(snapshot)
        ids = [mapping[u] for u in snapshot['selected']]
        for old, new in mapping.items():
            meta = snapshot['layout'][old]
            dx, dy = meta['offset']
            self.store.set_pos(new, x + dx, y + dy)
            self.tab['views'][new] = meta['view']
            if meta.get('width'):
                self.store.set_width(new, meta['width'])
        self.add_nodes(ids, arrange_new=False, force=True)
        self.sel = ids
        self._emit_selection()
        self._select_in_maya()
        self.status('Pasted %d nodes; external connections excluded' % count)

    @QtCore.Slot(float, float)
    def pasteFragment(self, x, y):
        try:
            self._paste_fragment(self._clipboard_fragment(), x, y)
        except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
            self.status(str(e).strip())

    @QtCore.Slot()
    def duplicateFragment(self):
        try:
            self._duplicate_nodes()
        except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
            self.status(str(e).strip())

    @ops.undo_chunk('duplicate nodes')
    def _duplicate_nodes(self):
        if self.locked:
            self.status('Unlock the graph to duplicate nodes')
            return
        ids = [u for u in self.sel if u in self.infos and u not in self.dead
               and model.path_of(u)]
        if not ids:
            raise ValueError('Select nodes to duplicate')
        if len(self.infos) + len(ids) > self.max_nodes:
            self.status('Duplicate needs %d free slots; raise Options > Node limit' % len(ids))
            return
        self._sync_tab_views()
        # Match Maya's standard Duplicate: copy shapes and hierarchy under the same parent.
        copies = cmds.duplicate([model.path_of(u) for u in ids],
                                returnRootsOnly=True, fullPath=True) or []
        new_ids = model.uuids_of(copies)
        placed = set()
        for old, new in zip(ids, new_ids):
            if new in placed:
                continue  # Selecting a transform and its shape returns the same new root twice.
            placed.add(new)
            self.store.set_pos(new, self.infos[old]['x'] + GRID * 2,
                               self.infos[old]['y'] + GRID * 2)
            self.tab['views'][new] = dict(self.tab['views'].get(old) or {},
                                         mode=self._view_for(old).mode or self.tab.get('mode', 'connected'))
            if self.store.width(old):
                self.store.set_width(new, self.store.width(old))
        self.sel = list(dict.fromkeys(new_ids))
        self.add_nodes(self.sel, arrange_new=False, force=True)
        self._emit_selection()
        self._select_in_maya()
        self.status('Duplicated %d nodes with shapes and hierarchy' % len(self.sel))

    @QtCore.Slot(str)
    def nodeMenu(self, u):
        if u not in self.sel:
            self.sel = [u]
            self._emit_selection()
            self._select_in_maya()
        menu = QtWidgets.QMenu()
        if (self.infos.get(u) or {}).get("conv"):
            menu.addAction("Hide unit conversion node", lambda: self.collapseConversion(u))
            menu.addSeparator()
        a = menu.addAction("Show all attributes", lambda: self.toggleFoot(u))
        a.setCheckable(True)
        a.setChecked(self._view_for(u).mode == model.ALL)
        a = menu.addAction("Rename\tF2", lambda: self.renameRequested.emit(u))
        a.setEnabled(u not in self.dead)
        menu.setToolTipsVisible(True)
        bypass = menu.addAction('Delete inbetween', lambda: self.deleteInbetween(u))
        try:
            if self.locked or u in self.dead:
                raise ValueError('Unlock the graph and select a live node')
            plan = ops.delete_inbetween_plan(model.path_of(u))
            bypass.setToolTip('Bypass %d active pairs and delete this node' % plan['pairs'])
        except (RuntimeError, ValueError, TypeError) as e:
            bypass.setEnabled(False)
            bypass.setToolTip(str(e).strip())
        menu.addSeparator()
        self.fill_edit_menu(menu)
        self._popup(menu)

    @QtCore.Slot(str, str)
    def renameNode(self, u, text):
        """the name typed into a node header (double-click on the name, or F2)."""
        old = model.path_of(u)
        if old is None or u in self.dead:
            return
        new, err = ops.rename_node(old, text)
        if err:
            self.status(err)
        elif new != old:
            self.status("Renamed %s to %s" % (old, new))
        self._queue(changed=[u], rewire=False)

    # ================================================================== frames (Blender)

    FRAME_COLORS = (("Grey", "#5A5A5E"), ("Red", "#8C3B3B"), ("Orange", "#8C5A2E"),
                    ("Yellow", "#857A33"), ("Green", "#3D7040"), ("Teal", "#2F6E6A"),
                    ("Blue", "#33558C"), ("Violet", "#5E428A"), ("Pink", "#874065"))

    def _frames(self):
        return self.tab.setdefault("frames", [])

    def _frame(self, fid):
        return next((f for f in self._frames() if f["id"] == fid), None)

    def _emit_frames(self):
        self.framesChanged.emit(json.dumps(self._frames()))
        self._mark_modified()

    def _fit_rect(self, ids, pad=26):
        xs = [(self.infos[u]["x"], self.infos[u]["y"], self.infos[u]["width"], self.infos[u]["height"])
              for u in ids if u in self.infos]
        if not xs:
            return None
        x0 = min(r[0] for r in xs) - pad
        y0 = min(r[1] for r in xs) - pad - 40          # room for the label and the node type line
        x1 = max(r[0] + r[2] for r in xs) + pad
        y1 = max(r[1] + r[3] for r in xs) + pad
        return x0, y0, x1 - x0, y1 - y0

    @QtCore.Slot()
    def addFrame(self):
        """Ctrl+J: a frame around the selection (Blender "Join in new frame"), else at the cursor."""
        ids = [u for u in self.sel if u in self.infos]
        rect = self._fit_rect(ids) if ids else None
        if rect is None:
            cx, cy = self.cursor or self._view_centre()
            rect = (cx - 160, cy - 40, 320, 200)
        n = 1 + max([int(f["id"][1:]) for f in self._frames() if f["id"][1:].isdigit()] or [0])
        self._frames().append({"id": "f%d" % n, "x": rect[0], "y": rect[1], "w": rect[2], "h": rect[3],
                               "color": self.FRAME_COLORS[6][1], "label": "Frame %d" % n, "text": ""})
        self._emit_frames()
        self.status("Frame added%s; drag its title to move it with its nodes"
                    % (" around %d nodes" % len(ids) if ids else ""))

    @QtCore.Slot(str, "QVariant")
    def setFrame(self, fid, props):
        f = self._frame(fid)
        props = _js(props) or {}
        if f is None:
            return
        for k in ("x", "y", "w", "h", "color", "label", "text"):
            if k in props:
                f[k] = props[k]
        self._emit_frames()

    @QtCore.Slot(str)
    def deleteFrame(self, fid):
        self.tab["frames"] = [f for f in self._frames() if f["id"] != fid]
        self._emit_frames()

    @QtCore.Slot(str, "QVariant")
    def frameMenu(self, fid, members):
        f = self._frame(fid)
        if f is None:
            return
        members = [u for u in _js(members) or [] if u in self.infos]
        menu = QtWidgets.QMenu()
        colors = menu.addMenu("Color")
        for name, c in self.FRAME_COLORS:
            pm = QtGui.QPixmap(14, 14)
            pm.fill(QtGui.QColor(c))
            a = colors.addAction(QtGui.QIcon(pm), name, lambda c=c: self.setFrame(fid, {"color": c}))
            a.setCheckable(True)
            a.setChecked(f["color"] == c)
        colors.addAction("Custom...", lambda: self._custom_frame_color(fid))
        menu.addAction("Rename\tdouble-click title", lambda: self.frameEditRequested.emit(fid, "label"))
        menu.addAction("Edit comment\tdouble-click body", lambda: self.frameEditRequested.emit(fid, "text"))
        menu.addSeparator()
        menu.addAction("Fit to nodes (%d)" % len(members), lambda: self._fit_frame(fid, members)).setEnabled(
            bool(members))
        menu.addAction("Select nodes in frame", lambda: self.selectNodes(members, False)).setEnabled(bool(members))
        menu.addSeparator()
        menu.addAction("Delete frame (keep nodes)", lambda: self.deleteFrame(fid))
        self._popup(menu)

    def _fit_frame(self, fid, members):
        rect = self._fit_rect(members)
        if rect:
            self.setFrame(fid, {"x": rect[0], "y": rect[1], "w": rect[2], "h": rect[3]})

    def _custom_frame_color(self, fid):
        f = self._frame(fid)
        c = QtWidgets.QColorDialog.getColor(QtGui.QColor(f["color"]), QtWidgets.QApplication.activeWindow(),
                                            "Frame color")
        if c.isValid():
            self.setFrame(fid, {"color": c.name()})

    @QtCore.Slot(float, float)
    def canvasMenu(self, x, y):
        self.cursor = (x, y)
        menu = QtWidgets.QMenu()
        menu.addAction("Create node...\tTab", lambda: self.createRequested.emit(x, y))
        n = len([u for u in self.sel if u in self.infos])
        menu.addAction("Frame selected nodes\tCtrl+J" if n else "Add frame\tCtrl+J", self.addFrame)
        menu.addAction("Add selected\t", self.addSelected)
        self.fill_arrange_menu(menu.addMenu("Arrange"))
        menu.addSeparator()
        self.fill_edit_menu(menu)
        self._popup(menu)

    # ================================================================== conversion nodes

    def _wire(self, wid):
        for w in self.wires:
            if w["id"] == wid:
                return w
        return None

    @QtCore.Slot(str)
    def wireMenu(self, wid):
        w = self._wire(wid)
        if w is None:
            return
        menu = QtWidgets.QMenu()
        if w.get("conv"):
            menu.addAction("Show unit conversion node", lambda: self.expandConversion(wid))
        for end in (w["src"], w["dst"]):
            if (self.infos.get(end) or {}).get("conv"):
                menu.addAction("Hide unit conversion node", lambda e=end: self.collapseConversion(e))
        if not menu.isEmpty():
            menu.addSeparator()
        menu.addAction("Disconnect\tDel", lambda: self.disconnectWires([wid]))
        between = menu.addMenu('Inbetween')
        between.setEnabled(not self.locked and len(self.infos) < self.max_nodes)
        self._fill_utility_menu(between, w)
        menu.addSeparator()
        menu.addAction('Move to new group', lambda: self.moveToNewGroup([w['src'], w['dst']]))
        self._popup(menu)

    @QtCore.Slot(str)
    def deleteInbetween(self, u):
        if self.locked or u in self.dead:
            return
        node = model.path_of(u)
        if not node:
            return
        neighbours = model.neighbours(u, 'both')
        try:
            plan = ops.delete_inbetween(node)
        except (RuntimeError, ValueError, TypeError) as e:
            self.status(str(e).strip())
            return
        self.remove_nodes([u], remember=True)
        self.sel = [uid for uid in self.sel if uid != u]
        self._emit_selection()
        self._queue(changed=[uid for uid in neighbours if uid in self.infos and uid not in self.dead])
        self.status('Deleted %s; bypassed %d active pairs to %d inputs' %
                    (node, plan['pairs'], len(plan['routes'])))

    def _wire_context(self, w):
        source = self._plug(w['src'], w['srcPlug'])
        dest = self._plug(w['dst'], w['dstPlug'])
        sc = model.attr_class(ops._mplug(source).attribute())
        dc = model.attr_class(ops._mplug(dest).attribute())
        return source, dest, sc, dc

    def _fill_utility_menu(self, menu, w):
        """Search..., then the eight best-ranked inbetween nodes: a click inserts with the shown
        sockets, Shift+click opens the socket chooser."""
        menu.addAction('Search...', lambda wid=w['id']: self.searchInbetween(wid))
        menu.addSeparator()
        try:
            source, dest, sc, dc = self._wire_context(w)
            rows = catalog.get().inbetween(sc, dc, src_hint=w['srcPlug'], dst_hint=w['dstPlug'], limit=8)
        except (RuntimeError, ValueError) as e:
            menu.addAction(str(e).strip()).setEnabled(False)
            return
        for t, i, o, _, _ in rows:
            menu.addAction('%s    %s -> %s' % (t, i, o),
                           lambda _=False, t=t, i=i, o=o, wid=w['id']: self._inbetween_pick(
                               wid, (t, i, o), bool(QtWidgets.QApplication.keyboardModifiers()
                                                    & QtCore.Qt.ShiftModifier)))
        if len(menu.actions()) == 2:
            menu.addAction('No compatible nodes').setEnabled(False)

    @QtCore.Slot(str)
    def searchInbetween(self, wid):
        """RMB wire > Inbetween...: search every node type that fits both ends of the wire."""
        w = self._wire(wid)
        if w is None or self.open_search is None:
            return
        try:
            source, dest, sc, dc = self._wire_context(w)
        except (RuntimeError, ValueError) as e:
            self.status(str(e).strip())
            return

        def rows(q):
            found = catalog.get().inbetween(sc, dc, query=q, src_hint=w['srcPlug'], dst_hint=w['dstPlug'])
            if not found:
                return [{'label': 'No node fits %s -> %s' % (sc, dc), 'head': True}]
            return [{'label': t, 'icon': t, 'data': (t, i, o), 'desc': '%s \u2192 %s' % (i, o)}
                    for t, i, o, _, _ in found]
        self.open_search(rows, lambda data, alt: self._inbetween_pick(wid, data, alt),
                         title='Insert into %s \u2192 %s' % (source, dest),
                         hint='Enter insert with the shown sockets  \u00b7  Shift+Enter choose sockets')

    def _inbetween_pick(self, wid, data, alt):
        t, i, o = data
        if alt:
            self.chooseInbetween(wid, t)
            return
        wire = self._wire(wid)
        if not wire or self.locked:
            return
        try:
            self._insert_inbetween(wire, t, i, o)
            catalog.Catalog.record(t)
        except (RuntimeError, ValueError, TypeError) as e:
            self.status(str(e).strip())

    # ================================================================== link-drag search (Blender)

    @QtCore.Slot(str, str, str, float, float)
    def linkSearch(self, u, path, side, x, y):
        """A new wire dropped on empty canvas: pick a node + socket, create it there, connect."""
        if self.locked or self.open_search is None or u in self.dead:
            return
        plug = self._plug(u, path)
        if not plug:
            return
        try:
            cls = model.attr_class(ops._mplug(plug).attribute())
        except (RuntimeError, ValueError):
            return
        output = side == 'out'

        def rows(q):
            found = catalog.get().link_targets(cls, output, query=q, hint=path)
            return [{'label': '%s  \u25b8  %s' % (t, p), 'icon': t, 'data': (t, p), 'desc': c}
                    for t, p, c in found] or [{'label': 'No node fits a %s wire' % cls, 'head': True}]
        self.open_search(rows, lambda data, alt: self._link_create(u, path, output, data, (x, y)),
                         title='Connect %s (%s)' % (plug, cls),
                         hint='"type.socket" narrows the socket, e.g. mult.matrixIn')

    @ops.undo_chunk('create and connect')
    def _link_create(self, u, path, output, data, pos):
        t, socket = data
        try:
            name = self.create_at(t, (pos[0] + (110 if output else -110), pos[1]))
            nu = model.uuids_of([name])[0]
            if output:
                err = self.connectPlugs(u, path, nu, socket)
            else:
                err = self.connectPlugs(nu, socket, u, path)
            if err:
                self.status(err)
        except (RuntimeError, ValueError, IndexError) as e:
            self.status(str(e).strip())

    # ================================================================== presets (JSON fragments)

    def create_rows(self, q):
        """Tab create rows: Recent + categories when empty, ranked types and presets when typing."""
        cat = catalog.get()
        types = cat.entries()
        rows = []
        if not q:
            recent = cat.recent(6)
            if recent:
                rows.append({'label': 'Recent', 'head': True})
                rows += [{'label': t, 'icon': t, 'data': t} for t in recent]
            for label, group in catalog.CREATE_GROUPS:
                rows.append({'label': label, 'head': True})
                rows += [{'label': t, 'icon': t, 'data': t} for t in group if t in types]
            plist = presets.entries()
            if plist:
                rows.append({'label': 'Presets', 'head': True})
                rows += [{'label': n, 'data': 'preset:' + p, 'desc': 'preset \u00b7 %d nodes' % k}
                         for n, p, k in plist]
            return rows
        ql = q.lower()
        for n, p, k in presets.entries():
            if ql in n.lower():
                rows.append({'label': n, 'data': 'preset:' + p, 'desc': 'preset \u00b7 %d nodes' % k})
        rows += [{'label': t, 'icon': t, 'data': t, 'desc': types[t].cls.split(':')[-1].split('/')[0]}
                 for t in cat.search(q)]
        return rows

    def fill_presets_menu(self, menu):
        menu.clear()
        n = len([u for u in self.sel if u not in self.dead])
        menu.addAction('Save selection as preset...', self.save_preset).setEnabled(n > 0)
        menu.addAction('Load preset from file...', self.load_preset_file).setEnabled(not self.locked)
        menu.addAction('Open presets folder', lambda: QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(presets.folder())))
        plist = presets.entries()
        if plist:
            menu.addSeparator()
        for name, path, k in plist:
            a = menu.addAction('%s    (%d nodes)' % (name, k),
                               lambda p=path: self.insert_preset(p, *self._view_centre()))
            a.setEnabled(not self.locked)

    def _view_centre(self):
        v = self.tab.get('view') or {}
        z = v.get('z', 1.0) or 1.0
        w, h = getattr(self, 'view_size', (800.0, 600.0))
        return ((w / 2.0 - v.get('x', 0.0)) / z, (h / 2.0 - v.get('y', 0.0)) / z)

    def save_preset(self):
        ids = [u for u in self.sel if u in self.infos and u not in self.dead]
        if not ids:
            self.status('Select nodes to save as a preset')
            return
        name, ok = QtWidgets.QInputDialog.getText(QtWidgets.QApplication.activeWindow(),
                                                  'Save NodeX preset', 'Preset name:')
        if not ok or not name.strip():
            return
        try:
            path = presets.write(self._capture_fragment(), name.strip())
        except (RuntimeError, ValueError, OSError) as e:
            self.status(str(e).strip())
            return
        self.status('Saved preset %s (%d nodes) to %s' % (name.strip(), len(ids), path))

    def load_preset_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            QtWidgets.QApplication.activeWindow(), 'Load NodeX preset', presets.folder(),
            'NodeX preset (*.json)')
        if path:
            self.insert_preset(path, *self._view_centre())

    def insert_preset(self, path, x, y):
        """Rebuild a saved fragment at (x, y): fresh nodes, internal connections, layout."""
        try:
            data = presets.read(path)
            self._paste_fragment(data['snapshot'], x, y)
        except (RuntimeError, ValueError, KeyError, TypeError, OSError) as e:
            self.status(str(e).strip())
            return
        self.status('Inserted preset %s' % data['name'])

    # ================================================================== groups

    def moveToNewGroup(self, ids):
        """RMB wire > Move to new group: a fresh tab with just these nodes, laid out side by side."""
        ids = [u for u in dict.fromkeys(ids) if model.path_of(u)]
        if not ids:
            return
        names = [model.path_of(u).split('|')[-1] for u in ids]
        self.new_tab()
        self.rename_tab(self.store.active, ' > '.join(names)[:40])
        self.add_nodes(ids, cursor=None, arrange_new=True, force=True)
        self.sel = list(ids)
        self._emit_selection()
        QtCore.QTimer.singleShot(80, lambda: self.frameRequested.emit(True))

    def chooseInbetween(self, wid, type_name):
        from .inbetween import SocketDialog
        wire = self._wire(wid)
        if not wire or self.locked:
            return
        source = self._plug(wire['src'], wire['srcPlug'])
        dest = self._plug(wire['dst'], wire['dstPlug'])
        try:
            sc = model.attr_class(ops._mplug(source).attribute())
            dc = model.attr_class(ops._mplug(dest).attribute())
            inputs = [(p, c) for p, c in ops.type_socket_options(type_name, False) if ops.compatible_sockets(sc, c)]
            outputs = [(p, c) for p, c in ops.type_socket_options(type_name, True) if ops.compatible_sockets(c, dc)]
            if not inputs or not outputs:
                self.status('%s has no compatible input/output pair for this wire' % type_name)
                return
            dialog = SocketDialog(type_name, source, dest, inputs, outputs,
                                  QtWidgets.QApplication.activeWindow())
            if exec_(dialog) == QtWidgets.QDialog.Accepted:
                self._insert_inbetween(wire, type_name, *dialog.attributes())
        except (RuntimeError, ValueError, TypeError) as e:
            self.status(str(e).strip())

    @ops.undo_chunk('inbetween')
    def _insert_inbetween(self, wire, type_name, input_attr, output_attr):
        if self.locked or len(self.infos) >= self.max_nodes:
            self.status('Unlock the graph and provide one free node slot to insert a node')
            return
        source = self._plug(wire['src'], wire['srcPlug'])
        dest = self._plug(wire['dst'], wire['dstPlug'])
        node = ops.insert_utility(source, dest, type_name, input_attr, output_attr)
        uid = model.uuids_of([node])[0]
        a, b = self.infos[wire['src']], self.infos[wire['dst']]
        pos = ((a['x'] + a['width'] + b['x']) / 2 - 90,
               (a['y'] + wire.get('srcY', 14) + b['y'] + wire.get('dstY', 14)) / 2 - 40)
        self.add_nodes([uid], cursor=pos, force=True)
        self.sel = [uid]
        self._emit_selection()
        self._select_in_maya()
        self.status('Inserted %s: %s -> %s' % (node, input_attr, output_attr))
        return node

    @QtCore.Slot(str)
    def expandConversion(self, wid):
        """Put the unitConversion hidden on a wire onto the board, between its two ends."""
        w = self._wire(wid)
        if w is None or not w.get("conv") or self.locked:
            return
        cu = w["conv"]
        a, b = self.infos.get(w["src"]), self.infos.get(w["dst"])
        if a is None or b is None:
            return
        self._view_for(cu).pinned.add("conversionFactor")   # the value worth editing
        if not self.store.pos(cu):
            x = (a["x"] + a["width"] + b["x"]) / 2.0 - 90
            y = (a["y"] + w.get("srcY", 14) + b["y"] + w.get("dstY", 14)) / 2.0 - 40
            self.store.set_pos(cu, x, y)
        self.add_nodes([cu], cursor=None, arrange_new=False, force=True)
        self.status("Showing %s" % model.path_of(cu))

    @QtCore.Slot(str)
    def collapseConversion(self, u):
        """Fold a conversion node back into its wire (double chevron)."""
        if (self.infos.get(u) or {}).get("conv"):
            self.remove_nodes([u], remember=False)

    def fill_edit_menu(self, menu):
        n = len(self.sel)
        if n == 2:
            menu.addAction('Find connections between', self.findConnectionsBetween)
            menu.addSeparator()
        menu.addAction('Copy graph fragment\tCtrl+C', self.copyFragment).setEnabled(n > 0)
        clipboard = QtWidgets.QApplication.clipboard()
        mime = clipboard.mimeData()
        menu.addAction('Paste graph fragment\tCtrl+V',
                       lambda: self.pasteFragment(*(self.cursor or (60.0, 60.0)))).setEnabled(
                           not self.locked and mime is not None and mime.hasFormat(FRAGMENT_MIME))
        menu.addAction('Duplicate nodes\tShift+D', self.duplicateFragment).setEnabled(
            n > 0 and not self.locked)
        menu.addSeparator()
        acts = [
            ("Transfer inputs to selected\tAlt+I", lambda: self.transfer("in"), n >= 2),
            ("Transfer outputs to selected\tAlt+O", lambda: self.transfer("out"), n >= 2),
            ("Transfer all connections\tAlt+T", lambda: self.transfer("all"), n >= 2),
            ("Link by name\tK / Alt+L", lambda: self.linkByName(False), n >= 2),
            ("Link by name, replace\tShift+K / Alt+Shift+L", lambda: self.linkByName(True), n >= 2),
            ("Swap inputs of two selected\tAlt+S", self.swapSelected, n == 2),
        ]
        for label, fn, ok in acts:
            a = menu.addAction(label, fn)
            a.setEnabled(ok)
        menu.addSeparator()
        a = menu.addAction("Remove from graph", self.removeSelected)
        a.setEnabled(n > 0)
        a = menu.addAction("Delete nodes\tDel", self.deleteSelected)
        a.setEnabled(n > 0)

    @QtCore.Slot()
    def findConnectionsBetween(self):
        ids = [u for u in dict.fromkeys(self.sel) if u in self.infos and u not in self.dead]
        if len(ids) != 2:
            self.status('Select two live nodes to find their connections')
            return
        try:
            found = model.connections_between(*ids)
        except (RuntimeError, ValueError) as e:
            self.status(str(e).strip())
            return
        if not found:
            self.status('No directed connection chain between these nodes')
            return
        # Fold hidden conversions as usual, while respecting explicitly graphed conversion nodes.
        shown = [u for u in found if u in self.infos or model.is_board_candidate(model.obj_from_uuid(u))]
        missing = [u for u in shown if u not in self.infos]
        if missing and self.locked:
            self.status('Unlock the graph to show intermediate nodes')
            return
        if len(self.infos) + len(missing) > self.max_nodes:
            self.status('Connection chains need %d free slots; raise Options > Node limit' % len(missing))
            return
        self.add_nodes(missing, arrange_new=True)
        self._connection_result = shown
        self._queue(changed=shown, wires=True)
        self.status('Found connection chains across %d nodes; click the canvas or Escape to leave' % len(shown))

    # ================================================================== slots: connection ops

    @QtCore.Slot(str, str, bool)
    def lazyConnect(self, su, du, choose):
        source, target = model.path_of(su), model.path_of(du)
        if not source or not target or su == du or su in self.dead or du in self.dead:
            return
        if not choose:
            sp, dp, error = ops.lazy_connect(source, target)
            self.status(error or 'Connected %s.%s -> %s.%s' % (source, sp, target, dp))
            return
        menu = QtWidgets.QMenu()
        inputs = ops.socket_options(target, False)
        for sp, sc in ops.socket_options(source, True):
            compatible = [(dp, dc) for dp, dc in inputs if ops.compatible_sockets(sc, dc)]
            if not compatible:
                continue
            sub = menu.addMenu(sp)
            for dp, dc in compatible:
                occupied = ops.source_of(target + '.' + dp, skip_conversion=False)
                action = sub.addAction(dp + (' (replace)' if occupied else ''),
                                       lambda _=False, s=sp, d=dp: self.connectPlugs(su, s, du, d))
                action.setEnabled(not ops._mplug(target + '.' + dp).isLocked)
        if menu.isEmpty():
            self.status('No compatible sockets on these nodes')
        else:
            self._popup(menu)

    def _lead_and_others(self):
        live = [u for u in self.sel if u not in self.dead]
        if len(live) < 2:
            self.status("Select at least two nodes; the last selected is the lead")
            return None, []
        lead = model.path_of(live[-1])
        others = [model.path_of(u) for u in live[:-1]]
        return lead, [o for o in others if o]

    @QtCore.Slot(str)
    def transfer(self, which):
        lead, others = self._lead_and_others()
        if not lead:
            return
        rep = ops.transfer(lead, others, which)
        self.status("Transferred %d connection%s from %s%s" % (
            len(rep["moved"]), "" if len(rep["moved"]) == 1 else "s", lead,
            ("; skipped %d" % len(rep["skipped"])) if rep["skipped"] else ""))

    @QtCore.Slot(bool)
    def linkByName(self, replace):
        lead, others = self._lead_and_others()
        if not lead:
            return
        res = ops.link_by_name(lead, others, replace)
        self.status("Linked %d attribute%s by name%s" % (
            len(res["made"]), "" if len(res["made"]) == 1 else "s",
            ("; skipped %d" % len(res["skipped"])) if res["skipped"] else ""))

    @QtCore.Slot()
    def swapSelected(self):
        if len(self.sel) != 2:
            return
        a, b = [model.path_of(u) for u in self.sel]
        # Swap every same-named connected input between the two nodes.
        ins_a = dict((ops.split(p)[1], s) for p, s in ops._inputs_of(a))
        ins_b = dict((ops.split(p)[1], s) for p, s in ops._inputs_of(b))
        names = sorted(set(ins_a) | set(ins_b))

        @ops.undo_chunk("swap links")
        def run():
            for n in names:
                pa, pb = a + "." + n, b + "." + n
                if ops.plug_exists(pa) and ops.plug_exists(pb):
                    ops.disconnect_inputs([pa, pb])
                    if n in ins_b:
                        ops.connect(ins_b[n], pa)
                    if n in ins_a:
                        ops.connect(ins_a[n], pb)
        run()
        self.status("Swapped inputs of %s and %s" % (a, b))

    # ================================================================== slots: nodes

    @QtCore.Slot()
    def deleteSelected(self):
        names = [model.path_of(u) for u in self.sel if u not in self.dead]
        dead = [u for u in self.sel if u in self.dead]
        if dead:
            self.remove_nodes(dead)
        names = [n for n in names if n]
        if names:
            ops.delete_nodes(names)
            self.status("Deleted %d node%s" % (len(names), "" if len(names) == 1 else "s"))

    @QtCore.Slot()
    def removeSelected(self):
        if self.locked:
            return
        self.remove_nodes(list(self.sel), remember=False)

    @QtCore.Slot()
    def addSelected(self):
        if self.locked:
            return
        picked = model.uuids_of(cmds.ls(selection=True, long=True) or [])
        uu = self._filter_shapes(picked, keep=picked)
        uu = [u for u in uu if model.is_board_candidate(model.obj_from_uuid(u))]
        added = self.add_nodes(uu, cursor=None)
        self.status("Added %d node%s%s" % (len(added), "" if len(added) == 1 else "s", self._over()))
        if added:
            QtCore.QTimer.singleShot(50, lambda: self.frameRequested.emit(True))

    def add_dropped(self, names, x, y):
        """Nodes dragged in from the Outliner (or any Maya list) and dropped at world x, y."""
        if self.locked:
            self.status("Graph is locked: nothing added")
            return []
        found = cmds.ls(names, long=True) or []
        picked = model.uuids_of(found)
        uu = self._filter_shapes(picked, keep=picked)
        uu = [u for u in uu if model.is_board_candidate(model.obj_from_uuid(u))]
        added = self.add_nodes(uu, cursor=(x, y))
        self.status("Added %d node%s%s" % (len(added), "" if len(added) == 1 else "s", self._over())
                    if added else ("Already on the board" if uu else "Nothing to add from the drop"))
        return added

    @QtCore.Slot()
    def clearGraph(self):
        if self.locked:
            return
        self.remove_nodes(list(self.infos), remember=False)

    def _seeds(self):
        names = cmds.ls(selection=True, long=True) or []
        uu = model.uuids_of(names)
        if not uu:
            uu = list(self.sel)
        return [u for u in uu if model.is_board_candidate(model.obj_from_uuid(u))]

    def set_shapes(self, mode):
        """Display buttons apply to the open tab too: shapes join their transforms, or leave."""
        self.shapes = mode
        cmds.optionVar(stringValue=(SHAPES_VAR, mode))
        if self.locked or not self.infos:
            return
        live = [u for u in self.infos if u not in self.dead]
        if mode == "none":
            shapes = [u for u in live if model.transform_of(u) != u]
            owners = [model.transform_of(u) for u in shapes]
            self.add_nodes([o for o in owners if o not in self.infos], cursor=None, arrange_new=False)
            self.remove_nodes(shapes, remember=True)
            self.status("Graph no shapes: %d shape%s replaced by transforms"
                        % (len(shapes), "" if len(shapes) == 1 else "s"))
        else:
            extra = [v for u in live for v in model.shapes_of(u) if v not in self.infos]
            self.add_nodes(extra, cursor=None, arrange_new=False)
            self.status("Graph all shapes%s: %d shape%s added"
                        % (" except shading networks" if mode == "except" else "", len(extra),
                           "" if len(extra) == 1 else "s"))

    def _filter_shapes(self, uuids, keep=()):
        """Display group: shapes come with their transforms, or are replaced by them."""
        return model.apply_shape_filter(uuids, self.shapes, keep=keep)

    @QtCore.Slot(str)
    def graphConnections(self, direction):
        """Graph input / input+output / output connections of the selection."""
        if self.locked:
            return
        seeds = self._seeds()
        if not seeds:
            self.status("Select nodes in the scene to graph their connections")
            return
        # One spare node tells "exactly at the limit" from "cut at the limit". Shapes filtered
        # out below make the cut land a little short of the limit; not worth a second walk.
        # Shapes walk with their transforms (a mesh's history hangs off the shape, not the
        # transform); "except" stops the walk at shading networks instead of trimming after it.
        if self.shapes != "none":
            seeds = model.apply_shape_filter(seeds, self.shapes, keep=seeds)
        stop = model.is_shading if self.shapes == "except" else None
        found = self._filter_shapes(model.traverse(seeds, direction, self.depth,
                                                   limit=self.max_nodes + 1, stop=stop), keep=seeds)
        cut = len(found) > self.max_nodes
        found = found[:self.max_nodes]
        # Replace the tab's graph with the network, as Maya does; known nodes keep their place.
        drop = [u for u in self.infos if u not in found]
        self.remove_nodes(drop, remember=False)
        added = self.add_nodes(found, cursor=None, arrange_new=True)
        if cut:
            self.status("Graphed the nearest %d nodes: the network is larger than the tab limit "
                        "of %d (Options > Node limit)" % (len(found), self.max_nodes))
        else:
            self.status("Graphed %d node%s" % (len(found), "" if len(found) == 1 else "s"))
        if added:
            QtCore.QTimer.singleShot(50, lambda: self.frameRequested.emit(True))

    @QtCore.Slot()
    def rearrange(self, aspect=None):
        """Explicit layout of the whole tab (the only action besides dragging that moves nodes),
        folded to the view's aspect so a big graph spreads evenly over the canvas."""
        ids = [u for u in self.infos]
        if not ids:
            return
        sizes = dict((u, (self.infos[u]["width"], self.infos[u]["height"])) for u in ids)
        hint = dict((u, (self.store.pos(u) or (0, 0))[1]) for u in ids)
        xs = [self.store.pos(u)[0] for u in ids if self.store.pos(u)]
        ys = [self.store.pos(u)[1] for u in ids if self.store.pos(u)]
        origin = (min(xs) if xs else 60.0, min(ys) if ys else 60.0)
        pos = layout.layered(ids, sizes, self._edges(ids), origin=origin, order_hint=hint)
        aspect = aspect or getattr(self, "view_aspect", 1.6)
        pos = layout.wrap(pos, sizes, aspect=max(0.3, min(4.0, aspect)))
        for u, (x, y) in pos.items():
            self.store.set_pos(u, x, y)
            self.infos[u]["x"], self.infos[u]["y"] = self.store.pos(u)
        self.nodesMoved.emit(dict((u, list(self.store.pos(u))) for u in ids), True)
        self._mark_modified()
        QtCore.QTimer.singleShot(320, lambda: self.frameRequested.emit(True))

    ARRANGE = (
        ("layered", "Layered, fit to view", "Columns by flow, folded to the view's shape"),
        ("flow", "Layered, one flow", "Columns by flow left to right, no folding"),
        ("straighten", "Straighten links", "Keep columns, move nodes so main wires run straight"),
        ("grid", "Grid by category", "Category, then type, then name, in rows"),
        ("row", "Align in a row", "Selection: one row, even gaps (Node Wrangler Align)"),
        ("column", "Align in a column", "Selection: one column, even gaps"),
    )

    def fill_arrange_menu(self, menu):
        n = len([u for u in self.sel if u in self.infos])
        scope = "selection" if n >= 2 else "whole tab"
        for kind, label, tip in self.ARRANGE:
            a = menu.addAction("%s  (%s)" % (label, scope) if kind not in ("row", "column") else label,
                               lambda k=kind: self.arrange(k))
            a.setToolTip(tip)
            a.setEnabled(n >= 2 if kind in ("row", "column") else bool(self.infos))
        menu.setToolTipsVisible(True)

    @QtCore.Slot(str)
    def arrange(self, kind):
        """Arrange variants; two or more selected nodes arrange only themselves."""
        picked = [u for u in self.sel if u in self.infos]
        ids = picked if len(picked) >= 2 else list(self.infos)
        if kind in ("row", "column") and len(picked) < 2:
            self.status("Select two or more nodes to align")
            return
        if not ids:
            return
        if kind == "layered" and len(ids) == len(self.infos):
            self.rearrange()
            return
        sizes = dict((u, (self.infos[u]["width"], self.infos[u]["height"])) for u in ids)
        pos = dict((u, tuple(self.store.pos(u) or (self.infos[u]["x"], self.infos[u]["y"]))) for u in ids)
        origin = (min(p[0] for p in pos.values()), min(p[1] for p in pos.values()))
        if kind in ("layered", "flow"):
            hint = dict((u, pos[u][1]) for u in ids)
            new = layout.layered(ids, sizes, self._edges(ids), origin=origin, order_hint=hint)
            if kind == "layered":
                new = layout.wrap(new, sizes, aspect=getattr(self, "view_aspect", 1.6))
        elif kind == "straighten":
            links = [(w["src"], w.get("srcY", 14), w["dst"], w.get("dstY", 14)) for w in self.wires]
            new = layout.straighten(ids, sizes, pos, links)
        elif kind == "grid":
            def key(u):
                i = self.infos[u]
                return (i.get("category", ""), i.get("type", ""), i.get("name", ""))
            new = layout.grid(ids, sizes, key, origin, aspect=getattr(self, "view_aspect", 1.6))
        elif kind == "row":
            new = layout.align_row(ids, sizes, pos)
        elif kind == "column":
            new = layout.align_column(ids, sizes, pos)
        else:
            return
        for u, (x, y) in new.items():
            self.store.set_pos(u, x, y)
            self.infos[u]["x"], self.infos[u]["y"] = self.store.pos(u)
        self.nodesMoved.emit(dict((u, list(self.store.pos(u))) for u in new), True)
        self._mark_modified()
        self.status("Arranged %d nodes: %s" % (len(new), dict((k, l) for k, l, _ in self.ARRANGE)[kind]))
        if len(ids) == len(self.infos):
            QtCore.QTimer.singleShot(320, lambda: self.frameRequested.emit(True))

    @QtCore.Slot(float, float)
    def openCreate(self, x, y):
        self.cursor = (x, y)
        self.createRequested.emit(x, y)

    def create_at(self, type_name, pos):
        name = ops.create_node(type_name)
        catalog.Catalog.record(type_name)
        u = model.uuids_of([name])[0]
        self.add_nodes([u], cursor=pos, force=True)
        self.sel = [u]
        self._emit_selection()
        self._select_in_maya()
        self.status("Created %s" % name)
        return name

    @QtCore.Slot(str)
    def setQuery(self, text):
        """Find field: nodes matched by an attribute reveal the matching rows."""
        q = (text or "").strip().lower()
        if q == self.query:
            return
        self.query = q
        hits = set(u for u, i in self.infos.items() if q and q in i.get("search", ""))
        changed = hits | self._revealed
        self._revealed = hits
        if changed:
            self._queue(changed=list(changed))

    @QtCore.Slot(str)
    def selectMatches(self, query):
        q = (query or "").strip().lower()
        if not q:
            return
        hits = [u for u, i in self.infos.items() if q in i.get("search", "")]
        self.sel = hits
        self._emit_selection()
        self._select_in_maya()
        self.frameRequested.emit(False)

    # ================================================================== sync / lock / tabs

    def set_sync(self, on):
        self.sync_on = bool(on)
        if self.sync_on:
            # Coming back on: drop what died meanwhile, refresh names.
            dead = list(self.dead)
            self.remove_nodes(dead, remember=True)
            self._queue(changed=list(self.infos), wires=True)
        self.syncChanged.emit(self.sync_on)

    def set_active_tab(self, i):
        if i == self.store.active:
            return
        self._sync_tab_views()
        self.store.set_active(i)
        self._load_tab()

    def new_tab(self):
        self._sync_tab_views()
        self.store.add_tab()
        self._load_tab()
        self._mark_modified()

    def close_tab(self, i):
        self._sync_tab_views()
        self.store.close_tab(i)
        self._load_tab()
        self._mark_modified()

    def restore_tab(self, j):
        self._sync_tab_views()
        self.store.restore_recent(j)
        self._load_tab()
        self._mark_modified()

    def rename_tab(self, i, name):
        self.store.rename_tab(i, name)
        self.tabsChanged.emit()
        self._mark_modified()

    # bookmarks: saved views of the active tab
    def add_bookmark(self):
        v = dict(self.tab.get("view") or {})
        self.tab.setdefault("bookmarks", []).append(v)
        self.tab["bmIndex"] = len(self.tab["bookmarks"]) - 1
        self.status("Bookmarked view %d" % len(self.tab["bookmarks"]))

    def goto_bookmark(self, step):
        bms = self.tab.get("bookmarks") or []
        if not bms:
            return
        i = (self.tab.get("bmIndex", -1) + step) % len(bms)
        self.tab["bmIndex"] = i
        b = bms[i]
        self.viewRequested.emit(float(b["x"]), float(b["y"]), float(b["z"]))
