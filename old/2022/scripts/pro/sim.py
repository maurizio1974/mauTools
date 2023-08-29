'''----------------------------------------------------------------------

MIMMO SIM UTILITY

Date = 16-05-2014
User = Maurizio Giglioli
Update =
    (15-05-2015)
    Added multiple yeti node sim
    (02-05-2014)
    Added the ability to simulate in maya directly
    (10-12-2014)
    Added prefix choice to the connection utility and UI
    (06-10-2014)
    Unified all the UI under main fx tool
    (27-09-2014)
    Added simshell for Yeti
    (17-09-2014)
    Now the sim tools saved in the right directory structure inside scenes
    (05-09-2014)
    Added a simPose script
    Added simConnect tool
    (28-08-2014)
    mWrapOut handles also transform only geometry
    (90-06-2014)
    mWrapOut has been replaced with UI version and shell execution
    (18-06-2014)
    mSimulate doesn't need the nucleus in the UI anymore
    (06-04-2014)
    mSimulate has multiple windows instance available
    and added preset for nucleus in the scenes
    (24-05-2014)
    Added presets for simUI and error checking
    and saved scene set with end frame on playback range
    (20-05-2014)
    Added nCloth standalone sim tool
    (17-05-2014)
    Added argument to pick the per frame evaluation
    of the cache to the geometry cacher
    Added frame range input to the geometry cacher

----------------------------------------------------------------------'''
import maya.cmds as cmds
import maya.mel as mel
import shutil as sh
import os



def dampTemp(tempFile):
    tmpDir = os.getenv('TEMP')
    log = os.path.join(tmpDir, 'cacheTemp_' + tempFile)
    os.system('>> ' + log)
    f = file(log, 'w')
    # sh.os.system('>> /tmp/cacheTemp_' + tempFile)
    # f = file('/tmp/simTemp_' + tempFile, 'w')
    f.write(cmd)
    f.close()


def mayaWrapOut(evaluate, start, end, clean, mode):
    ref = cmds.ls(type='reference')
    # everything = cmds.ls(l = True)
    # nondeletable = cmds.ls(ud = True)
    # clean = [x for x in everything if not x in nondeletable]
    # clean = [x for x in clean if not x in ref]
    wraps, geos, graph = [], [], ['{', '}']
    sel = cmds.ls(sl=True)
    rig = cmds.group(em=True, n='geo_chaged_GRP')
    grp = cmds.group(em=True, n='base_temp_GRP')
    cmds.select(cl=True)
    for s in sel:
        mesh = cmds.duplicate(s)
        cmds.parent(mesh[0], rig)
        cmds.select(mesh[0], s)
        wrap = mel.eval(
            'doWrapArgList "7" {"1", "0", "1", "2", "1", "1", "0", "0"}'
        )
        cmds.parent(s + 'Base', grp)
        wraps.append(wrap[0])
        geos.append(mesh[0])
    # Make Geomatry Cache
    cmds.select(cl=True)
    cmds.select(geos)
    cmd = (
        'doCreateGeometryCache 6 {4}'
        '"3","{0}","{1}","OneFilePerFrame",'
        '"1","","0","{2}","0","add","0","{3}",'
        '"1","0","1","mcc","0" {5}'
    ).format(start, end, geos[0], evaluate, graph[0], graph[1])
    mel.eval(cmd)
    cmds.delete(wraps, grp)
    if clean == 1:
        if ref:
            for r in ref:
                if 'RN' in r:
                    try:
                        loc = cmds.referenceQuery(r, f=True)
                        cmds.file(loc, rr=True)
                    except:
                        print 'Skipping ' + r
    cmds.select(cl=True)


def alembicWrapOut(evaluate, start, end, scene, mode):
    geos = ''
    aScene = scene.replace('scenes', 'cache/alembic')
    aScene = aScene.replace('.ma', '.abc')
    aScene = aScene.replace('.mb', '.abc')
    # everything = cmds.ls(l=True)
    # nondeletable = cmds.ls(ud=True)
    # clean = [x for x in everything if not x in nondeletable]
    sel = cmds.ls(sl=True, l=True)
    for s in sel:
        geos += ' -root ' + s
    # Make Alembic Cache
    cmd = (
        'AbcExport -j "'
        '-frameRange {0} {1} -step {2} '
        '-ro -stripNamespaces -uvWrite '
        '-worldSpace{3} '
        '-file {4}";'
    ).format(start, end, evaluate, geos, aScene)
    mel.eval(cmd)
    # cmds.delete(clean)
    mel.eval(
        'AbcImport -mode import "{0}"'.format(aScene)
    )
    cmds.select(cl=True)


