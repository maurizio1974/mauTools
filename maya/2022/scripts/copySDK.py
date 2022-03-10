# copySDK, 20110109
# Python definitions to mirror SDK setups to single/multiple objects.
# isoparmB
# for questions or suggestions, email me at martinik24@gmail.com

import maya.cmds as cmds
import re

def copySDK(curAttrs=[], mirrorAttrs=[], source='', targets=[], search='', replace='', specialIter=[], sort=False, fromDriven=True, fromDriver=False):
    '''This definition is used to copy SDK setups from one node to another node/s in Maya.
With no declarations, the script works by getting the selection list. The first selected object is the source, everything else is a target. The script will copy SDKs from the source and replicate it on the targets. SDKs will be linked to the original source driver by default.

Node and attribute options
curAttrs    - is for explicitly declaring which attributes to copy SDKs from. If you don't declare it, the script will search for SDKs on all keyable attributes of the source.
mirrorAttrs - is to tell the script which attributes wii receive a negative value.
source      - is to explicitly declare the source node to copy. targets must also be declared. If not declared, the selection list is used and the first selected object is the source.
targets     - is to explicitly decalare target nodes to apply SDKs to. source must also be declared. If not declared, the selection list is used and all other objects other than the first comprise the targets list.

String search options for driver nodes:
search      - is used for pattern searching in Driver names. search and replace both have to be declared. If not declared, the SDK's are connected to the original driver node attributes. This attribute accepts regex search strings.
replace     - is used for pattern searching in Driver names, to look for alternate Driver nodes. This provides the replace string to use when looking for Driver nodes. The replace string can use the special %s character to provide more flexibility with choosing different Drivers for multiple Driven nodes.
specialIter - is used when you want to provide a list or an iteratable object to use when you have want more flexibility in naming your driver object. Your replace variable must contain a replace string with %s, and that will get swapped by what you enter here.
            - You can use a single list ['a', 'b', 'c'], lists within lists for multiple %s's [ ['a', 'b', 'c'], [1, 2, 3] ], or python techniques such as range e.g., range(0,12).
            - The only rule is that the lists have to be as long as the number of targets.
sort        - Sort the target list alphabetically. Helps to reorganize the list if you're using the specialIter function.
'''
    # Make sure all variables are correct
    if not source or not targets:
        curlist  = cmds.ls(sl=True, ap=True)
        if not curlist or len(curlist) < 2:
            print ('\nPlease select at least two objects.')
            return
        source = curlist[0]
        targets = curlist[1:]
    elif targets.__class__ == ''.__class__ and targets.strip():
        targets = [targets]
    if sort:
        targets.sort()
    if curAttrs:
    	if curAttrs.__class__ == ''.__class__ and curAttrs.strip():
    	    curAttrs = [curAttrs]    	    
        attrs = [ cmds.attributeQuery(x, node=source, ln=True) for x in curAttrs if cmds.attributeQuery(x, node=source, ex=True) ]
        if not attrs:
            print 'Specified attributes ' + ', '.join(attrs)+ ', do not exist on driver ' + source + '.'
            return
    else:
        attrs =  cmds.listAttr(source, k=True)
    if mirrorAttrs:
    	if mirrorAttrs.__class__ == ''.__class__:
    	    mirrorAttrs = [mirrorAttrs] 
        mirrorAttrs = [ cmds.attributeQuery(x, node=source, ln=True) for x in mirrorAttrs if cmds.attributeQuery(x, node=source, ex=True) ]
        if not mirrorAttrs:
            print 'Specified attributes to be mirrored ' + ', '.join(mirrorAttrs)+ ', do not exist on driver ' + source + '.'
            return
        
        
    # Acquire SDK and blendweighted nodes from source
    SDKnodes = []
    blendWeightedNodes = []
    for attr in attrs:
        
        conn = cmds.listConnections(source + '.' + attr, scn=True, d=False, s=True, p=False)
        if conn:
            type = cmds.ls(conn[0], st=True)[1]
            mirrorAttr = False
            if attr in mirrorAttrs:
                mirrorAttr = True
            if type in ['animCurveUL', 'animCurveUA', 'animCurveUU']:
                SDKnodes.append( (conn[0], attr, mirrorAttr) )
            elif type == 'blendWeighted':
                blendWeightedNodes.append( (conn[0], attr, mirrorAttr) )
                
    
    # Determine special iteration parameters if there is a %s in the replace variable. Used for complex Driver name searching, if each of your targets has a different driver object.
    SDKResults = []
    BWNResults = []
    iterExec   = None
    if not search or not replace:
        search  = None
        replace = None
    elif replace.count('%s') and not specialIter:
        print ('\nWhen using the %s character, you must declare a specialIter list')
        return
    elif replace.count('%s'):
        if specialIter[0].__class__ == [].__class__ or specialIter[0].__class__ == ().__class__:
            numArgs  = len(specialIter)
            iterExec = 'feeder = ('
            iterScratch = []
            for x in range(0, numArgs + 1):
                if len(x) != len(targets):
                    print '\nspecialIter item ' + str(x) + ' length (' + str(len(x) ) + ') must be the same as target length (' + str(len(targets) ) + ') .'
                    return
                iterScratch.append('specialIter[' + str(x) + '][i]')
                
            iterExec += ', '.join(iterScratch) + ' )'
        else:
            if len(specialIter) != len(targets):
                print '\nspecialIter length (' + str(len(specialIter) ) + ') must be the same as target length (' + str(len(targets) ) + ') .'
                return
            iterExec = 'feeder = specialIter[i]' 
    i = 0
    
    
    # Go through all the targets and mirror SDK nodes and blendWeighted nodes with SDK from source.
    for target in targets:
        if SDKnodes:
            doSDKs(SDKnodes, target, search, replace, i, iterExec, specialIter, SDKResults, BWNResults)
                
        if blendWeightedNodes:
            for node in blendWeightedNodes:
            	SDKnodes2 = []
            	SKnodes   = []
            	attrs = cmds.listAttr(node[0] + '.input', multi=True)
            	if not attrs:
            	    print '\nNo SDK nodes connected to blendWeighted node ' + node[0] + ', skipping...'
            	    continue
            	for attr in attrs:
            	    conn = cmds.listConnections(node[0] + '.' + attr, scn=True, d=False, s=True, p=False)
            	    if conn:
                        type = cmds.ls(conn[0], st=True)[1]
                        mirrorAttr = node[2]
                        if type in ['animCurveUL', 'animCurveUA', 'animCurveUU']:
                            SDKnodes2.append( (conn[0], attr, mirrorAttr) )
                        elif type in ['animCurveTL', 'animCurveTA', 'animCurveTU']:
                            SKnodes.append(   (conn[0], attr, mirrorAttr) )
                if SDKnodes2:
                    newBlendNode = cmds.duplicate(node[0])[0]
                    doSDKs(SDKnodes2, newBlendNode, search, replace, i, iterExec, specialIter, SDKResults, BWNResults)
                    if SKnodes:
                        for node2 in SKnodes:
                            newKeyNode = cmds.duplicate(node2[0])[0]
                            if node2[2]:
                                mirrorKeys(newKeyNode)
                            cmds.connectAttr(newKeyNode + '.output', newBlendNode + '.' + node2[1], f=True)
                    cmds.connectAttr(newBlendNode + '.output', target + '.' + node[1], f=True)
                    BWNResults.append('Connected Blend Weighted node ' + newBlendNode + '.output' + ' to Driven node ' + target + '.' + node[1])
                else:
            	    print '\nNo SDK nodes connected to blendWeighted node ' + node[0] + ', skipping...'
        i += 1
        
        
        
