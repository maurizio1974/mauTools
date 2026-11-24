'''----------------------------------------------------------------------

OUPOST TIMEWARP UTILITY

Date = 15/11/2019
User = Maurizio Giglioli
Update =
        15/11/2019 First Release

----------------------------------------------------------------------'''
import os
from maya import cmds
from keyframeReduction import KeyframeReduction

# --------------------------------------------------------------------------------------------------------------------------
# MAIN TIMEWARP FUNCTION CREATION
# --------------------------------------------------------------------------------------------------------------------------
def makeTW():
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(t='Selection Error', m='Please select  anode with animation you want to timeWarp')
        return
    # GET INFO
    sceneN = cmds.file(q=True, sn=True, shn=True)
    sceneN = sceneN.replace('.' + sceneN.split('.')[-1], '')
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    # CREATE TIMEWARP
    for s in sel:
        attr = 'tw'
        if not cmds.attributeQuery(attr, n=s, ex=True):
            cmds.addAttr(s, at='message', ln=attr, k=False)
        conn = cmds.listConnections(s, s=True, d=False)
        if conn:
            for c in conn:
                tipo = cmds.nodeType(c)
                if tipo == 'animCurveTL' or tipo == 'animCurveTA' or tipo == 'animCurveTU':
                    # MAKE SETS
                    twws = 'timeWarp_scene_set'
                    tws = 'timeWarp_object_set'
                    for tt in [twws, tws]:
                        if not cmds.objExists(tt):
                            cmds.sets(em=True, n=tt)
                    cmds.sets(tws, add=twws)
                    twm = 'master_tw'
                    if sceneN:
                        twm = sceneN + '_master_tw'
                    # MAKE MASTER ANIM CURVE OF TIMEWARP
                    if not cmds.objExists(twm):
                        cmds.createNode('animCurveTT', n=twm)
                        if not cmds.attributeQuery('outpostTWM', n=twm, ex=True):
                            cmds.addAttr(twm, ln='outpostTWM', dt='string')
                        cmds.setKeyframe(twm, v=start, t=[start], itt='spline', ott='spline')
                        cmds.setKeyframe(twm, v=end, t=[end], itt='spline', ott='spline')
                        cmds.sets(twm, add=twws)
                        cmds.connectAttr('time1.outTime', twm + '.input')
                    # MAKE OBJECT ANIM CURVE OF TIMEWARP
                    tw = s + '_tw'
                    if not cmds.objExists(tw):
                        cmds.createNode('animCurveTT', n=tw)
                        cmds.sets(tw, add=tws)
                        cmds.connectAttr(tw + '.message', s + '.' + attr)
                        cmds.addAttr(tw, ln='outpostTW', dt='string')
                        cmds.setKeyframe(tw, v=start, t=[start], itt='spline', ott='spline')
                        cmds.setKeyframe(tw, v=end, t=[end], itt='spline', ott='spline')
                        cmds.connectAttr(twm + '.output', tw + '.input', f=True)
                    # print tipo, c
                    ch = c + '_tw_blender'
                    cmds.createNode('blendTwoAttr', n=ch)
                    cmds.connectAttr('time1.outTime', ch + '.input[0]', f=True)
                    cmds.connectAttr(tw + '.output', ch + '.input[1]', f=True)
                    cmds.connectAttr(ch + '.output', c + '.input', f=True)
                    attr = 'timeWarp'
                    if not cmds.attributeQuery(attr, n=s, ex=True):
                        cmds.addAttr(s, ln=attr, at='double', k=False)
                        # cmds.setAttr(s + '.' + attr, cb=True)
                        cmds.setAttr(s + '.' + attr, 1)
                    cmds.connectAttr(s + '.' + attr, ch + '.attributesBlender', f=True)
    cmds.select(sel, r=True)
# --------------------------------------------------------------------------------------------------------------------------
# UTILITIES
# --------------------------------------------------------------------------------------------------------------------------
# GET ALL THE TIMEWARP IN THE SCENE
def getTW():
    out, master = [], ''
    anims = cmds.ls(type='animCurveTT')
    for a in anims:
        if cmds.attributeQuery('outpostTW', n=a, ex=True):
            out.append(a)
        elif cmds.attributeQuery('outpostTWM', n=a, ex=True):
            master = a
    return out, master

# GET WARPED NODE
def getWarped():
    out = []
    anims = getTW()[0]
    for a in anims:
        if cmds.attributeQuery('outpostTW', n=a, ex=True):
            conn = cmds.listConnections(a + '.message')
            if conn:
                for c in conn:
                    tipo = cmds.nodeType(c)
                    if tipo == 'transform':
                        out.append(c)
    return out

# WRAPPER FOR CLEAN TIMEWARP
def cleanTW(tsl):
    sel = cmds.textScrollList(tsl, q=True, si=True)
    if not sel:
        cmds.confirmDialog(t='Selection Error', m='Please select one or more timewarp node in the ui')
        return
    for s in sel:
        do_cleanTW(s)

