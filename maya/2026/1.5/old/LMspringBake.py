##################################################################
#                                                                #
#                      SPRING BAKE 1.11.18                       #
#            by Luismi Herrera. Twitter: @luismiherrera          #
#                                                                #
#  1. Adjust the Range Slider to chose frames to be baked.       #
#  2. Execute SPRING BAKE by clicking on the shelf icon.         #
#                                                                #
##################################################################

import maya.cmds as cmds

minTime = cmds.playbackOptions(minTime=True, query=True)
maxTime = cmds.playbackOptions(maxTime=True, query=True)

LMspringObjects = cmds.ls('LMspring*')

if(len(LMspringObjects)>0):
    cmds.bakeResults(sel, t=(minTime,maxTime), simulation=True)
    cmds.delete(LMspringObjects)
else:
    cmds.warning( "Nothing to bake. Use SPRING PREVIS first." )