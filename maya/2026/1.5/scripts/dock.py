import maya.cmds as cmds
 
import inspect
 
import maya.OpenMayaUI as omui
 
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
 
# Maya 2025+ ships PySide6 (Qt6); older versions ship PySide2.
try:
    from PySide6 import QtGui, QtCore, QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets
 
# Maya Bug introduced in 2018
 
# Global holds all widgets restored from maya preferences so that qt doesnt garbage collect
 
# them if they aren't currently visible (ex: in a docked tab that isn't the currently displayed tab).
 
restored_widgets = []
 
class DockManager(object):
 
    def __init__(self):
 
        '''
 
        Must be overriden per UI.
 
        '''
 
        # Main UI widget class for tool
 
        self.mixin_cls = None
 
        # Name used by my to reference UI
 
        self.window_name = None
 
    @classmethod
 
    def show(cls, debug=True):
 
        '''
 
        Call to re-show or initiate the UI.
 
        :param bool debug: Set to True to re-initialize an existing UI.
 
        '''
 
        # init dock manager
 
        instance=cls()
 
        # Test if tool is already open
 
        if cmds.workspaceControl(instance.window_name + 'WorkspaceControl', ex=True):
 
            # Used to bypass saved dock preferences in maya workspaces. Useful for testing without restarting maya
 
            if debug:
 
                # Deletes existing UI
 
                cmds.deleteUI(instance.window_name + 'WorkspaceControl')
 
                # Init new dock manager
 
                instance.__init__()
 
                # Rerun this show to create new UI. (the else below)
 
                instance.show()
 
            # Shows UI
 
            cmds.workspaceControl(instance.window_name + 'WorkspaceControl', edit=True, restore=True)
 
        else:
 
            # Create mixin widget
 
            workspace_widget = instance.mixin_cls()
 
            # Get class name of widget
 
            class_name = instance.__class__.__name__
 
            # Get module name of widget
 
            module_name = inspect.getmodule(instance).__name__
 
            # Show widget and attach uiScript for restoring widget from maya close using class_name and module_name
 
            #  to define path to restore_from_close classmethod.
 
            # Import is in the uiScript to handle the case where it is not present in usersetup.py
 
            workspace_widget.show(dockable=True, uiScript='import {0}\n{0}.{1}.restore_from_close()'.format(module_name, class_name))
 
    @classmethod
 
    def restore_from_close(cls):
 
        '''
 
        Called by Maya from the preferences when starting a new session to restore last session's ui.
 
        '''
 
        # Init dock manager
 
        instance = cls()
 
        # Get the current maya control that the mixin widget should parent to
 
        restored_control = omui.MQtUtil.getCurrentParent()
 
        # Create mixin widget
 
        widget = instance.mixin_cls()
 
        # Find the widget created above as a maya control (aka a maya class)
 
        mixin_ptr = omui.MQtUtil.findControl(widget.objectName())
 
        # Hold on to pointer to widgte so qt doesnt garbage collect it
 
        restored_widgets.append(widget)
 
        # Add mixin widget to container UI
 
        omui.MQtUtil.addWidgetToMayaLayout(int(mixin_ptr), int(restored_control))
 
class MayaMixin(MayaQWidgetDockableMixin, QtWidgets.QWidget):
 
    def __init__(self, window_name, main_widget_cls, title, **kwargs):
 
        '''
 
        Wrapper for incoming widget(main_widget_cls).
 
        A Qwidget that is registered as a Maya Control (aka maya class wrapped UI) that is a container for our custom UI.
 
        :param str window_name: name used internally by maya to identify mixin
 
        :param QtWidgets.QWidget main_widget_cls: widget class to get wrapped in mixin
 
        :param str title: title for window/tab
 
        :param kwargs:
 
        '''
 
        super(MayaMixin, self).__init__(**kwargs)
 
        # Set the ui object name. Used by maya to find UI as maya control class
 
        self.setObjectName(window_name)
 
        # Layout to hold main_widget_cls
 
        self._mainLayout = QtWidgets.QVBoxLayout()
 
        # Set no margins so layout doesnt bulk up UI
 
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
 
        # Set the layout for this Qwidget
 
        self.setLayout(self._mainLayout)
 
        # Init main_widget_cls widget
 
        self.mainWidget = main_widget_cls()
 
        # Add mainWidget to the layout
 
        self._mainLayout.addWidget(self.mainWidget)
 
        # Set the title of the mixin widget
 
        self.setWindowTitle(title)