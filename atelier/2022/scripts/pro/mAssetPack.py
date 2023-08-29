'''-------------------------------------------------------------------------

        MINIMO ASSET PACKAGER

        Date = 25-08-2014
        User = Maurizio Giglioli
        info = Make a copy with texture,
        references and cahces in the desired location for delivery
        Update = (25-08-2014)
                First release.
                 (18-03-2015)
                Rewritten all with classes
                added support for udim UDIM and custom location paths

----------------------------------------------------------------------------'''

import maya.cmds as cmds
import maya.mel as mel
import shutil as sh
import datetime


# --------------------------------------------------------------- Classes
class mAssetFile(object):

    def __init__(self, name):
        self.name = name

    def fAttr(self):
        attr, out = '', ''
        if self.type() == 'pgYetiMaya':
            attr = 'cacheFileName'
            out = cmds.getAttr(self.name + '.' + attr)
        elif self.type() == 'file':
            mayaV = cmds.about(version=True)
            if mayaV == '2014':
                attr = 'fileTextureName'
                out = cmds.getAttr(self.name + '.' + attr)
            else:
                if cmds.getAttr(self.name + '.uvTilingMode') == 3:
                    attr = 'fileTextureName'
                    # attr = 'fileTextureNamePattern'
                    tex = cmds.getAttr(self.name + '.' + attr)
                    name = tex.rsplit('_', 1)[0]
                    ext = tex.rsplit('_', 1)[-1].split('.')[-1]
                    out = name + '_<UDIM>.' + ext
                else:
                    attr = 'fileTextureName'
                    out = cmds.getAttr(self.name + '.' + attr)
        elif self.type() == 'imagePlane':
            attr = 'imageName'
            out = cmds.getAttr(self.name + '.' + attr)
        elif self.type() == 'AlembicNode':
            attr = 'abc_File'
            out = cmds.getAttr(self.name + '.' + attr)
        elif self.type() == 'gpuCache':
            attr = 'cacheFileName'
            out = cmds.getAttr(self.name + '.' + attr)
        elif self.type() == 'aiStandIn':
            attr = 'dso'
            out = cmds.getAttr(self.name + '.' + attr)
        elif self.type() == 'cacheFile':
            attr = 'cachePath'
            out = cmds.getAttr(self.name + '.' + attr)
            out += cmds.getAttr(self.name + '.cacheName') + '.xml'
        elif self.type() == 'reference':
            out = cmds.referenceQuery(self.name, f=True)
        else:
            raise TypeError('Attribute not of type: ""')
        return out

    def fName(self, path=None):
        if path:
            return path.split('/')[-1]
        else:
            if self.fAttr():
                return self.fAttr().split('/')[-1]

    def fNameExt(self, path=None):
        if path:
            return path.split('.')[-1]
        else:
            if self.fAttr():
                return self.fAttr().split('.')[-1]

    def fPath(self, path=None):
        if path:
            return path.replace(self.fName(path), '')
        else:
            if self.fAttr():
                return self.fAttr().replace(self.fName(), '')

    def fReplace(self, path, cPath=None):
        ws, fileP, fileN = '', '', ''
        if self.type() == 'pgYetiMaya':
            fileN = self.name
        else:
            fileN = self.fName()
        if cPath:
            fileP = cPath
        else:
            fileP = self.fPath()
        if 'sourceimages' in fileP:
            ws = fileP.split('sourceimages')[0]
        elif 'cache' in fileP:
            ws = fileP.split('cache')[0]
        elif 'scenes' in fileP:
            ws = fileP.split('scenes')[0]
        else:
            print(fileN + ' not in standard directory !')
            if self.type() == 'file':
                return path + 'sourceimages/', path + 'sourceimages/' + fileN
            elif self.type() == 'pgYetiMaya' or self.type() == 'cacheFile':
                return path + 'cache/', path + 'cache/' + fileN
            elif self.type() == 'reference':
                return path + 'scenes/', path + 'scenes/' + fileN
        if ws:
            return fileP.replace(ws, path), fileP.replace(ws, path) + fileN
        else:
            return path + fileP, path + fileP + fileN

    def fUDIM(self, path=None):
        fileN, fileP, fileNE, textures = '', '', '', []
        if path:
            fileN = self.fName(path)
            fileP = self.fPath(path)
            fileNE = self.fNameExt(path)
        else:
            fileN = self.fName()
            fileP = self.fPath()
            fileNE = self.fNameExt()
        if sh.os.path.exists(fileP):
            texs = sh.os.listdir(fileP)
            for t in texs:
                if fileNE in t and fileN.split('<UDIM>')[0] in t:
                    textures.append(t)
            if textures:
                return fileN, textures

    def fNucleus(self):
        fileN = self.fName()
        fileP = self.fPath()
        fileNE = self.fNameExt()
        caches = []
        if sh.os.path.exists(fileP):
            cache = sh.os.listdir(fileP)
            for c in cache:
                if c.split('Frame')[0] in fileN and fileNE not in c:
                    caches.append(c)
            if caches:
                return fileN, caches

    def fAlembic(self):
        fileN = self.fName()
        fileP = self.fPath()
        fileNE = self.fNameExt()
        caches = []
        if sh.os.path.exists(fileP):
            cache = sh.os.listdir(fileP)
            for c in cache:
                if c.split('Frame')[0] in fileN and fileNE not in c:
                    caches.append(c)
            if caches:
                return fileN, caches

    def fYeti(self):
        fileN = self.fName()
        fileP = self.fPath()
        fileNE = self.fNameExt()
        caches = []
        if sh.os.path.exists(fileP):
            cache = sh.os.listdir(fileP)
            for c in cache:
                if fileNE in c:
                    caches.append(c)
            if caches:
                return fileN, caches

    def fYetiTex(self):
        attrs = []
        fileN = self.name
        texN = cmds.pgYetiGraph(fileN, listNodes=True, type='texture')
        textures = []
        for t in texN:
            cmd = 'pgYetiGraph -node ' + t + ' -param "file_name" '
            cmd += '-getParamValue ' + fileN
            attr = mel.eval(cmd)
            udim = self.fUDIM(attr)[1]
            if udim:
                for u in udim:
                    textures.append(u)
                    attrs.append(self.fPath(attr))
            else:
                textures.append(attr)
                attrs.append(self.fPath(attr))
        return attrs, textures


