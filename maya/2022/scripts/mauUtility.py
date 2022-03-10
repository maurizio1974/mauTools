import maya.cmds as cmds
import maya.mel as mel
import smtplib
import email
import shutil as sh
import pymel.core as pm


# MESH INTERSECT GEO CREATION
# USAGE :
#   give the procduree two mesh objects.
#   mgIntersectGeo({"terrain","palla"})

def mgIntersectGeo(surfs):
    surfS1, surfS2, mesh, toonNode = [], [], '', ''
    if not len(surfs) == 2:
        cmds.confirmDialog(t='Error', m='Need to pass two meshes')
        return
    if not cmds.objExists('Intersect_PFX'):
        toonNode = cmds.createNode('pfxToon', n='Intersect_PFX')
        cmds.setAttr(toonNode + '.displayInViewport', 0)
        cmds.setAttr(toonNode + '.creaseLines', 0)
        cmds.setAttr(toonNode + '.intersectionLines', 1)
        cmds.setAttr(toonNode + '.profileLines', 0)
        cmds.setAttr(toonNode + '.borderLines', 0)

    surfS1 = cmds.listRelatives(surfs[0], s=True)
    surfS2 = cmds.listRelatives(surfs[1], s=True)
    cmds.connectAttr(
        surfS1[0] + ".outMesh", toonNode + ".inputSurface[0].surface", f=True
    )
    cmds.connectAttr(
        surfS1[0] + ".worldMatrix[0]",
        toonNode + ".inputSurface[0].inputWorldMatrix",
        f=True
    )
    cmds.connectAttr(
        surfS2[0] + ".outMesh", toonNode + ".inputSurface[1].surface", f=True
    )
    cmds.connectAttr(
        surfS2[0] + ".worldMatrix[0]",
        toonNode + ".inputSurface[1].inputWorldMatrix",
        f=True
    )

    mesh = cmds.createNode('mesh', n='ringGeo')
    cmds.connectAttr(toonNode + '.worldMainMesh[0]', mesh + '.inMesh')


# FAST REMOVE UNUSED SKIN INFLUENCES
def rmSkinInf():
    skc = cmds.ls(type='skinCluster')
    if not skc:
        print 'No skinCLuster in the scene'
        return
    for s in skc:
        # ALL INFLUENCES
        all = cmds.skinCluster(s, q=True, inf=True)
        # ONLY INFLUENCES AFFECTING
        infs = cmds.skinCluster(s, q=True, wi=True)
        allInf = len(all)  # ALL NUMBER OF INFLUENCES
        # REMOVE NON AFFECTING INFLUENCES
        for i in infs:
            if i in all:
                all.remove(i)
        # DISCONNECT NON AFFECTING INFLUENCES
        for a in all:
            conn = cmds.listConnections(
                a + '.worldMatrix', s=False, d=True, p=True
            )
            if conn:
                for c in conn:
                    if s in c:
                        cmds.disconnectAttr(a + '.worldMatrix', c)
            conn1 = cmds.listConnections(
                a + '.objectColorRGB', s=False, d=True, p=True
            )
            if conn1:
                for c in conn1:
                    if s in c:
                        cmds.disconnectAttr(a + '.objectColorRGB', c)
            conn2 = cmds.listConnections(
                a + '.message', s=False, d=True, p=True
            )
            if conn2:
                for c in conn2:
                    if s in c:
                        cmds.disconnectAttr(a + '.message', c)
        # CHECK NUMBER OF INFLUENCES
        all = cmds.skinCluster(s, q=True, inf=True)

        print 'Old influence Number: ' + str(allInf)
        print 'New Influence Number: ' + str(len(all))