# DO CLEAN TIMEWARP
def do_cleanTW(node):
    attrs = ['timeWarp', 'tw']
    if node:
        if cmds.objExists(node):
            if cmds.attributeQuery('message', n=node, ex=True):
                trans = cmds.listConnections(node + '.message')
                chs = cmds.listConnections(node + '.output', scn=True)
                if chs:
                    for c in chs:
                        cmds.delete(c)
                if trans:
                    for t in trans:
                        if cmds.nodeType(t) == 'transform':
                            for a in attrs:
                                if cmds.attributeQuery(a, n=t, ex=True):
                                    cmds.deleteAttr(t + '.' + a)
                cmds.delete(node)

# CLEAN ALL TIMEWARPS
def do_cleanAllTW(tsl):
    sel = cmds.textScrollList(tsl, q=True, ai=True)
    if sel:
        for s in sel:
            do_cleanTW(s)
    masters = cmds.ls('*master_tw')
    if masters:
        for m in masters:
            tipo = cmds.nodeType(m)
            if tipo  == 'animCurveTT':
                if cmds.attributeQuery('outpostTWM', n=m, ex=True):
                    cmds.delete(m)

# WRAPPER FOR BAKING TIMEWARP
def bakeTW(tsl, full, key):
    baked = []
    sel = cmds.textScrollList(tsl, q=True, si=True)
    if full == 1:
        sel = cmds.textScrollList(tsl, q=True, ai=True)
    if not sel:
        cmds.confirmDialog(t='Selection Error', m='Please select one or more timewarp node in the ui')
        return
    # DISABLE VIEWPORT REFRESH
    cmds.refresh(suspend=True)
    for s in sel:
        do_bakeTW(s, key)
    # for s in sel:
    #     baked.append(s)
    # do_bakeTW2(baked, key)
    # ENABLE VIEWPORT REFRESH
    cmds.refresh(suspend=False)
    cmds.refresh(f=True)
    if full == 1:
        do_cleanAllTW(tsl)

# BAKE TIMEWARP
def do_bakeTW(node, key):
    attrs = []
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    cur = node.replace('_tw', '')
    # GET ATTRIBUTES TO BAKE
    trans = cmds.listConnections(node + '.message')
    if trans:
        for t in trans:
            if cmds.nodeType(t) == 'transform':
                curves = cmds.listConnections(t, s=True, d=False)
                if curves:
                    for c in curves:
                        tipo = cmds.nodeType(c)
                        if tipo == 'animCurveTA' or tipo == 'animCurveTL' or tipo == 'animCurveTU': 
                            a = cmds.listConnections(c + '.output', s=False, d=True, p=True)[0].split('.')[-1]
                            attrs.append(str(a))
    if attrs:
        # tr = cmds.createNode('transform')
        tr = cmds.duplicate(cur, rr=True, rc=True)[0]
        nodes = cmds.listRelatives(tr, f=True)
        pc, sc = None, None
        for n in nodes:
            cmds.delete(n)
        try:
            pc = cmds.parentConstraint(cur, tr)
            sc = cmds.scaleConstraint(cur, tr)
        except:
            pass
        # BAKE THE NODE WITH THE SPECIFIED ATTRIBUTES
        cmds.bakeResults(
            tr, at=attrs, simulation=True,
            t=(start, end), sampleBy=1, oversamplingRate=1,
            disableImplicitControl=True,
            preserveOutsideKeys=False,
            sparseAnimCurveBake=False,
            removeBakedAttributeFromLayer=False,
            removeBakedAnimFromLayer=False,
            bakeOnOverrideLayer=False,
            minimizeRotation=True,
            controlPoints=False, shape=False)
        # REMOVE CONTRAINTS
        for constr in [pc, sc]:
            if constr:
                for n in constr:
                    if cmds.objExists(n):
                        cmds.delete(n)
        # REDUCE KEYS
        if key:
            for a in attrs:
                reduceTW(tr + '_' + a)
        # RECONNECT BAKED CURVES
        animC = cmds.listConnections(cur, s=True, d=False)
        if animC:
            for c in animC:
                tipo = cmds.nodeType(c)
                if tipo == 'animCurveTA' or tipo == 'animCurveTL' or tipo == 'animCurveTU':
                    cmds.delete(c)
        animC = cmds.listConnections(tr, s=True, d=False)
        if animC:
            for c in animC:
                tipo = cmds.nodeType(c)
                if tipo == 'animCurveTA' or tipo == 'animCurveTL' or tipo == 'animCurveTU':
                    attr = cmds.listConnections(c + '.output', s=False, d=True, p=True)[0].split('.')[-1]
                    # attr = c.split('_')[-1]
                    new = cur + '_' + attr
                    cmds.rename(c, new)
                    cmds.connectAttr(new + '.output', cur + '.' + attr, f=True)
        # CLEANUP
        cmds.delete(tr)
        do_cleanTW(node)

