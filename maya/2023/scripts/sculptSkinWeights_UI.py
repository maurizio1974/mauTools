import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om2
import maya.OpenMaya as om
import re

try:
  from PySide2.QtCore import *
  from PySide2.QtGui import *
  from PySide2.QtWidgets import *
  from PySide2 import __version__
  from shiboken2 import wrapInstance
except ImportError:
  from PySide.QtCore import *
  from PySide.QtGui import *
  from PySide import __version__
  from shiboken import wrapInstance

class LockCheckBox(QPushButton):
    def __init__(self, *args, **kwargs):#initialize function
        super(LockCheckBox, self).__init__(*args, **kwargs)
        self.parentTree = None
        self.setText("")

    def lockFromClick(self):
        self.lockInfluence()
        # Make sure the other selected influences in the influenceTree
        # are assigned the same locking status
        for influenceItem in self.parentTree.selectedItems():
            selectedLockCheckBox = self.parentTree.itemWidget(influenceItem, 1)
            selectedLockCheckBox.setChecked(self.isChecked())
            selectedLockCheckBox.lockInfluence()

    def lockInfluence(self):
        src =  cmds.connectionInfo(self.lockAttr, sfd = True)
        if self.isChecked():
            if src:
                cmds.setAttr(src, 1)
            else:
                cmds.setAttr(self.lockAttr, 1)
        else:
            if src:
                cmds.setAttr(src, 0)
            else:
                cmds.setAttr(self.lockAttr, 0)

