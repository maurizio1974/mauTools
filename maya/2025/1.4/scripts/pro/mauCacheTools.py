'''----------------------------------------------------------------------

MAU SIM/CACHE UTILITY

Date = 19/04/2023
User = Maurizio Giglioli
Update =
        19/04/2023 MAUed
        19/04/2023 First Release

----------------------------------------------------------------------'''
import os
import re
import json
import getpass
import tempfile
import maya.mel as mel
import maya.cmds as cmds

# MAIN CACHING AND CONNECTIONS PROCEDURES


def alembicWrapOutSingle(start, end, sceneN, cacheSets, out):
    oStart = cmds.playbackOptions(q=True, min=True)
    oEnd = cmds.playbackOptions(q=True, max=True)
    for c in cacheSets:
        print(cmds.getAttr(c + '.assetName'))
    # TURN OFF CYCLE CHECK
    mel.eval('cycleCheck -e off')
    # DECLARATION OF VARIABLES NEEDED
    aScene = ''
    # MAKE DIRECTORIERS
    if not os.path.isdir(out):
        os.makedirs(out)
        print('Created missing directory: ' + out)
    # PREPARE SCENE TO BE CACHED
    for cache in cacheSets:
        attrG, geos = '', ''
        assetName = cmds.getAttr(cache + '.assetName')
        # ALEMBIC FILE NAME
        item = cmds.sets(cache, q=True)
        # abcCurrent = sceneN + '.abc'
        abcCurrent = cache + '.abc'
        aScene = os.path.join(out, abcCurrent).replace('\\', '/')
        # SET FRAME RANGE
        cmds.playbackOptions(e=True, ast=start, aet=end,
                             min=start, max=end, fps=24)
        # CURRENT ASSET
        cAst = cmds.getAttr(cache + '.assetName')
        cAstRes = 0
        if cmds.attributeQuery('res', n=cache, ex=True):
            cAstRes = cmds.getAttr(cache + '.res')
        # print '=' * 50
        # print cache, cAst + ' Asset ready to be cached at LOD: ' + str(cAstRes).zfill(2)
        # print '=' * 50
        # MOVE TIMELINE 1 FRAME TO REFRESH NUCLEUS EVALUATION
        # REFRESH UI TO EVALUATE NUCLEUS NODES CORRECTLY
        forceRefreshUI(start)
        # LIST TO PASS TO CACHE COMMAND -------------------------------------------
        grp = cmds.sets(cache, q=True)
        # ATTRIBUTES TO PASS TO COMMAND
        # attributes = cmds.listAttr(grp[0], ud=True)
        attributes = getAllUserAttrs(grp[0])
        if attributes:
            for aa in attributes:
                attrG += ' -attr ' + aa
        else:
            cmds.warning('No user defined attributes found')
        # GEO AND CURVES
        geos = '-root ' + grp[0]
        # ALEMBIC CACHE COMMAND
        cmd = (
            'AbcExport -verbose -j "-frameRange {0} {1} -step {2} '
            '-writeUVSets -uvWrite -dataFormat ogawa -stripNamespaces -writeVisibility '
            '-worldSpace {3} {4} -file {5}";').format(start, end, '1.0', attrG, geos, aScene)
        # DISABLE VIEWPORT REFRESH
        cmds.refresh(suspend=True)
        print('-' * len(cmd))
        print('ALEMBIC EXPORT COMMAND:\n' + cmd)
        print('-' * len(cmd))
        try:
            mel.eval(cmd)
            print('-' * len(aScene))
            # print aScene
            print('-' * len(aScene))
        except Exception:
            print("Error: Render failed")
        # ENABLE VIEWPORT REFRESH
        cmds.refresh(suspend=False)
        cmds.refresh(f=True)
    # RESTORE FRAME RANGE
    cmds.playbackOptions(e=True, ast=oStart, aet=oEnd,
                         min=oStart, max=oEnd, fps=24)


