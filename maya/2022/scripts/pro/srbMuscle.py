# Title: Muscle v1.0
# AUTHOR:   Maurizio Giglioli
# DATE: April 10th, 2017
# DESCRIPTION: Use this Tool to automatically create muscles or tendons...
# USAGE:  Enter the name for the muscle in the text field,
#         choose the options and click on Apply...
#         NOTE: The muscle geometry created is a nurbs model and should be
#         added to a skinned geometry as an influence object with use
#         geometry check box turned on.
#         Also, make sure that the skinCluster deformer's
#         Use components attribute is turned on...
#         The spCc and epCc are two start point and end point controllers
#         which can be parented or constrained to
#         any joints or objects. The mpCc controller is the middle point
#         controller which can be also be transformed,
#         and consists of attributes such as bulge, spPoint, epPoint,
#         spOrient and epOreint which controls the
#         behaviour and transformation of the muscle itself.

import maya.cmds as cmds
import maya.mel as mel


# CREATE THE MAIN PROCEDURE---
def srbMuscle():
    if cmds.window('srbMuscleWin', exists=True):
        cmds.deleteUI('srbMuscleWin')
    cmds.window(
        'srbMuscleWin',
        title="Muscle v1.0",
        rtf=1,
        maximizeButton=0)
    cmds.menuBarLayout()
    cmds.menu(label="Edit")
    cmds.menuItem(divider=True)
    cmds.menuItem(
        label="Add to muscle set",
        c="sets -edit -forceElement srbMuscleSet;")
    cmds.menuItem(
        label="Select muscle set",
        c="select srbMuscleSet")
    cmds.menuItem(divider=True)
    cmds.menuItem(
        label="Prepare muscle to be an influence object",
        c="srbPrepareMuscleProc")
    cmds.menuItem(divider=True)
    cmds.menuItem(
        label="Mirror muscle",
        c="srbMirrorMuscleProc")
    cmds.menuItem(divider=True)
    cmds.menuItem(
        label="Reset",
        c="reset")
    cmds.menu(label="Help")
    cmds.menuItem(
        label="About",
        c='cmds.confirmDialog(t="SRB - Muscle", m="Muscolitos", button="OK")')
    cmds.columnLayout(
        'srbMuscleMainColumnLayout',
        adj=1)
    cmds.textFieldGrp(
        'srbMuscleTextFildGrp',
        label="Muscle name:",
        text="muscle01")
    cmds.frameLayout(
        'srbMuscleFrameLayout',
        label="Muscle options:")
    cmds.columnLayout(adj=1)
    cmds.floatFieldGrp(
        'srbMuscleRadiusFloatFieldGrp',
        numberOfFields=3,
        label="Radius:",
        value1=0.25,
        value2=1.0,
        value3=0.25)
    cmds.separator(h=5)
    cmds.floatSliderGrp(
        'srbSurfaceDegreeFloatSliderGrp',
        label="Surface degree:",
        field=True,
        minValue=1.0,
        maxValue=10.0,
        fieldMinValue=1,
        fieldMaxValue=100.0,
        value=2)
    cmds.separator(h=5)
    cmds.floatSliderGrp(
        'srbMeshResFloatSliderGrp',
        label="Mesh Resolution:",
        field=True,
        minValue=20.0,
        maxValue=200.0,
        fieldMinValue=20.0,
        fieldMaxValue=1000.0,
        value=2)
    cmds.separator(h=5)
    cmds.radioButtonGrp(
        'srbMuscleTypeRadioButtonGrp',
        numberOfRadioButtons=2,
        label="Muscle Type:",
        labelArray2=("Muscle", "Tendon"),
        select=1)
    cmds.separator(h=5)
    cmds.radioButtonGrp(
        'srbMuscleAxisRadioButtonGrp',
        numberOfRadioButtons=3,
        label="Muscle Axis:",
        labelArray3=("X", "Y", "Z"),
        select=1)
    cmds.separator(h=5)
    cmds.floatSliderGrp(
        'srbMuscleLengthFloatSliderGrp',
        label="Muscle Length:",
        field=True,
        minValue=1.0,
        maxValue=20.0,
        fieldMinValue=1,
        fieldMaxValue=100.0,
        value=5)
    cmds.separator(h=5)
    cmds.button(
        label="Apply",
        c="srbMuscle.srbMuscleProc()")
    cmds.showWindow('srbMuscleWin')


