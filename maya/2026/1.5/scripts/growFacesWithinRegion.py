"""
--------------- Grow Selections Within Region --------------

Original MEL tool (v1.3) by Buwaneka Saranga - bsaranga@gmail.com
License Type: Freeware. Please do not sell, this is a simple tool made by an artist for the artists.

Python / Qt port for Maya 2026 (PySide6). Also runs on older Mayas with PySide2.

Usage:
    import growFacesWithinRegion
    growFacesWithinRegion.show()

Workflow:
    1. Select a closed border of edges and click 'Set Region'.
    2. Select one or more faces inside the border.
    3. Click 'Grow' - the selection grows until it reaches the border.
       Right-click the iterations field for presets.
"""

from maya import cmds, mel
from maya import OpenMayaUI

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance, isValid
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance, isValid


WINDOW_TITLE = "Grow Faces in Region"
ITER_PRESETS = (2, 4, 8, 16, 32)
DEFAULT_ITERATIONS = 8

_GREEN = 0x00458525
_RED = 0x00991000
_BLUE = 0x00002555


# --------------------------------------------------------------------------- logic

class _State(object):
    region = []           # border faces, the growth is never allowed past these
    compensated = False   # True once the growth has reached the border
    sel_sizes = []        # selection size after each grow step


def _message(text, color=_GREEN, stay=500):
    cmds.inViewMessage(smg=text, fts=9, ta=1, pos="botCenter", fof=80,
                       fst=stay, bkc=color, fade=True)


def set_region():
    """Converts the border edge selection to the faces around it and stores them."""
    sel = cmds.ls(sl=True, fl=True) or []
    verts = cmds.polyListComponentConversion(sel, toVertex=True) or []
    faces = cmds.polyListComponentConversion(verts, toFace=True) or []

    _State.region = cmds.ls(faces, fl=True) or []
    _State.compensated = False
    _State.sel_sizes = []
    cmds.select(cl=True)

    if _State.region:
        _message("Region set. Select faces inside it and click 'Grow'.")
    else:
        _message("Select a closed border with edges.", _RED)
    return len(_State.region)


def grow(iterations):
    """Returns True if growth reached the border."""
    if not _State.region:
        _message("Select a closed border with edges.", _RED)
        return False

    if _State.compensated:
        _State.sel_sizes = []
        _message("Growth has already reached defined border.", _RED)
        return True

    cmds.undoInfo(openChunk=True, chunkName="growFacesWithinRegion")
    try:
        for _ in range(iterations):
            mel.eval("PolySelectTraverse 1")  # grow selection
            cmds.select(_State.region, d=True)
            _State.sel_sizes.append(len(cmds.ls(sl=True, fl=True) or []))

            # Selection stopped growing: we hit the border, so grow once more to include it.
            if len(_State.sel_sizes) > 2 and _State.sel_sizes[-1] == _State.sel_sizes[-2]:
                mel.eval("PolySelectTraverse 1")
                _State.compensated = True
                break
    finally:
        cmds.undoInfo(closeChunk=True)

    return _State.compensated


def clear():
    cmds.select(cl=True)
    _State.region = []
    _State.compensated = False
    _State.sel_sizes = []
    _message("All Cleared.", _BLUE)


# --------------------------------------------------------------------------- ui

STYLE = """
QDialog#GrowFacesWithinRegion {
    background: #2b2e31;
}
QLabel { color: #c9cdd1; }
QLabel#title { color: #f0f2f4; font-size: 14px; font-weight: 600; }
QLabel#subtitle { color: #7d858c; font-size: 11px; }
QLabel#section { color: #8a939b; font-size: 10px; font-weight: 600; letter-spacing: 1px; }

QFrame#card {
    background: #33373b;
    border: 1px solid #3d4246;
    border-radius: 8px;
}

QLabel#status {
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}
QLabel#status[state="empty"]   { background: #3d4246; color: #9aa2a9; }
QLabel#status[state="ready"]   { background: #1f4a5c; color: #8fd3ef; }
QLabel#status[state="reached"] { background: #2f5233; color: #9fe0a6; }

QSpinBox {
    background: #24272a;
    color: #f0f2f4;
    border: 1px solid #454a4f;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 13px;
    font-weight: 600;
    min-height: 22px;
}
QSpinBox:focus { border: 1px solid #4aa3c9; }
QSpinBox::up-button, QSpinBox::down-button { width: 18px; border: none; background: transparent; }

QPushButton {
    background: #3d4246;
    color: #e3e6e8;
    border: none;
    border-radius: 6px;
    padding: 7px 12px;
    font-weight: 600;
}
QPushButton:hover   { background: #484e53; }
QPushButton:pressed { background: #2f3337; }

QPushButton#primary { background: #3a8fb7; color: white; font-size: 13px; padding: 10px; }
QPushButton#primary:hover   { background: #45a2cd; }
QPushButton#primary:pressed { background: #2f7799; }

QPushButton#region { background: #4a5a3c; color: #e4f0d8; }
QPushButton#region:hover { background: #566a46; }

QPushButton#ghost { background: transparent; color: #9aa2a9; border: 1px solid #454a4f; }
QPushButton#ghost:hover { color: #f0f2f4; border-color: #6a7177; }

QPushButton#chip { padding: 5px 0; font-size: 11px; border-radius: 5px; }

QMenu { background: #33373b; color: #e3e6e8; border: 1px solid #454a4f; padding: 4px; }
QMenu::item { padding: 5px 24px 5px 14px; border-radius: 4px; }
QMenu::item:selected { background: #3a8fb7; color: white; }
QMenu::separator { height: 1px; background: #454a4f; margin: 4px 6px; }

QToolTip { background: #24272a; color: #e3e6e8; border: 1px solid #454a4f; }
"""


