'''----------------------------------------------------------------------------

    MINIMO ATTRIBUTE LOCKER

    Date = 14-05-2014
    User = Maurizio Giglioli
    info = Sets the preferences for the locking of a
        trnasform and applyes the settings set to a hierarchy
    usage = run mlockAttr_UI that opens the UI, select the
        nodes and set the preference you want based on the
        UI selection after that run the lock button and check
        if you want the attribute visibles or not
    Update = (19-12-2019)
             Added extra buttons to turn off attrbs together, added the possibility to recreate
             the tags from current locked nodes
             (30-07-2014)
             Added Remove Lock preference button and procedure
             (14-05-2014)
             First Release

----------------------------------------------------------------------------'''
import maya.mel as mel
import maya.cmds as cmds


def mlockAttr_UI():
    if cmds.window('mLockAttr_WIN', ex=1) == 1:
        cmds.deleteUI('mLockAttr_WIN', window=True)

    win = cmds.window('mLockAttr_WIN', t='mLocker')

    fr = cmds.formLayout()
    btr = cmds.button(l='On', w=40, h=18)
    cbT = cmds.checkBoxGrp(ct4=['left', 'left', 'left', 'left'], cw4=[30, 40, 40, 40], v1=1, v2=1, v3=1, ncb=3, l='Tra ', la3=['X', 'Y', 'Z'])
    brt = cmds.button(l='On', w=40, h=18)
    cbR = cmds.checkBoxGrp(ct4=['left', 'left', 'left', 'left'], cw4=[30, 40, 40, 40], v1=1, v2=1, v3=1, ncb=3, l='Rot ', la3=['X', 'Y', 'Z'])
    bsc = cmds.button(l='On', w=40, h=18)
    cbZ = cmds.checkBoxGrp(ct4=['left', 'left', 'left', 'left'], cw4=[30, 40, 40, 40], v1=1, v2=1, v3=1, ncb=3, l='Sca ', la3=['X', 'Y', 'Z'])
    bv = cmds.button(l='Off', w=40, h=18)
    cbV = cmds.checkBoxGrp(ct2=['left', 'left'], cw2=[30, 40], l='Vis ', v1=0)
    b = cmds.button(
        l='Set lock Pref',
        c='mLockAttr.mSetLockAttr('
        '[cmds.checkBoxGrp("' + cbT + '",q = 1, v1 = 1),'
        'cmds.checkBoxGrp("' + cbT + '",q = 1, v2 = 1),'
        'cmds.checkBoxGrp("' + cbT + '",q = 1, v3 = 1)],'
        '[cmds.checkBoxGrp("' + cbR + '",q = 1, v1 = 1),'
        'cmds.checkBoxGrp("' + cbR + '",q = 1, v2 = 1),'
        'cmds.checkBoxGrp("' + cbR + '",q = 1, v3 = 1)],'
        '[cmds.checkBoxGrp("' + cbZ + '",q = 1, v1 = 1),'
        'cmds.checkBoxGrp("' + cbZ + '",q = 1, v2 = 1),'
        'cmds.checkBoxGrp("' + cbZ + '",q = 1, v3 = 1)],'
        '[cmds.checkBoxGrp("' + cbV + '",q = 1, v1 = 1)])'
        )
    br = cmds.button(l='Remove lock Prefs', c='mLockAttr.mUnSetLockAttr()')
    bg = cmds.button(l='Create from current selection', c='mLockAttr.mBuildLocking()')
    s = cmds.separator()
    cmds.button(
        btr, e=True, 
        c='mLockAttr.uiSwitch("' + btr + '", "' + cbT + '", "multi")')
    cmds.button(
        brt, e=True, 
        c='mLockAttr.uiSwitch("' + brt + '", "' + cbR + '", "multi")')
    cmds.button(
        bsc, e=True, 
        c='mLockAttr.uiSwitch("' + bsc + '", "' + cbZ + '", "multi")')
    cmds.button(
        bv, e=True, 
        c='mLockAttr.uiSwitch("' + bv + '", "' + cbV + '", "single")')
    cbH = cmds.checkBox(
        'visilock', l='Visible',
        onc='cmds.checkBox("visilock", e=True, l="hidden")',
        ofc='cmds.checkBox("visilock", e=True, l="Visible")')
    bl = cmds.button(
        l='lock',
        c='mLockAttr.mDoLockAttr(cmds.checkBox("' + cbH + '",q = 1, v = 1),"on")', w=50)
    bu = cmds.button(
        l='unlock',
        c='mLockAttr.mDoLockAttr(cmds.checkBox("' + cbH + '",q = 1, v = 1),"off")', w=50)
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (btr, 'left', 5), (btr, 'top', 10),
            (cbT, 'top', 10),
            (brt, 'left', 5),
            (bsc, 'left', 5),
            (bv, 'left', 5),
            (b, 'left', 5), (b, 'right', 0),
            (br, 'left', 5), (br, 'right', 0),
            (bg, 'left', 5), (bg, 'right', 0),
            (s, 'left', 5), (s, 'right', 0),
            (cbH, 'left', 10),
            (bl, 'left', 10),
            (bu, 'left', 10)],
        ac=[
            (cbT, 'left', 0, btr),
            (brt, 'top', 0, btr),
            (cbR, 'left', 0, brt), (cbR, 'top', 0, cbT),
            (bsc, 'top', 0, brt),
            (cbZ, 'left', 0, bsc), (cbZ, 'top', 0, cbR),
            (bv, 'top', 0, bsc),
            (cbV, 'left', 0, bv), (cbV, 'top', 0, cbZ),
            (b, 'top', 10, cbV),
            (br, 'top', 5, b),
            (bg, 'top', 5, br),
            (s, 'top', 10, bg),
            (cbH, 'top', 10, s),
            (bl, 'left', 10, cbH),
            (bl, 'top', 10, s),
            (bu, 'left', 5, bl),
            (bu, 'top', 10, s)
            ]
        )

    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[200, 225])

