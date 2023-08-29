"""					
					I N S T A L L A T I O N:
Copy the "rjRetargetBlendshape.py" to your Maya scripts directory:
	C:\Users\<USER>\Documents\maya\scripts

						   U S A G E:
Display the UI with the following code:
	import rjRetargetBlendshape
    rjRetargetBlendshape.show()
    
Command line:
    import rjRetargetBlendshape
    rjRetargetBlendshape.convert(
        source,
        blendshape,
        target,
        scale=True, 
        rotate=True, 
        smooth=0, 
        space=OpenMaya.MSpace.kObject,
    )
    
							N O T E:
Retarget your blendshapes between meshes with the same topology.
There are a few options that can be helpful to achieve the desired
results. 

    - Scaling your delta depending on the size difference between
      the source and the target vertex. 
      
    - Rotating the delta depending on the normal difference between 
      the source and the target vertex. 
      
    - Smoothing based on the vertex size between the retarget mesh
      and the blendshape mesh.
"""

from functools import partial
from PySide import QtGui, QtCore
from maya import OpenMaya, OpenMayaUI, cmds, mel

import math
import shiboken

__author__    = "Robert Joosten"
__version__   = "0.8.0"
__email__     = "rwm.joosten@gmail.com"

# ---------------------------------------------------------------------------------------------------------------------
# UI UTILS
# ---------------------------------------------------------------------------------------------------------------------

FONT = QtGui.QFont()
FONT.setFamily("Consolas")

BOLT_FONT = QtGui.QFont()
BOLT_FONT.setFamily("Consolas")
BOLT_FONT.setWeight(100)

def validate(func):
    def inner(*args, **kwargs):
        # Run Function
        ret = func(*args, **kwargs)
        
        # Validate
        if not args[0].source or not args[0].target or not args[0].blendshapes:
            args[0].retargetB.setEnabled(False)
        else:
            args[0].retargetB.setEnabled(True)
            
        return ret
            
    return inner

def mayaWindow():
    window = OpenMayaUI.MQtUtil.mainWindow()
    window = shiboken.wrapInstance( long( window ), QtGui.QMainWindow )
    
    return window

# ---------------------------------------------------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------------------------------------------------

