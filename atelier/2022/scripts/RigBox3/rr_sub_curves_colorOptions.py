"""
Rigbox Reborn - Sub: Color Options

Author: Jennifer Conley
Date Modified: 11/23/12
Script updated: check rr_ReadMe.txt

Description:
    A script to quickly color control icons for a rig. Able to be run on a selection.
    Also has options for templating an object.

How to run:
    import rr_sub_curves_colorOptions
    rr_sub_curves_colorOptions.window_creation()
    
    More info in the text file : rr_ReadMe.txt
"""

import pymel.core as pm

window_name = 'rr_colors_win'
window_bgc = (.2, .2, .2)
element_bgc = (.45, .45, .45)
width = 300

# Choose your colors in these 6 slots
colorL1C1=(1, 0, 0)
colorL1C2=(0, 0, 1)
colorL2C1=(0.3, 1, 1)
colorL2C2=(1, 0.5, 0)
colorL3C1=(0.7, 0.15, 1)
colorL3C2=(1, 1, 0)


# Gui Creation
def window_creation():
    if pm.window(window_name, q=True, ex=True):
        pm.deleteUI(window_name)

    if pm.windowPref(window_name, ex=True):
        pm.windowPref(window_name, r=True)

    window_object = pm.window(window_name, bgc=window_bgc, w=width, t='RigBox Reborn - Color Options')
    gui_creation()
    window_object.show()


def gui_creation():
    main = pm.columnLayout(w=width)
    main_form = pm.formLayout(nd=100, w=width)

    color_options_title = pm.columnLayout(w=width)
    create_grouping_title = pm.columnLayout()
    # pm.separator(w=width-15, h=5)
    # pm.text(l='Color Options', w=width-15, bgc=(.66, 1, .66))
    pm.separator(w=width - 15, h=5)
    pm.text(w=width, l='Select the curves for coloring.')
    pm.text(w=width, l='Then click a color.')
    pm.separator(w=width - 15, h=5)
    pm.setParent(main_form)

    # Old code:
    # color_options = pm.columnLayout()
    # pm.rowColumnLayout(nc=2)
    # pm.button(l='', w=90, bgc=(1, 0, 0), c=pm.Callback(rr_colorCurves_buttons, 13))
    # pm.button(l='', w=90, bgc=(0, 0, 1), c=pm.Callback(rr_colorCurves_buttons, 6))
    # pm.button(l='', w=90, bgc=(0, 1, 1), c=pm.Callback(rr_colorCurves_buttons, 18))
    # pm.button(l='', w=90, bgc=(1, 0.5, 0.4), c=pm.Callback(rr_colorCurves_buttons, 21))
    # pm.button(l='', w=90, bgc=(.6, 0, 1), c=pm.Callback(rr_colorCurves_buttons, 30))
    # pm.button(l='', w=90, bgc=(1, 1, 0), c=pm.Callback(rr_colorCurves_buttons, 17))
    # pm.setParent(main_form)
    
    color_options = pm.columnLayout()
    pm.rowColumnLayout(nc=2)
    pm.button(l='', w=90, bgc=colorL1C1, c=pm.Callback(rr_RGBcolorCurves_buttons, color=colorL1C1))
    pm.button(l='', w=90, bgc=colorL1C2, c=pm.Callback(rr_RGBcolorCurves_buttons, color=colorL1C2))
    pm.button(l='', w=90, bgc=colorL2C1, c=pm.Callback(rr_RGBcolorCurves_buttons, color=colorL2C1))
    pm.button(l='', w=90, bgc=colorL2C2, c=pm.Callback(rr_RGBcolorCurves_buttons, color=colorL2C2))
    pm.button(l='', w=90, bgc=colorL3C1, c=pm.Callback(rr_RGBcolorCurves_buttons, color=colorL3C1))
    pm.button(l='', w=90, bgc=colorL3C2, c=pm.Callback(rr_RGBcolorCurves_buttons, color=colorL3C2))
    pm.setParent(main_form)

    divider = pm.columnLayout()
    pm.separator(h=70, hr=False)
    pm.setParent(main_form)

    template_options = pm.columnLayout(w=width)
    pm.button(l='Template Attr', bgc=element_bgc, w=95, c=rr_template_attr)
    pm.button(l='Template', bgc=element_bgc, w=95, c=rr_template_object)
    pm.button(l='Untemplate', bgc=element_bgc, w=95, c=rr_untemplate)
    pm.setParent(main_form)

    pm.formLayout(main_form, e=True,
                  attachForm=[(divider, 'bottom', 5),
                              (color_options, 'bottom', 5),
                              (color_options, 'left', 5),
                              (template_options, 'bottom', 5),
                              (color_options_title, 'right', 5),
                              (color_options_title, 'left', 5),
                              (color_options_title, 'top', 5)],
                  attachControl=[(divider, 'top', 2, color_options_title),
                                 (divider, 'right', 0, template_options),
                                 (divider, 'left', 0, color_options),
                                 (color_options, 'top', 2, color_options_title),
                                 (template_options, 'left', 5, color_options),
                                 (template_options, 'top', 2, color_options_title)],
                  attachPosition=[(color_options_title, 'right', 2, 60)])


# Work Functions
def rr_colorCurves_buttons(color):
    selection = pm.ls(sl=True)

    for each in selection:
        pm.setAttr(each + '.overrideEnabled', True)
        pm.setAttr(each + '.overrideColor', color)

    print("Selection's color has been changed.")
    
def rr_RGBcolorCurves_buttons(color = (1,1,1)):
    selection = pm.ls(sl=True)
    rgb = ("R","G","B")

    for each in selection:
        pm.setAttr(each + '.overrideEnabled', 1)
        pm.setAttr(each + '.overrideRGBColors', 1)
           
        for channel, color in zip(rgb, color):
            pm.setAttr(each + ".overrideColor%s" %channel, color)

    print("Selection's RGB color has been changed.")


def rr_template_object(*args):
    selection = pm.ls(sl=True)

    for individual_object in selection:
        pm.setAttr(individual_object + '.template', k=True)
        pm.setAttr(individual_object + '.template', 1)

    print("Selection has been templated.")


def rr_untemplate(*args):
    selection = pm.ls(sl=True)

    for individual_object in selection:
        pm.setAttr(individual_object + '.template', 0)

    print("Selection has been untemplated.")


def rr_template_attr(*args):
    selection = pm.ls(sl=True)

    for individual_object in selection:
        pm.setAttr(individual_object + '.template', k=True)

    print("Selection has had the template attribute set to 'keyable'.")
