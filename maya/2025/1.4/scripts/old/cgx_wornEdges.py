##########################################################################################
##cgx_wornEdges : To paint the hard edges of your objects using vertex colors.
##NOTE: The original idea is from Neil Blevins. http://www.neilblevins.com
##Version: 2.0.0 Released: 18-12-2010
##Chris Granados - Xian chris.granados@xiancg.com http://chrisgranados.blogspot.com
##########################################################################################


##--------------------------------------------------------------------------------------------
##import maya and math
##--------------------------------------------------------------------------------------------
import maya.cmds as cmds
import maya.mel as mel
import math


##--------------------------------------------------------------------------------------------
##def that verifies the shading net to see if a node is missing
##--------------------------------------------------------------------------------------------
def verifyShadingNet (thisShader):
	"""def that verifies the shading net to see if a node is missing"""

	clampBlendNode = cmds.listConnections((thisShader + ".outColor"), destination = False , source = True , plugs = False , type = "remapValue")
	if len(clampBlendNode) == 1:
		luminanceNode = cmds.listConnections((clampBlendNode[0] + ".inputValue"), destination = False , source = True , plugs = False , type = "luminance")
		if len(luminanceNode) == 1:
			blendNode = ['0']
			blendNode.append(cmds.listConnections((luminanceNode[0] + ".value"), destination = False , source = True , plugs = False , type = "blendColors"))
			if blendNode[1] != None:
				return blendNode[1]
			else :
				cmds.warning('There is a missing node or connection in the shading net. The script will create a new one.')
				return 'None'
		else :
			cmds.warning('There is a missing node or connection in the shading net. The script will create a new one.')
			return 'None'
	else :
		cmds.warning('There is a missing node or connection in the shading net. The script will create a new one.')
		return 'None'


##---------------------------------------------------------------------------------------------
##def that verifies the existence of the shading net and acts accordingly
##---------------------------------------------------------------------------------------------
def useShadingNet (*args):
	"""def that verifies the existence of the shading net and acts accordingly"""
	
	#List selected objects and set createNet var
	allObjs = cmds.ls(sl = True, transforms = True)
	crearNet = False
	numeroSets = 0
	if len(allObjs) == 0 :
		cmds.warning('You have to select at least one object.')
	else :
		#Start progress bar
		cmds.text("processingTXT" , edit = True , enable = True)
		cmds.progressBar("progressBarPB" , edit = True , maxValue = (len(allObjs)) , enable = True , isInterruptable = True , isMainProgressBar = True , beginProgress = True)
		cmds.text("pressEscTXT" , edit = True , vis = True)
		for each in allObjs :
			if cmds.progressBar("progressBarPB" , q = True , isCancelled = True):
				break
			
			#Set progress status
			cmds.text("processingTXT" , edit = True , label = ("Processing: " + each))
			cmds.progressBar("progressBarPB" , edit = True , step = 1, status = ("Processing: " + each))
			
			objShape = cmds.listRelatives(each , shapes = True)
			#Create mentalRayVertexColors and connect the new colorSet
			createMrVtxCHKBOX = cmds.checkBox("createMrVtxCHKBOX" , q = True, value = True)
			mrVtxColorNode = []
			
			#Vtx map
			if createMrVtxCHKBOX == True :
				existingVertexNode = []
				existingVertexNode.append(cmds.listConnections((objShape[0] + ".colorSet[0].colorName") , destination = True , source = False , plugs = False))
				if existingVertexNode[0] == None:
					mrVtxColorNode = [mel.eval('mrCreateCustomNode -asTexture "" mentalrayVertexColors')]
					cmds.connectAttr((objShape[0] + ".colorSet[0].colorName") , (mrVtxColorNode[0] + ".cpvSets[0]") , force = True )
					if cmds.checkBox("shadingNetCHKBOX" , q = True, enable = True) == True and cmds.checkBox("shadingNetCHKBOX" , q = True, value = True) == True :
						crearNet = True
				else :
					mrVtxColorNode = existingVertexNode[0]
					if cmds.checkBox("shadingNetCHKBOX" , q = True, enable = True) == True and cmds.checkBox("shadingNetCHKBOX" , q = True, value = True) == True :
						crearNet = True
			
			#Shading network
			currentSG = cmds.listConnections(objShape[0] , destination = True , source = False , plugs = False , type = "shadingEngine")
			shaderName = cmds.listConnections((currentSG[0] + ".surfaceShader") , destination = False , source = True , plugs = False)
			if currentSG[0][:9] == 'wornEdges' and crearNet == True:
				#Verify shading net
				dialogOptions = cmds.confirmDialog( title='Existing shading net', message=('There is a ' + shaderName[0] + ' shader already connected to ' + objShape[0] + '. Do you want to use it or create a new one?'), button=['Use it','New one','Cancel','Cancel All'], defaultButton='Use it', cancelButton='Cancel', dismissString='Cancel' )
				#Verify if all nodes and connections are correct
				blendName = verifyShadingNet(shaderName[0])
				if dialogOptions == 'Use it' :
					if blendName.count('None') < 1 :
						filtrarBordes(each)
						if crearNet == True :
							crearShadingNet(mrVtxColorNode[0],'useIt',shaderName[0],blendName[0],objShape[0])
					else :
						filtrarBordes(each)
						if crearNet == True :
							crearShadingNet(mrVtxColorNode[0],'newOne',shaderName[0],"",objShape[0])
				elif dialogOptions == 'New one' :
					filtrarBordes(each)
					if crearNet == True :
						crearShadingNet(mrVtxColorNode[0],'newOne',shaderName[0],"",objShape[0])
				elif dialogOptions == 'Cancel' :
					continue
				elif dialogOptions == 'Cancel All' :
					break
			else :				
				#If there is no shading net then just create a new one
				filtrarBordes(each)
				if crearNet == True :
					crearShadingNet(mrVtxColorNode[0],'newOne',shaderName[0],"",objShape[0])
		
		#Disable progress bar
		cmds.text("processingTXT" , edit = True , label = ('Processing: ') , enable = False)
		cmds.progressBar("progressBarPB" , edit = True , maxValue = 100 , progress = 0 , width = 150 ,enable = False, isInterruptable = False , isMainProgressBar = False)
		cmds.progressBar("progressBarPB" , edit = True , endProgress = True)
		cmds.text("pressEscTXT" , edit = True , vis = False)


