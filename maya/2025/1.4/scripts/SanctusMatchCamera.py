# somesanctus@yandex.ru
# 01.06.2011

import maya.cmds as cmds
import sys
from functools import partial
import maya.mel as mel

MayaVer = mel.eval('getApplicationVersionAsFloat()')
plugin = 'cameraFinderNodes.py'
state = cmds.pluginInfo(plugin, query=True, loaded=True)
if (state == False):
	cmds.loadPlugin(plugin)
state = cmds.pluginInfo(plugin, query=True, loaded=True)
if (state == False):
	sys.exit()

def imageImporter():
	if (MayaVer < 2011.0):
		f = unicode(cmds.fileDialog(mode = 0))
		return f
	else:
		f = cmds.fileDialog2(dialogStyle = 2,fileMode = 1)
		if f != None:
			return f[0]
	'''
	if f==None:
		return None
		#matchCamEditor.clearSceneFromData()
		#sys.exit()
	else:	
		print f
		return f[0]
	'''
def createNodes():
	
	positionList=(((-4.5,0,25),(-22.5,0,17),(21,0,-23),(-5,0,-30)),
	              ((-32.5,0,-17.5),(-25,0,15),(22.5,0,-20),(19,0,10)),
	              ((0,0,26),(18,0,12),(-32,0,-21),(-7.5,0,-30)))
	              
	axisList='X','Y','Z'
	i=0
	listOfObj=[]
	for axis in positionList:
		n=1
		for point in axis:
			listOfObj.append( cmds.spaceLocator( name = "locator"+axisList[i]+str(n))[0])
			cmds.move(point[0],point[1],point[2])
			n=n+1
		i=i+1
			
	for axis in axisList:
		listOfObj.append(cmds.curve(name=('curve'+axis+'1'), degree=1, point=[(0, 0, 0), (0, 0, 0)]))
		listOfObj.append(cmds.curve(name=('curve'+axis+'2'), degree=1, point=[(0, 0, 0), (0, 0, 0)]))
		
	listOfObj.append(cmds.curve(name='horizon', degree=1, point=[(0, 0, 0), (0, 0, 0)]))
	
	listOfObj.append( cmds.spaceLocator( name = 'orientCheker')[0])
	cmds.move(-4,0,-9)
	
	
	for axis in axisList:
		listOfObj.append(cmds.curve(name=('orientChekerLine'+axis), degree=1, point=[(0, 0, 0), (0, 0, 0)]))
		
	for axis in axisList:
		listOfObj.append(cmds.createNode( 'vanishingPoint', name=('vanishingPoint'+axis)))
	
	listOfObj.append(cmds.createNode( 'cameraFinder' ,name='cameraFinder'))
	
	"""   
	x=0	
	for ex in listOfObj:
	
	    print x, ex
	    x=x+1
	"""
	
	
	#locator>line
	cmds.connectAttr(listOfObj[0]+'.translate', cmds.listRelatives(listOfObj[12],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[1]+'.translate', cmds.listRelatives(listOfObj[12],shapes=True)[0]+'.controlPoints[1]')
	cmds.connectAttr(listOfObj[2]+'.translate', cmds.listRelatives(listOfObj[13],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[3]+'.translate', cmds.listRelatives(listOfObj[13],shapes=True)[0]+'.controlPoints[1]')
	
	cmds.connectAttr(listOfObj[4]+'.translate', cmds.listRelatives(listOfObj[14],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[5]+'.translate', cmds.listRelatives(listOfObj[14],shapes=True)[0]+'.controlPoints[1]')
	cmds.connectAttr(listOfObj[6]+'.translate', cmds.listRelatives(listOfObj[15],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[7]+'.translate', cmds.listRelatives(listOfObj[15],shapes=True)[0]+'.controlPoints[1]')
	
	cmds.connectAttr(listOfObj[8]+'.translate', cmds.listRelatives(listOfObj[16],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[9]+'.translate', cmds.listRelatives(listOfObj[16],shapes=True)[0]+'.controlPoints[1]')
	cmds.connectAttr(listOfObj[10]+'.translate', cmds.listRelatives(listOfObj[17],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[11]+'.translate', cmds.listRelatives(listOfObj[17],shapes=True)[0]+'.controlPoints[1]')
	
	#horizont
	cmds.connectAttr(listOfObj[23]+'.output', cmds.listRelatives(listOfObj[18],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[25]+'.output', cmds.listRelatives(listOfObj[18],shapes=True)[0]+'.controlPoints[1]')
	
	#locators>vanishingPointX
	cmds.connectAttr(listOfObj[0]+'.translateX', listOfObj[23]+'.input10')
	cmds.connectAttr(listOfObj[0]+'.translateZ', listOfObj[23]+'.input11')
	
	cmds.connectAttr(listOfObj[1]+'.translateX', listOfObj[23]+'.input20')
	cmds.connectAttr(listOfObj[1]+'.translateZ', listOfObj[23]+'.input21')
	
	cmds.connectAttr(listOfObj[2]+'.translateX', listOfObj[23]+'.input30')
	cmds.connectAttr(listOfObj[2]+'.translateZ', listOfObj[23]+'.input31')
	
	cmds.connectAttr(listOfObj[3]+'.translateX', listOfObj[23]+'.input40')
	cmds.connectAttr(listOfObj[3]+'.translateZ', listOfObj[23]+'.input41')
	
	
	#locators>vanishingPointY	
	cmds.connectAttr(listOfObj[4]+'.translateX', listOfObj[24]+'.input10')
	cmds.connectAttr(listOfObj[4]+'.translateZ', listOfObj[24]+'.input11')
	
	cmds.connectAttr(listOfObj[5]+'.translateX', listOfObj[24]+'.input20')
	cmds.connectAttr(listOfObj[5]+'.translateZ', listOfObj[24]+'.input21')
	
	cmds.connectAttr(listOfObj[6]+'.translateX', listOfObj[24]+'.input30')
	cmds.connectAttr(listOfObj[6]+'.translateZ', listOfObj[24]+'.input31')
	
	cmds.connectAttr(listOfObj[7]+'.translateX', listOfObj[24]+'.input40')
	cmds.connectAttr(listOfObj[7]+'.translateZ', listOfObj[24]+'.input41')
	
	#locators>vanishingPointZ	
	cmds.connectAttr(listOfObj[8]+'.translateX', listOfObj[25]+'.input10')
	cmds.connectAttr(listOfObj[8]+'.translateZ', listOfObj[25]+'.input11')
	
	cmds.connectAttr(listOfObj[9]+'.translateX', listOfObj[25]+'.input20')
	cmds.connectAttr(listOfObj[9]+'.translateZ', listOfObj[25]+'.input21')
	
	cmds.connectAttr(listOfObj[10]+'.translateX', listOfObj[25]+'.input30')
	cmds.connectAttr(listOfObj[10]+'.translateZ', listOfObj[25]+'.input31')
	
	cmds.connectAttr(listOfObj[11]+'.translateX', listOfObj[25]+'.input40')
	cmds.connectAttr(listOfObj[11]+'.translateZ', listOfObj[25]+'.input41')
	
	#vaishingPoint>cameraFinder
	cmds.connectAttr(listOfObj[23]+'.output', listOfObj[26]+'.input1' )
	cmds.connectAttr(listOfObj[24]+'.output', listOfObj[26]+'.input2' )
	cmds.connectAttr(listOfObj[25]+'.output', listOfObj[26]+'.input3' )
	
	#vanishingPoint>orientCheker
	cmds.connectAttr(listOfObj[19]+'.translate', cmds.listRelatives(listOfObj[20],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[23]+'.output', cmds.listRelatives(listOfObj[20],shapes=True)[0]+'.controlPoints[1]')
	
	cmds.connectAttr(listOfObj[19]+'.translate', cmds.listRelatives(listOfObj[21],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[24]+'.output', cmds.listRelatives(listOfObj[21],shapes=True)[0]+'.controlPoints[1]')
	
	cmds.connectAttr(listOfObj[19]+'.translate', cmds.listRelatives(listOfObj[22],shapes=True)[0]+'.controlPoints[0]')
	cmds.connectAttr(listOfObj[25]+'.output', cmds.listRelatives(listOfObj[22],shapes=True)[0]+'.controlPoints[1]')

	#setcolors
	red = 0, 1, 2, 3, 12, 13 ,20
	green = 4 ,5, 6, 7, 14, 15, 21
	blue = 8, 9, 10, 11, 16, 17, 22
	yellow = 18
	
	for i in red:
	    cmds.setAttr(listOfObj[i]+'.overrideEnabled', True )
	    cmds.setAttr(listOfObj[i]+'.overrideColor', 13)
	    
	for i in green:
	    cmds.setAttr(listOfObj[i]+'.overrideEnabled', True )
	    cmds.setAttr(listOfObj[i]+'.overrideColor', 14)
	    
	for i in blue:
	    cmds.setAttr(listOfObj[i]+'.overrideEnabled', True )
	    cmds.setAttr(listOfObj[i]+'.overrideColor', 6)
	    
	cmds.setAttr(listOfObj[18]+'.overrideEnabled', True )
	cmds.setAttr(listOfObj[18]+'.overrideColor', 17)
	
	#locked
	locked=12,13,14,15,16,17,18,20,21,22
	attr=".translateX",".translateY",".translateZ",".rotateX",".rotateY",".rotateZ",".scaleX",".scaleY",".scaleZ"
	
	for i in locked:
	    for a in attr:
	        cmds.setAttr(listOfObj[i]+a, lock=True)
	        
	listOfObj.append( cmds.spaceLocator( name = "center")[0])
	cmds.connectAttr(listOfObj[26]+'.output', listOfObj[27]+'.translate')
	
	return listOfObj    	
	
def exportCamera(list, imageName, blah):
	
	'''
	a=0
	for i in list:
		print a,i
		a=a+1
	'''	
	vpx=cmds.spaceLocator(name='vpx')[0]	
	vpy=cmds.spaceLocator(name='vpy')[0]
	
	cmds.connectAttr(list[23]+'.output',vpx+'.translate')
	cmds.connectAttr(list[24]+'.output',vpy+'.translate')
	
	if (cmds.getAttr(vpy+'.translateZ')<0):
		constraint=cmds.aimConstraint(vpx, list[27], worldUpType='object', worldUpObject=vpy, upVector=(0.0, 1.0, 0.0) )
	else:
		constraint=cmds.aimConstraint(vpx, list[27], worldUpType='object', worldUpObject=vpy, upVector=(0.0, -1.0, 0.0) )
	
	
	
	camExp=cmds.camera(name='cameraExported')[0]
	cmds.setAttr(camExp+'.rotate', -90,0,0, type="double3")
	cmds.parent(camExp, list[27])
	cmds.setAttr(camExp+'.translate', 0,0,0, type="double3")
	
	cmds.delete(constraint)
	cmds.delete(vpx)
	cmds.delete(vpy)
	
	cmds.setAttr(list[27]+'.rotate', 0,0,0, type="double3")	
	


	image = cmds.createNode('imagePlane')
		
	cmds.connectAttr(image+'.message', camExp+'.imagePlane[0]')
	cmds.setAttr((image+'.lockedToCamera'),1)
	cmds.setAttr((image+'.type'),0)
	cmds.setAttr((image+'.imageName'), imageName, type ='string')
	cmds.setAttr((image+'.sizeY'),((cmds.getAttr(image+'.sizeX'))*(cmds.getAttr(image+'.coverageY'))/(cmds.getAttr(image+'.coverageX'))))
	
	cmds.parent(camExp,world=True)
	cmds.setAttr(camExp+'.translate', 0,0,0, type="double3")
	cmds.setAttr(camExp+'.rotateX', lock=True)
	cmds.setAttr(camExp+'.rotateY', lock=True)
	cmds.setAttr(camExp+'.rotateZ', lock=True)
	
	height=cmds.getAttr(list[27]+'.translateY')
	cmds.camera(camExp, edit=True, focalLength = (height/100)*36 )
	
	
def warningMessage():
	confurm = cmds.confirmDialog( title='Confirm', message='All data about matching will be deleted. Proceed?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
	if (confurm == "Yes"):
		return 1
	else:
		return 0



class matchCamEditor():
	def __init__(self):
		self.name = 'sanctusMatchCam'
		self.list = createNodes()

		self.checkWindow()
		self.image = imageImporter()
		if self.image == None:
			self.image = "C:\Program Files\Autodesk\Maya2013\icons\MayaStartupImage.png"
		self.camCreation()

		self.uiCreation()
		cmds.selectType(nurbsCurve=False)
	def checkWindow(self):
		if cmds.window(self.name, exists=True):
			print 'window exist'
			if warningMessage():
				cmds.deleteUI(self.name)
				print "confurm yes"
			else:
				sys.exit()
				print "confurm no"
		else:
			print "no window found"

	def clearSceneFromData(self):
		if warningMessage():
			self.list.reverse()
			for obj in self.list[1:]:
				cmds.delete(obj)
				# print obj, 'deleted'
			cmds.delete( self.list[0] )
			cmds.delete( self.cam )
			cmds.selectType(nurbsCurve=True)
			print 'scene cleared'
		else:
			self.uiCreation()

	def camCreation(self):
		self.cam = cmds.camera(name = 'SpecialCamera')
		camTransform = self.cam[0]
		cmds.move(0, 1000, 0)
		cmds.rotate(-90,0,0)
		img_plane = cmds.createNode('imagePlane')
		if MayaVer >= 2013.0:
			cmds.parent(img_plane, camTransform )
		cmds.setAttr((self.cam[1] + '.orthographic'), 1)
		cmds.setAttr((self.cam[1] + '.farClipPlane'), 2000)
		cmds.setAttr((self.cam[1] + '.orthographicWidth'), 100)
		cmds.connectAttr(img_plane+'.message', self.cam[1]+'.imagePlane[0]')
		cmds.setAttr((img_plane+'.lockedToCamera'),0)
		cmds.setAttr((img_plane+'.width'),100)
		cmds.setAttr((img_plane+'.height'),100)
		cmds.setAttr((img_plane+'.type'),0)
		if MayaVer >= 2013.0:
			cmds.setAttr((img_plane+ '.imageCenterY'),-1)
		else:
			cmds.setAttr((img_plane+ '.centerY'),-1)
		cmds.setAttr((img_plane+'.imageName'), self.image, type ='string')

	def uiCreation(self):

		cmds.window(self.name,title = 'Match Camera', retain = 0)
		form = cmds.formLayout()
		
		editor = cmds.modelEditor(camera = self.cam[1], grid = 0)
		c=cmds.columnLayout(adjustableColumn = 1)
		#cmds.rowLayout(numberOfColumns=3)
		#cmds.button(label='another image')
		#cmds.button(label='check')
		cmds.button(label='export', command=partial(exportCamera, self.list, self.image) )

		cmds.formLayout(form, edit=True, attachForm=[(c,'top',0),(c,'left',0),(editor,'top',0),(editor,'bottom',0),(editor,'right',0)],attachNone=[(c,'bottom'),(c,'right')],attachControl=(editor,'left',0,c))
		cmds.showWindow(self.name)
		#cmds.window(self.name, edit=True,widthHeight=(1024, 720))

		self.jobNum = cmds.scriptJob(uiDeleted=[self.name, self.clearSceneFromData])
		print 'scriptJob Number', self.jobNum,'started'


	def __del__(self):
		print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"






#matchCamEditor()
