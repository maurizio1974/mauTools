#! /usr/bin/python

"""
    File name: tpRenamer.py
    Author: Tomas Poveda - www.cgart3d.com
    Description: Renamer Tool with multiple renaming options
"""

try:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from shiboken import wrapInstance

import os
import maya.OpenMayaUI as OpenMayaUI
import maya.cmds as cmds

class tpRenameException(Exception):

    """
    Custom exception class that will handle errors when renaming elements using tpRenamer tool
    """

    def __init__(self, nodes):

        errorText = '======= tpRenamer: Failed to rename one or more nodes ======='

        if not hasattr(nodes, '__iter__'):
            nodes = [nodes]
        for node in nodes:
            if not cmds.objExists(node):
                errorText += "\t'%s' no longer exists.\n" % node
            elif cmds.lockNode(node, q=True, l=True):
                errorText += "\t'%s' is locked.\n" % node
            else:
                errorText += "\t'%s' failure unknows.\n" % node

        Exception.__init__(self, errorText)
        
def _getMayaWindow():
    
    """
    Return the Maya main window widget as a Python object
    :return: Maya Window
    """

    ptr = OpenMayaUI.MQtUtil.mainWindow ()
    if ptr is not None:
        return wrapInstance (long (ptr), QMainWindow)
        
    # -------------------------------------------------------------------------------------------------
        
def getAlpha(value, capital=False):

    """
    Convert an integer value to a character. a-z then double, aa-zz etc.
    @param value: int, Value to get an alphabetic character from
    @param capital: boolean: True if you want to get capital character
    @return: str, Character from an integer
    """

    # Calculate number of characters required
    base_power = base_start = base_end = 0
    while value >= base_end:
        base_power += 1
        base_start = base_end
        base_end += pow(26, base_power)
    base_index = value - base_start

    # Create alpha representation
    alphas = ['a'] * base_power
    for index in range(base_power - 1, -1, -1):
        alphas[index] = chr(97 + (base_index % 26))
        base_index /= 26

    if capital: return ''.join(alphas).upper()
    return ''.join(alphas)
        
def findAvaliableName(name, suffix, index, padding, letters=False, capital=False):

    """
    Recursively find a free name matching specified criteria
    @param name: str, Name to check if already exists in the scene
    @param index: int, Index of the name
    @param padding: int, Padding for the characters/numbers
    @param letters: bool, True if we want to use letters when renaming multiple nodes
    @param capital: bool, True if we want letters to be capital
    """

    test_name = name

    if letters is True:
        letter = getAlpha(index - 1, capital)
        test_name = '%s_%s' % (name, letter)
    else:
        test_name = '%s_%s' % (name, str(index).zfill(padding + 1))

    if suffix:
        test_name = '%s_%s' % (test_name, suffix)

    # if object exists, try next index
    if cmds.objExists(test_name):
        return findAvaliableName(name, suffix, index + 1,
                                 padding, letters, capital)

    return test_name
    
def tpUndo(fn):

    """
    tpRigLib simple undo wrapper. Use @tpUndo above the function to wrap it.
    @param fn: function to wrap
    @return wrapped function
    """

    def wrapper(*args, **kwargs):
        cmds.undoInfo(openChunk=True)
        try:
            ret = fn(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)
        return ret
    return wrapper
    
    # -------------------------------------------------------------------------------------------------

