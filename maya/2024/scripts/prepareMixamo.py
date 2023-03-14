from maya import mel
from maya import cmds


def mUI():
    if cmds.window('winPrepMixamoUI', q=True, ex=True):
        cmds.deleteUI('winPrepMixamoUI')
    win = cmds.window(
        'winPrepMixamoUI', t='Prepare Mixamo Mocap for Maya', rtf=True)
    # UI
    frT = cmds.formLayout()
    # UI ELEMENTS
    butM = cmds.button(l='Get Mixamo FBX', p=frT, en=True)
    mTx = cmds.textField(p=frT, en=True)
    nT = cmds.text('Clip Name', p=frT)
    nTx = cmds.textField(p=frT, en=True)
    butD = cmds.button(l='Set Rest Position', p=frT)
    butG = cmds.button(l='Characterize for Maya Mocap', p=frT)
    # FORMALYOUT ARRANGMENT
    cmds.formLayout(
        frT, e=True,
        af=[
            (butM, 'top', 5), (butM, 'left', 5),
            (mTx, 'top', 5), (mTx, 'right', 5),
            (butG, 'left', 5), (butG, 'right', 5),
            (nT, 'left', 5),
            (nTx, 'right', 5),
            (butD, 'left', 5), (butD, 'bottom', 5), (butD, 'right', 5)],
        ap=[
            (butM, 'right', 0, 50),
            (nT, 'right', 0, 50)],
        ac=[
            (mTx, 'left', 5, butM),
            (nT, 'top', 5, butM),
            (nTx, 'top', 5, butM), (nTx, 'left', 5, nT),
            (butG, 'top', 5, nTx),
            (butD, 'top', 5, butG)])
    # ADD COMMANDS TO UI
    cmds.button(butM, e=True, c='cmds.textField("' +
                mTx + '", e=True, tx=cmds.ls(sl=True)[0])')
    cmds.button(butG, e=True, c='cleanMixamo.makeCleanSkeleton("' +
                nTx + '", cmds.textField("' + nTx + '", q=True, tx=True))')
    cmds.button(
        butD, e=True, c='cleanMixamo.cleanUPcmd(["' + mTx + '", "' + nTx + '"])')
    # show window and size it
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[300, 180])
