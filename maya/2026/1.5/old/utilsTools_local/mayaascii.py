import re

__all__ = ["MayaAscii", "Reference", "AddReferenceError", "MayaAsciiError"]


def getMayaFile():
    import maya.cmds as cmds
    return cmds.file(q=True, sn=True)


class MayaAsciiError(Exception):
    """Base class for exceptions in this module."""
    pass


class AddReferenceError(MayaAsciiError):
    pass


class Reference(object):
    """
    """

    def __init__(self, path=None, namespace=None, referenceNode=None, parentNamespace=None, isDeferred=None):
        """
        @type path: str
        @type namespace: str
        @type referenceNode: str
        @type parentNamespace: str
        @type isDeferred: bool
        """
        self.path = path
        self.namespace = namespace
        self.isDeferred = isDeferred
        self.referenceNode = referenceNode
        self.parentNamespace = parentNamespace
        self.nestedReferences = []

    @classmethod
    def createFromReference(cls, r):
        """
        @type r: Reference
        @rtype: Reference
        """
        return cls(path=r.path, namespace=r.namespace, referenceNode=r.referenceNode)

    @classmethod
    def createFromLine(cls, line):
        """
        www.regexpal.com
        Line: file -rdi 1 -ns "character1" -dr 1 -rfn "character1_RN"
                 "/tmp/asset.ma";
        Result: "character1", "/tmp/asset.ma"
        @type line: str
        @rtype: Reference | None
        """
        regex = re.compile(r'-ns "(.*)".*-rfn "(.*)"\n?.*"(.*)"')
        r = regex.search(line)
        if r:
            parentNamespace = r.group(2).split(":")[0]
            return cls(path=r.group(3), namespace=r.group(1), referenceNode=r.group(2),
                       parentNamespace=parentNamespace)


