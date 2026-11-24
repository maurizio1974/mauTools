import os
import sys
import mSuperCB
import mWild as mW
from importlib import reload
from maya import mel, cmds, utils
import houdini_protan_maya


def setPaths(variable, value):
    current = os.environ.get(variable, "")
    paths = current.split(os.pathsep) if current else []
    if value not in sys.path:
        sys.path.append(value)
    if value not in paths:
        paths.append(value)
        os.environ[variable] = os.pathsep.join(paths)
        return True
    return False


# SET PATHS
base = os.path.join('/home/users', os.getlogin(), 'maya/extra/2026/mauTools/1.5', 'scripts/mauTools')
utils.executeDeferred("setPaths('MAYA_SCRIPT_PATH', base)")
utils.executeDeferred("setPaths('PYTHONPATH', base)")


# MAIN UI TWEAKS
utils.executeDeferred(mW.mSetWild)
# EXTRA CHANNEL BOX TOOLS
utils.executeDeferred(mSuperCB.superCB)
# REFERENCE SELECTION SCENE MATCH
cmds.evalDeferred("import refEdSelSync;refEdSelSync.install()", lowestPriority=True)

# COLORBLIND COLOR
maya.utils.executeDeferred(houdini_protan_maya.apply_ui_palette)

print('=' * 500)
print('Mau Environment Loaded')
print('=' * 500)
