import maya.cmds as cmds

def splyneToMP(curve=None):
    controls = ["spine_FK_0{}_cont".format(i) for i in range(1, 5)]
    if not cmds.objExists(curve):
        raise RuntimeError("Curve does not exist: {}".format(curve))
    curve_shape = cmds.listRelatives(curve, shapes=True, fullPath=True)[0]

    # --------------------------------------------------------
    # Find the spline IK driven by the curve
    # --------------------------------------------------------
    ik_handles = cmds.ls(type="ikHandle") or []
    spline_ik = None
    for ik in ik_handles:
        solver = cmds.ikHandle(ik, query=True, solver=True)
        if solver != "ikSplineSolver":
            continue
        connections = cmds.listConnections(curve_shape + ".worldSpace[0]", source=False, destination=True) or []
        if ik in connections:
            spline_ik = ik
            break
    if not spline_ik:
        raise RuntimeError("Could not find a spline IK driven by {}".format(curve))

    # --------------------------------------------------------
    # Get spline IK joint chain
    # --------------------------------------------------------
    joints = cmds.ikHandle(spline_ik, q=True, jointList=True) or []
    if not joints:
        raise RuntimeError("Could not find joints on {}".format(spline_ik))
    cmds.delete(spline_ik)

    # --------------------------------------------------------
    # Get curve paramU for each joint
    # --------------------------------------------------------
    curve_shape = cmds.listRelatives(curve, shapes=True, noIntermediate=True, fullPath=True)[0]
    motion_paths = []
    up_vectors = []
    for index, joint in enumerate(joints):
        cmds.select(cl=True)
        jnt = cmds.joint(n=joint.replace('_JNT', '_MP'))
        cmds.delete(cmds.parentConstraint(joint, jnt))
        pos = cmds.xform(joint, q=True, ws=True, t=True)
        # Find closest point on curve and convert it to U.
        point = cmds.createNode("closestPointOnCurve")
        cmds.connectAttr(curve_shape + ".worldSpace[0]", point + ".inCurve")
        cmds.setAttr(point + ".inPosition", *pos, type="double3")
        u = cmds.getAttr(point + ".paramU")
        cmds.delete(point)
        # ----------------------------------------------------
        # Motion path transform
        # ----------------------------------------------------
        mp = cmds.createNode("transform",name="{}_motionPath".format(joint.split("|")[-1]))
        cmds.createNode("motionPath", name="{}_motionPath_node".format(joint.split("|")[-1]))
        mp_node = "{}_motionPath_node".format(joint.split("|")[-1])
        cmds.connectAttr(curve_shape + ".worldSpace[0]", mp_node + ".geometryPath")
        cmds.connectAttr(mp_node + ".allCoordinates", mp + ".translate")
        cmds.connectAttr(mp_node + ".rotate", mp + ".rotate")
        cmds.setAttr(mp_node + ".uValue", u)
        cmds.setAttr(mp_node + ".fractionMode", False)
        cmds.setAttr(mp_node + ".follow", True)
        cmds.setAttr(mp_node + ".frontAxis", 0)
        cmds.setAttr(mp_node + ".upAxis", 1)
        cmds.setAttr(mp_node + ".worldUpType", 2)
        # ----------------------------------------------------
        # Up-vector locator
        # ----------------------------------------------------
        up = cmds.spaceLocator(n="{}_upVector".format(joint.split("|")[-1]))[0]
        cmds.xform(up, ws=True, t=pos)
        cmds.setAttr(f'{up}.tz', cmds.getAttr(f'{up}.tz') + 10)
        up_vectors.append(up)
        motion_paths.append(mp)
        # Parent joint under motion-path transform while
        # maintaining its current world-space position.
        cmds.parent(jnt, mp)

    # --------------------------------------------------------
    # Create up-vector controls
    # --------------------------------------------------------
    for index, up in enumerate(up_vectors):
        pos = cmds.xform(up, q=True, ws=True, t=True)
        # Find the closest point on the curve again so the
        # up-vector can be matched to the corresponding joint.
        point = cmds.createNode("closestPointOnCurve")
        cmds.connectAttr(curve_shape + ".worldSpace[0]", point + ".inCurve")
        cmds.setAttr(point + ".inPosition", *pos, type="double3")
        u = cmds.getAttr(point + ".paramU")
        cmds.delete(point)
        # Find the two controls surrounding this U.
        control_us = []
        for control in controls:
            control_pos = cmds.xform(control, q=True, ws=True, t=True)
            point = cmds.createNode("closestPointOnCurve")
            cmds.connectAttr(curve_shape + ".worldSpace[0]", point + ".inCurve")
            cmds.setAttr(point + ".inPosition", *control_pos, type="double3")
            control_u = cmds.getAttr(point + ".paramU")
            cmds.delete(point)
            control_us.append(control_u)
        if u <= control_us[0]:
            first = controls[0]
            second = controls[1]
            weight_second = 0.0
        elif u >= control_us[-1]:
            first = controls[-2]
            second = controls[-1]
            weight_second = 1.0
        else:
            first = controls[0]
            second = controls[1]
            weight_second = 0.0
            for i in range(len(controls) - 1):
                u1 = control_us[i]
                u2 = control_us[i + 1]
                if u1 <= u <= u2 or u2 <= u <= u1:
                    first = controls[i]
                    second = controls[i + 1]
                    if abs(u2 - u1) > 0.000001:
                        weight_second = abs((u - u1) / (u2 - u1))
                    break
        weight_first = 1.0 - weight_second

        # ----------------------------------------------------
        # Parent constraint between the two controls
        # ----------------------------------------------------
        constraint = cmds.parentConstraint(first, second, up, mo=True)[0]
        cmds.setAttr(f'{constraint}.interpType', 2)
        aliases = cmds.parentConstraint(constraint, q=True, weightAliasList=True)
        cmds.setAttr(constraint + "." + aliases[0], weight_first)
        cmds.setAttr(constraint + "." + aliases[1], weight_second)
        fv = round(weight_first * 100, 2)
        sv = round(weight_second * 100, 2)
        print(f'{up} : {first} {fv}% | {second} {sv}%')

    # --------------------------------------------------------
    # Connect up-vectors to motion paths
    # --------------------------------------------------------
    for mp, up in zip(motion_paths, up_vectors):
        mp_node = mp + "_node"
        cmds.setAttr(mp_node + ".worldUpType", 1)
        cmds.connectAttr(up + ".worldMatrix[0]", mp_node + ".worldUpMatrix", f=True)

    # --------------------------------------------------------
    # Connect spline ik joint to the motionpath ones
    # --------------------------------------------------------
    for index, joint in enumerate(joints):
        jnt = joint.replace('_JNT', '_MP')
        cmds.parentConstraint(jnt, joint, mo=True)

    print("\nCreated {} motion paths.".format(len(motion_paths)))
    print("Created {} up-vector drivers.".format(len(up_vectors)))
    print("Spline IK: {}".format(spline_ik))

def main(*args):
    splyneToMP(curve)