"""The mauTools window: tools grouped in tabs, each tab a column of
collapsible cards. Which card goes in which tab is decided by
MauToolsWindow.TABS; the colours live in STYLE / ACCENT.

Written for Qt 6. Maya 2026 ships PySide6, which is used when present;
PyQt6 is the fallback if it has been installed in mayapy.
"""
import getpass
import glob
import os
import re
import tempfile
import traceback

from maya import cmds, mel
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance, getCppPointer

    def _pointer(obj):
        return int(getCppPointer(obj)[0])
except ImportError:
    from PyQt6 import QtCore, QtGui, QtWidgets, sip
    wrapInstance = sip.wrapinstance

    def _pointer(obj):
        return int(sip.unwrapinstance(obj))

from . import __version__, selected, warn, undo_chunk
from . import naming, transforms, rigging, attributes, mesh, scene

Qt = QtCore.Qt
WINDOW_NAME = 'mauToolsWindow'
SYNC_MS = 400           # how often the Display card re-reads the viewport
_window = None


# ---------------------------------------------------------------------------
# look: one stylesheet for the whole window. Buttons and headers are matched
# through the "mau" property so the Maya shelf embedded in the window keeps
# its own look.
# ---------------------------------------------------------------------------
ACCENT = '#3fb8a0'
STYLE = '''
QWidget#mauToolsWindow, QDialog, QWidget[mau="page"] { background: #25272b; }
QScrollArea { background: transparent; border: none; }
QLabel { color: #c9cdd4; background: transparent; }
QLabel[mau="title"] { color: #f2f4f7; font-size: 15px; font-weight: bold; }
QLabel[mau="version"] { color: #7d838d; font-size: 10px; }
QLabel[mau="heading"] { color: ACCENT; font-size: 10px; font-weight: bold;
    padding-top: 7px; padding-bottom: 1px; }

QFrame[mau="card"] { background: #30333a; border: 1px solid #3b3f47;
    border-radius: 8px; }
QToolButton[mau="header"] { border: none; background: transparent;
    color: #eef0f3; font-weight: bold; font-size: 12px; padding: 7px 6px; }
QToolButton[mau="header"]:hover { color: ACCENT; }
QWidget[mau="well"] { background: #1f2125; border: 1px solid #3b3f47;
    border-radius: 6px; }

QPushButton[mau="btn"], QPushButton[mau="seg"] { background: #3d4149;
    color: #e6e8ec; border: 1px solid #4b5059; border-radius: 5px;
    padding: 4px 6px; min-height: 16px; }
QPushButton[mau="btn"]:hover, QPushButton[mau="seg"]:hover {
    background: #484d56; border-color: ACCENT; }
QPushButton[mau="btn"]:pressed, QPushButton[mau="btn"]:checked,
QPushButton[mau="seg"]:pressed, QPushButton[mau="seg"]:checked {
    background: ACCENT; border-color: ACCENT; color: #10201c; }
QPushButton[mau="btn"]:disabled, QPushButton[mau="seg"]:disabled {
    background: #33363c; border-color: #3b3f47; color: #6d727b; }
QPushButton[mau="seg"][pos="mid"] { border-radius: 0; }
QPushButton[mau="seg"][pos="first"] { border-top-right-radius: 0;
    border-bottom-right-radius: 0; }
QPushButton[mau="seg"][pos="last"] { border-top-left-radius: 0;
    border-bottom-left-radius: 0; }
QPushButton[mau="seg"][pos="mid"], QPushButton[mau="seg"][pos="last"] {
    border-left: none; }
QPushButton[mau="chip"] { background: #25272b; color: #8a909a;
    border: 1px solid #4b5059; border-radius: 11px; padding: 0;
    min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px;
    font-weight: bold; }
QPushButton[mau="chip"]:hover { border-color: ACCENT; }
QPushButton[mau="chip"]:checked { background: ACCENT; border-color: ACCENT;
    color: #10201c; }

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #1f2125;
    color: #e6e8ec; border: 1px solid #3f434b; border-radius: 5px;
    padding: 3px 6px; min-height: 16px;
    selection-background-color: ACCENT; selection-color: #10201c; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: ACCENT; }
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled,
QComboBox:disabled { background: #2a2c31; color: #646973; }
QLineEdit:read-only { color: #9aa0aa; }
QComboBox::drop-down { border: none; width: 18px; }
QComboBox::down-arrow { image: url(ICONS/down.png); width: 8px; height: 8px; }
QComboBox QAbstractItemView { background: #1f2125; color: #e6e8ec;
    border: 1px solid #3f434b; selection-background-color: ACCENT;
    selection-color: #10201c; outline: none; }
QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::down-button { border: none; width: 14px; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url(ICONS/up.png);
    width: 7px; height: 7px; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: url(ICONS/down.png); width: 7px; height: 7px; }

QCheckBox { color: #c9cdd4; spacing: 6px; background: transparent; }
QCheckBox:disabled { color: #646973; }
QCheckBox::indicator { width: 14px; height: 14px; border-radius: 4px;
    border: 1px solid #5a606a; background: #1f2125; }
QCheckBox::indicator:hover { border-color: ACCENT; }
QCheckBox::indicator:checked { background: ACCENT; border-color: ACCENT;
    image: url(ICONS/check.png); }
QCheckBox::indicator:disabled { border-color: #3f434b; background: #2a2c31; }

QListWidget, QTreeWidget { background: #1f2125; color: #e6e8ec;
    border: 1px solid #3f434b; border-radius: 6px; outline: none; }
QListWidget::item, QTreeWidget::item { padding: 2px 4px; }
QListWidget::item:selected, QTreeWidget::item:selected {
    background: ACCENT; color: #10201c; }
QHeaderView::section { background: #30333a; color: #9aa0aa; border: none;
    padding: 3px 6px; }

QTabWidget#mauToolsTabs::pane { border: none; }
QTabWidget#mauToolsTabs > QTabBar::tab { background: transparent;
    color: #8f95a0; font-weight: bold; padding: 6px 9px; border: none;
    border-bottom: 2px solid transparent; }
QTabWidget#mauToolsTabs > QTabBar::tab:hover { color: #e6e8ec; }
QTabWidget#mauToolsTabs > QTabBar::tab:selected { color: #ffffff;
    border-bottom: 2px solid ACCENT; }

QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #4b5059; border-radius: 4px;
    min-height: 24px; }
QScrollBar::handle:vertical:hover { background: ACCENT; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none; }
QMenu { background: #1f2125; color: #e6e8ec; border: 1px solid #3f434b; }
QMenu::item { padding: 3px 18px; }
QMenu::item:selected { background: ACCENT; color: #10201c; }
'''


