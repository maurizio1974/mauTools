import maya.cmds as cmds
import maya.mel as mel

# CHECK THE SOuP NODE AND RETURN THE TYPE
def checkNodeSOuP(node):
    out = 0
    sh = cmds.listRelatives( node, s = True)
    if type(sh[0]).__name__!='NoneType':
        n = cmds.nodeType(sh[0])        
        if n == 'nParticle':
            out = 1
        else:
            out = 0
    return out
    
# CHECK IF THERE IS ALREADY AN ATTRIBUTE TRANSFER ATTACHED
def checkConnectSOuP(node):
    out = 3
    sh = cmds.listRelatives( node, s = True)
    if type(sh[0]).__name__!= 'NoneType':
        conn = cmds.listConnections (sh[0], s = False, d = True)
        for c in conn:
            if tyoe(conn).__name__!= 'NoneType':
                if cmds.nodeType(c) == 'attributeTransfer':
                    out = 2
    return out

# FROM GEOMETRY SET UP SCATTER INSTANCES
def mgDynScatter():
    el = cmds.ls( sl = True)
    if type(cmds.filterExpand( sm = 12 )).__name__!='NoneType':
        for a in el:
            do_mgDynScatter(a)
    else:
        cmds.confirmDialog( t='OK', m='Select only meshes, subDs, nurbs, vertexs, subD vertexs or nurbs control Vertexes')
        
# THE ACTUAL PROCEDURE THAT MAKES ALL THE NODE AND CONNECTIONS        
def do_mgDynScatter(geo):
    TA = cmds.createNode('scatter')
    ATT = cmds.createNode('attributeTransfer')
    pCC = cmds.createNode('pointCloudToCurve')
    p = cmds.createNode('point')
    ADAin = cmds.createNode('arrayToDynArrays')
    ADAs = cmds.createNode('arrayToDynArrays')
    ADAp = cmds.createNode('arrayToDynArrays')
    ADAaim = cmds.createNode('arrayToDynArrays')
    inst = cmds.createNode ('instancer')
    BB = cmds.createNode ('boundingObject')
    sh = cmds.listRelatives(geo,s = True)
    
    # Connection of the mesh
    cmds.connectAttr ((sh[0]+'.worldMesh[0]'), (TA+'.inGeometry'))
    cmds.connectAttr ((geo+'.worldMatrix[0]'), (TA+'.inWorldMatrix'))
    
    # Connection of TransferAttr and Scatter Node
    cmds.connectAttr ((TA+'.outPositionPP'), (pCC+'.inArray'))
    cmds.connectAttr ((ATT+'.outNormalPP'), (p+'.inNormalPP'))
    cmds.connectAttr ((ATT+'.outNormalPP'), (ADAaim+'.inArray'))
    cmds.connectAttr ((ATT+'.outWeightPP'), (ADAin+'.inArray'))
    
    # Connections of the BoundingBox
    cmds.connectAttr((BB+'.outData'),(ATT+'.boundingObjects[0]'))
    cmds.connectAttr((sh[0]+'.worldMesh'),(BB+'.inMesh'))
    
    cmds.connectAttr ((pCC+'.outCurve'), (p+'.inGeometry'))
    cmds.connectAttr ((pCC+'.outCurve'), (ATT+'.inGeometry'))
    
    #Connection of pointCloudCurve Node
    cmds.connectAttr ((p+'.outRadiusPP'), (ADAs+'.inArray'))
    cmds.connectAttr ((p+'.outPositionPP'), (ADAp+'.inArray'))
    cmds.connectAttr ((ADAaim+'.outDynamicArrays'),(ADAs+'.inDynamicArrays'))
    cmds.connectAttr ((ADAs+'.outDynamicArrays'), (ADAin+'.inDynamicArrays'))
    cmds.connectAttr ((ADAin+'.outDynamicArrays'), (ADAp+'.inDynamicArrays'))
    cmds.connectAttr ((ADAp+'.outDynamicArrays'), (inst+'.inputPoints'))
    
    # Parameter of different Nodes
    cmds.setAttr ((TA+'.scatterMode'), 1)
    cmds.setAttr ((TA+'.pointDensity'), 1000)
    cmds.setAttr ((TA+'.display'), 0)
    cmds.setAttr ((p+'.enableWeight'), 1)
    cmds.setAttr ((p+'.enablePosition'), 1)
    cmds.setAttr ((p+'.enableNormal'), 1)
    cmds.setAttr ((ATT+'.normal'), 1)
    cmds.setAttr ((ATT+'.merge'), 0)
    cmds.setAttr ((ATT+'.blend'), 0)
    cmds.setATTAttr ((ADAp+'.name'), 'position', type = 'string')
    cmds.setAttr ((ADAs+'.name'), 'scale', type = 'string')
    cmds.setAttr ((ADAaim+'.name'), 'aimDirection', type = 'string')
    cmds.setAttr ((ADAin+'.name'), 'objectIndex', type = 'string')
    cmds.setAttr ((BB+'.type'), 3)
    cmds.setAttr ((BB+'.displayPointCloudBoundingVolumes'), 0)
    
    print 'Done'
    
    
