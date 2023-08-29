import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui

class MyScriptUI(QtWidgets.QDialog):
    def __init__(self):
        super(MyScriptUI, self).__init__()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle("karam_hard_surface")
        self.setMinimumWidth(500)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.button_execute = QtWidgets.QPushButton("The sweetest Retopology")
        self.button_execute.clicked.connect(self.execute_script)

        self.checkbox_preserve_hard_edges = QtWidgets.QCheckBox("Preserve Hard Edges")
        self.checkbox_preserve_hard_edges.setChecked(True)

        self.slider_target_face_count = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_target_face_count.setMinimum(1)
        self.slider_target_face_count.setMaximum(10000)
        self.slider_target_face_count.setValue(100)
        self.slider_target_face_count.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider_target_face_count.setTickInterval(100)
        self.slider_target_face_count.valueChanged.connect(self.update_target_face_count_label)

        self.label_target_face_count = QtWidgets.QLabel("Target Face Count: 100")

        self.button_apply_poly_soft_edge = QtWidgets.QPushButton("Apply HardenEdge")
        self.button_apply_poly_soft_edge.clicked.connect(self.apply_poly_soft_edge)

        self.label_result = QtWidgets.QLabel("")

        self.button_uv = QtWidgets.QPushButton("UV")
        self.button_uv.clicked.connect(self.execute_uv_script)

        self.button_circularize_edges = QtWidgets.QPushButton("Circularize Edges")
        self.button_circularize_edges.clicked.connect(self.apply_circularize_edges)     
     
        self.button_about = QtWidgets.QPushButton("About")
        self.button_about.clicked.connect(self.show_about_dialog)

        self.button_linkedin = QtWidgets.QPushButton("LinkedIn")
        self.button_linkedin.clicked.connect(self.open_linkedin_profile)


    def create_layout(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.button_execute)
        layout.addWidget(self.checkbox_preserve_hard_edges)
        layout.addWidget(self.slider_target_face_count)
        layout.addWidget(self.label_target_face_count)
        layout.addWidget(self.button_apply_poly_soft_edge)
        layout.addWidget(self.label_result)
        layout.addWidget(self.button_uv)
        layout.addWidget(self.button_circularize_edges)
        layout.addWidget(self.button_about)
        layout.addWidget(self.button_linkedin)


        try:
            obj = cmds.ls(type='polyCBoolOp')[0]
            attributes = cmds.listAttr(obj, userDefined=True)

            if attributes:
                for attr in attributes:
                    command = "polyCBoolOp -{} {}".format(attr, cmds.getAttr(obj + '.' + attr))
                    label = QtWidgets.QLabel(command)
                    layout.addWidget(label)

        except IndexError:
            label = QtWidgets.QLabel("Booleans")
            layout.addWidget(label)
            intersection_button = QtWidgets.QPushButton("Intersection")
            intersection_button.clicked.connect(self.create_polyCBoolOp_intersection)
            layout.addWidget(intersection_button)
            union_button = QtWidgets.QPushButton("Difference")
            union_button.clicked.connect(self.create_polyCBoolOp_union)
            layout.addWidget(union_button)
            difference_button = QtWidgets.QPushButton("Union")
            difference_button.clicked.connect(self.create_polyCBoolOp_difference)
            layout.addWidget(difference_button)
            label = QtWidgets.QLabel("To communicate")
            layout.addWidget(label)
            layout.addWidget(self.button_about)
            layout.addWidget(self.button_linkedin)


    def update_target_face_count_label(self, value):
        self.label_target_face_count.setText("Target Face Count: {}".format(value))

    def execute_script(self):
        def perform_sequence_of_commands():
            cmds.polyRemesh(maxEdgeLength=1, useRelativeValues=1, collapseThreshold=20, smoothStrength=0,
                            tessellateBorders=1, interpolationType=2)
            cmds.delete(constructionHistory=True)
            preserve_hard_edges = self.checkbox_preserve_hard_edges.isChecked()
            target_face_count = self.slider_target_face_count.value()
            result = cmds.polyRetopo(constructionHistory=1, replaceOriginal=1, preserveHardEdges=preserve_hard_edges,
                                     topologyRegularity=1, faceUniformity=0, anisotropy=0.75,
                                     targetFaceCount=target_face_count, targetFaceCountTolerance=10)
            self.label_result.setText("Result: {}".format(result))

        perform_sequence_of_commands()

    def apply_poly_soft_edge(self):
        selected_edges = cmds.ls(selection=True)

        if selected_edges:
            for edge in selected_edges:
                cmds.polySoftEdge(edge, angle=0, ch=1)

            self.label_result.setText("PolySoftEdge effect has been applied to the selected edges.")
        else:
            self.label_result.setText("Please select some edges.")

    def create_polyCBoolOp_intersection(self):
        selected_obj = cmds.ls(selection=True)[0]
        cmds.polyCBoolOp(op=3, ch=1, preserveColor=0, classification=1, name=selected_obj)
        cmds.delete(constructionHistory=True)

    def create_polyCBoolOp_union(self):
        selected_obj = cmds.ls(selection=True)[0]
        cmds.polyCBoolOp(op=2, ch=1, preserveColor=0, classification=1, name=selected_obj)
        cmds.delete(constructionHistory=True)

    def create_polyCBoolOp_difference(self):
        selected_obj = cmds.ls(selection=True)[0]
        cmds.polyCBoolOp(op=1, ch=1, preserveColor=0, classification=1, name=selected_obj)
        cmds.delete(constructionHistory=True)

    def execute_uv_script(self):
        selected_obj = cmds.ls(selection=True)

        if selected_obj:
            poly_auto_proj_result = cmds.polyAutoProjection(
                selected_obj[0],
                lm=0, pb=0, ibd=1, cm=0, l=2, sc=1, o=1, p=6, ps=0.2, ws=0
            )

            print(poly_auto_proj_result)

            cmds.select(selected_obj[0])
            cmds.u3dLayout(res=256, scl=1, spc=0.00048828125, mar=0.00048828125, box=[0, 1, 0, 1])
            cmds.delete(constructionHistory=True)  # Added line to delete construction history

        else:
            print("No object selected.")

    def show_about_dialog(self):
        about_text = "This Tool performs Retopology and UV in Maya."
        about_text += "\nVersion: 1.0"
        about_text += "\nGmail: mohamedkaram432@gmail.com"
        about_text += "\nMobile: +02 01281881801"

        QtWidgets.QMessageBox.about(self, "About", about_text)

    def open_linkedin_profile(self):
        url = QtCore.QUrl("https://www.linkedin.com/in/mohamed-karam-202811ba/")
        QtGui.QDesktopServices.openUrl(url)

    def apply_circularize_edges(self):
        selected_edges = cmds.ls(selection=True)

        if selected_edges:
            cmds.polyCircularizeEdge(selected_edges, constructionHistory=True, alignment=0, sa=0.5)
            self.label_result.setText("Circularize Edges effect has been applied to the selected edges.")
        else:
            self.label_result.setText("Please select some edges.")


if __name__ == '__main__':
    try:
        my_script_ui.close()
        my_script_ui.deleteLater()
    except:
        pass

    my_script_ui = MyScriptUI()
    my_script_ui.show()
