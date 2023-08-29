import maya.cmds as cmds
import maya.mel as mel
import string

def transAnim():
    sel = cmds.ls( sl = True )
    last = cmds.ls( tail = True, sl = True )
    
    current = cmds.currentTime( q = True )
    start = cmds.playbackOptions( q = True, min = True )
    simpleEn = cmds.checkBox( 'SiNcheckbox', q = True, en = True )
    simple = cmds.checkBox( 'SiNcheckbox', q = True, v = True )
    offSetEn = cmds.checkBox( 'offSetCB', q = True, en = True )
    offSet = cmds.checkBox( 'offSetCB', q = True, v = True )
    value = cmds.floatField( 'offSetFF', q = True, v = True )
    
    if len(sel) == 2 :
        for each in sel:
            if each != last[0]:
                conn = cmds.listConnections(each, d = False, s = True, t = "animCurve" )
                connD = cmds.listConnections(last[0], d = False, s = True, t = "animCurve" )
                #if type(connD).__name__!='NoneType':
                if connD:
                    cmds.delete( connD )
                if type(conn).__name__!='NoneType':
                    for eC in conn:
                        attr = cleanNameS( eC, 1 )
                        checkAttr = mel.eval('attributeExists '+attr+' '+last[0])
                        if checkAttr == 1:
                            copyCurve = cmds.duplicate( eC )
                            cmds.connectAttr( (copyCurve[0]+".output"), (last[0]+"."+attr) )

                    # GET THE NEW CURVES ON THE DESTINATION OBJECT    
                    connD = cmds.listConnections(last[0], d = False, s = True, t = "animCurve" )
                    
                    # IN CASE IT IS WORLD SPACE
                    if (cmds.radioButtonGrp( 'WLradioGrp', q = True, sl = True )) == 2:
                        autoKey = cmds.autoKeyframe (q = True, state = True )
                        cmds.autoKeyframe (e = True, state = False )
                        for eCC in connD:
                            x = 0
                            curveRange = cmds.keyframe( eCC, q = True, iub = True )
                            startC = int(curveRange[0])
                            endC = int(curveRange[len(curveRange)-1])
                            for x in range( startC, endC ):
                                cmds.currentTime( int(curveRange[0])+x );
                                attr = cleanNameS( eCC, 1 )
                                if attr == 'translateX' or attr == 'translateY' or attr == 'translateZ':
                                    mel.eval('matcher 1')
                                    cmds.setKeyframe( last[0], at = attr )
                                elif attr == 'rotateX' or attr == 'rotateY' or attr == 'rotateZ':
                                    mel.eval('matcher 2')
                                    cmds.setKeyframe( last[0], at = attr )
                                elif attr == 'scaleX' or attr == 'scaleY' or attr == 'scaleZ':
                                    mel.eval('matcher 3')
                                    cmds.setKeyframe( last[0], at = attr )
                                else:
                                    kValue = cmds.getAttr( sel[0]+"."+attr , t = x)
                                    cmds.setKeyframe( last[0], e = True, t = x, v = kValue, at = attr )
                                x = x+1
                        cmds.autoKeyframe (e = True, state = autoKey )
                        cmds.currentTime( start )
                    
                    # OFSETTING THE ANIMATION OF THE VALUE SPECIFIED
                    if offSetEn == 1 and offSet ==1:
                        cmds.keyframe( connD, e = True, iub = True, r = True, o = 'move', tc = value )
                        
                    # SIMPLIFYING THE CURVE WITH MAYA ALGORITHM
                    if simpleEn == 1 and simple == 1:
                        for eS in connD:
                            cmds.filterCurve( eS, f = 'simplify', tto = 0.05 )

                else:
                    print '------->>>> no animation to be copyed here. <<<<-------'
    else:
        print '------->>> please two objects to copy animation from the first to the second. <<<-------'

def cleanNameS( name, num ):
    if num == 0 :
        commas = ":"
    if num == 1 :
        commas = "_"
    for eComm in commas:
        buff = name.split( commas )
        cleanName = buff[(len(buff)-1)]
        return cleanName;
