import os
import re
import hou
import json
import pyseq
import platform
from PySide2 import QtGui
from PySide2 import QtCore
from PySide2 import QtWidgets
from pprint import pprint


'''----------------------------------------------------------------------------------------------------
HOW TO USE

import fileSearcher
reload(fileSearcher)

----------------------------------------------------------------------------------------------------'''


class Window(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(Window, self).__init__()
        self.layout = QtWidgets.QGridLayout()
        self.setObjectName("MainWindow")
        self.setWindowTitle('Global File Searcher')
        self.resize(500, 500)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: #333333; color: lightGray;")
        # LOCATIONS
        self.icons = os.path.join(
            os.getenv('mt_B'), 'houdini',
            os.getenv('HOUDINI_VERSION'),
            os.getenv('mt_V'), 'icons')
        self.loc = os.path.join(
            os.getenv('mt_B'), 'houdini',
            os.getenv('HOUDINI_VERSION'), os.getenv('mt_V'))
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.home()


    def home(self):
        job, jobs = '', self.get_jobs()
        if jobs:
            job = jobs[0]
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")

        self.label = QtWidgets.QLabel(self.centralwidget)

        self.label.setPixmap(QtGui.QPixmap(os.path.join(self.icons, 'fileSearcher_debug.png')))
        self.label.setScaledContents(True)
        self.gridLayout.addWidget(self.label, 0, 0, 1, 5)

        self.jobSRC = QtWidgets.QComboBox(self.centralwidget)
        self.jobSRC.setObjectName("jobSRC")
        self.gridLayout.addWidget(self.jobSRC, 1, 0, 1, 1)

        for j in jobs:
            self.jobSRC.addItem(j)

        self.discSRC = QtWidgets.QComboBox(self.centralwidget)
        self.discSRC.setObjectName("discSRC")
        self.gridLayout.addWidget(self.discSRC, 1, 1, 1, 1)

        for t in ['build', 'shots']:
            self.discSRC.addItem(t)

        self.assSRC = QtWidgets.QComboBox(self.centralwidget)
        self.assSRC.setObjectName("assSRC")
        self.gridLayout.addWidget(self.assSRC, 1, 2, 1, 1)

        self.radioG = QtWidgets.QCheckBox('Search: Asset', self.centralwidget)
        self.radioG.setObjectName("radioG")
        self.gridLayout.addWidget(self.radioG, 1, 3, 1, 1)
        self.radioG.toggle()

        self.radioF = QtWidgets.QCheckBox('No dB Refresh', self.centralwidget)
        self.radioF.setObjectName("radioF")
        self.gridLayout.addWidget(self.radioF, 1, 4, 1, 1)

        self.searcherButt = QtWidgets.QPushButton('Search in Asset', self.centralwidget)
        self.searcherButt.setObjectName("searcherButt")
        self.gridLayout.addWidget(self.searcherButt, 4, 0, 1, 5)

        self.listResult = QtWidgets.QListWidget(self.centralwidget)
        self.listResult.setEnabled(True)
        self.gridLayout.addWidget(self.listResult, 5, 0, 1, 5)

        self.fixFButt = QtWidgets.QPushButton('Fix Found', self.centralwidget)
        self.fixFButt.setObjectName("fixFButt")
        self.gridLayout.addWidget(self.fixFButt, 6, 0, 1, 5)
        self.fixFButt.setEnabled(False)

        self.listResult2 = QtWidgets.QListWidget(self.centralwidget)
        self.listResult2.setEnabled(True)
        self.gridLayout.addWidget(self.listResult2, 7, 0, 1, 5)

        self.fixUButt = QtWidgets.QPushButton('Fix UnFound', self.centralwidget)
        self.fixUButt.setObjectName("fixUButt")
        self.gridLayout.addWidget(self.fixUButt, 8, 0, 1, 5)
        self.fixUButt.setEnabled(False)

        self.fixButt = QtWidgets.QPushButton('Fix Them All', self.centralwidget)
        self.fixButt.setObjectName("fixButt")
        self.gridLayout.addWidget(self.fixButt, 9, 0, 1, 5)
        self.fixButt.setEnabled(False)

        self.setCentralWidget(self.centralwidget)

        # Add Signals --------------------------------------------------------
        self.radioG.toggled.connect(self.switchSearchUI)
        self.radioF.toggled.connect(self.switchDBui)
        self.searcherButt.clicked.connect(self.matcher)
        self.listResult.itemClicked.connect(self.navigateItem)
        self.listResult.itemDoubleClicked.connect(self.fixFound)
        self.listResult2.itemClicked.connect(self.navigateItem)
        self.listResult2.itemDoubleClicked.connect(self.fixUnFound)
        self.jobSRC.activated[str].connect(self.addAss)
        self.discSRC.activated[str].connect(self.addAss)
        self.fixFButt.clicked.connect(self.fixBFound)
        self.fixUButt.clicked.connect(self.fixBUnFound)
        self.fixButt.clicked.connect(self.fixThemAll)

        # Show Windows
        self.show()
        # Make main job search directory config cache
        # self.cacher()

        # palette = self.listResult.palette()
        # bg_color = palette.color(self.listResult.backgroundRole())
        # print (bg_color)

        # Set Current Job from Houdini session
        job = self.unixify(os.getenv('PRJ')).split('/')[-1]
        index = self.jobSRC.findText(str(job), QtCore.Qt.MatchFixedString)
        self.jobSRC.setCurrentIndex(index)
        disc = self.unixify(os.getenv('WORK')).split('/')[-2]
        index = self.discSRC.findText(str(disc), QtCore.Qt.MatchFixedString)
        self.discSRC.setCurrentIndex(index)

        # REFRESH UI
        self.addAss()

        # ADD CURRENT ASSET
        ass = self.unixify(os.getenv('WORK')).split('/')[-1]
        index = self.assSRC.findText(str(ass), QtCore.Qt.MatchFixedString)
        self.assSRC.setCurrentIndex(index)

        # Make database for show and current asset
        refr = self.radioF.isChecked()
        if refr:
            self.dbRefresher()


    def dbRefresher(self):
        asset = self.assSRC.currentText()
        config = os.path.join(os.environ["PRJ"], 'config', 'databases', 'show_search_database.json')
        if self.radioG.isChecked():
            config = os.path.join(os.environ["PRJ"], 'config', 'databases', asset + '_search_database.json')
        self.cacher()


    def get_jobs(self):
        main = os.getenv('MJOBS')
        jobs = os.listdir(main)
        out = []
        if jobs:
            for j in jobs:
                if os.path.isdir(os.path.join(main, j)):
                    if '.' not in j:
                        out.append(j)
        return sorted(out)


    def addAss(self):
        current = ''
        main = os.getenv('MJOBS')
        # Get Active Session
        job = str(self.jobSRC.currentText())
        typ = str(self.discSRC.currentText())
        current = self.unixify(os.path.join(main, job, typ))
        self.assSRC.clear()
        if os.path.isdir(current):
            work = os.listdir(current)
            if work:
                for w in work:
                    self.assSRC.addItem(w)


    def switchDBui(self):
        current = str(self.radioF.text())
        if current == 'Auto dB Refresh':
            self.radioF.setText('No dB Refresh')
        else:
            self.radioF.setText('Auto dB Refresh')
            self.dbRefresher()


    def switchSearchUI(self):
        current = str(self.radioG.text())
        if current == 'Search: Show':
            self.radioG.setText('Search: Asset')
            self.discSRC.setEnabled(True)
            self.assSRC.setEnabled(True)
            self.searcherButt.setText('Search in Asset')
        else:
            self.radioG.setText('Search: Show')
            self.discSRC.setEnabled(False)
            self.assSRC.setEnabled(False)
            self.searcherButt.setText('Search in Show')
        refr = self.radioF.isChecked()
        if refr:
            self.dbRefresher()


    def unixify(self, file):
        out = file.replace('\\', '/')
        return out


    def navigateItem(self, item):
        hou.clearAllSelected()
        node = hou.node(item.text().split('[')[0])
        node.setSelected(True)
        # Navigate to the selected node in the network editor
        network_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        if network_editor:
            network_editor.setCurrentNode(node)
        else:
            hou.ui.displayMessage('NO Network View open , please open one')


    def fixFound(self):
        sel_item = self.listResult.selectedItems()
        cur = sel_item[0].text()
        name = cur.split('[')[0]
        attr = cur.split('[')[-1].split(']')[0]
        val = cur.split('>> ')[-1]
        node = hou.node(name)
        node.setParms({attr: val})

        # REMOVE FIXED ITEMS
        if sel_item:
            for item in sel_item:
                row = self.listResult.row(item)
                self.listResult.takeItem(row)

        # RESTORE COLOR IF EVERYTHING IS FIXED
        items = self.listResult.count()
        if items == 0:
            self.listResult.setStyleSheet("QListWidget { background-color: rgba(50, 50, 50, 100); }")
            self.fixFButt.setEnabled(False)


    def fixBFound(self):
        lines = []
        for index in range(self.listResult.count()):
            item = self.listResult.item(index)
            lines.append(item)
        for l in reversed(lines):
            cur = l.text()
            name = cur.split('[')[0]
            attr = cur.split('[')[-1].split(']')[0]
            val = cur.split('>> ')[-1]
            node = hou.node(name)
            node.setParms({attr: val})
            # REMOVE FIXED ITEMS
            row = self.listResult.row(l)
            self.listResult.takeItem(row)

        # RESTORE COLOR IF EVERYTHING IS FIXED
        items = self.listResult.count()
        if items == 0:
            self.listResult.setStyleSheet("QListWidget { background-color: rgba(50, 50, 50, 100); }")
            self.fixFButt.setEnabled(False)


    def fixUnFound(self):
        sel_item = self.listResult2.selectedItems()
        cur = sel_item[0].text()
        name = cur.split('[')[0]
        node = hou.node(name)
        node.bypass(1)

        if node.isBypassed():
            # REMOVE BYPASSED ITEMS
            if sel_item:
                for item in sel_item:
                    row = self.listResult2.row(item)
                    self.listResult2.takeItem(row)

        # RESTORE COLOR IF EVERYTHING IS BYPASSED
        items = self.listResult2.count()
        if items == 0:
            self.listResult2.setStyleSheet("QListWidget { background-color: rgba(50, 50, 50, 100); }")
            self.fixUButt.setEnabled(False)


    def fixBUnFound(self):
        lines = []
        for index in range(self.listResult2.count()):
            item = self.listResult2.item(index)
            lines.append(item)
        for l in reversed(lines):
            cur = l.text()
            name = cur.split('[')[0]
            attr = cur.split('[')[-1].split(']')[0]
            val = cur.split('>> ')[-1]
            node = hou.node(name)
            node.bypass(1)
            # REMOVE FIXED ITEMS
            row = self.listResult2.row(l)
            self.listResult2.takeItem(row)

        # RESTORE COLOR IF EVERYTHING IS FIXED
        items = self.listResult2.count()
        if items == 0:
            self.listResult2.setStyleSheet("QListWidget { background-color: rgba(50, 50, 50, 100); }")
            self.fixUButt.setEnabled(False)


    def fixThemAll(self):
        for tsl in [self.listResult, self.listResult2]:
            lines = []
            for index in range(tsl.count()):
                item = tsl.item(index)
                lines.append(item)
            for l in reversed(lines):
                cur = l.text()
                name = cur.split('[')[0]
                attr = cur.split('[')[-1].split(']')[0]
                val = cur.split('>> ')[-1]
                node = hou.node(name)
                if tsl == self.listResult:
                    node.setParms({attr: val})
                else:
                    node.bypass(1)
                # REMOVE FIXED ITEMS
                row = tsl.row(l)
                tsl.takeItem(row)

            # RESTORE COLOR IF EVERYTHING IS FIXED
            items = tsl.count()
            if items == 0:
                tsl.setStyleSheet("QListWidget { background-color: rgba(50, 50, 50, 100); }")
                self.fixFButt.setEnabled(False)
                self.fixUButt.setEnabled(False)
                self.fixButt.setEnabled(False)


    def searcher(self):
        out = {}
        # get all contexts
        contexts = hou.node('/').children()
        for c in contexts:
            # get all top level nodes in a context
            nodes = hou.node('/' + c.name()).children()
            for x, node in enumerate(nodes):
                # get all children of a node
                all_children = node.allSubChildren()
                if not all_children:
                    all_children = [node]
                    # continue
                info = {}
                for child in all_children:
                    # Continue making the list of assets to copy
                    attrs = child.parms()
                    if not attrs:
                        continue
                    vals = {}
                    for attr in attrs:
                        val = child.parm(attr.name()).eval()
                        if not 'str' in str(type(val)):
                            continue
                        if not val:
                            continue
                        val = self.unixify(val)
                        # Check if val is a path
                        if ':/' in val or val.startswith('/'):
                            # if not val.startswith('/obj'):
                            if not val.startswith('string'):
                                if '=' not in val:
                                    if not val[0].isdigit():
                                        # Check if the file exists with this path
                                        if not os.path.isfile(val):
                                            # Check if the result is a valid file
                                            checkV = val.split('/')[-1].split('.')
                                            if len(checkV) > 1 :
                                                vals[attr.name()] = val
                    if vals:
                        info[child] = vals
                if info:
                    out[node.name()] = info
        return out


    def matcher(self):
        # Clear UI
        self.listResult.clear()
        self.listResult2.clear()
        # Get data of current scene
        out = self.searcher()
        # READ SAVED DATA FROM SHOW CONFIG
        asset = self.assSRC.currentText()
        config = os.path.join(os.environ["PRJ"], 'config', 'databases', 'show_search_database.json')
        if self.radioG.isChecked():
            config = os.path.join(os.environ["PRJ"], 'config', 'databases', asset + '_search_database.json')
        if not os.path.isfile(config):
            self.cacher()
        else:
            refr = self.radioF.isChecked()
            if refr:
                self.dbRefresher()
        with open(config, 'r') as f:
            data = json.load(f)
        
        # Start the matching
        for o in out.keys():
            for n in out[o].keys():
                found = []
                for a in out[o][n].keys():
                    node = hou.node(n.path())
                    tipo = node.type().name()
                    if not node.isInsideLockedHDA():
                        attr = node.parm(a)
                        raw = node.parm(a).rawValue()
                        val = out[o][n][a]
                        n_ext = val.split('.')[-1]
                        n_name = val.split('/')[-1].replace('.' + n_ext, '')
                        r_name = raw.split('/')[-1].replace('.' + n_ext, '')
                        state = 0
                        for d in data.keys():
                            if state == 0:
                                for cur in data[d]:
                                    ext = cur.split('.')[-1]
                                    d_name = cur.replace('.' + ext, '')
                                    data_val = self.unixify(os.path.join(d, cur))
                                    if '$F' in raw:
                                        tokens = r_name.split('.')
                                        idx, token = 0, '$F'
                                        for x, t in enumerate(tokens):
                                            if token in t:
                                                idx = x
                                                token = tokens[x]
                                        n_name = n_name.replace(n_name.split('.')[idx], token)
                                    if 'UDIM' in raw:
                                        n_name = n_name.split('%(UDIM)d')[0]
                                        d_name = d_name.split('.')[0]
                                        if n_name[-1] == '.':
                                            d_name = d_name.split('.')[0] + '.'
                                        data_val = self.unixify(os.path.join(d, d_name + '%(UDIM)d.' + ext))
                                    if n_name == d_name:
                                        found.append(node.path())
                                        if val != data_val:
                                            lines, state = [], 1
                                            self.listResult.setStyleSheet(
                                                "QListWidget { background-color: rgba(0, 255, 0, 50); }")
                                            msg = node.path() + '[' + attr.name() + '] -->> ' + data_val
                                            for x in range(0, self.listResult.count()):
                                                lines.append(str(self.listResult.item(x).text()))
                                            if msg not in lines:
                                                self.listResult.addItem(msg)
                                                self.fixFButt.setEnabled(True)
                        if state == 0:
                            if '$HIPNAME' in raw:
                                continue
                            if node.isBypassed():
                                continue
                            msg = node.path() + '[' + attr.name() + '] -->> ' + val
                            if node.path() not in found:
                                self.listResult2.setStyleSheet(
                                    "QListWidget { background-color: rgba(255, 0, 0, 50); }")
                                self.listResult2.addItem(msg)
                            self.fixUButt.setEnabled(True)
            if self.fixFButt.isEnabled() and self.fixUButt.isEnabled():
                self.fixButt.setEnabled(True)


    def cacher(self):
        src = self.unixify(os.environ["PRJ"])
        if self.radioG.isChecked():
            src = self.unixify(os.environ["WORK"])
        out = {}
        for root, dirs, files in os.walk(src, topdown=False):
            cur = []
            for x, f in enumerate(files):
                ext = f.split('.')[-1]
                cond = (
                    ext != 'hda', ext != 'hip', ext != 'hipnc', ext != 'swatches',
                    ext != 'atoms', ext != 'xgen', ext != 'atom', ext != 'ma', ext != 'mb',
                    ext != 'mel', ext != 'py', ext != 'xml', ext != 'ptx', ext != 'pyc', ext != 'ini',
                    ext != 'pdf', ext != 'bsr', ext != 'bsw', ext != 'jSkin', ext != 'mtl',
                    ext != 'xuv', ext != 'atomsskel', ext != 'json', ext != 'atomsclip', ext != 'db')
                if all(cond):
                    if '_u' in f and '_v' in f:
                        zbrush = f.split('_u')[0] + '_u%(U)d_v%(V)d.' + f.split('.')[-1]
                        if zbrush not in cur:
                            cur.append(zbrush)
                    else:
                        cur.append(f)
            if cur:
                geos = ['.abc', '.bgeo', '.bgeo.sc', '.obj', '.fbx', '.stl', '.usd', 'usda', 'usdz']
                imgs = ['.jpg', '.jpeg', '.tif', '.tiff','.exr', '.png', '.psd', '.tx']
                loc = self.unixify(root)
                for l in pyseq.iget_sequences(loc):
                    if '-' in str(l):
                        for x in range(1, 10):
                            rng1, rng2 = x * 100, ((x * 100) + (x * 1))
                            seq = ''
                            if str(rng1) in str(l) or str(rng2) in str(l):
                                seq = l.head() + '%(UDIM)d' + l.tail()
                                # print (seq)
                                if l.tail() not in geos:
                                    cur.append(seq)
                            else:
                                pad = str(len(str(l.end())))
                                seq = l.head() + '$F' + pad + l.tail()
                                if seq not in cur:
                                    if l.tail() not in imgs:
                                        cur.append(seq)
                out[loc] = cur
        asset = self.assSRC.currentText()
        cur_path = os.path.join(os.environ["PRJ"], 'config', 'databases')
        config = os.path.join(cur_path, 'show_search_database.json')
        if not os.path.isdir(cur_path):
            os.makedirs(cur_path)
        if self.radioG.isChecked():
            config = os.path.join(os.environ["PRJ"], 'config', 'databases', asset + '_search_database.json')
        with open(config, 'w') as outfile:
            json.dump(out, outfile, indent=4, sort_keys=True, separators=(',', ':'))
        print(config)



dialog = Window()
dialog.show()