def do_bakeTW2(nodes, key):
    baked = []
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    for n in nodes:
        cur = n.replace('_tw', '')
        tr = cmds.duplicate(cur, rr=True, rc=True)[0]
        nodes = cmds.listRelatives(tr, f=True)
        for n in nodes:
            cmds.delete(n)
        try:
            cmds.parentConstraint(cur, tr)
            cmds.scaleConstraint(cur, tr)
        except:
            pass
        # CONNECT UD ATTRS
        attrs = cmds.listAttr(cur, ud=True)
        for a in attrs:
            cmds.connectAttr(cur + '.' + a, tr + '.' + a, f=True)
            # print cur + '.' + a, '   --->>>   ', tr + '.' + a
        baked.append(tr)
    # BAKE THE NODE WITH THE SPECIFIED ATTRIBUTES
    cmds.bakeResults(
        baked, simulation=True, t=(start, end), sampleBy=1,
        oversamplingRate=1, disableImplicitControl=False,
        preserveOutsideKeys=False, sparseAnimCurveBake=False,
        removeBakedAttributeFromLayer=False, removeBakedAnimFromLayer=False,
        bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False,
        shape=False)
    # REMOVE CONTRAINTS
    for b in baked:
        const = cmds.listRelatives(b, type='transform')
        if const:
            for c in const:
                if 'Constraint' in c:
                    cmds.delete(c)
    # REMOVE STATIC CHANNELS
    cmds.select(baked, r=True)
    cmds.delete(
        staticChannels=True, unitlessAnimationCurves=False,
        hierarchy=False, controlPoints=0, shape=1)
    # REDUCE KEYS
    if key:
        for a in attrs:
            reduceTW(tr + '_' + a)
    # RECONNECT BAKED CURVES
    animC = cmds.listConnections(cur, s=True, d=False)
    if animC:
        for c in animC:
            tipo = cmds.nodeType(c)
            if tipo == 'animCurveTA' or tipo == 'animCurveTL' or tipo == 'animCurveTU':
                cmds.delete(c)
    animC = cmds.listConnections(tr, s=True, d=False)
    if animC:
        for c in animC:
            tipo = cmds.nodeType(c)
            if tipo == 'animCurveTA' or tipo == 'animCurveTL' or tipo == 'animCurveTU':
                attr = cmds.listConnections(c + '.output', s=False, d=True, p=True)[0].split('.')[-1]
                new = cur + '_' + attr
                cmds.rename(c, new)
                cmds.connectAttr(new + '.output', cur + '.' + attr, f=True)
    # CLEANUP
    for b in baked:
        cmds.delete(b)
    for n in nodes:
        do_cleanTW(n)

# REDUCE KEYFRAMES
def reduceTW(node):
    obj = KeyframeReduction(node)
    obj.reduce(error=0.1, weightedTangents=True)

# REVERSE THE SELECTED CURVE
def timeWRev(tsl, node):
    sceneN = cmds.file(q=True, sn=True, shn=True)
    sceneN = sceneN.replace('.' + sceneN.split('.')[-1], '')
    sel = cmds.textScrollList(tsl, q=True, si=True)
    if node:
        if node != 'master':
            sel = [node]
        else:
            twm = 'master_tw'
            if sceneN:
                twm = sceneN + '_master_tw'
            sel = [twm]
    if not sel:
        cmds.confirmDialog(t='Selection Error', m='Please select one or more timewarp node in the ui')
        return
    for s in sel:
        do_timeWRev(s)

def do_timeWRev(node):
    # out = {}
    # GET KEYFRAMES INFO
    # info = cmds.keyframe(node, q=True, vc=True, tc=True)
    infoT = cmds.keyframe(node, q=True, tc=True)
    first_frame = infoT[0]
    last_frame = infoT[-1]
    cmds.scaleKey(node, time=(first_frame, last_frame), nst=last_frame, net=first_frame)
    # for i in range(0, len(info), 2):
    #     out[info[i]] = info[i + 1]
    # # GET DIFFERENCE TO MOVE KEYFRAMES
    # diff_frame = last_frame - first_frame
    # mid_frame = diff_frame / 2 + first_frame
    # for o in out.keys():
    #     val = ''
    #     if o < mid_frame:
    #         val = o + diff_frame
    #     else:
    #         val = o - diff_frame
    #     cmds.keyframe(node, e=True, t=(o,o), tc=val, a=True, o='over')
    # # ROUND KEYS VALUES IF NEEDED
    # info = cmds.keyframe(node, q=True, tc=True)
    # kfs = {}
    # for i in info:
    #     kfs[i] = round(i)
    # # SNAP TO ROUND VALUE
    # for k in kfs.keys():
    #     cmds.keyframe(node, e=True, t=(k,k), tc=kfs[k], a=True, o='over')
    # # FLIP TANGETS
    # for x in kfs.values():
    #     vals = cmds.keyTangent(node, q=True, t=(x, x), ia=True, oa=True)
    #     if vals[0] != vals[1]:
    #         cmds.keyTangent(node, e=True, t=(x, x), oa=-1 * vals[0], ia=-1 * vals[1])



