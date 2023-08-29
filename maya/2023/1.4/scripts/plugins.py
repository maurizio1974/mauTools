#
# example BlendShapesManager plug-ins
#

import maya.cmds as mc
import maya.OpenMaya as om



# Every class in a .py file is considered a potential plug-in.
# The plug-in interface is defined in the "gui" method which
# is invoked at plug-in load time and appears in the "plug-ins"
# tab of the BlendShapesManager dialog.
class HelloWorld(object):

	# Every plug-in should have a "constructor", even if it does nothing.
	def __init__(self, *arg, **kwa): pass

	def gui(self):

		mc.text(l="Basic plug-in example.")
		mc.button(l="Hello World !", c=self.printHelloWorld)

	def printHelloWorld(self, *arg):

		mc.confirmDialog(t="example", m="Hello World !", b=["ok"], db="ok", cb="ok", ds="ok")



class Keyframe(object):

	# A PxPlugin class provides convenient ways to
	# interface with the BlendShapesManager's data.
	def __init__(self, plugin): self.plugin = plugin

	def gui(self):

		mc.text(l="Keyframe selected target weights over 100 frames.")
		mc.text(l="This is useful when testing how targets blend and work together.")
		mc.text(l="Scrub the time slider to see the result.")
		mc.paneLayout(cn="vertical2", st=1)
		mc.button(l="keyframe selected target(s)", c=self.keyframe)
		mc.button(l="un-keyframe all targets", c=self.unkeyframe)
		mc.setParent("..")

	def keyframe(self, *arg):

		# Check if the BlendShapesManager instance
		# is properly attached to a scene geometry.
		self.plugin.isAttached()

		mc.playbackOptions(min=1, max=100)
		deformer = self.plugin.deformer() # the underlying deformer name
		selectedTargets = self.plugin.selectedTargets() # all selected targets in the BlendShapesManager GUI
		for target in selectedTargets:
			mc.setKeyframe(deformer+"."+target, t=1, v=0) 
			mc.setKeyframe(deformer+"."+target, t=100, v=1)
			print("Keyframed target: "+target)

	def unkeyframe(self, *arg):

		self.plugin.isAttached()

		deformer = self.plugin.deformer()
		for target in self.plugin.selectedTargets():
			l = mc.listConnections(deformer+"."+target, s=True, d=False, p=True) or []
			if len(l) > 0: mc.disconnectAttr(l[0], deformer+"."+target)
			print("Un-keyframed target: "+target)



class XYZ(object):

	def __init__(self, plugin): self.plugin = plugin

	def gui(self):

		mc.text(l='Extract X/Y/Z "components" from selected target(s).')
		mc.rowLayout(nc=6, adj=6)
		mc.text(l="axis:", w=50)
		mc.checkBox("cb_x_XYZ", l="x", w=35)
		mc.checkBox("cb_y_XYZ", l="y", w=35)
		mc.checkBox("cb_z_XYZ", l="z", w=35)
		mc.text(l="", w=10)
		mc.button(l="extract", c=self.extract)
		mc.setParent("..")

	def extract(self, *arg):

		self.plugin.isAttached()

		x = mc.checkBox("cb_x_XYZ", q=True, v=True)
		y = mc.checkBox("cb_y_XYZ", q=True, v=True)
		z = mc.checkBox("cb_z_XYZ", q=True, v=True)
		if x+y+z == False: raise Exception("At least one axis should be active.")

		selectedTargets = self.plugin.selectedTargets()
		if len(selectedTargets) == 0:
			raise Exception("At least one target should be selected in the GUI.")

		# buffers
		xpts = om.MFloatPointArray()
		ypts = om.MFloatPointArray()
		zpts = om.MFloatPointArray()

		tgts = self.plugin.targets() # targets data - dictionary { targetName : deformerNode.targets[#] }
		base = self.plugin.baseObject() # base object's name - string
		bpts = self.plugin.basePoints() # base object's points - MFloatPointArray
		for t in selectedTargets:
			xpts.copy(bpts)
			ypts.copy(bpts)
			zpts.copy(bpts)
			pts = self.plugin.points(tgts[t])
			ids = self.plugin.ids(tgts[t])
			for i in range(ids.length()):
				idx = ids[i] # a tiny peformance boost, mostly to make me feel better :)
				if x == True: xpts[idx].x += pts[i].x
				if y == True: ypts[idx].y += pts[i].y
				if z == True: zpts[idx].z += pts[i].z
			if x == True:
				n = mc.duplicate(base, n=t+"___x")[0]
				self.plugin.setPoints(n, xpts)
				print("Result: "+n)
			if y == True:
				n = mc.duplicate(base, n=t+"___y")[0]
				self.plugin.setPoints(n, ypts)
				print("Result: "+n)
			if z == True:
				n = mc.duplicate(base, n=t+"___z")[0]
				self.plugin.setPoints(n, zpts)
				print("Result: "+n)

class EditPoseData(object):

	def __init__(self, plugin): self.plugin = plugin

	def gui(self):

		mc.text(l="Manually edit pose data for selected inverse target.")
		mc.button(l="load data", c=self.loadData)
		mc.scrollField("sf_poseData_EPD", h=200)
		mc.button(l="apply edits", c=self.applyEdits)

	def loadData(self, *arg):

		mc.scrollField("sf_poseData_EPD", e=True, tx="")

		self.plugin.isAttached()

		selectedTargets = self.plugin.selectedPrimaryTargets()
		if len(selectedTargets) == 0:
			raise Exception("At least one target should be selected in the GUI.")
		target = selectedTargets[0]

		# pose data is returned as a dictionary,
		# convert it to string, make it human-readable
		poseData = str(self.plugin.poseData(target))
		poseData = poseData[1:][:-1].replace(", '", "\n'")

		# update GUI
		mc.scrollField("sf_poseData_EPD", e=True, tx=poseData)

		print("Loaded pose data for target: "+target)

	def applyEdits(self, *arg):

		self.plugin.isAttached()

		selectedTargets = self.plugin.selectedPrimaryTargets()
		if len(selectedTargets) == 0:
			raise Exception("At least one target should be selected in the GUI.")
		target = selectedTargets[0]

		# get data from GUI, apply it to the selected target
		poseData = mc.scrollField("sf_poseData_EPD", q=True, tx=True).strip()
		poseData = "{"+poseData.replace("\n'", ", '")+"}"
		self.plugin.setPoseData(target, eval(poseData))

		print("Applied pose data for target: "+target)

		# refresh the blendShapesManager GUI and related scene entities
		self.plugin.refresh()
