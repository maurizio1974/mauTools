import os
import maya.mel as mel
import maya.cmds as cmds


def readChannelsData(node, channels, frameRange):
    channelsValue = {x:[] for x in channels}
    for i in range(frameRange[0], frameRange[1]+1):
        cmds.currentTime(i)
        for ch in channels:
            value = cmds.getAttr(node + '.' + ch)
            if ch in ['tx','ty','tz']:
                value = value
            channelsValue[ch].append(value)
    return channelsValue

def exporter(data, frameRange):
    units = {
        'game': 15, 'film': 24,
        'pal': 25, 'ntsc': 30,
        'show': 48, 'palf': 50,
        'ntscf': 60}
    fps = units[cmds.currentUnit(q=1, t=1)]
    # fps = mel.eval('float $fps = `currentTimeUnitToFPS`')
    startFrame = frameRange[0]-1
    length = frameRange[1]-frameRange[0] + 1
    count = len(data)
    text = '''\
{
   rate = %s
   start = %s
   tracklength = %s
   tracks = %s
''' % (fps, startFrame, length, count)
    for ch, values in list(data.items()):
        chanText = '''\
    {
        name = %s
        data = %s
    }\n''' % (ch.replace('.',':'), ' '.join([str(x) for x in values]))
        text += chanText
    text += '}'
    return text

def export(node, channels, outFile, frange):
    dataChannels = readChannelsData(node, channels, frange)
    text = exporter(dataChannels, frange)
    with open(outFile,'w') as f:
        f.write(text)

def setTransform(tsl):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(t='Selection Error', m='Please select te transforms to export')
        return
    cmds.textScrollList(tsl, e=True, ra=True)
    for s in sel:
        cmds.textScrollList(tsl, e=True, a=s)

def getBasePath(tx):
    scene = cmds.file(q=True, sn=True, sh=True)
    sceneN = cmds.file(q=True, sn=True, shn=True)
    if sceneN:
        new = (scene.split('work')[0] + 'publish/cache/facial').replace('\\', '/')
        if not os.path.isdir(new):
            os.makedirs(new)
            cmds.warning('Created new directory\n' + new)
        cmds.textField(tx, e=True, tx=new)

def oBrowser(mode):
    out = ''
    filter = "Houdini CHOPS (*.clip);;"
    r = cmds.fileDialog2(
        ff=filter,
        cap='CHOPS File Destination',
        dir="data/",
        fm=mode,
        ds=True
    )
    if r:
        out = r[0]
    return out

def bakeTrans(tsl, tx, cbT, cbR, cbS, cbU):
    # scene name
    sceneN = cmds.file(q=True, sn=True, shn=True)
    # FrameRange
    frameR = [
        int(cmds.playbackOptions(q=True, min=True)),
        int(cmds.playbackOptions(q=True, max=True))]
    # Channels
    tr = cmds.checkBox(cbT, q=True, v=True)
    ro = cmds.checkBox(cbR, q=True, v=True)
    sc = cmds.checkBox(cbS, q=True, v=True)
    us = cmds.checkBox(cbU, q=True, v=True)
    # Transform
    trans = cmds.textScrollList(tsl, q=True, ai=True)
    # Main Location
    mainLoc = cmds.textField(tx, q=True, tx=True)
    if not mainLoc:
        cmds.confirmDialog(t='Path Error', m='Please selct directory where to save files')
        return
    if not os.path.isdir(mainLoc):
        cmds.confirmDialog(t='Path Error', m='The selected directory doesn\'t exists')
        return
    # Bake Away
    if not trans:
        cmds.confirmDialog(t='Selection Error', m='Please add somethign to the list')
        return
    for t in trans:
        channels = []
        token = t.replace(':', '_')
        fName = sceneN.split('.m')[0] + '_' + token
        # File Location
        loc = os.path.join(
            mainLoc, fName + '.clip')
        if tr:
            for a in ['tx', 'ty', 'tz']:
                # channels.append(t + '.' + a)
                channels.append(a)
        if ro:
            for a in ['rx', 'ry', 'rz']:
                # channels.append(t + '.' + a)
                channels.append(a)
        if sc:
            for a in ['sx', 'sy', 'sz']:
                # channels.append(t + '.' + a)
                channels.append(a)
        if us:
            cur = cmds.listAttr(t, ud=True)
            if cur:
                for a in cur:
                    # channels.append(t + '.' + a)
                    channels.append(a)
        if channels:
            # print t
            # print channels
            # print loc
            # print frameR
            export(t, channels, loc, frameR)
        else:
            cmds.warning('Skipping this node because no attributes were specified ' + t)