class mAsset(mAssetFile):

    def __init__(self, name):
        mAssetFile.__init__(self, name)
        self.name = name

    def shape(self):
        sh = cmds.listRelatives(self.name, s=True)
        if sh:
            return sh[0]
        else:
            return self.name

    def type(self):
        return cmds.nodeType(self.shape())


# --------------------------------------------------------------- Definitions
def mBrowser(mode):
    out = ''
    filter = "Maya ASCII (*.ma);;Maya Binary (*.mb)"
    r = cmds.fileDialog2(
        ff=filter,
        cap='Asset Package Destination',
        dir="data/",
        fm=mode,
        ds=True
    )
    if r:
        out = r[0]
    return out


def mCopier(ofile, nfile):
    path = nfile.replace(nfile.split('/')[-1], '')
    if not sh.os.path.exists(path):  # make directories if needed
        sh.os.makedirs(path)
    if not sh.os.path.isfile(nfile):  # Check if file is already there
        if sh.os.path.isfile(ofile):  # Check if original file exist
            sh.copyfile(ofile, nfile)  # Copy Files to new Location
            print('Copying : ' + ofile + '\nTo      : ' + nfile)
    else:
        print(nfile + ' already there')


def mRefereceCopier(destination, status):
    ref = cmds.ls(type='reference')
    if ref:
        for r in ref:
            if 'RN' in r:
                try:
                    if cmds.referenceQuery(r, il=True):
                        asset = mAsset(r)
                        if status == 0:
                            cmds.file(asset.fAttr(), importReference=True)
                        elif status == 1:
                            mCopier(
                                asset.fAttr(),
                                asset.fReplace(destination)[1]
                            )
                            if '.mb' in asset.fReplace(destination):
                                type = 'mayaBinary'
                            if '.ma' in asset.fReplace(destination):
                                type = 'mayaAscii'
                            cmds.file(
                                asset.fReplace(destination),
                                lr=r,
                                lrd='none',
                                typ=type,
                                op='v=0')
                    else:
                        cmds.file(asset.fAttr(), rr=True)
                except:
                    print('skipping {0}'.format(r))


