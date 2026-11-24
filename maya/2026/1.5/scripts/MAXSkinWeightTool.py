"""
MAXSkinWeightTool - Python / Qt version for Maya 2026 (PySide6, also runs on PySide2).

Based on MAXSkinWeightTool v1.2 (MEL) by Preeth P.G. (pg.preeth@gmail.com), 2009:
a 3ds Max style skinning panel where you assign preset weights to vertices
instead of painting.

Usage:
    import MAXSkinWeightTool
    MAXSkinWeightTool.show()

Workflow:
    1. Select vertices (or edges / faces) on a skinned mesh.
    2. Pick an influence in "Influences" or "Vertex weights".
    3. Use the preset / set / scale / +- buttons.
"""

import re
import fnmatch

from maya import cmds, mel
from maya import OpenMayaUI
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance, isValid
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance, isValid


WINDOW_TITLE = "Skin Weight Tool"
PRESETS = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)
EPS = 1e-5


# =========================================================================== data

class SkinData(object):
    """Skin weights of the current selection, read through the API (fast)."""

    def __init__(self):
        self.obj = None          # selected object name
        self.skin = None         # skinCluster name
        self.skin_fn = None      # MFnSkinCluster
        self.dag = None          # MDagPath to the mesh shape
        self.influences = []     # influence names, in skinCluster order
        self.indices = []        # selected vertex indices
        self.weights = []        # per selected vertex: [weight per influence]
        self.vert_strings = []   # compact component strings for cmds

    @property
    def has_verts(self):
        return bool(self.skin and self.indices)

    def vtx(self, index):
        return "{}.vtx[{}]".format(self.dag.partialPathName(), index)

    def average(self):
        if not self.weights:
            return []
        n = float(len(self.weights))
        return [sum(col) / n for col in zip(*self.weights)]


