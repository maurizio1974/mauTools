import maya.cmds as cmds
import maya.mel as mel

def mgDynScatter():
    el = cmds.ls( sl = True)
    for a in el:
        do_mgDynScatter(a)
        
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
    cmds.setAttr ((ADAp+'.name'), 'position', type = 'string')
    cmds.setAttr ((ADAs+'.name'), 'scale', type = 'string')
    cmds.setAttr ((ADAaim+'.name'), 'aimDirection', type = 'string')
    cmds.setAttr ((ADAin+'.name'), 'objectIndex', type = 'string')
    cmds.setAttr ((BB+'.type'), 3)
    cmds.setAttr ((BB+'.displayPointCloudBoundingVolumes'), 0)
    
    print 'Done'
    
