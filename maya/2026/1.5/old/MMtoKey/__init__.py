import os
import sys
import maya.cmds as cmds
from MMtoKey import Engine, LanguageChange


def ui(*args):
    """open marking menu editor"""
    from MMtoKey import Editor
    Editor.MainWindow(engine)


def languageChange(*args):
    LanguageChange.MainWindow()


def hotkeyMaker(*args):
    from MMtoKey import HotkeyMaker
    HotkeyMaker.MainWindow()


def clearCache(*args):
    Engine.Menu.clearCache()


def menu(parent):
    """load via amTinyTools"""
    cmds.setParent(parent, menu=True)
    cmds.menuItem(label="MMtoKey", d=True)
    cmds.menuItem(label="MMtoKey", c=ui)
    cmds.menuItem(label="Hotkey Maker", c=hotkeyMaker)
    cmds.menuItem(label="Marking Menu Language", c=languageChange)
    cmds.menuItem(label="Clear Cache", c=clearCache)


sys.path.append(os.path.dirname(__file__))
engine = Engine.Engine()
pressSelected = engine.pressSelected    # sh, alt, ctl
releaseSelected = engine.releaseSelected
pressCustom = engine.pressCustom        # sh, alt, ctl, menu_name, menu_type
releaseCustom = engine.releaseCustom    # command, language, command_always
pressPreset = engine.pressPreset        # sh, alt, ctl
releasePreset = engine.releasePreset