# --------------------------------------------------------------------------------------------------------------------------
# UI UTILITIES
# CLEAN GRAPHEDITOR
def cleanGE(ge):
    gr = cmds.layout(ge,q = True, ca = True)
    fr = cmds.formLayout(gr[0],q = True, ca = True)
    ca = cmds.layout(fr[0], q = True, ca = True)
    fl = cmds.layout(ca[0], q = True, ca = True)
    deltes = {
        'directKeyTool','latticeDeformKeyTool','regionSelectKeyTool','retimeKeyTool','toolSeparator','keyframeStats',
        'centerCurrentTimeButton','frameRangeButton','plateauTanButton','bufferSeparator','bufferSnapButton','clampedTanButton',
        'bufferSwapButton','tangentSeparator','normSeparator','flatTanButton','stepTanButton','freeTanButton','normSeparator',
        'denormalizeCurvesButton','renormalizeCurvesButton','stackedCurvesButton','unstackedCurvesButton','normalizeCurvesButton',
        'unifyTanButton','curvesPrePostInfinitySeparator','curvesPreInfinityCycleButton','curvesPreInfinityCycleOffsetButton',
        'curvesPostInfinityCycleButton','lockTanButton','curvesPostInfinityCycleOffsetButton','rightSeparator','loadSeparator'}
    for d in deltes:
        cmds.deleteUI(d)
    cas = cmds.layout(fl[0], q = True, ca = True)
    for c in cas:
        if 'OutlineEd' in c:
            cmds.deleteUI(c)
# CLEAN OUTLINER
def cleanOT(ge):
    outL = ge + 'OutlineEd'
    cmds.outlinerEditor(outL, e=True, showAttributes=False)
    cmds.outlinerEditor(outL, e=True, showShapes=False)
    cmds.outlinerEditor(outL, e=True, showSetMembers=False)
    cmds.outlinerEditor(outL, e=True, expandAttribute=False)
    cmds.outlinerEditor(outL, e=True, showTimeEditor=False)
    cmds.outlinerEditor(outL, e=True, showDagOnly=False)
    cmds.outlinerEditor(outL, e=True, showConnected=False)
# ADD TO TEXTSCROLLLIST
def addTSL(tsl):
    cmds.textScrollList(tsl, e=True, ra=True)
    nodes = getTW()[0]
    if nodes:
        for g in nodes:
            # cmds.textScrollList(tsl, e=True, append=g, fn='boldLabelFont')
            cmds.textScrollList(tsl, e=True, append=g)

# SELECT THE NODE ON THE TEXTSCROLLLIST
def selTSL(tsl):
    nodes = cmds.textScrollList(tsl, q=True, si=True)
    if nodes:
        cmds.select(cl=True)
        for n in nodes:
            cmds.select(n, add=True)
# SELECT THE TRANSFORM OF THE SELECTED ITEM ON THE TEXTSCROLLLIST
def selTrans(tsl):
    nodes = cmds.textScrollList(tsl, q=True, si=True)
    if nodes:
        cmds.select(cl=True)
        for n in nodes:
            cur = n.replace('_tw', '')
            if cmds.objExists(cur):
                cmds.select(cur, r=True)
# SELECT MASTER TIME WARP
def selMTW():
    masters = cmds.ls('*master_tw')
    if masters:
        for m in masters:
            tipo = cmds.nodeType(m)
            if tipo  == 'animCurveTT':
                if cmds.attributeQuery('outpostTWM', n=m, ex=True):
                    cmds.select(m, r=True)
# ENABLE/DISABLE TIMEWARP ON SELECTED NODE
def enableDisableTW(tsl, bttm, val):
    sel = cmds.textScrollList(tsl, q=True, si=True)
    label = cmds.button(bttm, q=True, l=True)
    for s in sel:
        mesh = cmds.listConnections(s + '.message')
        for m in mesh:
            tipo = cmds.nodeType(m)
            if tipo == 'transform':
                cmds.setAttr(m + '.timeWarp', val)
# GET BANNER
def getbanner():
    dirname, filename = os.path.split(os.path.abspath(__file__))
    dirname = dirname.replace('\\', '/')
    out = dirname.replace(dirname.split('/')[-1], '')
    for x in range(0, 3):
        out = out.replace(out.split('/')[-2], '')
    out = os.path.join(out[:-1], 'icons', 'timewarp_logo.jpg')
    if os.path.isfile(out):
        return out

