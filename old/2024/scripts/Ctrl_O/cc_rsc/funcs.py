from copy import copy
from string import ascii_uppercase

try:
    from PySide.QtGui import QWidget
    from shiboken import wrapInstance as wrapinstance
except ImportError:
    from PySide2.QtWidgets import QWidget
    from shiboken2 import wrapInstance as wrapinstance

from maya.cmds import getAttr, parent, listRelatives, setAttr, curve, undoInfo, xform, ls, pointConstraint, \
    orientConstraint, delete, rename, group, makeIdentity
from maya.OpenMayaUI import MQtUtil

# some generic values
axis_eq = {'X': 0, 'Y': 1, 'Z': 2}
colors = {'red': 13, 'green': 14, 'purple': 9, 'blue': 6, 'yellow': 17,
          'lightblue': 28, 'lightred': 4, 'skin': 21}

# core class used by CtrlO


class V(list):
    """
    Compact simple 3D Vector class to multiply / add / sub arrays
    """
    def V_wrapper(self):
        def wrapper(*args, **kwargs):
            f = self(*[a if isinstance(a, V) else V([a, a, a]) for a in args], **kwargs)
            return f
        return wrapper

    def __init__(self, *args):
        super(V, self).__init__(*args)

    def reorder(self, order):
        """
        With a given 'order' sequence (ie (1, 2, 0)) the elements will be
        reordered, for Axis order purposes
        """
        return V([self[i] for i in order])

    @V_wrapper
    def __mul__(self, o):
        return V([self[i] * o[i] for i in range(3)])

    @V_wrapper
    def __sub__(self, o):
        return V([self[i] - o[i] for i in range(3)])

    @V_wrapper
    def __add__(self, o):
        return V([self[i] + o[i] for i in range(3)])

    def __imul__(self, o): return self * o
    def __rmul__(self, o): return self * o
    def __isub__(self, o): return self - o
    def __rsub__(self, o): return self - o
    def __iadd__(self, o): return self + o
    def __radd__(self, o): return self + o


mirror_vector = {None: V([1, 1, 1]),
                 'XY': V([1, 1, -1]),
                 'YZ': V([-1, 1, 1]),
                 'ZX': V([1, -1, 1])}


class Shape(object):
    """
    This class handle a shape as a sequence of points, have a simple
    function to transform the shape and a 'formatted' version using Shape()
    """
    def __init__(self, parent=None, coords=[], degrees=1, closed=False):
        super(Shape, self).__init__()
        self.parent = parent
        # unaltered coordinates
        self.__coordinates__ = [V(pt) for pt in copy(coords)]
        # these are the common coordinates, if the shape is smoothed this will be
        # updated
        self.coords = coords
        # these are the last coordinates, the one with the transforms
        self.transformed_coords = coords

        self.degrees = degrees
        self.closed = bool(closed)
        # if the shape is already smoothed
        self.smooth = False

        # default transforms
        self.tsf_offset = V([0, 0, 0])
        self.tsf_factor = V([-1, -1, -1])
        self.tsf_axis = range(3)
        self.tsf_mirror = mirror_vector[None]

    def __call__(self):
        """
        Return a formatted version of the shape for saving purpose
        """
        return self.__coordinates__, self.degrees, self.closed

    def transform(self, offset, scale, axis, mirror):
        """
        This store the new transform settings
        :param  offset: position offset
        :param   scale: scale factor
        :param    axis: the axis order
        """
        order = [axis_eq[x] for x in axis]
        self.tsf_offset = -1 * V(offset).reorder(order)
        self.tsf_factor = V(scale).reorder(order)
        self.tsf_axis = order
        self.tsf_mirror = mirror_vector[mirror]

        # and apply them
        self.apply_transform()

    def apply_transform(self):
        """
        Apply the transforms to the current shape
        """
        # baking the current coordinates
        points = copy(self.coords)

        for i, point in enumerate(points):
            point = V(point) * self.tsf_factor
            point -= self.tsf_offset
            point *= self.tsf_mirror
            points[i] = point.reorder(self.tsf_axis)

        self.transformed_coords = points


class Controller(object):
    """
    This basically get all the shapes for a given controller,
    with a Controller() function for saving purpose
    """
    def __init__(self, parent=None, name='', shapes=[]):
        super(Controller, self).__init__()
        self.parent = parent

        self.name = name
        self.shapes = []

        # baking the given shape(s)
        for coords, degrees, closed in shapes:
            self.shapes.append(Shape(self, coords, degrees, closed))

    def __call__(self):
        """
        For saving purpose
        """
        return self.name, [shape() for shape in self.shapes]


