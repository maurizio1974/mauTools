"""
weight_utils_cmds - undoable "setDeformerWeights" command used by weight_utils.py.

    setDeformerWeights <components or shape> -d <deformer> [-a <weight attribute>] -w <w> -w <w> ...

One -w value per component, in the order the components were given. If only the shape is
given, one value per deformerSet member, in deformerSet order.

Maya 2026 port (works on Python 2.7 and 3.x). Changes from the original:
- FIX: getObjects() needs an MStringArray (it was given a Python list).
- FIX: error messages used an undefined `deformer_node` (NameError instead of the message).
- FIX: NURBS-surface selections used an unbound MFnDoubleIndexedComponent().
- FIX: errors now stop the command instead of carrying on with empty data.
- FIX: weights are matched to components by index, so they can't be shifted when Maya
  merges/reorders the selection; the deformerSet intersection is a set lookup
  (it was a nested loop, O(selected x members), which stalled on dense meshes).
- Deformers that are not weightGeometryFilters (Maya 2022+ gives every deformer
  weightList[].weights) fall back to writing the `weights` plug, so undo still works.
"""
import re

import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
import maya.OpenMayaAnim as omAnim

COMMAND_NAME = "setDeformerWeights"

_SINGLE_RE = re.compile(r"\.(?:vtx|cv|pt)\[(\d+)\]$")
_DOUBLE_RE = re.compile(r"\.cv\[(\d+)\]\[(\d+)\]$")
_TRIPLE_RE = re.compile(r"\.pt\[(\d+)\]\[(\d+)\]\[(\d+)\]$")


def _fail(message):
    om.MGlobal.displayError(message)
    raise RuntimeError(message)


def _component_keys(components):
    """Element ids of a component MObject, in element order (int, (u, v) or (s, t, u))."""
    if components.hasFn(om.MFn.kSingleIndexedComponent):
        ints = om.MIntArray()
        om.MFnSingleIndexedComponent(components).getElements(ints)
        return [ints[i] for i in range(ints.length())], 1
    if components.hasFn(om.MFn.kDoubleIndexedComponent):
        u, v = om.MIntArray(), om.MIntArray()
        om.MFnDoubleIndexedComponent(components).getElements(u, v)
        return [(u[i], v[i]) for i in range(u.length())], 2
    if components.hasFn(om.MFn.kTripleIndexedComponent):
        s, t, u = om.MIntArray(), om.MIntArray(), om.MIntArray()
        om.MFnTripleIndexedComponent(components).getElements(s, t, u)
        return [(s[i], t[i], u[i]) for i in range(s.length())], 3
    _fail("unsupported component type: %s" % components.apiTypeStr())