class MayaAscii(object):
    """
    @type length: int
    @type animrange: list[int]
    @type _referencesLvl1: dict[]
    @type _referencesLvl2: dict[]
    """

    def __init__(self, path):
        """
        @type path: str
        """
        self.path = path
        self.resetCache()

    def resetCache(self):
        """
        """
        self.length = None
        self.animrange = None
        self._referencesLvl1 = None
        self._referencesLvl2 = None

    def getHeader(self):
        """
        @rtype: str
        """
        result = []
        with open(self.path) as f:
            for line in f:
                if line.startswith("createNode"):
                    break
                else:
                    result.append(line)
        return "".join(result)

    def getHeaderLines(self, splitter=";\n"):
        """
        @type: splitter
        """
        return self.getHeader().split(splitter)

    def read(self, path=None):
        """
        @type path: str
        """
        path = path or self.path
        f = open(path, 'r')
        data = f.read()
        f.close()
        return data

    def readlines(self, splitter=";\n"):
        """
        @type splitter: str
        @rtype: list[str]
        """
        lines = self.read().split(splitter)

        # If we split with ";" then the first reference will be attached to the "//" header.
        regex = re.compile(r'^//(.*\n//)*.*\n')
        h = regex.search(lines[0])
        line1 = h.group()
        line2 = lines[0].replace(line1, "")

        lines[0] = line1
        lines.insert(1, line2)
        return lines

    def writelines(self, lines, path=None, splitter=";\n"):
        """
        @type lines: list[str]
        @type splitter: str
        """
        path = path or self.path
        line1 = lines.pop(0)
        data = splitter.join(lines)
        data = line1 + data
        f = open(path, 'w')
        f.writelines(data)
        f.close()

    def replace(self, values, srcPath=None, dstPath=None):
        """
        @type values: list[list[str]]
        @type srcPath: str
        @type dstPath: str
        """
        data = self.read(srcPath)
        for old, new in values:
            data = re.sub(old, new, data)
        path = dstPath or self.path
        f = open(path, 'w')
        f.write(str(data))
        f.close()

    def replaceReference(self, oldReference, newReference):
        """
        @type oldReference: Reference
        @type newReference: Reference
        """
        return self.replaceReferences([[oldReference, newReference]])

    def replaceReferences(self, values, dstPath=None):
        """
        import mayaascii
        ma = mayaascii.MayaAscii("/shot.ma")

        oldReference = ma.getReferenceFromNamespace("character1")
        newReference = mayaascii.CreateFromReference(oldReference)
        newReference.path = "/new/charater.ma"

        ma.replaceReferences([(oldReference, newReference)]):

        @type values: list[list[Reference]]
        """
        newLines = []
        oldLines = self.readlines()
        for line in oldLines:
            newLine = line
            if line.startswith("file -r"):
                reference = Reference.createFromLine(line)
                if reference:
                    for oldReference, newReference in values:
                        if reference.namespace == oldReference.namespace:
                            if newReference.path is not None:
                                newLine = newLine.replace(
                                    '"%s"' % oldReference.path, '"%s"' % newReference.path)
                            if newReference.namespace is not None:
                                newLine = newLine.replace(
                                    '"%s"' % oldReference.namespace, '"%s"' % newReference.namespace)
                            if newReference.referenceNode is not None:
                                newLine = newLine.replace(
                                    '"%s"' % oldReference.referenceNode, '"%s"' % newReference.referenceNode)
            newLines.append(newLine)
        self.writelines(newLines, path=dstPath)

    @staticmethod
    def getReferenceFromLine(line):
        """
        @type line: str
        @rtype: Reference | None
        """
        return Reference.createFromLine(line)

    def getReferenceFromNode(self, node):
        """
        @type node: str
        @rtype: Reference | None
        """
        references = self.getReferences()
        for reference in references:
            if reference.referenceNode == node:
                return reference

    def getReferenceFromNamespace(self, namespace):
        """
        @type namespace: str
        @rtype: Reference | None
        """
        references = self.getReferences()
        for reference in references:
            if reference.namespace == namespace:
                return reference

    def getReferences(self):
        """
        @rtype: list[Reference]
        """
        if self._referencesLvl1 is None:
            self._referencesLvl1 = {}
            self._referencesLvl2 = {}

            for line in self.getHeaderLines():
                if "file -rdi 1" in line:
                    r = self.getReferenceFromLine(line)
                    if r:
                        self._referencesLvl1[r.namespace] = r

                elif "file -rdi 2" in line:
                    r = self.getReferenceFromLine(line)
                    if r:
                        if r.parentNamespace in list(self._referencesLvl2.keys()):
                            self._referencesLvl2[r.parentNamespace].append(r)
                        else:
                            self._referencesLvl2[r.parentNamespace] = [r]

        return list(self._referencesLvl1.values())

    def getAnimationRange(self):
        """
        @rtype: list[int] | None
        """
        if self.animrange is None:
            self.animrange = []
            lines = self.readlines()
            for line in lines:
                if "playbackOptions" in line:
                    regex = re.compile(
                        r'-min (.*) -max (.*) -ast (.*) -aet (.*) "')
                    m = regex.search(line)
                    if m:
                        self.length = int(m.group(2)) - int(m.group(1))
                        self.animrange = [int(m.group(3)), int(m.group(4))]
                    break
        return self.animrange

    def getLength(self):
        """
        @rtype: float | None
        """
        if self.length is None:
            self.getAnimationRange()
        return self.length

    def getRangeFromNode(self):
        pass

    def getReferenceEdits(self):
        pass

    def namespaceExists(self, namespace):
        """
        @type namespace: str
        @rtype: bool
        """
        namespaces = [r.namespace for r in self.getReferences()]
        return namespace in namespaces

    def referenceNodeExists(self, referenceNode):
        """
        @type referenceNode: str
        @rtype: bool
        """
        referenceNodes = [r.referenceNode for r in self.getReferences()]
        return referenceNode in referenceNodes

    def addReference(self, reference, dstPath=None):
        """
        Adds the following two lines to the maya ascii
        file -rdi 1 -ns "character1" -dr 1 -rfn "characterRN" "/tmp/character.ma";
        file -r -ns "character1" -dr 1 -rfn "characterRN" "/tmp/character.ma";
        @type reference: Reference
        """

        dstPath = dstPath or self.path
        deferred = "-dr 1 " if reference.isDeferred else ""

        if self.namespaceExists(reference.namespace):
            raise AddReferenceError(
                'The namespace "%s" already exists!' % reference.namespace)

        if self.referenceNodeExists(reference.referenceNode):
            raise AddReferenceError(
                'The referenceNode "%s" already exists!' % reference.referenceNode)

        referenceLine = '-ns "%s" %s-rfn "%s" "%s"' % (
            reference.namespace, deferred, reference.referenceNode, reference.path)
        referenceLine1 = 'file -rdi 1 ' + referenceLine
        referenceLine2 = 'file -r ' + referenceLine

        lines = self.readlines()

        for i, line in enumerate(lines):
            if not line.startswith("//"):
                lines.insert(i, referenceLine1)
                break

        for i, line in enumerate(lines):
            if line.startswith("requires"):
                lines.insert(i, referenceLine2)
                break
            if line.startswith("createNode"):
                raise AddReferenceError(
                    'Cannot add reference! The keyword "requires" not found.')

        self.writelines(lines, path=dstPath)
        self.resetCache()