##--------------------------------------------------------------------------------------------
##def that creates a base shading network using a noise texture
##--------------------------------------------------------------------------------------------
def crearShadingNet (vtxMap,useShading,shaderName,blendName,object) :
	"""def that creates a base shading network using a noise texture"""
	
	if useShading == 'newOne':
		#Create nodes
		clampNoise = cmds.shadingNode('remapValue' , asUtility = True , name = "clampNoise")
		clampBlend = cmds.shadingNode('remapValue' , asUtility = True , name = "clampBlend")
		blendColors = cmds.shadingNode('blendColors' , asUtility = True)
		blendToValue = cmds.shadingNode('luminance' , asUtility = True)
		noiseText = cmds.shadingNode('noise' , asTexture = True , name = "distortNoise")
		placeText = cmds.shadingNode('place2dTexture' , asUtility = True)
		shader = cmds.shadingNode('surfaceShader' , asShader = True, name = ("wornEdges_" + object + "_surface"))
		wornSG = cmds.sets(renderable = True , noSurfaceShader = True , empty = True , name = ('wornEdges_' + object +'_SG'))
		
		#Connect placeText to Noise and set noise attributes
		cmds.connectAttr((placeText + ".outUV") , (noiseText + ".uv") , force = True)
		cmds.connectAttr((placeText + ".outUvFilterSize") , (noiseText + ".uvFilterSize") , force = True)
		cmds.setAttr ((noiseText + ".frequency") , 100)
		cmds.setAttr ((noiseText + ".noiseType") , 0)
		cmds.setAttr ((noiseText + ".amplitude") , 0.35)
		
		#Connect noise and clamp
		cmds.connectAttr((noiseText + ".outAlpha") , (clampNoise + ".inputValue") , force = True)
		cmds.setAttr ((clampNoise + ".color[0].color_Position") , 0.525)
		cmds.setAttr ((clampNoise + ".color[1].color_Position") , 0.67)
		
		#Connect nodes to blend
		cmds.connectAttr((vtxMap + ".outAlpha") , (blendColors + ".blender") , force = True)
		cmds.connectAttr((clampNoise + ".outColor") , (blendColors + ".color1") , force = True)
		cmds.setAttr ((blendColors + ".color2") , 0 , 0 , 0 , type = "double3")
		
		#Connect blend to luminance
		cmds.connectAttr((blendColors + ".output") , (blendToValue + ".value") , force = True)
		
		#Connect luminance to clamp it
		cmds.connectAttr((blendToValue + ".outValue") , (clampBlend + ".inputValue") , force = True)
		cmds.setAttr ((clampBlend + ".value[0].value_Position") , 0.374)
		cmds.setAttr ((clampBlend + ".value[0].value_FloatValue") , 0)
		cmds.setAttr ((clampBlend + ".value[1].value_FloatValue") , 1)
		
		#Connect everything to the shader and the SG
		cmds.connectAttr((clampBlend + ".outColor") , (shader + ".outColor") , force = True)
		cmds.connectAttr((shader + ".outColor") , (wornSG + ".surfaceShader") , force = True)
		
		#Assign shader to object
		mel.eval('sets -forceElement ' + wornSG + ' ' + object + ';')
		