def mTexCopier(destination, tex):
    files = cmds.ls(type='file')
    for f in files:
        asset = mAsset(f)
        if asset.fAttr():
            if 'UDIM' in asset.fAttr() or 'udim' in asset.fAttr():
                if asset.fUDIM():
                    for u in list(asset.fUDIM())[1]:
                        if tex == 0:
                            mCopier(
                                asset.fPath() + u,
                                asset.fReplace(destination)[0] + u
                            )
                        elif tex == 1:
                            for formats in ['.tx', '.rstexbin']:
                                out = asset.fReplace(destination)[0]
                                out += u.split('.')[0] + formats
                                mCopier(
                                    asset.fPath() + u.split('.')[0] + formats,
                                    out
                                )
            else:
                if asset.fReplace(destination):
                    if tex == 0:
                        mCopier(asset.fAttr(), asset.fReplace(destination)[1])
                    elif tex == 1:
                        for formats in ['.tx', '.rstexbin']:
                            out = asset.fReplace(destination)[1]
                            out += out.split('.')[0] + formats
                            # Check if file exist
                            current = asset.fAttr().split('.')[0] + formats
                            if sh.os.path.isfile(current):
                                mCopier(
                                    asset.fAttr().split('.')[0] + formats,
                                    out
                                )
    files = cmds.ls(type='imagePlane')
    for f in files:
        f = f.split('->')[-1]
        asset = mAsset(f)
        if not asset.fAttr():
            return
        if asset.fReplace(destination):
            print(asset.fAttr())
            print(asset.fReplace(destination)[1])
            # mCopier(asset.fAttr(), asset.fReplace(destination)[1])
            # attr = asset.fReplace(destination)[1].split('sourceimages')[1]
            # cmds.setAttr(
            #     f + '.imageName',
            #     'sourceimages' + attr,
            #     type='string'
            # )


def mcYetiCopier(destination):
    files = cmds.ls(type='pgYetiMaya')
    for f in files:
        asset = mAsset(f)
        if asset.fAttr():
            for a in asset.fYeti()[1]:
                path = asset.fReplace(destination)[0]
                mCopier(asset.fPath() + a, path + a)
        texs = asset.fYetiTex()[1]
        print(f, texs)
        if texs:
            for i, a in enumerate(asset.fYetiTex()[1]):
                mCopier(
                    asset.fYetiTex()[0][i] + a,
                    asset.fReplace(destination, asset.fYetiTex()[0][i])[0] + a
                )


def mcCacheCopier(destination):
    files = cmds.ls(type='cacheFile')
    for f in files:
        asset = mAsset(f)
        print(asset.fNucleus()[0])
        for c in asset.fNucleus()[1]:
            mCopier(asset.fPath() + c, asset.fReplace(destination)[0] + c)

        mCopier(
            asset.fPath() + asset.fNucleus()[0],
            asset.fReplace(destination)[0] + asset.fNucleus()[0]
        )


def mcAlembicCopier(destination):
    files = cmds.ls(type='AlembicNode')
    for f in files:
        asset = mAsset(f)
        mCopier(
            asset.fPath() + asset.fName(),
            asset.fReplace(destination)[1]
        )


def mcGPUCopier(destination):
    files = cmds.ls(type='gpuCache')
    for f in files:
        asset = mAsset(f)
        mCopier(
            asset.fPath() + asset.fName(),
            asset.fReplace(destination)[1]
        )


