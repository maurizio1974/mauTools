import maya.cmds as cmds
import maya.api.OpenMaya as om


def getScale(ns, fbxNS):
    t1 = cmds.xform(fbxNS + ':root_jnt', q=True, ws=True, t=True)
    t2 = cmds.xform(fbxNS + ':spine09_jnt', q=True, ws=True, t=True)

    v1, v2 = om.MVector(t1), om.MVector(t2)
    fbxS = om.MVector(v2 - v1).length()

    r1 = cmds.xform(ns + 'root_jnt', q=True, ws=True, t=True)
    r2 = cmds.xform(ns + 'spine09_jnt', q=True, ws=True, t=True)
    v1, v2 = om.MVector(r1), om.MVector(r2)
    rigS = om.MVector(v2 - v1).length()

    result = fbxS / rigS
    return result


def mBrowser(mode):
    out = ''
    filter = "Fbx (*.fbx);;"
    r = cmds.fileDialog2(
        ff=filter,
        cap='Select Anim File', dir="data/",
        fm=mode, ds=True)
    if r:
        out = r[0]
    return out


def getRig():
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(
            t='Selection Error', m='Please select the top node of the Rig asset')
        return
    fa = cmds.listRelatives(sel[0], p=True)
    if fa:
        cmds.confirmDialog(
            t='Selection Error', m='Please select the top node of the Rig asset')
        return
    if sel[0].split(':') == 0:
        cmds.confirmDialog(
            t='Selection Error', m='Please Make sure the Rig Asset has a namespace')
        return
    return sel[0]


def getNSindex():
    refs = cmds.ls(type='reference')
    nss = []
    for r in refs:
        if r != 'sharedReferenceNode':
            ns = cmds.referenceQuery(r, ns=True)
            if 'MC' in ns[1:]:
                nss.append(ns[1:])
    return len(nss)


def do_connect(fbx, topN, bake):
    if not fbx:
        cmds.confirmDialog(
            t='Requirement Error', m='Please fille the UI with an fbx file from disc')
        return
    if not topN:
        cmds.confirmDialog(
            t='Requirement Error', m='Please fill the UI with the top node of the Rig Asset')
        return
    # READ FBX IN
    idx = getNSindex()
    fbxNS = 'MC'
    if idx > 0:
        fbxNS = 'MC' + str(idx)
    # cmds.file(
    #     fbx, i=True, type='FBX', ignoreVersion=True, ra=True,
    #     mergeNamespacesOnClash=False, namespace=fbxNS, options='fbx',
    #     pr=True, importTimeRange='combine')
    cmds.file(
        fbx, r=True, type='FBX', ignoreVersion=True, gl=True,
        mergeNamespacesOnClash=False, namespace=fbxNS, options='fbx')
    # CHECK AUTOKEY STATE AND SWITCH IT OFF
    auto = cmds.autoKeyframe(q=True, state=True)
    if auto:
        cmds.autoKeyframe(e=True, state=False)
    # GET NAMESPACE
    ns = ''
    for n in topN.split(':'):
        if n != topN.split(':')[-1]:
            ns += n + ':'
    # SET THE FBX SKELETON TO THE DEFAULT POSITION
    crowdSK = fbxNS + ':skin_export_grp'
    if not cmds.objExists(crowdSK):
        cmds.confirmDialog(
            t='FBX anim Error', m='The fbx file doesn\'t have teh standart skeleton anim rig')
        return
    jnts = cmds.ls(crowdSK, dag=True, type='joint')
    for j in jnts:
        jntR = ns + j.split(':')[-1]
        pos = cmds.getAttr(jntR + '.t')[0]
        rot = cmds.getAttr(jntR + '.r')[0]
        cmds.setAttr(j + '.t', pos[0], pos[1], pos[2])
        cmds.setAttr(j + '.r', rot[0], rot[1], rot[2])
        cmds.refresh()
    # SET NECK TO IK MODE
    cmds.setAttr(ns + 'shoulder_ctrl.neck_status', 0)
    # SET RIG SCALE TO MATCH FBX ANIM
    sc = getScale(ns, fbxNS)
    cmds.setAttr(ns + ':main_ctrl.globalScale', sc)
    cmds.refresh()
    print('*' * 100)
    print('Scaled matched with factor of: ' + str(sc))
    print('*' * 100)
    # CONTROLLERS TO CONNECT
    dict = {
        ns + 'L_front_shoulder_ctrl': [fbxNS + ':L_front_lowLegTwist1_jnt'],
        ns + 'R_front_shoulder_ctrl': [fbxNS + ':R_front_lowLegTwist1_jnt'],
        ns + 'L_back_hip_ctrl': [fbxNS + ':L_back_upLeg_jnt'],
        ns + 'R_back_hip_ctrl': [fbxNS + ':R_back_upLeg_jnt'],
        ns + 'L_front_foot_ctrl': [fbxNS + ':L_front_coffin_jnt'],
        ns + 'R_front_foot_ctrl': [fbxNS + ':R_front_coffin_jnt'],
        ns + 'L_back_foot_ctrl': [fbxNS + ':L_back_pastern_jnt'],
        ns + 'R_back_foot_ctrl': [fbxNS + ':R_back_pastern_jnt'],
        ns + 'pelvis_ctrl': [fbxNS + ':spine01_jnt', fbxNS + ':root_jnt'],
        ns + 'torso_ctrl': [fbxNS + ':spine06_jnt'],
        ns + 'head_ctrl': [fbxNS + ':head_jnt'],
        ns + 'neck_ctrl': [fbxNS + ':neck_02_jnt', fbxNS + ':neck_03_jnt', fbxNS + ':neck_04_jnt'],
        ns + 'shoulder_ctrl': [fbxNS + ':neck_02_jnt', fbxNS + ':spine10_jnt', fbxNS + ':neck_01_jnt'],
        ns + 'L_back_poleVector_ctrl': [fbxNS + ':L_back_lowLegTwist1_jnt', fbxNS + ':L_back_fetlock_correct_jnt'],
        ns + 'R_back_poleVector_ctrl': [fbxNS + ':R_back_lowLegTwist1_jnt', fbxNS + ':R_back_fetlock_correct_jnt'],
        ns + 'L_front_poleVector_ctrl': [fbxNS + ':L_front_fetlock_jnt', fbxNS + ':L_front_lowLegTwist1_jnt'],
        ns + 'R_front_poleVector_ctrl': [fbxNS + ':R_front_fetlock_jnt', fbxNS + ':R_front_lowLegTwist1_jnt']}
    # CONNECT SKELETON
    pcc = ns + 'bake_constraint_set'
    if cmds.objExists(pcc):
        cmds.delete(pcc)
    cmds.sets(em=True, n=pcc)
    bSet = ns + 'bake_anim_set'
    if cmds.objExists(bSet):
        cmds.delete(bSet)
    cmds.sets(em=True, n=bSet)
    for d in dict.keys():
        cmds.select(cl=True)
        cmds.select(dict[d], d, r=True)
        pc = []
        if '_front_shoulder_' in d:
            pc = cmds.parentConstraint(mo=True, sr=['x', 'y', 'z'])
        else:
            pc = cmds.parentConstraint(mo=True)
        cmds.setAttr(pc[0] + '.interpType', 2)
        cmds.select(cl=True)
        cmds.sets(d, add=bSet)
        cmds.sets(pc[0], add=pcc)
    # CONNECT TAIL
    tailJ = cmds.ls(fbxNS + ':tail*_jnt')
    for t in tailJ:
        ctrl = ns + t.split(':')[-1].replace('_jnt', '_ctrl')
        if cmds.objExists(ctrl):
            pc = cmds.parentConstraint(t, ctrl, mo=True)
            cmds.sets(ctrl, add=bSet)
            cmds.sets(pc[0], add=pcc)
    # SET AUTO KEYFRAME BACK TO ORIG STATE
    cmds.autoKeyframe(e=True, state=auto)
    if bake:
        ctrls = cmds.sets(bSet, q=True)
        start = str(int(cmds.playbackOptions(q=True, min=True)))
        end = str(int(cmds.playbackOptions(q=True, max=True)))
        cmds.bakeResults(
            ctrls, simulation=True, t=(start, end), sampleBy=1, oversamplingRate=1,
            disableImplicitControl=True, preserveOutsideKeys=False,
            sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False,
            removeBakedAnimFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True,
            controlPoints=False, shape=False)
        cmds.delete(cmds.sets(pcc, q=True))
        cmds.file(fbx, rr=True)
        cmds.confirmDialog(
            t='Result', m='Animation backed on the rig controllers')
    else:
        cmds.confirmDialog(
            t='Result', m='Animation skeleton conencted to the rig controllers')


