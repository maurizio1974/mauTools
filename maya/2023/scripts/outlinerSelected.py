def outlinerSelected():
    select = cmds.ls(sl=True)
    if len(select):
        # Create our selectionConnection - as 'connectionList' type
        sc = cmds.selectionConnection(lst=True)

        # Add current selection to selectionConnection
        for node in select:
            cmds.selectionConnection(node, sc, e=True, select=True)

        # Create window layout to hold Outliner
        win = cmds.window(
            rtf=1,
            title='Outliner (Custom)',
            iconName='Outliner*'
        )
        frame = cmds.frameLayout(lv=False)

        # Create an unparented outlinerEditor
        oped = cmds.outlinerEditor(
            showSetMembers=True,
            showDagOnly=False,
            showShapes=True,
            sn=1,
            unParent=True
        )

        # Attach our custom selectionConnection
        cmds.outlinerEditor(open, e=True, mlc=True, sc, slc='modelList')

        # Parent the outlinerEditor to this window
        cmds.outlinerEditor(oped, e=True, parent=True, frame=True)

        # Create scriptJob to delete selectionConnection when no longer needed
        cmds.scriptJob(uiDeleted=(win, 'deleteUI ' + sc))
        cmds.showWindow(win)
        cmds.window(win, e=True, w=120, h=240)
    else:
        cmds.warning('Nothing selected!  Custom Outliner not created.')