def cacheOut(cacheMesh, evaluate, start, end, settings, type, mode, clean):
    newScene, newSceneN, cmd = '', '', ''
    if not cacheMesh:
        cmds.confirmDialog(t='Not Kick Ass', m='Need some meshes in the UI')
        return
    # check the settings field for the scene name
    if not len(settings) > 0:
        cmds.confirmDialog(t='Not Kick Ass', m='Need info in the Setting UI')
        return
    if not len(cacheMesh[0].split(':')) > 1:
        cmds.confirmDialog(
            t='Not Kick Ass',
            m='You can only work with meshes that have namespace')
        return
    # scene Path
    scene = cmds.file(q=True, sn=True)
    # scene name
    sceneN = cmds.file(q=True, sn=True, shn=True)
    # active directory
    ws = cmds.workspace(q=True, act=True)
    if '.ma' in sceneN:
        newScene = scene.replace('.ma', '_' + str(settings) + '.ma')
        newSceneN = sceneN.replace('.ma', '_' + str(settings) + '.ma')
    elif '.mb' in sceneN:
        newScene = scene.replace('.mb', '_' + str(settings) + '.mb')
        newSceneN = sceneN.replace('.mb', '_' + str(settings) + '.mb')
    # create the command to send to the shell
    # 'source "/nfs/dev/data/config/linux_envs/envs.sh";'
    if not mode:
        cmd = r'/usr/autodesk/maya2014-x64/bin/maya '
        cmd += r'-batch -file {0} -c "'.format(scene)
        cmd += r'python(\"import fx.tools as sim;reload(sim)\");'
    else:
        cmd = 'mel.eval("'
    cmd += (
        r'setProject \"{0}\";'
        r'file -rename \"{1}\";'
        r'select '
    ).format(ws, newScene)
    for m in cacheMesh:
        cmd += m + ' '
    cmd += ';float $startTime = `timerX`;'
    if type == 1:
        cmd += (
            r'python(\"sim.mayaWrapOut({0}, {1}, {2}, {3}, {4})\");'
        ).format(evaluate, start, end, clean, mode)
    elif type == 2:
        cmd += (
            r'python(\"sim.alembicWrapOut('
            r'{0}, {1}, '
            r'{2}, \\\"{3}\\\", {4})\");'
        ).format(evaluate, start, end, scene, mode)
    cmd += (
        r'currentTime {0};'
        r'playbackOptions -min {0};'
        r'playbackOptions -max {1};'
    ).format(start, end)
    if not mode:
        cmd += (
            r'print(\"Full cache time :   \"'
            r'+((`timerX -startTime $startTime`)+\"'
            r'sec ( \"+(`timerX -startTime $startTime`)/60)+\" min )\n\");'
            r'file -save -type \"mayaAscii\";"'
        )
        # save temp file of the command executed
        tempFile = newSceneN.replace('.ma', '.mel').replace('.mb', '.mel')
        # dampTemp(tempFile)

        # Shoot the command out to the shell
        title = 'Shell Cache: ' + newSceneN + ' ' + str(start) + ':' + str(end)
        sh.os.system(
            'gnome-terminal -t \'' + title + '\' -e \'' + cmd + '\' &'
        )
    else:
        cmd += '")'
        exec cmd
        print cmd


def sim(simMesh, evaluate, start, end, settings, mode):
    newScene, newSceneN, brakets, fileT = '', '', ['{', '}'], ''
    nSolvers = cmds.ls(type='nucleus')
    # scene Path
    scene = cmds.file(q=True, sn=True)
    # scene name
    sceneN = cmds.file(q=True, sn=True, shn=True)
    # active directory
    ws = cmds.workspace(q=True, act=True)
    # some UI checks
    if not simMesh:
        cmds.confirmDialog(t='Not Kick Ass', m='Need some meshes in the UI')
        return
    # check the settings field for the scene name
    if not len(settings) > 0:
        cmds.confirmDialog(t='Not Kick Ass', m='Need info in the Setting UI')
        return
    # New maya scene name
    if '.ma' in sceneN:
        newScene = scene.replace('.ma', '_' + str(settings) + '.ma')
        newSceneN = sceneN.replace('.ma', '_' + str(settings) + '.ma')
        fileT = 'mayaAscii'
    elif '.mb' in sceneN:
        newScene = scene.replace('.mb', '_' + str(settings) + '.mb')
        newSceneN = sceneN.replace('.mb', '_' + str(settings) + '.mb')
        fileT = 'mayaBinary'
    # create the command to send to the shell
    if not mode:
        cmd = '/usr/autodesk/maya2014-x64/bin/maya -batch '
        cmd += '-file ' + scene + ' -c "'
        cmd += r'setProject \"{0}\";'.format(ws)
        cmd += 'select '
    else:
        cmd = 'mel.eval("select '
    for m in simMesh:
        cmd += '{0} '.format(m)
    for n in nSolvers:
        cmd += r';setAttr (\"{0}.timingOutput\") 1'.format(n)
    cmd += (
        r';file -rename \"{0}\";'
        r'$startTime = `timerX`;'
    ).format(newScene)

    # cmd += (
    #     r'doCreateNclothCache 5 {3} \"3\", \"{0}\", \"{1}\", '
    #     r'\"OneFilePerFrame\", \"1\", \"\", \"0\", \"\", \"0\", \"add\", '
    #     r'\"0\", \"{2}\", \"1\", \"0\", \"1\", \"mcc\" {4};'
    #     r'currentTime {0};'
    #     r'playbackOptions -max {1};'
    #     ).format(start, end, evaluate, brakets[0], brakets[1])

    cmd += (
        r'doCreateNclothCache 5 {3} \"3\", \"{0}\", \"{1}\", '
        r'\"OneFile\", \"1\", \"\", \"0\", \"\", \"0\", \"add\", '
        r'\"0\", \"{2}\", \"1\", \"0\", \"1\", \"mcx\" {4};'
        r'currentTime {0};'
        r'playbackOptions -max {1};'
    ).format(start, end, evaluate, brakets[0], brakets[1])

    if not mode:
        cmd += (
            r'print(\"Full sim time :   '
            r'\"+((`timerX -startTime $startTime`)+\" sec '
            r'( \"+(`timerX -startTime $startTime`)/60)+\" min )\n\");'
        )
    cmd += r'file -save -type \"{0}\";"'.format(fileT)

    if not mode:
        # save temp file of the command executed
        tempFile = newSceneN.replace('.ma', '.mel').replace('.mb', '.mel')
        # dampTemp(tempFile)

        # Shoot the command out to the shell
        title = newSceneN + ' ' + str(start) + ':' + str(end)
        sh.os.system(
            'gnome-terminal -t \'Shell Sim: ' + title + '\' -e \'' + cmd + '\' &'
        )
    else:
        cmd += ')'
        exec cmd


