"""Entry points of an installed NodeX: Windows menu item, shelf button, uninstall.

The installer (installer/install.py) copies the package into a Maya module; the module's
userSetup.py calls `run()` deferred on every Maya start. Nothing here touches the user's own
userSetup.py: removing the module's .mod file and folder removes NodeX completely.
"""
import os
import shutil

import __main__
from maya import cmds, mel

VERSION = "1.1.1"
MODULE = "NodeX"
LABEL = "NodeX Node Editor"
COMMAND = "import nodex; nodex.show()"
WIN_MENU = "mainWindowMenu"
ITEM = "nodexWindowsMenuItem"
ICON = "nodeGrapherModeAllLarge.png"
_HOOK = "_nodex_windows_menu_post"     # NodeX 1.0 kept Maya's postMenuCommand here


def run():
    """Called from the module's userSetup.py (deferred): hook the Windows menu."""
    if cmds.about(batch=True):
        return
    add_menu()


# ---------------------------------------------------------------------------- Windows menu

def add_menu():
    """Add Windows > NodeX Node Editor without touching Maya's own menu builder.

    Maya fills Windows lazily from its MEL postMenuCommand, and rebuilds it (deleting every
    item) when it decides to. NodeX 1.0 replaced that postMenuCommand with a Python hook that
    re-ran the MEL itself; when that failed (Maya 2025+), Windows opened empty. Now the
    command is left alone and the item is added from the QMenu's aboutToShow, which fires
    after Maya's own handler has built the menu."""
    if not cmds.menu(WIN_MENU, exists=True):
        return
    _restore_post_command()
    _enabled[0] = True
    if cmds.menu(WIN_MENU, q=True, numberOfItems=True):
        _add_item()
    _watch_menu()


_enabled = [False]


def _restore_post_command():
    """Undo the 1.0 hook if this Maya session still has it (installed over an older copy)."""
    orig = getattr(__main__, _HOOK, None)
    if orig is None:
        return
    try:
        mel.eval('menu -e -postMenuCommand "%s" %s'
                 % (orig.replace("\\", "\\\\").replace('"', '\\"'), WIN_MENU))
    except RuntimeError:
        pass
    delattr(__main__, _HOOK)


def _qmenu():
    try:
        import maya.OpenMayaUI as omui
        from .qt import QtWidgets, wrapInstance
        ptr = omui.MQtUtil.findMenuItem(WIN_MENU)
        if ptr:
            return wrapInstance(int(ptr), QtWidgets.QMenu)
        main = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
        return main.findChild(QtWidgets.QMenu, WIN_MENU)
    except Exception:
        return None


def _watch_menu():
    menu = _qmenu()
    if menu is None or menu.property("nodexWatched"):
        return
    menu.setProperty("nodexWatched", True)
    menu.aboutToShow.connect(_on_about_to_show)


def _on_about_to_show():
    if not _enabled[0]:
        return
    try:
        if cmds.menu(WIN_MENU, q=True, numberOfItems=True):
            _add_item()
        else:
            # Maya's builder has not run yet: add the item right after it.
            cmds.evalDeferred(_add_item)
    except Exception as e:
        print("NodeX: could not add the Windows menu item: %s" % e)


def _add_item():
    if not _enabled[0] or cmds.menuItem(ITEM, exists=True):
        return
    kw = {"insertAfter": "wmNodeEditor"} if cmds.menuItem("wmNodeEditor", exists=True) else {}
    cmds.menuItem(ITEM, parent=WIN_MENU, label=LABEL, image=ICON, command=_show,
                  annotation="Open the NodeX node editor", **kw)


def remove_menu():
    _enabled[0] = False
    if cmds.menu(WIN_MENU, exists=True):
        _restore_post_command()
    if cmds.menuItem(ITEM, exists=True):
        cmds.deleteUI(ITEM, menuItem=True)


def _show(*_):
    import nodex
    nodex.show()


# ---------------------------------------------------------------------------- shelf

def _shelves():
    if cmds.about(batch=True):
        return None, []
    top = mel.eval("$_nx_shelf = $gShelfTopLevel")
    if not top or not cmds.shelfTabLayout(top, exists=True):
        return None, []
    return top, cmds.shelfTabLayout(top, q=True, childArray=True) or []


def _our_buttons(shelf):
    out = []
    for b in cmds.shelfLayout(shelf, q=True, childArray=True) or []:
        if cmds.shelfButton(b, exists=True) and \
                (cmds.shelfButton(b, q=True, docTag=True) or "") == MODULE:
            out.append(b)
    return out


def add_shelf_button():
    """One NodeX button on the current shelf (none added when any shelf already has one)."""
    top, shelves = _shelves()
    if not top:
        return None
    for s in shelves:
        found = _our_buttons(s)
        if found:
            return found[0]
    shelf = cmds.shelfTabLayout(top, q=True, selectTab=True)
    btn = cmds.shelfButton(parent=shelf, label=LABEL, annotation=LABEL, docTag=MODULE,
                           image=ICON, imageOverlayLabel="NX", sourceType="python",
                           command=COMMAND)
    mel.eval("saveAllShelves $gShelfTopLevel")
    return btn


def remove_shelf_buttons():
    top, shelves = _shelves()
    n = 0
    for s in shelves:
        for b in _our_buttons(s):
            cmds.deleteUI(b)
            n += 1
    if n:
        mel.eval("saveAllShelves $gShelfTopLevel")
    return n


# ---------------------------------------------------------------------------- uninstall

def module_dir():
    return os.path.join(cmds.internalVar(userAppDir=True), "modules")


def uninstall():
    """Remove the menu item, shelf buttons, the .mod file and the module folder."""
    try:
        import nodex
        nodex.close()
    except Exception:
        pass
    remove_menu()
    removed = remove_shelf_buttons()
    mods = module_dir()
    mod_file = os.path.join(mods, MODULE + ".mod")
    if os.path.isfile(mod_file):
        os.remove(mod_file)
    shutil.rmtree(os.path.join(mods, MODULE), ignore_errors=True)
    return "NodeX removed (%d shelf button%s); restart Maya to unload it" % (
        removed, "" if removed == 1 else "s")
