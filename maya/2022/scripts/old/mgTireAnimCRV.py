import maya.cmds as cmds
import maya.mel as mel

def makeMP(nodes):

    cmds.select(nodes[2])
    tire = cmds.ls(sl=True)
    crv = nodes[0]
    mp = nodes[1]

    for t in tire:
        loc = cmds.spaceLocator(n =( t+'_LOL'))
        cmds.setAttr ((mp+'.fm'), False)
        cmds.connectAttr ((mp+'.rotateOrder'), (loc[0]+'.rotateOrder'))
        cmds.connectAttr ((mp+'.rotateZ'), (loc[0]+'.rotate.rotateZ'))
        cmds.connectAttr ((mp+'.rotateY'), (loc[0]+'.rotate.rotateY'))
        cmds.connectAttr ((mp+'.rotateX'), (loc[0]+'.rotate.rotateX'))

        adlY = cmds.createNode('addDoubleLinear', n = 'transY_ADL')
        cmds.connectAttr ((mp+'.yCoordinate'), (adlY+'.input2'))
        cmds.connectAttr ((adlY+'.output'), (loc[0]+'.translate.translateY'))

        adlX = cmds.createNode('addDoubleLinear', n = 'transX_ADL')
        cmds.connectAttr ((mp+'.xCoordinate'), (adlX+'.input2'))
        cmds.connectAttr ((adlX+'.output'), (loc[0]+'.translate.translateX'))

        adlZ = cmds.createNode('addDoubleLinear', n = 'transZ_ADL')
        cmds.connectAttr ((mp+'.zCoordinate'), (adlZ+'.input2'))
        cmds.connectAttr ((adlZ+'.output'), (loc[0]+'.translate.translateZ'))

        const = cmds.parentConstraint(loc[0], t, sr = ['y','z'])
        nodes.append(const[0])

        print (loc[0]+' centroid has been baked as a curve')

        return nodes


def bakeTireRoll(nodes):
    start = cmds.playbackOptions( q = True, min = True )
    end = cmds.playbackOptions( q = True, max = True )
    cmds.currentTime( start, e = True )

    cmds.select(nodes[2], nodes[3])
    cmds.bakeResults( sm = True, t = (start, end), sb = 1, dic = True, pok = True, sac = True, ral = True, bol = True)

    # CLEAN UP
    curva = cmds.listRelatives(nodes[0], p = True )
    cmds.delete(curva, nodes[1], (nodes[2]+"_LOL"), nodes[4], nodes[5], nodes[6], nodes[7])

def makeTireRoll(nodes):

    cmds.select(nodes[1])
    o = cmds.ls( sl = True )
    t = o[0]
    chi = nodes[1][:-8]+'Rot_grp_CTRL'

    p = cmds.listRelatives(t, typ = 'transform', p = True)
    sh = cmds.listRelatives(nodes[0], s = True)
    crv = sh[0]


    pos1 = cmds.xform( t, q = True, ws = True, t = True )
    grpED = cmds.group ( em = True, n = (t+'.tireED'))
    cmds.setAttr((grpED+'.t'), pos1[0], pos1[1], pos1[2] )

    pos2 = cmds.xform( t, q= True, ws = True, t = True )
    grpSD = cmds.group ( em = True, n = (t+'.tireSD'))
    cmds.setAttr((grpSD+'.t'), pos2[0], pos2[1], pos2[2])

    cmds.parent(grpED, t)
    cmds.parent(grpSD, t)

    radius = cmds.getAttr((nodes[1]+'.radius'))
    print '-------------------------------------------------'
    print radius
    print '-------------------------------------------------'

    cmds.setAttr((grpSD+'.ty'), radius)  # SET RADIUS OF THE TIRE

    ddB = cmds.createNode( 'distanceBetween', n = (t+'_tireDD'))

    cmds.connectAttr ((grpED+'.worldMatrix[0]'), (ddB+'.inMatrix2'))
    cmds.connectAttr ((grpSD+'.worldMatrix[0]'), (ddB+'.inMatrix1'))

    # CREATE NEEDED NODES
    cI = cmds.createNode( 'curveInfo' , n = (t+"COS") )

    cmds.connectAttr ((crv+'.worldSpace[0]'), (cI+'.inputCurve'))

    roP = cmds.createNode( 'multiplyDivide', n = (crv+'_rotationsOnPath_MD'))
    cmds.setAttr((roP+'.operation'), 2)

    piD = cmds.createNode( 'multiplyDivide', n = (crv+'_pi_diameter_MD'))
    cmds.setAttr((piD+'.operation'), 1)

    ofS = cmds.createNode( 'multiplyDivide', n = (crv+'_oneFrameStep_MD'))
    cmds.setAttr((ofS+'.operation'), 1)

    cmD = cmds.createNode( 'multiplyDivide', n = (crv+'_circonference_MD'))
    cmds.setAttr((cmD+'.operation'), 1)

    mp = cmds.createNode( 'motionPath', n = (crv+'_MP'))

    # CONNECT NODES TOGETHER
    cmds.connectAttr ((crv+'.worldSpace[0]'), (mp+'.geometryPath'))
    cmds.connectAttr ((cI+'.arcLength'), (roP+'.input1X'))
    cmds.setAttr((piD+'.input1X'), 6.284)
    cmds.setAttr((piD+'.input1X'), l = True )

    cmds.connectAttr ((roP+'.outputX'), (cmD+'.input2X'))
    cmds.connectAttr ((piD+'.outputX'), (roP+'.input2X'))
    cmds.connectAttr ((cmD+'.outputX'), (ofS+'.input2Z'))
    cmds.setAttr((cmD+'.input1X'), 360.000)
    cmds.connectAttr ((ddB+'.distance'), (piD+'.input2X'))
    cmds.connectAttr ((mp+'.uValue'), (ofS+'.input1Z'))

    #parent = cmds.listRelatives( t, p = True )
    cmds.connectAttr ((ofS+'.outputZ'), (chi+'.rotateX'), f = True )

    # REBUILD CURVE PARAMETRIZATION
    spN = cmds.getAttr(crv+'.spans')
    cmds.rebuildCurve(nodes[0], ch = 0, rpo = 1, rt = 0, end = 1, kr = 0, kcp = 0, kep = 1, kt = 0, s = spN, d = 3, tol =0)

    # MAKE LOCATOR TO FIND UV VALUE SULLA CRV
    cpC = cmds.createNode('closestPointOnCurve', n = (crv+'_CPOC'))
    loc = cmds.spaceLocator( n = (nodes[0]+'director_null'))
    cmds.connectAttr((crv+'.worldSpace'), (cpC+'.inCurve'))
    cmds.setAttr((loc[0]+'.t'), pos1[0], pos1[1], pos1[2])
    cmds.connectAttr((loc[0]+'.t'), (cpC+'.inPosition'))
    cmds.connectAttr((cpC+'.paramU'), (mp+'.uValue'))

    cmds.parentConstraint( p[0], loc)

    print ('The Roll network set up for '+t+' has been set')

    return[crv, mp, nodes[1], chi, grpED, grpSD, loc]
