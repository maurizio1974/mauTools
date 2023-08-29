"""
User interface for advanced controllers creation, you can view the controller shape,
can be binded to a joint directly, preview ability, creates zero, color override, and so on :)

v2.0      :   Now you can capture the selected controller
              Controllers are stored in a database
              You can preview the selected joint in the internal viewport
              You can toggle axis display
              Handle closed shapes

v2.1      :   (Fake) 3D Viewport way more comfortable
              Can recover from scratch if no database
              Smooth controller preview using catmull rom formula
              Controller can be renamed by double-clicking on
              Clear filter button

v2.2      :   Class based controllers
              Merge multiple selection into one object
              Merge multiple shapes into one shape
              Now working with a simple .cfg file containing the controllers

v2.3      :   Adding mirroring tool
              Visual comfort

v2.3.1    :   2017 Compatible
"""

__author__ = "Mehdi Louala"
__copyright__ = "Copyright 2017, Mehdi Louala"
__credits__ = ["Mehdi Louala"]
__license__ = "GPL"
__version__ = "2.3.1"
__maintainer__ = "Mehdi Louala"
__email__ = "mlouala@gmail.com"
__status__ = "Stable Version"

from copy import copy
import os
import json

try:
    from PySide.QtCore import Qt
    from PySide.QtGui import QTreeWidgetItem, QWidget
except ImportError:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QTreeWidgetItem

from maya.cmds import ls, getAttr, xform, listRelatives, jointDisplayScale, error, warning,\
                      duplicate, makeIdentity, delete, select, parent, undoInfo
from maya.OpenMaya import MEventMessage, MMessage

from cc_rsc.funcs import Controller, Controller_Pool, from_shape, get_maya_win, \
    mirror_shape, override_color, colors
from cc_rsc.widgets import Ctrl_O_UI, Capture