class RetargetUI(QtGui.QWidget):
    def __init__( self, parent ):
        super(RetargetUI, self).__init__(parent)
        
        # Variables
        self.source = []
        self.target = []
        self.blendshapes = []
           
        # Set as Window
        self.setParent( parent )        
        self.setWindowFlags(QtCore.Qt.Window)   
        self.setWindowIcon(QtGui.QIcon(":/blendShape.png"))

        self.setWindowTitle("Retarget Blendshapes")           
        self.setObjectName("RetargetUI")
        self.resize(300, 200)
                
        mainVL = QtGui.QVBoxLayout(self)
        mainVL.setContentsMargins(5, 5, 5, 5)
        mainVL.setSpacing(5)
                
        retargetL = QtGui.QLabel(self)
        retargetL.setText("Retarget Blendshapes")
        retargetL.setFont(BOLT_FONT)
        mainVL.addWidget(retargetL) 
        
        for b, f in zip(
                ["Set Source", "Set Blendshape(s)", "Set Target"],
                [self.setSource, self.setBlendshapes, self.setTarget],
            ):
                hl = QtGui.QHBoxLayout(self)
                hl.setContentsMargins(3, 0, 3, 0)
                hl.setSpacing(0)
                mainVL.addLayout(hl)
                
                label = QtGui.QLabel(self)
                label.setText("( 0 ) Mesh(es)")
                label.setFont(FONT)
                hl.addWidget(label)
                
                button = QtGui.QPushButton(self)
                button.setText(b)
                button.setFont(FONT)
                button.released.connect(partial(f, label))
                
                hl.addWidget(button)

        line = QtGui.QFrame(self)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        mainVL.addWidget(line) 
        
        optionsL = QtGui.QLabel(self)
        optionsL.setText("Options")
        optionsL.setFont(BOLT_FONT)
        mainVL.addWidget(optionsL) 
        
        hl = QtGui.QHBoxLayout(self)
        hl.setContentsMargins(3, 0, 3, 0)
        hl.setSpacing(0)
        mainVL.addLayout(hl)

        self.scaleCB = QtGui.QCheckBox(self)
        self.scaleCB.setText("Scale Delta")
        self.scaleCB.setFont(FONT)
        self.scaleCB.setChecked(True)
        self.scaleCB.setToolTip((
            "If checked, the vertex delta will be scaled based on the difference\n"
            "of the averaged connected edge length between the source and the target."))
        hl.addWidget(self.scaleCB) 
        
        hl = QtGui.QHBoxLayout(self)
        hl.setContentsMargins(3, 0, 3, 0)
        hl.setSpacing(0)
        mainVL.addLayout(hl)
        
        self.rotateCB = QtGui.QCheckBox(self)
        self.rotateCB.setText("Rotate Delta")
        self.rotateCB.setFont(FONT)
        self.rotateCB.setChecked(True)
        self.rotateCB.setToolTip((
            "If checked, the vertex delta will be rotated based on the difference \n"
            "of the vertex normal between the source and the target."))
        hl.addWidget(self.rotateCB) 
        
        hl = QtGui.QHBoxLayout(self)
        hl.setContentsMargins(3, 0, 3, 0)
        hl.setSpacing(0)
        mainVL.addLayout(hl)
        
        self.smoothCB = QtGui.QCheckBox(self)
        self.smoothCB.setText("Smooth Factor")
        self.smoothCB.setFont(FONT)
        self.smoothCB.setChecked(True)
        self.smoothCB.setToolTip((
            "If checked, the targets will be smoothed based on the difference\n"
            "between source and blendshape and original target and output."))
        hl.addWidget(self.smoothCB) 
        
        self.smoothSB = QtGui.QDoubleSpinBox(self)
        self.smoothSB.setFont(FONT)
        self.smoothSB.setValue(10)
        self.smoothSB.setMaximum(1000.0)
        hl.addWidget(self.smoothSB) 
        
        line = QtGui.QFrame(self)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        mainVL.addWidget(line) 
        
        hl = QtGui.QHBoxLayout(self)
        hl.setContentsMargins(3, 0, 3, 0)
        hl.setSpacing(0)
        mainVL.addLayout(hl)
        
        spaceL = QtGui.QLabel(self)
        spaceL.setText("Calculation Space:")
        spaceL.setFont(FONT)
        spaceL.setToolTip((
            "Determine space in which all the calculations take place."))
        hl.addWidget(spaceL) 
        
        self.spaceCB = QtGui.QComboBox(self)
        self.spaceCB.setFont(FONT)
        self.spaceCB.addItems(["kObject", "kWorld"])
           
        hl.addWidget(self.spaceCB) 
        
        line = QtGui.QFrame(self)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        mainVL.addWidget(line) 
        
        self.retargetB = QtGui.QPushButton(self)
        self.retargetB.setText("Retarget")
        self.retargetB.setFont(FONT)
        self.retargetB.setEnabled(False)
        self.retargetB.released.connect(self.retarget)
        mainVL.addWidget(self.retargetB) 
                
        spacer = QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        mainVL.addItem(spacer)
        
        self.progressBar = QtGui.QProgressBar(self)   
        mainVL.addWidget(self.progressBar)
          
    # -----------------------------------------------------------------------------------------------------------------
                
    def setSelection(self, label, mode="single"):
        container = []
        selection = cmds.ls(sl=True, l=True)
        
        for sel in selection:
            child = cmds.listRelatives(sel, s=True, ni=True, f=True)
            if not child:
                continue
            
            if cmds.nodeType(child[0]) == "mesh":
                container.append(sel)
                
        if mode == "single" and container:
            container = [container[0]]
        
        label.setText("( {0} ) Mesh(es)".format(len(container)))
        label.setToolTip("\n".join(container))

        return container
        
    # -----------------------------------------------------------------------------------------------------------------
       
    @validate
    def setSource(self, label):
        self.source = self.setSelection(label)
    
    @validate
    def setTarget(self, label):
        self.target = self.setSelection(label)
   
    @validate
    def setBlendshapes(self, label):
        self.blendshapes = self.setSelection(label, "multi")
        
    # -----------------------------------------------------------------------------------------------------------------
        
    def retarget(self):        
        # Set Progress Bar
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len(self.blendshapes))
        self.progressBar.setValue(0)  
        
        # Scale and Rotate Deltas
        scale = self.scaleCB.isChecked()
        rotate = self.rotateCB.isChecked()
        
        # Smooth Factor
        smooth = 0
        if self.smoothCB.isChecked():
            smooth = self.smoothSB.value()
        
        # Space
        space = SPACE[self.spaceCB.currentIndex()]
        
        # Convert
        for i, blendshape in enumerate(self.blendshapes):
            convert(self.source[0], blendshape, self.target[0], scale, rotate, smooth, space)
            self.progressBar.setValue(i+1)  

        
