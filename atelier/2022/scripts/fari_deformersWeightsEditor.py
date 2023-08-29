'''
    SCRIPT NAME:
        fari_deformersWeightsEditor

    AUTHOR:
        Paolo Farinello - paolo.farinello@gmail.com

    DESCRIPTION:
        Enables operations such as import/export, copy, mirror and flip on deformers weights, focusing on deformers which differ from the skinCluster.
        Affected deformers are: blend shape, cluster, lattice, non-linear, shrinkwrap and wire deformers.

    INSTALL:
        1. Put the script file in Maya scripts folder
        2. In a python tab type the following: import fari_deformersWeightsEditor; reload(fari_deformersWeightsEditor)

    LOG:
        Version: 1.0.0
        Date: 10 August 2021
        - First release
'''

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds
import os
import sys
import json
from builtins import object as builtin_object
    
class DeformersWeightsEditor(builtin_object):

    @classmethod
    def showUI(cls):
        win = cls()
        win.create()
        cmds.textFieldButtonGrp(win.importExportGroup,edit=True,fileName=win.workingDir)
        return win

    def __init__(self):
        super(DeformersWeightsEditor,self).__init__()
        self.winName = 'DWEwindow'
        self.winTitle = 'Deformers Weights Editor'
        self.winSize = (600,540)
        self.workingDir = cmds.workspace(query=True,directory=True)
        self.validDeformers = ['blendShape','cluster','ffd','nonLinear','shrinkWrap','wire']
        self.symmetryAxis = {1:(0,[-1,1,1]),2:(1,[1,-1,1]),3:(2,[1,1,-1])}
        self.copySourceInfo = []
        self.copyTargetInfo = []

    def create(self):
        if(cmds.window(self.winName,exists=True)):
            cmds.deleteUI(self.winName,window=True)
        cmds.window(self.winName,title=self.winTitle,widthHeight=self.winSize,sizeable=True)
        
        self.mainForm = cmds.formLayout(numberOfDivisions=100)
        self.deformerFrame = cmds.frameLayout(parent=self.mainForm,label='Deformer Select',collapsable=True)
        self.importExportFrame = cmds.frameLayout(parent=self.mainForm,label='Weights Import/Export',collapsable=True)  
        self.mirrorFrame = cmds.frameLayout(parent=self.mainForm,label='Weights Mirror',collapsable=True) 
        self.copyFrame = cmds.frameLayout(parent=self.mainForm,label='Weights Copy',collapsable=True)              
        cmds.formLayout(self.mainForm,edit=True,
                        attachForm=([self.deformerFrame,'top',0],[self.deformerFrame,'left',0],[self.deformerFrame,'right',0],[self.importExportFrame,'left',0],[self.importExportFrame,'right',0],[self.mirrorFrame,'left',0],[self.mirrorFrame,'right',0],[self.copyFrame,'left',0],[self.copyFrame,'right',0]),
                        attachControl=([self.importExportFrame,'top',10,self.deformerFrame],[self.mirrorFrame,'top',10,self.importExportFrame],[self.copyFrame,'top',10,self.mirrorFrame]))
       
        self.deformerForm = cmds.formLayout(parent=self.deformerFrame,numberOfDivisions=100)
        self.meshGroup = cmds.textFieldButtonGrp(parent=self.deformerForm,label='Mesh:',buttonLabel='<<<',adjustableColumn=2,columnAttach3=['left','left','left'],columnWidth3=[30,100,100],columnOffset3=[0,10,10],buttonCommand=self.meshButton,changeCommand=self.meshText)
        self.deformersText = cmds.text(parent=self.deformerForm,label='Deformers:')        
        self.deformersList = cmds.textScrollList(parent=self.deformerForm,allowMultiSelection=False,numberOfRows=1,height=100,width=455)        
        cmds.formLayout(self.deformerForm,edit=True,
                        attachForm=([self.meshGroup,'top',5],[self.meshGroup,'left',5],[self.meshGroup,'right',5],[self.deformersText,'left',5]),
                        attachControl=([self.deformersText,'top',5,self.meshGroup],[self.deformersList,'top',5,self.meshGroup],[self.deformersList,'left',5,self.deformersText]))                

        self.importExportForm = cmds.formLayout(parent=self.importExportFrame,numberOfDivisions=100)
        self.importExportGroup = cmds.textFieldButtonGrp(parent=self.importExportForm,label='Start Directory:',buttonLabel='Browse',adjustableColumn=2,columnAttach3=['left','left','left'],columnWidth3=[75,100,100],columnOffset3=[0,10,10],buttonCommand=self.dirBrowser,changeCommand=self.inputDir)
        self.loadParameters = cmds.text(parent=self.importExportForm,label='Load Parameters:')
        self.loadVertices = cmds.radioButtonGrp(parent=self.importExportForm,numberOfRadioButtons=2,label='Algorithm:',labelArray2=['vertex index','vertex position'],select=1,columnAttach3=['left','left','left'],columnWidth3=[60,100,100],columnOffset3=[0,0,0],onCommand1=self.indexAlgorithm,onCommand2=self.positionAlgorithm)        
        self.loadTolerance = cmds.textFieldGrp(parent=self.importExportForm,label='Tolerance:',adjustableColumn=2,columnAttach2=['left','left'],columnWidth2=[55,100],columnOffset2=[0,0],text='0.1',enable=False,changeCommand=self.setTolerance,annotation='Tolerance must be of type "float". Only positive, non-zero values are allowed')
        self.saveButton = cmds.button(parent=self.importExportForm,label='Save Weights',width=150,command=self.saveWeights,annotation='Select the vertices whose weights to be saved')
        self.loadButton = cmds.button(parent=self.importExportForm,label='Load Weights',width=150,command=self.loadWeights,annotation='Select the vertices whose weights to be loaded')        
        cmds.formLayout(self.importExportForm,edit=True,
                        attachForm=([self.importExportGroup,'top',5],[self.importExportGroup,'left',5],[self.importExportGroup,'right',5],[self.loadParameters,'left',5],[self.loadVertices,'left',50],[self.saveButton,'left',125]),
                        attachControl=([self.loadParameters,'top',5,self.importExportGroup],[self.loadVertices,'top',5,self.loadParameters],[self.loadTolerance,'top',5,self.loadParameters],[self.loadTolerance,'left',50,self.loadVertices],[self.saveButton,'top',10,self.loadVertices],[self.loadButton,'top',10,self.loadVertices],[self.loadButton,'left',50,self.saveButton]))        
        
        self.mirrorForm = cmds.formLayout(parent=self.mirrorFrame,numberOfDivisions=100)
        self.symmetryPlane = cmds.radioButtonGrp(parent=self.mirrorForm,numberOfRadioButtons=3,label='Symmetry Plane:',labelArray3=['YZ','XZ','XY'],select=1,columnAttach4=['left','left','left','left'],columnOffset4=[0,0,0,0],columnWidth4=[100,80,80,80],annotation='Symmertry plane refers to the selected mesh local axes')
        self.symmetryDirection = cmds.radioButtonGrp(parent=self.mirrorForm,numberOfRadioButtons=2,label='Direction:',labelArray2=['from positive to negative','from negative to positive'],select=1,columnAttach3=['left','left','left'],columnOffset3=[0,0,0],columnWidth3=[100,200,200])
        self.mirrorButton = cmds.button(parent=self.mirrorForm,label='Mirror Weights',command=self.mirrorWeights,annotation='Select the vertices whose weights to be mirrored',width=150) 
        self.flipButton = cmds.button(parent=self.mirrorForm,label='Flip Weights',command=self.flipWeights,annotation='Select the vertices whose weights to be flipped',width=150)        
        cmds.formLayout(self.mirrorForm,edit=True,
                        attachForm=([self.symmetryPlane,'top',5],[self.symmetryPlane,'left',5],[self.symmetryDirection,'left',5],[self.mirrorButton,'left',125]),
                        attachControl=([self.symmetryDirection,'top',5,self.symmetryPlane],[self.mirrorButton,'top',10,self.symmetryDirection],[self.flipButton,'top',10,self.symmetryDirection],[self.flipButton,'left',50,self.mirrorButton]))
        
        self.copyForm = cmds.formLayout(parent=self.copyFrame,numberOfDivisions=100)
        self.sourceButton = cmds.button(parent=self.copyForm,label='Source',command=self.copySource,annotation='Select the deformer to copy weights from',width=100) 
        self.sourceText = cmds.text(parent=self.copyForm,label=' - Select a valid deformer from the deformers list above')
        self.targetButton = cmds.button(parent=self.copyForm,label='Target',command=self.copyTarget,annotation='Select the deformer to copy weights to',width=100)         
        self.targetText = cmds.text(parent=self.copyForm,label=' - Select a valid deformer from the deformers list above')
        self.copyButton = cmds.button(parent=self.copyForm,label='Copy',command=self.copyWeights,annotation='Select valid source and target deformers',width=150) 
        cmds.formLayout(self.copyForm,edit=True,
                        attachForm=([self.sourceButton,'top',5],[self.sourceButton,'left',10],[self.sourceText,'top',10],[self.targetButton,'left',10],[self.copyButton,'left',225]),
                        attachControl=([self.sourceText,'left',10,self.sourceButton],[self.targetButton,'top',5,self.sourceButton],[self.targetText,'top',15,self.sourceText],[self.targetText,'left',10,self.targetButton],[self.copyButton,'top',5,self.targetButton]))        

        cmds.showWindow()
       
    def getDeformers(self,target):        
        try:
            selList = om.MSelectionList()
            selList.add(target)
        except RuntimeError:
            raise ValueError('Current scene does not contain any "{Name}" node'.format(Name=target))                
        targetObj = selList.getDependNode(0)
        targetType = targetObj.apiTypeStr
        if (targetType == 'kTransform'):        
            targetDAG = selList.getDagPath(0)
            targetShape = targetDAG.extendToShape(0)
            targetObj = targetShape.node()
            targetType = targetObj.apiTypeStr
        if not (targetType == 'kMesh'):    
            raise ValueError('Select a valid mesh to display its deformers')
        deformersList = []
        targetFn = om.MFnDependencyNode(targetObj)
        targetPlug_IOG = targetFn.findPlug('instObjGroups',True)
        IOG_indexArray = targetPlug_IOG.getExistingArrayAttributeIndices()
        for index_IOG in IOG_indexArray:
            targetPlug_OG = targetPlug_IOG.elementByLogicalIndex(index_IOG).child(0)        
            OG_indexArray = targetPlug_OG.getExistingArrayAttributeIndices()
            for index_OG in OG_indexArray:
                deformerSet_DSMplug = targetPlug_OG.elementByLogicalIndex(index_OG).connectedTo(False,True)
                if deformerSet_DSMplug:
                    deformerSet_obj = deformerSet_DSMplug[0].node()                                             
                    deformerSet_Fn = om.MFnDependencyNode(deformerSet_obj)
                    try:
                        deformerSet_UBplug = deformerSet_Fn.findPlug('usedBy',True)
                        UB_indexArray = deformerSet_UBplug.getExistingArrayAttributeIndices()
                    except RuntimeError:
                        wrongSet = deformerSet_Fn.name()
                        cmds.warning('Node "{Name}" does not have any attribute "usedBy"'.format(Name=wrongSet))
                        continue
                    for index_UB in UB_indexArray:
                        deformerPlug_message = deformerSet_UBplug.elementByLogicalIndex(index_UB).connectedTo(True,False)
                        if deformerPlug_message:
                            deformer_obj = deformerPlug_message[0].node()                                        
                            deformer_Fn = om.MFnDependencyNode(deformer_obj)
                            deformer_name = deformer_Fn.name()
                            deformer_type = deformer_Fn.typeName
                            if deformer_type in self.validDeformers:
                                deformersList.append({'Name':deformer_name,'Type':deformer_type})
        if deformersList:
            def customSort(listElement):
                return listElement['Type']+listElement['Name']
            deformersList.sort(key=customSort)
            return deformersList
        else:
            return None   
            
    def deformersScrollList(self,mesh):
        cmds.textScrollList(self.deformersList,edit=True,removeAll=True)
        try:
            deformersList = self.getDeformers(mesh)
        except ValueError as VE:
            if mesh:
                raise
            else:
                return
        if deformersList:
            for token in deformersList:
                newEntry = token['Type'] + ' - ' + token['Name']
                cmds.textScrollList(self.deformersList,edit=True,append=newEntry)
        else:
            cmds.warning('No valid deformer applies to the selected mesh')  
           
    def meshButton(self):
        selList = om.MGlobal.getActiveSelectionList(orderedSelectionIfAvailable=True)      
        numberOfItems = selList.length()
        if numberOfItems:
            lastItem = selList.getSelectionStrings(numberOfItems-1)[0]
        else:
            lastItem = ''
        cmds.textFieldButtonGrp(self.meshGroup,edit=True,text=lastItem)
        self.deformersScrollList(lastItem)
        
    def meshText(self,input_text):
        self.deformersScrollList(input_text)        

    def getTargetShape(self):
        target = cmds.textFieldButtonGrp(self.meshGroup,query=True,text=True)
        selection = om.MSelectionList()
        selection.add(target)
        target_dag = selection.getDagPath(0)
        target_shape = target_dag.extendToShape(0)
        return target_shape

    def dirBrowser(self):
        inputDir = cmds.textFieldButtonGrp(self.importExportGroup,query=True,fileName=True)
        oldDir = inputDir
        if not os.path.isdir(inputDir):
            oldDir = self.workingDir
        startDir = cmds.fileDialog2(dialogStyle=1,caption='Select Start Directory',startingDirectory=oldDir,fileMode=3)
        if startDir:
            cmds.textFieldButtonGrp(self.importExportGroup,edit=True,fileName=startDir[0])
            
    def inputDir(self,input_text):                                                                       
        startDir = cmds.textFieldButtonGrp(self.importExportGroup,query=True,fileName=True)        
        if not os.path.isdir(startDir):
            cmds.warning('Invalid start directory: default directory will be used instead')        

    def findTargetIndex(self,deformerObj,target_shape):
        target_index = []
        deformerFn = oma.MFnGeometryFilter(deformerObj)
        outputGeoCount = deformerFn.numOutputConnections()
        for index in range(0,outputGeoCount):
            plugIndex = deformerFn.indexForOutputConnection(index)
            outputGeo = deformerFn.getPathAtIndex(plugIndex)
            if (outputGeo == target_shape):
                target_index.append(plugIndex)
                break
        return target_index
                                                 
    def getDeformerWeights(self,Target=None,ID=None,DeformerName=None):        
        weightsMap = {}
        if Target:                                                   
            target_shape = Target
            selection = om.MSelectionList()
            try:
                selection.add(target_shape)
            except:
                raise ValueError('Target "' + str(target_shape) + '" does not exist')
            test_node = selection.getDependNode(0)
            test_type = test_node.apiTypeStr
            if not test_type == 'kMesh':
                raise ValueError('Target "' + str(target_shape) + '" is not a valid mesh')
        else:
            target_shape = self.getTargetShape()     
        if DeformerName:
            deformer_name = DeformerName
            selection = om.MSelectionList()
            try:
                selection.add(deformer_name)
            except:
                raise ValueError('Deformer "' + str(deformer_name) + '" does not exist')            
        else:
            deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
            deformer_entry = deformerEntry_list[0].split(' - ')
            deformer_name = deformer_entry[1]            
        deformer_selection = om.MSelectionList()
        deformer_selection.add(deformer_name)
        deformerObj = deformer_selection.getDependNode(0)
        deformerFn = om.MFnDependencyNode(deformerObj)
        target_index = self.findTargetIndex(deformerObj,target_shape)
        if not target_index:
            raise ValueError('"{Name1}" does not affect "{Name2}"'.format(Name1=deformer_name,Name2=target_shape))
        if ID:
            memberID = ID
            nonMemberID = []
            target_fn = om.MFnMesh(target_shape)
            target_vtxCount = target_fn.numVertices
            target_vtx = list(range(0,target_vtxCount))
            for element in ID:
                if not element in target_vtx:
                    raise ValueError('Vertex ID ' + str(element) + ' does not belong to mesh "' + str(target_shape) + '"')
            deformerFilter = oma.MFnGeometryFilter(deformerObj)        
            deformerSet = deformerFilter.deformerSet
            fnSet = om.MFnSet(deformerSet)
            setMembers = fnSet.getMembers(flatten=True)
            component_fn = om.MFnSingleIndexedComponent() 
            vtx_component = component_fn.create(om.MFn.kMeshVertComponent)
            component_fn.addElements(ID) 
            vertices_iterator = om.MItMeshVertex(target_shape,vtx_component) 
            while not vertices_iterator.isDone():
                current_vtxComponent = vertices_iterator.currentItem()
                if not setMembers.hasItem((target_shape,current_vtxComponent)):
                    current_index = vertices_iterator.index()
                    nonMemberID.append(current_index)
                    memberID.remove(current_index)
                next(vertices_iterator)                 
        else:
            memberID = []
            nonMemberID = []
            deformerFilter = oma.MFnGeometryFilter(deformerObj)        
            deformerSet = deformerFilter.deformerSet
            fnSet = om.MFnSet(deformerSet)
            setMembers = fnSet.getMembers(flatten=True)
            components_selection = om.MGlobal.getActiveSelectionList()
            components_iterator = om.MItSelectionList(components_selection,om.MFn.kMeshVertComponent)
            if components_iterator.isDone():
                raise ValueError('Select the mesh vertices to operate on')
            while not components_iterator.isDone():
                component = components_iterator.getComponent()
                vertices_iterator = om.MItMeshVertex(component[0],component[1])
                if not (component[0].extendToShape(0) == target_shape): 
                    raise ValueError('The selected vertices do not belong to "{Name}"'.format(Name=target_shape))
                while not vertices_iterator.isDone():
                    current_vtxComponent = vertices_iterator.currentItem()
                    if setMembers.hasItem((component[0],current_vtxComponent)):
                        memberID.append(vertices_iterator.index())
                    else:
                        nonMemberID.append(vertices_iterator.index())
                    next(vertices_iterator)
                next(components_iterator)                      
        deformerPlug_WL = deformerFn.findPlug('weightList',True)
        WL_indexArray = deformerPlug_WL.getExistingArrayAttributeIndices() 
        if target_index[0] in WL_indexArray:
            deformerPlug_W = deformerPlug_WL.elementByLogicalIndex(target_index[0]).child(0)
            W_indexArray = deformerPlug_W.getExistingArrayAttributeIndices()
            for token in W_indexArray:
                if token in memberID:
                    weightsMap.setdefault(token,deformerPlug_W.elementByLogicalIndex(token).asFloat())
                    memberID.remove(token)
        for token in memberID:
            weightsMap.setdefault(token,1)
        for token in nonMemberID:
            weightsMap.setdefault(token,0)
        if weightsMap:
            return weightsMap 
            
    def getBlendShapeWeights(self,Target=None,ID=None,DeformerName=None):        
        weightsMap = {}
        if Target:                                                   
            target_shape = Target
            selection = om.MSelectionList()
            try:
                selection.add(target_shape)
            except:
                raise ValueError('Target "' + str(target_shape) + '" does not exist')
            test_node = selection.getDependNode(0)
            test_type = test_node.apiTypeStr
            if not test_type == 'kMesh':
                raise ValueError('Target "' + str(target_shape) + '" is not a valid mesh')
        else:
            target_shape = self.getTargetShape()
        if DeformerName:
            deformer_name = DeformerName
            selection = om.MSelectionList()
            try:
                selection.add(deformer_name)
            except:
                raise ValueError('Deformer "' + str(deformer_name) + '" does not exist') 
        else:                
            deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
            deformer_entry = deformerEntry_list[0].split(' - ')
            deformer_name = deformer_entry[1]
        deformer_selection = om.MSelectionList()
        deformer_selection.add(deformer_name)
        deformerObj = deformer_selection.getDependNode(0)
        deformerFn = om.MFnDependencyNode(deformerObj)
        target_index = self.findTargetIndex(deformerObj,target_shape)
        if not target_index:
            raise ValueError('"{Name1}" does not affect "{Name2}"'.format(Name1=deformer_name,Name2=target_shape))        
        if ID:
            memberID = ID
            nonMemberID = []
            target_fn = om.MFnMesh(target_shape)
            target_vtxCount = target_fn.numVertices
            target_vtx = list(range(0,target_vtxCount))
            for element in ID:
                if not element in target_vtx:
                    raise ValueError('Vertex ID ' + str(element) + ' does not belong to mesh "' + str(target_shape) + '"')
            deformerFilter = oma.MFnGeometryFilter(deformerObj)        
            deformerSet = deformerFilter.deformerSet
            fnSet = om.MFnSet(deformerSet)
            setMembers = fnSet.getMembers(flatten=True)
            component_fn = om.MFnSingleIndexedComponent() 
            vtx_component = component_fn.create(om.MFn.kMeshVertComponent)
            component_fn.addElements(ID) 
            vertices_iterator = om.MItMeshVertex(target_shape,vtx_component) 
            while not vertices_iterator.isDone():
                current_vtxComponent = vertices_iterator.currentItem()
                if not setMembers.hasItem((target_shape,current_vtxComponent)):
                    current_index = vertices_iterator.index()
                    nonMemberID.append(current_index)
                    memberID.remove(current_index)
                next(vertices_iterator)                 
        else:
            memberID = []
            nonMemberID = []
            deformerFilter = oma.MFnGeometryFilter(deformerObj)        
            deformerSet = deformerFilter.deformerSet
            fnSet = om.MFnSet(deformerSet)
            setMembers = fnSet.getMembers(flatten=True)
            components_selection = om.MGlobal.getActiveSelectionList()
            components_iterator = om.MItSelectionList(components_selection,om.MFn.kMeshVertComponent)
            if components_iterator.isDone():
                raise ValueError('Select the mesh vertices to operate on')
            while not components_iterator.isDone():
                component = components_iterator.getComponent()
                vertices_iterator = om.MItMeshVertex(component[0],component[1])
                if not (component[0].extendToShape(0) == target_shape): 
                    raise ValueError('The selected vertices do not belong to "{Name}"'.format(Name=target_shape))
                while not vertices_iterator.isDone():
                    current_vtxComponent = vertices_iterator.currentItem()
                    if setMembers.hasItem((component[0],current_vtxComponent)):
                        memberID.append(vertices_iterator.index())
                    else:
                        nonMemberID.append(vertices_iterator.index())
                    next(vertices_iterator)
                next(components_iterator)      
        deformerPlug_IT = deformerFn.findPlug('inputTarget',True)
        IT_indexArray = deformerPlug_IT.getExistingArrayAttributeIndices() 
        if target_index[0] in IT_indexArray:
            deformerPlug_BW = deformerPlug_IT.elementByLogicalIndex(target_index[0]).child(1)
            BW_indexArray = deformerPlug_BW.getExistingArrayAttributeIndices()
            for token in BW_indexArray:
                if token in memberID:
                    weightsMap.setdefault(token,deformerPlug_BW.elementByLogicalIndex(token).asFloat())
                    memberID.remove(token)
        for token in memberID:
            weightsMap.setdefault(token,1)
        for token in nonMemberID:
            weightsMap.setdefault(token,0)            
        if weightsMap:
            return weightsMap                            

    def setDeformerWeights(self,weightsMap,importDeformer,Target=None,ID=None,DeformerName=None):        
        if Target:                                                   
            target_shape = Target
            selection = om.MSelectionList()
            try:
                selection.add(target_shape)
            except:
                raise ValueError('Target "' + str(target_shape) + '" does not exist')
            test_node = selection.getDependNode(0)
            test_type = test_node.apiTypeStr
            if not test_type == 'kMesh':
                raise ValueError('Target "' + str(target_shape) + '" is not a valid mesh')
        else:
            target_shape = self.getTargetShape()     
        if ID:
            verticesID = ID
            target_fn = om.MFnMesh(target_shape)
            target_vtxCount = target_fn.numVertices
            target_vtx = list(range(0,target_vtxCount))
            for element in verticesID:
                if not element in target_vtx:
                    raise ValueError('Vertex ID ' + str(element) + ' does not belong to mesh "' + str(target_shape) + '"')
        else:    
            verticesID = []        
            components_selection = om.MGlobal.getActiveSelectionList()
            components_iterator = om.MItSelectionList(components_selection,om.MFn.kMeshVertComponent)
            if components_iterator.isDone():
                raise ValueError('Select the mesh vertices to operate on')
            while not components_iterator.isDone():
                component = components_iterator.getComponent()
                vertices_iterator = om.MItMeshVertex(component[0],component[1])
                if not (component[0].extendToShape(0) == target_shape): 
                    raise ValueError('The selected vertices do not belong to "{Name}"'.format(Name=target_shape))
                while not vertices_iterator.isDone():
                    verticesID.append(vertices_iterator.index())
                    next(vertices_iterator)
                next(components_iterator)  
        if DeformerName:
            deformer_name = DeformerName
            selection = om.MSelectionList()
            try:
                selection.add(deformer_name)
            except:
                raise ValueError('Deformer "' + str(deformer_name) + '" does not exist') 
        else:                
            deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
            deformer_entry = deformerEntry_list[0].split(' - ')
            deformer_name = deformer_entry[1]
        if not (deformer_name == importDeformer):
            answer = cmds.confirmDialog(title='Confirm',message='You are trying to import weights of "'+importDeformer+'" deformer into "'+deformer_name+'" deformer. Proceed anyway?',button=['Yes','No'],defaultButton='Yes',cancelButton='No',dismissString='No')
            if answer == 'No':
                status = 'aborted'
                return status 
        deformer_selection = om.MSelectionList()
        deformer_selection.add(deformer_name)
        deformerObj = deformer_selection.getDependNode(0)
        deformerFn = om.MFnDependencyNode(deformerObj)
        target_index = self.findTargetIndex(deformerObj,target_shape)
        if not target_index:
            raise ValueError('"{Name1}" does not affect "{Name2}"'.format(Name1=deformer_name,Name2=target_shape))        
        deformerPlug_WL = deformerFn.findPlug('weightList',True)
        deformerPlug_W = deformerPlug_WL.elementByLogicalIndex(target_index[0]).child(0)
        if weightsMap:
            weightsMap_keys = list(weightsMap.keys())
            weightsMap_items = [(int(key),weightsMap[key]) for key in weightsMap_keys]
            weightsMap_validItems = [item for item in weightsMap_items if item[0] in verticesID]
            for item in weightsMap_validItems:
                deformerPlug_W.elementByLogicalIndex(item[0]).setFloat(item[1])
            if not weightsMap_validItems:
                status = 'failure'
            else:
                status = 'complete'
        else:
            status = 'failure'
        return status 

    def setBlendShapeWeights(self,weightsMap,importDeformer,Target=None,ID=None,DeformerName=None):        
        if Target:                                                   
            target_shape = Target
            selection = om.MSelectionList()
            try:
                selection.add(target_shape)
            except:
                raise ValueError('Target "' + str(target_shape) + '" does not exist')
            test_node = selection.getDependNode(0)
            test_type = test_node.apiTypeStr
            if not test_type == 'kMesh':
                raise ValueError('Target "' + str(target_shape) + '" is not a valid mesh')
        else:
            target_shape = self.getTargetShape()       
        if ID:
            verticesID = ID
            target_fn = om.MFnMesh(target_shape)
            target_vtxCount = target_fn.numVertices
            target_vtx = list(range(0,target_vtxCount))
            for element in verticesID:
                if not element in target_vtx:
                    raise ValueError('Vertex ID ' + str(element) + ' does not belong to mesh "' + str(target_shape) + '"')
        else:         
            verticesID = []        
            components_selection = om.MGlobal.getActiveSelectionList()
            components_iterator = om.MItSelectionList(components_selection,om.MFn.kMeshVertComponent)
            if components_iterator.isDone():
                raise ValueError('Select the mesh vertices to operate on')
            while not components_iterator.isDone():
                component = components_iterator.getComponent()
                vertices_iterator = om.MItMeshVertex(component[0],component[1])
                if not (component[0].extendToShape(0) == target_shape): 
                    raise ValueError('The selected vertices do not belong to "{Name}"'.format(Name=target_shape))
                while not vertices_iterator.isDone():
                    verticesID.append(vertices_iterator.index())
                    next(vertices_iterator)
                next(components_iterator)  
        if DeformerName:
            deformer_name = DeformerName
            selection = om.MSelectionList()
            try:
                selection.add(deformer_name)
            except:
                raise ValueError('Deformer "' + str(deformer_name) + '" does not exist') 
        else:     
            deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
            deformer_entry = deformerEntry_list[0].split(' - ')
            deformer_name = deformer_entry[1]
        if not (deformer_name == importDeformer):
            answer = cmds.confirmDialog(title='Confirm',message='You are trying to import weights of "'+importDeformer+'" deformer into "'+deformer_name+'" deformer. Proceed anyway?',button=['Yes','No'],defaultButton='Yes',cancelButton='No',dismissString='No')
            if answer == 'No':
                status = 'aborted'
                return status 
        deformer_selection = om.MSelectionList()
        deformer_selection.add(deformer_name)
        deformerObj = deformer_selection.getDependNode(0)
        deformerFn = om.MFnDependencyNode(deformerObj)
        target_index = self.findTargetIndex(deformerObj,target_shape)
        if not target_index:
            raise ValueError('"{Name1}" does not affect "{Name2}"'.format(Name1=deformer_name,Name2=target_shape))        
        deformerPlug_IT = deformerFn.findPlug('inputTarget',True)
        deformerPlug_BW = deformerPlug_IT.elementByLogicalIndex(target_index[0]).child(1)
        if weightsMap:
            weightsMap_keys = list(weightsMap.keys())
            weightsMap_items = [(int(key),weightsMap[key]) for key in weightsMap_keys]
            weightsMap_validItems = [item for item in weightsMap_items if item[0] in verticesID]        
            for item in weightsMap_validItems:
                deformerPlug_BW.elementByLogicalIndex(item[0]).setFloat(item[1])
            if not weightsMap_validItems:
                status = 'failure'
            else:
                status = 'complete'
        else:
            status = 'failure'
        return status            
           
    def getVerticesPosition(self):
        target_shape = self.getTargetShape()     
        coordinatesTable = {}                     
        components_selection = om.MGlobal.getActiveSelectionList()
        components_iterator = om.MItSelectionList(components_selection,om.MFn.kMeshVertComponent)
        if components_iterator.isDone():
            raise ValueError('Select the mesh vertices to operate on')  
        while not components_iterator.isDone():
            component = components_iterator.getComponent()
            vertices_iterator = om.MItMeshVertex(component[0],component[1])
            if not (component[0].extendToShape(0) == target_shape): 
                raise ValueError('The selected vertices do not belong to "{Name}"'.format(Name=target_shape))
            while not vertices_iterator.isDone():
                vtx_ID = vertices_iterator.index()
                vtx_position = vertices_iterator.position(om.MSpace.kWorld)
                coordinatesTable.setdefault(vtx_ID,[vtx_position.x,vtx_position.y,vtx_position.z])
                next(vertices_iterator)
            next(components_iterator) 
        if coordinatesTable:
            return coordinatesTable   

    def saveWeights(self,*args):
        try:
            target_shape = self.getTargetShape()
        except:
            raise ValueError('Select a valid mesh')
        target_shapeFn = om.MFnDagNode(target_shape)
        target_transform = target_shapeFn.parent(0)                                      
        target_transformFn = om.MFnDependencyNode(target_transform)
        mesh_name = target_transformFn.name()                    
        deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
        if not deformerEntry_list:
            raise ValueError('Select a valid deformer')           
        deformer_entry = deformerEntry_list[0].split(' - ')
        deformer_name = deformer_entry[1]  
        if deformer_entry[0] == 'blendShape':
            weightsMap = self.getBlendShapeWeights()
        else:
            weightsMap = self.getDeformerWeights()
        coordinatesTable = self.getVerticesPosition()
        vtx_count = len(list(weightsMap.keys()))
        startDir = cmds.textFieldButtonGrp(self.importExportGroup,query=True,fileName=True)        
        if not os.path.isdir(startDir):
            startDir = self.workingDir
        save_file = cmds.fileDialog2(dialogStyle=1,caption='Save As',startingDirectory=startDir,fileMode=0,fileFilter='*.json')
        if not save_file:
            sys.stdout.write('Save operation aborted')
            return None
        file_name = save_file[0]        
        header = {}
        header.setdefault('FILE NAME',file_name)
        header.setdefault('MESH NAME',mesh_name)        
        header.setdefault('DEFORMER NAME',deformer_name)
        header.setdefault('VERTICES COUNT',vtx_count)                
        exportData = {}
        exportData.setdefault('header',header)
        exportData.setdefault('weightsMap',weightsMap)
        exportData.setdefault('coordinatesTable',coordinatesTable)                
        with open(file_name,mode='w') as exportFile:
            json.dump(exportData,exportFile,indent=4,sort_keys=True)
        sys.stdout.write('Save operation ended successfully')              
  
    def indexAlgorithm(self,*args):
        cmds.textFieldGrp(self.loadTolerance,edit=True,enable=False)
  
    def positionAlgorithm(self,*args):
        cmds.textFieldGrp(self.loadTolerance,edit=True,enable=True)
  
    def setTolerance(self,input_text):
        try:
            value = float(input_text)
            if not (value>0):
                raise ValueError
        except ValueError as VE:
            cmds.warning('Tolerance must be of type "float". Only positive, non-zero values are allowed. A default tolerance of 0.1 is applied otherwise')    

    def findClosestVertices(self,vtxSourcePoint,vtxTargetMap,toleranceVal):  
        radiusVector = om.MVector([toleranceVal,toleranceVal,toleranceVal])
        BB_min = vtxSourcePoint - radiusVector
        BB_max = vtxSourcePoint + radiusVector
        BoundingBox = om.MBoundingBox(BB_min,BB_max)
        vtxTarget_items = list(vtxTargetMap.items())
        vtxIndex_list = []
        for item in vtxTarget_items:
            if BoundingBox.contains(item[1]):
                vtxIndex_list.append(item[0])
        closest_vtxInfo = {}
        for index in vtxIndex_list:
            distance = vtxSourcePoint.distanceTo(vtxTargetMap[index])
            if not distance > toleranceVal:
                closest_vtxInfo.setdefault(index,distance)
        if closest_vtxInfo:
            return closest_vtxInfo
            
    def averageWeightsMap(self,coordinatesTable,weightsMap):
        toleranceInput = cmds.textFieldGrp(self.loadTolerance,query=True,text=True)
        try:
            toleranceVal = float(toleranceInput)
            if not (toleranceVal > 0):
                raise ValueError
        except ValueError:
            toleranceVal = 0.1
        coordinatesTable_items = list(coordinatesTable.items())
        vtxTargetMap = {item[0]: om.MPoint(item[1]) for item in coordinatesTable_items}                           
        target_shape = self.getTargetShape() 
        components_selection = om.MGlobal.getActiveSelectionList()
        components_count = 0
        screening_iterator = om.MItSelectionList(components_selection,om.MFn.kMeshVertComponent)
        while not screening_iterator.isDone():
            components_count = components_count + 1
            next(screening_iterator)
        if components_count == 0:
            raise ValueError('Select the mesh vertices to operate on')  
        components_iterator = om.MItSelectionList(components_selection,om.MFn.kMeshVertComponent) 
        averageWeightsMap = {}
        component_step = 0
        while not components_iterator.isDone():            
            component = components_iterator.getComponent()
            vertices_iterator = om.MItMeshVertex(component[0],component[1])
            if not (component[0].extendToShape(0) == target_shape): 
                raise ValueError('The selected vertices do not belong to "{Name}"'.format(Name=target_shape))
            vtx_count = vertices_iterator.count()
            component_step = component_step + 1
            pb_titleString = '...Step ' + str(component_step) + ' of ' + str(components_count) + '...'
            pbWinName = 'DWE_PB'          
            if cmds.window(pbWinName,exists=True):
                cmds.deleteUI(pbWinName)
            cmds.window(pbWinName,title=pb_titleString,sizeable=False,widthHeight=[350,50])
            pbLayout = cmds.formLayout(numberOfDivisions=100)
            pbControl = cmds.progressBar(parent=pbLayout,width=330,height=30,minValue=0,maxValue=vtx_count,progress=0)
            cmds.formLayout(pbLayout,edit=True,attachForm=([pbControl,'left',10],[pbControl,'top',10]))  
            if cmds.windowPref(pbWinName,exists=True):
                cmds.windowPref(pbWinName,remove=True)
            cmds.showWindow(pbWinName)                
            while not vertices_iterator.isDone():
                vtx_ID = vertices_iterator.index()
                point = vertices_iterator.position(space=om.MSpace.kWorld)
                closest_vtxInfo = self.findClosestVertices(point,vtxTargetMap,toleranceVal)
                avg_weight = 0
                if closest_vtxInfo:                    
                    closest_vtxItems = list(closest_vtxInfo.items())
                    closest_vtxDistances = list(closest_vtxInfo.values())
                    if 0 in closest_vtxDistances:
                        for item in closest_vtxItems:
                            if item[1] == 0:
                                avg_weight = weightsMap[item[0]]
                                break
                    else:
                        factor = 0
                        for item in closest_vtxItems:
                            avg_weight = avg_weight + weightsMap[item[0]]*1.0/item[1]
                            factor = factor + 1.0/item[1]
                        avg_weight = float(avg_weight) / factor  
                averageWeightsMap.setdefault(str(vtx_ID),avg_weight)
                next(vertices_iterator)
                cmds.progressBar(pbControl,edit=True,step=1)
            cmds.deleteUI(pbWinName)   
            next(components_iterator)
        if averageWeightsMap:
            return averageWeightsMap
        
    def loadWeights(self,*args):                     
        try:
            target_shape = self.getTargetShape()
        except:
            raise ValueError('Select a valid mesh')        
        deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
        if not deformerEntry_list:
            raise ValueError('Select a valid deformer')           
        deformer_entry = deformerEntry_list[0].split(' - ')
        startDir = cmds.textFieldButtonGrp(self.importExportGroup,query=True,fileName=True)        
        if not os.path.isdir(startDir):
            startDir = self.workingDir
        load_file = cmds.fileDialog2(dialogStyle=1,caption='Load',startingDirectory=startDir,fileMode=1,fileFilter='*.json')
        if not load_file:
            sys.stdout.write('Load operation aborted')
            return None
        file_name = load_file[0]
        algorithm = cmds.radioButtonGrp(self.loadVertices,query=True,select=True) 
        with open(file_name,mode='r') as importFile:
            importData = json.load(importFile)
        try:
            header = importData['header']
        except:
            raise KeyError('Unable to find "header" key in import file')
        try:
            coordinatesTable = importData['coordinatesTable']
        except:
            raise KeyError('Unable to find "coordinatesTable" key in import file')
        try:
            weightsMap = importData['weightsMap']
        except:
            raise KeyError('Unable to find "weightsMap" key in import file')
        outputMessage = {}
        outputMessage.setdefault('complete','Load operation ended successfully')
        outputMessage.setdefault('failure','No weight was set: check stored vertices IDs or try increasing tolerance value')                
        outputMessage.setdefault('aborted','Load operation aborted')   
        if algorithm == 1:         
            if deformer_entry[0] == 'blendShape':
                status = self.setBlendShapeWeights(weightsMap,header['DEFORMER NAME'])                
                sys.stdout.write(outputMessage[status])
                return
            else: 
                status = self.setDeformerWeights(weightsMap,header['DEFORMER NAME'])            
                sys.stdout.write(outputMessage[status])
                return    
        if algorithm == 2:
            averageWeightsMap = self.averageWeightsMap(coordinatesTable,weightsMap)
            if deformer_entry[0] == 'blendShape':
                status = self.setBlendShapeWeights(averageWeightsMap,header['DEFORMER NAME'])                
                sys.stdout.write(outputMessage[status])
                return
            else: 
                status = self.setDeformerWeights(averageWeightsMap,header['DEFORMER NAME'])            
                sys.stdout.write(outputMessage[status])
                return 
          
    def mirrorWeights(self,*args):
        symmetry_plane = cmds.radioButtonGrp(self.symmetryPlane,query=True,select=True)
        mirror_direction = cmds.radioButtonGrp(self.symmetryDirection,query=True,select=True)
        try:
            target_shape = self.getTargetShape()
        except:
            raise ValueError('Select a valid mesh')   
        target_fn = om.MFnMesh(target_shape)
        target_vtx = target_fn.numVertices
        target_IDs = list(range(0,target_vtx))          
        deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
        if not deformerEntry_list:
            raise ValueError('Select a valid deformer')        
        deformer_entry = deformerEntry_list[0].split(' - ')
        deformer_name = deformer_entry[1] 
        if deformer_entry[0] == 'blendShape':
            weightsMap = self.getBlendShapeWeights(Target=target_shape,ID=target_IDs,DeformerName=deformer_name)
        else:
            weightsMap = self.getDeformerWeights(Target=target_shape,ID=target_IDs,DeformerName=deformer_name)
        coordinatesTable = self.getVerticesPosition()
        vtx_IDs = list(coordinatesTable.keys())
        coordinatesTableFlipped = {ID: list(map(lambda a,b:a*b,coordinatesTable[ID],self.symmetryAxis[symmetry_plane][1])) for ID in vtx_IDs}        
        if mirror_direction == 1:
            targetMap = {ID: om.MPoint(coordinatesTableFlipped[ID]) for ID in vtx_IDs if coordinatesTable[ID][self.symmetryAxis[symmetry_plane][0]] < 0}                                  
        if mirror_direction == 2:
            targetMap = {ID: om.MPoint(coordinatesTableFlipped[ID]) for ID in vtx_IDs if coordinatesTable[ID][self.symmetryAxis[symmetry_plane][0]] > 0}                                  
        target_items = list(targetMap.items())
        targetItemsCounts = len(target_items)
        mirrorWeightsMap = {str(ID): weightsMap[ID] for ID in vtx_IDs} 
        pbWinName = 'DWE_PB'          
        if cmds.window(pbWinName,exists=True):
            cmds.deleteUI(pbWinName)
        cmds.window(pbWinName,title='...Mirroring Weights...',sizeable=False,widthHeight=[350,50])
        pbLayout = cmds.formLayout(numberOfDivisions=100)
        pbControl = cmds.progressBar(parent=pbLayout,width=330,height=30,minValue=0,maxValue=targetItemsCounts,progress=0)
        cmds.formLayout(pbLayout,edit=True,attachForm=([pbControl,'left',10],[pbControl,'top',10]))  
        if cmds.windowPref(pbWinName,exists=True):
            cmds.windowPref(pbWinName,remove=True)
        cmds.showWindow(pbWinName)                 
        for token in target_items:
            closestPoint = target_fn.getClosestPoint(token[1],om.MSpace.kWorld)
            component = om.MFnSingleIndexedComponent()
            face_component = component.create(om.MFn.kMeshPolygonComponent)
            component.addElement(closestPoint[1])
            polyIT = om.MItMeshPolygon(target_shape,face_component) 
            face_triangles = polyIT.getTriangles(om.MSpace.kWorld)                  
            numTriangles = len(face_triangles[0])/3
            for counter in range(0,numTriangles):
                vec_A = om.MVector(face_triangles[0][0+counter*3])
                vec_B = om.MVector(face_triangles[0][1+counter*3])
                vec_C = om.MVector(face_triangles[0][2+counter*3])
                vec_P = om.MVector(closestPoint[0])
                barycentric_coordinates = self.barycenter(vec_A,vec_B,vec_C,vec_P)
                if max(barycentric_coordinates) > 0:
                    break
            interpolated_weight = weightsMap[face_triangles[1][0+counter*3]]*barycentric_coordinates[0] + weightsMap[face_triangles[1][1+counter*3]]*barycentric_coordinates[1] + weightsMap[face_triangles[1][2+counter*3]]*barycentric_coordinates[2]          
            mirrorWeightsMap[str(token[0])] = interpolated_weight
            cmds.progressBar(pbControl,edit=True,step=1)
        cmds.deleteUI(pbWinName)              
        if deformer_entry[0] == 'blendShape':
            status = self.setBlendShapeWeights(mirrorWeightsMap,deformer_name)                
            sys.stdout.write('Mirror operation ended successfully')
            return
        else: 
            status = self.setDeformerWeights(mirrorWeightsMap,deformer_name)            
            sys.stdout.write('Mirror operation ended successfully')
            return     
            
    def flipWeights(self,*args):
        symmetry_plane = cmds.radioButtonGrp(self.symmetryPlane,query=True,select=True)
        try:
            target_shape = self.getTargetShape()
        except:
            raise ValueError('Select a valid mesh')   
        target_fn = om.MFnMesh(target_shape)
        target_vtx = target_fn.numVertices
        target_IDs = list(range(0,target_vtx))  
        deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
        if not deformerEntry_list:
            raise ValueError('Select a valid deformer')        
        deformer_entry = deformerEntry_list[0].split(' - ')
        deformer_name = deformer_entry[1] 
        if deformer_entry[0] == 'blendShape':
            weightsMap = self.getBlendShapeWeights(Target=target_shape,ID=target_IDs,DeformerName=deformer_name)
        else:
            weightsMap = self.getDeformerWeights(Target=target_shape,ID=target_IDs,DeformerName=deformer_name)
        coordinatesTable = self.getVerticesPosition()
        vtx_IDs = list(coordinatesTable.keys())
        coordinatesTableFlipped = {ID: list(map(lambda a,b:a*b,coordinatesTable[ID],self.symmetryAxis[symmetry_plane][1])) for ID in vtx_IDs}                                       
        targetMap = {ID: om.MPoint(coordinatesTableFlipped[ID]) for ID in vtx_IDs}
        target_items = list(targetMap.items())
        targetItemsCounts = len(target_items)
        flippedWeightsMap = {}       
        pbWinName = 'DWE_PB'          
        if cmds.window(pbWinName,exists=True):
            cmds.deleteUI(pbWinName)
        cmds.window(pbWinName,title='...Flipping Weights...',sizeable=False,widthHeight=[350,50])
        pbLayout = cmds.formLayout(numberOfDivisions=100)
        pbControl = cmds.progressBar(parent=pbLayout,width=330,height=30,minValue=0,maxValue=targetItemsCounts,progress=0)
        cmds.formLayout(pbLayout,edit=True,attachForm=([pbControl,'left',10],[pbControl,'top',10]))  
        if cmds.windowPref(pbWinName,exists=True):
            cmds.windowPref(pbWinName,remove=True)
        cmds.showWindow(pbWinName)              
        for token in target_items:
            closestPoint = target_fn.getClosestPoint(token[1],om.MSpace.kWorld)
            component = om.MFnSingleIndexedComponent()
            face_component = component.create(om.MFn.kMeshPolygonComponent)
            component.addElement(closestPoint[1])
            polyIT = om.MItMeshPolygon(target_shape,face_component) 
            face_triangles = polyIT.getTriangles(om.MSpace.kWorld)                  
            numTriangles = len(face_triangles[0])/3
            for counter in range(0,numTriangles):
                vec_A = om.MVector(face_triangles[0][0+counter*3])
                vec_B = om.MVector(face_triangles[0][1+counter*3])
                vec_C = om.MVector(face_triangles[0][2+counter*3])
                vec_P = om.MVector(closestPoint[0])
                barycentric_coordinates = self.barycenter(vec_A,vec_B,vec_C,vec_P)
                if max(barycentric_coordinates) > 0:
                    break
            interpolated_weight = weightsMap[face_triangles[1][0+counter*3]]*barycentric_coordinates[0] + weightsMap[face_triangles[1][1+counter*3]]*barycentric_coordinates[1] + weightsMap[face_triangles[1][2+counter*3]]*barycentric_coordinates[2]          
            flippedWeightsMap.setdefault(str(token[0]),interpolated_weight)  
            cmds.progressBar(pbControl,edit=True,step=1)
        cmds.deleteUI(pbWinName)   
        if deformer_entry[0] == 'blendShape':
            status = self.setBlendShapeWeights(flippedWeightsMap,deformer_name)                
            sys.stdout.write('Flip operation ended successfully')
            return
        else: 
            status = self.setDeformerWeights(flippedWeightsMap,deformer_name)            
            sys.stdout.write('Flip operation ended successfully')
            return                        
            
    def copySource(self,*args):
        try:
            source_shape = self.getTargetShape()
        except:
            raise ValueError('Select a valid mesh')
        deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
        if not deformerEntry_list:
            raise ValueError('Select a valid deformer')
        deformer_entry = deformerEntry_list[0].split(' - ')
        deformer_type = deformer_entry[0]
        deformer_name = deformer_entry[1]         
        message = str(source_shape) + ' -> ' + deformer_name  
        cmds.text(self.sourceText,edit=True,label=message)   
        self.copySourceInfo = []
        self.copySourceInfo.append(source_shape)     
        self.copySourceInfo.append((deformer_type,deformer_name))           
        
    def copyTarget(self,*args):
        try:
            target_shape = self.getTargetShape()
        except:
            raise ValueError('Select a valid mesh')
        deformerEntry_list = cmds.textScrollList(self.deformersList,query=True,selectItem=True)
        if not deformerEntry_list:
            raise ValueError('Select a valid deformer')
        deformer_entry = deformerEntry_list[0].split(' - ')
        deformer_type = deformer_entry[0]
        deformer_name = deformer_entry[1]         
        message = str(target_shape) + ' -> ' + deformer_name  
        cmds.text(self.targetText,edit=True,label=message) 
        self.copyTargetInfo = []   
        self.copyTargetInfo.append(target_shape)     
        self.copyTargetInfo.append((deformer_type,deformer_name))             

    def barycenter(self,vec_A,vec_B,vec_C,vec_P,toleranceVal=0.001):
        barycentricCoor = [0,0,0]
        vec_AB = vec_B - vec_A
        vec_AC = vec_C - vec_A
        vec_BC = vec_C - vec_B   
        vec_CA = vec_A - vec_C             
        vec_AP = vec_P - vec_A
        vec_BP = vec_P - vec_B
        vec_CP = vec_P - vec_C        
        vec_Normal = vec_AB^vec_AC
        factor = 1.0/(vec_Normal*vec_Normal)
        barycentric_u = (vec_BC^vec_BP) * vec_Normal * factor        
        if barycentric_u < -toleranceVal:                    
            return barycentricCoor  
        barycentric_v = (vec_CA^vec_CP) * vec_Normal * factor        
        if barycentric_v < -toleranceVal:                    
            return barycentricCoor                    
        barycentric_w = (vec_AB^vec_AP) * vec_Normal * factor
        if barycentric_w < -toleranceVal:                    
            return barycentricCoor                                                  
        barycentricCoor = (barycentric_u,barycentric_v,barycentric_w)
        return barycentricCoor
        
    def copyWeights(self,*args):
        if not self.copySourceInfo:
            raise ValueError('Select a valid source deformer')          
        if not self.copyTargetInfo:
            raise ValueError('Select a valid target deformer')
        source_shape = self.copySourceInfo[0]
        source_deformerType = self.copySourceInfo[1][0]
        source_deformer = self.copySourceInfo[1][1]  
        target_shape = self.copyTargetInfo[0]
        target_deformerType = self.copyTargetInfo[1][0]
        target_deformer = self.copyTargetInfo[1][1]
        selection = om.MSelectionList()
        try:
            selection.add(source_shape)
        except:
            raise ValueError('Source shape "' + str(source_shape) + '" no longer exists')
        try:
            selection.add(source_deformer)
        except:
            raise ValueError('Source deformer "' + str(source_deformer) + '" no longer exists')            
        try:
            selection.add(target_shape)
        except:
            raise ValueError('Target shape "' + str(target_shape) + '" no longer exists')            
        try:
            selection.add(target_deformer)
        except:
            raise ValueError('Target deformer "' + str(target_deformer) + '" no longer exists')            
        source_fn = om.MFnMesh(source_shape)
        source_vtx = source_fn.numVertices
        source_IDs = list(range(0,source_vtx))
        if source_deformerType == 'blendShape':
            source_weights = self.getBlendShapeWeights(Target=source_shape,ID=source_IDs,DeformerName=source_deformer)
        else:
            source_weights = self.getDeformerWeights(Target=source_shape,ID=source_IDs,DeformerName=source_deformer)   
        target_fn = om.MFnMesh(target_shape)
        target_vtx = target_fn.numVertices 
        target_IDs = list(range(0,target_vtx))               
        target_points = target_fn.getPoints(om.MSpace.kWorld)
        target_weights = {}
        pbWinName = 'DWE_PB'          
        if cmds.window(pbWinName,exists=True):
            cmds.deleteUI(pbWinName)
        cmds.window(pbWinName,title='...Copying Weights...',sizeable=False,widthHeight=[350,50])
        pbLayout = cmds.formLayout(numberOfDivisions=100)
        pbControl = cmds.progressBar(parent=pbLayout,width=330,height=30,minValue=0,maxValue=target_vtx,progress=0)
        cmds.formLayout(pbLayout,edit=True,attachForm=([pbControl,'left',10],[pbControl,'top',10]))  
        if cmds.windowPref(pbWinName,exists=True):
            cmds.windowPref(pbWinName,remove=True)
        cmds.showWindow(pbWinName)          
        for index,pointItem in enumerate(target_points):
            closestPoint = source_fn.getClosestPoint(pointItem,om.MSpace.kWorld)
            component = om.MFnSingleIndexedComponent()
            face_component = component.create(om.MFn.kMeshPolygonComponent)
            component.addElement(closestPoint[1])
            polyIT = om.MItMeshPolygon(source_shape,face_component) 
            face_triangles = polyIT.getTriangles(om.MSpace.kWorld)                  
            numTriangles = len(face_triangles[0])/3
            for counter in range(0,numTriangles):
                vec_A = om.MVector(face_triangles[0][0+counter*3])
                vec_B = om.MVector(face_triangles[0][1+counter*3])
                vec_C = om.MVector(face_triangles[0][2+counter*3])
                vec_P = om.MVector(closestPoint[0])
                barycentric_coordinates = self.barycenter(vec_A,vec_B,vec_C,vec_P)
                if max(barycentric_coordinates) > 0:
                    break
            interpolated_weight = source_weights[face_triangles[1][0+counter*3]]*barycentric_coordinates[0] + source_weights[face_triangles[1][1+counter*3]]*barycentric_coordinates[1] + source_weights[face_triangles[1][2+counter*3]]*barycentric_coordinates[2]          
            target_weights.setdefault(index,interpolated_weight)
            cmds.progressBar(pbControl,edit=True,step=1)
        cmds.deleteUI(pbWinName) 
        outputMessage = {}
        outputMessage.setdefault('complete','Copy operation ended successfully')
        outputMessage.setdefault('failure','No weight was set')                
        outputMessage.setdefault('aborted','Copy operation aborted')                                                                
        if target_deformerType == 'blendShape':
            status = self.setBlendShapeWeights(target_weights,source_deformer,Target=target_shape,ID=target_IDs,DeformerName=target_deformer)
            sys.stdout.write(outputMessage[status])
            return
        else:
            status = self.setDeformerWeights(target_weights,source_deformer,Target=target_shape,ID=target_IDs,DeformerName=target_deformer)
            sys.stdout.write(outputMessage[status])
            return

# dwe_win = DeformersWeightsEditor.showUI()
