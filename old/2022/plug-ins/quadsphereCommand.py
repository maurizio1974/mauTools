# -*- coding: utf-8 -*-

__author__ = "James.N"
__version__ = "1.0.0"

import sys

import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as om


kPluginCmdName = 'polyQuadsphere'


class QuadsphereCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

        self._division = 10
        self._radius = 1.0
        self._spherical = 1.0

        self._name = "pQuadsphere"
        self._nodePath = None

    def doIt(self, args):
        self._parseArgs(args)
        self.redoIt()

    def _parseArgs(self, args):
        argData = om.MArgDatabase(self.syntax(), args)

        if argData.isFlagSet('-d'):
            division = argData.flagArgumentInt('-d', 0)
            if division > 1:
                self._division = division
            else:
                sys.stderr.write("invalid division: %d, division must be greater than 1" % division)
                raise

        if argData.isFlagSet('-r'):
            radius = argData.flagArgumentDouble('-r', 0)
            if radius >= 0:
                self._radius = radius
            else:
                sys.stderr.write("invalid radius: %s, radius cannot be negative" % radius)
                raise

        if argData.isFlagSet('-s'):
            spherical = argData.flagArgumentDouble('-r', 0)
            if spherical >= 0.0 and spherical <= 1.0:
                self._spherical = spherical

        if argData.isFlagSet('-na'):
            self._name = argData.flagArgumentString('-na', 0)

    def redoIt(self):
        # transform node
        transNodeFn = om.MFnDagNode()
        if self._name:
            transNodeFn.create('transform', self._name)
        else:
            transNodeFn.create('transform')

        # mesh node
        meshNodeFn = om.MFnDagNode()
        meshNodeFn.create('mesh', transNodeFn.name() + 'Shape', transNodeFn.object())

        # quad sphere node
        qsNodeFn = om.MFnDependencyNode()
        qsNodeFn.create('quadsphere')

        divisionPlug = qsNodeFn.findPlug('division')
        divisionPlug.setInt(self._division)

        radiusPlug = qsNodeFn.findPlug('radius')
        radiusPlug.setFloat(self._radius)

        sphericalPlug = qsNodeFn.findPlug('spherical')
        sphericalPlug.setFloat(self._spherical)

        outMeshPlug = qsNodeFn.findPlug('outputMesh')
        meshInputPlug = meshNodeFn.findPlug('inMesh')

        dgModifier = om.MDGModifier()
        dgModifier.connect(outMeshPlug, meshInputPlug)
        dgModifier.doIt()

        self._nodePath = om.MDagPath()
        transNodeFn.getPath(self._nodePath)

        self._assignDefaultShading(meshNodeFn, dgModifier)
        self._selectCreatedObject(self._nodePath)

        self.setResult([transNodeFn.name(), meshNodeFn.name()])

    def _assignDefaultShading(self, meshNodeFn, dgModifier):
        dgModifier.commandToExecute('sets -e -forceElement initialShadingGroup %s' %meshNodeFn.fullPathName())
        dgModifier.doIt()

    def _selectCreatedObject(self, dgPath):
        selectionList = om.MSelectionList()
        selectionList.add(dgPath)
        om.MGlobal.setActiveSelectionList(selectionList)

    def isUndoable(self):
        return True

    def undoIt(self):
        if self._nodePath is not None:
            try:
                om.MGlobal.executeCommand('delete %s' %self._nodePath.fullPathName())
            finally:
                self._nodePath = None


def commandCreator():
    return OpenMayaMPx.asMPxPtr(QuadsphereCommand())

def syntaxCreator():
    syntax = om.MSyntax()

    syntax.addFlag('-d', '-division', om.MSyntax.kLong)
    syntax.addFlag('-r', '-radius', om.MSyntax.kDouble)
    syntax.addFlag('-s', '-spherical', om.MSyntax.kDouble)
    syntax.addFlag('-na', '-name', om.MSyntax.kString)

    return syntax

# plugin initialization
def initializePlugin(mObject):
    mplugin = OpenMayaMPx.MFnPlugin(mObject, __author__)
    try:
        mplugin.registerCommand(kPluginCmdName, commandCreator, syntaxCreator)
        mplugin.setVersion(__version__)
    except:
        sys.stderr.write("Failed to register command: %s" % kPluginCmdName)
        raise

    try:
        om.MGlobal.sourceFile("quadsphere_createui.mel")
        om.MGlobal.executeCommand("Quadsphere_UIInit()")
    except:
        sys.stderr.write("quadsphere: error occurred when run createui script")
        pass

def uninitializePlugin(mObject):
    mplugin = OpenMayaMPx.MFnPlugin(mObject)
    try:
        mplugin.deregisterCommand(kPluginCmdName)
    except:
        sys.stderr.write("Failed to deregister command: %s" %kPluginCmdName)
        raise

    try:
        om.MGlobal.sourceFile("quadsphere_deleteui.mel")
    except:
        sys.stderr.write("quadsphere: error occurred when run deleteui script")
        pass
