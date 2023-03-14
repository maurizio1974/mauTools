from maya import cmds


def makeJNT(crv, index):
    name = crv.replace('Curve', '_') + str(index).zfill(2)
    sh = cmds.listRelatives(crv, s=True)
    spans = cmds.getAttr(sh[0] + '.spans')
    posx, posy, posz = 0, 0, 0
    for x in range(0, spans):
        pos = cmds.pointPosition(crv + '.cv[' + str(x) + ']')
        posx += pos[0]
        posy += pos[1]
        posz += pos[2]
    # GET CENTROID AND CREATE JOINT
    ctr = [posx / spans, posy / spans, posz / spans]
    jnt = cmds.joint(n=name + '_jnt', radius=0.1)
    cmds.xform(jnt, ws=True, t=(ctr[0], ctr[1], ctr[2]))
    return(jnt)


def makeCrv(jnts):
    name = jnts[0].replace('_jnt', '')
    pos = cmds.xform(jnts[0], q=True, ws=True, t=True)
    crv = cmds.curve(d=3, p=(pos[0], pos[1], pos[2]), n=name + '_crv')
    for j in jnts:
        pos = cmds.xform(j, q=True, ws=True, t=True)
        cmds.curve(crv, append=True, p=(pos[0], pos[1], pos[2]))
    return crv


def makeSpIK(jnts, ctn):
    name = jnts[0].replace('_jnt', '')
    crvIK = makeCrv(jnts)
    shape = cmds.listRelatives(crvIK, s=True, f=True)
    sh = [crvIK + 'Shape']
    cmds.rename(shape[0], sh[0])
    spans = cmds.getAttr(sh[0] + '.spans') + 2
    cmds.ikHandle(
        c=crvIK, sj=jnts[0], ee=jnts[-1], sol='ikSplineSolver',
        ccv=False, tws='easeInOut', pcv=False, n=name + '_ikHandle')
    # MAKE STRETCHY
    crvDUP = cmds.duplicate(crvIK, rr=True)
    crvOrig = crvIK.replace('_crv', '_orig_crv')
    cmds.rename(crvDUP[0], crvOrig)
    shape = cmds.listRelatives(crvOrig, s=True, f=True)
    shOrig = [crvOrig + 'Shape']
    cmds.rename(shape[0], shOrig[0])
    # MAKE CONTROL CURVE
    rc = cmds.createNode('rebuildCurve', n=name + '_rc')
    cmds.connectAttr(crvOrig + '.worldSpace[0]', rc + '.inputCurve')
    cmds.setAttr(rc + '.rebuildType', 0)
    cmds.setAttr(rc + '.spans', ctn)
    cmds.setAttr(rc + '.degree', 3)
    cmds.setAttr(rc + '.keepRange', 0)
    cmds.setAttr(rc + '.keepControlPoints', 0)
    cmds.setAttr(rc + '.keepEndPoints', 1)
    cmds.setAttr(rc + '.keepTangents', 1)
    crvCtrl = crvIK.replace('_crv', '_ctrl_crv')
    cmds.createNode('nurbsCurve', n=crvCtrl + 'Shape')
    cmds.connectAttr(rc + '.outputCurve', crvCtrl + '.create')
    rch = cmds.createNode('rebuildCurve', n=name + '_high_rc')
    cmds.connectAttr(crvCtrl + '.worldSpace[0]', rch + '.inputCurve')
    cmds.setAttr(rch + '.rebuildType', 0)
    cmds.setAttr(rch + '.spans', spans)
    print(spans, '*' * 100)
    cmds.setAttr(rch + '.degree', 3)
    cmds.setAttr(rch + '.keepRange', 0)
    cmds.setAttr(rch + '.keepControlPoints', 0)
    cmds.setAttr(rch + '.keepEndPoints', 1)
    cmds.setAttr(rch + '.keepTangents', 1)
    cmds.connectAttr(rch + '.outputCurve', crvIK + '.create')
    # MAKE CHAIN STRETCHY
    md = cmds.createNode('multiplyDivide', n=name + '_md')
    cmds.setAttr(md + '.operation', 2)
    cin1 = cmds.createNode('curveInfo', n=name + '_cfo')
    cin2 = cmds.createNode('curveInfo', n=name + '_orig_cfo')
    cmds.connectAttr(crvIK + '.worldSpace[0]', cin1 + '.inputCurve')
    cmds.connectAttr(crvOrig + '.worldSpace[0]', cin2 + '.inputCurve')
    cmds.connectAttr(cin1 + '.arcLength', md + '.input1X')
    cmds.connectAttr(cin2 + '.arcLength', md + '.input2X')
    for j in jnts[1:-1]:
        mdl = cmds.createNode('multDoubleLinear', n=name + '_mdl')
        cmds.connectAttr(md + '.outputX', mdl + '.input1')
        val = cmds.getAttr(j + '.tx')
        cmds.setAttr(mdl + '.input2', val)
        cmds.connectAttr(mdl + '.output', j + '.tx')
    # CLEANUP
    cmds.parent(sh[0], crvCtrl, r=True, s=True)
    cmds.setAttr(sh[0] + '.intermediateObject', 1)
    cmds.parent(shOrig[0], crvCtrl, r=True, s=True)
    cmds.setAttr(shOrig[0] + '.intermediateObject', 1)
    cmds.delete(crvIK, crvOrig)

    return crvCtrl