class setTargetWeights(ompx.MPxCommand):

    def __init__(self):
        ompx.MPxCommand.__init__(self)
        self.shape_index = 0
        self.oldWeights = om.MFloatArray()
        self.newWeights = []
        self.validWeights = om.MFloatArray()

        self.objectStrings = []
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
        self.parseArgs(args)
        self.processArgs()
        self.getOldWeights()
        return self.redoIt()

    # ------------------------------------------------------------------ args
    def parseArgs(self, args):
        dataBase = om.MArgDatabase(self.syntax(), args)

        objects = om.MStringArray()
        dataBase.getObjects(objects)
        self.objectStrings = [objects[i] for i in range(objects.length())]
        if not self.objectStrings:
            _fail(COMMAND_NAME + ": no components or shape given")

        if not dataBase.isFlagSet("-d"):
            _fail(COMMAND_NAME + ": the -deformer flag is required")
        self.deformerString = dataBase.flagArgumentString("-d", 0)

        if dataBase.isFlagSet("-a"):
            self.attributeString = dataBase.flagArgumentString("-a", 0)

        self.newWeights = []
        if dataBase.isFlagSet("-w"):
            for i in range(dataBase.numberOfFlagUses("-w")):
                weights_argList = om.MArgList()
                dataBase.getFlagArgumentList("-w", i, weights_argList)
                self.newWeights.append(weights_argList.asDouble(0))

    def processArgs(self):
        sel = om.MSelectionList()
        try:
            sel.add(self.deformerString)
        except RuntimeError:
            _fail('"%s" does not exist' % self.deformerString)
        sel.getDependNode(0, self.deformer_mObj)
        if not self.deformer_mObj.hasFn(om.MFn.kGeometryFilt):
            _fail('%s is not a deformer' % self.deformerString)

        # All the strings name one shape; Maya merges them into one selection item.
        stringSel = om.MSelectionList()
        for eachItem in self.objectStrings:
            stringSel.add(eachItem)
        stringSel.getDagPath(0, self.inputDagPath, self.inputComponents)
        stringSel.getDependNode(0, self.inputMObject)

        self.getValidSel()

        # Maya 2022+: every deformer has weightList[].weights, but only weightGeometryFilters
        # (cluster, softMod, ...) have MFnWeightGeometryFilter. Use the plug for the rest.
        if not self.attributeString and not self.deformer_mObj.hasFn(om.MFn.kWeightGeometryFilt):
            self.attributeString = 'weights'

        if self.attributeString:
            self.attribute_plug = self._resolveWeightPlug()

    def _resolveWeightPlug(self):
        mFnDepend = om.MFnDependencyNode(self.deformer_mObj)
        try:
            weights_plug = mFnDepend.findPlug(self.attributeString.split('.')[-1], False)
        except RuntimeError:
            _fail('%s has no attribute "%s"' % (self.deformerString, self.attributeString))

        prefix = '%s is not a valid weights plug for %s because ' % (weights_plug.name(), self.deformerString)
        if not weights_plug.isArray():
            _fail(prefix + 'it is not an array.')
        if not weights_plug.isChild():
            _fail(prefix + 'it has no parent.')
        if not weights_plug.parent().isElement() and not weights_plug.parent().isArray():
            _fail(prefix + "its parent is not an array.")
        if weights_plug.isCompound():
            _fail(prefix + 'it has children.')

        # blahblah[0].blahblah[0].weightList[-1].weights
        # The last two tokens are weights[*] and the per-shape weightList element,
        # whose index comes from the shape.
        parentTokens = reversed(self.attributeString.split('.')[:-2])
        parent_indices = [int(x.split('[')[-1][:-1]) for x in parentTokens]
        parent_indices.insert(0, self.shape_index)

        currentPlug = om.MPlug(weights_plug)
        for parent_id in parent_indices:
            if currentPlug.isElement():
                currentPlug = currentPlug.array()
            currentPlug = currentPlug.parent()
            weights_plug.selectAncestorLogicalIndex(parent_id, currentPlug.attribute())
        return weights_plug

    # ------------------------------------------------------------ selection
    def _inputKeys(self, dimension):
        """Component ids of the input strings, in the order given (one per -w value)."""
        regex = {1: _SINGLE_RE, 2: _DOUBLE_RE, 3: _TRIPLE_RE}[dimension]
        keys = []
        for item in self.objectStrings:
            m = regex.search(item)
            if m is None:
                keys = None
                break
            g = tuple(int(x) for x in m.groups())
            keys.append(g[0] if dimension == 1 else g)
        if keys is not None:
            return keys
        # Ranges ("vtx[0:9]") or other forms: ask Maya, one string at a time, to keep the order.
        keys = []
        for item in self.objectStrings:
            one = om.MSelectionList()
            one.add(item)
            path, comps = om.MDagPath(), om.MObject()
            one.getDagPath(0, path, comps)
            if comps.isNull():
                _fail('"%s" is not a component' % item)
            keys.extend(_component_keys(comps)[0])
        return keys

    def getValidSel(self):
        members = om.MSelectionList()
        mFnGeometryFilter = omAnim.MFnGeometryFilter(self.deformer_mObj)
        # Deformer set members, or (Maya 2022+ component tags, no set) the tagged components.
        from weight_utils import get_deformer_members
        get_deformer_members(mFnGeometryFilter, members)

        member_index = -1
        for i in range(members.length()):
            members_mObj = om.MObject()
            members.getDependNode(i, members_mObj)
            if members_mObj == self.inputMObject:
                member_index = i
                break
        if member_index == -1:
            _fail('%s is not deformed by %s' % (self.inputDagPath.partialPathName(), self.deformerString))

        membersDagPath = om.MDagPath()
        membersComponents = om.MObject()
        members.getDagPath(member_index, membersDagPath, membersComponents)
        if membersComponents.isNull():
            _fail('the deformerSet of %s has no components for %s'
                  % (self.deformerString, membersDagPath.partialPathName()))

        member_keys, dimension = _component_keys(membersComponents)

        if self.inputComponents.isNull():
            # Whole shape: one weight per deformerSet member, in the order weight_utils
            # walks them (MItGeometry over the deformerSet components).
            input_keys = member_keys
            if dimension == 1:
                mit = om.MItGeometry(membersDagPath, membersComponents)
                input_keys = []
                while not mit.isDone():
                    input_keys.append(mit.index())
                    mit.next()
        else:
            input_keys = self._inputKeys(dimension)

        if len(self.newWeights) != len(input_keys):
            _fail('%s: got %d weights for %d components'
                  % (COMMAND_NAME, len(self.newWeights), len(input_keys)))

        weight_by_key = dict(zip(input_keys, self.newWeights))   # last value wins for duplicates
        member_set = set(member_keys)

        apiType = membersComponents.apiType()
        if dimension == 1:
            mFn = om.MFnSingleIndexedComponent()
        elif dimension == 2:
            mFn = om.MFnDoubleIndexedComponent()
        else:
            mFn = om.MFnTripleIndexedComponent()
        validComps = mFn.create(apiType)

        # Add the elements in index order, so the component's element order, MItGeometry's
        # order and the weight order are all the same whatever order the input came in.
        valid_keys = sorted(set(k for k in input_keys if k in member_set))
        for key in valid_keys:
            if dimension == 1:
                mFn.addElement(key)
            else:
                mFn.addElement(*key)
        if not valid_keys:
            _fail('none of the given components are in the deformerSet of %s' % self.deformerString)

        self.validWeights = om.MFloatArray()
        for key in valid_keys:
            self.validWeights.append(weight_by_key[key])

        self.validDagPath = membersDagPath
        self.validComponents = validComps
        self.shape_index = mFnGeometryFilter.indexForOutputShape(self.inputMObject)
        return True

    # ---------------------------------------------------------------- weights
    def _plugIndices(self):
        mit = om.MItGeometry(self.validDagPath, self.validComponents)
        indices = []
        while not mit.isDone():
            indices.append(mit.index())
            mit.next()
        return indices

    def getOldWeights(self):
        self.oldWeights = om.MFloatArray()
        if self.attributeString:
            self.plugIndices = self._plugIndices()
            for comp_index in self.plugIndices:
                self.oldWeights.append(self.attribute_plug.elementByLogicalIndex(comp_index).asFloat())
        else:
            mFnWeight = omAnim.MFnWeightGeometryFilter(self.deformer_mObj)
            mFnWeight.getWeights(self.shape_index, self.validComponents, self.oldWeights)

    def _apply(self, values):
        if self.attributeString:
            mdg = om.MDGModifier()
            # Force an update by setting the first element
            zeroPlug = self.attribute_plug.elementByLogicalIndex(0)
            mdg.newPlugValueFloat(zeroPlug, zeroPlug.asFloat())
            for i, comp_index in enumerate(self.plugIndices):
                mdg.newPlugValueFloat(self.attribute_plug.elementByLogicalIndex(comp_index), values[i])
            mdg.doIt()
        else:
            mFnWeight = omAnim.MFnWeightGeometryFilter(self.deformer_mObj)
            mFnWeight.setWeight(self.validDagPath, self.shape_index, self.validComponents, values)

    def redoIt(self):
        self._apply(self.validWeights)

    def undoIt(self):
        self._apply(self.oldWeights)


def newSyntax():
    syntax = om.MSyntax()
    syntax.setObjectType(om.MSyntax.kStringObjects, 1)
    syntax.useSelectionAsDefault(False)
    syntax.enableQuery(False)
    syntax.enableEdit(False)
    syntax.addFlag('-d', '-deformer', om.MSyntax.kString)
    syntax.addFlag('-a', '-attribute', om.MSyntax.kString)
    syntax.addFlag('-w', '-weights', om.MSyntax.kDouble)
    syntax.makeFlagMultiUse('-w')
    return syntax


def creator():
    return ompx.asMPxPtr(setTargetWeights())


def initializePlugin(obj):
    plugin = ompx.MFnPlugin(obj, 'J Reinhart', "4.0", "Any")
    try:
        plugin.registerCommand(COMMAND_NAME, creator, newSyntax)
    except Exception:
        om.MGlobal.displayError("Failed to register command " + COMMAND_NAME)
        raise


def uninitializePlugin(obj):
    plugin = ompx.MFnPlugin(obj)
    try:
        plugin.deregisterCommand(COMMAND_NAME)
    except Exception:
        om.MGlobal.displayError("Failed to deregister command " + COMMAND_NAME)
        raise
