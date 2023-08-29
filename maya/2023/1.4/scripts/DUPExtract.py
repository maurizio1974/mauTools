# DESCRIPTION:
# DUPExtract is an extremely efficient tool for both detaching faces from an
# object, or cloning the selected faces
# of an object.  Select a group of faces, and run DUPExtract.
# It will ask you if you want to detach the faces or clone them.
# If you detach, the selected faces will be removed from the orginal object
# and placed in a new one.
# If you clone, the original object will remain intact, and the faces will
# be duplicated into a new object.

import maya.cmds as cmds
import maya.mel as mel


def do_DUPExtract(dir):
    faces, out = cmds.ls(sl=True), []
    if faces:
        mesh = faces[0].split('.')
        dup = cmds.duplicate(mesh[0], rr=True)
        if dir == 0:
            mel.eval('InvertSelection')
            current = cmds.ls(sl=True)
            cmds.delete(faces)
            for c in current:
                out.append(c.replace(mesh[0], dup[0]))
            # for f in faces:
                # out.append(f.replace(mesh[0], dup[0]))
            cmds.delete(out)
        else:
            cmds.select(faces, r=True)
            mel.eval('InvertSelection')
            current = cmds.ls(sl=True)
            for c in current:
                out.append(c.replace(mesh[0], dup[0]))
            cmds.delete(out)

        cmds.rename(dup[0], dup[0] + '_DUP')
        dup[0] = dup[0] + '_DUP'

        cmds.select(cl=True)
        cmds.CenterPivot()
        return dup[0]
    else:
        print('--->>> Please Select some faces to duplicate or detach. <<<---')


def DUPExtract():
    if cmds.window('DelFacesConfirm', ex=True):
        cmds.deleteUI('DelFacesConfirm')

    cmds.window('DelFacesConfirm', t='Detach or Clone?', wh=(100, 100), s=True)
    cmds.formLayout('dupFR')
    cmds.button(
        'detachBttn',
        label="Detach",
        w=50,
        h=35,
        c='DUPExtract.do_DUPExtract(0)'
    )
    cmds.button(
        'cloneButt',
        label="Clone",
        w=50,
        h=35,
        c='DUPExtract.do_DUPExtract(1)'
    )

    cmds.formLayout(
        'dupFR',
        e=True,
        af=[
            ('detachBttn', "left", 5),
            ('detachBttn', "top", 5),
            ('detachBttn', "bottom", 5),
            ('cloneButt', "right", 5),
            ('cloneButt', "top", 5),
            ('cloneButt', "bottom", 5)
        ],
        ap=[
            ('detachBttn', "right", 5, 48)
        ],
        ac=[
            ('cloneButt', "left", 5, "detachBttn")
        ]
    )
    cmds.showWindow('DelFacesConfirm')
    cmds.window('DelFacesConfirm', e=True, wh=(150, 70))