def _mobject(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDependNode(0)


def find_skin(obj):
    try:
        return mel.eval('findRelatedSkinCluster "{}"'.format(obj)) or None
    except RuntimeError:
        return None


def read_selection():
    sel = cmds.ls(sl=True) or []
    if not sel:
        return None

    data = SkinData()
    comps = [s for s in sel if "." in s]
    if comps:
        data.obj = comps[0].split(".")[0]
        comps = [c for c in comps if c.split(".")[0] == data.obj]
        verts = cmds.polyListComponentConversion(comps, toVertex=True) or []
    else:
        data.obj = sel[0]
        verts = []

    data.skin = find_skin(data.obj)
    if not data.skin:
        return data

    data.skin_fn = oma.MFnSkinCluster(_mobject(data.skin))
    data.influences = [p.partialPathName() for p in data.skin_fn.influenceObjects()]

    if verts:
        try:
            msel = om.MSelectionList()
            for v in verts:
                msel.add(v)
            dag, comp = msel.getComponent(0)
            if dag.apiType() == om.MFn.kTransform:
                dag.extendToShape()
            flat, n = data.skin_fn.getWeights(dag, comp)
            data.dag = dag
            data.vert_strings = verts
            data.indices = list(om.MFnSingleIndexedComponent(comp).getElements())
            data.weights = [list(flat[i * n:(i + 1) * n]) for i in range(len(data.indices))]
        except (RuntimeError, ValueError):
            data.indices, data.weights = [], []
    return data


def _weights_for(data, indices):
    """Weights of arbitrary vertices of the same mesh -> {index: [weights]}."""
    fn_comp = om.MFnSingleIndexedComponent()
    comp = fn_comp.create(om.MFn.kMeshVertComponent)
    fn_comp.addElements(list(indices))
    flat, n = data.skin_fn.getWeights(data.dag, comp)
    ordered = fn_comp.getElements()
    return {ordered[i]: list(flat[i * n:(i + 1) * n]) for i in range(len(ordered))}


def _is_sole(weights, j):
    return weights[j] > 1.0 - EPS


def _apply_full(data, vertex, weights_by_name):
    tv = [(inf, w) for inf, w in weights_by_name.items() if w > EPS]
    if tv:
        cmds.skinPercent(data.skin, vertex, transformValue=tv, zeroRemainingInfluences=True)


# =========================================================================== operations

def op_set(data, joint, value):
    """Absolute weight for the active influence on every selected vertex."""
    j = data.influences.index(joint)
    targets, skipped = [], 0
    for idx, w in zip(data.indices, data.weights):
        if value < 1.0 and _is_sole(w, j):
            skipped += 1
        else:
            targets.append(data.vtx(idx))
    if targets:
        cmds.skinPercent(data.skin, targets, transformValue=[(joint, value)])
    return _result("Set {} to {:.3f}".format(joint, value), len(targets), skipped)


def op_relative(data, joint, func, label):
    """Per-vertex relative change: new = func(current), clamped to 0..1."""
    j = data.influences.index(joint)
    groups, skipped = {}, 0
    for idx, w in zip(data.indices, data.weights):
        new = max(0.0, min(1.0, func(w[j])))
        if abs(new - w[j]) < EPS:
            continue
        if new < 1.0 and _is_sole(w, j):
            skipped += 1
            continue
        groups.setdefault(round(new, 6), []).append(data.vtx(idx))
    count = 0
    for value, verts in groups.items():
        cmds.skinPercent(data.skin, verts, transformValue=[(joint, value)])
        count += len(verts)
    return _result("{} {}".format(label, joint), count, skipped)


def _result(text, count, skipped):
    msg = "{} on {} vert{}".format(text, count, "" if count == 1 else "s")
    if skipped:
        msg += " - skipped {} with a single influence (add another influence first)".format(skipped)
    return msg


def op_prune(data, value):
    cmds.skinPercent(data.skin, data.vert_strings, pruneWeights=value)
    return "Pruned weights below {:.4f} on {} verts".format(value, len(data.indices))


def op_copy(data):
    w = data.weights[0]
    buffer = {inf: v for inf, v in zip(data.influences, w) if v > EPS}
    return buffer, data.vtx(data.indices[0])


def op_paste(data, buffer):
    available = set(data.influences)
    usable = {k: v for k, v in buffer.items() if k in available}
    missing = len(buffer) - len(usable)
    if not usable:
        return "None of the copied influences are in {}".format(data.skin)
    cmds.skinPercent(data.skin, data.vert_strings,
                     transformValue=list(usable.items()), zeroRemainingInfluences=True)
    msg = "Pasted weights on {} verts".format(len(data.indices))
    if missing:
        msg += " ({} influences not in this skin were skipped)".format(missing)
    return msg


def op_blend(data):
    """Each selected vertex gets the average of itself and its neighbours."""
    it = om.MItMeshVertex(data.dag)
    neighbours, needed = {}, set(data.indices)
    for idx in data.indices:
        it.setIndex(idx)
        nb = list(it.getConnectedVertices())
        neighbours[idx] = nb
        needed.update(nb)

    weights = _weights_for(data, sorted(needed))
    for idx in data.indices:
        ring = [idx] + neighbours[idx]
        avg = [sum(col) / len(ring) for col in zip(*(weights[i] for i in ring))]
        total = sum(avg) or 1.0
        _apply_full(data, data.vtx(idx),
                    {inf: w / total for inf, w in zip(data.influences, avg)})
    return "Blended {} verts with their neighbours".format(len(data.indices))


_SIDE_SWAP = {"L": "R", "R": "L", "l": "r", "r": "l", "Lf": "Rt", "Rt": "Lf",
              "lf": "rt", "rt": "lf", "Left": "Right", "Right": "Left",
              "left": "right", "right": "left"}
_SIDE_RE = re.compile(r"(?<![A-Za-z])(Left|Right|left|right|Lf|Rt|lf|rt|L|R|l|r)(?=$|[_0-9A-Z])")


def mirror_influence_map(influences):
    """influence -> mirrored influence, by name first, then by mirrored position."""
    by_short = {inf.split("|")[-1]: inf for inf in influences}
    positions = {}
    for inf in influences:
        try:
            positions[inf] = cmds.xform(inf, q=True, ws=True, rp=True)
        except RuntimeError:
            positions[inf] = None

    result = {}
    for inf in influences:
        short = inf.split("|")[-1]
        mirrored = _SIDE_RE.sub(lambda m: _SIDE_SWAP[m.group(1)], short)
        if mirrored != short and mirrored in by_short:
            result[inf] = by_short[mirrored]
            continue

        pos, best, best_dist = positions[inf], inf, 0.1
        if pos is not None:
            target = om.MPoint(-pos[0], pos[1], pos[2])
            for other, opos in positions.items():
                if opos is None:
                    continue
                d = target.distanceTo(om.MPoint(*opos))
                if d < best_dist:
                    best, best_dist = other, d
        result[inf] = best
    return result


def op_mirror_paste(data):
    """Copies the selected verts' weights to the vertices on the other side of X."""
    mesh = om.MFnMesh(data.dag)
    points = mesh.getPoints(om.MSpace.kWorld)
    inf_map = mirror_influence_map(data.influences)

    total = len(data.indices)
    cmds.progressWindow(title="Paste mirror", progress=0, isInterruptable=True,
                        status="Vertices: 0/{}".format(total))
    done = 0
    try:
        for k, (idx, w) in enumerate(zip(data.indices, data.weights)):
            if cmds.progressWindow(q=True, isCancelled=True):
                break
            p = points[idx]
            mp = om.MPoint(-p.x, p.y, p.z)
            _, face = mesh.getClosestPoint(mp, om.MSpace.kWorld)
            target = min(mesh.getPolygonVertices(face), key=lambda v: points[v].distanceTo(mp))

            new = {}
            for inf, val in zip(data.influences, w):
                if val > EPS:
                    m = inf_map[inf]
                    new[m] = new.get(m, 0.0) + val
            _apply_full(data, data.vtx(target), new)
            done += 1
            if k % 10 == 0:
                cmds.progressWindow(e=True, progress=int(100.0 * k / total),
                                    status="Vertices: {}/{}".format(k, total))
    finally:
        cmds.progressWindow(endProgress=True)
    return "Mirrored {} verts across X".format(done)


def op_mirror_skin(data, inverse):
    cmds.copySkinWeights(ss=data.skin, ds=data.skin, mirrorMode="YZ", mirrorInverse=inverse,
                         surfaceAssociation="closestPoint", influenceAssociation="closestJoint")
    return "Mirrored whole skin {}".format("-X > +X" if inverse else "+X > -X")


def sel_loop():
    mel.eval("ConvertSelectionToContainedEdges; polySelectEdges edgeLoopOrBorder; PolySelectConvert 3;")


def sel_ring():
    mel.eval("ConvertSelectionToContainedEdges; polySelectEdges edgeRing; PolySelectConvert 3;")


# =========================================================================== ui

STYLE = """
QDialog#SkinWeightTool { background: #2b2e31; }
QLabel { color: #c9cdd1; }
QLabel#title { color: #f0f2f4; font-size: 14px; font-weight: 600; }
QLabel#subtitle { color: #7d858c; font-size: 11px; }
QLabel#section { color: #8a939b; font-size: 10px; font-weight: 600; letter-spacing: 1px; }
QLabel#hint { color: #7d858c; font-size: 11px; }
QLabel#status { color: #9aa2a9; font-size: 11px; }
QLabel#active { color: #8fd3ef; font-weight: 600; }

QFrame#card { background: #33373b; border: 1px solid #3d4246; border-radius: 8px; }

QLabel#badge { border-radius: 10px; padding: 3px 10px; font-size: 11px; font-weight: 600; }
QLabel#badge[state="empty"] { background: #3d4246; color: #9aa2a9; }
QLabel#badge[state="object"] { background: #4a4330; color: #f0d58f; }
QLabel#badge[state="ready"] { background: #1f4a5c; color: #8fd3ef; }

QPushButton {
    background: #3d4246; color: #e3e6e8; border: none; border-radius: 6px;
    padding: 6px 8px; font-weight: 600;
}
QPushButton:hover { background: #484e53; }
QPushButton:pressed { background: #2f3337; }
QPushButton:disabled { background: #303437; color: #5f666c; }

QPushButton#preset { background: #2f4a37; color: #bfe8c8; font-size: 12px; padding: 8px 0; }
QPushButton#preset:hover { background: #3a5c44; }
QPushButton#preset:disabled { background: #303437; color: #5f666c; }

QPushButton#primary { background: #3a8fb7; color: white; }
QPushButton#primary:hover { background: #45a2cd; }
QPushButton#primary:disabled { background: #303437; color: #5f666c; }

QPushButton#minus { background: #4a3535; color: #f0c4c4; }
QPushButton#minus:hover { background: #5a4040; }
QPushButton#plus { background: #2f4a37; color: #bfe8c8; }
QPushButton#plus:hover { background: #3a5c44; }

QPushButton#mirror { background: #5a4330; color: #f5d9bf; }
QPushButton#mirror:hover { background: #6b5039; }

QDoubleSpinBox, QLineEdit {
    background: #24272a; color: #f0f2f4; border: 1px solid #454a4f;
    border-radius: 6px; padding: 3px 6px; min-height: 20px;
}
QDoubleSpinBox:focus, QLineEdit:focus { border: 1px solid #4aa3c9; }
QDoubleSpinBox:disabled { color: #5f666c; }

QListWidget, QTreeWidget {
    background: #24272a; color: #e3e6e8; border: 1px solid #3d4246;
    border-radius: 6px; outline: none;
}
QListWidget::item, QTreeWidget::item { padding: 3px 4px; }
QListWidget::item:selected, QTreeWidget::item:selected { background: #2f5d75; color: white; }
QHeaderView::section {
    background: #33373b; color: #8a939b; border: none; padding: 4px; font-size: 10px; font-weight: 600;
}

QSplitter::handle { background: transparent; height: 6px; }
QToolTip { background: #24272a; color: #e3e6e8; border: 1px solid #454a4f; }
"""


def _maya_main_window():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


class WeightBarDelegate(QtWidgets.QStyledItemDelegate):
    """Draws the weight column as a small bar with the value on it."""

    def paint(self, painter, option, index):
        value = index.data(QtCore.Qt.UserRole)
        if value is None:
            return super(WeightBarDelegate, self).paint(painter, option, index)

        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, QtGui.QColor("#2f5d75"))

        r = option.rect.adjusted(4, 4, -6, -4)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor("#1c1e20"))
        painter.drawRoundedRect(r, 3, 3)

        fill = QtCore.QRect(r)
        fill.setWidth(max(2, int(r.width() * min(1.0, value))))
        color = QtGui.QColor("#3a8fb7") if value < 0.999 else QtGui.QColor("#4f9d63")
        painter.setBrush(color)
        painter.drawRoundedRect(fill, 3, 3)

        painter.setPen(QtGui.QColor("#f0f2f4"))
        painter.drawText(r, QtCore.Qt.AlignCenter, "{:.3f}".format(value))
        painter.restore()


