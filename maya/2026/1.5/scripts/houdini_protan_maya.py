"""
houdini_protan for Maya 2026 (works back to Maya 2022)
=====================================================

Applies the houdini_protan palette to Maya:

1. UI panels / menus / fields  -> dark greys via a Qt palette
2. Color Settings (viewport, timeline, Graph Editor, selection, ...)
   -> every saturated red becomes orange, every saturated green becomes a
      light sky blue, blues and yellows are kept. This is done by reading
      Maya's own colour list, so it covers every entry Maya exposes,
      whatever its internal name.
3. Graph Editor curves         -> X orange, Y light sky, Z blue
4. Viewport background         -> dark grey gradient

Why these colours: protans see red as dark and confuse red with green.
Orange vs light sky vs deep blue stay apart in hue AND lightness, and
Maya's yellow "active" highlight stays unique.

Usage (Script Editor, Python tab):
    import houdini_protan_maya as hp
    hp.apply()        # apply + save colour prefs
    hp.report()       # print what would change, change nothing
    hp.reset()        # restore your colours from the backup

To keep the UI palette after a restart, add to userSetup.py:
    import maya.utils, houdini_protan_maya
    maya.utils.executeDeferred(houdini_protan_maya.apply_ui_palette)
(Color Settings are saved in Maya's prefs, so only the Qt palette
needs re-applying at startup.)
"""
from __future__ import annotations

import colorsys
import json
import os

try:
    from maya import cmds
except ImportError:          # allows testing the colour logic outside Maya
    cmds = None

# --------------------------------------------------------------------------
# Palette (identical to houdini_protan.hcs)
# --------------------------------------------------------------------------
P = {
    "crust": "#151619", "mantle": "#1E2023", "base": "#27292D",
    "surface0": "#323439", "surface1": "#3A3D42", "surface2": "#44474D",
    "overlay0": "#565A62", "overlay2": "#878C95",
    "subtext0": "#A3A8B1", "subtext1": "#C0C4CC", "text": "#DCDFE5",
    "primary": "#4C8DFF", "error": "#FF8530", "warn": "#FFF59A",
    "ok": "#35B8FF", "sky_light": "#8FD8FF", "blue": "#3D6BFF",
}

AXIS = {"X": "#FF8530", "Y": "#8FD8FF", "Z": "#3D6BFF"}

# exact Color Settings names to force (only applied if Maya has them)
EXPLICIT = {
    "background":       P["surface0"],
    "backgroundTop":    P["surface1"],
    "backgroundBottom": P["mantle"],
}

BACKUP_NAME = "houdini_protan_color_backup.json"


