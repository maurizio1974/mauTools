import maya.cmds as cmds
import operator


def mSetManager_UI():
    if cmds.window('mSetsWin', q=True, ex=True):
        cmds.deleteUI('mSetsWin')
    win = cmds.window('mSetsWin', t='Mimmo Set Manager', s=True)
    fra = cmds.formLayout(p=win)
    banner = cmds.symbolButton(i='sets_banner.png', p=fra)
    tf = cmds.textField(tx='Set', p=fra)
    tsl = cmds.textScrollList(h=300, w=50, ams=True, p=fra)
    tsls = cmds.textScrollList(h=300, w=50, ams=True, p=fra)
    btl = cmds.button(l='load')
    bts = cmds.button(l='save')
    # ORGANIZE UI
    cmds.formLayout(
        fra,
        e=True,
        af=[
            (banner, 'top', 5), (banner, 'left', 10),
            (tf, 'left', 10), (tf, 'right', 10),
            (tsl, 'left', 10), (tsl, 'right', 10),
            (tsls, 'left', 10), (tsls, 'right', 10), (tsls, 'bottom', 40),
            (btl, 'left', 10),
            (bts, 'right', 10)
        ],
        ap=[
            (btl, 'right', 10, 50)
        ],
        ac=[
            (tf, 'top', 5, banner),
            (tsl, 'top', 10, tf),
            (tsls, 'top', 10, tsl),
            (btl, 'top', 5, tsls),
            (bts, 'top', 5, tsls), (bts, 'left', 5, btl)
        ]
    )
    # POPULATE UI AND ADD COMMANDS
    tSel = 'cmds.textScrollList("' + tsl + '", q=True, si=True)[0]'
    tSels = 'cmds.textScrollList("' + tsl + '", q=True, si=True)'
    tSelsra = 'cmds.textScrollList("' + tsls + '", e=True, ra=True)'
    sc = 'cmds.textField("' + tf + '", e=True, tx=' + tSel + ');ms.mTslsPopulate("' + tsls + '", "' + tsl + '")'
    scs = 'cmds.select(cmds.textScrollList("' + tsls + '", q=True, si=True), r=True)'
    dcc = 'cmds.select(cmds.textScrollList("' + tsl + '", q=True, si=True))'
    dkc = 'cmds.delete(cmds.textScrollList("' + tsl + '", q=True, si=True))'
    cmdC = 'ms.mSetCreate(cmds.textField("' + tf + '", q=True, tx=True))'
    cmdRe = 'ms.mSetRename(' + tSel + ');ms.mTslPopulate("' + tsl + '", "' + tsls + '")'
    cmdD = 'ms.mSetCopy(' + tSel + ')'
    cmdA = 'ms.mSetAdd(' + tSel + ')'
    cmdR = 'ms.mSetRem(' + tSel + ')'
    cmdU = 'ms.mSetUn(' + tSels + ')'
    cmdS = 'ms.mSetSub(' + tSels + ')'
    cmdI = 'ms.mSetIntr(' + tSels + ')'
    cmdIN = 'ms.mSetInv(' + tSel + ')'
    cmdRF = 'ms.mTslPopulate("' + tsl + '", "' + tsls + '")'
    cmds.symbolButton(
        banner,
        e=True,
        c='ms.mTslPopulate("' + tsl + '", "' + tsls + '")'
    )
    cmds.textScrollList(tsl, e=True, sc=sc, dcc=dcc, dkc=dkc)
    cmds.textScrollList(tsls, e=True, sc=scs)
    cmds.button(btl, e=True, c='ms.mLoadSet("' + tsl + '")')
    cmds.button(
        bts,
        e=True,
        c='ms.mSaveSet(cmds.textScrollList("' + tsl + '", q=True, si=True))'
    )
    mTslPopulate(tsl, tsls)
    # POPUPS FIRST TSL
    pp = {
        'A, Create, Set': cmdC,
        'B, Delete, Set': dkc,
        'C, Rename, Set': cmdRe,
        'D, ------ Sel,------': '',
        'E, Add, Selection': cmdA,
        'F, Remove, Selection': cmdR,
        'G, ------ Sets,------': '',
        'H, Duplicate, Set': cmdD,
        'I, Subtract, Set': cmdS,
        'L, Unite, Sets': cmdU,
        'M, Intersect, Sets': cmdI,
        'N, Invert, Sets': cmdIN,
        'O, ------ UI,------': '',
        'P, Refresh, UI': cmdRF
    }
    x = sorted(pp.items(), key=operator.itemgetter(0))
    pps = cmds.popupMenu('tslPP', p=tsl)
    for i in range(0, len(x)):
        label = x[i][0].split(',')[1] + ' ' + x[i][0].split(',')[2]
        cmds.menuItem(
            l=label,
            p=pps,
            c=x[i][1] + ';ms.mTslPopulate("' + tsl + '", "' + tsls + '")'
        )
    # POPUPS SECOND TSL
    ppp = {'A, Clear, Set': tSelsra}
    x = sorted(ppp.items(), key=operator.itemgetter(0))
    ppss = cmds.popupMenu('tslsPP', p=tsls)
    for i in range(0, len(x)):
        label = x[i][0].split(',')[1] + ' ' + x[i][0].split(',')[2]
        cmds.menuItem(l=label, p=ppss, c=x[i][1])
    # SHOW UI
    cmds.showWindow(win)
    cmds.window(win, e=True, w=50)
    # MAKE WINDOW DOCKABLE
    # dcName = ("mSetManager_DC")
    # if cmds.dockControl(dcName, q=True, ex=True) == 1:
    #     cmds.deleteUI(dcName)
    # cmds.dockControl(
    #     dcName,
    #     allowedArea="all",
    #     area="left",
    #     floating=1,
    #     content=win,
    #     label="Mimmo Sets Manager"
    # )