class SkinWeightTool(QtWidgets.QDialog):

    OBJECT_NAME = "SkinWeightTool"

    def __init__(self, parent=None):
        super(SkinWeightTool, self).__init__(parent or _maya_main_window())
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setStyleSheet(STYLE)
        self.resize(380, 960)

        self.data = None
        self.active = None      # active influence name
        self.buffer = None      # copied weights {influence: weight}
        self._job = None
        self._refresh_pending = False

        self._build()
        self.refresh()
        self._job = cmds.scriptJob(event=["SelectionChanged", self._on_selection_changed])

    # ------------------------------------------------------------ layout helpers

    def _card(self, heading):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)
        label = QtWidgets.QLabel(heading)
        label.setObjectName("section")
        layout.addWidget(label)
        return card, layout

    def _button(self, text, slot, name=None, tip=None):
        b = QtWidgets.QPushButton(text)
        if name:
            b.setObjectName(name)
        if tip:
            b.setToolTip(tip)
        b.clicked.connect(slot)
        return b

    def _row(self, *widgets, spacing=4):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(spacing)
        for w in widgets:
            if isinstance(w, int):
                row.addStretch(w)
            else:
                row.addWidget(w)
        return row

    def _spin(self, lo, hi, value, step, decimals):
        s = QtWidgets.QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setDecimals(decimals)
        s.setSingleStep(step)
        s.setValue(value)
        s.setFixedWidth(78)
        s.setAlignment(QtCore.Qt.AlignCenter)
        return s

    # ------------------------------------------------------------ build

    def _build(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 10)
        root.setSpacing(8)

        # Header
        titles = QtWidgets.QVBoxLayout()
        titles.setSpacing(1)
        title = QtWidgets.QLabel("Skin Weight Tool")
        title.setObjectName("title")
        self.subtitle = QtWidgets.QLabel()
        self.subtitle.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(self.subtitle)
        header = QtWidgets.QHBoxLayout()
        header.addLayout(titles)
        header.addStretch()
        self.badge = QtWidgets.QLabel()
        self.badge.setObjectName("badge")
        header.addWidget(self.badge, 0, QtCore.Qt.AlignTop)
        root.addLayout(header)

        self.active_label = QtWidgets.QLabel()
        self.active_label.setObjectName("active")
        root.addWidget(self.active_label)

        # Selection
        card, lay = self._card("SELECTION")
        lay.addLayout(self._row(
            self._button("Grow", lambda: self._sel_cmd(lambda: mel.eval("GrowPolygonSelectionRegion"))),
            self._button("Shrink", lambda: self._sel_cmd(lambda: mel.eval("ShrinkPolygonSelectionRegion"))),
            self._button("Loop", lambda: self._sel_cmd(sel_loop), tip="Select at least two vertices"),
            self._button("Ring", lambda: self._sel_cmd(sel_ring), tip="Select at least two vertices"),
        ))
        root.addWidget(card)

        # Weights
        card, lay = self._card("WEIGHTS  —  ACTIVE INFLUENCE")
        self.joint_widgets = []
        presets = []
        for v in PRESETS:
            b = self._button("{:g}".format(v), lambda _=False, v=v: self._run_joint(op_set, v),
                             name="preset", tip="Set weight to {:g}".format(v))
            presets.append(b)
        self.joint_widgets += presets
        lay.addLayout(self._row(*presets))

        self.set_spin = self._spin(0.0, 1.0, 0.1, 0.05, 3)
        self.scale_spin = self._spin(0.001, 5.0, 0.95, 0.05, 3)
        set_btn = self._button("Set", lambda: self._run_joint(op_set, self.set_spin.value()), name="primary")
        scale_btn = self._button(
            "Scale", lambda: self._run_joint(
                op_relative, (lambda w, f=self.scale_spin.value(): w * f), "Scaled"),
            name="primary", tip="Multiply the current weight")
        lay.addLayout(self._row(set_btn, self.set_spin, 1, scale_btn, self.scale_spin))

        steps = [
            self._button("−5%", lambda: self._run_joint(op_relative, lambda w: w * 0.95, "-5%"), name="minus"),
            self._button("−0.05", lambda: self._run_joint(op_relative, lambda w: w - 0.05, "-0.05"), name="minus"),
            self._button("+0.05", lambda: self._run_joint(op_relative, lambda w: w + 0.05, "+0.05"), name="plus"),
            self._button("+5%", lambda: self._run_joint(op_relative, lambda w: w * 1.05, "+5%"), name="plus"),
        ]
        lay.addLayout(self._row(*steps))
        self.joint_widgets += [set_btn, scale_btn, self.set_spin, self.scale_spin] + steps
        root.addWidget(card)

        # Transfer
        card, lay = self._card("TRANSFER")
        self.copy_btn = self._button("Copy", self._copy, tip="Copy the first selected vertex's weights")
        self.paste_btn = self._button("Paste", self._paste)
        self.blend_btn = self._button("Blend", lambda: self._run(op_blend),
                                      tip="Average each vertex with its neighbours")
        lay.addLayout(self._row(self.copy_btn, self.paste_btn, self.blend_btn))
        self.buffer_label = QtWidgets.QLabel("Nothing copied")
        self.buffer_label.setObjectName("hint")
        lay.addWidget(self.buffer_label)
        root.addWidget(card)

        # Influences / vertex weights
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.setChildrenCollapsible(False)

        card, lay = self._card("INFLUENCES")
        self.inf_filter = QtWidgets.QLineEdit()
        self.inf_filter.setPlaceholderText("Filter  (e.g. L_arm*)")
        self.inf_filter.textChanged.connect(self._fill_influences)
        self.inf_list = QtWidgets.QListWidget()
        self.inf_list.itemClicked.connect(lambda item: self._set_active(item.data(QtCore.Qt.UserRole)))
        self.inf_list.setMinimumHeight(110)
        lay.addWidget(self.inf_filter)
        lay.addWidget(self.inf_list)
        splitter.addWidget(card)

        card, lay = self._card("VERTEX WEIGHTS")
        self.vtx_filter = QtWidgets.QLineEdit()
        self.vtx_filter.setPlaceholderText("Filter")
        self.vtx_filter.textChanged.connect(self._fill_vertex_weights)
        self.vtx_tree = QtWidgets.QTreeWidget()
        self.vtx_tree.setColumnCount(2)
        self.vtx_tree.setHeaderLabels(["INFLUENCE", "WEIGHT"])
        self.vtx_tree.setRootIsDecorated(False)
        self.vtx_tree.setItemDelegateForColumn(1, WeightBarDelegate(self.vtx_tree))
        self.vtx_tree.header().setStretchLastSection(False)
        self.vtx_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.vtx_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.vtx_tree.setColumnWidth(1, 120)
        self.vtx_tree.itemClicked.connect(lambda item, _c: self._set_active(item.data(0, QtCore.Qt.UserRole)))
        self.vtx_tree.setMinimumHeight(130)
        lay.addWidget(self.vtx_filter)
        lay.addWidget(self.vtx_tree)
        splitter.addWidget(card)
        splitter.setSizes([180, 220])
        root.addWidget(splitter, 1)

        # Cleanup + mirror
        card, lay = self._card("CLEANUP & MIRROR")
        self.prune_spin = self._spin(0.0001, 1.0, 0.01, 0.005, 4)
        self.prune_btn = self._button("Remove weights below",
                                      lambda: self._run(op_prune, self.prune_spin.value()))
        lay.addLayout(self._row(self.prune_btn, self.prune_spin))
        self.mirror_paste_btn = self._button(
            "Paste Mirror", lambda: self._run(op_mirror_paste), name="mirror",
            tip="Copy the selected verts' weights to their mirrored verts on the other side of X")
        self.pos_neg_btn = self._button("+X ▸ −X", lambda: self._run(op_mirror_skin, False, needs_verts=False),
                                        tip="Mirror the whole skin from +X to -X")
        self.neg_pos_btn = self._button("−X ▸ +X", lambda: self._run(op_mirror_skin, True, needs_verts=False),
                                        tip="Mirror the whole skin from -X to +X")
        lay.addLayout(self._row(self.mirror_paste_btn, self.pos_neg_btn, self.neg_pos_btn))
        root.addWidget(card)

        # Footer
        self.status = QtWidgets.QLabel()
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        credit = QtWidgets.QLabel("Based on MAXSkinWeightTool by Preeth P.G.")
        credit.setObjectName("hint")
        root.addWidget(credit)

        self.vert_widgets = [self.copy_btn, self.blend_btn, self.prune_btn, self.prune_spin,
                             self.mirror_paste_btn]

    # ------------------------------------------------------------ refresh

    def _on_selection_changed(self):
        if not isValid(self) or self._refresh_pending:
            return
        self._refresh_pending = True
        QtCore.QTimer.singleShot(0, self.refresh)

    def refresh(self):
        self._refresh_pending = False
        try:
            self.data = read_selection()
        except RuntimeError as err:
            self.data = None
            self._status(str(err))

        d = self.data
        if d is None:
            self._badge("empty", "Nothing selected")
            self.subtitle.setText("Select vertices on a skinned mesh")
        elif not d.skin:
            self._badge("empty", "No skin")
            self.subtitle.setText("{} has no skinCluster".format(d.obj))
        elif not d.indices:
            self._badge("object", "Object")
            self.subtitle.setText("{}  ·  {}".format(d.obj, d.skin))
        else:
            n = len(d.indices)
            self._badge("ready", "{} vert{}".format(n, "" if n == 1 else "s"))
            self.subtitle.setText("{}  ·  {}".format(d.obj, d.skin))

        if d and d.skin and self.active not in d.influences:
            self.active = None
        if d and d.has_verts and self.active is None:
            avg = d.average()
            self.active = d.influences[max(range(len(avg)), key=avg.__getitem__)]

        self._fill_influences()
        self._fill_vertex_weights()
        self._update_enabled()

    def _badge(self, state, text):
        self.badge.setText(text)
        self.badge.setProperty("state", state)
        self.badge.style().unpolish(self.badge)
        self.badge.style().polish(self.badge)

    def _matches(self, name, pattern):
        pattern = pattern.strip()
        if not pattern:
            return True
        if not any(c in pattern for c in "*?["):
            pattern = "*{}*".format(pattern)
        return fnmatch.fnmatch(name.split("|")[-1].lower(), pattern.lower())

    def _locked(self, inf):
        try:
            return bool(cmds.getAttr(inf + ".liw"))
        except (RuntimeError, ValueError):
            return False

    def _fill_influences(self):
        self.inf_list.blockSignals(True)
        self.inf_list.clear()
        d = self.data
        if d and d.skin:
            pattern = self.inf_filter.text()
            for inf in d.influences:
                if not self._matches(inf, pattern):
                    continue
                locked = self._locked(inf)
                item = QtWidgets.QListWidgetItem(inf.split("|")[-1] + ("   \U0001F512" if locked else ""))
                item.setData(QtCore.Qt.UserRole, inf)
                if locked:
                    item.setForeground(QtGui.QColor("#7d858c"))
                self.inf_list.addItem(item)
                if inf == self.active:
                    item.setSelected(True)
                    self.inf_list.setCurrentItem(item)
        self.inf_list.blockSignals(False)

    def _fill_vertex_weights(self):
        self.vtx_tree.blockSignals(True)
        self.vtx_tree.clear()
        d = self.data
        if d and d.has_verts:
            n = len(d.indices)
            self.vtx_tree.setHeaderLabels(["INFLUENCE", "WEIGHT" if n == 1 else "AVG ({})".format(n)])
            pattern = self.vtx_filter.text()
            rows = [(inf, w) for inf, w in zip(d.influences, d.average()) if w > 0.0001]
            for inf, w in sorted(rows, key=lambda r: -r[1]):
                if not self._matches(inf, pattern):
                    continue
                item = QtWidgets.QTreeWidgetItem([inf.split("|")[-1], ""])
                item.setData(0, QtCore.Qt.UserRole, inf)
                item.setData(1, QtCore.Qt.UserRole, float(w))
                self.vtx_tree.addTopLevelItem(item)
                if inf == self.active:
                    item.setSelected(True)
        self.vtx_tree.blockSignals(False)

    def _update_enabled(self):
        d = self.data
        verts = bool(d and d.has_verts)
        for w in self.joint_widgets:
            w.setEnabled(verts and self.active is not None)
        for w in self.vert_widgets:
            w.setEnabled(verts)
        self.paste_btn.setEnabled(verts and self.buffer is not None)
        skin = bool(d and d.skin)
        self.pos_neg_btn.setEnabled(skin)
        self.neg_pos_btn.setEnabled(skin)
        self.active_label.setText(
            "Active:  {}".format(self.active.split("|")[-1]) if self.active else "Active:  —  pick an influence")

    def _set_active(self, inf):
        if not inf:
            return
        self.active = inf
        try:
            mel.eval('setSmoothSkinInfluence "{}"'.format(inf))  # sync the paint tool, if open
        except RuntimeError:
            pass
        self._fill_influences()
        self._fill_vertex_weights()
        self._update_enabled()

    def _status(self, text, warn=False):
        self.status.setText(text)
        if warn:
            cmds.warning(text)

    # ------------------------------------------------------------ actions

    def _sel_cmd(self, func):
        try:
            func()
        except RuntimeError as err:
            self._status(str(err), warn=True)

    def _run(self, op, *args, needs_verts=True):
        d = self.data
        if not d or not d.skin or (needs_verts and not d.indices):
            self._status("Select vertices on a skinned mesh first.", warn=True)
            return
        cmds.undoInfo(openChunk=True, chunkName="skinWeightTool")
        try:
            msg = op(d, *args)
            self._status(msg)
        except RuntimeError as err:
            self._status(str(err).strip(), warn=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.refresh()

    def _run_joint(self, op, *args):
        if not self.active:
            self._status("Pick an influence first.", warn=True)
            return
        self._run(op, self.active, *args)

    def _copy(self):
        d = self.data
        if not d or not d.has_verts:
            return
        self.buffer, source = op_copy(d)
        self.buffer_label.setText("Copied: {}  ({} influences)".format(source.split("|")[-1], len(self.buffer)))
        self._status("Copied weights from " + source.split("|")[-1])
        self._update_enabled()

    def _paste(self):
        if self.buffer:
            self._run(op_paste, self.buffer)

    # ------------------------------------------------------------ close

    def closeEvent(self, event):
        if self._job is not None and cmds.scriptJob(exists=self._job):
            cmds.scriptJob(kill=self._job, force=True)
        self._job = None
        super(SkinWeightTool, self).closeEvent(event)


_window = None


def show():
    global _window
    if _window is not None and isValid(_window):
        _window.close()
    main = _maya_main_window()
    if main:
        for child in main.findChildren(QtWidgets.QDialog, SkinWeightTool.OBJECT_NAME):
            child.close()
    _window = SkinWeightTool()
    _window.show()
    return _window


# Old MEL entry point names
SkinWeightTool_Win = show
MAXSkinWeightTool = show


if __name__ == "__main__":
    show()
