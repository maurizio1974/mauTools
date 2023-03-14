import maya.cmds as cmds
import maya.mel as mel

def mgCopyMulti(node):
        weights = []
        attrsList = cmds.listAttr(node, m = True)
        for a in attrsList:
            if 'weightList[0].weights' in a:
                weights.append(cmds.getAttr(node+"."+a))
        return weights

def mnmPasteMulti(node1,node2):
        weights = mgCopyMulti(node1)
        i = 0
        for w in weights:
            cmds.setAttr(node2 + '.weightList[0].weights[%d]' % i, w)
            i = i + 1

def mnmSaveMulti(node, path):
        fileName = path + '.vd'
        fileid = open( fileName, 'w')
        attrs = 'weightList[0].weights'
        value = cmds.getAttr ( node+'.'+attrs)

        cmd =  node+'.'+attrs
        for v in range (len(value[0])):
            cmd += ' '+str(value[0][v])
        fileid.write( cmd )
        fileid.close()

def mnmReadMulti(txFile, node):
        fileid = open(txFile, "r+")
        str = fileid.read();
        value = str.split(' ')
        if len(node)== 0:
            node = value[0]
        else:
            node = node+'.weightList[0].weights'
        for i in range (len(value)-1):
            mel.eval('setAttr '+node+'[%d] '%i+value[i+1])

        fileid.close()


def mnmCopyPerVertex(node,vertexMap):
        weights = []
        weights = cmds.getAttr(node+'.'+vertexMap)
        return weights

def mnmPastePerVertex(node1,node2,vertexMap1,vertexMap2, state):
        weights = mnmCopyPerVertex(node1,vertexMap1)
        rWeights = mnmInvertPerVertex(node1,vertexMap1)
        if state == 0:
            cmds.setAttr(node2+'.'+vertexMap2, weights, type = 'doubleArray')
        if state ==1:
            cmds.setAttr(node2+'.'+vertexMap2, rWeights, type = 'doubleArray')

def mnmInvertPerVertex(node,vertexMap):
        weights = []
        rWeights = []
        weights = cmds.getAttr(node+'.'+vertexMap)
        for w in weights:
            rWeights.append(1-w)
        return rWeights

def mnmMirrorPerVertex(geo, deformer, axe='x', dir='+', clear=True, tol=0.01):
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    geo = 'tiger_lod2_geo'
    deformer = 'R_eye_cls'
    vtx = cmds.polyEvaluate(geo, v=True)
    cpm = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr(geo + '.worldMesh', cpm + '.inMesh', f=True)
    cmds.progressBar(
        gMainProgressBar, e=True, bp=True,
        ii=True, st='Vertex Left to mirror', max=vtx)
    for x in range(0, vtx):
        cw = cmds.getAttr(deformer + '.weightList[0].weights[' + str(x) + ']')
        if cw > tol:
            pos = cmds.pointPosition(geo + '.vtx[' + str(x) + ']')
            mir = [pos[0] * -1, pos[1], pos[2]]
            if axe == 'y':
                mir = [pos[0], pos[1] * -1, pos[2]]
            elif axe == 'z':
                mir = [pos[0], pos[1], pos[2] * -1]
            if clear:
                cmds.setAttr(deformer + '.weightList[0].weights[' + str(x) + ']', cw)
            if dir == '+':
                if pos[0] > 0:
                    cmds.setAttr(cpm + '.inPosition', mir[0], mir[1], mir[2])
                    out = cmds.getAttr(cpm + '.closestVertexIndex')
                    cmds.setAttr(deformer + '.weightList[0].weights[' + str(out) + ']', cw)
            elif dir == '-':
                if pos[0] < 0:
                    cmds.setAttr(cpm + '.inPosition', mir[0], mir[1], mir[2])
                    out = cmds.getAttr(cpm + '.closestVertexIndex')
                    cmds.setAttr(deformer + '.weightList[0].weights[' + str(out) + ']', cw)
        cmds.progressBar(gMainProgressBar, e=True, s=1)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)
    cmds.delete(cpm)
