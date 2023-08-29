import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
import maya.OpenMayaAnim as omAnim
import sys


class setTargetWeights(ompx.MPxCommand):

	def __init__(self):
		ompx.MPxCommand.__init__(self)
		self.shape_index = 0
		self.oldWeights = om.MFloatArray()
		self.newWeights = om.MFloatArray()
		self.validWeights = om.MFloatArray()

		self.deformerString = ''
		self.deformer_mObj = om.MObject()

		self.attribute_plug = om.MPlug()
		self.attributeString = ''

		self.inputDagPath = om.MDagPath()
		self.inputMObject = om.MObject()
		self.inputComponents = om.MObject()

		self.validDagPath = om.MDagPath()
		self.validComponents = om.MObject()

	def isUndoable(self):
		return True 

	def doIt(self, args):
		# Get the values of the arguments and the flags
		self.parseArgs(args)

		# Turn the values from the form they were passed
		# To the form you want them in
		self.processArgs()

		self.getOldWeights()
	
		return self.redoIt()

	def parseArgs(self,args):
		status = None
		argLength = args.length()

		dataBase = om.MArgDatabase(self.syntax(),args)

		# Get the object list
		self.objectStringArray = []
		dataBase.getObjects(self.objectStringArray)

		# Get the deformer name
		if dataBase.isFlagSet("-d"):
			self.deformerString = dataBase.flagArgumentString("-d", 0)	
		else:
			sys.stderr.write('This command requires the deformer flag to be used')
			return

		# Get the attribute name
		if dataBase.isFlagSet("-a"):
			self.attributeString = dataBase.flagArgumentString("-a", 0)	

		# Get the weights
		if dataBase.isFlagSet("-w"):
			for i in range(dataBase.numberOfFlagUses("-w")):
				weights_argList = om.MArgList()
				dataBase.getFlagArgumentList("-w",i,weights_argList)
				self.newWeights.append(weights_argList.asDouble(0))	

	def processArgs(self):
		# Convert deformer node to MObject
		sel = om.MSelectionList()
		sel.add(self.deformerString)
		deformer_mObj = om.MObject()
		sel.getDependNode(0, self.deformer_mObj)

		if not self.deformer_mObj.hasFn(om.MFn.kGeometryFilt):
			sys.stderr.write('{} is not a deformer'.format(deformer_node))

		# Convert the object stringArray to an MSelectionsList
		stringSel = om.MSelectionList()
		for eachItem in self.objectStringArray:
			stringSel.add(eachItem)

		# Limit the MSelectionList to 1 item
		stringSel.getDagPath(0,self.inputDagPath,self.inputComponents)
		stringSel.getDependNode(0,self.inputMObject)

		# If the inputComponents are NULL then we will use the whole component set
		if self.inputComponents.isNull():
			mFn_validComponents = om.MFnSingleIndexedComponent()
			validComps = mFn_validComponents.create(om.MFn.kMeshVertComponent);
			mit = om.MItGeometry(self.inputDagPath);
			mFn_validComponents.setCompleteData(mit.count())
			self.inputComponents = validComps

		
		# Get the shape id from the deformerSet
		# And restrict the stringSel to the deformerSet
		hasValiSel = self.getValidSel()
		if not hasValiSel:
			cmds.error("sel invalid")

		# Convert the attribute to a plug
		if self.attributeString:
			# Check if that attribute is valid
			mFnDepend = om.MFnDependencyNode(self.deformer_mObj)
			weights_plug = mFnDepend.findPlug(self.attributeString.split('.')[-1], False)

			# It needs to be an array
			if not weights_plug.isArray():
				sys.stderr.write('{} is not a valid weights plug for {} because it is not an array.'.format(weights_plug.name(),deformer_node))
				return

			# It has to have a parent
			if not weights_plug.isChild():
				sys.stderr.write('{} is not a valid weights plug for {} because it has no parent'.format(weights_plug.name(),deformer_node))
				return

			# The parent needs to be an array
			if not weights_plug.parent().isElement():
				sys.stderr.write('{} is not a valid weights plug for {} because it\'s parent is not an array.'.format(weights_plug.name(),deformer_node))
				return

			# It can't have any children
			if weights_plug.isCompound():
				sys.stderr.write('{} is not a valid weights plug for {} because it has children'.format(weights_plug.name(),deformer_node))
				return

			# Get the index for each parent of the attribute
			# blahblah[0].blahblah[0].weightList[-1].weights
			# We ignore the last two attributes because one is weights[*]
			# And the other is the per-shape weightList attribute
			# And we get the index for that based on the provided shape
			parentTokens = reversed(self.attributeString.split('.')[:-2])
			parent_indices = [int(x.split('[')[-1][:-1]) for x in parentTokens]
			parent_indices.insert(0,self.shape_index)

			# Step up through the attribute heirarchy and assign the right element
			currentPlug = om.MPlug(weights_plug)
			for parent_id in parent_indices:
			    if currentPlug.isElement():
			        currentPlug = currentPlug.array()

			    currentPlug = currentPlug.parent()
			    weights_plug.selectAncestorLogicalIndex(parent_id,currentPlug.attribute())

			self.attribute_plug = weights_plug
			
	def getValidSel(self):
		# Get the  contents of the deformerSet
		members = om.MSelectionList()
		mFnGeometryFilter = omAnim.MFnGeometryFilter(self.deformer_mObj)
		mFnSet = om.MFnSet(mFnGeometryFilter.deformerSet())
		mFnSet.getMembers(members, False)

		# Get the element in the deformerSet that is for
		# The shape we are setting weights on 
		member_index = -1
		for i in range(members.length()):
			members_mObj = om.MObject()
			members.getDependNode(i, members_mObj)
			if (members_mObj == self.inputMObject):
				member_index = i
				break

		if member_index == -1:
			sys.stderr.write('The specified shape is not deformed'.format())
			return

		# Get the dagPath and components from the deformerSet
		membersDagPath = om.MDagPath()
		membersComponents = om.MObject()	
		members.getDagPath(member_index, membersDagPath, membersComponents)

		validComps = om.MObject() 
		self.validWeights = om.MFloatArray()
		# Get the component ids for the deformerSet components
		membersTInts = om.MIntArray()
		membersUInts = om.MIntArray()
		membersVInts = om.MIntArray()
		activeTInts = om.MIntArray()
		activeUInts = om.MIntArray()
		activeVInts = om.MIntArray()
		hasComps = False

		if (membersComponents.hasFn(om.MFn.kMeshVertComponent) or 
			membersComponents.hasFn(om.MFn.kCurveCVComponent)):

			mFnMemberComps = om.MFnSingleIndexedComponent(membersComponents)
			mFnMemberComps.getElements(membersUInts)
			mFnActiveComps = om.MFnSingleIndexedComponent(self.inputComponents)
			mFnActiveComps.getElements(activeUInts)

			# Prepare to create the valid components
			mFn_validComponents = om.MFnSingleIndexedComponent()
			if (membersComponents.hasFn(om.MFn.kMeshVertComponent)):
				validComps = mFn_validComponents.create(om.MFn.kMeshVertComponent)

			elif (membersComponents.hasFn(om.MFn.kCurveCVComponent)):
				validComps = mFn_validComponents.create(om.MFn.kCurveCVComponent)

			# For each id in the selection
			for k in range(activeUInts.length()):
				# Check each id in the deformerSet
				for m in range(membersUInts.length()):
					# If they match that id is valid
					if (activeUInts[k] == membersUInts[m]):
						mFn_validComponents.addElement(activeUInts[k])
						self.validWeights.append(self.newWeights[k])
						hasComps = True
						break

		elif (membersComponents.hasFn(om.MFn.kSurfaceCVComponent)):
			mFnMemberComps = om.MFnDoubleIndexedComponent(membersComponents)
			mFnMemberComps.getElements(membersUInts, membersVInts)
			mFnActiveComps = MFnDoubleIndexedComponent()
			mFnActiveComps.getElements(activeUInts, activeVInts)

			# Prepare to create the valid components
			mFn_validComponents = om.MFnDoubleIndexedComponent()
			if (membersComponents.hasFn(om.MFn.kSurfaceCVComponent)):
				validComps = mFn_validComponents.create(om.MFn.kSurfaceCVComponent)

			# Get the intersection of them
			# For each id in the selection
			for k in range(activeUInts.length()):
				# Check each id in the deformerSet
				for m in range(membersUInts.length()):
					#if they match that id is valid
					if (activeUInts[k] == membersUInts[m] and
						activeVInts[k] == membersVInts[m]):

						mFn_validComponents.addElement(activeUInts[k], activeVInts[k])
						self.validWeights.append(self.newWeights[k])
						hasComps = True
						break

		elif (membersComponents.hasFn(om.MFn.kLatticeComponent)):
			mFnMemberComps = om.MFnTripleIndexedComponent(membersComponents)
			mFnMemberComps.getElements(membersTInts, membersUInts, membersVInts)
			mFnActiveComps = om.MFnTripleIndexedComponent(self.inputComponents)
			mFnActiveComps.getElements(activeTInts, activeUInts, activeVInts)

			#prepare to create the valid components
			mFn_validComponents = om.MFnTripleIndexedComponent()
			if (membersComponents.hasFn(om.MFn.kLatticeComponent)):
				validComps = mFn_validComponents.create(om.MFn.kLatticeComponent)

			#get the intersection of them
			#for each id in the selection
			for k in range(activeUInts.length()):
				# Check each id in the deformerSet
				for m in range(membersUInts.length()):
					#if they match that id is valid
					if (activeTInts[k] == membersTInts[m] and
						activeUInts[k] == membersUInts[m] and
						activeVInts[k] == membersVInts[m]):

						mFn_validComponents.addElement(activeTInts[k], activeUInts[k], activeVInts[k])
						self.validWeights.append(self.newWeights[k])
						hasComps = True
						break

		if (hasComps):
			self.validDagPath = membersDagPath#!!!
			self.validComponents = validComps

		# Get the plug index being used by the shape
		self.shape_index = mFnGeometryFilter.indexForOutputShape(self.inputMObject)

		return True

	def getOldWeights(self):
		# If the user provided a specific attribute
		if self.attributeString:
			# Prepare the iterator
			mit = om.MItGeometry(self.validDagPath,self.validComponents)			

			# Get all the weights and store them for undo
			while not mit.isDone():
				comp_index = mit.index()
				self.oldWeights.append(self.attribute_plug.elementByLogicalIndex(comp_index).asFloat())
				mit.next()

		# If it isn't a weightedGeometryFilter
		elif self.deformer_mObj.hasFn(om.MFn.kWeightGeometryFilt):
			#get the old weights and store them for undo
			mFnWeight = omAnim.MFnWeightGeometryFilter(self.deformer_mObj)
			mFnWeight.getWeights(self.validDagPath, self.validComponents, self.oldWeights)

	def redoIt(self):
		if self.attributeString:
			# Prepare the iterator
			mit = om.MItGeometry(self.validDagPath,self.validComponents)			
			# Get all the weights and store them for undo
			mdg = om.MDGModifier()
			i = 0

			# Force an update by setting the first element
			zeroPlug = self.attribute_plug.elementByLogicalIndex(0)
			mdg.newPlugValueFloat(zeroPlug,zeroPlug.asFloat())

			while not mit.isDone():
				comp_index = mit.index()
				mdg.newPlugValueFloat(self.attribute_plug.elementByLogicalIndex(comp_index),self.validWeights[i])
				mit.next()
				i += 1

			mdg.doIt()

		elif  self.deformer_mObj.hasFn(om.MFn.kWeightGeometryFilt):
			# Create the function set to set weights
			mFnWeight = omAnim.MFnWeightGeometryFilter(self.deformer_mObj)
			mFnWeight.setWeight(self.validDagPath, self.shape_index, self.validComponents, self.validWeights)
			
	def undoIt(self):
		if self.attributeString:
			# Prepare the iterator
			mit = om.MItGeometry(self.validDagPath, self.validComponents)			
			# Get all the weights and store them for undo
			mdg = om.MDGModifier()
			i = 0

			# Force an update by setting the first element
			zeroPlug = self.attribute_plug.elementByLogicalIndex(0)
			mdg.newPlugValueFloat(zeroPlug,zeroPlug.asFloat())

			while not mit.isDone():
				comp_index = mit.index()
				mdg.newPlugValueFloat(self.attribute_plug.elementByLogicalIndex(comp_index),self.oldWeights[i])
				mit.next()
				i += 1

			mdg.doIt()

		elif self.deformer_mObj.hasFn(om.MFn.kWeightGeometryFilt):
			mFnWeight = omAnim.MFnWeightGeometryFilter(self.deformer_mObj)
			mFnWeight.setWeight(self.validDagPath, self.shape_index, self.validComponents, self.oldWeights)