def _maya_main_window():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


class IterationSpinBox(QtWidgets.QSpinBox):
    """Spin box with a right-click menu of presets."""

    def __init__(self, parent=None):
        super(IterationSpinBox, self).__init__(parent)
        self.setRange(1, 999)
        self.setValue(DEFAULT_ITERATIONS)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setToolTip("Grow steps per click.\nRight-click for presets.")

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        title = menu.addAction("Presets")
        title.setEnabled(False)
        menu.addSeparator()
        for preset in ITER_PRESETS:
            action = menu.addAction(str(preset))
            action.setCheckable(True)
            action.setChecked(preset == self.value())
            action.triggered.connect(lambda _=False, v=preset: self.setValue(v))
        menu.exec(event.globalPos()) if hasattr(menu, "exec") else menu.exec_(event.globalPos())


class GrowFacesWindow(QtWidgets.QDialog):

    OBJECT_NAME = "GrowFacesWithinRegion"

    def __init__(self, parent=None):
        super(GrowFacesWindow, self).__init__(parent or _maya_main_window())
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setStyleSheet(STYLE)
        self.setMinimumWidth(320)

        self._build()
        self._refresh_status()

    # ---------------------------------------------------------------- layout

    def _build(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # Header
        header = QtWidgets.QHBoxLayout()
        titles = QtWidgets.QVBoxLayout()
        titles.setSpacing(1)
        title = QtWidgets.QLabel("Grow Within Region")
        title.setObjectName("title")
        subtitle = QtWidgets.QLabel("Border edges → faces inside")
        subtitle.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch()
        self.status = QtWidgets.QLabel()
        self.status.setObjectName("status")
        header.addWidget(self.status, 0, QtCore.Qt.AlignTop)
        root.addLayout(header)

        # Region card
        region_card, region_layout = self._card("1  REGION")
        region_row = QtWidgets.QHBoxLayout()
        region_row.setSpacing(6)
        self.set_region_btn = QtWidgets.QPushButton("Set Region")
        self.set_region_btn.setObjectName("region")
        self.set_region_btn.setToolTip("Select a closed border of edges, then click.")
        self.set_region_btn.clicked.connect(self._on_set_region)
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.setObjectName("ghost")
        self.clear_btn.clicked.connect(self._on_clear)
        region_row.addWidget(self.set_region_btn, 1)
        region_row.addWidget(self.clear_btn)
        region_layout.addLayout(region_row)
        root.addWidget(region_card)

        # Grow card
        grow_card, grow_layout = self._card("2  GROW")
        iter_row = QtWidgets.QHBoxLayout()
        iter_label = QtWidgets.QLabel("Iterations")
        self.iterations = IterationSpinBox()
        self.iterations.setFixedWidth(90)
        iter_row.addWidget(iter_label)
        iter_row.addStretch()
        iter_row.addWidget(self.iterations)
        grow_layout.addLayout(iter_row)

        self.grow_btn = QtWidgets.QPushButton("Grow")
        self.grow_btn.setObjectName("primary")
        self.grow_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.grow_btn.clicked.connect(self._on_grow)
        grow_layout.addWidget(self.grow_btn)
        root.addWidget(grow_card)

        # Convert card
        convert_card, convert_layout = self._card("CONVERT SELECTION")
        chips = QtWidgets.QHBoxLayout()
        chips.setSpacing(4)
        for label, cmd, tip in (
            ("Vtx", "ConvertSelectionToVertices", "To vertices"),
            ("VtxPr", "ConvertSelectionToVertexPerimeter", "To vertex perimeter"),
            ("CEdg", "ConvertSelectionToContainedEdges", "To contained edges"),
            ("UV", "ConvertSelectionToUVs", "To UVs"),
            ("Fcs", "ConvertSelectionToFaces", "To faces"),
        ):
            btn = QtWidgets.QPushButton(label)
            btn.setObjectName("chip")
            btn.setToolTip(tip)
            btn.clicked.connect(lambda _=False, c=cmd: mel.eval(c))
            chips.addWidget(btn)
        convert_layout.addLayout(chips)
        root.addWidget(convert_card)

    def _card(self, heading):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)
        label = QtWidgets.QLabel(heading)
        label.setObjectName("section")
        layout.addWidget(label)
        return card, layout

    # ---------------------------------------------------------------- status

    def _refresh_status(self):
        if not _State.region:
            state, text = "empty", "No region"
        elif _State.compensated:
            state, text = "reached", "Border reached"
        else:
            state, text = "ready", "{} border faces".format(len(_State.region))

        self.status.setText(text)
        self.status.setProperty("state", state)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.grow_btn.setEnabled(bool(_State.region))

    # ---------------------------------------------------------------- slots

    def _on_set_region(self):
        set_region()
        self._refresh_status()

    def _on_grow(self):
        grow(self.iterations.value())
        self._refresh_status()

    def _on_clear(self):
        clear()
        self._refresh_status()


_window = None


def show():
    global _window
    if _window is not None and isValid(_window):
        _window.close()

    # Also close windows left over from a previous reload of this module.
    main = _maya_main_window()
    if main:
        for child in main.findChildren(QtWidgets.QDialog, GrowFacesWindow.OBJECT_NAME):
            child.close()

    _window = GrowFacesWindow()
    _window.show()
    _message("Make a closed border edge selection and click on 'Set Region'.", stay=2000)
    return _window


if __name__ == "__main__":
    show()