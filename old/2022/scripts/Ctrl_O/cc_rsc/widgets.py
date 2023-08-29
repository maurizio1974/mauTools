"""
A bunch of widgets needed by the Control Creator derived from Qt Widgets with
some tweaks

2DO: the smooth method (catmull rom) should be changed to fit with the Maya shape smoothing method
     improve the draw_grid method of the viewer, calculate lines before then only render calculated lines, of course !!!
"""
from copy import copy
from functools import partial
from math import cos, sin, radians, tan

try:
    from PySide.QtCore import Qt, QPoint, QRect, QRectF, QPointF, QLineF
    from PySide.QtGui import QLineEdit, QDoubleValidator, QPainter, QColor, QWidget, QLinearGradient, QBrush, QPen, QComboBox, \
    QCheckBox, QLabel, QTreeWidget, QPushButton, QAbstractItemView, QHBoxLayout, QVBoxLayout, QIcon, QStandardItem, \
    QGroupBox, QSpinBox, QDialog, QRadioButton, QButtonGroup
except ImportError:
    from PySide2.QtCore import Qt, QPoint, QRect, QRectF, QPointF, QLineF
    from PySide2.QtGui import QDoubleValidator, QPainter, QColor, QLinearGradient, QBrush, QPen, QIcon, QStandardItem
    from PySide2.QtWidgets import QLineEdit, QWidget, QComboBox, QCheckBox, QLabel, QTreeWidget, QPushButton, \
        QAbstractItemView, QHBoxLayout, QVBoxLayout, QGroupBox, QSpinBox, QDialog, QRadioButton, QButtonGroup

from maya.cmds import getAttr, ls

from .funcs import V, get_maya_win

# some generic values
axis_eq = {'X': 0, 'Y': 1, 'Z': 2}

class DragSpinBox(QLineEdit):
    """
    derived from a QLineEdit, using the middle mouse from left to right will scale the
    value, a little green / red bar under the text zone shows you the percent of the
    current value
    """
    def __init__(self, parent, start=0.0, maxi=10, mini=-10, positive=False):
        super(DragSpinBox, self).__init__(parent)
        self.click = False
        self.setValidator(QDoubleValidator())
        self.setText(str(start))
        self.default = str(start)
        self.mouse_position = QPoint(0, 0)
        self.min = 0.01 if positive else mini
        self.max = maxi
        self.sup = positive

    def mousePressEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self.click = True
            self.mouse_position = e.pos()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self.click = False

    def mouseDoubleClickEvent(self, e):
        self.setText(self.default)

    def mouseMoveEvent(self, e):
        if self.click:
            delta = e.x() - self.mouse_position.x()
            v = float(self.text()) + delta / 100.0
            v = max(self.min, min(self.max, v))
            self.setText(str(v))
            self.mouse_position = e.pos()

    def paintEvent(self, e):
        super(DragSpinBox, self).paintEvent(e)
        p = QPainter()
        p.begin(self)
        v = float(self.text())
        v /= self.max if v > 0 else (self.min * -1)
        if self.sup:
            p.fillRect(QRect(0, self.height() - 2, v * self.width(), 2),
                       QColor(0, 255, 0))
        else:
            p.fillRect(QRect(self.width()/2, self.height() - 2, v * self.width() / 2, 2),
                       QColor(0, 255, 0) if v > 0 else QColor(255, 0, 0))
        p.end()

    def value(self):
        return float(self.text())


class DefaultField(QLineEdit):
    """
    A simple QLineEdit field which will override if empty and takes a different color
    """
    off_style = 'QLineEdit{color:rgb(125, 125, 125);}'
    on_style = 'QLineEdit{color:rgb(255, 255, 255);}'

    def __init__(self, parent=None, default=''):
        super(DefaultField, self).__init__(parent)
        self._value = ''
        self.default = ''
        self.setDefault(default)
        self.textChanged.connect(self.change)

    def setDefault(self, text):
        self.setText(text)
        self.default = text
        self.setStyleSheet(self.off_style)

    def change(self, text):
        if text != self.default:
            self.setStyleSheet(self.on_style)
            self.value = text
        else:
            self.setStyleSheet(self.off_style)

    def focusInEvent(self, e):
        if self.text() == self.default:
            self.setText('')
            self.setStyleSheet(self.on_style)

    def focusOutEvent(self, e):
        if self.text() == '':
            self.setText(self.default)
            self.setStyleSheet(self.off_style)

    @property
    def value(self):
        if self.text() == self.default:
            return ''
        else:
            return self._value

    @value.setter
    def value(self, text):
        self._value = text