##--------------------------------------------------------------------------------------------
##def that makes the vertex paint
##--------------------------------------------------------------------------------------------
def pintarVertex (listaVertex , objeto) :
	"""def that makes the vertex paint"""
	
	colorMask = 0.0
	colorFondo = 0.0
	
	if cmds.radioButton("blackOverWhiteRADBTN", q = True , select = True) == True :
		colorMask = 0.0
		colorFondo = 1.0
	elif cmds.radioButton("whiteOverBlackRADBTN", q = True , select = True) == True :
		colorMask = 1.0
		colorFondo = 0.0
	
	#Finally, paint vertex
	numeroVertex = cmds.polyEvaluate(objeto , vertex = True)
	for i in range(0 , numeroVertex-1 , 1) :
		esteComponente = str(objeto + ".vtx[" + str(i) + "]")
		if listaVertex.count(esteComponente) >= 1 :
			cmds.polyColorPerVertex(esteComponente , notUndoable = True , colorDisplayOption = True , r = colorMask , g = colorMask , b = colorMask)
		else :
			cmds.polyColorPerVertex(esteComponente , notUndoable = True , colorDisplayOption = True , r = colorFondo , g = colorFondo , b = colorFondo)


##--------------------------------------------------------------------------------------------
##def based in the MEL proc by Joseph A. Hansen (Beyond Games)
##--------------------------------------------------------------------------------------------
def translatePolyInfoNormal (pin):
	"""def based in the MEL proc by Joseph A. Hansen (Beyond Games)"""

	#pin format: FACE_NORMAL      0: 0.000000 0.000000 1.000000
	#Take out everything but the vector and cast the vector's components in an array
	pin = pin[20:]
	pinSplitted = pin.split(" ")
	normal = [float(pinSplitted[0]) , float(pinSplitted[1]) , float(pinSplitted[2])]
	#Normalize
	normal = mel.eval('unit <<%f,%f,%f>>' %(normal[0] , normal[1] , normal[2]))
	
	return normal


##--------------------------------------------------------------------------------------------
##def that calculates the angle between two vectors
##--------------------------------------------------------------------------------------------
def angleBetweenVectors (vectorA,vectorB):
	"""def that calculates the angle between two vectors"""
	#Find the dot product
	dotProduct = (vectorA[0]*vectorB[0])+(vectorA[1]*vectorB[1])+(vectorA[2]*vectorB[2])
	#Find the vector lengths
	lenVectorA = math.sqrt( math.pow(vectorA[0],2) + math.pow(vectorA[1],2) + math.pow(vectorA[2],2) )
	lenVectorB = math.sqrt( math.pow(vectorB[0],2) + math.pow(vectorB[1],2) + math.pow(vectorB[2],2) )
	#Final ops
	finalVar = (dotProduct/(lenVectorA*lenVectorB))
	if finalVar > 1.0 :
	    finalVar = 1.0

	angleRad = math.acos(finalVar)
	angleDeg = math.degrees(angleRad)
	#Final return
	return angleDeg
	
	