# CREATE THE PROCEDURE---
def srbMuscleProc():
    # STORE SOME USER DEFINED VARIABLES---
    mPrefix = cmds.textFieldGrp(
        'srbMuscleTextFildGrp', q=True, text=True)
    spRadius = cmds.floatFieldGrp(
        'srbMuscleRadiusFloatFieldGrp', q=True, value1=True)
    mpRadius = cmds.floatFieldGrp(
        'srbMuscleRadiusFloatFieldGrp', q=True, value2=True)
    epRadius = cmds.floatFieldGrp(
        'srbMuscleRadiusFloatFieldGrp', q=True, value3=True)
    surfaceDegree = cmds.floatSliderGrp(
        'srbSurfaceDegreeFloatSliderGrp', q=True, value=True)
    meshRes = cmds.floatSliderGrp(
        'srbMeshResFloatSliderGrp', q=True, value=True)
    muscleType = cmds.radioButtonGrp(
        'srbMuscleTypeRadioButtonGrp', q=True, select=True)
    muscleAxis = cmds.radioButtonGrp(
        'srbMuscleAxisRadioButtonGrp', q=True, select=True)
    masterG = mPrefix + "_grp"

    if cmds.objExists(masterG):
        cmds.confirmDialog(
            t='Error',
            m='This muscle name already exists change it please')
        return

    muscleAxisVal = ''
    circleAxis = [0, 0, 0]
    if muscleAxis == 1:
        muscleAxisVal = "X"
        circleAxis[0] = 1
    if muscleAxis == 2:
        muscleAxisVal = "Y"
        circleAxis[1] = 1
    if muscleAxis == 3:
        muscleAxisVal = "Z"
        circleAxis[2] = 1
    muscleLength = cmds.floatSliderGrp(
        'srbMuscleLengthFloatSliderGrp', q=True, value=True)

    # CALCULATE THE MEASUREMENTS FOR DISTANCE OR LENGTH OF THE MUSCLE---
    spMpLength = epMpLength = muscleLength / 2
    spMpLength = spMpLength * -1
    epMpLength = epMpLength * 1

    # CREATE THREE CIRCLES SP, MP AND EP CIRCLES---
    spCircle = cmds.circle(
        c=(0, 0, 0),
        nr=(circleAxis[0], circleAxis[1], circleAxis[2]),
        sw=360, r=spRadius, d=3, ut=0, tol=6.10236e-005,
        s=8, ch=1, n=mPrefix + "_spCircle")
    mpCircle = cmds.circle(
        c=(0, 0, 0),
        nr=(circleAxis[0], circleAxis[1], circleAxis[2]),
        sw=360, r=mpRadius, d=3, ut=0, tol=6.10236e-005,
        s=8, ch=1, n=mPrefix + "_mpCircle")
    epCircle = cmds.circle(
        c=(0, 0, 0),
        nr=(circleAxis[0], circleAxis[1], circleAxis[2]),
        sw=360, r=epRadius, d=3, ut=0, tol=6.10236e-005,
        s=8, ch=1, n=mPrefix + "_epCircle")

    # MOVE THE CIRCLES TO APPROPRIATE LOCATIONS---
    cmds.setAttr(
        spCircle[0] + ".translate" + muscleAxisVal, spMpLength)
    cmds.setAttr(
        epCircle[0] + ".translate" + muscleAxisVal, epMpLength)

    # CREATE AND STORE THE ARC LENGTH OF THE MP CIRCLE---
    oldArcLength = cmds.arclen(mpCircle[0])

    # LOFT THE CIRCLES TO CREATE A NURBS TUBE---
    muscleGeo = cmds.loft(
        spCircle[0],
        mpCircle[0],
        epCircle[0],
        ch=1, u=1, c=0, ar=1, d=3,
        ss=surfaceDegree, rn=0, po=0, rsn=True)

    # Set preferences for loft poligon mesh creation
    cmds.nurbsToPolygonsPref(polyType=1, polyCount=meshRes)
    muscleMesh = cmds.loft(
        spCircle[0], mpCircle[0], epCircle[0],
        ch=0, u=1, c=0, ar=1, d=3, ss=1, rn=0, po=1, rsn=True)

    muscleGeo[0] = cmds.rename(muscleGeo[0], mPrefix + "_geoInf")
    muscleMesh[0] = cmds.rename(muscleMesh[0], mPrefix + "_MeshInf")

    # Wrap Muscle Geo to Muscle Nurbs Surface
    cmds.select(muscleMesh[0], muscleGeo[0], r=True)
    wrap = mel.eval(
        'doWrapArgList "7" { "1","0","1", "2", "1", "1", "0", "0" }'
    )
    print wrap

    # CREATE SP, MP AND EP CONTROL OBJECTS---
    spCc = cmds.curve(
        d=1,
        p=(
            [0, 0, 1], [0, 0.5, 0.866025], [0, 0.866025, 0.5],
            [0, 1, 0], [0, 0.866025, 0.5], [0, 0.5, 0.866025],
            [0, 0, 1], [0, -0.5, -0.866025], [0, -0.866025, -0.5],
            [0, -1, 0], [0, -0.866025, 0.5], [0, -0.5, 0.866025],
            [0, 0, 1], [0.707107, 0, 0.707107], [1, 0, 0],
            [0.707107, 0, -0.707107], [0, 0, -1], [-0.707107, 0, -0.707107],
            [-1, 0, 0], [-0.866025, 0.5, 0], [-0.5, 0.866025, 0],
            [0, 1, 0], [0.5, 0.866025, 0], [0.866025, 0.5, 0],
            [1, 0, 0], [0.866025, -0.5, 0], [0.5, -0.866025, 0],
            [0, -1, 0], [-0.5, -0.866025, 0], [-0.866025, -0.5, 0],
            [-1, 0, 0], [-0.707107, 0, 0.707107], [0, 0, 1]
        ),
        k=(
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
            18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32),
        n=mPrefix + "_spCc")
    mpCc = cmds.curve(
        d=1,
        p=(
            [0, 0, 1], [0, 0.5, 0.866025], [0, 0.866025, 0.5],
            [0, 1, 0], [0, 0.866025, 0.5], [0, 0.5, 0.866025],
            [0, 0, 1], [0, -0.5, -0.866025], [0, -0.866025, -0.5],
            [0, -1, 0], [0, -0.866025, 0.5], [0, -0.5, 0.866025],
            [0, 0, 1], [0.707107, 0, 0.707107], [1, 0, 0],
            [0.707107, 0, -0.707107], [0, 0, -1], [-0.707107, 0, -0.707107],
            [-1, 0, 0], [-0.866025, 0.5, 0], [-0.5, 0.866025, 0],
            [0, 1, 0], [0.5, 0.866025, 0], [0.866025, 0.5, 0],
            [1, 0, 0], [0.866025, -0.5, 0], [0.5, -0.866025, 0],
            [0, -1, 0], [-0.5, -0.866025, 0], [-0.866025, -0.5, 0],
            [-1, 0, 0], [-0.707107, 0, 0.707107], [0, 0, 1]
        ),
        k=(
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
            18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32),
        n=mPrefix + "_mpCc")
    epCc = cmds.curve(
        d=1,
        p=(
            [0, 0, 1], [0, 0.5, 0.866025], [0, 0.866025, 0.5],
            [0, 1, 0], [0, 0.866025, 0.5], [0, 0.5, 0.866025],
            [0, 0, 1], [0, -0.5, -0.866025], [0, -0.866025, -0.5],
            [0, -1, 0], [0, -0.866025, 0.5], [0, -0.5, 0.866025],
            [0, 0, 1], [0.707107, 0, 0.707107], [1, 0, 0],
            [0.707107, 0, -0.707107], [0, 0, -1], [-0.707107, 0, -0.707107],
            [-1, 0, 0], [-0.866025, 0.5, 0], [-0.5, 0.866025, 0],
            [0, 1, 0], [0.5, 0.866025, 0], [0.866025, 0.5, 0],
            [1, 0, 0], [0.866025, -0.5, 0], [0.5, -0.866025, 0],
            [0, -1, 0], [-0.5, -0.866025, 0], [-0.866025, -0.5, 0],
            [-1, 0, 0], [-0.707107, 0, 0.707107], [0, 0, 1]
        ),
        k=(
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
            18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32),
        n=mPrefix + "_epCc")

    # MOVE EACH CONTROL OBJECTS TO THE LOCATION OF RESPECTIVE CIRCLES---
    cmds.setAttr(spCc + ".translate" + muscleAxisVal, spMpLength)
    cmds.setAttr(epCc + ".translate" + muscleAxisVal, epMpLength)

    # PARENT EACH CIRCLES TO RESPECTIVE CONTROLLERS---
    cmds.parent(spCircle[0], spCc)
    cmds.parent(mpCircle[0], mpCc)
    cmds.parent(epCircle[0], epCc)

    # CREATE SOME ATTRIBUTES ON MPCC---
    cmds.addAttr(
        "|" + mpCc, ln="muscle", at='double', k=1)
    cmds.setAttr(mpCc + ".muscle", lock=True)

    if muscleType == 1:
        cmds.addAttr(
            "|" + mpCc,
            ln="bulge", at='double', k=1, dv=1)

    cmds.addAttr(
        "|" + mpCc,
        ln="spPoint", at='double', k=1, min=0, max=1, dv=1)
    cmds.addAttr(
        "|" + mpCc,
        ln="epPoint", at='double', k=1, min=0, max=1, dv=1)
    cmds.addAttr(
        "|" + mpCc,
        ln="spOrient", at='double', k=1, min=0, max=1, dv=1)
    cmds.addAttr(
        "|" + mpCc,
        ln="epOrient", at='double', k=1, min=0, max=1, dv=1)

    # CREATE A DISTANCE BETWEEN NODE AND CONNECT
    # REQUIRED DATA TO MEASURE THE DISTANCE BETWEEN SP AND EP CC---
    db = cmds.createNode('distanceBetween', n=mPrefix + "_db")
    cmds.connectAttr(
        spCc + ".worldMatrix", db + ".inMatrix1")
    cmds.connectAttr(
        epCc + ".worldMatrix", db + ".inMatrix2")

    # POINT AND ORIENT CONSTRAINT MPCC OFFSET
    # GROUP NODE BY BOTH SPCC AND EPCC AND MAKE SOME CONNECTIONS---
    cmds.select(mpCc, r=True)
    mpCc_off = cmds.group(n=mPrefix + "_mpCc_off")

    cmds.select(spCc, r=True)
    cmds.select(epCc, add=True)
    cmds.select(mpCc_off, add=True)
    pc = cmds.pointConstraint(mo=True, weight=1)

    cmds.select(spCc, r=True)
    cmds.select(epCc, add=True)
    cmds.select(mpCc_off, add=True)
    oc = cmds.orientConstraint(mo=True, weight=1)

    cmds.connectAttr(
        mpCc + ".spPoint",
        pc[0] + "." + mPrefix + "_spCcW0")
    cmds.connectAttr(
        mpCc + ".epPoint",
        pc[0] + "." + mPrefix + "_epCcW1")
    cmds.connectAttr(
        mpCc + ".spOrient",
        oc[0] + "." + mPrefix + "_spCcW0")
    cmds.connectAttr(
        mpCc + ".epOrient",
        oc[0] + "." + mPrefix + "_epCcW1")

    # QUERY IF THE USER SELECTION OF MUSCLE
    # TYPE AND EXECUTE THE PROCESS REQUIRED---
    if muscleType == 1:
        # CREATE A MULTIPLY DIVIDE NODE AND MAKE REQUIRED CONNECTIONS---
        mdS = cmds.createNode('multiplyDivide', n=mPrefix + "_scale_MD")
        cmds.connectAttr(
            db + ".distance", mdS + ".input1X")
        cmds.setAttr(mdS + ".input2X", 1)
        cmds.setAttr(mdS + ".operation", 2)

        md = cmds.createNode('multiplyDivide', n=mPrefix + "_MD")
        cmds.connectAttr(
            mpCc + ".bulge", md + ".input1X")
        cmds.connectAttr(
            mdS + ".outputX", md + ".input2X")
        cmds.setAttr(
            md + ".operation", 2)

        # MAKE A SCALE CONNECTION BETWEEN MD AND MP CC---
        cmds.connectAttr(
            md + ".outputX",
            mpCc_off + ".sx", f=True)
        cmds.connectAttr(
            md + ".outputX",
            mpCc_off + ".sy", f=True)
        cmds.connectAttr(
            md + ".outputX",
            mpCc_off + ".sz", f=True)

    # AUTO ADJUST THE SCALE OF MP CIRCLE---
    scaleOffset = 1
    newArcLength = cmds.arclen(mpCircle[0])
    if oldArcLength > newArcLength:
        while oldArcLength > newArcLength:
            scaleOffset = scaleOffset + 0.01
            cmds.setAttr(
                mpCircle[0] + '.s', scaleOffset, scaleOffset, scaleOffset)
            newArcLength = cmds.arclen(mpCircle[0])
    else:
        while oldArcLength < newArcLength:
            scaleOffset = scaleOffset - 0.01
            cmds.setAttr(
                mpCircle[0] + '.s', scaleOffset, scaleOffset, scaleOffset)
            newArcLength = cmds.arclen(mpCircle[0])

    # COLOR CODE THE CONTROL OBJECTS---
    cmds.setAttr(mpCc + ".overrideEnabled", 1)
    cmds.setAttr(mpCc + ".overrideColor", 17)
    cmds.setAttr(spCc + ".overrideEnabled", 1)
    cmds.setAttr(spCc + ".overrideColor", 30)
    cmds.setAttr(epCc + ".overrideEnabled", 1)
    cmds.setAttr(epCc + ".overrideColor", 4)

    # OVERRIDE THE RENDER SETTINGS SO THAT
    # THE MUSCLE GEOMETRY IS NOT RENDERRED---
    attrOn = [
        ".overrideShading", ".overrideTexturing",
        ".overridePlayback", ".overrideVisibility"]
    attrOff = [
        ".overrideLevelOfDetail", ".castsShadows", ".receiveShadows",
        ".motionBlur", ".primaryVisibility", ".smoothShading",
        ".visibleInReflections", ".visibleInRefractions"]
    for temp in [muscleGeo[0], muscleMesh[0]]:
        for aon in attrOn:
            cmds.setAttr(temp + aon, 1)
        for aoff in attrOff:
            cmds.setAttr(temp + aoff, 0)

    # CREATE A MUSCLE SHADER---
    # CHECK IF THE MUSCLE SHADER ALREADY EXISTS---
    shaders = cmds.ls(mat=True)
    shader = ''
    shaderQuery = 1
    for shader in shaders:
        if shader == "srbMuscleShader":
            shaderQuery = 0
    if shaderQuery == 1:
        muscleShader = cmds.shadingNode('lambert', asShader=True)
        cmds.rename(muscleShader, "srbMuscleShader")

        # CREATE THE RAMP TEXTURE---
        rampShader = cmds.shadingNode('ramp', asTexture=True)
        cmds.rename(rampShader, "srbMuscleRamp")
        cmds.setAttr('srbMuscleRamp.type', 0)
        cmds.setAttr('srbMuscleRamp.interpolation', 4)

        # CREATE RAMP COLOR SET THE COLOR GRADATION ALIGNMENTS---
        cmds.setAttr(
            'srbMuscleRamp.colorEntryList[0].color',
            1.0, 0.95, 0.75, type='double3')
        cmds.setAttr(
            'srbMuscleRamp.colorEntryList[1].color',
            1.0, 0.1, 0.1, type='double3')
        cmds.setAttr(
            'srbMuscleRamp.colorEntryList[2].color',
            1.0, 0, 0, type='double3')
        cmds.setAttr(
            'srbMuscleRamp.colorEntryList[3].color',
            1.0, 0.1, 0.1, type='double3')
        cmds.setAttr(
            'srbMuscleRamp.colorEntryList[4].color',
            1.0, 0.95, 0.75, type='double3')

        cmds.setAttr('srbMuscleRamp.colorEntryList[0].position', 0.0)
        cmds.setAttr('srbMuscleRamp.colorEntryList[1].position', 0.35)
        cmds.setAttr('srbMuscleRamp.colorEntryList[2].position', 0.5)
        cmds.setAttr('srbMuscleRamp.colorEntryList[3].position', 0.65)
        cmds.setAttr('srbMuscleRamp.colorEntryList[4].position', 1.0)

        # SET THE TRANSPARENCY & INCANDESCENCE FOR THE SHADER---
        cmds.setAttr("srbMuscleShader.transparency", 0, 0, 0, type='double3')
        cmds.setAttr("srbMuscleShader.incandescence", 0, 0, 0, type='double3')

        # CONNECT THE RAMP SHADER TO THE SHADER---
        cmds.connectAttr(
            "srbMuscleRamp.outColor", "srbMuscleShader.color", f=True)

    # CREATE MUSCLE SETS---
    muscleSets = cmds.ls(type='objectSet')
    muscleSet = ''
    muscleSetQuery = 1
    for muscleSet in muscleSets:
        if muscleSet == "srbMuscleSet":
            muscleSetQuery = 0
    if muscleSetQuery == 1:
        cmds.select(cl=True)
        cmds.sets(name="srbMuscleSet")

    # ADD THE MUSCLE GEOMETRY TO THE SET--
    cmds.select(muscleMesh[0], r=True)
    cmds.sets(e=True, forceElement='srbMuscleSet')

    # ASSIGN THE MUSCLE SHADER TO THE MUSCLE GEOMETRY---
    cmds.select(muscleMesh[0], r=True)
    cmds.hyperShade(assign="srbMuscleShader")

    # CLEANUP
    ctrls = [
        muscleGeo[0],
        muscleMesh[0],
        spCircle[0],
        mpCircle[0],
        epCircle[0]]
    attrs = [
        '.tx', '.ty', '.tz',
        '.rx', '.ry', '.rz',
        '.sx', '.sy', '.sz']
    for ctrl in ctrls:
        for a in attrs:
            cmds.setAttr(ctrl + a, lock=True, k=True)

    for temp in [muscleGeo[0], muscleMesh[0]]:
        cmds.setAttr(temp + ".inheritsTransform", 0)
        cmds.setAttr(temp + ".overrideEnabled", 1)
        cmds.setAttr(temp + ".overrideDisplayType", 2)

    # GROUP EVERYTHING---
    grp = cmds.group(em=True, n=masterG)
    temp = [
        muscleGeo[0], muscleGeo[0] + "Base",
        muscleMesh[0], spCc,
        mpCc_off, epCc]
    for t in temp:
        cmds.parent(t, grp)

    # Connect scale to multiply divide for rig scalability
    if muscleType == 1:
        cmds.connectAttr(
            masterG + ".sx",
            mdS + ".input2X")

    # cmds.setAttr(mPrefix + "_geoInf.v", 0)
    cmds.setAttr(muscleGeo[0] + ".v", 0)
    cmds.select(cl=True)

    print "Sucessfully created the " + mPrefix + " muscle..."