class Controller_Pool(set):
    """
    This is the big stack which contains all the controllers loaded in the Application
    """
    def __init__(self, *args, **kwargs):
        super(Controller_Pool, self).__init__(*args, **kwargs)

    def __contains__(self, search):
        return self._find(search)

    def __call__(self, *args, **kwargs):
        """
        Returns a formatted version of the list
        """
        return {name()[0]: name()[1] for name in self}

    def __setitem__(self, key, value):
        self.add(value)

    def __getitem__(self, item):
        return self._find(item)

    def _find(self, search):
        for item in self:
            if item.name == search:
                return item

    def remove(self, target):
        super(Controller_Pool, self).remove(self._find(target))


get_maya_win = lambda : wrapinstance(long(MQtUtil.mainWindow()), QWidget)


# useful functions for controller's creation


def getpos(node, x=False, v=True):
    """
    get the absolute object's position, shorter than typing the whole xform
    :param node: object we want to get the position
    :param    x: force xform
    :param    v: force boundingBox
    :return    : object's position
    """
    # we go to xform if nothing is specified and object is joint or locator
    if (ls(node, showType=True)[1] in ('joint', 'locator') or x) and v:
        r = xform(node, q=True, t=True, ws=True)
    else:
        r = [getAttr(node + '.boundingBoxCenter' + a) for a in 'XYZ']
    return r


def snap(master, slave, pos=True, rot=True, t=True, r=True, clear=True, c=True):
    """
    snap an object to an other
    :param master: the reference
    :param  slave: object which will be aligned
    :param    pos: align position
    :param    rot: align rotations
    :param  clear: if you want to keep the constraints after evaluation, set to False
    :param  t,r,c: short hand for pos, rot and clear
    """
    r, t, c = rot and r, pos and t, clear and c
    cons = []
    if t:
        cons.append(pointConstraint(master, slave, w=1)[0])
    if r:
        cons.append(orientConstraint(master, slave, w=1)[0])
    if c:
        delete(cons)


def override_color(obj, oc=None):
    """
    overriding the colors
    :param  obj: object to override
    :param   oc: color code
    """
    # function will be ignored if oc isn't provided
    if oc:
        # we get the shape
        shapes = listRelatives(obj, c=True, s=True, ni=True, f=True) or obj
        for shape in shapes:
            # setting overridecolor
            setAttr('%s.overrideEnabled' % shape, 1)
            setAttr('%s.overrideColor' % shape, oc)


def shape_to_transform(shapes=[], transforms=[]):
    """
    Parent n shapes directly to n transforms
    :param     shapes: a list of shapes' transforms
    :param transforms: a list of transforms
    """
    # we convert variables to list if they are unique
    shapes = shapes if isinstance(shapes, list) else [shapes]
    transforms = transforms if isinstance(transforms, list) else [transforms]
    # we first check if lengthes are equal, otherwise abort
    assert len(shapes) == len(transforms)
    # storing in a double dim list
    for s, t in zip(shapes, transforms):
        # we get the shape
        shape = listRelatives(s, c=True, s=True, ni=True, f=True)
        parent(shape, t, s=True, add=True)
        if len(shape) == 1:
            rename(shape, t + 'Shape')
        else:
            for i, shp in enumerate(shape):
                rename(shp, '%s_Shape_%02d' % (t, i))
        # and delete the old shape's transform
        delete(s)


def zero(target=None, depth=1):
    """
    zero selected nodes or input if target is specified and not useSelection
    can number of group created (1 to 3), will create multiple group
    :param       target: where to put zeros, if none is provided, zero the selection
    :param         depth: how much group depth
    :return: list of zeros
    """
    # loop through objects/selection
    target = ([target] if target else ls(sl=True)) if not isinstance(target, list) else target
    ret = []
    for a in target:
        ro = getAttr(a + '.rotateOrder')
        # loop through iterations
        for it in range(depth):
            # retrieve parents
            obj_parent = listRelatives(a, p=True, f=True)
            # create group
            null = group(em=True, n='G_%s_%s' % (ascii_uppercase[it], a))
            setAttr(null + '.rotateOrder', ro)
            # if node has parent, reparent the empty group
            if obj_parent:
                parent(null, obj_parent)
            # grab object's transforms
            transform = [getAttr('%s.%s' % (a, b)) for b in 'tsr']
            # parent object to group
            parent(a, null)
            # loop through transforms
            for i, b in enumerate('tsr'):
                setAttr('%s.%s' % (null, b), *transform[i][0], type='double3')
                # set variable depends if transform is (translate and rotate) or scale
                reset = (0, 0, 0) if i != 1 else (1, 1, 1)
                setAttr('%s.%s' % (a, b), *reset, type='double3')
            ret.append(null)
    return ret


