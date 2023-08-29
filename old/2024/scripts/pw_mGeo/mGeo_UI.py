# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Dropbox\Dropbox\pw_prefs\RnD\maya\pythonscripts\Export\pw_mGeo\mGeo.ui'
#
# Created: Mon Aug 12 14:31:23 2013
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_mgeoWindow(object):
    def setupUi(self, mgeoWindow):
        mgeoWindow.setObjectName(_fromUtf8("mgeoWindow"))
        mgeoWindow.resize(619, 794)
        self.centralwidget = QtGui.QWidget(mgeoWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout_22 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_22.setObjectName(_fromUtf8("verticalLayout_22"))
        self.gridLayout_8 = QtGui.QGridLayout()
        self.gridLayout_8.setObjectName(_fromUtf8("gridLayout_8"))
        self.optionsWidget_wd = QtGui.QWidget(self.centralwidget)
        self.optionsWidget_wd.setObjectName(_fromUtf8("optionsWidget_wd"))
        self.verticalLayout_10 = QtGui.QVBoxLayout(self.optionsWidget_wd)
        self.verticalLayout_10.setSpacing(3)
        self.verticalLayout_10.setContentsMargins(3, 3, 3, 0)
        self.verticalLayout_10.setObjectName(_fromUtf8("verticalLayout_10"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.groupBox_2 = QtGui.QGroupBox(self.optionsWidget_wd)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.gridLayout_9 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_9.setSpacing(3)
        self.gridLayout_9.setContentsMargins(9, 3, 5, 3)
        self.gridLayout_9.setObjectName(_fromUtf8("gridLayout_9"))
        self.label_6 = QtGui.QLabel(self.groupBox_2)
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout_9.addWidget(self.label_6, 2, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBox_2)
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout_9.addWidget(self.label_2, 0, 0, 1, 1)
        self.widget = QtGui.QWidget(self.groupBox_2)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout_3.setSpacing(5)
        self.horizontalLayout_3.setMargin(1)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.formatGeo_rb = QtGui.QRadioButton(self.widget)
        self.formatGeo_rb.setMinimumSize(QtCore.QSize(71, 0))
        self.formatGeo_rb.setChecked(True)
        self.formatGeo_rb.setObjectName(_fromUtf8("formatGeo_rb"))
        self.horizontalLayout_3.addWidget(self.formatGeo_rb)
        self.formatBgeo_rb = QtGui.QRadioButton(self.widget)
        self.formatBgeo_rb.setObjectName(_fromUtf8("formatBgeo_rb"))
        self.horizontalLayout_3.addWidget(self.formatBgeo_rb)
        self.gridLayout_9.addWidget(self.widget, 0, 2, 1, 1)
        self.formatGzip_cb = QtGui.QCheckBox(self.groupBox_2)
        self.formatGzip_cb.setObjectName(_fromUtf8("formatGzip_cb"))
        self.gridLayout_9.addWidget(self.formatGzip_cb, 0, 3, 1, 1)
        self.widget_2 = QtGui.QWidget(self.groupBox_2)
        self.widget_2.setObjectName(_fromUtf8("widget_2"))
        self.horizontalLayout_8 = QtGui.QHBoxLayout(self.widget_2)
        self.horizontalLayout_8.setSpacing(6)
        self.horizontalLayout_8.setMargin(1)
        self.horizontalLayout_8.setObjectName(_fromUtf8("horizontalLayout_8"))
        self.sequence_rb = QtGui.QRadioButton(self.widget_2)
        self.sequence_rb.setChecked(True)
        self.sequence_rb.setObjectName(_fromUtf8("sequence_rb"))
        self.horizontalLayout_8.addWidget(self.sequence_rb)
        self.mdd_rb = QtGui.QRadioButton(self.widget_2)
        self.mdd_rb.setObjectName(_fromUtf8("mdd_rb"))
        self.horizontalLayout_8.addWidget(self.mdd_rb)
        self.gridLayout_9.addWidget(self.widget_2, 2, 2, 1, 1)
        self.line = QtGui.QFrame(self.groupBox_2)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.gridLayout_9.addWidget(self.line, 1, 0, 1, 4)
        self.writeFile_cb = QtGui.QCheckBox(self.groupBox_2)
        self.writeFile_cb.setChecked(True)
        self.writeFile_cb.setObjectName(_fromUtf8("writeFile_cb"))
        self.gridLayout_9.addWidget(self.writeFile_cb, 2, 3, 1, 1)
        self.horizontalLayout_2.addWidget(self.groupBox_2)
        self.verticalLayout_10.addLayout(self.horizontalLayout_2)
        self.gridLayout_8.addWidget(self.optionsWidget_wd, 0, 0, 1, 1)
        self.outFile_gb = QtGui.QGroupBox(self.centralwidget)
        self.outFile_gb.setObjectName(_fromUtf8("outFile_gb"))
        self.verticalLayout_12 = QtGui.QVBoxLayout(self.outFile_gb)
        self.verticalLayout_12.setSpacing(1)
        self.verticalLayout_12.setMargin(1)
        self.verticalLayout_12.setObjectName(_fromUtf8("verticalLayout_12"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setSpacing(1)
        self.horizontalLayout_5.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.exportPath_le = QtGui.QLineEdit(self.outFile_gb)
        self.exportPath_le.setText(_fromUtf8(""))
        self.exportPath_le.setObjectName(_fromUtf8("exportPath_le"))
        self.horizontalLayout_5.addWidget(self.exportPath_le)
        self.applets_btn = QtGui.QPushButton(self.outFile_gb)
        self.applets_btn.setMaximumSize(QtCore.QSize(20, 16777215))
        self.applets_btn.setObjectName(_fromUtf8("applets_btn"))
        self.horizontalLayout_5.addWidget(self.applets_btn)
        self.verticalLayout_12.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_19 = QtGui.QHBoxLayout()
        self.horizontalLayout_19.setObjectName(_fromUtf8("horizontalLayout_19"))
        self.fileAsk_rb = QtGui.QRadioButton(self.outFile_gb)
        self.fileAsk_rb.setChecked(True)
        self.fileAsk_rb.setObjectName(_fromUtf8("fileAsk_rb"))
        self.horizontalLayout_19.addWidget(self.fileAsk_rb)
        self.fileOverride_rb = QtGui.QRadioButton(self.outFile_gb)
        self.fileOverride_rb.setChecked(False)
        self.fileOverride_rb.setObjectName(_fromUtf8("fileOverride_rb"))
        self.horizontalLayout_19.addWidget(self.fileOverride_rb)
        self.fileSkip_rb = QtGui.QRadioButton(self.outFile_gb)
        self.fileSkip_rb.setObjectName(_fromUtf8("fileSkip_rb"))
        self.horizontalLayout_19.addWidget(self.fileSkip_rb)
        self.fileRename_rb = QtGui.QRadioButton(self.outFile_gb)
        self.fileRename_rb.setObjectName(_fromUtf8("fileRename_rb"))
        self.horizontalLayout_19.addWidget(self.fileRename_rb)
        self.horizontalLayout_19.setStretch(3, 1)
        self.verticalLayout_12.addLayout(self.horizontalLayout_19)
        self.gridLayout_8.addWidget(self.outFile_gb, 1, 0, 1, 2)
        self.frameRangeSettings_gb = QtGui.QGroupBox(self.centralwidget)
        self.frameRangeSettings_gb.setObjectName(_fromUtf8("frameRangeSettings_gb"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.frameRangeSettings_gb)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setContentsMargins(5, 2, 2, 2)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.widget_3 = QtGui.QWidget(self.frameRangeSettings_gb)
        self.widget_3.setObjectName(_fromUtf8("widget_3"))
        self.horizontalLayout_15 = QtGui.QHBoxLayout(self.widget_3)
        self.horizontalLayout_15.setSpacing(2)
        self.horizontalLayout_15.setMargin(2)
        self.horizontalLayout_15.setObjectName(_fromUtf8("horizontalLayout_15"))
        self.singleFrame_rb = QtGui.QRadioButton(self.widget_3)
        self.singleFrame_rb.setChecked(True)
        self.singleFrame_rb.setObjectName(_fromUtf8("singleFrame_rb"))
        self.horizontalLayout_15.addWidget(self.singleFrame_rb)
        self.rangeFrame_rb = QtGui.QRadioButton(self.widget_3)
        self.rangeFrame_rb.setObjectName(_fromUtf8("rangeFrame_rb"))
        self.horizontalLayout_15.addWidget(self.rangeFrame_rb)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_15.addItem(spacerItem)
        self.verticalLayout_2.addWidget(self.widget_3)
        self.range_wd = QtGui.QWidget(self.frameRangeSettings_gb)
        self.range_wd.setEnabled(False)
        self.range_wd.setObjectName(_fromUtf8("range_wd"))
        self.verticalLayout_21 = QtGui.QVBoxLayout(self.range_wd)
        self.verticalLayout_21.setSpacing(2)
        self.verticalLayout_21.setMargin(2)
        self.verticalLayout_21.setObjectName(_fromUtf8("verticalLayout_21"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setContentsMargins(0, -1, 5, -1)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.startFrame_le = QtGui.QLineEdit(self.range_wd)
        self.startFrame_le.setMaximumSize(QtCore.QSize(11111111, 16777215))
        self.startFrame_le.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.startFrame_le.setText(_fromUtf8(""))
        self.startFrame_le.setObjectName(_fromUtf8("startFrame_le"))
        self.horizontalLayout.addWidget(self.startFrame_le)
        self.endFrame_le = QtGui.QLineEdit(self.range_wd)
        self.endFrame_le.setMaximumSize(QtCore.QSize(1111111, 16777215))
        self.endFrame_le.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.endFrame_le.setText(_fromUtf8(""))
        self.endFrame_le.setObjectName(_fromUtf8("endFrame_le"))
        self.horizontalLayout.addWidget(self.endFrame_le)
        self.stepFrame_le = QtGui.QLineEdit(self.range_wd)
        self.stepFrame_le.setMaximumSize(QtCore.QSize(30, 16777215))
        self.stepFrame_le.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.stepFrame_le.setText(_fromUtf8(""))
        self.stepFrame_le.setObjectName(_fromUtf8("stepFrame_le"))
        self.horizontalLayout.addWidget(self.stepFrame_le)
        self.setrange_btn = QtGui.QPushButton(self.range_wd)
        self.setrange_btn.setMinimumSize(QtCore.QSize(30, 0))
        self.setrange_btn.setMaximumSize(QtCore.QSize(111, 16777215))
        self.setrange_btn.setObjectName(_fromUtf8("setrange_btn"))
        self.horizontalLayout.addWidget(self.setrange_btn)
        self.verticalLayout_21.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addWidget(self.range_wd)
        self.gridLayout_8.addWidget(self.frameRangeSettings_gb, 0, 1, 1, 1)
        self.verticalLayout_22.addLayout(self.gridLayout_8)
        self.textWidget_sp = QtGui.QSplitter(self.centralwidget)
        self.textWidget_sp.setOrientation(QtCore.Qt.Vertical)
        self.textWidget_sp.setObjectName(_fromUtf8("textWidget_sp"))
        self.splitter = QtGui.QSplitter(self.textWidget_sp)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.groupBox_5 = QtGui.QGroupBox(self.splitter)
        self.groupBox_5.setObjectName(_fromUtf8("groupBox_5"))
        self.verticalLayout_23 = QtGui.QVBoxLayout(self.groupBox_5)
        self.verticalLayout_23.setSpacing(2)
        self.verticalLayout_23.setMargin(2)
        self.verticalLayout_23.setObjectName(_fromUtf8("verticalLayout_23"))
        self.horizontalLayout_18 = QtGui.QHBoxLayout()
        self.horizontalLayout_18.setObjectName(_fromUtf8("horizontalLayout_18"))
        self.createSet_btn = QtGui.QPushButton(self.groupBox_5)
        self.createSet_btn.setMinimumSize(QtCore.QSize(30, 30))
        self.createSet_btn.setMaximumSize(QtCore.QSize(30, 30))
        self.createSet_btn.setFlat(True)
        self.createSet_btn.setObjectName(_fromUtf8("createSet_btn"))
        self.horizontalLayout_18.addWidget(self.createSet_btn)
        self.deleteSet_btn = QtGui.QPushButton(self.groupBox_5)
        self.deleteSet_btn.setMinimumSize(QtCore.QSize(30, 30))
        self.deleteSet_btn.setMaximumSize(QtCore.QSize(30, 30))
        self.deleteSet_btn.setFlat(True)
        self.deleteSet_btn.setObjectName(_fromUtf8("deleteSet_btn"))
        self.horizontalLayout_18.addWidget(self.deleteSet_btn)
        self.reloadSets_btn = QtGui.QPushButton(self.groupBox_5)
        self.reloadSets_btn.setMinimumSize(QtCore.QSize(30, 30))
        self.reloadSets_btn.setMaximumSize(QtCore.QSize(30, 30))
        self.reloadSets_btn.setFlat(True)
        self.reloadSets_btn.setObjectName(_fromUtf8("reloadSets_btn"))
        self.horizontalLayout_18.addWidget(self.reloadSets_btn)
        self.line_3 = QtGui.QFrame(self.groupBox_5)
        self.line_3.setFrameShape(QtGui.QFrame.VLine)
        self.line_3.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_3.setObjectName(_fromUtf8("line_3"))
        self.horizontalLayout_18.addWidget(self.line_3)
        self.addToSet_btn = QtGui.QPushButton(self.groupBox_5)
        self.addToSet_btn.setMinimumSize(QtCore.QSize(30, 30))
        self.addToSet_btn.setMaximumSize(QtCore.QSize(30, 30))
        self.addToSet_btn.setFlat(True)
        self.addToSet_btn.setObjectName(_fromUtf8("addToSet_btn"))
        self.horizontalLayout_18.addWidget(self.addToSet_btn)
        self.removeFromSet_btn = QtGui.QPushButton(self.groupBox_5)
        self.removeFromSet_btn.setMinimumSize(QtCore.QSize(30, 30))
        self.removeFromSet_btn.setMaximumSize(QtCore.QSize(30, 30))
        self.removeFromSet_btn.setFlat(True)
        self.removeFromSet_btn.setObjectName(_fromUtf8("removeFromSet_btn"))
        self.horizontalLayout_18.addWidget(self.removeFromSet_btn)
        self.replaceSet_btn = QtGui.QPushButton(self.groupBox_5)
        self.replaceSet_btn.setMinimumSize(QtCore.QSize(30, 30))
        self.replaceSet_btn.setMaximumSize(QtCore.QSize(30, 30))
        self.replaceSet_btn.setFlat(True)
        self.replaceSet_btn.setObjectName(_fromUtf8("replaceSet_btn"))
        self.horizontalLayout_18.addWidget(self.replaceSet_btn)
        self.clearSet_btn = QtGui.QPushButton(self.groupBox_5)
        self.clearSet_btn.setMinimumSize(QtCore.QSize(30, 30))
        self.clearSet_btn.setMaximumSize(QtCore.QSize(30, 30))
        self.clearSet_btn.setFlat(True)
        self.clearSet_btn.setObjectName(_fromUtf8("clearSet_btn"))
        self.horizontalLayout_18.addWidget(self.clearSet_btn)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_18.addItem(spacerItem1)
        self.verticalLayout_23.addLayout(self.horizontalLayout_18)
        self.scrollArea_5 = QtGui.QScrollArea(self.groupBox_5)
        self.scrollArea_5.setWidgetResizable(True)
        self.scrollArea_5.setObjectName(_fromUtf8("scrollArea_5"))
        self.scrollAreaWidgetContents_5 = QtGui.QWidget()
        self.scrollAreaWidgetContents_5.setGeometry(QtCore.QRect(0, 0, 261, 306))
        self.scrollAreaWidgetContents_5.setObjectName(_fromUtf8("scrollAreaWidgetContents_5"))
        self.verticalLayout_8 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents_5)
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setMargin(0)
        self.verticalLayout_8.setObjectName(_fromUtf8("verticalLayout_8"))
        self.sets_ly = QtGui.QVBoxLayout()
        self.sets_ly.setSpacing(0)
        self.sets_ly.setObjectName(_fromUtf8("sets_ly"))
        self.verticalLayout_8.addLayout(self.sets_ly)
        self.scrollArea_5.setWidget(self.scrollAreaWidgetContents_5)
        self.verticalLayout_23.addWidget(self.scrollArea_5)
        self.geoExport_btn = QtGui.QPushButton(self.groupBox_5)
        self.geoExport_btn.setMinimumSize(QtCore.QSize(100, 0))
        self.geoExport_btn.setObjectName(_fromUtf8("geoExport_btn"))
        self.verticalLayout_23.addWidget(self.geoExport_btn)
        self.expoptions_gb = QtGui.QGroupBox(self.splitter)
        self.expoptions_gb.setObjectName(_fromUtf8("expoptions_gb"))
        self.verticalLayout = QtGui.QVBoxLayout(self.expoptions_gb)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout_10 = QtGui.QGridLayout()
        self.gridLayout_10.setObjectName(_fromUtf8("gridLayout_10"))
        self.horizontalLayout_12 = QtGui.QHBoxLayout()
        self.horizontalLayout_12.setObjectName(_fromUtf8("horizontalLayout_12"))
        self.label = QtGui.QLabel(self.expoptions_gb)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_12.addWidget(self.label)
        self.widget_4 = QtGui.QWidget(self.expoptions_gb)
        self.widget_4.setMinimumSize(QtCore.QSize(50, 0))
        self.widget_4.setObjectName(_fromUtf8("widget_4"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.widget_4)
        self.horizontalLayout_4.setSpacing(10)
        self.horizontalLayout_4.setMargin(2)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.worldPos_rb = QtGui.QRadioButton(self.widget_4)
        self.worldPos_rb.setChecked(True)
        self.worldPos_rb.setObjectName(_fromUtf8("worldPos_rb"))
        self.horizontalLayout_4.addWidget(self.worldPos_rb)
        self.localPos_rb = QtGui.QRadioButton(self.widget_4)
        self.localPos_rb.setObjectName(_fromUtf8("localPos_rb"))
        self.horizontalLayout_4.addWidget(self.localPos_rb)
        self.horizontalLayout_12.addWidget(self.widget_4)
        self.gridLayout_10.addLayout(self.horizontalLayout_12, 0, 0, 1, 1)
        self.expVis_cb = QtGui.QCheckBox(self.expoptions_gb)
        self.expVis_cb.setObjectName(_fromUtf8("expVis_cb"))
        self.gridLayout_10.addWidget(self.expVis_cb, 0, 2, 1, 1)
        self.horizontalLayout_9 = QtGui.QHBoxLayout()
        self.horizontalLayout_9.setObjectName(_fromUtf8("horizontalLayout_9"))
        self.label_8 = QtGui.QLabel(self.expoptions_gb)
        self.label_8.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_8.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.horizontalLayout_9.addWidget(self.label_8)
        self.scale_le = QtGui.QLineEdit(self.expoptions_gb)
        self.scale_le.setMaximumSize(QtCore.QSize(50, 16777215))
        self.scale_le.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.scale_le.setObjectName(_fromUtf8("scale_le"))
        self.horizontalLayout_9.addWidget(self.scale_le)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem2)
        self.gridLayout_10.addLayout(self.horizontalLayout_9, 1, 0, 1, 1)
        self.line_2 = QtGui.QFrame(self.expoptions_gb)
        self.line_2.setFrameShape(QtGui.QFrame.VLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.gridLayout_10.addWidget(self.line_2, 0, 1, 2, 1)
        self.expHierarchy_cb = QtGui.QCheckBox(self.expoptions_gb)
        self.expHierarchy_cb.setChecked(True)
        self.expHierarchy_cb.setObjectName(_fromUtf8("expHierarchy_cb"))
        self.gridLayout_10.addWidget(self.expHierarchy_cb, 1, 2, 1, 1)
        self.gridLayout_10.setColumnStretch(2, 1)
        self.verticalLayout.addLayout(self.gridLayout_10)
        self.line_12 = QtGui.QFrame(self.expoptions_gb)
        self.line_12.setFrameShape(QtGui.QFrame.HLine)
        self.line_12.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_12.setObjectName(_fromUtf8("line_12"))
        self.verticalLayout.addWidget(self.line_12)
        self.mainTab = QtGui.QTabWidget(self.expoptions_gb)
        self.mainTab.setObjectName(_fromUtf8("mainTab"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.verticalLayout_14 = QtGui.QVBoxLayout(self.tab)
        self.verticalLayout_14.setSpacing(0)
        self.verticalLayout_14.setMargin(0)
        self.verticalLayout_14.setObjectName(_fromUtf8("verticalLayout_14"))
        self.polyScroll_sa = QtGui.QScrollArea(self.tab)
        self.polyScroll_sa.setWidgetResizable(True)
        self.polyScroll_sa.setObjectName(_fromUtf8("polyScroll_sa"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 313, 279))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_5.setMargin(2)
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.polyGroupEnable_cb = QtGui.QCheckBox(self.scrollAreaWidgetContents)
        self.polyGroupEnable_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.polyGroupEnable_cb.setChecked(True)
        self.polyGroupEnable_cb.setObjectName(_fromUtf8("polyGroupEnable_cb"))
        self.horizontalLayout_7.addWidget(self.polyGroupEnable_cb)
        self.expGeoGlobalGroupName_le = QtGui.QLineEdit(self.scrollAreaWidgetContents)
        self.expGeoGlobalGroupName_le.setObjectName(_fromUtf8("expGeoGlobalGroupName_le"))
        self.horizontalLayout_7.addWidget(self.expGeoGlobalGroupName_le)
        self.verticalLayout_5.addLayout(self.horizontalLayout_7)
        self.pointAttrib_gb = QtGui.QGroupBox(self.scrollAreaWidgetContents)
        self.pointAttrib_gb.setObjectName(_fromUtf8("pointAttrib_gb"))
        self.verticalLayout_13 = QtGui.QVBoxLayout(self.pointAttrib_gb)
        self.verticalLayout_13.setSpacing(2)
        self.verticalLayout_13.setMargin(2)
        self.verticalLayout_13.setObjectName(_fromUtf8("verticalLayout_13"))
        self.horizontalLayout_13 = QtGui.QHBoxLayout()
        self.horizontalLayout_13.setObjectName(_fromUtf8("horizontalLayout_13"))
        self.exportUv_cb = QtGui.QCheckBox(self.pointAttrib_gb)
        self.exportUv_cb.setChecked(False)
        self.exportUv_cb.setObjectName(_fromUtf8("exportUv_cb"))
        self.horizontalLayout_13.addWidget(self.exportUv_cb)
        self.exportVertexColor_cb = QtGui.QCheckBox(self.pointAttrib_gb)
        self.exportVertexColor_cb.setObjectName(_fromUtf8("exportVertexColor_cb"))
        self.horizontalLayout_13.addWidget(self.exportVertexColor_cb)
        self.exportVerNorm_cb = QtGui.QCheckBox(self.pointAttrib_gb)
        self.exportVerNorm_cb.setChecked(False)
        self.exportVerNorm_cb.setObjectName(_fromUtf8("exportVerNorm_cb"))
        self.horizontalLayout_13.addWidget(self.exportVerNorm_cb)
        self.exportCrease_cb = QtGui.QCheckBox(self.pointAttrib_gb)
        self.exportCrease_cb.setObjectName(_fromUtf8("exportCrease_cb"))
        self.horizontalLayout_13.addWidget(self.exportCrease_cb)
        self.horizontalLayout_13.setStretch(3, 1)
        self.verticalLayout_13.addLayout(self.horizontalLayout_13)
        self.verticalLayout_5.addWidget(self.pointAttrib_gb)
        self.groupBox_8 = QtGui.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_8.setObjectName(_fromUtf8("groupBox_8"))
        self.verticalLayout_15 = QtGui.QVBoxLayout(self.groupBox_8)
        self.verticalLayout_15.setSpacing(2)
        self.verticalLayout_15.setMargin(2)
        self.verticalLayout_15.setObjectName(_fromUtf8("verticalLayout_15"))
        self.horizontalLayout_14 = QtGui.QHBoxLayout()
        self.horizontalLayout_14.setObjectName(_fromUtf8("horizontalLayout_14"))
        self.customGeoAttr_cb = QtGui.QCheckBox(self.groupBox_8)
        self.customGeoAttr_cb.setText(_fromUtf8(""))
        self.customGeoAttr_cb.setChecked(True)
        self.customGeoAttr_cb.setObjectName(_fromUtf8("customGeoAttr_cb"))
        self.horizontalLayout_14.addWidget(self.customGeoAttr_cb)
        self.customGeoAttr_le = QtGui.QLineEdit(self.groupBox_8)
        self.customGeoAttr_le.setObjectName(_fromUtf8("customGeoAttr_le"))
        self.horizontalLayout_14.addWidget(self.customGeoAttr_le)
        self.verticalLayout_15.addLayout(self.horizontalLayout_14)
        self.verticalLayout_5.addWidget(self.groupBox_8)
        self.primGroups_gb = QtGui.QGroupBox(self.scrollAreaWidgetContents)
        self.primGroups_gb.setObjectName(_fromUtf8("primGroups_gb"))
        self.gridLayout = QtGui.QGridLayout(self.primGroups_gb)
        self.gridLayout.setMargin(2)
        self.gridLayout.setHorizontalSpacing(4)
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.byMtl_cb = QtGui.QCheckBox(self.primGroups_gb)
        self.byMtl_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.byMtl_cb.setObjectName(_fromUtf8("byMtl_cb"))
        self.gridLayout.addWidget(self.byMtl_cb, 2, 0, 1, 1)
        self.byMtl_le = QtGui.QLineEdit(self.primGroups_gb)
        self.byMtl_le.setText(_fromUtf8(""))
        self.byMtl_le.setObjectName(_fromUtf8("byMtl_le"))
        self.gridLayout.addWidget(self.byMtl_le, 2, 2, 1, 1)
        self.byPar_cb = QtGui.QCheckBox(self.primGroups_gb)
        self.byPar_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.byPar_cb.setObjectName(_fromUtf8("byPar_cb"))
        self.gridLayout.addWidget(self.byPar_cb, 6, 0, 1, 1)
        self.byPar_le = QtGui.QLineEdit(self.primGroups_gb)
        self.byPar_le.setText(_fromUtf8(""))
        self.byPar_le.setObjectName(_fromUtf8("byPar_le"))
        self.gridLayout.addWidget(self.byPar_le, 6, 2, 1, 1)
        self.displayer_cb = QtGui.QCheckBox(self.primGroups_gb)
        self.displayer_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.displayer_cb.setObjectName(_fromUtf8("displayer_cb"))
        self.gridLayout.addWidget(self.displayer_cb, 11, 0, 1, 1)
        self.byLayer_le = QtGui.QLineEdit(self.primGroups_gb)
        self.byLayer_le.setText(_fromUtf8(""))
        self.byLayer_le.setObjectName(_fromUtf8("byLayer_le"))
        self.gridLayout.addWidget(self.byLayer_le, 11, 2, 1, 1)
        self.label_3 = QtGui.QLabel(self.primGroups_gb)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.label_4 = QtGui.QLabel(self.primGroups_gb)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 0, 2, 1, 1)
        self.line_4 = QtGui.QFrame(self.primGroups_gb)
        self.line_4.setFrameShape(QtGui.QFrame.HLine)
        self.line_4.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_4.setObjectName(_fromUtf8("line_4"))
        self.gridLayout.addWidget(self.line_4, 1, 0, 1, 4)
        self.byMtlPref_le = QtGui.QLineEdit(self.primGroups_gb)
        self.byMtlPref_le.setObjectName(_fromUtf8("byMtlPref_le"))
        self.gridLayout.addWidget(self.byMtlPref_le, 2, 1, 1, 1)
        self.byParPref_le = QtGui.QLineEdit(self.primGroups_gb)
        self.byParPref_le.setObjectName(_fromUtf8("byParPref_le"))
        self.gridLayout.addWidget(self.byParPref_le, 6, 1, 1, 1)
        self.byLayerPref_le = QtGui.QLineEdit(self.primGroups_gb)
        self.byLayerPref_le.setObjectName(_fromUtf8("byLayerPref_le"))
        self.gridLayout.addWidget(self.byLayerPref_le, 11, 1, 1, 1)
        self.label_5 = QtGui.QLabel(self.primGroups_gb)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 1, 1, 1)
        self.byObj_cb = QtGui.QCheckBox(self.primGroups_gb)
        self.byObj_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.byObj_cb.setObjectName(_fromUtf8("byObj_cb"))
        self.gridLayout.addWidget(self.byObj_cb, 4, 0, 1, 1)
        self.byObjPref_le = QtGui.QLineEdit(self.primGroups_gb)
        self.byObjPref_le.setObjectName(_fromUtf8("byObjPref_le"))
        self.gridLayout.addWidget(self.byObjPref_le, 4, 1, 1, 1)
        self.byObj_le = QtGui.QLineEdit(self.primGroups_gb)
        self.byObj_le.setText(_fromUtf8(""))
        self.byObj_le.setObjectName(_fromUtf8("byObj_le"))
        self.gridLayout.addWidget(self.byObj_le, 4, 2, 1, 1)
        self.byShape_cb = QtGui.QCheckBox(self.primGroups_gb)
        self.byShape_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.byShape_cb.setObjectName(_fromUtf8("byShape_cb"))
        self.gridLayout.addWidget(self.byShape_cb, 5, 0, 1, 1)
        self.bySpahePref_le = QtGui.QLineEdit(self.primGroups_gb)
        self.bySpahePref_le.setObjectName(_fromUtf8("bySpahePref_le"))
        self.gridLayout.addWidget(self.bySpahePref_le, 5, 1, 1, 1)
        self.byShape_le = QtGui.QLineEdit(self.primGroups_gb)
        self.byShape_le.setText(_fromUtf8(""))
        self.byShape_le.setObjectName(_fromUtf8("byShape_le"))
        self.gridLayout.addWidget(self.byShape_le, 5, 2, 1, 1)
        self.verticalLayout_5.addWidget(self.primGroups_gb)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem3)
        self.polyScroll_sa.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_14.addWidget(self.polyScroll_sa)
        self.mainTab.addTab(self.tab, _fromUtf8(""))
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName(_fromUtf8("tab_4"))
        self.verticalLayout_11 = QtGui.QVBoxLayout(self.tab_4)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setMargin(0)
        self.verticalLayout_11.setObjectName(_fromUtf8("verticalLayout_11"))
        self.curvScroll_sa = QtGui.QScrollArea(self.tab_4)
        self.curvScroll_sa.setWidgetResizable(True)
        self.curvScroll_sa.setObjectName(_fromUtf8("curvScroll_sa"))
        self.scrollAreaWidgetContents_2 = QtGui.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 313, 279))
        self.scrollAreaWidgetContents_2.setObjectName(_fromUtf8("scrollAreaWidgetContents_2"))
        self.verticalLayout_16 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_16.setSpacing(2)
        self.verticalLayout_16.setMargin(2)
        self.verticalLayout_16.setObjectName(_fromUtf8("verticalLayout_16"))
        self.horizontalLayout_10 = QtGui.QHBoxLayout()
        self.horizontalLayout_10.setObjectName(_fromUtf8("horizontalLayout_10"))
        self.curveGroupEnable_cb = QtGui.QCheckBox(self.scrollAreaWidgetContents_2)
        self.curveGroupEnable_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.curveGroupEnable_cb.setChecked(True)
        self.curveGroupEnable_cb.setObjectName(_fromUtf8("curveGroupEnable_cb"))
        self.horizontalLayout_10.addWidget(self.curveGroupEnable_cb)
        self.expCurvesGlobalGroupName_le = QtGui.QLineEdit(self.scrollAreaWidgetContents_2)
        self.expCurvesGlobalGroupName_le.setObjectName(_fromUtf8("expCurvesGlobalGroupName_le"))
        self.horizontalLayout_10.addWidget(self.expCurvesGlobalGroupName_le)
        self.verticalLayout_16.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_16 = QtGui.QHBoxLayout()
        self.horizontalLayout_16.setObjectName(_fromUtf8("horizontalLayout_16"))
        self.curvToNURBS_rb = QtGui.QRadioButton(self.scrollAreaWidgetContents_2)
        self.curvToNURBS_rb.setChecked(True)
        self.curvToNURBS_rb.setObjectName(_fromUtf8("curvToNURBS_rb"))
        self.horizontalLayout_16.addWidget(self.curvToNURBS_rb)
        self.curvToPoly_rb = QtGui.QRadioButton(self.scrollAreaWidgetContents_2)
        self.curvToPoly_rb.setObjectName(_fromUtf8("curvToPoly_rb"))
        self.horizontalLayout_16.addWidget(self.curvToPoly_rb)
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_16.addItem(spacerItem4)
        self.verticalLayout_16.addLayout(self.horizontalLayout_16)
        self.groupBox_6 = QtGui.QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_6.setObjectName(_fromUtf8("groupBox_6"))
        self.gridLayout_4 = QtGui.QGridLayout(self.groupBox_6)
        self.gridLayout_4.setMargin(2)
        self.gridLayout_4.setSpacing(2)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.byCurvObj_le = QtGui.QLineEdit(self.groupBox_6)
        self.byCurvObj_le.setText(_fromUtf8(""))
        self.byCurvObj_le.setObjectName(_fromUtf8("byCurvObj_le"))
        self.gridLayout_4.addWidget(self.byCurvObj_le, 2, 2, 1, 1)
        self.byCrvObj_cb = QtGui.QCheckBox(self.groupBox_6)
        self.byCrvObj_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.byCrvObj_cb.setObjectName(_fromUtf8("byCrvObj_cb"))
        self.gridLayout_4.addWidget(self.byCrvObj_cb, 2, 0, 1, 1)
        self.label_9 = QtGui.QLabel(self.groupBox_6)
        self.label_9.setObjectName(_fromUtf8("label_9"))
        self.gridLayout_4.addWidget(self.label_9, 0, 0, 1, 1)
        self.label_10 = QtGui.QLabel(self.groupBox_6)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.gridLayout_4.addWidget(self.label_10, 0, 2, 1, 1)
        self.line_5 = QtGui.QFrame(self.groupBox_6)
        self.line_5.setFrameShape(QtGui.QFrame.HLine)
        self.line_5.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_5.setObjectName(_fromUtf8("line_5"))
        self.gridLayout_4.addWidget(self.line_5, 1, 0, 1, 4)
        self.byCrvPar_cb = QtGui.QCheckBox(self.groupBox_6)
        self.byCrvPar_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.byCrvPar_cb.setObjectName(_fromUtf8("byCrvPar_cb"))
        self.gridLayout_4.addWidget(self.byCrvPar_cb, 3, 0, 1, 1)
        self.byCurvPar_le = QtGui.QLineEdit(self.groupBox_6)
        self.byCurvPar_le.setText(_fromUtf8(""))
        self.byCurvPar_le.setObjectName(_fromUtf8("byCurvPar_le"))
        self.gridLayout_4.addWidget(self.byCurvPar_le, 3, 2, 1, 1)
        self.curvDisplayer_cb = QtGui.QCheckBox(self.groupBox_6)
        self.curvDisplayer_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.curvDisplayer_cb.setObjectName(_fromUtf8("curvDisplayer_cb"))
        self.gridLayout_4.addWidget(self.curvDisplayer_cb, 4, 0, 1, 1)
        self.byCurvLayer_le = QtGui.QLineEdit(self.groupBox_6)
        self.byCurvLayer_le.setText(_fromUtf8(""))
        self.byCurvLayer_le.setObjectName(_fromUtf8("byCurvLayer_le"))
        self.gridLayout_4.addWidget(self.byCurvLayer_le, 4, 2, 1, 1)
        self.byCurvObjPref_le = QtGui.QLineEdit(self.groupBox_6)
        self.byCurvObjPref_le.setObjectName(_fromUtf8("byCurvObjPref_le"))
        self.gridLayout_4.addWidget(self.byCurvObjPref_le, 2, 1, 1, 1)
        self.byCurvParPref_le = QtGui.QLineEdit(self.groupBox_6)
        self.byCurvParPref_le.setObjectName(_fromUtf8("byCurvParPref_le"))
        self.gridLayout_4.addWidget(self.byCurvParPref_le, 3, 1, 1, 1)
        self.byCurvLayerPref_le = QtGui.QLineEdit(self.groupBox_6)
        self.byCurvLayerPref_le.setObjectName(_fromUtf8("byCurvLayerPref_le"))
        self.gridLayout_4.addWidget(self.byCurvLayerPref_le, 4, 1, 1, 1)
        self.label_11 = QtGui.QLabel(self.groupBox_6)
        self.label_11.setObjectName(_fromUtf8("label_11"))
        self.gridLayout_4.addWidget(self.label_11, 0, 1, 1, 1)
        self.verticalLayout_16.addWidget(self.groupBox_6)
        spacerItem5 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_16.addItem(spacerItem5)
        self.curvScroll_sa.setWidget(self.scrollAreaWidgetContents_2)
        self.verticalLayout_11.addWidget(self.curvScroll_sa)
        self.mainTab.addTab(self.tab_4, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.verticalLayout_6 = QtGui.QVBoxLayout(self.tab_2)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setMargin(0)
        self.verticalLayout_6.setObjectName(_fromUtf8("verticalLayout_6"))
        self.partScroll_sa = QtGui.QScrollArea(self.tab_2)
        self.partScroll_sa.setWidgetResizable(True)
        self.partScroll_sa.setObjectName(_fromUtf8("partScroll_sa"))
        self.scrollAreaWidgetContents_4 = QtGui.QWidget()
        self.scrollAreaWidgetContents_4.setGeometry(QtCore.QRect(0, 0, 313, 279))
        self.scrollAreaWidgetContents_4.setObjectName(_fromUtf8("scrollAreaWidgetContents_4"))
        self.verticalLayout_18 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents_4)
        self.verticalLayout_18.setSpacing(2)
        self.verticalLayout_18.setMargin(2)
        self.verticalLayout_18.setObjectName(_fromUtf8("verticalLayout_18"))
        self.horizontalLayout_11 = QtGui.QHBoxLayout()
        self.horizontalLayout_11.setObjectName(_fromUtf8("horizontalLayout_11"))
        self.partGroupEnable_cb = QtGui.QCheckBox(self.scrollAreaWidgetContents_4)
        self.partGroupEnable_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.partGroupEnable_cb.setChecked(True)
        self.partGroupEnable_cb.setObjectName(_fromUtf8("partGroupEnable_cb"))
        self.horizontalLayout_11.addWidget(self.partGroupEnable_cb)
        self.expParticlesGlobalGroupName_le = QtGui.QLineEdit(self.scrollAreaWidgetContents_4)
        self.expParticlesGlobalGroupName_le.setObjectName(_fromUtf8("expParticlesGlobalGroupName_le"))
        self.horizontalLayout_11.addWidget(self.expParticlesGlobalGroupName_le)
        self.verticalLayout_18.addLayout(self.horizontalLayout_11)
        self.groupBox_4 = QtGui.QGroupBox(self.scrollAreaWidgetContents_4)
        self.groupBox_4.setObjectName(_fromUtf8("groupBox_4"))
        self.gridLayout_6 = QtGui.QGridLayout(self.groupBox_4)
        self.gridLayout_6.setMargin(2)
        self.gridLayout_6.setSpacing(2)
        self.gridLayout_6.setObjectName(_fromUtf8("gridLayout_6"))
        self.customAttr_cb = QtGui.QCheckBox(self.groupBox_4)
        self.customAttr_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.customAttr_cb.setText(_fromUtf8(""))
        self.customAttr_cb.setChecked(True)
        self.customAttr_cb.setObjectName(_fromUtf8("customAttr_cb"))
        self.gridLayout_6.addWidget(self.customAttr_cb, 0, 0, 1, 1)
        self.customAttr_le = QtGui.QLineEdit(self.groupBox_4)
        self.customAttr_le.setText(_fromUtf8(""))
        self.customAttr_le.setObjectName(_fromUtf8("customAttr_le"))
        self.gridLayout_6.addWidget(self.customAttr_le, 0, 1, 1, 1)
        self.verticalLayout_18.addWidget(self.groupBox_4)
        self.groupBox_3 = QtGui.QGroupBox(self.scrollAreaWidgetContents_4)
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox_3)
        self.gridLayout_2.setMargin(2)
        self.gridLayout_2.setSpacing(2)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.byPartObj_cb = QtGui.QCheckBox(self.groupBox_3)
        self.byPartObj_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.byPartObj_cb.setObjectName(_fromUtf8("byPartObj_cb"))
        self.gridLayout_2.addWidget(self.byPartObj_cb, 2, 0, 1, 1)
        self.byEmit_cb = QtGui.QCheckBox(self.groupBox_3)
        self.byEmit_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.byEmit_cb.setObjectName(_fromUtf8("byEmit_cb"))
        self.gridLayout_2.addWidget(self.byEmit_cb, 3, 0, 1, 1)
        self.label_12 = QtGui.QLabel(self.groupBox_3)
        self.label_12.setObjectName(_fromUtf8("label_12"))
        self.gridLayout_2.addWidget(self.label_12, 0, 0, 1, 1)
        self.line_6 = QtGui.QFrame(self.groupBox_3)
        self.line_6.setFrameShape(QtGui.QFrame.HLine)
        self.line_6.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_6.setObjectName(_fromUtf8("line_6"))
        self.gridLayout_2.addWidget(self.line_6, 1, 0, 1, 4)
        self.byPartObj_le = QtGui.QLineEdit(self.groupBox_3)
        self.byPartObj_le.setText(_fromUtf8(""))
        self.byPartObj_le.setObjectName(_fromUtf8("byPartObj_le"))
        self.gridLayout_2.addWidget(self.byPartObj_le, 2, 2, 1, 1)
        self.label_14 = QtGui.QLabel(self.groupBox_3)
        self.label_14.setObjectName(_fromUtf8("label_14"))
        self.gridLayout_2.addWidget(self.label_14, 0, 2, 1, 1)
        self.byEmit_le = QtGui.QLineEdit(self.groupBox_3)
        self.byEmit_le.setText(_fromUtf8(""))
        self.byEmit_le.setObjectName(_fromUtf8("byEmit_le"))
        self.gridLayout_2.addWidget(self.byEmit_le, 3, 2, 1, 1)
        self.byPartObjPref_le = QtGui.QLineEdit(self.groupBox_3)
        self.byPartObjPref_le.setObjectName(_fromUtf8("byPartObjPref_le"))
        self.gridLayout_2.addWidget(self.byPartObjPref_le, 2, 1, 1, 1)
        self.byEmitPref_le = QtGui.QLineEdit(self.groupBox_3)
        self.byEmitPref_le.setObjectName(_fromUtf8("byEmitPref_le"))
        self.gridLayout_2.addWidget(self.byEmitPref_le, 3, 1, 1, 1)
        self.label_13 = QtGui.QLabel(self.groupBox_3)
        self.label_13.setObjectName(_fromUtf8("label_13"))
        self.gridLayout_2.addWidget(self.label_13, 0, 1, 1, 1)
        self.verticalLayout_18.addWidget(self.groupBox_3)
        spacerItem6 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_18.addItem(spacerItem6)
        self.partScroll_sa.setWidget(self.scrollAreaWidgetContents_4)
        self.verticalLayout_6.addWidget(self.partScroll_sa)
        self.mainTab.addTab(self.tab_2, _fromUtf8(""))
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName(_fromUtf8("tab_3"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.tab_3)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setMargin(0)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.pivScroll_sa = QtGui.QScrollArea(self.tab_3)
        self.pivScroll_sa.setWidgetResizable(True)
        self.pivScroll_sa.setObjectName(_fromUtf8("pivScroll_sa"))
        self.scrollAreaWidgetContents_3 = QtGui.QWidget()
        self.scrollAreaWidgetContents_3.setGeometry(QtCore.QRect(0, 0, 313, 279))
        self.scrollAreaWidgetContents_3.setObjectName(_fromUtf8("scrollAreaWidgetContents_3"))
        self.verticalLayout_17 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents_3)
        self.verticalLayout_17.setSpacing(2)
        self.verticalLayout_17.setMargin(2)
        self.verticalLayout_17.setObjectName(_fromUtf8("verticalLayout_17"))
        self.gridLayout_3 = QtGui.QGridLayout()
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.expPivotsGlobalGroupName_le = QtGui.QLineEdit(self.scrollAreaWidgetContents_3)
        self.expPivotsGlobalGroupName_le.setObjectName(_fromUtf8("expPivotsGlobalGroupName_le"))
        self.gridLayout_3.addWidget(self.expPivotsGlobalGroupName_le, 1, 2, 1, 1)
        self.label_22 = QtGui.QLabel(self.scrollAreaWidgetContents_3)
        self.label_22.setObjectName(_fromUtf8("label_22"))
        self.gridLayout_3.addWidget(self.label_22, 2, 1, 1, 1)
        self.pivotFilter_le = QtGui.QLineEdit(self.scrollAreaWidgetContents_3)
        self.pivotFilter_le.setText(_fromUtf8(""))
        self.pivotFilter_le.setObjectName(_fromUtf8("pivotFilter_le"))
        self.gridLayout_3.addWidget(self.pivotFilter_le, 2, 2, 1, 1)
        self.pivSkipTransform_cb = QtGui.QCheckBox(self.scrollAreaWidgetContents_3)
        self.pivSkipTransform_cb.setObjectName(_fromUtf8("pivSkipTransform_cb"))
        self.gridLayout_3.addWidget(self.pivSkipTransform_cb, 3, 1, 1, 2)
        self.pivotGroupEnable_cb = QtGui.QCheckBox(self.scrollAreaWidgetContents_3)
        self.pivotGroupEnable_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.pivotGroupEnable_cb.setChecked(True)
        self.pivotGroupEnable_cb.setObjectName(_fromUtf8("pivotGroupEnable_cb"))
        self.gridLayout_3.addWidget(self.pivotGroupEnable_cb, 1, 1, 1, 1)
        self.verticalLayout_17.addLayout(self.gridLayout_3)
        self.pivotAttr_gb = QtGui.QGroupBox(self.scrollAreaWidgetContents_3)
        self.pivotAttr_gb.setCheckable(False)
        self.pivotAttr_gb.setObjectName(_fromUtf8("pivotAttr_gb"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.pivotAttr_gb)
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setMargin(2)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.gridLayout_5 = QtGui.QGridLayout()
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.exportOrient_cb = QtGui.QCheckBox(self.pivotAttr_gb)
        self.exportOrient_cb.setChecked(True)
        self.exportOrient_cb.setObjectName(_fromUtf8("exportOrient_cb"))
        self.gridLayout_5.addWidget(self.exportOrient_cb, 0, 0, 1, 1)
        self.scale_cb = QtGui.QCheckBox(self.pivotAttr_gb)
        self.scale_cb.setChecked(True)
        self.scale_cb.setObjectName(_fromUtf8("scale_cb"))
        self.gridLayout_5.addWidget(self.scale_cb, 0, 1, 1, 1)
        spacerItem7 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_5.addItem(spacerItem7, 0, 2, 1, 1)
        self.verticalLayout_3.addLayout(self.gridLayout_5)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.customPivotAttr_cb = QtGui.QCheckBox(self.pivotAttr_gb)
        self.customPivotAttr_cb.setText(_fromUtf8(""))
        self.customPivotAttr_cb.setChecked(True)
        self.customPivotAttr_cb.setObjectName(_fromUtf8("customPivotAttr_cb"))
        self.horizontalLayout_6.addWidget(self.customPivotAttr_cb)
        self.customPivotAttr_le = QtGui.QLineEdit(self.pivotAttr_gb)
        self.customPivotAttr_le.setObjectName(_fromUtf8("customPivotAttr_le"))
        self.horizontalLayout_6.addWidget(self.customPivotAttr_le)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)
        self.verticalLayout_17.addWidget(self.pivotAttr_gb)
        self.groupBox_9 = QtGui.QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox_9.setObjectName(_fromUtf8("groupBox_9"))
        self.gridLayout_7 = QtGui.QGridLayout(self.groupBox_9)
        self.gridLayout_7.setMargin(2)
        self.gridLayout_7.setSpacing(2)
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        self.expPivotObj_le = QtGui.QLineEdit(self.groupBox_9)
        self.expPivotObj_le.setObjectName(_fromUtf8("expPivotObj_le"))
        self.gridLayout_7.addWidget(self.expPivotObj_le, 4, 2, 1, 1)
        self.expPivotParent_le = QtGui.QLineEdit(self.groupBox_9)
        self.expPivotParent_le.setObjectName(_fromUtf8("expPivotParent_le"))
        self.gridLayout_7.addWidget(self.expPivotParent_le, 6, 2, 1, 1)
        self.expPivotShape_le = QtGui.QLineEdit(self.groupBox_9)
        self.expPivotShape_le.setObjectName(_fromUtf8("expPivotShape_le"))
        self.gridLayout_7.addWidget(self.expPivotShape_le, 5, 2, 1, 1)
        self.label_17 = QtGui.QLabel(self.groupBox_9)
        self.label_17.setObjectName(_fromUtf8("label_17"))
        self.gridLayout_7.addWidget(self.label_17, 2, 0, 1, 1)
        self.line_7 = QtGui.QFrame(self.groupBox_9)
        self.line_7.setFrameShape(QtGui.QFrame.HLine)
        self.line_7.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_7.setObjectName(_fromUtf8("line_7"))
        self.gridLayout_7.addWidget(self.line_7, 3, 0, 1, 4)
        self.label_18 = QtGui.QLabel(self.groupBox_9)
        self.label_18.setObjectName(_fromUtf8("label_18"))
        self.gridLayout_7.addWidget(self.label_18, 2, 2, 1, 1)
        self.expPivotObj_cb = QtGui.QCheckBox(self.groupBox_9)
        self.expPivotObj_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.expPivotObj_cb.setObjectName(_fromUtf8("expPivotObj_cb"))
        self.gridLayout_7.addWidget(self.expPivotObj_cb, 4, 0, 1, 1)
        self.expPivotShape_cb = QtGui.QCheckBox(self.groupBox_9)
        self.expPivotShape_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.expPivotShape_cb.setObjectName(_fromUtf8("expPivotShape_cb"))
        self.gridLayout_7.addWidget(self.expPivotShape_cb, 5, 0, 1, 1)
        self.expPivotParent_cb = QtGui.QCheckBox(self.groupBox_9)
        self.expPivotParent_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.expPivotParent_cb.setObjectName(_fromUtf8("expPivotParent_cb"))
        self.gridLayout_7.addWidget(self.expPivotParent_cb, 6, 0, 1, 1)
        self.expPivotObjPref_le = QtGui.QLineEdit(self.groupBox_9)
        self.expPivotObjPref_le.setObjectName(_fromUtf8("expPivotObjPref_le"))
        self.gridLayout_7.addWidget(self.expPivotObjPref_le, 4, 1, 1, 1)
        self.expPivotShapePref_le = QtGui.QLineEdit(self.groupBox_9)
        self.expPivotShapePref_le.setObjectName(_fromUtf8("expPivotShapePref_le"))
        self.gridLayout_7.addWidget(self.expPivotShapePref_le, 5, 1, 1, 1)
        self.expPivotParentPref_le = QtGui.QLineEdit(self.groupBox_9)
        self.expPivotParentPref_le.setObjectName(_fromUtf8("expPivotParentPref_le"))
        self.gridLayout_7.addWidget(self.expPivotParentPref_le, 6, 1, 1, 1)
        self.label_19 = QtGui.QLabel(self.groupBox_9)
        self.label_19.setObjectName(_fromUtf8("label_19"))
        self.gridLayout_7.addWidget(self.label_19, 2, 1, 1, 1)
        self.expPivotLayer_cb = QtGui.QCheckBox(self.groupBox_9)
        self.expPivotLayer_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.expPivotLayer_cb.setObjectName(_fromUtf8("expPivotLayer_cb"))
        self.gridLayout_7.addWidget(self.expPivotLayer_cb, 7, 0, 1, 1)
        self.expPivotLayerPref_le = QtGui.QLineEdit(self.groupBox_9)
        self.expPivotLayerPref_le.setObjectName(_fromUtf8("expPivotLayerPref_le"))
        self.gridLayout_7.addWidget(self.expPivotLayerPref_le, 7, 1, 1, 1)
        self.expPivotlayer_le = QtGui.QLineEdit(self.groupBox_9)
        self.expPivotlayer_le.setObjectName(_fromUtf8("expPivotlayer_le"))
        self.gridLayout_7.addWidget(self.expPivotlayer_le, 7, 2, 1, 1)
        self.verticalLayout_17.addWidget(self.groupBox_9)
        spacerItem8 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_17.addItem(spacerItem8)
        self.pivScroll_sa.setWidget(self.scrollAreaWidgetContents_3)
        self.verticalLayout_4.addWidget(self.pivScroll_sa)
        self.mainTab.addTab(self.tab_3, _fromUtf8(""))
        self.verticalLayout.addWidget(self.mainTab)
        self.layoutWidget = QtGui.QWidget(self.textWidget_sp)
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.verticalLayout_9 = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_9.setMargin(0)
        self.verticalLayout_9.setObjectName(_fromUtf8("verticalLayout_9"))
        self.output_te = QtGui.QTextEdit(self.layoutWidget)
        self.output_te.setReadOnly(True)
        self.output_te.setObjectName(_fromUtf8("output_te"))
        self.verticalLayout_9.addWidget(self.output_te)
        self.clearText_btn = QtGui.QPushButton(self.layoutWidget)
        self.clearText_btn.setMaximumSize(QtCore.QSize(16777215, 10))
        self.clearText_btn.setText(_fromUtf8(""))
        self.clearText_btn.setObjectName(_fromUtf8("clearText_btn"))
        self.verticalLayout_9.addWidget(self.clearText_btn)
        self.verticalLayout_9.setStretch(1, 1)
        self.verticalLayout_22.addWidget(self.textWidget_sp)
        mgeoWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(mgeoWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 619, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        self.menuMenu = QtGui.QMenu(self.menubar)
        self.menuMenu.setObjectName(_fromUtf8("menuMenu"))
        mgeoWindow.setMenuBar(self.menubar)
        self.statusBar = QtGui.QStatusBar(mgeoWindow)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        mgeoWindow.setStatusBar(self.statusBar)
        self.help_act = QtGui.QAction(mgeoWindow)
        self.help_act.setObjectName(_fromUtf8("help_act"))
        self.about_act = QtGui.QAction(mgeoWindow)
        self.about_act.setObjectName(_fromUtf8("about_act"))
        self.resetAll_act = QtGui.QAction(mgeoWindow)
        self.resetAll_act.setObjectName(_fromUtf8("resetAll_act"))
        self.options_act = QtGui.QAction(mgeoWindow)
        self.options_act.setObjectName(_fromUtf8("options_act"))
        self.default_act = QtGui.QAction(mgeoWindow)
        self.default_act.setCheckable(False)
        self.default_act.setObjectName(_fromUtf8("default_act"))
        self.saveDefault_act = QtGui.QAction(mgeoWindow)
        self.saveDefault_act.setObjectName(_fromUtf8("saveDefault_act"))
        self.extReport_act = QtGui.QAction(mgeoWindow)
        self.extReport_act.setCheckable(True)
        self.extReport_act.setObjectName(_fromUtf8("extReport_act"))
        self.save_act = QtGui.QAction(mgeoWindow)
        self.save_act.setObjectName(_fromUtf8("save_act"))
        self.load_act = QtGui.QAction(mgeoWindow)
        self.load_act.setObjectName(_fromUtf8("load_act"))
        self.isolateExported_act = QtGui.QAction(mgeoWindow)
        self.isolateExported_act.setCheckable(True)
        self.isolateExported_act.setObjectName(_fromUtf8("isolateExported_act"))
        self.colorInd_act = QtGui.QAction(mgeoWindow)
        self.colorInd_act.setCheckable(True)
        self.colorInd_act.setObjectName(_fromUtf8("colorInd_act"))
        self.showWarnings_act = QtGui.QAction(mgeoWindow)
        self.showWarnings_act.setCheckable(True)
        self.showWarnings_act.setObjectName(_fromUtf8("showWarnings_act"))
        self.menuHelp.addAction(self.help_act)
        self.menuHelp.addAction(self.about_act)
        self.menuMenu.addAction(self.save_act)
        self.menuMenu.addAction(self.load_act)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.default_act)
        self.menuMenu.addAction(self.saveDefault_act)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.extReport_act)
        self.menuMenu.addAction(self.isolateExported_act)
        self.menuMenu.addAction(self.colorInd_act)
        self.menuMenu.addAction(self.showWarnings_act)
        self.menubar.addAction(self.menuMenu.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(mgeoWindow)
        self.mainTab.setCurrentIndex(0)
        QtCore.QObject.connect(self.mdd_rb, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.writeFile_cb.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(mgeoWindow)

    def retranslateUi(self, mgeoWindow):
        mgeoWindow.setWindowTitle(_translate("mgeoWindow", "MainWindow", None))
        self.groupBox_2.setTitle(_translate("mgeoWindow", "Formats", None))
        self.label_6.setText(_translate("mgeoWindow", "Cache:", None))
        self.label_2.setText(_translate("mgeoWindow", "File format:", None))
        self.formatGeo_rb.setToolTip(_translate("mgeoWindow", "Write to GEO format", None))
        self.formatGeo_rb.setText(_translate("mgeoWindow", "GEO", None))
        self.formatBgeo_rb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Write to BGEO (bynary GEO) format. </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Need to install the Houdini !</span></p></body></html>", None))
        self.formatBgeo_rb.setText(_translate("mgeoWindow", "BGEO", None))
        self.formatGzip_cb.setToolTip(_translate("mgeoWindow", "Use GZip archive", None))
        self.formatGzip_cb.setText(_translate("mgeoWindow", "GZIP", None))
        self.sequence_rb.setToolTip(_translate("mgeoWindow", "Export to file sequence", None))
        self.sequence_rb.setText(_translate("mgeoWindow", "Sequence", None))
        self.mdd_rb.setToolTip(_translate("mgeoWindow", "Export single GEO file + MDD cache", None))
        self.mdd_rb.setText(_translate("mgeoWindow", "MDD", None))
        self.writeFile_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Write GEO and MDD / MDD only</span></p></body></html>", None))
        self.writeFile_cb.setText(_translate("mgeoWindow", "Write geometry", None))
        self.outFile_gb.setTitle(_translate("mgeoWindow", "Output file", None))
        self.exportPath_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"result_box\"></a><span style=\" font-size:8pt;\">U</span><span style=\" font-size:8pt;\">se the </span><span style=\" font-size:8pt; font-weight:600;\">$ F#</span><span style=\" font-size:8pt;\"> to replace the frame number</span></p></body></html>", None))
        self.applets_btn.setText(_translate("mgeoWindow", "...", None))
        self.fileAsk_rb.setToolTip(_translate("mgeoWindow", "Ask a new file name if exists", None))
        self.fileAsk_rb.setText(_translate("mgeoWindow", "Ask", None))
        self.fileOverride_rb.setToolTip(_translate("mgeoWindow", "Owerwrite old file", None))
        self.fileOverride_rb.setText(_translate("mgeoWindow", "Overwrite", None))
        self.fileSkip_rb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Skip export if file exists</span></p></body></html>", None))
        self.fileSkip_rb.setText(_translate("mgeoWindow", "Skip", None))
        self.fileRename_rb.setToolTip(_translate("mgeoWindow", "Automatically rename", None))
        self.fileRename_rb.setText(_translate("mgeoWindow", "Rename", None))
        self.frameRangeSettings_gb.setTitle(_translate("mgeoWindow", "Frame range", None))
        self.singleFrame_rb.setToolTip(_translate("mgeoWindow", "Export single frame", None))
        self.singleFrame_rb.setText(_translate("mgeoWindow", "Single", None))
        self.rangeFrame_rb.setToolTip(_translate("mgeoWindow", "Export frame range", None))
        self.rangeFrame_rb.setText(_translate("mgeoWindow", "Range", None))
        self.startFrame_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Start frame</span></p></body></html>", None))
        self.endFrame_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">End Frame</span></p></body></html>", None))
        self.stepFrame_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Step</span></p></body></html>", None))
        self.setrange_btn.setToolTip(_translate("mgeoWindow", "Set range from current timeline", None))
        self.setrange_btn.setText(_translate("mgeoWindow", "<<", None))
        self.groupBox_5.setTitle(_translate("mgeoWindow", "Export sets", None))
        self.createSet_btn.setToolTip(_translate("mgeoWindow", "Create new export set from selection", None))
        self.createSet_btn.setText(_translate("mgeoWindow", "*", None))
        self.deleteSet_btn.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Remove set</span></p></body></html>", None))
        self.deleteSet_btn.setText(_translate("mgeoWindow", "x", None))
        self.reloadSets_btn.setToolTip(_translate("mgeoWindow", "Reload sets from scene", None))
        self.reloadSets_btn.setText(_translate("mgeoWindow", "R", None))
        self.addToSet_btn.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Add selected objects to set. </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Supported types:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">- Mesh objects (component skipped)</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">- Particles / nParticles</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">- Nurbs curves</span></p></body></html>", None))
        self.addToSet_btn.setText(_translate("mgeoWindow", "add", None))
        self.removeFromSet_btn.setToolTip(_translate("mgeoWindow", "Remove selected objects from set", None))
        self.removeFromSet_btn.setText(_translate("mgeoWindow", "rem", None))
        self.replaceSet_btn.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Replace all objects in set to the selected</span></p></body></html>", None))
        self.replaceSet_btn.setText(_translate("mgeoWindow", "repl", None))
        self.clearSet_btn.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Clear set</span></p></body></html>", None))
        self.clearSet_btn.setText(_translate("mgeoWindow", "CL", None))
        self.geoExport_btn.setToolTip(_translate("mgeoWindow", "START EXPORT!!!", None))
        self.geoExport_btn.setText(_translate("mgeoWindow", "EXPORT", None))
        self.expoptions_gb.setTitle(_translate("mgeoWindow", "Export Options", None))
        self.label.setText(_translate("mgeoWindow", "Global Position:", None))
        self.worldPos_rb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Read position in world space</span></p></body></html>", None))
        self.worldPos_rb.setText(_translate("mgeoWindow", "World", None))
        self.localPos_rb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Read position in local space</span></p></body></html>", None))
        self.localPos_rb.setText(_translate("mgeoWindow", "Local", None))
        self.expVis_cb.setToolTip(_translate("mgeoWindow", "Export only visible objects", None))
        self.expVis_cb.setText(_translate("mgeoWindow", "Visible only", None))
        self.label_8.setText(_translate("mgeoWindow", "Global Scale:", None))
        self.scale_le.setToolTip(_translate("mgeoWindow", "Global scale of geometry", None))
        self.scale_le.setText(_translate("mgeoWindow", "1.0", None))
        self.expHierarchy_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Export all parented objects</span></p></body></html>", None))
        self.expHierarchy_cb.setText(_translate("mgeoWindow", "Export Hierarchy", None))
        self.mainTab.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Export types</span></p></body></html>", None))
        self.polyGroupEnable_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Enable/disable global Popy group</span></p></body></html>", None))
        self.polyGroupEnable_cb.setText(_translate("mgeoWindow", "Poly Group", None))
        self.expGeoGlobalGroupName_le.setToolTip(_translate("mgeoWindow", "Main polygons group name", None))
        self.expGeoGlobalGroupName_le.setText(_translate("mgeoWindow", "POLY", None))
        self.pointAttrib_gb.setToolTip(_translate("mgeoWindow", "Vertex Atributes", None))
        self.pointAttrib_gb.setTitle(_translate("mgeoWindow", "Vertex attributes", None))
        self.exportUv_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Export uv as vertex attribute.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">attrib: </span><span style=\" font-size:8pt; font-weight:600;\">uv</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">type: vector3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">(RMB to select the method of naming)</span></p></body></html>", None))
        self.exportUv_cb.setText(_translate("mgeoWindow", "UV", None))
        self.exportVertexColor_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Export vertex color as vertex attribute.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">attrib: </span><span style=\" font-size:8pt; font-weight:600;\">Cd</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">type: vector3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">(RMB to select the method of naming)</span></p></body></html>", None))
        self.exportVertexColor_cb.setText(_translate("mgeoWindow", "Color", None))
        self.exportVerNorm_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Export normals as vertex attribute (hard-soft edges).</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">attrib: </span><span style=\" font-size:8pt; font-weight:600;\">N</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">type: vector3</span></p></body></html>", None))
        self.exportVerNorm_cb.setText(_translate("mgeoWindow", "Vertex Normal", None))
        self.exportCrease_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Export edge crease as vertex attribute.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">attrib: </span><span style=\" font-size:8pt; font-weight:600;\">creaseweight</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">type: float</span></p></body></html>", None))
        self.exportCrease_cb.setText(_translate("mgeoWindow", "Edge Crease", None))
        self.groupBox_8.setTitle(_translate("mgeoWindow", "Prim attributes", None))
        self.customGeoAttr_cb.setToolTip(_translate("mgeoWindow", "Enable\\disable export custom attributes", None))
        self.customGeoAttr_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\">Create </span><span style=\" font-family:\'sans-serif\'; font-size:8pt; text-decoration: underline; color:#000000; background-color:#ffffff;\">primitive</span><span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\"> attributes from object (shape, transform). </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\">Separate your attribute names with space.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\">Supported types: </span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'sans-serif\'; font-size:8pt; color:#000000;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">bool (int)</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">int</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">float</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">vector2</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">vector3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">vector4</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\">Default = 0</span></p></body></html>", None))
        self.primGroups_gb.setTitle(_translate("mgeoWindow", "Groups", None))
        self.byMtl_cb.setToolTip(_translate("mgeoWindow", "Create primitive group by assigned material. \n"
"<prefix><matName>", None))
        self.byMtl_cb.setText(_translate("mgeoWindow", "Material", None))
        self.byMtl_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Material name filter</span></p></body></html>", None))
        self.byPar_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Create primitive group by parent.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;parentNodeName&gt; </span></p></body></html>", None))
        self.byPar_cb.setText(_translate("mgeoWindow", "Parent", None))
        self.byPar_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Parent group filter.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"result_box\"></a><span style=\" font-size:8pt;\">T</span><span style=\" font-size:8pt;\">o use a specific node, use the prefix in naming</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;findPrefix&gt;&lt;name&gt; </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"result_box\"></a><span style=\" font-size:8pt;\">I</span><span style=\" font-size:8pt;\">f the prefix is empty, use the closest parent.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">If the prefix is not found, use default group name &lt;prefis&gt;&quot;noParent&quot;</span></p></body></html>", None))
        self.displayer_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Groups by display layers</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;layerName&gt;</span></p></body></html>", None))
        self.displayer_cb.setText(_translate("mgeoWindow", "Display layer", None))
        self.byLayer_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Display layer name filter</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">If the prefix is not found, use default group name &lt;prefis&gt;&quot;deflayer&quot;</span></p></body></html>", None))
        self.label_3.setText(_translate("mgeoWindow", "Prim groups by:", None))
        self.label_4.setText(_translate("mgeoWindow", "Filter:", None))
        self.byMtlPref_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Material group prefix</span></p></body></html>", None))
        self.byMtlPref_le.setText(_translate("mgeoWindow", "MTL_", None))
        self.byParPref_le.setToolTip(_translate("mgeoWindow", "Parent group prefix", None))
        self.byParPref_le.setText(_translate("mgeoWindow", "PRNT_", None))
        self.byLayerPref_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Display layer group prefix</span></p></body></html>", None))
        self.byLayerPref_le.setText(_translate("mgeoWindow", "LAYER_", None))
        self.label_5.setText(_translate("mgeoWindow", "Prefix:", None))
        self.byObj_cb.setToolTip(_translate("mgeoWindow", "Create primitive group by object name. \n"
"<prefix><nodeName>", None))
        self.byObj_cb.setText(_translate("mgeoWindow", "Object name", None))
        self.byObjPref_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Object group prefix</span></p></body></html>", None))
        self.byObjPref_le.setText(_translate("mgeoWindow", "OBJ_", None))
        self.byObj_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Object name filter</span></p></body></html>", None))
        self.byShape_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Create primitive group by shape name. </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;nodeName&gt;</span></p></body></html>", None))
        self.byShape_cb.setText(_translate("mgeoWindow", "Shape name", None))
        self.bySpahePref_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Shape group prefix</span></p></body></html>", None))
        self.bySpahePref_le.setText(_translate("mgeoWindow", "SHAPE_", None))
        self.byShape_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Shape name filter</span></p></body></html>", None))
        self.mainTab.setTabText(self.mainTab.indexOf(self.tab), _translate("mgeoWindow", "Polygons", None))
        self.curveGroupEnable_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Enable/disable global Curve group</span></p></body></html>", None))
        self.curveGroupEnable_cb.setText(_translate("mgeoWindow", "Curves Group:", None))
        self.expCurvesGlobalGroupName_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Main curves group</span></p></body></html>", None))
        self.expCurvesGlobalGroupName_le.setText(_translate("mgeoWindow", "CURV", None))
        self.curvToNURBS_rb.setToolTip(_translate("mgeoWindow", "Export as NURBS", None))
        self.curvToNURBS_rb.setText(_translate("mgeoWindow", "NURBS", None))
        self.curvToPoly_rb.setToolTip(_translate("mgeoWindow", "Export as Poly line", None))
        self.curvToPoly_rb.setText(_translate("mgeoWindow", "Polyline", None))
        self.groupBox_6.setTitle(_translate("mgeoWindow", "Groups", None))
        self.byCurvObj_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Object name filter</span></p></body></html>", None))
        self.byCrvObj_cb.setToolTip(_translate("mgeoWindow", "Create primitive group by object name. \n"
"<prefix><nodeName>", None))
        self.byCrvObj_cb.setText(_translate("mgeoWindow", "Object name", None))
        self.label_9.setText(_translate("mgeoWindow", "Group by:", None))
        self.label_10.setText(_translate("mgeoWindow", "Filter:", None))
        self.byCrvPar_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Create primitive group by parent name. </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;nodeName&gt;</span></p></body></html>", None))
        self.byCrvPar_cb.setText(_translate("mgeoWindow", "Parent", None))
        self.byCurvPar_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Parent group filter.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"result_box\"></a><span style=\" font-size:8pt;\">T</span><span style=\" font-size:8pt;\">o use a specific node, use the prefix in naming</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;findPrefix&gt;&lt;name&gt; </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"result_box\"></a><span style=\" font-size:8pt;\">I</span><span style=\" font-size:8pt;\">f the prefix is empty, use the closest parent.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">If the prefix is not found, use default group name &lt;prefis&gt;&quot;noParent&quot;</span></p></body></html>", None))
        self.curvDisplayer_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Create primitive group by layer name. </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;layerName&gt;</span></p></body></html>", None))
        self.curvDisplayer_cb.setText(_translate("mgeoWindow", "Display layer", None))
        self.byCurvLayer_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Display layer name filter</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">If the prefix is not found, use default group name &lt;prefis&gt;&quot;deflayer&quot;</span></p></body></html>", None))
        self.byCurvObjPref_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Object group prefix</span></p></body></html>", None))
        self.byCurvObjPref_le.setText(_translate("mgeoWindow", "OBJ_", None))
        self.byCurvParPref_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Parent group prefix</span></p></body></html>", None))
        self.byCurvParPref_le.setText(_translate("mgeoWindow", "PAR_", None))
        self.byCurvLayerPref_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Display layer group prefix</span></p></body></html>", None))
        self.byCurvLayerPref_le.setText(_translate("mgeoWindow", "LAYER_", None))
        self.label_11.setText(_translate("mgeoWindow", "Prefix:", None))
        self.mainTab.setTabText(self.mainTab.indexOf(self.tab_4), _translate("mgeoWindow", "Curves", None))
        self.partGroupEnable_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Enable/disable global Particles group</span></p></body></html>", None))
        self.partGroupEnable_cb.setText(_translate("mgeoWindow", "Particles Group:", None))
        self.expParticlesGlobalGroupName_le.setToolTip(_translate("mgeoWindow", "Main particles group name", None))
        self.expParticlesGlobalGroupName_le.setText(_translate("mgeoWindow", "PART", None))
        self.groupBox_4.setTitle(_translate("mgeoWindow", "Particle  attributes", None))
        self.customAttr_cb.setToolTip(_translate("mgeoWindow", "Enable\\ disable export custom attributes", None))
        self.customAttr_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Export custom attrubutes from shape, transform or particles (per particle attributes)</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Names must be separated by a space. </span><span style=\" font-size:8pt;\">In brackets, you can specify a default value.</span><span style=\" font-size:8pt;\"> </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:600;\">Example: </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">float - </span><span style=\" font-size:8pt; font-style:italic;\">raduisPP(1)</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">vector - </span><span style=\" font-size:8pt; font-style:italic;\">rgbPP(1)</span><span style=\" font-size:8pt;\"> </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Value  will be automatically converted into a vector if need.</span></p></body></html>", None))
        self.groupBox_3.setTitle(_translate("mgeoWindow", "Groups", None))
        self.byPartObj_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Create point groups by objects name (particle system)</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;nodeName&gt;</span></p></body></html>", None))
        self.byPartObj_cb.setText(_translate("mgeoWindow", "Object name", None))
        self.byEmit_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Create point groups by emitter name</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;nodeName&gt;</span></p></body></html>", None))
        self.byEmit_cb.setText(_translate("mgeoWindow", "Emitter", None))
        self.label_12.setText(_translate("mgeoWindow", "Group by:", None))
        self.byPartObj_le.setToolTip(_translate("mgeoWindow", "Object name filter", None))
        self.label_14.setText(_translate("mgeoWindow", "Filter:", None))
        self.byEmit_le.setToolTip(_translate("mgeoWindow", "Emitter name filter", None))
        self.byPartObjPref_le.setToolTip(_translate("mgeoWindow", "Object group prefix", None))
        self.byPartObjPref_le.setText(_translate("mgeoWindow", "OBJ_", None))
        self.byEmitPref_le.setToolTip(_translate("mgeoWindow", "Emitter group prefix", None))
        self.byEmitPref_le.setText(_translate("mgeoWindow", "EMITTER_", None))
        self.label_13.setText(_translate("mgeoWindow", "Prefix:", None))
        self.mainTab.setTabText(self.mainTab.indexOf(self.tab_2), _translate("mgeoWindow", "Particles", None))
        self.expPivotsGlobalGroupName_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Main pivots group name</span></p></body></html>", None))
        self.expPivotsGlobalGroupName_le.setText(_translate("mgeoWindow", "PIVOT", None))
        self.label_22.setText(_translate("mgeoWindow", "Object filter", None))
        self.pivotFilter_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Filter objects by name</span></p></body></html>", None))
        self.pivSkipTransform_cb.setToolTip(_translate("mgeoWindow", "Do not export transfom nodes without shape", None))
        self.pivSkipTransform_cb.setText(_translate("mgeoWindow", "Skip transform without shape", None))
        self.pivotGroupEnable_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Enable/disable global Pivot group</span></p></body></html>", None))
        self.pivotGroupEnable_cb.setText(_translate("mgeoWindow", "Pivots Group:", None))
        self.pivotAttr_gb.setTitle(_translate("mgeoWindow", "Object Attributes", None))
        self.exportOrient_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Export rotate as point attribute.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">attrib: </span><span style=\" font-size:8pt; font-weight:600;\">orient</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">type: vector4 (Quaternion)</span></p></body></html>", None))
        self.exportOrient_cb.setText(_translate("mgeoWindow", "Orient", None))
        self.scale_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Export scale as point attribute.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">attrib: </span><span style=\" font-size:8pt; font-weight:600;\">scale</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">type: vector3</span></p></body></html>", None))
        self.scale_cb.setText(_translate("mgeoWindow", "Scale", None))
        self.customPivotAttr_cb.setToolTip(_translate("mgeoWindow", "Enable\\disable export custom attributes", None))
        self.customPivotAttr_le.setToolTip(_translate("mgeoWindow", "<html>\n"
"    <head>\n"
"        <title>HTML Online Editor Sample</title>\n"
"    </head>\n"
"    <body>\n"
"        <p>\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\">Create </span><span style=\" font-family:\'sans-serif\'; font-size:8pt; text-decoration: underline; color:#000000; background-color:#ffffff;\">point</span><span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\"> attributes from object (shape, transform). </span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\">Separate your attribute names with space.</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\">Supported types: </span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">bool (int)</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">int</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">float</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">vector2</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">vector3</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">vector4</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\">Default = 0</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'MS Shell Dlg 2\'; font-size:8pt;\">In brackets, you can specify a default value</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; color:#000000; background-color:#ffffff;\">Example:</span></p>\n"
"        <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">\n"
"            <span style=\" font-family:\'sans-serif\'; font-size:8pt; font-style:italic; color:#000000; background-color:#ffffff;\">myAttr(1)</span></p></body>\n"
"</html>", None))
        self.groupBox_9.setTitle(_translate("mgeoWindow", "Groups", None))
        self.expPivotObj_le.setToolTip(_translate("mgeoWindow", "Object name filter", None))
        self.expPivotParent_le.setToolTip(_translate("mgeoWindow", "Parent name filter", None))
        self.expPivotShape_le.setToolTip(_translate("mgeoWindow", "Shape name filter", None))
        self.label_17.setText(_translate("mgeoWindow", "Group by:", None))
        self.label_18.setText(_translate("mgeoWindow", "Filter:", None))
        self.expPivotObj_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Create point groups by object name</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;nodeName&gt;</span></p></body></html>", None))
        self.expPivotObj_cb.setText(_translate("mgeoWindow", "Object name", None))
        self.expPivotShape_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Create point groups by shape name</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;nodeName&gt;</span></p></body></html>", None))
        self.expPivotShape_cb.setText(_translate("mgeoWindow", "Shape name", None))
        self.expPivotParent_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Create point groups by parent name</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;nodeName&gt;</span></p></body></html>", None))
        self.expPivotParent_cb.setText(_translate("mgeoWindow", "Parent", None))
        self.expPivotObjPref_le.setToolTip(_translate("mgeoWindow", "Object group prefix", None))
        self.expPivotObjPref_le.setText(_translate("mgeoWindow", "OBJ_", None))
        self.expPivotShapePref_le.setToolTip(_translate("mgeoWindow", "Shape group prefix", None))
        self.expPivotShapePref_le.setText(_translate("mgeoWindow", "INSTATCE_", None))
        self.expPivotParentPref_le.setToolTip(_translate("mgeoWindow", "Parent group prefix", None))
        self.expPivotParentPref_le.setText(_translate("mgeoWindow", "PAR_", None))
        self.label_19.setText(_translate("mgeoWindow", "Prefix:", None))
        self.expPivotLayer_cb.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Groups by display layers</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">&lt;prefix&gt;&lt;layerName&gt;</span></p></body></html>", None))
        self.expPivotLayer_cb.setText(_translate("mgeoWindow", "Display layer", None))
        self.expPivotLayerPref_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Display layer group prefix</span></p></body></html>", None))
        self.expPivotLayerPref_le.setText(_translate("mgeoWindow", "LAYER_", None))
        self.expPivotlayer_le.setToolTip(_translate("mgeoWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Display layer name filter</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">If the prefix is not found, use default group name &lt;prefis&gt;&quot;deflayer&quot;</span></p></body></html>", None))
        self.mainTab.setTabText(self.mainTab.indexOf(self.tab_3), _translate("mgeoWindow", "Pivots", None))
        self.menuHelp.setTitle(_translate("mgeoWindow", "Help", None))
        self.menuMenu.setTitle(_translate("mgeoWindow", "Menu", None))
        self.help_act.setText(_translate("mgeoWindow", "Help", None))
        self.about_act.setText(_translate("mgeoWindow", "About", None))
        self.resetAll_act.setText(_translate("mgeoWindow", "Reset All", None))
        self.options_act.setText(_translate("mgeoWindow", "Options...", None))
        self.default_act.setText(_translate("mgeoWindow", "Default", None))
        self.saveDefault_act.setText(_translate("mgeoWindow", "Save as default", None))
        self.extReport_act.setText(_translate("mgeoWindow", "Extended report", None))
        self.save_act.setText(_translate("mgeoWindow", "Save settings...", None))
        self.load_act.setText(_translate("mgeoWindow", "Load settinds...", None))
        self.isolateExported_act.setText(_translate("mgeoWindow", "Isolate exported", None))
        self.colorInd_act.setText(_translate("mgeoWindow", "Color indicators", None))
        self.showWarnings_act.setText(_translate("mgeoWindow", "Show Warnings", None))

