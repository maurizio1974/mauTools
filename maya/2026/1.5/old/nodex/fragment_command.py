"""Maya command owning undo/redo for native graph-fragment imports."""
import json

import maya.api.OpenMaya as om


def maya_useNewAPI():
    pass


class PasteFragment(om.MPxCommand):
    def doIt(self, args):
        from nodex import fragment, model
        snapshot = fragment._requests[args.asString(0)]
        mapping, created = fragment._import_snapshot(snapshot)
        self.created = created
        self.deletion = None
        self.setResult(json.dumps(mapping))

    def _delete(self):
        from nodex import model
        self.deletion = om.MDagModifier()
        objects = [model.obj_from_uuid(u) for u in self.created]
        ids = set(self.created)
        self.connections = om.MDGModifier()
        for obj in objects:
            if obj is None:
                continue
            for plug in om.MFnDependencyNode(obj).getConnections():
                if plug.isDestination:
                    self.connections.disconnect(plug.sourceWithConversion(), plug)
        self.connections.doIt()  # disconnect first: conversion deletion can cascade upstream
        roots = []
        for obj in objects:
            if obj is None:
                continue
            if obj.hasFn(om.MFn.kDagNode):
                fn = om.MFnDagNode(obj)
                if any(model.uuid_of(fn.parent(i)) in ids for i in range(fn.parentCount())):
                    continue  # deleting a copied parent also deletes its copied children
            roots.append(obj)
        # deleteNode changes the DAG immediately; determine roots before queuing deletions.
        for obj in roots:
            self.deletion.deleteNode(obj, False)
            self.deletion.doIt()

    def isUndoable(self):
        return True

    def undoIt(self):
        self._delete()

    def redoIt(self):
        self.deletion.undoIt()
        self.connections.undoIt()


def initializePlugin(obj):
    om.MFnPlugin(obj, 'NodeX', '1.0', 'Any').registerCommand('nodexPasteFragment', PasteFragment)


def uninitializePlugin(obj):
    om.MFnPlugin(obj).deregisterCommand('nodexPasteFragment')
