"""
mnmConnectPopUP - quick node connector popup for Maya
-----------------------------------------------------
Select two nodes (SOURCE first, TARGET second) and run:

    import mnmConnectPopUP as cp
    cp.show()

Two steps, like the original tool:
  1. A popup opens at the mouse with the OUTPUT attributes of the source.
  2. Click one: the popup jumps to the cursor and shows only the INPUT
     attributes of the target that can take that output (same data type,
     or a generic input). Click one to connect.

What gets listed
  Transform / joint : Transform (t/r/s + children, rotateOrder, visibility,
                      jointOrient), Matrix, User Defined, Keyable, and the
                      shape's geometry plugs (two mesh transforms connect
                      shape to shape without selecting the shapes).
  mesh              : outMesh / worldMesh / outSmoothMesh  ->  inMesh
  nurbsCurve        : local / worldSpace                   ->  create
  nurbsSurface      : local / worldSpace                   ->  create
                      + shape display attrs, user defined, keyable
  any other node    : in*/input* or out*/output*/world*/result* plugs,
                      user defined, keyable
  "All" button      : every connectable attribute, and on step 2 also the
                      inputs with a different type (dimmed).

Multi attributes get the next free index on the input side
(e.g. input1D[3]) and their used indices on the output side.

Keys / mouse
  * Type to filter (* and ? wildcards), Up/Down to move, Enter to pick.
  * Shift-click (or Shift+Enter) an input = connect and stay on the input
    list, to wire the same output into several inputs.
  * Back button, Backspace or Left (with an empty filter) = back to step 1.
  * The attribute selected in the Channel Box is preselected on step 1.
  * Click outside or Esc closes. The swap button swaps source and target.

Transparency (0 = solid, 100 = invisible, capped at 90)
  TRANSPARENCY = 12            default, edit it below
  cp.show(transparency=30)     this popup only
  cp.set_transparency(30)      saved in Maya prefs, used from now on
"""
from fnmatch import fnmatch

import maya.cmds as cmds
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance


# =========================================================================== attribute rules
XFORM_ATTRS = [
    'translate', 'translateX', 'translateY', 'translateZ',
    'rotate', 'rotateX', 'rotateY', 'rotateZ',
    'scale', 'scaleX', 'scaleY', 'scaleZ',
    'rotateOrder', 'visibility',
]
JOINT_ATTRS = ['jointOrient', 'jointOrientX', 'jointOrientY', 'jointOrientZ']

MATRIX = {
    'out': ['matrix', 'worldMatrix', 'inverseMatrix', 'worldInverseMatrix',
            'parentMatrix', 'parentInverseMatrix', 'xformMatrix'],
    'in': ['offsetParentMatrix'],
}
SHAPE_MATRIX = {'out': ['worldMatrix', 'worldInverseMatrix'], 'in': []}

GEO = {
    'mesh': {'label': 'Mesh',
             'out': ['outMesh', 'worldMesh', 'outSmoothMesh'],
             'in': ['inMesh']},
    'nurbsCurve': {'label': 'Curve',
                   'out': ['local', 'worldSpace'],
                   'in': ['create']},
    'nurbsSurface': {'label': 'Surface',
                     'out': ['local', 'worldSpace'],
                     'in': ['create']},
}
DISPLAY_ATTRS = ['visibility', 'intermediateObject', 'overrideEnabled',
                 'overrideDisplayType', 'overrideVisibility', 'overrideColor']
CURVE_DISPLAY = ['lineWidth', 'dispCV']

GENERIC_PREFIX = {
    'out': ('out', 'output', 'world', 'result'),
    'in': ('in', 'input'),
}
OUT_INDEX_CAP = 6     # max existing indices listed for an output multi
ALL_CAP = 600         # max items in the "All" section

# colours
C_XFORM = '#e8a45a'
C_MATRIX = '#b48cf2'
C_GEO = '#6fcf97'
C_DISP = '#8fb3d9'
C_USER = '#56c2e6'
C_KEY = '#c9ccd1'
C_GEN = '#f2c94c'
C_ALL = '#7c828c'