# --------------------------------------------------------------- UI
def mAssetPackUI():
    scene = cmds.file(q=True, sn=True, shn=True)
    ws = cmds.workspace(q=True, act=True)
    win = cmds.window(t='Mimmo Asset Packager', s=False, rtf=True)
    # UI
    frT = cmds.formLayout()
    fro = cmds.frameLayout(
        label='Options',
        cl=1,
        cll=1,
        p=frT,
        ec='cmds.window(\'' + win + '\', e = True, wh =[300,240])',
        cc='cmds.window(\'' + win + '\', e = True, wh =[300,140])'
    )
    frF = cmds.formLayout(p=fro)
    frS = cmds.formLayout(p=frT)
    # MAIN FORMLAYOUT ARRANGMENT
    cmds.formLayout(
        frT,
        e=True,
        af=[
            (fro, 'top', 5), (fro, 'left', 5), (fro, 'right', 5),
            (frS, 'left', 5), (frS, 'right', 5)],
        ac=[
            (frS, 'top', 5, fro)]
    )
    # FIRST FORMLAYOUT UI
    cbT = cmds.checkBox(label='Textures', p=frF, v=1)
    cbTx = cmds.checkBox(label='No TX', p=frF, v=0,)
    cbR = cmds.checkBox(label='Keep References', p=frF, v=1)
    cbA = cmds.checkBox(label='Alembic', p=frF, v=1)
    cbG = cmds.checkBox(label='GPU', p=frF, v=1)
    cbN = cmds.checkBox(label='No Nucleus', p=frF, v=0)
    cbY = cmds.checkBox(label='No Yeti', p=frF, v=0)
    cbAS = cmds.checkBox(label='No Ass Standin', p=frF, v=0)
    cb = cmds.checkBox(label='Compress', p=frF, v=0)
    omC = cmds.optionMenu(en=False, p=frF)
    omS = cmds.optionMenu(en=False, p=frF)
    cbRM = cmds.checkBox(label='Keep Package', p=frF, en=False, v=0)
    # ADD FIRST FORMLAYOUT UI COMMANDS
    cmds.checkBox(
        cbT,
        e=True,
        onc='cmds.checkBox(\'{0}\',e=True, l=\'Textures\')'.format(cbT),
        ofc='cmds.checkBox(\'{0}\',e=True, l=\'No Textures\')'.format(cbT)
    )
    cmds.checkBox(
        cbTx,
        e=True,
        onc='cmds.checkBox(\'{0}\',e=True, l=\'TX\')'.format(cbTx),
        ofc='cmds.checkBox(\'{0}\',e=True, l=\'No TX\')'.format(cbTx)
    )
    cmds.checkBox(
        cbR,
        e=True,
        onc='cmds.checkBox(\'' + cbR + '\', e=True, l=\'Keep References\')',
        ofc='cmds.checkBox(\'' + cbR + '\', e=True, l=\'Import References\')'
    )
    cmds.checkBox(
        cbA,
        e=True,
        onc='cmds.checkBox(\'' + cbA + '\', e=True, l=\'Alembic\')',
        ofc='cmds.checkBox(\'' + cbA + '\', e=True, l=\'No Alembic\')'
    )
    cmds.checkBox(
        cbG,
        e=True,
        onc='cmds.checkBox(\'' + cbG + '\', e=True, l=\'GPU\')',
        ofc='cmds.checkBox(\'' + cbG + '\', e=True, l=\'No GPU\')'
    )
    cmds.checkBox(
        cbN,
        e=True,
        onc='cmds.checkBox(\'' + cbN + '\', e=True, l=\'Nucleus\')',
        ofc='cmds.checkBox(\'' + cbN + '\', e=True, l=\'No Nucleus\')'
    )
    cmds.checkBox(
        cbY,
        e=True,
        onc='cmds.checkBox(\'' + cbY + '\', e=True, l=\'Yeti\')',
        ofc='cmds.checkBox(\'' + cbY + '\', e=True, l=\'No Yeti\')'
    )
    cmds.checkBox(
        cbAS,
        e=True,
        onc='cmds.checkBox(\'' + cbAS + '\', e=True, l=\'Ass Standin\')',
        ofc='cmds.checkBox(\'' + cbAS + '\', e=True, l=\'No Ass Standin\')'
    )
    cmdon = (
        'cmds.optionMenu(\'' + omC + '\', e=True, en=True);'
        'cmds.checkBox(\'' + cbRM + '\', e=True, en=False)'
    )
    cmdoff = (
        'cmds.optionMenu(\'' + omC + '\', e=True, en=False);'
        'cmds.optionMenu(\'' + omC + '\', e=True, v=\'zip\');'
        'cmds.optionMenu(\'' + omS + '\', e=True, en=False);'
        'cmds.checkBox(\'' + cbRM + '\', e=True, en=False)'
    )
    cmds.checkBox(
        cb,
        e=True,
        onc=cmdon,
        ofc=cmdoff
    )
    cmds.checkBox(
        cbRM,
        e=True,
        onc='cmds.checkBox(\'' + cbRM + '\', e=True, l=\'Delete Package\')',
        ofc='cmds.checkBox(\'' + cbRM + '\', e=True, l=\'Keep Package\')',
    )
    cmdoff = (
        'cmds.optionMenu(\'' + omS + '\', e=True, en=True)'
        'if cmds.optionMenu(\'' + omC + '\', q=True, v=True) != \'zip\''
        'else cmds.optionMenu(\'' + omS + '\', e=True, en=False)'
    )
    cmds.optionMenu(
        omC,
        e=True,
        cc=cmdoff
    )
    # POPULATE OPTIONMENUS
    compressors = ['zip', 'rar', '7z']
    for c in compressors:
        cmds.menuItem(label=c, p=omC)
    split = ['Full', '2g', '5g', '10g']
    for s in split:
        cmds.menuItem(label=s, p=omS)
    # FIRST FORMALYOUT ARRANGMENT
    cmds.formLayout(
        frF,
        e=True,
        af=[
            (cbT, 'top', 5), (cbT, 'left', 5),
            (cbTx, 'top', 5),
            (cbR, 'top', 5), (cbR, 'right', 5),
            (cbA, 'left', 5), (cb, 'left', 5),
            (cbY, 'left', 5)
        ],
        ac=[
            (cbTx, 'left', 5, cbT),
            (cbR, 'left', 5, cbTx),
            (cbA, 'top', 5, cbT),
            (cbG, 'top', 5, cbT), (cbG, 'left', 5, cbA),
            (cbN, 'top', 5, cbT), (cbN, 'left', 5, cbG),
            (cbY, 'top', 5, cbA),
            (cbAS, 'top', 5, cbG), (cbAS, 'left', 5, cbY),
            (cb, 'top', 5, cbY),
            (omC, 'top', 5, cbY), (omC, 'left', 5, cb),
            (omS, 'top', 5, cbY), (omS, 'left', 5, omC),
            (cbRM, 'top', 5, cbY), (cbRM, 'left', 5, omS)
        ]
    )
    # SECOND FORMLAYOUT UI
    tf1 = cmds.textField(tx=sh.os.path.join(ws, 'scenes/'), p=frS)
    bt1 = cmds.button(
        label='path',
        c='cmds.textField(\"' + tf1 + '\", e=True, tx=mA.mBrowser(3)+\"/\")',
        p=frS
    )
    tx1 = cmds.text(
        label='Package :',
        p=frS
    )
    tf2 = cmds.textField(
        tx=scene.replace('.ma', '').replace('.mb', ''),
        p=frS
    )
    tx2 = cmds.text(
        label='Asset :',
        p=frS
    )
    tf3 = cmds.textField(
        tx=scene,
        p=frS
    )
    bt2 = cmds.button(
        label='Make Package',
        p=frS,
        c='mA.mAssetPack('
        'cmds.textField(\"' + tf1 + '\", q=True, tx=True),'  # path
        'cmds.textField(\"' + tf2 + '\", q=True, tx=True),'  # package
        'cmds.textField(\"' + tf3 + '\", q=True, tx=True),'  # asset
        '[cmds.checkBox(\'' + cbT + '\', q=True, v=True),'  # Texture
        'cmds.checkBox(\'' + cbTx + '\', q=True, v=True),'   # TX
        'cmds.checkBox(\'' + cbR + '\', q=True, v=True),'  # References
        'cmds.checkBox(\'' + cbA + '\', q=True, v=True),'  # Alembic
        'cmds.checkBox(\'' + cbG + '\', q=True, v=True),'  # GPU
        'cmds.checkBox(\'' + cbN + '\', q=True, v=True),'  # Nucleus
        'cmds.checkBox(\'' + cbY + '\', q=True, v=True),'  # Yeti
        'cmds.textField(\'' + tf3 + '\', q=True, tx=True),'  # scene name
        'cmds.checkBox(\'' + cb + '\', q=True, v=True),'  # Compression
        'cmds.optionMenu(\'' + omC + '\', q=True, v=True),'  # codec
        'cmds.optionMenu(\'' + omS + '\', q=True, v=True),'  # Split
        'cmds.checkBox(\'' + cbRM + '\', q=True, v=True)])'  # Remove
    )
    # SECOND FORMALYOUT ARRANGMENT
    cmds.formLayout(
        frS,
        e=True,
        af=[
            (bt1, 'top', 5), (bt1, 'left', 5),
            (tf1, 'top', 5), (tf1, 'right', 5),
            (tx1, 'left', 5),
            (tf2, 'right', 5),
            (bt2, 'left', 5), (bt2, 'right', 5),
            (tx2, 'left', 5),
            (tf3, 'right', 5)],
        ap=[
            (bt1, 'right', 0, 20),
            (tx1, 'right', 0, 20),
            (tx2, 'right', 0, 20)],
        ac=[
            (tf1, 'left', 5, bt1),
            (tx1, 'top', 5, tf1),
            (tf2, 'top', 5, tf1), (tf2, 'left', 5, tx1),
            (tx2, 'top', 5, tf2),
            (tf3, 'top', 5, tf2), (tf3, 'left', 5, tx2),
            (bt2, 'top', 5, tf3)]
    )

    # show window and size it
    cmds.showWindow(win)
    cmds.window(win, e=True, wh=[300, 140])