# FIND AND FIX DUPLICATE NAMES ------------------------------------------------
def mCheckDupNames():
    allNodes = cmds.ls(sl=True, dag=True, type='transform')
    stop = 0
    for a in allNodes:
        num = len(a.split('|'))
        if num > 1:
            if cmds.objExists(a):
                stop = 1
                number = len(cmds.ls(a.split('|')[-1]))
                cmds.rename(a, a.split('|')[-1] + str(number))
    if stop == 1:
        print 'Restart'
        mCheckDupNames()
    cmds.confirmDialog(
        t='Ole\'',
        m='Duplicate Names Fixed !\nTime needed: '
    )


# SWAP MAYA REFERENCES --------------------------------------------------------
def mRefSwapper_UI():
    if cmds.window('RefereceSwapWin', ex=True):
        cmds.deleteUI('RefereceSwapWin')
    win = cmds.window('RefereceSwapWin', t='Referece Swap')
    fr = cmds.formLayout()
    omc = cmds.optionMenu(l='Current')
    omn = cmds.optionMenu(l='Latest  ')
    omt = cmds.optionMenu(l='Discipline', w=100)
    omd = cmds.optionMenu(l='Type    ', w=95)
    oms = cmds.optionMenu(l='', w=70, en=False)
    print omd, oms
    bt1 = cmds.button(
        l="swap",
        c='mU.mSwapRefs(["' + omc + '","' + omn + '","' + omt + '"])'
    )
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (omc, 'left', 5), (omc, 'top', 5), (omc, 'right', 5),
            (omn, 'left', 5), (omn, 'right', 5),
            (omt, 'right', 5),
            (omd, 'left', 5),
            (bt1, 'left', 5), (bt1, 'right', 5)
        ],
        ac=[
            (omn, 'top', 5, omc),
            (omd, 'top', 5, omn),
            (oms, 'top', 5, omn),
            (oms, 'left', 5, omd),
            (omt, 'top', 5, omn),
            (omt, 'left', 5, oms),
            (bt1, 'top', 5, omt)
        ]
    )
    # ADD UI STUFF
    mRefPopulateUI([omc], mAllRef())
    mRefPopulateUI([omn], mGetProject('animation'))
    mRefPopulateUI(
        [omt, omn],
        [
            'animation', 'fx', 'groom',
            'lighting', 'model', 'rig',
            'rigFX', 'texture'
        ]
    )
    cmds.menuItem(l='Build', p=omd)
    cmds.menuItem(l='Shots', p=omd)
    cmds.optionMenu(
        omd,
        e=True,
        cc='cmds.optionMenu("' + oms + '",e=True,en=False)'
        ' if '
        'cmds.optionMenu("' + omd + '",q=True,v=True) == \'Build\''
        ' else '
        'cmds.optionMenu("' + oms + '", e=True, en=True)'
    )
    # cc='cmds.optionMenu("'+oms+'", e=True, en=True)'
    mPopulateShots(oms)
    # SHOW UI
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[300, 120])


def mRefPopulateUI(ui, items):
    if items:
        for i in items:
            if len(i.split('/')) > 1:
                mi = cmds.optionMenu(ui[0], q=True, ils=True)
                if mi:
                    for m in mi:
                        cmds.deleteUI(m)
                for i in items:
                    cmds.menuItem(l=i.split('/')[-1], p=ui[0], ann=i)
            else:
                if not cmds.optionMenu(ui[0], q=True, ils=True):
                    for i in items:
                        cmds.menuItem(l=i, p=ui[0], ann=i)
                    cmd = 'mU.mRefPopulateUI(["'+ui[1]+'"], mU.mGetProject(cmds.menuItem(cmds.optionMenu("'+ui[0]+'", q=True, ils=True)[cmds.optionMenu("'+ui[0]+'", q=True, sl=True)-1], q=True, ann=True)))'
                    cmds.optionMenu(
                        ui[0],
                        e=True,
                        cc=cmd
                    )
    else:
        mi = cmds.optionMenu(ui[0], q=True, ils=True)
        print mi
        if mi:
            for m in mi:
                cmds.deleteUI(m)