def yetiSim(yetiN, samples, start, end, settings, preview, mode):
    newScene, newSceneN, cmd = '', '', ''
    # SCENE PATH
    scene = cmds.file(q=True, sn=True)
    # SCENE NAME
    sceneN = cmds.file(q=True, sn=True, shn=True)
    # ACTIVE WORKSPACE
    ws = cmds.workspace(q=True, act=True)
    # NEW MAYA SCENE NAME
    if '.ma' in sceneN:
        newScene = scene.replace('.ma', '_' + str(settings) + '.ma')
        newSceneN = sceneN.replace('.ma', '_' + str(settings) + '.ma')
    elif '.mb' in sceneN:
        newSceneN = sceneN.replace('.mb', '_' + str(settings) + '.mb')
        newScene = scene.replace('.mb', '_' + str(settings) + '.mb')
    # UI CHECK
    if not yetiN[0]:
        cmds.confirmDialog(t='Not Kick Ass', m='Need Yeti nodes in the UI')
        return
    if cmds.nodeType(cmds.listRelatives(yetiN[0], s=True)[0]) != 'pgYetiMaya':
        cmds.confirmDialog(t='Not Kick Ass', m='Need a Yeti Node')
        return
    if not len(settings) > 0:
        cmds.confirmDialog(t='Not Kick Ass', m='Need info in the Setting UI')
        return
    # YETI PREVIEW CACHE CHECK
    if preview:
        preview = 1
    else:
        preview = 0
    yeticmd = ''
    for y in yetiN:
        # YETI SHAPE NODE
        yS = cmds.listRelatives(y, s=True)
        # CACHE NAME
        nameNNS = y.split(':')[-1]
        cache = sh.os.path.join(
            ws,
            'cache/yeti/' + newSceneN.split('.')[0] + '/' + nameNNS + '/' + nameNNS
        )
        cache = cache + '.%04d.fur'
        cachePath = ''
        for a in cache.split('/')[0:-1]:
            cachePath += a + '/'
        if not sh.os.path.exists(cachePath):  # MAKE DIRECTORIES
            sh.os.makedirs(cachePath)
        yeticmd += (
            r'setAttr (\"' + yS[0] + '.fileMode\\") 0;'
            r'setAttr (\"' + yS[0] + '.cacheFileName\\") '
            r'-type \"string\" \"' + cache + '\\";'
            r'pgYetiCommand -writeCache \"' + cache + '\\" '
            r'-generatePreview ' + str(preview) + ' '
            r'-range ' + str(start) + ' ' + str(end) + ' '
            r'-samples ' + str(samples) + ' \\"' + yS[0] + '\\";'
            r'setAttr (\"' + yS[0] + '.fileMode\\") 2;'
        )

    # CREATE NEW COMMAND TO SEND TO SHELL
    if not mode:
        cmd = r'/usr/autodesk/maya2014-x64/bin/maya -batch -file {0} -c '.format(scene)
    else:
        cmd = 'mel.eval('
    cmd += (
        r'"setProject \"{0}\";'
        r'file -rename \"{1}\";'
        r'{2}'
        r'file -save -type \"mayaAscii\";"'
    ).format(ws, newScene, yeticmd)
    if not mode:
        # DAMP TEMP FILE OF THE COMMAND EXECUTED
        tempFile = newSceneN.replace('.ma', '.mel').replace('.mb', '.mel')
        # dampTemp(tempFile)

        # SHOOT THE COMMAND OUT TO THE SHELL
        title = 'Shell Yeti: ' + newSceneN + ' ' + str(start) + ':' + str(end)
        sh.os.system(
            'gnome-terminal -t \'' + title + '\' -e \'' + cmd + '\' &'
        )
    else:
        cmd += ')'
        exec cmd


def simConnect(ns, sel, uno, due):
    ns[0] = ns[0] + ':'
    ns[1] = ns[1].split(':')[0] + ':'
    # CHECK UI
    if not sel:
        cmds.confirmDialog(l='Error', m='No Meshes added in the UI')
        return
    # CHECK NAMESPACE
    if not ns[1]:
        cmds.confirmDialog(l='Error', m='Need nameSpace on the fx meshes')
        return
    # START CONNECTION
    for s in sel:
        sh = cmds.listRelatives(s, s=True, ni=True)
        current = sh[0].replace(ns[1], ns[0]).rsplit(uno, 1)[0] + due
        if cmds.attributeQuery('res', n=s, ex=True):
            if cmds.attributeQuery('res', n=current, ex=True):
                try:
                    cmds.connectAttr(current + '.res', s + '.res')
                    print 'Resolution: ' + current + '.res  --->>>  ' + s + '.res'
                except StandardError:
                    print 'Res attribute missing on this node: ' + current
        if cmds.objExists(current):
            obj1 = current
            obj2 = sh[0]
            if cmds.listHistory(obj1, ac=True, lv=1, pdo=True):
                attrO = 'worldMesh[0]'
                attrI = 'inMesh'
                if cmds.nodeType(sh[0]) == 'nurbsCurve':
                    attrO = 'worldSpace[0]'
                    attrI = 'create'
                bs = current + '_BS'
                if not cmds.objExists(bs):
                    cmds.blendShape(obj1, obj2, origin='world', w=(0, 1), n=current + '_BS')
                print 'BlendShape:  {0} --> {1}'.format(obj1, obj2)
                # cmds.connectAttr(obj1 + '.' + attrO, obj2 + '.' + attrI, f=True)
                # print 'Direct: {0} --> {1}'.format(obj1 + '.' + attrO, obj2 + '.' + attrI)
            else:
                cmds.blendShape(obj1, obj2, origin='world', w=(0, 1))
                print 'BlendShape:  {0} --> {1}'.format(obj1, obj2)
        else:
            obj1 = current
            print 'Skipping {0}, because it is not in the scene.'.format(obj1)


