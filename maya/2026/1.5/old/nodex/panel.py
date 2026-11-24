"""The NodeX panel: Maya chrome in QWidgets around a QML board (QQuickWidget).

    import nodex; nodex.show()

The panel lives in a workspaceControl. Cleanup hangs on the control's closeCommand: a
dockable control never calls closeEvent (global leaf maya-qt-window-and-widget-traps).
"""
import os

from .qt import QT_MAJOR, QActionGroup, QtCore, QtGui, QtQuickWidgets, QtWidgets, ival, wrapInstance

from . import bridge as bridge_mod
from . import keys, model, theme

HERE = os.path.dirname(os.path.abspath(__file__))
QML_DIR = os.path.join(HERE, "qml")
TB_DIR = os.path.join(HERE, "icons", "toolbar")
CONTROL = "NodeXWorkspaceControl"

# Maya's nodeEdCreateToolbar, same groups and order.
TOOLBAR = [
    (None, [("create", "createNode", "Create node (Tab)")]),
    ("Graph", [("sync", "syncOn", "Sync: nodes created / deleted / renamed in the scene follow on the board"),
               ("up", "hsUpStreamCon", "Graph input connections"),
               ("updown", "hsUpDownStreamCon", "Graph input and output connections"),
               ("down", "hsDownStreamCon", "Graph output connections")]),
    ("Layout", [("clear", "hsClearView", "Clear graph"),
                ("add", "nodeGrapherAddNodes", "Add selected nodes to graph"),
                ("remove", "nodeGrapherRemoveNodes", "Remove selected nodes from graph"),
                ("arrange", "hsRearrange", "Rearrange graph")]),
    ("Attributes", [("simple", "nodeGrapherModeSimpleLarge", "Simple mode: header only (1)"),
                    ("connected", "nodeGrapherModeConnectedLarge", "Connected mode: connected attributes (2)"),
                    ("full", "nodeGrapherModeAllLarge", "Full mode: Maya's interesting attributes (3)"),
                    ("custom", "nodeGrapherModeCustomLarge", "Custom mode: Maya's node template + connected (4)"),
                    ("filter", "search", "Attribute filter on all nodes"),
                    ("swatch", "nodeGrapherSwatchToggle", "Toggle swatch size (no swatches in v1)")]),
    ("Bookmarks", [("bmAdd", "addBookmark", "Bookmark the current view"),
                   ("bmEdit", "editBookmark", "Edit bookmarks (v2)"),
                   ("bmPrev", "SP_FileDialogBack", "Previous bookmark"),
                   ("bmNext", "SP_FileDialogForward", "Next bookmark")]),
    ("Display", [("shAll", "nodeGrapherDisplayAll", "Graph all shapes"),
                 ("shExc", "nodeGrapherDisplayAllExcept", "Graph all shapes except shading networks"),
                 ("shNone", "nodeGrapherDisplayNone", "Graph no shapes"),
                 ("lock", "nodeGrapherUnlocked", "Lock graph: nothing is added or removed")]),
    ("Traversal depth", [("dZero", "zeroDepth", "Traversal depth 0"),
                         ("dLess", "reduceDepth", "Reduce traversal depth"),
                         ("depth", None, "Traversal depth for input and output graphing"),
                         ("dMore", "increaseDepth", "Increase traversal depth"),
                         ("dInf", "unlimitedDepth", "Unlimited traversal depth")]),
    ("Wires", [("links", "nodeLinks", "Node links (W): one wire per node pair, detail on hover and "
                                      "selection; on by itself above 1200 connections")]),
    ("Grid", [("grid", "nodeGridDisplay", "Show grid"),
              ("snap", "snapGrid", "Snap nodes to grid")]),
    ("Filter", [("find", None, "Find node or attribute")]),
]

def _icon(name):
    return QtGui.QIcon(os.path.join(TB_DIR, name + ".png"))


MAYA_MIME_HINTS = ("maya", "text/plain", "text/uri-list")


def dropped_names(mime):
    """Node names carried by a drag from the Outliner / Hypergraph / any Maya list.

    Maya's drags carry the names as text (one per line, sometimes space separated) and in a
    Maya-specific format; every readable text format is scanned and the names are resolved
    against the scene by the caller (cmds.ls), so stray words cost nothing."""
    chunks = []
    if mime.hasText():
        chunks.append(mime.text())
    for fmt in mime.formats():
        if "maya" not in fmt.lower():
            continue
        raw = bytes(mime.data(fmt))
        for enc in ("utf-8", "utf-16"):
            try:
                chunks.append(raw.decode(enc))
                break
            except UnicodeDecodeError:
                continue
    names = []
    for chunk in chunks:
        for tok in chunk.replace("\0", " ").split():
            tok = tok.strip().strip("'\"")
            if tok and tok not in names and all(c.isalnum() or c in "_|:" for c in tok):
                names.append(tok)
    return names


def _is_maya_drag(mime):
    return mime.hasText() or any("maya" in f.lower() for f in mime.formats())


def _event_pos(ev):
    """Drop position in widget coordinates: position() in Qt 6, pos() in Qt 5."""
    return ev.position() if hasattr(ev, "position") else QtCore.QPointF(ev.pos())


def maya_qml_dir():
    root = os.environ.get("MAYA_LOCATION") or "C:/Program Files/Autodesk/Maya2024"
    return os.path.join(root, "qml")