def show():
    retargetUI = RetargetUI(mayaWindow())
    retargetUI.show()

    
# ---------------------------------------------------------------------------------------------------------------------
# CORE
# ---------------------------------------------------------------------------------------------------------------------

def convert(source, blendshape, target, scale=True, rotate=True, smooth=0, space=OpenMaya.MSpace.kObject):
    # Convert to Dag
    sourceD = toDag(source)
    blendshapeD = toDag(blendshape)
    
    # Convert to MFnMesh
    sourceM = toMFnMesh(source)
    blendshapeM = toMFnMesh(blendshape)
    targetM = toMFnMesh(target)

    # Compare Vertex Counts
    count = set([
        sourceM.numVertices(), 
        blendshapeM.numVertices(), 
        targetM.numVertices()
    ])
    
    if len(count) != 1:
        cmds.warning("Source - Target - Blendshapes don't have matching vertex counts!")
        
    # Duplicate Target
    targetB = target.split("|")[-1].split(":")[-1]
    blendshapeB = blendshape.split("|")[-1].split(":")[-1]
    
    target = cmds.duplicate(target, rr=True, n="{0}_{1}".format(targetB, blendshapeB))[0]
    if cmds.listRelatives(target, p=True):
        target = cmds.parent(target, world=True)[0]
    
    targetD = toDag(target)
    targetM = toMFnMesh(target)
    
    # Iterate Vertices
    count = next(iter(count))
    positions = OpenMaya.MPointArray()
    
    sourceLengths = []
    blendshapeLenghths = []
    targetLengths = []
    
    for i in range(count):
        # Calculate Position Offset
        sourceP = OpenMaya.MPoint()
        blendshapeP = OpenMaya.MPoint()
        targetP = OpenMaya.MPoint()
        
        sourceM.getPoint(i, sourceP, space)
        blendshapeM.getPoint(i, blendshapeP, space)
        targetM.getPoint(i, targetP, space)
        
        vector = blendshapeP - sourceP
        
        # Calculate Scale Factor
        component = toComponent(i)
        sourceLength = getAverageLength(sourceD, component, space)
        blendshapeLength = getAverageLength(blendshapeD, component, space)
        targetLength = getAverageLength(targetD, component, space)
        
        sourceLengths.append(sourceLength)
        blendshapeLenghths.append(blendshapeLength)
        targetLengths.append(targetLength)
        
        if scale:
            if not sourceLength or not targetLength:
                scaleFactor = 1
            else:    
                scaleFactor = targetLength/sourceLength
                
            vector = vector * scaleFactor 
        
        # Calculate Normal Offset
        if rotate:
            sourceN = OpenMaya.MVector()
            targetN = OpenMaya.MVector()
            
            sourceM.getVertexNormal(i, True, sourceN, space)
            targetM.getVertexNormal(i, True, targetN, space)

            quaternion = sourceN.rotateTo(targetN)
            vector = vector.rotateBy(quaternion)
            
        positions.append(targetP + vector)
    
    # Set All Positions
    targetM.setPoints(positions, space)
    
    # Set Smooth Values
    for i in range(2):
        for i, sl, bl, tl in zip(range(count), sourceLengths, blendshapeLenghths, targetLengths):
            setSmooth(targetD, i, space, sl, bl, tl, smooth)
        