def _icons():
    """Draw the tick and arrow images the stylesheet needs; returns their
    folder (with forward slashes, as stylesheets want)."""
    folder = os.path.join(tempfile.gettempdir(), 'mauTools_icons')
    os.makedirs(folder, exist_ok=True)
    shapes = {
        'check': ('#10201c', [(3.5, 8.5), (6.5, 11.5), (12.5, 4.5)]),
        'down': ('#9aa0aa', [(3.5, 6), (8, 10.5), (12.5, 6)]),
        'up': ('#9aa0aa', [(3.5, 10), (8, 5.5), (12.5, 10)]),
    }
    for name, (colour, points) in shapes.items():
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor(colour))
        pen.setWidthF(2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPolyline(
            QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in points]))
        painter.end()
        pixmap.save(os.path.join(folder, name + '.png'))
    return folder.replace('\\', '/')


def stylesheet():
    return STYLE.replace('ACCENT', ACCENT).replace('ICONS', _icons())


# ---------------------------------------------------------------------------
# small building blocks
# ---------------------------------------------------------------------------
def run(function, *args, **kwargs):
    """Call a tool as one undo step; errors go to the script editor."""
    try:
        with undo_chunk():
            return function(*args, **kwargs)
    except Exception as exc:
        traceback.print_exc()
        cmds.warning('mauTools: %s' % str(exc).strip())


def push(text, kind='btn', tip=''):
    """A styled push button that is not connected to anything yet."""
    widget = QtWidgets.QPushButton(text)
    widget.setProperty('mau', kind)
    widget.setToolTip(tip)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if kind != 'chip':
        widget.setMinimumWidth(24)      # lets the window get narrow
    return widget


def button(text, function, tip=''):
    widget = push(text, tip=tip)
    widget.clicked.connect(lambda *_: run(function))
    return widget


def is_chip(widget):
    return widget.property('mau') == 'chip'


def row(*items):
    """Horizontal layout; None is a stretch. Labels, check boxes and chips
    keep their size, everything else shares the width."""
    layout = QtWidgets.QHBoxLayout()
    layout.setSpacing(4)
    for item in items:
        if item is None:
            layout.addStretch(1)
        elif isinstance(item, QtWidgets.QLayout):
            layout.addLayout(item, 1)
        elif isinstance(item, (QtWidgets.QLabel, QtWidgets.QCheckBox)) \
                or is_chip(item):
            layout.addWidget(item)
        else:
            layout.addWidget(item, 1)
    return layout


def remember(widget):
    """Mark a widget whose value is written to the settings when the window
    closes and put back when it opens. Only widgets made by the helpers
    below are marked, so Maya's own widgets (the embedded shelf) and the
    per-object fields of the Rename Box are left alone."""
    widget.setProperty('mau_keep', True)
    return widget


def edit(placeholder='', tip=''):
    widget = QtWidgets.QLineEdit()
    widget.setPlaceholderText(placeholder)
    widget.setToolTip(tip)
    return remember(widget)


def label(text, kind=''):
    widget = QtWidgets.QLabel(text)
    if kind:
        widget.setProperty('mau', kind)
    return widget


def heading(text):
    return label(text.upper(), 'heading')


def check(text, state=False, tip=''):
    widget = QtWidgets.QCheckBox(text)
    widget.setChecked(state)
    widget.setToolTip(tip)
    return remember(widget)


def spin(value=0, low=0, high=9999, tip=''):
    widget = QtWidgets.QSpinBox()
    widget.setRange(low, high)
    widget.setValue(value)
    widget.setToolTip(tip)
    return remember(widget)


def fspin(value=0.0, low=-1e6, high=1e6, decimals=2, step=1.0, tip=''):
    widget = QtWidgets.QDoubleSpinBox()
    widget.setRange(low, high)
    widget.setDecimals(decimals)
    widget.setSingleStep(step)
    widget.setValue(value)
    widget.setToolTip(tip)
    return remember(widget)


def combo(items, current=0, tip=''):
    widget = QtWidgets.QComboBox()
    widget.addItems(list(items))
    widget.setCurrentIndex(current)
    widget.setToolTip(tip)
    return remember(widget)


def segments(buttons):
    """Join buttons into one rounded strip."""
    layout = QtWidgets.QHBoxLayout()
    layout.setSpacing(0)
    for index, widget in enumerate(buttons):
        widget.setProperty('mau', 'seg')
        widget.setProperty('pos', 'first' if index == 0 else
                           'last' if index == len(buttons) - 1 else 'mid')
        layout.addWidget(widget, 1)
    return layout


def radios(labels, current=0):
    """One-of-many choice drawn as a segmented strip.
    Returns (layout, QButtonGroup); group.checkedId() is the chosen index."""
    group = QtWidgets.QButtonGroup()
    buttons = []
    for index, text in enumerate(labels):
        widget = push(text)
        widget.setCheckable(True)
        widget.setChecked(index == current)
        group.addButton(widget, index)
        buttons.append(remember(widget))
    group.setParent(buttons[0])         # keeps the group alive
    return segments(buttons), group


def xyz(states=(True, True, True)):
    """Three round X / Y / Z toggles."""
    chips = []
    for axis, state in zip('XYZ', states):
        chip = push(axis, 'chip')
        chip.setCheckable(True)
        chip.setChecked(state)
        chips.append(remember(chip))
    return chips


def states(checks):
    return [c.isChecked() for c in checks]


class PresetEdit(QtWidgets.QLineEdit):
    """Line edit whose right-click menu inserts the naming presets."""

    def __init__(self, placeholder='', presets=naming.PRESETS):
        super(PresetEdit, self).__init__()
        self.setPlaceholderText(placeholder)
        self.presets = presets
        remember(self)

    def preset_menu(self):
        menu = QtWidgets.QMenu(self)
        menu.addAction('--- clear ---').triggered.connect(
            lambda *_: self.clear())
        for preset in sorted(self.presets):
            menu.addAction(preset).triggered.connect(
                lambda *_, p=preset: self.setText(p))
        return menu

    def contextMenuEvent(self, event):
        self.preset_menu().popup(event.globalPos())


def narrow(widget, width=60):
    widget.setMaximumWidth(width)
    return widget


def pick_button(edit, text='>>>', tip='Use the first selected object',
                after=None):
    """Button that writes the first selected object into a line edit."""
    def pick():
        sel = selected()
        if not sel:
            return warn('select something first.')
        edit.setText(sel[0])
        if after:
            after()
    return narrow(button(text, pick, tip))


def widget_value(widget):
    """What to store for a widget, or None if there is nothing to store."""
    if isinstance(widget, QtWidgets.QComboBox):
        return widget.currentText()      # by text: combos filled from the
    if isinstance(widget, QtWidgets.QLineEdit):   # scene change their order
        return None if widget.isReadOnly() else widget.text()
    if isinstance(widget, QtWidgets.QAbstractSpinBox):
        return widget.value()
    if isinstance(widget, QtWidgets.QAbstractButton) and widget.isCheckable():
        return widget.isChecked()
    return None


def apply_value(widget, value):
    """Put a stored value back. Anything that no longer fits is ignored."""
    if isinstance(widget, QtWidgets.QComboBox):
        index = widget.findText(str(value))
        if index >= 0:
            widget.setCurrentIndex(index)
        elif widget.isEditable():
            widget.setEditText(str(value))
    elif isinstance(widget, QtWidgets.QLineEdit):
        if not widget.isReadOnly():
            widget.setText(str(value))
    elif isinstance(widget, QtWidgets.QSpinBox):
        widget.setValue(int(float(value)))
    elif isinstance(widget, QtWidgets.QDoubleSpinBox):
        widget.setValue(float(value))
    elif isinstance(widget, QtWidgets.QAbstractButton):
        widget.setChecked(str(value).lower() in ('true', '1'))


