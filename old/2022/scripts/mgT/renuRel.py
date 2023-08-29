import maya.mel as mel
import maya.cmds as cmds
import string

def renuRel(int1,int2,text1):
    # num, sel = 0, cmds.ls(sl=True,type = 'transform', l=True)
    num, sel = 0, cmds.ls(sl=True, l=True)
    if not sel:
        print 'Please select the top node of what you are trying to renumber.'
        return
    if not text1:
        print 'Please input something in the text field.'
        return
    if len(sel) == 1:
        sel = cmds.ls( sel[0], l=1, typ = 'transform', dag=1, ap=1)
        sel.reverse()
        selNew = sel
    elif len(sel) > 1:
        sel.reverse()
        selNew = sel
    for i in range(len(selNew)):
        num = num + 1
    num = num + int1 - 1
    for i in range(len(selNew)):
        num = str(num)
        name = selNew[i].split('|')[-1]
        name = selNew[i].rstrip(name)
        cmds.rename(selNew[i], (text1+num.zfill(int2)))
        num = int(num)
        num = num -1