class Filter(QLineEdit):
    def __init__(self, *args):
        super(Filter, self).__init__(*args)
        self.textChanged.connect(self.isClean)

        self.clear_button = QPushButton('x', self)
        self.clear_button.setVisible(False)
        self.clear_button.clicked.connect(self.clear)

    def isClean(self, text):
        # as long as text isn't empty we display the X button
        self.clear_button.setVisible(text != '')

    def resizeEvent(self, e):
        super(Filter, self).resizeEvent(e)
        self.clear_button.setGeometry(self.width() - 18, 2, 16, 16)


class Editable_List(QTreeWidget):
    editing = False

    class Edit(QLineEdit):
        def __init__(self, *args):
            super(Editable_List.Edit, self).__init__(*args)

        def keyPressEvent(self, e):
            if e.key() == Qt.Key_Escape:
                self.deleteLater()
            elif e.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.parent().parent().updateItem()
            else:
                super(Editable_List.Edit, self).keyPressEvent(e)

    def __init__(self, parent=None):
        super(Editable_List, self).__init__(parent)
        self.itemDoubleClicked.connect(self.double_click)
        self.itemClicked.connect(self.click)

    def double_click(self, item, col):
        # entering in editing mode
        edit = Editable_List.Edit(item.text(0), self)
        self.setItemWidget(item, 0, edit)
        edit.selectAll()
        self.editing = item

    def click(self, item, col):
        # if we click outside the edited item
        if self.editing and item is not self.editing:
            self.updateItem()

    def updateItem(self):
        """
        If an item has been edited we update the list and
        we (kindly) ask the parent to update the modified item
        """
        i = self.editing
        w = self.itemWidget(i, 0)

        # this means we're not on duplicate names
        if w and not self.findItems(w.text(), Qt.MatchExactly, 0):
            self.parent().update_controller(i.text(0), w.text())
            i.setText(0, w.text())
            self.scrollToItem(i)
            self.editing = False
        if i:
            self.removeItemWidget(i, 0)