def makeChainCtrls(crv):
    spans = cmds.getAttr(crv + '.spans') + 2
    name = crv.replace('_ctrl_crv', '')
    grp = name + '_clusters_grp'
    if not cmds.objExists(grp):
        cmds.group(em=True, n=grp)
    for x in range(0, spans):
        if x < spans - 1:
            cmds.select(crv + '.cv[' + str(x) + ']', r=True)
        else:
            cmds.select(crv + '.cv[' + str(x) + ']', r=True)
            cmds.select(crv + '.cv[' + str(x + 1) + ']', add=True)
        clh = cmds.cluster()
        cmds.parent(clh[1], grp)
        cmds.rename(clh[1], name + '_' + str(x + 1).zfill(2) + '_clh')
        # cpc = cmds.createNode('closestPointOnCurve')
        # ctrl = cmds.circle(c=(0, 0, 0)nr=(0, 1, 0), sw=360, r=1, d=3, ut=0, tol=0.0001, s=8, ch=True)


def pipeChain(res=None, cnt=None):
    if not res:
        res = 1
    if not cnt:
        cnt = 4
    sel = cmds.ls(sl=True)
    for s in sel:
        dup = cmds.duplicate(s, rr=True)
        s = dup[0]
        sh = cmds.listRelatives(s, s=True)
        toS = cmds.polyToSubdiv(
            s, ap=0, ch=0, aut=1, maxPolyCount=32000, maxEdgesPerVert=32)
        cmds.delete(sh[0])
        sn = cmds.subdToNurbs(toS[0], ch=0, aut=1, ot=0)
        cmds.delete(toS[0])
        cur = sn[0] + '_1'
        curs = sn[0] + '_Shape1'
        u = cmds.getAttr(curs + '.spansUV')[0][0]
        v = cmds.getAttr(curs + '.spansUV')[0][1]
        grp = 'curves_TEMP'
        if not cmds.objExists(grp):
            cmds.group(em=True, n=grp)
        # MAKE JOINTS
        jnts = []
        for x in range(0, v + 1, res):
            cmds.select(cur + '.v[' + str(x) + ']', r=True)
            crv = cmds.duplicateCurve(
                cur + '.v[' + str(x) + ']', ch=0, rn=0, local=0)
            cmds.select(cl=True)
            jnt = makeJNT(crv[0], x)
            cmds.parent(jnt, grp)
            jnts.append(jnt)
            cmds.delete(crv)
        cmds.select(cl=True)
        # PARENT CHAIN
        jnts.reverse()
        for x, j in enumerate(jnts):
            if x < len(jnts) - 1:
                cmds.parent(jnts[x], jnts[x + 1])
        cmds.parent(jnts[-1], w=True)
        cmds.delete(dup, grp)
        # RENAME CHAIN
        chain = cmds.ls(jnts[-1], dag=True, type='joint')
        chain.reverse()
        jnts = []
        for x, c in enumerate(chain):
            cur = s + '_' + str(len(chain) - x).zfill(2) + '_jnt'
            cmds.rename(c, cur)
            jnts.append(cur)
        # ORIENT CHAIN
        chain = cmds.ls(s + '_01_jnt', dag=True, type='joint')
        cmds.joint(
            chain[0], e=True, oj='xyz', secondaryAxisOrient='yup', ch=True, zso=True)
        cmds.setAttr(chain[-1] + '.jointOrient', 0, 0, 0)
        grp = s + '_grp'
        if not cmds.objExists(grp):
            cmds.group(em=True, n=grp)
        cmds.delete(cmds.parentConstraint(chain[0], grp))
        cmds.parent(chain[0], grp)
        # MAKE SPLINE IK
        crvCtrl = makeSpIK(chain, cnt)
        # MAKE CONTROLLERS FOR CURVE
        makeChainCtrls(crvCtrl)
