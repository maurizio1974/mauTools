from maya import cmds


def prinOutput(cur, new):
    print('*' * len(cur + new + ' '))
    print('Renamed:\n\t' + cur)
    print('To:\n\t' + new)


def getCurrentSel(presets):
    new = ''
    out = selectionFilter(False, 'temp')
    if out:
        for s in out:
            cur = s.split('|')[-1]
            for p in presets:
                if p in cur:
                    index = len(p) - 1
                    new = cur[:-index]
            if not new:
                new = cur
    return new


def selectionFilter(mode, txt1):
    # sel = cmds.ls(sl=True, int=True)
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(
            t='error', m='Please select nodes to rename')
        return
    if not txt1:
        cmds.confirmDialog(
            t='error', m='Please add something in the text field')
        return
    out = sel
    if mode:
        out = []
        for s in sel:
            # full = cmds.ls(s, dag=True, type='transform', int=True)
            full = cmds.ls(s, dag=True, type='transform')
            for f in full:
                out.append(f)
        out.reverse()
    return out


def addRemoveString(mode, where, what, txt):
    cur, new = '', ''
    out = selectionFilter(mode, txt)
    if out:
        print('=' * 100)
        for s in out:
            cur = s.split('|')[-1]
            if not what:
                if not where:
                    new = cur + txt
                elif where:
                    new = txt + cur
            else:
                if not where:
                    if txt in cur:
                        index = len(txt)
                        new = cur[:-index]
                elif where:
                    new = cur.replace(txt, '', 1)
            if cur != new:
                prinOutput(cur, new)
                cmds.rename(s, new)
        print('=' * 100)


def replaceString(mode, where, txt1, txt2):
    cur, new = '', ''
    out = selectionFilter(mode, txt1)
    if out:
        print('=' * 100)
        for s in out:
            index = len(cur.split(txt1))
            if index > 1:
                if where == 1:
                    new = cur.replace(txt1, txt2, 1)
                elif where == 2:
                    new = txt2.join(cur.rsplit(txt1, 1))
                elif where == 3:
                    new = cur.replace(txt1, txt2)
                print(new)
                prinOutput(cur, new)
                cmds.rename(s, new)
        print('=' * 100)


def renumberString(mode, start, pad, txt):
    new = ''
    out = selectionFilter(mode, txt)
    if out:
        print('=' * 100)
        for x, s in enumerate(out):
            cur = s.split('|')[-1]
            inter = str(((len(out) - 1) - x) + start).zfill(pad)
            new = txt + inter
            if cur != new:
                prinOutput(cur, new)
                cmds.rename(s, new)
        print('=' * 100)


def makeOptionVars(cbs, cbb, arcb, arbtt, artc, rbgrf, rftc1, rftc2, nftc1, nfif1, nfif2, flar, flr, flrn):
    labels = {
        cbs: ['Hierarchy based', 'Selection based'],
        cbb: ['before', 'after'],
        arcb: ['Remove', 'Add']
    }
    # RADIOBUTTONGRP
    opv = {'renamer_mode': rbgrf}
    for o in list(opv.keys()):
        val = cmds.radioButtonGrp(opv[o], q=True, select=True)
        check = cmds.optionVar(ex=o)
        if check:
            val = cmds.optionVar(q=o)
        else:
            cmds.optionVar(iv=(o, val))
        cmds.radioButtonGrp(opv[o], e=True, select=val)
    # INTFIELDS
    opv = {
        'renamer_start': nfif1, 'renamer_padding': nfif2
    }
    for o in list(opv.keys()):
        val = cmds.intField(opv[o], q=True, v=True)
        check = cmds.optionVar(ex=o)
        if check:
            val = cmds.optionVar(q=o)
        else:
            cmds.optionVar(iv=(o, val))
        cmds.intField(opv[o], e=True, v=val)
    # CHECKBOXES
    opv = {
        'renamer_selectionBase': cbs, 'renamer_after': cbb,
        'renamer_add': arcb
    }
    for o in list(opv.keys()):
        val = cmds.checkBox(opv[o], q=True, v=True)
        check = cmds.optionVar(ex=o)
        if check:
            val = cmds.optionVar(q=o)
        else:
            cmds.optionVar(iv=(o, val))
        cmds.checkBox(opv[o], e=True, v=val)
        # checkBox labels
        if val:
            if opv[o] == arcb:
                cmds.button(arbtt, e=True, label=labels[opv[o]][0])
            else:
                cmds.checkBox(opv[o], e=True, label=labels[opv[o]][0])
        else:
            if opv[o] == arcb:
                cmds.button(arbtt, e=True, label=labels[opv[o]][1])
            else:
                cmds.checkBox(opv[o], e=True, label=labels[opv[o]][1])
    # TEXTFIELDS
    opv = {
        'renamer_add_Remove': artc, 'renamer_replace1': rftc1,
        'renamer_replace2': rftc2, 'renamer_>>>': nftc1
    }
    for o in list(opv.keys()):
        val = cmds.textField(opv[o], q=True, tx=True)
        check = cmds.optionVar(ex=o)
        if check:
            val = cmds.optionVar(q=o)
        else:
            cmds.optionVar(sv=(o, val))
        cmds.textField(opv[o], e=True, tx=val)
    # FRAMELAYOUTS
    opv = {
        'renamer_add_Remove_layout': flar, 'renamer_replace_layout': flr, 'renamer_renumber_layout': flrn
    }
    for o in list(opv.keys()):
        val = cmds.frameLayout(opv[o], q=True, cl=True)
        check = cmds.optionVar(ex=o)
        if check:
            val = cmds.optionVar(q=o)
        else:
            cmds.optionVar(iv=(o, val))
        cmds.frameLayout(opv[o], e=True, cl=val)