class tpSplitter (QWidget, object):
    def __init__(self, text=None, shadow=True, color=(150, 150, 150)):

        """
        Basic standard splitter with optional text
        :param str text: Optional text to include as title in the splitter
        :param bool shadow: True if you want a shadow above the splitter
        :param tuple(int) color: Color of the slitter's text
        """

        super (tpSplitter, self).__init__ ()

        self.setMinimumHeight (2)
        self.setLayout (QHBoxLayout ())
        self.layout ().setContentsMargins (0, 0, 0, 0)
        self.layout ().setSpacing (0)
        self.layout ().setAlignment (Qt.AlignVCenter)

        firstLine = QFrame ()
        firstLine.setFrameStyle (QFrame.HLine)
        self.layout ().addWidget (firstLine)

        mainColor = 'rgba(%s, %s, %s, 255)' % color
        shadowColor = 'rgba(45, 45, 45, 255)'

        bottomBorder = ''
        if shadow:
            bottomBorder = 'border-bottom:1px solid %s;' % shadowColor

        styleSheet = "border:0px solid rgba(0,0,0,0); \
                      background-color: %s; \
                      max-height: 1px; \
                      %s" % (mainColor, bottomBorder)

        firstLine.setStyleSheet (styleSheet)

        if text is None:
            return

        firstLine.setMaximumWidth (5)

        font = QFont ()
        font.setBold (True)

        textWidth = QFontMetrics (font)
        width = textWidth.width (text) + 6

        label = QLabel ()
        label.setText (text)
        label.setFont (font)
        label.setMaximumWidth (width)
        label.setAlignment (Qt.AlignCenter | Qt.AlignVCenter)

        self.layout ().addWidget (label)

        secondLine = QFrame ()
        secondLine.setFrameStyle (QFrame.HLine)
        secondLine.setStyleSheet (styleSheet)

        self.layout ().addWidget (secondLine)
        
class tpSplitterLayout (QHBoxLayout, object):
    
    def __init__(self):

        """
        Basic splitter to separate layouts
        """

        super(tpSplitterLayout, self).__init__()

        self.setContentsMargins(40, 2, 40, 2)

        splitter = tpSplitter(shadow=False, color=(60, 60, 60))
        splitter.setFixedHeight(2)

        self.addWidget(splitter)
        
    # -------------------------------------------------------------------------------------------------

@tpUndo
def rename(nodes, text,
           prefix=None,
           suffix=None,
           padding=0,
           letters=False,
           capital=False,
           side='',
           lastJointIsEnd=False):

    """
    Method that renames a group of nodes
    @param nodes: list(str): Nodes to rename
    @param text: str: New base name
    @param prefix: str, Prefix for the nodes
    @param suffix: str, Suffix for the nodes
    @param padding: int, Padding for the characters/numbers
    @param letters: bool, True if we want to use letters when renaming multiple nodes
    @param capital: bool, True if we want letters to be capital
    @param side: str, Side of the node
    @param lastJointIsEnd: bool, True if the last node is an end node
    """

    if prefix:
        if side != '':
            text = '%s_%s_%s' % (prefix, side, text)
        else:
            text = '%s_%s' % (prefix, text)

    # if single node, try without letter or number
    if len(nodes) == 1:
        node = nodes[0]

        newName = text
        if suffix:
            newName += '_' + suffix

        if node == newName:
            return newName

        failedNodes = []
        if not cmds.objExists(newName):
            try:
                cmds.rename(node, newName)
            except RuntimeError:
                raise tpRenameException(node)
            return newName

    # Rename nodes to tmp
    newNodeNames = []
    failedNodes = []
    for i, node in enumerate(reversed(nodes)):
        try:
            newNodeNames.insert(0, cmds.rename(node, '__tmp__' + str(i)))
        except RuntimeError:
            failedNodes.insert(0, node)

    # Get new names
    newNodes = []
    for nodeName in newNodeNames:
        newName = findAvaliableName(text, suffix, 1, padding, letters, capital)
        if lastJointIsEnd and nodeName == newNodeNames[-1]:
            newName = newName + 'End'
        try:
            newNodes.append(cmds.rename(nodeName, newName))
        except RuntimeError:
            failedNodes.append(node)

    if failedNodes:
        raise tpRenameException(failedNodes)

    return newNodes

