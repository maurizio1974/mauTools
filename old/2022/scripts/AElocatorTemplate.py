from maya import cmds, OpenMaya, OpenMayaUI
import maya.mel as mel
from pymel.core import *

class AEBaseTemplate(ui.AETemplate):
    def __init__(self, nodeName):
        ui.AETemplate.__init__(self, nodeName)

        self.__nodeName = nodeName

        #beginLayout
        cmds.editorTemplate(beginScrollLayout = True, collapse = False)
        cmds.editorTemplate(beginLayout = "Mau Stuff", collapse = False)

        #ButtonCommand
        self.callCustom(self.new, self.replace, '')
        cmds.editorTemplate(endLayout = True)


        self.addExtraControls(label="Attributes")
        mel.AEdependNodeTemplate(self.__nodeName)

        cmds.editorTemplate(endScrollLayout=True)

    def openNodeEditor(self, arg):
        mel.eval("NodeEditorWindow;")

    def openGraphEditor(self, arg):
        mel.eval("GraphEditor;")


    def new(self, attr):
        cmds.setUITemplate("attributeEditorTemplate", pushTemplate=True)
        cmds.button(label='Open Node Editor', command=self.openNodeEditor)
        # cmds.button(label='Open Graph Editor', command=self.openGraphEditor)
        cmds.setUITemplate(popTemplate=True)

    def replace(self, attr):
        pass

class AElocatorTemplate(AEBaseTemplate):
    _nodeType = 'locator'