class ClipRow(QtWidgets.QWidget):
    """Holds a row of chrome at its natural width and cuts it off at the right edge, as Maya's
    Node Editor toolbar does, instead of squeezing the buttons or holding the panel wide."""

    def __init__(self, inner, height, parent=None):
        super(ClipRow, self).__init__(parent)
        self.inner = inner
        inner.setParent(self)
        inner.installEventFilter(self)
        self.setFixedHeight(height)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)

    def minimumSizeHint(self):
        return QtCore.QSize(0, self.height())

    def sizeHint(self):
        return QtCore.QSize(self.inner.sizeHint().width(), self.height())

    def _fit(self):
        self.inner.setGeometry(0, 0, max(self.width(), self.inner.sizeHint().width()), self.height())

    def resizeEvent(self, ev):
        self._fit()

    def eventFilter(self, obj, ev):
        # A group grip hides or shows buttons: the natural width changes.
        if obj is self.inner and ev.type() == QtCore.QEvent.LayoutRequest:
            QtCore.QTimer.singleShot(0, self._fit)
        return False


class _DescDelegate(QtWidgets.QStyledItemDelegate):
    """icon, name, then a faint description in its own column."""
    DESC_X = 170

    def paint(self, painter, option, index):
        desc = index.data(QtCore.Qt.UserRole + 1)
        super(_DescDelegate, self).paint(painter, option, index)
        if desc:
            painter.save()
            painter.setPen(QtGui.QColor(theme.CHROME["faint"] if not option.state & QtWidgets.QStyle.State_Selected
                                        else theme.CHROME["text"]))
            r = option.rect.adjusted(self.DESC_X, 0, -6, 0)
            painter.drawText(r, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                             option.fontMetrics.elidedText(desc, QtCore.Qt.ElideRight, r.width()))
            painter.restore()


class SearchPalette(QtWidgets.QFrame):
    """One search popup for every "which node?" question: Tab create, wire inbetween and
    link-drag search. `provider(query)` returns rows {"label", "data", "desc", "icon", "head"};
    a head row is a bold group title. Enter / click picks, Shift+Enter picks with `alt` set."""
    chosen = QtCore.Signal(object, bool)

    def __init__(self, parent=None):
        super(SearchPalette, self).__init__(parent, QtCore.Qt.Popup)
        self.setFixedWidth(380)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.title = QtWidgets.QLabel()
        self.title.setStyleSheet("color:%s;padding:4px 8px 2px 8px" % theme.CHROME["muted"])
        self.edit = QtWidgets.QLineEdit()
        self.list = QtWidgets.QListWidget()
        self.list.setIconSize(QtCore.QSize(16, 16))
        self.list.setFixedHeight(340)
        self.list.setItemDelegate(_DescDelegate(self.list))
        self.hint = QtWidgets.QLabel()
        self.hint.setStyleSheet("color:%s;padding:2px 8px 4px 8px;font-size:11px" % theme.CHROME["faint"])
        for w in (self.title, self.edit, self.list, self.hint):
            lay.addWidget(w)
        self.edit.textChanged.connect(self.refill)
        self.edit.installEventFilter(self)
        self.list.itemActivated.connect(lambda it: self._pick(it, False))
        self.list.itemClicked.connect(lambda it: self._pick(
            it, bool(QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier)))
        self.provider = None
        self.on_pick = None
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(60)
        self._timer.timeout.connect(self._fill)

    def _add(self, row):
        it = QtWidgets.QListWidgetItem(row.get("label", ""))
        if row.get("head"):
            it.setFlags(QtCore.Qt.NoItemFlags)
            f = it.font()
            f.setBold(True)
            it.setFont(f)
        else:
            icon_type = row.get("icon")
            if icon_type:
                icon = QtGui.QIcon(":/out_%s.png" % icon_type)
                if not icon.pixmap(16, 16).isNull():
                    it.setIcon(icon)
            it.setData(QtCore.Qt.UserRole, row.get("data"))
            it.setData(QtCore.Qt.UserRole + 1, row.get("desc", ""))
            if row.get("tip"):
                it.setToolTip(row["tip"])
        self.list.addItem(it)

    def refill(self, *_):
        self._timer.start()

    def _fill(self):
        self.list.clear()
        try:
            rows = self.provider(self.edit.text().strip()) if self.provider else []
        except Exception as e:                     # a provider error must not kill the popup
            rows = [{"label": "Search failed: %s" % e, "head": True}]
        for row in rows[:300]:
            self._add(row)
        for i in range(self.list.count()):
            if self.list.item(i).flags() & QtCore.Qt.ItemIsSelectable:
                self.list.setCurrentRow(i)
                break

    def eventFilter(self, obj, ev):
        if obj is self.edit and ev.type() == QtCore.QEvent.KeyPress:
            k = ev.key()
            if k in (QtCore.Qt.Key_Down, QtCore.Qt.Key_Up, QtCore.Qt.Key_PageDown, QtCore.Qt.Key_PageUp):
                step = 1 if k in (QtCore.Qt.Key_Down, QtCore.Qt.Key_PageDown) else -1
                times = 10 if k in (QtCore.Qt.Key_PageDown, QtCore.Qt.Key_PageUp) else 1
                r = self.list.currentRow()
                for _ in range(times):
                    for _ in range(self.list.count()):
                        r = (r + step) % max(1, self.list.count())
                        if self.list.item(r).flags() & QtCore.Qt.ItemIsSelectable:
                            break
                self.list.setCurrentRow(r)
                return True
            if k in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                if self._timer.isActive():
                    self._timer.stop()
                    self._fill()
                it = self.list.currentItem()
                if it is not None:
                    self._pick(it, bool(ev.modifiers() & QtCore.Qt.ShiftModifier))
                return True
            if k in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Tab):
                self.hide()
                return True
        return super(SearchPalette, self).eventFilter(obj, ev)

    def _pick(self, it, alt):
        data = it.data(QtCore.Qt.UserRole)
        if data is None:
            return
        self.hide()
        cb = self.on_pick
        if cb is not None:
            cb(data, alt)
        self.chosen.emit(data, alt)

    def open(self, provider, on_pick, global_pos, title="", hint="", text=""):
        self.provider, self.on_pick = provider, on_pick
        self.title.setText(title)
        self.title.setVisible(bool(title))
        self.hint.setText(hint)
        self.hint.setVisible(bool(hint))
        self.edit.blockSignals(True)
        self.edit.setText(text)
        self.edit.blockSignals(False)
        self.edit.setPlaceholderText("Search")
        self._fill()
        screen = QtWidgets.QApplication.screenAt(global_pos) or QtWidgets.QApplication.primaryScreen()
        g = screen.availableGeometry()
        self.adjustSize()
        x = min(max(g.left(), global_pos.x()), g.right() - self.width())
        y = min(max(g.top(), global_pos.y()), g.bottom() - self.sizeHint().height())
        self.move(x, y)
        self.show()
        self.raise_()
        self.edit.setFocus()