# type families for compatibility
_NUM = {'double', 'doubleLinear', 'doubleAngle', 'float', 'long', 'short',
        'byte', 'char', 'bool', 'enum', 'time', 'floatLinear', 'floatAngle'}
# input types that accept many kinds of data (generic / geometry inputs)
_GENERIC_IN = {'', 'Nothing', 'generic', 'geometry', 'TdataCompound'}


def _family(t):
    if t in _NUM:
        return 'num'
    if t in ('matrix', 'fltMatrix'):
        return 'matrix'
    for n in ('2', '3', '4'):
        if t.endswith(n) and t[:-1] in ('double', 'float', 'long', 'short'):
            return 'vec' + n
    return t


def _compatible(out_type, in_type):
    """True / False, or None when it can't be told (generic or unknown input)."""
    if not out_type or in_type in _GENERIC_IN:
        return None
    return _family(out_type) == _family(in_type)


# =========================================================================== maya queries
def _attr_query(node, attr, **kw):
    try:
        return cmds.attributeQuery(attr, node=node, **kw)
    except (RuntimeError, TypeError):
        return None


def _is_multi(node, attr):
    return bool(_attr_query(node, attr, multi=True))


def _indices(node, attr, mode):
    try:
        idx = cmds.getAttr('{}.{}'.format(node, attr), multiIndices=True) or []
    except (RuntimeError, ValueError):
        idx = []
    if mode == 'out':
        return idx[:OUT_INDEX_CAP] or [0]
    return [max(idx) + 1 if idx else 0]


def _expand(node, attr, mode):
    """Turn an attribute name into concrete plug names (handles multis)."""
    if '.' in attr:                       # child of a multi compound: a.b
        parent, child = attr.split('.', 1)
        if '.' in child:
            return []
        if not _is_multi(node, parent):
            return [child]
        return ['{}[{}].{}'.format(parent, i, child)
                for i in _indices(node, parent, mode)]
    if _is_multi(node, attr):
        return ['{}[{}]'.format(attr, i) for i in _indices(node, attr, mode)]
    return [attr]


def _plug_type(plug):
    try:
        return cmds.getAttr(plug, type=True) or ''
    except (RuntimeError, ValueError):
        return ''


def _plug_info(node, attr, mode):
    plug = '{}.{}'.format(node, attr)
    try:
        conns = cmds.listConnections(plug, s=(mode == 'in'), d=(mode == 'out'),
                                     p=True, skipConversionNodes=True) or []
    except (RuntimeError, ValueError):
        conns = []
    return {'plug': plug, 'node': node, 'attr': attr, 'mode': mode,
            'type': _plug_type(plug), 'conns': conns}


def _make_plugs(node, attrs, mode, seen, cap=None):
    items = []
    for a in attrs or []:
        leaf = a.split('.')[-1]
        if not _attr_query(node, leaf, exists=True):
            continue
        flag = 'writable' if mode == 'in' else 'readable'
        if not _attr_query(node, leaf, **{flag: True}):
            continue
        if '.' not in a:
            a = _attr_query(node, a, longName=True) or a
        for plug_attr in _expand(node, a, mode):
            key = '{}.{}'.format(node, plug_attr)
            if key in seen:
                continue
            seen.add(key)
            items.append(_plug_info(node, plug_attr, mode))
            if cap and len(items) >= cap:
                return items
    return items


def _shapes(node):
    return cmds.listRelatives(node, s=True, ni=True, pa=True) or []


