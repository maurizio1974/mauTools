#######################################################################################
#                                                                                     #
#                            SPRING PREVIS 1.11.18                                    #
#                  by Luismi Herrera. Twitter: @luismiherrera                         #
#                                                                                     #
# 1. Select something (normaly an animation control, but it could be anything).       #
# 2. Execute SPRING PREVIS script (by clicking on the shelf icon).                    #
# 3. Change or animate 'Goal Weight[0]' value (under 'luismiParticleShape') until     #
#    you are happy with the result.                                                   #
# 4. Execute SPRING BAKE script (by clicking on the shelf icon).                      #
#                                                                                     #
#######################################################################################

import maya.cmds as cmds

minTime = cmds.playbackOptions(minTime=True, query=True)
maxTime = cmds.playbackOptions(maxTime=True, query=True)
sel = cmds.ls(selection=True)

units = cmds.currentUnit(query=True, linear=True)
modifier = 1.0
if(units!='cm'):
    unitsInCm = (cmds.convertUnit(1, fromUnit=units, toUnit='cm'))
    modifier = float(unitsInCm[:-2])

if len(sel) == 0:
    cmds.warning( "Nothing Selected" )
else:
    if(cmds.objExists('LMspring')):
        cmds.warning('There are existing LMspring particles in the scene! Use Spring Bake or delete the LMspring group.')
    else:
        cmds.group(name='LMspring', empty=True)
        for i in range(len(sel)):
            cmds.currentTime( minTime, edit=True )
            selLoc = cmds.spaceLocator(name='OriginalPosition_Loc'+str(i))
            luismiPart =cmds.particle(p=[(0, 0, 0)], name='luismiParticle'+str(i))
            tempConst = cmds.parentConstraint(sel[i],selLoc,mo=False)
            # cmds.bakeResults(selLoc, t=(minTime,maxTime))
            cmds.delete(tempConst)
            tempConst2 = cmds.parentConstraint(selLoc,'luismiParticle'+str(i),mo=False)
            cmds.delete(tempConst2)
            cmds.goal( 'luismiParticle'+str(i), g=selLoc, w=.55)
            phyLoc = cmds.spaceLocator(name='physicsLoc'+str(i))
            expression = 'physicsLoc{0}.translateX = luismiParticle{0}Shape.worldCentroidX/{1};physicsLoc{0}.translateY = luismiParticle{0}Shape.worldCentroidY/{1};physicsLoc{0}.translateZ = luismiParticle{0}Shape.worldCentroidZ/{1};'.format(i, modifier)
            cmds.expression(object='physicsLoc'+str(i),string=expression)
            tempConst3 = cmds.pointConstraint('physicsLoc'+str(i), sel[i], mo=True)
            cmds.parent(selLoc, luismiPart, phyLoc, 'LMspring')
        cmds.select('luismiParticle*')
