import os
import hou
import sys
import shutil
# import OpenEXR
from pprint import pprint
from PySide2 import QtGui
from PySide2 import QtCore
from PySide2 import QtWidgets


'''----------------------------------------------------------------------------------------------------
HOW TO USE

import hDenoiser
reload(hDenoiser)
loc = '/jobs/NYAD/sw1_104_1700/CG/CG_sw1_104_1700_lighting_LGT_ocean_sim_all_L010_BEAUTY_v005'
To Just print the result and build the nextowrk but without running the file write

hDenoiser.denoise(loc, True)

To process the nodes also
hDenoiser.denoise(loc, False)
----------------------------------------------------------------------------------------------------'''


class Window(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(Window, self).__init__()
        self.layout = QtWidgets.QGridLayout()
        self.setObjectName("MainWindow")
        self.setWindowTitle('Denoise Render')
        self.resize(500, 160)
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

        self.home()

    def home(self):
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")

        self.label = QtWidgets.QLabel(self.centralwidget)

        self.label.setPixmap(
            QtGui.QPixmap(os.path.join(self.icons, 'denoisePublisher1.png')))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 3)

        self.pathPBT = QtWidgets.QPushButton('Get Render Directory', self.centralwidget)
        self.pathPBT.setObjectName("pathPBT")
        self.gridLayout.addWidget(self.pathPBT, 1, 0, 1, 2)

        self.radioD = QtWidgets.QRadioButton('Debug Mode', self.centralwidget)
        self.radioD.setObjectName("radioD")
        self.gridLayout.addWidget(self.radioD, 1, 2, 1, 1)
        self.radioD.toggle()
        
        self.linePath = QtWidgets.QLineEdit(self.centralwidget)
        self.linePath.setObjectName("linePath")
        self.gridLayout.addWidget(self.linePath, 4, 0, 1, 3)

        self.denoiseButt = QtWidgets.QPushButton('Denoise', self.centralwidget)
        self.denoiseButt.setObjectName("denoiseButt")
        self.gridLayout.addWidget(self.denoiseButt, 5, 0, 1, 3)

        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setMinimumHeight(40)
        self.gridLayout.addWidget(self.progressBar, 6, 0, 1, 3)

        self.setCentralWidget(self.centralwidget)

        # Add Signals --------------------------------------------------------
        self.pathPBT.clicked.connect(self.selectFile)
        self.radioD.toggled.connect(self.switchUI)
        self.denoiseButt.clicked.connect(self.do_denoise)

        # Get latest Session
        self.getSession()
        # Show Windows
        self.show()

    def selectFile(self):
        mainJ = os.getenv('HIP')
        self.linePath.setText(
            QtWidgets.QFileDialog.getExistingDirectory(
                self, 'Select Render Directory', mainJ))
        path = str(self.linePath.text())
        self.saveDefault(path)

    def saveDefault(self, path):
        fileOut = os.path.join(self.loc, 'intellastHSession.path')
        with open(fileOut, 'w') as f:
            f.write(path)

    def getSession(self):
        data = ''
        fileIn = os.path.join(self.loc, 'intellastHSession.path')
        if os.path.isfile(fileIn):
            with open(fileIn) as f:
                data = f.readlines()
            if data:
                self.linePath.setText(data[0])

    def switchUI(self):
        current = str(self.radioD.text())
        if current == 'Debug Mode':
            self.radioD.setText('Processing Mode')
            self.label.setPixmap(
                QtGui.QPixmap(os.path.join(self.icons, 'denoisePublisher2.png')))
        else:
            self.radioD.setText('Debug Mode')
            self.label.setPixmap(
                QtGui.QPixmap(os.path.join(self.icons, 'denoisePublisher1.png')))

    def do_denoise(self):
        file = str(self.linePath.text())
        current = str(self.radioD.text())
        cmd = 'self.denoise("' + file + '")'
        print(cmd)
        if current != 'Debug Mode':
            # eval(cmd)
            self.denoise(file)


    def getChannel(self, node):
        out = []
        items = node.parm('copyto1').menuItems()
        for o in items:
            if '.' not in o and ':' not in o and '(' not in o:
                out.append(o)
        return out


    def denoise(self, src, debug=True):
        bad = []
        shot = src.split('/')[-1]
        # MAKE THE IMAGE NETWORK NODE THAT WILL HOLD THE NODES
        denoise_name = shot + '_denoise'
        img = hou.node('/img/' + denoise_name)
        if not img:
            img = hou.node('/img').createNode('img', denoise_name)
        # RUN OVER ALL THE DIRECTORY OF THE SHOT PASSED TO GET THE AOVS
        aovs = os.listdir(src)
        completed = 0
        for x, a in enumerate(sorted(aovs)):
            seqs, seq, idx = {}, [], []
            cur = os.path.join(src, a)
            if os.path.isdir(cur):
                res = os.listdir(cur)
                for r in res:
                    aov = os.listdir(os.path.join(cur, r))
                    for s in aov:
                        image = os.path.join(cur, r, s)
                        if os.path.isfile(image):
                            if image.endswith('.exr'):
                                index = int(image.split('.')[-2])
                                # CHECH WITH OpenEXR Libs if the file are corrupted
                                # checkIMG = OpenEXR.InputFile(image)
                                # if not checkIMG.isComplete():
                                #     bad.append(image)
                                seq.append(image)
                                idx.append(index)
            # IN CASE THERE ARE CORRUPETED IMAGES THE PROCESS WILL  NOT RUN
            # if bad:
            #     print('There are corrupted files in these render I cannot run the tool')
            #     print('Here the list of bad frames:')
            #     for b in bad:
            #         print('    ' + b.split('/')[-1])
            #     return
            if seq:
                seqs[a] = seq
                fr = [str(min(idx)), str(max(idx))]
                tokens = ['_L010_', '_DENOISED_L010_']
                # SEPARATING THE NODES THAT CNNOT BE PROCESSED AND JUST RENAMING AND COPY THEM OVER
                if 'Crypto' in a or 'deep' in a or 'Render_Time' in a:
                    for y, a in enumerate(seqs.keys()):
                        for z, imag in enumerate(seqs[a]):
                            new = imag.replace(tokens[0], tokens[1])
                            new_dir = new.split('/' + new.split('/')[-1])[0]
                            if not os.path.isdir(new_dir):
                                if not debug:
                                    print('Making missing dir:', new_dir)
                                    os.makedirs(new_dir)
                            if not os.path.isfile(new):
                                if not debug:
                                    shutil.copy2(imag, new)
                                print('Left to do:   ' + str(len(seqs[a]) - z))
                                print('      From:   ' + imag)
                                print('      To  :   ' + new)
                else:
                    # HERE WE CREATE THE NODES AND WE FILTER FOR THE BEAUTY THAT DOESN;T NEED THE CHANNEL RENAMING
                    seq_path = seq[0].replace('/' + seq[0].split('/')[-1], '')
                    seq_name = seq[0].split('.')[0] + '.$F.exr'
                    seq_new_path = seq_path.replace(tokens[0], tokens[1])
                    seq_new_name = seq[0].split('.')[0] + '.$F.exr'
                    seq_new_name = seq_new_name.replace(tokens[0], tokens[1])
                    name = seq[0].split('.')[0].split('/')[-1]
                    # READ
                    image_read = hou.node('/img/' + denoise_name).createNode('file', a + '_READ')
                    image_read.setParms({'filename1': seq_name})
                    imageY = image_read.parm('size1').eval()
                    imageX = image_read.parm('size2').eval()
                    # OVERSCAN READ
                    overscan_read = hou.node('/img/' + denoise_name).createNode('window', a + '_OVERSCANIN')
                    of1 = 'ch("../' + image_read.name() + '/size1")*5/100'
                    of2 = 'ch("../' + image_read.name() + '/size2")*5/100'
                    ha2 = 'ch("../' + image_read.name() + '/size1") + (ch("../' + image_read.name() + '/size1")*10/100)'
                    va2 = 'ch("../' + image_read.name() + '/size2") + (ch("../' + image_read.name() + '/size2")*10/100)'
                    overscan_read.setParms({'window': 0, 'units': 1, 'hold': 0})
                    dic = {'harea2': ha2, 'varea2': va2, 'offset1': of1, 'offset2': of2}
                    for d in dic.keys():
                        overscan_read.parm(d).setExpression(dic[d])
                    overscan_read.setInput(0, image_read, 0)
                    # RESTORE OVERSCAN
                    overscan_out = hou.node('/img/' + denoise_name).createNode('window', a + '_OVERSCANOUT')
                    ofr1 = '(ch("../' + image_read.name() + '/size1")*5/100) * -1'
                    ofr2 = '(ch("../' + image_read.name() + '/size2")*5/100) * -1'
                    har2 = 'ch("../' + image_read.name() + '/size1")'
                    var2 = 'ch("../' + image_read.name() + '/size2")'
                    overscan_out.setParms({'window': 0, 'units': 1, 'hold': 0})
                    dic = {'harea2': har2, 'varea2': var2, 'offset1': ofr1, 'offset2': ofr2}
                    for d in dic.keys():
                        overscan_out.parm(d).setExpression(dic[d])
                    # print(imageY, imageX)
                    # FEEDBACK
                    print('Layers Left to do:', len(aovs) - x)
                    print('Working on:')
                    print('   Pass:  ' + seq_name.split('/')[-1].split('___')[-1])
                    print('   From:  ' + seq_name.split('/')[-1].split('___')[0])
                    print('   To  :  ' + seq_new_name.split('/')[-1].split('___')[0])
                    # WRITE
                    image_write = hou.node('/img/' + denoise_name).createNode('rop_comp', a + '_WRITE')
                    if a != 'beauty':
                        # SHUFFLE JUST TO GET THE CAHNNEL TO WORK ON
                        shuffle = hou.node('/img/' + denoise_name).createNode('channelcopy', a + '_SHUFFLE')
                        shuffle.setInput(0, overscan_read, 0)
                        channel = self.getChannel(shuffle)[0]
                        shuffle.destroy()
                        # print(channel)
                        # shuffle.setParms({'copyto1': '(plane)', 'newplane1': 0, 'copyfrom1': channel})
                        # RENAME
                        rename = hou.node('/img/' + denoise_name).createNode('rename', a + '_RENAME_IN')
                        rename.setParms({'from': '__' + a, 'to': 'C'})
                        rename.setInput(0, overscan_read, 0)
                        # DENOISE
                        denoise = hou.node('/img/' + denoise_name).createNode('aidenoise', a + '_DENOISE')
                        denoise.setInput(0, rename, 0)
                        # OVERSCAN RESTORE
                        overscan_out.setInput(0, denoise, 0)
                        # RENAME
                        rename = hou.node('/img/' + denoise_name).createNode('rename', a + '_RENAME_OUT')
                        rename.setParms({'from': 'C', 'to': '__' + a})
                        rename.setInput(0, overscan_out, 0)
                        # WRITE SETTINGS
                        image_write.setInput(0, rename, 0)
                        image_write.setParms({
                            'copoutput': seq_new_name, 'scopeplanes': channel, 'f1': fr[0], 'f2': fr[1],
                            'outputarea': 2, 'limitcanvaspixels': 0, 'limitcanvaspercent': 10})
                        if not debug:
                            image_write.parm('execute').pressButton()
                        completed += float(100 / len(aovs) - 2)
                    else:
                        # DENOISE
                        denoise = hou.node('/img/' + denoise_name).createNode('aidenoise', a + '_DENOISE')
                        denoise.setInput(0, overscan_read, 0)
                        # OVERSCAN RESTORE
                        overscan_out.setInput(0, denoise, 0)
                        # WRITE SETTINGS
                        image_write.setInput(0, overscan_out, 0)
                        image_write.setParms({
                            'copoutput': seq_new_name, 'f1': fr[0], 'f2': fr[1],
                            'outputarea': 2, 'limitcanvaspixels': 0, 'limitcanvaspercent': 10})
                        if not debug:
                            image_write.parm('execute').pressButton()
                        completed += float(100 / len(aovs) - 2)
                    self.progressBar.setValue(completed)
        self.progressBar.setValue(100)
        img.layoutChildren()
        # pprint(seqs)
        print('-' * 100)
        print('\n' * 3)
        print(' ' * 42, 'ALL DONE')
        print('\n' * 3)
        print('-' * 100)


    def denoise2(self, src, debug=True):
        channels = sorted(os.listdir(src))
        xpos = 0
        ypos = 0
        channel_nodes = []
        # node_loc = "/img/img2"
        # MAKE THE IMAGE NETWORK NODE THAT WILL HOLD THE NODES
        shot = src.split('/')[-1]
        denoise_name = shot + '_denoise'
        img = hou.node('/img/' + denoise_name)
        if not img:
            img = hou.node('/img').createNode('img', denoise_name)
        node_loc = img.path()
        # FIRST MERGE
        merge_node = hou.node(node_loc).createNode("merge", node_name="merge_channels")
        merge_node.setPosition(((len(channels)),ypos))
        ypos = ypos - 2
        # OPENNING THE OVERSCAN
        overscan_read = hou.node(node_loc).createNode('window', 'overscan_in')
        overscan_read.setParms({'window': 0, 'units': 1})
        overscan_read.setPosition(((len(channels)),ypos))
        overscan_read.setInput(0, merge_node, 0)
        ypos = ypos - 2
        # DENOISE NODE
        aidenoise_node = hou.node(node_loc).createNode("aidenoise", node_name="aidenoise_channels")
        aidenoise_node.setPosition(((len(channels)),ypos))
        aidenoise_node.setInput(0, overscan_read)
        aidenoise_node.parm("pscope").set("*")
        ypos = ypos - 2
        # RESTORE OVERSCAN
        overscan_restore = hou.node(node_loc).createNode('window', 'overscan_out')
        overscan_restore.setParms({'window': 0, 'units': 1})
        overscan_restore.setInput(0, aidenoise_node, 0)
        overscan_restore.setPosition(((len(channels)),ypos))
        ypos = ypos - 2
        for channel in channels:
            indir  = os.path.join(src, channel)
            for render_path, render_dirs, render_files in os.walk(indir):
                for x, render_file in enumerate(render_files):
                    render_path_new = render_path.replace('_L010_', '_DENOISED_L010_')
                    render_file_new = render_file.replace('_L010_', '_DENOISED_L010_')
                    infile = os.path.join(render_path, render_file)
                    infile = infile.split(".")[0] + ".$F4.exr"
                    outfile = os.path.join(render_path_new, render_file_new)
                    outfile = outfile.split(".")[0] + ".$F4.exr"
                    file_node = hou.node(node_loc).createNode("file", node_name="read_" + channel)
                    file_node.parm("filename1").set(infile)
                    file_node.setPosition((xpos,(ypos + 10)))
                    merge_node.setInput(channels.index(channel), file_node)
                    file_out_node = hou.node(node_loc).createNode("rop_comp", node_name="write_" + channel)
                    file_out_node.setPosition((xpos,(ypos - 2)))
                    file_out_node.setInput(0, overscan_restore)
                    file_out_node.parm("copoutput").set(outfile)
                    if channel == "beauty":
                        imageY = file_node.parm('size1').eval()
                        imageX = file_node.parm('size2').eval()
                        of1 = imageY*5/100
                        of2 = imageX*5/100
                        ha2 = imageY + (imageY*10/100)
                        va2 = imageX + (imageX*10/100)
                        overscan_read.setParms({'harea2': ha2, 'varea2': va2, 'offset1': of1, 'offset2': of2})

                        ofr1 = (imageY*5/100) * -1
                        ofr2 = (imageX*5/100) * -1
                        har2 = imageY
                        var2 = imageX
                        overscan_restore.setParms({'harea2': har2, 'varea2': var2, 'offset1': ofr1, 'offset2': ofr2})
                        print(imageY, imageX)
                    if channel == "beauty":
                        file_out_node.parm("scopeplanes").set("C A")
                    else:
                        file_out_node.parm("scopeplanes").set("__" + channel)
                    xpos = xpos + 2
                    print('Working on', channel)
                    break

dialog = Window()
dialog.show()


def checkResult(src):
    aovs = os.listdir(src)
    print('Missing Passes:')
    for x, a in enumerate(sorted(aovs)):
        cur = os.path.join(src, a)
        if os.path.isdir(cur):
            res = os.listdir(cur)
            for r in res:
                denoise = os.path.join(cur, r, 'denoised')
                if os.path.isdir(denoise):
                    images = os.listdir(denoise)
                    if not images:
                        print(denoise)