def mayaHoudiniChannel_UI():
    winN = 'mayaHoudini_UI'
    if cmds.window(winN, q=True, ex=True):
        cmds.deleteUI(winN)
    win = cmds.window(winN, t='Maya to Houdini Channel Export', rtf=True)
    fl = cmds.formLayout(p=win)

    tx = cmds.textField(p=fl)
    bt1 = cmds.button(l='Save Location', p=fl)
    tsl = cmds.textScrollList(p=fl)
    cbT = cmds.checkBox(l='translate', p=fl)
    cbR = cmds.checkBox(l='rotate', p=fl)
    cbS = cmds.checkBox(l='scale', p=fl)
    cbU = cmds.checkBox(l='User Defined', p=fl, v=True)
    btnG = cmds.button(l='Get transforms', p=fl)
    btnS = cmds.button(l='Save File', p=fl)

    cmds.formLayout(
        fl, e=True,
        af = [
            (bt1, 'left', 5), (bt1, 'top', 5), (bt1, 'right', 5),
            (tx, 'top', 5), (tx, 'right', 5),
            (tsl, 'left', 5),(tsl, 'right', 5),
            (cbT, 'left', 5),
            (btnG, 'left', 5), (btnG, 'right', 5),
            (btnS, 'left', 5), (btnS, 'right', 5), (btnS, 'bottom', 5)
            ],
        ap = [
            (bt1, 'right', 5, 20),
            (cbT, 'right', 5, 20)
        ],
        ac=[
            (tx, 'left', 5, bt1),
            (tsl, 'top', 5, tx), (tsl, 'bottom', 5, cbT),
            (cbT, 'bottom', 5, btnG),
            (cbR, 'bottom', 5, btnG), (cbR, 'left', 5, cbT),
            (cbS, 'bottom', 5, btnG), (cbS, 'left', 5, cbR),
            (cbU, 'bottom', 5, btnG), (cbU, 'left', 5, cbS),
            (btnG, 'bottom', 5, btnS)
        ]
    )
    # ADD COMMANDS TO UI
    cmds.button(btnG, e=True, c='mayaToHouTrans.setTransform("' + tsl + '")')
    cmds.button(
        bt1, e=True,
        c='cmds.textField("' + tx + '", e=True, tx=mayaToHouTrans.oBrowser(3))')
    cmds.button(
        btnS, e=True,
        c='mayaToHouTrans.bakeTrans("' + tsl + '","' + tx + '", "' + cbT + '", "' + cbR + '", "' + cbS + '", "' + cbU + '")')
    # SHOW WINDOW
    cmds.showWindow(win)
    getBasePath(tx)
    cmds.window(win, e=True, w=300, h=285)


# node = 'CHAR_Lion_lionRig_ma:facial_out'
# channels = cmds.listAttr(node, ud=True)
# channels = []
# for a in attrs:
#     channels.append(node + '.' + a)
# outFile = '/mnt/jobs/Bounty_81040/sequences/GRD_sc131/00140/anim/work/maya/mgiglioli/export/GRD_sc131_00140.v016_test/facial_out2.clip'
# frameRange = [1017, 1108]
# export(node, channels, outFile, frameRange)
