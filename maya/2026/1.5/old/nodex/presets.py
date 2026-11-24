"""Graph presets: a copied fragment (fragment.capture + board layout) kept as a .json file.

The snapshot is the same one Ctrl+C puts on the clipboard, so loading a preset is a paste:
fresh nodes, internal connections only, values, shapes and the saved board layout.
"""
import json
import os
import re
import time

import maya.cmds as cmds

VERSION = 1


def folder():
    path = os.path.join(cmds.internalVar(userAppDir=True), "nodex_presets")
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def safe_name(name):
    name = re.sub(r"[^\w\- ]+", "_", (name or "").strip()).strip()
    return name or "preset"


def entries():
    """[(name, path, node_count)] sorted by name; unreadable files are skipped."""
    out = []
    d = folder()
    for fn in sorted(os.listdir(d), key=str.lower):
        if not fn.lower().endswith(".json"):
            continue
        path = os.path.join(d, fn)
        try:
            meta = read(path)
        except (ValueError, OSError):
            continue
        out.append((meta.get("name") or fn[:-5], path, len(meta["snapshot"].get("selected", []))))
    return out


def write(snapshot, name, path=None):
    path = path or os.path.join(folder(), safe_name(name) + ".json")
    data = {"nodexPreset": VERSION, "name": name, "saved": time.strftime("%Y-%m-%d %H:%M"),
            "snapshot": snapshot}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    return path


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("Not a NodeX preset: %s" % path)
    # A bare clipboard snapshot saved by hand is accepted too.
    snap = data.get("snapshot") if "nodexPreset" in data else data
    if not isinstance(snap, dict) or snap.get("version") != 1 or "selected" not in snap:
        raise ValueError("Unsupported NodeX preset: %s" % os.path.basename(path))
    return {"name": data.get("name") or os.path.splitext(os.path.basename(path))[0], "snapshot": snap}