def newSyntax():
	syntax = om.MSyntax()
	syntax.setObjectType(om.MSyntax.kStringObjects ,1); # Objects
	syntax.useSelectionAsDefault(False);
	#syntax.addArg(om.MSyntax.kSelectionItem) # Selection list
	#syntax.addArg(om.MSyntax.kString) # Deformer
	syntax.enableQuery(False)
	syntax.enableEdit(False)
	syntax.addFlag('-d', '-deformer', om.MSyntax.kString)
	syntax.addFlag('-a', '-attribute', om.MSyntax.kString)
	syntax.addFlag('-w', '-weights', om.MSyntax.kDouble)
	syntax.makeFlagMultiUse('-w')
	return syntax

def creator():
	return ompx.asMPxPtr(setTargetWeights())

#
# The following routines are used to register/unregister
# the command we are creating within Maya
#
def initializePlugin(obj):
	plugin = ompx.MFnPlugin(obj, 'J Reinhart', "4.0", "Any")
	try:
		status = plugin.registerCommand("setDeformerWeights",
		creator,
		newSyntax)	
	except:
		cmds.error("Failed to register command")
		raise

	return

def uninitializePlugin(obj):
	plugin = ompx.MFnPlugin(obj)
	try:
		plugin.deregisterCommand("setDeformerWeights")
	except:
		cmds.error("Failed to deregister command")
		raise

	return