# CREATE RESET PROCEDURE---
def reset():
    cmds.deleteUI('srbMuscleWin')
    srbMuscle()


# PROCEDURE FOR PREPARING OBJECTS TO BE INFLUENCE ONBJECTS---
# SO THAT WEIGHTS WILL MIRROR LATER---
def srbPrepareMuscleProc():
    attrs = [
        '.tx', '.ty', '.tz',
        '.rx', '.ry', '.rz'
        '.sx', '.sy', '.sz']
    sel = cmds.ls(sl=True)
    if len(sel) > 0:
        for obj in sel:
            cmds.select(obj, r=True)

            # UNLOCK CHANNELS---
            for a in attrs:
                cmds.setAttr(obj + a, lock=False, k=True)

            cmds.CenterPivot()
            cmds.FreezeTransformations()
            objPos = cmds.xform(q=True, a=True, ws=True, piv=True)
            cmds.move(0, 0, 0, rpr=True)
            cmds.FreezeTransformations()
            cmds.xform(a=True, ws=True, t=(objPos[0], objPos[1], objPos[2]))

            # LOCK CHANNELS---
            for a in attrs:
                cmds.setAttr(obj + a, lock=True, k=True)

        print "Sucessfully completed preparing muscle object..."
    else:
        cmds.warning("Select at least one or more muscle object...")


