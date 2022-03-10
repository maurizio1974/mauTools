import maya.cmds as cmds
import maya.mel as mel


'''USAGE

import mgCableChain
reload(mgCableChain)

# direction to be followed by the chain
dir = 'v'
# resolution of the chain , all the edge loops or one every 2 or more
res = 1
# Create Ik Curve solver and controllers
# if IK is flase then a curve matching every joint will be made
ik = False
# number of point in the curve of the IK Chain solver
ns = 6

mgCableChain.mgCableChain(dir, res, ik, ns)

'''



def mgCableChain(dir='v', res=1, ik=False, ns=1):
   sel = cmds.ls(sl=True)
   for each in sel:
      subD = cmds.polyToSubdiv(each, ap=0, ch=0, aut=0, maxPolyCount=100000, maxEdgesPerVert=32)
      nub = cmds.subdToNurbs(subD[0], ch=0, aut=1, ot=0)
      selectIsoParmCustom(nub[0], dir, res)
      
      mel.eval('DuplicateCurve')
      circles=cmds.ls("duplicatedCurve*", type="transform")
      cmds.select(cl=True)
      
      cmds.delete(subD[0])
      counter = 0
      
      # MAKE JOINTS
      name = each.split('_geo')[0]
      grp = name + '_grp'
      if not cmds.objExists(grp):
          cmds.group(em=True, w=True, n=grp)
      jnts = []
      for x, eachCircle in enumerate(circles):
         cmds.select(eachCircle)
         mel.eval('CenterPivot')
         bone = cmds.joint(rad=0.1, n=name + '_' + str(x + 1).zfill(2) + '_jnt')
         cmds.delete(cmds.pointConstraint(eachCircle, bone))
         cmds.parent(bone, grp)
         cmds.delete(eachCircle)
         jnts.append(bone)

      # REPARENT AND ORIENT JOINT CHAIN
      jnts.reverse()
      for x in range(0, len(jnts)):
         cur = jnts[x]
         if cur != jnts[-1]:
            cmds.parent(jnts[x], jnts[x+1])
      cmds.select(jnts[-1], r=True)
      cmds.joint(e=True, oj='xyz', secondaryAxisOrient='yup', ch=True, zso=True)
      cmds.setAttr(jnts[0] + '.jointOrient', 0, 0 ,0)

      # MAKE IK SPLINE
      if ik:
         iks = cmds.ikHandle(
             sj=jnts[-1], ee=jnts[0],
             sol='ikSplineSolver', ccv=True, scv=True, ns=ns)
         ikh = name + '_ikHandle'
         eff = name + '_effector'
         crv = name + '_crv'

         cmds.rename(iks[0], ikh)
         cmds.rename(iks[1], eff)
         cmds.rename(iks[2], crv)
         # MAKE CDEFOMARION CLUSTERS
         grpC = name + '_clusters_ctrls_grp'
         if not cmds.objExists(grpC):
            cmds.group(em=True, n=grpC)
         ns = cmds.getAttr(crv + '.spans')
         dg = cmds.getAttr(crv + '.degree')
         clss = []
         for x in range(ns + dg):
            cls = cmds.cluster(crv + '.cv[' + str(x) + ']', n=name + '_' + str(x + 1).zfill(2) + '_clh')
            cmds.parent(cls[1], grpC)
         ci = cmds.createNode('curveInfo', n=name + '_cinfo')
         ciO = cmds.createNode('curveInfo', n=name + '_orig_cinfo')
         sh = cmds.listRelatives(crv, s=True)
         cmds.connectAttr(sh[0] + '.worldSpace[0]', ci + '.inputCurve')
         cmds.connectAttr(sh[1] + '.worldSpace[0]', ciO + '.inputCurve')
         md = cmds.createNode('multiplyDivide', n=name + '_md')
         cmds.setAttr(md + '.operation', 2)
         cmds.connectAttr(ci + '.arcLength', md + '.input1X')
         cmds.connectAttr(ciO + '.arcLength', md + '.input2X')
         for j in jnts:
            cmds.connectAttr(md + '.outputX', j + '.sx')
      else:
         # MAKE NURB CURVES
         pos = cmds.xform(jnts[0], q=True, ws=True, t=True)
         crv = cmds.curve(p=(pos[0], pos[1], pos[2]), n=each.split('_geo')[0])
         cmds.parent(crv, grp)
         for x in range(0, len(jnts)):
            pos = cmds.xform(jnts[x], q=True, ws=True, t=True)
            cmds.curve(crv, a=True, p=(pos[0], pos[1], pos[2]))
      # MAKE CONTROLLERS
      # sel = cmds.ls(sl=True)
      # for s in sel:
      #     name = s.replace('_clhHandle', '')
      #     grph = cmds.group(em=True, n=name + '_h_grp')
      #     grp = cmds.group(em=True, n=name + '_grp')
      #     cmds.parent(grp, grph)
      #     ctrl = cmds.circle(n=name + '_ctrl')
      #     cmds.parent(ctrl[0], grp)
      #     cmds.delete(cmds.parentConstraint(s, grph))
   print('DONE !!!')

def selectIsoParmCustom(sel, dir, res):
   shape = cmds.listRelatives(sel, c=True)
   sele = cmds.ls(shape[0] + '.u[*][*]', fl=True)
   # get a loop for the selection
   nurb1 = sele[0].split(':')[-2].split(']')[0]
   nurb2 = sele[0].split(':')[-1].split(']')[0]
   cmds.select(cl=True)
   nurbX = nurb2
   if int(nurb1) > float(nurb2):
      nurbX = nurb1
   # Loop trou all the isoparms and select them
   for x in range(0, int(nurbX) + 1, res):
      cmds.select(shape[0] + '.' + dir + '[' + str(x) + ']', add=True)