def simPose(topNode, lenght, still, ext, eAttr=None):
    start = cmds.timerX()
    sf = cmds.playbackOptions(q=True, min=True)
    ns, attrs = '', []
    if eAttr:
        for ea in eAttr:
            attrs.append(ea)
    # GET THE NAME SPACE
    for t in topNode.split(':')[0:-1]:
        ns += t + ':'
    # CHECK IF THE ANIM LAYER simPose EXIST
    if not cmds.animLayer(ns + "simPose", q=True, ex=True):
        cmds.animLayer(ns + "simPose", m=False, s=False, o=False, l=False)
    # UNLOCK ALL ANIM LAYERS
    an = cmds.ls(typ='animLayer')
    for a in an:
        cmds.animLayer(a, e=True, l=False)
    # ADD ALL THE CONTROLS TO THE SIMPOSE LAYER
    for e in ext:
        ctrls = cmds.ls(ns + '*' + e)
        for c in ctrls:
            attOut = []
            attrR = cmds.listAttr(c, k=True)
            # CHECK WHICH CHANNEL HAS ANIMATION
            if attrR:
                for ar in attrR:
                    if cmds.listConnections(c + '.' + ar, s=True, d=False):
                        attOut.append(ar)
            for ao in attOut:
                conditions = [
                    ao != 'visibility',
                    ao != 'scaleX',
                    ao != 'scaleY',
                    ao != 'scaleZ'
                ]
                if all(conditions):
                    cmds.animLayer(ns + 'simPose', e=True, at=c + '.' + ao)
            cmds.currentTime(sf)
            # CREATE THE SIMPOSE ANIMATION
            if 'global' + e not in c:
                for a in attOut:
                    conditions = [
                        a != 'visibility',
                        a != 'scaleX',
                        a != 'scaleY',
                        a != 'scaleZ'
                    ]
                    if all(conditions):
                        cv = cmds.getAttr(c + '.' + a)
                        cmds.setKeyframe(
                            c, al=ns + 'simPose', at=a, t=int(sf), v=cv
                        )
                        cmds.setKeyframe(
                            c, al=ns + 'simPose', at=a, t=int(sf) - still, v=cv
                        )
                        cmds.setKeyframe(
                            c, al=ns + 'simPose', at=a, t=int(sf) - lenght, v=0
                        )
    # LOCK ANIM LAYERS
    an = cmds.ls(typ='animLayer')
    for a in an:
        cmds.animLayer(a, e=True, l=True)
    print 'Simpose done for ' + topNode + ' in ' + str(cmds.timerX(startTime=start))


def simpleSimPose(node, lenght, still):
    sf = cmds.playbackOptions(q=True, min=True)
    attrs = cmds.listAttr(node, k=True)
    if attrs:
        for a in attrs:
            attrs.append(a)
    # CHECK IF THE ANIM LAYER CALLED simPose ALREADY EXIST OTHERWISE MAKE IT
    if not cmds.animLayer("simPose", q=True, ex=True):
        cmds.animLayer("simPose", m=False, s=False, o=False, l=False)
    # UNLOCK ALL ANIM LAYERS
    an = cmds.ls(typ='animLayer')
    if an:
        for a in an:
            cmds.animLayer(a, e=True, l=False)
    # ADD ALL THE CONTROLS TO THE SIMPOSE LAYER
    cmds.select(node, r=True)
    cmds.animLayer(
        'simPose',
        e=True,
        aso=True,
        esc=True,
        evs=True,
        edn=True,
        een=True,
        ebl=True
    )
    # CREATE THE SIMPOSE ANIMATION
    cmds.currentTime(sf)
    for a in attrs:
        cmds.animLayer('simPose', e=True, at=node + '.' + a)
        cv = cmds.getAttr(node + '.' + a)
        cmds.setKeyframe(
            node, al='simPose', at=a, t=int(sf), v=cv
        )
        cmds.setKeyframe(
            node, al='simPose', at=a, t=int(sf) - still, v=cv
        )
        cmds.setKeyframe(
            node, al='simPose', at=a, t=int(sf) - lenght, v=0
        )
    # LOCK ANIM LAYERS
    an = cmds.ls(typ='animLayer')
    for a in an:
        cmds.animLayer(a, e=True, l=True)
    print 'Done with ' + node


def fxAllNodes(node):
    ncs = cmds.ls(type=node)
    mesh = []
    for n in ncs:
        if cmds.nodeType(n) == 'pgYetiMaya':
            mesh.append(cmds.listRelatives(n, p=True)[0])
        else:
            print n
            mesh.append(cmds.listConnections(n, type='mesh')[0])
    return mesh


# -----------------------------------------------------------------------------
# UI TOOLS
# -----------------------------------------------------------------------------
def fxToolsUI():
    win = cmds.window(t='FX Tools', s=False)
    # CREATE UI PIECES
    frb = cmds.formLayout()
    tl = cmds.tabLayout(p=frb)
    frcc = cmds.formLayout(p=tl)  # Connect UI
    frn = cmds.formLayout(p=tl)  # NUCLEUS UI
    fry = cmds.formLayout(p=tl)  # YETI UI
    frc = cmds.formLayout(p=tl)  # CACHE UI
    cmds.tabLayout(
        tl,
        e=True,
        tl=(
            (frcc, 'Connect'),
            (frn, 'Nucleus'),
            (fry, 'Yeti'),
            (frc, 'Cache')
        )
    )
    # ORGANIZE UI
    cmds.formLayout(
        frb,
        e=True,
        af=[
            (tl, 'top', 0),
            (tl, 'left', 0),
            (tl, 'right', 0),
            (tl, 'bottom', 0)
        ]
    )
    mConnectUI(frcc)
    mSimUI(frn)
    mYetiSimUI(fry)
    mCacheUI(frc)
    # SHOW WINDOW AND SIZE IT
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[240, 380])


