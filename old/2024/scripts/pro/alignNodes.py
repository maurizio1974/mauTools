# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Tech\Code\alignNodes\alignNodes.ui'
#
# Created: Fri Sep 22 23:10:24 2017
#      by: pyside2-uic  running on PySide2 2.0.0~alpha0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets
import maya.OpenMayaUI as mui
import maya.cmds as mc
import maya.mel as mm
from shiboken2 import wrapInstance
import images

class alignNodesUI_DockWidget(object):
	def setupUi(self, DockWidget):
		DockWidget.setObjectName("DockWidget")
		DockWidget.resize(760, 110)
		DockWidget.setMinimumSize(QtCore.QSize(360, 90))
		DockWidget.setMaximumSize(QtCore.QSize(360, 90))
		self.alignLabel = QtWidgets.QLabel(DockWidget)
		self.alignLabel.setGeometry(QtCore.QRect(10, 10, 120, 20))
		font = QtGui.QFont()
		font.setPointSize(12)
		font.setWeight(75)
		font.setBold(True)
		self.alignLabel.setFont(font)
		self.alignLabel.setObjectName("alignLabel")
		self.horizontalAlignLeftBtn = QtWidgets.QLabel(DockWidget)
		self.horizontalAlignLeftBtn.setGeometry(QtCore.QRect(10, 40, 40, 40))
		self.horizontalAlignLeftBtn.setText("")
		self.horizontalAlignLeftBtn.setPixmap(QtGui.QPixmap(":/images/horizontalAlignLeft.png"))
		self.horizontalAlignLeftBtn.setScaledContents(True)
		self.horizontalAlignLeftBtn.setObjectName("horizontalAlignLeftBtn")
		self.horizontalAlignCenterBtn = QtWidgets.QLabel(DockWidget)
		self.horizontalAlignCenterBtn.setGeometry(QtCore.QRect(60, 40, 40, 40))
		self.horizontalAlignCenterBtn.setText("")
		self.horizontalAlignCenterBtn.setPixmap(QtGui.QPixmap(":/images/horizontalAlignCenter.png"))
		self.horizontalAlignCenterBtn.setScaledContents(True)
		self.horizontalAlignCenterBtn.setObjectName("horizontalAlignCenterBtn")
		self.horizontalAlignRightBtn = QtWidgets.QLabel(DockWidget)
		self.horizontalAlignRightBtn.setGeometry(QtCore.QRect(110, 40, 40, 40))
		self.horizontalAlignRightBtn.setText("")
		self.horizontalAlignRightBtn.setPixmap(QtGui.QPixmap(":/images/horizontalAlignRight.png"))
		self.horizontalAlignRightBtn.setScaledContents(True)
		self.horizontalAlignRightBtn.setObjectName("horizontalAlignRightBtn")
		self.verticalAlignTopBtn = QtWidgets.QLabel(DockWidget)
		self.verticalAlignTopBtn.setGeometry(QtCore.QRect(210, 40, 40, 40))
		self.verticalAlignTopBtn.setText("")
		self.verticalAlignTopBtn.setPixmap(QtGui.QPixmap(":/images/verticalAlignTop.png"))
		self.verticalAlignTopBtn.setScaledContents(True)
		self.verticalAlignTopBtn.setObjectName("verticalAlignTopBtn")
		self.verticalAlignCenterBtn = QtWidgets.QLabel(DockWidget)
		self.verticalAlignCenterBtn.setGeometry(QtCore.QRect(260, 40, 40, 40))
		self.verticalAlignCenterBtn.setText("")
		self.verticalAlignCenterBtn.setPixmap(QtGui.QPixmap(":/images/verticalAlignCenter.png"))
		self.verticalAlignCenterBtn.setScaledContents(True)
		self.verticalAlignCenterBtn.setObjectName("verticalAlignCenterBtn")
		self.verticalAlignBottomBtn = QtWidgets.QLabel(DockWidget)
		self.verticalAlignBottomBtn.setGeometry(QtCore.QRect(310, 40, 40, 40))
		self.verticalAlignBottomBtn.setText("")
		self.verticalAlignBottomBtn.setPixmap(QtGui.QPixmap(":/images/verticalAlignBottom.png"))
		self.verticalAlignBottomBtn.setScaledContents(True)
		self.verticalAlignBottomBtn.setObjectName("verticalAlignBottomBtn")

		self.retranslateUi(DockWidget)
		QtCore.QMetaObject.connectSlotsByName(DockWidget)

	def retranslateUi(self, DockWidget):
		DockWidget.setWindowTitle(QtWidgets.QApplication.translate("DockWidget", "rbAlignNodes", None, -1))
		self.alignLabel.setText(QtWidgets.QApplication.translate("DockWidget", "Align Nodes:", None, -1))
		self.horizontalAlignLeftBtn.setToolTip(QtWidgets.QApplication.translate("DockWidget", "horizontalAlignLeft", None, -1))
		self.horizontalAlignCenterBtn.setToolTip(QtWidgets.QApplication.translate("DockWidget", "horizontalAlignCenter", None, -1))
		self.horizontalAlignRightBtn.setToolTip(QtWidgets.QApplication.translate("DockWidget", "horizontalAlignRight", None, -1))
		self.verticalAlignTopBtn.setToolTip(QtWidgets.QApplication.translate("DockWidget", "verticalAlignTop", None, -1))
		self.verticalAlignCenterBtn.setToolTip(QtWidgets.QApplication.translate("DockWidget", "verticalAlignCenter", None, -1))
		self.verticalAlignBottomBtn.setToolTip(QtWidgets.QApplication.translate("DockWidget", "verticalAlignBottom", None, -1))

		self.horizontalAlignLeftBtn.mousePressEvent=self.horizontalAlignLeftFn
		self.horizontalAlignCenterBtn.mousePressEvent=self.horizontalAlignCenterFn
		self.horizontalAlignRightBtn.mousePressEvent=self.horizontalAlignRightFn
		self.verticalAlignTopBtn.mousePressEvent=self.verticalAlignTopFn
		self.verticalAlignCenterBtn.mousePressEvent=self.verticalAlignCenterFn
		self.verticalAlignBottomBtn.mousePressEvent=self.verticalAlignBottomFn

