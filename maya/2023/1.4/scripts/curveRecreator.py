#--------------------------------------------------------------------------------#
#             only for maya 2011+
#
#
#             curveRecreator.py
#             version 2.1, last modified 30/04/2015
#             Copyright (C) 2015 Perry Leijten
#             Email: perryleijten@gmail.com
#             Website: www.perryleijten.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See http://www.gnu.org/licenses/gpl.html for a copy of the GNU General
# Public License.
#--------------------------------------------------------------------------------#
#                    I N S T A L L A T I O N:
#
# Copy the "curveRecreator.py" together with "ControlCurveCreater.ui", Icon folder and curves folder to your Maya scriptsdirectory:
#     MyDocuments\Maya\scripts\
#         use this text as a python script within Maya:
'''
import curveRecreator
curveRecreator.StartUI()
'''
# this text can be entered from the script editor and can be made into a button
#
# note: PyQt and sip or pyside  libraries are necessary to run this file
import curveRecreator, os, sys, re, stat, functools,shutil, platform, logging

from maya import mel, cmds, OpenMayaUI

uiLanguage = cmds.about(uil=True)

if uiLanguage == "ja_JP":
    language = {"subwindowTitle":       "\u30b3\u30f3\u30c8\u30ed\u30fc\u30e9\u753b\u50cf",
                "normalText":           "\u6cd5\u7dda",
                "templateText":         "\u30c6\u30f3\u30d7\u30ec\u30fc\u30c8",
                "referenceText":        "\u5f15\u304d\u5408\u3044",
                "displayTitle":         "\u9673\u5217",
                "assignColor":          "\u9078\u629e\u3057\u305f\u30aa\u30d6\u30b8\u30a7\u30af\u30c8\u306b\u8272\u3092\u5272\u308a\u5f53\u3066\u307e\u3059:",
                "saveTitle":            "\u6551\u3046",
                "saveLabel":            "\u30b3\u30f3\u30c8\u30ed\u30fc\u30e9\u3092\u4fdd\u5b58",
                "nameCheck":            "\u4f7f\u7528\u30b3\u30f3\u30c8\u30ed\u30fc\u30eb\u540d",
                "centered":             "\u4e2d\u5fc3",
                "GiveName":             "\u307e\u305f\u306f\u3001\u3053\u306e\u540d\u524d\u3092\u4ed8\u3051\uff1a",
                "curveButton":          "\u66f2\u7dda\u3092\u53d6\u5f97\u3057\u307e\u3059",
                "textTitle":            "\u30c6\u30ad\u30b9\u30c8",
                "textLabel":            "\u30c6\u30ad\u30b9\u30c8\u30b3\u30f3\u30c8\u30ed\u30fc\u30e9\u30fc\u3092\u4f5c\u6210\u3057\u307e\u3059\u3002:",
                "textButton":           "\u30c6\u30ad\u30b9\u30c8\u3092\u4f5c\u6210",
                "loadTitle":            "\u30ed\u30fc\u30c9",
                "loadLabel":            "\u8ca0\u8377\u30b3\u30f3\u30c8\u30ed\u30fc\u30e9\uff1a",
                "combine":              "\u66f2\u7dda\u3092\u7d44\u307f\u5408\u308f\u305b\u307e\u3059",
                "delete":               "\u524a\u9664",
                "closelabel":           "\u30af\u30ed\u30fc\u30ba",
                "Control_Creator":      "\u30b3\u30f3\u30c8\u30ed\u30fc\u30eb\u30af\u30ea\u30a8\u30fc\u30bf\u30fc",
                "Control_Creator_Dock": "\u5236\u5fa1\u30af\u30ea\u30a8\u30fc\u30bf\u30fc\u30c9\u30c3\u30af",
                "modelPanel":           "\u66f2\u7dda\u306e\u30e2\u30c7\u30eb\u30d1\u30cd\u30eb",
                "saveAndClose":         "\u4fdd\u5b58\u3057\u3066\u9589\u3058\u307e\u3059",
                "Author":               "Author",
                "Date":                 "Date",
                "Version":              "Version",
                "Web":                  "Web",
                "warning1":             "warning, nothing selected to copy!",
                "warning2":             "No text put in the textfield!",
                "warning3":             "PySide and PyQt4 not found"}