# Nucleus UI
def mSimUI(parent):
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    # create ui pieces
    fr = cmds.formLayout(p=parent)
    ts = cmds.textScrollList(h=120, ams=True)
    cbS = cmds.checkBoxGrp(l='Shell sim', cal=(1, 'center'))
    bfi = cmds.button(
        l='Get All nCloths',
        c='cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'ra=True);'
        'cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'a=sim.fxAllNodes(\'nCloth\'))'.format(ts)
    )
    bs = cmds.button(
        l='Add Selected:',
        c='cmds.textScrollList("{0}", e=True, ra=True);'
        'cmds.textScrollList("{0}", e=True, a=cmds.ls(sl=True))'.format(ts)
    )
    bsr = cmds.button(
        l='Remove Selected',
        c='cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'ri=cmds.textScrollList("{0}", q=True, si=True))'.format(ts)
    )
    bsn = cmds.separator()
    tt = cmds.text(l='  evaluate:', al='left')
    fx = cmds.floatField(v=1.0, pre=2)
    fs = cmds.floatField(v=start, pre=1)
    fe = cmds.floatField(v=end, pre=1)
    tv = cmds.text(l='  settings:', al='left')
    ttv = cmds.textField(tx='simmed')
    bss = cmds.button(
        l='Sim in Shell',
        c='sim.sim('
        'cmds.textScrollList("' + ts + '", q=True, ai=True),'
        'cmds.floatField("' + fx + '", q=True, v=True),'
        'cmds.floatField("' + fs + '", q=True, v=True),'
        'cmds.floatField("' + fe + '", q=True, v=True),'
        'cmds.textField("' + ttv + '", q=True, tx=True),'
        'cmds.checkBoxGrp("' + cbS + '", q=True, v1=True))')
    # organize UI pieces
    cmds.formLayout(
        parent,
        e=True,
        af=[
            (fr, 'left', 5),
            (fr, 'right', 5)
        ]
    )
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (cbS, 'top', 5), (cbS, 'left', 10), (cbS, 'right', 10),
            (bfi, 'left', 10), (bfi, 'right', 10),
            (bs, 'left', 10), (bs, 'right', 10),
            (bsr, 'left', 10), (bsr, 'right', 10),
            (ts, 'left', 10), (ts, 'right', 10),
            (bsn, 'left', 10), (bsn, 'right', 10),
            (tt, 'left', 10),
            (fx, 'right', 10),
            (fs, 'left', 10),
            (fe, 'right', 10),
            (tv, 'left', 10),
            (ttv, 'right', 10),
            (bss, 'left', 10), (bss, 'right', 10)],
        ap=[
            (tt, 'right', 0, 50),
            (fs, 'right', 0, 50),
            (tv, 'right', 0, 50)],
        ac=[
            (bfi, 'top', 5, cbS),
            (bs, 'top', 5, bfi),
            (bsr, 'top', 5, bs),
            (ts, 'top', 5, bsr),
            (bsn, 'top', 5, ts),
            (tt, 'top', 3, bsn),
            (fx, 'top', 0, bsn), (fx, 'left', 0, tt),
            (fs, 'top', 0, fx),
            (fe, 'top', 0, fx), (fe, 'left', 0, fs),
            (tv, 'top', 3, fe),
            (ttv, 'top', 0, fe), (ttv, 'left', 0, tv),
            (bss, 'top', 5, ttv)])
    # add ui commands
    cmdon = (
        'cmds.checkBoxGrp(\'' + cbS + '\', e=True, l=\'Maya Sim\');'
        'cmds.button(\'' + bss + '\', e=True, l=\'Sim in Scene\')'
    )
    cmdoff = (
        'cmds.checkBoxGrp(\'' + cbS + '\', e=True, l=\'Shell Sim\');'
        'cmds.button(\'' + bss + '\', e=True, l=\'Sim in Shell\')'
    )
    cmds.checkBoxGrp(
        cbS, e=True,
        onc=cmdon,
        ofc=cmdoff
    )
    # preset for start and end frame
    prst = [
        '-50', '-20', '-10', '-8', '-4',
        'orig',
        '+4', '+8', '+10', '+20', '+50'
    ]
    UI = [fs, fe]
    for u in UI:
        ppfs = cmds.popupMenu('frameRangePP', p=u)
        for p in prst:
            if p != 'orig':
                cmds.menuItem(
                    l=p,
                    p=ppfs,
                    c="cmds.floatField("
                    "'{0}', "
                    "e=True, "
                    "v=cmds.floatField('{0}', q=True, v=1){1})".format(u, p)
                )
            else:
                if u == fs:
                    cmds.menuItem(
                        l=p,
                        p=ppfs,
                        c="cmds.floatField("
                        "'{0}', "
                        "e=True, "
                        "v={1})".format(u, 'cmds.playbackOptions(q=True, min=True)')
                    )
                else:
                    cmds.menuItem(
                        l=p,
                        p=ppfs,
                        c="cmds.floatField("
                        "'{0}', "
                        "e=True, "
                        "v={1})".format(u, 'cmds.playbackOptions(q=True, max=True)')
                    )
    # preset for iterations
    prst = [
        '1.0', '0.75', '0.5', '0.25', '0.1'
    ]
    pps = cmds.popupMenu('iterationPP', p=fx)
    for p in prst:
        cmds.menuItem(
            l=p,
            p=pps,
            c="cmds.floatField('" + fx + "', e=True, v=" + p + ")"
        )
    # presets for scene name
    prst = [
        'out',
        'simmed', 'low', 'high',
        'scale_1', 'scale_10',
        'scale_object', 'scale_link'
    ]
    pps = cmds.popupMenu('settingsPP', p=ttv)
    for p in prst:
        cmds.menuItem(
            l=p,
            p=pps,
            c="cmds.textField('" + ttv + "', e=True, tx=\'" + p + "\')"
        )