def reverse_UI():
    if cmds.window('crowdRevUI', q=True, ex=True):
        cmds.deleteUI('crowdRevUI')
    win = cmds.window('crowdRevUI', t='Connect Crowd Anim', rtf=True)
    # UI
    frT = cmds.formLayout()
    # UI ELEMENTS
    fbxBT = cmds.button(l='Get fbx File', p=frT, en=True)
    fbxTF = cmds.textField(p=frT, en=True)
    rigBT = cmds.button(l='Get rig top node', p=frT)
    rigTF = cmds.textField(p=frT, en=True)
    bkCB = cmds.checkBox(l='Bake anim', v=False)
    conBT = cmds.button(l='Let\'s do it', p=frT)
    # FORMALYOUT ARRANGMENT
    cmds.formLayout(
        frT, e=True,
        af=[
            (fbxBT, 'top', 5), (fbxBT, 'left', 5), (fbxBT, 'right', 5),
            (fbxTF, 'left', 5), (fbxTF, 'right', 5),
            (rigBT, 'left', 5), (rigBT, 'right', 5),
            (rigTF, 'left', 5), (rigTF, 'right', 5),
            (bkCB, 'right', 5),
            (conBT, 'left', 5)],
        ap=[(conBT, 'right', 5, 70)],
        ac=[
            (fbxTF, 'top', 5, fbxBT),
            (rigBT, 'top', 5, fbxTF),
            (rigTF, 'top', 5, rigBT),
            (conBT, 'top', 5, rigTF),
            (bkCB, 'top', 5, rigTF), (bkCB, 'left', 15, conBT)])
    # ADD COMMANDS TO UI
    cmds.button(
        fbxBT, e=True,
        c='cmds.textField("' + fbxTF + '", e=True, tx=rigReverseAnim.mBrowser(1))')
    cmds.button(
        rigBT, e=True,
        c='cmds.textField("' + rigTF + '", e=True, tx=rigReverseAnim.getRig())')
    cmds.button(
        conBT, e=True,
        c='rigReverseAnim.do_connect(cmds.textField("' + fbxTF + '", q=True, tx=True), cmds.textField("' + rigTF + '", q=True, tx=True), cmds.checkBox("' + bkCB + '", q=True, v=True))')
    # SHOW WINDOW AND SIZE IT
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[280, 140])