def mSwapRefs(ui):
    scene = cmds.file(q=True, sn=True)  # Scene File
    current = cmds.menuItem(
        cmds.optionMenu(
            ui[0],
            q=True,
            ils=True
        )[cmds.optionMenu(ui[0], q=True, sl=True)-1], q=True, ann=True)
    latest = cmds.menuItem(
        cmds.optionMenu(
            ui[1],
            q=True,
            ils=True
        )[cmds.optionMenu(ui[1], q=True, sl=True)-1], q=True, ann=True)

    f = file(scene, 'r')
    data = f.read()
    # sh.copyfile(scene, '/home/mau/Desktop/temp.ma')
    sh.os.system('>> /home/mau/Desktop/temp.ma')
    newdata = data.replace(current, latest)
    f = open('/home/mau/Desktop/temp.ma', 'w')
    f.write(newdata)
    f.close()
    '''
    for s in data.split('\n'):
        if current:
            if current in s:  # check is the reference is there
                print s+'  ---->  '+s.replace(current, latest)
    f.close()
    '''


def mAllRef():
    all = []
    topRef = cmds.file(q=True, r=True)
    for t in topRef:
        all.append(t)
        try:
            nestedRef = cmds.file(t, q=True, r=True)
            for n in nestedRef:
                all.append(n)
        except:
            pass
    return all


def mGetProject(discipline):
    path = '/nfs/jobs/'
    ws = cmds.workspace(q=True, act=True)
    out = ws.replace(path, '')
    path = sh.os.path.join(path + out.split('/')[0], 'build')
    assets, result = [], []
    if sh.os.path.isdir(path):
        for a in sh.os.listdir(path):
            if sh.os.path.isdir(sh.os.path.join(path, a)):
                assets.append(sh.os.path.join(path, a))
                if mGetAsset(sh.os.path.join(path, a), discipline):
                    result.append(
                        mGetAsset(sh.os.path.join(path, a), discipline)
                    )
    return result


def mPopulateShots(ui):
    path = '/nfs/jobs/'
    ws = cmds.workspace(q=True, act=True)
    out = ws.replace(path, '')
    path = sh.os.path.join(path + out.split('/')[0], 'shots')
    assets = []
    if sh.os.path.isdir(path):
        for a in sh.os.listdir(path):
            if sh.os.path.isdir(sh.os.path.join(path, a)):
                assets.append(sh.os.path.join(path, a))
    for a in assets:
        cmds.menuItem(l=a.split('/')[-1], p=ui, ann=a)


def mGetAsset(path, discipline):
    models, mod = [], ''
    path = sh.os.path.join(path, discipline, 'scenes/releases')
    if sh.os.path.isdir(path):
        sa = sh.os.listdir(path)
        for aa in sa:
            if '.ma' in aa and aa != '.mayaSwatches':
                models.append(sh.os.path.join(path, aa))
    # print models
    mod = [(sh.os.path.getmtime(x), x) for x in models]
    mod.sort()
    # latest = [mod[-1][1], mod[-2][1], mod[-3][1]]
    if len(mod) > 0:
        # print mod
        return mod[-1][1]


