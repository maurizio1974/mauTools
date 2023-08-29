from maya import cmds


def superCB():
    superCBOFF()
    cbf = cmds.layout('MainChannelsLayersLayout', q=True, ca=True)[0]
    # tools = cmds.formLayout(cbf, q=True, ca=True)
    key = cmds.symbolButton(
        p=cbf, w=19, i='executeDebug.png', ann='Set Keyframe to current selected Channels')
    rst = cmds.symbolButton(
        p=cbf, w=19, i='rebuild.png', ann='Reset selected Channels to default Value')
    lock = cmds.symbolButton(
        p=cbf, w=19, i='Lock_ON.png', ann='Lock Selected Attributes')
    unlock = cmds.symbolButton(
        p=cbf, w=19, i='Lock_OFF.png', ann='UnLock Selected Attributes')
    vis = cmds.symbolButton(
        p=cbf, w=19, i='eye.png', ann='Make Attribute Visible')
    unvis = cmds.symbolButton(
        p=cbf, w=19, i='hidden.png', ann='Make Attribute Hidden')
    up = cmds.symbolButton(
        p=cbf, w=19, i='UVTkNudgeUp.png', ann='Move Attribute up')
    dwn = cmds.symbolButton(
        p=cbf, w=19, i='UVTkNudgeDown.png', ann='Move Attribute down')
    top = cmds.symbolButton(
        p=cbf, w=19, i='alignVMax.png', ann='Move Attribute to the Top')
    bttm = cmds.symbolButton(
        p=cbf, w=19, i='alignVMin.png', ann='Move Attribute to the Bottom')
    conn = cmds.symbolButton(
        p=cbf, w=19, i='increaseDepth.png', ann='Connect Selected Attribute of Selected Transforms')
    conn2 = cmds.symbolButton(
        p=cbf, w=19, i='constrainDragX.png', ann='Connect the mesh attribute of a node to another')
    add = cmds.symbolButton(
        p=cbf, w=19, i='setEdAddCmd.png', ann='Add Attribute to te selected Transform')
    dele = cmds.symbolButton(
        p=cbf, w=19, i='delete.png', ann='Delete selected Attributes')
    cmds.formLayout(
        cbf, e=True,
        af=[
            (key, 'top', 0), (key, 'left', 0),
            (rst, 'top', 0),
            (lock, 'top', 0),
            (unlock, 'top', 0),
            (vis, 'top', 0),
            (unvis, 'top', 0),
            (up, 'top', 0),
            (dwn, 'top', 0),
            (top, 'top', 0),
            (bttm, 'top', 0),
            (conn, 'top', 0),
            (conn2, 'top', 0),
            (add, 'top', 0),
            (dele, 'top', 0)
        ],
        ac=[
            (rst, 'left', 1, key),
            (lock, 'left', 1, rst),
            (unlock, 'left', 1, lock),
            (vis, 'left', 1, unlock),
            (unvis, 'left', 1, vis),
            (up, 'left', 1, unvis),
            (dwn, 'left', 1, up),
            (top, 'left', 1, dwn),
            (bttm, 'left', 1, top),
            (conn, 'left', 1, bttm),
            (conn2, 'left', 1, conn),
            (add, 'left', 1, conn2),
            (dele, 'left', 1, add)
        ])
    # ADD COMMAND TO BUTTONS
    cmds.symbolButton(key, e=True, c='mSuperCB.setK()')
    cmds.symbolButton(rst, e=True, c='mSuperCB.resetA()')
    cmds.symbolButton(lock, e=True, c='mSuperCB.locK(True)')
    cmds.symbolButton(unlock, e=True, c='mSuperCB.locK(False)')

    cmds.symbolButton(up, e=True, c='mSuperCB.attrUp()')
    cmds.symbolButton(dwn, e=True, c='mSuperCB.attrDwn()')
    cmds.symbolButton(top, e=True, c='mSuperCB.attrTop()')
    cmds.symbolButton(bttm, e=True, c='mSuperCB.attrBttm()')


def setK():
    sel = cmds.ls(sl=True)
    attrs = cmds.channelBox('mainChannelBox', q=True, sma=True)
    if attrs:
        for s in sel:
            for a in attrs:
                cmds.setKeyframe(s + '.' + a)


def locK(dir):
    sel = cmds.ls(sl=True)
    attrs = cmds.channelBox('mainChannelBox', q=True, sma=True)
    if attrs:
        for s in sel:
            for a in attrs:
                cmds.setAttr(s + '.' + a, l=dir)


def resetA():
    sel = cmds.ls(sl=True)
    attrs = cmds.channelBox('mainChannelBox', q=True, sma=True)
    if attrs:
        for s in sel:
            for a in attrs:
                val = cmds.attributeQuery(a, n=s, listDefault=True)
                cmds.setAttr(s + '.' + a, val[0])


def attrUp():
    sel = cmds.ls(sl=True)
    for s in sel:
        origA = cmds.listAttr(s, ud=True)
        attrs = cmds.channelBox('mainChannelBox', q=True, sma=True)
        index = origA.index(attrs[0]) - 1
        if origA.index(attrs[0]) == 0:
            index = 0
        if index != 0:
            attrMover(attrs[0], [origA[index]])


def attrDwn():
    sel = cmds.ls(sl=True)
    for s in sel:
        origA = cmds.listAttr(s, ud=True)
        attrs = cmds.channelBox('mainChannelBox', q=True, sma=True)
        index = origA.index(attrs[0]) + 1
        if origA.index(attrs[0]) == len(origA) - 1:
            index = len(origA) - 1
        if index <= len(origA) - 1:
            attrMover(origA[index], [attrs[0]])


def attrTop():
    sel = cmds.ls(sl=True)
    for s in sel:
        origA = cmds.listAttr(s, ud=True)
        attrs = cmds.channelBox('mainChannelBox', q=True, sma=True)
        if attrs[0] != origA[0]:
            attrMover(origA[0], [attrs[0]])
            attrMover(attrs[0], [origA[0]])


def attrBttm():
    sel = cmds.ls(sl=True)
    for s in sel:
        origA = cmds.listAttr(s, ud=True)
        attrs = cmds.channelBox('mainChannelBox', q=True, sma=True)
        if attrs[0] != origA[-1]:
            attrMover(origA[-1], [attrs[0]])


def attrMover(top, move):
    Objs = cmds.ls(sl=True)
    for obj in Objs:
        Attrs = []
        origA = cmds.listAttr(obj, ud=True)
        for m in move:
            origA.remove(m)
        for orig in origA:
            Attrs.append(orig)
            if orig == top:
                for m in move:
                    Attrs.append(m)
        for attr in Attrs:
            if cmds.attributeQuery(attr, n=obj, ex=True):
                if cmds.getAttr(obj + '.' + attr, lock=True):
                    cmds.setAttr(obj + '.' + attr, lock=False)
                    try:
                        cmds.deleteAttr(obj, at=attr)
                    except Exception:
                        print('nothing to delete:')
                    cmds.undo()
                    cmds.setAttr(obj + '.' + attr, lock=True)
                else:
                    try:
                        cmds.deleteAttr(obj, at=attr)
                    except Exception:
                        print('nothing to delete:')
                    cmds.undo()


def superCBOFF():
    cbf = cmds.layout('MainChannelsLayersLayout', q=True, ca=True)[0]
    tools = cmds.formLayout(cbf, q=True, ca=True)
    for t in tools:
        if 'symbolButton' in t:
            cmds.deleteUI(t)