def cacheOut(cacheSets, start, end):
    cacheMeshes = []
    # CHECK FOR BAD REFERENCE NODES AND NODES
    checkUKN()
    cleanUP()
    # CHANGE TO VP1
    # viewPortCache()
    # UI CHECKS
    if not cacheSets:
        print('NO INFO ADDED TO THE LIST TO EXPORT')
        return
    # UI Checks
    if not cacheSets:
        cmds.confirmDialog(t='Not Kick Ass', m='Need some Sets in the UI')
        return
    tipo = cmds.getAttr(cacheSets[0] + '.assetType')
    # MAKE STRING OUT OR CACHESTES LIST
    out = '['
    for c in cacheSets:
        if c != cacheSets[-1]:
            out += '"' + c + '", '
        else:
            out += '"' + c + '"'
    out += ']'
    # MAIN LOCATION FOR PROC
    sceneN = getCacheLocation()[1]
    out = getCacheLocation()[0]
    # CALL FUNCTION FOR ALEMBIC EXPORT
    alembicWrapOutSingle(start, end, sceneN, cacheSets, out)
    # exportNameSapces(scene, sceneN, cacheSets)

# -----------------------------------------------------------------------------
# UTILITIES
# -----------------------------------------------------------------------------


def getAllUserAttrs(node):
    out = []
    meshes = cmds.ls(node, dag=True)
    for m in meshes:
        atty = cmds.listAttr(m, ud=True)
        if atty:
            for cur in atty:
                out.append(cur)
    attributes = list(set(out))
    print('=' * 100)
    print('EXPORTING THESE ATTRIBUTES:\n' + ', '.join(attributes))
    print('=' * 100)
    return attributes


def forceRefreshUI(start):
    cmds.currentTime(start, u=True)
    cmds.refresh(f=True)
    cmds.currentTime(start + 1, u=True)
    cmds.refresh(f=True)
    cmds.currentTime(start, u=True)
    cmds.refresh(f=True)


def checkUKN():
    refs, badr = cmds.ls(type='reference'), []
    for r in refs:
        if 'UNKNOWN' in r:
            badr.append(r)
            print('Bad Reference: ' + r)
    if badr:
        result = cmds.confirmDialog(
            t='Ooops', button=['Ignore', 'Yes'], db='Yes',
            m='There is some extra crap in this scene,\nDo you want flush it out ?')
        if result == 'Yes':
            cmds.delete(badr)
            # print 'SCENE CLEANED'
        else:
            # print 'CACHE PROCESS STOPPED'
            return


def viewPortCache():
    # CHANGE TO VP1
    vp1 = mel.eval('$tempMelVar=$gLegacyViewport')
    for elem in getPanel(typ='modelPanel'):
        try:
            mel.eval('setRendererInModelPanel ' + vp1 + ' ' + elem.name())
        except:
            print('--')
    cmds.refresh()


def getNameSpace(node):
    ns = node.replace(node.split(':')[-1], '')
    return ns


def namespaceUtils(mode, sceneN=None, fullP=None):
    path = tempfile.gettempdir()
    if fullP:
        path = fullP
    out = os.path.join(path, 'data', 'namespaces', sceneN)
    # JSON FILE
    jFile = os.path.join(
        out, sceneN + '.json').replace('\\', '/').replace('//', '/')
    # LET'S GO
    data, namespaces = {}, []
    if mode == 'write':
        defaults = ['UI', 'shared']
        nss = [ns for ns in cmds.namespaceInfo(
            lon=True, r=True) if ns not in defaults]
        for n in nss:
            namespaces.append(n)
        data['ns'] = namespaces
        # CHECK IF DIRECTORY EXISTS
        if not os.path.isdir(out):
            os.makedirs(out)
            cmds.warning('Made directory: ' + out)
        with open(jFile, 'w') as jf:
            data = json.dump(data, jf)
            print('File saved here ' + jFile)
    elif mode == 'read':
        if os.path.isfile(jFile):
            with open(jFile) as jf:
                data = json.load(jf)
        if data:
            for ns in list(data.keys()):
                for n in data[ns]:
                    if not cmds.namespace(ex=n):
                        cmds.namespace(add=n)
                        print('Recreated namespace: ' + n)
                    else:
                        print(n + ' already Exists')
    elif mode == 'clean':
        defaults = ['UI', 'shared']
        nss = cmds.namespaceInfo(lon=True, r=True)
        if nss:
            namespaces = [ns for ns in nss if ns not in defaults]
            namespaces.sort(key=nsChildren, reverse=True)
            for ns in namespaces:
                try:
                    if not namespaceInfo(ns, ls=True):
                        cmds.namespace(rm=ns, mnr=True)
                        print('Cleaned ' + ns + ' because it is empty')
                except RuntimeError as e:
                    pass


