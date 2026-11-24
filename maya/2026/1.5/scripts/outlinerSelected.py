"""
Opens a small Outliner that shows only the nodes that were selected when it was opened.

Usage:
    import outlinerSelected
    outlinerSelected.outlinerSelected()
"""

from maya import cmds


def _delete_connection(sc):
    if cmds.selectionConnection(sc, exists=True):
        cmds.deleteUI(sc)


def outlinerSelected():
    selection = cmds.ls(sl=True)
    if not selection:
        cmds.warning("Nothing selected!  Custom Outliner not created.")
        return None

    # Create our selectionConnection - as 'connectionList' type
    sc = cmds.selectionConnection(lst=True)

    # Add current selection to the selectionConnection
    for node in selection:
        cmds.selectionConnection(sc, e=True, select=node)

    # Create window layout to hold the Outliner
    win = cmds.window(rtf=True, title="Outliner (Custom)", iconName="Outliner*")
    frame = cmds.frameLayout(lv=False)

    # Create an unparented outlinerEditor
    editor = cmds.outlinerEditor(
        showSetMembers=True, showDagOnly=False, showShapes=True,
        showNamespace=True, unParent=True)

    # Show our custom list, keep selection in sync with the scene
    cmds.outlinerEditor(editor, e=True, mainListConnection=sc, selectionConnection="modelList")

    # Parent the outlinerEditor to this window
    cmds.outlinerEditor(editor, e=True, parent=frame)

    # Delete the selectionConnection when the window is closed
    cmds.scriptJob(uiDeleted=(win, lambda: _delete_connection(sc)), runOnce=True)

    cmds.showWindow(win)
    cmds.window(win, e=True, w=240, h=240)
    return win


if __name__ == "__main__":
    outlinerSelected()