def uiSwitch(ui, cb, mode):
    if cmds.button(ui, q=True, l=True) == "Off":
        cmds.button(ui, e=True, l="On")
        cmds.checkBoxGrp(cb, e=True, v1=True)
        if mode == 'multi':
            cmds.checkBoxGrp(cb, e=True, v2=True)
            cmds.checkBoxGrp(cb, e=True, v3=True)
    else:
        cmds.button(ui, e=True, l="Off")
        cmds.checkBoxGrp(cb, e=True, v1=False)
        if mode == 'multi':
            cmds.checkBoxGrp(cb, e=True, v2=False)
            cmds.checkBoxGrp(cb, e=True, v3=False)


def mSetLockAttr(cbT, cbR, cbZ, cbV):
    sel = cmds.ls(sl=True, tr=True)
    if not len(sel) > 0:
        cmds.confirmDialog(t='Not Kick Ass', m='Nothing Selected !"')
        return
    if cbT[0]: cbT[0] = 'tx'
    if cbT[1]: cbT[1] = 'ty'
    if cbT[2]: cbT[2] = 'tz'

    if cbR[0]: cbR[0] = 'rx'
    if cbR[1]: cbR[1] = 'ry'
    if cbR[2]: cbR[2] = 'rz'

    if cbZ[0]: cbZ[0] = 'sx'
    if cbZ[1]: cbZ[1] = 'sy'
    if cbZ[2]: cbZ[2] = 'sz'

    if cbV[0]: cbV[0] = 'v'

    value = [
        cbT[0], cbT[1], cbT[2],
        cbR[0], cbR[1], cbR[2],
        cbZ[0], cbZ[1], cbZ[2],
        cbV[0]
        ]
    out = ''
    for v in value:  # Create the attribute string
        if v:
            out = out+' '+v

    for s in sel:
        if cmds.attributeQuery('mLocker', node=s, ex=1) == 0:
            cmds.addAttr(s, ln='mLocker', dt='string')
            cmds.setAttr(
                s+'.mLocker',
                out.replace('[', '').replace(']', ''),
                type='string',
                l=1
                )
        else:
            cmds.setAttr(s+'.mLocker', l=0)
            cmds.setAttr(
                s+'.mLocker',
                out.replace('[', '').replace(']', ''),
                type='string'
                )
            cmds.setAttr(s+'.mLocker', l=1)


def mUnSetLockAttr():
    sel = cmds.ls(sl=True, tr=True)
    for s in sel:
        if not len(sel) > 0:
            cmds.confirmDialog(t='Not Kick Ass', m='Nothing Selected !"')
            return
        if cmds.attributeQuery('mLocker', node=s, ex=1) == 1:
            cmds.setAttr(s+'.mLocker', l=0)
            cmds.deleteAttr(s, at='mLocker')


def mDoLockAttr(state, switch):
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    sel = cmds.ls(sl=True, dag=True, tr=True)
    if not sel:
        cmds.confirmDialog(t='Not Kick Ass', m='Nothing Selected !"')
        return
    cmds.progressBar(gMainProgressBar, e=True, bp=True, ii=True, st='Nodes left to do', max=len(sel))
    msg, attrs = 'locked', ''
    for s in sel:
        if cmds.progressBar(gMainProgressBar, q=True, ic=True):
            break
        if cmds.attributeQuery('mLocker', node=s, ex=1) == 1:
            attrs = cmds.getAttr(s+'.mLocker')
            if switch == 'on':
                for a in attrs.split(' '):
                    if len(a) >= 1:
                        cmds.setAttr(s+'.'+a, l=True)
                        if state == 1:
                            cmds.setAttr(s+'.'+a, k=False)
            elif switch == 'off':
                msg = 'unLocked'
                for a in attrs.split(' '):
                    if len(a) >= 1:
                        cmds.setAttr(s+'.'+a, l=False)
                        cmds.setAttr(s+'.'+a, k=True)
        cmds.progressBar(gMainProgressBar, e=True, s=1)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)
    print('Structure ' + msg)


def mBuildLocking():
    node = cmds.ls(sl=True)
    if not node:
        cmds.confirmDialog(
                t='Not Kick Ass',
                m='Please select the top node of the hierarchy you want to copy locking information from')
        return
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    sel = cmds.ls(node, dag=True, type='transform')
    cmds.progressBar(gMainProgressBar, e=True, bp=True, ii=True, st='Nodes left to do', max=len(sel))
    attrs = ['t', 'r', 's', 'v']
    axes = ['x', 'y', 'z']
    cmd = 'import mLockAttr\n'
    for x, s in enumerate(sel):
        if cmds.progressBar(gMainProgressBar, q=True, ic=True):
            break
        cmd += 'cmds.select(\'' + s + '\', r=True)\n'
        cmd += 'mLockAttr.mSetLockAttr('
        for a in attrs:
            info = []
            if a != 'v':
                for ax in axes:
                    state = cmds.getAttr(s + '.' + a + ax, l=True)
                    info.append(state)
            else:
                state = cmds.getAttr(s + '.' + a, l=True)
                info = [state]
            if a == 'v':
                cmd += str(info)
            else:
                cmd += str(info) + ', '
        cmd += ')\n'
        exec(cmd)
        cmds.progressBar(gMainProgressBar, e=True, s=1)
    cmds.progressBar(gMainProgressBar, e=True, ep=True)
    print('Locking Structure tagged')