# INVERT DEFORMER WEIGHTS -----------------------------------------------------
def prMau(deformer):
    if cmds.window('invWeightWin', ex=True):
        cmds.deleteUI('invWeightWin')
    win = cmds.window('invWeightWin', t='inverWeights')
    fr = cmds.formLayout()
    tf = cmds.textField(tx=deformer, w=140)
    itf = cmds.intField(en=False)
    bt = cmds.button(l='invert', en=False)
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (tf, 'left', 5), (tf, 'top', 5),
            (bt, 'left', 5), (bt, 'right', 5), (bt, 'top', 5),
            (itf, 'right', 5), (itf, 'top', 5)
        ],
        ac=[
            (bt, 'top', 5, tf),
            (itf, 'left', 5, tf)
        ]
    )
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[175, 60])

    # UI COMMANDS
    if deformer == 'cluster':
        cmds.button(
            bt,
            e=True,
            c='mU.invCL(cmds.textField("' + tf + '", q=True, tx=True))'
        )
    elif deformer == 'blendShape':
        cmds.button(
            bt,
            e=True,
            c='mU.invBS('
            'cmds.textField("' + tf + '", q=True, tx=True),'
            'cmds.intField("' + itf + '", q=True, v=True))'
        )
    # PRESETS
    deformers = cmds.ls(type=deformer)
    if deformers:
        pp = cmds.popupMenu('deformerPP', p=tf)
        for df in deformers:
            if cmds.nodeType(df) == 'blendShape':
                cmds.menuItem(
                    l=df,
                    p=pp,
                    c='cmds.textField("' + tf + '", e=True, tx="' + df + '");'
                    'cmds.intField("' + itf + '", e=True, en=True);'
                    'cmds.button("' + bt + '", e=True, en=True)'
                )
            elif cmds.nodeType(df) == 'cluster':
                cmds.menuItem(
                    l=df,
                    p=pp,
                    c='cmds.textField("{0}", e=True, tx="{1}");'
                    'cmds.button("{2}", e=True, en=True)'.format(tf, df, bt)
                )
    pp1 = cmds.popupMenu('deformerPP', p=itf)
    for x in range(10):
        cmds.menuItem(
            l=x,
            p=pp1,
            c='cmds.intField("' + itf + '", e=True, v=' + str(x) + ');'
        )


def invBS(bs, index):
    index = str(index)
    vtxs, inv = [], []
    attr = [
        bs,
        'inputTarget[0]',
        'inputTargetGroup[' + index + ']',
        'targetWeights'
    ]
    if not cmds.nodeType(bs) == 'blendShape':
        cmds.confirmDialog(
            t='error',
            m='{0} is not a BlendShape'.format(bs)
        )
        return
    bIN = cmds.getAttr('.'.join(attr))[0]
    vb = cmds.listAttr('.'.join(attr), multi=True)
    tg = cmds.blendShape(bs, q=True, t=True)
    vCount = cmds.polyEvaluate(tg[0], v=True)
    if vb:
        for v in vb:
            ind = v.split('.')[-1].split('[')[1].split(']')[0]
            vtxs.append(int(ind))
    for x in range(vCount):
        inv.append(x)
    if len(vtxs) > 0:
        inv = [x for x in inv if x not in vtxs]
    for x in range(len(bIN)):
        value = 1 - bIN[x]
        cmds.setAttr('.'.join(attr) + '[' + str(vtxs[x]) + ']', value)
    for x in inv:
        cmds.setAttr('.'.join(attr) + '[' + str(x) + ']', 0)


def invCL(cl):
    vtxs, inv, cIN = [], [], []
    attr = [
        cl,
        'weightList[0]',
        'weights'
    ]
    if not cmds.nodeType(cl) == 'cluster':
        cmds.confirmDialog(
            t='error',
            m='{0} is no a Cluster'.format(cl)
        )
        return
    try:
        cIN = cmds.getAttr('.'.join(attr))[0]
        vc = cmds.listAttr('.'.join(attr), multi=True)
        if vc:
            for v in vc:
                ind = v.split('.')[-1].split('[')[1].split(']')[0]
                vtxs.append(int(ind))
    except:
        pass
    tg = cmds.cluster(cl, q=True, g=True)
    vCount = cmds.polyEvaluate(tg[0], v=True)
    for x in range(vCount):
        inv.append(x)
    if len(vtxs) > 0:
        inv = [x for x in inv if x not in vtxs]
    if len(cIN) > 0:
        for x in range(len(cIN)):
            value = 1 - cIN[x]
            cmds.setAttr('.'.join(attr) + '[' + str(vtxs[x]) + ']', value)
    for x in inv:
        cmds.setAttr('.'.join(attr) + '[' + str(x) + ']', 0)