class Section(QtWidgets.QFrame):
    """Collapsible card: click the header to open or close it."""
    FULL = 16777215                     # Qt's "no maximum" height

    def __init__(self, title, parent=None):
        super(Section, self).__init__(parent)
        self.title = title
        self.resized = None             # called whenever the height changes
        self.setObjectName('mauTools_' + re.sub(r'\W', '', title))
        self.setProperty('mau', 'card')
        self.header = QtWidgets.QToolButton()
        self.header.setProperty('mau', 'header')
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header.setArrowType(Qt.ArrowType.RightArrow)
        self.header.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                  QtWidgets.QSizePolicy.Policy.Fixed)
        self.body = QtWidgets.QWidget()
        self.body.setObjectName(self.objectName() + '_body')
        self.body.setVisible(False)
        self.form = QtWidgets.QVBoxLayout(self.body)
        self.form.setContentsMargins(9, 0, 9, 10)
        self.form.setSpacing(4)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)
        outer.addWidget(self.header)
        outer.addWidget(self.body)
        self.slide = QtCore.QPropertyAnimation(
            self.body, b'maximumHeight', self)
        self.slide.setDuration(140)
        self.slide.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self.slide.valueChanged.connect(lambda *_: self._changed())
        self.slide.finished.connect(self._settle)
        self.header.clicked.connect(
            lambda *_: self.set_open(self.header.isChecked(), True))

    def set_open(self, state, animate=False):
        self.header.setChecked(state)
        self.header.setArrowType(
            Qt.ArrowType.DownArrow if state else Qt.ArrowType.RightArrow)
        self.slide.stop()
        if not animate:
            self.body.setMaximumHeight(self.FULL)
            self.body.setVisible(state)
            self._changed()
            return
        if state:
            self.body.setMaximumHeight(0)
            self.body.setVisible(True)
            self.slide.setStartValue(0)
            self.slide.setEndValue(self.body.sizeHint().height())
        else:
            self.slide.setStartValue(self.body.height())
            self.slide.setEndValue(0)
        self.slide.start()

    def _settle(self):
        if not self.header.isChecked():
            self.body.setVisible(False)
        self.body.setMaximumHeight(self.FULL)
        self._changed()

    def _changed(self):
        if self.resized:
            self.resized()

    def is_open(self):
        return self.header.isChecked()

    def add(self, *items):
        """Add widgets / layouts, one per line; several items share a row."""
        for item in items:
            if isinstance(item, (list, tuple)):
                self.form.addLayout(row(*item))
            elif isinstance(item, QtWidgets.QLayout):
                self.form.addLayout(item)
            else:
                self.form.addWidget(item)

    def kept(self):
        """The widgets of this card whose value is remembered, in the order
        they were built."""
        return [w for w in self.body.findChildren(QtWidgets.QWidget)
                if w.property('mau_keep')]


# ---------------------------------------------------------------------------
# rename box
# ---------------------------------------------------------------------------
class RenameBox(QtWidgets.QDialog):
    """One name field per selected object; Enter renames."""

    def __init__(self, parent=None):
        super(RenameBox, self).__init__(parent)
        self.setWindowTitle('Rename Box')
        layout = QtWidgets.QVBoxLayout(self)
        for uuid in cmds.ls(selected(long=True), uuid=True) or []:
            edit = QtWidgets.QLineEdit(
                cmds.ls(uuid, long=True)[0].split('|')[-1])
            edit.editingFinished.connect(
                lambda e=edit, u=uuid: run(self.rename, e, u))
            layout.addWidget(edit)
        close = push('Close')
        close.clicked.connect(self.close)
        layout.addWidget(close)

    @staticmethod
    def rename(edit, uuid):
        path = cmds.ls(uuid, long=True)
        new = edit.text().strip()
        if path and new and new != path[0].split('|')[-1]:
            edit.setText(cmds.rename(path[0], new).split('|')[-1])


