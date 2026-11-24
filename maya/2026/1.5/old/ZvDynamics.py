'''
ZV Dynamics

Usage:

import ZvDynamics
ZvDynamics.ZvDynamics()
'''

__author__ = "Paolo Dominici (paolodominici@gmail.com)"
__version__ = "2.0"
__date__ = "2012/08/01"
__copyright__ = "Copyright (c) 2007-2012 Paolo Dominici"

import sys, webbrowser
from maya import cmds

_rkNode = "rungeKutta"
_lastSettings = [-1]
_methodsRB = ["ZvParticleRB", "ZvNParticleRB", "ZvRungeKuttaRB"]
_isQt = not cmds.about(version=True).split()[0] in ['8.5', '2008', '2009', '2010']

def rungeKuttaMethod(obj, stiffness=0.5, dampingRatio=0.5, transfShapes=False):
	"Metodo di dinamica basata su runge-kutta"
	
	objNoPath = obj[obj.rfind("|")+1:]
	dynName = objNoPath + "_DYN"
	
	pos = cmds.xform(obj, q=True, rp=True, ws=True)
	
	# nodo runge-kutta
	rkNode = cmds.createNode("rungeKutta", n=objNoPath + "_RK")
	
	# oggetto init
	initObj = drawOct(objNoPath + "_INIT", r=0.25, pos=pos)
	
	# colora lo shape
	octShapeName = cmds.listRelatives(initObj, s=True, pa=True)[0]
	cmds.setAttr(octShapeName + ".overrideEnabled", True)
	cmds.setAttr(octShapeName + ".overrideColor", 13)

	# se e' attivo transfer shapes uso un gruppo invece di creare il cubetto
	if transfShapes:
		dyn = cmds.group(n=dynName, em=True)
	else:
		# cubetto colorato di blu orientato secondo l'oggetto
		dyn = drawCube(dynName, l=0.5)
		cubeShape = cmds.listRelatives(dyn, s=True, pa=True)[0]
		cmds.setAttr(cubeShape + ".overrideEnabled", True)		# colore
		cmds.setAttr(cubeShape + ".overrideColor", 6)
	
	# ruoto il cubetto (molto + carino)
	cmds.xform(dyn, ro=cmds.xform(obj, q=True, ro=True, ws=True), ws=True)
	cmds.xform(dyn, t=pos, ws=True)
	dyn = cmds.parent(dyn, obj)[0]
	cmds.makeIdentity(dyn, apply=True)						# in questo modo il cubo assume le coordinate dell'oggetto pur essendo posizionato nel suo pivot
	
	# aggiungo gli attributi
	cmds.addAttr(obj, ln="info", at="enum", en=" ", keyable=True)
	cmds.setAttr(obj + ".info", l=True)
	cmds.addAttr(obj, ln="velocity", at="double3")
	cmds.addAttr(obj, ln="velocityX", at="double", p="velocity", k=True)
	cmds.addAttr(obj, ln="velocityY", at="double", p="velocity", k=True)
	cmds.addAttr(obj, ln="velocityZ", at="double", p="velocity", k=True)
	# not keyable
