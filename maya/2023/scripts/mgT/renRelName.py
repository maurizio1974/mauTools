import maya.cmds as cmds


def renRelN(dir, hirCB, hirCB2, hirEV, txFB, txRep1FD, txRep2FD):

    sel = cmds.ls(sl=1, l=1)
    text = txFB
    text1 = ''
    text2 = ''
    check = hirCB
    checkAll = hirEV
    check == hirCB
    text1 = txRep1FD
    text2 = txRep2FD
    check2 = hirCB2
    selNew = []
    newName = ''

    # THIS PART IS TO RESET THE UI
    if dir is 0:
        cmds.textField(txFB, e=1, tx='')
        cmds.textField(txRep1FD, e=1, tx='')
        cmds.textField(txRep2FD, e=1, tx='')
        cmds.checkBox(hirEV, e=1, v=1)
        if cmds.frameLayout(renumberFR, q=1, cl=1) == 1:
            cmds.checkBox(hirCB, e=1, v=0)
            cmds.checkBox(hirCB, e=1, l=' Selection Based')
            cmds.checkBox(hirCB2, e=1, v=0)
            cmds.checkBox(hirCB2, e=1, l=' Before')
            cmds.checkBox(hirCB, e=1, en=1)
            cmds.checkBox(hirCB2, e=1, en=1)
    else:
        if checkAll == 1:
            newSel = cmds.ls('*', typ='transform', l=1, dag=1, ap=1)
            if dir == 1:
                for eNew in newSel:
                    name = eNew.split('|')[-1]
                    if check2 is 0:
                        newName = text + name
                    else:
                        newName = name + text
                    cmds.rename(eNew, newName)
            if dir == 2:
                name2 = eNew2.split('|')[-1]
                if check2 is 0:
                    index = name2.find(text)
                    newName = name2[0:index] + name2[index + len(text):]
                else:
                    index = name2.rfind(text)
                    newName = name2[0:index] + name2[index + len(text):]
                    if index > -1:
                        cmds.rename(eNew2, newName)
                    else:
                        print(('Nothing to rename for ' + eNew2))
        else:
            if sel and dir is not 0:
                if check == 1:
                    sel = cmds.ls(sel, typ='transform', l=1, dag=1, ap=1)
                    sel.reverse()
                    selNew = sel
                else:
                    selNew = sel
                # THIS PART ADD FROM THE SELECTION
                if dir == 1:
                    for eNew in selNew:
                        name = eNew.split('|')[-1]
                        if check2 == 0:
                            newName = text + name
                        else:
                            newName = name + text
                        cmds.rename(eNew, newName)
                # THIS PART REMOVE FROM THE SELECTION
                if dir is 2:
                    for eNew2 in selNew:
                        name2 = eNew2.split('|')[-1]
                        if check2 == 0:
                            index = name2.find(text)
                            newName = name2[0:index] + \
                                name2[index + len(text):]
                        else:
                            index = name2.rfind(text)
                            newName = name2[0:index] + \
                                name2[index + len(text):]
                        if index > -1:
                            cmds.rename(eNew2, newName)
                        else:
                            print(('Nothing to rename for ' + eNew2))
                # THIS PART REPLACE FROM THE SELECTION
                if dir is 3:
                    for eNew3 in selNew:
                        name3 = eNew3.split('|')[-1]
                        if text2 != '':
                            newName = name3.replace(text1, text2)
                            cmds.rename(eNew3, newName)
                        else:
                            newName = name3.replace(text1, '')
                            cmds.rename(eNew3, newName)
            else:
                if len(sel) is 0:
                    print('>>> please select at leat one thing to rename. <<<')


def findSel(check, checkE, text, sel):

    if checkE is 0:
        selNew = cmds.ls((text + '*'), l=1)

    if len(sel) != 0 and checkE is 1:
        if check == 1:
            sel = cmds.ls(sel, typ='transform', l=1, dag=1, ap=1)
            sel.reverse()
            selNew = sel
        else:
            selNew = sel

    return selNew
