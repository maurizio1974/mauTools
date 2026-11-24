# Recovered from D:/My Documents/maya/scripts\deformer_utils_ui.py (compiled 2022-03-06) by decompiling the Python 2.7 bytecode
# (uncompyle6, checked against the original bytecode), then ported to Python 3 /
# PySide6 for Maya 2025+. Changes from the original are marked "FIX".
import maya.cmds as cmds, maya.mel as mel, maya.OpenMayaUI as omui, maya.OpenMaya as om, maya.OpenMayaAnim as omAnim, time, maya.api.OpenMaya as om2, re, json
try:
    import weight_utils as wt_utils
    if not hasattr(wt_utils, 'get_shape_deformers'):
        # An older weight_utils was imported (an earlier copy on the path, or one still loaded
        # in this Maya session). Load it again from disk.
        import importlib
        wt_utils = importlib.reload(wt_utils)
        if not hasattr(wt_utils, 'get_shape_deformers'):
            cmds.warning('weight_utils is an old version, from {}. Replace it with the one that came with '
                         'deformer_utils_ui.py.'.format(wt_utils.__file__))
except Exception as _wt_error:
    cmds.warning('Could not import weight_utils: {}'.format(_wt_error))

try:
    # Maya 2025+ ships Qt6 / PySide6
    from PySide6.QtCore import *
    from PySide6.QtGui import *
    from PySide6.QtWidgets import *
    from PySide6 import __version__
    from shiboken6 import wrapInstance
except ImportError:
    try:
        from PySide2.QtCore import *
        from PySide2.QtGui import *
        from PySide2.QtWidgets import *
        from PySide2 import __version__
        from shiboken2 import wrapInstance
    except ImportError:
        from PySide.QtCore import *
        from PySide.QtGui import *
        from PySide import __version__
        from shiboken import wrapInstance


def _deformer_set_of(deformer_node):
    """The deformer's objectSet, or None (with a warning) for component-tag deformers (Maya 2022+)."""
    sets = [x for x in (cmds.listConnections(deformer_node + '.message') or []) if cmds.nodeType(x) == 'objectSet']
    if sets:
        return sets[0]
    cmds.warning('{} uses component tags and has no deformer set to edit'.format(deformer_node))
    return None


def _ls_type(node_type):
    """
    cmds.ls(type=...) without the "Unknown object type" warning when the node type's
    plug-in isn't loaded (multiTranslate, translateUVN, multiRotate, curveDeformer and
    repulsor come from separate custom plug-ins).
    """
    global _known_node_types
    try:
        _known_node_types
    except NameError:
        _known_node_types = set(cmds.allNodeTypes() or [])
    if node_type not in _known_node_types:
        _known_node_types = set(cmds.allNodeTypes() or [])   # a plug-in may have been loaded since
        if node_type not in _known_node_types:
            return []
    return cmds.ls(type=node_type) or []


def _eval_literal(text):
    """
    Python 3 replacement for the original ``exec('name = {}'.format(text))``.
    The text is a Python literal (a list or dict written with str()/repr()).
    """
    import ast
    if not isinstance(text, str):
        text = str(text)
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        # Strings stored by the Python 2 version can hold long literals like 12L.
        import re as _re
        return ast.literal_eval(_re.sub(r'(?<=\d)[lL]\b', '', text))


try:
    del deformer_ui
except:
    pass

color_vector_list = [
 (
  1, 1, 1),
 (
  1, 0, 0),
 (
  0, 0, 1),
 (
  0, 1, 0),
 (
  1, 1, 0),
 (
  0, 1, 1),
 (
  1, 0, 1),
 (
  1, 0.65, 0),
 (
  0.5, 0, 0.5),
 (
  0.5, 0.5, 1),
 (
  0.5, 1, 0.5),
 (
  1, 0.5, 0.5)]
primary_highlight_background_color = (
 1, 0.25, 0.25)
primary_highlight_text_color = (0, 0, 0)
secondary_highlight_background_color = (
 1, 0.5, 0.5)
secondary_highlight_text_color = (0, 0, 0)
weight_threshhold = 0.01

def get_true_sel(shape):
    sel = cmds.ls(sl=True, fl=True)
    true_sel = []
    shape_transform = cmds.listRelatives(shape, p=True)[0]
    if sel:
        for x in sel:
            if shape in x or shape_transform in x:
                if '.' in x:
                    true_sel.append(x)

    if true_sel == []:
        true_sel = None
    return true_sel


class _CollapsibleSection(QWidget):
    """
    A titled section that opens / closes when its header is clicked. Its open state is
    stored in a Maya optionVar, so it is remembered between sessions (default: closed).
    """

    OPTION_VAR = 'deformerUtilsUI_section_{}'

    def __init__(self, title, key, parent=None):
        super(_CollapsibleSection, self).__init__(parent)
        self._option_var = self.OPTION_VAR.format(key)
        self.header = QToolButton()
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.header.setStyleSheet('QToolButton { font-weight: bold; text-align: left; border: none; padding: 4px 2px; }')
        self.content = QFrame()
        self.content.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.content)
        self.header.toggled.connect(self._set_open)
        self.header.setChecked(self._load_state())
        self._set_open(self.header.isChecked(), save=False)

    def _load_state(self):
        try:
            if cmds.optionVar(exists=self._option_var):
                return bool(cmds.optionVar(q=self._option_var))
        except Exception:
            pass
        return False

    def _set_open(self, is_open, save=True):
        self.header.setArrowType(Qt.DownArrow if is_open else Qt.RightArrow)
        self.content.setVisible(is_open)
        if save:
            try:
                cmds.optionVar(iv=(self._option_var, int(bool(is_open))))
            except Exception:
                pass

    def is_open(self):
        return self.header.isChecked()


class _SectionList(QWidget):
    """One column of collapsible sections, with the free space at the bottom."""

    def __init__(self, parent=None):
        super(_SectionList, self).__init__(parent)
        self._groups = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        layout.addStretch(1)

    def add_group(self, section):
        self._groups.append(section)
        self.layout().insertWidget(self.layout().count() - 1, section)


class Communicate(QObject):
    mouseClicked = Signal()
    direction_updated = Signal()
    axis_updated = Signal()
    uv_axis_updated = Signal()
    curve_method_updated = Signal()
    surface_method_updated = Signal()
    load_matching_method_updated = Signal()
    match_method_updated = Signal()
    falloff_updated = Signal()
    coordinate_updated = Signal()


class deformer_treeWidget(QTreeWidget):

    def __init__(self, *args, **kwargs):
        super(deformer_treeWidget, self).__init__(*args, **kwargs)
        self.c = Communicate()
        self.header().hide()
        return

    def mouseMoveEvent(self, event):
        if not self.selectedItems():
            return
        else:
            dragged_item = self.selectedItems()[-1]
            mimeData_str = str([
             'deformer',
             dragged_item.node,
             None,
             None,
             None,
             None,
             None,
             None,
             dragged_item.shape,
             None])
            mimeData = QMimeData()
            mimeData.setText(mimeData_str)
            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.exec(Qt.CopyAction)
            self.c.mouseClicked.emit()
            return

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            super(deformer_treeWidget, self).mousePressEvent(event)
            self.c.mouseClicked.emit()
        return

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            super(deformer_treeWidget, self).mouseReleaseEvent(event)
            if self.selectedItems:
                self.c.mouseClicked.emit()
        return


class deformer_treeWidgetItem(QTreeWidgetItem):

    def __init__(self, *args, **kwargs):
        super(deformer_treeWidgetItem, self).__init__(*args, **kwargs)
        self.item_type = 'deformer'
        self.paintable = False
        self.custom = False
        return

    def get_weights(self, position_list=None):
        if self.plug:
            if not isinstance(self.plug, str):
                true_sel = get_true_sel(self.shape.split('|')[-1])
                return wt_utils.get_weightList_weights(self.node, self.shape, self.plug, position_list=position_list, component_list=true_sel)
            else:
                return

        else:
            true_sel = get_true_sel(self.shape.split('|')[-1])
            return wt_utils.get_deformer_weights(self.node, shape=self.shape, position_list=position_list, component_list=true_sel)
        return

    def set_weights(self, weights):
        if self.plug:
            if not isinstance(self.plug, str):
                true_sel = get_true_sel(self.shape.split('|')[-1])
                return wt_utils.set_weightList_weights(self.node, self.shape, self.plug, weights, component_list=true_sel, undoable=False)
            else:
                return

        return wt_utils.set_deformer_weights(self.node, weights, shape=self.shape, component_list=get_true_sel(self.shape), undoable=False)

    def get_deformerSet(self):
        return wt_utils.get_deformer_component_ids(self.node, self.shape)

    def set_deformerSet(self, deformerSet_ids):
        return wt_utils.set_deformer_components(self.node, self.shape, deformerSet_ids)

    def primary_highlight(self):
        self.setBackground(QColor(255 * primary_highlight_background_color[0], 255 * primary_highlight_background_color[1], 255 * primary_highlight_background_color[2], 255))
        self.setForeground(QColor(255 * primary_highlight_text_color[0], 255 * primary_highlight_text_color[1], 255 * primary_highlight_text_color[2], 255))
        return

    def highlight(self):
        self.setBackground(QColor(255 * secondary_highlight_background_color[0], 255 * secondary_highlight_background_color[1], 255 * secondary_highlight_background_color[2], 255))
        self.setForeground(QColor(255 * secondary_highlight_text_color[0], 255 * secondary_highlight_text_color[1], 255 * secondary_highlight_text_color[2], 255))
        return

    def unhighlight(self):
        self.setBackground(QColor(0, 0, 0, 0))
        self.setForeground(QColor(200, 200, 200, 255))
        return


class blendShape_treeWidget(QTreeWidget):

    def __init__(self, *args, **kwargs):
        super(blendShape_treeWidget, self).__init__(*args, **kwargs)
        self.c = Communicate()
        self.header().hide()
        return

    def mouseMoveEvent(self, event):
        if not self.selectedItems():
            return
        else:
            dragged_item = self.selectedItems()[-1]
            mimeData_str = str([
             dragged_item.item_type,
             dragged_item.node,
             dragged_item.target_name,
             dragged_item.inBetween_name,
             dragged_item.inBetween_weight,
             None,
             None,
             None,
             dragged_item.shape,
             None])
            mimeData = QMimeData()
            mimeData.setText(mimeData_str)
            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.exec(Qt.CopyAction)
            return

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            super(blendShape_treeWidget, self).mousePressEvent(event)
            self.c.mouseClicked.emit()
        return

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            super(blendShape_treeWidget, self).mouseReleaseEvent(event)
            if self.selectedItems:
                self.c.mouseClicked.emit()
        return


class blendShape_treeWidgetItem(QTreeWidgetItem):

    def __init__(self, *args, **kwargs):
        super(blendShape_treeWidgetItem, self).__init__(*args, **kwargs)
        self.item_type = 'blendShape'
        self.node = None
        self.target_name = None
        self.inBetween_name = None
        self.inBetween_weight = None
        self.shape = None
        return

    def get_deltas(self, position_list=None):
        if self.inBetween_name:
            return wt_utils.get_blendShape_target_deltas(self.node, self.target_name, inBetween_weight=self.inBetween_weight, position_list=position_list)
        else:
            if self.target_name:
                return wt_utils.get_blendShape_target_deltas(self.node, self.target_name)
            return

        return

    def set_deltas(self, deltas):
        if self.inBetween_name:
            wt_utils.set_blendShape_target_deltas(self.node, self.target_name, deltas, inBetween_weight=self.inBetween_weight, shape=self.shape)
        elif self.target_name:
            wt_utils.set_blendShape_target_deltas(self.node, self.target_name, deltas, shape=self.shape)
        return

    def get_weights(self, position_list=None):
        if self.inBetween_name:
            return
        else:
            if self.target_name:
                return wt_utils.get_blendShape_target_weights(self.node, self.target_name, position_list=position_list, shape=self.shape)
            return wt_utils.get_blendShape_base_weights(self.node, position_list=position_list, shape=self.shape)

        return

    def set_weights(self, weights):
        if self.inBetween_name:
            return
        if self.target_name:
            wt_utils.set_blendShape_target_weights(self.node, self.target_name, weights, shape=self.shape)
        else:
            wt_utils.set_blendShape_base_weights(self.node, weights, shape=self.shape)
        return

    def primary_highlight(self):
        self.setBackground(0, QColor(255 * primary_highlight_background_color[0], 255 * primary_highlight_background_color[1], 255 * primary_highlight_background_color[2], 255))
        self.setForeground(0, QColor(255 * primary_highlight_text_color[0], 255 * primary_highlight_text_color[1], 255 * primary_highlight_text_color[2], 255))
        return

    def highlight(self):
        self.setBackground(0, QColor(255 * secondary_highlight_background_color[0], 255 * secondary_highlight_background_color[1], 255 * secondary_highlight_background_color[2], 255))
        self.setForeground(0, QColor(255 * secondary_highlight_text_color[0], 255 * secondary_highlight_text_color[1], 255 * secondary_highlight_text_color[2], 255))
        return

    def unhighlight(self):
        self.setBackground(0, QColor(0, 0, 0, 0))
        self.setForeground(0, QColor(200, 200, 200, 255))
        return


class split_QTableWidget(QTableWidget):

    def __init__(self, *args, **kwargs):
        super(split_QTableWidget, self).__init__(*args, **kwargs)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setColumnCount(1)
        return

    def setRowColors(self):
        for i in range(self.rowCount()):
            row_color = color_vector_list[i]
            row_color = [128 * x for x in row_color]
            rowHeader = QTableWidgetItem(str(i))
            rowHeader.setBackground(QColor(*row_color))
            rowHeader.setTextAlignment(Qt.AlignCenter)
            self.setVerticalHeaderItem(i, rowHeader)

        return

    def empty(self):
        for row_num in range(self.rowCount()):
            for column_num in range(self.columnCount()):
                self.setItem(row_num, column_num, None)

        return

    def dragEnterEvent(self, event):
        event.setDropAction(Qt.CopyAction)
        if event.mimeData().hasText():
            info_list = event.mimeData().text()
            # FIX (Python 3): exec() can't assign function locals
            _info = _eval_literal(info_list)
            item_type = _info[0]
            target_name = _info[2]
            inBetween_name = _info[3]
            if self.drop_accept_type == 'weight':
                if item_type == 'deformer':
                    event.accept()
                    return
                if item_type == 'blendShape':
                    if not inBetween_name:
                        event.accept()
                        return
            elif self.drop_accept_type == 'delta':
                if item_type == 'blendShape':
                    if target_name:
                        event.accept()
                        return
        event.ignore()
        return

    def dropEvent(self, event):
        if event.mimeData().hasText():
            info_list = event.mimeData().text()
            # FIX (Python 3): exec() can't assign function locals
            item_type, node, target_name, inBetween_name, inBetween_weight, layer_name, layer_ID, influence_name, shape, arbitrary_attr = _eval_literal(info_list)
            dropped_item = split_QTableWidgetItem(item_type, node, target_name, inBetween_name, inBetween_weight, layer_name, layer_ID, influence_name, shape, arbitrary_attr)
            if self.drop_accept_type == 'weight':
                if item_type == 'deformer':
                    displayed_name = node
                    dropped_item.setText(displayed_name)
                if item_type == 'blendShape':
                    if inBetween_name:
                        return
                    if target_name:
                        displayed_name = ('{} | {}').format(node, target_name)
                        dropped_item.setText(displayed_name)
                    else:
                        dropped_item.setText(('{}').format(node))
                for column_num in range(self.columnCount() + 1):
                    for row_num in range(self.rowCount() + 1):
                        item = self.item(row_num, column_num)
                        if item:
                            if item.text() == displayed_name:
                                dropped_item.start_weights = item.start_weights

            if self.drop_accept_type == 'delta':
                if item_type == 'deformer':
                    return
                if item_type == 'blendShape':
                    if inBetween_name:
                        dropped_item.setText(('{} | {} | {}').format(node, target_name, inBetween_name))
                    elif target_name:
                        dropped_item.setText(('{} | {}').format(node, target_name))
                    else:
                        return
            pos = event.pos()
            row = self.rowAt(pos.y())
            column = self.columnAt(pos.x())
            self.setItem(row, column, dropped_item)
            event.accept()
            self.drop_update_function()
        else:
            event.ignore()
        return

    def dragMoveEvent(self, event):
        event.accept()
        return

    def mouseMoveEvent(self, event):
        if not self.selectedItems():
            return
        dragged_item = self.selectedItems()[-1]
        mimeData_str = str([
         dragged_item.item_type,
         dragged_item.node,
         dragged_item.target_name,
         dragged_item.inBetween_name,
         dragged_item.inBetween_weight,
         dragged_item.layer_name,
         dragged_item.layer_ID,
         dragged_item.influence_name,
         dragged_item.shape,
         dragged_item.plug])
        mimeData = QMimeData()
        mimeData.setText(mimeData_str)
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec(Qt.CopyAction)
        return


class split_QTableWidgetItem(QTableWidgetItem):

    def __init__(self, item_type, node, target_name, inBetween_name, inBetween_weight, layer_name, layer_ID, influence_name, shape, arbitrary_attr, *args, **kwargs):
        super(split_QTableWidgetItem, self).__init__(*args, **kwargs)
        self.item_type = item_type
        self.node = node
        self.target_name = target_name
        self.inBetween_name = inBetween_name
        self.inBetween_weight = inBetween_weight
        self.layer_name = layer_name
        self.layer_ID = layer_ID
        self.influence_name = influence_name
        self.shape = shape
        self.setFlags(self.flags() & ~Qt.ItemIsEditable)
        self.setFlags(self.flags() | Qt.ItemIsDragEnabled)
        self.start_weights = self.get_weights()
        self.start_deltas = self.get_deltas()
        return

    def get_weights(self, position_list=None):
        if self.item_type == 'deformer':
            return wt_utils.get_deformer_weights(self.node, self.shape)
        if self.item_type == 'blendShape':
            if self.inBetween_name:
                return
            else:
                if self.target_name:
                    return wt_utils.get_blendShape_target_weights(self.node, self.target_name)
                return wt_utils.get_blendShape_base_weights(self.node)

        return

    def set_weights(self, weights):
        if self.item_type == 'deformer':
            wt_utils.set_deformer_weights(self.node, weights, shape=self.shape)
        elif self.item_type == 'blendShape':
            if self.inBetween_name:
                return
            if self.target_name:
                wt_utils.set_blendShape_target_weights(self.node, self.target_name, weights)
            else:
                wt_utils.set_blendShape_base_weights(self.node, weights, shape=self.shape)
        return

    def get_deltas(self, position_list=None):
        if self.inBetween_name:
            return wt_utils.get_blendShape_target_deltas(self.node, self.target_name, inBetween_weight=self.inBetween_weight, position_list=position_list)
        else:
            if self.target_name:
                return wt_utils.get_blendShape_target_deltas(self.node, self.target_name, inBetween_weight=self.inBetween_weight, position_list=position_list)
            return

        return

    def set_deltas(self, deltas):
        if self.inBetween_name:
            wt_utils.set_blendShape_target_deltas(self.node, self.target_name, deltas, inBetween_weight=self.inBetween_weight)
        elif self.target_name:
            wt_utils.set_blendShape_target_deltas(self.node, self.target_name, deltas)
        return