class Control_Viewer(QWidget):
    """
    A widget made from nothing to display a controller, it's like a cheap
    3D view with some basic info display such as axis,
    with click + move cursor left - right - up - down will turn around the controller
    """
    class Shape_Pool(object):
        """
        Inner stack for the displayed shapes, with a direct conversion to Qlines
        """
        def __init__(self):
            super(Control_Viewer.Shape_Pool, self).__init__()
            self.shapes = []

        def flush(self, length):
            for idx in range(len(self.shapes) - 1, -1, -1):
                self.shapes.pop(idx)

            for i in range(length):
                self.shapes.append([])

        def __setitem__(self, key, points):
            pts = []
            if len(points):
                start = points[0]
                for pt in points[1:]:
                    pts.append(QLineF(start, pt))
                    start = pt
            self.shapes[key] = pts

        def __iter__(self):
            for shape in self.shapes:
                yield shape

    def __init__(self, parent=None):
        super(Control_Viewer, self).__init__(parent)
        self.shapes = []
        self.baked_lines = self.Shape_Pool()
        self.controller = ''

        self.mouse_pos = QPoint(0, 0)
        self.mouse_press = False

        # drawing settings
        self.draw_ref = False
        self.draw_axis = True

        # view settings
        self.scale = 30
        self.ref = 0.5
        self.rotation = 235
        self.height_rotate = 60

        # additionnal UI widgets
        self.ref_display = QCheckBox('joint', self)
        sheet = '''
        QCheckBox {color:white;}
        QCheckBox:unchecked {color:rgb(212, 201, 206);}
        QCheckBox::indicator {width: 10px;height: 10px;background:rgb(34, 38, 45);
            border:1px solid rgb(134, 138, 145);border-radius:5px;}
        QCheckBox::indicator:hover {background:rgb(34, 108, 185);border:1px solid white;
            border-radius:5px;}
        QCheckBox::indicator:checked{background:rgb(74, 168, 235);border:2px solid rgb(34, 108, 185);
            padding:-1px;}
        QCheckBox::indicator:checked:hover{background:rgb(74, 168, 235);border:1px solid white;
            padding:0px;}
        '''
        self.ref_display.setStyleSheet(sheet)
        self.ref_display.setGeometry(5, -2, self.ref_display.width(), self.ref_display.height())
        self.ref_display.stateChanged.connect(self.toggle_ref)

        self.axis_display = QCheckBox('axis', self)
        self.axis_display.setStyleSheet(sheet)
        self.axis_display.setGeometry(5, 13, self.axis_display.width(), self.axis_display.height())
        self.axis_display.stateChanged.connect(self.toggle_axis)
        self.axis_display.setChecked(True)

        self.infos = QLabel('', self)
        self.infos.setStyleSheet('QLabel {color:rgb(134, 138, 145);}')

        # color attributes
        gradient = QLinearGradient(QRectF(self.rect()).bottomLeft(), QRectF(self.rect()).topLeft())
        gradient.setColorAt(0, QColor(24, 26, 28))
        gradient.setColorAt(1, QColor(124, 143, 163))
        self.background = QBrush(gradient)
        self.controller_pen = QPen(QColor(240, 245, 255), 1.5)
        self.axis_pens = [QPen(QColor(255, 0, 0), 0.5), QPen(QColor(0, 255, 0), 0.5), QPen(QColor(125, 125, 255), 0.5)]
        self.sub_grid_pen = QPen(QColor(74, 78, 75), .25)

    def resizeEvent(self, *args, **kwargs):
        # updating the background's gradient to fit with the new window's size
        gradient = QLinearGradient(QRectF(self.rect()).bottomLeft(), QRectF(self.rect()).topLeft())
        gradient.setColorAt(0, QColor(44, 46, 48))
        gradient.setColorAt(1, QColor(124, 143, 163))
        self.background = QBrush(gradient)

    def toggle_axis(self, state):
        self.draw_axis = state
        self.repaint()

    def toggle_ref(self, state):
        self.draw_ref = state
        self.repaint()

    def draw_grid(self, painter):
        """
        we draw the grid of the viewport, displaying the main axis bolder
        """
        # drawing some axis lines depending on the self.ref value, which is the
        # reference size of the scene, depending on jointDisplayScale, joint's selection radius
        if self.draw_axis:
            parent_main_axis = self.parent().rotate_order.currentText()
            for x in range(3):
                self.axis_pens[x].setWidthF(0.5)
            self.axis_pens[axis_eq[parent_main_axis[0]]].setWidthF(1.5)
            painter.setPen(self.axis_pens[0])
            painter.drawLine(self.conv_3D_to_2D(0, 0, 0), self.conv_3D_to_2D(100, 0, 0))
            painter.setPen(self.sub_grid_pen)
            step = self.ref if self.ref > 0.3 else (5*self.ref if self.ref > 0.05 else 50*self.ref)
            rows = int(10 * (1 / step) * 0.75)

            for i in range(-rows, rows):
                painter.drawLine(self.conv_3D_to_2D(-100, 0, i * step), self.conv_3D_to_2D(100, 0, i * step))
                painter.drawLine(self.conv_3D_to_2D(i * step, 0, -100), self.conv_3D_to_2D(i * step, 0, 100))

            painter.setPen(self.axis_pens[1])
            painter.drawLine(self.conv_3D_to_2D(0, 0, 0), self.conv_3D_to_2D(0, 100, 0))
            painter.setPen(self.axis_pens[2])
            painter.drawLine(self.conv_3D_to_2D(0, 0, 0), self.conv_3D_to_2D(0, 0, 100))

        # drawing a joint shape in light grey as a reference
        if self.draw_ref:
            painter.setPen(QPen(QColor(125, 165, 185), 0.8))
            sp = [[0.0, 0.0, 1.0], [-0.5, 0.0, 0.87], [-0.87, 0.0, 0.5], [-1.0, 0.0, 0.0], [-0.87, 0.0, -0.5], [-0.5, 0.0, -0.87], [0.0, 0.0, -1.0], [0.5, 0.0, -0.87], [0.87, 0.0, -0.5], [1.0, 0.0, 0.0], [0.87, 0.0, 0.5], [0.5, 0.0, 0.87], [0.0, 0.0, 1.0], [0.0, 0.7, 0.7], [0.0, 1.0, 0.0], [0.0, 0.7, -0.7], [0.0, 0.0, -1.0], [0.0, -0.7, -0.7], [0.0, -1.0, 0.0], [-0.5, -0.87, 0.0], [-0.87, -0.5, 0.0], [-1.0, 0.0, 0.0], [-0.87, 0.5, 0.0], [-0.5, 0.87, 0.0], [0.0, 1.0, 0.0], [0.5, 0.87, 0.0], [0.87, 0.5, 0.0], [1.0, 0.0, 0.0], [0.87, -0.5, 0.0], [0.5, -0.87, 0.0], [0.0, -1.0, 0.0], [0.0, -0.7, 0.7], [0.0, 0.0, 1.0]]
            for i, p in enumerate(sp[:-1]):
                s, e = V(p), V(sp[i + 1])
                s *= self.ref * 0.5
                e *= self.ref * 0.5
                painter.drawLine(self.conv_3D_to_2D(*s), self.conv_3D_to_2D(*e))

        height = 40
        info = 'degree%s : %i' % ('s' if self.shapes[0].degrees > 1 else '', self.shapes[0].degrees)
        info += '\nclosed : %s' % ('no', 'yes')[bool(self.shapes[0].closed)]
        if len(self.shapes) > 1:
            info += '\nshapes : %i' % len(self.shapes)
            height += 20
        self.infos.setText(info)
        self.infos.setFixedHeight(height)
        self.infos.setGeometry(10, self.height() - height, self.width(), self.infos.height())

    def paintEvent(self, e):
        """
        here we paint the controller lines
        """
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(painter.Antialiasing)
        painter.setBrush(self.background)
        painter.drawRoundedRect(QRect(0, 0, self.size().width(), self.size().height()), 4, 4)
        # painter.fillRect(QRect(0, 0, self.size().width(), self.size().height()), self.background)
        self.draw_grid(painter)
        painter.setPen(self.controller_pen)

        for shape in self.baked_lines:
            painter.drawLines(shape)

        painter.end()

    def mousePressEvent(self, e):
        if e.button() == 1:
            self.mouse_pos = e.pos()

    def wheelEvent(self, e):
        self.scale = max(self.scale + e.delta() / 40, 10)
        self.setCoords()

    def mouseMoveEvent(self, e):
        """
        When the mouse moves we inject the delta into our two view rotates
        cropping the vertical rotate
        """
        delta = self.mouse_pos - e.pos()
        self.rotation -= delta.x()
        self.height_rotate = min(max(self.height_rotate + delta.y(), 60), 120)
        self.mouse_pos = e.pos()
        self.setCoords()

    def conv_3D_to_2D(self, x, y, z):
        """
        Cheap conversion from 3D coordinates to 2D coordinates,
        depends on the view (self.rotation & self.height_rotate)
        :param x: X Coordinate
        :type  x: int
        :param y: Y Coordinate
        :type  y: int
        :param z: Z Coordinate
        :type  z: int
        :return : 2D coordinates as QPointF
        :rtype  : QPointF
        """
        X = x*cos(radians(self.rotation))
        X -= z*cos(radians(-self.rotation + 90))
        X *= self.scale

        # the Y coordinate is the key to fake the the vertical camera rotation
        # first '2D' projection
        Y = (x*sin(radians(self.rotation)) - y + z*sin(radians(-self.rotation + 90)))*self.scale
        # then we 'round' the vertical rotate, this make an uniform scaling
        # on the shape when the camera turns up & down
        Y *= cos(radians(self.height_rotate))
        # then we push compensations from the y attribute of the point
        Y += y * self.scale * (tan(radians(90 - self.height_rotate)) + sin(radians(self.height_rotate)))
        Y *= -1
        # finally we 'center' the point in the view
        X += self.width()*.5
        Y += self.height()*.5
        return QPointF(X, Y)

    def smooth(self, crd, deg, closed):
        """
        Smoothing the given coordinates (crd) using the catmull rom method,
        to be honest the deg isn't so important because catmull rom have it's
        own division method, but we set the degrees as the number of division
        of the catmull rom method, this is not the right way, must be change
        to fit with the Maya's method
        :param    crd: shape's coordinates
        :type     crd: list
        :param    deg: shape's degrees
        :type     deg: int
        :param closed: is shape closed ?
        :type  closed: bool
        :return: smoothed points
        :rtype: list
        """
        pts = []
        l = len(crd)
        # mapping the division's steps
        div_map = [j / float(deg) for j in range(deg)]
        for i in range(0, l + 1):
            if (i < 0 or (i - deg) > l) and closed:
                continue
            if (i <= 0 or (i + deg) > l) and not closed:
                continue
            p0 = V(crd[i - 1])
            p1 = V(crd[i if i < l else (i - l)])
            p2 = V(crd[(i + 1) if (i + 1) < l else (i + 1 - l)])
            p3 = V(crd[(i + 2) if (i + 2) < l else (i + 2 - l)])

            # CUBIC       spline smoothing #
            # a = p3 - p2 - p0 + p1
            # b = p0 - p1 - a
            # c = p2 - p0
            # d = p1
            # for j in range(deg):
            #     t = j / float(deg)
            #     t2 = t**2
            #     pos = a*t*t2 + b*t2 + c*t + d

            # CATMULL ROM   spline smoothing #

            a = .5 * (p1 * 2)
            b = .5 * (p2 - p0)
            c = .5 * (2 * p0 - 5 * p1 + 4 * p2 - p3)
            d = .5 * (-1 * p0 + 3 * p1 - 3 * p2 + p3)

            for j, t in enumerate(div_map):
                pos = a + (b * t) + (c * t * t) + (d * t * t * t)
                pts.append(pos)

        return pts

    def load(self, shapes):
        """
        This function update the viewport with new shapes, cleaning old stuff
        and smoothing the shape using the Catmull Rom method (see smooth method above)
        """
        self.shapes = shapes

        for i, shape in enumerate(self.shapes):
            if shape.degrees != 1 and not shape.smooth:
                shape.coords = self.smooth(copy(shape.coords), shape.degrees, shape.closed)
                shape.smooth = True
                shape.apply_transform()

        self.setCoords()

    def setCoords(self):
        """
        This function refresh the 2D lines' array
        """
        self.baked_lines.flush(len(self.shapes))

        for i, shape in enumerate(self.shapes):
            self.set_shape_coords(shape, i)

        self.update()

    def set_shape_coords(self, shape, shape_index):
        """
        This converts the shape's transformed coordinates into
        2D points for the viewer's drawing, then sent to the self.baked_lines
        for QLines conversion and final storage
        """
        pts_2D = []

        for pt in shape.transformed_coords:
            pts_2D.append(self.conv_3D_to_2D(*pt))

        # if the shape is closed we add the first points to close the loop
        if shape.closed and shape.degrees == 1:
            pts_2D.append(self.conv_3D_to_2D(*shape.transformed_coords[0]))

        # sending for Qlines conversion
        self.baked_lines[shape_index] = pts_2D


