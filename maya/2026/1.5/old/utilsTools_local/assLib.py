'''----------------------------------------------------------------------
OUTPOST ASS LIB

Date = 22-08-2019
User = Maurizio Giglioli
Usage:
    from utilsTools import *
    reload(assLib)

Update =
    (22-08-2019) First Release
----------------------------------------------------------------------'''
import os
import json
import maya.cmds as cmds
from pprint import pprint
import maya.api.OpenMaya as om


def uiSwitcher(cb, bbox, obbox, pwire, wire, pc, spoly, shd):
    dict = {
        cb: 'checkBox', bbox: 'button', obbox: 'button',
        pwire: 'button', wire: 'button', pc: 'button',
        spoly: 'button', shd: 'button'}
    for d in list(dict.keys()):
        cmd = 'cmds.' + dict[d] + '("' + d + '", q=True, l=True)'
        lab = eval(cmd)
        if 'Selection' in lab:
            info = 'Hierarchy'
            if 'Set' in lab:
                info = lab.replace('Selection', 'Hierarchy')
            cmd = 'cmds.' + dict[d] + '("' + d + '", e=True, l="' + info + '")'
            eval(cmd)
        else:
            info = 'Selection'
            if 'Set' in lab:
                info = lab.replace('Hierarchy', 'Selection')
            cmd = 'cmds.' + dict[d] + '("' + d + '", e=True, l="' + info + '")'
            eval(cmd)

def switchState(state, mode):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning('Please select an arnold standin')
        return
    for s in sel:
        if mode == 0:
            hir = cmds.ls(s, dag=True, type='transform')
            for h in hir:
                cur = cmds.listRelatives(h, s=True, ni=True)
                if cur:
                    for c in cur:
                        nt = cmds.nodeType(c)
                        if nt == 'aiStandIn':
                            cmds.setAttr(c + '.mode', state)
                        else:
                            print('Skipping ' + h + ' because it is not a standin')
        else:
            cur = cmds.listRelatives(s, s=True, ni=True)
            if cur:
                for c in cur:
                    nt = cmds.nodeType(c)
                    if nt == 'aiStandIn':
                        cmds.setAttr(c + '.mode', state)
                    else:
                        print('Skipping ' + s + ' because it is not a standin')

def ass_tools_UI():
    wht = 300
    winN = 'assTools_win'
    if cmds.window(winN, q=True, ex=True):
        cmds.deleteUI(winN)
    win = cmds.window(winN, t='ASS Tools')

    fl = cmds.formLayout(p=win)
    chb = cmds.checkBox(l='Selection', v=True, al='center')
    assB = cmds.button(l='Set Selection to bbox', p=fl)
    assPB = cmds.button(l='Set Selection to per Object bbox', p=fl)
    assPW = cmds.button(l='Set Selection to polyWire', p=fl)
    assW = cmds.button(l='Set Selection to wireframe', p=fl)
    assP = cmds.button(l='Set Selection to point cloud', p=fl)
    assSP = cmds.button(l='Set Selection to shaded polywire', p=fl)
    assS = cmds.button(l='Set Selection to shaded', p=fl)

    # ORGANIZE UI
    cmds.formLayout(
        fl,
        e=True,
        af=[
            (chb, 'left', wht/2.5), (chb, 'top', 5), (chb, 'right', 5),
            (assB, 'left', 5), (assB, 'right', 5),
            (assPB, 'left', 5), (assPB, 'right', 5),
            (assPW, 'left', 5), (assPW, 'right', 5),
            (assW, 'left', 5), (assW, 'right', 5),
            (assP, 'left', 5), (assP, 'right', 5),
            (assSP, 'left', 5), (assSP, 'right', 5),
            (assS, 'left', 5), (assS, 'right', 5)
        ],
        ac=[
            (assB, 'top', 5, chb),
            (assPB, 'top', 5, assB),
            (assPW, 'top', 5, assPB),
            (assW, 'top', 5, assPW),
            (assP, 'top', 5, assW),
            (assSP, 'top', 5, assP),
            (assS, 'top', 5, assSP)
        ]
    )
    # ADD COMMANDS TO BUTTONS
    ui = [chb, assB, assPB, assPW, assW, assP, assSP, assS]
    ui = '"' + ('", "').join(ui) + '"'

    cmds.checkBox(
        chb, e=True,
        onc='assLib.uiSwitcher(' + ui + ')',
        ofc='assLib.uiSwitcher(' + ui + ')')

    bts = [assB, assPB, assPW, assW, assP, assSP, assS]
    for x, b in enumerate(bts):
        cmds.button(
            b, e=True,
            c='assLib.switchState(' + str(x) + ', cmds.checkBox("' + chb + '", q=True, v=True))')

    # ADD DISCIPLINES PRESETS


    # SHOW WINDOW AND SIZE IT
    cmds.showWindow(win)
    cmds.window(win, e=True, w=wht, h=240)