# def addSC(node):
#     for n in node:
#         for s in cmds.ls(sl=True):
#             cmds.selectionConnection(sc, e=True, select=s)    
# def clearSC(sc):
#     cmds.selectionConnection(sc, e=True, clr=True)

# --------------------------------------------------------------------------------------------------------------------------
# UI
def outpostTimeWarp_UI_old():
    image = getbanner()
    winT, winN = 'OutPost VFX TimeWarp', 'OutPost_VFXtimeWarpWIN'
    if cmds.window(winN, ex=True):
        cmds.deleteUI(winN)
    if cmds.animCurveEditor('graphEditorOutpostGraphEd', ex=True):
        cmds.deleteUI('graphEditorOutpostGraphEd')
    win = cmds.window(winN, t=winT)
    fr = cmds.formLayout()
    # print image
    logo = cmds.iconTextStaticLabel(st='iconOnly', i1=image, l=image.split('/')[-1].split('.')[0], bgc=[0, 0, 0])
    tsl = cmds.textScrollList(p=fr, h=150, ams=True)
    btr = cmds.button(l='Get All TimeWarps')
    btm = cmds.button(l='Make TimeWarp')
    btd = cmds.button(l='Delete Selected TimeWarps')
    btdd = cmds.button(l='Delete all TimeWarps')
    btb = cmds.button(l='Bake Selected TimeWarps')
    btbb = cmds.button(l='Bake all TimeWarps')
    afs = cmds.button(l='Disable selected nodes', w=150)
    afsE = cmds.button(l='Enable selected nodes', w=150)
    btInv = cmds.button(l='Invert Selected Curves', w=150, m=True)
    btInvM = cmds.button(l='Invert Master Curve', w=150, m=True)
    cb = cmds.checkBox(l='Auto Key Reduce', v=False)
    btsm = cmds.button(l='Select Master TimeWarp')
    # GRAPHEDITOR TIMEWARP UI
    flg = cmds.frameLayout(cll=True, cl=True, l='Graph TimeWarp', p=fr)
    pl = cmds.paneLayout(p=flg, h=250)
    ge = cmds.scriptedPanel(type='graphEditor', mbv=True, p=pl)
    # EDIT MAIN UI FORMLAYOUT
    cmds.formLayout(
        fr, e=True,
        af=[
                (logo, 'left', 5), (logo, 'top', 5), (logo, 'right', 5),
                (tsl, 'left', 5),
                (btr, 'left', 5), (btr, 'bottom', 5),
                (btm, 'right', 5),
                (btb, 'right', 5),
                (btbb, 'right', 5),
                (cb, 'right', 150),
                (flg, 'right', 5),
                (btsm, 'right', 5), (btsm, 'bottom', 5)
            ],
        ap=[
                (tsl, 'right', 5, 15),
                (btr, 'right', 5, 15),
                (btd, 'right', 5, 55),
                (btdd, 'right', 5, 55)
            ],
        ac=[
                (tsl, 'top', 5, logo), (tsl, 'bottom', 5, btr),
                (btm, 'top', 5, logo), (btm, 'left', 5, tsl),
                (btd, 'left', 5, tsl), (btd, 'top', 5, btm),
                (btdd, 'left', 5, tsl), (btdd, 'top', 5, btd),
                (btb, 'left', 5, btd), (btb, 'top', 5, btm),
                (btbb, 'left', 5, btdd), (btbb, 'top', 5, btb),
                (afs, 'left', 5, tsl), (afs, 'top', 5, btbb),
                (afsE, 'left', 5, afs), (afsE, 'top', 5, btbb),
                (btInv, 'left', 5, afsE), (btInv, 'top', 5, btbb),
                (btInvM, 'left', 5, btInv), (btInvM, 'top', 5, btbb),
                (cb, 'left', 25, btInvM), (cb, 'top', 5, btbb),
                (flg, 'top', 5, afs), (flg, 'left', 5, tsl), (flg, 'bottom', 5, btsm),
                (btsm, 'left', 5, tsl)
            ]
        )
    # ADDC OMMANDS TO THE UI
    cmds.frameLayout(
        flg, e=True,
        cc='cmds.window("' + win + '", e=True, h=250)',
        ec='cmds.window("' + win + '", e=True, h=620)')
    cmds.textScrollList(
        tsl, e=True,
        sc='outpostTimeWarp.selTSL("' + tsl + '")',
        dcc='outpostTimeWarp.selTrans("' + tsl + '")')
    cmds.button(afs, e=True, c='outpostTimeWarp.enableDisableTW("' + tsl + '", "' + afs + '", 0)')
    cmds.button(afsE, e=True, c='outpostTimeWarp.enableDisableTW("' + tsl + '", "' + afsE + '", 1)')
    cmds.button(btr, e=True, c='outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btm, e=True, c='outpostTimeWarp.makeTW();outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btd, e=True, c='outpostTimeWarp.cleanTW("' + tsl + '");outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btdd, e=True, c='outpostTimeWarp.do_cleanAllTW("' + tsl + '");outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btsm, e=True, c='outpostTimeWarp.selMTW()')
    cmds.button(btInv, e=True, c='outpostTimeWarp.timeWRev("' + tsl + '", None)')
    cmds.button(btInvM, e=True, c='outpostTimeWarp.timeWRev("' + tsl + '", "master")')
    cmds.button(
        btb, e=True,
        c='outpostTimeWarp.bakeTW("'+ tsl +'", 0, cmds.checkBox("' +cb + '", q=True, v=True));outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(
        btbb, e=True,
        c='outpostTimeWarp.bakeTW("'+ tsl +'", 1, cmds.checkBox("' +cb + '", q=True, v=True));outpostTimeWarp.addTSL("' + tsl + '")')
    # SHOW UI
    cmds.showWindow(win)
    cmds.window(win, e = True, wh = [910, 250])
    # FILL AND CUSTOMIZE UI
    addTSL(tsl)
    # cleanGE(ge)
    cleanOT(ge)


