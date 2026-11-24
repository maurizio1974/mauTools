"""Board data kept in the scene: tabs, node positions, per-node view state, recently closed.

One `network` node (nodexBoard) holds the whole board as JSON in a string attribute, so
nothing Maya does to its own Node Editor can move our board (the board lives in the
scene, not in Maya's editor state). Writes bypass the undo queue: moving a node on the board is not a scene edit.
"""
import copy
import json

import maya.cmds as cmds

STORE_NODE = "nodexBoard"
STORE_ATTR = "nodexData"
VERSION = 1
MAX_RECENT = 12


def new_tab(name):
    return {
        "name": name,
        "nodes": {},       # uuid -> [x, y]
        "widths": {},      # uuid -> width the user dragged the node to; absent = computed
        "views": {},       # uuid -> {"mode", "expanded", "pinned"}
        "gone": {},        # uuid -> [x, y] of nodes deleted while on the tab (undo brings them back)
        "view": {"x": 60.0, "y": 60.0, "z": 1.0},
        "mode": "connected",
        "bookmarks": [],
        "frames": [],      # Blender frames: {"id", "x", "y", "w", "h", "color", "label", "text"}
    }


def default_data():
    return {"version": VERSION, "tabs": [new_tab("Graph 1")], "active": 0, "recent": []}


class _undo_off(object):
    """Suspend undo recording without flushing the user's queue."""

    def __enter__(self):
        self.state = cmds.undoInfo(q=True, state=True)
        if self.state:
            cmds.undoInfo(stateWithoutFlush=False)

    def __exit__(self, *exc):
        if self.state:
            cmds.undoInfo(stateWithoutFlush=True)
        return False


def store_node():
    """The scene's board node, or None."""
    hits = cmds.ls(STORE_NODE, type="network") or []
    for h in hits:
        if cmds.attributeQuery(STORE_ATTR, node=h, exists=True):
            return h
    return None


class Store(object):
    def __init__(self):
        self.data = default_data()

    # ------------------------------------------------------------------ scene I/O

    def load(self):
        node = store_node()
        self.data = default_data()
        if node:
            raw = cmds.getAttr(node + "." + STORE_ATTR) or ""
            try:
                data = json.loads(raw) if raw else None
            except ValueError:
                data = None
            if isinstance(data, dict) and data.get("tabs"):
                self.data = _normalise(data)
        return self.data

    def save(self):
        """Write the board into the scene (creates the node on first save)."""
        raw = json.dumps(self.data, separators=(",", ":"))
        with _undo_off():
            node = store_node()
            if node is None:
                node = cmds.createNode("network", name=STORE_NODE, skipSelect=True)
                cmds.addAttr(node, longName=STORE_ATTR, dataType="string")
            cmds.setAttr(node + "." + STORE_ATTR, raw, type="string")
        return node

    # ------------------------------------------------------------------ tabs

    @property
    def tabs(self):
        return self.data["tabs"]

    @property
    def active(self):
        return self.data["active"]

    @property
    def tab(self):
        return self.data["tabs"][self.data["active"]]

    def set_active(self, i):
        self.data["active"] = max(0, min(int(i), len(self.tabs) - 1))
        return self.tab

    def unique_name(self, base="Graph"):
        names = set(t["name"] for t in self.tabs)
        i = 1
        while "%s %d" % (base, i) in names:
            i += 1
        return "%s %d" % (base, i)

    def add_tab(self, name=None):
        self.tabs.append(new_tab(name or self.unique_name()))
        self.data["active"] = len(self.tabs) - 1
        return self.tab

    def rename_tab(self, i, name):
        name = (name or "").strip()
        if name:
            self.tabs[i]["name"] = name

    def close_tab(self, i):
        """Close tab i into "Recently closed". A board always keeps one tab."""
        tab = self.tabs.pop(i)
        self.data["recent"].insert(0, {"tab": tab, "index": i})
        del self.data["recent"][MAX_RECENT:]
        if not self.tabs:
            self.tabs.append(new_tab(self.unique_name()))
        if self.data["active"] >= len(self.tabs) or self.data["active"] > i:
            self.data["active"] = max(0, self.data["active"] - 1)
        self.data["active"] = min(self.data["active"], len(self.tabs) - 1)
        return tab

    def restore_recent(self, j=0):
        """Put a closed tab back where it was."""
        entry = self.data["recent"].pop(j)
        i = min(entry["index"], len(self.tabs))
        tab = entry["tab"]
        if tab["name"] in set(t["name"] for t in self.tabs):
            tab["name"] = self.unique_name(tab["name"])
        self.tabs.insert(i, tab)
        self.data["active"] = i
        return tab

    @property
    def recent(self):
        return self.data["recent"]

    # ------------------------------------------------------------------ nodes on the active tab

    def set_pos(self, uuid, x, y, tab=None):
        (tab or self.tab)["nodes"][uuid] = [round(float(x), 1), round(float(y), 1)]

    def pos(self, uuid, tab=None):
        t = tab or self.tab
        p = t["nodes"].get(uuid)
        return tuple(p) if p else None

    def set_width(self, uuid, w, tab=None):
        """A width the user chose for a node; 0 / None goes back to the computed one."""
        t = tab or self.tab
        if w and w > 0:
            t.setdefault("widths", {})[uuid] = round(float(w), 1)
        else:
            t.setdefault("widths", {}).pop(uuid, None)

    def width(self, uuid, tab=None):
        return (tab or self.tab).get("widths", {}).get(uuid)

    def remove(self, uuid, remember=True, tab=None):
        t = tab or self.tab
        p = t["nodes"].pop(uuid, None)
        if remember and p:
            t["gone"][uuid] = p
        elif not remember:
            t["views"].pop(uuid, None)
            t.setdefault("widths", {}).pop(uuid, None)

    def prune(self, alive):
        """Forget 'gone' entries of nodes that no longer exist anywhere (called on save)."""
        alive = set(alive)
        for t in self.tabs + [r["tab"] for r in self.recent]:
            for u in list(t["gone"]):
                if u not in alive:
                    del t["gone"][u]
                    t["views"].pop(u, None)
                    t.setdefault("widths", {}).pop(u, None)

    def snapshot(self):
        return copy.deepcopy(self.data)


def _normalise(data):
    out = default_data()
    out["tabs"] = []
    for t in data.get("tabs", []):
        nt = new_tab(t.get("name") or "Graph")
        for k in nt:
            if k in t:
                nt[k] = t[k]
        out["tabs"].append(nt)
    if not out["tabs"]:
        out["tabs"] = [new_tab("Graph 1")]
    out["active"] = max(0, min(int(data.get("active", 0)), len(out["tabs"]) - 1))
    out["recent"] = [r for r in data.get("recent", []) if isinstance(r, dict) and "tab" in r]
    return out
