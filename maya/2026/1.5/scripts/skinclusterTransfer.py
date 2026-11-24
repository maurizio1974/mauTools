import maya.cmds as cmds
import os
import json
from PySide6 import QtWidgets, QtCore
from shiboken6 import wrapInstance
import maya.OpenMayaUI as omui

ROOT = "/mnt/cache/skincluster"
WIN = "skinClusterTransferUI"

def maya_main_window():
    return wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)

def get_top_node(mesh):
    path = cmds.ls(mesh, long=True)[0]
    return path.split("|")[1]

def find_joint(name):
    if cmds.objExists(name):
        return name
    short = name.split("|")[-1]
    matches = cmds.ls("*:" + short, type="joint") or []
    if matches:
        return matches[0]
    matches = cmds.ls(short, type="joint") or []
    return matches[0] if matches else None

class SkinTransferUI(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)
        self.setObjectName(WIN)
        self.setWindowTitle("SkinCluster Transfer")
        self.setMinimumSize(460, 420)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        self.setStyleSheet("""
            QDialog { background:#292929; color:#ddd; }
            QLabel { color:#ddd; }
            QLabel#title { font-size:20px; font-weight:bold; color:#f0f0f0; }
            QLabel#subtitle { color:#999; font-size:11px; }
            QFrame#panel { background:#333; border:1px solid #414141; border-radius:6px; }
            QTabWidget::pane { border:1px solid #414141; background:#333; }
            QTabBar::tab { background:#292929; color:#aaa; padding:8px 20px; border:none; }
            QTabBar::tab:selected { background:#333; color:#eee; }
            QListWidget {
                background:#222; border:1px solid #444; border-radius:5px;
                padding:4px; color:#ddd; outline:none;
            }
            QListWidget::item { padding:8px 10px; border-radius:4px; }
            QListWidget::item:hover { background:#3b3b3b; }
            QListWidget::item:selected { background:#4b6985; color:white; }
            QPushButton {
                background:#3d3d3d; border:1px solid #505050;
                border-radius:5px; padding:8px 14px; color:#ddd;
            }
            QPushButton:hover { background:#4a4a4a; }
            QPushButton:pressed { background:#303030; }
            QPushButton#mainButton {
                background:#4b6985; border:1px solid #6688a8;
                font-weight:bold; padding:11px;
            }
            QPushButton#mainButton:hover { background:#587b9b; }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18,18,18,18)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("SkinCluster Transfer")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QtWidgets.QLabel(
            "Export skin setups or transfer them to meshes in another scene."
        )
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self.build_export_tab(), "Export")
        self.tabs.addTab(self.build_import_tab(), "Import")
        layout.addWidget(self.tabs, 1)

        self.status = QtWidgets.QLabel("Ready")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.status.setStyleSheet("color:#777; font-size:10px;")
        layout.addWidget(self.status)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_selection)
        self.timer.start(500)

    def build_export_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(12,12,12,12)
        layout.setSpacing(10)

        info = QtWidgets.QFrame()
        info.setObjectName("panel")
        info_layout = QtWidgets.QVBoxLayout(info)

        text = QtWidgets.QLabel(
            "Select one or more skinned meshes in Maya.\n\n"
            "The top node of each mesh hierarchy becomes the cache folder.\n\n"
            "Example:\n"
            "robot_grp/proxy_grp/body_geo\n"
            "→ /mnt/cache/skincluster/robot_grp/"
        )
        text.setWordWrap(True)
        text.setStyleSheet("color:#aaa; line-height:140%;")
        info_layout.addWidget(text)
        layout.addWidget(info)

        layout.addStretch()

        self.export_selection = QtWidgets.QLabel("Selected meshes: 0")
        self.export_selection.setStyleSheet("color:#999;")
        layout.addWidget(self.export_selection)

        button = QtWidgets.QPushButton("Export SkinCluster")
        button.setObjectName("mainButton")
        button.clicked.connect(self.export_skin)
        layout.addWidget(button)

        return tab

    def build_import_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(12,12,12,12)
        layout.setSpacing(8)

        row = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel("Saved skin setups")
        label.setStyleSheet("font-weight:bold;")
        row.addWidget(label)
        row.addStretch()

        self.folder_count = QtWidgets.QLabel("0 folders")
        self.folder_count.setStyleSheet("color:#888;")
        row.addWidget(self.folder_count)

        layout.addLayout(row)

        self.folders = QtWidgets.QListWidget()
        self.folders.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.folders.itemDoubleClicked.connect(self.import_skin)
        layout.addWidget(self.folders, 1)

        row = QtWidgets.QHBoxLayout()

        self.selection_label = QtWidgets.QLabel("Selected meshes: 0")
        self.selection_label.setStyleSheet("color:#999;")
        row.addWidget(self.selection_label)
        row.addStretch()

        refresh = QtWidgets.QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        row.addWidget(refresh)

        layout.addLayout(row)

        button = QtWidgets.QPushButton("Import SkinCluster")
        button.setObjectName("mainButton")
        button.clicked.connect(self.import_skin)
        layout.addWidget(button)

        return tab

    def refresh(self):
        self.folders.clear()

        if not os.path.exists(ROOT):
            self.folder_count.setText("0 folders")
            return

        folders = sorted(
            x for x in os.listdir(ROOT)
            if os.path.isdir(os.path.join(ROOT,x))
        )

        for folder in folders:
            item = QtWidgets.QListWidgetItem(folder)
            item.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
            )
            self.folders.addItem(item)

        count = len(folders)
        self.folder_count.setText(
            "{} folder{}".format(count, "" if count == 1 else "s")
        )

    def update_selection(self):
        meshes = cmds.ls(sl=True, type="transform") or []
        count = len(meshes)
        self.selection_label.setText("Selected meshes: {}".format(count))
        self.export_selection.setText("Selected meshes: {}".format(count))

    def export_skin(self):
        meshes = cmds.ls(sl=True, type="transform") or []

        if not meshes:
            self.status.setText("Select the meshes to export")
            return

        exported = 0
        skipped = 0

        for mesh in meshes:
            skins = cmds.ls(
                cmds.listHistory(mesh),
                type="skinCluster"
            ) or []

            if not skins:
                cmds.warning("{} has no skinCluster".format(mesh))
                skipped += 1
                continue

            skin = skins[0]
            name = mesh.split("|")[-1]
            top = get_top_node(mesh)
            path = os.path.join(ROOT, top)

            if not os.path.exists(path):
                os.makedirs(path)

            influences = cmds.skinCluster(
                skin,
                q=True,
                influence=True
            ) or []

            data = {
                "mesh": name,
                "influences": influences
            }

            json_file = os.path.join(
                path,
                "{}_sk.json".format(name)
            )

            with open(json_file, "w") as f:
                json.dump(data, f, indent=4)

            cmds.deformerWeights(
                "{}_sk.xml".format(name),
                export=True,
                deformer=skin,
                path=path
            )

            print("Exported:", name)
            print("  Folder:", path)
            print("  Skin:", skin)
            print("  Influences:", len(influences))

            exported += 1

        self.status.setText(
            "Exported {} mesh{}{}".format(
                exported,
                "" if exported == 1 else "es",
                "  |  Skipped: {}".format(skipped) if skipped else ""
            )
        )

        self.refresh()

    def import_skin(self, *args):
        item = self.folders.currentItem()

        if not item:
            self.status.setText("Select a skin setup first")
            return

        meshes = cmds.ls(sl=True, type="transform") or []

        if not meshes:
            self.status.setText("Select the destination meshes")
            return

        folder = item.text()
        path = os.path.join(ROOT, folder)

        imported = 0
        skipped = 0

        for mesh in meshes:
            name = mesh.split("|")[-1]

            json_file = os.path.join(
                path,
                "{}_sk.json".format(name)
            )

            xml_file = os.path.join(
                path,
                "{}_sk.xml".format(name)
            )

            if not os.path.exists(json_file):
                cmds.warning("Missing JSON for {}".format(name))
                skipped += 1
                continue

            if not os.path.exists(xml_file):
                cmds.warning("Missing XML for {}".format(name))
                skipped += 1
                continue

            with open(json_file, "r") as f:
                data = json.load(f)

            joints = []
            missing = []

            for influence in data.get("influences", []):
                joint = find_joint(influence)

                if joint:
                    joints.append(joint)
                else:
                    missing.append(influence)

            if missing:
                cmds.warning(
                    "{} missing influences: {}".format(
                        name,
                        missing
                    )
                )
                skipped += 1
                continue

            for skin in cmds.ls(
                cmds.listHistory(mesh),
                type="skinCluster"
            ) or []:
                cmds.skinCluster(skin, e=True, ub=True)

            skin_name = name.replace("_geo", "_sk")

            skin = cmds.skinCluster(
                joints,
                mesh,
                tsb=True,
                name=skin_name + "#"
            )[0]

            cmds.deformerWeights(
                "{}_sk.xml".format(name),
                im=True,
                deformer=skin,
                path=path,
                method="index"
            )

            cmds.skinCluster(
                skin,
                e=True,
                forceNormalizeWeights=True
            )

            cmds.setAttr(
                skin + ".normalizeWeights",
                1
            )

            print("Imported:", name, "->", skin)
            imported += 1

        self.status.setText(
            "Imported {} mesh{}{}".format(
                imported,
                "" if imported == 1 else "es",
                "  |  Skipped: {}".format(skipped) if skipped else ""
            )
        )

def show_ui():
    global skin_transfer_ui

    try:
        skin_transfer_ui.close()
        skin_transfer_ui.deleteLater()
    except:
        pass

    skin_transfer_ui = SkinTransferUI()
    skin_transfer_ui.show()
    skin_transfer_ui.raise_()
    skin_transfer_ui.activateWindow()