class Color_Picker(QComboBox):
    """
    A simple list with a rectangle at its right display the currently
    selected color
    """
    colors_order = ['blue', 'red', 'green', 'yellow', 'purple', 'greenblue', 'lightred', 'skin']
    colors_name = {'red': 13, 'green': 14, 'purple': 9, 'blue': 6, 'yellow': 17,
                   'greenblue': 28, 'lightred': 4, 'skin': 21}
    colors_code = {13: QColor(255, 0, 0), 14: QColor(0, 255, 0),
                   9: QColor(255, 0, 255), 6: QColor(0, 0, 255),
                   17: QColor(255, 255, 0), 28: QColor(48, 161, 161),
                   4: QColor(155, 0, 40), 21: QColor(255, 176, 176)}

    def __init__(self, *args, **kwargs):
        super(Color_Picker, self).__init__(*args, **kwargs)
        for i, color in enumerate(self.colors_order):
            self.addItem(color)
            self.setItemData(i, self.colors_code[self.colors_name[color]])

    def paintEvent(self, e):
        w = self.width()
        self.setFixedWidth(w - 20)
        super(Color_Picker, self).paintEvent(e)
        self.setFixedWidth(w)
        p = QPainter()
        p.begin(self)
        p.setPen(Qt.NoPen)
        color = copy(self.itemData(self.currentIndex()))
        if not self.isEnabled():
            color = color.lighter()
        p.setBrush(color)
        p.drawRect(QRect(w - 17, 2, 16, 16))
        p.end()

    def color(self):
        return self.colors_name[self.currentText()]