class SculptSkinWeightsUI(QWidget):# Create a class that inherits from the QWidget class
    def __init__(self, *args, **kwargs):#initialize function
        super(SculptSkinWeightsUI, self).__init__(*args, **kwargs)
        # Check to see if the plugin is loaded
        if not cmds.contextInfo('weightSculptContext1', exists = True):
            cmds.warning('The UI could not launch because the weightSculpt plugin is not loaded')
            return

        # Define any important variables
        self.activeInfluence = ''
        self.influenceTree = None
        self.hierarchy_tree = {}
        self.sculptContext = ''
        self.nonDagInfluences = []
        self.pinningActive = False
        self.pinnedInfluences = []
        self.selectedNames = []

        # Get the main window as a widget
        omui.MQtUtil.mainWindow()
        ptr = omui.MQtUtil.mainWindow()
        mainWindow_widget = wrapInstance(int(ptr), QWidget)
        self.mainWindow_widget = mainWindow_widget
        # Parent widget under Maya main window
        self.setParent(mainWindow_widget)
        self.setWindowFlags(Qt.Window)
        self.setObjectName('sculptSkinWeightsUI')
        # Delete the UI if an instance already exists
        try:
            child_windows = mainWindow_widget.findChildren(QWidget)
            for widget in child_windows:
                if widget is not self:
                    if widget.objectName() == self.objectName():
                        widget.close()
                        widget.deleteLater()

        except:
            pass

        # Set the object name, window title, and window size
        self.setWindowTitle('Sculpt Skin Weights')
        self.setGeometry(50, 50, 250, 150)
        # Create the main layout
        self.window_layout = QVBoxLayout()
        self.setLayout(self.window_layout)
        self.initUI()

    def initUI(self):
        # Create a button that reloads the influence list
        self.reloadButton = QPushButton("Refresh Influence List")
        self.reloadButton.clicked.connect(self.reloadDataFromScene)
        self.reloadButton.setToolTip('Updates the UI to ensure the info displayed matches the info in the default Maya tool')
        self.window_layout.addWidget(self.reloadButton)

        # Create a groupBox to hold radioButtons that control how the influences are oranized
        self.sortButtonGroupBox = QGroupBox()
        self.sortButtonLayout = QHBoxLayout()
        self.sortButtonGroupBox.setLayout(self.sortButtonLayout)

        sortLabel = QLabel("Sort:")
        self.alphaSortButton = QRadioButton("Alphabetically")
        self.hierarchySortButton = QRadioButton("By Heierarchy")
        self.flatSortButton = QRadioButton("Flat")
        self.hierarchySortButton.setChecked(1)

        self.alphaSortButton.clicked.connect(self.updateInfluenceTree)
        self.hierarchySortButton.clicked.connect(self.updateInfluenceTree)
        self.flatSortButton.clicked.connect(self.updateInfluenceTree)

        self.sortButtonLayout.addWidget(sortLabel)
        self.sortButtonLayout.addWidget(self.alphaSortButton)
        self.sortButtonLayout.addWidget(self.hierarchySortButton)
        self.sortButtonLayout.addWidget(self.flatSortButton)
        self.window_layout.addWidget(self.sortButtonGroupBox)

        # Add a search list and a pin button
        self.searchLayout = QHBoxLayout()
        self.window_layout.addLayout(self.searchLayout)

        self.influenceSearchField = QLineEdit()
        self.searchLayout.addWidget(self.influenceSearchField)
        self.influenceSearchField.textChanged.connect(self.updateInfluenceTree)
        self.influenceSearchField.setToolTip('A search bar to filter the list of influences you can use * as wildcard character.')

        self.pinSelectionButton = QPushButton("PIN")
        self.searchLayout.addWidget(self.pinSelectionButton)
        self.pinSelectionButton.setCheckable(True)
        self.pinSelectionButton.setToolTip('Will hide all the influences in the UI except the ones you have selected.')
        self.pinSelectionButton.clicked.connect(self.pinSelection)

        # Add a checkbox to toggle case-sensitive search
        self.caseSensitiveCheckBox = QCheckBox("Case-Sensitive:")
        self.window_layout.addWidget(self.caseSensitiveCheckBox)
        self.influenceSearchField.setToolTip('If it is off the search bar filtering will ignore capitalization.')
        self.caseSensitiveCheckBox.stateChanged.connect(self.updateInfluenceTree)

        # Create a QTreeWidget
        # Where one columb is the list of influences
        # And another column shows if they are locked
        self.influenceTree = QTreeWidget()
        #self.influenceTree.setStyleSheet("QTreeView::item:selected {background : blue;} QTreeView::item:active {background : red;}");

        self.influenceTree.setHeaderHidden(True)
        self.influenceTree.setColumnCount(2)
        self.influenceTree.setColumnWidth(1,25)
        self.influenceTree.header().setSectionResizeMode(0,QHeaderView.Stretch)
        self.influenceTree.header().setSectionResizeMode(1,QHeaderView.Fixed)
        self.influenceTree.header().setStretchLastSection(0)
        self.influenceTree.setRootIsDecorated(True)
        self.influenceTree.itemSelectionChanged.connect(self.updateActiveInfluence)
        self.influenceTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.window_layout.addWidget(self.influenceTree)

        # Add a display for the currently active influence
        self.activeInfluenceLabel = QLabel("Active Influence:")
        self.activeInfluenceLabel.setToolTip('The influnece you are modifying the weights of.')
        self.window_layout.addWidget(self.activeInfluenceLabel)

        self.scrollToActiveButton = QPushButton("Scroll To Active Influence")
        self.scrollToActiveButton.setToolTip('Scrolls to the influence you are painting on.')
        self.window_layout.addWidget(self.scrollToActiveButton)
        self.scrollToActiveButton.clicked.connect(self.scrollToActive)

        # Add some additional buttons
        self.selectFromSceneButton = QPushButton("Select From Viewport")
        self.selectFromSceneButton.setToolTip('Selects the influences in the UI that you have selected in the viewport.')
        self.window_layout.addWidget(self.selectFromSceneButton)
        self.selectFromSceneButton.clicked.connect(self.selectFromScene)

        self.selectFromComponentsButton = QPushButton("Select Influences From Components")
        self.selectFromComponentsButton.setToolTip('Selects the influences that affect the selected components.')
        self.window_layout.addWidget(self.selectFromComponentsButton)
        self.selectFromComponentsButton.clicked.connect(self.selectFromComponents)

        self.launchToolButton = QPushButton("Launch Tool")
        self.launchToolButton.setToolTip('Launches the sculptWeights tool.')
        self.window_layout.addWidget(self.launchToolButton)
        self.launchToolButton.clicked.connect(self.launchTool)

        self.reloadDataFromScene()

    def getActiveSkincluster(self):
        # Get the selection
        sels = cmds.ls(sl = True)
        # Get the skinCluster
        self.activeSkinCluster = None
        for sel in sels:
            sel = sel.split('.')[0]
            thisSkinCluster = mel.eval('findRelatedSkinCluster "{}"'.format(sel))
            if thisSkinCluster:
                self.activeSkinCluster = thisSkinCluster
                break

    def reloadDataFromScene(self):
        self.updateSkinClusterData()
        self.updateWeightSculptData()
        # Set the selection based on the current influence
        if self.activeInfluence:
                self.selectedNames = [cmds.ls(self.activeInfluence, l = True)[0]]

        self.updateInfluenceTree()

    def updateWeightSculptData(self):
        # Get the latest weightSculptContext
        i = 1
        while cmds.contextInfo('weightSculptContext{}'.format(i), exists = True):
            i += 1

        if i == 1:
            self.sculptContext = ''
        else:
            self.sculptContext = 'weightSculptContext{}'.format(i-1)

        # Get the active influence from the context
        currentInfluence = cmds.weightSculptContext(self.sculptContext, q = True, inf = True)
        if currentInfluence:
            if cmds.objExists(currentInfluence):
                self.activeInfluence = currentInfluence
                self.activeInfluenceLabel.setText("Active Influence: {}".format(cmds.ls(self.activeInfluence)[0]))
                return

        self.activeInfluence = ''
        self.activeInfluenceLabel.setText("Active Influence: {}".format(self.activeInfluence))

    def launchTool(self):
        cmds.setToolTo(self.sculptContext)

    def updateSkinClusterData(self):
        # Get the skinCluster from the selection
        self.getActiveSkincluster()
        if not self.activeSkinCluster:
            return

        # Get the hierarchy as a dictionary
        self.getHierarchyDict()

    def updateInfluenceTree(self):
        self.influenceTree.itemSelectionChanged.disconnect(self.updateActiveInfluence)
        self.populateInfluenceTree()
        self.influenceTree.itemSelectionChanged.connect(self.updateActiveInfluence)

    def populateInfluenceTree(self):
        # Clear the contents of treeWidget
        self.influenceTree.clear()

        if not self.activeSkinCluster:
            return

        if not self.sculptContext:
            return

        if not cmds.objExists(self.activeSkinCluster):
            return

        # Get the searchField contents
        entry_string = self.influenceSearchField.text()
        if not self.caseSensitiveCheckBox.isChecked():
            entry_string = entry_string.lower()

        regex_string = entry_string.replace('*','.*')
        filterNames = False
        try:
            re.compile(regex_string)
            filterNames = True
        except:
            return
        
        if self.hierarchySortButton.isChecked():
            # Iterate through the dictionary creating the treeWidgetItems
            def addItemHierarchy(fullName, hTree, parentWidget):
                # Get the shortest unique name to display in the UI
                shortestUniqueName = cmds.ls(fullName)[0]
                influence = shortestUniqueName
                if not self.caseSensitiveCheckBox.isChecked():
                    influenceFilter = influence.lower()
                else:
                    influenceFilter = influence

                # Skip to the children if it is not pinned 
                if (self.pinningActive):
                    if influence not in self.pinnedInfluences:
                        # Skip to the children
                        for child in hTree[fullName]['children']:
                            addItemHierarchy(child, hTree[fullName]['children'],parentWidget)

                        return

                else:
                    # Check to see if it fits the naming scheme
                    if (filterNames):
                        if not re.search(regex_string,influenceFilter):
                            # Skip to the children
                            for child in hTree[fullName]['children']:
                                addItemHierarchy(child, hTree[fullName]['children'],parentWidget)

                            return

                # Get the associated attributes from the influenceAttrDict
                influenceAttrs = hTree[fullName]['attributes']
                destinationIndex = hTree[fullName]['destinationIndex'][0]
                influenceItem = None
                if len(influenceAttrs) == 1 and influenceAttrs[0] == 'worldMatrix':
                    influenceItem = self.addTreeItem(parentWidget,shortestUniqueName,destinationIndex)
                    if fullName in self.selectedNames:
                        influenceItem.setSelected(True)

                else:
                    cmds.warning('"{}" has more than one attribute as a driver on this skinCluster'.format(fullName))
                    cmds.warning('The sculptWeights tool is not able to handle that yet'.format(fullName))
                    return
                
                for child in hTree[fullName]['children']:
                    addItemHierarchy(child, hTree[fullName]['children'],influenceItem)

            for topLevelInfluence in self.hierarchy_tree.keys():
                addItemHierarchy(topLevelInfluence,self.hierarchy_tree,self.influenceTree)

        elif self.alphaSortButton.isChecked():
            # Iterate through self.tree_hierarchy creating a flattened list version of it
            flat_tree_hierarchy = []
            def iterateTreeHierarchy(fullName,hTree):
                # Get the short name because we will sort using it
                shortName = fullName.split('|')[-1]
                flat_tree_hierarchy.append(
                    [
                        fullName, shortName, 
                        {
                            'attributes':hTree[fullName]['attributes'],
                            'destinationIndex':hTree[fullName]['destinationIndex']
                        }
                    ]
                )

                for child in hTree[fullName]['children']:
                    iterateTreeHierarchy(child, hTree[fullName]['children'])

            for topLevelInfluence in self.hierarchy_tree.keys():
                iterateTreeHierarchy(topLevelInfluence,self.hierarchy_tree)

            # Sort the contents alphabetically based on the short name
            flat_tree_hierarchy = sorted(flat_tree_hierarchy, key = lambda x:x[1])

            for fullName, shortName, eachNodeData in flat_tree_hierarchy:
                # Get the shortest unique name to display in the UI
                influence = cmds.ls(fullName)[0]
                if not self.caseSensitiveCheckBox.isChecked():
                    influenceFilter = influence.lower()
                else:
                    influenceFilter = influence

                if (self.pinningActive):
                    # Check to see if the influence is pinned
                    if influence not in self.pinnedInfluences:
                        continue
                else:
                    # Check to see if it fits the naming scheme
                    if (filterNames):
                        if not re.search(regex_string,influenceFilter):
                            continue

                # Get the associated attributes from the influenceAttrDict
                influenceAttrs = eachNodeData['attributes']
                destinationIndex = eachNodeData['destinationIndex'][0]
                influenceItem = None
                if len(influenceAttrs) == 1 and influenceAttrs[0] == 'worldMatrix':
                    influenceItem = self.addTreeItem(self.influenceTree,influence,destinationIndex)
                    if fullName in self.selectedNames:
                        influenceItem.setSelected(True)
                else:
                    cmds.warning('"{}" has more than one attribute as a driver on this skinCluster'.format(fullName))
                    cmds.warning('The sculptWeights tool is not able to handle that yet'.format(fullName))

        else:
            # Iterate through the dictionary creating the treeWidgetItems
            def addItemFlat(fullName, hTree, parentWidget):
                # Get the shortest unique name to display in the UI
                shortestUniqueName = cmds.ls(fullName)[0]
                influence = shortestUniqueName
                if not self.caseSensitiveCheckBox.isChecked():
                    influenceFilter = influence.lower()
                else:
                    influenceFilter = influence

                # Get the associated attributes from the influenceAttrDict
                influenceAttrs = hTree[fullName]['attributes']
                destinationIndex = hTree[fullName]['destinationIndex'][0]
                influenceItem = None
                if len(influenceAttrs) == 1 and influenceAttrs[0] == 'worldMatrix':
                    influenceItem = self.addTreeItem(parentWidget,shortestUniqueName,destinationIndex)
                    if fullName in self.selectedNames:
                        influenceItem.setSelected(True)
                else:
                    cmds.warning('"{}" has more than one attribute as a driver on this skinCluster'.format(fullName))
                    cmds.warning('The sculptWeights tool is not able to handle that yet'.format(fullName))
                    return
                
                for child in hTree[fullName]['children']:
                    if (self.pinningActive):
                        # Check if the influence is pinned
                        if influence not in self.pinnedInfluences:
                            continue
                    else:
                        # Check to see if it fits the naming scheme
                        if (filterNames):
                            if not re.search(regex_string,influenceFilter):
                                continue

                    addItemFlat(child, hTree[fullName]['children'],self.influenceTree)# Always influenceTree

            for topLevelInfluence in self.hierarchy_tree.keys():
                addItemFlat(topLevelInfluence,self.hierarchy_tree,self.influenceTree)

        # Add blendWeights if needed
        if cmds.getAttr(self.activeSkinCluster + '.skinningMethod') == 2:
            blendWeightsItem = QTreeWidgetItem(self.influenceTree,['blendWeights',''])  

    def addTreeItem(self,parentWidget,itemName,destinationIndex):
        influenceItem = QTreeWidgetItem(parentWidget,[itemName,''])  
        lockCheckBox = LockCheckBox(str(destinationIndex),self.influenceTree)
        lockCheckBox.parentTree = self.influenceTree
        lockCheckBox.setCheckable(True)
        lockCheckBox.setMaximumSize(25,18)
        lockCheckBox.setMinimumSize(25,18)
        self.influenceTree.setItemWidget(influenceItem,1,lockCheckBox)
        if type(parentWidget) == QTreeWidgetItem:
            parentWidget.setExpanded(True)

        # Lock the influence if you need to 
        lockAttr = self.activeSkinCluster + '.lockWeights[{}]'.format(destinationIndex)
        lockCheckBox.lockAttr = lockAttr
        lockCheckBox.clicked.connect(lockCheckBox.lockFromClick)

        if cmds.getAttr(lockAttr) == 1:
            lockCheckBox.setChecked(True)

        return influenceItem

    def updateActiveInfluence(self):
        # Get the selected item
        selectedItems = self.influenceTree.selectedItems()

        # Store the selected item names so we can restore them when needed
        selectedItems = self.influenceTree.selectedItems()
        self.selectedNames = [cmds.ls(x.text(0), l = True)[0] for x in selectedItems]

        # Check that the activeInfluence exists
        if not self.selectedNames:
            return

        self.activeInfluence = self.selectedNames[-1]
        if not cmds.objExists(self.activeInfluence) and self.activeInfluence != 'blendWeights':
            return

        # Use the context command to update it
        try:
            if self.activeInfluence == 'blendWeights':
                cmds.weightSculptContext(self.sculptContext, e = True, wtm = 'dualQuaternion')
            else:
                cmds.weightSculptContext(self.sculptContext, e = True, wtm = 'skinCluster', inf = self.activeInfluence)
            
            cmds.setToolTo(self.sculptContext)
        except:
            cmds.warning('The active influence could not be set')

        self.activeInfluence = cmds.weightSculptContext(self.sculptContext, q = True, inf = True)

        if not selectedItems:
            self.activeInfluence = ''
            self.activeInfluenceLabel.setText("Active Influence: {}".format(''))
        else:
            self.activeInfluence = selectedItems[-1].text(0)
            self.activeInfluenceLabel.setText("Active Influence: {}".format(cmds.ls(self.activeInfluence)[0]))

    def pinSelection(self):
        self.pinnedInfluences = []

        if self.pinSelectionButton.isChecked():
            for eachItem in self.influenceTree.selectedItems():
                self.pinnedInfluences.append(eachItem.text(0))
                self.pinningActive = True
        else:
            self.pinningActive = False

        self.updateInfluenceTree()

    def getHierarchyDict(self):
        # Get the attribut and destinationIndex for each 
        # to the skinCluster. We can fill out the attribute and destination index
        connections = cmds.listConnections(self.activeSkinCluster + '.matrix', c = True, p = True, s = True, d = False)
        destinations = connections[::2]
        sources = connections[1::2]
        self.attributeDataDict = {}
        for s, d in zip(sources,destinations):
            # Get the node
            sourceNode = s.split('.')[0]
            sourceNode = cmds.ls(sourceNode, l = True)[0]
            # Get the destination index
            destinationIndex = int(d.split('[')[-1][:-1])
            # Get the attr
            sourceAttr = '.'.join(s.split('.')[1:])
            # Add the data to the hierarchy_tree
            if sourceNode not in self.attributeDataDict:
                self.attributeDataDict[sourceNode] = {
                    "destinationIndex":[],
                    "attributes":[]
                }

            self.attributeDataDict[sourceNode]["destinationIndex"].append(destinationIndex)
            self.attributeDataDict[sourceNode]["attributes"].append(sourceAttr)

        # Get the full name of all the DAG sources
        sourceDAGs = cmds.listConnections(self.activeSkinCluster + '.matrix', type = 'dagNode', s = True, d = False)
        sourceDAGs = [cmds.ls(x, l = True)[0] for x in sourceDAGs]
        sourceDAGs = set(sourceDAGs)

        def traverseHierarchy(currentNode, tree):
            # Get the list of children
            children = cmds.listRelatives(currentNode, c=True, f = True, type = 'dagNode')
            
            if currentNode in sourceDAGs:
                # If the current node is an influence
                # Then add it to the dictionary
                # The child dictionary will be empty to start
                tree[currentNode] = {
                    "children":{},
                    "destinationIndex": self.attributeDataDict[currentNode]["destinationIndex"],
                    "attributes": self.attributeDataDict[currentNode]["attributes"]
                }
                
                # Do the same checks on each of this objects children
                # Adding them to the dictionary that is the value 
                # For their parent (the current object)
                if children:
                    for child in children:
                        traverseHierarchy(child, tree[currentNode]["children"])

            else:
                if children:
                    for child in children:
                        traverseHierarchy(child, tree)

        # Loop through the hierarchy under each top level DAG node
        # This wil produce a dictionary with all the parent-child info
        # This dictionary will not contain any other data though
        self.hierarchy_tree = {}
        for top_node in cmds.ls(assemblies=True, l = True):
            traverseHierarchy(top_node, self.hierarchy_tree)

        # Loop through all the source nodes that are not DAG nodes
        # And add them to the dictionary
        sourceDGs = cmds.listConnections(self.activeSkinCluster + '.matrix', s = True, d = False)
        sourceDGs = [x for x in sourceDGs if 'dagNode' not in cmds.nodeType(x, i = True)]
        sourceDGs = [x.split('.')[0] for x in sourceDGs]
        sourceDGs = [cmds.ls(x, l = True)[0] for x in sourceDGs]
        sourceDGs = set(sourceDGs)

        for sourceDG in sourceDGs:
            self.hierarchy_tree[sourceDG] = {
                "children":{},
                "destinationIndex": self.attributeDataDict[sourceDG]["destinationIndex"],
                "attributes": self.attributeDataDict[sourceDG]["attributes"]
            }

    def selectFromScene(self):
        # Get the scen selection
        sceneSel = cmds.ls(sl = True, type = 'joint')
        # Get the shortest unique name
        sceneSel = [cmds.ls(x)[0] for x in sceneSel]
        
        # Loop through all the items in the influence tree
        # And select them if they are in the sceneSel
        def checkChildren(influenceItem):
            # If it is is in the sceneSel then select it 
            if influenceItem.text(0) in sceneSel:
                influenceItem.setSelected(True)
            else:
                influenceItem.setSelected(False)

            # Loop through the children
            for i in range(influenceItem.childCount()):
                checkChildren(influenceItem.child(i))

        for i in range(self.influenceTree.topLevelItemCount()):
            checkChildren(self.influenceTree.topLevelItem(i))

    def selectFromComponents(self):
        sceneSel = []
        for comp in cmds.ls(sl = True, fl = True):
            componentInfluences = cmds.skinPercent(self.activeSkinCluster,comp, query = True, transform = None)
            componentWeights = cmds.skinPercent(self.activeSkinCluster,comp, query = True, value = True)

            for weight,influence in zip(componentWeights,componentInfluences):
                if weight > .001:
                    sceneSel.append(influence)

        # Loop through all the items in the influence tree
        # And select them if they are in the sceneSel
        def checkChildren(influenceItem):
            # If it is is in the sceneSel then select it 
            if influenceItem.text(0) in sceneSel:
                influenceItem.setSelected(True)
            else:
                influenceItem.setSelected(False)

            # Loop through the children
            for i in range(influenceItem.childCount()):
                checkChildren(influenceItem.child(i))

        for i in range(self.influenceTree.topLevelItemCount()):
            checkChildren(self.influenceTree.topLevelItem(i))

        self.scrollToActive()

    def scrollToActive(self):
        print self.activeInfluence
        shortName = cmds.ls(self.activeInfluence)[0]
        activeInfluenceItem =  self.influenceTree.findItems(shortName, Qt.MatchRecursive)
        if activeInfluenceItem:
            activeInfluenceItem = activeInfluenceItem[0]

            self.influenceTree.scrollTo(
                self.influenceTree.indexFromItem(activeInfluenceItem)
            );

    def show(self):
        super(SculptSkinWeightsUI, self).show()
        self.move(self.mainWindow_widget.geometry().center() - self.rect().center());