def setSmooth(dag, index, space, sl, bl, tl, smooth):
    # Calculate Factor
    component = toComponent(index)
    ntl = getAverageLength(dag, component, space)
    
    if not sl or not tl:    tf = 1
    else:                   tf = bl/sl
    
    if not sl or not bl:    bf = 1
    else:                   bf = ntl/tl
                
    factor = abs((1-tf/bf)*smooth)
    factor = max(min(factor, 1), 0)
    
    # Ignore if no Factor
    if not factor:
        return

    connected = OpenMaya.MIntArray()

    component = toComponent(index)
    main = OpenMaya.MItMeshVertex(dag, component)
    main.getConnectedVertices(connected)
      
    # Ignore if no Connected Vertices
    if not connected.length():
        return
    
    # Get Positions
    originalPos = main.position(space)
    averagePos = OpenMaya.MPoint()
 
    component = toComponent(connected)
    iterate = OpenMaya.MItMeshVertex(dag, component)
    while not iterate.isDone():
        averagePos += OpenMaya.MVector(iterate.position(space))
        iterate.next()
    
    # Calculate Average Position
    averagePos = averagePos/connected.length()
    averagePos = averagePos * factor
    originalPos = originalPos * (1-factor)
    newPos = averagePos + OpenMaya.MVector(originalPos)
    main.setPosition(newPos, space)

def getAverageLength(dag, component, space):
    total = 0

    # Get Connected Edges
    connected = OpenMaya.MIntArray()

    iterate = OpenMaya.MItMeshVertex(dag, component)
    iterate.getConnectedEdges(connected)
    
    if not connected.length():
        return 0
    
    component = toComponent(connected, OpenMaya.MFn.kMeshEdgeComponent)
    
    # Get Length Connected Edges
    iterate = OpenMaya.MItMeshEdge(dag, component)
    while not iterate.isDone():
        lengthUtil = OpenMaya.MScriptUtil()
        lengthPtr = lengthUtil.asDoublePtr()
    
        iterate.getLength(lengthPtr, space)
        total += lengthUtil.getDouble(lengthPtr)
        
        iterate.next()
        
    return total/connected.length()

    
# ---------------------------------------------------------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------------------------------------------------------

SPACE = []
SPACE.append(OpenMaya.MSpace.kObject)
SPACE.append(OpenMaya.MSpace.kWorld)
  
def toComponent(index, t=OpenMaya.MFn.kMeshVertComponent):
    if type(index) != OpenMaya.MIntArray:
        array = OpenMaya.MIntArray()
        array.append(index)
    else:
        array = index

    component = OpenMaya.MFnSingleIndexedComponent().create(t)
    OpenMaya.MFnSingleIndexedComponent(component).addElements(array)
    return component
    
def toMFnMesh(name):
    dag = toDag(name)
    dag.extendToShape()

    mFnMesh = OpenMaya.MFnMesh(dag)
    return mFnMesh
    
def toDag(name):
    mObj = toMObject(name)
    return OpenMaya.MDagPath.getAPathTo(mObj)
    
def toMObject(name):
    selectionList = OpenMaya.MSelectionList()
    selectionList.add(name)
    node = OpenMaya.MObject()
    selectionList.getDependNode(0, node)
    return node