# Yeti UI
def mYetiSimUI(parent):
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    # create ui pieces
    fr = cmds.formLayout(p=parent)
    # ts = cmds.textField()
    ts = cmds.textScrollList(h=110, ams=True)
    cbS = cmds.checkBoxGrp(l='Shell sim', cal=(1, 'center'))
    bfi = cmds.button(
        l='Get All Yeti Nodes',
        c='cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'ra=True);'
        'cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'a=sim.fxAllNodes(\'pgYetiMaya\'))'.format(ts)
    )
    bs = cmds.button(
        l='Yeti Nodes:',
        c='cmds.textScrollList("{0}", e=True, a=cmds.ls(sl=True));'.format(ts)
    )
    bsr = cmds.button(
        l='Remove Selected',
        c='cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'ri=cmds.textScrollList("{0}", q=True, si=True))'.format(ts)
    )
    # bsn = cmds.separator()
    cbp = cmds.checkBox(l='Generate Preview', v=1)
    tt = cmds.text(l='  samples:', al='left')
    fx = cmds.intField(v=3)
    fs = cmds.floatField(v=start, pre=1)
    fe = cmds.floatField(v=end, pre=1)
    tv = cmds.text(l='  settings:', al='left')
    ttv = cmds.textField(tx='out')
    bss = cmds.button(
        l='Sim in Shell',
        c='sim.yetiSim('
        'cmds.textScrollList("' + ts + '", q=True, ai=True),'
        'cmds.intField("' + fx + '", q=True, v=True),'
        'cmds.floatField("' + fs + '", q=True, v=True),'
        'cmds.floatField("' + fe + '", q=True, v=True),'
        'cmds.textField("' + ttv + '", q=True, tx=True),'
        'cmds.checkBox("' + cbp + '", q=True, v=True),'
        'cmds.checkBoxGrp("' + cbS + '", q=True, v1=True))'
    )
    # organize UI pieces
    cmds.formLayout(
        parent,
        e=True,
        af=[
            (fr, 'left', 5),
            (fr, 'right', 5)
        ]
    )
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (cbS, 'top', 5), (cbS, 'left', 10), (cbS, 'right', 10),
            (bfi, 'left', 10), (bfi, 'right', 10),
            (bs, 'left', 10), (bs, 'right', 10),
            (bsr, 'left', 10), (bsr, 'right', 10),
            (ts, 'left', 10), (ts, 'right', 10),
            (cbp, 'left', 10), (cbp, 'right', 10),
            (tt, 'left', 10),
            (fx, 'right', 10),
            (fs, 'left', 10),
            (fe, 'right', 10),
            (tv, 'left', 10),
            (ttv, 'right', 10),
            (bss, 'left', 10), (bss, 'right', 10)],
        ap=[
            (tt, 'right', 0, 50),
            (fs, 'right', 0, 50),
            (tv, 'right', 0, 50)],
        ac=[
            (bfi, 'top', 5, cbS),
            (bs, 'top', 5, bfi),
            (bsr, 'top', 5, bs),
            (ts, 'top', 5, bsr),
            (cbp, 'top', 5, ts),
            (tt, 'top', 3, cbp),
            (fx, 'top', 0, cbp), (fx, 'left', 0, tt),
            (fs, 'top', 0, fx),
            (fe, 'top', 0, fx), (fe, 'left', 0, fs),
            (tv, 'top', 3, fe),
            (ttv, 'top', 0, fe), (ttv, 'left', 0, tv),
            (bss, 'top', 5, ttv)])
    # add ui commands
    cmdon = (
        'cmds.checkBoxGrp(\'' + cbS + '\', e=True, l=\'Maya Sim\');'
        'cmds.button(\'' + bss + '\', e=True, l=\'Sim in Scene\')'
    )
    cmdoff = (
        'cmds.checkBoxGrp(\'' + cbS + '\', e=True, l=\'Shell Sim\');'
        'cmds.button(\'' + bss + '\', e=True, l=\'Sim in Shell\')'
    )
    cmds.checkBoxGrp(
        cbS, e=True,
        onc=cmdon,
        ofc=cmdoff
    )
    # preset for start and end frame
    prst = [
        '-50', '-20', '-10', '-8', '-4',
        'orig',
        '+4', '+8', '+10', '+20', '+50'
    ]
    UI = [fs, fe]
    for u in UI:
        ppfs = cmds.popupMenu('frameRangePP', p=u)
        for p in prst:
            if p != 'orig':
                cmds.menuItem(
                    l=p,
                    p=ppfs,
                    c="cmds.floatField("
                    "'{0}', "
                    "e=True, "
                    "v=cmds.floatField('{0}', q=True, v=1){1})".format(u, p)
                )
            else:
                if u == fs:
                    cmds.menuItem(
                        l=p,
                        p=ppfs,
                        c="cmds.floatField("
                        "'{0}', "
                        "e=True, "
                        "v={1})".format(u, 'cmds.playbackOptions(q=True, min=True)')
                    )
                else:
                    cmds.menuItem(
                        l=p,
                        p=ppfs,
                        c="cmds.floatField("
                        "'{0}', "
                        "e=True, "
                        "v={1})".format(u, 'cmds.playbackOptions(q=True, max=True)')
                    )
    # preset for iterations
    prst = [
        '3', '4', '6', '9', '12'
    ]
    pps = cmds.popupMenu('iterationPP', p=fx)
    for p in prst:
        cmds.menuItem(
            l=p,
            p=pps,
            c="cmds.floatField('" + fx + "', e=True, v=" + p + ")"
        )
    # presets for scene name
    prst = [
        'yetiSim', 'damp', 'stiff',
    ]
    pps = cmds.popupMenu('settingsPP', p=ttv)
    for p in prst:
        cmds.menuItem(
            l=p,
            p=pps,
            c="cmds.textField('" + ttv + "', e=True, tx=\'" + p + "\')"
        )