else:
    language = {"subwindowTitle":       "Controller Image",
                "normalText":           "Normal",
                "templateText":         "Template",
                "referenceText":        "Reference",
                "displayTitle":         "Display",
                "assignColor":          "Assign color to selected objects:",
                "saveTitle":            "Save",
                "saveLabel":            "Save Controller:",
                "nameCheck":            "Use Control name",
                "centered":             "Center",
                "GiveName":             "or Give this name:",
                "curveButton":          "Get Curve",
                "textTitle":            "Text",
                "textLabel":            "Create Text Controller:",
                "textButton":           "Create Text",
                "loadTitle":            "Load",
                "loadLabel":            "Load Controller:",
                "combine":              "Combine Curves",
                "delete":               "Delete",
                "closelabel":           "Close",
                "Control_Creator":      "Control_Creator",
                "Control_Creator_Dock": "Control_Creator_Dock",
                "modelPanel":           "ModelPanel for Curves",
                "saveAndClose":         "Save and Close",
                "Author":               "Author",
                "Date":                 "Date",
                "Version":              "Version",
                "Web":                  "Web",
                "warning1":             "warning, nothing selected to copy!",
                "warning2":             "No text put in the textfield!",
                "warning3":             "PySide and PyQt4 not found"}

default = "none"
try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4 import uic, QtGui
    import sip
    logging.Logger.manager.loggerDict["PyQt4.uic.uiparser"].setLevel(logging.CRITICAL)
    logging.Logger.manager.loggerDict["PyQt4.uic.properties"].setLevel(logging.CRITICAL)
    default = "pyqt4"
except:
    try:
        import xml.etree.ElementTree as xml
        from io import StringIO
        from PySide.QtGui import *
        from PySide.QtCore import *
        from PySide import QtGui
        import pysideuic, shiboken
        logging.Logger.manager.loggerDict["pysideuic.uiparser"].setLevel(logging.CRITICAL)
        logging.Logger.manager.loggerDict["pysideuic.properties"].setLevel(logging.CRITICAL)
        default = "pyside"
    except:
        try:
            import xml.etree.ElementTree as xml
            from io import StringIO
            from PySide2.QtGui import *
            from PySide2.QtCore import *
            from PySide2.QtWidgets import *
            from PySide2 import QtGui
            import pyside2uic as pysideuic
            import shiboken2 as shiboken
            logging.Logger.manager.loggerDict["pyside2uic.uiparser"].setLevel(logging.CRITICAL)
            logging.Logger.manager.loggerDict["pyside2uic.properties"].setLevel(logging.CRITICAL)
            default = "pyside2"
        except:
            print(language["warning3"])

print(default)

def loadUiType( uiFile ):
    '''workaround to be able to load QT designer uis with both PySide and PyQt4'''
    # http://nathanhorne.com/?p=451
    if default ==  "pyqt4":
        form_class, base_class =  uic.loadUiType( uiFile )
    else:
        parsed = xml.parse( uiFile )
        widget_class = parsed.find( 'widget' ).get( 'class' )
        form_class = parsed.find( 'class' ).text

        with open( uiFile, 'r' ) as f:
            o = StringIO()
            frame = {}

            pysideuic.compileUi( f, o, indent=0 )
            pyc = compile( o.getvalue(), '<string>', 'exec' )
            exec(pyc, frame)

            form_class = frame[ 'Ui_%s'%form_class ]
            base_class = eval( '%s'%widget_class )
    return form_class, base_class

def wrapinstance( ptr, base=None ):
    '''workaround to be able to wrap objects with both PySide and PyQt4'''
    # http://nathanhorne.com/?p=485'''
    if ptr is None:
        return None
    ptr = int( ptr )
    if 'shiboken' in globals():
        if base is None:
            qObj = shiboken.wrapInstance( int( ptr ), QObject )
            metaObj = qObj.metaObject()
            cls = metaObj.className()
            superCls = metaObj.superClass().className()
            if hasattr( QtGui, cls ):
                base = getattr( QtGui, cls )
            elif hasattr( QtGui, superCls ):
                base = getattr( QtGui, superCls )
            else:
                base = QWidget
        return shiboken.wrapInstance( int( ptr ), base )
    elif 'sip' in globals():
        base = QObject
        return sip.wrapinstance( int( ptr ), base )
    else:
        return None

FilePath = os.path.dirname(__file__)
Control_CreatorUI_form, Control_CreatorUI_base         = loadUiType('%s/ControlCurveCreator.ui'%FilePath )
Control_CreatorUI_form_sub, Control_CreatorUI_base_sub = loadUiType('%s/controlImageInterface.ui'%FilePath)