class deformer_ui(QWidget):

    def __init__(self, *args, **kwargs):
        super(deformer_ui, self).__init__(*args, **kwargs)
        self.c = Communicate()
        self.shape = ''
        self.clipboard_weights = {}
        self.clipboard_deformerSet = []
        self.clipboard_shape = ''
        self.axis = 'x'
        self.uv_axis = 'u'
        self.side_index = 0
        self.direction = '+ to -'
        self.selected_wtHolder_list = []
        self.loaded_object = ''
        self.direction_short = 'p'
        self.load_matching_method = 'index'
        self.matching_method = 'closestComponent'
        self.curve_method = 'parameter'
        self.surface_method = 0
        self.display_selected_weights = True
        self.cancel_function = None
        self.idx = None
        self.showNonPaintable = False
        self.showCustomPaintable = True
        omui.MQtUtil.mainWindow()
        ptr = omui.MQtUtil.mainWindow()
        mainWindow_widget = wrapInstance(int(ptr), QWidget)
        self.mainWindow_widget = mainWindow_widget
        self.setParent(mainWindow_widget)
        self.setWindowFlags(Qt.Window)
        self.setObjectName('test')
        try:
            child_windows = mainWindow_widget.findChildren(QWidget)
            for widget in child_windows:
                if widget is not self:
                    if widget.objectName() == self.objectName():
                        widget.close()

        except:
            pass

        self.setWindowTitle('DEFORMER UTILS')
        # Bigger default size than the original 250 x 150, so the lists and options fit without resizing.
        self.setGeometry(50, 50, 760, 640)
        self.setMinimumSize(440, 320)

        def selectionChanged(*args, **kwargs):
            if cmds.objExists(self.shape):
                shape_transform = cmds.listRelatives(self.shape, p=True, f=True)[0]
                shape_transform_selected = shape_transform in cmds.ls(sl=True, l=True)
                shape_selected = cmds.ls(self.shape, l=True)[0] in cmds.ls(sl=True, l=True)
                if not shape_transform_selected and not shape_selected:
                    self.clear_weights()
                else:
                    self.update_displayed_weights()
            return

        self.initUI()
        return

    def changeEvent(self, event):
        try:
            self.update_deformer_treeWidget_display()
            self.update_blendShape_treeWidget_display()
        except:
            pass

        return

    def closeEvent(self, event):
        try:
            om.MMessage.removeCallback(self.idx)
        except:
            pass

        if self.cancel_function:
            try:
                self.cancel_function()
            except:
                pass

        self.clear_weights()
        return

    def initUI(self):
        self.window_layout = QVBoxLayout()
        self.window_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.window_layout)
        main_tabWidget = QTabWidget()
        self.window_layout.addWidget(main_tabWidget)
        self.primary_tab = QWidget()
        self.secondary_tab = QWidget()
        main_tabWidget.addTab(self.primary_tab, 'Main')
        main_tabWidget.addTab(self.secondary_tab, 'Options')
        self.primary_tab_layout = QVBoxLayout()
        self.primary_tab_layout.setContentsMargins(2, 2, 2, 2)
        self.primary_tab.setLayout(self.primary_tab_layout)
        self.secondary_tab_layout = QVBoxLayout()
        self.secondary_tab.setLayout(self.secondary_tab_layout)
        self.split_table_splitter = QSplitter()
        self.split_table_splitter.setOrientation(Qt.Vertical)
        self.split_table_splitter.setChildrenCollapsible(False)
        self.primary_tab_layout.addWidget(self.split_table_splitter)
        self.split_table_upper_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.split_table_upper_widget.setLayout(self.main_layout)
        self.split_table_splitter.addWidget(self.split_table_upper_widget)
        qFont_header = QFont()
        qFont_header.setPointSize(10)
        qFont_header.setBold(True)
        self.loadShape_layout = QHBoxLayout()
        self.main_layout.addLayout(self.loadShape_layout)
        self.load_shape_button = QPushButton('Shape >', self)
        self.load_shape_button.setMaximumSize(60, 28)
        self.load_shape_button.setMinimumSize(60, 28)
        self.load_shape_button.clicked.connect(self.load_shape_button_clicked)
        self.loadShape_layout.addWidget(self.load_shape_button)
        self.shape_name = QLineEdit(self)
        self.shape_name.setMaximumSize(10000, 30)
        self.shape_name.setMinimumSize(50, 30)
        self.shape_name.setReadOnly(True)
        self.loadShape_layout.addWidget(self.shape_name)
        self.all_list_splitter = QSplitter()
        self.main_layout.addWidget(self.all_list_splitter)
        self.deformer_list_widget = QWidget()
        self.deformer_list_layout = QVBoxLayout()
        self.deformer_list_layout.setContentsMargins(2, 2, 2, 2)
        self.deformer_list_widget.setLayout(self.deformer_list_layout)
        self.all_list_splitter.addWidget(self.deformer_list_widget)
        self.deformer_QLabel = QLabel('Deformers')
        self.deformer_QLabel.setAlignment(Qt.AlignCenter)
        self.deformer_QLabel.setFont(qFont_header)
        self.deformer_list_layout.addWidget(self.deformer_QLabel)
        self.deformer_name_search = QLineEdit(self)
        self.deformer_list_layout.addWidget(self.deformer_name_search)
        self.deformer_name_search.setMaximumSize(10000, 30)
        self.deformer_name_search.setMinimumSize(150, 30)
        self.deformer_name_search.textChanged.connect(self.update_deformer_treeWidget_display)
        self.deformer_name_search.returnPressed
        self.deformer_active_checkBox = QCheckBox()
        self.deformer_active_checkBox.setText('Show Only Active Deformers')
        self.deformer_list_layout.addWidget(self.deformer_active_checkBox)
        self.deformer_active_checkBox.stateChanged.connect(self.update_deformer_treeWidget_display)
        self.deformer_treeWidget = deformer_treeWidget()
        self.deformer_list_layout.addWidget(self.deformer_treeWidget)
        self.deformer_treeWidget.setDragEnabled(True)
        self.deformer_treeWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.deformer_treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.deformer_treeWidget.c.mouseClicked.connect(self.update_selected_deformer)
        self.deformer_treeWidget.customContextMenuRequested.connect(self.deformer_list_rightClicked)
        self.blendShape_list_widget = QWidget()
        self.blendShape_list_layout = QVBoxLayout()
        self.blendShape_list_layout.setContentsMargins(2, 2, 2, 2)
        self.blendShape_list_widget.setLayout(self.blendShape_list_layout)
        self.all_list_splitter.addWidget(self.blendShape_list_widget)
        self.blendShape_qLabel = QLabel('Blendshapes')
        self.blendShape_qLabel.setAlignment(Qt.AlignCenter)
        self.blendShape_qLabel.setFont(qFont_header)
        self.blendShape_list_layout.addWidget(self.blendShape_qLabel)
        self.blendShape_name_search = QLineEdit(self)
        self.blendShape_list_layout.addWidget(self.blendShape_name_search)
        self.blendShape_name_search.setMaximumSize(10000, 30)
        self.blendShape_name_search.setMinimumSize(0, 30)
        self.blendShape_name_search.textChanged.connect(self.update_blendShape_treeWidget_display)
        self.blendShape_active_checkBox = QCheckBox()
        self.blendShape_active_checkBox.setText('Show Only Active Targets')
        self.blendShape_list_layout.addWidget(self.blendShape_active_checkBox)
        self.blendShape_active_checkBox.stateChanged.connect(self.update_blendShape_treeWidget_display)
        self.blendShape_treeWidget = blendShape_treeWidget()
        self.blendShape_treeWidget.setDragEnabled(True)
        self.blendShape_list_layout.addWidget(self.blendShape_treeWidget)
        self.blendShape_treeWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.blendShape_treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.blendShape_treeWidget.c.mouseClicked.connect(self.update_selected_blendShape)
        self.blendShape_treeWidget.customContextMenuRequested.connect(self.blendShape_list_rightClicked)
        # ---- Options tab ---------------------------------------------------------
        # Reworked for Maya 2026: one column of collapsible sections (click a header to open
        # or close it). Which sections are open is remembered between sessions; all start
        # closed. Same widgets, names and signals as before.
        self.options_scrollArea = QScrollArea()
        self.options_scrollArea.setFrameShape(QFrame.NoFrame)
        self.options_scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.options_scrollArea.setWidgetResizable(True)
        self.secondary_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.secondary_tab_layout.addWidget(self.options_scrollArea)
        self.scrollContainer = _SectionList()
        self.options_scrollArea.setWidget(self.scrollContainer)
        self._option_button_groups = []

        def option_group(title):
            key = re.sub(r'\W+', '_', title.replace('&&', 'and')).strip('_')
            section = _CollapsibleSection(title, key)   # '&&' shows a single '&' in a button
            layout = QGridLayout(section.content)
            layout.setContentsMargins(10, 6, 10, 8)
            layout.setHorizontalSpacing(10)
            layout.setVerticalSpacing(4)
            self.scrollContainer.add_group(section)
            return section, layout

        def radio_row(layout, row, label, radios, columns=3, slot=None):
            """A label in column 0, then the radio buttons (wrapping after `columns`)."""
            group = QButtonGroup(self)
            group.setExclusive(True)
            self._option_button_groups.append(group)
            first_col = 0
            if label:
                lbl = QLabel(label)
                layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
                first_col = 1
            for i, radio in enumerate(radios):
                group.addButton(radio)
                layout.addWidget(radio, row + i // columns, first_col + i % columns)
                if slot:
                    radio.clicked.connect(slot)
            layout.setColumnStretch(first_col + columns, 1)   # keep the buttons packed to the left
            return row + (len(radios) + columns - 1) // columns

        # Lists & weight display
        self.column_box, column_grid = option_group('Lists && Weight Display')
        self.showBlendShapeColumn = QCheckBox('Show BlendShape Column')
        self.showBlendShapeColumn.clicked.connect(self.toggleBlendShapeColumn)
        self.showBlendShapeColumn.setChecked(True)
        self.showNonPaintable_checkBox = QCheckBox('Show Non-Paintable Attributes')
        self.showNonPaintable_checkBox.clicked.connect(self.toggleShowNonPaintable)
        self.showNonPaintable_checkBox.setChecked(False)
        self.showCustomPaintable_checkBox = QCheckBox('Show Custom Paintable Attributes')
        self.showCustomPaintable_checkBox.clicked.connect(self.toggleShowCustomPaintable)
        self.showCustomPaintable_checkBox.setChecked(True)
        self.display_deformer_weights_checkBox = QCheckBox('Display Selected Deformer Weights')
        self.display_deformer_weights_checkBox.setChecked(False)
        self.display_blendShape_weights_checkBox = QCheckBox('Display Selected BlendShape Weights')
        self.display_blendShape_weights_checkBox.setChecked(True)
        self.display_preflip_weights_checkBox = QCheckBox('Display Preflip Weights')
        self.display_preflip_weights_checkBox.setChecked(True)
        for row, widget in enumerate([self.showBlendShapeColumn, self.showNonPaintable_checkBox,
                                      self.showCustomPaintable_checkBox, self.display_deformer_weights_checkBox,
                                      self.display_blendShape_weights_checkBox, self.display_preflip_weights_checkBox]):
            column_grid.addWidget(widget, row, 0)

        # Mirror / flip
        self.direction_box, mirror_grid = option_group('Mirror / Flip')
        self.axis_selector_X_radio = QRadioButton('X')
        self.axis_selector_Y_radio = QRadioButton('Y')
        self.axis_selector_Z_radio = QRadioButton('Z')
        self.axis_selector_X_radio.setChecked(True)
        row = radio_row(mirror_grid, 0, 'Axis', [self.axis_selector_X_radio, self.axis_selector_Y_radio,
                                                 self.axis_selector_Z_radio], slot=self.update_axis)
        self.uv_axis_selector_U_radio = QRadioButton('U')
        self.uv_axis_selector_V_radio = QRadioButton('V')
        self.uv_axis_selector_U_radio.setChecked(True)
        row = radio_row(mirror_grid, row, 'UV Axis', [self.uv_axis_selector_U_radio, self.uv_axis_selector_V_radio],
                        slot=self.update_uv_axis)
        self.direction_pos_radio = QRadioButton('+ to -')
        self.direction_neg_radio = QRadioButton('- to +')
        self.direction_pos_radio.setChecked(True)
        row = radio_row(mirror_grid, row, 'Direction', [self.direction_pos_radio, self.direction_neg_radio],
                        slot=self.update_direction)
        self.max_matching_distance_checkbox = QCheckBox('Max Matching Distance')
        self.max_matching_distance_QSpinBox = QDoubleSpinBox()
        self.max_matching_distance_QSpinBox.setDecimals(4)
        self.max_matching_distance_QSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.max_matching_distance_QSpinBox.setEnabled(False)
        self.max_matching_distance_checkbox.stateChanged.connect(self.max_matching_distance_QSpinBox.setEnabled)
        mirror_grid.addWidget(self.max_matching_distance_checkbox, row, 0, 1, 2)
        mirror_grid.addWidget(self.max_matching_distance_QSpinBox, row, 2, 1, 2)
        # kept for code that refers to the old names
        self.axis_box = self.uv_axis_box = self.direction_box

        # Matching methods
        self.matching_method_box, matching_grid = option_group('Matching Methods')
        self.matching_method_component_radio = QRadioButton('Closest Component')
        self.matching_method_pointOnSurface_radio = QRadioButton('Closest Point On Surface')
        self.matching_method_UV_radio = QRadioButton('UV Space')
        self.matching_method_component_radio.setChecked(True)
        matching_grid.addWidget(QLabel('Mirror / paste / match:'), 0, 0, 1, 2)
        row = radio_row(matching_grid, 1, None, [self.matching_method_component_radio,
                                                 self.matching_method_pointOnSurface_radio,
                                                 self.matching_method_UV_radio], columns=2,
                        slot=self.update_matching_method)
        self.load_matching_method_index_radio = QRadioButton('Index')
        self.load_matching_method_component_radio = QRadioButton('Closest Component')
        self.load_matching_method_pointOnSurface_radio = QRadioButton('Closest Point On Surface')
        self.load_matching_method_UV_radio = QRadioButton('UV Space')
        self.load_matching_method_index_radio.setChecked(True)
        matching_grid.addWidget(QLabel('Loading weights from file:'), row, 0, 1, 2)
        radio_row(matching_grid, row + 1, None, [self.load_matching_method_index_radio,
                                                 self.load_matching_method_component_radio,
                                                 self.load_matching_method_pointOnSurface_radio,
                                                 self.load_matching_method_UV_radio], columns=2,
                  slot=self.update_loading_matching_method)
        self.load_matching_method_box = self.matching_method_box

        # Split methods
        self.curve_method_box, split_grid = option_group('Split Methods')
        self.curve_method_parameter_radio = QRadioButton('Parameter')
        self.curve_method_distance_along_radio = QRadioButton('Distance Along')
        self.curve_method_distance_from_radio = QRadioButton('Distance From')
        self.curve_method_parameter_radio.setChecked(True)
        row = radio_row(split_grid, 0, 'Curve', [self.curve_method_parameter_radio,
                                                 self.curve_method_distance_along_radio,
                                                 self.curve_method_distance_from_radio],
                        columns=3, slot=self.update_curve_method)
        self.surface_method_U_radio = QRadioButton('U Parameter')
        self.surface_method_V_radio = QRadioButton('V Parameter')
        self.surface_method_N_radio = QRadioButton('Distance From')
        self.surface_method_U_radio.setChecked(True)
        radio_row(split_grid, row, 'Surface', [self.surface_method_U_radio, self.surface_method_V_radio,
                                               self.surface_method_N_radio], columns=3,
                  slot=self.update_surface_method)
        self.curve_method_distance_along_radio.setToolTip('Distance Along Curve')
        self.curve_method_distance_from_radio.setToolTip('Distance From Curve')
        self.surface_method_N_radio.setToolTip('Distance From Surface')
        self.surface_method_box = self.curve_method_box

        # Clamp
        self.clamp_weights_GroupBox, clamp_grid = option_group('Clamp When Adding / Subtracting')
        self.clamp_weights_min_checkbox = QCheckBox('Minimum')
        self.clamp_weights_min_field = QDoubleSpinBox()
        self.clamp_weights_min_field.setEnabled(False)
        self.clamp_weights_min_checkbox.stateChanged.connect(self.clamp_weights_min_field.setEnabled)
        self.clamp_weights_max_checkbox = QCheckBox('Maximum')
        self.clamp_weights_max_field = QDoubleSpinBox()
        self.clamp_weights_max_field.setEnabled(False)
        self.clamp_weights_max_checkbox.stateChanged.connect(self.clamp_weights_max_field.setEnabled)
        for field in (self.clamp_weights_min_field, self.clamp_weights_max_field,
                      self.max_matching_distance_QSpinBox):
            field.setButtonSymbols(QAbstractSpinBox.NoButtons)
            field.setFixedWidth(90)
        clamp_grid.addWidget(self.clamp_weights_min_checkbox, 0, 0)
        clamp_grid.addWidget(self.clamp_weights_min_field, 0, 1)
        clamp_grid.addWidget(self.clamp_weights_max_checkbox, 0, 2)
        clamp_grid.addWidget(self.clamp_weights_max_field, 0, 3)
        clamp_grid.setColumnStretch(4, 1)
        self.display_weights_groupBox = self.column_box

        # Other
        self.misc_box, misc_grid = option_group('Other Options')
        self.keep_extracted_shape_checkbox = QCheckBox('Keep Object After Extracting Deltas')
        self.keep_extracted_shape_checkbox.setChecked(True)
        self.mirror_inBetweens_checkbox = QCheckBox('Duplicate InBetweens With Targets')
        self.mirror_names_lineEdit = QLineEdit()
        self.mirror_names_lineEdit.setText('{"left_":"right_","L_":"R_","Lf_":"Rt_"}')
        self.mirror_names_lineEdit.setToolTip('JSON dictionary of left / right name pairs used when mirroring targets')
        misc_grid.addWidget(self.keep_extracted_shape_checkbox, 0, 0, 1, 2)
        misc_grid.addWidget(self.mirror_inBetweens_checkbox, 1, 0, 1, 2)
        misc_grid.addWidget(QLabel('Left / Right Names'), 2, 0)
        misc_grid.addWidget(self.mirror_names_lineEdit, 2, 1)
        misc_grid.setColumnStretch(1, 1)
        self.scrollArea_layout = self.scrollContainer.layout()
        self.object_parentWidget = QWidget()
        self.object_parentWidget.setMinimumSize(100, 80)
        self.object_parentWidget.setMaximumSize(3000, 80)
        self.loaded_object_layout = QVBoxLayout()
        self.object_parentWidget.setLayout(self.loaded_object_layout)
        self.main_layout.addWidget(self.object_parentWidget)
        self.loaded_object_label = QLabel('Split Surface')
        self.loaded_object_label.setAlignment(Qt.AlignCenter)
        self.loaded_object_label.setFont(qFont_header)
        self.loaded_object_layout.addWidget(self.loaded_object_label)
        self.split_field_layout = QHBoxLayout()
        self.loaded_object_layout.addLayout(self.split_field_layout)
        self.load_object_button = QPushButton('Load')
        self.load_object_button.setMaximumSize(75, 28)
        self.load_object_button.setMinimumSize(75, 28)
        self.split_field_layout.addWidget(self.load_object_button)
        self.load_object_button.clicked.connect(self.load_object_button_clicked)
        self.refresh_object_button = QPushButton('Refresh')
        self.refresh_object_button.setMaximumSize(75, 28)
        self.refresh_object_button.setMinimumSize(75, 28)
        self.split_field_layout.addWidget(self.refresh_object_button)
        self.loaded_object_textField = QLineEdit()
        self.loaded_object_textField.setMaximumSize(5000, 30)
        self.loaded_object_textField.setMinimumSize(150, 30)
        self.loaded_object_textField.setReadOnly(True)
        self.split_field_layout.addWidget(self.loaded_object_textField)
        self.falloff_parentWidget = QWidget()
        self.falloff_parentWidget.setMinimumSize(100, 80)
        self.falloff_parentWidget.setMaximumSize(3000, 80)
        self.falloff_parentLayout = QVBoxLayout()
        self.falloff_parentWidget.setLayout(self.falloff_parentLayout)
        self.main_layout.addWidget(self.falloff_parentWidget)
        self.falloff_label = QLabel('Falloff')
        self.falloff_label.setAlignment(Qt.AlignCenter)
        self.falloff_label.setFont(qFont_header)
        self.falloff_parentLayout.addWidget(self.falloff_label)
        self.falloff_slider_layout = QHBoxLayout()
        self.falloff_parentLayout.addLayout(self.falloff_slider_layout)
        self.falloff_field = QDoubleSpinBox()
        self.falloff_slider_layout.addWidget(self.falloff_field)
        self.falloff_field.setMinimumSize(100, 30)
        self.falloff_field.setMaximumSize(100, 30)
        self.falloff_field.setDecimals(2)
        self.falloff_field.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.falloff_slider = QSlider(Qt.Horizontal)
        self.falloff_slider_layout.addWidget(self.falloff_slider)
        self.falloff_slider.valueChanged.connect(self.update_falloff_field)
        self.falloff_field.editingFinished.connect(self.update_falloff_slider)
        self.coordinate_parentWidget = QWidget()
        self.coordinate_parentWidget.setMinimumSize(100, 80)
        self.coordinate_parentWidget.setMaximumSize(3000, 80)
        self.coordinate_parentLayout = QVBoxLayout()
        self.coordinate_parentWidget.setLayout(self.coordinate_parentLayout)
        self.main_layout.addWidget(self.coordinate_parentWidget)
        self.coordinate_label = QLabel('Coordinate')
        self.coordinate_label.setAlignment(Qt.AlignCenter)
        self.coordinate_label.setFont(qFont_header)
        self.coordinate_parentLayout.addWidget(self.coordinate_label)
        self.coordinate_slider_layout = QHBoxLayout()
        self.coordinate_parentLayout.addLayout(self.coordinate_slider_layout)
        self.coordinate_field = QDoubleSpinBox()
        self.coordinate_slider_layout.addWidget(self.coordinate_field)
        self.coordinate_field.setMinimumSize(100, 30)
        self.coordinate_field.setMaximumSize(100, 30)
        self.coordinate_field.setDecimals(2)
        self.coordinate_field.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.coordinate_slider = QSlider(Qt.Horizontal)
        self.coordinate_slider_layout.addWidget(self.coordinate_slider)
        self.coordinate_slider.valueChanged.connect(self.update_coordinate_field)
        self.coordinate_field.editingFinished.connect(self.update_coordinate_slider)
        self.number_parentWidget = QWidget()
        self.main_layout.addWidget(self.number_parentWidget)
        self.number_parentLayout = QVBoxLayout()
        self.number_parentWidget.setLayout(self.number_parentLayout)
        self.number_label = QLabel('Number Of Sections')
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setFont(qFont_header)
        self.number_parentLayout.addWidget(self.number_label)
        self.number_field = QSpinBox()
        self.number_field.setMinimumSize(200, 60)
        self.number_field.setMaximumSize(200, 60)
        self.number_field.setAlignment(Qt.AlignCenter)
        self.number_field.setMinimum(1)
        self.number_field.setMaximum(12)
        self.number_parentLayout.addWidget(self.number_field)
        self.cc_buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.cc_buttons_layout)
        self.confirm_button = QPushButton('Confirm')
        self.cancel_button = QPushButton('Cancel')
        self.cc_buttons_layout.addWidget(self.confirm_button)
        self.cc_buttons_layout.addWidget(self.cancel_button)
        self.split_table_lower_widget = QWidget()
        self.lower_layout = QVBoxLayout()
        self.split_table_lower_widget.setLayout(self.lower_layout)
        self.split_table_splitter.addWidget(self.split_table_lower_widget)
        self.split_table_header = QLabel('Split Targets')
        self.split_table_header.setAlignment(Qt.AlignCenter)
        self.split_table_header.setFont(qFont_header)
        self.lower_layout.addWidget(self.split_table_header)
        self.split_target_tableWidget = split_QTableWidget()
        self.lower_layout.addWidget(self.split_target_tableWidget)
        self.split_target_tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.split_target_tableWidget.setDragEnabled(True)
        self.split_target_tableWidget.setAcceptDrops(True)
        self.split_target_tableWidget.customContextMenuRequested.connect(self.split_table_rightClicked)
        self.load_shape_button_clicked()
        self.hide_extra_widgets()
        return

    def load_shape_button_clicked(self):
        self.clear_weights()
        self.shape_name.setText('')
        self.shape = ''
        long_selection_list = cmds.ls(sl=True, l=True)
        short_selection_list = cmds.ls(sl=True)
        if len(long_selection_list) > 0:
            if '.' in long_selection_list[0]:
                long_selection_list = [
                 long_selection_list[0].split('.')[0]]
                short_selection_list = [short_selection_list[0].split('.')[0]]
            if cmds.nodeType(long_selection_list[0]) == 'transform':
                short_selection_list = cmds.listRelatives(long_selection_list[0], s=True)
                long_selection_list = cmds.listRelatives(long_selection_list[0], s=True, f=True)
            if long_selection_list:
                if cmds.nodeType(long_selection_list[0]) in ('mesh', 'nurbsCurve',
                                                             'nurbsSurface', 'lattice'):
                    self.shape_name.setText(short_selection_list[0])
                    self.shape = long_selection_list[0]
                    self.shape_shortName = short_selection_list[0]
                    self.ip_dictionary = wt_utils.convert_shape_to_index_position_dictionary(shape=self.shape)
                    self.position_list = wt_utils.get_position_list(self.shape)
        self.update_deformer_treeWidget()
        self.update_blendShape_treeWidget()
        return

    def load_object_button_clicked(self):
        self.loaded_object_textField.setText('')
        selection_list = cmds.ls(sl=True, l=True)
        short_selection_list = cmds.ls(sl=True)
        if len(selection_list) > 0:
            if self.object_type == 'nurbsSurface':
                selection_list[0] = selection_list[0].split('.')[0]
                if cmds.nodeType(selection_list[0]) == 'transform':
                    short_selection_list = cmds.listRelatives(selection_list[0], s=True)
                    selection_list = cmds.listRelatives(selection_list[0], s=True, f=True)
                    if len(selection_list) == 0:
                        return
                if cmds.nodeType(selection_list[0]) == 'nurbsSurface':
                    self.loaded_object_textField.setText(short_selection_list[0])
                    self.loaded_object = selection_list[0]
                    return
            elif self.object_type == 'nurbsCurve':
                selection_list[0] = selection_list[0].split('.')[0]
                if cmds.nodeType(selection_list[0]) == 'transform':
                    short_selection_list = cmds.listRelatives(selection_list[0], s=True)
                    selection_list = cmds.listRelatives(selection_list[0], s=True, f=True)
                    if len(selection_list) == 0:
                        return
                if cmds.nodeType(selection_list[0]) == 'nurbsCurve':
                    self.loaded_object_textField.setText(short_selection_list[0])
                    self.loaded_object = selection_list[0]
                    return
            elif self.object_type == 'transform':
                if cmds.nodeType(selection_list[0]) == 'transform':
                    self.loaded_object_textField.setText(short_selection_list[0])
                    self.loaded_object = selection_list[0]
                    return
            self.loaded_object_textField.setText('')
            self.loaded_object = ''
        return

    def update_axis(self):
        if self.axis_selector_X_radio.isChecked():
            self.axis = 'x'
        elif self.axis_selector_Y_radio.isChecked():
            self.axis = 'y'
        elif self.axis_selector_Z_radio.isChecked():
            self.axis = 'z'
        self.c.axis_updated.emit()
        return

    def update_uv_axis(self):
        if self.uv_axis_selector_U_radio.isChecked():
            self.uv_axis = 'u'
        elif self.uv_axis_selector_V_radio.isChecked():
            self.uv_axis = 'v'
        self.c.uv_axis_updated.emit()
        return

    def update_direction(self):
        if self.direction_pos_radio.isChecked():
            self.direction = '+ to -'
            self.direction_short = 'p'
        else:
            self.direction = '- to +'
            self.direction_short = 'n'
        self.c.direction_updated.emit()
        return

    def update_matching_method(self):
        if self.matching_method_component_radio.isChecked():
            self.matching_method = 'closestComponent'
        if self.matching_method_pointOnSurface_radio.isChecked():
            self.matching_method = 'closestPointOnSurface'
        if self.matching_method_UV_radio.isChecked():
            self.matching_method = 'closestComponentUV'
        self.c.match_method_updated.emit()
        return

    def update_loading_matching_method(self):
        if self.load_matching_method_index_radio.isChecked():
            self.load_matching_method = 'index'
        if self.load_matching_method_component_radio.isChecked():
            self.load_matching_method = 'closestComponent'
        if self.load_matching_method_pointOnSurface_radio.isChecked():
            self.load_matching_method = 'closestPointOnSurface'
        if self.load_matching_method_UV_radio.isChecked():
            self.load_matching_method = 'closestComponentUV'
        self.c.load_matching_method_updated.emit()
        return

    def update_curve_method(self):
        if self.curve_method_parameter_radio.isChecked():
            self.curve_method = 'parameter'
        if self.curve_method_distance_along_radio.isChecked():
            self.curve_method = 'distanceAlong'
        if self.curve_method_distance_from_radio.isChecked():
            self.curve_method = 'distanceFrom'
        self.c.curve_method_updated.emit()
        return

    def update_surface_method(self):
        if self.surface_method_U_radio.isChecked():
            self.surface_method = 0
        if self.surface_method_V_radio.isChecked():
            self.surface_method = 1
        if self.surface_method_N_radio.isChecked():
            self.surface_method = 2
        self.c.surface_method_updated.emit()
        return

    def update_falloff_field(self):
        set_value = float(self.falloff_slider.value()) / 100
        self.falloff_field.setValue(set_value)
        return

    def update_falloff_slider(self):
        set_value = float(self.falloff_field.value()) * 100
        self.falloff_slider.setValue(set_value)
        return

    def update_coordinate_field(self):
        set_value = float(self.coordinate_slider.value()) / 100
        self.coordinate_field.setValue(set_value)
        return

    def update_coordinate_slider(self):
        set_value = float(self.coordinate_field.value()) * 100
        self.coordinate_slider.setValue(set_value)
        return

    def hide_extra_widgets(self):
        self.falloff_parentWidget.setVisible(False)
        self.coordinate_parentWidget.setVisible(False)
        self.confirm_button.setVisible(False)
        self.cancel_button.setVisible(False)
        self.object_parentWidget.setVisible(False)
        self.number_parentWidget.setVisible(False)
        self.split_table_lower_widget.setVisible(False)
        self.load_shape_button.setEnabled(True)
        return

    def update_deformer_treeWidget(self):
        self.deformer_treeWidget.clear()
        valid_node_list = ['wire', 'cluster', 'nonLinear', 'softMod', 'ffd', 'repulsor']
        # Node types with their own branch below, or their own tab (skinCluster, blendShape).
        special_node_list = ['translateUVN', 'twistUVN', 'multiTranslate', 'multiRotate', 'curveDeformer',
                             'skinCluster', 'blendShape', 'tweak']
        if cmds.objExists(self.shape):
            deformer_node_list = wt_utils.get_ordered_deformer_list(self.shape)
        else:
            return
        for deformer_node in sorted(deformer_node_list):
            deformer_item = None
            node_type = cmds.nodeType(deformer_node)
            # List every deformer that has a default weight map, i.e. is a weightGeometryFilter
            # (cluster, softMod, wire, nonLinear, ffd, deltaMush, tension, jiggle, sculpt, ...;
            # plug-in deformers too). Deformers without one, like wrap, are left out.
            has_default_weights = 'weightGeometryFilter' in (cmds.nodeType(deformer_node, inherited=True) or [])
            if node_type in valid_node_list or (node_type not in special_node_list and has_default_weights):
                deformer_item = deformer_treeWidgetItem(self.deformer_treeWidget, [deformer_node])
                deformer_item.name = deformer_node
                deformer_item.node = deformer_node
                deformer_item.shape = self.shape
                deformer_item.inBetween_name = None
                deformer_item.plug = None
                deformer_item.paintable = True
                deformer_item.custom = False
            elif cmds.nodeType(deformer_node) == 'translateUVN':
                deformer_item = deformer_treeWidgetItem(self.deformer_treeWidget, [deformer_node])
                deformer_item.name = deformer_node
                deformer_item.node = deformer_node
                deformer_item.shape = self.shape
                deformer_item.inBetween_name = None
                deformer_item.plug = None
                sel = om2.MSelectionList()
                sel.add(deformer_node)
                mFn = om2.MFnDependencyNode(sel.getDependNode(0))
                offset_plug = mFn.findPlug('offset', False)
                existingIndices = offset_plug.getExistingArrayAttributeIndices()
                for a in existingIndices:
                    offset_item = deformer_treeWidgetItem(deformer_item, [('offset[{}]').format(a)])
                    offset_item.name = ('{}.offset[{}]').format(deformer_node, a)
                    offset_item.node = deformer_node
                    offset_item.shape = self.shape
                    offset_item.inBetween_name = None
                    offset_item.plug = None
                    for axis in 'UVN':
                        for direction in ['positive', 'negative']:
                            weight_item = deformer_treeWidgetItem(offset_item, [direction + axis])
                            weight_item.node = deformer_node
                            weight_item.shape = self.shape
                            weight_item.inBetween_name = None
                            weightList_plug = mFn.findPlug(direction + axis, False).elementByLogicalIndex(a).child(0)
                            weight_item.plug = weightList_plug

            elif cmds.nodeType(deformer_node) == 'twistUVN':
                deformer_item = deformer_treeWidgetItem(self.deformer_treeWidget, [deformer_node])
                deformer_item.name = deformer_node
                deformer_item.node = deformer_node
                deformer_item.shape = self.shape
                deformer_item.inBetween_name = None
                deformer_item.plug = None
                sel = om2.MSelectionList()
                sel.add(deformer_node)
                mFn = om2.MFnDependencyNode(sel.getDependNode(0))
                twist_plug = mFn.findPlug('twist', False)
                existingIndices = twist_plug.getExistingArrayAttributeIndices()
                for a in existingIndices:
                    twist_item = deformer_treeWidgetItem(deformer_item, [('twist[{}]').format(a)])
                    twist_item.name = ('{}.twist[{}]').format(deformer_node, a)
                    twist_item.node = deformer_node
                    twist_item.shape = self.shape
                    twist_item.inBetween_name = None
                    twist_item.plug = None
                    for direction in ['positive', 'negative']:
                        weight_item = deformer_treeWidgetItem(twist_item, [direction])
                        weight_item.node = deformer_node
                        weight_item.shape = self.shape
                        weight_item.inBetween_name = None
                        weightList_plug = mFn.findPlug(direction, False).elementByLogicalIndex(a).child(0)
                        weight_item.plug = weightList_plug

            elif cmds.nodeType(deformer_node) == 'multiTranslate':
                deformer_item = deformer_treeWidgetItem(self.deformer_treeWidget, [deformer_node])
                deformer_item.name = deformer_node
                deformer_item.node = deformer_node
                deformer_item.shape = self.shape
                deformer_item.inBetween_name = None
                deformer_item.plug = None
                sel = om2.MSelectionList()
                sel.add(deformer_node)
                mFn = om2.MFnDependencyNode(sel.getDependNode(0))
                offset_plug = mFn.findPlug('offset', False)
                existingIndices = offset_plug.getExistingArrayAttributeIndices()
                for a in existingIndices:
                    offset_item = deformer_treeWidgetItem(deformer_item, [('offset[{}]').format(a)])
                    offset_item.name = ('{}.offset[{}]').format(deformer_node, a)
                    offset_item.node = deformer_node
                    offset_item.shape = self.shape
                    offset_item.inBetween_name = None
                    offset_item.plug = None
                    for axis in 'XYZ':
                        for direction in ['positive', 'negative']:
                            weight_item = deformer_treeWidgetItem(offset_item, [direction + axis])
                            weight_item.node = deformer_node
                            weight_item.shape = self.shape
                            weight_item.inBetween_name = None
                            weightList_plug = mFn.findPlug(direction + axis, False).elementByLogicalIndex(a).child(0)
                            weight_item.plug = weightList_plug

            elif cmds.nodeType(deformer_node) == 'multiRotate':
                deformer_item = deformer_treeWidgetItem(self.deformer_treeWidget, [deformer_node])
                deformer_item.name = deformer_node
                deformer_item.node = deformer_node
                deformer_item.shape = self.shape
                deformer_item.inBetween_name = None
                deformer_item.plug = None
                sel = om2.MSelectionList()
                sel.add(deformer_node)
                mFn = om2.MFnDependencyNode(sel.getDependNode(0))
                offset_plug = mFn.findPlug('offset', False)
                existingIndices = offset_plug.getExistingArrayAttributeIndices()
                for a in existingIndices:
                    offset_item = deformer_treeWidgetItem(deformer_item, [('offset[{}]').format(a)])
                    offset_item.name = ('{}.offset[{}]').format(deformer_node, a)
                    offset_item.node = deformer_node
                    offset_item.shape = self.shape
                    offset_item.inBetween_name = None
                    offset_item.plug = None
                    for axis in 'XYZ':
                        for direction in ['positive', 'negative']:
                            weight_item = deformer_treeWidgetItem(offset_item, [direction + axis])
                            weight_item.node = deformer_node
                            weight_item.shape = self.shape
                            weight_item.inBetween_name = None
                            weightList_plug = mFn.findPlug(direction + axis, False).elementByLogicalIndex(a).child(0)
                            weight_item.plug = weightList_plug

            elif cmds.nodeType(deformer_node) == 'curveDeformer':
                deformer_item = deformer_treeWidgetItem(self.deformer_treeWidget, [deformer_node])
                deformer_item.name = deformer_node
                deformer_item.node = deformer_node
                deformer_item.shape = self.shape
                deformer_item.inBetween_name = None
                deformer_item.plug = None
                sel = om2.MSelectionList()
                sel.add(deformer_node)
                mFn = om2.MFnDependencyNode(sel.getDependNode(0))
                twist_plug = mFn.findPlug('twist', False)
                existingIndices = twist_plug.getExistingArrayAttributeIndices()
                for a in existingIndices:
                    twist_item = deformer_treeWidgetItem(deformer_item, [('twist[{}]').format(a)])
                    twist_item.name = ('{}.twist[{}]').format(deformer_node, a)
                    twist_item.node = deformer_node
                    twist_item.shape = self.shape
                    twist_item.inBetween_name = None
                    twist_item.plug = None
                    for direction in ['positiveTwist', 'negativeTwist']:
                        weight_item = deformer_treeWidgetItem(twist_item, [direction])
                        weight_item.node = deformer_node
                        weight_item.shape = self.shape
                        weight_item.inBetween_name = None
                        weightList_plug = mFn.findPlug(direction, False).elementByLogicalIndex(a).child(0)
                        weight_item.plug = weightList_plug

            if deformer_item:
                paintableAttributes = wt_utils.listPaintableAttributes(deformer_node)
                for each_attr in paintableAttributes:
                    if each_attr.split('.')[-1] == 'weights':
                        continue
                    weight_item = deformer_treeWidgetItem(deformer_item, [each_attr.split('.')[-1]])
                    weight_item.node = deformer_node
                    weight_item.shape = self.shape
                    weight_item.inBetween_name = None
                    weight_item.paintable = True
                    weight_item.custom = True
                    sel = om2.MSelectionList()
                    sel.add(deformer_node)
                    mFn = om2.MFnDependencyNode(sel.getDependNode(0))
                    weightList_plug = mFn.findPlug(each_attr.split('.')[0], False)
                    weight_item.plug = weightList_plug

        self.update_deformer_treeWidget_display()
        return

    def update_deformer_treeWidget_display(self):
        entry_string = self.deformer_name_search.text().lower()
        regex_string = entry_string.replace('*', '.*')
        try:
            re.compile(regex_string)
        except:
            return

        for i in range(self.deformer_treeWidget.topLevelItemCount()):
            listItem = self.deformer_treeWidget.topLevelItem(i)
            listItem_name = listItem.text(0)
            if re.search(regex_string, listItem_name.lower()):
                listItem.setHidden(False)
                child_count = listItem.childCount()
                if child_count:
                    for i in range(child_count):
                        listItem.child(i).setHidden(False)

            else:
                foundChild = False
                child_count = listItem.childCount()
                if child_count:
                    for i in range(child_count):
                        if re.search(regex_string, listItem.child(i).text(0).lower()):
                            listItem.child(i).setHidden(False)
                            foundChild = True
                        else:
                            listItem.child(i).setHidden(True)

                    if foundChild:
                        listItem.setHidden(False)
                    else:
                        listItem.setHidden(True)
                else:
                    listItem.setHidden(True)

        def go_upstream(upstream_attr):
            source_attribute = cmds.connectionInfo(upstream_attr, sfd=True)
            if not source_attribute:
                return False
            source_node = source_attribute.split('.')[0]
            if 'geometryFilter' in cmds.nodeType(source_node, inherited=True):
                if source_node not in active_deformers:
                    active_deformers.append(source_node)
                weightList_attr = source_attribute.split('.')[-1].split('[')[0]
                weights_attr = cmds.attributeQuery(weightList_attr, node=source_node, listChildren=True)[0]
                hasUpstreamMap = go_upstream(source_attribute)
                if not hasUpstreamMap:
                    if source_node not in active_maps:
                        active_maps[source_node] = [
                         weights_attr]
                    else:
                        active_maps[source_node].append(weights_attr)
                return True
            if cmds.nodeType(source_node) in ('weightSplitter', 'weightConnector',
                                              'weightMirror', 'weightFlipper'):
                perShape_index = source_attribute.split('[')[-1].split(']')[0]
                src_attr_perShape = source_node + '.inputWeightList[' + perShape_index + ']'
                ret = go_upstream(src_attr_perShape)
                return ret
            return

        if self.deformer_active_checkBox.isChecked():
            active_deformers = []
            active_maps = {}
            for multiTranslate in _ls_type('multiTranslate'):
                sel = om.MSelectionList()
                sel.add(multiTranslate)
                sel.add(self.shape)
                deformerObj = om.MObject()
                shapeObj = om.MObject()
                sel.getDependNode(0, deformerObj)
                sel.getDependNode(1, shapeObj)
                shapeIndex = omAnim.MFnGeometryFilter(deformerObj).indexForOutputShape(shapeObj)
                offset_count = cmds.getAttr(multiTranslate + '.offset', multiIndices=True)
                for index in offset_count:
                    for axis in 'XYZ':
                        offset_val = cmds.getAttr(multiTranslate + ('.offset[{}].offset{}').format(index, axis))
                        if offset_val > 0.01:
                            active_deformers.append(multiTranslate)
                            attr = multiTranslate + ('.positive{}[{}].positive{}_WeightList').format(axis, index, axis)
                            per_shape_attr = ('{}[{}]').format(attr, shapeIndex)
                            ret = go_upstream(per_shape_attr)
                            if ret:
                                break
                        elif offset_val < -0.01:
                            active_deformers.append(multiTranslate)
                            attr = multiTranslate + ('.negative{}[{}].negative{}_WeightList').format(axis, index, axis)
                            per_shape_attr = ('{}[{}]').format(attr, shapeIndex)
                            ret = go_upstream(per_shape_attr)
                            if ret:
                                break

            for multiTranslate in _ls_type('translateUVN'):
                sel = om.MSelectionList()
                sel.add(multiTranslate)
                sel.add(self.shape)
                deformerObj = om.MObject()
                shapeObj = om.MObject()
                sel.getDependNode(0, deformerObj)
                sel.getDependNode(1, shapeObj)
                try:
                    shapeIndex = omAnim.MFnGeometryFilter(deformerObj).indexForOutputShape(shapeObj)
                except:
                    continue

                offset_count = cmds.getAttr(multiTranslate + '.offset', multiIndices=True)
                for index in offset_count:
                    for axis in 'UVN':
                        offset_val = cmds.getAttr(multiTranslate + ('.offset[{}].offset{}').format(index, axis))
                        if offset_val > 0.01:
                            active_deformers.append(multiTranslate)
                            attr = multiTranslate + ('.positive{}[{}].positive{}_WeightList').format(axis, index, axis)
                            per_shape_attr = ('{}[{}]').format(attr, shapeIndex)
                            ret = go_upstream(per_shape_attr)
                        elif offset_val < -0.01:
                            active_deformers.append(multiTranslate)
                            attr = multiTranslate + ('.negative{}[{}].negative{}_WeightList').format(axis, index, axis)
                            per_shape_attr = ('{}[{}]').format(attr, shapeIndex)
                            ret = go_upstream(per_shape_attr)

            for multiTranslate in _ls_type('multiRotate'):
                sel = om.MSelectionList()
                sel.add(multiTranslate)
                sel.add(self.shape)
                deformerObj = om.MObject()
                shapeObj = om.MObject()
                sel.getDependNode(0, deformerObj)
                sel.getDependNode(1, shapeObj)
                shapeIndex = omAnim.MFnGeometryFilter(deformerObj).indexForOutputShape(shapeObj)
                offset_count = cmds.getAttr(multiTranslate + '.offset', multiIndices=True)
                for index in offset_count:
                    for axis in 'XYZ':
                        offset_val = cmds.getAttr(multiTranslate + ('.offset[{}].offset{}').format(index, axis))
                        if offset_val > 0.01:
                            active_deformers.append(multiTranslate)
                            attr = multiTranslate + ('.positive{}[{}].positive{}_WeightList').format(axis, index, axis)
                            per_shape_attr = ('{}[{}]').format(attr, shapeIndex)
                            ret = go_upstream(per_shape_attr)
                            if ret:
                                continue
                        elif offset_val < -0.01:
                            active_deformers.append(multiTranslate)
                            attr = multiTranslate + ('.negative{}[{}].negative{}_WeightList').format(axis, index, axis)
                            per_shape_attr = ('{}[{}]').format(attr, shapeIndex)
                            ret = go_upstream(per_shape_attr)
                            if ret:
                                continue

            for multiTranslate in _ls_type('curveDeformer'):
                sel = om.MSelectionList()
                sel.add(multiTranslate)
                sel.add(self.shape)
                deformerObj = om.MObject()
                shapeObj = om.MObject()
                sel.getDependNode(0, deformerObj)
                sel.getDependNode(1, shapeObj)
                shapeIndex = omAnim.MFnGeometryFilter(deformerObj).indexForOutputShape(shapeObj)
                offset_count = cmds.getAttr(multiTranslate + '.twist', multiIndices=True)
                for index in offset_count:
                    offset_val = cmds.getAttr(multiTranslate + ('.twist[{}]').format(index))
                    if offset_val > 0.01:
                        active_deformers.append(multiTranslate)
                        attr = multiTranslate + ('.positiveTwist[{}].positiveTwistWeightList').format(index)
                        per_shape_attr = ('{}[{}]').format(attr, shapeIndex)
                        ret = go_upstream(per_shape_attr)
                        if ret:
                            continue
                    elif offset_val < -0.01:
                        active_deformers.append(multiTranslate)
                        attr = multiTranslate + ('.negativeTwist[{}].negativeTwistWeightList').format(index)
                        per_shape_attr = ('{}[{}]').format(attr, shapeIndex)
                        ret = go_upstream(per_shape_attr)
                        if ret:
                            continue

            for each_cluster in _ls_type('cluster'):
                sel = om2.MSelectionList()
                sel.add(each_cluster)
                if not cmds.getAttr(each_cluster + '.weightedMatrix'):
                    continue
                plug = om2.MFnDependencyNode(sel.getDependNode(0)).findPlug('weightedMatrix', False)
                weightedMatrix = om2.MFnMatrixData(plug.asMObject()).matrix()
                if not weightedMatrix.isEquivalent(om2.MMatrix()):
                    active_deformers.append(each_cluster)

            for each_lattice in _ls_type('ffd'):
                latticePoint_src = cmds.connectionInfo(each_lattice + '.deformedLatticePoints', sfd=True)
                if not latticePoint_src:
                    continue
                else:
                    latticePoint_src = latticePoint_src.split('.')[0]
                lattice_pnts = wt_utils.get_position_list(latticePoint_src, prePose=False, object_space=True)
                sel = om2.MSelectionList()
                sel.add(each_lattice)
                plug = om2.MFnDependencyNode(sel.getDependNode(0)).findPlug('baseLatticeMatrix', False)
                s_divisions = float(cmds.getAttr(latticePoint_src + '.sDivisions') - 1)
                t_divisions = float(cmds.getAttr(latticePoint_src + '.tDivisions') - 1)
                u_divisions = float(cmds.getAttr(latticePoint_src + '.uDivisions') - 1)
                lattice_pnts = [[x[0] * s_divisions * 2, x[1] * t_divisions * 2, x[2] * u_divisions * 2] for x in lattice_pnts]
                deformed_lattice = False
                for pnt in lattice_pnts:
                    for axis in pnt:
                        if abs(axis - int(round(axis))) > 0.01:
                            deformed_lattice = True
                            break

                    if deformed_lattice:
                        break

                if deformed_lattice:
                    active_deformers.append(each_lattice)

            for each_nonLinear in _ls_type('nonLinear'):
                nonLinear_shape = cmds.connectionInfo(each_nonLinear + '.deformerData', sfd=True)
                if not nonLinear_shape:
                    continue
                else:
                    nonLinear_shape = nonLinear_shape.split('.')[0]
                if abs(cmds.getAttr(nonLinear_shape + '.curvature')) > 0.01:
                    active_deformers.append(each_nonLinear)

            for each_repulsor in _ls_type('repulsor'):
                if abs(cmds.getAttr(each_repulsor + '.offsetDistance')) > 0.01:
                    active_deformers.append(each_repulsor)

            # FIX: deformers without a specific test above (wrap, deltaMush, softMod, wire, the
            # non-bend nonLinears, ...) count as active when their envelope isn't 0.
            tested_types = ('cluster', 'ffd', 'repulsor', 'translateUVN', 'twistUVN', 'multiTranslate',
                            'multiRotate', 'curveDeformer')
            for i in range(self.deformer_treeWidget.topLevelItemCount()):
                node = self.deformer_treeWidget.topLevelItem(i).text(0)
                if node in active_deformers or not cmds.objExists(node):
                    continue
                node_type = cmds.nodeType(node)
                if node_type in tested_types:
                    continue
                if node_type == 'nonLinear':
                    handle = (cmds.connectionInfo(node + '.deformerData', sfd=True) or '').split('.')[0]
                    if handle and cmds.nodeType(handle) == 'deformBend':
                        continue   # tested by curvature above
                try:
                    if abs(cmds.getAttr(node + '.envelope')) > 0.0001:
                        active_deformers.append(node)
                except (ValueError, RuntimeError):
                    active_deformers.append(node)

            for i in range(self.deformer_treeWidget.topLevelItemCount()):
                deformerItem = self.deformer_treeWidget.topLevelItem(i)
                deformerName = deformerItem.text(0)
                if deformerName not in active_deformers:
                    deformerItem.setHidden(True)
                else:
                    child_count = deformerItem.childCount()
                    if deformerName not in active_maps:
                        if child_count:
                            for j in range(child_count):
                                deformerItem.child(j).setHidden(True)

                    elif child_count:
                        for j in range(child_count):
                            map_name = deformerItem.child(j).text(0)
                            if map_name not in active_maps[deformerName]:
                                deformerItem.child(j).setHidden(True)

        for i in range(self.deformer_treeWidget.topLevelItemCount()):
            deformerItem = self.deformer_treeWidget.topLevelItem(i)
            if deformerItem.isHidden():
                continue
            for j in range(deformerItem.childCount()):
                childItem = deformerItem.child(j)
                if childItem.custom and not self.showCustomPaintable:
                    childItem.setHidden(True)
                if not childItem.paintable and not self.showNonPaintable:
                    childItem.setHidden(True)

        return

    def update_blendShape_treeWidget(self):
        self.blendShape_treeWidget.clear()
        if cmds.objExists(self.shape):
            # FIX: found through history; Maya 2022+ component-tag deformers have no deformer set,
            # so the original listSets() lookup found no blendShapes.
            blendShape_node_list = wt_utils.get_shape_deformers(self.shape, 'blendShape')
            if not blendShape_node_list:
                return
            for node in blendShape_node_list:
                blendShape_node_treeWidgetItem = blendShape_treeWidgetItem(self.blendShape_treeWidget, [node])
                blendShape_node_treeWidgetItem.shape = self.shape
                blendShape_node_treeWidgetItem.name = node
                blendShape_node_treeWidgetItem.node = node
                sel = om2.MSelectionList()
                sel.add(node)
                mFn = om2.MFnDependencyNode(sel.getDependNode(0))
                ibInfo_mPlug = mFn.findPlug('inbetweenInfoGroup', False)
                ib_target_indices = ibInfo_mPlug.getExistingArrayAttributeIndices()
                ib_target_indices = [int(x) for x in ib_target_indices]
                target_attr_list = cmds.aliasAttr(node, query=True)
                if target_attr_list:
                    target_list = target_attr_list[::2]
                    index_list = target_attr_list[1::2]
                    index_list = [int(x.split('[')[-1][:-1]) for x in index_list]
                    for index, target in sorted(zip(index_list, target_list), key=(lambda x: x[1])):
                        blendShape_target_treeWidgetItem = blendShape_treeWidgetItem(blendShape_node_treeWidgetItem, [target])
                        blendShape_target_treeWidgetItem.name = ('{} | {}').format(node, target)
                        blendShape_target_treeWidgetItem.node = node
                        blendShape_target_treeWidgetItem.target_name = target
                        blendShape_target_treeWidgetItem.target_index = index
                        blendShape_target_treeWidgetItem.inBetween_weight = 1.0
                        blendShape_target_treeWidgetItem.shape = self.shape
                        if index in ib_target_indices:
                            ib_weight_indices = ibInfo_mPlug.elementByLogicalIndex(index).child(0).getExistingArrayAttributeIndices()
                            ib_weight_indices = [x for x in ib_weight_indices]
                            if 0 in ib_weight_indices:
                                ib_weight_indices.remove(0)
                            for ib_weight_indice in ib_weight_indices:
                                ib_target_name = ibInfo_mPlug.elementByLogicalIndex(index).child(0).elementByLogicalIndex(ib_weight_indice).child(1).asString()
                                blendShape_ib_treeWidgetItem = blendShape_treeWidgetItem(blendShape_target_treeWidgetItem, [ib_target_name])
                                blendShape_target_treeWidgetItem.name = ('{} | {} | {}').format(node, target, ib_target_name)
                                blendShape_ib_treeWidgetItem.node = node
                                blendShape_ib_treeWidgetItem.target_name = target
                                blendShape_ib_treeWidgetItem.target_index = index
                                blendShape_ib_treeWidgetItem.inBetween_name = ib_target_name
                                blendShape_ib_treeWidgetItem.inBetween_weight = float((ib_weight_indice - 5000) / 1000.0)
                                blendShape_ib_treeWidgetItem.shape = self.shape

                else:
                    target_list = []

            self.update_blendShape_treeWidget_display()
        return

    def update_blendShape_treeWidget_display(self):
        entry_string = self.blendShape_name_search.text().lower()
        regex_string = entry_string.replace('*', '.*')
        try:
            re.compile(regex_string)
        except:
            return

        blendShape_node_count = self.blendShape_treeWidget.topLevelItemCount()
        treeWidget_node_list = [self.blendShape_treeWidget.topLevelItem(i) for i in range(blendShape_node_count)]
        for node in treeWidget_node_list:
            child_count = node.childCount()
            for i in range(child_count):
                if re.search(regex_string, node.child(i).text(0).lower()):
                    node.child(i).setHidden(False)
                else:
                    node.child(i).setHidden(True)
                if self.blendShape_active_checkBox.isChecked():
                    if abs(cmds.getAttr(('{}.{}').format(node.text(0), node.child(i).text(0)))) < weight_threshhold:
                        node.child(i).setHidden(True)

        return

    def selection_off(self):
        self.rightClick_off()
        self.deformer_treeWidget.setSelectionMode(QAbstractItemView.NoSelection)
        self.blendShape_treeWidget.setSelectionMode(QAbstractItemView.NoSelection)
        self.selected_wtHolder_list = []
        return

    def selection_on(self):
        self.rightClick_on()
        self.deformer_treeWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.blendShape_treeWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        return

    def rightClick_off(self):
        self.deformer_treeWidget.setContextMenuPolicy(Qt.NoContextMenu)
        self.blendShape_treeWidget.setContextMenuPolicy(Qt.NoContextMenu)
        for item in self.deformer_treeWidget.selectedItems():
            item.setSelected(False)

        for item in self.blendShape_treeWidget.selectedItems():
            item.setSelected(False)

        return

    def rightClick_on(self):
        self.deformer_treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.blendShape_treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        return

    def highlight_selected_wtHolders(self):
        if self.selected_wtHolder_list:
            self.selected_wtHolder_list[0].primary_highlight()
            for item in self.selected_wtHolder_list[1:]:
                item.highlight()

        return

    def unhighlight_wtHolders(self):
        for item in self.active_wtHolder_list:
            item.unhighlight()

        return

    def display_weights(self, weight_dict_list):
        if cmds.objExists(self.shape):
            shape_transform = cmds.listRelatives(self.shape, p=True, f=True)[0]
            shape_transform_selected = shape_transform in cmds.ls(sl=True, l=True)
            shape_selected = cmds.ls(self.shape, l=True)[0] in cmds.ls(sl=True, l=True)
            if not shape_transform_selected and not shape_selected:
                self.clear_weights()
        else:
            return
        if cmds.getAttr(self.shape + '.displayColors', l=True):
            return
        if weight_dict_list == []:
            return
        all_color_list = []
        display_dict_list = weight_dict_list[:len(color_vector_list)]
        last_weight_dict = display_dict_list.pop(-1)
        display_dict_list.insert(0, last_weight_dict)
        mIndexArray = om2.MIntArray()
        for i, weight_dict in enumerate(display_dict_list):
            if i == 0:
                index_list = list(range(len(wt_utils.get_component_list(self.shape))))
                mIndexArray = om2.MIntArray()
                for index in index_list:
                    mIndexArray.append(index)

            weight_list = [0 for x in range(len(index_list))]
            items = list(weight_dict.items())
            for index, (pos, wt) in items:
                weight_list[index] = wt

            clamped_weight_list = [min(max(0, weight), 1) for weight in weight_list]
            color_list = [[rgb * x for rgb in color_vector_list[i]] for x in clamped_weight_list]
            all_color_list.append(color_list)

        color_list = [[sum(x) for x in zip(*index_color_list)] for index_color_list in zip(*all_color_list)]
        mColorArray = om2.MColorArray()
        mColorArray.copy(color_list)
        if cmds.nodeType(self.shape) == 'mesh':
            sel = om2.MSelectionList()
            sel.add(self.shape)
            shape_mObject = sel.getDependNode(0)
            mFnMesh = om2.MFnMesh(shape_mObject)
            mFnMesh.displayColors = True
            mFnMesh.setVertexColors(mColorArray, mIndexArray)
        else:
            return
        return

    def clear_weights(self):
        if not self.shape:
            return
        if cmds.objExists(self.shape):
            if cmds.nodeType(self.shape) == 'mesh':
                vert_color_node = [node for node in cmds.listHistory(self.shape) if cmds.nodeType(node) == 'polyColorPerVertex']
                if vert_color_node != []:
                    cmds.delete(vert_color_node[0])
            else:
                if cmds.nodeType(self.shape) == 'nurbsCurve':
                    return
                else:
                    if cmds.nodeType(self.shape) == 'nurbsSurface':
                        return
                    if cmds.nodeType(self.shape) == 'lattice':
                        return
                    return

        return

    def update_selected_deformer(self):
        for item in self.blendShape_treeWidget.selectedItems():
            item.setSelected(False)

        self.selected_wtHolder_list = self.deformer_treeWidget.selectedItems()
        if self.display_selected_weights == True:
            self.update_displayed_weights()
        return

    def update_selected_blendShape(self):
        for item in self.deformer_treeWidget.selectedItems():
            item.setSelected(False)

        self.selected_wtHolder_list = self.blendShape_treeWidget.selectedItems()
        if self.display_selected_weights == True:
            self.update_displayed_weights()
        return

    def update_displayed_weights(self):
        self.clear_weights()
        if self.selected_wtHolder_list:
            display_weights = False
            if type(self.selected_wtHolder_list[0]) == deformer_treeWidgetItem and self.display_deformer_weights_checkBox.isChecked():
                display_weights = True
            if type(self.selected_wtHolder_list[0]) == blendShape_treeWidgetItem and self.display_blendShape_weights_checkBox.isChecked():
                display_weights = True
            if display_weights:
                weight_dict_list = [item.get_weights(self.position_list) for item in self.selected_wtHolder_list]
                weight_dict_list = [weight for weight in weight_dict_list if weight]
                if weight_dict_list != []:
                    self.display_weights(weight_dict_list)
        return

    def create_rightClicked_menus(self, type):
        self.weight_function_menu = QMenu('Modify Weights')
        menu_item = self.weight_function_menu.addAction('Paint Weights')
        menu_item.triggered.connect(self.paint_weights)
        if type in ('deformer', 'blendShape'):
            menu_item = self.weight_function_menu.addAction('Sculpt Weights')
            menu_item.triggered.connect(self.drag_weights)
        menu_item = self.weight_function_menu.addAction('Copy Weights')
        menu_item.triggered.connect(self.copy_weights)
        menu_item = self.weight_function_menu.addAction('Paste Weights')
        menu_item.triggered.connect(self.paste_weights)
        self.weight_function_menu.addSeparator()
        symm_menu = QMenu('Symmetrisize Weights')
        self.weight_function_menu.addMenu(symm_menu)
        menu_item = symm_menu.addAction('Symmetrisize Over Axis')
        menu_item.triggered.connect(self.symmetrisize_weights_over_axis)
        menu_item = symm_menu.addAction('Symmetrisize Over Plane')
        menu_item.triggered.connect(self.start_symmetrisize_weights_with_plane)
        split_subMenu = QMenu('Split Weights')
        self.weight_function_menu.addMenu(split_subMenu)
        menu_item = split_subMenu.addAction('Split At Coordinate')
        menu_item.triggered.connect(self.start_split_weights_at_coordinate)
        menu_item = split_subMenu.addAction('Split With Surface')
        menu_item.triggered.connect(self.start_split_weights_with_surface)
        menu_item = split_subMenu.addAction('Split Radially')
        menu_item.triggered.connect(self.start_split_weights_radially)
        menu_item = split_subMenu.addAction('Split Along Curve')
        menu_item.triggered.connect(self.start_split_weights_along_curve)
        menu_item = split_subMenu.addAction('Split Along Surface')
        menu_item.triggered.connect(self.start_split_weights_along_surface)
        flip_subMenu = QMenu('Flip Weights')
        self.weight_function_menu.addMenu(flip_subMenu)
        menu_item = flip_subMenu.addAction('Flip Over Axis')
        menu_item.triggered.connect(self.flip_weights_over_axis)
        menu_item = flip_subMenu.addAction('Flip At Coordinate')
        menu_item.triggered.connect(self.start_flip_weights_over_coordinate)
        menu_item = flip_subMenu.addAction('Flip Over Plane')
        menu_item.triggered.connect(self.start_flip_weights_with_plane)
        menu_item = self.weight_function_menu.addAction('Invert Weights')
        menu_item.triggered.connect(self.invert_weights)
        self.weight_function_menu.addSeparator()
        menu_item = self.weight_function_menu.addAction('Add Copied Weights')
        menu_item.triggered.connect(self.add_copied_weights)
        menu_item = self.weight_function_menu.addAction('Subtract Copied Weights')
        menu_item.triggered.connect(self.subtract_copied_weights)
        menu_item = self.weight_function_menu.addAction('Multiply By Copied Weights')
        menu_item.triggered.connect(self.multiply_by_copied_weights)
        menu_item = self.weight_function_menu.addAction('Normalize Selected Weights')
        menu_item.triggered.connect(self.normalize_weights)
        self.weight_function_menu.addSeparator()
        menu_item = self.weight_function_menu.addAction('Save Weights')
        menu_item.triggered.connect(self.save_weights)
        menu_item = self.weight_function_menu.addAction('Load Weights')
        menu_item.triggered.connect(self.load_weights)
        if type == 'deformer':
            self.weight_function_menu.addSeparator()
            menu_item = self.weight_function_menu.addAction('Copy Soft Selection As Weights')
            menu_item.triggered.connect(self.copy_softselect)
            menu_item = self.weight_function_menu.addAction('Copy Wire As Weights')
            menu_item.triggered.connect(self.copy_wire)
            menu_item = self.weight_function_menu.addAction('Copy SoftMod As Weights')
            menu_item.triggered.connect(self.copy_softMod)
        self.delta_function_menu = QMenu('Modify Deltas')
        menu_item = self.delta_function_menu.addAction('Copy Deltas')
        menu_item.triggered.connect(self.copy_deltas)
        menu_item = self.delta_function_menu.addAction('Paste Deltas')
        menu_item.triggered.connect(self.paste_deltas)
        self.delta_function_menu.addSeparator()
        self.symm_delta_function_menu = QMenu('Symmetrisize Deltas')
        self.delta_function_menu.addMenu(self.symm_delta_function_menu)
        menu_item = self.symm_delta_function_menu.addAction('Symmetrisize Deltas Over Axis')
        menu_item.setIconText('Split Over Axis')
        menu_item.triggered.connect(self.symmetrisize_deltas_over_axis)
        menu_item = self.symm_delta_function_menu.addAction('Symmetrisize Deltas Over Plane')
        menu_item.setIconText('Split Over Plane')
        menu_item.triggered.connect(self.start_symmetrisize_deltas_with_plane)
        self.split_deltas_subMenu = QMenu('Split Deltas')
        menu_item = self.split_deltas_subMenu.addAction('Split Deltas At Coordinate')
        menu_item.setIconText('Split At Coordinate')
        menu_item.triggered.connect(self.start_split_deltas_at_coordinate)
        menu_item = self.split_deltas_subMenu.addAction('Split Deltas With Surface')
        menu_item.setIconText('Split With Surface')
        menu_item.triggered.connect(self.start_split_deltas_with_surface)
        menu_item = self.split_deltas_subMenu.addAction('Split Deltas Radially')
        menu_item.setIconText('Split Radially')
        menu_item.triggered.connect(self.start_split_deltas_radially)
        menu_item = self.split_deltas_subMenu.addAction('Split Deltas Along Curve')
        menu_item.setIconText('Split Along Curve')
        menu_item.triggered.connect(self.start_split_deltas_along_curve)
        menu_item = self.split_deltas_subMenu.addAction('Split Deltas Along Surface')
        menu_item.setIconText('Split Along Surface')
        menu_item.triggered.connect(self.start_split_deltas_along_surface)
        menu_item = self.delta_function_menu.addMenu(self.split_deltas_subMenu)
        self.flip_deltas_subMenu = QMenu('Flip Deltas')
        menu_item = self.flip_deltas_subMenu.addAction('Flip Deltas Over Axis')
        menu_item.setIconText('Flip Over Axis')
        menu_item.triggered.connect(self.flip_deltas_over_axis)
        menu_item = self.flip_deltas_subMenu.addAction('Flip Deltas Over Coordinate')
        menu_item.setIconText('Flip Over Coordinate')
        menu_item.triggered.connect(self.start_flip_deltas_over_coordinate)
        menu_item = self.flip_deltas_subMenu.addAction('Flip Deltas With Plane')
        menu_item.setIconText('Flip Over Plane')
        menu_item.triggered.connect(self.start_flip_deltas_with_plane)
        menu_item = self.delta_function_menu.addMenu(self.flip_deltas_subMenu)
        self.delta_function_menu.addSeparator()
        menu_item = self.delta_function_menu.addAction('Add Copied Deltas')
        menu_item = menu_item.triggered.connect(self.add_copied_deltas)
        menu_item = self.delta_function_menu.addAction('Subtract Copied Deltas')
        menu_item.triggered.connect(self.subtract_copied_deltas)
        self.delta_function_menu.addSeparator()
        menu_item = self.delta_function_menu.addAction('Clear Deltas')
        menu_item.triggered.connect(self.clear_deltas)
        menu_item = self.delta_function_menu.addAction('Swap Deltas')
        menu_item.triggered.connect(self.swap_deltas)
        menu_item = self.delta_function_menu.addAction('Bake Weights')
        menu_item.triggered.connect(self.bake_weights)
        self.delta_function_menu.addSeparator()
        menu_item = self.delta_function_menu.addAction('Save Deltas')
        menu_item.triggered.connect(self.save_deltas)
        menu_item = self.delta_function_menu.addAction('Load Deltas')
        menu_item.triggered.connect(self.load_deltas)
        self.delta_function_menu.addSeparator()
        menu_item = self.delta_function_menu.addAction('Create Flipped Target')
        menu_item.triggered.connect(self.create_flipped_target)
        menu_item = self.delta_function_menu.addAction('Update Flipped Target')
        menu_item.triggered.connect(self.update_flipped_target)
        menu_item = self.delta_function_menu.addAction('Duplicate Target')
        menu_item.triggered.connect(self.duplicate_target)
        menu_item = self.delta_function_menu.addAction('Add In-Between At Current Weight')
        menu_item.triggered.connect(self.add_inBetween)
        menu_item = self.delta_function_menu.addAction('Extract Target')
        menu_item.triggered.connect(self.extract_target)
        menu_item = self.delta_function_menu.addAction('Add New Target')
        menu_item.triggered.connect(self.add_new_target)
        menu_item = self.delta_function_menu.addAction('Delete Target')
        menu_item.triggered.connect(self.delete_target)
        menu_item = self.delta_function_menu.addAction('Replace Target With Posed Shape')
        menu_item.triggered.connect(self.replace_with_posed_target)
        menu_item = self.delta_function_menu.addAction('Replace Target With Default Shape')
        menu_item.triggered.connect(self.replace_target_with_default_shape)
        menu_item = self.delta_function_menu.addAction('Add Selected Shape As Posed Target')
        menu_item.triggered.connect(self.add_selection_as_posed_target)
        menu_item = self.delta_function_menu.addAction('Add Selected Shape As Default Target')
        menu_item.triggered.connect(self.add_selection_as_default_target)
        if type == 'deformer':
            self.deformerSet_functions_menu = QMenu('Modify DeformerSet')
            self.weight_function_menu.addMenu(self.deformerSet_functions_menu)
            menu_item = self.deformerSet_functions_menu.addAction('Select DeformerSet')
            menu_item.triggered.connect(self.select_deformerSet)
            menu_item = self.deformerSet_functions_menu.addAction('Edit DeformerSet')
            menu_item.triggered.connect(self.edit_deformerSet)
            menu_item = self.deformerSet_functions_menu.addAction('Copy DeformerSet')
            menu_item.triggered.connect(self.copy_deformerSet)
            menu_item = self.deformerSet_functions_menu.addAction('Paste DeformerSet')
            menu_item.triggered.connect(self.paste_deformerSet)
            menu_item = self.deformerSet_functions_menu.addAction('Set DeformerSet To Selection')
            menu_item.triggered.connect(self.set_deformerSet)
            menu_item = self.deformerSet_functions_menu.addAction('Add Selection To DeformerSet')
            menu_item.triggered.connect(self.add_deformerSet)
            menu_item = self.deformerSet_functions_menu.addAction('Symmetrize DeformerSet')
            menu_item.triggered.connect(self.symm_deformerSet)
        return

    def select_deformerSet(self):
        if len(self.selected_wtHolder_list) > 0:
            each_deformer = self.selected_wtHolder_list[-1].node
            deformerSet = _deformer_set_of(each_deformer)
            if not deformerSet:
                return
            cmds.select(deformerSet)
        return

    def edit_deformerSet(self):
        if len(self.selected_wtHolder_list) > 0:
            each_deformer = self.selected_wtHolder_list[-1].node
            deformerSet = _deformer_set_of(each_deformer)
            if not deformerSet:
                return
            cmds.select(each_deformer)
            cmds.setToolTo('setEditContext')
        return

    def add_deformerSet(self):
        if len(self.selected_wtHolder_list) > 0:
            each_deformer = self.selected_wtHolder_list[-1].node
            deformerSet = _deformer_set_of(each_deformer)
            if not deformerSet:
                return
            cmds.sets(cmds.ls(sl=True), add=deformerSet)
            if cmds.nodeType(each_deformer) == 'translateUVN':
                cmds.translateUVN(self.shape, rebind=each_deformer)
        return

    def copy_deformerSet(self):
        if len(self.selected_wtHolder_list) > 0:
            self.clipboard_deformerSet = self.selected_wtHolder_list[-1].get_deformerSet()
            self.clipboard_shape = self.shape
            self.clipboard_shape_data = wt_utils.get_shape_data(self.shape)
        return

    def set_deformerSet(self):
        true_sel = get_true_sel(self.shape)
        if not true_sel:
            return
        for each_wtHolder in self.selected_wtHolder_list:
            each_wtHolder.set_deformerSet(wt_utils.get_index_list(true_sel))

        return

    def paste_deformerSet(self):
        if self.shape == self.clipboard_shape:
            for each_wtHolder in self.selected_wtHolder_list:
                each_wtHolder.set_deformerSet(self.clipboard_deformerSet)

        return

    def symm_deformerSet(self):
        ii_dict = None
        for each_wtHolder in self.selected_wtHolder_list:
            deformerSet_ids = each_wtHolder.get_deformerSet()
            symmed_ids, ii_dict = wt_utils.symmetrize_deformerSet(deformerSet_ids, self.shape, ii_dict=ii_dict, axis=self.axis, direction=self.direction, symm_coordinate=0)
            each_wtHolder.set_deformerSet(symmed_ids)

        return

    def deformer_list_rightClicked(self, QPos):
        self.create_rightClicked_menus(type='deformer')
        self.deformer_RC_menu = self.weight_function_menu
        parentPosition = self.deformer_treeWidget.mapToGlobal(QPoint(0, 0))
        self.deformer_RC_menu.move(parentPosition + QPos)
        self.deformer_RC_menu.show()
        return

    def blendShape_list_rightClicked(self, QPos):
        self.create_rightClicked_menus(type='blendShape')
        self.blendShape_RC_menu = QMenu()
        self.blendShape_RC_menu.addMenu(self.weight_function_menu)
        self.blendShape_RC_menu.addMenu(self.delta_function_menu)
        parentPosition = self.blendShape_treeWidget.mapToGlobal(QPoint(0, 0))
        self.blendShape_RC_menu.move(parentPosition + QPos)
        self.blendShape_RC_menu.show()
        return

    def split_table_rightClicked(self, QPos):
        self.split_table_menu = QMenu()
        remove_action = self.split_table_menu.addAction('Remove')
        remove_action.triggered.connect(self.remove_splitTableWidgeItem)
        parentPosition = self.split_target_tableWidget.mapToGlobal(QPoint(0, 0))
        self.split_table_menu.move(parentPosition + QPos)
        self.split_table_menu.show()
        return

    def remove_splitTableWidgeItem(self):
        for item in self.split_target_tableWidget.selectedItems():
            row = item.row()
            column = item.column()
            if self.split_target_tableWidget.drop_accept_type == 'weight':
                item.set_weights(item.start_weights)
            elif self.split_target_tableWidget.drop_accept_type == 'delta':
                item.set_deltas(item.start_deltas)
            self.split_target_tableWidget.setItem(row, column, None)

        self.split_target_tableWidget.drop_update_function()
        return

    def restore_preSplit_weights(self):
        for column_num in range(self.split_target_tableWidget.columnCount() + 1):
            for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                target_item = self.split_target_tableWidget.item(row_num, column_num)
                if target_item:
                    target_item.set_weights(target_item.start_weights)

        for wtHolder, wt in zip(self.active_wtHolder_list, self.start_weights_list):
            wtHolder.set_weights(wt)

        return

    def paint_weights(self):
        if len(self.selected_wtHolder_list) == 0:
            return
        paint_deformer = self.selected_wtHolder_list[-1].node
        paint_deformer_type = cmds.nodeType(paint_deformer)
        if self.selected_wtHolder_list[-1].item_type == 'deformer':
            if not self.selected_wtHolder_list[-1].plug:
                mel.eval(('artSetToolAndSelectAttr( "artAttrCtx", "{}.{}.weights")').format(paint_deformer_type, paint_deformer))
            else:
                paint_attr = self.selected_wtHolder_list[-1].plug.elementByLogicalIndex(0).child(0).name().split('.')[-1]
                cmds.makePaintable(cmds.nodeType(self.selected_wtHolder_list[-1].plug.name().split('.')[0]), paint_attr, at='multiFloat', sm='deformer')
                mel.eval(('artSetToolAndSelectAttr( "artAttrCtx", "{}.{}.{}")').format(paint_deformer_type, paint_deformer, paint_attr))
        else:
            mel.eval(('artSetToolAndSelectAttr( "artAttrCtx", "{}.{}.baseWeights")').format(paint_deformer_type, paint_deformer))
            mel.eval(('artBlendShapeSelectTarget artAttrCtx "{}"').format(paint_deformer))
            if self.selected_wtHolder_list[-1].target_name:
                mel.eval(('artBlendShapeSelectTarget artAttrCtx "{}"').format(self.selected_wtHolder_list[-1].target_name))
        true_sel = get_true_sel(self.shape)
        if not true_sel:
            cmds.select(self.shape)
        return

    def drag_weights(self):
        if len(self.selected_wtHolder_list) == 0:
            return
        paint_deformer = self.selected_wtHolder_list[-1].node
        paint_deformer_type = cmds.nodeType(paint_deformer)
        # FIX: load the plug-in / make a context if needed (the original then called setToolTo "").
        if not cmds.pluginInfo('weightSculpt', q=True, loaded=True):
            try:
                cmds.loadPlugin('weightSculpt', quiet=True)
            except RuntimeError:
                cmds.warning('The weightSculpt plug-in is not installed')
                return
        i = 1
        while cmds.contextInfo(('weightSculptContext{}').format(i), exists=True):
            i += 1

        if i == 1:
            self.sculptContext = cmds.weightSculptContext()
        else:
            self.sculptContext = ('weightSculptContext{}').format(i - 1)
        if self.selected_wtHolder_list[-1].item_type == 'deformer':
            if not self.selected_wtHolder_list[-1].plug:
                mel.eval(('setToolTo {}').format(self.sculptContext))
                cmds.weightSculptContext(self.sculptContext, e=True, wtm='default', deformer=paint_deformer)
            else:
                cmds.setToolTo(self.sculptContext)
                plug_name = self.selected_wtHolder_list[-1].plug.elementByLogicalIndex(-1).child(0).partialName()
                plug_name = plug_name.split('.')[-1]
                cmds.weightSculptContext(self.sculptContext, e=True, wtm='plug', deformer=paint_deformer, plug=plug_name)
        if self.selected_wtHolder_list[-1].item_type == 'blendShape':
            if not self.selected_wtHolder_list[-1].target_name:
                cmds.setToolTo(self.sculptContext)
                cmds.weightSculptContext(self.sculptContext, e=True, wtm='blendShapeBase', deformer=paint_deformer)
            else:
                cmds.setToolTo(self.sculptContext)
                cmds.weightSculptContext(self.sculptContext, e=True, wtm='blendShapeTarget', deformer=paint_deformer, t=self.selected_wtHolder_list[-1].target_index)
        return

    def copy_weights(self):
        if len(self.selected_wtHolder_list) > 0:
            self.clipboard_weights = self.selected_wtHolder_list[-1].get_weights(self.position_list)
            self.clipboard_shape = self.shape
            self.clipboard_shape_data = wt_utils.get_shape_data(self.shape)
        return

    def paste_weights(self):
        if self.clipboard_weights and self.selected_wtHolder_list:
            if self.shape == self.clipboard_shape:
                if len(self.clipboard_weights) == len(self.position_list):
                    for selected_deformer in self.selected_wtHolder_list:
                        selected_deformer.set_weights(self.clipboard_weights)

                else:
                    source_ip_dictionary = wt_utils.convert_weightDelta_dictionary_to_index_position_dictionary(self.clipboard_weights)
                    destination_ip_dictionary = wt_utils.convert_shape_to_index_position_dictionary(self.shape)
                    paste_ii_dict = wt_utils.match_points_to_closest_point(source_ip_dictionary, destination_ip_dictionary)
                    matched_weights = wt_utils.apply_ii_dictionary_to_weight_dictionary({}, self.clipboard_weights, paste_ii_dict)
                    for selected_deformer in self.selected_wtHolder_list:
                        selected_deformer.set_weights(matched_weights)

            elif self.matching_method == 'closestPointOnSurface':
                if self.clipboard_shape_data[-1] == 'mesh':
                    if cmds.objExists(self.clipboard_shape):
                        matched_weights, extra_dict = wt_utils.match_weights_to_shape(self.clipboard_weights, self.shape, matching_method='closestPointOnSurface', source_shape=self.clipboard_shape)
                    else:
                        new_shape = wt_utils.create_shape_from_data(self.clipboard_shape_data)
                        matched_weights, extra_dict = wt_utils.match_weights_to_shape(self.clipboard_weights, self.shape, matching_method='closestPointOnSurface', source_shape=new_shape)
                        cmds.delete(cmds.listRelatives(new_shape, p=True)[0])
                    for selected_deformer in self.selected_wtHolder_list:
                        selected_deformer.set_weights(matched_weights)

                else:
                    cmds.warning('"closestPointOnsurface" matching_method only works when the source_shape is a mesh')
            elif self.matching_method == 'closestComponentUV':
                if cmds.nodeType(self.clipboard_shape) == 'mesh' and cmds.nodeType(self.shape) == 'mesh':
                    matched_weights, extra_dict = wt_utils.match_weights_to_shape(self.clipboard_weights, self.shape, matching_method='closestComponentUV', source_shape=self.clipboard_shape)
                    for selected_deformer in self.selected_wtHolder_list:
                        selected_deformer.set_weights(matched_weights)

            elif self.matching_method == 'closestComponent':
                matched_weights, extra_dict = wt_utils.match_weights_to_shape(self.clipboard_weights, self.shape, matching_method='closestComponent', source_shape=self.clipboard_shape)
                for selected_deformer in self.selected_wtHolder_list:
                    selected_deformer.set_weights(matched_weights)

            self.update_displayed_weights()
        return

    def symmetrisize_weights_over_axis(self):
        if self.matching_method == 'closestComponent':
            ii_dict = None
            stored_attr = ('{}_{}_{}_{}').format('symm', self.axis, self.direction_short, 'ii')
            stored_dict = False
            if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                stored_dict = True
            for selected_deformer in self.selected_wtHolder_list:
                wts = selected_deformer.get_weights(self.position_list)
                symm_wts, ii_dict = wt_utils.symmetrisize_weights(wts, symm_coordinate=0, axis=self.axis, direction=self.direction, matching_method=self.matching_method, source_shape=None, ii_dict=ii_dict, ibw_dict=None)
                selected_deformer.set_weights(symm_wts)

            if not stored_dict:
                cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
        elif self.matching_method == 'closestPointOnSurface':
            if cmds.nodeType(self.shape) == 'mesh':
                ibw_dict = None
                stored_attr = ('{}_{}_{}_{}').format('symm', self.axis, self.direction_short, 'ibw')
                stored_dict = False
                if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                    ibw_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                    stored_dict = True
                for selected_deformer in self.selected_wtHolder_list:
                    wts = selected_deformer.get_weights(self.position_list)
                    symm_wts, ibw_dict = wt_utils.symmetrisize_weights(wts, symm_coordinate=0, axis=self.axis, direction=self.direction, matching_method=self.matching_method, source_shape=self.shape, ii_dict=None, ibw_dict=ibw_dict)
                    selected_deformer.set_weights(symm_wts)

                if not stored_dict:
                    cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                    cmds.setAttr(self.shape + '.' + stored_attr, str(ibw_dict), type='string')
            else:
                cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
        elif self.matching_method == 'closestComponentUV':
            if cmds.nodeType(self.shape) == 'mesh':
                ii_dict = None
                stored_attr = ('{}_{}_{}_{}').format('symm', self.axis, self.direction_short, 'ii')
                stored_dict = False
                if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                    ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                    stored_dict = True
                for selected_deformer in self.selected_wtHolder_list:
                    wts = selected_deformer.get_weights(self.position_list)
                    symm_wts, ii_dict = wt_utils.symmetrisize_weights(wts, symm_coordinate=0.5, axis=self.axis, uv_axis=self.uv_axis, direction=self.direction, matching_method=self.matching_method, source_shape=self.shape, ii_dict=ii_dict, ibw_dict=None)
                    selected_deformer.set_weights(symm_wts)

                if not stored_dict:
                    cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                    cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
                self.update_displayed_weights()
            else:
                cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')
        self.update_displayed_weights()
        return

    def start_symmetrisize_weights_with_plane(self):
        self.active_wtHolder_list = [x for x in self.selected_wtHolder_list if not x.inBetween_name]
        if len(self.active_wtHolder_list) == 0:
            return
        self.active_start_weights = self.active_wtHolder_list[0].get_weights(self.position_list)
        self.highlight_selected_wtHolders()
        self.selection_off()
        self.display_selected_weights = False
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.loaded_object_label.setText('Symm Surface')
        self.object_type = 'nurbsSurface'
        self.confirm_button.clicked.connect(self.confirm_symmetrisize_weights_with_plane)
        self.cancel_button.clicked.connect(self.cancel_symmetrisize_weights_with_plane)
        self.load_object_button.clicked.connect(self.update_symmetrisize_weights_with_plane)
        self.refresh_object_button.clicked.connect(self.update_symmetrisize_weights_with_plane)
        self.c.direction_updated.connect(self.update_symmetrisize_weights_with_plane)
        self.c.match_method_updated.connect(self.update_symmetrisize_weights_with_plane)
        self.cancel_function = self.cancel_symmetrisize_weights_with_plane
        self.update_symmetrisize_weights_with_plane()
        return

    def update_symmetrisize_weights_with_plane(self):
        if cmds.objExists(self.loaded_object):
            sel = om2.MSelectionList()
            sel.add(self.loaded_object)
            mDagPath = sel.getDagPath(0)
            objMatrix = mDagPath.inclusiveMatrix()
            mFn = om2.MFnNurbsSurface(mDagPath)
            if self.matching_method == 'closestComponent':
                symm_wts, self.ii_dict = wt_utils.symmetrisize_weights_with_plane(self.active_start_weights, plane_position=tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3], plane_normal=tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3], direction=self.direction, matching_method='closestComponent', source_shape=None, max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled(), ii_dict=None, ibw_dict=None)
            elif self.matching_method == 'closestComponentUV':
                cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')
            elif self.matching_method == 'closestPointOnSurface':
                if cmds.nodeType(self.shape) == 'mesh':
                    symm_wts, self.ibw_dict = wt_utils.symmetrisize_weights_with_plane(self.active_start_weights, plane_position=tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3], plane_normal=tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3], direction=self.direction, matching_method='closestPointOnSurface', max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled(), source_shape=self.shape, ii_dict=None, ibw_dict=None)
                else:
                    cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
            self.active_wtHolder_list[0].set_weights(symm_wts)
            self.display_weights([symm_wts])
        return

    def confirm_symmetrisize_weights_with_plane(self):
        self.update_symmetrisize_weights_with_plane()
        if cmds.objExists(self.loaded_object):
            sel = om2.MSelectionList()
            sel.add(self.loaded_object)
            mDagPath = sel.getDagPath(0)
            objMatrix = mDagPath.inclusiveMatrix()
            mFn = om2.MFnNurbsSurface(mDagPath)
            if self.matching_method == 'closestComponent':
                for wtHolder in self.active_wtHolder_list[1:]:
                    self.ii_dict, symm_wts = symmetrisize_weights_with_plane(self.active_start_weights, plane_position=tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3], plane_normal=tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3], direction=self.direction, matching_method='closestComponent', source_shape=None, max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled(), ii_dict=self.ii_dict, ibw_dict=None)
                    self.active_wtHolder_list[0].set_weights(symm_wts)

            elif self.matching_method == 'closestComponentUV':
                if cmds.nodeType(self.shape) == 'mesh':
                    for wtHolder in self.active_wtHolder_list[1:]:
                        self.ii_dict, symm_wts = symmetrisize_weights_with_plane(self.active_start_weights, plane_position=tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3], plane_normal=tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3], direction=self.direction, matching_method='closestComponentUV', source_shape=self.shape, max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled(), ii_dict=self.ii_dict, ibw_dict=None)
                        self.active_wtHolder_list[0].set_weights(symm_wts)

                else:
                    cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')
            elif self.matching_method == 'closestPointOnSurface':
                if cmds.nodeType(self.shape) == 'mesh':
                    for wtHolder in self.active_wtHolder_list[1:]:
                        self.ii_dict, symm_wts = symmetrisize_weights_with_plane(self.active_start_weights, plane_position=tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3], plane_normal=tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3], direction=self.direction, matching_method='closestPointOnSurface', source_shape=self.shape, max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled(), ii_dict=None, ibw_dict=self.ibw_dict)
                        self.active_wtHolder_list[0].set_weights(symm_wts)

                else:
                    cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
        self.selection_on()
        self.unhighlight_wtHolders()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.confirm_button.clicked.disconnect(self.confirm_symmetrisize_weights_with_plane)
        self.cancel_button.clicked.disconnect(self.cancel_symmetrisize_weights_with_plane)
        self.c.direction_updated.disconnect(self.update_symmetrisize_weights_with_plane)
        self.c.match_method_updated.disconnect(self.update_symmetrisize_weights_with_plane)
        self.load_object_button.clicked.disconnect(self.update_symmetrisize_weights_with_plane)
        self.refresh_object_button.clicked.disconnect(self.update_symmetrisize_weights_with_plane)
        self.update_displayed_weights()
        self.cancel_function = None
        return

    def cancel_symmetrisize_weights_with_plane(self):
        self.active_wtHolder_list[0].set_weights(self.active_start_weights)
        self.selection_on()
        self.unhighlight_wtHolders()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.confirm_button.clicked.disconnect(self.confirm_symmetrisize_weights_with_plane)
        self.cancel_button.clicked.disconnect(self.cancel_symmetrisize_weights_with_plane)
        self.c.direction_updated.disconnect(self.update_symmetrisize_weights_with_plane)
        self.c.match_method_updated.disconnect(self.update_symmetrisize_weights_with_plane)
        self.load_object_button.clicked.disconnect(self.update_symmetrisize_weights_with_plane)
        self.refresh_object_button.clicked.disconnect(self.update_symmetrisize_weights_with_plane)
        self.update_displayed_weights()
        self.cancel_function = None
        return

    def start_split_weights_at_coordinate(self):
        self.active_wtHolder_list = [x for x in self.selected_wtHolder_list if not x.inBetween_name]
        if not self.active_wtHolder_list:
            return
        self.start_weights_list = [x.get_weights(self.position_list) for x in self.active_wtHolder_list]
        self.rightClick_off()
        self.display_selected_weights = False
        self.falloff_parentWidget.setVisible(True)
        self.coordinate_parentWidget.setVisible(True)
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.split_table_lower_widget.setVisible(True)
        self.split_target_tableWidget.drop_accept_type = 'weight'
        self.split_target_tableWidget.setRowCount(2)
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.name for x in self.active_wtHolder_list])
        self.coordinate_label.setText('Split Coordinate')
        self.falloff_label.setText('Falloff Distance')
        pos_list = [x[1][0] for x in list(self.start_weights_list[0].items())]
        pos_list = [pos for tuple in pos_list for pos in tuple]
        self.coordinate_slider.setMinimum(100 * min(pos_list))
        self.coordinate_slider.setMaximum(100 * max(pos_list))
        self.coordinate_field.setMinimum(min(pos_list))
        self.coordinate_field.setMaximum(max(pos_list))
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(100 * (max(pos_list) - min(pos_list)))
        self.confirm_button.clicked.connect(self.confirm_split_weights_at_coordinate)
        self.cancel_button.clicked.connect(self.cancel_split_weights_at_coordinate)
        self.falloff_slider.valueChanged.connect(self.update_split_weights_at_coordinate)
        self.coordinate_slider.valueChanged.connect(self.update_split_weights_at_coordinate)
        self.c.axis_updated.connect(self.update_split_weights_at_coordinate)
        self.split_target_tableWidget.drop_update_function = self.update_split_weights_at_coordinate
        self.cancel_function = self.cancel_symmetrisize_weights_with_plane
        self.update_split_weights_at_coordinate()
        return

    def update_split_weights_at_coordinate(self):
        mask_weights = []
        used_node_list = []
        for column_num, start_weights in enumerate(self.start_weights_list):
            if mask_weights != []:
                split_dict_list = [wt_utils.multiply_weights(start_weights, mask_wt) for mask_wt in mask_weights]
            else:
                split_dict_list, mask_weights = wt_utils.split_weights(start_weights.copy(), self.coordinate_field.value(), axis=self.axis, falloff_distance=self.falloff_field.value())
            for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                target_item = self.split_target_tableWidget.item(row_num, column_num)
                if target_item:
                    if target_item.node not in used_node_list:
                        target_item.set_weights(split_dict_list[row_num])
                        used_node_list.append(target_item.node)
                    else:
                        wts = target_item.get_weights(self.position_list)
                        sum_wts = wt_utils.add_weights(split_dict_list[row_num], wts)
                        target_item.set_weights(sum_wts)

        last_weight_dict = mask_weights.pop(0)
        mask_weights.append(last_weight_dict)
        self.display_weights(mask_weights)
        return

    def confirm_split_weights_at_coordinate(self):
        self.update_split_weights_at_coordinate()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.split_target_tableWidget.empty()
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_at_coordinate)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_at_coordinate)
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_at_coordinate)
        self.coordinate_slider.valueChanged.disconnect(self.update_split_weights_at_coordinate)
        self.c.axis_updated.disconnect(self.update_split_weights_at_coordinate)
        self.cancel_function = None
        return

    def cancel_split_weights_at_coordinate(self):
        self.restore_preSplit_weights()
        self.split_target_tableWidget.empty()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_at_coordinate)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_at_coordinate)
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_at_coordinate)
        self.coordinate_slider.valueChanged.disconnect(self.update_split_weights_at_coordinate)
        self.c.axis_updated.disconnect(self.update_split_weights_at_coordinate)
        self.cancel_function = None
        return

    def start_split_weights_with_surface(self):
        if len(self.selected_wtHolder_list) == 0:
            return
        self.active_wtHolder_list = self.selected_wtHolder_list
        self.rightClick_off()
        self.display_selected_weights = False
        self.falloff_parentWidget.setVisible(True)
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.split_table_lower_widget.setVisible(True)
        self.split_target_tableWidget.drop_accept_type = 'weight'
        self.split_target_tableWidget.setRowCount(2)
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.name for x in self.active_wtHolder_list])
        self.start_weights_list = [x.get_weights(self.position_list) for x in self.active_wtHolder_list]
        self.loaded_object_label.setText('Split Surface')
        self.falloff_label.setText('Falloff Distance')
        self.falloff_label.setText('Falloff Distance')
        self.object_type = 'nurbsSurface'
        self.confirm_button.clicked.connect(self.confirm_split_weights_with_surface)
        self.cancel_button.clicked.connect(self.cancel_split_weights_with_surface)
        self.falloff_slider.valueChanged.connect(self.update_split_weights_with_surface)
        self.load_object_button.clicked.connect(self.update_split_weights_with_surface)
        self.refresh_object_button.clicked.connect(self.update_split_weights_with_surface)
        self.split_target_tableWidget.drop_update_function = self.update_split_weights_with_surface
        pos_list = [x[1][0] for x in list(self.start_weights_list[0].items())]
        pos_list = [item for sublist in pos_list for item in sublist]
        pos_list = [abs(x) for x in pos_list]
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(200 * max(pos_list))
        self.update_split_weights_with_surface()
        return

    def update_split_weights_with_surface(self):
        if cmds.objExists(self.loaded_object):
            used_node_list = []
            mask_weights = []
            for column_num, start_weights in enumerate(self.start_weights_list):
                if mask_weights != []:
                    split_dict_list = [wt_utils.multiply_weights(start_weights, mask_wt) for mask_wt in mask_weights]
                else:
                    split_dict_list, mask_weights = wt_utils.split_weights_with_surface(start_weights, self.loaded_object, falloff_distance=self.falloff_field.value())
                for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                    target_item = self.split_target_tableWidget.item(row_num, column_num)
                    if target_item:
                        if target_item.node not in used_node_list:
                            target_item.set_weights(split_dict_list[row_num])
                            used_node_list.append(target_item.node)
                        else:
                            wts = target_item.get_weights(self.position_list)
                            sum_wts = wt_utils.add_weights(split_dict_list[row_num], wts)
                            target_item.set_weights(sum_wts)

            last_weight_dict = mask_weights.pop(0)
            mask_weights.append(last_weight_dict)
            self.display_weights(mask_weights)
        return

    def confirm_split_weights_with_surface(self):
        self.update_split_weights_with_surface()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.split_target_tableWidget.empty()
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_with_surface)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_with_surface)
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_with_surface)
        self.load_object_button.clicked.disconnect(self.update_split_weights_with_surface)
        self.refresh_object_button.clicked.disconnect(self.update_split_weights_with_surface)
        self.cancel_function = None
        return

    def cancel_split_weights_with_surface(self):
        self.restore_preSplit_weights()
        self.split_target_tableWidget.empty()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_with_surface)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_with_surface)
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_with_surface)
        self.load_object_button.clicked.disconnect(self.update_split_weights_with_surface)
        self.refresh_object_button.clicked.disconnect(self.update_split_weights_with_surface)
        self.cancel_function = None
        return

    def start_split_weights_radially(self):
        self.active_wtHolder_list = self.selected_wtHolder_list
        self.rightClick_off()
        self.display_selected_weights = False
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.falloff_parentWidget.setVisible(True)
        self.number_parentWidget.setVisible(True)
        self.split_table_lower_widget.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.split_target_tableWidget.drop_accept_type = 'weight'
        split_number = int(self.number_field.value())
        self.split_target_tableWidget.setRowCount(len(color_vector_list))
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.name for x in self.active_wtHolder_list])
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        self.loaded_object_label.setText('Split Object')
        self.falloff_label.setText('Falloff Angle')
        self.object_type = 'transform'
        self.load_object_button_clicked()
        self.falloff_field.setMinimum(0)
        self.falloff_field.setMaximum(180)
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(18000)
        self.start_weights_list = [x.get_weights(self.position_list) for x in self.active_wtHolder_list]
        self.falloff_slider.valueChanged.connect(self.update_split_weights_radially)
        self.number_field.valueChanged.connect(self.update_split_weights_radially)
        self.confirm_button.clicked.connect(self.confirm_split_weights_radially)
        self.cancel_button.clicked.connect(self.cancel_split_weights_radially)
        self.load_object_button.clicked.connect(self.update_split_weights_radially)
        self.refresh_object_button.clicked.connect(self.update_split_weights_radially)
        self.split_target_tableWidget.drop_update_function = self.update_split_weights_radially
        self.update_split_weights_radially()
        return

    def update_split_weights_radially(self):
        split_number = int(self.number_field.value())
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        if cmds.objExists(self.loaded_object):
            mask_weights = []
            used_node_list = []
            split_object_string = self.loaded_object
            sel = om2.MSelectionList()
            sel.add(split_object_string)
            split_MMatrix = sel.getDagPath(0).inclusiveMatrix()
            for column_num, start_weights in enumerate(self.start_weights_list):
                if mask_weights != []:
                    split_dict_list = [wt_utils.multiply_weights(start_weights, mask_wt) for mask_wt in mask_weights]
                else:
                    split_dict_list, mask_weights = wt_utils.split_weights_radially(start_weights, split_MMatrix, number_of_sections=split_number, falloff_angle=self.falloff_field.value())
                for row_num in range(split_number):
                    target_item = self.split_target_tableWidget.item(row_num, column_num)
                    if target_item:
                        if target_item.node not in used_node_list:
                            target_item.set_weights(split_dict_list[row_num])
                            used_node_list.append(target_item.node)
                        else:
                            wts = target_item.get_weights(self.position_list)
                            sum_wts = wt_utils.add_weights(split_dict_list[row_num], wts)
                            target_item.set_weights(sum_wts)

            last_weight_dict = mask_weights.pop(0)
            mask_weights.append(last_weight_dict)
            self.display_weights(mask_weights)
        return

    def confirm_split_weights_radially(self):
        self.update_split_weights_radially()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_radially)
        self.number_field.valueChanged.disconnect(self.update_split_weights_radially)
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_radially)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_radially)
        self.load_object_button.clicked.disconnect(self.update_split_weights_radially)
        self.refresh_object_button.clicked.disconnect(self.update_split_weights_radially)
        self.cancel_function = None
        return

    def cancel_split_weights_radially(self):
        self.restore_preSplit_weights()
        self.split_target_tableWidget.empty()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_radially)
        self.number_field.valueChanged.disconnect(self.update_split_weights_radially)
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_radially)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_radially)
        self.load_object_button.clicked.disconnect(self.update_split_weights_radially)
        self.refresh_object_button.clicked.disconnect(self.update_split_weights_radially)
        self.cancel_function = None
        return

    def start_split_weights_along_curve(self):
        self.active_wtHolder_list = self.selected_wtHolder_list
        self.rightClick_off()
        self.display_selected_weights = False
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.falloff_parentWidget.setVisible(True)
        self.number_parentWidget.setVisible(True)
        self.split_table_lower_widget.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.split_target_tableWidget.drop_accept_type = 'weight'
        split_number = int(self.number_field.value())
        self.split_target_tableWidget.setRowCount(len(color_vector_list))
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.name for x in self.active_wtHolder_list])
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        self.loaded_object_label.setText('Split Curve')
        self.falloff_label.setText('Falloff Distance')
        self.object_type = 'nurbsCurve'
        self.load_object_button_clicked()
        self.falloff_field.setMinimum(0)
        self.falloff_field.setMaximum(10)
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(100)
        self.start_weights_list = [x.get_weights(self.position_list) for x in self.active_wtHolder_list]
        self.falloff_slider.valueChanged.connect(self.update_split_weights_along_curve)
        self.number_field.valueChanged.connect(self.update_split_weights_along_curve)
        self.confirm_button.clicked.connect(self.confirm_split_weights_along_curve)
        self.cancel_button.clicked.connect(self.cancel_split_weights_along_curve)
        self.c.curve_method_updated.connect(self.update_split_weights_along_curve)
        self.load_object_button.clicked.connect(self.update_split_weights_along_curve)
        self.refresh_object_button.clicked.connect(self.update_split_weights_along_curve)
        self.split_target_tableWidget.drop_update_function = self.update_split_weights_along_curve
        self.load_object_button_clicked()
        self.update_split_weights_radially()
        return

    def update_split_weights_along_curve(self):
        split_number = int(self.number_field.value())
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        if cmds.objExists(self.loaded_object):
            if self.curve_method == 'parameter':
                max_position = cmds.getAttr(self.loaded_object + '.minMaxValue.maxValue')
            elif self.curve_method == 'distanceAlong':
                max_position = cmds.arclen(self.loaded_object)
            else:
                max_position = 300
            self.falloff_slider.setMaximum(max_position * 100)
            used_node_list = []
            mask_weights = []
            for column_num, start_weights in enumerate(self.start_weights_list):
                if mask_weights != []:
                    split_dict_list = [wt_utils.multiply_weights(start_weights, mask_wt) for mask_wt in mask_weights]
                else:
                    split_dict_list, mask_weights = wt_utils.split_weights_along_curve(start_weights, self.loaded_object, falloff_distance=self.falloff_field.value(), split_number=int(self.number_field.value()), mode=self.curve_method)
                for row_num in range(split_number):
                    target_item = self.split_target_tableWidget.item(row_num, column_num)
                    if target_item:
                        if target_item.node not in used_node_list:
                            target_item.set_weights(split_dict_list[row_num])
                            used_node_list.append(target_item.node)
                        else:
                            wts = target_item.get_weights(self.position_list)
                            sum_wts = wt_utils.add_weights(split_dict_list[row_num], wts)
                            target_item.set_weights(sum_wts)

            last_weight_dict = mask_weights.pop(0)
            mask_weights.append(last_weight_dict)
            self.display_weights(mask_weights)
        return

    def confirm_split_weights_along_curve(self):
        self.update_split_weights_along_curve()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_along_curve)
        self.number_field.valueChanged.disconnect(self.update_split_weights_along_curve)
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_along_curve)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_along_curve)
        self.c.curve_method_updated.disconnect(self.update_split_weights_along_curve)
        self.load_object_button.clicked.disconnect(self.update_split_weights_along_curve)
        self.refresh_object_button.clicked.disconnect(self.update_split_weights_along_curve)
        self.cancel_function = None
        return

    def cancel_split_weights_along_curve(self):
        self.restore_preSplit_weights()
        for wtHolder, wt in zip(self.active_wtHolder_list, self.start_weights_list):
            wtHolder.set_weights(wt)

        self.split_target_tableWidget.empty()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_along_curve)
        self.number_field.valueChanged.disconnect(self.update_split_weights_along_curve)
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_along_curve)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_along_curve)
        self.c.curve_method_updated.disconnect(self.update_split_weights_along_curve)
        self.load_object_button.clicked.disconnect(self.update_split_weights_along_curve)
        self.refresh_object_button.clicked.disconnect(self.update_split_weights_along_curve)
        self.cancel_function = None
        return

    def start_split_weights_along_surface(self):
        self.active_wtHolder_list = self.selected_wtHolder_list
        self.rightClick_off()
        self.display_selected_weights = False
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.falloff_parentWidget.setVisible(True)
        self.number_parentWidget.setVisible(True)
        self.split_table_lower_widget.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.split_target_tableWidget.drop_accept_type = 'weight'
        split_number = int(self.number_field.value())
        self.split_target_tableWidget.setRowCount(len(color_vector_list))
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.name for x in self.active_wtHolder_list])
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        self.loaded_object_label.setText('Split Surface')
        self.falloff_label.setText('Falloff Distance')
        self.object_type = 'nurbsSurface'
        self.load_object_button_clicked()
        self.falloff_field.setMinimum(0)
        self.falloff_field.setMaximum(180)
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(300)
        self.start_weights_list = [x.get_weights(self.position_list) for x in self.active_wtHolder_list]
        self.falloff_slider.valueChanged.connect(self.update_split_weights_along_surface)
        self.number_field.valueChanged.connect(self.update_split_weights_along_surface)
        self.confirm_button.clicked.connect(self.confirm_split_weights_along_surface)
        self.cancel_button.clicked.connect(self.cancel_split_weights_along_surface)
        self.load_object_button.clicked.connect(self.update_split_weights_along_surface)
        self.c.surface_method_updated.connect(self.update_split_weights_along_surface)
        self.refresh_object_button.clicked.connect(self.update_split_weights_along_surface)
        self.split_target_tableWidget.drop_update_function = self.update_split_weights_along_surface
        self.update_split_weights_along_surface()
        return

    def update_split_weights_along_surface(self):
        split_number = int(self.number_field.value())
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        if cmds.objExists(self.loaded_object):
            mask_weights = []
            used_node_list = []
            for column_num, start_weights in enumerate(self.start_weights_list):
                if mask_weights != []:
                    split_dict_list = [wt_utils.multiply_weights(start_weights, mask_wt) for mask_wt in mask_weights]
                else:
                    split_dict_list, mask_weights = wt_utils.split_weights_along_surface(start_weights, self.loaded_object, falloff_distance=self.falloff_field.value(), split_number=int(self.number_field.value()), mode=self.surface_method)
                for row_num in range(split_number):
                    target_item = self.split_target_tableWidget.item(row_num, column_num)
                    if target_item:
                        if target_item.text() not in used_node_list:
                            target_item.set_weights(split_dict_list[row_num])
                            used_node_list.append(target_item.text())
                        else:
                            wts = target_item.get_weights(self.position_list)
                            sum_wts = wt_utils.add_weights(split_dict_list[row_num], wts)
                            target_item.set_weights(sum_wts)

            last_weight_dict = mask_weights.pop(0)
            mask_weights.append(last_weight_dict)
            self.display_weights(mask_weights)
        return

    def confirm_split_weights_along_surface(self):
        self.update_split_weights_along_surface()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_along_surface)
        self.number_field.valueChanged.disconnect(self.update_split_weights_along_surface)
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_along_surface)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_along_surface)
        self.c.surface_method_updated.disconnect(self.update_split_weights_along_surface)
        self.load_object_button.clicked.disconnect(self.update_split_weights_along_surface)
        self.refresh_object_button.clicked.disconnect(self.update_split_weights_along_surface)
        self.cancel_function = None
        return

    def cancel_split_weights_along_surface(self):
        self.restore_preSplit_weights()
        for wtHolder, wt in zip(self.active_wtHolder_list, self.start_weights_list):
            wtHolder.set_weights(wt)

        self.split_target_tableWidget.empty()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_weights_along_surface)
        self.number_field.valueChanged.disconnect(self.update_split_weights_along_surface)
        self.confirm_button.clicked.disconnect(self.confirm_split_weights_along_surface)
        self.cancel_button.clicked.disconnect(self.cancel_split_weights_along_surface)
        self.c.surface_method_updated.disconnect(self.update_split_weights_along_surface)
        self.load_object_button.clicked.disconnect(self.update_split_weights_along_surface)
        self.refresh_object_button.clicked.disconnect(self.update_split_weights_along_surface)
        self.cancel_function = None
        return

    def flip_weights_over_axis(self):
        if self.matching_method == 'closestComponent':
            ii_dict = None
            stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ii')
            stored_dict = False
            if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                stored_dict = True
            for selected_deformer in self.selected_wtHolder_list:
                wts = selected_deformer.get_weights(self.position_list)
                flipped_wts, ii_dict = wt_utils.flip_weights(wts, flip_coordinate=0, axis=self.axis, matching_method=self.matching_method, source_shape=None, ii_dict=ii_dict, ibw_dict=None)
                selected_deformer.set_weights(flipped_wts)

            if not stored_dict:
                cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
        elif self.matching_method == 'closestPointOnSurface':
            if cmds.nodeType(self.shape) == 'mesh':
                ibw_dict = None
                stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ibw')
                stored_dict = False
                if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                    ibw_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                    stored_dict = True
                for selected_deformer in self.selected_wtHolder_list:
                    wts = selected_deformer.get_weights(self.position_list)
                    flipped_wts, ibw_dict = wt_utils.flip_weights(wts, flip_coordinate=0, axis=self.axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=None, ibw_dict=ibw_dict)
                    selected_deformer.set_weights(flipped_wts)

                if not stored_dict:
                    cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                    cmds.setAttr(self.shape + '.' + stored_attr, str(ibw_dict), type='string')
            else:
                cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
        elif self.matching_method == 'closestComponentUV':
            if cmds.nodeType(self.shape) == 'mesh':
                ii_dict = None
                stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ii')
                stored_dict = False
                if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                    ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                    stored_dict = True
                for selected_deformer in self.selected_wtHolder_list:
                    wts = selected_deformer.get_weights(self.position_list)
                    flipped_wts, ii_dict = wt_utils.flip_weights(wts, flip_coordinate=0, uv_axis=self.uv_axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=ii_dict, ibw_dict=None)
                    selected_deformer.set_weights(flipped_wts)

                if not stored_dict:
                    cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                    cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
                self.update_displayed_weights()
            else:
                cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')
        self.update_displayed_weights()
        return

    def start_flip_weights_over_coordinate(self):
        self.active_wtHolder_list = self.selected_wtHolder_list
        self.highlight_selected_wtHolders()
        self.selection_off()
        self.rightClick_off()
        self.display_selected_weights = False
        self.load_shape_button.setEnabled(False)
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.coordinate_parentWidget.setVisible(True)
        self.active_start_weights = self.active_wtHolder_list[0].get_weights(self.position_list)
        pos_list = [x[1][0] for x in list(self.active_start_weights.items())]
        pos_list = [pos for tuple in pos_list for pos in tuple]
        pos_list = [abs(pos) for pos in pos_list]
        self.coordinate_slider.setMinimum(-100 * min(pos_list))
        self.coordinate_slider.setMaximum(100 * max(pos_list))
        self.coordinate_label.setText('Flip Coordinate')
        self.coordinate_field.valueChanged.connect(self.update_flip_over_coordinate)
        self.c.axis_updated.connect(self.update_flip_over_coordinate)
        self.display_preflip_weights_checkBox.stateChanged.connect(self.update_flip_over_coordinate)
        self.c.match_method_updated.connect(self.update_flip_over_coordinate)
        self.confirm_button.clicked.connect(self.confirm_flip_over_coordinate)
        self.cancel_button.clicked.connect(self.cancel_flip_over_coordinate)
        self.update_flip_over_coordinate()
        return

    def update_flip_over_coordinate(self):
        self.ii_dict = None
        self.ibw_dict = None
        if self.matching_method == 'closestComponent':
            flipped_wts, self.ii_dict = wt_utils.flip_weights(self.active_start_weights, flip_coordinate=self.coordinate_field.value(), axis=self.axis, matching_method=self.matching_method)
            self.active_wtHolder_list[0].set_weights(flipped_wts)
            if self.display_preflip_weights_checkBox.isChecked():
                self.display_weights([self.active_start_weights, flipped_wts])
            else:
                self.display_weights([flipped_wts])
        elif self.matching_method == 'closestPointOnSurface':
            if cmds.nodeType(self.shape) == 'mesh':
                flipped_wts, self.ibw_dict = wt_utils.flip_weights(self.active_start_weights, flip_coordinate=self.coordinate_field.value(), axis=self.axis, matching_method=self.matching_method, source_shape=self.shape)
                self.active_wtHolder_list[0].set_weights(flipped_wts)
                if self.display_preflip_weights_checkBox.isChecked():
                    self.display_weights([self.active_start_weights, flipped_wts])
                else:
                    self.display_weights([flipped_wts])
            else:
                cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
        elif self.matching_method == 'closestComponentUV':
            if cmds.nodeType(self.shape) == 'mesh':
                flipped_wts, self.ii_dict = wt_utils.flip_weights(self.active_start_weights, flip_coordinate=0, uv_axis=self.uv_axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=self.ii_dict, ibw_dict=None)
                self.active_wtHolder_list[0].set_weights(flipped_wts)
                if self.display_preflip_weights_checkBox.isChecked():
                    self.display_weights([self.active_start_weights, flipped_wts])
                else:
                    self.display_weights([flipped_wts])
            else:
                cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')
        return

    def confirm_flip_over_coordinate(self):
        self.update_flip_over_coordinate()
        if self.ii_dict or self.ibw_dict:
            for each_deformer in self.active_wtHolder_list[1:]:
                wts = each_deformer.get_weights(shape=self.shape)
                flipped_wts, extra_dict = wt_utils.flip_weights(wts, flip_coordinate=0, uv_axis=self.uv_axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=self.ii_dict, ibw_dict=self.ibw_dict)
                each_deformer.set_weights(flipped_wts)

        self.unhighlight_wtHolders()
        self.selection_on()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.coordinate_label.setText('Flip Coordinate')
        self.coordinate_field.valueChanged.disconnect(self.update_flip_over_coordinate)
        self.c.axis_updated.disconnect(self.update_flip_over_coordinate)
        self.display_preflip_weights_checkBox.stateChanged.disconnect(self.update_flip_over_coordinate)
        self.c.match_method_updated.disconnect(self.update_flip_over_coordinate)
        self.confirm_button.clicked.disconnect(self.confirm_flip_over_coordinate)
        self.cancel_button.clicked.disconnect(self.cancel_flip_over_coordinate)
        self.cancel_function = None
        return

    def cancel_flip_over_coordinate(self):
        self.active_wtHolder_list[0].set_weights(self.active_start_weights)
        self.unhighlight_wtHolders()
        self.selection_on()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_displayed_weights()
        self.coordinate_label.setText('Flip Coordinate')
        self.coordinate_field.valueChanged.disconnect(self.update_flip_over_coordinate)
        self.c.axis_updated.disconnect(self.update_flip_over_coordinate)
        self.confirm_button.clicked.disconnect(self.confirm_flip_over_coordinate)
        self.cancel_button.clicked.disconnect(self.cancel_flip_over_coordinate)
        self.cancel_function = None
        return

    def start_flip_weights_with_plane(self):
        if len(self.selected_wtHolder_list) == 0:
            return
        self.active_wtHolder_list = self.selected_wtHolder_list
        self.highlight_selected_wtHolders()
        self.selection_off()
        self.rightClick_off()
        self.display_selected_weights = False
        self.load_shape_button.setEnabled(False)
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.active_start_weights = self.active_wtHolder_list[0].get_weights(self.position_list)
        self.loaded_object_label.setText('Flip Surface')
        self.object_type = 'nurbsSurface'
        self.confirm_button.clicked.connect(self.confirm_flip_weights_with_plane)
        self.cancel_button.clicked.connect(self.cancel_flip_weights_with_plane)
        self.c.match_method_updated.connect(self.update_flip_weights_with_plane)
        self.load_object_button.clicked.connect(self.update_flip_weights_with_plane)
        self.refresh_object_button.clicked.connect(self.update_flip_weights_with_plane)
        self.display_preflip_weights_checkBox.stateChanged.connect(self.update_flip_weights_with_plane)
        self.update_flip_weights_with_plane()
        return

    def update_flip_weights_with_plane(self):
        start_time = time.time()
        if cmds.objExists(self.loaded_object):
            sel = om2.MSelectionList()
            sel.add(self.loaded_object)
            mFn = om2.MFnNurbsSurface(sel.getDependNode(0))
            mDagPath = sel.getDagPath(0)
            objMatrix = mDagPath.inclusiveMatrix()
            planeCenter = tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3]
            planeNormal = tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3]
            self.ii_dict = None
            self.ibw_dict = None
            if self.matching_method == 'closestComponent':
                flipped_wts, self.ii_dict = wt_utils.flip_weights_with_plane(self.active_start_weights, plane_position=planeCenter, plane_normal=planeNormal, matching_method=self.matching_method, source_shape=self.shape, max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled())
                self.active_wtHolder_list[0].set_weights(flipped_wts)
                if self.display_preflip_weights_checkBox.isChecked():
                    self.display_weights([self.active_start_weights, flipped_wts])
                else:
                    self.display_weights([flipped_wts])
            elif self.matching_method == 'closestPointOnSurface':
                if cmds.nodeType(self.shape) == 'mesh':
                    flipped_wts, self.ibw_dict = wt_utils.flip_weights_with_plane(self.active_start_weights, plane_position=planeCenter, plane_normal=planeNormal, matching_method=self.matching_method, source_shape=self.shape, max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled())
                    self.active_wtHolder_list[0].set_weights(flipped_wts)
                    if self.display_preflip_weights_checkBox.isChecked():
                        self.display_weights([self.active_start_weights, flipped_wts])
                    else:
                        self.display_weights([flipped_wts])
                else:
                    cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
            elif self.matching_method == 'closestComponentUV':
                cmds.warning('Matching method "closestComponentUV" does not work with "Flip Weights Over Plane"')
        return

    def confirm_flip_weights_with_plane(self):
        if cmds.objExists(self.loaded_object):
            sel = om2.MSelectionList()
            sel.add(self.loaded_object)
            mFn = om2.MFnNurbsSurface(sel.getDependNode(0))
            mDagPath = sel.getDagPath(0)
            objMatrix = mDagPath.inclusiveMatrix()
            planeCenter = tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3]
            planeNormal = tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3]
            if self.ii_dict or self.ibw_dict:
                for i, each_deformer in enumerate(self.active_wtHolder_list[1:]):
                    wts = each_deformer.get_weights(self.position_list)
                    flipped_wts, extra_dict = wt_utils.flip_weights_with_plane(wts, plane_position=planeCenter, plane_normal=planeNormal, matching_method=self.matching_method, source_shape=self.shape, ii_dict=self.ii_dict, ibw_dict=self.ibw_dict, max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled())
                    each_deformer.set_weights(flipped_wts)

        self.update_displayed_weights()
        self.confirm_button.clicked.disconnect(self.confirm_flip_weights_with_plane)
        self.cancel_button.clicked.disconnect(self.cancel_flip_weights_with_plane)
        self.c.match_method_updated.disconnect(self.update_flip_weights_with_plane)
        self.load_object_button.clicked.disconnect(self.update_flip_weights_with_plane)
        self.refresh_object_button.clicked.disconnect(self.update_flip_weights_with_plane)
        self.display_preflip_weights_checkBox.stateChanged.disconnect(self.update_flip_weights_with_plane)
        self.unhighlight_wtHolders()
        self.selection_on()
        self.rightClick_on()
        self.display_selected_weights = False
        self.hide_extra_widgets()
        self.cancel_function = None
        return

    def cancel_flip_weights_with_plane(self):
        self.active_wtHolder_list[0].set_weights(self.active_start_weights)
        self.confirm_button.clicked.disconnect(self.confirm_flip_weights_with_plane)
        self.cancel_button.clicked.disconnect(self.cancel_flip_weights_with_plane)
        self.c.match_method_updated.disconnect(self.update_flip_weights_with_plane)
        self.load_object_button.clicked.disconnect(self.update_flip_weights_with_plane)
        self.refresh_object_button.clicked.disconnect(self.update_flip_weights_with_plane)
        self.unhighlight_wtHolders()
        self.selection_on()
        self.rightClick_on()
        self.display_selected_weights = False
        self.hide_extra_widgets()
        self.update_selected_deformer()
        self.cancel_function = None
        return

    def invert_weights(self):
        for selected_deformer in self.selected_wtHolder_list:
            wts = selected_deformer.get_weights(self.position_list)
            wts = wt_utils.invert_weights(wts)
            selected_deformer.set_weights(wts)

        self.update_displayed_weights()
        return

    def add_copied_weights(self):
        if self.shape == self.clipboard_shape:
            for i, selected_deformer in enumerate(self.selected_wtHolder_list):
                wts = selected_deformer.get_weights(self.position_list)
                sum_wts = wt_utils.add_weights(wts, self.clipboard_weights, minimum=self.clamp_weights_min_field.value() and self.clamp_weights_min_field.isEnabled(), maximum=self.clamp_weights_max_field.value() and self.clamp_weights_max_field.isEnabled())
                selected_deformer.set_weights(sum_wts)

        else:
            # FIX: the original called self.matching_method (a string) and the
            # non-existent wt_utils.match_points, so this branch always failed.
            matched_clipboard_wts, extra_dict = wt_utils.match_weights_to_shape(self.clipboard_weights, self.shape, matching_method=self.matching_method, source_shape=self.clipboard_shape)
            for i, selected_deformer in enumerate(self.selected_wtHolder_list):
                wts = selected_deformer.get_weights(self.position_list)
                sum_wts = wt_utils.add_weights(wts, matched_clipboard_wts, minimum=self.clamp_weights_min_field.value() and self.clamp_weights_min_field.isEnabled(), maximum=self.clamp_weights_max_field.value() and self.clamp_weights_max_field.isEnabled())
                selected_deformer.set_weights(sum_wts)

        self.update_displayed_weights()
        return

    def subtract_copied_weights(self):
        if self.shape == self.clipboard_shape:
            for i, selected_deformer in enumerate(self.selected_wtHolder_list):
                wts = selected_deformer.get_weights(self.position_list)
                sum_wts = wt_utils.subtract_weights(wts, self.clipboard_weights, minimum=self.clamp_weights_min_field.value() and self.clamp_weights_min_field.isEnabled(), maximum=self.clamp_weights_max_field.value() and self.clamp_weights_max_field.isEnabled())
                selected_deformer.set_weights(sum_wts)

        else:
            # FIX: the original called self.matching_method (a string) and the
            # non-existent wt_utils.match_points, so this branch always failed.
            matched_clipboard_wts, extra_dict = wt_utils.match_weights_to_shape(self.clipboard_weights, self.shape, matching_method=self.matching_method, source_shape=self.clipboard_shape)
            for i, selected_deformer in enumerate(self.selected_wtHolder_list):
                wts = selected_deformer.get_weights(self.position_list)
                sum_wts = wt_utils.subtract_weights(wts, matched_clipboard_wts, minimum=self.clamp_weights_min_field.value() and self.clamp_weights_min_field.isEnabled(), maximum=self.clamp_weights_max_field.value() and self.clamp_weights_max_field.isEnabled())
                selected_deformer.set_weights(sum_wts)

        self.update_displayed_weights()
        return

    def multiply_by_copied_weights(self):
        if self.shape == self.clipboard_shape:
            for i, selected_deformer in enumerate(self.selected_wtHolder_list):
                wts = selected_deformer.get_weights(self.position_list)
                sum_wts = wt_utils.multiply_weights(wts, self.clipboard_weights)
                selected_deformer.set_weights(sum_wts)

        else:
            # FIX: the original called self.matching_method (a string) and the
            # non-existent wt_utils.match_points, so this branch always failed.
            matched_clipboard_wts, extra_dict = wt_utils.match_weights_to_shape(self.clipboard_weights, self.shape, matching_method=self.matching_method, source_shape=self.clipboard_shape)
            for i, selected_deformer in enumerate(self.selected_wtHolder_list):
                wts = selected_deformer.get_weights(self.position_list)
                sum_wts = wt_utils.multiply_weights(wts, matched_clipboard_wts)
                selected_deformer.set_weights(sum_wts)

        self.update_displayed_weights()
        return

    def normalize_weights(self):
        weight_dict_list = [each_deformer.get_weights(self.position_list) for each_deformer in self.selected_wtHolder_list]
        normalized_weight_list = wt_utils.normalize_weights(weight_dict_list)
        for weight_dict, each_deformer in zip(normalized_weight_list, self.selected_wtHolder_list):
            each_deformer.set_weights(weight_dict)

        self.update_displayed_weights()
        return

    def save_weights(self):
        for selected_deformer in [item for item in self.selected_wtHolder_list if not item.inBetween_name]:
            if selected_deformer.item_type == 'deformer':
                nice_name = selected_deformer.node
            if selected_deformer.item_type == 'blendShape':
                nice_name = selected_deformer.node
                if selected_deformer.target_name:
                    nice_name += '.' + selected_deformer.target_name
            filePath = cmds.fileDialog2(cap=('Save {} Weights To File').format(nice_name), fm=0, ds=1, ff='*json;;*xml')
            if filePath == None:
                continue
            else:
                filePath = filePath[0]
                if 'xml' in filePath:
                    if filePath.split('.')[-1] == 'xml':
                        short_path = filePath.split('/')[-1]
                        long_path = ('/').join(filePath.split('/')[:-1])
                        for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                            cmds.select(self.shape)
                            cmds.deformerWeights(short_path, export=True, deformer=selected_deformer.node, path=long_path, method='index')

                    return
                if '.json' not in filePath:
                    filePath = filePath + '.json'
            if cmds.nodeType(self.shape) == 'mesh':
                shape_data = wt_utils.get_shape_data(self.shape)
            else:
                shape_data = None
            wts = selected_deformer.get_weights(self.position_list)
            wt_utils.save_dictionary(filePath, wts, shape_data)

        return

    def load_weights(self):
        filePath = cmds.fileDialog2(ff='*.json;;*.xml', fm=1)
        if filePath == None:
            return {}
        else:
            filePath = filePath[0]
            if filePath.split('.')[-1] == 'xml':
                short_path = filePath.split('/')[-1]
                long_path = ('/').join(filePath.split('/')[:-1])
                for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                    cmds.select(self.shape)
                    cmds.deformerWeights(short_path, im=True, deformer=selected_deformer.node, path=long_path, method='nearest')

                return

            def load_json(load_path):
                try:
                    open(load_path, 'r')
                except:
                    return {}

                with open(load_path, 'r') as rf:
                    data = json.load(rf)
                return data

            dictionary_contents = load_json(filePath)
            if isinstance(dictionary_contents, list):
                wts, shape_data = dictionary_contents
            else:
                wts = dictionary_contents
            wts = {int(key): value for key, value in list(wts.items())}
            if self.load_matching_method == 'index':
                if set(wts.keys()) == set(self.ip_dictionary.keys()):
                    for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                        selected_deformer.set_weights(wts)

                else:
                    cmds.warning('weights could not be loaded because the component indices do not match')
            elif self.load_matching_method == 'closestComponent':
                ii_dict = wt_utils.match_points_to_closest_point({index: position for index, (position, weight) in list(wts.items())}, self.ip_dictionary)
                new_weight_dictionary = {new: [self.ip_dictionary[new][0], wts[old][1]] for new, old in list(ii_dict.items())}
                for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                    selected_deformer.set_weights(new_weight_dictionary)

            elif self.load_matching_method == 'closestPointOnSurface':
                if not shape_data:
                    cmds.warning(('The weights cannot be loaded by "closestPointOnSurface" because {} does not contain any shape data').format(filePath[0]))
                new_shape = wt_utils.create_shape_from_data(shape_data)
                if not new_shape:
                    return
                ibw_dict = wt_utils.match_points_to_closest_point_on_surface(new_shape, self.ip_dictionary)
                cmds.delete(cmds.listRelatives(new_shape, p=True))
                new_weight_dictionary = {}
                for new_id, (comp_ids, barycentric_weights) in list(ibw_dict.items()):
                    new_weight_dictionary[new_id] = [
                     self.ip_dictionary[new_id][0], sum([wts[id][1] * bary for id, bary in zip(comp_ids, barycentric_weights)])]

                for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                    selected_deformer.set_weights(new_weight_dictionary)

            elif self.load_matching_method == 'closestComponentUV':
                if cmds.nodeType(self.shape) != 'mesh' or shape_data[-1] != 'mesh':
                    cmds.warning(('The weights cannot be loaded by "closestComponentUV" because {} is not a mesh').format(self.shape))
                if not shape_data:
                    cmds.warning(('The weights cannot be loaded by "closestPointOnSurface" because {} does not contain any shape data').format(filePath[0]))
                points, verts, vert_connects, (U_list, V_list), shape_type = shape_data
                index_list = list(wts.keys())
                temporary_shape_ip_dict = {}
                for index in index_list:
                    temporary_shape_ip_dict[index] = (
                     U_list[index], V_list[index], 0)

                if cmds.nodeType(self.shape):
                    i_UV_dict = wt_utils.convert_ip_dict_positions_to_UV_coordinates(self.ip_dictionary, self.shape)
                ii_dict = wt_utils.match_points_to_closest_point(temporary_shape_ip_dict, i_UV_dict)
                new_weight_dictionary = {new: [self.ip_dictionary[new][0], wts[old][1]] for new, old in list(ii_dict.items())}
                for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                    selected_deformer.set_weights(new_weight_dictionary)

            self.update_displayed_weights()
            return

    def copy_softselect(self):
        self.clipboard_shape = None
        self.clipboard_weights = None
        softSelect_result = wt_utils.convert_softSelect_to_weights()
        if softSelect_result:
            for wts, shape in zip(*softSelect_result):
                if shape == self.shape:
                    self.clipboard_weights = wts
                    self.clipboard_shape = self.shape
                    return

        return

    def copy_wire(self):
        self.clipboard_shape = None
        self.clipboard_weights = None
        softMod_wtHolders = [x for x in self.selected_wtHolder_list if cmds.nodeType(x.node) == 'wire']
        if softMod_wtHolders:
            softMod_weights = wt_utils.convert_wire_to_weights(softMod_wtHolders[0].node, self.shape)
            if softMod_weights:
                self.clipboard_weights = softMod_weights
        return

    def copy_softMod(self):
        self.clipboard_shape = None
        self.clipboard_weights = None
        softMod_wtHolders = [x for x in self.selected_wtHolder_list if cmds.nodeType(x.node) == 'softMod']
        if softMod_wtHolders:
            softMod_weights = wt_utils.convert_softMod_to_weights(softMod_wtHolders[0].node, self.shape)
            if softMod_weights:
                self.clipboard_weights = softMod_weights
        return

    def copy_deltas(self):
        if len(self.selected_wtHolder_list) != 0:
            valid_wtHolder_list = [wtHolder for wtHolder in self.selected_wtHolder_list if wtHolder.target_name]
            if valid_wtHolder_list:
                deltas = valid_wtHolder_list[0].get_deltas(self.position_list)
                self.clipboard_deltas = deltas
                self.clipboard_deltas_shape = self.shape
                self.clipboard_shape_data = wt_utils.get_shape_data(self.shape)
        return

    def paste_deltas(self):
        if self.clipboard_deltas and self.selected_wtHolder_list:
            if self.shape == self.clipboard_deltas_shape:
                for selected_deformer in self.selected_wtHolder_list:
                    selected_deformer.set_deltas(self.clipboard_deltas)

            elif self.matching_method == 'closestPointOnSurface':
                if self.clipboard_shape_data[-1] == 'mesh':
                    if cmds.objExists(self.clipboard_shape):
                        matched_deltas, extra_dict = wt_utils.match_deltas_to_shape(self.clipboard_deltas, self.shape, matching_method='closestPointOnSurface', source_shape=self.clipboard_deltas_shape)
                    else:
                        new_shape = wt_utils.create_shape_from_data(self.clipboard_shape_data)
                        matched_deltas, extra_dict = wt_utils.match_deltas_to_shape(self.clipboard_deltas, self.shape, matching_method='closestPointOnSurface', source_shape=new_shape)
                        cmds.delete(cmds.listRelatives(new_shape, p=True)[0])
                    for selected_deformer in self.selected_wtHolder_list:
                        selected_deformer.set_deltas(matched_deltas)

                else:
                    cmds.warning('"closestPointOnsurface" matching_method only works when the source_shape is a mesh')
            elif self.matching_method == 'closestComponentUV':
                if cmds.nodeType(self.clipboard_shape) == 'mesh' and cmds.nodeType(self.shape) == 'mesh':
                    matched_deltas, extra_dict = wt_utils.match_deltas_to_shape(self.clipboard_deltas, self.shape, matching_method='closestComponentUV', source_shape=self.clipboard_deltas_shape)
                    for selected_deformer in self.selected_wtHolder_list:
                        selected_deformer.set_deltas(matched_deltas)

            elif self.matching_method == 'closestComponent':
                matched_deltas, extra_dict = wt_utils.match_deltas_to_shape(self.clipboard_deltas, self.shape, matching_method='closestComponent', source_shape=self.clipboard_deltas_shape)
                for selected_deformer in self.selected_wtHolder_list:
                    selected_deformer.set_deltas(matched_deltas)

        return

    def symmetrisize_deltas_over_axis(self):
        valid_wtHolder_list = [wtHolder for wtHolder in self.selected_wtHolder_list if wtHolder.get_deltas(self.position_list)]
        if self.matching_method == 'closestComponent':
            ii_dict = None
            stored_attr = ('{}_{}_{}_{}').format('symm', self.axis, self.direction_short, 'ii')
            stored_dict = False
            if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                stored_dict = True
            for selected_target in valid_wtHolder_list:
                deltas = selected_target.get_deltas(self.position_list)
                symm_deltas, ii_dict = wt_utils.symmetrisize_deltas(deltas, symm_coordinate=0, axis=self.axis, direction=self.direction, matching_method=self.matching_method, source_shape=None, ii_dict=ii_dict, ibw_dict=None)
                selected_target.set_deltas(symm_deltas)

            if not stored_dict:
                cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
        elif self.matching_method == 'closestPointOnSurface':
            if cmds.nodeType(self.shape) == 'mesh':
                ibw_dict = None
                stored_attr = ('{}_{}_{}_{}').format('symm', self.axis, self.direction_short, 'ibw')
                stored_dict = False
                if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                    ibw_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                    stored_dict = True
                for selected_target in valid_wtHolder_list:
                    deltas = selected_target.get_deltas(self.position_list)
                    symm_deltas, ibw_dict = wt_utils.symmetrisize_deltas(deltas, symm_coordinate=0, axis=self.axis, direction=self.direction, matching_method=self.matching_method, source_shape=self.shape, ii_dict=None, ibw_dict=ibw_dict)
                    selected_target.set_deltas(symm_deltas)

                if not stored_dict:
                    cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                    cmds.setAttr(self.shape + '.' + stored_attr, str(ibw_dict), type='string')
            else:
                cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
        elif self.matching_method == 'closestComponentUV':
            if cmds.nodeType(self.shape) == 'mesh':
                ii_dict = None
                stored_attr = ('{}_{}_{}_{}').format('symm', self.axis, self.direction_short, 'ii')
                stored_dict = False
                if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                    ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                    stored_dict = True
                for selected_target in valid_wtHolder_list:
                    deltas = selected_target.get_deltas(self.position_list)
                    symm_deltas, ii_dict = wt_utils.symmetrisize_deltas(deltas, symm_coordinate=0.5, axis=self.axis, uv_axis=self.uv_axis, direction=self.direction, matching_method=self.matching_method, source_shape=self.shape, ii_dict=ii_dict, ibw_dict=None)
                    selected_target.set_deltas(symm_deltas)

                if not stored_dict:
                    cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                    cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
                self.update_displayed_deltas()
            else:
                cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')
        return

    def start_symmetrisize_deltas_with_plane(self):
        self.active_wtHolder_list = [wtHolder for wtHolder in self.selected_wtHolder_list if wtHolder.target_name]
        if not self.active_wtHolder_list:
            return
        self.active_start_deltas = self.active_wtHolder_list[0].get_deltas(self.position_list)
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.rightClick_off()
        self.loaded_object_label.setText('Symm Surface')
        self.object_type = 'nurbsSurface'
        self.confirm_button.clicked.connect(self.confirm_symmetrisize_deltas_with_plane)
        self.cancel_button.clicked.connect(self.cancel_symmetrisize_deltas_with_plane)
        self.c.direction_updated.connect(self.update_symmetrisize_deltas_with_plane)
        self.c.match_method_updated.connect(self.update_symmetrisize_deltas_with_plane)
        self.load_object_button.clicked.connect(self.update_symmetrisize_deltas_with_plane)
        self.refresh_object_button.clicked.connect(self.update_symmetrisize_deltas_with_plane)
        self.update_symmetrisize_deltas_with_plane()
        return

    def update_symmetrisize_deltas_with_plane(self):
        if cmds.objExists(self.loaded_object):
            sel = om2.MSelectionList()
            sel.add(self.loaded_object)
            mDagPath = sel.getDagPath(0)
            objMatrix = mDagPath.inclusiveMatrix()
            mFn = om2.MFnNurbsSurface(mDagPath)
            planePosition = tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3]
            planeNormal = tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3]
            if self.matching_method == 'closestComponent':
                symm_deltas, self.ii_dict = wt_utils.symmetrisize_deltas_with_plane(self.active_start_deltas, plane_position=planePosition, plane_normal=planeNormal, direction=self.direction, matching_method='closestComponent', source_shape=None, ii_dict=None, ibw_dict=None, max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled())
            elif self.matching_method == 'closestComponentUV':
                cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')
            elif self.matching_method == 'closestPointOnSurface':
                if cmds.nodeType(self.shape) == 'mesh':
                    symm_deltas, self.ibw_dict = wt_utils.symmetrisize_deltas_with_plane(self.active_start_deltas, plane_position=planePosition, plane_normal=planeNormal, direction=self.direction, matching_method='closestPointOnSurface', source_shape=self.shape, ii_dict=None, ibw_dict=None, max_distance=self.max_matching_distance_QSpinBox.value() and self.max_matching_distance_QSpinBox.isEnabled())
                else:
                    cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
            self.active_wtHolder_list[0].set_deltas(symm_deltas)
        return

    def confirm_symmetrisize_deltas_with_plane(self):
        if self.ii_dict or self.ibw_dict:
            if cmds.objExists(self.loaded_object):
                sel = om2.MSelectionList()
                sel.add(self.loaded_object)
                mDagPath = sel.getDagPath(0)
                objMatrix = mDagPath.inclusiveMatrix()
                mFn = om2.MFnNurbsSurface(mDagPath)
                planePosition = tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3]
                planeNormal = tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3]
                for each_blendShape in self.active_wtHolder_list[1:]:
                    deltas = each_blendShape.get_deltas(self.position_list)
                    symm_deltas, extra_dict = wt_utils.symmetrisize_deltas_with_plane(self.active_start_deltas, plane_position=planePosition, plane_normal=planeNormal, direction=self.direction, matching_method='closestComponent', source_shape=None, ii_dict=self.ii_dict, ibw_dict=self.ibw_dict, max_distance=self.max_matching_distance_QSpinBox.value())
                    each_blendShape.set_deltas(symm_deltas)

        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.confirm_button.clicked.disconnect(self.confirm_symmetrisize_deltas_with_plane)
        self.cancel_button.clicked.disconnect(self.cancel_symmetrisize_deltas_with_plane)
        self.c.direction_updated.disconnect(self.update_symmetrisize_deltas_with_plane)
        self.c.match_method_updated.disconnect(self.update_symmetrisize_deltas_with_plane)
        self.load_object_button.clicked.disconnect(self.update_symmetrisize_deltas_with_plane)
        self.refresh_object_button.clicked.disconnect(self.update_symmetrisize_deltas_with_plane)
        self.cancel_function = None
        return

    def cancel_symmetrisize_deltas_with_plane(self):
        blendShape_target = self.active_wtHolder_list[0]
        blendShape_target.set_deltas(self.active_start_deltas)
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.confirm_button.clicked.disconnect(self.confirm_symmetrisize_deltas_with_plane)
        self.cancel_button.clicked.disconnect(self.cancel_symmetrisize_deltas_with_plane)
        self.c.direction_updated.disconnect(self.update_symmetrisize_deltas_with_plane)
        self.c.match_method_updated.disconnect(self.update_symmetrisize_deltas_with_plane)
        self.load_object_button.clicked.disconnect(self.update_symmetrisize_deltas_with_plane)
        self.refresh_object_button.clicked.disconnect(self.update_symmetrisize_deltas_with_plane)
        return

    def flip_deltas_over_axis(self):
        if self.matching_method == 'closestComponent':
            ii_dict = None
            stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ii')
            stored_dict = False
            if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                stored_dict = True
            for selected_deformer in self.selected_wtHolder_list:
                deltas = selected_deformer.get_deltas(self.position_list)
                flipped_deltas, ii_dict = wt_utils.flip_deltas(deltas, flip_coordinate=0, axis=self.axis, matching_method=self.matching_method, source_shape=None, ii_dict=ii_dict, ibw_dict=None)
                selected_deformer.set_deltas(flipped_deltas)

            if not stored_dict:
                cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
        elif self.matching_method == 'closestPointOnSurface':
            if cmds.nodeType(self.shape) == 'mesh':
                ibw_dict = None
                stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ibw')
                stored_dict = False
                if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                    ibw_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                    stored_dict = True
                for selected_deformer in self.selected_wtHolder_list:
                    deltas = selected_deformer.get_deltas(self.position_list)
                    flipped_deltas, ibw_dict = wt_utils.flip_deltas(deltas, flip_coordinate=0, axis=self.axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=None, ibw_dict=ibw_dict)
                    selected_deformer.set_deltas(flipped_deltas)

                if not stored_dict:
                    cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                    cmds.setAttr(self.shape + '.' + stored_attr, str(ibw_dict), type='string')
            else:
                cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
        elif self.matching_method == 'closestComponentUV':
            if cmds.nodeType(self.shape) == 'mesh':
                ii_dict = None
                stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ii')
                stored_dict = False
                if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                    ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                    stored_dict = True
                for selected_deformer in self.selected_wtHolder_list:
                    deltas = selected_deformer.get_deltas(self.position_list)
                    flipped_deltas, ii_dict = wt_utils.flip_deltas(deltas, flip_coordinate=0.5, axis=self.axis, uv_axis=self.uv_axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=ii_dict, ibw_dict=None)
                    selected_deformer.set_deltas(flipped_deltas)

                if not stored_dict:
                    cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                    cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
            else:
                cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')
        return

    def start_flip_deltas_over_coordinate(self):
        self.active_wtHolder_list = [wtHolder for wtHolder in self.selected_wtHolder_list if wtHolder.target_name]
        self.active_start_deltas = self.active_wtHolder_list[0].get_deltas(self.position_list)
        self.rightClick_off()
        self.load_shape_button.setEnabled(False)
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.coordinate_parentWidget.setVisible(True)
        pos_list = [x[1][0] for x in list(self.active_start_deltas.items())]
        pos_list = [pos for tuple in pos_list for pos in tuple]
        pos_list = [abs(pos) for pos in pos_list]
        self.coordinate_slider.setMinimum(-100 * max(pos_list))
        self.coordinate_slider.setMaximum(100 * max(pos_list))
        self.coordinate_field.setMinimum(-1 * max(pos_list))
        self.coordinate_field.setMaximum(max(pos_list))
        self.coordinate_label.setText('Flip Coordinate')
        self.coordinate_field.valueChanged.connect(self.update_flip_deltas_over_coordinate)
        self.c.axis_updated.connect(self.update_flip_deltas_over_coordinate)
        self.c.match_method_updated.connect(self.update_flip_deltas_over_coordinate)
        self.confirm_button.clicked.connect(self.confirm_flip_deltas_over_coordinate)
        self.cancel_button.clicked.connect(self.cancel_flip_deltas_over_coordinate)
        self.update_flip_deltas_over_coordinate()
        return

    def update_flip_deltas_over_coordinate(self):
        self.ii_dict = None
        self.ibw_dict = None
        if self.matching_method == 'closestComponent':
            flipped_deltas, self.ii_dict = wt_utils.flip_deltas(self.active_start_deltas, flip_coordinate=self.coordinate_field.value(), axis=self.axis, matching_method=self.matching_method)
            self.active_wtHolder_list[0].set_deltas(flipped_deltas)
        elif self.matching_method == 'closestPointOnSurface':
            if cmds.nodeType(self.shape) == 'mesh':
                flipped_deltas, self.ibw_dict = wt_utils.flip_deltas(self.active_start_deltas, flip_coordinate=self.coordinate_field.value(), axis=self.axis, matching_method=self.matching_method, source_shape=self.shape)
                self.active_wtHolder_list[0].set_deltas(flipped_deltas)
            else:
                cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
        elif self.matching_method == 'closestComponentUV':
            if cmds.nodeType(self.shape) == 'mesh':
                flipped_deltas, self.ii_dict = wt_utils.flip_deltas(self.active_start_deltas, flip_coordinate=0, axis=self.axis, uv_axis=self.uv_axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=self.ii_dict, ibw_dict=None)
                self.active_wtHolder_list[0].set_deltas(flipped_deltas)
            else:
                cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')
        active_blendShape = self.active_wtHolder_list[0]
        active_blendShape.set_deltas(flipped_deltas)
        return

    def confirm_flip_deltas_over_coordinate(self):
        self.update_flip_deltas_over_coordinate()
        if self.ii_dict or self.ibw_dict:
            for i, each_target in enumerate(self.active_wtHolder_list[1:]):
                deltas = each_target.get_deltas(self.position_list)
                flipped_deltas, extra_dict = wt_utils.flip_deltas(self.active_start_deltas, flip_coordinate=self.coordinate_field.value(), axis=self.axis, matching_method=self.matching_method, source_shape=self.shape)
                each_target.set_deltas(flipped_deltas)

        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_selected_deformer()
        self.coordinate_label.setText('Flip Coordinate')
        self.coordinate_field.valueChanged.disconnect(self.update_flip_deltas_over_coordinate)
        self.c.axis_updated.disconnect(self.update_flip_deltas_over_coordinate)
        self.c.match_method_updated.disconnect(self.update_flip_deltas_over_coordinate)
        self.confirm_button.clicked.disconnect(self.confirm_flip_deltas_over_coordinate)
        self.cancel_button.clicked.disconnect(self.cancel_flip_deltas_over_coordinate)
        self.cancel_function = None
        return

    def cancel_flip_deltas_over_coordinate(self):
        self.active_wtHolder_list[0].set_deltas(self.active_start_deltas)
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_selected_blendShape()
        self.coordinate_label.setText('Flip Coordinate')
        self.coordinate_field.valueChanged.disconnect(self.update_flip_deltas_over_coordinate)
        self.c.axis_updated.disconnect(self.update_flip_deltas_over_coordinate)
        self.c.match_method_updated.disconnect(self.update_flip_deltas_over_coordinate)
        self.confirm_button.clicked.disconnect(self.confirm_flip_deltas_over_coordinate)
        self.cancel_button.clicked.disconnect(self.cancel_flip_deltas_over_coordinate)
        return

    def start_flip_deltas_with_plane(self):
        self.active_wtHolder_list = [x for x in self.selected_wtHolder_list if x.target_name]
        if not self.active_wtHolder_list:
            return
        self.active_start_deltas = self.active_wtHolder_list[0].get_deltas(self.position_list)
        self.rightClick_off()
        self.display_selected_weights = False
        self.load_shape_button.setEnabled(False)
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        blendShape_target = self.selected_wtHolder_list[0]
        self.loaded_object_label.setText('Flip Surface')
        self.object_type = 'nurbsSurface'
        self.confirm_button.clicked.connect(self.confirm_flip_deltas_with_plane)
        self.cancel_button.clicked.connect(self.cancel_flip_deltas_with_plane)
        self.c.match_method_updated.connect(self.update_flip_deltas_with_plane)
        self.load_object_button.clicked.connect(self.update_flip_deltas_with_plane)
        self.refresh_object_button.clicked.connect(self.update_flip_deltas_with_plane)
        self.update_flip_deltas_with_plane()
        return

    def update_flip_deltas_with_plane(self):
        if cmds.objExists(self.loaded_object):
            sel = om2.MSelectionList()
            sel.add(self.loaded_object)
            mFn = om2.MFnNurbsSurface(sel.getDependNode(0))
            mDagPath = sel.getDagPath(0)
            objMatrix = mDagPath.inclusiveMatrix()
            planeCenter = tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3]
            planeNormal = tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3]
            og_shape = cmds.listRelatives(cmds.listRelatives(self.shape, p=True)[0], s=True)[-1]
            self.ii_dict = None
            self.ibw_dict = None
            if self.matching_method == 'closestComponent':
                flipped_deltas, self.ii_dict = wt_utils.flip_deltas_with_plane(self.active_start_deltas, plane_position=planeCenter, plane_normal=planeNormal, matching_method=self.matching_method, source_shape=og_shape, max_distance=self.max_matching_distance_QSpinBox.value())
                self.active_wtHolder_list[0].set_deltas(flipped_deltas)
            elif self.matching_method == 'closestPointOnSurface':
                if cmds.nodeType(self.shape) == 'mesh':
                    flipped_deltas, self.ibw_dict = wt_utils.flip_deltas_with_plane(self.active_start_deltas, plane_position=planeCenter, plane_normal=planeNormal, matching_method=self.matching_method, source_shape=og_shape, max_distance=self.max_matching_distance_QSpinBox.value())
                    self.active_wtHolder_list[0].set_deltas(flipped_deltas)
                else:
                    cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
            elif self.matching_method == 'closestComponentUV':
                cmds.warning('Matching method "closestComponentUV" does not work with "Flip Deltas Over Plane"')
        return

    def confirm_flip_deltas_with_plane(self):
        self.update_flip_deltas_with_plane()
        if self.ii_dict or self.ibw_dict:
            sel = om2.MSelectionList()
            sel.add(self.loaded_object)
            mFn = om2.MFnNurbsSurface(sel.getDependNode(0))
            mDagPath = sel.getDagPath(0)
            objMatrix = mDagPath.inclusiveMatrix()
            planeCenter = tuple(mFn.getPointAtParam(0.5, 0.5) * objMatrix)[0:3]
            planeNormal = tuple(mFn.normal(0.5, 0.5) * objMatrix)[0:3]
            for i, each_blendShape in enumerate(self.active_wtHolder_list[1:]):
                deltas = each_blendShape.get_deltas(self.position_list)
                flipped_deltas, self.ii_dict = wt_utils.flip_deltas_with_plane(self.active_start_weights, plane_position=planeCenter, plane_normal=planeNormal, matching_method=self.matching_method, source_shape=self.shape, max_distance=self.max_matching_distance_QSpinBox.value())
                each_blendShape.set_deltas(flipped_deltas)

        self.rightClick_on()
        self.display_selected_weights = True
        self.load_shape_button.setEnabled(True)
        self.hide_extra_widgets()
        self.confirm_button.clicked.disconnect(self.confirm_flip_deltas_with_plane)
        self.cancel_button.clicked.disconnect(self.cancel_flip_deltas_with_plane)
        self.c.match_method_updated.disconnect(self.update_flip_deltas_with_plane)
        self.load_object_button.clicked.disconnect(self.update_flip_deltas_with_plane)
        self.refresh_object_button.clicked.disconnect(self.update_flip_deltas_with_plane)
        self.cancel_function = None
        self.update_selected_blendShape()
        return

    def cancel_flip_deltas_with_plane(self):
        self.active_wtHolder_list[0].set_deltas(self.active_start_deltas)
        self.confirm_button.clicked.disconnect(self.confirm_flip_deltas_with_plane)
        self.cancel_button.clicked.disconnect(self.cancel_flip_deltas_with_plane)
        self.c.match_method_updated.disconnect(self.update_flip_deltas_with_plane)
        self.load_object_button.clicked.disconnect(self.update_flip_deltas_with_plane)
        self.refresh_object_button.clicked.disconnect(self.update_flip_deltas_with_plane)
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_selected_blendShape()
        return

    def start_split_deltas_with_surface(self):
        self.active_wtHolder_list = [x for x in self.selected_wtHolder_list if x.target_name]
        if not self.active_wtHolder_list:
            return
        self.start_deltas_list = [x.get_deltas(self.position_list) for x in self.active_wtHolder_list]
        self.selection_off()
        self.rightClick_off()
        self.display_selected_weights = False
        self.falloff_parentWidget.setVisible(True)
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.loaded_object_label.setText('Split Surface')
        self.falloff_label.setText('Falloff Distance')
        self.falloff_label.setText('Falloff Distance')
        self.object_type = 'nurbsSurface'
        self.split_table_lower_widget.setVisible(True)
        self.split_target_tableWidget.drop_accept_type = 'delta'
        self.split_target_tableWidget.setRowCount(2)
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.text(0) for x in self.active_wtHolder_list])
        self.confirm_button.clicked.connect(self.confirm_split_deltas_with_surface)
        self.cancel_button.clicked.connect(self.cancel_split_deltas_with_surface)
        self.falloff_slider.valueChanged.connect(self.update_split_deltas_with_surface)
        self.load_object_button.clicked.connect(self.update_split_deltas_with_surface)
        self.refresh_object_button.clicked.connect(self.update_split_deltas_with_surface)
        self.split_target_tableWidget.drop_update_function = self.update_split_deltas_with_surface
        pos_list = [x[1][0] for x in list(self.start_deltas_list[0].items())]
        pos_list = [item for sublist in pos_list for item in sublist]
        pos_list = [abs(x) for x in pos_list]
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(200 * max(pos_list))
        self.update_split_deltas_with_surface()
        return

    def update_split_deltas_with_surface(self):
        if cmds.objExists(self.loaded_object):
            mask_weights = []
            used_node_list = []
            for column_num, start_deltas in enumerate(self.start_deltas_list):
                # FIX: the original split before this loop, reading start_deltas before it
                # existed, and wrote the deltas with set_weights instead of set_deltas.
                if mask_weights:
                    split_dict_list = [wt_utils.multiply_deltas_by_weights(weight_dictionary=mask_wt, delta_dictionary=start_deltas) for mask_wt in mask_weights]
                else:
                    split_dict_list, mask_weights = wt_utils.split_deltas_with_surface(start_deltas, self.loaded_object, falloff_distance=self.falloff_field.value())
                for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                    target_item = self.split_target_tableWidget.item(row_num, column_num)
                    if target_item:
                        if target_item.node not in used_node_list:
                            target_item.set_deltas(split_dict_list[row_num])
                            used_node_list.append(target_item.node)
                        else:
                            deltas = target_item.get_deltas(self.position_list)
                            sum_deltas = wt_utils.add_deltas(split_dict_list[row_num], deltas)
                            target_item.set_deltas(sum_deltas)

            last_weight_dict = mask_weights.pop(0)
            mask_weights.append(last_weight_dict)
            self.display_weights(mask_weights)
        return

    def confirm_split_deltas_with_surface(self):
        self.update_split_deltas_with_surface()
        self.selection_on()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_selected_blendShape()
        self.split_target_tableWidget.empty()
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_with_surface)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_with_surface)
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_with_surface)
        self.direction_pos_radio.clicked.disconnect(self.update_split_deltas_with_surface)
        self.direction_neg_radio.clicked.disconnect(self.update_split_deltas_with_surface)
        self.load_object_button.clicked.disconnect(self.update_split_deltas_with_surface)
        self.refresh_object_button.clicked.disconnect(self.update_split_deltas_with_surface)
        self.cancel_function = None
        return

    def cancel_split_deltas_with_surface(self):
        for column_num in range(self.split_target_tableWidget.columnCount() + 1):
            for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                target_item = self.split_target_tableWidget.item(row_num, column_num)
                if target_item:
                    target_item.set_deltas(target_item.start_deltas)

        for wtHolder, deltas in zip(self.active_wtHolder_list, self.start_deltas_list):
            wtHolder.set_deltas(deltas)

        self.selection_on()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.split_target_tableWidget.empty()
        self.update_selected_blendShape()
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_with_surface)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_with_surface)
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_with_surface)
        self.load_object_button.clicked.disconnect(self.update_split_deltas_with_surface)
        self.refresh_object_button.clicked.disconnect(self.update_split_deltas_with_surface)
        self.cancel_function = None
        return

    def start_split_deltas_at_coordinate(self):
        self.active_wtHolder_list = [wtHolder for wtHolder in self.selected_wtHolder_list if wtHolder.target_name]
        if not self.active_wtHolder_list:
            return
        self.start_deltas_list = [wtHolder.get_deltas(self.position_list) for wtHolder in self.active_wtHolder_list]
        self.rightClick_off()
        self.display_selected_weights = False
        self.falloff_parentWidget.setVisible(True)
        self.coordinate_parentWidget.setVisible(True)
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.coordinate_label.setText('Split Coordinate')
        self.falloff_label.setText('Falloff Distance')
        self.confirm_button.clicked.connect(self.confirm_split_deltas_at_coordinate)
        self.cancel_button.clicked.connect(self.cancel_split_deltas_at_coordinate)
        self.falloff_slider.valueChanged.connect(self.update_split_deltas_at_coordinate)
        self.coordinate_slider.valueChanged.connect(self.update_split_deltas_at_coordinate)
        self.axis_selector_X_radio.clicked.connect(self.update_split_deltas_at_coordinate)
        self.axis_selector_Y_radio.clicked.connect(self.update_split_deltas_at_coordinate)
        self.axis_selector_Z_radio.clicked.connect(self.update_split_deltas_at_coordinate)
        self.direction_pos_radio.pressed.connect(self.update_split_deltas_at_coordinate)
        self.direction_neg_radio.pressed.connect(self.update_split_deltas_at_coordinate)
        self.split_target_tableWidget.drop_update_function = self.update_split_deltas_at_coordinate
        pos_list = [x[1][0] for x in list(self.start_deltas_list[0].items())]
        pos_list = [pos for tuple in pos_list for pos in tuple]
        self.coordinate_slider.setMinimum(100 * min(pos_list))
        self.coordinate_slider.setMaximum(100 * max(pos_list))
        self.coordinate_field.setMinimum(min(pos_list))
        self.coordinate_field.setMaximum(max(pos_list))
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(100 * (max(pos_list) - min(pos_list)))
        self.split_table_lower_widget.setVisible(True)
        self.split_target_tableWidget.drop_accept_type = 'delta'
        self.split_target_tableWidget.setRowCount(2)
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.text(0) for x in self.active_wtHolder_list])
        self.split_target_tableWidget.drop_update_function = self.update_split_deltas_at_coordinate
        self.update_split_deltas_at_coordinate()
        return

    def update_split_deltas_at_coordinate(self):
        used_node_list = []
        mask_weights = []
        for column_num, start_deltas in enumerate(self.start_deltas_list):
            if mask_weights:
                split_dict_list = [wt_utils.multiply_deltas_by_weights(weight_dictionary=mask_wt, delta_dictionary=start_deltas) for mask_wt in mask_weights]
            else:
                split_dict_list, mask_weights = wt_utils.split_deltas(start_deltas, self.coordinate_field.value(), axis=self.axis, falloff_distance=self.falloff_field.value())
            for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                target_item = self.split_target_tableWidget.item(row_num, column_num)
                if target_item:
                    if target_item.text() not in used_node_list:
                        target_item.set_deltas(split_dict_list[row_num])
                        used_node_list.append(target_item.text())
                    else:
                        deltas = target_item.get_deltas(self.position_list)
                        sum_deltas = wt_utils.add_deltas(split_dict_list[row_num], deltas)
                        target_item.set_deltas(sum_deltas)

        last_weight_dict = mask_weights.pop(0)
        mask_weights.append(last_weight_dict)
        self.display_weights(mask_weights)
        return

    def confirm_split_deltas_at_coordinate(self):
        self.update_split_deltas_at_coordinate()
        self.selection_on()
        self.rightClick_on()
        self.display_selected_weights = True
        self.update_selected_blendShape()
        self.split_target_tableWidget.empty()
        self.hide_extra_widgets()
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_at_coordinate)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_at_coordinate)
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_at_coordinate)
        self.coordinate_slider.valueChanged.disconnect(self.update_split_deltas_at_coordinate)
        self.axis_selector_X_radio.clicked.disconnect(self.update_split_deltas_at_coordinate)
        self.axis_selector_Y_radio.clicked.disconnect(self.update_split_deltas_at_coordinate)
        self.axis_selector_Z_radio.clicked.disconnect(self.update_split_deltas_at_coordinate)
        self.direction_pos_radio.pressed.disconnect(self.update_split_deltas_at_coordinate)
        self.direction_neg_radio.pressed.disconnect(self.update_split_deltas_at_coordinate)
        self.cancel_function = None
        return

    def cancel_split_deltas_at_coordinate(self):
        for column_num in range(self.split_target_tableWidget.columnCount() + 1):
            for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                target_item = self.split_target_tableWidget.item(row_num, column_num)
                if target_item:
                    target_item.set_deltas(target_item.start_deltas)

        for wtHolder, deltas in zip(self.active_wtHolder_list, self.start_deltas_list):
            wtHolder.set_deltas(deltas)

        self.selection_on()
        self.rightClick_on()
        self.display_selected_weights = True
        self.update_selected_blendShape()
        self.split_target_tableWidget.empty()
        self.hide_extra_widgets()
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_at_coordinate)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_at_coordinate)
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_at_coordinate)
        self.coordinate_slider.valueChanged.disconnect(self.update_split_deltas_at_coordinate)
        self.axis_selector_X_radio.clicked.disconnect(self.update_split_deltas_at_coordinate)
        self.axis_selector_Y_radio.clicked.disconnect(self.update_split_deltas_at_coordinate)
        self.axis_selector_Z_radio.clicked.disconnect(self.update_split_deltas_at_coordinate)
        self.direction_pos_radio.pressed.disconnect(self.update_split_deltas_at_coordinate)
        self.direction_neg_radio.pressed.disconnect(self.update_split_deltas_at_coordinate)
        return

    def start_split_deltas_radially(self):
        self.active_wtHolder_list = [x for x in self.selected_wtHolder_list if x.target_name]
        if not self.active_wtHolder_list:
            return
        self.start_deltas_list = [x.get_deltas(self.position_list) for x in self.active_wtHolder_list]
        self.rightClick_off()
        self.display_selected_weights = False
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.falloff_parentWidget.setVisible(True)
        self.number_parentWidget.setVisible(True)
        self.split_table_lower_widget.setVisible(True)
        self.loaded_object_label.setText('Split Object')
        self.falloff_label.setText('Falloff Angle')
        self.object_type = 'transform'
        self.load_object_button_clicked()
        self.falloff_field.setMinimum(0)
        self.falloff_field.setMaximum(180)
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(18000)
        self.split_table_lower_widget.setVisible(True)
        self.split_target_tableWidget.drop_accept_type = 'delta'
        self.split_target_tableWidget.setRowCount(2)
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.text(0) for x in self.active_wtHolder_list])
        self.split_target_tableWidget.drop_update_function = self.update_split_deltas_radially
        split_number = int(self.number_field.value())
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        self.number_field.valueChanged.connect(self.update_split_deltas_radially)
        self.confirm_button.clicked.connect(self.confirm_split_deltas_radially)
        self.cancel_button.clicked.connect(self.cancel_split_deltas_radially)
        self.falloff_slider.valueChanged.connect(self.update_split_deltas_radially)
        self.load_object_button.clicked.connect(self.update_split_deltas_radially)
        self.refresh_object_button.clicked.connect(self.update_split_deltas_radially)
        self.update_split_deltas_radially()
        return

    def update_split_deltas_radially(self):
        split_number = int(self.number_field.value())
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        if cmds.objExists(self.loaded_object):
            split_object_string = self.loaded_object
            sel = om2.MSelectionList()
            sel.add(split_object_string)
            split_MMatrix = sel.getDagPath(0).inclusiveMatrix()
            used_node_list = []
            mask_weights = []
            for column_num, start_deltas in enumerate(self.start_deltas_list):
                if mask_weights:
                    split_dict_list = [wt_utils.multiply_deltas_by_weights(weight_dictionary=mask_wt, delta_dictionary=start_deltas) for mask_wt in mask_weights]
                else:
                    split_dict_list, mask_weights = wt_utils.split_deltas_radially(start_deltas, split_MMatrix, number_of_sections=split_number, falloff_angle=self.falloff_field.value())
                for row_num in range(split_number):
                    target_item = self.split_target_tableWidget.item(row_num, column_num)
                    if target_item:
                        if target_item.node not in used_node_list:
                            target_item.set_deltas(split_dict_list[row_num])
                            used_node_list.append(target_item.node)
                        else:
                            wts = target_item.get_deltas(self.position_list)
                            sum_wts = wt_utils.add_deltas(split_dict_list[row_num], wts)
                            target_item.set_deltas(sum_wts)

        last_weight_dict = mask_weights.pop(0)
        mask_weights.append(last_weight_dict)
        self.display_weights(mask_weights)
        return

    def confirm_split_deltas_radially(self):
        self.update_split_deltas_radially()
        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.update_selected_blendShape()
        self.split_target_tableWidget.empty()
        self.number_field.valueChanged.connect(self.update_split_deltas_radially)
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_radially)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_radially)
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_radially)
        self.load_object_button.clicked.disconnect(self.update_split_deltas_radially)
        self.refresh_object_button.clicked.disconnect(self.update_split_deltas_radially)
        self.cancel_function = None
        return

    def cancel_split_deltas_radially(self):
        for column_num in range(self.split_target_tableWidget.columnCount() + 1):
            for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                target_item = self.split_target_tableWidget.item(row_num, column_num)
                if target_item:
                    target_item.set_deltas(target_item.start_deltas)

        for wtHolder, deltas in zip(self.active_wtHolder_list, self.start_deltas_list):
            wtHolder.set_deltas(deltas)

        self.rightClick_on()
        self.display_selected_weights = True
        self.hide_extra_widgets()
        self.split_target_tableWidget.empty()
        self.update_selected_blendShape()
        self.number_field.valueChanged.connect(self.update_split_deltas_radially)
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_radially)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_radially)
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_radially)
        self.load_object_button.clicked.disconnect(self.update_split_deltas_radially)
        self.refresh_object_button.clicked.disconnect(self.update_split_deltas_radially)
        return

    def start_split_deltas_along_curve(self):
        self.active_wtHolder_list = [x for x in self.selected_wtHolder_list if x.target_name]
        if not self.active_wtHolder_list:
            return
        self.rightClick_off()
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.falloff_parentWidget.setVisible(True)
        self.number_parentWidget.setVisible(True)
        self.split_table_lower_widget.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.split_target_tableWidget.drop_accept_type = 'delta'
        split_number = int(self.number_field.value())
        self.split_target_tableWidget.setRowCount(len(color_vector_list))
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.name for x in self.active_wtHolder_list])
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        self.loaded_object_label.setText('Split Curve')
        self.falloff_label.setText('Falloff Distance')
        self.object_type = 'nurbsCurve'
        self.load_object_button_clicked()
        self.falloff_field.setMinimum(0)
        self.falloff_field.setMaximum(180)
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(300)
        self.start_deltas_list = [x.get_deltas(self.position_list) for x in self.active_wtHolder_list]
        self.falloff_slider.valueChanged.connect(self.update_split_deltas_along_curve)
        self.number_field.valueChanged.connect(self.update_split_deltas_along_curve)
        self.confirm_button.clicked.connect(self.confirm_split_deltas_along_curve)
        self.cancel_button.clicked.connect(self.cancel_split_deltas_along_curve)
        self.load_object_button.clicked.connect(self.update_split_deltas_along_curve)
        self.refresh_object_button.clicked.connect(self.update_split_deltas_along_curve)
        self.c.curve_method.connect(self.update_split_deltas_along_curve)
        self.split_target_tableWidget.drop_update_function = self.update_split_deltas_along_curve
        self.update_split_deltas_radially()
        return

    def update_split_deltas_along_curve(self):
        split_number = int(self.number_field.value())
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        if cmds.objExists(self.loaded_object):
            used_node_list = []
            mask_weights = []
            for column_num, start_deltas in enumerate(self.start_deltas_list):
                if mask_weights:
                    split_dict_list = [wt_utils.multiply_deltas_by_weights(weight_dictionary=mask_wt, delta_dictionary=start_deltas) for mask_wt in mask_weights]
                else:
                    split_dict_list, mask_weights = wt_utils.split_deltas_along_curve(start_deltas, self.loaded_object, falloff_distance=self.falloff_field.value(), split_number=int(self.number_field.value()), mode=self.curve_method)
                for row_num in range(split_number):
                    target_item = self.split_target_tableWidget.item(row_num, column_num)
                    if target_item:
                        if target_item.node not in used_node_list:
                            target_item.set_deltas(split_dict_list[row_num])
                            used_node_list.append(target_item.node)
                        else:
                            wts = target_item.get_deltas(self.position_list)
                            sum_wts = wt_utils.add_deltas(split_dict_list[row_num], wts)
                            target_item.set_deltas(sum_wts)

        last_weight_dict = mask_weights.pop(0)
        mask_weights.append(last_weight_dict)
        self.display_weights(mask_weights)
        return

    def confirm_split_deltas_along_curve(self):
        self.update_split_deltas_along_curve()
        self.rightClick_on()
        self.hide_extra_widgets()
        self.update_selected_blendShape()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_along_curve)
        self.number_field.valueChanged.disconnect(self.update_split_deltas_along_curve)
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_along_curve)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_along_curve)
        self.load_object_button.clicked.disconnect(self.update_split_deltas_along_curve)
        self.refresh_object_button.clicked.disconnect(self.update_split_deltas_along_curve)
        self.c.curve_method.disconnect(self.update_split_deltas_along_curve)
        self.cancel_function = None
        return

    def cancel_split_deltas_along_curve(self):
        for column_num in range(self.split_target_tableWidget.columnCount() + 1):
            for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                target_item = self.split_target_tableWidget.item(row_num, column_num)
                if target_item:
                    target_item.set_deltas(target_item.start_deltas)

        for wtHolder, deltas in zip(self.active_wtHolder_list, self.start_deltas_list):
            wtHolder.set_deltas(deltas)

        self.split_target_tableWidget.empty()
        self.rightClick_on()
        self.hide_extra_widgets()
        self.update_selected_blendShape()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_along_curve)
        self.number_field.valueChanged.disconnect(self.update_split_deltas_along_curve)
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_along_curve)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_along_curve)
        self.load_object_button.clicked.disconnect(self.update_split_deltas_along_curve)
        self.refresh_object_button.clicked.disconnect(self.update_split_deltas_along_curve)
        self.c.curve_method.disconnect(self.update_split_deltas_along_curve)
        self.cancel_function = None
        return

    def start_split_deltas_along_surface(self):
        self.active_wtHolder_list = [x for x in self.selected_wtHolder_list if x.target_name]
        if len(self.active_wtHolder_list) == 0:
            return
        self.rightClick_off()
        self.confirm_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.object_parentWidget.setVisible(True)
        self.falloff_parentWidget.setVisible(True)
        self.number_parentWidget.setVisible(True)
        self.split_table_lower_widget.setVisible(True)
        self.load_shape_button.setEnabled(False)
        self.split_target_tableWidget.drop_accept_type = 'delta'
        split_number = int(self.number_field.value())
        self.split_target_tableWidget.setRowCount(len(color_vector_list))
        self.split_target_tableWidget.setRowColors()
        self.split_target_tableWidget.setColumnCount(len(self.active_wtHolder_list))
        self.split_target_tableWidget.setHorizontalHeaderLabels([x.name for x in self.active_wtHolder_list])
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        self.loaded_object_label.setText('Split Surface')
        self.falloff_label.setText('Falloff Distance')
        self.object_type = 'nurbsSurface'
        self.load_object_button_clicked()
        self.falloff_field.setMinimum(0)
        self.falloff_field.setMaximum(180)
        self.falloff_slider.setMinimum(0)
        self.falloff_slider.setMaximum(300)
        self.start_deltas_list = [x.get_deltas(self.position_list) for x in self.active_wtHolder_list]
        self.falloff_slider.valueChanged.connect(self.update_split_deltas_along_surface)
        self.number_field.valueChanged.connect(self.update_split_deltas_along_surface)
        self.confirm_button.clicked.connect(self.confirm_split_deltas_along_surface)
        self.cancel_button.clicked.connect(self.cancel_split_deltas_along_surface)
        self.load_object_button.clicked.connect(self.update_split_deltas_along_surface)
        self.refresh_object_button.clicked.connect(self.update_split_deltas_along_surface)
        self.c.surface_method.connect(self.update_split_deltas_along_surface)
        self.update_split_deltas_along_surface()
        return

    def update_split_deltas_along_surface(self):
        split_number = int(self.number_field.value())
        for row_num in range(self.split_target_tableWidget.rowCount()):
            if row_num < split_number:
                self.split_target_tableWidget.showRow(row_num)
            else:
                self.split_target_tableWidget.hideRow(row_num)

        if cmds.objExists(self.loaded_object):
            used_node_list = []
            mask_weights = []
            for column_num, start_deltas in enumerate(self.start_deltas_list):
                if mask_weights:
                    split_dict_list = [wt_utils.multiply_deltas_by_weights(weight_dictionary=mask_wt, delta_dictionary=start_deltas) for mask_wt in mask_weights]
                else:
                    split_dict_list, mask_weights = wt_utils.split_deltas_along_surface(start_deltas, self.loaded_object, falloff_distance=self.falloff_field.value(), split_number=int(self.number_field.value()), mode=self.surface_method)
                for row_num in range(split_number):
                    target_item = self.split_target_tableWidget.item(row_num, column_num)
                    if target_item:
                        if target_item.node not in used_node_list:
                            target_item.set_deltas(split_dict_list[row_num])
                            used_node_list.append(target_item.node)
                        else:
                            wts = target_item.get_deltas(self.position_list)
                            sum_deltas = wt_utils.add_deltas(split_dict_list[row_num], wts)
                            target_item.set_deltas(sum_deltas)

            last_weight_dict = mask_weights.pop(0)
            mask_weights.append(last_weight_dict)
            self.display_weights(mask_weights)
        return

    def confirm_split_deltas_along_surface(self):
        self.update_split_deltas_along_surface()
        self.rightClick_on()
        self.hide_extra_widgets()
        self.update_selected_blendShape()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_along_surface)
        self.number_field.valueChanged.disconnect(self.update_split_deltas_along_surface)
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_along_surface)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_along_surface)
        self.load_object_button.clicked.disconnect(self.update_split_deltas_along_surface)
        self.refresh_object_button.clicked.disconnect(self.update_split_deltas_along_surface)
        self.c.surface_method.disconnect(self.update_split_deltas_along_surface)
        self.cancel_function = None
        return

    def cancel_split_deltas_along_surface(self):
        for column_num in range(self.split_target_tableWidget.columnCount() + 1):
            for row_num in range(self.split_target_tableWidget.rowCount() + 1):
                target_item = self.split_target_tableWidget.item(row_num, column_num)
                if target_item:
                    target_item.set_deltas(target_item.start_deltas)

        for wtHolder, deltas in zip(self.active_wtHolder_list, self.start_deltas_list):
            wtHolder.set_deltas(deltas)

        self.split_target_tableWidget.empty()
        self.rightClick_on()
        self.hide_extra_widgets()
        self.update_selected_blendShape()
        self.split_target_tableWidget.empty()
        self.falloff_slider.valueChanged.disconnect(self.update_split_deltas_along_surface)
        self.number_field.valueChanged.disconnect(self.update_split_deltas_along_surface)
        self.confirm_button.clicked.disconnect(self.confirm_split_deltas_along_surface)
        self.cancel_button.clicked.disconnect(self.cancel_split_deltas_along_surface)
        self.load_object_button.clicked.disconnect(self.update_split_deltas_along_surface)
        self.c.surface_method.disconnect(self.update_split_deltas_along_surface)
        self.refresh_object_button.clicked.disconnect(self.update_split_deltas_along_surface)
        return

    def add_copied_deltas(self):
        for blendShape_target in self.selected_wtHolder_list:
            deltas = blendShape_target.get_deltas(self.position_list)
            if not deltas:
                continue
            if self.shape == self.clipboard_deltas_shape:
                sum_deltas = wt_utils.add_deltas(deltas, self.clipboard_deltas)
                blendShape_target.set_deltas(sum_deltas)
            else:
                source_ip_dictionary = {index: position for index, (position, weight) in list(self.clipboard_deltas.items())}
                iip_dict = wt_utils.match_points_to_closest_point(source_ip_dictionary, self.ip_dictionary)
                matched_clipboard_deltas = wt_utils.match_points(iip_dict, self.clipboard_deltas)
                sum_deltas = wt_utils.add_deltas(deltas, matched_clipboard_deltas)
                blendShape_target.set_deltas(sum_deltas)

        return

    def subtract_copied_deltas(self):
        for blendShape_target in [wtHolder for wtHolder in self.selected_wtHolder_list if wtHolder.target_name]:
            deltas = blendShape_target.get_deltas(self.position_list)
            if self.shape == self.clipboard_deltas_shape:
                sum_deltas = wt_utils.subtract_deltas(deltas, self.clipboard_deltas)
                blendShape_target.set_deltas(sum_deltas)
            else:
                source_ip_dictionary = {index: position for index, (position, weight) in list(self.clipboard_deltas.items())}
                iip_dict = wt_utils.match_points_to_closest_point(source_ip_dictionary, self.ip_dictionary)
                matched_clipboard_deltas = wt_utils.match_points(iip_dict, self.clipboard_deltas)
                sum_deltas = wt_utils.subtract_deltas(deltas, matched_clipboard_deltas)
                blendShape_target.set_deltas(sum_deltas)

        return

    def save_deltas(self):
        for blendShape_target in [item for item in self.selected_wtHolder_list if item.target_name and not item.inBetween_name]:
            nice_name = ('{}.{}').format(blendShape_target.node, blendShape_target.target_name)
            filePath = cmds.fileDialog2(cap=('Save {} Weights To File').format(nice_name), fm=0, ds=1, ff='*json')
            if filePath == None:
                continue
            else:
                filePath = filePath[0]
                if '.json' not in filePath:
                    filePath = filePath + '.json'
            if cmds.nodeType(self.shape) == 'mesh':
                shape_data = wt_utils.get_shape_data(self.shape)
            else:
                shape_data = None
            deltas = blendShape_target.get_deltas(self.position_list)
            if not deltas:
                continue
            wt_utils.save_dictionary(filePath, deltas, shape_data)

        return

    def load_deltas(self):
        filePath = cmds.fileDialog2(ff='*.json', fm=1)
        if filePath == None:
            return {}
        else:
            filePath = filePath[0]
            deltas, shape_data = wt_utils.load_dictionary(filePath)
            if self.load_matching_method == 'index':
                if set(deltas.keys()) == set(self.ip_dictionary.keys()):
                    for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                        selected_deformer.set_deltas(deltas)

                else:
                    cmds.warning('deltas could not be loaded because the component indices do not match')
            elif self.load_matching_method == 'closestComponent':
                ii_dict = wt_utils.match_points_to_closest_point({index: position for index, (position, delta) in list(deltas.items())}, self.ip_dictionary)
                new_delta_dictionary = {new: [self.ip_dictionary[new][0], deltas[old][1]] for new, old in list(ii_dict.items())}
                for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                    selected_deformer.set_deltas(new_delta_dictionary)

            elif self.load_matching_method == 'closestPointOnSurface':
                if not shape_data:
                    cmds.warning(('The deltas cannot be loaded by "closestPointOnSurface" because {} does not contain any shape data').format(filePath[0]))
                    return
                new_shape = wt_utils.create_shape_from_data(shape_data)
                ibw_dict = wt_utils.match_points_to_closest_point_on_surface(new_shape, self.ip_dictionary)
                cmds.delete(cmds.listRelatives(new_shape, p=True))
                new_delta_dict = {}
                for new_id, (comp_ids, barycentric_weights) in list(ibw_dict.items()):
                    delta_partial_sum = []
                    for id, bary in zip(comp_ids, barycentric_weights):
                        delta_partial_sum.append([x * bary for x in deltas[id][1]])

                    new_delta_dict[new_id] = list(map(sum, list(zip(*delta_partial_sum))))

                new_delta_dictionary = {new_id: [self.ip_dictionary[new_id][0], new_delta_dict[new_id]] for new_id in list(ibw_dict.keys())}
                for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                    selected_deformer.set_deltas(new_delta_dictionary)

            elif self.load_matching_method == 'closestComponentUV':
                if cmds.nodeType(self.shape) != 'mesh' or shape_data[-1] != 'mesh':
                    cmds.warning(('The deltas cannot be loaded by "closestComponentUV" because {} is not a mesh').format(self.shape))
                    return
                points, verts, vert_connects, (U_list, V_list), shape_type = shape_data
                index_list = list(deltas.keys())
                temporary_shape_ip_dict = {}
                for index in index_list:
                    temporary_shape_ip_dict[index] = (
                     U_list[index], V_list[index], 0)

                if cmds.nodeType(self.shape):
                    i_UV_dict = wt_utils.convert_ip_dict_positions_to_UV_coordinates(self.ip_dictionary, self.shape)
                ii_dict = wt_utils.match_points_to_closest_point(temporary_shape_ip_dict, i_UV_dict)
                new_delta_dictionary = {new: [self.ip_dictionary[new][0], deltas[old][1]] for new, old in list(ii_dict.items())}
                for selected_deformer in [x for x in self.selected_wtHolder_list if not x.inBetween_name]:
                    selected_deformer.set_deltas(new_delta_dictionary)

            return

    def create_flipped_target(self):
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name and x.inBetween_weight == 1.0]
        if selected_items:
            LR_dict = {}
            LR_dict = _eval_literal(self.mirror_names_lineEdit.text())
            for item in selected_items:
                target_name = item.target_name
                valid_sub = False
                for left_string, right_string in list(LR_dict.items()):
                    if left_string in target_name:
                        flipped_target_name = target_name.replace(left_string, right_string)
                        valid_sub = True
                        break
                    elif right_string in target_name:
                        flipped_target_name = target_name.replace(right_string, left_string)
                        valid_sub = True
                        break

                if not valid_sub:
                    cmds.warning('This target does match any of entries in the mirror names dictionary')
                    target_list = cmds.aliasAttr(item.node, q=True)[::2]
                    flipped_target_name = target_name + '_flipped'
                    if flipped_target_name in target_list:
                        i = 1
                        while ('{}_flipped{}').format(target_name, i) in target_list:
                            i = +1

                        flipped_target_name = ('{}_flipped{}').format(target_name, i)
                new_target_name, new_target_index = wt_utils.add_empty_blendShape_target(item.node, target_name=flipped_target_name)
                new_item = blendShape_treeWidgetItem(item.parent(), [new_target_name])
                new_item.name = ('{} | {}').format(item.node, new_target_name)
                new_item.node = item.node
                new_item.target_name = new_target_name
                new_item.target_index = new_target_index
                new_item.inBetween_weight = 1.0
                new_item.shape = self.shape
                deltas = item.get_deltas()
                if self.matching_method == 'closestComponent':
                    ii_dict = None
                    stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ii')
                    stored_dict = False
                    if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                        ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                        stored_dict = True
                    deltas = item.get_deltas(self.position_list)
                    flipped_deltas, ii_dict = wt_utils.flip_deltas(deltas, flip_coordinate=0, axis=self.axis, matching_method=self.matching_method, source_shape=None, ii_dict=ii_dict, ibw_dict=None)
                    wt_utils.set_blendShape_target_deltas(item.node, flipped_target_name, flipped_deltas)
                    if not stored_dict:
                        cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                        cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
                elif self.matching_method == 'closestPointOnSurface':
                    if cmds.nodeType(self.shape) == 'mesh':
                        ibw_dict = None
                        stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ibw')
                        stored_dict = False
                        if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                            ibw_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                            stored_dict = True
                        deltas = item.get_deltas(self.position_list)
                        flipped_deltas, ibw_dict = wt_utils.flip_deltas(deltas, flip_coordinate=0, axis=self.axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=None, ibw_dict=ibw_dict)
                        wt_utils.set_blendShape_target_deltas(item.node, flipped_target_name, flipped_deltas)
                        if not stored_dict:
                            cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                            cmds.setAttr(self.shape + '.' + stored_attr, str(ibw_dict), type='string')
                    else:
                        cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
                elif self.matching_method == 'closestComponentUV':
                    if cmds.nodeType(self.shape) == 'mesh':
                        ii_dict = None
                        stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ii')
                        stored_dict = False
                        if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                            ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                            stored_dict = True
                        deltas = item.get_deltas(self.position_list)
                        flipped_deltas, ii_dict = wt_utils.flip_deltas(deltas, flip_coordinate=0, axis=self.axis, uv_axis=self.uv_axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=ii_dict, ibw_dict=None)
                        wt_utils.set_blendShape_target_deltas(item.node, flipped_target_name, flipped_deltas)
                        if not stored_dict:
                            cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                            cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
                    else:
                        cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')

        return

    def update_flipped_target(self):
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name and x.inBetween_weight == 1.0]
        if selected_items:
            LR_dict = {}
            LR_dict = _eval_literal(self.mirror_names_lineEdit.text())
            for item in selected_items:
                target_name = item.target_name
                valid_sub = False
                for left_string, right_string in list(LR_dict.items()):
                    if left_string in target_name:
                        flipped_target_name = target_name.replace(left_string, right_string)
                        valid_sub = True
                        break
                    elif right_string in target_name:
                        flipped_target_name = target_name.replace(right_string, left_string)
                        valid_sub = True
                        break

                if not valid_sub:
                    cmds.warning(('The target {}.{} does match any of entries in the mirror names dictionary').format(item.node, item.target_name))
                target_list = cmds.aliasAttr(item.node, q=True)[::2]
                if flipped_target_name in target_list:
                    deltas = item.get_deltas(self.position_list)
                    if self.matching_method == 'closestComponent':
                        ii_dict = None
                        stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ii')
                        stored_dict = False
                        if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                            ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                            stored_dict = True
                        for selected_deformer in self.selected_wtHolder_list:
                            flipped_deltas, ii_dict = wt_utils.flip_deltas(deltas, flip_coordinate=0, axis=self.axis, matching_method=self.matching_method, source_shape=None, ii_dict=ii_dict, ibw_dict=None)
                            wt_utils.set_blendShape_target_deltas(item.node, flipped_target_name, flipped_deltas)

                        if not stored_dict:
                            cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                            cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
                    elif self.matching_method == 'closestPointOnSurface':
                        if cmds.nodeType(self.shape) == 'mesh':
                            ibw_dict = None
                            stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ibw')
                            stored_dict = False
                            if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                                ibw_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                                stored_dict = True
                            for selected_deformer in self.selected_wtHolder_list:
                                flipped_deltas, ibw_dict = wt_utils.flip_deltas(deltas, flip_coordinate=0, axis=self.axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=None, ibw_dict=ibw_dict)
                                wt_utils.set_blendShape_target_deltas(item.node, flipped_target_name, flipped_deltas)

                            if not stored_dict:
                                cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                                cmds.setAttr(self.shape + '.' + stored_attr, str(ibw_dict), type='string')
                        else:
                            cmds.warning('Matching method "closestPointOnSurface" does not work with non-mesh type objects')
                    elif self.matching_method == 'closestComponentUV':
                        if cmds.nodeType(self.shape) == 'mesh':
                            ii_dict = None
                            stored_attr = ('{}_{}_{}_{}').format('flip', self.axis, self.direction_short, 'ii')
                            stored_dict = False
                            if cmds.attributeQuery(stored_attr, node=self.shape, exists=True):
                                ii_dict = _eval_literal(cmds.getAttr(self.shape + '.' + stored_attr))
                                stored_dict = True
                            for selected_deformer in self.selected_wtHolder_list:
                                flipped_deltas, ii_dict = wt_utils.flip_deltas(deltas, flip_coordinate=0, axis=self.axis, uv_axis=self.uv_axis, matching_method=self.matching_method, source_shape=self.shape, ii_dict=ii_dict, ibw_dict=None)
                                wt_utils.set_blendShape_target_deltas(item.node, flipped_target_name, flipped_deltas)

                            if not stored_dict:
                                cmds.addAttr(self.shape, ln=stored_attr, dt='string')
                                cmds.setAttr(self.shape + '.' + stored_attr, str(ii_dict), type='string')
                        else:
                            cmds.warning('Matching method "closestComponentUV" does not work with non-mesh type objects')

        return

    def duplicate_target(self):
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name and x.inBetween_weight == 1.0]
        for item in selected_items:
            dup_target_name, dup_target_index, inBetween_info = duplicate_blendShape_target(item.node, item.target_name, include_inBetweens=self.mirror_inBetweens_checkbox.isChecked())
            copied_weights = item.get_weights()
            set_blendShape_target_weights(item.node, dup_target_name, copied_weights)
            new_item = blendShape_treeWidgetItem(item.parent(), [dup_target_name])
            new_item.name = ('{} | {}').format(item.node, dup_target_name)
            new_item.node = item.node
            new_item.target_name = dup_target_name
            new_item.target_index = dup_target_index
            new_item.inBetween_weight = 1.0
            new_item.shape = self.shape
            for dup_inBetween_name, dup_target_weight in inBetween_info:
                new_item = blendShape_treeWidgetItem(new_item, [dup_inBetween_name])
                new_item.name = ('{} | {} | {}').format(item.node, dup_target_name, dup_inBetween_name)
                new_item.node = item.node
                new_item.target_name = dup_target_name
                new_item.target_index = dup_target_index
                new_item.inBetween_weight = dup_target_weight
                new_item.shape = self.shape

        return

    def add_inBetween(self):
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name and x.inBetween_weight == 1.0]
        for item in selected_items:
            current_weight = cmds.getAttr(('{}.{}').format(item.node, item.target_name))
            if current_weight != 0 and current_weight != 1.0:
                wt_utils.add_inBetween_blendShape_target(item.node, item.target_name, current_weight)
                new_item = blendShape_treeWidgetItem(item, [emptyInbetween])
                new_item.name = ('{} | {}').format(item.node, emptyInbetween)
                new_item.node = item.node
                new_item.target_name = dup_target_name
                new_item.target_index = dup_target_index
                new_item.inBetween_weight = current_weight
                new_item.shape = self.shape

        return

    def extract_target(self):
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name and x.inBetween_weight == 1.0]
        for item in selected_items:
            wt_utils.extract_blendShape_target(item.node, item.target_name)

        return

    def add_new_target(self):
        selected_items = [x for x in self.selected_wtHolder_list if cmds.nodeType(x.node) == 'blendShape' and not x.target_name]
        if selected_items:
            for item in selected_items:
                dup_target_name, dup_target_index = wt_utils.add_empty_blendShape_target(item.node, target_name='emptyTarget')
                new_item = blendShape_treeWidgetItem(item, [dup_target_name])
                new_item.name = ('{} | {}').format(item, dup_target_name)
                new_item.node = item.node
                new_item.target_name = dup_target_name
                new_item.target_index = dup_target_index
                new_item.inBetween_weight = 1.0
                new_item.shape = self.shape

        return

    def delete_target(self):
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name and x.inBetween_weight < 1]
        for item in selected_items:
            wt_utils.delete_inBetween_blendShape_target(item.node, item.target_name, item.inBetween_weight)
            item.parent().removeChild(item)

        selected_items = [x for x in self.selected_wtHolder_list if x.target_name and x.inBetween_weight == 1.0]
        for item in selected_items:
            wt_utils.delete_blendShape_target(item.node, item.target_name)
            item.parent().removeChild(item)

        return

    def make_radial(self):
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name and not x.inBetween_weight]
        for item in selected_items:
            wt_utils.make_blendShape_target_radial(item.node, item.target_name, center_point, rotation_vector=None)

        return

    def clear_deltas(self):
        for blendShape_target in self.selected_wtHolder_list:
            wt_utils.clear_deltas(blendShape_target.node, blendShape_target.target_name, blendShape_target.inBetween_weight)

        return

    def swap_deltas(self):
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name]
        if selected_items:
            if len(selected_items) > 1:
                if len(selected_items) > 2:
                    cmds.warning('"Swap Deltas" will only be performed for the first two selected items')
                    return
                deltas0 = selected_items[0].get_deltas()
                deltas1 = selected_items[1].get_deltas()
                selected_items[0].set_deltas(deltas1)
                selected_items[1].set_deltas(deltas0)
        return

    def bake_weights(self):
        for blendShape_target in self.selected_wtHolder_list:
            if blendShape_target.target_name:
                wt_utils.bake_weights_onto_blendShape_target(blendShape_target.node, blendShape_target.target_name)
                self.update_displayed_weights()

        return

    def replace_with_posed_target(self):
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name and x.inBetween_weight == 1]
        if not len(selected_items):
            return
        else:
            sel = cmds.ls(sl=True)
            if not len(sel):
                return
            try:
                selected_node = wt_utils.convert_transform_to_shape(sel[0])
            except:
                return

            if cmds.nodeType(selected_node) != cmds.nodeType(self.shape):
                cmds.warning(('{} is not the same shape type as {}').format(selected_node, self.shape))
                return
            if selected_node == self.shape:
                return
            selected_ip_dict = wt_utils.convert_shape_to_index_position_dictionary(selected_node, prePose=False, object_space=True)
            if len(self.ip_dictionary) != len(selected_ip_dict):
                return
            each_item = selected_items[0]
            target_index = wt_utils.get_blendShape_target_index(each_item.node, each_item.target_name)
            postDeformersMode = cmds.getAttr(each_item.node + ('.inputTarget[0].inputTargetGroup[{}].postDeformersMode').format(target_index))
            if postDeformersMode:
                postDeformersMode = True
            target_weight = cmds.getAttr(('{}.{}').format(each_item.node, each_item.target_name))
            if target_weight == 0:
                return
            num_inBetweens = each_item.childCount()
            if num_inBetweens:
                inBetween_list = [each_item.child(i) for i in range(num_inBetweens)]
                inBetween_list = sorted(inBetween_list, key=(lambda x: x.inBetween_weight))
                floor_inBetween = None
                floor_index = None
                exact_match = False
                for i, inBetween in enumerate(inBetween_list):
                    if inBetween.inBetween_weight < target_weight:
                        floor_inBetween = inBetween
                        floor_index = i
                    elif inBetween.inBetween_weight == target_weight:
                        exact_match = True
                        floor_inBetween = inBetween
                    else:
                        break

                if exact_match:
                    each_item = floor_inBetween
                    wt_utils.clear_deltas(each_item.node, each_item.target_name, inBetween_weight=each_item.inBetween_weight)
                    extracted_deltas = wt_utils.extract_deltas(self.shape, selected_ip_dict, post_deformation=postDeformersMode)
                    wt_utils.set_blendShape_target_deltas(floor_inBetween.node, floor_inBetween.target_name, extracted_deltas, inBetween_weight=floor_inBetween.inBetween_weight)
                elif floor_index == None:
                    each_item = inBetween_list[0]
                    wt_utils.clear_deltas(each_item.node, each_item.target_name, inBetween_weight=each_item.inBetween_weight)
                    extracted_deltas = wt_utils.extract_deltas(self.shape, selected_ip_dict, post_deformation=postDeformersMode)
                    floor_value = each_item.inBetween_weight
                    extracted_deltas = wt_utils.multiply_deltas(extracted_deltas, floor_value / target_weight)
                    wt_utils.set_blendShape_target_deltas(each_item.node, each_item.target_name, extracted_deltas, inBetween_weight=floor_value)
                elif floor_index == num_inBetweens - 1:
                    each_item = selected_items[0]
                    floor_deltas = wt_utils.get_blendShape_target_deltas(floor_inBetween.node, floor_inBetween.target_name, inBetween_weight=floor_inBetween.inBetween_weight)
                    extracted_deltas = wt_utils.extract_deltas(self.shape, selected_ip_dict, post_deformation=postDeformersMode)
                    floor_value = floor_inBetween.inBetween_weight
                    scaled_deltas = wt_utils.multiply_deltas(extracted_deltas, (1 - floor_value) / (target_weight - floor_value))
                    current_deltas = wt_utils.get_blendShape_target_deltas(each_item.node, each_item.target_name)
                    result_deltas = wt_utils.add_deltas(scaled_deltas, current_deltas)
                    wt_utils.set_blendShape_target_deltas(each_item.node, each_item.target_name, result_deltas, inBetween_weight=each_item.inBetween_weight)
                else:
                    multi_line_error = 'Deltas could not be set because the weightValue you are on is between two inBetweens.'
                    multi_line_error = '\nSo we cannot determine which one you want to modify.'
                    cmds.warning(multi_line_error)
                    wt_utils.set_blendShape_target_deltas(each_item.node, each_item.target_item, backup_deltas)
                    return
            else:
                wt_utils.clear_deltas(each_item.node, each_item.target_name)
                extracted_deltas = wt_utils.extract_deltas(self.shape, selected_ip_dict, post_deformation=postDeformersMode)
                wt_utils.set_blendShape_target_deltas(each_item.node, each_item.target_name, extracted_deltas)
                extracted_deltas = wt_utils.multiply_deltas(extracted_deltas, 1.0 / target_weight)
                wt_utils.set_blendShape_target_deltas(each_item.node, each_item.target_name, extracted_deltas)
            if not self.keep_extracted_shape_checkbox.isChecked():
                cmds.delete(cmds.listRelatives(selected_node, p=True))
            return

    def replace_target_with_default_shape(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        if cmds.nodeType(sel[0]) == 'transform':
            shapes = cmds.listRelatives(sel[0], s=True, f=True)
            if shapes:
                sel[0] = shapes[0]
            else:
                return
        selected_items = [x for x in self.selected_wtHolder_list if x.target_name]
        for item in selected_items:
            shape_list = cmds.blendShape(item.node, g=True, q=True)
            if not shape_list:
                cmds.error(('{} does not deform a shape').format(item.node))
                return
            if not cmds.nodeType(shape_list[0]) == cmds.nodeType(self.shape):
                cmds.error(('{} is not the same shape type as {}').format(shape_list[0], self.shape))
                return
            if not len(wt_utils.get_component_list(shape_list[0])) == len(self.position_list):
                cmds.error(('{} and {} do not having matching component counts').format(shape_list[0], self.shape))
                return
            target_index_list = cmds.aliasAttr(item.node, q=True)
            if not target_index_list:
                return
            target_list = target_index_list[0::2]
            index_list = target_index_list[1::2]
            index_list = [int(index.split('[')[1].split(']')[0]) for index in index_list]
            target_index_dict = dict(list(zip(target_list, index_list)))
            if item.target_name in target_list:
                target_index = target_index_dict[item.target_name]
            item_index = int(5000 + 1000 * item.inBetween_weight)
            if cmds.nodeType(sel[0]) == 'mesh':
                cmds.connectAttr(sel[0] + '.worldMesh', ('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(item.node, target_index, item_index))
            elif cmds.nodeType(sel[0]) == 'nurbsSurface':
                cmds.connectAttr(sel[0] + '.worldSpace', ('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(item.node, target_index, item_index))
            elif cmds.nodeType(sel[0]) == 'nurbsCurve':
                cmds.connectAttr(sel[0] + '.worldSpace', ('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(item.node, target_index, item_index))
            elif cmds.nodeType(sel[0]) == 'lattice':
                cmds.connectAttr(sel[0] + '.worldLattice', ('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(item.node, target_index, item_index))
            if not self.keep_extracted_shape_checkbox.checked():
                cmds.delete(sel[0])

        return

    def add_selection_as_posed_target(self):
        selected_items = [x for x in self.selected_wtHolder_list if cmds.nodeType(x.node) == 'blendShape' and not x.target_name]
        if len(selected_items):
            sel = cmds.ls(sl=True)
            if len(sel):
                if cmds.nodeType(sel[0]) == 'transform':
                    shapes = cmds.listRelatives(sel[0], s=True, f=True)
                    if shapes:
                        sel[0] = shapes[0]
                if cmds.nodeType(sel[0]) == cmds.nodeType(self.shape):
                    if sel[0] != self.shape:
                        new_target_name, new_target_index = wt_utils.add_empty_blendShape_target(selected_items[0].node, target_name=sel[0].split('|')[-1])
                        extracted_deltas = wt_utils.extract_deltas(self.shape, wt_utils.convert_shape_to_index_position_dictionary(sel[0], prePose=False))
                        wt_utils.set_blendShape_target_deltas(selected_items[0].node, new_target_name, extracted_deltas, inBetween_weight=1)
                if not self.keep_extracted_shape_checkbox.isChecked():
                    cmds.delete(sel[0])
        return

    def add_selection_as_default_target(self):
        selected_items = [x for x in self.selected_wtHolder_list if cmds.nodeType(x.node) == 'blendShape' and not x.target_name]
        if selected_items:
            sel = cmds.ls(sl=True)
            if not sel:
                return
            if cmds.nodeType(sel[0]) == 'transform':
                shapes = cmds.listRelatives(sel[0], s=True, f=True)
                if shapes:
                    sel[0] = shapes[0]
                else:
                    return
            for item in selected_items:
                new_target_name, new_target_index = wt_utils.add_empty_blendShape_target(selected_items[0].node, target_name=sel[0].split('|')[-1])
                shape_list = cmds.blendShape(item.node, g=True, q=True)
                if not shape_list:
                    cmds.error(('{} does not deform a shape').format(item.node))
                    return
                if not cmds.nodeType(shape_list[0]) == cmds.nodeType(self.shape):
                    cmds.error(('{} is not the same shape type as {}').format(shape_list[0], self.shape))
                    return
                if not len(wt_utils.get_component_list(shape_list[0])) == len(self.position_list):
                    cmds.error(('{} and {} do not having matching component counts').format(shape_list[0], self.shape))
                    return
                item_index = 6000
                if cmds.nodeType(sel[0]) == 'mesh':
                    cmds.connectAttr(sel[0] + '.worldMesh', ('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(item.node, new_target_index, item_index))
                elif cmds.nodeType(sel[0]) == 'nurbsSurface':
                    cmds.connectAttr(sel[0] + '.worldSpace', ('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(item.node, new_target_index, item_index))
                elif cmds.nodeType(sel[0]) == 'nurbsCurve':
                    cmds.connectAttr(sel[0] + '.worldSpace', ('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(item.node, new_target_index, item_index))
                elif cmds.nodeType(sel[0]) == 'lattice':
                    cmds.connectAttr(sel[0] + '.worldLattice', ('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[{}].inputGeomTarget').format(item.node, new_target_index, item_index))
                if not self.keep_extracted_shape_checkbox.checked():
                    cmds.delete(sel[0])

        return

    def toggleBlendShapeColumn(self):
        if self.showBlendShapeColumn.isChecked():
            self.blendShape_list_widget.setVisible(True)
        else:
            self.blendShape_list_widget.setVisible(False)
        return

    def toggleShowNonPaintable(self):
        if self.showNonPaintable_checkBox.isChecked():
            self.showNonPaintable = True
        else:
            self.showNonPaintable = False
        self.update_deformer_treeWidget_display()
        return

    def toggleShowCustomPaintable(self):
        if self.showCustomPaintable_checkBox.isChecked():
            self.showCustomPaintable = True
        else:
            self.showCustomPaintable = False
        self.update_deformer_treeWidget_display()
        return



def show():
    """Open (or re-open) the Deformer Utils window."""
    window = deformer_ui()
    window.show()
    return window


# The original opened the window as soon as the module was imported; kept.
# Use deformer_utils_ui.show() to open it again later in the same session.
show()