#--------------------------------------------------------------------------------------------
##def that filters the hard edges
##--------------------------------------------------------------------------------------------
def filtrarBordes (objeto):
	"""def that filters the hard edges"""
	
	#List selected objects and for each object its edges
	each = objeto
	vtxList = []
	#User defined vars
	bordesCHKBOX = cmds.checkBox("openEdgesCHKBOX", q = True , v = True)
	anguloMax = cmds.floatField("maxAngleFF", q = True , v = True)
	anguloMin = cmds.floatField("minAngleFF", q = True , v = True)
	
	numeroEdges = cmds.polyEvaluate(each , edge = True)
	for i in range(0 , numeroEdges-1 , 1) :
		esteEdge = each + ".e[" + str(i) + "]"
		coFaces = cmds.polyListComponentConversion(esteEdge , toFace = True)
		#Expand the list (Maya returns compressed lists if the components are next to each other)
		coFacesExp = cmds.filterExpand(coFaces , selectionMask = 34 , expand = True)
		if len(coFacesExp) == 1 and bordesCHKBOX == True :
			estosVtx = cmds.polyListComponentConversion(esteEdge , toVertex = True)
			estosVtxExp = cmds.filterExpand(estosVtx , selectionMask = 31 , expand = True)
			vtxList += estosVtxExp
		
		if len(coFacesExp) > 1 :
			primerFaceInfo = cmds.polyInfo(coFacesExp[0] , faceNormals = True)
			primerFaceNormal = translatePolyInfoNormal(primerFaceInfo[0])
			segundoFaceInfo = cmds.polyInfo(coFacesExp[1] , faceNormals = True)
			segundoFaceNormal = translatePolyInfoNormal(segundoFaceInfo[0])
			anguloVectores = angleBetweenVectors(primerFaceNormal,segundoFaceNormal)
			#If the angle is inside the user defined threshold then add vtx to the list
			if (anguloVectores >= anguloMin) and (anguloVectores <= anguloMax) :
				estosVtx = cmds.polyListComponentConversion(esteEdge , toVertex = True)
				estosVtxExp = cmds.filterExpand(estosVtx , selectionMask = 31 , expand = True)
				vtxList += estosVtxExp
	
	#Execute paintVertex
	cleanVtxList = []
	for item in vtxList :
		if cleanVtxList.count(item) < 1:
			cleanVtxList.append(item)
	pintarVertex(cleanVtxList , each)
	

##--------------------------------------------------------------------------------------------
##def that shows an about window
##--------------------------------------------------------------------------------------------
def aboutWindow (*args):
	"""def that shows an about window"""
	
	if cmds.window("cgx_wornEdgesAbout" , exists = True) :
		cmds.deleteUI("cgx_wornEdgesAbout")

	cmds.window("cgx_wornEdgesAbout" , title = "cgx_wornEdgesAbout" , mxb = False , wh = (377,201) )
	cmds.columnLayout("mainColAbout" , adj = True)
	cmds.scrollField(h = 199 , wordWrap = True , editable = True , text = ("::cgx_wornEdges::" + "\n \nVersion: 2.0.0\nReleased: 18-12-2010" + "\nAuthor: Chris Granados- Xian \nchris.granados@xiancg.com http://chrisgranados.blogspot.com" + "\n \nScript based upon Neil Blevins' (http://www.neilblevins.com/cg_education/vertex_map_wear/vertex_map_wear.htm): Worn Edges Using A Distorted Vertex Map and his DVD for The Gnomon Workshop"))
	cmds.showWindow("cgx_wornEdgesAbout")	
	
	