class Capture(QDialog):
    """
    This is the Capture dialog when you click on the "Capture" button
    this provide a simple interface with some settings on how you want
    to save the selected shapes
    """
    def __init__(self, parent=None, default_name='test', degrees=1, closed=False):
        def line(*widgets):
            l = QHBoxLayout()
            for widget in widgets:
                l.addWidget(widget)
            return l

        super(Capture, self).__init__(parent)

        self.title = 'Capture controller'

        self.setWindowTitle(self.title)
        self.setObjectName(self.title)
        self.setWindowFlags(Qt.Dialog)

        # we check if the objects have transform values, if not we set the has_tsf
        # flags to False
        has_pos_tsf, has_rot_tsf = True, True
        for obj in ls(sl=True):
            has_pos_tsf &= bool(sum([getAttr('%s.t%s' % (obj, axis)) for axis in 'xyz']))
            has_rot_tsf &= bool(sum([getAttr('%s.r%s' % (obj, axis)) for axis in 'xyz']))

        # UI STUFFS
        self.setFixedSize(230, 120)

        # Centering the dialog by the parent
        x = parent.width() / 2 - self.width() / 2
        y = parent.height() / 2 - self.height() / 2
        self.setGeometry(parent.x() + x, parent.y() + y, self.width(), self.height())

        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(10, 8, 10, 4)

        self.name = QLineEdit(default_name, self)
        self.name.selectAll()
        self.degrees = QSpinBox(self)
        self.degrees.setValue(degrees)
        self.degrees.setToolTip("The number of degrees for this shape")
        self.closed = QCheckBox('Closed', self)
        self.closed.setChecked(bool(closed))
        self.closed.setToolTip("If the shape is closed ? (Periodic > 0)")

        self.absolute_pos = QRadioButton('Absolute', self)
        self.absolute_pos.setChecked(not has_pos_tsf)
        self.absolute_pos.setToolTip("Getting translates as absolute will bake the translates "
                                     "of the shape in world space into the shape's coordinates")

        self.relative_pos = QRadioButton('Relative', self)
        self.relative_pos.setChecked(has_pos_tsf)
        self.absolute_pos.setToolTip("Getting translates as relative will ignore the translates "
                                     "of the shape in world space")

        local_group = QButtonGroup(self)
        local_group.addButton(self.absolute_pos)
        local_group.addButton(self.relative_pos)

        self.absolute_rot = QRadioButton('Absolute', self)
        self.absolute_rot.setChecked(not has_rot_tsf)
        self.absolute_pos.setToolTip("Getting rotations as absolute will bake the rotations "
                                     "of the shape in world space into the shape's coordinates")

        self.relative_rot = QRadioButton('Relative', self)
        self.relative_rot.setChecked(has_rot_tsf)
        self.absolute_pos.setToolTip("Getting rotations as relative will ignore the rotations "
                                     "of the shape in world space")

        local_group = QButtonGroup(self)
        local_group.addButton(self.absolute_rot)
        local_group.addButton(self.relative_rot)

        self.OK = QPushButton('Valid', self)
        self.Cancel = QPushButton('Cancel', self)

        self.layout().addLayout(line(QLabel('Controller\'s name', self), self.name))

        self.keep = None
        # if there is more than one shape selected we allow the user to keep the
        # individual shape's settings
        if len(ls(sl=True)) > 1:
            self.keep = QCheckBox('Keep individual shape\'s setting', self)
            self.keep.stateChanged.connect(self.degrees.setDisabled)
            self.keep.stateChanged.connect(self.closed.setDisabled)
            self.keep.setChecked(True)
            self.layout().addWidget(self.keep)

        self.layout().addLayout(line(QLabel('Shape\'s degrees', self), self.degrees,
                                     self.closed))
        self.layout().addLayout(line(QLabel('Position space', self), self.absolute_pos, self.relative_pos))
        self.layout().addLayout(line(QLabel('Rotation space', self), self.absolute_rot, self.relative_rot))
        self.layout().addLayout(line(self.Cancel, self.OK))
        self.OK.clicked.connect(partial(self.close, True))
        self.Cancel.clicked.connect(partial(self.close, False))

        # this is the function which will be run when the dialog correctly close
        self.func = None

    # BUILT IN functions

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.close(True)
        elif e.key() == Qt.Key_Escape:
            self.close(False)
        else:
            super(Capture, self).keyPressEvent(e)

    def show(self, next_function=None):
        if next_function:
            super(Capture, self).show()
            self.func = next_function

    def close(self, state=False, *args):
        if state:
            # if we receive a valid close order we make up the arguments' list
            # just sending 3 args if we have multiple shapes and we want to use
            # each own shape's setting (self.keep).
            args = [self.name.text(), self.absolute_pos.isChecked(), self.absolute_rot.isChecked()]
            if self.keep and not self.keep.isChecked() or not self.keep:
                args.append(self.degrees.value())
                args.append(self.closed.isChecked())

            # forwarding arguments to the previously given function
            self.func(*args)

        super(Capture, self).close()


