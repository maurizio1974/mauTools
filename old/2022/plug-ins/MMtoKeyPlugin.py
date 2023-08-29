import maya.api.OpenMaya as om2
import __main__
import MMtoKey
from MMtoKey.Version import version


maya_useNewAPI = True


def initializePlugin(m_object):
    om2.MFnPlugin(m_object, "Andrey Menshikov", version)
    __main__.MMtoKey = MMtoKey


def uninitializePlugin(*args):
    try:
        __main__.__delattr__("MMtoKey")
    except AttributeError:
        pass