# ---------------------------------------------------------------------------
# shelf: a Maya shelf embedded in the window, with presets saved on disk
# ---------------------------------------------------------------------------
class ShelfPanel(QtWidgets.QWidget):
    SUFFIX = '_mauUtyShelf.mel'

    def __init__(self, parent=None):
        super(ShelfPanel, self).__init__(parent)
        self.setObjectName('mauToolsShelfPanel')
        self.tabs = None
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        self.holder = QtWidgets.QWidget()
        self.holder.setObjectName('mauToolsShelfHolder')
        self.holder.setProperty('mau', 'well')
        self.holder.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.holder.setMinimumHeight(110)
        holder_layout = QtWidgets.QVBoxLayout(self.holder)
        holder_layout.setObjectName('mauToolsShelfHolderLayout')
        holder_layout.setContentsMargins(2, 2, 2, 2)
        self.presets = QtWidgets.QListWidget()
        self.presets.setMaximumHeight(70)
        self.presets.setToolTip('Saved shelves, double-click to load')
        self.presets.itemDoubleClicked.connect(lambda *_: run(self.load))

        layout.addLayout(segments([
            button('<<', lambda: scene.step_main_shelf('first'),
                   'Maya shelf: first tab'),
            button('<', lambda: scene.step_main_shelf('previous'),
                   'Maya shelf: previous tab'),
            button('>', lambda: scene.step_main_shelf('next'),
                   'Maya shelf: next tab'),
            button('>>', lambda: scene.step_main_shelf('last'),
                   'Maya shelf: last tab')]))
        layout.addWidget(self.holder)
        layout.addLayout(row(
            button('Get', self.get_main,
                   'Copy the buttons of the current Maya shelf here'),
            button('Clear', self.clear, 'Remove every button'),
            button('Delete', self.delete, 'Delete the selected preset'),
            button('Save', self.save, 'Save this shelf as a preset')))
        layout.addWidget(self.presets)

    # -- maya side ---------------------------------------------------------
    def build(self):
        """Create the Maya shelf inside the Qt holder (needs the window to
        be parented to Maya already)."""
        try:
            cmds.setParent(omui.MQtUtil.fullName(
                _pointer(self.holder.layout())))
            self.tabs = cmds.shelfTabLayout(
                image='smallTrash.xpm', imageVisible=True,
                childResizable=True, height=110,
                changeCommand=lambda *_: self.refresh())
            for name in ('Primary', 'Secondary'):
                cmds.shelfLayout(name, parent=self.tabs, height=80)
            cmds.setParent('..')
        except Exception:
            traceback.print_exc()
            self.tabs = None
            self.holder.layout().addWidget(
                label('The Maya shelf could not be created.'))
        self.refresh()

    def active(self):
        return cmds.shelfTabLayout(self.tabs, q=True, selectTab=True)

    def shelf(self):
        return self.tabs + '|' + self.active()

    @staticmethod
    def user():
        return re.sub(r'\W', '_', os.environ.get('USER') or getpass.getuser())

    def files(self):
        folder = cmds.internalVar(userShelfDir=True)
        return sorted(glob.glob(os.path.join(
            folder, '*_%s%s' % (self.active(), self.SUFFIX))))

    def refresh(self):
        self.presets.clear()
        if not self.tabs:
            return
        prefix = self.user() + '_'
        ending = '_%s%s' % (self.active(), self.SUFFIX)
        for path in self.files():
            name = os.path.basename(path)[:-len(ending)]
            if name.startswith(prefix):
                name = name[len(prefix):]
            item = QtWidgets.QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.presets.addItem(item)

    def selected_file(self):
        item = self.presets.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else ''

    def clear(self):
        if not self.tabs:
            return
        shelf = self.shelf()
        for child in cmds.shelfLayout(shelf, q=True, childArray=True) or []:
            cmds.deleteUI(shelf + '|' + child)

    def get_main(self):
        if not self.tabs:
            return
        main = mel.eval('$mauToolsTmp = $gShelfTopLevel')
        current = cmds.shelfTabLayout(main, q=True, selectTab=True)
        self.clear()
        cmds.setParent(self.shelf())
        mel.eval('shelf_%s()' % current)

    def load(self):
        path = self.selected_file()
        if not self.tabs or not path:
            return
        with open(path) as handle:
            found = re.search(r'global\s+proc\s+(\w+)', handle.read())
        if not found:
            return warn('%s is not a shelf file.' % path)
        self.clear()
        cmds.setParent(self.shelf())
        mel.eval('source "%s"; %s();' % (
            path.replace('\\', '/'), found.group(1)))

    def save(self):
        if not self.tabs:
            return
        path = self.selected_file()
        if path:
            if cmds.confirmDialog(
                    title='Overwrite Shelf', button=['Overwrite', 'Cancel'],
                    message='Overwrite "%s" ?' % os.path.basename(path),
                    defaultButton='Cancel', cancelButton='Cancel',
                    dismissString='Cancel') != 'Overwrite':
                return
        else:
            if cmds.promptDialog(
                    title='Save Shelf', message='Shelf name:',
                    button=['OK', 'Cancel'], defaultButton='OK',
                    cancelButton='Cancel', dismissString='Cancel') != 'OK':
                return
            name = re.sub(r'\W', '_', cmds.promptDialog(q=True, text=True))
            if not name:
                return
            path = os.path.join(
                cmds.internalVar(userShelfDir=True), '%s_%s_%s%s' % (
                    self.user(), name, self.active(), self.SUFFIX))
        mel.eval('saveShelf "%s" "%s"' % (
            self.shelf(), path[:-len('.mel')].replace('\\', '/')))
        self.refresh()

    def delete(self):
        path = self.selected_file()
        if not path:
            return warn('pick the preset to delete in the list.')
        if cmds.confirmDialog(
                title='Delete Shelf', button=['Delete', 'Cancel'],
                message='Delete "%s" ?' % os.path.basename(path),
                defaultButton='Cancel', cancelButton='Cancel',
                dismissString='Cancel') != 'Delete':
            return
        os.remove(path)
        self.refresh()