##--------------------------------------------------------------------------------------------
##def that shows a help window
##--------------------------------------------------------------------------------------------
def helpWindow (*args):
	"""def that shows a help window"""
	
	if cmds.window("cgx_wornEdgesHelp" , exists = True) :
		cmds.deleteUI("cgx_wornEdgesHelp")

	cmds.window("cgx_wornEdgesHelp" , title = "cgx_wornEdgesHelp" , mxb = False , wh = (430,292) )
	cmds.columnLayout("mainColHelp" , adj = True)
	cmds.scrollField(h = 290 , wordWrap = True , editable = True , text = ("::cgx_wornEdges::" + "\n \nThis script paints hard edges, in a user defined threshold, using Vertex Paint." + "\n \nBASIC INSTRUCTIONS: " + "\n1. Select all the objects you want to apply this process to." + "\n2. Set your preferred settings." + "\n3. Hit the Paint them!! button and that's it. You can cancel any time by pressing ESC on your keyboard." + "\n \nOPTIONS: " + "\n>>Angle Threshold: Defines a range. Angles between the given range will be painted. NOTE: Every edge has one or two corresponding faces. The measured angle is the angle between the normals of those faces." + "\n>>Open Edges: If the surface is not completely closed then the open edges will be painted." + "\n>>Create MentalRay Vertex Color: Creates a mentalrayVertexColor node and connects it to each evaluated surface." + "\n>>Create base shading network: Uses the created map to create a basic shading network to start using the result right away. NOTE: This is only a base network. You should combine it with your own ideas to get the best results. Try, for example, using a Warp node like the one from www.binaryalchemy.de ." + "\n>>Black or white edges: Paints the edges black or white and the rest of the surface with the inverted color." + "\n \nTIPS: " + "\n-Visit Neil Blevins' web and read all the great info he has there for you. Remember this script was based on this tutorial by him http://www.neilblevins.com/cg_education/vertex_map_wear/vertex_map_wear.htm ." + "\n-Use a Warp Node to get better results. Try http://www.binaryalchemy.de/ ." + "\n-The script will return odd results if your surface is not All Quads." + "\n-Use Maya's Vertex Paint tools to fine tune the results." + "\n-If you have beveled corners a good start for Min Value is 40." + "\n \nScript based upon Neil Blevins' (http://www.neilblevins.com/cg_education/vertex_map_wear/vertex_map_wear.htm): Worn Edges Using A Distorted Vertex Map and his DVD for The Gnomon Workshop" + "\n \nAuthor: Chris Granados- Xian \nchris.granados@xiancg.com http://chrisgranados.blogspot.com"))
	cmds.showWindow("cgx_wornEdgesHelp")

	
##--------------------------------------------------------------------------------------------
##def that resets to default values
##--------------------------------------------------------------------------------------------		
def resetDefaults (*args):
	"""def that resets to default values"""

	cmds.floatField("minAngleFF" , edit = True , value = 85)
	cmds.floatField("maxAngleFF" , edit = True , value = 91)
	cmds.checkBox("openEdgesCHKBOX" , edit = True , v = True)
	cmds.checkBox("createMrVtxCHKBOX" , edit = True , v = False)
	cmds.checkBox("shadingNetCHKBOX" , edit = True , v = True , enable = False)
	cmds.radioButton("whiteOverBlackRADBTN" , edit = True , select = True)
	cmds.radioButton("blackOverWhiteRADBTN" , edit = True , select = False)

	
##--------------------------------------------------------------------------------------------
##def that changes shadingNetCHKBOX' enable state
##--------------------------------------------------------------------------------------------		
def mrVtxCreateChkBox (*args) :
	"""def para cambiar el estado del checkbox shadingNetCHKBOX"""
	
	if (cmds.checkBox("createMrVtxCHKBOX" , q = True, value = True) != True) :
		cmds.checkBox("shadingNetCHKBOX" , e = True , enable = False)
	else :
		cmds.checkBox("shadingNetCHKBOX" , e = True , enable = True)	
	
		
##--------------------------------------------------------------------------------------------
##def to open and close the Help frame and adjust the window height accordingly
##--------------------------------------------------------------------------------------------
def acortarVentana () :
	"""def to close the Help frame"""
	
	cmds.window("cgx_wornEdgesUI" , e = True , h = 200)
	
def alargarVentana () :
	"""def to open the Help frame"""
	
	cmds.window("cgx_wornEdgesUI" , e = True , h = 353)
	