def collect(node, mode, show_all=False):
    """Return [(title, colour, [plug dicts])] for a node in 'in' or 'out' mode."""
    seen, sections = set(), []

    def add(title, colour, attrs, n=node, cap=None):
        items = _make_plugs(n, attrs, mode, seen, cap)
        if items:
            sections.append((title, colour, items))

    def add_shape(shape, suffix=''):
        stype = cmds.nodeType(shape)
        spec = GEO.get(stype)
        if spec:
            add(spec['label'] + suffix, C_GEO, spec[mode], n=shape)
        add('Display' + suffix, C_DISP,
            DISPLAY_ATTRS + (CURVE_DISPLAY if stype == 'nurbsCurve' else []), n=shape)
        add('User Defined' + suffix, C_USER, cmds.listAttr(shape, ud=True), n=shape)

    ntype = cmds.nodeType(node)
    inherited = cmds.nodeType(node, inherited=True) or []

    if 'transform' in inherited:
        main = XFORM_ATTRS + (JOINT_ATTRS if ntype == 'joint' else [])
        add('Transform', C_XFORM, main)
        add('Matrix', C_MATRIX, MATRIX[mode])
        add('User Defined', C_USER, cmds.listAttr(node, ud=True))
        add('Keyable', C_KEY, cmds.listAttr(node, k=True))
        for shape in _shapes(node):
            add_shape(shape, '  ·  ' + shape.split('|')[-1])
    elif ntype in GEO:
        add_shape(node)
        add('Matrix', C_MATRIX, SHAPE_MATRIX[mode])
        add('Keyable', C_KEY, cmds.listAttr(node, k=True))
    else:
        flags = {'w': True} if mode == 'in' else {'r': True}
        prefixes = GENERIC_PREFIX[mode]
        cand = [a for a in (cmds.listAttr(node, c=True, v=True, **flags) or [])
                if a.split('.')[-1].lower().startswith(prefixes)]
        add('Inputs' if mode == 'in' else 'Outputs', C_GEN, cand)
        add('User Defined', C_USER, cmds.listAttr(node, ud=True))
        add('Keyable', C_KEY, cmds.listAttr(node, k=True))

    if show_all:
        flags = {'w': True} if mode == 'in' else {'r': True}
        add('All connectable', C_ALL,
            sorted(cmds.listAttr(node, c=True, **flags) or []), cap=ALL_CAP)
    return sections


def _channelbox_attr(node):
    try:
        sel = cmds.channelBox('mainChannelBox', q=True, sma=True) or []
    except RuntimeError:
        return None
    for a in sel:
        long_name = _attr_query(node, a, longName=True)
        if long_name:
            return long_name
    return None


# =========================================================================== UI
STYLE = """
QFrame#panel {
    background: #24262b; border: 1px solid #3a3d44; border-radius: 10px;
}
QLabel { color: #d7d9dd; }
QLabel#chip {
    background: #2f3238; border-radius: 6px; padding: 4px 9px;
}
QLabel#arrow { color: #4a7cf0; font-size: 15px; font-weight: bold; }
QLabel#step { color: #9aa0a6; font-size: 11px; padding-left: 2px; }
QLabel#status { color: #8a9099; font-size: 11px; padding: 0 2px; }
QLineEdit {
    background: #1b1d21; border: 1px solid #33363d; border-radius: 6px;
    padding: 5px 8px; color: #e6e6e6; selection-background-color: #4a7cf0;
}
QLineEdit:focus { border-color: #4a7cf0; }
QTreeWidget {
    background: #1e2024; border: 1px solid #2f3238; border-radius: 6px;
    color: #d7d9dd; outline: 0; padding: 3px;
}
QTreeWidget::item { height: 21px; border-radius: 4px; padding-left: 2px; }
QTreeWidget::item:hover { background: #2c3038; }
QTreeWidget::item:selected { background: #355bb8; color: #ffffff; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #3d414a; border-radius: 4px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #4a4f59; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: none; }
QPushButton#flat {
    background: transparent; border: none; color: #9aa0a6;
    font-size: 13px; padding: 3px 8px; border-radius: 5px;
}
QPushButton#flat:hover { background: #33363d; color: #ffffff; }
QPushButton#flat:checked { background: #355bb8; color: #ffffff; }
QToolTip {
    background: #1b1d21; color: #e6e6e6; border: 1px solid #3a3d44; padding: 4px;
}
"""

STATUS_COLORS = {'hint': '#8a9099', 'ok': '#6fcf97', 'warn': '#f2c94c', 'error': '#eb5757'}
HINT_OUT = 'Pick the attribute to connect from   ·   type to filter'
POPUP_WIDTH = 360
ROW_H = 22