def exportNameSapces(scene, sceneN, cacheSets, ext=None):
    for cache in cacheSets:
        nsc = getNameSpace(cache)
        if not cmds.namespace(ex=nsc):
            cmds.namespace(add=nsc)
            print('Added this namespace to the scene: ' + nsc)
        if ext:
            ns = nsc[0:-1] + ext
            if not cmds.namespace(ex=ns):
                cmds.namespace(add=ns)
                print('Added this namespace to the scene: ' + ns)
    # SAVE ALL NAMESPACES
    fullP = scene.replace(sceneN, '')
    fullP = fullP.replace('scenes', '')
    namespaceUtils('write', sceneN, fullP)


def nsChildren(ns):
    return ns.count(':')


def getVersion():
    version, valid = 0, []
    scene = cmds.file(q=True, sn=True, shn=True)
    try:
        version = re.findall('\d+', scene)[-1]
        return str(version), int(version)
    except Exception:
        # dialogOut()
        pass


def getCacheLocation():
    # ws = cmds.workspace(q=True, act=True)
    name = cmds.file(q=True, sn=True, shn=True)
    ws = cmds.file(q=True, sn=True).replace('/scenes/' + name, '').split('.')[0]
    name = name.replace('.' + name.split('.')[-1], '')
    name = name.replace('.', '_')
    loc = os.path.join(ws, 'cache/alembic').replace('\\', '/')
    return loc, name


def getExportSET(mode):
    out, aName = [], []
    obs = cmds.ls(type='objectSet')
    for o in obs:
        if cmds.attributeQuery('assetType', n=o, ex=True):
            value = cmds.getAttr(o + '.assetType')
            if value in mode or value in mode.lower():
                out.append(o)
                if cmds.attributeQuery('assetName', n=o, ex=True):
                    value = cmds.getAttr(o + '.assetName')
                    aName.append(value)
    return out, aName


def cleanUP(sceneN=None, fullP=None):
    # Namespaces part
    if sceneN:
        namespaceUtils('clean', sceneN, fullP)
    # CLEAN UNKNOWN NODES
    for s in cmds.ls('*'):
        try:
            if cmds.nodeType(s) == 'unknown':
                cmds.lockNode(s, l=False)
                cmds.delete(s)
        except Exception:
            cmds.warning(s + ' ain\'t here')
    # print 'Scene cleaned'


def plugInCheck():
    plugs = ['AbcExport', 'AbcImport', 'gpuCache']
    for p in plugs:
        state = cmds.pluginInfo(p, q=True, l=True)
        if not state:
            try:
                cmds.loadPlugin(p)
                print('Loaded plugin: ' + p)
            except:
                continue

# -----------------------------------------------------------------------------
# UI TOOLS
# -----------------------------------------------------------------------------
# MAIN UI


def mau_ToolsUI():
    win = cmds.window(t='Mau Cache Tools', s=True)
    # CREATE UI PIECES
    frb = cmds.formLayout()
    tl = cmds.tabLayout(p=frb)
    frc = cmds.formLayout(p=tl)  # CACHE UI
    cmds.tabLayout(
        tl,
        e=True,
        tl=(frc, 'Cache'))
    # ORGANIZE UI
    cmds.formLayout(
        frb,
        e=True,
        af=[
            (tl, 'top', 0),
            (tl, 'left', 0),
            (tl, 'right', 0),
            (tl, 'bottom', 0)])
    mCacheUI(frc)
    # CHECK NEEDED PLUGINS ARE LOADED
    plugInCheck()
    # SHOW WINDOW AND SIZE IT
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[900, 500])