@tpUndo
def replace(nodes, find_text, replace_text):
    shapes = cmds.ls(nodes, s=True)
    shape_set = set(shapes)

    new_nodes_names = [];
    failed_nodes = []
    for i, node in enumerate(nodes):
        if not find_text in node: continue
        if node in shape_set:     continue

        try:
            new_nodes_names.append((node, cmds.rename(node, '__tmp__' + str(i))))
        except RuntimeError:
            failed_nodes.append(node)

    for i, shape in enumerate(shapes):
        if not find_text in shape: continue
        if not cmds.objExists(shape):
            try:
                new_name = cmds.rename(shape, shape.replace(find_text, '__tmp__' + str(i)))
                new_nodes_names.append((shape, new_name))
            except RuntimeError:
                failed_nodes.append(node)

    new_names = []
    for name, new_node in new_nodes_names:
        new_name = name.replace(find_text, replace_text)
        new_names.append(cmds.rename(new_node, new_name))

    return new_names

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

class tpRenamer(QDialog, object):
    def __init__(self):
        super(tpRenamer, self).__init__(parent=_getMayaWindow())
        
        winName = 'tpRenamerBaseDialog'
        
        # Check if this UI is already open. If it is then delete it before  creating it anew
        if cmds.window (winName, exists=True):
            cmds.deleteUI (winName, window=True)
        elif cmds.windowPref (winName, exists=True):
            cmds.windowPref (winName, remove=True)

        # Set the dialog object name, window title and size
        self.setObjectName(winName)
        self.setWindowTitle('tpRenamer')
        self.setMinimumSize(330, 590)
        self.setFixedSize(QSize(330, 590))
        
        self.customUI()
        
        self.show()

    def keyPressEvent(self, event):

        # Prevent lost focus when writing on QLineEdits
        if event.key() in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_CapsLock):
            event.accept()
        else:
            event.ignore()

    def customUI(self):
        

        self.setLayout (QVBoxLayout ())
        self.layout ().setContentsMargins (5, 5, 5, 5)
        self.layout ().setSpacing (2)
        self.layout ().setAlignment (Qt.AlignTop)

        # === Renamer Widget === #

        renamerWidget = QWidget()
        renamerWidget.setLayout(QVBoxLayout())
        renamerWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        renamerWidget.layout().setContentsMargins(0,0,0,0)
        renamerWidget.layout().setSpacing(2)

        self.layout().addWidget(renamerWidget)

        renamerSplitter = tpSplitter('RENAME')
        renamerWidget.layout().addWidget(renamerSplitter)

        renamerTextLayout = QHBoxLayout()
        renamerTextLayout.setContentsMargins(4,0,4,0)
        renamerTextLayout.setSpacing(2)

        renamerWidget.layout().addLayout(renamerTextLayout)

        renamerTextLbl = QLabel('New Name: ')
        self.renamerLine = QLineEdit()
        renamerTextLayout.addWidget(renamerTextLbl)
        renamerTextLayout.addWidget(self.renamerLine)

        regEx = QRegExp ("^(?!^_)[a-zA-Z_]+")
        textValidator = QRegExpValidator (regEx, self.renamerLine)
        self.renamerLine.setValidator (textValidator)

        renamerWidget.layout ().addLayout (tpSplitterLayout ())

        renameMultLayout = QHBoxLayout ()
        renameMultLayout.setContentsMargins (4, 0, 4, 0)
        renameMultLayout.setSpacing (2)

        renamerWidget.layout ().addLayout (renameMultLayout)

        renameMultMethodLbl = QLabel ('Multiples Naming Method: ')
        self.renamerMultMethodCombo = QComboBox ()
        self.renamerMultMethodCombo.addItem ('Numbers (0-9)')
        self.renamerMultMethodCombo.addItem ('Letters (a-z)')
        self.renamerMultMethodCombo.setFixedWidth (100)

        renameMultLayout.addWidget (renameMultMethodLbl)
        renameMultLayout.addWidget (self.renamerMultMethodCombo)

        multOptionsLayout = QHBoxLayout ()
        multOptionsLayout.setContentsMargins (4, 0, 4, 0)
        multOptionsLayout.setSpacing (2)
        renamerWidget.layout ().addLayout (multOptionsLayout)

        self.framePadLbl = QLabel ('No. Padding: ')
        self.framePadSpin = QSpinBox ()
        self.framePadSpin.setFixedWidth (40)
        self.framePadSpin.setMinimum (0)
        self.framePadSpin.setMaximum (10)

        self.lowerRadio = QRadioButton ('Lowercase')
        self.upperRadio = QRadioButton ('Uppercase')
        self.lowerRadio.setVisible (False)
        self.upperRadio.setVisible (False)
        self.lowerRadio.setFixedHeight (19)
        self.upperRadio.setFixedHeight (19)
        self.lowerRadio.setChecked (True)

        multOptionsLayout.addWidget (self.framePadLbl)
        multOptionsLayout.addWidget (self.lowerRadio)
        multOptionsLayout.addSpacerItem (QSpacerItem (5, 5, QSizePolicy.Expanding))
        multOptionsLayout.addWidget (self.framePadSpin)
        multOptionsLayout.addWidget (self.upperRadio)

        fixLayout = QHBoxLayout ()
        fixLayout.setContentsMargins (4, 0, 4, 0)
        fixLayout.setSpacing (2)

        renamerWidget.layout ().addLayout (fixLayout)

        self.prefixCheck = QCheckBox ('Prefix: ')
        self.prefixLine = QLineEdit ()
        self.prefixLine.setEnabled (False)
        self.prefixLine.setFixedWidth (85)
        self.prefixLine.setValidator (textValidator)

        self.suffixCheck = QCheckBox ('Suffix: ')
        self.suffixLine = QLineEdit ()
        self.suffixLine.setEnabled (False)
        self.suffixLine.setFixedWidth (85)
        self.suffixLine.setValidator (textValidator)

        fixLayout.addWidget (self.prefixCheck)
        fixLayout.addWidget (self.prefixLine)
        fixLayout.addSpacerItem (QSpacerItem (5, 5, QSizePolicy.Expanding))
        fixLayout.addWidget (self.suffixCheck)
        fixLayout.addWidget (self.suffixLine)

        renamerWidget.layout ().addLayout (tpSplitterLayout ())

        sideLayout = QHBoxLayout ()
        sideLayout.setContentsMargins (0, 2, 0, 0)
        sideLayout.setSpacing (2)

        sideBox = QGroupBox ()
        sideBox.setLayout (sideLayout)
        sideBox.setStyleSheet ("border:0px;")

        renamerWidget.layout ().addWidget (sideBox)

        self.sideLbl = QLabel ('Side: ')
        self.noneSide = QRadioButton ('None')
        self.rightSide = QRadioButton ('Right')
        self.centerSide = QRadioButton ('Center')
        self.midSide = QRadioButton('Mid')
        self.leftSide = QRadioButton ('Left')

        self.noneSide.setFixedHeight (15)
        self.rightSide.setFixedHeight (15)
        self.centerSide.setFixedHeight (15)
        self.midSide.setFixedHeight(15)
        self.leftSide.setFixedHeight (15)

        self.noneSide.setChecked (True)

        self.capitalSide = QCheckBox('Capital?')

        sideLayout.addWidget (self.sideLbl)
        sideLayout.addWidget (self.noneSide)
        sideLayout.addWidget (self.rightSide)
        sideLayout.addWidget (self.centerSide)
        sideLayout.addWidget(self.midSide)
        sideLayout.addWidget (self.leftSide)

        renamerWidget.layout().addWidget(self.capitalSide)

        renamerWidget.layout ().addLayout (tpSplitterLayout ())

        lastJointLayout = QVBoxLayout ()
        renamerWidget.layout ().addLayout (lastJointLayout)

        self.lastJointIsEndCbx = QCheckBox ('Last joint is an endJoint?')
        self.lastJointIsEndCbx.setChecked (True)
        lastJointLayout.addWidget (self.lastJointIsEndCbx)

        renameBtnLayout = QHBoxLayout ()
        renameBtnLayout.setContentsMargins (4, 0, 4, 0)
        renameBtnLayout.setSpacing (0)

        renamerWidget.layout ().addLayout (renameBtnLayout)

        self.renamerLbl = QLabel ('e.g. ')
        renamerBtn = QPushButton ('Rename')
        renamerBtn.setFixedHeight (20)
        renamerBtn.setFixedWidth (55)

        renameBtnLayout.addWidget (self.renamerLbl)
        renameBtnLayout.addWidget (renamerBtn)

        spacerItem = QSpacerItem (20, 20, QSizePolicy.Fixed)
        self.layout ().addSpacerItem (spacerItem)

        # ------------------------------------------------------------------------

        ### Replacer Widget ###

        replacerWidget = QWidget ()
        replacerWidget.setLayout (QVBoxLayout ())
        replacerWidget.layout ().setContentsMargins (0, 0, 0, 0)
        replacerWidget.layout ().setSpacing (2)
        replacerWidget.setSizePolicy (QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout ().addWidget (replacerWidget)

        replaceSplitter = tpSplitter ('FIND/REPLACE')
        replacerWidget.layout ().addWidget (replaceSplitter)

        replaceLbl = QLabel('Find: ')
        self.replaceLine = QLineEdit()
        withLbl = QLabel('Replace: ')
        self.withLine = QLineEdit()
        replaceLbl.setFixedWidth(55)
        withLbl.setFixedWidth(55)

        regEx = QRegExp("[a-zA-Z_0-9]+")
        textValidator = QRegExpValidator(regEx, self.replaceLine)
        self.replaceLine.setValidator(textValidator)
        self.withLine.setValidator(textValidator)

        replaceLayout = QHBoxLayout()
        replaceLayout.setContentsMargins(4, 0, 4, 0)
        replaceLayout.setSpacing(2)
        replaceLayout.addWidget(replaceLbl)
        replaceLayout.addWidget(self.replaceLine)
        withLayout = QHBoxLayout()
        withLayout.setContentsMargins(4, 0, 4, 0)
        withLayout.setSpacing(2)
        withLayout.addWidget(withLbl)
        withLayout.addWidget(self.withLine)
        replacerWidget.layout().addLayout(replaceLayout)
        replacerWidget.layout().addLayout(withLayout)

        replacerWidget.layout().addLayout(tpSplitterLayout())

        selectionLayout = QHBoxLayout()
        selectionLayout.setContentsMargins(4, 0, 4, 0)
        selectionLayout.setSpacing(2)

        replacerWidget.layout().addLayout(selectionLayout)

        selectionModeLbl = QLabel('Selection Mode: ')
        self.allRadio = QRadioButton('All')
        self.allRadio.setFixedHeight(19)
        self.selectedRadio = QRadioButton('Selected')
        self.selectedRadio.setFixedHeight(19)
        self.selectedRadio.setChecked(True)
        self.hierarchyCbx = QCheckBox('Hierarchy')
        self.hierarchyCbx.setFixedHeight(19)

        selectionLayout.addWidget(selectionModeLbl)
        spacerItem = QSpacerItem(5, 5, QSizePolicy.Expanding)
        selectionLayout.addSpacerItem(spacerItem)
        selectionLayout.addWidget(self.allRadio)
        selectionLayout.addWidget(self.selectedRadio)
        selectionLayout.addWidget(self.hierarchyCbx)

        replacerWidget.layout().addLayout(tpSplitterLayout())

        replaceBtn = QPushButton('Replace')
        replaceBtn.setFixedHeight(20)
        replaceBtn.setFixedWidth(55)

        replaceBtnLayout = QHBoxLayout()
        replaceBtnLayout.setContentsMargins(4, 0, 4, 0)
        replaceBtnLayout.setSpacing(0)
        replaceBtnLayout.setAlignment(Qt.AlignRight)
        replaceBtnLayout.addWidget(replaceBtn)

        replacerWidget.layout().addLayout(replaceBtnLayout)

        spacerItem = QSpacerItem(20, 20, QSizePolicy.Fixed)
        self.layout().addSpacerItem(spacerItem)

        ### Add Prefix Widget ###
        addPrefixWidget = QWidget()
        addPrefixWidget.setLayout(QVBoxLayout())
        addPrefixWidget.layout().setContentsMargins(0, 0, 0, 0)
        addPrefixWidget.layout().setSpacing(2)
        addPrefixWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().addWidget(addPrefixWidget)

        addPrefixSplitter = tpSplitter('ADD PREFIX')
        addPrefixWidget.layout().addWidget(addPrefixSplitter)

        addPrefixLbl = QLabel('Prefix: ')
        self.addPrefixLine = QLineEdit()
        replaceLbl.setFixedWidth(55)

        regEx = QRegExp("[a-zA-Z_]+")
        textValidator = QRegExpValidator(regEx, self.addPrefixLine)
        self.addPrefixLine.setValidator(textValidator)

        addPrefixLayout = QHBoxLayout()
        addPrefixLayout.setContentsMargins(4, 0, 4, 0)
        addPrefixLayout.setSpacing(2)
        addPrefixLayout.addWidget(addPrefixLbl)
        addPrefixLayout.addWidget(self.addPrefixLine)
        addPrefixWidget.layout().addLayout(addPrefixLayout)

        addPrefixWidget.layout().addLayout(tpSplitterLayout())

        addPrefixBtn = QPushButton('Add')
        addPrefixBtn.setFixedHeight(20)
        addPrefixBtn.setFixedWidth(55)

        addPrefixBtnLayout = QHBoxLayout()
        addPrefixBtnLayout.setContentsMargins(4, 0, 4, 0)
        addPrefixBtnLayout.setSpacing(0)
        addPrefixBtnLayout.setAlignment(Qt.AlignRight)
        addPrefixBtnLayout.addWidget(addPrefixBtn)

        addPrefixWidget.layout().addLayout(addPrefixBtnLayout)

        spacerItem = QSpacerItem(20, 20, QSizePolicy.Fixed)
        self.layout().addSpacerItem(spacerItem)

        ### Add Suffix Widget ###
        addSuffixWidget = QWidget()
        addSuffixWidget.setLayout(QVBoxLayout())
        addSuffixWidget.layout().setContentsMargins(0, 0, 0, 0)
        addSuffixWidget.layout().setSpacing(2)
        addSuffixWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().addWidget(addSuffixWidget)

        addSuffixSplitter = tpSplitter('ADD SUFFIX')
        addSuffixWidget.layout().addWidget(addSuffixSplitter)

        addSuffixLbl = QLabel('Sufix: ')
        self.addSuffixLine = QLineEdit()
        replaceLbl.setFixedWidth(55)

        regEx = QRegExp("[a-zA-Z_]+")
        textValidator = QRegExpValidator(regEx, self.addSuffixLine)
        self.addSuffixLine.setValidator(textValidator)

        addSuffixLayout = QHBoxLayout()
        addSuffixLayout.setContentsMargins(4, 0, 4, 0)
        addSuffixLayout.setSpacing(2)
        addSuffixLayout.addWidget(addSuffixLbl)
        addSuffixLayout.addWidget(self.addSuffixLine)
        addSuffixWidget.layout().addLayout(addSuffixLayout)

        addSuffixWidget.layout().addLayout(tpSplitterLayout())

        addSuffixBtn = QPushButton('Add')
        addSuffixBtn.setFixedHeight(20)
        addSuffixBtn.setFixedWidth(55)

        addSuffixBtnLayout = QHBoxLayout()
        addSuffixBtnLayout.setContentsMargins(4, 0, 4, 0)
        addSuffixBtnLayout.setSpacing(0)
        addSuffixBtnLayout.setAlignment(Qt.AlignRight)
        addSuffixBtnLayout.addWidget(addSuffixBtn)

        addSuffixWidget.layout().addLayout(addSuffixBtnLayout)

        spacerItem = QSpacerItem(20, 20, QSizePolicy.Fixed)
        self.layout().addSpacerItem(spacerItem)

        ### Extra Layout ###

        extraLayout = QHBoxLayout()
        extraLayout.setContentsMargins(10, 10, 10, 10)
        self.layout().addLayout(extraLayout)

        selectHierarchyBtn = QPushButton('Select Hierarchy')
        extraLayout.addWidget(selectHierarchyBtn)

        # ------------------------------------------------------------------------

        # === SIGNALS === #

        self.prefixCheck.stateChanged.connect(self.prefixLine.setEnabled)
        self.suffixCheck.stateChanged.connect(self.suffixLine.setEnabled)
        self.prefixCheck.stateChanged.connect(self._updateExampleRename)
        self.suffixCheck.stateChanged.connect(self._updateExampleRename)

        self.renamerMultMethodCombo.currentIndexChanged.connect(self._toggleMultNamingMethod)

        self.lowerRadio.clicked.connect(self._updateExampleRename)
        self.upperRadio.clicked.connect(self._updateExampleRename)
        self.framePadSpin.valueChanged.connect(self._updateExampleRename)

        self.noneSide.toggled.connect (self._updateExampleRename)
        self.rightSide.toggled.connect (self._updateExampleRename)
        self.centerSide.toggled.connect (self._updateExampleRename)
        self.midSide.toggled.connect(self._updateExampleRename)
        self.leftSide.toggled.connect (self._updateExampleRename)
        self.capitalSide.toggled.connect(self._updateExampleRename)

        self.renamerLine.textChanged.connect(self._updateExampleRename)
        self.prefixLine.textChanged.connect (self._updateExampleRename)
        self.suffixLine.textChanged.connect (self._updateExampleRename)

        renamerBtn.clicked.connect(self.renameNodes)

        # ---------------------------------------

        self.selectedRadio.toggled.connect(self._updateHierarchyCbx)
        self.allRadio.toggled.connect(self._updateHierarchyCbx)

        replaceBtn.clicked.connect(self.replaceNodes)

        # ---------------------------------------

        addPrefixBtn.clicked.connect(self.addPrefix)

        addSuffixBtn.clicked.connect(self.addSuffix)

        selectHierarchyBtn.clicked.connect(self.selectHierarchy)

        # ---------------------------------------

        self._updateExampleRename()

    def _getRenameSettings(self):

        text = str (self.renamerLine.text ()).strip ()

        namingMethod = bool (self.renamerMultMethodCombo.currentIndex ())
        padding = 0
        upper = True

        if namingMethod == 0:
            padding = self.framePadSpin.value ()
        else:
            upper = self.upperRadio.isChecked ()

        prefix = ''
        suffix = ''

        if self.prefixCheck.isChecked ():
            prefix = self.prefixLine.text ()
        if self.suffixCheck.isChecked ():
            suffix = self.suffixLine.text ()

        if self.noneSide.isChecked ():
            side = ''
        if self.rightSide.isChecked ():
            if self.capitalSide.isChecked(): side = 'R'
            else: side = 'r'
        if self.centerSide.isChecked ():
            if self.capitalSide.isChecked(): side = 'C'
            else: side = 'c'
        if self.midSide.isChecked():
            if self.capitalSide.isChecked(): side = 'M'
            else: side = 'm'
        if self.leftSide.isChecked ():
            if self.capitalSide.isChecked(): side = 'L'
            else: side = 'l'

        jointEnd = self.lastJointIsEndCbx.isChecked ()

        return text, prefix, suffix, padding, namingMethod, upper, side, jointEnd

    def _updateExampleRename(self):
        
        """
        Method that updates the example line edit
        """

        exampleText = ''

        text, prefix, suffix, padding, namingMethod, upper, side, jointEnd = self._getRenameSettings ()

        if not text:
            self.renamerLbl.setText ('<font color=#646464>e.g.</font>')
            return

        if prefix:
            exampleText += '%s_' % prefix

        if side != '':
            exampleText += '%s_' % side

        exampleText += '%s_' % text

        if namingMethod:
            if upper:
                exampleText += 'A'
            else:
                exampleText += 'a'
        else:
            exampleText += (padding * '0') + '1'

        if suffix:
            exampleText += '_%s' % suffix

        self.renamerLbl.setText ('<font color=#646464>e.g. \'%s\'</font>' % exampleText)

    def _toggleMultNamingMethod(self, index):

        """
        Method that updates the status of the radio buttons considering which option es enabled
        """

        self.lowerRadio.setVisible (index)
        self.upperRadio.setVisible (index)
        self.framePadLbl.setVisible (not (index))
        self.framePadSpin.setVisible (not (index))

        self._updateExampleRename ()

    def renameNodes(self):

        """
        Method that renames selected nodes
        """

        rename (cmds.ls (sl=True), *self._getRenameSettings ())

    # -------------------------------------------------------------------------------------------------

    def _updateHierarchyCbx(self):
        if self.allRadio.isChecked():
            self.hierarchyCbx.setEnabled(False)
        else:
            self.hierarchyCbx.setEnabled(True)

    def replaceNodes(self):

        """
        Method that replace node names
        """

        replaceText = str(self.replaceLine.text())
        withText = str(self.withLine.text())

        if self.allRadio.isChecked():
            nodes = cmds.ls()
            replaceNodes = replace(nodes, replaceText, withText)
        else:
            nodes = cmds.ls(sl=True)

            if self.hierarchyCbx.isChecked() and self.hierarchyCbx.isEnabled():
                newNodes = []
                replaceNodes = []

                # First, replace the hierarchy elements of the selected objects
                for node in nodes:
                    cmds.select(node)
                    cmds.select(hi=True)
                    childs = cmds.ls(sl=True, type='transform')
                    if node in childs:
                        childs.remove(node)
                    for child in childs:
                        newNodes.append(child)
                    returnNodes = replace(newNodes, replaceText, withText)
                    for n in returnNodes:
                        replaceNodes.append(n)

                # Finally we replace the names of the selected nodes
                returnNodes = replace(nodes, replaceText, withText)
                for n in returnNodes:
                    replaceNodes.append(n)
            else:
                replaceNodes = replace(nodes, replaceText, withText)

        try:
            if len(replaceNodes) > 0:
                cmds.select(replaceNodes)
                print 'Sucesfully renamed ' + str(len(replaceNodes)) + ' node(s)!'
        except:
            cmds.select(clear=True)

    # -------------------------------------------------------------------------------------------------

    @tpUndo
    def addPrefix(self):

        """
        Method that adds a prefix to selected nodes
        """

        sel = cmds.ls(sl=True)
        prefix = str(self.addPrefixLine.text())
        if len(sel) > 0:
            if prefix == '':
                pass
            else:
                for obj in sel:
                    newName = '%s_%s' % (prefix, obj)
                    cmds.rename(obj, newName)
                    print 'Sucesfully renamed ' + str(len(sel)) + ' node(s)!'

    # -------------------------------------------------------------------------------------------------

    @tpUndo
    def addSuffix(self):

        """
        Method that adds a suffix to selected nodes
        """

        sel = cmds.ls(selection=True)
        suffix = str(self.addSuffixLine.text())

        if len(sel) <= 0:
            cmds.warning('tpRenamer: You have to select at least one object')
        elif suffix == '':
            pass
        else:
            for obj in sel:
                newName = "%s_%s" % (obj, suffix)
                cmds.rename(obj, newName)
                print 'Sucesfully renamed ' + str(len(sel)) + ' node(s)!'

    # -------------------------------------------------------------------------------------------------

    def selectHierarchy(self):

        """
        Method that selects the hierachy of the selected nodes
        """

        sel = cmds.ls(selection=True)

        for obj in sel:
            cmds.select(obj, hi=True, add=True)

    # -------------------------------------------------------------------------------------------------
        
def initUI():
    tpRenamer()
    
initUI()