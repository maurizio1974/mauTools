import maya.cmds as cmds
import maya.mel as mel


def mnmMultiAttr(node):
        attr = []
        if cmds.nodeType(node) == 'cluster':
                attr.append('weightList[0].weights')
        if cmds.nodeType(node) == 'mesh':
                attributes = cmds.listAttr(node)
                for a in attributes:
                        if 'Mesh' in a or 'Geo' in a:
                                attr.append(a)
        if cmds.nodeType(node) == 'transform':
                attributes = cmds.listAttr(node)
                for a in attributes:
                        if 'eX' in a or 'eZ' in a or 'eY' in a:
                                attr.append(a)
        if cmds.nodeType(node) == 'nCloth':
                attributes = cmds.listAttr(node)
                for a in attributes:
                        if 'Vertex' in a:
                                attr.append(a)
        return attr
        
