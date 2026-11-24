"""Colours for NodeX.

Every data colour comes from ../palette.json, which tools/build_palette.py generates from Maya's
colour prefs. Chrome tokens are the UI chrome colours of the panel;
QML cannot see Qt Style Sheets, so these are repeated here once and handed to QML as a map.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# An installed build carries palette.json inside the package; the source tree keeps it one up.
PALETTE_PATH = next((p for p in (os.path.join(HERE, "palette.json"),
                                 os.path.join(os.path.dirname(HERE), "palette.json"))
                     if os.path.isfile(p)), os.path.join(os.path.dirname(HERE), "palette.json"))

# UI chrome tokens.
CHROME = {
    "panel": "#444444",
    "panelLo": "#3A3A3A",
    "canvas": "#2F2F30",
    "plate": "#3B3B3D",
    "field": "#2B2B2B",
    "ink": "#E3E3E3",
    "text": "#C8C8C8",
    "muted": "#9A9A9A",
    "faint": "#6E6E70",
    "accent": "#5285A6",
    "gridAlpha": 0.06,                  # white dots at 6% alpha, GPU shader
}

_palette = None


def palette():
    global _palette
    if _palette is None:
        with open(PALETTE_PATH, "r", encoding="utf-8") as fh:
            _palette = json.load(fh)
    return _palette


def attr_color(cls):
    """Port / wire colour for a Maya attribute class."""
    table = palette()["attr"]
    entry = table.get(cls) or table["MultiAmbiguous"]
    return entry["styled"]


# NodeX's own header categories, not in Maya's colour prefs. Matrix nodes are
# rigging plumbing, not render utilities: Maya's purple Utility made them read as shading.
EXTRA_NODE = {
    "Matrix": "#285485",                # header blue, lightness kept in the 0.25-0.34 header band
}


def node_color(category):
    """Header colour for a Maya node category."""
    if category in EXTRA_NODE:
        return EXTRA_NODE[category]
    table = palette()["node"]
    entry = table.get(category) or table["Other"]
    return entry["styled"]


def selection_colors():
    sel = palette()["sel"]
    return {"lead": sel["lead"]["styled"], "active": sel["active"]["styled"]}


def qml_theme():
    """Everything QML needs, as one plain dict."""
    t = dict(CHROME)
    t.update({"sel" + k.capitalize(): v for k, v in selection_colors().items()})
    t["unitConversion"] = attr_color("UnitConversion")
    t["message"] = attr_color("MultiAmbiguous")
    return t
