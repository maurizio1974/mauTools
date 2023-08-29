
# save the code below in file named uninstancer.py
# select at least one instancer node in the maya scene and run the next command:
# import imp; uninstancer = imp.load_source('uninstancer','/usr/people/maurizio-g/maya/scripts/dynamics/uninstancer.py'); uninstancer.uninstancer().main()


import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaFX as omfx

class uninstancer():
    def main(self):
        li = []
        l = mc.ls(sl=True) or []
        for n in l:
            if mc.nodeType(n) != "instancer": continue
            li.append(n)
        if len(li) == 0: raise Exception('Select at least one instancer node.')
        l = []
        m = om.MMatrix()
        dp = om.MDagPath()
        dpa = om.MDagPathArray()
        sa = om.MScriptUtil()
        sa.createFromList([0.0, 0.0, 0.0], 3)
        sp = sa.asDoublePtr()
        sf = int(mc.playbackOptions(q=True, min=True))
        ef = int(mc.playbackOptions(q=True, max=True))
        for i in range(sf, ef):
            mc.currentTime(i)
            for inst in li:
                g = inst+"_objects"
                if i == sf:
                    if mc.objExists(g) == True: mc.delete(g)
                    mc.createNode("transform", n=g)
                    l.append(g)
                sl = om.MSelectionList()
                sl.add(inst)
                sl.getDagPath(0, dp)
                fni = omfx.MFnInstancer(dp)
                for j in range(fni.particleCount()):
                    fni.instancesForParticle(j, dpa, m)
                    for k in range(dpa.length()):
                        n = inst+"_"+str(j)+"_"+dpa[k].partialPathName()
                        if mc.objExists(n) == False:
                            n2 = mc.duplicate(dpa[k].partialPathName(), ilf = True )[0]
                            n = mc.rename(n2, n)
                            if mc.listRelatives(n, p=True) != g:
                                n = mc.parent(n, g)[0]
                            mc.setKeyframe(n+".v", t=i-1, v=False)
                        tm = om.MTransformationMatrix(m)
                        t = tm.getTranslation(om.MSpace.kWorld)
                        mc.setAttr(n+".t", t[0], t[1], t[2])
                        mc.setKeyframe(n+".t")
                        r = tm.eulerRotation().asVector()
                        mc.setAttr(n+".r", r[0]*57.2957795, r[1]*57.2957795, r[2]*57.2957795)
                        mc.setKeyframe(n+".r")
                        tm.getScale(sp, om.MSpace.kWorld)
                        sx = om.MScriptUtil().getDoubleArrayItem(sp, 0)
                        sy = om.MScriptUtil().getDoubleArrayItem(sp, 1)
                        sz = om.MScriptUtil().getDoubleArrayItem(sp, 2)
                        s = om.MTransformationMatrix(dpa[k].inclusiveMatrix()).getScale(sp, om.MSpace.kWorld)
                        sx2 = om.MScriptUtil().getDoubleArrayItem(sp, 0)
                        sy2 = om.MScriptUtil().getDoubleArrayItem(sp, 1)
                        sz2 = om.MScriptUtil().getDoubleArrayItem(sp, 2)
                        mc.setAttr(n+".s", sx*sx2, sy*sy2, sz*sz2)
                        mc.setKeyframe(n+".s")
                        mc.setAttr(n+".v", True)
                        mc.setKeyframe(n+".v")
                        mc.setKeyframe(n+".v", t=i+1, v=False)
        return l