def mBrowser(mode):
    ws = cmds.workspace(q=True, act=True)
    out = ''
    filter = "*"
    r = cmds.fileDialog2(
        ff=filter,
        cap='Set Destination',
        dir=ws + "/",
        fm=mode,
        ds=True
    )
    if r:
        out = r[0]
    return out


def mTslPopulate(tsl, tsls):
    sets = cmds.ls(type='objectSet')
    cmds.textScrollList(tsl, e=True, ra=True)
    cmds.textScrollList(tsls, e=True, ra=True)
    for s in sets:
        if cmds.attributeQuery('mSet', n=s, ex=True):
            cmds.textScrollList(tsl, e=True, a=s)


def mTslsPopulate(tsls, tsl):
    ts = cmds.textScrollList(tsl, q=True, si=True)
    sel = cmds.sets(ts, q=True)
    cmds.textScrollList(tsls, e=True, ra=True)
    for s in sel:
        cmds.textScrollList(tsls, e=True, a=s)


def mSetRename(name):
    result = cmds.promptDialog(
        t='Rename Set',
        tx=name,
        m='Enter Name:',
        b=['OK', 'Cancel'],
        db='OK',
        cb='Cancel',
        ds='Cancel')

    if result == 'OK':
        text = cmds.promptDialog(q=True, tx=True)

    cmds.rename(name, text)


def mSetCreate(name):
    sel = cmds.ls(sl=True)
    iters = len(cmds.ls(name + '*'))
    if iters != 0:
        name = name + str(iters)
    if sel:
        cmds.sets(n=name)
    else:
        cmds.sets(n=name, em=True)
    cmds.addAttr(name, ln='mSet', dt='string')
    return name


def mSetAdd(set):
    sel = cmds.ls(sl=True, fl=True)
    for s in sel:
        cmds.sets(s, add=set)


def mSetRem(set):
    sel = cmds.ls(sl=True, fl=True)
    for s in sel:
        cmds.sets(s, rm=set)


def mSetUn(set):
    cmds.select(cl=True)
    name = ''
    for s in set:
        cmds.select(s, add=True)
        if s != set[-1]:
            name += s + '_'
        else:
            name += s
    mSetCreate(name)
    cmds.select(cl=True)


def mSetCopy(set):
    cmds.select(set)
    mSetCreate(set + '_copy')
    cmds.select(cl=True)


def mSetSub(set):
    cmds.select(set[0])
    name = mSetCreate(set[0] + '_' + set[1] + '_sub')
    cmds.select(set[1])
    mSetRem(name)
    cmds.select(cl=True)


def mSetIntr(set):
    cmds.select(cl=True)
    name, intr = '', []
    i = 0
    for s in set:
        if len(set) - 1 != i:
            part = cmds.sets(s, int=set[i + 1])
            if part:
                for p in part:
                    intr.append(p)
            i = i + 1
        if s != set[-1]:
            name += s + '_'
        else:
            name += s + '_intr'
    cmds.select(cl=True)
    cmds.select(intr)
    mSetCreate(name)
    cmds.select(cl=True)


def mSetInv(set):
    cmds.select(cl=True)
    cmds.select(set)
    cmds.InvertSelection()
    mSetCreate(set + '_inv')


def mLoadSet(tsl):
    path = mBrowser(1)
    with open(path, 'r') as f:
        data = f.read()
    f.close()
    for x in range(1, len(data.split('\n')), 2):
        sel = data.split('\n')[x - 1]
        name = data.split('\n')[x]
        if len(sel.split(',')) > 1:
            cmds.select(cl=True)
            for sss in sel.split(','):
                cmds.select(sss, add=True)
        else:
            cmds.select(sel, r=True)
        mSetCreate(name)
        mTslPopulate(tsl)
    cmds.select(cl=True)


def mSaveSet(set):
    path = mBrowser(0)
    open(path, 'w')
    if set:
        for s in set:
            sel = cmds.sets(s, q=True)
            cs = ''
            for ss in sel:
                if len(ss.split('.')) > 1:
                    if ss != sel[-1]:
                        cs += ss + ', '
                    else:
                        cs += ss + '\n'
                else:
                    if ss != sel[-1]:
                        cs += '' + ss + ' '
                    else:
                        cs += '' + ss + '\n'
            with open(path, 'a') as f:
                f.write(cs)
                f.write('' + s + '\n')
            f.close()
