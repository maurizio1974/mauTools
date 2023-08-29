from maya import cmds, OpenMaya
from maya import mel
from ..utils import QualityAssurance, reference, path


class DuplicateName(QualityAssurance):
    """
    All transforms will be checked to see if their name is unique. When fixing
    the not uniquely named transforms will be made unique.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Duplicate Names"
        self._message = "{0} transform(s) don't have a unique name"
        self._categories = ["Atelier VFX"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Nodes with duplicate name
        :rtype: generator
        """
        obj = OpenMaya.MObject()
        iterator = self.lsApi(nodeType=OpenMaya.MFn.kTransform)
        while not iterator.isDone():
            iterator.getDependNode(obj)

            dagNode = OpenMaya.MDagPath.getAPathTo(obj)
            depNode = OpenMaya.MFnDependencyNode(obj)

            if not depNode.hasUniqueName():
                yield dagNode.fullPathName()

            next(iterator)

    def _fix(self, node):
        """
        :param str node:
        """
        # get root name
        root = path.rootName(node)

        # find new name
        for i in range(1, 1000):
            new = "{0}_{1:03d}".format(root, i)
            if not cmds.ls(new):
                break

        # rename node
        cmds.rename(node, new)

class CheckNaming(QualityAssurance):
    """
    Shapes will be checked to see if they have correct extensions
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Check Name Extensions"
        self._message = "{0} node(s) have wrong extensions"
        self._categories = ["Atelier VFX"]
        self._selectable = True

        self._ignoreNodes = [
            "|persp", "|front", "|top", "|side"]

        # EXTRA STUFF FOR ARNOLD LIGHTS THAT RETURNS AS TRANSFORMS
        ignoreT = [
            'aiAreaLight', 'aiSkyDomeLight', 'aiPhotometricLight',
            'aiLightPortal', 'aiSkyDomeLight', 'aiMeshLight']
        for i in ignoreT:
            cur = self.ls(type=i, l=True)
            if cur:
                for c in cur:
                    self._ignoreNodes.append(c)

    # ------------------------------------------------------------------------

    @property
    def ignoreNodes(self):
        """
        :return: Nodes to ignore
        :rtype: list
        """
        return self._ignoreNodes

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Check Name Extensions
        :rtype: generator
        """
        out = []
        # tipi = {
        #     'mesh': ['_geo', '_mesh'],
        #     'nurbsSurface': ['_surf', '_nurb'],
        #     'nurbsCurve': ['_ctrl', '_crv'],
        #     'locator': ['_loc'],
        #     'transform': ['_grp']}
        tipi = {
            'mesh': ['_geo', '_mesh'],
            'nurbsSurface': ['_surf', '_nurb'],
            'nurbsCurve': ['_ctrl', '_crv'],
            'locator': ['_loc']}
        for t in list(tipi.keys()):
            nodes = self.ls(type=t, l=True)
            nodes = reference.removeReferenced(nodes)
            for node in nodes:
                if node in self.ignoreNodes:
                    continue
                tr = cmds.listRelatives(node, p=True)
                if tr:
                    ext = tr[0].split('_')[-1]
                else:
                    ext = node.split('_')[-1]
                if not any(e.endswith(ext) for e in tipi[t]):
                    yield node

    def _fix(self, node):
        """
        :param str node:
        """
        # tipi = {
        #     'mesh': ['_geo', '_mesh'],
        #     'nurbsSurface': ['_surf', '_nurb'],
        #     'nurbsCurve': ['_crv', '_ctrl'],
        #     'locator': ['_loc'],
        #     'transform': ['_grp']}
        tipi = {
            'mesh': ['_geo', '_mesh'],
            'nurbsSurface': ['_surf', '_nurb'],
            'nurbsCurve': ['_crv', '_ctrl'],
            'locator': ['_loc']}
        tipo = cmds.nodeType(node)
        sh = cmds.listRelatives(node, p=True, ni=True)
        if sh:
            node = sh[0]
        if tipi[tipo][0] != '_grp':
            cmds.rename(node, node + tipi[tipo][0])
        else:
            sh = cmds.listRelatives(node, s=True)
            if not sh:
                cmds.rename(node, node + tipi[tipo][0])


