# ######### Mok_AttributeReorder v1.0 ##########
#
# Description: Script For reorder Attributes in channelbox
# and Attribute Editor/Extra attributes
#
#
# Intallation:
#        place files in yourdocument\maya\2012\scripts
#
# How to use:
#         import Mok_AttributeReorder
#         Mok_AttributeReorder.UI()
#
# Author: PERIN Morgan
#      scudyreal@gmail.com

import maya.cmds as cmds
import maya.mel as mel
import os


def Mok_AttributeReorderUI():
    # mayaVersion = float(cmds.about(version=True))
    Attrs = []
    fileAddress = os.path.split(__file__)[0]
    LayoutName = "Win_Mok_AttrReorder"
    if cmds.formLayout(LayoutName, ex=True):
        cmds.deleteUI(LayoutName, lay=True)
    Objs = cmds.channelBox('mainChannelBox', q=True, mol=True)
    if len(Objs) > 0:
        Attrs = cmds.listAttr(Objs[0], ud=True)
    NameLayout = 'ChannelsLayersPaneLayout'
    if cmds.paneLayout(NameLayout, q=True, cn=True) == 'horizontal2':
        cmds.paneLayout(NameLayout, e=True, cn='horizontal3')
        cmds.paneLayout(NameLayout, e=True, setPane=('LayerEditorForm', 3))

    # Command for deleting UI
    cmd = 'Mok_AttributeReorder.Mok_AttributeReorderUI_Delete("'
    cmd += LayoutName + '")'

    # Edit formLayout
    cmds.formLayout(LayoutName, nd=100, p='ChannelsLayersPaneLayout')
    b1 = cmds.button(
        w=100, h=20,
        label=' Check ',
        c='Mok_AttributeReorder.Mok_AttributeReorderCheck()',
        p=LayoutName
    )
    b2 = cmds.button(
        w=100, h=20,
        label=' Reorder ',
        c='Mok_AttributeReorder.Mok_AttributeReorder()',
        p=LayoutName
    )
    b3 = cmds.button(
        w=20, h=20,
        label='X',
        c=cmd,
        p=LayoutName
    )
    Scroll = cmds.loadUI(uiFile=fileAddress + '/Mok_AttributeReorderUI.ui')
    cmds.showWindow(Scroll)
    cmds.window(Scroll, e=True, vis=0, wh=(10, 10), tlc=(0, 0))
    cmds.textScrollList('ScrollListAttrReor', e=True, p='Win_Mok_AttrReorder')
    cmds.deleteUI(Scroll, wnd=True)
    for Attr in Attrs:
        cmds.textScrollList('ScrollListAttrReor', e=True, append=Attr)
    cmds.formLayout(
        LayoutName,
        e=True,
        af=[
            (b1, 'top', 5),
            (b1, 'left', 5),
            (b2, 'top', 5),
            (b3, 'top', 5),
            (b3, 'right', 5),
            ('ScrollListAttrReor', 'left', 5),
            ('ScrollListAttrReor', 'right', 5),
            ('ScrollListAttrReor', 'bottom', 5)
        ],
        ac=[
            ('ScrollListAttrReor', 'top', 5, b1),
            (b2, 'left', 5, b1),
            (b2, 'right', 5, b3)
        ]
    )


def Mok_AttributeReorderCheck():
    Objs = cmds.channelBox('mainChannelBox', q=True, mol=True)
    Attrs = []
    if len(Objs) > 0:
        Attrs = cmds.listAttr(Objs[0], ud=True)
    cmds.textScrollList('ScrollListAttrReor', e=True, ra=True)
    for Attr in Attrs:
        cmds.textScrollList('ScrollListAttrReor', e=True, append=Attr)


def Mok_AttributeReorderUI_Delete(Layout):
    cmds.deleteUI(Layout, lay=True)
    cmds.paneLayout(
        'ChannelsLayersPaneLayout', e=True, setPane=('LayerEditorForm', 2)
    )
    cmds.paneLayout('ChannelsLayersPaneLayout', e=True, cn='horizontal2')


def Mok_AttributeReorder():
    Objs = cmds.channelBox('mainChannelBox', q=True, mol=True)
    Attrs = cmds.textScrollList('ScrollListAttrReor', q=True, ai=True)
    for obj in Objs:
        for attr in Attrs:
            if cmds.attributeQuery(attr, n=obj, ex=True):
                if cmds.getAttr(obj + '.' + attr, lock=True):
                    cmds.setAttr(obj + '.' + attr, lock=False)
                    try:
                        cmds.deleteAttr(obj, at=attr)
                    except:
                        print('nothing to delete')
                    cmds.undo()
                    cmds.setAttr(obj + '.' + attr, lock=True)
                else:
                    try:
                        cmds.deleteAttr(obj, at=attr)
                    except:
                        print('nothing to delete')
                    cmds.undo()
    mel.eval('refreshEditorTemplates')


def UI():
    Mok_AttributeReorderUI()