# PROCEDURE FOR MIRRORING MUSCLE OBJECT---
def srbMirrorMuscleProc():
    replaceString = "_grp"
    sel = cmds.ls(sl=True)
    sizeSel = len(sel)

    if sizeSel == 0 and sizeSel < 2 and sizeSel > 2:
        cmds.warning(
            "Error...Select the base muscle and the target muscle")
    else:
        base = sel[0].replace(replaceString, '')
        target = sel[1].replace(replaceString, '')

        # STORE SCALE---
        objGrpScl = cmds.xform(sel[0], q=True, r=True, os=True, s=True)
        epScl = cmds.xform(
            base + "_epCc", q=True, r=True, os=True, s=True)
        spScl = cmds.xform(
            base + "_spCc", q=True, r=True, os=True, s=True)
        mpScl = cmds.xform(
            base + "_mpCc", q=True, r=True, os=True, s=True)
        cmds.xform(
            sel[1], os=True, r=True,
            s=(objGrpScl[0], objGrpScl[1], objGrpScl[2]))
        cmds.xform(
            target + "_epCc", os=True, r=True,
            s=(epScl[0], epScl[1], epScl[2]))
        cmds.xform(
            target + "_spCc", os=True, r=True,
            s=(spScl[0], spScl[1], spScl[2]))
        cmds.xform(
            target + "_mpCc", os=True, r=True,
            s=(mpScl[0], mpScl[1], mpScl[2]))

        # STORE TRANSLATION---
        objGrpPos = cmds.xform(sel[0], q=True, a=True, ws=True, t=True)
        epPos = cmds.xform(
            base + "_epCc", q=True, a=True, ws=True, t=True)
        spPos = cmds.xform(
            base + "_spCc", q=True, a=True, ws=True, t=True)
        mpPos = cmds.xform(
            base + "_mpCc", q=True, a=True, ws=True, t=True)

        # APPLY ROTATION
        cmds.xform(
            sel[1], a=True, ws=True,
            t=(objGrpPos[0] * -1, objGrpPos[1], objGrpPos[2]))
        cmds.xform(
            target + "_epCc", a=True, os=True,
            t=(epPos[0] * -1, epPos[1], epPos[2]))
        cmds.xform(
            target + "_spCc", a=True, os=True,
            t=(spPos[0] * -1, spPos[1], spPos[2]))
        cmds.xform(
            target + "_mpCc", a=True, os=True,
            t=(mpPos[0] * -1, mpPos[1], mpPos[2]))

        # STORE ROTATION---
        objGrpRot = cmds.xform(sel[0], q=True, a=True, ws=True, ro=True)
        epRot = cmds.xform(
            base + "_epCc", q=True, a=True, os=True, ro=True)
        spRot = cmds.xform(
            base + "_spCc", q=True, a=True, os=True, ro=True)
        mpRot = cmds.xform(
            base + "_mpCc", q=True, a=True, os=True, ro=True)

        # APPLY ROTATION---
        cmds.xform(
            sel[1], a=True, ws=True,
            ro=(objGrpRot[0], objGrpRot[1] * -1, objGrpRot[2] * -1))
        cmds.xform(
            target + "_epCc", a=True, os=True,
            ro=(epRot[0], epRot[1] * -1, epRot[2] * -1))
        cmds.xform(
            target + "_spCc", a=True, os=True,
            ro=(spRot[0], spRot[1] * -1, spRot[2] * -1))
        cmds.xform(
            target + "_mpCc", a=True, os=True,
            ro=(mpRot[0], mpRot[1] * -1, mpRot[2] * -1))

        print "Muscle v1.0 has sucessfully mirrored the muscle..."