# subwindow for creation of images
class SubWindow(Control_CreatorUI_form_sub, Control_CreatorUI_base_sub):
    def __init__(self, parent = None, filePath = None, inputPreset = None , name = 'test', ischecked = True):
        super(SubWindow , self).__init__(parent)
        self.setupUi(self)

        self.isChecked     = ischecked
        self.__itemCreated = False
        self.inputPresets  = inputPreset
        self.name          = name
        self.filePath      = filePath

        self.setObjectName("subwindow")
        self.setWindowTitle(language["subwindowTitle"])
        self.viewportLayout.setObjectName("mainLayout")

        polyDetails    = cmds.optionVar(q='polyCountVisibility')
        self.polyCount = False
        if polyDetails == 1 :
            cmds.TogglePolyCount()
            self.polyCount = True

        self.__addViewport()
        self.SaveAndCloseButton.clicked.connect(self.__saveAndClose)
        self.SaveAndCloseButton.setText(language["saveAndClose"])

    def __addViewport(self, *args):
        if default == "pyqt4":
            layout = OpenMayaUI.MQtUtil.fullName(int(sip.unwrapinstance(self.viewportLayout)))
        else:
            layout = OpenMayaUI.MQtUtil.fullName(int(shiboken.getCppPointer(self.viewportLayout)[0]))
        cmds.setParent(layout)

        paneLayoutName = cmds.paneLayout("test")
        ptr = OpenMayaUI.MQtUtil.findControl(paneLayoutName)

        self.paneLayout = wrapinstance(int(ptr))
        self.cameraName = cmds.camera()[0]
        cmds.hide(self.cameraName)
        self.modelPanelName = cmds.modelPanel(label=language["modelPanel"], cam=self.cameraName, mbv=False)

        mel.eval('modelPanelBarDecorationsCallback("GridBtn","'+self.modelPanelName+'", "'+self.modelPanelName+'|modelEditorIconBar");')
        ptr = OpenMayaUI.MQtUtil.findControl(self.modelPanelName)
        self.modelPanel = wrapinstance(int(ptr))

        self.viewportLayout.addWidget(self.paneLayout)

        cmds.modelEditor( self.modelPanelName, edit = True, displayAppearance='smoothShaded', lw=2)
        cmds.viewFit( self.cameraName, all=True )
        barLayout = cmds.modelPanel(self.modelPanelName, q=True, bl=True)
        ptr = OpenMayaUI.MQtUtil.findControl(barLayout)
        self.barLayout = wrapinstance(int(ptr))
        children =  self.barLayout.children()

        if default == "pyqt4":
            sip.delete(children[0])

    def createSnapshot(self, width=200, height=200):
        cmds.setFocus(self.modelPanelName)

        filename=self.filePath+ 'Curves/' + self.name
        try:
            f = cmds.playblast(wh=(width,height),
                               fp=0,
                               frame=cmds.currentTime(q=True),
                               format='image',
                               compression='png',
                               forceOverwrite=True,
                               viewer=False)
        except Exception as e:
            cmds.warning(e.message)
        cmds.modelEditor( self.modelPanelName, edit = True,lw =1)
        f = os.path.abspath(f.replace('####', '0'))
        shutil.move(f, filename+'.png')

        return os.path.abspath(filename)

    def __saveAndClose(self, *args):
        self.createSnapshot()
        self.GetControler(self.inputPresets)
        self.__itemCreated = True
        self.close()

    def returnCreatedItem(self):
        return self.__itemCreated

    def closeEvent(self, event):
        cmds.delete(self.cameraName)
        if self.polyCount:
            cmds.TogglePolyCount()

    def __fileWriteOrAdd(self, inFileName, inText, inWriteOption):
        if os.path.exists(inFileName):
            read_only_or_write_able = os.stat(inFileName)[0]
            if read_only_or_write_able != stat.S_IWRITE:
                os.chmod(inFileName, stat.S_IWRITE)

        file = open(inFileName, inWriteOption)
        file.write(inText)
        file.close()

    def GetControler(self, Selected, *args):
        cmds.delete(Selected, ch=True)

        curveDirectory = (self.filePath+ 'Curves/' + self.name+ '.py')

        directory = os.path.dirname(str(curveDirectory))
        if not os.path.exists(directory):
            os.makedirs(directory)

        baseText = 'import maya.cmds as cmds\n'
        self.__fileWriteOrAdd((curveDirectory), baseText, 'w')
        multipleShapes = False

        def completeList(input):
            childrenBase = cmds.listRelatives(input, ad=True, type="transform")
            childrenBase.append(input)
            childrenBase.reverse()
            return childrenBase

        childrenBase = cmds.listRelatives( Selected, ad=True, type="transform")
        if childrenBase:
            selection = completeList(Selected)
        else:
            selection = [Selected]

        for Selected in selection:
            shapeNode = cmds.listRelatives(Selected, s=True, f=True)
            listdef = '%s = []\n'%Selected
            self.__fileWriteOrAdd((curveDirectory), listdef, 'a')


            for shapes in shapeNode:
                controlVerts      = cmds.getAttr(shapes+'.cv[*]')
                curveDegree       = cmds.getAttr(shapes+'.degree')
                period            = cmds.getAttr(shapes+'.f')
                localPosition     = cmds.getAttr(Selected+'.translate')
                worldPosition     = cmds.xform(Selected, q=True, piv=True, ws=True)

                print(controlVerts)
                infoNode = cmds.createNode('curveInfo')
                cmds.connectAttr((shapes + '.worldSpace'), (infoNode+'.inputCurve'))

                if len(shapeNode) > 1:
                    multipleShapes = True

                list1 = []
                list2 = []
                list3 = []

                knots = cmds.getAttr(infoNode+'.knots')
                for i in knots[0]:
                    list3.append(int(i))

                if self.isChecked:
                    for i in range(len(controlVerts)):
                        for j in range(3):
                            originCalculation     =  (float(controlVerts[i][j])-float(worldPosition[j]))
                            localSpaceAddition    =  originCalculation + float(localPosition[0][j])
                            list1.append(localSpaceAddition)
                        list2.append(list1)
                        list1=[]
                else:
                    list2 = controlVerts

                if period == 0 :
                    periodNode = ',per = False'
                else:
                    periodNode = ',per = True'
                    for i in range(curveDegree):
                        list2.append(list2[i])

                CurveCreation = ('cmds.curve( p =' + str(list2).replace('[','(').replace(']',')').replace('((','[(').replace('))',')]') + periodNode+ ', d=' + str(curveDegree) + ', k=' + str(list3)  + ')')
                CurveCreation = ('%s.append('%Selected+CurveCreation+')')
                self.__fileWriteOrAdd((curveDirectory), str(CurveCreation+'\n'), 'a')

                cmds.delete(infoNode)

            if multipleShapes == True:
                End = 'for x in range(len(%s)-1):\n\tcmds.makeIdentity(%s[x+1], apply=True, t=1, r=1, s=1, n=0)\n\tshapeNode = cmds.listRelatives(%s[x+1], shapes=True)\n\tcmds.parent(shapeNode, %s[0], add=True, s=True)\n\tcmds.delete(%s[x+1])\n'%(Selected,Selected,Selected,Selected,Selected)
                self.__fileWriteOrAdd((curveDirectory), End, 'a')

            parentObject = cmds.listRelatives(Selected, parent=True)
            if parentObject:
                listdef = 'cmds.parent(%s[0], %s[0])\n'%(Selected, parentObject[0])
                self.__fileWriteOrAdd((curveDirectory), listdef, 'a')

        close = 'fp = cmds.listRelatives(%s[0], f=True)[0]\npath = fp.split("|")[1]\ncmds.select(path)'%Selected
        self.__fileWriteOrAdd((curveDirectory), close, 'a')