# GEOMETRY CACHE UI

def mCacheUI(parent):
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    # UI PIECES
    fr = cmds.formLayout(p=parent)
    oms = cmds.optionMenu()
    for it in ['MODEL', 'RIG']:
        cmds.menuItem(label=it, p=oms)
    bs = cmds.button(l='Export Geo:')
    ts = cmds.textScrollList(h=130)
    fs = cmds.intField(v=start)
    fe = cmds.intField(v=start, en=False)
    tvs = cmds.text(l='Cache will be saved:', al='left')
    txs = cmds.text(l=getCacheLocation()[0])
    bss = cmds.button(l='Cache OUT')
    # ORGANIZE UI
    cmds.formLayout(
        parent, e=True,
        af=[
            (fr, 'top', 5),
            (fr, 'left', 5),
            (fr, 'right', 5),
            (fr, 'bottom', 5)
        ]
    )
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (oms, 'left', 10), (oms, 'top', 10),
            (bs, 'right', 10), (bs, 'top', 10),
            (ts, 'left', 10), (ts, 'right', 10),
            (fs, 'left', 10),
            (fe, 'right', 10),
            (tvs, 'left', 10),
            (txs, 'right', 10),
            (bss, 'left', 10), (bss, 'bottom', 10), (bss, 'right', 10)
        ],
        ap=[
            (fs, 'right', 0, 50)
        ],
        ac=[
            (bs, 'left', 10, oms),
            (ts, 'top', 10, bs), (ts, 'bottom', 10, fs),
            (fs, 'bottom', 10, tvs),
            (fe, 'bottom', 10, tvs), (fe, 'left', 10, fs),
            (tvs, 'bottom', 10, bss),
            (txs, 'left', 10, tvs), (txs, 'bottom', 10, bss)
        ]
    )
    # ADD UI COMANDS
    # STAGE SWITCH
    cmdOm = (
        'cmds.intField("{2}", e=True, v=cmds.intField("{1}", q=True, v=True));cmds.intField("{2}", e=True, en=False) '
        'if cmds.optionMenu("{0}", q=True, v=True) == "MODEL" else '
        'cmds.intField("{2}", e=True, v=cmds.playbackOptions(q=True, max=True));cmds.intField("{2}", e=True, en=True)'.format(oms, fs, fe))
    cmds.optionMenu(oms, e=True, cc=cmdOm)

    # GET EXPORT GEO BUTTON
    cmds.button(
        bs, e=True,
        c='cmds.textScrollList("{0}", e=True, ra=True);cmds.textScrollList("{0}", e=True, a=mauCacheTools.getExportSET(cmds.optionMenu("{1}", q=True, v=True))[0])'.format(ts, oms))
    # LIST UI
    cmdRem = 'cmds.textScrollList("{0}", e=True, ri=cmds.textScrollList("{0}", q=True, si=True))'.format(
        ts)
    cmds.textScrollList(ts, e=True, dcc=cmdRem)
    # CACHE OUT BUTTON
    cmds.button(
        bss, e=True,
        c='mauCacheTools.cacheOut('
        'cmds.textScrollList("{0}", q = True, ai = True),'
        'cmds.intField("{1}", q=True, v=True),'
        'cmds.intField("{2}", q=True, v=True))'.format(ts, fs, fe))
    # PRESET FOR START AND END FRAME
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
                    l=p, p=ppfs,
                    c="cmds.intField('{0}', e=True, "
                    "v=cmds.intField('{0}', q=True, v=1){1})".format(u, p))
            else:
                if u == fs:
                    cmds.menuItem(
                        l=p, p=ppfs,
                        c="cmds.intField('{0}', e=True, "
                        "v={1})".format(
                            u, 'cmds.playbackOptions(q=True, min=True)'))
                else:
                    cmds.menuItem(
                        l=p, p=ppfs,
                        c="cmds.intField('{0}', e=True, "
                        "v={1})".format(
                            u, 'cmds.playbackOptions(q=True, max=True)'))
