import maya.cmds as cmds
import maya.mel as mel


def mgCableChain(dir, res):
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
      
      jnts = []
      for x, eachCircle in enumerate(circles):
         name = each.split('_geo')[0]
         cmds.select(eachCircle)
         mel.eval('CenterPivot')
         bone = cmds.joint(rad=0.1, n=name + '_' + str(x + 1).zfill(2) + '_jnt')
         cmds.delete(cmds.pointConstraint(eachCircle, bone))
         grp = name + '_grp'
         if not cmds.objExists(grp):
             cmds.group(em=True, w=True, n=grp)
         cmds.parent(bone, grp)
         cmds.delete(eachCircle)
         jnts.append(bone)

      # allJNT = cmds.ls('cable' + each + '*')
      jnts.reverse()
      for x in range(0, len(jnts)):
         cur = jnts[x]
         if cur != jnts[-1]:
            cmds.parent(jnts[x], jnts[x+1])
      cmds.select(jnts[-1], r=True)
      cmds.joint(e=True, oj='xyz', secondaryAxisOrient='yup', ch=True, zso=True)
      cmds.setAttr(jnts[0] + '.jointOrient', 0, 0 ,0)
   print('DONE !!!')

def selectIsoParmCustom(sel, dir, res):
   shape = cmds.listRelatives(sel, c=True)
   sele = cmds.ls(shape[0] + '.u[*][*]', fl=True)
   # get a loop for the selection
   nurb1 = sele[0].split(':')[-2].split(']')[0]
   nurb2 = sele[0].split(':')[-1].split(']')[0]
   cmds.select(cl=True)

   nurbX = nurb2
   if nurb1 > nurb2:
      nurbX = nurb1
   # Loop trou all the isoparms and select them
   for x in range(0, int(nurbX), res):
      cmds.select(shape[0] + '.' + dir + '[' + str(x) + ']', add=True)