class Control_CreatorUI(Control_CreatorUI_form, Control_CreatorUI_base):
    def __init__(self, parent=None):
        super(Control_CreatorUI, self).__init__(parent)
        self.setupUi(self)
        self.mayaVersion = int(str(cmds.about(apiVersion=True))[:-2])

        self.__ColorCurveCommand()
        self.__getAllFonts()
        self.__BasicTestSetting()
        self.__readOutFiles()
        self.__CheckNameGet()

        self.presetPath = FilePath

        self.__qt_normal_color = QPalette(self.ControlNameLineEdit.palette()).color(QPalette.Base)

        self.GetCurveButton.clicked.connect(self.__imageCreationWindow)
        self.CreateTextButton.clicked.connect(self.__createText)
        self.CombineButton.clicked.connect(self.CombineCurveShapes)
        self.TextlineEdit.textEdited[str].connect(self.__ButtonEnable)
        self.ControlNameLineEdit.textEdited[str].connect(    self.__lineEdit_FieldEditted)
        self.NamecheckBox.toggled.connect(self.__CheckNameGet)
        self.normal_state_Button.clicked.connect(self.__normalStateObject)
        self.template_state_Button.clicked.connect(self.__templateStateObject)
        self.refference_state_Button.clicked.connect(self.__refferenceStateObject)
        self.presetsTreeWidget.itemSelectionChanged.connect(self.__handleChanged)

        if self.mayaVersion < 2015:
            self.Color_comboBox.hide()
        self.Color_comboBox.currentIndexChanged.connect(self.__changeColorPicker)

        self.presetsTreeWidget.itemDoubleClicked.connect(self.__doubleClicked)

        self.deleteButton.clicked.connect(self._deletecontroller)

        def keyPressEventOverride(superFn, event):
            key = event.key()
            if key == Qt.Key_Control or key == Qt.Key_Shift: return
            superFn(event)

        buttonIcon = QIcon("%s/Icon/%s.png"%(os.path.dirname(__file__), "TextCurve"))
        self.InfoButton.setIcon(buttonIcon)


        fn = self.TextlineEdit.keyPressEvent
        superFn  = functools.partial(fn, self.TextlineEdit)
        self.TextlineEdit.keyPressEvent = functools.partial(keyPressEventOverride, fn)

        fn = self.ControlNameLineEdit.keyPressEvent
        superFn  = functools.partial(fn, self.ControlNameLineEdit)
        self.ControlNameLineEdit.keyPressEvent = functools.partial(keyPressEventOverride, fn)

        self.languageSetup()

    def languageSetup(self):
        self.normal_state_Button.setText(language["normalText"])
        self.template_state_Button.setText(language["templateText"])
        self.refference_state_Button.setText(language["referenceText"])
        self.groupBox_4.setTitle(language["displayTitle"])
        self.label.setText(language["assignColor"])
        self.groupBox_2.setTitle(language["saveTitle"])
        self.label_4.setText(language["saveLabel"])
        self.NamecheckBox.setText(language["nameCheck"])
        self.centeredCheck.setText(language["centered"])
        self.label_2.setText(language["GiveName"])
        self.GetCurveButton.setText(language["curveButton"])
        self.groupBox_3.setTitle(language["textTitle"])
        self.label_3.setText(language["textLabel"])
        self.CreateTextButton.setText(language["textButton"])
        self.groupBox.setTitle(language["loadTitle"])
        self.label_5.setText(language["loadLabel"])
        self.CombineButton.setText(language["combine"])
        self.deleteButton.setText(language["delete"])

    def _deletecontroller(self, *args):
        getItem = self.presetsTreeWidget.selectedItems()
        path = FilePath+ 'Curves/'
        if not getItem == []:
            inObject = getItem[0].text(0)
            try:
                os.remove(path + str(inObject) + '.png' )
            except:
                pass
            try:
                os.remove(path + str(inObject) + '.py' )
            except:
                pass
        self.__readOutFiles()

    def __imageCreationWindow(self, *args):
        selection = cmds.ls(sl=True)
        if len(selection) == 0:
            cmds.warning(language["warning1"])
        else:
            for Selected in selection:
                checked = self.NamecheckBox.isChecked()
                if checked:
                    curvename = Selected
                else:
                    InputText = self.ControlNameLineEdit.displayText()
                    curvename = InputText

                mel.eval("HideUnselectedObjects;")

                MayaWindowPtr = wrapinstance(int( OpenMayaUI.MQtUtil.mainWindow() ))
                ischecked = self.centeredCheck.isChecked()
                print(ischecked)
                subWindow = SubWindow(MayaWindowPtr ,filePath= self.presetPath, inputPreset=Selected, name =curvename, ischecked = ischecked)
                subWindow.exec_()
                if subWindow.returnCreatedItem():
                    self.__readOutFiles()

                mel.eval("ShowLastHidden;")
                self.__readOutFiles()

    def __normalStateObject(self, *args):
        self.DisplayType(0)
    def __templateStateObject(self, *args):
        self.DisplayType(1)
    def __refferenceStateObject(self, *args):
        self.DisplayType(2)

    def __CheckNameGet(self,*args):
        checked = self.NamecheckBox.isChecked()
        if checked == True:
            self.ControlNameLineEdit.setEnabled(False)
        else:
            self.ControlNameLineEdit.setEnabled(True)
            self.__lineEdit_FieldEditted()

    def __lineEdit_FalseFolderCharacters(self, inLineEdit):
        return re.search(r'[\\/:<>"!@#$%^&-.]', inLineEdit) or re.search(r'[*?|]', inLineEdit) or re.match(r'[0-9]', inLineEdit)

    def __lineEdit_Color(self, inLineEdit, inColor):
        PalleteColor = QPalette(inLineEdit.palette())
        PalleteColor.setColor(QPalette.Base,QColor(inColor))
        inLineEdit.setPalette(PalleteColor)

    def __lineEdit_FieldEditted(self,*args):
        Controller_name_text = self.ControlNameLineEdit.displayText()

            # Give object field a red color if the input contains wrong characters
        if self.__lineEdit_FalseFolderCharacters(Controller_name_text) != None:
            self.__lineEdit_Color(self.ControlNameLineEdit, 'red')
            self.GetCurveButton.setEnabled(False)
        elif Controller_name_text == "":
            self.GetCurveButton.setEnabled(False)
        else:
            self.__lineEdit_Color(self.ControlNameLineEdit, self.__qt_normal_color)
            self.GetCurveButton.setEnabled(True)

    def CombineCurveShapes(self, *args):
        cmds.undoInfo(ock=True)
        selection  = cmds.ls(selection=True)
        for i in selection:
            cmds.xform(i, ws=True, piv = (0,0,0))
        cmds.makeIdentity(selection, apply=True, t=1, r=1, s=1, n=0)
        base = selection[0]
        selection.remove(base)
        for i in selection:
            shapeNode = cmds.listRelatives(i, shapes=True)

            cmds.parent(shapeNode, base, add=True, s=True)
            cmds.delete(i)
        cmds.select(base)
        cmds.undoInfo(cck=True)

    def __getAllFonts(self, *args):
        fontList = []
        fonts = cmds.fontDialog(FontList=True)
        for i in fonts:
            removed = i.split('-')
            fontList.append(removed[0])

        AllFonts = self.__RemoveDuplicates(fontList)
        for i in AllFonts:
            self.FontComboBox.addItem(i)

    def __RemoveDuplicates(self, seq):
        noDuplicates = []
        [noDuplicates.append(i) for i in seq if not noDuplicates.count(i)]
        return noDuplicates

    def __BasicTestSetting(self):
        menu_items = self.FontComboBox.count()
        self.__read_hda = []

            # Set base filter as empty filter  (NoFilter)
        for i in range(menu_items):
            if self.FontComboBox.itemText(i) == "Times New Roman":
                self.FontComboBox.setCurrentIndex(i)

    def __changeColorPicker(self):
        if self.removeableObjects != None:
            for child in self.removeableObjects:
                try:
                   cmds.deleteUI(child)
                except:
                    pass

        if self.Color_comboBox.currentIndex() == 0:
            self.__ColorCurveCommand()
        else:
            self.__ColorRgbCommand()

    def __ColorRgbCommand(self):
        self.removeableObjects = []
        if default == "pyqt4":
            parentlayout = OpenMayaUI.MQtUtil.fullName( int(sip.unwrapinstance(self.formColorLayout)) )
        else:
            parentlayout = OpenMayaUI.MQtUtil.fullName( int(shiboken.getCppPointer(self.formColorLayout)[0]) )
        self.colorSlider = cmds.colorSliderGrp( label='Color: ', rgb=(0, 0, 1), p=parentlayout )
        button = cmds.button( l='Set Color', parent=parentlayout, c=('import maya.cmds as cmds\nselection = cmds.ls(sl=True)\ncolorSet = cmds.colorSliderGrp("%s", q=True, rgb=True)\nfor select in selection:\n\tshapes = cmds.listRelatives(select,ad=True,s=True,f=True )\n\tfor node in shapes:\n\t\tcmds.setAttr(node + ".overrideRGBColors", 1)\n\t\tcmds.setAttr((node+".overrideEnabled"), 1)\n\t\tcmds.setAttr((node+".overrideColorRGB"), colorSet[0], colorSet[1], colorSet[2])'%self.colorSlider))

        self.removeableObjects.append(self.colorSlider)
        self.removeableObjects.append(button)

    def __ColorCurveCommand(self):
        self.colorList = [[0,[0.38, 0.38, 0.38], 'None'],    [1,[0.0, 0.0, 0.0]],         [2,[0.75, 0.75, 0.75]],
                          [3,[0.5, 0.5, 0.5]],               [4,[0.8, 0.0, 0.2]],         [5,[0.0, 0.0, 0.4]],
                          [6,[0.0, 0.0, 1.0]],               [7,[0.0, 0.3, 0.0]],         [8,[0.2, 0.0, 0.2]],
                          [9,[0.8, 0.0, 0.8]],               [10,[0.6, 0.3, 0.2]],        [11,[0.25, 0.13, 0.13]],
                          [12,[0.7,0.2,0.0]],                [13,[1.0,0.0,0.0]],          [14,[0.0,1.0,0.0]],
                          [15,[0.0,0.3,0.6]],                [16,[1.0,1.0,1.0]],          [17,[1.0,1.0,0.0]],
                          [18,[0.0,1.0,1.0]],                [19,[0.0,1.0,0.8]],          [20,[1.0,0.7,0.7]],
                          [21,[0.9,0.7,0.7]],                [22,[1.0,1.0,0.4]],          [23,[0.0,0.7,0.4]],
                          [24,[0.6,0.4,0.2]],                [25,[0.63,0.63,0.17]],       [26,[0.4,0.6,0.2]],
                          [27,[0.2,0.63,0.35]],              [28,[0.18,0.63,0.63]],       [29,[0.18,0.4,0.63]],
                          [30,[0.43,0.18,0.63]],             [31,[0.63,0.18,0.4]]]

        self.removeableObjects = []
        if default == "pyqt4":
            parentlayout = OpenMayaUI.MQtUtil.fullName( int(sip.unwrapinstance(self.formColorLayout)) )
        else:
            parentlayout = OpenMayaUI.MQtUtil.fullName( int(shiboken.getCppPointer(self.formColorLayout)[0]) )
        layout = cmds.gridLayout(numberOfColumns=8,cellWidthHeight=[45,25],parent=parentlayout)
        self.removeableObjects.append(layout)
        for i in self.colorList:
            if len(i) == 3:
                if self.mayaVersion < 2015:
                    button = cmds.button( l='None', bgc=tuple(i[1]),parent=layout, c=('import maya.cmds as cmds\nselection = cmds.ls(sl=True)\nfor select in selection:\n\tshapes = cmds.listRelatives(select,ad=True,s=True,f=True)\n\tfor node in shapes:\n\t\tcmds.setAttr((node+".overrideEnabled"), 0)'))
                else:
                    button = cmds.button( l='None', bgc=tuple(i[1]),parent=layout, c=('import maya.cmds as cmds\nselection = cmds.ls(sl=True)\nfor select in selection:\n\tshapes = cmds.listRelatives(select,ad=True,s=True,f=True)\n\tfor node in shapes:\n\t\tcmds.setAttr(node + ".overrideRGBColors", 0)\n\t\tcmds.setAttr((node+".overrideEnabled"), 0)'))
            else:
                if self.mayaVersion < 2015:
                    button = cmds.button( l='', bgc=tuple(i[1]),parent=layout, c=('import maya.cmds as cmds\nselection = cmds.ls(sl=True)\nfor select in selection:\n\tshapes = cmds.listRelatives(select,ad=True,s=True,f=True )\n\tfor node in shapes:\n\t\tcmds.setAttr((node+".overrideEnabled"), 1)\n\t\tcmds.setAttr((node+".overrideColor"),' + str(i[0]) + ')'))
                else:
                    button = cmds.button( l='', bgc=tuple(i[1]),parent=layout, c=('import maya.cmds as cmds\nselection = cmds.ls(sl=True)\nfor select in selection:\n\tshapes = cmds.listRelatives(select,ad=True,s=True,f=True )\n\tfor node in shapes:\n\t\tcmds.setAttr(node + ".overrideRGBColors", 0)\n\t\tcmds.setAttr((node+".overrideEnabled"), 1)\n\t\tcmds.setAttr((node+".overrideColor"),' + str(i[0]) + ')'))
            self.removeableObjects.append(button)

    def DisplayType(self, Type, *args):
        selection         = cmds.ls(sl=True)
        if len(selection) == 0:
            cmds.warning(language["warning1"])
        else:
            for Selected in selection:
                cmds.delete(Selected, ch=True)
                shapeNode = cmds.listRelatives(Selected,ad=True, s=True)
                for shapes in shapeNode:
                    cmds.setAttr((shapes + ".overrideEnabled"), 1)
                    cmds.setAttr((shapes + ".overrideDisplayType"), Type)
                    if Type == 0:
                        cmds.setAttr((shapes + ".overrideEnabled"), 0)

    def __readOutFiles(self,*args):
        parentLayout = self.presetsTreeWidget
        parentLayout.clear()

        path = FilePath+ '/Curves/'
        if platform.system() == "Windows" or platform.system() == "Linux":
            listing = os.listdir(path)
        else:
            import glob
            files = glob.glob(os.path.join(path, "*.py"))
            listing = []
            for file in files:
                listing.append(os.path.basename(file))

        for infile in listing:
            if not '.py' in infile:
                continue
            file = infile.split('.')

            f = open((path + infile), "r")
            text = f.read()

            item    = QTreeWidgetItem()
            item.setText(0, str(file[0]))
            try:
                icon = QIcon(path+file[0]+".png")
                item.setIcon(0, icon)
            except:
                pass
            parentLayout.addTopLevelItem(item)

    def __handleChanged(self):
        getItem = self.presetsTreeWidget.selectedItems()
        path = FilePath+ '/Curves/'
        if not getItem == []:
            inObject = getItem[0].text(0)
            try:
                icon = QPixmap(path+ inObject+'.png')
                self.iconButton.setPixmap(icon)
            except:
                pass

    def __doubleClicked(self):
        getItem = self.presetsTreeWidget.selectedItems()
        path = FilePath+ '/Curves/'
        if not getItem == []:
            inObject = getItem[0].text(0)

            f = open((path + inObject + '.py'), "r")
            text = f.read()
            exec (text)

    def __ButtonEnable(self):
        InputText = self.TextlineEdit.text()

        if InputText == "":
            self.CreateTextButton.setEnabled(False)
        else:
            self.CreateTextButton.setEnabled(True)

    def __createText(self, *args):
        InputText = self.TextlineEdit.text()
        FontType  = self.FontComboBox.currentText()
        if str(InputText) == "":
            cmds.error(language["warning2"])
        else:
            self.createTextController(str(InputText),str(FontType))

    def createTextController(self, inText, inFont):
        createdText = cmds.textCurves( f=inFont, t=inText )
        list = cmds.listRelatives( createdText[0], ad=True)
        list1 = []
        for i in list:
            if 'curve' in i and 'Shape' not in i:
                list1.append(i)
        for i in range(len(list1)):
            cmds.parent(list1[i],w=True)
            cmds.makeIdentity(list1[i], apply=True, t=1, r=1, s=1, n=0)
            if i == 0:
                parentGuide = list1[0]
            else:
                shape = cmds.listRelatives(list1[i], s=True)
                cmds.move(0,0,0,(list1[i]+'.scalePivot'),(list1[i]+'.rotatePivot'))
                cmds.parent(shape,parentGuide,add=True,s=True)
                cmds.delete(list1[i])
        cmds.delete(createdText[0])
        cmds.xform(list1[0], cp=True)
        worldPosition     = cmds.xform(list1[0], q=True, piv=True, ws=True)
        cmds.xform(list1[0], t=(-worldPosition[0],-worldPosition[1],-worldPosition[2]))
        cmds.makeIdentity(list1[0], apply=True, t=1, r=1, s=1, n=0)
        cmds.select(list1[0])

    def closeEvent(self, *args):
        self.parent().deleteLater()
        self.parent().close()

def StartUI():
    MayaWindowPtr = wrapinstance( int( OpenMayaUI.MQtUtil.mainWindow() ) )

    window_name         = 'Control_Creator'
    dock_control        = 'Control_Creator_Dock'

    if cmds.window( window_name, exists=True ):
        cmds.deleteUI( window_name )

    if cmds.window( window_name, exists=True ):
        cmds.deleteUI( dock_control  )

    window = Control_CreatorUI( MayaWindowPtr )
    window.setObjectName( window_name )
    main = QDockWidget( dock_control, MayaWindowPtr )
    main.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
    main.setObjectName( dock_control )
    main.setWidget(window)
    main.setFloating( True )
    main.show()