class CheckShapeNames(QualityAssurance):
    """
    Shapes will be checked to see if they have correct name based on the transform
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Check Shape Name"
        self._message = "{0} node(s) have wrong shape name"
        self._categories = ["Atelier VFX"]
        self._selectable = True

        self._ignoreNodes = []

    # ------------------------------------------------------------------------

    @property
    def ignoreNodes(self):
        """
        :return: Nodes to ignore
        :rtype: list
        """
        return self._ignoreNodes

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Check Name Extensions
        :rtype: generator
        """
        nodes = self.ls(type='transform', l=True)
        for node in nodes:
            chi = cmds.listRelatives(node, s=True, ni=True, f=True)
            if chi:
                if chi[0].split('|')[-1] != node.split('|')[-1] + 'Shape':
                    yield chi[0]

    def _fix(self, node):
        """
        :param str node:
        """
        tr = cmds.listRelatives(node, p=True)
        cmds.lockNode(node, l=False)
        try:
            cmds.rename(node, tr[0] + 'Shape')
        except:
            pass
        

class VertexmeshValues(QualityAssurance):
    """
    Mesh shapes will be checked to see if they have values on the vertex
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Mesh with Vertex Value"
        self._message = "{0} mesh(es) contain vertex values"
        self._categories = ["Atelier VFX"]
        self._selectable = True


    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Meshes with vertex values
        :rtype: generator
        """

        meshes = self.ls(type="mesh", l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            out = None
            vtx = cmds.polyEvaluate(mesh, v=True)
            for x in range(0, vtx):
                if not out:
                    cx = cmds.getAttr(mesh + '.pnts[' + str(x) + '].pntx')
                    cy = cmds.getAttr(mesh + '.pnts[' + str(x) + '].pnty')
                    cz = cmds.getAttr(mesh + '.pnts[' + str(x) + '].pntz')
                    if cx != 0 or cy != 0 or cz != 0:
                        out = 1
            if out:
                yield mesh

    def _fix(self, mesh):
        """
        :param str mesh:
        """
        conn = cmds.listConnections(mesh + '.inMesh', s=True, d=False)
        cmds.select(mesh, r=True)
        clh = cmds.cluster()
        cmds.select(mesh, r=True)
        cmds.DeleteHistory()
        cmds.select(cl=True)

class FixLS(QualityAssurance):
    """
    Transforms will be checked for local space values, bad for rigs
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Transforms with local space values"
        self._message = "{0} node(s) has local space values"
        self._categories = ["Atelier VFX"]
        self._selectable = True


    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Transforms with local space values
        :rtype: generator
        """

        nodes = self.ls(type="transform", l=True)
        nodes = reference.removeReferenced(nodes)

        for node in nodes:
            out = False
            cur = cmds.getAttr(node + '.rotatePivot')[0]
            if cur[0] != 0 or cur[1] != 0 or cur[2] != 0:
                out = True
            if out:
                yield node

    def _fix(self, node):
        """
        :param str mesh:
        """
        # DELETE STATIC CHANNELS
        cmds.delete(
            node, staticChannels=True,
            unitlessAnimationCurves=False,
            hierarchy=0, controlPoints=0, shape=0)
        # CHEKC FOR INCOMING CONNECTIONS
        conn = cmds.listConnections(node, s=True, d=False, c=True, p=True)
        if conn:
            for x in range(0, len(conn), 2):
                cmds.disconnectAttr(conn[x+1], conn[x])
        # DO CLEANUP
        if cmds.objExists(node):
            cmds.select(node, r=True)
            mel.eval('bakeCustomToolPivot 1 1')
            cmds.select(cl=True)


class fixAlembicUVexport(QualityAssurance):
    """
    All unknown nodes will be added to the error list. When fixing these nodes
    will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Alembic UV Export Fix"
        self._message = "{0} alembic uv fx"
        self._categories = ["Atelier VFX"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Unknown nodes
        :rtype: generator
        """
        meshNodes = self.ls(type="mesh")
        meshNodes = reference.removeReferenced(meshNodes)

        for meshNode in meshNodes:
            tr = cmds.listRelatives(meshNode, p=True)[0]
            yield tr

    def _fix(self, node):
        """
        :param str node:
        """
        uv_name = cmds.getAttr(node + '.uvSet[0].uvSetName')
        if uv_name != 'map1':
            cmds.polyUVSet(tr, rename=True, uvSet=uv_name, newUVSet="map1")


class UnknownNodes(QualityAssurance):
    """
    All unknown nodes will be added to the error list. When fixing these nodes
    will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Unknown Nodes"
        self._message = "{0} unknown node(s)"
        self._categories = ["Atelier VFX"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Unknown nodes
        :rtype: generator
        """
        unknownNodes = self.ls(type="unknown")
        unknownNodes = reference.removeReferenced(unknownNodes)

        for unknownNode in unknownNodes:
            yield unknownNode

    def _fix(self, node):
        """
        :param str node:
        """
        if cmds.lockNode(node, query=True, lock=True)[0]:
            cmds.lockNode(node, lock=False)

        cmds.delete(node)

class NotConnectedIntermediateShape(QualityAssurance):
    """
    All not connected intermediate nodes will be added to the error list.
    When fixing these nodes will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Not Connected Intermediate Shape"
        self._message = "{0} intermediate shape(s) are not connected"
        self._categories = ["Atelier VFX"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Not connected intermediate nodes
        :rtype: generator
        """
        intermediates = self.ls(shapes=True, intermediateObjects=True)
        intermediates = reference.removeReferenced(intermediates)

        for intermediate in intermediates:
            if cmds.listConnections(intermediate):
                continue

            yield intermediate

    def _fix(self, intermediate):
        """
        :param str intermediate:
        """
        cmds.delete(intermediate)

class NotConnectedGroupID(QualityAssurance):
    """
    All not connected intermediate nodes will be added to the error list.
    When fixing these nodes will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Not Connected Group ID"
        self._message = "{0} group id(s) are not connected"
        self._categories = ["Atelier VFX"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Not connected intermediate nodes
        :rtype: generator
        """
        groupIds = self.ls(type="groupId")
        groupIds = reference.removeReferenced(groupIds)

        for groupId in groupIds:
            if cmds.listConnections(groupId):
                continue

            yield groupId

    def _fix(self, groupId):
        """
        :param str groupId:
        """
        cmds.delete(groupId)

class HyperBookmarks(QualityAssurance):
    """
    All hyper bookmarks of the predefined node types will be added to the
    error list. When fixing these nodes will be deleted. To make sure no
    no connected nodes are deleted. The nodes will be locked before deletion.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Hyper Bookmarks"
        self._message = "{0} hyper bookmark(s) found"
        self._categories = ["Atelier VFX"]
        self._selectable = True

        self._nodeTypes = ["hyperLayout", "hyperGraphInfo", "hyperView"]
        self._nodeIgnore = ["hyperGraphInfo", "hyperGraphLayout"]

    # ------------------------------------------------------------------------

    @property
    def nodeTypes(self):
        """
        :return: List of node types that should be checked
        :rtype: list
        """
        return self._nodeTypes

    @property
    def nodeIgnore(self):
        """
        :return: List of nodes to be ignored
        :rtype: list
        """
        return self._nodeIgnore

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Hyper book marks
        :rtype: generator
        """
        bookmarks = self.ls(type=self.nodeTypes)
        bookmarks = reference.removeReferenced(bookmarks)

        for bookmark in bookmarks:
            if bookmark in self.nodeIgnore:
                continue

            yield bookmark

    def _fix(self, bookmark):
        """
        :param str bookmark:
        """
        # connected data
        hyperPositionStored = {}
        hyperPosition = "{0}.hyperPosition".format(bookmark)

        try:
            # get connections with lock state
            if cmds.objExists(hyperPosition):
                connections = cmds.listConnections(hyperPosition) or []
                connections = list(set(connections))
                for connection in connections:
                    state = cmds.lockNode(connection, query=True, lock=True)[0]
                    cmds.lockNode(connection, lock=True)

                    hyperPositionStored[connection] = state

            # delete bookmark
            cmds.delete(bookmark)
        except:
            pass
        finally:
            # reset connections locked state
            for node, state in hyperPositionStored.items():
                cmds.lockNode(node, lock=state)

class NonReferencedNamespace(QualityAssurance):
    """
    All nodes will be checked to see if they have a non-referenced namespace.
    When fixing this the namespace will be removed from the node.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Non Referenced Namespaces"
        self._message = "{0} node(s) have a non-referenced namespace"
        self._categories = ["Atelier VFX"]
        self._selectable = False

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Nodes that contain a non-referenced namespace
        :rtype: generator
        """
        nodes = self.ls(l=True)
        nodes = reference.removeReferenced(nodes)

        for node in nodes:
            root = path.rootName(node)
            if root.find(":") != -1:
                yield node

    def _fix(self, node):
        """
        :param str node:
        """
        # get namespace
        namespace = path.namespace(node)

        # get node
        cmds.rename(node, path.baseName(node))

        # remove namespace
        if not cmds.namespaceInfo(namespace, listOnlyDependencyNodes=True):
            cmds.namespace(set=":")
            cmds.namespace(removeNamespace=namespace)


class EmptyNamespaces(QualityAssurance):
    """
    All namespaces will be checked to see if they are empty. When fixing
    these namespaces will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Empty Namespaces"
        self._message = "{0} namespace(s) are empty"
        self._categories = ["Atelier VFX"]
        self._selectable = False

        self._ignoreNamespaces = ["shared", "UI"]

    # ------------------------------------------------------------------------

    @property
    def ignoreNamespaces(self):
        """
        :return: Namespaces to ignore
        :rtype: list
        """
        return self._ignoreNamespaces

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Empty namespaces
        :rtype: generator
        """
        # set namespace to root
        cmds.namespace(set=":")

        # get all namespaces
        namespaces = cmds.namespaceInfo(":", listOnlyNamespaces=True, recurse=True)
        namespaces.reverse()

        # loop namespaces
        for ns in namespaces:
            if ns in self.ignoreNamespaces:
                continue

            # yield empty namespaces
            if not cmds.namespaceInfo(ns, listOnlyDependencyNodes=True):
                yield ns

    def _fix(self, namespace):
        """
        :param str namespace:
        """
        cmds.namespace(set=":")
        cmds.namespace(removeNamespace=namespace)

class DeleteHistory(QualityAssurance):
    """
    Mesh shapes will be checked to see if they have history attached to them.
    When fixing this error the history will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "History"
        self._message = "{0} mesh(es) contain history nodes"
        self._categories = ["Atelier VFX"]
        self._selectable = True

        self._ignoreNodes = [
            "tweak", "groupParts", "groupId",
            "shape", "shadingEngine", "mesh"
        ]


    # ------------------------------------------------------------------------

    @property
    def ignoreNodes(self):
        """
        :return: Nodes to ignore
        :rtype: list
        """
        return self._ignoreNodes

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Meshes with history
        :rtype: generator
        """

        meshes = self.ls(type="mesh", l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            history = cmds.listHistory(mesh) or []
            types = [cmds.nodeType(h) for h in history]

            for t in types:
                if t in self.ignoreNodes:
                    continue

                yield mesh
                break

    def _fix(self, mesh):
        """
        :param str mesh:
        """
        cmds.delete(mesh, ch=True)