def storeOptionVars(cbs, cbb, arcb, arbtt, artc, rbgrf, rftc1, rftc2, nftc1, nfif1, nfif2, flar, flr, flrn):
    # radioButtonGrp
    opv = {'renamer_mode': rbgrf}
    for o in list(opv.keys()):
        val = cmds.radioButtonGrp(opv[o], q=True, select=True)
        check = cmds.optionVar(ex=o)
        if check:
            cmds.optionVar(iv=(o, val))
            cmds.radioButtonGrp(opv[o], e=True, select=val)
    # intField
    opv = {
        'renamer_start': nfif1, 'renamer_padding': nfif2
    }
    for o in list(opv.keys()):
        val = cmds.intField(opv[o], q=True, v=True)
        check = cmds.optionVar(ex=o)
        if check:
            cmds.optionVar(iv=(o, val))
            cmds.intField(opv[o], e=True, v=val)
    # checkBox
    opv = {
        'renamer_selectionBase': cbs, 'renamer_after': cbb,
        'renamer_add': arcb
    }
    for o in list(opv.keys()):
        val = cmds.checkBox(opv[o], q=True, v=True)
        check = cmds.optionVar(ex=o)
        if check:
            cmds.optionVar(iv=(o, val))
            cmds.checkBox(opv[o], e=True, v=val)
    # textField
    opv = {
        'renamer_add_Remove': artc, 'renamer_replace1': rftc1,
        'renamer_replace2': rftc2, 'renamer_>>>': nftc1
    }
    for o in list(opv.keys()):
        val = cmds.textField(opv[o], q=True, tx=True)
        check = cmds.optionVar(ex=o)
        if check:
            cmds.optionVar(sv=(o, val))
            cmds.textField(opv[o], e=True, tx=val)
    # frameLayout
    opv = {
        'renamer_add_Remove_layout': flar, 'renamer_replace_layout': flr, 'renamer_renumber_layout': flrn
    }
    for o in list(opv.keys()):
        val = cmds.frameLayout(opv[o], q=True, cl=True)
        check = cmds.optionVar(ex=o)
        if check:
            cmds.optionVar(iv=(o, val))
            cmds.frameLayout(opv[o], e=True, cl=val)


