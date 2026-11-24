"""
ngst_compat - ngSkinTools 1 ``MllInterface`` on top of ngSkinTools 2.

deformer_utils_ui.py and weight_utils.py were written for ngSkinTools 1
(``from ngSkinTools.mllInterface import MllInterface``). ngSkinTools 1 does not
exist for Maya 2025/2026; ngSkinTools 2 has a different Python API. This module
gives those scripts the subset of the old interface they use:

    setCurrentMesh, listLayers, isLayerEnabled, setLayerEnabled,
    listLayerInfluences, getTargetInfo, listInfluencePaths, listInfluenceIndexes,
    getInfluenceWeights, setInfluenceWeights, getLayerMask, setLayerMask,
    getDualQuaternionWeights, setDualQuaternionWeights, getVertCount,
    createLayer, deleteLayer, layerMergeDown

If the real ngSkinTools 1 is importable it is used unchanged.

Name conventions used here (the two scripts rely on them being consistent):
  * listLayerInfluences() returns (shortest unique name, logical index)
  * listInfluencePaths()  returns long DAG paths ("|root|spine|arm")
  * weight_utils resolves a name to its long path before looking it up.
"""
import maya.cmds as cmds

try:  # the real thing, if someone still has it
    from ngSkinTools.mllInterface import MllInterface  # noqa: F401
    NG_VERSION = 1
except Exception:
    from ngSkinTools2.api import layers as _ng_layers
    from ngSkinTools2.api import target_info as _ng_target

    NG_VERSION = 2

    _MASK = "mask"
    _DQ = "dq"

    def _long(name):
        found = cmds.ls(name, long=True) or []
        return found[0] if found else name

    def _short(name):
        found = cmds.ls(name) or []
        return found[0] if found else name

    class MllInterface(object):
        """ngSkinTools 1 style wrapper around ngSkinTools2.api."""

        def __init__(self, mesh=None):
            self.mesh = mesh

        # ---- target -----------------------------------------------------
        def setCurrentMesh(self, mesh):
            self.mesh = mesh

        def _layers(self):
            return _ng_layers.Layers(self.mesh)

        def _layer(self, layer_id):
            return _ng_layers.Layer.load(self.mesh, int(layer_id))

        def getTargetInfo(self):
            """(mesh, skinCluster), or None when the mesh has no skinCluster."""
            if not self.mesh:
                return None
            skin_cluster = _ng_target.get_related_skin_cluster(self.mesh)
            if not skin_cluster:
                return None
            return (self.mesh, skin_cluster)

        def getVertCount(self):
            try:
                return int(cmds.ngst2Layers(self.mesh, q=True, vertexCount=True))
            except Exception:
                return int(cmds.polyEvaluate(self.mesh, vertex=True))

        # ---- layers -----------------------------------------------------
        def listLayers(self):
            """
            Yields (layerId, name, parentId); parentId is None for top-level layers.
            Parents always come before their children (the UI builds its tree in
            this order).
            """
            if not _ng_target.get_related_data_node(self.mesh):
                raise RuntimeError("no ngSkinTools2 layer data on %s" % self.mesh)
            all_layers = list(self._layers().list())
            by_id = dict((l.id, l) for l in all_layers)

            def parent_id(layer):
                p = layer.parent
                if p is None:
                    return None
                return p.id if hasattr(p, "id") else p

            emitted = set()
            ordered = []

            def emit(layer):
                if layer.id in emitted:
                    return
                pid = parent_id(layer)
                if pid is not None and pid in by_id:
                    emit(by_id[pid])
                emitted.add(layer.id)
                ordered.append(layer)

            for layer in all_layers:
                emit(layer)
            for layer in ordered:
                yield (layer.id, layer.name, parent_id(layer))

        def isLayerEnabled(self, layerId):
            return bool(self._layer(layerId).enabled)

        def setLayerEnabled(self, layerId, enabled):
            self._layer(layerId).enabled = bool(enabled)

        def createLayer(self, name, forceEmpty=False):
            if _ng_target.get_related_data_node(self.mesh):
                layers = self._layers()
            else:
                layers = _ng_layers.init_layers(self.mesh)
            return layers.add(name, force_empty=forceEmpty).id

        def deleteLayer(self, layerId):
            self._layers().delete(self._layer(layerId))

        def layerMergeDown(self, layerId):
            """
            Merge the layer into the sibling directly below it (ngSkinTools 1
            "merge down"). NOT TESTED in Maya: check the result on a copy first.
            """
            from ngSkinTools2.api import tools as _ng_tools
            layer = self._layer(layerId)
            siblings = [l for l in self._layers().list()
                        if getattr(l.parent, "id", l.parent) == getattr(layer.parent, "id", layer.parent)]
            siblings.sort(key=lambda l: l.index)
            below = [l for l in siblings if l.index < layer.index]
            if not below:
                cmds.warning("ngst_compat: layer %r has no layer below it to merge into" % layer.name)
                return None
            return _ng_tools.merge_layers([layer, below[-1]])

        # ---- influences -------------------------------------------------
        def _influences(self):
            return list(_ng_target.list_influences(self.mesh))

        def listInfluencePaths(self):
            return [_long(i.path) for i in self._influences()]

        def listInfluenceIndexes(self):
            return [int(i.logicalIndex) for i in self._influences()]

        def listLayerInfluences(self, layerId=None, activeInfluences=True):
            """Yields (name, logicalIndex). activeInfluences=True: only influences with weights on this layer."""
            infs = self._influences()
            if activeInfluences:
                used = set(int(x) for x in (self._layer(layerId).get_used_influences() or []))
                infs = [i for i in infs if int(i.logicalIndex) in used]
            for i in infs:
                yield (_short(i.path), int(i.logicalIndex))

        # ---- weights ----------------------------------------------------
        def getInfluenceWeights(self, layerId, influenceIndex):
            return list(self._layer(layerId).get_weights(int(influenceIndex)) or [])

        def setInfluenceWeights(self, layerId, influenceIndex, weights, undoEnabled=True):
            self._layer(layerId).set_weights(int(influenceIndex), list(weights), undo_enabled=undoEnabled)

        def getLayerMask(self, layerId):
            return list(self._layer(layerId).get_weights(_MASK) or [])

        def setLayerMask(self, layerId, weights, undoEnabled=True):
            self._layer(layerId).set_weights(_MASK, list(weights), undo_enabled=undoEnabled)

        def getDualQuaternionWeights(self, layerId):
            return list(self._layer(layerId).get_weights(_DQ) or [])

        def setDualQuaternionWeights(self, layerId, weights, undoEnabled=True):
            self._layer(layerId).set_weights(_DQ, list(weights), undo_enabled=undoEnabled)
