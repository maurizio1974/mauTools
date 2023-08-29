import pymel.core as pm, maya.mel as mel, maya.cmds as mc, os, os.path, sys, maya.OpenMaya as om
mc.scriptEditorInfo(ch=True)

class av_ControlMaker:
    """-------------------------------------------------------------------
        Author: Ajay Kumar Verma 15-08-2018
                        ajayrigger@gmail.com
        
        Description :
                A simple but handy little script that will allow you to snap and constrain a control to a joint(or any object).
                Select one objects.
                Select a control type (all NURBS curves)
                Enter control name (auto add '_Ctrl') no need to add
                Select a type of constraint you want (point, orient, scale, parent, shape parent, only control (just snap))
                Change control size 
                Create an extra group. Helpful for SDK's on groups
                Auto lock and hide of channels
                Change any controls shape

        How to use :
                Put the script ('av_ControlMaker.pyc') in your scripts folder then start Maya.
                
                MAYA_SCRIPT_PATH = 'C:/Users/'+username+'/Documents/maya/scripts/'
                
                Copy this command in python tab and run

                from av_ControlMaker import *
                av_ControlMaker().av_ControlMakerUI()
                
        -------------------------------------------------------------------"""

    def __init__(self):
        self.ui_name = 'av_ControlMaker_ui'
        self.ui_title = 'av_ControlMaker'

    def av_ControlMakerUI(self):
        if mc.window(self.ui_name, exists=True):
            mc.deleteUI(self.ui_name)
        self.window = mc.window(self.ui_name, t=self.ui_title, iconName='AVC', mnb=False, mxb=False, s=False)
        self.main_column = mc.columnLayout('av_main_clolumn', adj=True)
        mc.separator(st='none', h=5)
        mc.frameLayout(l='Create Controller', cll=0, cl=0, bgc=(0.5, 0, 0))
        mc.separator(st='double', h=5)
        mc.rowColumnLayout('av_control_name_row', nc=2, cs=[(1, 1), (2, 1)], cw=[(1, 90), (2, 120)])
        mc.text(l='Control Name')
        self.av_ctrl_name = mc.textField('av_ctrl_name', tx='')
        mc.setParent('..')
        mc.separator(st='double', h=5)
        mc.rowColumnLayout(nc=2, cs=[(1, 1), (2, 1)], cw=[(1, 90), (2, 120)])
        mc.text(l='Control Shape')
        self.av_ctrl_shape = mc.optionMenu('av_ctrl_shape', bgc=(0.25, 0.25, 0.25))
        labels = ['Circle', 'Cube', 'Sphere', 'Square', 'Frame', 'Triangle', 'Plus', 'Swirl',
         'Single Arrow', 'Triple Arrow', 'Quad Arrow', 'Diamond', 'Ring', 'Cone',
         'Pointer', 'Curved Single Arrow']
        for label in labels:
            mc.menuItem(l=label)

        mc.setParent('..')
        mc.separator(st='double', h=5)
        mc.rowColumnLayout(nc=2, cs=[(1, 8), (2, 10)], cw=[(1, 100), (2, 100)])
        mc.checkBox('av_point_constrain_cb', onc=lambda *args: self.av_point_constraint_enable(), ofc=lambda *args: self.av_check_box_disable(), l='Point Constrain')
        mc.checkBox('av_orient_constrain_cb', onc=lambda *args: self.av_orient_constrain_enable(), ofc=lambda *args: self.av_check_box_disable(), l='Orient Constrain')
        mc.checkBox('av_scale_constrain_cb', onc=lambda *args: self.av_scale_constrain_enable(), ofc=lambda *args: self.av_check_box_disable(), l='Scale Constrain')
        mc.checkBox('av_parent_constrain_cb', onc=lambda *args: self.av_parent_constrain_enable(), ofc=lambda *args: self.av_check_box_disable(), l='Parent Constrain')
        mc.checkBox('av_shape_parent_cb', onc=lambda *args: self.av_shape_parent_enable(), ofc=lambda *args: self.av_check_box_disable(), l='Shape Parent')
        mc.checkBox('av_just_snap_cb', onc=lambda *args: self.av_just_snap_enable(), ofc=lambda *args: self.av_check_box_disable(), l='Just Snap')
        mc.setParent('..')
        mc.separator(st='double', h=5)
        mc.rowColumnLayout(nc=4, cs=[(1, 8), (2, 3), (3, 3), (4, 3)], cw=[(1, 50), (2, 50), (3, 50), (4, 50)])
        mc.checkBox('av_translate_cb', l='Tran', en=False)
        mc.checkBox('av_rotate_cb', l='Rot', en=False)
        mc.checkBox('av_scale_cb', l='Scal', en=False)
        mc.checkBox('av_visibility_cb', l='Vis', en=False)
        mc.setParent('..')
        mc.separator(st='double', h=5)
        mc.rowColumnLayout(nc=2, cs=[(1, 1), (2, 1)], cw=[(1, 90), (2, 120)])
        mc.text(l='Control Size')
        self.av_ctrl_size = mc.floatField('av_ctrl_size', min=0.1, max=10, v=1, pre=2)
        mc.setParent('..')
        mc.separator(st='double', h=5)
        mc.button(l='Create Control', c=lambda *args: self.av_create_control(), bgc=(0.5,
                                                                                     0.7,
                                                                                     0.8))
        mc.separator(st='double', h=3)
        mc.frameLayout(l='Repalce Shape', cll=0, cl=0, bgc=(0.5, 0, 0))
        mc.separator(st='double', h=5)
        mc.rowColumnLayout(nc=2, cs=[(1, 1), (2, 1)], cw=[(1, 90), (2, 120)])
        mc.text(l='Control Shape')
        self.av_ctrl_repalce_shape = mc.optionMenu('av_ctrl_repalce_shape', bgc=(0.25,
                                                                                 0.25,
                                                                                 0.25))
        labels = ['Circle', 'Cube', 'Sphere', 'Square', 'Frame', 'Triangle', 'Plus', 'Swirl',
         'Single Arrow', 'Triple Arrow', 'Quad Arrow', 'Diamond', 'Ring', 'Cone',
         'Pointer', 'Curved Single Arrow']
        for label in labels:
            mc.menuItem(l=label)

        mc.setParent('..')
        mc.separator(st='double', h=5)
        mc.button(l='Repalce Shape', c=lambda *args: self.av_replace_control_shape(), bgc=(0.5,
                                                                                           0.7,
                                                                                           0.8))
        mc.separator(st='none', h=1)
        mc.setParent('..')
        mc.setParent('..')
        mc.separator(st='double', h=5)
        mc.separator(st='none', h=5)
        mc.text(l='AJAY KUMAR VERMA  ', fn='smallBoldLabelFont', al='right', h=8)
        mc.separator(st='none', h=3)
        mc.text(l='ajayrigger@gmail.com  ', fn='boldLabelFont', al='right', h=12)
        mc.separator(st='none', h=3)
        mc.showWindow(self.ui_name)
        mc.window(self.ui_name, e=True, w=225, h=465)

    def av_point_constraint_enable(self):
        mc.checkBox('av_point_constrain_cb', en=True, e=True)
        mc.checkBox('av_orient_constrain_cb', en=False, e=True)
        mc.checkBox('av_scale_constrain_cb', en=False, e=True)
        mc.checkBox('av_parent_constrain_cb', en=False, e=True)
        mc.checkBox('av_shape_parent_cb', en=False, e=True)
        mc.checkBox('av_just_snap_cb', en=False, e=True)
        self.av_transform_disable()

    def av_orient_constrain_enable(self):
        mc.checkBox('av_point_constrain_cb', en=False, e=True)
        mc.checkBox('av_orient_constrain_cb', en=True, e=True)
        mc.checkBox('av_scale_constrain_cb', en=False, e=True)
        mc.checkBox('av_parent_constrain_cb', en=False, e=True)
        mc.checkBox('av_shape_parent_cb', en=False, e=True)
        mc.checkBox('av_just_snap_cb', en=False, e=True)
        self.av_transform_disable()

    def av_scale_constrain_enable(self):
        mc.checkBox('av_point_constrain_cb', en=False, e=True)
        mc.checkBox('av_orient_constrain_cb', en=False, e=True)
        mc.checkBox('av_scale_constrain_cb', en=True, e=True)
        mc.checkBox('av_parent_constrain_cb', en=False, e=True)
        mc.checkBox('av_shape_parent_cb', en=False, e=True)
        mc.checkBox('av_just_snap_cb', en=False, e=True)
        self.av_transform_disable()

    def av_parent_constrain_enable(self):
        mc.checkBox('av_point_constrain_cb', en=False, e=True)
        mc.checkBox('av_orient_constrain_cb', en=False, e=True)
        mc.checkBox('av_scale_constrain_cb', en=False, e=True)
        mc.checkBox('av_parent_constrain_cb', en=True, e=True)
        mc.checkBox('av_shape_parent_cb', en=False, e=True)
        mc.checkBox('av_just_snap_cb', en=False, e=True)
        self.av_transform_disable()

    def av_shape_parent_enable(self):
        mc.checkBox('av_point_constrain_cb', en=False, e=True)
        mc.checkBox('av_orient_constrain_cb', en=False, e=True)
        mc.checkBox('av_scale_constrain_cb', en=False, e=True)
        mc.checkBox('av_parent_constrain_cb', en=False, e=True)
        mc.checkBox('av_shape_parent_cb', en=True, e=True)
        mc.checkBox('av_just_snap_cb', en=False, e=True)
        self.av_transform_disable()
        mc.textField('av_ctrl_name', tx='', e=True)
        mc.rowColumnLayout('av_control_name_row', en=False, e=True)

    def av_just_snap_enable(self):
        mc.checkBox('av_point_constrain_cb', en=False, e=True)
        mc.checkBox('av_orient_constrain_cb', en=False, e=True)
        mc.checkBox('av_scale_constrain_cb', en=False, e=True)
        mc.checkBox('av_parent_constrain_cb', en=False, e=True)
        mc.checkBox('av_shape_parent_cb', en=False, e=True)
        mc.checkBox('av_just_snap_cb', en=True, e=True)
        self.av_transform_enable()

    def av_check_box_disable(self):
        mc.checkBox('av_point_constrain_cb', en=True, e=True)
        mc.checkBox('av_orient_constrain_cb', en=True, e=True)
        mc.checkBox('av_scale_constrain_cb', en=True, e=True)
        mc.checkBox('av_parent_constrain_cb', en=True, e=True)
        mc.checkBox('av_shape_parent_cb', en=True, e=True)
        mc.checkBox('av_just_snap_cb', en=True, e=True)
        self.av_transform_disable()
        mc.rowColumnLayout('av_control_name_row', en=True, e=True)

    def av_transform_enable(self):
        mc.checkBox('av_translate_cb', en=True, v=1, e=True)
        mc.checkBox('av_rotate_cb', en=True, v=1, e=True)
        mc.checkBox('av_scale_cb', en=True, v=1, e=True)
        mc.checkBox('av_visibility_cb', en=True, v=0, e=True)

    def av_transform_disable(self):
        mc.checkBox('av_translate_cb', en=False, v=0, e=True)
        mc.checkBox('av_rotate_cb', en=False, v=0, e=True)
        mc.checkBox('av_scale_cb', en=False, v=0, e=True)
        mc.checkBox('av_visibility_cb', en=False, v=0, e=True)

    def av_non_keyable(self, object):
        try:
            mc.setAttr(object + '.tx', k=False, cb=True)
            mc.setAttr(object + '.ty', k=False, cb=True)
            mc.setAttr(object + '.tz', k=False, cb=True)
            mc.setAttr(object + '.rx', k=False, cb=True)
            mc.setAttr(object + '.ry', k=False, cb=True)
            mc.setAttr(object + '.rz', k=False, cb=True)
            mc.setAttr(object + '.sx', k=False, cb=True)
            mc.setAttr(object + '.sy', k=False, cb=True)
            mc.setAttr(object + '.sz', k=False, cb=True)
            mc.setAttr(object + '.v', k=False, cb=True)
        except:
            mc.warning('No object matches name : %s' % object)

    def av_shape(self, shape='', name=''):
        self.shape = shape
        self.name = name
        self.ctrl_name = self.name + '_Ctrl'
        self.ctrl_extra_grp = self.name + '_Extra'
        self.ctrl_offset_grp = self.name + '_Offset'
        self.ctrl_grp = self.name + '_Grp'
        if not mc.objExists(self.ctrl_name) == True:
            if self.shape == 'Circle':
                self.circle_crv = mc.rename(mc.circle(r=1, nr=(1, 0, 0), ch=False), self.ctrl_name)
            else:
                if self.shape == 'Cube':
                    self.cube_crv = mc.rename(mc.curve(d=1, p=[(1, 1, 1), (1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, -1, 1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1), (1, -1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, -1, 1), (1, -1, 1)], k=list(range(0, 16))), self.ctrl_name)
                elif self.shape == 'Square':
                    self.square_crv = mc.rename(mc.curve(d=1, p=[(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1), (-1, 0, -1)], k=list(range(0, 5))), self.ctrl_name)
                elif self.shape == 'Frame':
                    self.frame_crv = mc.rename(mc.curve(d=1, p=[(-1, 0, -1), (-1, 0, 1), (1, 0, 1), (1, 0, -1), (-1, 0, -1), (-2, 0, -2), (2, 0, -2), (1, 0, -1), (1, 0, 1), (2, 0, 2), (2, 0, -2), (2, 0, 2), (-2, 0, 2), (-1, 0, 1), (-2, 0, 2), (-2, 0, -2)], k=list(range(0, 16))), self.ctrl_name)
                elif self.shape == 'Triangle':
                    self.triangle_crv = mc.rename(mc.curve(d=1, p=[(-1, 0, 1), (1, 0, 1), (0, 0, -1), (-1, 0, 1)], k=list(range(0, 4))), self.ctrl_name)
                elif self.shape == 'Plus':
                    self.plus_crv = mc.rename(mc.curve(d=1, p=[(-1, 0, -3), (1, 0, -3), (1, 0, -1), (3, 0, -1), (3, 0, 1), (1, 0, 1), (1, 0, 3), (-1, 0, 3), (-1, 0, 1), (-3, 0, 1), (-3, 0, -1), (-1, 0, -1), (-1, 0, -3)], k=list(range(0, 13))), self.ctrl_name)
                elif self.shape == 'Swirl':
                    self.swirl_crv = mc.rename(mc.curve(d=3, p=[(0, 0, 0.0360697), (-0.746816, 0, 1), (-2, 0, -0.517827), (0, 0, -2), (2, 0, 0), (0.536575, 0, 2.809361), (-3.191884, 0, 1.292017), (-2.772303, 0, -2.117866), (-0.771699, 0, -3), (1.229059, 0, -3), (3, 0, -1.863394), (3.950518, 0, 0.314344), (3, 0, 3.347373), (0, 0, 4.152682)], k=[0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11, 11]), self.ctrl_name)
                elif self.shape == 'Single Arrow':
                    self.single_arrow_crv = mc.rename(mc.curve(d=1, p=[(0, 1.003235, 0), (0.668823, 0, 0), (0.334412, 0, 0), (0.334412, -0.167206, 0), (0.334412, -0.501617, 0), (0.334412, -1.003235, 0), (-0.334412, -1.003235, 0), (-0.334412, -0.501617, 0), (-0.334412, -0.167206, 0), (-0.334412, 0, 0), (-0.668823, 0, 0), (0, 1.003235, 0)], k=list(range(0, 12))), self.ctrl_name)
                elif self.shape == 'Curved Single Arrow':
                    self.curved_single_arrow_crv = mc.rename(mc.curve(d=1, p=[(-0.251045, 0, 1.015808), (-0.761834, 0, 0.979696), (-0.486547, 0, 0.930468), (-0.570736, 0, 0.886448), (-0.72786, 0, 0.774834), (-0.909301, 0, 0.550655), (-1.023899, 0, 0.285854), (-1.063053, 0, 9.80765e-09), (-0.961797, 0, 8.87346e-09), (-0.926399, 0, 0.258619), (-0.822676, 0, 0.498232), (-0.658578, 0, 0.701014), (-0.516355, 0, 0.802034), (-0.440202, 0, 0.841857), (-0.498915, 0, 0.567734), (-0.251045, 0, 1.015808)], k=list(range(0, 16))), self.ctrl_name)
                elif self.shape == 'Triple Arrow':
                    self.triple_arrow_crv = mc.rename(mc.curve(d=1, p=[(-1, 1, 0), (-3, 1, 0), (-3, 2, 0), (-5, 0, 0), (-3, -2, 0), (-3, -1, 0), (-1, -1, 0), (1, -1, 0), (3, -1, 0), (3, -2, 0), (5, 0, 0), (3, 2, 0), (3, 1, 0), (1, 1, 0), (1, 3, 0), (2, 3, 0), (0, 5, 0), (-2, 3, 0), (-1, 3, 0), (-1, 1, 0)], k=list(range(0, 20))), self.ctrl_name)
                elif self.shape == 'Quad Arrow':
                    self.quad_arrow_crv = mc.rename(mc.curve(d=1, p=[(1, 0, 1), (3, 0, 1), (3, 0, 2), (5, 0, 0), (3, 0, -2), (3, 0, -1), (1, 0, -1), (1, 0, -3), (2, 0, -3), (0, 0, -5), (-2, 0, -3), (-1, 0, -3), (-1, 0, -1), (-3, 0, -1), (-3, 0, -2), (-5, 0, 0), (-3, 0, 2), (-3, 0, 1), (-1, 0, 1), (-1, 0, 3), (-2, 0, 3), (0, 0, 5), (2, 0, 3), (1, 0, 3), (1, 0, 1)], k=list(range(0, 25))), self.ctrl_name)
                elif self.shape == 'Diamond':
                    self.diamond_crv = mc.rename(mc.curve(d=1, p=[(0, 1, 0), (-1, 0.00278996, 6.18172e-08), (0, 0, 1), (0, 1, 0), (1, 0.00278996, 0), (0, 0, 1), (1, 0.00278996, 0), (0, 0, -1), (0, 1, 0), (0, 0, -1), (-1, 0.00278996, 6.18172e-08), (0, -1, 0), (0, 0, -1), (1, 0.00278996, 0), (0, -1, 0), (0, 0, 1)], k=list(range(0, 16))), self.ctrl_name)
                elif self.shape == 'Ring':
                    self.ring_crv = mc.rename(mc.curve(d=1, p=[(-0.707107, 0.0916408, 0.707107), (0, 0.0916408, 1), (0, -0.0916408, 1), (-0.707107, -0.0916408, 0.707107), (-0.707107, 0.0916408, 0.707107), (-1, 0.0916408, 0), (-1, -0.0916408, 0), (-0.707107, -0.0916408, 0.707107), (-1, -0.0916408, 0), (-0.707107, -0.0916408, -0.707107), (-0.707107, 0.0916408, -0.707107), (-1, 0.0916408, 0), (-0.707107, 0.0916408, -0.707107), (0, 0.0916408, -1), (0, -0.0916408, -1), (-0.707107, -0.0916408, -0.707107), (-0.707107, 0.0916408, -0.707107), (-0.707107, -0.0916408, -0.707107), (0, -0.0916408, -1), (0.707107, -0.0916408, -0.707107), (0.707107, 0.0916408, -0.707107), (0, 0.0916408, -1), (0.707107, 0.0916408, -0.707107), (1, 0.0916408, 0), (1, -0.0916408, 0), (0.707107, -0.0916408, -0.707107), (1, -0.0916408, 0), (0.707107, -0.0916408, 0.707107), (0.707107, 0.0916408, 0.707107), (1, 0.0916408, 0), (0.707107, 0.0916408, 0.707107), (0, 0.0916408, 1), (0, -0.0916408, 1), (0.707107, -0.0916408, 0.707107)], k=list(range(0, 34))), self.ctrl_name)
                elif self.shape == 'Cone':
                    self.cone_crv = mc.rename(mc.curve(d=1, p=[(-0.5, -1, 0.866025), (0, 1, 0), (0.5, -1, 0.866025), (-0.5, -1, 0.866025), (-1, -1, -1.5885e-07), (0, 1, 0), (-1, -1, -1.5885e-07), (-0.5, -1, -0.866026), (0, 1, 0), (0.5, -1, -0.866025), (-0.5, -1, -0.866026), (0.5, -1, -0.866025), (0, 1, 0), (1, -1, 0), (0.5, -1, -0.866025), (1, -1, 0), (0.5, -1, 0.866025)], k=list(range(0, 17))), self.ctrl_name)
                elif self.shape == 'Pointer':
                    self.pointer_crv = mc.rename(mc.curve(d=1, p=[(0, 1.003235, 0), (0.668823, 0, 0), (0.334412, 0, 0), (0.334412, -0.167206, 0), (0.334412, -0.501617, 0), (0.334412, -1.003235, 0), (-0.334412, -1.003235, 0), (-0.334412, -0.501617, 0), (-0.334412, -0.167206, 0), (-0.334412, 0, 0), (-0.668823, 0, 0), (0, 1.003235, 0), (0, 0, -0.668823), (0, 0, -0.334412), (0, -0.167206, -0.334412), (0, -0.501617, -0.334412), (0, -1.003235, -0.334412), (0, -1.003235, 0.334412), (0, -0.501617, 0.334412), (0, -0.167206, 0.334412), (0, 0, 0.334412), (0, 0, 0.668823), (0, 1.003235, 0)], k=list(range(0, 23))), self.ctrl_name)
                elif self.shape == 'Sphere':
                    self.sphere_crv = mc.rename(mc.curve(d=1, p=[(-0.369552, 0, 0.153073), (-0.282843, 0, 0.282843), (-0.153073, 0, 0.369552), (0, 0, 0.4), (0.153073, 0, 0.369552), (0.282843, 0, 0.282843), (0.369552, 0, 0.153073), (0.4, 0, 0), (0.369552, 0, -0.153073), (0.282843, 0, -0.282843), (0.153073, 0, -0.369552), (0, 0, -0.4), (-0.153073, 0, -0.369552), (-0.282843, 0, -0.282843), (-0.369552, 0, -0.153073), (-0.4, 0, 0), (-0.369552, 0.153073, 0), (-0.282843, 0.282843, 0), (-0.153073, 0.369552, 0), (0, 0.4, 0), (0.153073, 0.369552, 0), (0.282843, 0.282843, 0), (0.369552, 0.153073, 0), (0.4, 0, 0), (0.369552, -0.153073, 0), (0.282843, -0.282843, 0), (0.153073, -0.369552, 0), (0, -0.4, 0), (-0.153073, -0.369552, 0), (-0.282843, -0.282843, 0), (-0.369552, -0.153073, 0), (-0.4, 0, 0), (-0.369552, 0, 0.153073), (-0.282843, 0, 0.282843), (-0.153073, 0, 0.369552), (0, 0, 0.4), (0, 0.153073, 0.369552), (0, 0.282843, 0.282843), (0, 0.369552, 0.153073), (0, 0.4, 0), (0, 0.369552, -0.153073), (0, 0.282843, -0.282843), (0, 0.153073, -0.369552), (0, 0, -0.4), (0, -0.153073, -0.369552), (0, -0.282843, -0.282843), (0, -0.369552, -0.153073), (0, -0.4, 0), (0, -0.369552, 0.153073), (0, -0.282843, 0.282843), (0, -0.153073, 0.369552), (0, 0, 0.4)], k=list(range(0, 52))), self.ctrl_name)
                elif self.shape == 'Star':
                    self.star_crv = mc.rename(mc.curve(d=1, p=[(0, -1, 0), (0, -0.6, -0.4), (0, -0.6, -0.2), (0, -0.2, -0.2), (0, -0.2, -0.6), (0, -0.4, -0.6), (0, 0, -1), (0, 0.4, -0.6), (0, 0.2, -0.6), (0, 0.2, -0.2), (0, 0.6, -0.2), (0, 0.6, -0.4), (0, 1, 0), (0, 0.6, 0.4), (0, 0.6, 0.2), (0, 0.2, 0.2), (0, 0.2, 0.6), (0, 0.4, 0.6), (0, 0, 1), (0, -0.4, 0.6), (0, -0.2, 0.6), (0, -0.2, 0.2), (0, -0.6, 0.2), (0, -0.6, 0.4), (0, -1, 0)], k=list(range(0, 25))), self.ctrl_name)
                else:
                    om.MGlobal.displayInfo('No shape matches name : %s' % self.shape)
                try:
                    self.extra_grp = self.av_non_keyable(mc.group(n=self.ctrl_extra_grp))
                    self.offset_grp = self.av_non_keyable(mc.group(n=self.ctrl_offset_grp))
                    self.grp = self.av_non_keyable(mc.group(n=self.ctrl_grp))
                except:
                    pass

        else:
            om.MGlobal.displayInfo('More than one object matches name : %s' % self.name)

    def av_trnsform_lock_unlock(self, object='', translate=1, rotate=1, scale=1, visibility=1):
        for each_object in object:
            if translate == 0:
                mc.setAttr(each_object + '.tx', l=True, cb=False, k=False)
                mc.setAttr(each_object + '.ty', l=True, cb=False, k=False)
                mc.setAttr(each_object + '.tz', l=True, cb=False, k=False)
            if translate == 1:
                mc.setAttr(each_object + '.tx', l=False, cb=False, k=True)
                mc.setAttr(each_object + '.ty', l=False, cb=False, k=True)
                mc.setAttr(each_object + '.tz', l=False, cb=False, k=True)
            if rotate == 0:
                mc.setAttr(each_object + '.rx', l=True, cb=False, k=False)
                mc.setAttr(each_object + '.ry', l=True, cb=False, k=False)
                mc.setAttr(each_object + '.rz', l=True, cb=False, k=False)
            if rotate == 1:
                mc.setAttr(each_object + '.rx', l=False, cb=False, k=True)
                mc.setAttr(each_object + '.ry', l=False, cb=False, k=True)
                mc.setAttr(each_object + '.rz', l=False, cb=False, k=True)
            if scale == 0:
                mc.setAttr(each_object + '.sx', l=True, cb=False, k=False)
                mc.setAttr(each_object + '.sy', l=True, cb=False, k=False)
                mc.setAttr(each_object + '.sz', l=True, cb=False, k=False)
            if scale == 1:
                mc.setAttr(each_object + '.sx', l=False, cb=False, k=True)
                mc.setAttr(each_object + '.sy', l=False, cb=False, k=True)
                mc.setAttr(each_object + '.sz', l=False, cb=False, k=True)
            if visibility == 0:
                mc.setAttr(each_object + '.v', l=True, cb=False, k=False)
            if visibility == 1:
                mc.setAttr(each_object + '.v', l=False, cb=False, k=True)

    def av_create_control(self):
        self.shape = mc.optionMenu('av_ctrl_shape', q=True, v=True)
        self.place = mc.ls(sl=True)
        self.point_constraint = mc.checkBox('av_point_constrain_cb', q=True, v=True)
        self.orient_constraint = mc.checkBox('av_orient_constrain_cb', q=True, v=True)
        self.scale_constraint = mc.checkBox('av_scale_constrain_cb', q=True, v=True)
        self.parent_constraint = mc.checkBox('av_parent_constrain_cb', q=True, v=True)
        self.shape_parent = mc.checkBox('av_shape_parent_cb', q=True, v=True)
        self.just_snap = mc.checkBox('av_just_snap_cb', q=True, v=True)
        self.av_scale = mc.floatField('av_ctrl_size', q=True, v=True)
        self.translate_enable = int(mc.checkBox('av_translate_cb', q=True, v=True))
        self.rotate_enable = int(mc.checkBox('av_rotate_cb', q=True, v=True))
        self.scale_enable = int(mc.checkBox('av_scale_cb', q=True, v=True))
        self.visibility_enable = int(mc.checkBox('av_visibility_cb', q=True, v=True))
        if self.shape_parent == True:
            if len(self.place) >= 1:
                self.name_check = mc.ls(sl=True)
                self.name_check_temp = pm.mel.substituteAllString(self.name_check[0], 'avShape', '')
                mc.select(self.name_check_temp)
                self.name = mc.ls(sl=True)
                self.temp_ctrl_name = self.name[0] + '_Temp'
                self.shape_parent_name = pm.mel.substituteAllString(self.temp_ctrl_name, '_Temp', '')
                try:
                    if not self.shape_parent_name + 'avShape' == True:
                        mc.delete(self.shape_parent_name + 'avShape')
                    self.av_shape(self.shape, self.temp_ctrl_name)
                    mc.select(self.ctrl_name)
                    mc.SelectCurveCVsAll()
                    mc.scale(1 * self.av_scale, 1 * self.av_scale, 1 * self.av_scale, ocp=True, r=True, ws=True)
                    mc.select(self.ctrl_name)
                    self.av_trnsform_lock_unlock([self.ctrl_name], self.translate_enable, self.rotate_enable, self.scale_enable, self.visibility_enable)
                    mc.rename(self.temp_ctrl_name + '_Ctrl', self.shape_parent_name + 'av')
                    mc.parent(self.shape_parent_name + 'avShape', self.shape_parent_name, r=True, s=True)
                    mc.delete(self.ctrl_grp)
                    mc.select(cl=True)
                except:
                    self.av_shape(self.shape, self.temp_ctrl_name)
                    mc.select(self.ctrl_name)
                    mc.SelectCurveCVsAll()
                    mc.scale(1 * self.av_scale, 1 * self.av_scale, 1 * self.av_scale, ocp=True, r=True, ws=True)
                    mc.select(self.ctrl_name)
                    self.av_trnsform_lock_unlock([self.ctrl_name], self.translate_enable, self.rotate_enable, self.scale_enable, self.visibility_enable)
                    mc.rename(self.temp_ctrl_name + '_Ctrl', self.shape_parent_name + 'av')
                    mc.parent(self.shape_parent_name + 'avShape', self.shape_parent_name, r=True, s=True)
                    mc.delete(self.ctrl_grp)
                    mc.select(cl=True)

            else:
                om.MGlobal.displayInfo('Select object')
        else:
            self.name = mc.textField('av_ctrl_name', q=True, tx=True).replace(' ', '_').title()
            if not mc.objExists(self.name + '_Ctrl') == True:
                if len(self.name) >= 1:
                    if len(self.place) >= 1:
                        if self.point_constraint == True:
                            self.av_shape(self.shape, self.name)
                            mc.delete(mc.parentConstraint(self.place, self.ctrl_grp))
                            mc.pointConstraint(self.ctrl_name, self.place, mo=True)
                            mc.select(self.ctrl_name)
                            mc.SelectCurveCVsAll()
                            mc.scale(1 * self.av_scale, 1 * self.av_scale, 1 * self.av_scale, ocp=True, r=True, ws=True)
                            mc.select(self.ctrl_name)
                            self.av_trnsform_lock_unlock([self.ctrl_name], 1, self.rotate_enable, self.scale_enable, self.visibility_enable)
                        if self.orient_constraint == True:
                            self.av_shape(self.shape, self.name)
                            mc.delete(mc.parentConstraint(self.place, self.ctrl_grp))
                            mc.orientConstraint(self.ctrl_name, self.place, mo=True)
                            mc.select(self.ctrl_name)
                            mc.SelectCurveCVsAll()
                            mc.scale(1 * self.av_scale, 1 * self.av_scale, 1 * self.av_scale, ocp=True, r=True, ws=True)
                            mc.select(self.ctrl_name)
                            self.av_trnsform_lock_unlock([self.ctrl_name], self.translate_enable, 1, self.scale_enable, self.visibility_enable)
                        if self.scale_constraint == True:
                            self.av_shape(self.shape, self.name)
                            mc.delete(mc.parentConstraint(self.place, self.ctrl_grp))
                            mc.scaleConstraint(self.ctrl_name, self.place, mo=True)
                            mc.select(self.ctrl_name)
                            mc.SelectCurveCVsAll()
                            mc.scale(1 * self.av_scale, 1 * self.av_scale, 1 * self.av_scale, ocp=True, r=True, ws=True)
                            mc.select(self.ctrl_name)
                            self.av_trnsform_lock_unlock([self.ctrl_name], self.translate_enable, self.rotate_enable, 1, self.visibility_enable)
                        if self.parent_constraint == True:
                            self.av_shape(self.shape, self.name)
                            mc.delete(mc.parentConstraint(self.place, self.ctrl_grp))
                            mc.parentConstraint(self.ctrl_name, self.place, mo=True)
                            mc.select(self.ctrl_name)
                            mc.SelectCurveCVsAll()
                            mc.scale(1 * self.av_scale, 1 * self.av_scale, 1 * self.av_scale, ocp=True, r=True, ws=True)
                            mc.select(self.ctrl_name)
                            self.av_trnsform_lock_unlock([self.ctrl_name], 1, 1, self.scale_enable, self.visibility_enable)
                        if self.just_snap == True:
                            self.av_shape(self.shape, self.name)
                            mc.delete(mc.parentConstraint(self.place, self.ctrl_grp))
                            mc.select(self.ctrl_name)
                            mc.SelectCurveCVsAll()
                            mc.scale(1 * self.av_scale, 1 * self.av_scale, 1 * self.av_scale, ocp=True, r=True, ws=True)
                            mc.select(self.ctrl_name)
                            self.av_trnsform_lock_unlock([self.ctrl_name], self.translate_enable, self.rotate_enable, self.scale_enable, self.visibility_enable)
                    else:
                        om.MGlobal.displayInfo('Select object')
                else:
                    om.MGlobal.displayInfo('Enter control name')
            else:
                om.MGlobal.displayInfo('More than one object matches name : %s' % self.name)

    def av_replace_control_shape(self):
        self.av_scale = mc.floatField('av_ctrl_size', q=True, v=True)
        self.shape = mc.optionMenu('av_ctrl_repalce_shape', q=True, v=True)
        if len(mc.ls(sl=True)) >= 1:
            self.name_check = mc.ls(sl=True)
            self.name_check_temp = pm.mel.substituteAllString(self.name_check[0], 'avShape', '')
            mc.select(self.name_check_temp)
            self.name = mc.ls(sl=True)
            self.temp_ctrl_name = self.name[0] + '_Temp'
            self.old_shape_name = mc.listRelatives(self.name[0], s=True)
            if not self.old_shape_name == True:
                mc.delete(self.old_shape_name)
            self.shape_parent_name = pm.mel.substituteAllString(self.temp_ctrl_name, '_Temp', '')
            try:
                if not self.shape_parent_name + 'avShape' == True:
                    mc.delete(self.shape_parent_name + 'avShape')
                self.av_shape(self.shape, self.temp_ctrl_name)
                mc.select(self.ctrl_name)
                mc.SelectCurveCVsAll()
                mc.scale(1 * self.av_scale, 1 * self.av_scale, 1 * self.av_scale, ocp=True, r=True, ws=True)
                mc.select(self.ctrl_name)
                mc.rename(self.temp_ctrl_name + '_Ctrl', self.shape_parent_name + 'av')
                mc.parent(self.shape_parent_name + 'avShape', self.shape_parent_name, r=True, s=True)
                mc.delete(self.ctrl_grp)
                mc.select(cl=True)
                mc.rename(self.shape_parent_name + 'avShape', self.old_shape_name)
            except:
                self.av_shape(self.shape, self.temp_ctrl_name)
                mc.select(self.ctrl_name)
                mc.SelectCurveCVsAll()
                mc.scale(1 * self.av_scale, 1 * self.av_scale, 1 * self.av_scale, ocp=True, r=True, ws=True)
                mc.select(self.ctrl_name)
                mc.rename(self.temp_ctrl_name + '_Ctrl', self.shape_parent_name + 'av')
                mc.parent(self.shape_parent_name + 'avShape', self.shape_parent_name, r=True, s=True)
                mc.delete(self.ctrl_grp)
                mc.select(cl=True)
                mc.rename(self.shape_parent_name + 'avShape', self.old_shape_name)

        else:
            om.MGlobal.displayInfo('Select object')