def mauRenamer_UI():
    presets = [
        "L_", "R_", "_grp", "_jnt", "_null", "_loc", "_riv", "_fol",
        "_clh", "_cls", "_crv", "_mesh", "_geo", '_surf']
    win = 'outpostRenamerWin'
    if cmds.window(win, ex=True):
        cmds.deleteUI(win)
    cmds.window(win, t='OutpostVFX Renamer', rtf=True)

    fr = cmds.formLayout(p=win)
    cbs = cmds.checkBox(label='Selection based', p=fr)
    cbb = cmds.checkBox(label='after', p=fr)
    flar = cmds.frameLayout(
        label="Add/ Remove", cll=True, cl=True, p=fr,
        ec='cmds.window("' + win + '", e=True, h=cmds.window("' +
        win + '", q=True, h=True) + 18 )',
        cc='cmds.window("' + win + '", e=True, h=cmds.window("' + win + '", q=True, h=True) - 18 )')
    flr = cmds.frameLayout(
        label="Replace", cll=True, cl=True, p=fr,
        ec='cmds.window("' + win + '", e=True, h=cmds.window("' +
        win + '", q=True, h=True) + 20 )',
        cc='cmds.window("' + win + '", e=True, h=cmds.window("' + win + '", q=True, h=True) - 20 )')
    flrn = cmds.frameLayout(
        label="Renumber", cll=True, cl=True, p=fr,
        ec='cmds.window("' + win + '", e=True, h=cmds.window("' +
        win + '", q=True, h=True) + 20 )',
        cc='cmds.window("' + win + '", e=True, h=cmds.window("' + win + '", q=True, h=True) - 20 )')

    cmds.formLayout(
        fr, e=True,
        af=[
            (cbs, 'left', 50), (cbs, 'top', 5),
            (cbb, 'top', 5),
            (flar, 'left', 5), (flar, 'right', 5),
            (flr, 'left', 5), (flr, 'right', 5),
            (flrn, 'left', 5), (flrn, 'right', 5)
        ],
        ac=[
            (cbb, 'left', 30, cbs),
            (flar, 'top', 5, cbs),
            (flr, 'top', 5, flar),
            (flrn, 'top', 5, flr)
        ]
    )
    # ADD COMMANDS
    cmds.checkBox(
        cbs, e=True,
        onc='cmds.checkBox("' + cbs + '", e=True, label="Hierarchy based")',
        ofc='cmds.checkBox("' + cbs + '", e=True, label="Selection based")')
    cmds.checkBox(
        cbb, e=True,
        onc='cmds.checkBox("' + cbb + '", e=True, label="before")',
        ofc='cmds.checkBox("' + cbb + '", e=True, label="after")')

    flarf = cmds.formLayout(p=flar)
    artc = cmds.textField()
    arcb = cmds.checkBox(label='')
    arbtt = cmds.button(label='Add')

    cmds.formLayout(
        flarf, e=True,
        af=[
            (artc, 'left', 5), (artc, 'top', 5), (artc, 'right', 5),
            (arcb, 'left', 5),
            (arbtt, 'right', 5)
        ],
        ap=[(arcb, 'right', 5, 10)],
        ac=[
            (arcb, 'top', 5, artc),
            (arbtt, 'left', 5, arcb), (arbtt, 'top', 5, artc)
        ]
    )
    # ADD COMMANDS FOR ADD/REMOVE TAB
    cmds.checkBox(
        arcb, e=True,
        onc='cmds.button("' + arbtt + '", e=True, label="Remove")',
        ofc='cmds.button("' + arbtt + '", e=True, label="Add")')
    cmds.button(
        arbtt, e=True,
        c='mauRenamer.addRemoveString(\
        cmds.checkBox("' + cbs + '", q=True, v=True),\
        cmds.checkBox("' + cbb + '", q=True, v=True),\
        cmds.checkBox("' + arcb + '", q=True, v=True),\
        cmds.textField("' + artc + '", q=True, tx=True))')

    flrf = cmds.formLayout(p=flr)
    rbgrf = cmds.radioButtonGrp(
        nrb=3, label='Mode', labelArray3=['First', 'Last', 'All'],
        cat=[1, 'left', 5], cw4=[60, 50, 50, 50], select=1, p=flrf)
    rftc1 = cmds.textField(p=flrf)
    rftc2 = cmds.textField(p=flrf)
    rfbtt = cmds.button(label='Replace', p=flrf)

    cmds.formLayout(
        flrf, e=True,
        af=[
            (rbgrf, 'left', 5), (rbgrf, 'top', 5), (rbgrf, 'right', 5),
            (rftc1, 'left', 5), (rftc1, 'right', 5),
            (rftc2, 'left', 5), (rftc2, 'right', 5),
            (rfbtt, 'left', 5), (rfbtt, 'right', 5)
        ],
        ac=[
            (rftc1, 'top', 5, rbgrf),
            (rftc2, 'top', 5, rftc1),
            (rfbtt, 'top', 5, rftc2)
        ]
    )
    # ADD COMMANDS FOR REPLACE TAB
    cmds.button(
        rfbtt, e=True,
        c='mauRenamer.replaceString(\
        cmds.checkBox("' + cbs + '", q=True, v=True),\
        cmds.radioButtonGrp("' + rbgrf + '", q=True, select=True),\
        cmds.textField("' + rftc1 + '", q=True, tx=True),\
        cmds.textField("' + rftc2 + '", q=True, tx=True))')

    flrnf = cmds.formLayout(p=flrn)
    nfbtt1 = cmds.button(label='>>>', p=flrnf)
    nftc1 = cmds.textField(p=flrnf)
    nftx1 = cmds.text(label='Start#', p=flrnf)
    nfif1 = cmds.intField(p=flrnf, w=50, v=1)
    nftx2 = cmds.text(label='Padding#', p=flrnf, al='left')
    nfif2 = cmds.intField(p=flrnf, w=50, v=2)
    nfbtt2 = cmds.button(label='Renumber', p=flrnf)

    cmds.formLayout(
        flrnf, e=True,
        af=[
            (nfbtt1, 'left', 5), (nfbtt1, 'top', 5),
            (nftc1, 'top', 5), (nftc1, 'right', 5),
            (nftx1, 'left', 5),
            (nfbtt2, 'left', 5), (nfbtt2, 'right', 5),
        ],
        ap=[
            (nfbtt1, 'right', 5, 20),
            (nftx1, 'right', 5, 20),
        ],
        ac=[
            (nftc1, 'left', 5, nfbtt1),
            (nftx1, 'top', 10, nftc1),
            (nfif1, 'left', 5, nftx1), (nfif1, 'top', 10, nftc1),
            (nftx2, 'left', 5, nfif1), (nftx2, 'top', 10, nftc1),
            (nfif2, 'left', 5, nftx2), (nfif2, 'top', 10, nftc1),
            (nfbtt2, 'top', 10, nftx1)
        ]
    )
    # ADD COMMANDS FOR RENUMBER TAB
    cmds.button(
        nfbtt1, e=True,
        c='cmds.textField("' + nftc1 + '", e=True, tx=mauRenamer.getCurrentSel(["' + ('", "').join(presets) + '"]))')
    cmds.button(
        nfbtt2, e=True,
        c='mauRenamer.renumberString(\
        cmds.checkBox("' + cbs + '", q=True, v=True),\
        cmds.intField("' + nfif1 + '", q=True, v=True),\
        cmds.intField("' + nfif2 + '", q=True, v=True),\
        cmds.textField("' + nftc1 + '", q=True, tx=True))')

    # ADD PRESETS FOR ALL TEXT FIELDS
    for ui in [artc, rftc1, rftc2, nftc1]:
        pm = cmds.popupMenu(p=ui)
        cmds.menuItem(
            label=' --- CLEAR --- ', p=pm, c='cmds.textField("' + ui + '", e=True, tx="")')
        if ui != nftc1:
            for p in sorted(presets):
                cmds.menuItem(
                    label=p, p=pm, c='cmds.textField("' + ui + '", e=True, tx="' + p + '")')
    # ADD PRESETS FOR ALL INT FIELDS
    for ui in [nfif1, nfif2]:
        pm = cmds.popupMenu(p=ui)
        for x in range(0, 10):
            cmds.menuItem(
                label=str(x), p=pm, c='cmds.intField("' + ui + '", e=True, v=' + str(x) + ')')
    # SHOW WINDOW
    cmds.window(
        win, e=True,
        cc='mauRenamer.storeOptionVars("' + cbs + '", "' + cbb + '", "' + arcb + '", "' + arbtt + '", "' + artc + '", "' + rbgrf + '", "' + rftc1 + '", "' + rftc2 + '", "' + nftc1 + '", "' + nfif1 + '", "' + nfif2 + '", "' + flar + '", "' + flr + '", "' + flrn + '")')
    cmds.showWindow(win)
    cmds.window(win, e=True, w=260, h=120)
    # MAKE OPTIONVARS
    makeOptionVars(
        cbs, cbb, arcb, arbtt, artc, rbgrf, rftc1, rftc2, nftc1, nfif1, nfif2, flar, flr, flrn)