# BASE DEFINITION TO RUN TOOLS
def mAssetPack(path, package, asset, UI):
    cmd, ext, mode = '', '', ''
    prj = path + package + '/'
    data = datetime.datetime.now()
    date = str(data).split(' ')[0]
    if not sh.os.path.exists(prj):
        sh.os.mkdir(prj)
    if not sh.os.path.exists(prj + 'scenes'):
        sh.os.mkdir(prj + 'scenes')
    if UI[0] == 1:  # check textures
        mTexCopier(prj, 0)
    if UI[1] == 1:  # check TX
        mTexCopier(prj, 1)
    if UI[3] == 1:  # check alembic caches
        mcAlembicCopier(prj)
    if UI[4] == 1:  # check alembic caches
        mcGPUCopier(prj)
    if UI[5] == 1:  # check nucleus caches
        mcCacheCopier(prj)
    if UI[6] == 1:  # check Yeti caches and Textures
        mcYetiCopier(prj)
    mRefereceCopier(prj, UI[2])  # check references
    # SAVE NEW SCENE
    if asset.endswith('mb'):
        mode = 'mayaBinary'
        ext = '.mb'
    else:
        mode = 'mayaAscii'
        ext = '.ma'
    cmds.file(rename=prj + 'scenes/' + asset + ext)
    cmds.file(f=True, options='v=0;', typ=mode, s=True)
    cmds.file(new=True)
    # MAKE COMPRESSED PACKAGE
    if UI[6] == 1:
        if UI[7] == 'zip':
            cmd = UI[7] + ' -9 -v -r ' + path + package + '_'
            cmd += date + ' ' + '.zip ' + prj
        elif UI[7] == 'rar':
            if UI[8] == 'Full':
                cmd = UI[7] + ' a ' + path + package + '_'
                cmd += date + ' ' + '.rar ' + prj[:-1]
            else:
                cmd = UI[7] + ' a ' + path + package + '_'
                cmd += date + ' ' + '.rar -v' + UI[8] + ' ' + prj[:-1]
        elif UI[7] == '7z':
            if UI[8] == 'Full':
                cmd = '7za a ' + path + package + '_'
                cmd += date + ' ' + '.7z ' + prj
            else:
                cmd = '7za a ' + path + package + '_'
                cmd += date + ' ' + '.7z -v' + UI[8] + ' ' + prj
    # LAUNCH COMPRESSION
    sh.os.system('gnome-terminal -t \'Compress Package\' -e \'' + cmd + '\' &')
    # DELETE ORIGINAL PACKAGE AFTER COMPRESSION
    if UI[9] == 1:
        sh.os.system('rm -R ' + prj)
    # END DIALOG
    cmds.confirmDialog(
        t='Minimo Asset Packager',
        m='Asset Package created here:\n' + prj
    )