def outpostTimeWarp_UI_old2():
    image = getbanner()
    winT, winN = 'OutPost VFX TimeWarp', 'OutPost_VFXtimeWarpWIN'
    if cmds.window(winN, ex=True):
        cmds.deleteUI(winN)
    if cmds.animCurveEditor('graphEditorOutpostGraphEd', ex=True):
        cmds.deleteUI('graphEditorOutpostGraphEd')
    win = cmds.window(winN, t=winT, mb=True)
    mbk = cmds.menu(l='Bake Option', p=win)
    mcb = cmds.menuItem(l='Auto Key Reduce', cb=False, p=mbk)
    mfr = cmds.formLayout()
    logo = cmds.iconTextStaticLabel(st='iconOnly', i1=image, l=image.split('/')[-1].split('.')[0], bgc=[0, 0, 0], p=mfr)
    pl = cmds.paneLayout(configuration='vertical2', ps=[1, 25, 100], p=mfr)
    tsl = cmds.textScrollList(p=pl, h=150, ams=True)
    fr = cmds.formLayout(p=pl)
    cmds.formLayout(
        mfr, e=True,
        af=[
            (logo, 'left', 5), (logo, 'top', 5), (logo, 'right', 5),
            (pl, 'left', 5), (pl, 'right', 5), (pl, 'bottom', 5)
        ],
        ac=[
            (pl, 'top', 5, logo)
        ])
    btr = cmds.button(l='Get Warps', p=fr)
    btm = cmds.button(l='Make Warps', p=fr)
    btd = cmds.button(l='Delete Selected Warps', p=fr)
    btdd = cmds.button(l='Delete all Warps', p=fr)
    btb = cmds.button(l='Bake Selected Warps', p=fr)
    btbb = cmds.button(l='Bake all Warps', p=fr)
    afs = cmds.button(l='Disable selected Warps', p=fr, w=150)
    afsE = cmds.button(l='Enable selected Warps', p=fr, w=150)
    btInv = cmds.button(l='Invert Selected Warps', p=fr, w=150, m=True)
    btInvM = cmds.button(l='Invert Master Warp', p=fr, w=150, m=True)
    # cb = cmds.checkBox(l='Auto Key Reduce', v=False, p=fr)
    btsm = cmds.button(l='Select Master Warps', p=fr)
    # GRAPHEDITOR TIMEWARP UI
    flg = cmds.frameLayout(cll=True, cl=True, l='Graph Warp', p=fr)
    pla = cmds.paneLayout(p=flg, h=250, w=50)
    ge = cmds.scriptedPanel(type='graphEditor', mbv=True, p=pla)
    # EDIT MAIN UI FORMLAYOUT
    cmds.formLayout(
        fr, e=True,
        af=[
                (btr, 'top', 5), (btr, 'left', 5),
                (btm, 'top', 5), (btm, 'right', 5),
                (btd, 'left', 5),
                (btdd, 'left', 5),
                (btb, 'right', 5),
                (btbb, 'right', 5),
                (afs, 'left', 5), 
                (afsE, 'right', 5), 
                (btInv, 'left', 5,),
                (btInvM, 'right', 5),
                (flg, 'left', 5), (flg, 'right', 5),
                (btsm, 'left', 5), (btsm, 'right', 5), (btsm, 'bottom', 5)
            ],
        ap=[
                (btr, 'right', 5, 50),
                (btd, 'right', 5, 50),
                (btdd, 'right', 5, 50),
                (afs, 'right', 5, 50),
                (btInv, 'right', 5, 50)
            ],
        ac=[
                (btm, 'left', 5, btr),
                (btd, 'top', 5, btm),
                (btdd, 'top', 5, btd),
                ( btb, 'left', 5, btd), (btb, 'top', 5, btm),
                (btbb, 'left', 5, btdd), (btbb, 'top', 5, btb),
                (afs, 'top', 5, btbb),
                (afsE, 'left', 5, afs), (afsE, 'top', 5, btbb),
                (btInv, 'top', 5, afs),
                (btInvM, 'top', 5, afsE), (btInvM, 'left', 5, afs),
                (flg, 'top', 5, btInv), (flg, 'bottom', 5, btsm)
            ]
        )
    # ADDC OMMANDS TO THE UI
    cmds.frameLayout(
        flg, e=True,
        cc='cmds.window("' + win + '", e=True, h=250)',
        ec='cmds.window("' + win + '", e=True, h=620)')
    cmds.textScrollList(
        tsl, e=True,
        sc='outpostTimeWarp.selTSL("' + tsl + '")',
        dcc='outpostTimeWarp.selTrans("' + tsl + '")')
    cmds.button(afs, e=True, c='outpostTimeWarp.enableDisableTW("' + tsl + '", "' + afs + '", 0)')
    cmds.button(afsE, e=True, c='outpostTimeWarp.enableDisableTW("' + tsl + '", "' + afsE + '", 1)')
    cmds.button(btr, e=True, c='outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btm, e=True, c='outpostTimeWarp.makeTW();outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btd, e=True, c='outpostTimeWarp.cleanTW("' + tsl + '");outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btdd, e=True, c='outpostTimeWarp.do_cleanAllTW("' + tsl + '");outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btsm, e=True, c='outpostTimeWarp.selMTW()')
    cmds.button(btInv, e=True, c='outpostTimeWarp.timeWRev("' + tsl + '", None)')
    cmds.button(btInvM, e=True, c='outpostTimeWarp.timeWRev("' + tsl + '", "master")')
    cmds.button(
        btb, e=True,
        c='outpostTimeWarp.bakeTW("'+ tsl +'", 0, cmds.menuItem("' + mcb + '", q=True, cb=True));outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(
        btbb, e=True,
        c='outpostTimeWarp.bakeTW("'+ tsl +'", 1, cmds.checkBox("' + mcb + '", q=True, cb=True));outpostTimeWarp.addTSL("' + tsl + '")')
    # SHOW UI
    cmds.showWindow(win)
    cmds.window(win, e = True, wh = [910, 300])
    # FILL AND CUSTOMIZE UI
    addTSL(tsl)
    # cleanGE(ge)
    cleanOT(ge)