# Popup transparency, 0 = solid, 100 = invisible (capped at 90 so it never vanishes).
# Change it here, per call with show(transparency=30), or permanently with
# set_transparency(30), which is saved in Maya's prefs and wins over this default.
TRANSPARENCY = 12
OV_TRANSPARENCY = 'mnmConnectPopUP_transparency'

_DOTS = {}
_POPUP = None


def _dot(colour, filled):
    key = (colour, filled)
    if key not in _DOTS:
        pm = QtGui.QPixmap(12, 12)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        c = QtGui.QColor(colour)
        p.setPen(QtGui.QPen(c, 1.6))
        p.setBrush(QtGui.QBrush(c) if filled else QtCore.Qt.NoBrush)
        p.drawEllipse(QtCore.QRectF(2.5, 2.5, 7, 7))
        p.end()
        _DOTS[key] = QtGui.QIcon(pm)
    return _DOTS[key]


def _scaled_font(scale=0.85, bold=False):
    f = QtGui.QFont()
    if f.pointSizeF() > 0:
        f.setPointSizeF(f.pointSizeF() * scale)
    f.setBold(bold)
    return f


def _chip_html(node, active):
    ntype = cmds.nodeType(node)
    shapes = _shapes(node) if ntype in ('transform', 'joint') else []
    if shapes:
        ntype += ' · ' + cmds.nodeType(shapes[0])
    name_col = '#ffffff' if active else '#8a9099'
    return ("<span style='color:{};font-weight:600'>{}</span>"
            "&nbsp;&nbsp;<span style='color:#6f757e;font-size:10px'>{}</span>"
            ).format(name_col, node.split('|')[-1], ntype)


def _maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


def _children(tree):
    for i in range(tree.topLevelItemCount()):
        group = tree.topLevelItem(i)
        for j in range(group.childCount()):
            yield group, group.child(j)