# Geometry Cache UI
def mCacheUI(parent):
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    # create ui pieces
    fr = cmds.formLayout(p=parent)
    ts = cmds.textScrollList(h=130)
    cbS = cmds.checkBoxGrp(l='Shell sim', cw=(1, 50), cal=(1, 'left'))
    cbC = cmds.checkBoxGrp(l='Clean Scene', cw=(1, 70), cal=(1, 'left'))
    bs = cmds.button(
        l='Cache Meshes:',
        c='cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'ra=True);'
        'cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'a=cmds.ls(sl=True))'.format(ts)
    )
    tt = cmds.text(l='  evaluate:', al='left')
    fx = cmds.floatField(v=1.0, pre=2)
    fs = cmds.floatField(v=start, pre=1)
    fe = cmds.floatField(v=end, pre=1)
    tv = cmds.text(l='  settings:', al='left')
    ttv = cmds.textField(tx='cached')
    rcb = cmds.radioButtonGrp(
        cal=(1, 'left'),
        cw2=(70, 0),
        la2=['Maya', 'Alembic'],
        nrb=2,
        sl=1
    )
    bss = cmds.button(
        l='Cache in Shell',
        c='sim.cacheOut('
        'cmds.textScrollList( "' + ts + '", q = True, ai = True),'
        'cmds.floatField("' + fx + '", q = True, v = True),'
        'cmds.floatField("' + fs + '", q = True, v = True),'
        'cmds.floatField("' + fe + '", q = True, v = True),'
        'cmds.textField("' + ttv + '", q = True, tx = True),'
        'cmds.radioButtonGrp("' + rcb + '", q = True, sl = True),'
        'cmds.checkBoxGrp("' + cbS + '", q=True, v1=True),'
        'cmds.checkBoxGrp("' + cbC + '", q=True, v1=True))'
    )
    # organize UI pieces
    cmds.formLayout(
        parent,
        e=True,
        af=[
            (fr, 'left', 5),
            (fr, 'right', 5)
        ]
    )
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (cbS, 'top', 5), (cbS, 'right', 10),
            (cbC, 'top', 5), (cbC, 'left', 5),
            (bs, 'left', 10), (bs, 'right', 10),
            (ts, 'left', 10), (ts, 'right', 10),
            (tt, 'left', 10),
            (fx, 'right', 10),
            (fs, 'left', 10),
            (fe, 'right', 10),
            (tv, 'left', 10),
            (ttv, 'right', 10),
            (bss, 'left', 10), (bss, 'right', 10),
            (rcb, 'left', 10), (rcb, 'right', 10)
        ],
        ap=[
            (cbC, 'right', 0, 50),
            (tt, 'right', 0, 50),
            (fs, 'right', 0, 50),
            (tv, 'right', 0, 50)
        ],
        ac=[
            (cbS, 'left', 5, cbC),
            (bs, 'top', 5, cbS),
            (ts, 'top', 5, bs),
            (tt, 'top', 3, ts),
            (fx, 'top', 0, ts), (fx, 'left', 0, tt),
            (fs, 'top', 0, fx),
            (fe, 'top', 0, fx), (fe, 'left', 0, fs),
            (tv, 'top', 3, fe),
            (ttv, 'top', 0, fe), (ttv, 'left', 0, tv),
            (rcb, 'top', 5, ttv), (bss, 'top', 5, rcb)
        ]
    )
    # add ui commands
    cmdon = (
        'cmds.checkBoxGrp(\'' + cbS + '\', e=True, l=\'Maya Sim\');'
        'cmds.button(\'' + bss + '\', e=True, l=\'Cache in Scene\')'
    )
    cmdoff = (
        'cmds.checkBoxGrp(\'' + cbS + '\', e=True, l=\'Shell Sim\');'
        'cmds.button(\'' + bss + '\', e=True, l=\'Cache in Shell\')'
    )
    cmds.checkBoxGrp(
        cbS, e=True,
        onc=cmdon,
        ofc=cmdoff
    )
    # preset for start and end frame
    prst = [
        '-50', '-20', '-10', '-8', '-4',
        'orig',
        '+4', '+8', '+10', '+20', '+50'
    ]
    UI = [fs, fe]
    for u in UI:
        ppfs = cmds.popupMenu('frameRangePP', p=u)
        for p in prst:
            if p != 'orig':
                cmds.menuItem(
                    l=p,
                    p=ppfs,
                    c="cmds.floatField("
                    "'{0}', "
                    "e=True, "
                    "v=cmds.floatField('{0}', q=True, v=1){1})".format(u, p)
                )
            else:
                if u == fs:
                    cmds.menuItem(
                        l=p,
                        p=ppfs,
                        c="cmds.floatField("
                        "'{0}', "
                        "e=True, "
                        "v={1})".format(u, 'cmds.playbackOptions(q=True, min=True)')
                    )
                else:
                    cmds.menuItem(
                        l=p,
                        p=ppfs,
                        c="cmds.floatField("
                        "'{0}', "
                        "e=True, "
                        "v={1})".format(u, 'cmds.playbackOptions(q=True, max=True)')
                    )
    # preset for iterations
    prst = [
        '1.0', '0.75', '0.5', '0.25', '0.1'
    ]
    pps = cmds.popupMenu('iterationPP', p=fx)
    for p in prst:
        cmds.menuItem(
            l=p,
            p=pps,
            c="cmds.floatField('" + fx + "', e=True, v=" + p + ")"
        )
    # presets for scene name
    prst = [
        'cached', 'test', 'mayaC', 'alembic'
    ]
    pps = cmds.popupMenu('settingsPP', p=ttv)
    for p in prst:
        cmds.menuItem(
            l=p,
            p=pps,
            c="cmds.textField('" + ttv + "', e=True, tx=\'" + p + "\')"
        )