# MIMMO WRAP -----------------------------------------------------------------
def mauWrap():
    wrapping = []
    sel = cmds.ls(sl=True)
    if not len(sel) > 1:
        cmds.confirmDialog(t='WTF !', m='Select at least two objects')
        return
    cmds.select(cl=True)
    for s in sel:
        if s is not sel[-1]:
            wrapping.append(s)
    cmds.select(wrapping, sel[-1])
    wrap = mel.eval(
        'doWrapArgList "7" { "1","0","1", "2", "1", "1", "0", "0" }'
    )
    for w in wrap:
        cmds.addAttr(w, ln='mWrap', at='message')
        cmds.connectAttr(sel[-1] + '.message', w + '.mWrap', f=True)
    cmds.select(sel)
    return wrap

def mGetWrap():
    sel = cmds.ls(sl=True)
    node = ''
    if not sel:
        cmds.confirmDialog(t='WTF !', m='Select sopmething')
        return
    for s in sel:
        history = cmds.listHistory()
        for h in history:
            if cmds.attributeQuery('mWrap', n=h, ex=True):
                node = cmds.listConnections(h + '.mWrap', s=True, d=False)
                print h, node[0]
    if node:
        cmds.select(node)
    else:
        cmds.warning('No mimmo Wrap on the selected mesh')

def nurbJoint(object, surf):
    pos = cmds.xform(object, q=True, ws=True, t=True)
    cps = cmds.createNode('closestPointOnSurface', n=surf[0] + '_CPS')
    sh = cmds.listRelatives(surf, s=True)
    cmds.connectAttr(sh[0] + '.worldSpace', cps + '.inputSurface')
    loc = [object]
    locC = cmds.spaceLocator(n=object + '_ctrl_S')
    cmds.setAttr(locC[0] + '.v', 0)
    locS = cmds.listRelatives(locC[0], s=True)
    cmds.setAttr(locS[0] + '.localScale', 0.1, 0.1, 0.1)
    grpH = cmds.group(em=True, n=object + '_null_SS')
    cmds.parent(locC[0], grpH)
    cmds.setAttr(loc[0] + '.t', pos[0], pos[1], pos[2])
    cmds.setAttr(loc[0] + '.v', 0)
    cmds.setAttr(grpH + '.t', pos[0], pos[1], pos[2])
    cmds.parentConstraint(locC[0], loc[0])
    cmds.connectAttr(loc[0] + '.t', cps + '.inPosition')
    j = cmds.joint(n=object + '_JNT')
    grp = cmds.group(em=True, n=object + '_jnt_SS')
    cmds.connectAttr(cps + '.position', grp + '.translate')
    cmds.normalConstraint(sh[0], grp)
    cmds.parent(j, grp)
    cmds.setAttr(j + '.t', 0, 0, 0)
    cmds.setAttr(j + '.r', 0, 0, 0)
    cmds.setAttr(j + '.jointOrient', 0, 0, 0)
    cmds.setAttr(j + '.radius', 0.5)
    cmds.select(cl=True)
    return[object, grpH, locC[0], j, grp]

def renderViewBatch(start, end):
    destination = 10
    for i in range(start, end, destination):
        cmds.currentTime(i)
        btPath = cmds.file(query=True, location=True)
        fileName = sh.os.path.basename(btPath)
        cleanName = fileName.rsplit('.ma')
        name = cleanName[0] + '.' + str(i)
        btInput = destination
        mel.eval('renderWindowRenderCamera render renderView Camera01')
        cmds.setAttr('defaultRenderGlobals.imageFormat', 8)
        editor = 'renderView'
        cmds.renderWindowEditor(
            editor,
            e=True,
            writeImage=btInput + name + '.jpg'
        )
        cmds.setAttr('defaultRenderGlobals.imageFormat', 51)
        cmds.currentTime(i + 1)

