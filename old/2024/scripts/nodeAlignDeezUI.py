from Qt import QtCore, QtGui, QtWidgets
import shiboken2 as shiboken
import maya.OpenMayaUI as mui
import nodeAlignDeez
import importlib
importlib.reload(nodeAlignDeez)


from Qt import __binding__

if __binding__ in ('PySide2', 'PyQt5'):
    print('Qt5 binding available')
elif __binding__ in ('PySide', 'PyQt4'):
    print('Qt4 binding available.')
else:
    print('No Qt binding available.')


def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    return shiboken.wrapInstance(int(ptr), QtWidgets.QMainWindow)


def run():
    global _nodeAlignDeezUI
    try:
        _nodeAlignDeezUI.close()
        _nodeAlignDeezUI.deleteLater()
    except:
        pass

    _nodeAlignDeezUI = NodeAlignDeezUI()
    _nodeAlignDeezUI.show()


style = '\n\t\tQPushButton{\n\t\t\tbackground-color: rgb(90, 90, 90);\n\t\t\tborder-style: solid;\n\t\t\tborder-width:0px;\n\t\t\tborder-color: rgb(60, 60, 60);\n\t\t\tborder-radius:5px;\n\t\t\tcolor: rgb(200, 200, 200);\n\t\t\tfont: 7pt "Tahoma";\n\t\t}\n\n\t\tQPushButton:pressed{\n\t\t\tbackground-color: rgb(80, 80, 80);\n\t\t}\n\n\t\tQSlider:groove{\n\t\t\tbackground-color: rgb(140, 46, 69);\n\t\t\tborder-radius:5px;\n\t\t}\n\n\t\tQSlider:handle:horizontal{\n\t\t\twidth: 3px;\n\t\t\tbackground-color: rgb(200, 66, 100);\n\t\t}\n\n\t\tQSlider:sub-page:horizontal{\t\t\n\t\t\tbackground-color: rgb(140, 46, 69);\n\t\t\tborder-top-left-radius:5px;\n\t\t\tborder-bottom-left-radius:5px;\n\t\t}\n\n\t\tQSlider:add-page:horizontal{\t\t\n\t\t\tborder-top-right-radius:5px;\n\t\t\tborder-bottom-right-radius:5px;\n\t\t\tbackground-color: rgb(100, 33, 49);\n\t\t}\n\t\t'

class NodeAlignDeezUI(QtWidgets.QMainWindow):

    def __init__(self, parent=getMayaWindow()):
        super(NodeAlignDeezUI, self).__init__(parent)
        self.initWidgets()
        self.initConnections()
        self.initStyle()
        self.alignDeez = nodeAlignDeez.NodeAlignDeez()

    def initStyle(self):
        self.setWindowTitle('AlignDeez')
        self.setMinimumSize(165, 190)
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowStaysOnTopHint)
        self.setStyleSheet(style)
        self.resize(self.sizeHint())

    def _reset(self):
        self.alignDeez.itemsToScale = []

    def initWidgets(self):
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)
        self._initAlignWidgets(layout)
        self._initDistributeWidgets(layout)
        self._initStackWidgets(layout)
        self._initCenterWidgets(layout)
        self._initScaleSlider(layout)
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def _initAlignWidgets(self, layout):
        lay = QtWidgets.QHBoxLayout()
        lay.setSpacing(2)
        self.uiAlignXBTN = QtWidgets.QPushButton()
        self.uiAlignXBTN.setText('Align\nX')
        self.uiAlignXBTN.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        lay.addWidget(self.uiAlignXBTN)
        self.uiAlignYBTN = QtWidgets.QPushButton()
        self.uiAlignYBTN.setText('Align\nY')
        self.uiAlignYBTN.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        lay.addWidget(self.uiAlignYBTN)
        layout.addItem(lay)

    def _initDistributeWidgets(self, layout):
        lay = QtWidgets.QHBoxLayout()
        lay.setSpacing(2)
        self.uiDistributeXBTN = QtWidgets.QPushButton()
        self.uiDistributeXBTN.setText('Distribute\nX')
        self.uiDistributeXBTN.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        lay.addWidget(self.uiDistributeXBTN)
        self.uiDistributeYBTN = QtWidgets.QPushButton()
        self.uiDistributeYBTN.setText('Distribute\nY')
        self.uiDistributeYBTN.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        lay.addWidget(self.uiDistributeYBTN)
        layout.addItem(lay)

    def _initStackWidgets(self, layout):
        lay = QtWidgets.QHBoxLayout()
        lay.setSpacing(2)
        self.uiStackXBTN = QtWidgets.QPushButton()
        self.uiStackXBTN.setText('Stack\nX')
        self.uiStackXBTN.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        lay.addWidget(self.uiStackXBTN)
        self.uiStackYBTN = QtWidgets.QPushButton()
        self.uiStackYBTN.setText('Stack\nY')
        self.uiStackYBTN.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        lay.addWidget(self.uiStackYBTN)
        layout.addItem(lay)

    def _initCenterWidgets(self, layout):
        lay = QtWidgets.QHBoxLayout()
        lay.setSpacing(2)
        self.uiCenterXBTN = QtWidgets.QPushButton()
        self.uiCenterXBTN.setText('Center\nX')
        self.uiCenterXBTN.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        lay.addWidget(self.uiCenterXBTN)
        self.uiCenterBTN = QtWidgets.QPushButton()
        self.uiCenterBTN.setText('Center')
        self.uiCenterBTN.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        lay.addWidget(self.uiCenterBTN)
        self.uiCenterYBTN = QtWidgets.QPushButton()
        self.uiCenterYBTN.setText('Center\nY')
        self.uiCenterYBTN.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        lay.addWidget(self.uiCenterYBTN)
        layout.addItem(lay)

    def _initScaleSlider(self, layout):
        self.uiScaleSLDR = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.uiScaleSLDR.setMinimumHeight(30)
        self.uiScaleSLDR.setMinimum(-100)
        self.uiScaleSLDR.setMaximum(100)
        self.uiScaleSLDR.setValue(0)
        layout.addWidget(self.uiScaleSLDR)

    def initConnections(self):
        self.uiAlignXBTN.clicked.connect(lambda: self.alignDeez.alignPosX())
        self.uiAlignYBTN.clicked.connect(lambda: self.alignDeez.alignPosY())
        self.uiDistributeXBTN.clicked.connect(
            lambda: self.alignDeez.distributePosX())
        self.uiDistributeYBTN.clicked.connect(
            lambda: self.alignDeez.distributePosY())
        self.uiStackXBTN.clicked.connect(lambda: self.alignDeez.stackPosX())
        self.uiStackYBTN.clicked.connect(lambda: self.alignDeez.stackPosY())
        self.uiCenterXBTN.clicked.connect(lambda: self.alignDeez.centerPosX())
        self.uiCenterBTN.clicked.connect(lambda: self.alignDeez.centerPos())
        self.uiCenterYBTN.clicked.connect(lambda: self.alignDeez.centerPosY())
        self.uiScaleSLDR.sliderPressed.connect(
            lambda: self.alignDeez.setItemsToBeScaled())
        self.uiScaleSLDR.sliderMoved.connect(
            lambda: self.alignDeez.scaleSetItems(self.uiScaleSLDR.value() * 0.01))
        self.uiScaleSLDR.sliderReleased.connect(
            lambda: self.uiScaleSLDR.setValue(0))
        self.uiScaleSLDR.sliderReleased.connect(self._reset)