class NodeXPanel(QtWidgets.QWidget):
    # Keys the board handles itself; Maya's hotkeys must not steal them while it has focus.
    OWN_KEYS = {QtCore.Qt.Key_1, QtCore.Qt.Key_2, QtCore.Qt.Key_3, QtCore.Qt.Key_4, QtCore.Qt.Key_W,
                QtCore.Qt.Key_F, QtCore.Qt.Key_F2, QtCore.Qt.Key_A,
                QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Escape, QtCore.Qt.Key_Tab,
                QtCore.Qt.Key_I, QtCore.Qt.Key_O, QtCore.Qt.Key_T, QtCore.Qt.Key_L, QtCore.Qt.Key_S}

    @classmethod
    def owns_key(cls, key, modifiers):
        """Reserve only supported combinations while the board, rather than an editor, has focus."""
        mods = ival(modifiers) & ival(QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier |
                                      QtCore.Qt.ShiftModifier | QtCore.Qt.MetaModifier)
        ctrl, alt, shift = [ival(m) for m in (QtCore.Qt.ControlModifier, QtCore.Qt.AltModifier,
                                           QtCore.Qt.ShiftModifier)]
        if mods == ctrl:
            return key in (QtCore.Qt.Key_C, QtCore.Qt.Key_V, QtCore.Qt.Key_J)
        if mods & ctrl or mods & ival(QtCore.Qt.MetaModifier):
            return False
        if mods & alt:
            return key in (QtCore.Qt.Key_I, QtCore.Qt.Key_O, QtCore.Qt.Key_T,
                           QtCore.Qt.Key_L, QtCore.Qt.Key_S)
        if key == QtCore.Qt.Key_K:
            return mods in (0, shift)
        if key == QtCore.Qt.Key_D:
            return mods == shift
        return key in cls.OWN_KEYS

    def __init__(self, parent=None):
        super(NodeXPanel, self).__init__(parent)
        self.setObjectName("NodeXPanel")
        self.bridge = bridge_mod.Bridge(self)
        self.buttons = {}
        self._build()
        self._connect()
        self.bridge.start()

    # ------------------------------------------------------------------ build

    def _build(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.menubar = QtWidgets.QMenuBar()
        self.menu_row = ClipRow(self.menubar, 22)      # true height once the menus exist
        lay.addWidget(self.menu_row)
        self._build_toolbar(lay)
        self._build_tabs(lay)

        self.quick = QtQuickWidgets.QQuickWidget(self)
        self.quick.setResizeMode(QtQuickWidgets.QQuickWidget.SizeRootObjectToView)
        self.quick.setClearColor(QtGui.QColor(theme.CHROME["canvas"]))
        self.quick.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.quick.setMinimumSize(0, 0)
        self.quick.setAcceptDrops(True)       # nodes dragged in from the Outliner
        self.quick.engine().addImportPath(maya_qml_dir())
        self.quick.rootContext().setContextProperty("bridge", self.bridge)
        # Qt 6 ShaderEffects take precompiled .qsb files, Qt 5 inline GLSL: Board/Node pick by this.
        self.quick.rootContext().setContextProperty("qtMajor", QT_MAJOR)
        self.quick.setSource(QtCore.QUrl.fromLocalFile(os.path.join(QML_DIR, "Board.qml")))
        errs = [e.toString() for e in self.quick.errors()]
        if errs:
            raise RuntimeError("NodeX QML failed:\n" + "\n".join(errs))
        self.quick.installEventFilter(self)
        self.quick.quickWindow().installEventFilter(self)
        lay.addWidget(self.quick, 1)

        self._build_status(lay)
        self._build_menus()
        self.menu_row.setFixedHeight(self.menubar.sizeHint().height())
        self.palette = SearchPalette(self)
        self.bridge.open_search = self._open_search
        self._create_pos = None

    def _tool_button(self, key, icon, tip):
        b = QtWidgets.QToolButton()
        b.setAutoRaise(True)
        b.setIcon(_icon(icon))
        b.setIconSize(QtCore.QSize(20, 20))
        b.setFixedSize(28, 26)
        b.setToolTip(tip)
        self.buttons[key] = b
        return b

    def _build_toolbar(self, lay):
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(32)
        h = QtWidgets.QHBoxLayout(bar)
        h.setContentsMargins(12, 2, 12, 2)
        h.setSpacing(1)
        self.groups = {}
        checkable = {"sync", "filter", "swatch", "lock", "grid", "snap", "links", "simple", "connected", "full",
                     "custom", "shAll", "shExc", "shNone"}
        for grp, items in TOOLBAR:
            box = QtWidgets.QWidget()
            bh = QtWidgets.QHBoxLayout(box)
            bh.setContentsMargins(0, 0, 0, 0)
            bh.setSpacing(1)
            inner = []
            if grp:
                grip = QtWidgets.QToolButton()
                grip.setAutoRaise(True)
                grip.setIcon(_icon("openBar"))
                grip.setIconSize(QtCore.QSize(7, 20))
                grip.setFixedSize(12, 26)
                grip.setToolTip("Show or hide the %s buttons" % grp)
                bh.addWidget(grip)
            for key, icon, tip in items:
                if key == "depth":
                    w = QtWidgets.QLineEdit("1")
                    w.setFixedWidth(30)
                    w.setAlignment(QtCore.Qt.AlignCenter)
                    w.setToolTip(tip)
                    self.depth_field = w
                elif key == "find":
                    w = QtWidgets.QLineEdit()
                    w.setPlaceholderText("Find node or attribute")
                    w.setFixedWidth(210)
                    w.setClearButtonEnabled(True)
                    w.setToolTip("Dims what does not match; Enter selects and frames the matches")
                    self.find_field = w
                else:
                    w = self._tool_button(key, icon, tip)
                    if key in checkable:
                        w.setCheckable(True)
                bh.addWidget(w)
                inner.append(w)
            if grp:
                grip.clicked.connect(lambda _=False, ws=inner: [x.setVisible(not x.isVisible()) for x in ws])
            h.addWidget(box)
            if grp not in ("Filter",):
                h.addSpacing(4)
        h.addStretch(1)
        lay.addWidget(ClipRow(bar, 32))
        b = self.buttons
        b["sync"].setChecked(True)
        b["connected"].setChecked(True)
        b[{"all": "shAll", "none": "shNone"}.get(self.bridge.shapes, "shExc")].setChecked(True)
        b["grid"].setChecked(True)
        self.mode_group = QtWidgets.QButtonGroup(self)
        for k in ("simple", "connected", "full", "custom"):
            self.mode_group.addButton(b[k])
        self.shape_group = QtWidgets.QButtonGroup(self)
        for k in ("shAll", "shExc", "shNone"):
            self.shape_group.addButton(b[k])

    def _build_tabs(self, lay):
        # 26 px row on --panel, flat --panel-lo tabs with 4 px top radii,
        # the active tab takes the canvas colour so it merges into the board below.
        c = theme.CHROME
        row = QtWidgets.QWidget()
        row.setObjectName("nodexTabs")
        row.setFixedHeight(26)
        row.setStyleSheet(
            "#nodexTabs{background:%(panel)s}"
            "QTabBar{background:transparent;border:0}"
            "QTabBar::tab{background:%(panelLo)s;color:%(muted)s;border:0;margin:4px 1px 0 0;"
            "padding:3px 14px;border-top-left-radius:4px;border-top-right-radius:4px}"
            "QTabBar::tab:hover:!selected{color:%(text)s}"
            "QTabBar::tab:selected{background:%(canvas)s;color:%(ink)s}"
            "QTabBar::close-button{subcontrol-position:right;margin-left:4px}"
            "QToolButton{background:transparent;border:0;color:%(muted)s;padding:3px 8px;margin-top:4px}"
            "QToolButton:hover{color:%(ink)s}"
            "QToolButton::menu-indicator{image:none}"
            # "+" sits right after the last tab and reads as a button, not as a stray glyph.
            "QToolButton#nodexAddTab{color:%(ink)s;font-size:15px;padding:0 7px 1px 7px;"
            "margin:4px 0 0 4px;border-radius:4px;background:%(panelLo)s}"
            "QToolButton#nodexAddTab:hover{background:#555555}" % c)
        h = QtWidgets.QHBoxLayout(row)
        h.setContentsMargins(16, 0, 12, 0)
        h.setSpacing(0)
        self.tabbar = QtWidgets.QTabBar()
        self.tabbar.setTabsClosable(True)
        self.tabbar.setMovable(False)
        self.tabbar.setExpanding(False)
        self.tabbar.setDocumentMode(True)
        self.tabbar.setDrawBase(False)
        # Never wider than its tabs, so "+" follows the last tab. Scroll arrows and eliding make
        # the minimum width 145 px even for one 86 px tab (a gap before "+", measured live); the
        # ClipRow already cuts an overlong row, so neither is needed.
        self.tabbar.setUsesScrollButtons(False)
        self.tabbar.setElideMode(QtCore.Qt.ElideNone)
        self.tabbar.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        h.addWidget(self.tabbar)
        self.add_tab_btn = QtWidgets.QToolButton()
        self.add_tab_btn.setObjectName("nodexAddTab")
        # Same box as a tab (the tabbar measures 23 px live, 4 px top margin in the QSS), so the
        # tops and bottoms line up; the tabbar has no tabs yet to ask here.
        self.add_tab_btn.setFixedHeight(23)
        self.add_tab_btn.setText("+")
        self.add_tab_btn.setAutoRaise(True)
        self.add_tab_btn.setToolTip("New tab")
        h.addWidget(self.add_tab_btn)
        h.addStretch(1)
        # Kept, but out of the tab strip, at its far right.
        self.recent_btn = QtWidgets.QToolButton()
        self.recent_btn.setText("Recently closed")
        self.recent_btn.setAutoRaise(True)
        self.recent_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.recent_menu = QtWidgets.QMenu(self.recent_btn)
        self.recent_btn.setMenu(self.recent_menu)
        h.addWidget(self.recent_btn)
        for w in (self.tabbar, self.add_tab_btn, self.recent_btn):
            h.setAlignment(w, QtCore.Qt.AlignBottom)
        lay.addWidget(ClipRow(row, 26))

    def _build_status(self, lay):
        row = QtWidgets.QWidget()
        row.setFixedHeight(24)
        h = QtWidgets.QHBoxLayout(row)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(16)
        self.counts = QtWidgets.QLabel()
        h.addWidget(self.counts)
        legend = []
        for cls, label in (("Numeric", "double"), ("ThreeDNumericVector", "double3"),
                           ("Rotation", "rotation"), ("Matrix", "matrix"), ("Boolean", "bool"),
                           ("MultiAmbiguous", "message")):
            legend.append('<span style="color:%s">&#9679;</span> %s' % (theme.attr_color(cls), label))
        legend.append('<span style="color:%s">&#8250;&#8250;</span> unit conversion' % theme.attr_color("UnitConversion"))
        lg = QtWidgets.QLabel("&nbsp;&nbsp;".join(legend))
        lg.setStyleSheet("color:%s" % theme.CHROME["muted"])
        h.addWidget(lg)
        self.message = QtWidgets.QLabel()
        self.message.setStyleSheet("color:%s" % theme.CHROME["faint"])
        h.addWidget(self.message, 1)
        self.zoom_label = QtWidgets.QLabel("100%")
        h.addWidget(self.zoom_label)
        lay.addWidget(ClipRow(row, 24))

    def _build_menus(self):
        br = self.bridge
        # Menus filled on aboutToShow are built in Python and kept on self: the wrapper that
        # QMenuBar.addMenu(str) returned went invalid in Maya (C++ alive, PySide said deleted),
        # so the slot raised and Edit / Presets opened empty.
        self.edit_menu = self._menu(self.menubar, "Edit")
        self.edit_menu.aboutToShow.connect(self._fill_edit)
        m = self.menubar.addMenu("View")
        m.addAction("Frame selected\tF", lambda: self.root().frame(False))
        m.addAction("Frame all\tA", lambda: self.root().frame(True))
        m.addSeparator()
        for mode, key in (("simple", "1"), ("connected", "2"), ("full", "3"), ("custom", "4")):
            m.addAction("%s mode\t%s" % (mode.capitalize(), key), lambda mo=mode: br.setBoardMode(mo))
        m.addSeparator()
        wm = m.addMenu("Wires")
        self.links_actions = {}
        grp = QActionGroup(self)
        for mode, label in (("auto", "Auto (node links above 1200 connections)"),
                            ("off", "Every connection"), ("on", "Node links\tW")):
            a = wm.addAction(label, lambda mo=mode: br.setLinks(mo))
            a.setCheckable(True)
            grp.addAction(a)
            self.links_actions[mode] = a
        self.menubar.addMenu("Bookmarks").addAction("Bookmark view", br.add_bookmark)
        m = self.menubar.addMenu("Tabs")
        m.addAction("New tab", br.new_tab)
        m.addAction("Close tab", lambda: br.close_tab(self.tabbar.currentIndex()))
        m.addAction("Rename tab...", self._rename_tab)
        m = self.menubar.addMenu("Graph")
        m.addAction("Input connections", lambda: br.graphConnections("up"))
        m.addAction("Input and output connections", lambda: br.graphConnections("both"))
        m.addAction("Output connections", lambda: br.graphConnections("down"))
        m.addSeparator()
        m.addAction("Add selected", br.addSelected)
        m.addAction("Remove selected", br.removeSelected)
        m.addAction("Clear graph", br.clearGraph)
        m.addAction("Rearrange", lambda: br.arrange("layered"))
        self.arrange_menu = self._menu(m, "Arrange")
        self.arrange_menu.aboutToShow.connect(
            lambda: (self.arrange_menu.clear(), br.fill_arrange_menu(self.arrange_menu)))
        self.presets_menu = self._menu(self.menubar, "Presets")
        self.presets_menu.aboutToShow.connect(lambda: br.fill_presets_menu(self.presets_menu))
        self.window_menu = m = self._menu(self.menubar, "Window")
        for label, command in (("Maya Node Editor", "NodeEditorWindow"),
                               ("Outliner", "OutlinerWindow"),
                               ("Attribute Editor", "AttributeEditor"),
                               ("Hypershade", "HypershadeWindow"),
                               ("Connection Editor", "ConnectionEditor"),
                               ("Script Editor", "ScriptEditor")):
            m.addAction(label, lambda c=command: _run_mel(c))
        m = self.menubar.addMenu("Options")
        self.sync_action = m.addAction("Sync with scene")
        self.sync_action.setCheckable(True)
        self.sync_action.setChecked(True)
        self.sync_action.toggled.connect(lambda on: self.buttons["sync"].setChecked(on))
        m.addAction("Node limit...", self._ask_node_limit)
        bulk = m.addAction("Bulk connect from selection")
        bulk.setCheckable(True)
        bulk.setChecked(True)
        bulk.setToolTip("A wire dragged between selected nodes repeats for every selected pair with "
                        "similar names; into a selected node, for every selected node of its type")
        bulk.toggled.connect(lambda on: setattr(br, "bulk", on))
        m.setToolTipsVisible(True)
        m = self.menubar.addMenu("Help")
        m.addAction("Keys...", self._show_help)

    def _menu(self, owner, title):
        menu = QtWidgets.QMenu(title, owner)
        owner.addMenu(menu)
        return menu

    def _fill_edit(self):
        menu = self.edit_menu
        menu.clear()
        n = len([u for u in self.bridge.sel if u in self.bridge.infos])
        menu.addAction("Frame selected nodes	Ctrl+J" if n else "Add frame	Ctrl+J",
                       self.bridge.addFrame).setEnabled(not self.bridge.locked)
        menu.addSeparator()
        self.bridge.fill_edit_menu(menu)

    # ------------------------------------------------------------------ wiring

    def root(self):
        return self.quick.rootObject()

    def _connect(self):
        br, b = self.bridge, self.buttons
        br.tabsChanged.connect(self._refresh_tabs)
        br.statusChanged.connect(self.message.setText)
        br.countsChanged.connect(lambda n, w: self.counts.setText(
            "%d / %d nodes \u00b7 %d connection%s" % (n, br.max_nodes, w, "" if w == 1 else "s")))
        br.zoomChanged.connect(lambda z: self.zoom_label.setText("%d%%" % round(z * 100)))
        br.modeChanged.connect(self._mode_changed)
        br.createRequested.connect(self._open_create)
        self.tabbar.currentChanged.connect(self._tab_changed)
        self.tabbar.tabCloseRequested.connect(lambda i: br.close_tab(i))
        self.tabbar.tabBarDoubleClicked.connect(lambda i: self._rename_tab(i))
        self.add_tab_btn.clicked.connect(br.new_tab)
        self.recent_menu.aboutToShow.connect(self._fill_recent)

        b["create"].clicked.connect(lambda: self._open_create(None, None))
        b["sync"].toggled.connect(self._sync_toggled)
        b["up"].clicked.connect(lambda: br.graphConnections("up"))
        b["updown"].clicked.connect(lambda: br.graphConnections("both"))
        b["down"].clicked.connect(lambda: br.graphConnections("down"))
        b["clear"].clicked.connect(br.clearGraph)
        b["add"].clicked.connect(br.addSelected)
        b["remove"].clicked.connect(br.removeSelected)
        b["arrange"].clicked.connect(lambda: br.arrange("layered"))
        # Arrow on the button: the other arrange variants (Blender / Node Wrangler references).
        am = QtWidgets.QMenu(b["arrange"])
        am.aboutToShow.connect(lambda: (am.clear(), br.fill_arrange_menu(am)))
        b["arrange"].setMenu(am)
        b["arrange"].setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        b["arrange"].setFixedSize(40, 26)
        for mode in ("simple", "connected", "full"):
            b[mode].clicked.connect(lambda _=False, mo=mode: br.setBoardMode(mo))
        b["custom"].clicked.connect(lambda: br.setBoardMode("custom"))
        b["filter"].toggled.connect(br.setAllFilters)
        b["bmAdd"].clicked.connect(br.add_bookmark)
        b["bmPrev"].clicked.connect(lambda: br.goto_bookmark(-1))
        b["bmNext"].clicked.connect(lambda: br.goto_bookmark(1))
        b["shAll"].clicked.connect(lambda: br.set_shapes("all"))
        b["shExc"].clicked.connect(lambda: br.set_shapes("except"))
        b["shNone"].clicked.connect(lambda: br.set_shapes("none"))
        b["lock"].toggled.connect(self._lock_toggled)
        b["dZero"].clicked.connect(lambda: self._set_depth(0))
        b["dLess"].clicked.connect(lambda: self._set_depth(None if br.depth is None else max(0, br.depth - 1), less=True))
        b["dMore"].clicked.connect(lambda: self._set_depth(None if br.depth is None else br.depth + 1))
        b["dInf"].clicked.connect(lambda: self._set_depth(None))
        self.depth_field.editingFinished.connect(self._depth_edited)
        b["links"].clicked.connect(lambda on: br.setLinks("on" if on else "off"))
        br.linksChanged.connect(self._links_changed)
        self._links_changed(br.links_on(), br.links_mode())
        b["grid"].toggled.connect(lambda on: self.root().setProperty("showGrid", on))
        b["snap"].toggled.connect(lambda on: self.root().setProperty("snap", on))
        # Dimming follows every key; revealing matched rows re-describes nodes, so it waits
        # for a pause in typing.
        self._find_timer = QtCore.QTimer(self)
        self._find_timer.setSingleShot(True)
        self._find_timer.setInterval(150)
        self._find_timer.timeout.connect(lambda: br.setQuery(self.find_field.text()))
        self.find_field.textChanged.connect(lambda t: self.root().setProperty("query", t.strip().lower()))
        self.find_field.textChanged.connect(lambda t: self._find_timer.start())
        self.find_field.returnPressed.connect(lambda: br.selectMatches(self.find_field.text()))

    def _links_changed(self, on, mode):
        self.buttons["links"].setChecked(on)
        self.links_actions[mode].setChecked(True)


    def _sync_toggled(self, on):
        self.buttons["sync"].setIcon(_icon("syncOn" if on else "syncOff"))
        self.sync_action.setChecked(on)
        self.bridge.set_sync(on)

    def _lock_toggled(self, on):
        self.buttons["lock"].setIcon(_icon("nodeGrapherLocked" if on else "nodeGrapherUnlocked"))
        self.bridge.locked = on

    def _ask_node_limit(self):
        n, ok = QtWidgets.QInputDialog.getInt(
            self, "Node limit", "Most nodes a tab takes from Graph, Add selected and scene sync:",
            self.bridge.max_nodes, 1, 100000, 50)
        if ok:
            self.bridge.set_max_nodes(n)
            self.bridge.status("Node limit is %d" % n)

    def _set_depth(self, d, less=False):
        if d is None and less:
            d = 5
        self.bridge.depth = d
        self.depth_field.setText("\u221e" if d is None else str(d))

    def _depth_edited(self):
        try:
            self._set_depth(max(0, int(self.depth_field.text())))
        except ValueError:
            self._set_depth(None)

    def _mode_changed(self, mode):
        key = mode if mode in self.buttons else "connected"
        self.buttons[key].setChecked(True)

    def _refresh_tabs(self):
        st = self.bridge.store
        self.tabbar.blockSignals(True)
        while self.tabbar.count():
            self.tabbar.removeTab(0)
        for t in st.tabs:
            self.tabbar.addTab(t["name"])
        self.tabbar.setCurrentIndex(st.active)
        self.tabbar.blockSignals(False)
        self.recent_btn.setEnabled(bool(st.recent))

    def _tab_changed(self, i):
        if i >= 0:
            self.bridge.set_active_tab(i)

    def _fill_recent(self):
        self.recent_menu.clear()
        for j, r in enumerate(self.bridge.store.recent):
            n = len(r["tab"].get("nodes", {}))
            self.recent_menu.addAction("%s  (%d node%s)" % (r["tab"]["name"], n, "" if n == 1 else "s"),
                                       lambda jj=j: self.bridge.restore_tab(jj))

    def _rename_tab(self, i=None):
        i = self.tabbar.currentIndex() if i is None or i < 0 else i
        # Inline editor on the tab itself: no modal dialog (modals hang the command port).
        edit = QtWidgets.QLineEdit(self.tabbar.tabText(i), self.tabbar)
        edit.setGeometry(self.tabbar.tabRect(i))
        edit.selectAll()
        edit.show()
        edit.setFocus()

        def done():
            self.bridge.rename_tab(i, edit.text())
            edit.deleteLater()
        edit.editingFinished.connect(done)

    def _show_help(self):
        box = getattr(self, "_help", None)
        if box is None:
            c = theme.CHROME
            box = QtWidgets.QTextBrowser(self)
            box.setWindowFlags(QtCore.Qt.Tool)
            box.setWindowTitle("NodeX keys")
            box.setStyleSheet("QTextBrowser { background: %s; border: none; padding: 10px; }"
                              % c["panelLo"])
            box.setHtml(keys.html(c))
            box.resize(620, 720)
            self._help = box
        box.show()
        box.raise_()

    # ------------------------------------------------------------------ create node (Tab)

    def _open_search(self, provider, on_pick, title="", hint="", at_cursor=True):
        """Bridge entry point: inbetween and link-drag searches open under the pointer."""
        pos = QtGui.QCursor.pos() if at_cursor else self.quick.mapToGlobal(
            QtCore.QPoint(max(0, self.quick.width() // 2 - 190), 20))
        self.palette.open(provider, on_pick, pos, title=title, hint=hint)

    def _open_create(self, x=None, y=None):
        if x is None:
            w = self.root().property("mouseWorld")
            x, y = (w.x(), w.y()) if w is not None else (0.0, 0.0)
            if self.bridge.cursor is None and not self.quick.underMouse():
                r = self.root()
                z = r.property("zoom") or 1.0
                x = (self.quick.width() / 2.0 - r.property("panX")) / z
                y = (self.quick.height() / 2.0 - r.property("panY")) / z
        self._create_pos = (x, y)
        self._open_search(self.bridge.create_rows, self._create_chosen, title="Create node",
                          hint="Enter create  \u00b7  type to search: name, initials (dm), aliases (add, blend)",
                          at_cursor=False)

    def _create_chosen(self, data, alt=False):
        try:
            if isinstance(data, str) and data.startswith("preset:"):
                self.bridge.insert_preset(data[7:], *self._create_pos)
            else:
                self.bridge.create_at(data, self._create_pos)
        except (RuntimeError, ValueError, OSError) as e:
            self.bridge.status(str(e).strip())
        self.quick.setFocus()

    # ------------------------------------------------------------------ keys

    def _typing(self):
        item = self.quick.quickWindow().activeFocusItem()
        name = item.metaObject().className() if item is not None else ""
        return "TextInput" in name or "TextEdit" in name

    def eventFilter(self, obj, ev):
        if obj is self.quick and ev.type() in (QtCore.QEvent.DragEnter, QtCore.QEvent.DragMove,
                                               QtCore.QEvent.Drop):
            return self._drag_event(ev)
        if obj is self.quick or obj is self.quick.quickWindow():
            t = ev.type()
            if t == QtCore.QEvent.ShortcutOverride:
                typing = self._typing()
                text_key = typing and ev.modifiers() & QtCore.Qt.ControlModifier and ev.key() in (
                    QtCore.Qt.Key_C, QtCore.Qt.Key_V, QtCore.Qt.Key_X, QtCore.Qt.Key_A,
                    QtCore.Qt.Key_Z, QtCore.Qt.Key_Y)
                if text_key or not typing and self.owns_key(ev.key(), ev.modifiers()):
                    ev.accept()
                    return True
            if t == QtCore.QEvent.KeyPress and ev.key() == QtCore.Qt.Key_Tab and not self._typing():
                w = self.root().property("mouseWorld")
                self._open_create(w.x(), w.y())
                return True
            if t == QtCore.QEvent.KeyPress and not self._typing() and self.owns_key(
                    ev.key(), ev.modifiers()) and ev.modifiers() == QtCore.Qt.ControlModifier:
                # QQuickWidget forwards the event into a second shortcut map. Consume graph
                # clipboard keys here so Maya's own Ctrl+C/V cannot run during that forward.
                if ev.key() == QtCore.Qt.Key_C:
                    self.bridge.copyFragment()
                elif ev.key() == QtCore.Qt.Key_J:
                    self.bridge.addFrame()
                else:
                    pos = self.root().property('mouseWorld')
                    self.bridge.pasteFragment(pos.x(), pos.y())
                ev.accept()
                return True
        return super(NodeXPanel, self).eventFilter(obj, ev)

    def _drag_event(self, ev):
        """Outliner -> board: the dropped nodes land where the mouse lets go."""
        mime = ev.mimeData()
        if not _is_maya_drag(mime):
            return False
        if ev.type() != QtCore.QEvent.Drop:
            ev.acceptProposedAction()
            return True
        names = dropped_names(mime)
        if not names:
            # Some Maya drags carry no readable names: they drag the current selection.
            import maya.cmds as cmds
            names = cmds.ls(selection=True, long=True) or []
        p = _event_pos(ev)
        r = self.root()
        if r is not None:      # Board.toWorld(), done here: QML functions are not Python methods
            z = r.property("zoom") or 1.0
            x, y = (p.x() - r.property("panX")) / z, (p.y() - r.property("panY")) / z
        else:
            x, y = 60.0, 60.0
        ev.acceptProposedAction()
        try:
            self.bridge.add_dropped(names, x, y)
        except Exception as e:
            self.bridge.status("Drop failed: %s" % str(e).strip())
        self.quick.setFocus()
        return True

    # ------------------------------------------------------------------ dock / undock

    def showEvent(self, ev):
        super(NodeXPanel, self).showEvent(ev)
        QtCore.QTimer.singleShot(0, self._check_host)

    def _check_host(self):
        """Undocking leaves the board in a floating window that paints solid white for good:
        measured live on a bare QQuickWidget test window (repaint, 1 px resize, hide/show,
        reparenting and even a brand-new QQuickWidget in that window all stayed white, a plain
        QWidget window never went white). A floating window created from scratch paints fine,
        so the panel rebuilds its control when it goes from docked to floating."""
        try:
            floating = self.window().metaObject().className() != "TmainWindow"
        except RuntimeError:
            return
        was_docked = getattr(self, "_docked", None)
        self._docked = not floating
        if was_docked and floating:
            self._refloat_when_dropped()

    def _refloat_when_dropped(self):
        # Rebuilding mid-drag tears the window away from the mouse: wait for the drop.
        if QtWidgets.QApplication.mouseButtons() != QtCore.Qt.NoButton:
            QtCore.QTimer.singleShot(100, self._refloat_when_dropped)
            return
        try:
            if self.window().metaObject().className() == "TmainWindow":
                return                    # dropped back into a dock: nothing to repair
            f, c = self.window().frameGeometry(), self.window().geometry()
        except RuntimeError:
            return
        QtCore.QTimer.singleShot(0, lambda: refloat(f.x(), f.y(), c.width(), c.height()))

    # ------------------------------------------------------------------ lifetime

    def shutdown(self):
        self.bridge.shutdown()
        self.palette.hide()
        self.quick.setSource(QtCore.QUrl())


# ====================================================================== Maya hosting

def _run_mel(command):
    import maya.mel as mel
    try:
        mel.eval(command)
    except RuntimeError as e:
        print("NodeX: %s failed: %s" % (command, e))


_panel = [None]


def instance():
    return _panel[0]


def _build_into_current():
    """uiScript of the workspaceControl: builds the panel into the control's layout."""
    import maya.OpenMayaUI as omui
    close(delete_control=False)
    ptr = omui.MQtUtil.getCurrentParent()
    parent = wrapInstance(int(ptr), QtWidgets.QWidget)
    panel = NodeXPanel(parent)
    parent.layout().addWidget(panel)
    _panel[0] = panel
    return panel


def _on_close():
    close(delete_control=False)


def show(width=1280, height=760):
    import maya.cmds as cmds
    if cmds.workspaceControl(CONTROL, exists=True):
        close(delete_control=True)
    cmds.workspaceControl(
        CONTROL, label="NodeX", retain=False, floating=True,
        initialWidth=width, initialHeight=height, widthProperty="free", heightProperty="free",
        uiScript="import nodex.panel; nodex.panel._build_into_current()",
        closeCommand="import nodex.panel; nodex.panel._on_close()")
    return _panel[0]


def refloat(x, y, w, h):
    """A fresh floating control where the undocked one is (see NodeXPanel._check_host). The
    board comes back from the store: close() saves it, the new panel loads it, view included."""
    p = show(w, h)
    if p is not None:
        p.window().setGeometry(p.window().geometry().translated(x - p.window().frameGeometry().x(),
                                                                y - p.window().frameGeometry().y()))
    return p


def close(delete_control=True):
    import maya.cmds as cmds
    p = _panel[0]
    _panel[0] = None
    if p is not None:
        try:
            p.shutdown()
        except Exception:
            pass
        try:
            p.setParent(None)
            p.deleteLater()
        except RuntimeError:
            pass
    # Anything an older copy of the module left behind.
    from . import sync
    sync.remove_stale()
    if delete_control and cmds.workspaceControl(CONTROL, exists=True):
        cmds.deleteUI(CONTROL)