def from_shape(shape, over, prefix='', suffix='', radius=1, oc=None, name=None, offset=(0, 0, 0), p=None, ori=(1, 1, 1), axis_order='XYZ', fwg=False, shape_parent=False, mirror=None):
    """
    Creates a shape controller from the Controller class
    :param          shape: the shape's name from the dictionnary
    :param           over: the object(s) on which we'll create controller(s)
    :param         prefix: the controller's prefix , in form cc_ObjectName
    :param         radius: the radius of the controller (multiply the shape's size)
    :param             oc: override the color
    :param           name: name of the controller if not set will take from object
    :param         offset: X, Y or Z offset around the object
    :param              p: parent to
    :param            ori: X, Y or Z multiply of the shape (1.0, 1.0, 1.0)
    :param     axis_order: 'XYZ' will take X as main axis, 'YZX' Y etc
    :param            fwg: if > 0 create n freeze groups
    :param   shape_parent: if True will parent the shape to the target object
    :return              : a list of created controllers
    """
    # make a list from over if is alone
    over = [over] if not isinstance(over, list) else over
    ccs = []
    orient = V(ori)

    def make(shape, name, offset):
        """
        creates a curve an apply the transforms to the shape
        :param   shape: shape(s) object(s) with the coordinate
        :param    name: curve name
        :param  offset: X, Y or Z offset around the object
        :return       : the created controller
        """
        # we get the original unchanged coordinates arguments of the shape
        points, degree, closed = copy(shape.__coordinates__), shape.degrees, shape.closed
        # reorder depending on main axis
        order = [axis_eq[x] for x in axis_order]

        for i, point in enumerate(points):
            point *= radius * orient.reorder(order)
            point += offset.reorder(order)
            point *= mirror_vector[mirror]
            points[i] = point.reorder(order)

        # while loop to create a unique controller's name
        i, n = 2, name
        try:
            while getAttr('%s.t' % n):
                n = '%s_%02d' % (name, i)
                i += 1
        except ValueError:
            name = n

        # making the curve periodic if closed
        if closed and points[0] != points[-degree]:
            points.extend(points[0:degree])
        # create the curve
        return curve(n=name, d=degree, p=points, k=[i for i in range(-degree + 1, len(points))], per=closed)

    def make_name(obj_name):
        print obj_name, prefix, suffix
        compo_name = [name if len(name) else obj_name]
        if len(prefix):
            compo_name.insert(0, prefix)
        if len(suffix):
            compo_name.append(suffix)
        return '_'.join(compo_name)

    if len(over) != 0 and over[0]:
        for obj in over:
            ctrls = []
            # we get the rotationOrder
            ro = getAttr('%s.ro' % obj)

            cc_name = make_name(obj)

            for shp in shape:
                try:
                    offset_perc = [getAttr('%s.t%s' % (listRelatives(obj, c=True, type='joint')[0], x))[0] * offset[i] for i, x in enumerate('xyz')]
                except (ValueError, TypeError):
                    offset_perc = offset
                finally:
                    ctrl = make(shp, cc_name, V(offset_perc))

                # we realign the new controller
                setAttr('%s.t' % ctrl, *getpos(obj), type='double3')
                snap(obj, ctrl, t=False)
                # we paste the rotationOrder
                setAttr(ctrl+'.ro', ro)

                ctrls.append(ctrl)
            ccs.append(ctrls)
    else:
        ccs.append([make(shp, make_name('ctrl'), V(offset)) for shp in shape])

    # then we loop through controllers to apply last effects
    for i, ctrls in enumerate(ccs):
        ctrl = ctrls[0]
        if len(shape) > 1:
            for obj in ctrls[1:]:
                shape = listRelatives(obj, s=True, ni=True, f=True)
                parent(shape, ctrl, s=True, add=True, relative=True)
            delete(ctrls[1:])

        override_color(ctrl, oc)
        if p:
            parent(ctrl, p)
        elif shape_parent and len(over) != 0:
            shape_to_transform(ctrl, over[i])
        elif fwg:
            zero(ctrl, fwg)

    return ccs


def mirror_shape(shape, plane='x'):
    crvs = shape
    grp = group(em=True)
    parent(crvs, grp)
    setAttr('%s.s%s' % (grp, plane), -1)
    parent(crvs, w=True)
    makeIdentity(crvs, apply=True, t=0, r=0, s=1)
    delete(grp)