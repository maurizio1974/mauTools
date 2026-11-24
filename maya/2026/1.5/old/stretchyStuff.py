import maya.cmds as cmds


def stretchyStuff():
    iks = cmds.ls(sl=True)
    # pC, oC, buffer, eJnt
    # sLoc, eLoc, sLocS, eLocS, chain, ikParent, sJparent
    # sJnt, endEff, name, DD, DDS, MD, result, text
    # sPos, float, ePos

    for eIK in iks:
        if cmds.objectType(eIK) == 'ikHandle':
            if cmds.ikHandle(eIK, q=True, sol=True) != 'ikSplineSolver':
                # GET THE START AND JOINT AND END EFFECTOR OR THE CHAIN
                sJnt = cmds.ikHandle(eIK, q=True, sj=True)
                sJparent = cmds.listRelatives(sJnt, p=True)
                ikParent = cmds.listRelatives(eIK, p=True)
                endEff = cmds.ikHandle(eIK, q=True, ee=True)
                # STRIP POSSIBLE SUFFIXES TO THE JOINTS
                name = ''
                if "jnt" in sJnt:
                    name = name.rstrip('jnt')
                else:
                    result = cmds.promptDialog(t='Stretchy', m='Name:', tx=sJnt, b='OK', b='Cancel', db="OK", cb='Cancel', ds='Cancel')
                    if result == 'OK':
                        text = cmds.promptDialog(q=True, t=True)
                        name = text

                # GET THE END JOINT
                cmds.select(cl=True)
                cmds.select(endEff)
                cmds.pickWalk(d='up')
                cmds.pickWalk(d='down')
                eJnt = cmds.ls(sl=True)

                # GET POSITION IN WORLD SPACE OF THE START AND END JOINT
                # sPos = cmds.xform(sJnt, q=True, ws=True, t=True)
                # ePos = cmds.xform(eJnt[0], q=True, ws=True, t=True)

                # CREATE LOCATORS FOR THE DISATNCE UTILITY
                sLoc = cmds.spaceLocator(n=(name + 'SD'))
                eLoc = cmds.spaceLocator(n=(name + 'ED'))
                cmds.setAttr(sLoc[0] + "Shape.visibility", 0)
                cmds.setAttr(eLoc[0] + ".localScale", 0.25, 0.25, 0.25)

                # MOVE THEM TO THE START AND END JOINT RESPECTVILY
                pC = cmds.pointConstraint(sJnt, sLoc[0])
                oC = cmds.orientConstraint(sJnt, sLoc[0])
                cmds.delete(pC[0], oC[0])
                pC = cmds.pointConstraint(eJnt, eLoc[0])
                oC = cmds.orientConstraint(eJnt, eLoc[0])
                cmds.delete(pC[0], oC[0])

                # CREATE LOCATORS FOR THE DISATNCE UTILITY USED FOR THE SCALE OF THE WHOLE RIG
                sLocS = cmds.spaceLocator(n=(name + 'SDS'))
                eLocS = cmds.spaceLocator(n=(name + 'EDS'))
                cmds.setAttr(sLocS[0] + "Shape.visibility", 0)
                cmds.setAttr(eLocS[0] + "Shape.visibility", 0)

                # MOVE THESE TO THE START AND END JOINT RESPECTVILY
                pC = cmds.pointConstraint(sJnt, sLocS[0])
                oC = cmds.orientConstraint(sJnt, sLocS[0])
                cmds.delete(pC[0], oC[0])
                pC = cmds.pointConstraint(eJnt, eLocS[0])
                oC = cmds.orientConstraint(eJnt, eLocS[0])
                cmds.delete(pC[0], oC[0])

                # CREATE THE DISTANCES UTILITY NODES
                DD = cmds.shadingNode(
                    asUtility='distanceBetween', n=(name + 'DD'))
                DDS = cmds.shadingNode(
                    asUtility='distanceBetween', n=(name + 'DDS'))

                # CONNECTED TO THE RESPECTIVE LOCATOR PREVIOUSLY CREATED
                # CONNECTION FOR THE DISTANCE USED FOR THE STRETCH
                cmds.connectAttr(
                    (sLoc[0] + 'Shape.worldPosition[0]'), (DD + '.point1'))
                cmds.connectAttr(
                    (eLoc[0] + 'Shape.worldPosition[0]'), (DD + '.point2'))

                # CONNECTION FOR THE DISTANCE THAT WILL TELL US THE WORD SCALE OF THE RIG
                cmds.connectAttr(
                    (sLocS[0] + 'Shape.worldPosition[0]'), (DDS + '.point1'))
                cmds.connectAttr(
                    (eLocS[0] + 'Shape.worldPosition[0]'), (DDS + '.point2'))

                # CRETAE THE MULTIPLY DIVIDE NODE NAD THE CONDITIONA NODE
                MD = cmds.createNode('multiplyDivide', n=name + "MD")
                cmds.setAttr(MD + '.operation', 2)
                CND = cmds.shadingNode(asUtility='condition', n=name + 'CND')
                cmds.setAttr(CND + ".operation", 4)

                # CONNECT IT TO THE DISTANCE NODES CREATED
                cmds.connectAttr((DDS + '.distance')(CND + '.firstTerm'))
                cmds.connectAttr((DDS + '.distance')(CND + '.colorIfFalseR'))
                cmds.connectAttr((DD + '.distance')(CND + '.secondTerm'))
                cmds.connectAttr((DD + '.distance'), (CND + '.colorIfTrueR'))

                cmds.connectAttr((CND + '.outColorR'), (MD + '.input1X'))
                cmds.connectAttr((DDS + '.distance'), (MD + '.input2X'))

                # GET AL THE JOINT IN THE CHAIN
                cmds.select(cl=True)
                chain = cmds.ls(sJnt, l=1, dag=1, ap=1)

                # LOOP THROUGH AND CONNECT THEIR SCALEX TO THE MULTIPLY DIVIDE NODE
                for eChain in chain:
                    if cmds.objectType(eChain) == 'joint':
                        cmds.connectAttr(
                            MD + '.outputX', eChain + '.scaleX')

                # PARENT THE IKHANDLE TO THE LOCATOR THAT IS THE END OF THE DISTANCE NODE FOR THE STRETCH
                cmds.parent(eLoc[0], ikParent[0])
                cmds.parent(eIK, eLoc[0])

                cmds.parent(eLocS[0], sJparent[0])
                cmds.parent(sLocS[0], sJparent[0])
                cmds.parent(sLoc, sJparent[0])
            else:
                # THIS IS IN CASE IT"S A SPLINEIK
                # LET'S GET TEH SPLINE CURVE USED BY THE IK
                conn = cmds.listConnections(eIK, s=True, d=False)
                for eC in conn:
                    shape = cmds.listRelatives(eC, s=True)
                    if len(shape[0]) != 0:
                        if cmds.nodeType(shape[0]) == "nurbsCurve":
                            # CREATE TEH CURVEINFO NODE TO GET THE LENGTH OF THE SURVE
                            cINFO = cmds.createNode(
                                'curveInfo', n=(eIK + 'CINFO'))

                            # CREATE THE MULTIPLYDIVIDE NODE TO SCALE OF THE JOINTS BASED ON THE LENGTH OF THE CURVE
                            MD = cmds.createNode(
                                'multiplyDivide', n=(eIK + "MD"))

                            #  MAKE THE CONNECTION FORM THE CURVEINFO NODE AND THE SPLINE IK CURVE
                            cmds.connectAttr(
                                (shape[0] + '.worldSpace[0]'), (cINFO + '.inputCurve'))
                            cLen = cmds.getAttr((cINFO + '.arcLength'))

                            # CONNECT THE CURVE INFO NODE TO A MULTIPLY DIVIDE NODE TO CONTROL THE SCALE BASED ON THE DISTANCE
                            cmds.connectAttr(
                                cINFO + '.arcLength', MD + '.input1X')

                            cmds.setAttr(MD + ".input2X", cLen)
                            cmds.setAttr(MD + ".operation", 2)

                            # GET THE START JOINT OF THE CHAIN AND THEN ALL OF THE JOINTS OF THE CHAIN
                            start = cmds.ikHandle(eIK, q=True, sj=True)
                            chain = cmds.ls(start, l=1, dag=1, ap=1)

                            for eC in chain:
                                # CONNECT THE MULTIPLYDIVIDE NODE TO THE SCALE X OF THE JOINTS
                                if cmds.nodeType(eC) != 'ikEffector':
                                    cmds.connectAttr(
                                        MD + ".outputX", eC + ".scaleX")
        else:
            print('please make sure you select only ikHandles.')