def getMayaWindow():
	ptr = mui.MQtUtil.mainWindow()
	return wrapInstance(int(ptr), QtWidgets.QMainWindow)

class alignNodesUI(QtWidgets.QWidget, alignNodesUI_DockWidget):
	def __init__(self, parent=getMayaWindow()):
		QtWidgets.QWidget.__init__(self, parent)
		self.setWindowFlags(QtCore.Qt.Dialog)
		self.setupUi(self)

	def getNodeEdUI(self):
		nodeEdPane = wrapInstance(int(mui.MQtUtil.findControl('nodeEditorPanel1NodeEditorEd')), QtWidgets.QWidget)
		nodeEdGraphViewAttr = nodeEdPane.findChild(QtWidgets.QGraphicsView)
		nodeEdSceneAttr = nodeEdGraphViewAttr.scene()
		return nodeEdGraphViewAttr, nodeEdSceneAttr

	def horizontalAlignLeftFn(self,event):
		nodeEdGraphView, nodeEdScene = self.getNodeEdUI()

		#Collect Items In Scene
		#nodeEdSceneItems = nodeEdScene.items()
		nodeEdSceneItems = nodeEdScene.selectedItems()

		nodePosList = []
		for i in nodeEdSceneItems:
			if type(i) == QtWidgets.QGraphicsItem:
				nodePosList.append([i.pos().x(), i.pos().y()])
		#Get minimum in X Axis
		minX = min([i[0] for i in nodePosList])

		for j in nodeEdSceneItems:
			if type(j) == QtWidgets.QGraphicsItem:
				j.setX(minX)

	def horizontalAlignRightFn(self,event):
		nodeEdGraphView, nodeEdScene = self.getNodeEdUI()

		#Collect Items In Scene
		nodeEdSceneItems = nodeEdScene.selectedItems()

		nodePosList = []
		for i in nodeEdSceneItems:
			if type(i) == QtWidgets.QGraphicsItem:
				nodePosList.append([i.pos().x(), i.pos().y()])
		#Get minimum in X Axis
		maxX = max([i[0] for i in nodePosList])

		for j in nodeEdSceneItems:
			if type(j) == QtWidgets.QGraphicsItem:
				j.setX(maxX)


	def horizontalAlignCenterFn(self,event):
		nodeEdGraphView, nodeEdScene = self.getNodeEdUI()

		#Collect Items In Scene
		nodeEdSceneItems = nodeEdScene.selectedItems()

		nodePosList = []
		for i in nodeEdSceneItems:
			if type(i) == QtWidgets.QGraphicsItem:
				nodePosList.append([i.pos().x(), i.pos().y()])
		#Get minimum in X Axis
		minX = min([i[0] for i in nodePosList])
		maxX = max([i[0] for i in nodePosList])

		for j in nodeEdSceneItems:
			if type(j) == QtWidgets.QGraphicsItem:
				j.setX(((minX+maxX)/2))



	def verticalAlignTopFn(self,event):
		nodeEdGraphView, nodeEdScene = self.getNodeEdUI()

		#Collect Items In Scene
		nodeEdSceneItems = nodeEdScene.selectedItems()

		nodePosList = []
		for i in nodeEdSceneItems:
			if type(i) == QtWidgets.QGraphicsItem:
				nodePosList.append([i.pos().x(), i.pos().y()])
		#Get minimum in X Axis
		minY = min([i[1] for i in nodePosList])

		for j in nodeEdSceneItems:
			if type(j) == QtWidgets.QGraphicsItem:
				j.setY(minY)

	def verticalAlignBottomFn(self,event):
		nodeEdGraphView, nodeEdScene = self.getNodeEdUI()

		#Collect Items In Scene
		nodeEdSceneItems = nodeEdScene.selectedItems()

		nodePosList = []
		for i in nodeEdSceneItems:
			if type(i) == QtWidgets.QGraphicsItem:
				nodePosList.append([i.pos().x(), i.pos().y()])
		#Get minimum in X Axis
		maxY = max([i[1] for i in nodePosList])

		for j in nodeEdSceneItems:
			if type(j) == QtWidgets.QGraphicsItem:
				j.setY(maxY)


	def verticalAlignCenterFn(self,event):
		nodeEdGraphView, nodeEdScene = self.getNodeEdUI()

		#Collect Items In Scene
		nodeEdSceneItems = nodeEdScene.selectedItems()

		nodePosList = []
		for i in nodeEdSceneItems:
			if type(i) == QtWidgets.QGraphicsItem:
				nodePosList.append([i.pos().x(), i.pos().y()])
		#Get minimum in X Axis
		minY = min([i[1] for i in nodePosList])
		maxY = max([i[1] for i in nodePosList])

		for j in nodeEdSceneItems:
			if type(j) == QtWidgets.QGraphicsItem:
				j.setY(((minY+maxY)/2))