# MIMMO ATTRIBUTE STORE ------------------------------------------------------
def mStoreAttr(ns):
    cmd, node = '', ''
    sel = cmds.ls(sl=1, long=1)
    tipo = ''
    for s in sel:
        attr = cmds.listAttr(s, k=True)
        for a in attr:
            try:
                tipo = cmds.getAttr(s + '.' + a, type=1)
            except Exception:
                pass
            conditions = [
                tipo,
                'TdataCompound' not in tipo,
                'double3' not in tipo,
                'float3' not in tipo
            ]
            if all(conditions):  # check for unwanted types
                print a + '  ' + tipo
                value = cmds.getAttr(s + '.' + a)
                conditions = [
                    not cmds.listConnections(s + '.' + a, s=1, d=0),
                    not cmds.getAttr(s + '.' + a, l=True)
                ]
                if all(conditions):  # Check Connections and lock state
                    if ns is 1:  # with nameSpace
                        node = s + '.' + a
                    elif ns is 0:  # without nameSpace
                        nsp = s.split(':')[0].replace('|', '')
                        node = s.replace(nsp + ':', '')
                    if tipo in 'string':
                        cmd += (
                            'cmds.setAttr("{0}.{1}", "{2}", type="{3}")\n'
                        ).format(node, a, str(value), tipo)
                    else:
                        cmd += (
                            'cmds.setAttr("{0}.{1}", {2})\n'
                        ).format(node, a, str(value))

    # save temp file of the command to be executed
    sh.os.system('>> /tmp/mStoreTemp')
    f = file('/tmp/mStoreTemp', 'w')
    f.write(cmd)
    f.close()

def mGetAttr():
    f = file('/tmp/mStoreTemp', 'r')
    info = f.read()
    f.close()
    temp = info.split('\n')
    for t in temp:
        exec t
        print 'done this: ' + t
    print 'Attrubute transfered'

def mBrowser(mode):
    filter = "Maya ASCII (*.ma);;Maya Binary (*.mb)"
    r = cmds.fileDialog2(
        ff=filter,
        cap='cacheScene',
        dir="data/",
        fm=mode,
        ds=True
    )
    out = r[0]
    return out

def mEmail(subject, body):
    msg = email.mime.Multipart.MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = 'maurizio1974@gmail.com'
    msg['To'] = 'maurizio1974@gmail.com'
    msg.attach(email.mime.Text.MIMEText(body))
    password = raw_input()

    s = smtplib.SMTP('smtp.gmail.com:587')
    s.starttls()
    s.login(msg['From'], password)
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()

def mProjects():
    if pm.menu('mauProjectsMenu', ex=True):
        pm.deleteUI('mauProjectsMenu')
    mMenu = pm.menu('mimmoProjectsMenu', l="@Mau Prjs", p='MayaWindow')
    disciplines = [
        'fx',
        'rigFX',
        'lighting',
        'texture',
        'rig',
        'model',
        'groom',
        'animation'
    ]
    path = '/nfs/jobs/'
    jobs = sh.os.listdir(path)
    for j in jobs:
        if not sh.os.path.isdir(path + j):
            return
        base = sh.os.listdir(path + j)
        for b in base:
            if b not in 'build':
                return
            prjItem = cmds.menuItem(
                j + 'menuItem',
                subMenu=True,
                tearOff=True,
                l=j,
                p=mMenu
            )
            assets = sh.os.listdir(path + j + '/' + b)
            for a in assets:
                if not sh.os.path.isdir(path + j + '/' + b + '/' + a):
                    return
                disci = sh.os.listdir(path + j + '/' + b + '/' + a)
                for d in disci:
                    for dd in disciplines:
                        if d != dd:
                            return
                        if cmds.menuItem(j, ex=True):
                            return
                        path = path + j + '/' + b + '/' + a + '/' + d
                        cmd = 'mel.eval(\'setProject "' + path + '"\')'
                        cmds.menuItem(p=prjItem, c=cmd, l=a + '_' + d)

