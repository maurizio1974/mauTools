## EXPORT ASS ON FARM
import os
import sys
import maya.cmds as cmds
import maya.mel as mel
import pickle
import atelier_utils
import importlib
importlib.reload(atelier_utils)

anamorphic ={}
anamorphic['GEX']=0

os.umask(2)

class TL_AVFX():
    def __init__(self, child=False):
        if child is False:
            if cmds.window("TL_AVFX", q=True, ex=True):
                cmds.deleteUI("TL_AVFX", wnd=True)
            self.window = cmds.window("TL_AVFX", title="TL_AVFX" )
        else:
            self.window = window

        self.workspace = cmds.workspace(q=True, rd=True)
        self.file = cmds.file(q=True, sn=True)
        self.fileName = os.path.basename(self.file)
        self.fileNameSplit = ""
        self.prod =  ""
        self.shot = ""
        self.department = ""
        self.setString = ""
        if self.workspace != "" and self.workspace !='C:/Users/thoma/Documents/maya/projects/default':
            self.workspaceSplit = (self.workspace.split("/"))
            self.prod = self.workspaceSplit[2]
            self.department = self.workspaceSplit[-4]
            self.shot =  self.workspaceSplit[-5]
            if self.fileName != "":
                self.fileNameSplit = self.fileName.split("_")
                self.setString = os.path.basename(self.file)
                print (self.setString)


        self.window = cmds.window("TL_AVFX", title="TL_AVFX")
        cmds.columnLayout()
        cmds.window(self.window, e=True, width=400)

        self.mainLogo = cmds.image(w=400,h=80,i="avfx_logo.jpg",)



        #SET TOOLS
        cmds.frameLayout(label="SCENE TOOLS",w=400,bgc=[0.3,0.3,0.3],collapsable=True,cl=False)
        self.sTglobalPanel = cmds.formLayout(bgc=[.4,.4,.4]);
        self.flProdOp = cmds.rowColumnLayout(nc=2,columnWidth=[(1,85),(2,500)],cs=[(1,0),(2,5)])
        cmds.text(label="Prod",align="right")
        self.flProdStringField = cmds.textField( text=self.prod,en=True,)
        cmds.setParent( '..' )
        self.flShotRootOp = cmds.rowColumnLayout(nc=2,columnWidth=[(1,85),(2,500)],cs=[(1,0),(2,5)])
        cmds.text(label="Shot",align="right")
        self.flShotRootStringField = cmds.textField( text=self.shot,en=True,)
        cmds.setParent( '..' )
        self.flShotTaskOp = cmds.rowColumnLayout(nc=2,columnWidth=[(1,85),(2,500)],cs=[(1,0),(2,5)])
        cmds.text(label="Task",align="right")
        self.flShotTaskStringField = cmds.textField( text=self.department,en=True,)
        cmds.setParent( '..' )
        self.flFileNameOp = cmds.rowColumnLayout(nc=2,columnWidth=[(1,85),(2,500)],cs=[(1,0),(2,5)])
        cmds.text(label="Scene",align="right")
        self.sTsetStringField = cmds.textField( text=self.setString,en=True,)
        cmds.setParent( '..' )
        self.sTseparatorGlobal_3 = cmds.separator(style="in");
        self.sTglobalOp = cmds.rowColumnLayout(nc=5,columnWidth=[(1,85),(2,125),(3,125),(4,125),(5,125)],cs=[(1,0),(2,5),(2,5),(2,5),(3,1)])
        cmds.text(label="Operation",align="right")
        self.sTbtSetCreate = cmds.button(label="Set Scene",bgc=[.77,.77,.77],c=self.setScene)
        self.sTbtSetAdd = cmds.button(label="Import 3DE",bgc=[.77,.77,.77],c=self.import3de)
        self.sTbtSetRm = cmds.button(label="Set overscan FOV",bgc=[.77,.77,.77],c=self.setOS)
        self.sTbtSetSelect = cmds.button(label="Export .abc",bgc=[.77,.77,.77],c=self.exportABC)
        cmds.setParent( '..' )
        self.sTglobalOp2 = cmds.rowColumnLayout(nc=5,columnWidth=[(1,85),(2,125),(3,125),(4,125),(5,125)],cs=[(1,0),(2,5),(2,5),(2,5),(3,1)])
        cmds.text(label="",align="right")
        self.sTbtSaveScene = cmds.button(label="Save Scene",bgc=[.77,.77,.77],c=self.saveScene)
        self.sTbtCones = cmds.button(label="Create Cones",bgc=[.77,.77,.77],c=self.createCones)
        self.sTbtCones = cmds.button(label="",bgc=[.77,.77,.77],c=self.createCones)
        self.sTbtobjTrack = cmds.button(label="Export ObjTrack .abc",bgc=[.77,.77,.77],c=self.exportObjTrackABC)
        
        cmds.formLayout(self.sTglobalPanel,edit=True,
            attachForm=[
            (self.flProdOp,'top',3),
            (self.flProdOp,'left',3),
            (self.flProdOp,'right',3),
            
            (self.flShotRootOp,'top',3),
            (self.flShotRootOp,'left',3),
            (self.flShotRootOp,'right',3),

            (self.flShotTaskOp,'top',3),
            (self.flShotTaskOp,'left',3),
            (self.flShotTaskOp,'right',3),    

            (self.flFileNameOp,'top',3),
            (self.flFileNameOp,'left',3),
            (self.flFileNameOp,'right',3),

            (self.sTseparatorGlobal_3,"left",3),
            (self.sTseparatorGlobal_3,"top",3),
            (self.sTseparatorGlobal_3,"right",3),

            (self.sTglobalOp,"left",3),
            (self.sTglobalOp,"top",3),
            (self.sTglobalOp,"right",3),

            (self.sTglobalOp2,"left",3),
            (self.sTglobalOp2,"top",3),
            (self.sTglobalOp2,"right",3),
            (self.sTglobalOp2,"bottom",3),],


            attachControl=[
            (self.flShotRootOp,"top",3,self.flProdOp),
            (self.flShotTaskOp,"top",3,self.flShotRootOp),
            (self.flFileNameOp,"top",3,self.flShotTaskOp),
            (self.sTseparatorGlobal_3,"top",3,self.flFileNameOp),
            (self.sTglobalOp,"top",3,self.sTseparatorGlobal_3),
            (self.sTglobalOp2,"top",3,self.sTglobalOp)])

        cmds.setParent( '..' )
        cmds.setParent( '..' )
        cmds.showWindow( self.window )
       

    
    def nothing(self, *args):
        self.nothing
        
    def setScene(self, *args):
        name = "{}_{}".format(self.prod, self.shot)
        atelier_utils.setScene(name)
        
    def saveScene(self, *args):
        sceneName = self.fileName
        if sceneName == "":
            sceneName = "%s_mm_v001.ma"%(self.shot)
            scenePath = "%s/scenes/%s"%(self.workspace,sceneName)
            try:
                answer = cmds.confirmDialog(
                    title='Save Scene',
                    message='Are you sure you want to save your scene as %s?'%scenePath,
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')
                if answer == 'OK':
                    if not os.path.exists(os.path.dirname(scenePath)):
                        os.makedirs(os.path.dirname(scenePath))
                    cmds.file(rename=scenePath)
                    print ('INFO: Saving scene to %s' %scenePath)
                    cmds.file(save=True, type='mayaAscii')
            except Exception as e:
                print (e)
            finally:
                self.__init__()
                cmds.showWindow( self.window )
        elif sceneName != "":
            answer = cmds.confirmDialog(
                    title='Version Up',
                    message='Are you sure you want to version up your scene ?',
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')
            if answer == 'OK':
                try:
                    current_version = sceneName.split(".")[0].split("_")[-1][1:]
                    print ("Current Version is %s"%current_version)
                    versionUp = int(current_version)+1
                    newName = "_".join(sceneName.split(".")[0].split("_")[0:-1])
                    newName = "%s_%s"%(newName,str(versionUp).zfill(3))
                    cmds.file(rn=newName)
                    print ('INFO: Saving scene to %s' %newName)
                    cmds.file(save=True, type='mayaAscii')
                except Exception as e:
                    print (e)
                finally:
                    self.__init__()
                    cmds.showWindow( self.window )
            
    def import3de(self, *args):
        pathTo3de = self.workspace.split("maya")[0]+"/3de"
        basicFilter = "*.mel"
        ret = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2,fm=1,dir=pathTo3de)
        print (ret)
        if ret is not None:
            cmds.file(ret[0],i=True)
    
    def setOS(self, *args):
        sel = cmds.ls(sl=True)
        if len(sel)>0:
            shape = cmds.listRelatives(sel[0],s=True)
            nodeType = cmds.nodeType(shape)
            if nodeType == "camera":
                pathTo3de = self.workspace.split("Maya")[0]+"/3DE"
                basicFilter = "*.pkl"
                ret = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2,fm=1,dir=pathTo3de)
                if ret is not None:
                    f	= open(ret[0],"r")
                    if not f.closed:
                        fovScale = pickle.load(f)
                        print ("# TLHOMME importing fov scale")
                        print ("#FBW = %f"%fovScale[0])
                        print ("#FBH = %f"%fovScale[1])
                        f.close()
                        cmds.setAttr("%s.horizontalFilmAperture"%shape[0],fovScale[0])
                        cmds.setAttr("%s.verticalFilmAperture"%shape[0],fovScale[1])
                        cmds.setAttr("%s.nearClipPlane"%shape[0],1)
                        cmds.setAttr("%s.farClipPlane"%shape[0],10000000)
                        if anamorphic[self.prod] == 1:
                            print ("# setting anamorphic squeezeCorrection")
                            cmds.setAttr("%s.lensSqueezeRatio"%shape[0],2.0)
                            ip =  cmds.listRelatives(shape[0],ad=True,c=True,typ="imagePlane")
                            print(ip)
                            if ip is not None:
                                if len(ip)>0:
                                    cmds.setAttr("%s.fit"%ip[0],4)
                                    cmds.setAttr("%s.squeezeCorrection"%ip[0],2.0)
                                    cmds.setAttr("%s.depth"%ip[0],100000)

    def createCones(self, *args):
        pointCloud = cmds.ls(sl=True,fl=True)
        ppos = []
        allCones = []
        for obj in pointCloud:
            ppos = cmds.pointPosition(obj)
            cone = cmds.polyCone(r=1,h=2,sx=12,sz=0,n="cone_%s"%obj)
            allCones.append(cone[0])
            cmds.setAttr("%s.rotateX"%cone[0],180)
            cmds.setAttr("%s.scaleX"%cone[0],.6)
            cmds.setAttr("%s.scaleZ"%cone[0],.6)
            cmds.move(0,1,0,"%s.scalePivot"%cone[0],ls=True)
            cmds.move(0,1,0,"%s.rotatePivot"%cone[0],ls=True)
            cmds.setAttr("%s.translateX"%cone[0],ppos[0])
            cmds.setAttr("%s.translateY"%cone[0],ppos[1]+1)
            cmds.setAttr("%s.translateZ"%cone[0],ppos[2])
            cmds.parent(cone[0],"Cones")
        cmds.select(allCones,r=True)

    def exportABC(self, *args):
        command = 'AbcExport -j "-frameRange {} {} -root {} -eulerFilter -worldSpace -uvWrite -file \\"{}\\""'
        cones = "Cones"
        geos = "Geo"
        objTrack = "ObjTrack"
        sel = cmds.ls(sl=True)
        publishPath = self.workspace.split("scripts")[0]+"output"
        version = self.fileNameSplit[-1].split(".")[0]
        camPath = publishPath+"/camera/%s_cam_%s.abc"%(self.shot,version)
        conesPath = publishPath+"/geos/%s_cones_%s.abc"%(self.shot,version)
        envPath = publishPath+"/geos/%s_geo_%s.abc"%(self.shot,version)
        objPath = publishPath+"/geos/%s_objTrack_%s.abc"%(self.shot,version)
        renderPath = publishPath+"/qts/"
        if len(sel)>0:
            camTr=sel[0]
            shape = cmds.listRelatives(camTr,s=True)
            nodeType = cmds.nodeType(shape)
            if nodeType == "camera":
                try:
                    cmds.refresh(suspend=True)
                    #export cam
                    print ("# exporting cam:\n#%s"%camPath)
                    cmds.select(camTr,r=True)
                    longName = cmds.ls(sl=True,l=True)[0]
                    frStart = int(cmds.playbackOptions(q=True, ast=True))
                    frEnd = int(cmds.playbackOptions(q=True, aet=True))
                    cmd = command.format(frStart,frEnd,longName,camPath)
                    print (cmd)
                    if not os.path.exists(os.path.dirname(camPath)):
                        os.makedirs(os.path.dirname(camPath))
                    mel.eval(cmd)
                except Exception as e:
                    print (e)
                finally:
                    cmds.refresh(suspend=False)
                    
                try:
                    cmds.refresh(suspend=True)
                    #export cones
                    print ("# exporting cones:\n#%s"%conesPath)
                    cmds.select(cones,r=True)
                    longName = cmds.ls(sl=True,l=True)[0]
                    frStart = int(cmds.playbackOptions(q=True, ast=True))
                    frEnd = int(cmds.playbackOptions(q=True, aet=True))
                    cmd = command.format(frStart,frEnd,longName,conesPath)
                    print (cmd)
                    if not os.path.exists(os.path.dirname(conesPath)):
                        os.makedirs(os.path.dirname(conesPath))
                    mel.eval(cmd)
                except Exception as e:
                    print (e)
                finally:
                    cmds.refresh(suspend=False)
                    
                try:
                    cmds.refresh(suspend=True)
                    #export env
                    print ("# exporting env:\n#%s"%envPath)
                    cmds.select(geos,r=True)
                    longName = cmds.ls(sl=True,l=True)[0]
                    frStart = int(cmds.playbackOptions(q=True, ast=True))
                    frEnd = int(cmds.playbackOptions(q=True, aet=True))
                    cmd = command.format(frStart,frEnd,longName,envPath)
                    print (cmd)
                    if not os.path.exists(os.path.dirname(envPath)):
                        os.makedirs(os.path.dirname(envPath))
                    mel.eval(cmd)
                    
                except Exception as e:
                    print (e)
                finally:
                    cmds.refresh(suspend=False)

                try:
                    cmds.refresh(suspend=True)
                    #export geo
                    cmds.select(objTrack,hi=True,r=True)
                    if len(cmds.ls(sl=True,ap=True))>1:
                        print ("# exportinfg ObjTrack:\n#%s"%objPath)
                        cmds.select(objTrack,r=True)
                        longName = cmds.ls(sl=True,l=True)[0]
                        print (longName)
                        frStart = int(cmds.playbackOptions(q=True, ast=True))
                        frEnd = int(cmds.playbackOptions(q=True, aet=True))
                        cmd = command.format(frStart,frEnd,longName,objPath)
                        print (cmd)
                        if not os.path.exists(os.path.dirname(objPath)):
                            os.makedirs(os.path.dirname(objPath))
                        mel.eval(cmd)
                    
                except Exception as e:
                    print (e)
                finally:
                    cmds.refresh(suspend=False)
                    
                try:
                    if not os.path.exists(renderPath):
                        os.makedirs(renderPath)
                except Exception as e:
                    print (e)    

    def exportObjTrackABC(self, *args):
        command = 'AbcExport -j "-frameRange {} {} -root {} -eulerFilter -worldSpace -uvWrite -file \\"{}\\""'
        cones = "Cones"
        geos = "Geo"
        objTrack = "ObjTrack"
        sel = cmds.ls(sl=True)
        publishPath = self.workspace.split("Tasks")[0]+"Publish"
        version = self.fileNameSplit[-1].split(".")[0]
        objPath = publishPath+"/geos/%s_objTrack_%s.abc"%(self.shot,version)
        renderPath = publishPath+"/qts"
        if len(sel)>0:
            camTr=sel[0]
            shape = cmds.listRelatives(camTr,s=True)
            nodeType = cmds.nodeType(shape)
            if nodeType == "camera":
                try:
                    cmds.refresh(suspend=True)
                    #export geo
                    cmds.select(objTrack,hi=True,r=True)
                    if len(cmds.ls(sl=True,ap=True))>1:
                        print ("# exportinfg ObjTrack:\n#%s"%objPath)
                        cmds.select(objTrack,r=True)
                        longName = cmds.ls(sl=True,l=True)[0]
                        print (longName)
                        frStart = int(cmds.playbackOptions(q=True, ast=True))
                        frEnd = int(cmds.playbackOptions(q=True, aet=True))
                        cmd = command.format(frStart,frEnd,longName,objPath)
                        print (cmd)
                        if not os.path.exists(os.path.dirname(objPath)):
                            os.makedirs(os.path.dirname(objPath))
                        mel.eval(cmd)
                    
                except Exception as e:
                    print (e)
                finally:
                    cmds.refresh(suspend=False)
                    
                try:
                    if not os.path.exists(renderPath):
                        os.makedirs(renderPath)
                except Exception as e:
                    print (e)    

                
                
                
                
                

def tlAvfxTools():
    tlAvfxToolsWin = TL_AVFX()
    cmds.dockControl( area='left', content=tlAvfxToolsWin.window)

if __name__ == "__main__":
    tlAvfxTools()