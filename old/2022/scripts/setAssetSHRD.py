import maya.cmds as cmds
import time

def setAssetSHRD(creature):
        start = time.clock()
        # GET ASSET WITH SHADER ON
        if creature == '':
                sel = ['rig_ROOT']
                for s in sel:
                        if cmds.attributeQuery(s, ex, 'mnmCreature'):
                                crt = cmds.getAttr(s+'.mnmCreature')
                if len(crt) is not 0 :
                        cmds.file('/media/space/jobs/monsters/build/pipeline/'+crt+'/'+crt+'_shaders.ma', i = True, typ = 'mayaAscii',  iv = True, ra = True, namespace = 'TEMP', op = 'v=0', lrd = 'none')
                else:
                        cmds.warning('no creature Defined !')
        else:
                crt = creature
                cmds.file('/media/space/jobs/monsters/build/pipeline/'+crt+'/'+crt+'_shaders.ma', i = True, typ = 'mayaAscii',  iv = True, ra = True, namespace = 'TEMP', op = 'v=0', lrd = 'none')
                
        # GET ALL THE OBJECT IMPORTED
        geoTrans = cmds.ls('TEMP:*', type = "mesh")
        shadingEng = [""]
        shr = [""]
        shrd = ['']
        check = [""]
        for gT in geoTrans:
                if cmds.objExists(gT):
                        # GET ALL THE SHADER ATTACHED TO THE OBJECT
                        shr = cmds.listConnections(gT,  s =  0, d = 1, p = 0, c =  0, type = 'shadingEngine')
                        for sg in shr:
                                if sg is not "initialShadingGroup":
                                        cmds.select(clear = True )
                                        cmds.select(gT[5:])
                                        cmds.sets( e = True, fe  = sg)
        dsp = cmds.listConnections( "TEMP:shader_MD.outputX", d = True, s = False, p = True)
        if len(dsp) != 0 :
                for d in dsp:
                        if cmds.objExists(d[5:]):
                                if cmds.isConnected("TEMP:shader_MD.outputX",d[5:]):
                                        cmds.connectAttr( "TEMP:shader_MD.outputX",d[5:], f = True )
        dsp = cmds.listConnections( "TEMP:shader_MD.outputY", d = True, s = False, p = True)
        if len(dsp) != 0 :
                for d in dsp:
                        if cmds.objExists(d[5:]):
                                if cmds.isConnected("TEMP:shader_MD.outputY",d[5:]):
                                        cmds.connectAttr( "TEMP:shader_MD.outputY",d[5:], f = True )
        
        # RENAME AND CLEAN UP THE SCENE
        cleanUp = [ 'lambert','materialInfo','ramp','bump2d','displacementShader','aiStandard','aiAmbientOcclusion','aiShadowCatcher','aiAOV','aiAOVDriver','aiAOVFilter','aiOptions','aiUtility','aiSkinSss','shadingEngine','file','plusMinusAverage','place2dTexture','gammaCorrect','luminance','reverse','multiplyDivide' ]
        for c in cleanUp:
                node = cmds.ls('TEMP:*', typ = c)
                for n in node:
                        cmds.rename( n, n[5:] )
        
        cmds.delete('TEMP:*')
        cmds.namespace(f  = True, rm = 'TEMP')
        
        elapsed = (time.clock() - start)
        print elapsed
        