class ConnectPopup(QtWidgets.QWidget):
    def __init__(self, src, dst, parent=None):
        super(ConnectPopup, self).__init__(parent)
        self.src, self.dst = src, dst
        self.step = 1
        self.current_out = None
        self.show_all = False

        self.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint
                            | QtCore.Qt.NoDropShadowWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._show_outputs(preselect_channelbox=True)

    # ------------------------------------------------------------------ layout
    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        panel = QtWidgets.QFrame(objectName='panel')
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 6)
        shadow.setColor(QtGui.QColor(0, 0, 0, 170))
        panel.setGraphicsEffect(shadow)
        outer.addWidget(panel)

        lay = QtWidgets.QVBoxLayout(panel)
        lay.setContentsMargins(10, 10, 10, 8)
        lay.setSpacing(7)

        # row 1: source -> target
        row1 = QtWidgets.QHBoxLayout()
        row1.setSpacing(5)
        self.src_chip = QtWidgets.QLabel(objectName='chip')
        self.dst_chip = QtWidgets.QLabel(objectName='chip')
        arrow = QtWidgets.QLabel('➜', objectName='arrow')
        close_btn = self._flat_btn('✕', 'Close (Esc)')
        for w in (self.src_chip, arrow, self.dst_chip):
            row1.addWidget(w)
        row1.addStretch(1)
        row1.addWidget(close_btn)
        lay.addLayout(row1)

        # row 2: step label + buttons
        row2 = QtWidgets.QHBoxLayout()
        row2.setSpacing(4)
        self.back_btn = self._flat_btn('‹  Back', 'Back to the source attributes (Backspace)')
        self.step_label = QtWidgets.QLabel(objectName='step')
        self.all_btn = self._flat_btn('All', 'Show every connectable attribute', checkable=True)
        swap_btn = self._flat_btn('⇄', 'Swap source and target')
        row2.addWidget(self.back_btn)
        row2.addWidget(self.step_label, 1)
        row2.addWidget(self.all_btn)
        row2.addWidget(swap_btn)
        lay.addLayout(row2)

        self.search = QtWidgets.QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.installEventFilter(self)
        lay.addWidget(self.search)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(6)
        self.tree.setUniformRowHeights(True)
        self.tree.setFocusPolicy(QtCore.Qt.NoFocus)   # keep typing in the filter
        self.tree.setMouseTracking(True)
        self.tree.setIconSize(QtCore.QSize(12, 12))
        h = self.tree.header()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        h.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        lay.addWidget(self.tree, 1)

        self.status = QtWidgets.QLabel(objectName='status')
        self.status.setWordWrap(True)
        lay.addWidget(self.status)

        self.search.textChanged.connect(self._apply_filter)
        self.search.returnPressed.connect(self._on_return)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.back_btn.clicked.connect(self._back)
        self.all_btn.toggled.connect(self._toggle_all)
        swap_btn.clicked.connect(self._swap)
        close_btn.clicked.connect(self.close)

    def _flat_btn(self, text, tip, checkable=False):
        b = QtWidgets.QPushButton(text, objectName='flat')
        b.setToolTip(tip)
        b.setCheckable(checkable)
        b.setFocusPolicy(QtCore.Qt.NoFocus)
        b.setCursor(QtCore.Qt.PointingHandCursor)
        return b

    # ------------------------------------------------------------------ steps
    def _show_outputs(self, preselect_channelbox=False):
        """Step 1: output attributes of the source."""
        keep = self.current_out['plug'] if self.current_out else None
        self.step = 1
        self.back_btn.hide()
        self.src_chip.setText(_chip_html(self.src, True))
        self.dst_chip.setText(_chip_html(self.dst, False))
        self.step_label.setText(
            "<span style='color:#4a7cf0;font-weight:bold'>1</span>&nbsp;&nbsp;"
            "OUTPUT of <b>{}</b>".format(self.src.split('|')[-1]))
        self.search.setPlaceholderText('Filter outputs…')

        self._fill(collect(self.src, 'out', self.show_all))
        self._reset_filter()

        want = _channelbox_attr(self.src) if preselect_channelbox and not keep else None
        for item in self._visible_items():
            d = item.data(0, QtCore.Qt.UserRole)
            if d['plug'] == keep or (want and d['attr'] == want):
                self._set_current(item)
                break

        self._status(HINT_OUT)
        self._fit_and_place()

    def _show_inputs(self):
        """Step 2: inputs of the target that can take the chosen output."""
        out = self.current_out
        self.step = 2
        self.back_btn.show()
        self.src_chip.setText(_chip_html(self.src, False))
        self.dst_chip.setText(_chip_html(self.dst, True))
        self.step_label.setText(
            "<span style='color:#4a7cf0;font-weight:bold'>2</span>&nbsp;&nbsp;"
            "INPUT of <b>{}</b>".format(self.dst.split('|')[-1]))
        self.search.setPlaceholderText('Filter inputs…')

        sections = collect(self.dst, 'in', self.show_all)
        if not self.show_all:
            filtered = []
            for title, colour, items in sections:
                keep = [i for i in items if _compatible(out['type'], i['type']) is not False]
                if keep:
                    filtered.append((title, colour, keep))
            sections = filtered

        self._fill(sections)
        self._dim_incompatible()
        self._reset_filter()

        if sections:
            self._status("<b>{}</b>  <span style='color:#6f757e'>{}</span>  ➜  pick the input"
                         .format(out['attr'], out['type'] or 'unknown type'))
        else:
            self._status('No inputs on {} take a {} – press All to see everything'
                         .format(self.dst.split('|')[-1], out['type'] or 'this'), 'warn')
        self._fit_and_place()

    def _back(self):
        if self.step == 2:
            self._show_outputs()

    # ------------------------------------------------------------------ list helpers
    def _fill(self, sections):
        self.tree.clear()
        group_font = _scaled_font(0.85, bold=True)
        small_font = _scaled_font(0.85)
        group_bg = QtGui.QColor('#25282d')
        for title, colour, items in sections:
            g = QtWidgets.QTreeWidgetItem(self.tree)
            g.setText(0, title.upper())
            g.setText(1, str(len(items)))
            g.setFlags(QtCore.Qt.ItemIsEnabled)
            g.setForeground(0, QtGui.QColor(colour))
            g.setForeground(1, QtGui.QColor('#5b6068'))
            for col in (0, 1):
                g.setFont(col, group_font)
                g.setBackground(col, group_bg)
            for it in items:
                c = QtWidgets.QTreeWidgetItem(g)
                c.setText(0, it['attr'])
                c.setText(1, it['type'])
                c.setIcon(0, _dot(colour, bool(it['conns'])))
                c.setFont(1, small_font)
                c.setForeground(1, QtGui.QColor('#6f757e'))
                c.setData(0, QtCore.Qt.UserRole, it)
                arrow = '← ' if it['mode'] == 'in' else '→ '
                tip = '<b>{}</b><br><span style="color:#8a9099">{}</span>'.format(
                    it['plug'], it['type'] or 'unknown type')
                if it['conns']:
                    tip += '<br>' + '<br>'.join(arrow + p for p in it['conns'][:8])
                c.setToolTip(0, tip)
            g.setExpanded(True)

    def _dim_incompatible(self):
        out_type = self.current_out['type'] if self.current_out else None
        dim = QtGui.QColor('#565b63')
        for _, c in _children(self.tree):
            if _compatible(out_type, c.data(0, QtCore.Qt.UserRole)['type']) is False:
                c.setForeground(0, dim)

    def _visible_items(self):
        return [c for g, c in _children(self.tree) if not g.isHidden() and not c.isHidden()]

    def _set_current(self, item):
        self.tree.setCurrentItem(item)
        self.tree.scrollToItem(item)

    def _current_visible(self):
        cur = self.tree.currentItem()
        if cur is not None and cur.parent() is not None and not cur.isHidden():
            return cur
        vis = self._visible_items()
        return vis[0] if vis else None

    def _reset_filter(self):
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self._apply_filter('')

    def _apply_filter(self, text):
        text = text.strip().lower()
        wild = '*' in text or '?' in text
        for i in range(self.tree.topLevelItemCount()):
            g = self.tree.topLevelItem(i)
            visible = 0
            for j in range(g.childCount()):
                c = g.child(j)
                name = c.text(0).lower()
                match = (not text) or (fnmatch(name, text) if wild else text in name)
                c.setHidden(not match)
                visible += match
            g.setHidden(visible == 0)
        cur = self.tree.currentItem()
        if cur is None or cur.isHidden() or cur.parent() is None:
            vis = self._visible_items()
            if vis:
                self._set_current(vis[0])

    def _move(self, delta):
        vis = self._visible_items()
        if not vis:
            return
        cur = self.tree.currentItem()
        idx = vis.index(cur) if cur in vis else -1
        self._set_current(vis[max(0, min(len(vis) - 1, idx + delta))])

    # ------------------------------------------------------------------ actions
    def _pick(self, item):
        d = item.data(0, QtCore.Qt.UserRole) if item else None
        if not d:
            return
        if self.step == 1:
            self.current_out = d
            self._show_inputs()
        else:
            self._connect(self.current_out['plug'], d['plug'])

    def _on_item_clicked(self, item, _col=0):
        self._pick(item)

    def _on_return(self):
        item = self._current_visible()
        if item is None:
            self._status('Nothing matches this filter', 'warn')
            return
        self._pick(item)

    def _connect(self, src_plug, dst_plug):
        try:
            cmds.connectAttr(src_plug, dst_plug, f=True)
        except RuntimeError as e:
            msg = str(e).strip().splitlines()[-1] if str(e).strip() else 'connection refused'
            self._status('✕  {}  ➜  {}<br>{}'.format(src_plug, dst_plug, msg), 'error')
            return
        print('{} --->>> {}'.format(src_plug, dst_plug))

        if QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            self._show_inputs()      # refresh dots / next free multi index
            self._status('✓  {}  ➜  {}   (Shift: still open)'.format(src_plug, dst_plug), 'ok')
        else:
            cmds.inViewMessage(amg='<hl>{}</hl>  ➜  <hl>{}</hl>'.format(src_plug, dst_plug),
                               pos='botCenter', fade=True)
            self.close()

    def _swap(self):
        self.src, self.dst = self.dst, self.src
        self.current_out = None
        self._show_outputs()

    def _toggle_all(self, state):
        self.show_all = bool(state)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            if self.step == 2 and self.current_out:
                self._show_inputs()
            else:
                self._show_outputs()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _status(self, text, kind='hint'):
        self.status.setStyleSheet('color: {};'.format(STATUS_COLORS.get(kind, STATUS_COLORS['hint'])))
        self.status.setText(text)

    # ------------------------------------------------------------------ keys
    def eventFilter(self, obj, ev):
        if obj is self.search and ev.type() == QtCore.QEvent.KeyPress:
            key = ev.key()
            if key == QtCore.Qt.Key_Down:
                self._move(1)
                return True
            if key == QtCore.Qt.Key_Up:
                self._move(-1)
                return True
            if (key in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Left)
                    and not self.search.text() and self.step == 2):
                self._back()
                return True
        return super(ConnectPopup, self).eventFilter(obj, ev)

    # ------------------------------------------------------------------ size / placement
    def _fit_and_place(self):
        rows = sum(1 for i in range(self.tree.topLevelItemCount())) + len(self._visible_items())
        height = max(260, min(620, 150 + rows * ROW_H))
        self.resize(POPUP_WIDTH + 32, height)
        # First list opens at the cursor; every later list (step 2, Back, All,
        # Swap) keeps that same top-left corner, only pulled in if the new
        # height would run off the screen.
        anchor = getattr(self, '_anchor', None)
        if anchor is None:
            self.place_at_cursor()
            self._anchor = self.pos()
        else:
            self._move_on_screen(anchor)
        self.search.setFocus()

    def _move_on_screen(self, pos):
        screen = QtGui.QGuiApplication.screenAt(pos) or QtGui.QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = min(max(pos.x(), geo.left()), geo.right() - self.width())
        y = min(max(pos.y(), geo.top()), geo.bottom() - self.height())
        self.move(x, y)

    def place_at_cursor(self):
        pos = QtGui.QCursor.pos()
        screen = QtGui.QGuiApplication.screenAt(pos) or QtGui.QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        w, h = self.width(), self.height()
        x = min(max(pos.x() - w // 2, geo.left()), geo.right() - w)
        y = min(max(pos.y() - 90, geo.top()), geo.bottom() - h)
        self.move(x, y)


# =========================================================================== entry points
def get_transparency():
    """Current transparency 0-100: saved pref if set, otherwise TRANSPARENCY."""
    if cmds.optionVar(exists=OV_TRANSPARENCY):
        return cmds.optionVar(q=OV_TRANSPARENCY)
    return TRANSPARENCY


def set_transparency(value):
    """Save the popup transparency (0 = solid, 100 = invisible) in Maya's prefs."""
    value = max(0, min(90, int(value)))
    cmds.optionVar(iv=(OV_TRANSPARENCY, value))
    try:
        if _POPUP is not None:
            _POPUP.setWindowOpacity(1.0 - value / 100.0)
    except RuntimeError:
        pass
    return value


def show(transparency=None):
    """Open the connect popup for the two selected nodes (source, target).

    transparency: 0-100 for this popup only; None uses get_transparency().
    """
    global _POPUP
    sel = cmds.ls(sl=True)
    if len(sel) != 2:
        cmds.inViewMessage(amg='Select <hl>two</hl> nodes: source, then target',
                           pos='midCenter', fade=True)
        return None
    try:
        if _POPUP is not None:
            _POPUP.close()
    except RuntimeError:      # Qt object already deleted
        pass
    _POPUP = ConnectPopup(sel[0], sel[1], _maya_window())
    amount = get_transparency() if transparency is None else transparency
    amount = max(0, min(90, int(amount)))
    _POPUP.setWindowOpacity(1.0 - amount / 100.0)
    _POPUP.show()
    _POPUP.activateWindow()
    _POPUP.search.setFocus()
    return _POPUP


def mnmNodeAttr(*_args, **_kwargs):
    """Backward compatible name: old shelf buttons calling mnmNodeAttr('out') still work."""
    return show()