# Rigs Connect UI
def mConnectUI(parent):
    # create ui pieces
    fr = cmds.formLayout(p=parent)
    win = cmds.formLayout(fr, q=True, p=True).split('|')[0]
    om = cmds.optionMenu(l='Name Space', w=120)
    tf1 = cmds.textField(tx='_in')
    tf2 = cmds.textField(tx='_geo')
    bs = cmds.button(l='Fx Meshes:')
    ts = cmds.textScrollList(h=155)
    bss = cmds.button(
        l='Connect',
        c='sim.simConnect('
        '[cmds.optionMenu(\'{0}\',q=True, v=True),'
        'cmds.textScrollList(\'{1}\',q=True, ai=True)[0]],'
        'cmds.textScrollList(\'{1}\', q=True, ai=True),'
        'cmds.textField(\'{2}\', q=True, tx=True),'
        'cmds.textField(\'{3}\', q=True, tx=True))'.format(om, ts, tf1, tf2)
    )
    frl = cmds.frameLayout(l='Simpose', p=fr, cll=True, cl=True)
    frm = cmds.formLayout(p=frl)
    stf = cmds.textField()
    sbt = cmds.button(l='Top Node')
    sff = cmds.intFieldGrp(
        l='Length', el='Still', cw4=[50, 50, 50, 50], v1=30, v2=15, nf=2
    )
    stx = cmds.text(l='CTRL')
    som = cmds.optionMenu()
    sbs = cmds.button(l='Simpose')
    # ADD UI COMMANDS
    nss = cmds.namespaceInfo(lon=True, r=True)
    if nss:
        for n in nss:
            if n != 'shared' and n != 'UI':
                cmds.menuItem(l=n, p=om)
    cmds.button(
        bs,
        e=True,
        c='cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'ra=True );'
        'cmds.textScrollList('
        '"{0}", '
        'e=True, '
        'a=cmds.ls(sl=True))'.format(ts)
    )
    cmds.frameLayout(
        frl,
        e=True,
        ec='cmds.window("' + win + '", e=True, h=430)',
        cc='cmds.window("' + win + '", e=True, h=380)'
    )
    cmds.button(
        sbt,
        e=True,
        c='cmds.textField("' + stf + '", e=True, tx=cmds.ls(sl=True)[0])'
    )
    cmds.button(
        sbs,
        e=True,
        c='sim.simPose('
        'cmds.textField("{0}", q=True, tx=True),'
        'cmds.intFieldGrp("{1}", q=True, v1=True),'
        'cmds.intFieldGrp("{1}", q=True, v2=True),'
        '["_"+cmds.optionMenu("{2}", q=True, v=True)],'
        '[""])'.format(stf, sff, som)
    )
    # ADD UI PRESETS
    items = ['CTRL', 'LOC', 'GRP', 'ctrl', 'loc', 'grp']
    for i in items:
        cmds.menuItem(l=i, p=som)
    prst = [
        '_in', '_geo', '_mesh', '_crv', '_proxy'
    ]
    for t in [tf1, tf2]:
        pps = cmds.popupMenu('suffPP', p=t)
        for p in prst:
            cmds.menuItem(
                l=p,
                p=pps,
                c="cmds.textField('" + t + "', e=True, tx='" + p + "')"
            )
    # ORGANIZE UI PIECES
    cmds.formLayout(
        parent,
        e=True,
        af=[
            (fr, 'left', 5),
            (fr, 'right', 5)
        ]
    )
    cmds.formLayout(
        frm,
        e=True,
        af=[
            (stf, 'top', 5), (stf, 'left', 5),
            (sbt, 'top', 5), (sbt, 'right', 5),
            (sff, 'left', 5), (sff, 'right', 5),
            (stx, 'left', 5),
            (som, 'right', 5),
            (sbs, 'left', 5), (sbs, 'right', 5)
        ],
        ap=[
            (stf, 'right', 5, 70),
            (stx, 'right', 5, 30)
        ],
        ac=[
            (sbt, 'left', 5, stf),
            (sff, 'top', 5, stf),
            (stx, 'top', 5, sff),
            (som, 'top', 5, sff), (som, 'left', 5, stx),
            (sbs, 'top', 5, som)
        ]
    )
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (om, 'top', 5), (om, 'left', 10), (om, 'right', 10),
            (tf1, 'top', 5), (tf1, 'left', 10),
            (tf2, 'top', 5), (tf2, 'right', 10),
            (bs, 'left', 10), (bs, 'right', 10),
            (ts, 'left', 10), (ts, 'right', 10),
            (bss, 'left', 10), (bss, 'right', 10),
            (frl, 'left', 10), (frl, 'right', 10)
        ],
        ap=[
            (tf1, 'right', 0, 50)
        ],
        ac=[
            (tf1, 'top', 5, om),
            (tf2, 'top', 5, om), (tf2, 'left', 5, tf1),
            (bs, 'top', 5, tf1),
            (ts, 'top', 5, bs),
            (bss, 'top', 5, ts),
            (frl, 'top', 5, bss)
        ]
    )