##--------------------------------------------------------------------------------------------
##def to create the window
##--------------------------------------------------------------------------------------------
def cgx_wornEdges () :
	"""def to create the window"""
	
	if cmds.window("cgx_wornEdgesUI" , exists = True) :
		cmds.deleteUI("cgx_wornEdgesUI")
	
	cmds.window("cgx_wornEdgesUI" , title = "cgx_wornEdgesUI" , mxb = False , wh = (282,246) )
	
	cmds.columnLayout("mainCol" , adj = True)
	
	cmds.menuBarLayout("renamerMBL")
	cmds.menu(label = "Edit")
	cmds.menuItem(c = resetDefaults , label = "Reset")
	cmds.menu(label = "Help")
	cmds.menuItem(c = helpWindow , label = "Help")
	cmds.menuItem(c = aboutWindow , label = "About")
	
	cmds.frameLayout("wornEdgesFL" , label = "Worn Edges" , collapsable = True , marginHeight = 2 , marginWidth = 2 , collapse = False , borderStyle = "etchedOut")
	cmds.formLayout("wornEdgesFORM" , p = "wornEdgesFL")
	#form content --------------------------------------
	cmds.text("angleThresholdTXT" , label = "Angle Threshold: ")
	cmds.text("minAngleTXT" , label = "Min Angle")
	cmds.floatField("minAngleFF" , minValue = 0.0001 , maxValue = 360 , value = 85)
	cmds.text("maxAngleTXT" , label = "Max Angle")
	cmds.floatField("maxAngleFF" , minValue = 0.0001 , maxValue = 360 , value = 91)
	cmds.checkBox("openEdgesCHKBOX" , label = "Open Edges" , v = True)
	cmds.checkBox("createMrVtxCHKBOX" , label = "Create MentalRay Vertex Color" , v = False , changeCommand = mrVtxCreateChkBox)
	cmds.checkBox("shadingNetCHKBOX" , label = "Create base shading network" , v = True , enable = False)
	cmds.separator("separador1S" , w = 275)
	cmds.radioCollection ("radioCOL" , p = "wornEdgesFORM")
	cmds.radioButton("blackOverWhiteRADBTN" , collection = "radioCOL" , label = "Black edges" )
	cmds.radioButton("whiteOverBlackRADBTN" , collection = "radioCOL" , label = "White edges" , select = True)
	cmds.separator("separador2S" , w = 275)
	cmds.button("paintThemBTN" , l = "Paint them!!" , bgc = (0.0,0.465,0.764) , c = useShadingNet)
	cmds.separator("separador3S" , w = 275)
	cmds.text("processingTXT" , label = ("Processing: ") , enable = False)
	cmds.progressBar("progressBarPB" , maxValue = 100 , width = 150, enable = False)
	cmds.text("pressEscTXT" , label = ("(Press ESC to cancel)") , vis = False)
	#form content --------------------------------------
	cmds.formLayout("wornEdgesFORM" , e = True , attachForm = [('angleThresholdTXT','top',0) , ('angleThresholdTXT','left',2) , ('minAngleTXT','left',2) , ('openEdgesCHKBOX','left',2) , ('createMrVtxCHKBOX','left',2) , ('shadingNetCHKBOX','left',2) , ('separador1S','left',2) , ('separador1S','right',2) , ('blackOverWhiteRADBTN','left',2) , ('separador2S','left',2) , ('separador2S','right',2) , ('paintThemBTN','left',2) , ('paintThemBTN','right',2) , ('separador3S','left',2) , ('separador3S','right',2) , ('processingTXT','left',0) , ('processingTXT','right',0) , ('progressBarPB','left',4) , ('progressBarPB','bottom',2)] , attachControl = [('minAngleTXT','top',2,'angleThresholdTXT') , ('minAngleFF','top',0,'angleThresholdTXT') , ('minAngleFF','left',2,'minAngleTXT') , ('maxAngleTXT','top',2,'angleThresholdTXT') , ('maxAngleTXT','left',6,'minAngleFF') , ('maxAngleFF','top',0,'angleThresholdTXT') , ('maxAngleFF','left',2,'maxAngleTXT') , ('openEdgesCHKBOX','top',2,'maxAngleFF') , ('createMrVtxCHKBOX','top',2,'openEdgesCHKBOX') , ('shadingNetCHKBOX','top',2,'createMrVtxCHKBOX') , ('separador1S','top',2,'shadingNetCHKBOX') , ('blackOverWhiteRADBTN','top',2,'separador1S') , ('whiteOverBlackRADBTN','top',2,'separador1S') , ('whiteOverBlackRADBTN','left',2,'blackOverWhiteRADBTN') , ('separador2S','top',2,'blackOverWhiteRADBTN') , ('paintThemBTN','top',2,'separador2S') , ('separador3S','top',2,'paintThemBTN') , ('processingTXT','top',2,'separador3S') , ('progressBarPB','top',2,'processingTXT') , ('pressEscTXT','top',5,'processingTXT') , ('pressEscTXT','left',5,'progressBarPB')])
	cmds.setParent("mainCol")
	
	cmds.showWindow("cgx_wornEdgesUI")
	
	cmds.radioButton("whiteOverBlackRADBTN" , e = True , select = True)