# from nParticle set up color and Radius information on volume
def mgPartcileSOuP():
    el = cmds.ls( sl = True)
    if type(cmds.filterExpand( sm = 12 )).__name__!='NoneType':
        for a in el:
            do_mgPartcileSOuP(a)

def do_mgPartcileSOuP(nPart):
    if checkConnectSOuP(nPart) == 3:
        if checkNodeSOuP(nPart) == 1 :
            ATT = cmds.createNode('attributeTransfer')
            RGB = cmds.createNode('rgbaToColorAndAlpha')
            pCC = cmds.createNode('pointCloudToCurve')
            BB = cmds.createNode ('boundingObject')
            pS = cmds.listRelatives(nPart,s = True)
            
            cmds.connectAttr ((ATT+'.outRgbaPP'), (RGB+'.inRgbaPP'))
            cmds.setAttr ((ATT+'.color'), 1)
            cmds.setAttr ((ATT+'.radius'), 1)
            cmds.connectAttr ((RGB+'.outRgbPP'), (pS[0]+'.input[0]'))
            cmds.connectAttr ((ATT+'.outRadiusPP'), (pS[0]+'.input[1]'))
            cmds.connectAttr ((pS[0]+'.worldPosition'), (pCC+'.inArray'))
            cmds.connectAttr ((pCC+'.outCurve'), (ATT+'.inGeometry'))
            
            tr = cmds.listRelatives( BB, p = True) 
            cmds.connectAttr ( (tr[0]+'.matrix'), BB+'.inParentMatrix', f = True)
            cmds.connectAttr((BB+'.outData'),(ATT+'.boundingObjects[0]'))
            cmds.connectAttr((BB+'.parentMatrix'),(ATT+'.boundingObjects[0].boundParentMatrix'))
            cmds.setAttr ((BB+'.type'), 2)
            
            mel.eval('AEgenericBreakConnection "'+pS[0]+'" ( "'+pS[0]+'.internalColorRamp" ) ( "'+pS[0]+'.rgbPP" )')
            mel.eval('AEgenericBreakConnection "'+pS[0]+'" ( "'+pS[0]+'.internalRadiusRamp" ) ( "'+pS[0]+'.radiusPP" )')
            cmds.dynExpression( pS[0], s='rgbPP = '+RGB+'.outRgbPP;\n(getAttr "'+pS[0]+'.radius") + radiusPP = '+ATT+'.outRadiusPP;', rbd=1 )
            cmds.dynExpression( pS[0], s='rgbPP = '+RGB+'.outRgbPP;\n(getAttr "'+pS[0]+'.radius") + radiusPP = '+ATT+'.outRadiusPP;', c=1 )
        
            print 'Done'
        elif checkNodeSOuP(nPart) == 0 :
            cmds.confirmDialog( t='Confirm', m='Please select only nParticle' )
    elif checkConnectSOuP(nPart) == 2 :
        cmds.confirmDialog( t='Confirm', m='There is already an AttributeTransfer node attached to the particleShape, delete it please.' )
        
       
# CONTROL A BLEND SHAPE WITH VOLUME
def mgBlendShapeSOuP(blendShapeNode):
    el = cmds.ls( sl = True)
    if type(el[0]).__name__!='NoneType':
        MTT = cmds.createNode('multiAttributeTransfer')
        BB = cmds.createNode ('boundingObject')
        p = cmds.createNode('point')
        tr = cmds.listRelatives( BB, p = True)

        cn = (cmds.listConnections(blendShapeNode, s = True, d = False))
        for c in cn:
            if 'GroupParts' in c:
                cmds.connectAttr( c+'.outputGeometry', MTT+'.inGeometry', f = True)
                cmds.connectAttr( blendShapeNode+'.outputGeometry[0]', p+'.inGeometry', f = True)
                cmds.connectAttr(MTT+'.outGeometry', blendShapeNode+'.input[0].inputGeometry', f = True)

                cmds.connectAttr(p+'.outGeometry', el[0]+'.inMesh', f = True)
                cmds.connectAttr(MTT+'.outWeightList[0].weights', blendShapeNode+'.inputTarget[0].inputTargetGroup[0].targetWeights', f = True)
                 
                cmds.connectAttr ( (tr[0]+'.matrix'), BB+'.inParentMatrix', f = True)
                cmds.connectAttr((BB+'.outData'),(MTT+'.boundingObjects[0]'))
                cmds.connectAttr((BB+'.parentMatrix'),(MTT+'.boundingObjects[0].boundParentMatrix'))

                cmds.setAttr(p+'.stringStartBlock', 'getAttr '+blendShapeNode+'.inputTarget[0].inputTargetGroup[0].targetWeights;', type = 'string')
                cmds.setAttr(p+'.enablePosition', 1)
    else:
        cmds.confirmDialog( t='OK', m='Please select a mesh with a blendShape Node on it' )