def outpostTimeWarp_UI():
    image = getbanner()
    winT, winN = 'OutPost VFX TimeWarp', 'OutPost_VFXtimeWarpWIN'
    if cmds.window(winN, ex=True):
        cmds.deleteUI(winN)
    if cmds.animCurveEditor('graphEditorOutpostGraphEd', ex=True):
        cmds.deleteUI('graphEditorOutpostGraphEd')
    win = cmds.window(winN, t=winT, mb=True)
    mbk = cmds.menu(l='Bake Option', p=win)
    mcb = cmds.menuItem(l='Auto Key Reduce', cb=False, p=mbk)
    mfr = cmds.formLayout()
    logo = cmds.iconTextStaticLabel(st='iconOnly', i1=image, l=image.split('/')[-1].split('.')[0], bgc=[0, 0, 0], p=mfr)
    pl = cmds.paneLayout(configuration='vertical2', ps=[1, 25, 100], p=mfr)
    tsl = cmds.textScrollList(p=pl, h=150, ams=True)
    fr = cmds.formLayout(p=pl)
    
    cmds.formLayout(
        mfr, e=True,
        af=[
            (logo, 'left', 5), (logo, 'top', 5), (logo, 'right', 5),
            (pl, 'left', 5), (pl, 'right', 5), (pl, 'bottom', 5)
        ],
        ac=[
            (pl, 'top', 5, logo)
        ])
    flc = cmds.frameLayout(cll=False, cl=False, l='Create', p=fr)
    frc = cmds.formLayout(p=flc)
    btr = cmds.button(l='Refresh Warps', p=frc)
    btm = cmds.button(l='Make Warps', p=frc)
    btd = cmds.button(l='Delete Selected Warps', p=frc)
    btdd = cmds.button(l='Delete all Warps', p=frc)
    cmds.formLayout(
        frc, e=True,
        af=[
                (btm, 'top', 5), (btm, 'left', 5),
                (btr, 'top', 5), (btr, 'right', 5),
                (btd, 'left', 5),
                (btdd, 'right', 5),
            ],
        ap=[
                (btm, 'right', 5, 50),
                (btd, 'right', 5, 50),
            ],
        ac=[
                (btr, 'left', 5, btm),
                (btd, 'top', 5, btm),
                (btdd, 'top', 5, btm), (btdd, 'left', 5, btd)
            ]
        )
    flb = cmds.frameLayout(cll=True, cl=True, l='Edit / Bake', p=fr)
    frb = cmds.formLayout(p=flb)
    btb = cmds.button(l='Bake Selected Warps', p=frb)
    btbb = cmds.button(l='Bake all Warps', p=frb)
    afs = cmds.button(l='Disable selected Warps', p=frb, w=150)
    afsE = cmds.button(l='Enable selected Warps', p=frb, w=150)
    btInv = cmds.button(l='Invert Selected Warps', p=frb, w=150, m=True)
    btInvM = cmds.button(l='Invert Master Warp', p=frb, w=150, m=True)
    cmds.formLayout(
        frb, e=True,
        af=[
                (btb, 'left', 5), (btb, 'top', 5), 
                (btbb, 'right', 5), (btbb, 'top', 5), 
                (afs, 'left', 5),
                (afsE, 'right', 5),
                (btInv, 'left', 5,),
                (btInvM, 'right', 5),
            ],
        ap=[
                (btb, 'right', 5, 50),
                (afs, 'right', 5, 50),
                (btInv, 'right', 5, 50)
            ],
        ac=[
                (btbb, 'left', 5, btb),
                (afs, 'top', 5, btb),
                (afsE, 'left', 5, afs), (afsE, 'top', 5, btb),
                (btInv, 'top', 5, afs),
                (btInvM, 'top', 5, afsE), (btInvM, 'left', 5, afs),
            ]
        )
    # GRAPHEDITOR TIMEWARP UI
    flg = cmds.frameLayout(cll=True, cl=True, l='Warp Graph', p=fr)
    pla = cmds.paneLayout(p=flg, h=250, w=50)
    ge = cmds.scriptedPanel(type='graphEditor', mbv=True, p=pla)
    
    btsm = cmds.button(l='Select Master Warps', p=fr)
    # EDIT MAIN UI FORMLAYOUT
    cmds.formLayout(
        fr, e=True,
        af=[
                (flc, 'top', 5), (flc, 'left', 5), (flc, 'right', 5),
                (flb, 'left', 5), (flb, 'right', 5),
                (flg, 'left', 5), (flg, 'right', 5),
                (btsm, 'bottom', 5), (btsm, 'left', 5), (btsm, 'right', 5),
            ],
        ac=[
                (flb, 'top', 5, flc),
                (flg, 'top', 5, flb), (flg, 'bottom', 5, btsm),
            ]
        )
    # ADDC OMMANDS TO THE UI
    cmds.frameLayout(
        flg, e=True,
        cc='cmds.window("' + win + '", e=True, h=cmds.window("' + win + '", q=True, h=True) - 350)',
        ec='cmds.window("' + win + '", e=True, h=cmds.window("' + win + '", q=True, h=True) + 350)')
    cmds.frameLayout(
        flb, e=True,
        cc='cmds.window("' + win + '", e=True, h=cmds.window("' + win + '", q=True, h=True) - 70)',
        ec='cmds.window("' + win + '", e=True, h=cmds.window("' + win + '", q=True, h=True) + 70)')
    cmds.textScrollList(
        tsl, e=True,
        sc='outpostTimeWarp.selTSL("' + tsl + '")',
        dcc='outpostTimeWarp.selTrans("' + tsl + '")')
    cmds.button(afs, e=True, c='outpostTimeWarp.enableDisableTW("' + tsl + '", "' + afs + '", 0)')
    cmds.button(afsE, e=True, c='outpostTimeWarp.enableDisableTW("' + tsl + '", "' + afsE + '", 1)')
    cmds.button(btr, e=True, c='outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btm, e=True, c='outpostTimeWarp.makeTW();outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btd, e=True, c='outpostTimeWarp.cleanTW("' + tsl + '");outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btdd, e=True, c='outpostTimeWarp.do_cleanAllTW("' + tsl + '");outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(btsm, e=True, c='outpostTimeWarp.selMTW()')
    cmds.button(btInv, e=True, c='outpostTimeWarp.timeWRev("' + tsl + '", None)')
    cmds.button(btInvM, e=True, c='outpostTimeWarp.timeWRev("' + tsl + '", "master")')
    cmds.button(
        btb, e=True,
        c='outpostTimeWarp.bakeTW("'+ tsl +'", 0, cmds.menuItem("' + mcb + '", q=True, cb=True));outpostTimeWarp.addTSL("' + tsl + '")')
    cmds.button(
        btbb, e=True,
        c='outpostTimeWarp.bakeTW("'+ tsl +'", 1, cmds.checkBox("' + mcb + '", q=True, cb=True));outpostTimeWarp.addTSL("' + tsl + '")')
    # SHOW UI
    cmds.showWindow(win)
    cmds.window(win, e = True, wh = [910, 275])
    # FILL AND CUSTOMIZE UI
    addTSL(tsl)
    # cleanGE(ge)
    cleanOT(ge)
# outpostTimeWarp_UI2()