# MIRROR CONTROLLERS SHAPES
def mirrorCtrl(dir):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.confirmDialog(t='eror', m='plase select a nurbCurve Shape')
        return
    for s in sel:
        if not cmds.nodeType(s) == 'nurbsCurve':
            cmds.confirmDialog(t='Selection Error', m='Please select the shape you want to missor not the transform')
            return
        sh = s
        # sh = cmds.listRelatives(s, s=True)[0]
        # if not sh:
        #     cmds.confirmDialog(t='eror', m='plase select a nurb shape transform')
        #     return
        # if cmds.nodeType(sh) != 'nurbsCurve':
        #     cmds.confirmDialog(t='eror', m='plase select a nurb shape transform')
        #     return
        # GET DIRECTION
        shN = sh
        if 'L' in sh:
            shN = sh.replace('L', 'R')
        elif 'R' in sh:
            shN = sh.replace('R', 'L')
        if not cmds.objExists(shN):
            cmds.confirmDialog(t='eror', m='This shape doesn\'t exists ' + shN + '\nMake sure to have prefix on your selections L or R')
            return
        # GET CURVE POINTS INFORMATION
        spans = cmds.getAttr(sh + '.spans')
        for x in xrange(0, spans):
            pos = cmds.pointPosition(sh + '.cv[' + str(x) + ']')
            # xp = cmds.getAttr(sh + '.controlPoints[' + str(x) + '].xValue')
            # yp = cmds.getAttr(sh + '.controlPoints[' + str(x) + '].yValue')
            # zp = cmds.getAttr(sh + '.controlPoints[' + str(x) + '].zValue')
            # pos = [xp, yp, zp]
            if dir == 'x':
                pos = [pos[0] * -1, pos[1], pos[2]]
            elif dir == 'y':
                pos = [pos[0], pos[1] * -1, pos[2]]
            elif dir == 'z':
                pos = [pos[0], pos[1], pos[2] * -1]
            # loc = cmds.spaceLocator()
            # cmds.move(pos[0], pos[1], pos[2], loc[0], absolute=True)
            # cmds.move(pos[0], pos[1], pos[2], shN + '.cv[' + str(x) + ']', absolute=True)
            cmds.xform(shN + '.cv[' + str(x) + ']', ws=True, t=(pos[0], pos[1], pos[2]))
            # cmds.setAttr(shN + '.controlPoints[' + str(x) + '].xValue', pos[0])
            # cmds.setAttr(shN + '.controlPoints[' + str(x) + '].yValue', pos[1])
            # cmds.setAttr(shN + '.controlPoints[' + str(x) + '].zValue', pos[2])
            # print pos


'''
LAYOUT STUFF
layout = cmds.panelConfiguration(l='tempLayout', sc=0)
mel.eval('updatePanelLayoutFromCurrent "tempLayout"')
mel.eval('setNamedPanelLayout "Single Perspective View"')
perspPane=cmds.getPanel(vis=1)
cmds.scriptedPanel('graphEditor1',e=1,rp=perspPane[0])
mel.eval('setNamedPanelLayout "tempLayout"')
killMe = cmds.getPanel(cwl='tempLayout')
cmds.deleteUI(killMe,pc=1)


def makeHiddenLayout(name):
    # store a temporary panel configuration.
    layout = cmds.panelConfiguration(l=name, sc=0)
    evalStr = 'updatePanelLayoutFromCurrent "'+name+'"'
    mel.eval(evalStr)
    # switch to fast "hidden" layout
    evalStr = 'setNamedPanelLayout "Single Perspective View"'
    mel.eval(evalStr)
    perspPane = cmds.getPanel(vis=1)
    cmds.scriptedPanel('graphEditor1',e=1,rp=perspPane[0])
    return name


def restoreLayout(name):
    # restore the layout returned from makeHiddenLayout.
    evalStr = 'setNamedPanelLayout "'+name+'"'
    mel.eval(evalStr)
    # now delete the old layout.
    killMe = cmds.getPanel(cwl=name)
    cmds.deleteUI(killMe,pc=1)


makeHiddenLayout('tempLayout')
try:
    runSomeBakingMethod()
    maybeSomeOtherMethodHere()
finally:
    restoreLayout('tempLayout')


'''