class Ctrl_O_UI(QWidget):
    """
    This is the main Ctrl-O user interface layout
    """
    def __init__(self, parent=None):
        super(Ctrl_O_UI, self).__init__(parent)
        self.title = u'Ctrl \u0298'

        try:
            [c.close() for c in get_maya_win().findChildren(QWidget, self.title)]
        except TypeError:
            pass

        self.setWindowTitle(self.title)
        self.setObjectName(self.title)
        self.setWindowFlags(Qt.Dialog)
        self.setFixedSize(400, 550)
        self.container = QHBoxLayout()
        self.setLayout(QVBoxLayout())

        column = QVBoxLayout()
        self.filter = Filter(self)
        column.addWidget(self.filter)

        self.controller_list = Editable_List(self)
        self.controller_list.setFixedWidth(175)
        self.controller_list.setHeaderHidden(True)
        self.controller_list.setSortingEnabled(True)
        self.controller_list.setRootIsDecorated(False)
        self.controller_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.controller_list.sortByColumn(0, Qt.AscendingOrder)
        self.controller_list.setUniformRowHeights(True)
        self.controller_list.setAlternatingRowColors(True)
        self.controller_list.setStyleSheet('''QTreeView{alternate-background-color: #3b3b3b;}
        QTreeView::item {padding:3px;}
        QTreeView::item:!selected:hover {
            background-color: #5b5b5b;
            margin-left:-3px;
            border-left:0px;
        }
        QTreeView::item:selected {
            background-color: #6a485c;
            border-left:2px solid #cf6f9f;
            padding-left:2px;
        }
        QTreeView::item:selected:hover {
            background-color: #7a586c;
            border-left:2px solid #cf6f9f;
            padding-left:2px;
        }
        ''')

        column.addWidget(self.controller_list)
        self.capture = QPushButton('Capture', self)
        self.capture.setIcon(QIcon(':snapshot'))
        self.capture.setStyleSheet('QPushButton:hover{background:#5f5f5f;border-radius:4px;border:2px solid #00FF00;}')

        self.pop = QPushButton('Del', self)
        self.pop.setIcon(QIcon(':removeRenderable'))
        self.pop.setStyleSheet('QPushButton:hover{background:#5f5f5f;border-radius:4px;border:2px solid red;}')
        self.pop.setFixedWidth(50)

        line = QHBoxLayout()
        line.addWidget(self.capture)
        line.addWidget(self.pop)
        line.setSpacing(2)
        column.addLayout(line)
        column.setSpacing(2)
        self.container.addLayout(column)

        column = QVBoxLayout()
        self.viewer = Control_Viewer(self)
        self.viewer.setFixedSize(200, 150)

        self.name_prefix = DefaultField(self, 'pre_')
        self.name_prefix.setText('cc')
        self.name_prefix.setFixedWidth(30)
        self.name = DefaultField(self, 'Auto naming')
        self.name.setFixedWidth(78)
        self.name_suffix = DefaultField(self, '_suf')
        self.name_suffix.setFixedWidth(30)

        self.radius = DragSpinBox(self, start=1.0, maxi=100, positive=True)

        self.offsetX = DragSpinBox(self, mini=-1000, maxi=1000)
        self.offsetY = DragSpinBox(self, mini=-1000, maxi=1000)
        self.offsetZ = DragSpinBox(self, mini=-1000, maxi=1000)
        self.offset = lambda: [self.offsetX.value(), self.offsetY.value(), self.offsetZ.value()]

        self.factorX = DragSpinBox(self, start=1.0, mini=-1, maxi=1)
        self.factorY = DragSpinBox(self, start=1.0, mini=-1, maxi=1)
        self.factorZ = DragSpinBox(self, start=1.0, mini=-1, maxi=1)
        self.factor = lambda: [self.factorX.value(), self.factorY.value(), self.factorZ.value()]

        self.rotate_order = QComboBox(self)
        axis_orders = ['XYZ', 'YXZ', 'ZYX']
        for x in axis_orders:
            it = QStandardItem(x[0])
            self.rotate_order.addItem(x[0], it)
            self.rotate_order.setItemData(axis_eq[x[0]], x)

        self.color_picker = Color_Picker(self)

        def line(title, *widgets):
            layout = QHBoxLayout()
            layout.setContentsMargins(1, 1, 1, 1)
            label = QLabel(title, self)
            layout.addWidget(label)
            for widget in widgets:
                layout.addWidget(widget)
            return layout

        def col(*widgets):
            layout = QVBoxLayout()
            for widget in widgets:
                layout.addLayout(widget)
            return layout

        column.addWidget(self.viewer)

        name_line = line('Name : ', self.name_prefix, self.name, self.name_suffix)
        name_line.setSpacing(0)
        name_line.setContentsMargins(0, 0, 0, 0)

        sub_col = col(name_line,
                      line('Radius : ', self.radius),
                      line('Offset : ', self.offsetX, self.offsetY, self.offsetZ),
                      line('Factor : ', self.factorX, self.factorY, self.factorZ),
                      line('Axis : ', self.rotate_order),
                      line('Color : ', self.color_picker))
        sub_col.setContentsMargins(5, 10, 0, 5)
        column.addLayout(sub_col)

        column.setSpacing(2)
        group = QGroupBox(self)
        group.setTitle('Parenting')
        glay = QVBoxLayout()
        glay.setSpacing(2)
        glay.setContentsMargins(4, 4, 4, 4)

        self.zero = QCheckBox('Zero Controller', self)
        self.parent_shape = QCheckBox('Parent Shape to Transform', self)

        zline = QHBoxLayout()
        zline.addWidget(self.zero)
        self.zero_iter = QSpinBox(self)
        self.zero_iter.setMinimum(1)
        self.zero_iter.setMaximum(5)
        self.zero_iter.setEnabled(False)
        zdepth = QLabel('depth', self)
        zline.addWidget(self.zero_iter)
        zline.addWidget(zdepth)
        glay.addLayout(zline)

        glay.addWidget(self.parent_shape)
        group.setLayout(glay)
        column.addWidget(group)

        group = QGroupBox(self)
        group.setTitle('Mirroring')
        glay = QVBoxLayout()
        glay.setSpacing(2)
        glay.setContentsMargins(4, 4, 4, 4)
        group.setLayout(glay)

        self.mirror = QButtonGroup(self)
        self.none = QPushButton('None', self)
        self.none.setStyleSheet("QPushButton:checked{background:#6a485c;}")
        self.none.setCheckable(True)
        self.none.setChecked(True)
        self.none.value = None
        self.mirror.addButton(self.none)

        self.xy = QPushButton('XY', self)
        self.yz = QPushButton('YZ', self)
        self.zx = QPushButton('ZX', self)

        def mirror_click(button, e):
            enabled = not button.isChecked() and button is not self.none
            for widget in (self.mirror_color, self.from_name, self.to_name, self.mirror_reparent):
                widget.setEnabled(enabled)
            if button.isChecked():
                self.none.setChecked(True)
                self.mirror.buttonClicked.emit(self.none)
            else:
                QPushButton.mousePressEvent(button, e)

        self.none.mousePressEvent = partial(mirror_click, self.none)

        for button in (self.xy, self.yz, self.zx):
            self.mirror.addButton(button)
            button.setStyleSheet(self.none.styleSheet())
            button.setToolTip('Set mirror mode on %s plane' % button.text())
            button.setCheckable(True)
            button.value = button.text()
            button.mousePressEvent = partial(mirror_click, button)

        glay.addLayout(line('Axis : ', self.none, self.xy, self.yz, self.zx))

        self.mirror_color = Color_Picker(self)
        glay.addLayout(line('Mirror color : ', self.mirror_color))
        self.from_name = DefaultField(self, 'from')
        self.to_name = DefaultField(self, 'to')
        glay.addLayout(line('Name pattern : ',
                            self.from_name,
                            QLabel(u'\u25ba', self),
                            self.to_name))
        self.mirror_reparent = QPushButton('Mirror Shape(s)', self)
        for widget in (self.mirror_color, self.from_name, self.to_name, self.mirror_reparent):
            widget.setEnabled(False)
        glay.addWidget(self.mirror_reparent)
        self.mirror_color.setCurrentIndex(1)

        column.addWidget(group)

        column.setAlignment(Qt.AlignTop)

        # final layout !
        self.container.addLayout(column)
        self.layout().addLayout(self.container)

        self.create = QPushButton('Create Controller(s)', self)
        self.layout().addWidget(self.create)

        # TOOLTIPS

        self.capture.setToolTip("Save the current shape selection as a controller")
        self.pop.setToolTip("Remove the current controller, <b>NOT UNDOABLE</b>")
        self.viewer.setToolTip("Cheapest 3D Fake view of the world")
        self.name.setToolTip("Set the default controller's name")
        self.radius.setToolTip("Set the radius' multiplier of the controller")
        self.rotate_order.setToolTip("Set the main axis of the controller, if your joint "
                                     "is oriented by another axis you may want to change this "
                                     "attribute")
        self.color_picker.setToolTip("Default colors for the controller's shape(s)")
        self.zero.setToolTip("This will create N group(s) above the shape")
        self.parent_shape.setToolTip("Directly parent the shape to the transform, "
                                     "can ease manipulation but should be used carefully")
        self.zero_iter.setToolTip("Number of group(s) above the controller")