class Ctrl_O(Ctrl_O_UI, QWidget):
    """
    The main widget window
    """
    jds = jointDisplayScale(q=True)
    config_path = os.path.join(os.path.dirname(__file__), 'cc_rsc', 'config.cfg')

    def __init__(self, parent=None):
        self.controllers = Controller_Pool()

        # first we check if the config file exists, if no, we create a new one with
        # few shapes
        exists = os.path.isfile(self.config_path)

        with open(self.config_path, 'a+') as f:
            if not exists:
                data = {'circle': [([(0.0, 0.7, -0.7), (0.0, 0.0, -1.0), (0.0, -0.7, -0.7), (0.0, -1.0, 0.0), (0.0, -0.7, 0.7), (0.0, 0.0, 1.0), (0.0, 0.7, 0.7), (0.0, 1.0, 0.0)], 3, 1)],
                        'cross': [([(0.0, 0.5, -0.5), (0.0, 1.0, -0.5), (0.0, 1.0, 0.5), (0.0, 0.5, 0.5), (0.0, 0.5, 1.0), (0.0, -0.5, 1.0), (0.0, -0.5, 0.5), (0.0, -1.0, 0.5), (0.0, -1.0, -0.5), (0.0, -0.5, -0.5), (0.0, -0.5, -1.0), (0.0, 0.5, -1.0), (0.0, 0.5, -0.5)], 1, 1)],
                        'cube': [([(-1.0, -1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, 1.0, -1.0), (-1.0, -1.0, -1.0), (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0), (1.0, 1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, 1.0, -1.0), (1.0, 1.0, -1.0), (1.0, -1.0, -1.0), (-1.0, -1.0, -1.0)], 1, 1)],
                        'locator': [([(-1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, -1.0)], 1, 0)],
                        'square': [([(0.0, -1.0, 1.0), (0.0, 1.0, 1.0), (0.0, 1.0, -1.0), (0.0, -1.0, -1.0), (0.0, -1.0, 1.0)], 1, 1)],
                        'square_rounded': [([(0.0, 0.0, -1.0), (0.0, 0.5, -1.0), (0.0, 0.75, -1.0), (0.0, 1.0, -1.0), (0.0, 1.0, -0.75), (0.0, 1.0, -0.5), (0.0, 1.0, 0.5), (0.0, 1.0, 0.75), (0.0, 1.0, 1.0), (0.0, 0.75, 1.0), (0.0, 0.5, 1.0), (0.0, -0.5, 1.0), (0.0, -0.75, 1.0), (0.0, -1.0, 1.0), (0.0, -1.0, 0.75), (0.0, -1.0, 0.5), (0.0, -1.0, -0.5), (0.0, -1.0, -0.75), (0.0, -1.0, -1.0), (0.0, -0.75, -1.0), (0.0, -0.5, -1.0), (0.0, 0.0, -1.0)], 3, 1)],
                        'thin_cross': [([(0.0, 0.2, -0.2), (0.0, 0.2, -1.0), (0.0, -0.2, -1.0), (0.0, -0.2, -0.2), (0.0, -1.0, -0.2), (0.0, -1.0, 0.2), (0.0, -0.2, 0.2), (0.0, -0.2, 1.0), (0.0, 0.2, 1.0), (0.0, 0.2, 0.2), (0.0, 1.0, 0.2), (0.0, 1.0, -0.2), (0.0, 0.2, -0.2)], 1, 1)],
                        'triangle': [([(0.0, 1.0, 0.0), (0.0, -0.5, -0.86), (0.0, -0.5, 0.86), (0.0, 1.0, 0.0)], 1, 1)]}

            else:
                data = json.load(f)

        for control in data:
            new = Controller(self, control, data[control])
            self.controllers.add(new)

        # need to save our new controllers if the file doesn't exists
        if not exists:
            self.save_config()

        super(Ctrl_O, self).__init__(parent)

        # CONNECTIONS

        self.filter.textChanged.connect(self.filterList)
        self.controller_list.itemSelectionChanged.connect(self.display_controller)

        self.capture.clicked.connect(self.capture_controller)
        self.pop.clicked.connect(self.delete_controller)

        self.radius.textChanged.connect(self.display_controller)
        self.radius.textChanged.connect(self.rescale)

        for offset in (self.offsetX, self.offsetY, self.offsetZ):
            offset.setToolTip("Define the position offset of the shape(s)")
            offset.textChanged.connect(self.display_controller)

        for factor in (self.factorX, self.factorY, self.factorZ):
            factor.setToolTip("Define the scale factor of the shape(s)")
            factor.textChanged.connect(self.display_controller)

        self.rotate_order.currentIndexChanged.connect(self.display_controller)

        def toggle_zero(state):
            if state and self.zero.isChecked():
                self.zero.setChecked(False)

        def toggle_shape(state):
            if state and self.parent_shape.isChecked():
                self.parent_shape.setChecked(False)
            self.zero_iter.setEnabled(state)

        self.parent_shape.stateChanged.connect(toggle_zero)
        self.zero.stateChanged.connect(toggle_shape)

        self.mirror.buttonClicked.connect(self.display_controller)

        self.mirror_reparent.clicked.connect(self.mirror_shapes)

        self.create.clicked.connect(self.execute)

        # FINAL MANAGEMENT OF THE CONTROLLER LIST

        # we get all the shapes contained by the dictionnary and add them as
        # items in our list
        for control in self.controllers:
            item = QTreeWidgetItem(self.controller_list, [control.name])
            item.controller = control
            item.shapes = control.shapes
            self.controller_list.addTopLevelItem(item)

        # evaluate the controller
        self.controller_list.setCurrentItem(self.controller_list.topLevelItem(0))
        self.controller_list.setFocus(Qt.TabFocusReason)

        # CALLBACKz

        self.callbacks = []
        try:
            self.callbacks.append(MEventMessage.addEventCallback('SelectionChanged', self.rescale))
        except TypeError:
            pass

    def closeEvent(self, *args, **kwargs):
        for callback in reversed(self.callbacks):
            MMessage.removeCallback(callback)
            self.callbacks.remove(callback)

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.controllers(), f, sort_keys=True,
                      indent=4, separators=(',', ': '))

    def execute(self):
        """
        apply the presets on the Maya's selection
        """
        item = self.controller_list.currentItem()
        if item:
            undoInfo(openChunk=True)

            ccs = from_shape(item.shapes,
                             ls(sl=True),
                             radius=self.radius.value(),
                             prefix=self.name_prefix.value,
                             name=self.name.value,
                             suffix=self.name_suffix.value,
                             oc=self.color_picker.color() if not self.mirror.checkedButton().value else self.mirror_color.color(),
                             offset=self.offset(),
                             ori=self.factor(),
                             axis_order=self.rotate_order.itemData(self.rotate_order.currentIndex()),
                             fwg=self.zero_iter.value() if self.zero.isChecked() else False,
                             shape_parent=self.parent_shape.isChecked(),
                             mirror=self.mirror.checkedButton().value)
            select(cl=1)
            for ctrls in ccs:
                select(ctrls, add=True)

            undoInfo(closeChunk=True)

    def filterList(self, txt):
        """
        filter the controllers' list
        :param txt: typed filter text
        """
        for i in range(self.controller_list.topLevelItemCount()):
            item = self.controller_list.topLevelItem(i)
            item.setHidden(txt not in item.text(0))

    def rescale(self, v=None):
        """
        In case the joint's selection have a different radius,
        or the jointDisplayScale has changed, we update our cheap viewport
        :param v:
        :return:
        """
        v = float(self.radius.value())
        try:
            r = getAttr('%s.radius' % ls(sl=True, type='joint')[0]) * self.jds
        except TypeError:
            r = 1
        except IndexError:
            r = self.viewer.ref * v
        finally:
            self.viewer.ref = r / v
        self.viewer.setCoords()

    def display_controller(self):
        """
        Making the last transforms on the controller, forwarding to the viewer
        """
        item = self.controller_list.currentItem()
        if item:
            cc = item.text(0)
            # global settings sent to the shapes
            offset = self.offset()
            factor = self.factor()
            axis = self.rotate_order.itemData(self.rotate_order.currentIndex())
            mirror = self.mirror.checkedButton().value

            if self.viewer.controller != cc:
                self.viewer.controller = cc
                self.viewer.load(copy(item.shapes))

                # defining the scene's scale for the viewer
                try:
                    r = getAttr('%s.radius' % ls(sl=True, type='joint')[0]) * self.jds
                except (TypeError, IndexError):
                    r = 1
                finally:
                    self.viewer.ref = r

            for i, shape in enumerate(self.viewer.shapes):
                shape.transform(offset, factor, axis, mirror)

            self.viewer.setCoords()

    def capture_controller(self):
        """
        This is the first step when we want to get a new controller from
        Maya's scene selection, it gets selection summary then opens
        the Capture dialog
        """
        crvs = ls(sl=True)

        # abort if selection's empty
        if not len(crvs):
            warning('Cannot capture an empty selection :]')
            return

        # getting the max values for degrees and closed from all shapes
        degree = 0
        closed = -1
        for crv in crvs:
            shapes = listRelatives(crv, s=True, ni=True, f=True)
            for shape in shapes:
                degree = max(degree, getAttr('%s.d' % shape))
                closed = max(closed, getAttr('%s.f' % shape))

        # calling the Capture dialog
        Capture(self, crvs[0], degree, closed).show(self.add_controller)

    def add_controller(self, *args):
        """
        This function is called by the Capture dialog after valid closing
        it can send 3 or 5 arguments, it depends if global settings are
        used for the degrees & closed state
        :param  t: transform (name)
        :param ts: translate space
        :param rs: rotate space
        :param  d: degree (ADDITIONNAL)
        :param  c: closed (ADDITIONNAL)
        """
        try:
            t, ts, rs, d, c = args
        except ValueError:
            # Unpack error, this (probably) means we have 3 args, not 5
            t, ts, rs = args
            d, c = None, None

        # We raise an error in case of duplicate, will prevent the
        # dialog to be closed
        if t in self.controllers:
            error('Duplicate controller name')
            return

        # original selection which we duplicate to freeze transform
        orig = ls(sl=True)
        crvs = duplicate(orig, n='duplicates')

        shapes = []
        mx = -1

        # we first get the global bounds of the selection so we can
        # normalize the cv coordinates later
        for obj in crvs:
            if listRelatives(obj, p=True):
                parent(obj, w=True)
            if ts or rs:
                makeIdentity(obj, apply=True, t=ts, r=rs, s=1, n=0, pn=1)

            for crv in listRelatives(obj, c=True, s=True, f=True):
                for i in range(getAttr('%s.degree' % crv) + getAttr('%s.spans' % crv)):
                    for p in xform('%s.cv[%d]' % (crv, i), q=True, t=True, os=True):
                        if mx < abs(p):
                            mx = abs(p)

        # second loop to store the normalized data of the shapes
        for obj in crvs:
            for crv in listRelatives(obj, c=True, s=True, f=True):
                # number of CVs = spans + (degree if not closed).
                degs = getAttr('%s.degree' % crv)
                spans = getAttr('%s.spans' % crv)
                closed = getAttr('%s.f' % crv)
                pts = []

                for i in range(spans + (0 if closed else degs)):
                    pts.append(xform('%s.cv[%d]' % (crv, i), q=True, t=True, os=True))

                pts = [[p / mx for p in pt] for pt in pts]
                shapes.append((pts, d or degs, c or closed))

        # creating the Controller class for this record
        new = Controller(self, t, shapes)
        self.controllers.add(new)

        # and making the treewidget item
        item = QTreeWidgetItem(self.controller_list, [t])
        item.controller = new
        item.shapes = new.shapes

        self.controller_list.addTopLevelItem(item)
        self.controller_list.setCurrentItem(item)

        # saving the .cfg file
        self.save_config()

        # cleaning the mess
        delete(crvs)
        select(orig)

    def delete_controller(self):
        """
        We pop a controller from our controllers' list
        """
        item = self.controller_list.currentItem()
        self.controller_list.takeTopLevelItem(self.controller_list.indexOfTopLevelItem(item))
        self.controllers.remove(item.text(0))
        self.save_config()

    def update_controller(self, fr, to):
        """
        Renaming a controller
        :param fr: from name
        :param to: new name
        """
        self.controllers[fr].name = to
        # updating the .cfg
        self.save_config()

    def mirror_shapes(self):
        undoInfo(openChunk=True)
        f, t = self.from_name.value, self.to_name.value
        plane = {'XY': 'z', 'YZ': 'x', 'ZX': 'y'}[self.mirror.checkedButton().text()]
        if not len(f) and not len(t):
            warning("Replacement pattern - name conflict")
        sel = ls(sl=True)
        dups = list()
        for shape in sel:
            old_parent = listRelatives(shape, p=True)
            dup = duplicate(shape, n=shape.replace(f, t))
            mirror_shape(dup, plane)
            override_color(dup, colors[self.mirror_color.currentText()])
            if old_parent:
                parent(dup, old_parent.replace(f, t))
            dups.extend(dup)
        select(dups)
        undoInfo(closeChunk=True)


def Display_CtrlO_UI():
    """
    Display function
    """
    CC_Window = Ctrl_O(get_maya_win())
    CC_Window.show()
    return CC_Window