def doSDKs(SDKnodes, target, search, replace, i, iterExec, specialIter, SDKResults, BWNResults):
    '''This is the procedure that actually performs the SDK replication'''
    
    for node in SDKnodes:
        driver = cmds.connectionInfo(node[0] + '.input', sfd=True)
        if not driver or (not cmds.attributeQuery(node[1], node=target, ex=True) and not cmds.attributeQuery(node[1].split('[')[0], node=target, ex=True)):
            continue
        newKeyNode = cmds.duplicate(node[0])[0]
        if search:
            curRegexer = re.search(search, driver)
            repPattern = curRegexer.group(0)
            if repPattern:
            	
    	        if replace.count('%s'):
    	            currentRep = replace
    	            exec(iterExec)
    	            currentRep = currentRep % feeder
    	            newDriver  = driver.split('.')[0].replace(repPattern, currentRep)
    	        else:
    	            newDriver  = driver.split('.')[0].replace(repPattern, replace)
    	            
    	        if  cmds.objExists(newDriver) and cmds.attributeQuery('.'.join(driver.split('.')[1:]), node=newDriver, ex=True):
    	            cmds.connectAttr(newDriver + '.' + '.'.join(driver.split('.')[1:]), newKeyNode + '.input', f=True)
    	        elif cmds.objExists(newDriver) and not cmds.attributeQuery('.'.join(driver.split('.')[1:]), node=newDriver, ex=True):
    	            print '\nDriver node ' + newDriver + ' does not have the attribute ' + '.'.join(driver.split('.')[1:]) + ' .'
    	            cmds.delete(newKeyNode)
    	            continue
    	        else:
    	            print '\nFailure to find a driver for node ' + target + ' based on search criteria ' + search + ' for driver node ' + driver.split('.')[0] + ' .'
    	            cmds.delete(newKeyNode)
    	            continue
    	    else:
    	        print '\nFailure to find a driver for node ' + target + ' based on search criteria ' + search + ' for driver node ' + driver.split('.')[0] + ' .'
    	        cmds.delete(newKeyNode)
    	        continue
        else:
            cmds.connectAttr(driver, newKeyNode + '.input', f=True)
            newDriver = driver
        if node[2]:
            mirrorKeys(newKeyNode)
        cmds.connectAttr(newKeyNode + '.output', target + '.' + node[1], f=True)
        SDKResults.append('Connected Driver node ' + newDriver + '.' + '.'.join(driver.split('.')[1:]) + '.output' + ' to Driven node ' + target + '.' + node[1] )
        
        
        
def mirrorKeys(newKeyNode):
    '''Mirror keyframe node procedure, in case you need to flip your SDK's. Also works with ordinary keyframe nodes.'''
    keyType = cmds.ls(newKeyNode, st=True)[1]
    try:
        cmds.selectKey(clear=True)
    except:
        pass
    numKeys = len(cmds.listAttr(newKeyNode + '.ktv', multi=True) ) / 3
    for x in range(0, numKeys):
        v = cmds.getAttr(newKeyNode + '.keyTimeValue[' + str(x) + ']')
        v = [v[0][0], v[0][1] * -1]
        if keyType in ['animCurveTU', 'animCurveTA', 'animCurveTL']:
        	cmds.selectKey(newKeyNode, add=True, k=True, t=(v[0],v[0]) )
        elif keyType in ['animCurveUU', 'animCurveUA', 'animCurveUL']:
        	cmds.selectKey(newKeyNode, add=True, k=True, f=(v[0],v[0]) )
        cmds.keyframe(animation='keys', absolute=True, valueChange=v[1])
        try:
            cmds.selectKey(clear=True)
        except:
            pass