def _hex(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


# --------------------------------------------------------------------------
# Colour remap: red -> orange, green -> light sky; everything else unchanged
# --------------------------------------------------------------------------
def protan_remap(r, g, b):
    """Return a protan-safe replacement for (r, g, b) in 0..1, or None if
    the colour is fine as it is (greys, blues, yellows, purples...)."""
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    deg = h * 360.0
    if s < 0.30 or v < 0.15:
        return None                                  # grey-ish / near black
    if deg >= 340 or deg < 22:                       # red / red-orange
        # -> orange, never darker than mid so it reads on dark backgrounds
        return colorsys.hsv_to_rgb(24 / 360.0, min(s, 0.85), max(v, 0.92))
    if 70 <= deg < 170:                              # yellow-green .. green .. teal-green
        # -> light sky blue (lightness separates it from deep blue)
        return colorsys.hsv_to_rgb(199 / 360.0, min(s, 0.48), max(v, 0.85))
    return None


# --------------------------------------------------------------------------
# Maya helpers
# --------------------------------------------------------------------------
def _color_list():
    """[(name, [r, g, b] or [r, g, b, a])] for every Color Settings entry."""
    raw = cmds.displayRGBColor(list=True) or ""
    # Depending on the Maya version this is one string ("name r g b\n..."),
    # a list of such lines, or a flat list of tokens. Tokenise everything and
    # read it as: name followed by 3 (rgb) or 4 (rgba) numbers.
    def flatten(x):
        if isinstance(x, (list, tuple)):
            for y in x:
                for z in flatten(y):
                    yield z
        else:
            yield str(x)

    tokens = " ".join(flatten(raw)).replace(",", " ").split()

    def is_num(t):
        try:
            float(t)
            return True
        except ValueError:
            return False

    out = []
    i = 0
    while i < len(tokens):
        name = tokens[i]
        if is_num(name):
            i += 1
            continue
        j = i + 1
        vals = []
        while j < len(tokens) and is_num(tokens[j]) and len(vals) < 4:
            vals.append(float(tokens[j]))
            j += 1
        if len(vals) >= 3:
            out.append((name, vals))
        i = j
    return out


def _backup_path():
    return os.path.join(cmds.internalVar(userPrefDir=True), BACKUP_NAME)


def _plan():
    changes = []
    for name, vals in _color_list():
        r, g, b = vals[:3]
        if name in EXPLICIT:
            new = _hex(EXPLICIT[name])
        else:
            new = protan_remap(r, g, b)
        if new is not None and max(abs(a - c) for a, c in zip(new, (r, g, b))) > 1e-3:
            changes.append((name, vals, list(new)))
    return changes


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def report():
    """Print the Color Settings entries that apply() would change."""
    changes = _plan()
    for name, old, new in changes:
        print("{:40s} {} -> {}".format(
            name,
            "#%02X%02X%02X" % tuple(int(c * 255) for c in old[:3]),
            "#%02X%02X%02X" % tuple(int(c * 255) for c in new)))
    print("houdini_protan: {} colour settings would change".format(len(changes)))
    return changes


def apply_color_settings(save=True):
    changes = _plan()
    path = _backup_path()
    if not os.path.exists(path):                 # keep the very first original
        with open(path, "w") as f:
            json.dump({n: v for n, v, _ in changes}, f, indent=1)
    for name, old, new in changes:
        try:
            if len(old) == 4:
                cmds.displayRGBColor(name, new[0], new[1], new[2], old[3], alpha=True)
            else:
                cmds.displayRGBColor(name, new[0], new[1], new[2])
        except RuntimeError as e:
            print("houdini_protan: skipped {} ({})".format(name, e))

    # Graph Editor curves, wildcard per axis (documented curveRGBColor usage)
    for axis, col in AXIS.items():
        cmds.curveRGBColor("*" + axis, *_hex(col))

    if save:
        cmds.savePrefs(colors=True)
    print("houdini_protan: changed {} colour settings (backup: {})".format(len(changes), path))


_ORIGINAL = {}   # palettes saved at first apply_ui_palette() in this session


def _qt():
    try:
        from PySide6 import QtGui, QtWidgets          # Maya 2025+
    except ImportError:
        from PySide2 import QtGui, QtWidgets          # Maya 2022-2024
    return QtGui, QtWidgets


def apply_ui_palette():
    """Dark Qt palette for Maya's panels, menus and fields (not saved by
    Maya: re-apply from userSetup.py)."""
    QtGui, QtWidgets = _qt()
    app = QtWidgets.QApplication.instance()
    if app is None:
        return
    # remember Maya's own palettes once, so reset() can put them back
    if not _ORIGINAL:
        _ORIGINAL["app"] = QtGui.QPalette(app.palette())
        _ORIGINAL["widgets"] = [(w, QtGui.QPalette(w.palette()))
                                for w in app.topLevelWidgets()]
    C = lambda k: QtGui.QColor(P[k])
    R = QtGui.QPalette.ColorRole
    pal = QtGui.QPalette(_ORIGINAL["app"])
    roles = {
        R.Window: C("base"), R.WindowText: C("text"),
        R.Base: C("crust"), R.AlternateBase: C("mantle"),
        R.Text: C("text"), R.PlaceholderText: C("subtext0"),
        R.Button: C("surface1"), R.ButtonText: C("text"),
        R.ToolTipBase: C("surface1"), R.ToolTipText: C("text"),
        R.BrightText: QtGui.QColor(P["error"]),
        R.Highlight: QtGui.QColor("#2D5BB0"), R.HighlightedText: QtGui.QColor("#FFFFFF"),
        R.Link: C("primary"), R.LinkVisited: QtGui.QColor("#C79BFF"),
        R.Light: C("surface2"), R.Midlight: C("surface1"), R.Mid: C("surface0"),
        R.Dark: C("mantle"), R.Shadow: C("crust"),
    }
    for role, col in roles.items():
        pal.setColor(QtGui.QPalette.ColorGroup.All, role, col)
    dis = QtGui.QPalette.ColorGroup.Disabled
    for role in (R.WindowText, R.Text, R.ButtonText):
        pal.setColor(dis, role, C("overlay0"))
    app.setPalette(pal)
    for w in app.topLevelWidgets():
        w.setPalette(pal)
    print("houdini_protan: UI palette applied")


def reset_ui_palette():
    """Put back the Qt palettes Maya had before apply_ui_palette()."""
    QtGui, QtWidgets = _qt()
    app = QtWidgets.QApplication.instance()
    if app is None or not _ORIGINAL:
        print("houdini_protan: UI palette was not applied in this session "
              "(if it is still dark, remove the userSetup.py lines and restart Maya)")
        return
    app.setPalette(_ORIGINAL["app"])
    saved = {id(w): pal for w, pal in _ORIGINAL["widgets"]}
    for w in app.topLevelWidgets():
        try:
            w.setPalette(saved.get(id(w), _ORIGINAL["app"]))
        except RuntimeError:          # widget deleted since
            pass
    _ORIGINAL.clear()
    print("houdini_protan: UI palette restored")


def apply():
    apply_color_settings(save=True)
    apply_ui_palette()


def reset(factory=False):
    """Undo apply().

    reset()              restores the colours you had before the first
                         apply() (from the backup file), removes the custom
                         Graph Editor curve colours and restores the UI palette.
    reset(factory=True)  resets ALL Color Settings and curve colours to
                         Maya's factory defaults (also drops any colours you
                         customised yourself before using this script).
    """
    if factory:
        cmds.displayRGBColor(resetToFactory=True)
        cmds.curveRGBColor(resetToFactory=True)
        path = _backup_path()
        if os.path.exists(path):
            os.remove(path)
        print("houdini_protan: Color Settings reset to Maya factory defaults")
    else:
        path = _backup_path()
        failed = []
        if os.path.exists(path):
            with open(path) as f:
                backup = json.load(f)
            for name, vals in backup.items():
                try:
                    if len(vals) == 4:
                        cmds.displayRGBColor(name, *vals, alpha=True)
                    else:
                        cmds.displayRGBColor(name, *vals)
                except RuntimeError as e:
                    failed.append((name, str(e)))
            os.remove(path)
            print("houdini_protan: restored {} colour settings".format(len(backup) - len(failed)))
            for name, err in failed:
                print("houdini_protan: could not restore {} ({})".format(name, err))
        else:
            print("houdini_protan: no backup found - use hp.reset(factory=True)")
        for axis in AXIS:
            try:
                cmds.curveRGBColor("*" + axis, remove=True)
            except RuntimeError:
                pass
    cmds.savePrefs(colors=True)
    reset_ui_palette()