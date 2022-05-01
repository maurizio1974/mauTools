
from maya import cmds, OpenMaya

class RigError(Exception):
    pass

class n_mirrorComponents(object):
    '''
    Given a list of mesh components (as a valid selection or by using the components argument), 
    this class will return and/or select the mirror components.
    
    ARGUMENTS:
        components     = poly verts, faces or edges (I will expand to nurbs soon)
        tolerance      = error threshold for the search mechanism. The lower this value, the more precise the results,
                         but also the more prone to error in the case the mesh is not perfectly symmetrical
        axis           = 0 for x, 1 for y and 2 for z. No need to specify positive or negative
        absolute       = if True, the search will occur in world space
        doSelect       = should we select what we find? You may not always want this...
        addToSelection = if True, the class returns a list of both initial components and mirroredComponents
        
    USAGE:
        #copy this file to your PYTHONPATH
        from n_mirrorComponents import n_mirrorComponents
        
        #Just return the results
        #create a poly sphere and select a few verts, then run
        mc = n_mirrorComponents()
        mc.doIt()
        print mc.mirroredComponents
        
        #Select and return the results, 
        #specify some arguments
        mc = n_mirrorComponents(axis = 0, doSelect = 1, addToSelection = 1)
        mc.doIt()
        
        #use a predefined components list instead of a selection
        myList = ["pSphere1.vtx[258]", "pSphere1.vtx[238]"]
        mc = n_mirrorComponents(components = myList, doSelect = 1)
        mc.doIt()
    
    NOTE1: Currently only poly meshes are supported (maybe I'll extend to nurbs too at some point)
    NOTE2: Internally the search mechanism needs verts. If the components are faces, edges or uvs,
           I am converting to verts, do the work and then convert back to your initial components or selection,
           based on the type of the first component. I may extend this functionality at some point if need be.
            
    AUTHOR:        Catalin Niculescu
    n_loc blog:    http://3desque.wordpress.com/2011/03/23/n_mirrorcomponents/
    '''
    def __init__(self, 
                 components = None, 
                 tolerance = 0.001, 
                 axis = 0, 
                 absolute = False, 
                 doSelect = True,
                 addToSelection = False ):
        
        #args
        self.components = components
        self.tolerance = tolerance
        self.axis = axis
        self.absolute = absolute
        self.doSelect = doSelect
        self.addToSelection = addToSelection
        
        #vars
        self.mirroredComponents = []
        self.selList = OpenMaya.MSelectionList()
        self.componentType = "vertex"
        self.hadSelection = False
        self.origComponents = None
        
    def __convertToVerts(self):
        iter = OpenMaya.MItSelectionList(self.selList)
        component = OpenMaya.MObject()
        dp = OpenMaya.MDagPath()
        arr = OpenMaya.MIntArray()
        convertedList = None 
        
        while not iter.isDone():
            try:
                iter.getDagPath( dp, component );
            except:
                raise RigError("Invalid selection.")
            
            if component.hasFn(OpenMaya.MFn.kMeshVertComponent):
                self.componentType = "vertex"
            elif component.hasFn(OpenMaya.MFn.kMeshEdgeComponent):
                self.componentType = "edge"
                convertedList = cmds.polyListComponentConversion(self.components, fe = 1, tv = 1)
            elif component.hasFn(OpenMaya.MFn.kMeshPolygonComponent):
                self.componentType = "face"
                convertedList = cmds.polyListComponentConversion(self.components, ff = 1, tv = 1)
            elif component.hasFn(OpenMaya.MFn.kMeshMapComponent):
                self.componentType = "uv"
                convertedList = cmds.polyListComponentConversion(self.components, fuv = 1, tv = 1)
            else:
                raise RigError("The first element is not a mesh component.")
             
            break
        
        self.origComponents = self.components
        if self.componentType != "vertex":
            self.components = cmds.ls(convertedList, fl = 1)
            self.selList.clear()
            for i in self.components:
                self.selList.add(i)
            
    def __prepare(self):
                
        #check the selection if self.components is None
        if not self.components:
            self.components = []
            component = OpenMaya.MObject()
            
            #get the selection
            OpenMaya.MGlobal.getActiveSelectionList(self.selList)
            
            dp = OpenMaya.MDagPath()
            self.selList.getSelectionStrings(self.components)
            self.hadSelection = True
        else:
            for i in self.components:
                self.selList.add(i)
                    
        #if we still don't have anything, error out
        if not self.components:
            raise RigError("Invalid selection. Expecting mesh components.")
        
        #make sure the components are verts
        self.__convertToVerts()
        
    def doIt(self):
        self.__prepare()

        #vars
        component = OpenMaya.MObject()
        vertDP = OpenMaya.MDagPath()
        meshFn = OpenMaya.MFnMesh()
        origPoint = OpenMaya.MPoint()
        closestPoint = OpenMaya.MPoint()
        faceVertPoint = OpenMaya.MPoint()
        vertexId = 0
        closestPolygonPtr = OpenMaya.MScriptUtil()
        closestPolygonPtr.createFromInt(0)
        closestPolygon = closestPolygonPtr.asIntPtr()
        points = OpenMaya.MIntArray()
        mirroPoints = OpenMaya.MIntArray()
        mirrorSpace = OpenMaya.MSpace.kObject
        componentsPaths = []
        
        #selList iterator
        selListIter = OpenMaya.MItSelectionList(self.selList, OpenMaya.MFn.kMeshVertComponent)
        
        while not selListIter.isDone(): 
            selListIter.getDagPath( vertDP, component) 
            meshFn.setObject( vertDP ) 
            uvMap = meshFn.currentUVSetName()
            
            if self.absolute:
                mirrorSpace = OpenMaya.MSpace.kWorld
                    
            if not component.isNull():
                vertexIter = OpenMaya.MItMeshVertex(vertDP, component)
                
                while not vertexIter.isDone():
                    vertexId = vertexIter.index()
                    origPoint = vertexIter.position(mirrorSpace)
    
                    #negate according to axis
                    if self.axis == 0:
                        origPoint.x *= -1
                    elif self.axis == 1:
                        origPoint.y *= -1
                    elif self.axis == 2:
                        origPoint.z *= -1
    
                    #get the closest point to the x-negated origPoint
                    meshFn.getClosestPoint(origPoint, closestPoint, mirrorSpace, closestPolygon)

                    #get the closest faceID's verts
                    meshFn.getPolygonVertices(OpenMaya.MScriptUtil(closestPolygon).asInt(), points)
    
    
                    for i in range(points.length()):
                        meshFn.getPoint(points[i], faceVertPoint, mirrorSpace)
    
                        if faceVertPoint.isEquivalent(origPoint, self.tolerance):
                            mirroPoints.append(points[i])
                            self.mirroredComponents.append(meshFn.fullPathName() + ".vtx[" + str(points[i]) + "]")
                            break

                    vertexIter.next()
            
            selListIter.next()

        #convert back if needed
        if self.componentType == "face":
            self.mirroredComponents = cmds.polyListComponentConversion(self.mirroredComponents, fv = 1, tf = 1, internal = 1)
        elif self.componentType == "edge":
            self.mirroredComponents = cmds.polyListComponentConversion(self.mirroredComponents, fv = 1, te = 1, internal = 1)
        if self.componentType == "uv":
            self.mirroredComponents = cmds.polyListComponentConversion(self.mirroredComponents, fv = 1, tuv = 1)
        
        if self.addToSelection:
            for i in self.origComponents:
                self.mirroredComponents.append(i)
                    
        if self.doSelect:
            cmds.select(self.mirroredComponents)