# ---------------------------------------------------------------------------
# the window
# ---------------------------------------------------------------------------
class MauToolsWindow(QtWidgets.QWidget):
    # tab title, the sections it holds (top to bottom). Move a name to
    # another line to regroup the window.
    TABS = (
        ('Basic', ('shelf_section', 'rename_section', 'scene_section')),
        ('Xform', ('transform_section', 'attribute_section')),
        ('Rig', ('joint_section', 'rivet_section', 'node_section')),
        ('Vtx Data', ('skin_section', 'vertex_data_section',
                      'proxy_section')),
        ('Pick', ('picker_section', 'selection_section')),
        ('Display', ('display_section',)),
    )

    def __init__(self, parent=None):
        super(MauToolsWindow, self).__init__(parent)
        self.setObjectName(WINDOW_NAME)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle('mauTools v' + __version__)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.settings = QtCore.QSettings('mauTools', 'mauTools')
        self.sections = []
        self.show_timer = QtCore.QTimer(self)
        self.show_timer.setInterval(SYNC_MS)
        self.show_timer.timeout.connect(self.refresh_show)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setObjectName('mauToolsMainLayout')
        outer.setContentsMargins(8, 8, 8, 6)
        outer.setSpacing(6)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet(stylesheet())

        outer.addLayout(row(label('mauTools', 'title'),
                            label('v' + __version__, 'version'), None))
        outer.addLayout(segments([
            button(text, lambda n=name: scene.menu_set(n),
                   'Switch Maya to the %s menu set' % text)
            for text, name in scene.MENU_SETS]))

        self.shelf_panel = ShelfPanel()
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setObjectName('mauToolsTabs')
        self.tabs.setUsesScrollButtons(True)
        outer.addWidget(self.tabs, 1)
        for index, (title, builders) in enumerate(self.TABS):
            scroll = QtWidgets.QScrollArea()
            scroll.setObjectName('mauToolsScroll%d' % index)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            content = QtWidgets.QWidget()
            content.setObjectName('mauToolsContent%d' % index)
            content.setProperty('mau', 'page')
            content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
            column = QtWidgets.QVBoxLayout(content)
            column.setContentsMargins(0, 6, 6, 0)
            column.setSpacing(6)
            for position, name in enumerate(builders):
                section = getattr(self, name)()
                section.open_by_default = position == 0
                section.resized = self.fit
                section.page = scroll
                self.sections.append(section)
                column.addWidget(section)
            column.addStretch(1)       # only shows if the user stretches
            scroll.setWidget(content)
            self.tabs.addTab(scroll, title)

        self.restore_state()
        self.shelf_panel.build()
        self.refresh_show()
        self.tabs.currentChanged.connect(lambda *_: self.fit())
        application = QtWidgets.QApplication.instance()
        if application:         # Qt drops this when the window is destroyed
            application.aboutToQuit.connect(self.save_state)

    # -- window size -------------------------------------------------------
    def fit(self):
        """Make the window exactly as tall as the current tab with its open
        cards. If that is taller than the screen the tab scrolls instead."""
        page = self.tabs.currentWidget()
        if not self.isVisible() or page is None:
            return
        self.layout().activate()
        chrome = self.height() - page.viewport().height()
        height = chrome + page.widget().sizeHint().height()
        screen = self.screen().availableGeometry().height() - 60
        self.resize(self.width(), min(height, screen))
        self.update_show_watch()

    def showEvent(self, event):
        super(MauToolsWindow, self).showEvent(event)
        QtCore.QTimer.singleShot(0, self.fit)

    def hideEvent(self, event):
        self.show_timer.stop()
        self.save_state()
        super(MauToolsWindow, self).hideEvent(event)

    # -- window state ------------------------------------------------------
    def restore_state(self):
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)      # position and width;
        else:                                   # fit() sets the height
            self.resize(420, 400)
        try:
            self.tabs.setCurrentIndex(int(self.settings.value('tab', 0)))
        except (TypeError, ValueError):
            pass
        for section in self.sections:
            value = self.settings.value('open/' + section.title,
                                        section.open_by_default)
            section.set_open(str(value).lower() in ('true', '1'))
        self.restore_values()

    def restore_values(self):
        """Put back every field, pull-down, spin box and tick box."""
        for section in self.sections:
            widgets = section.kept()
            key = 'state/' + section.title
            if self.settings.value(key + '/layout') != self.signature(widgets):
                continue        # the card was rebuilt: the old values would
            for index, widget in enumerate(widgets):    # land in the wrong
                value = self.settings.value('%s/%d' % (key, index))   # places
                if value is not None:
                    try:
                        apply_value(widget, value)
                    except (TypeError, ValueError):
                        pass

    def save_values(self):
        for section in self.sections:
            widgets = section.kept()
            key = 'state/' + section.title
            self.settings.setValue(key + '/layout', self.signature(widgets))
            for index, widget in enumerate(widgets):
                value = widget_value(widget)
                if value is not None:
                    self.settings.setValue('%s/%d' % (key, index), value)

    @staticmethod
    def signature(widgets):
        """Fingerprint of a card's widgets, so values saved by an older
        version of mauTools are dropped instead of misapplied."""
        return ','.join(type(w).__name__ for w in widgets)

    def save_state(self):
        try:
            self.settings.setValue('geometry', self.saveGeometry())
            self.settings.setValue('tab', self.tabs.currentIndex())
            for section in self.sections:
                self.settings.setValue('open/' + section.title,
                                       section.is_open())
            self.save_values()
            self.settings.sync()
        except RuntimeError:        # the window is already gone
            pass

    def closeEvent(self, event):
        self.show_timer.stop()
        self.save_state()
        super(MauToolsWindow, self).closeEvent(event)

    # -- shelf -------------------------------------------------------------
    def shelf_section(self):
        section = Section('Shelf')
        section.add(self.shelf_panel)
        return section

    # -- rename ------------------------------------------------------------
    def rename_section(self):
        section = Section('Rename')
        scope = combo(('Selection', 'Hierarchy', 'Everything'),
                      tip='Which nodes get renamed')

        def flags():
            return {'hierarchy': scope.currentIndex() == 1,
                    'everything': scope.currentIndex() == 2}

        text = PresetEdit('text (right-click for presets)')
        where_row, where = radios(('Prefix', 'Suffix'))
        search = PresetEdit('search for')
        replace = PresetEdit('replace with')
        mode = combo(('All', 'First', 'Last'), tip='Which match to replace')
        base = PresetEdit('base name')
        start = spin(1, 0, 99999)
        padding = spin(2, 1, 10)

        def reset():
            for edit in (text, search, replace, base):
                edit.clear()
            scope.setCurrentIndex(0)
            where.button(0).setChecked(True)
            mode.setCurrentIndex(0)
            start.setValue(1)
            padding.setValue(2)

        get_base = narrow(button(
            '>>>', lambda: base.setText(naming.base_name()),
            'Base name from the first selected object'))
        section.add(
            (label('Rename'), scope),
            heading('Add / Remove'), text, where_row,
            (button('Add', lambda: naming.add(
                text.text(), where.checkedId() == 1, **flags())),
             button('Remove', lambda: naming.remove(
                 text.text(), where.checkedId() == 1, **flags()),
                 'Prefix removes the first match, Suffix the last one')),
            heading('Replace'), search, replace,
            (mode, button('Replace', lambda: naming.replace(
                search.text(), replace.text(),
                mode.currentText().lower(), **flags()))),
            heading('Renumber'), (get_base, base),
            (label('Start'), start, label('Padding'), padding),
            button('Renumber', lambda: naming.renumber(
                base.text(), start.value(), padding.value(),
                scope.currentIndex() == 1)),
            heading('More'),
            (button('Rename Box', lambda: RenameBox(self).show(),
                    'One name field per selected object'),
             button('Reset', reset, 'Clear every rename field')))
        return section

    # -- transform ---------------------------------------------------------
    def transform_section(self):
        section = Section('Transform')
        to_first = check('Match to first selected', False,
                         'Off: like Maya, everything goes to the last '
                         'selected.\nOn: everything goes to the first.')
        t, r, s = xyz(), xyz(), xyz()

        def match(*groups):
            flags = {'to_first': to_first.isChecked()}
            for name, checks in (('translate', t), ('rotate', r),
                                 ('scale', s)):
                if name in groups:
                    flags[name] = states(checks)
            transforms.match(**flags)

        section.add(
            heading('Match'), to_first,
            [button('Translate', lambda: match('translate'))] + t,
            [button('Rotate', lambda: match('rotate'))] + r,
            [button('Scale', lambda: match('scale'))] + s,
            (button('All', lambda: match('translate', 'rotate', 'scale')),
             button('Centroid', transforms.centroid,
                    'Locator at the centre of the selected points / objects'),
             button('Average', transforms.average_locator,
                    'Locator at the average position and rotation')))

        space_row, space = radios(('Local', 'World'))
        turn = xyz((False, True, False))
        angle = fspin(90, -360, 360, 1, 5)
        section.add(
            heading('Rotate by steps'), space_row,
            turn + [label('Angle'), angle],
            (button('<---', lambda: transforms.rotate_step(
                -angle.value(), states(turn), space.checkedId() == 1)),
             button('--->', lambda: transforms.rotate_step(
                 angle.value(), states(turn), space.checkedId() == 1))))

        axis_row, axis = radios(('X', 'Y', 'Z'))
        flip_t = check('Translate', True)
        flip_r = check('Rotate', True)
        plane = push('Ref Plane',
                     tip='Show a template plane on the mirror plane')
        plane.setCheckable(True)
        plane.toggled.connect(lambda *_: run(
            transforms.reference_plane, axis.checkedId(),
            plane.isChecked()))
        section.add(
            heading('Flip'), axis_row, (flip_t, flip_r, None),
            (button('Flip it', lambda: transforms.mirror(
                axis.checkedId(), flip_t.isChecked(), flip_r.isChecked()),
                'One object: mirror onto a new locator.\n'
                'Even selection: first half onto second half.'),
             plane))

        anim_row, anim_space = radios(('Local', 'World'))
        use_offset = check('Offset')
        offset = fspin(0, -1e5, 1e5, 1)
        offset.setEnabled(False)
        use_offset.toggled.connect(offset.setEnabled)
        simplify = check('Simplify', False, 'Simplify the copied curves')
        section.add(
            heading('Animation'), anim_row,
            (use_offset, offset, simplify),
            (button('Transfer Anim', lambda: transforms.transfer_anim(
                anim_space.checkedId() == 1,
                offset.value() if use_offset.isChecked() else 0.0,
                simplify.isChecked()),
                'Copy animation from the first selected to the second'),
             button('Motion Curve', transforms.motion_curve,
                    'Curve along the path of each selected object')),
            heading('World space'),
            (button('Store World', transforms.store_world,
                    'Store world transforms of the selection (temp file)'),
             button('Read World', transforms.restore_world,
                    'Apply the stored world transforms')),
            button('Matrix Constraint', transforms.matrix_constraint,
                   'Driver then driven: parent constraint made of '
                   'matrix nodes'))
        return section

    # -- joints and IK -----------------------------------------------------
    def joint_section(self):
        section = Section('Joints and IK')
        connect = check('Constrain', False,
                        'Also add the pole vector constraint')
        section.add(
            (button('Joint on Vtx', rigging.joints_on_vertices),
             button('HmNull', rigging.home_null,
                    'Locator above each selected node taking its transform'),
             button('Shape > Joints', rigging.shape_to_joints,
                    'Joints, then a curve: copy its shape on every joint')),
            (connect,
             button('Pole Vector',
                    lambda: rigging.pole_vector(connect.isChecked())),
             button('Stretchy', rigging.stretchy_ik,
                    'Make the selected IK handles stretchy')))

        mode = combo(('World Axis', 'Object Rotation'))
        order = combo(rigging.ORIENT_ORDERS, tip='Orient axes')
        second = combo(('+x', '-x', '+y', '-y', '+z', '-z', 'none'), 2,
                       'World direction of the second axis')
        children = check('Orient children', True)
        zero = check('Reorient local scale axes', True)
        target = edit('transform to orient like')
        get_target = pick_button(target)

        def switch(index):
            for widget in (order, second, children, zero):
                widget.setEnabled(index == 0)
            for widget in (target, get_target):
                widget.setEnabled(index == 1)

        def orient():
            if mode.currentIndex() == 1:
                return rigging.orient_joint_like(target.text())
            rigging.orient_joints(
                order.currentText(),
                rigging.SECONDARY_AXES[second.currentIndex()],
                children.isChecked(), zero.isChecked())

        mode.currentIndexChanged.connect(switch)
        switch(0)
        section.add(
            heading('Orient'), mode,
            (label('Axes'), order, label('Second'), second),
            children, zero, (get_target, target),
            button('Orient', orient))
        return section

    # -- rivets ------------------------------------------------------------
    def rivet_section(self):
        section = Section('Rivets and Follicles')
        pairs = check('Edge pairs', True,
                      'On: edges 1-2, 3-4 ...\nOff: edges 1-2, 2-3, 3-4 ...')
        use_input = check('Before deformers', False,
                          'Rivet on the mesh that feeds inMesh')
        section.add(
            (pairs, use_input, None),
            (button('Rivet', lambda: rigging.rivet(
                pairs.isChecked(), False, use_input.isChecked()),
                'Locator rivets between the selected edges'),
             button('Loft Follicle', lambda: rigging.rivet(
                 pairs.isChecked(), True),
                 'Follicles on a loft between the selected edges')),
            (button('Follicle', rigging.follicle,
                    'On the selected mesh faces (UVs) or surface points'),
             button('Follicle no UV', rigging.follicle_no_uv,
                    'On the selected mesh faces, without using UVs')),
            button('Reverse Follicle', rigging.reverse_follicle,
                   'Flip the selected loft follicles'))
        return section

    # -- nodes -------------------------------------------------------------
    def node_section(self):
        section = Section('Nodes')
        kind = combo(rigging.UTILITY_NODES)
        kind.setEditable(True)
        name = edit('node name (optional)')

        def create():
            rigging.create_node(kind.currentText(), name.text().strip())
            name.clear()

        section.add(
            kind, name, button('Create Node', create),
            button('Connection Editor', cmds.ConnectionEditor),
            (button('Lock Node', lambda: rigging.lock_nodes(True)),
             button('Unlock Node', lambda: rigging.lock_nodes(False))),
            button('Clean Unknown Nodes', rigging.clean_unknown_nodes))
        return section

    # -- attributes --------------------------------------------------------
    def attribute_section(self):
        section = Section('Attributes')
        name = edit('attribute name')
        kind = combo(attributes.TYPES)
        keyable = check('Keyable', True)
        visible = check('Channel box', False,
                        'Show a non-keyable attribute in the channel box')
        visible.setEnabled(False)
        keyable.toggled.connect(
            lambda *_: visible.setEnabled(not keyable.isChecked()))
        limits = check('Min / Max')
        low, high = fspin(0), fspin(1)
        enum = edit('enum names, comma separated')

        def switch(*_):
            numeric = kind.currentText() in ('float', 'int')
            limits.setEnabled(numeric)
            low.setEnabled(numeric and limits.isChecked())
            high.setEnabled(numeric and limits.isChecked())
            enum.setEnabled(kind.currentText() == 'enum')

        def add():
            use = limits.isChecked() and limits.isEnabled()
            attributes.add_attribute(
                name.text().strip(), kind.currentText(), keyable.isChecked(),
                visible.isChecked(), low.value() if use else None,
                high.value() if use else None,
                [n.strip() for n in enum.text().split(',') if n.strip()])

        kind.currentIndexChanged.connect(switch)
        limits.toggled.connect(switch)
        switch()
        section.add(
            heading('Create'), name, (label('Type'), kind),
            (keyable, visible, None), (limits, low, high), enum,
            (button('Add Attr', add),
             button('Remove Attr', lambda: attributes.remove_attribute(
                 name.text().strip()))))

        t, r, s = xyz(), xyz(), xyz()
        vis = check('Visibility')
        user = check('User attrs', False, 'Also lock user-defined attributes')

        def toggle_all(checks):
            state = not all(c.isChecked() for c in checks)
            for box in checks:
                box.setChecked(state)

        def lock_row(text, checks):
            toggle = push(text, tip='Tick / untick the three axes')
            toggle.clicked.connect(lambda *_: toggle_all(checks))
            return [toggle] + checks

        hierarchy = check('Hierarchy', True,
                          'Lock everything below the selection too')
        hide = check('Hide', False, 'Also hide the locked attributes')
        section.add(
            heading('Locking'),
            lock_row('Translate', t), lock_row('Rotate', r),
            lock_row('Scale', s), (vis, user, None),
            (button('Set Pref', lambda: attributes.set_lock_pref(
                states(t), states(r), states(s), vis.isChecked(),
                user.isChecked()),
                'Tag the selected transforms with what to lock'),
             button('Remove Pref', attributes.remove_lock_pref),
             button('From Scene', attributes.lock_pref_from_scene,
                    'Tag the hierarchy with what is locked right now')),
            (hierarchy, hide, None),
            (button('Lock', lambda: attributes.apply_lock(
                True, hide.isChecked(), hierarchy.isChecked())),
             button('Unlock', lambda: attributes.apply_lock(
                 False, False, hierarchy.isChecked()))),
            heading('Values'),
            (button('Store Attrs', attributes.store_attributes,
                    'Store keyable values of the selection (temp file)'),
             button('Read Attrs', attributes.restore_attributes,
                    'Apply the stored values')))
        return section

    # -- selection ---------------------------------------------------------
    def selection_section(self):
        section = Section('Selection')
        add = check('Add', False, 'Keep the current selection')
        first = check('1st letter', False,
                      'Only names starting with L or R')
        chars = spin(0, 0, 99, 'Characters to take from the name '
                               '(0 = whole name)')
        end = combo(('Tail', 'Head'), tip='Take them from the end or start')
        swap_from = PresetEdit('from')
        swap_to = PresetEdit('to')

        def take(edit):
            sel = selected()
            if not sel:
                return warn('select something first.')
            count = chars.value()
            name = sel[0]
            if count:
                name = name[:count] if end.currentIndex() else name[-count:]
            edit.setText(name)

        def exchange():
            a, b = swap_from.text(), swap_to.text()
            swap_from.setText(b)
            swap_to.setText(a)

        def small(text, function, tip):
            return narrow(button(text, function, tip), 40)

        axis = combo(('X', 'Y', 'Z'), tip='Mirror axis')
        section.add(
            (button('Invert L / R', lambda: scene.select_opposite(
                add.isChecked(), first.isChecked()),
                'Select the other side of the selection'), add, first),
            heading('Swap by name'),
            (label('Chars'), chars, end, None),
            (small('>>>', lambda: take(swap_from), 'From the selection'),
             swap_from,
             small('<>', exchange, 'Exchange the two fields'),
             swap_to,
             small('<<<', lambda: take(swap_to), 'From the selection')),
            button('Swap Sel', lambda: scene.swap_selection(
                swap_from.text(), swap_to.text())),
            heading('Components'),
            (button('Mirror', lambda: mesh.mirror_components(
                axis=axis.currentIndex()),
                'Select the mirrored components'), axis,
             button('Invert', mesh.invert_components,
                    'Invert the component selection')),
            heading('Store'),
            (button('Store Sel', scene.store_selection),
             button('Read Sel', scene.restore_selection)),
            (button('Print Python', lambda: scene.selection_as_text(True)),
             button('Print MEL', lambda: scene.selection_as_text(False))))

        return section

    def picker_section(self):
        section = Section('Picker')
        picker = QtWidgets.QListWidget()
        picker.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        picker.setMinimumHeight(150)

        def names():
            return [picker.item(i).text() for i in range(picker.count())]

        def pick_new():
            curves = []
            for node in selected():
                if cmds.listRelatives(node, shapes=True, type='nurbsCurve'):
                    curves.append(node)
                else:
                    warn('%s is not a curve, skipped.' % node)
            picker.clear()
            picker.addItems(curves)

        def pick_add():
            picker.addItems([n for n in selected() if n not in names()])

        def pick_clear():
            chosen = picker.selectedItems()
            if not chosen:
                return picker.clear()
            for item in chosen:
                picker.takeItem(picker.row(item))

        def pick_select():
            found = [i.text() for i in picker.selectedItems()
                     if cmds.objExists(i.text())]
            if found:
                cmds.select(found, r=True)

        picker.itemSelectionChanged.connect(lambda *_: run(pick_select))
        tip = label('Click an item to select it in the scene.')
        tip.setStyleSheet('color: #7d838d; font-size: 10px;')
        section.add(
            picker, tip,
            (button('New', pick_new,
                    'Replace the list with the selected curves'),
             button('Add', pick_add, 'Add the selection to the list'),
             button('Clear', pick_clear, 'Remove the highlighted items, '
                                         'or everything')))
        return section

    # -- skin --------------------------------------------------------------
    def skin_section(self):
        section = Section('Skin')
        mirror = check('Mirror L / R', False,
                       'Paste L_ influences from their R_ twin and back')
        section.add(
            heading('Copy / paste vertex weights'),
            (mirror, None),
            (button('Copy Vtx', mesh.copy_vertex_weights),
             button('Paste Vtx', lambda: mesh.paste_vertex_weights(
                 mirror.isChecked()))))

        joint1, joint2 = edit('joint one'), edit('joint two')
        weight1 = fspin(0.5, 0, 1, 4, 0.05)
        weight2 = fspin(0.5, 0, 1, 4, 0.05)

        def link(source, other):
            def update(value):
                other.blockSignals(True)
                other.setValue(1.0 - value)
                other.blockSignals(False)
            source.valueChanged.connect(update)

        def pick_joints():
            joints = selected(type='joint')
            if joints:
                joint1.setText(joints[0])
            if len(joints) > 1:
                joint2.setText(joints[1])

        def pick_second():
            joints = selected(type='joint')
            if joints:
                joint2.setText(joints[0])

        link(weight1, weight2)
        link(weight2, weight1)
        section.add(
            heading('Weight between two joints'),
            (button('Joint One', pick_joints,
                    'First selected joint (and the second, if any)'),
             button('Joint Two', pick_second)),
            (joint1, joint2), (weight1, weight2),
            button('Assign to selected vertices',
                   lambda: mesh.weights_between_joints(
                       joint1.text(), joint2.text(), weight1.value(),
                       weight2.value())))

        change = fspin(0, 0, 100, 2, 1, 'Weight change tolerance, percent')
        iterations = spin(2, 1, 100)
        radius = spin(1, 1, 50, 'Grow the selection this many times')
        section.add(
            heading('Average weights'),
            (label('Weight change'), change),
            (label('Iterations'), iterations), (label('Radius'), radius),
            button('Average Weights', lambda: mesh.average_weights(
                change.value(), iterations.value(), radius.value())))

        everything = check('Everything in the scene', False,
                           'Off: the selected joints')
        section.add(
            heading('Bind pose'), everything,
            (button('Set new bindPose',
                    lambda: mesh.set_bind_pose(everything.isChecked())),
             button('Reset bindPose',
                    lambda: mesh.reset_bind_pose(everything.isChecked()))))
        return section

    # -- vertex data -------------------------------------------------------
    def vertex_data_section(self):
        section = Section('Vertex Data')

        def node_field(maps=None):
            node = edit('deformer or nCloth node')

            def fill():
                if maps is not None:
                    maps.clear()
                    maps.addItems(mesh.map_attributes(node.text()))
            node.editingFinished.connect(fill)
            return node, fill

        def browse(edit, folder):
            found = cmds.fileDialog2(
                fileMode=3 if folder else 1, dialogStyle=2,
                fileFilter='Vertex data (*.vdt *.vd *.tmp);;All files (*.*)')
            if found:
                edit.setText(found[0])

        save_node, _ = node_field()
        save_dir = edit('folder (empty = temp file)')
        section.add(
            heading('Save'),
            (pick_button(save_node, 'Node'), save_node),
            (narrow(button('Folder', lambda: browse(save_dir, True),
                           'Browse for a folder')), save_dir),
            button('Save', lambda: mesh.save_maps(
                save_node.text(), save_dir.text())))

        load_node, _ = node_field()
        load_file = edit('file (empty = temp file)')
        section.add(
            heading('Load'),
            (pick_button(load_node, 'Node'), load_node),
            (narrow(button('File', lambda: browse(load_file, False),
                           'Browse for a file')), load_file),
            button('Load', lambda: mesh.load_maps(
                load_node.text(), load_file.text())))

        from_maps, to_maps = combo(()), combo(())
        from_node, fill_from = node_field(from_maps)
        to_node, fill_to = node_field(to_maps)
        inverted = check('Inverted', False, 'Copy 1 - weight')
        section.add(
            heading('Copy'),
            (pick_button(from_node, 'From', after=fill_from), from_node),
            from_maps,
            (pick_button(to_node, 'To', after=fill_to), to_node), to_maps,
            (inverted, button('Copy', lambda: mesh.copy_map(
                from_node.text(), from_maps.currentText(), to_node.text(),
                to_maps.currentText(), inverted.isChecked()))))

        mirror_from, _ = node_field()
        mirror_to, _ = node_field()
        mirror_to.setPlaceholderText('destination (empty = same node)')
        axis_row, axis = radios(('X', 'Y', 'Z'))
        section.add(
            heading('Mirror deformer weights'),
            (pick_button(mirror_from, 'From'), mirror_from),
            (pick_button(mirror_to, 'To'), mirror_to), axis_row,
            button('Mirror selected vertices', lambda: mesh.mirror_map(
                mirror_from.text(), mirror_to.text(), axis.checkedId())))
        return section

    # -- proxy -------------------------------------------------------------
    def proxy_section(self):
        section = Section('Proxy')
        top = edit('top node of the asset')
        suffix = combo(mesh.PROXY_SUFFIXES, 0, 'Meshes whose name contains '
                                               'this get a proxy')
        average = edit()
        average.setReadOnly(True)
        use_exclude = check('Exclude under')
        exclude = fspin(10, 0, 1e9, 2)
        exclude.setEnabled(False)
        use_exclude.toggled.connect(exclude.setEnabled)
        low, mid, high = spin(1, 1, 64), spin(2, 1, 64), spin(4, 1, 64)
        section.add(
            (pick_button(top, 'Source'), top, suffix),
            (button('Avg Vol', lambda: average.setText('%.3f' % (
                mesh.average_volume(top.text(), suffix.currentText()))),
                'Average bounding-box volume of the meshes'), average),
            (use_exclude, exclude),
            (label('Resolution'), low, mid, high),
            button('Make Proxy', lambda: mesh.make_proxy(
                top.text(), suffix.currentText(), low.value(), mid.value(),
                high.value(),
                exclude.value() if use_exclude.isChecked() else 0.0),
                'Shrink-wrapped cube for every mesh: small, average and '
                'big meshes use the three resolutions'))
        return section

    # -- display -----------------------------------------------------------
    def display_section(self):
        section = Section('Display')
        self.show_section = section
        self.show_sync = check(
            'Follow viewport', True,
            'While this card is open, keep the boxes in step with the '
            'active viewport, so changes made in Maya show up here')
        self.show_sync.toggled.connect(lambda *_: self.update_show_watch())
        section.add(
            (button('Template it', scene.toggle_template),
             button('Toggle Shape', scene.toggle_shape_visibility)),
            (button('Toggle xRay', scene.toggle_xray),
             button('Reset xRay', scene.reset_xray)),
            button('Toggle Isolate', lambda: scene.isolate('toggle')),
            (button('Add Isolate', lambda: scene.isolate('add')),
             button('Rem Isolate', lambda: scene.isolate('remove'))),
            heading('Show in viewport'),
            (self.show_sync,
             button('Refresh', self.refresh_show,
                    'Read the boxes from the active viewport now')),
            (button('All', lambda: self.show_all(True)),
             button('None', lambda: self.show_all(False))))
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(1)
        self.show_boxes = {}
        for index, (flag, text) in enumerate(scene.SHOW_FLAGS):
            box = check(text)
            box.clicked.connect(
                lambda *_, f=flag, b=box: run(
                    self.set_show, f, b.isChecked()))
            box.setProperty('mau_keep', False)   # the viewport decides
            self.show_boxes[flag] = box
            grid.addWidget(box, index // 2, index % 2)
        section.add(grid)
        return section

    def update_show_watch(self):
        """Start or stop the viewport poll. Maya sends no event when a
        modelEditor flag changes, so reading it every SYNC_MS while the
        Display card is on screen is how a change made in the viewport
        reaches the boxes."""
        section = getattr(self, 'show_section', None)
        wanted = bool(
            section is not None and self.isVisible()
            and self.show_sync.isChecked() and section.is_open()
            and self.tabs.currentWidget() is section.page)
        if wanted and not self.show_timer.isActive():
            self.refresh_show()
            self.show_timer.start()
        elif not wanted and self.show_timer.isActive():
            self.show_timer.stop()

    def refresh_show(self):
        """Read the active viewport into the boxes."""
        try:
            for flag, state in scene.show_states().items():
                box = self.show_boxes.get(flag)
                if box is not None and box.isChecked() != state:
                    # setChecked sends no clicked(), so this cannot loop back
                    box.setChecked(state)
        except Exception:
            self.show_timer.stop()      # rather than an error every tick
            traceback.print_exc()

    def set_show(self, flag, state):
        scene.set_show(flag, state)
        self.refresh_show()             # show what the viewport accepted

    def show_all(self, state):
        scene.set_show_all(state)
        for box in self.show_boxes.values():
            box.setChecked(state)
        self.refresh_show()

    # -- scene -------------------------------------------------------------
    def scene_section(self):
        section = Section('Scene')
        info = QtWidgets.QTreeWidget()
        info.setHeaderLabels(['Node type', 'Count'])
        info.setRootIsDecorated(False)
        info.setMaximumHeight(160)
        info.setToolTip('Double-click a row to select those nodes')

        def refresh():
            info.clear()
            for node_type, count in scene.scene_counts():
                QtWidgets.QTreeWidgetItem(info, [node_type, str(count)])
            info.resizeColumnToContents(0)

        def select_type(item=None, *_):
            if item is not None:
                cmds.select(cmds.ls(type=item.text(0)), r=True)

        info.itemDoubleClicked.connect(lambda *a: run(select_type, *a))
        section.add(
            button('New Version', scene.save_new_version,
                   'Save the scene under the next version number'),
            heading('Scene info'), info, button('Refresh', refresh))
        return section


# ---------------------------------------------------------------------------
def forget():
    """Clear everything mauTools remembers: window size and position, the
    tab, which cards are open and every field value. Takes effect the next
    time the window is opened."""
    QtCore.QSettings('mauTools', 'mauTools').clear()


def maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget) if pointer else None


def existing_windows():
    """Every mauTools window on screen, including one left behind by an
    earlier load of this module (found by object name, so a reload of the
    package still finds it)."""
    found = []
    application = QtWidgets.QApplication.instance()
    for widget in (application.topLevelWidgets() if application else []):
        try:
            if widget.objectName() == WINDOW_NAME:
                found.append(widget)
        except RuntimeError:        # the C++ side is already gone
            pass
    parent = maya_main_window()
    for widget in (parent.findChildren(QtWidgets.QWidget, WINDOW_NAME)
                   if parent else []):
        if widget not in found:
            found.append(widget)
    return found


def show():
    """Open the mauTools window, closing any window already open."""
    global _window
    for old in existing_windows():
        try:
            old.close()
        except RuntimeError:
            pass
    _window = MauToolsWindow(maya_main_window())
    _window.show()
    return _window