#	[cmds.setAttr("%s.%s" % (dyn, s), cb=True) for s in ["velocityX", "velocityY", "velocityZ"]]
	cmds.addAttr(dyn, ln="settings", at="enum", en=" ", keyable=True)
	cmds.setAttr(dyn + ".settings", l=True)
	cmds.addAttr(dyn, ln="iterations", at="long", min=1, max=5, dv=1)
	cmds.setAttr(dyn + ".iterations", cb=True)
	cmds.addAttr(dyn, ln="dynamicsBlend", at="double", min=0.0, max=1.0, dv=1.0, keyable=True)
	cmds.addAttr(dyn, ln="stiffness", at="double", min=0.0, dv=stiffness, keyable=True)
	cmds.addAttr(dyn, ln="dampingRatio", at="double", min=0.0, max=1.0, dv=dampingRatio, keyable=True)

	# parento dyn allo stesso parente dell'oggetto
	parentObj = cmds.listRelatives(obj, p=True, pa=True)
	if parentObj:
		dyn = cmds.parent([dyn, parentObj[0]])[0]
	else:
		dyn = cmds.parent(dyn, w=True)[0]
	
	# parento l'oggetto dentro il DYN
	obj = cmds.parent(obj, dyn)[0]
	
	# point constraint dell'init sul dyn in modo da sapere sempre le sue coord nello spazio di coord del suo parente
	pcInit = cmds.createNode("pointConstraint", n=objNoPath + "_INIT_PC")
	# locco gli attrs del pointConstraint
	[cmds.setAttr("%s.%s" % (pcInit, s), k=False, l=True) for s in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v", "offsetX", "offsetY", "offsetZ"]]
	cmds.connectAttr(dyn + ".t", pcInit + ".target[0].targetTranslate")
	cmds.connectAttr(dyn + ".parentMatrix[0]", pcInit + ".target[0].targetParentMatrix")
	cmds.connectAttr(dyn + ".rotatePivotTranslate", pcInit + ".target[0].targetRotateTranslate")
	cmds.connectAttr(dyn + ".rotatePivot", pcInit + ".target[0].targetRotatePivot")
	# connetti il pointConstraint all'oggetto
	cmds.connectAttr(pcInit + ".constraintTranslate", initObj + ".t")
	cmds.connectAttr(initObj + ".parentInverseMatrix[0]", pcInit + ".constraintParentInverseMatrix")
	cmds.connectAttr(initObj + ".rotatePivotTranslate", pcInit + ".constraintRotateTranslate")
	cmds.connectAttr(initObj + ".rotatePivot", pcInit + ".constraintRotatePivot")
	
	# connetti la traslazione dell'init a rk
	cmds.connectAttr(pcInit + ".constraintTranslate", rkNode + ".tp")
	# parento il constraint all'initObj
	cmds.parent(pcInit, initObj, r=True)
	# connetti il nodo rk al tempo
	cmds.connectAttr(cmds.ls(type="time")[0] + ".o", rkNode + ".t")
	
	# parametri
	cmds.connectAttr(dyn + ".stiffness", rkNode + ".k")
	cmds.connectAttr(dyn + ".dampingRatio", rkNode + ".dr")
	cmds.connectAttr(dyn + ".iterations", rkNode + ".fi")
	cmds.connectAttr(rkNode + ".ov", obj + ".velocity")
	
	# point constraint per il blend, prende gli attributi dall'init
	pcBlend = cmds.createNode("pointConstraint", n=objNoPath + "_PC")
	# locco gli attrs del pointConstraint
	[cmds.setAttr("%s.%s" % (pcBlend, s), k=False) for s in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v", "offsetX", "offsetY", "offsetZ"]]
	cmds.connectAttr(initObj + ".t", pcBlend + ".target[0].targetTranslate")
	cmds.connectAttr(rkNode + ".op", pcBlend + ".target[1].targetTranslate")
	cmds.connectAttr(initObj + ".parentMatrix[0]", pcBlend + ".target[0].targetParentMatrix")
	cmds.connectAttr(initObj + ".parentMatrix[0]", pcBlend + ".target[1].targetParentMatrix")
	cmds.connectAttr(initObj + ".rotatePivotTranslate", pcBlend + ".target[0].targetRotateTranslate")
	cmds.connectAttr(initObj + ".rotatePivotTranslate", pcBlend + ".target[1].targetRotateTranslate")
	cmds.connectAttr(initObj + ".rotatePivot", pcBlend + ".target[0].targetRotatePivot")
	cmds.connectAttr(initObj + ".rotatePivot", pcBlend + ".target[1].targetRotatePivot")
	# connetti il pointConstraint all'oggetto
	cmds.connectAttr(pcBlend + ".constraintTranslate", obj + ".t")
	cmds.connectAttr(obj + ".parentInverseMatrix[0]", pcBlend + ".constraintParentInverseMatrix")
	cmds.connectAttr(obj + ".rotatePivotTranslate", pcBlend + ".constraintRotateTranslate")
	cmds.connectAttr(obj + ".rotatePivot", pcBlend + ".constraintRotatePivot")
	
	# blend
	cmds.connectAttr(dyn + ".dynamicsBlend", pcBlend + ".target[1].targetWeight")
	revNode = cmds.createNode("reverse", n=objNoPath + "_REV")
	cmds.connectAttr(dyn + ".dynamicsBlend", revNode + ".inputX")
	cmds.connectAttr(revNode + ".outputX", pcBlend + ".target[0].targetWeight")
	
	# parento il constraint all'obj
	cmds.parent(pcBlend, obj, r=True)
	
	cmds.hide(initObj)
	
	# se il check e' attivo trasferisci le geometrie nel nodo dinamico
	if transfShapes:
		shapes = cmds.listRelatives(obj, s=True, pa=True)
		if shapes:
			cmds.parent(shapes, dyn, r=True, s=True)
	
	# locks
	[cmds.setAttr("%s.%s" % (rkNode, s), l=True) for s in ["t", "k", "dr", "fi", "tpx", "tpy", "tpz"]]
	[cmds.setAttr("%s.%s" % (revNode, s), l=True) for s in ["inputX", "inputY", "inputZ"]]
	[cmds.setAttr("%s.%s" % (initObj, s), k=False, cb=True) for s in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]]
	
	return dyn

def particleMethod(obj, weight=0.5, conserve=1.0, transfShapes=False):
	return _particleDyn(obj, weight, conserve, transfShapes, False)

def nParticleMethod(obj, weight=0.5, conserve=1.0, transfShapes=False):
	return _particleDyn(obj, weight, conserve, transfShapes, True)

def _particleDyn(obj, weight, conserve, transfShapes, nucleus):
	"Metodo generico di dinamica basata sulla particella"
	c = obj
	
	cNoPath = c[c.rfind("|")+1:]
	dynName = cNoPath + "_DYN"
	partName = cNoPath + "_INIT"
	dynLocName = cNoPath + "_DYN_LOC"
	statLocName = cNoPath + "_STAT_LOC"
	revName = cNoPath + "_REV"
	exprName = cNoPath + "_Expression"
	octName = cNoPath + "Oct"
	
	# leggo la posizione dell'oggetto
	pos = cmds.xform(c, q=True, rp=True, ws=True)
	
	# creo la particella
	if nucleus:
		partic, partShape = cmds.nParticle(n=partName, p=pos)
	else:
		partic, partShape = cmds.particle(n=partName, p=pos)
	
	partShape = "%s|%s" % (partic, partShape)
	
	# sposto il pivot
	cmds.xform(partic, piv=pos, ws=True)
	# aggiungo uno shape alla particella
	octName = drawOct(octName, r=0.25, pos=pos)
	octShapeName = cmds.listRelatives(octName, s=True, pa=True)[0]
	
	cmds.setAttr(octShapeName + ".overrideEnabled", True)
	cmds.setAttr(octShapeName + ".overrideColor", 13)
	cmds.parent([octShapeName, partic], s=True, r=True)
	cmds.delete(octName)
	
	# creo i locator
	statLocGrp = cmds.group("|" + cmds.spaceLocator(n=statLocName)[0], n="g_" + statLocName)
	dynLocGrp = cmds.group("|" + cmds.spaceLocator(n=dynLocName)[0], n="g_" + dynLocName)
	cmds.setAttr("|%s|%s.overrideEnabled" % (dynLocGrp, dynLocName), True)
	cmds.setAttr("|%s|%s.overrideColor" % (dynLocGrp, dynLocName), 6)
	
	# se e' attivo transfer shapes uso un gruppo invece di creare il cubetto
	if transfShapes:
		dyn = cmds.group(n=dynName, em=True)
	else:
		# cubetto colorato di blu orientato secondo l'oggetto
		dyn = drawCube(dynName, l=0.5)
		cubeShape = cmds.listRelatives(dyn, s=True, pa=True)[0]
		cmds.setAttr(cubeShape + ".overrideEnabled", True)		# colore
		cmds.setAttr(cubeShape + ".overrideColor", 6)
	
	# ruoto il cubetto e i locator (molto + carino)
	cmds.xform(["|" + statLocGrp, "|" + dynLocGrp, dyn], ro=cmds.xform(c, q=True, ro=True, ws=True), ws=True)
	cmds.xform(["|" + statLocGrp, "|" + dynLocGrp, dyn], t=pos, ws=True)
	dyn = cmds.parent([dyn, c])[0]
	cmds.makeIdentity(dyn, apply=True)						# in questo modo il cubo assume le coordinate dell'oggetto pur essendo posizionato nel suo pivot
	
	# parento dyn allo stesso parente dell'oggetto
	parentObj = cmds.listRelatives(c, p=True, pa=True)
	if parentObj:
		dyn = cmds.parent([dyn, parentObj[0]])[0]
	else:
		dyn = cmds.parent(dyn, w=True)[0]
	c = cmds.parent([c, dyn])[0]
	
	cmds.parent(["|" + statLocGrp, "|" + dynLocGrp, dyn])
	
	# aggiorna i nomi con i percorsi
	statLocGrp = "%s|%s" % (dyn, statLocGrp)
	dynLocGrp = "%s|%s" % (dyn, dynLocGrp)
	statLoc = "%s|%s" % (statLocGrp, statLocName)
	dynLoc = "%s|%s" % (dynLocGrp, dynLocName)
	
	# goal particella-loc statico
	cmds.goal(partic, g=statLoc, utr=True, w=weight)
	
	# nascondo locator
	cmds.hide([statLocGrp, dynLocGrp])
	
	# rendo template la particella
	cmds.setAttr(partShape + '.template', True)
	
	# aggiungo l'attributo di velocita'
	cmds.addAttr(c, ln="info", at="enum", en=" ", keyable=True)
	cmds.setAttr(c + ".info", l=True)
	cmds.addAttr(c, ln="velocity", at="double3")
	cmds.addAttr(c, ln="velocityX", at="double", p="velocity", k=True)
	cmds.addAttr(c, ln="velocityY", at="double", p="velocity", k=True)
	cmds.addAttr(c, ln="velocityZ", at="double", p="velocity", k=True)

	# point oggetto tra i locator statico e dinamico
	pc = cmds.pointConstraint(statLoc, dynLoc, c, n=cNoPath + "_PC")[0]
	cmds.addAttr(dyn, ln="settings", at="enum", en=" ", keyable=True)
	cmds.setAttr(dyn + ".settings", l=True)
	cmds.addAttr(dyn, ln="dynamicsBlend", at="double", min=0.0, max=1.0, dv=1.0, keyable=True)
	cmds.addAttr(dyn, ln="weight", at="double", min=0.0, max=1.0, dv=weight, keyable=True)
	cmds.addAttr(dyn, ln="conserve", at="double", min=0.0, max=1.0, dv=conserve, keyable=True)
	rev = cmds.createNode("reverse", n=revName)
	cmds.connectAttr(dyn + ".dynamicsBlend", pc + ".w1")
	cmds.connectAttr(dyn + ".dynamicsBlend", rev + ".inputX")
	cmds.connectAttr(rev + ".outputX", pc + ".w0")
	cmds.connectAttr(dyn + ".weight", partShape + ".goalWeight[0]")
	cmds.connectAttr(dyn + ".conserve", partShape + ".conserve")
	# locco il point constraint
	[cmds.setAttr("%s.%s" % (pc, s), l=True) for s in ["offsetX", "offsetY", "offsetZ", "w0", "w1", "nodeState"]]
	# locco il reverse
	[cmds.setAttr("%s.%s" % (revName, s), l=True) for s in ["inputX", "inputY", "inputZ"]]
	
	# nParticle
	if nucleus:
		nucleusNode = cmds.listConnections(partShape + ".currentState")[0]
		cmds.setAttr(nucleusNode + '.gravity', 0.0)
		
		expr = """// rename if needed
string $dynHandle = "%s";
string $particleObject = "%s";
string $dynLocator = "%s";

undoInfo -swf 0;
$ast = `playbackOptions -q -ast`;
if (`currentTime -q` - $ast < 2) {
//	%s.startFrame = $ast;						// remove it if you don't want to change nucleus start time
	$destPiv = `xform -q -rp -ws $dynHandle`;
	$origPiv = `xform -q -rp -ws $particleObject`;
	xform -t ($destPiv[0]-$origPiv[0]) ($destPiv[1]-$origPiv[1]) ($destPiv[2]-$origPiv[2]) -r -ws $particleObject;
}

$zvPos = `getParticleAttr -at worldPosition ($particleObject + ".pt[0]")`;
$currUnit = `currentUnit -q -linear`;
if ($currUnit != "cm") {
	$zvPos[0] = `convertUnit -f "cm" -t $currUnit ((string)$zvPos[0])`;
	$zvPos[1] = `convertUnit -f "cm" -t $currUnit ((string)$zvPos[1])`;
	$zvPos[2] = `convertUnit -f "cm" -t $currUnit ((string)$zvPos[2])`;
}
xform -a -ws -t $zvPos[0] $zvPos[1] $zvPos[2] $dynLocator;
$zvVel = `getParticleAttr -at velocity ($particleObject + ".pt[0]")`;		// velocity relative to the particleObject
%s.velocityX = $zvVel[0];
%s.velocityY = $zvVel[1];
%s.velocityZ = $zvVel[2];
undoInfo -swf 1;""" % (dyn, partic, dynLocName, nucleusNode, c, c, c)
	
	# particella standard
	else:
		cmds.setAttr(partic + ".visibility", False)
		expr = """// rename if needed
string $dynHandle = "%s";
string $particleObject = "%s";
string $dynLocator = "%s";

undoInfo -swf 0;
$ast = `playbackOptions -q -ast`;
if (`currentTime -q` - $ast < 2) {
	%s.startFrame = $ast;
	$destPiv = `xform -q -rp -ws $dynHandle`;
	$origPiv = `xform -q -rp -ws $particleObject`;
	xform -t ($destPiv[0]-$origPiv[0]) ($destPiv[1]-$origPiv[1]) ($destPiv[2]-$origPiv[2]) -r -ws $particleObject;
}

$zvPos = `getParticleAttr -at worldPosition ($particleObject + ".pt[0]")`;
$currUnit = `currentUnit -q -linear`;
if ($currUnit != "cm") {
	$zvPos[0] = `convertUnit -f "cm" -t $currUnit ((string)$zvPos[0])`;
	$zvPos[1] = `convertUnit -f "cm" -t $currUnit ((string)$zvPos[1])`;
	$zvPos[2] = `convertUnit -f "cm" -t $currUnit ((string)$zvPos[2])`;
}
xform -a -ws -t $zvPos[0] $zvPos[1] $zvPos[2] $dynLocator;
$zvVel = `getParticleAttr -at velocity ($particleObject + ".pt[0]")`;		// velocity relative to the particleObject
%s.velocityX = $zvVel[0];
%s.velocityY = $zvVel[1];
%s.velocityZ = $zvVel[2];
undoInfo -swf 1;""" % (dyn, partic, dynLocName, partShape, c, c, c)
	
	# crea l'espressione
	cmds.expression(n=exprName, s=expr)
	
	# se il check e' attivo trasferisci le geometrie nel nodo dinamico
	if transfShapes:
		shapes = cmds.listRelatives(c, s=True, pa=True)
		if shapes:
			cmds.parent(shapes + [dyn], r=True, s=True)
	
	# locks
	[cmds.setAttr(partic + s, k=False, cb=True) for s in [".tx", ".ty", ".tz", ".rx", ".ry", ".rz", ".sx", ".sy", ".sz", ".v", ".startFrame"]]
	
	return dyn

def drawOct(name, r=1.0, pos=(0.0, 0.0, 0.0)):
	p = [(s[0]+pos[0], s[1]+pos[1], s[2]+pos[2]) for s in [(0, 0, r), (r, 0, 0), (0, 0, -r), (-r, 0, 0), (0, -r, 0), (r, 0, 0), (0, r, 0), (-r, 0, 0), (0, 0, r), (0, r, 0), (0, 0, -r), (0, -r, 0), (0, 0, r)]]
	return cmds.rename(cmds.curve(d=1, p=p), name)

def drawCube(name, l=1.0, pos=(0.0, 0.0, 0.0)):
	r = l*0.5
	p = [(s[0]+pos[0], s[1]+pos[1], s[2]+pos[2]) for s in [(-r, r, r,), (r, r, r,), (r, r, -r,), (-r, r, -r,), (-r, -r, -r,), (r, -r, -r,), (r, -r, r,), (-r, -r, r,), (-r, r, r,), (-r, r, -r,), (-r, -r, -r,), (-r, -r, r,), (r, -r, r,), (r, r, r,), (r, r, -r,), (r, -r, -r,)]]
	return cmds.rename(cmds.curve(d=1, p=p), name)

def zvDynBtn():
	var1 = cmds.floatSliderGrp("ZvVar1Slider", q=True, value=True)
	var2 = cmds.floatSliderGrp("ZvVar2Slider", q=True, value=True)
	transf = cmds.checkBox("ZvTransferShapes", q=True, value=True)
	
	sel = cmds.ls(sl=True)
	
	# setta il metodo
	if cmds.radioButton(_methodsRB[0], q=True, select=True):
		dynMethod = particleMethod
		_lastSettings[0] = 0
	elif cmds.radioButton(_methodsRB[1], q=True, select=True):
		dynMethod = nParticleMethod
		_lastSettings[0] = 1
	else:
		dynMethod = rungeKuttaMethod
		_lastSettings[0] = 2
	
	if not sel:
		raise Exception, "Select a transform node. You can select meshes, surfaces, clusters, cameras, curves, etc..."
	
	objsToSel = []
	
	# per ogni oggetto selezionato
	for c in sel:
		objsToSel.append(dynMethod(c, var1, var2, transf))
	
	cmds.select(objsToSel)	

def stuffToDelete(obj):
	"Restituisce gli oggetti da cancellare dopo il bake e il dyn"
	pc = cmds.listConnections(obj + ".rotatePivot", s=False)
	if not pc: return

	deleteList = []
	
	pc = pc[0]
	
	unk = cmds.listConnections(pc + ".target[1].targetTranslate", d=False)[0]
	
	# ho usato il metodo rk
	if cmds.nodeType(unk) == _rkNode:
		rkNode = unk
		init = cmds.listConnections(pc + ".target[0].targetRotatePivot", d=False)[0]
		dyn = cmds.listConnections(pc + ".target[1].targetWeight", d=False)[0]
		
		return ([init, rkNode], dyn)
	# ho usato il metodo particle
	else:
		revNode = cmds.listConnections(pc + ".w0", d=False)[0]
		dyn = cmds.listConnections(pc + ".w1", d=False)[0]
		statLoc = cmds.listConnections(pc + ".target[0].targetTranslate", d=False)[0]
		dynLoc = unk
		init = cmds.listConnections(statLoc + ".wm", s=False)[0]
		
		statLocGrpList = cmds.listRelatives(statLoc, p=True)
		dynLocGrpList = cmds.listRelatives(dynLoc, p=True)
	
		# aggiungi gli elementi alla lista di oggetti da cancellare
		if statLocGrpList and statLocGrpList[0].endswith("_LOC"):
			deleteList.append(statLocGrpList[0])
		else:
			deleteList.append(statLoc)
		
		if dynLocGrpList and dynLocGrpList[0].endswith("_LOC"):
			deleteList.append(dynLocGrpList[0])
		else:
			deleteList.append(dynLoc)
		
		deleteList.extend([revNode, init])
		
		return (deleteList, dyn)

def zvBakeBtn():
	useRange = cmds.radioButton("ZvTimeSliderRB", q=True, select=True)
	
	sel = cmds.ls(sl=True, transforms=True)
	if not sel or sel[0].endswith("_DYN"):
		raise Exception, "Select the object you applied ZV Dynamics to"

	obj = sel[0]
	
	stuff = stuffToDelete(obj)
	if not stuff:
		raise Exception, "Select the object you applied ZV Dynamics to"
	
	stuffToDel, dyn = stuff
	
	currentFrame = cmds.currentTime(q=True)
	
	start = cmds.playbackOptions(q=True, ast=True)
	
	if useRange:
		end = cmds.playbackOptions(q=True, max=True)
	else:
		end = cmds.playbackOptions(q=True, aet=True)
	
	# vai al primo frame e inizia il bake
	cmds.currentTime(start)
	cmds.bakeResults(obj, at=["tx", "ty", "tz", "velocityX", "velocityY", "velocityZ"], sm=True, t=(start, end), dic=True, pok=True)
	
	cmds.currentTime(currentFrame)
	try:
		cmds.delete(stuffToDel)
	except:
		sys.stdout.write("Can't delete the constraints\n")
	
	sys.stdout.write("%s baked. Frame range [%d, %d]\n" % (obj, start, end))

def helpBtn():
	webbrowser.open("http://www.paolodominici.com/products/zvdynamics/#help")

def methodChanged():
	if cmds.radioButton(_methodsRB[2], q=True, select=True):
		cmds.floatSliderGrp("ZvVar1Slider", e=True, label="Stiffness:", minValue=0.0, maxValue=1.0, fmn=0.0, fmx=1000.0, value=0.5, step=0.01)
		cmds.floatSliderGrp("ZvVar2Slider", e=True, label="Damping Ratio:", minValue=0.0, maxValue=1.0, fmn=0.0, fmx=1.0, value=0.5, step=0.01)
	else:
		cmds.floatSliderGrp("ZvVar1Slider", e=True, label="Weight:", minValue=0.0, maxValue=1.0, fmn=0.0, fmx=1.0, value=0.5, step=0.01)
		cmds.floatSliderGrp("ZvVar2Slider", e=True, label="Conserve:", minValue=0.0, maxValue=1.0, fmn=0.0, fmx=1.0, value=1.0, step=0.01)

def closeWindow(winName):
	cmds.deleteUI(winName, window=True)

def ZvDynamics():
	if __name__ == "__main__":
		prfx = ""
	else:
		prfx = __name__ + "."
	
	winName = "ZvDynamicsWin"
	if cmds.window(winName, exists=True):
		cmds.deleteUI(winName, window=True)
	
	cmds.window(winName, title="ZV Dynamics " + __version__)
	
	# verifica se c'e' nucleus e runge-kutta
	nPartEnabled = "nParticle" in cmds.ls(nt=True)
	try:
		if not cmds.pluginInfo(_rkNode, q=True, l=True):
			cmds.loadPlugin(_rkNode + ".py")
		rkEnabled = True
	except:
		rkEnabled = False
	
	tabs = cmds.tabLayout(innerMarginWidth=2, innerMarginHeight=2)
	
	# primo tab
	child1 = cmds.formLayout(nd=20)
	
	fl1 = cmds.frameLayout(l="Method", labelAlign="center", borderStyle="etchedOut", mw=10, mh=10, li=5)
	cmds.rowLayout(numberOfColumns=4, columnWidth4=(40, 80, 80, 100), adjustableColumn=4)
	cmds.canvas()
	cmds.radioCollection()
	if _lastSettings[0] == -1:
		if nPartEnabled:
			selMethod = _methodsRB[1]
		else:
			selMethod = _methodsRB[0]
	else:
		selMethod = _methodsRB[_lastSettings[0]]
	
	cmds.radioButton(_methodsRB[0], l="Particle", cc="%smethodChanged()" % prfx)
	cmds.radioButton(_methodsRB[1], l="nParticle", enable=nPartEnabled, cc="%smethodChanged()" % prfx)
	cmds.radioButton(_methodsRB[2], l="Runge-Kutta", enable=rkEnabled, cc="%smethodChanged()" % prfx)
	cmds.radioButton(selMethod, e=True, select=True)
	
	cmds.setParent("..")
	cmds.setParent("..")
	
	fs1 = cmds.floatSliderGrp("ZvVar1Slider", label="Weight:", field=True, minValue=0.0, maxValue=1.0, fmn=0.0, fmx=1.0, value=0.5, step=0.01, cw=[(1, 110), (2, 50)])
	fs2 = cmds.floatSliderGrp("ZvVar2Slider", label="Conserve:", field=True, minValue=0.0, maxValue=1.0, fmn=0.0, fmx=1.0, value=1.0, step=0.01, cw=[(1, 110), (2, 50)])
	methodChanged()
	
	cb = cmds.checkBox("ZvTransferShapes", l="Transfer Shapes", value=False, align="left")
	
	# pulsanti
	b1 = cmds.button(l="Make objects dynamic", height=28, c="%szvDynBtn()" % prfx)
	b2 = cmds.button(l="Close", height=28, c="%scloseWindow(\"%s\")" % (prfx, winName))
	
	cmds.formLayout(child1, e=True, attachForm=[(fl1, "left", 0), (fs1, "left", 0), (fs2, "left", 0), (cb, "left", 130), (fl1, "right", 0), (fl1, "top", 0), (fs1, "top", 65), (fs2, "top", 90), (cb, "top", 125), (b1, "left", 0), (b2, "right", 0), (b1, "bottom", 0), (b2, "bottom", 0)],\
					attachPosition=[(b2, "left", 0, 10), (b1, "right", 0, 10)])
	cmds.setParent(tabs)
	
	# secondo tab
	child2 = cmds.formLayout(nd=20)
	fl2 = cmds.frameLayout(l="Time Range", labelAlign="center", borderStyle="etchedOut", mw=10, mh=10, li=5)
	cmds.rowLayout(numberOfColumns=3, columnWidth3=(50, 100, 100), adjustableColumn=3)
	cmds.canvas()
	cmds.radioCollection()
	cmds.radioButton("ZvTimeSliderRB", l="Time Slider", select=False)
	cmds.radioButton(l="Start/End Animation", select=True)
	cmds.setParent(child2)
	b3 = cmds.button(l="Bake", height=28, c="%szvBakeBtn()" % prfx)
	b4 = cmds.button(l="Close", height=28, c="%scloseWindow(\"%s\")" % (prfx, winName))
	cmds.formLayout(child2, e=True, attachForm=[(fl2, "left", 0), (fl2, "right", 0), (fl2, "top", 0), (b3, "left", 0), (b4, "right", 0), (b3, "bottom", 0), (b4, "bottom", 0)],\
					attachPosition=[(b4, "left", 0, 10), (b3, "right", 0, 10)])
	cmds.setParent(tabs)
	
	# terzo tab
	child3 = cmds.formLayout(nd=30)
	b5 = cmds.button(l="Online Help", height=28, c="%shelpBtn()" % prfx)
	b6 = cmds.button(l="Close", height=28, c="%scloseWindow(\"%s\")" % (prfx, winName))
	cmds.formLayout(child3, e=True, attachForm=[(b6, "left", 0), (b6, "right", 0), (b6, "bottom", 0), (b5, "top", 50)],\
					attachPosition=[(b5, "left", 0, 8), (b5, "right", 0, 22)])
	
	cmds.tabLayout(tabs, edit=True, tabLabel=((child1, 'Dynamics'), (child2, 'Baking'), (child3, 'Help')), sti=1)
	
	cmds.showWindow(winName)
	cmds.window(winName, edit=True, widthHeight=(380, 248))
	
	sys.stdout.write("ZV Dynamics %s          http://www.paolodominici.com          paolodominici@gmail.com\n" % __version__)
