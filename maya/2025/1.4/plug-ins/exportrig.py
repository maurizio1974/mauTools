#
# THREEJS Exporter script for Maya.
#
# Exporter for THREEJS (www.threejs.org)
# Use with the THREE.JSONLoader
#
# <license>
# THREEJS Exporter script for Maya.
# Copyright (C) 2018  Bob Mercier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# </license>

#
# Bits of code liberally lifted from threeJsFileTranslator.py
# Sean Griffin,  sean@thoughtbot.com
#

import pymel.core as pm
import maya.mel as mel
import maya.cmds as mc

def generateUUID():
    import random
    lut = [("%02X" % i) for i in range(0, 256)]

    d0 = random.randint(0, 2**32-1)
    d1 = random.randint(0, 2**32-1)
    d2 = random.randint(0, 2**32-1)
    d3 = random.randint(0, 2**32-1)
    uuid = lut[ d0 & 0xff ] + lut[ d0 >> 8 & 0xff ] + lut[ d0 >> 16 & 0xff ] + lut[ d0 >> 24 & 0xff ] + '-' + \
           lut[ d1 & 0xff ] + lut[ d1 >> 8 & 0xff ] + '-' + \
           lut[ d1 >> 16 & 0x0f | 0x40 ] + lut[ d1 >> 24 & 0xff ] + '-' + \
           lut[ d2 & 0x3f | 0x80 ] + lut[ d2 >> 8 & 0xff ] + '-' + \
           lut[ d2 >> 16 & 0xff ] + lut[ d2 >> 24 & 0xff ] + \
           lut[ d3 & 0xff ] + lut[ d3 >> 8 & 0xff ] + lut[ d3 >> 16 & 0xff ] + lut[ d3 >> 24 & 0xff ]
    return uuid

#
# Main class
#
class SkelExporter(object):
    def __init__(self, mesh):
        self._meshName = mesh
        self._meshShape = pm.PyNode(mesh).getShape()
        
        self._joints = None

        skins = self._meshShape.listConnections(type="skinCluster")
        if skins:
            self._skin = skins[0]
            if self._skin:
                self._joints = self._skin.influenceObjects()
                self._jointNames = dict([(joint.name(), i) for i, joint in enumerate(self._joints)])

    def _hasRig(self):
        return self._joints != None

    def _indexOfJoint(self, name):    
        if name in self._jointNames:
            return self._jointNames[name]
        else:
            return -1
 
    def _exportMaterials(self, options = {}):
        self._engines = self._meshShape.listConnections(type="shadingEngine",s=True,d=False)
        self._materials = list()
        self._textures = list()
        self._images = list()
        for mtl in self._engines:
            shaders = pm.cmds.listConnections(mtl.name()+".surfaceShader")
            shader = pm.PyNode(shaders[0])
            map_uuid = None
            for f in shader.attr('color').inputs():
                src = f.ftn.get()
                import os
                fileName = os.path.basename(src)
                image_uuid = generateUUID()
                img = {
                    "url": fileName,
                    "uuid": image_uuid,
                    "name": f.name()
                }
                self._images.append(img)

                map_uuid = generateUUID()
                map = {
                    "repeat": [1,1],
                    "wrap": [1000,1000],
                    "image": image_uuid,
                    "name": "color_texture",
                    "uuid": map_uuid
                }
                self._textures.append(map)

            res = {
                "name": mtl.name(),
                "uuid": generateUUID()
            }

            if not options.has_key("emitrig") or options.get("emitrig"):
                res.update({ "skinning": True })

            if type(shader) is pm.nodetypes.Phong:
                res.update({"type": "MeshPhongMaterial" })
            else:
                res.update({"type": "MeshLambertMaterial" })

            if map_uuid:
                res.update({"map": map_uuid})

            self._materials.append(res)

    def _roundPos(self, pos):
        return map(lambda x: round(x, 6), [pos.x, pos.y, pos.z])

    def _roundQuat(self, rot):
        return map(lambda x: round(x, 6), [rot.x, rot.y, rot.z, rot.w])
   
    def _exportSkinWeights(self):
        self._skinWeights = list()
        self._skinIndices = list()
        for weights in self._skin.getWeights(self._meshShape.vtx):         
            numWeights = 0
            for i in range(0, len(weights)):
                if weights[i] > 0:
                    self._skinWeights.append(weights[i])
                    self._skinIndices.append(i)
                    numWeights += 1
            
            for i in range(0, 4 - numWeights):
                self._skinWeights.append(0)
                self._skinIndices.append(0)
            
    def _exportBones(self):
        self._bones = list()
        for joint in self._joints:
            if joint.getParent():
                parentIndex = self._indexOfJoint(joint.getParent().name())
            else:
                parentIndex = -1;
            
            rotq = joint.getRotation(quaternion=True) * joint.getOrientation()
            pos = joint.getTranslation()
            self._bones.append({"parent": parentIndex,
                                "pos": self._roundPos(pos),
                                "rotq": self._roundQuat(rotq),
                                "scl": [1,1,1],
                                "name": joint.name()})

    def _exportBoneAnim(self, options = {}):
        jointAnim = dict()
        firstFrame = int( pm.cmds.playbackOptions(minTime=True, query=True) )
        lastFrame = int( pm.cmds.playbackOptions(maxTime=True, query=True) )

        firstFrame = options.get("startFrame", firstFrame)
        lastFrame = options.get("endFrame", lastFrame)

        for fr in range(firstFrame, lastFrame+1):
            pm.cmds.currentTime(fr)
            for joint in self._joints:
                rotq = joint.getRotation(quaternion=True) * joint.getOrientation()
                pos = joint.getTranslation()
                if not jointAnim.has_key(joint.name()):
                    jointAnim.update({joint.name(): list()})

                jointAnim[joint.name()].append({"pos": self._roundPos(pos),
                                                "time": (fr - firstFrame)/24.0,
                                                "scl": [1,1,1],
                                                "rot": self._roundQuat(rotq)})
                
        self._boneAnim = list()
        boneAnimHier = list()
        for joint in self._joints:
            if joint.getParent():
                parentIndex = self._indexOfJoint(joint.getParent().name())
            else:
                parentIndex = -1;
                
            boneAnimHier.append({"parent": parentIndex,
                                   "keys": jointAnim.get(joint.name())})

        self._boneAnim.append({"hierarchy": boneAnimHier,
                               "length": (lastFrame - firstFrame + 1)/24.0,
                               "fps": 24.0,
                               "name": "lindy"})
    
    def _getMaterialIndex(self, face):
        if not hasattr(self, '_materialIndices'):
            self._materialIndices = dict([(mat.get('name'), i) for i, mat in enumerate(self._materials)])

        for engine in self._engines:
            if pm.sets(engine, isMember=face) or pm.sets(engine, isMember=self._meshShape):
                if self._materialIndices.has_key(engine.name()):
                    return self._materialIndices.get(engine.name())
        return -1

    def _exportSkin(self, options = {}):
        self._faces = list()
        mtlMask = (1 << 1)
        for face in self._meshShape.faces:
            faceMask = 0
            if self._meshShape.numNormals() > 0:
                faceMask |= (1 << 5)
            if face.hasUVs():
                faceMask |= (1 << 3)
            mtlIndex = self._getMaterialIndex(face)
            vertexCount = face.polygonVertexCount()
            if vertexCount == 4:
                self._faces.append(faceMask | (1 << 0) | mtlMask)
            else:
                self._faces.append(faceMask | mtlMask)
            self._faces += face.getVertices()
            self._faces.append(mtlIndex)
            if face.hasUVs():
                self._faces += map(lambda v: face.getUVIndex(v), range(face.polygonVertexCount()))
            if self._meshShape.numNormals() > 0:
                self._faces += [face.normalIndex(i) for i in range(face.polygonVertexCount())]

        self._vertices = [coord for point in self._meshShape.getPoints(space='world')
                                for coord in [round(point.x, 6), round(point.y, 6), round(point.z, 6)]]
        self._normals = [normal for triplet in self._meshShape.getNormals()
                                for normal in [round(triplet.x, 6), round(triplet.y, 6), round(triplet.z, 6)]]

        us, vs = self._meshShape.getUVs()
        self._uvs = list()
        for i, u in enumerate(us):
            self._uvs.append(u)
            self._uvs.append(vs[i])

    def _export(self, fileName = "/Users/mercier/out.json", options = {}):
        self._exportMaterials(options)

        pm.cmds.select(self._meshName)
        if self._hasRig() and options.get("emitrig"):
            mel.eval('gotoBindPose;')
        self._exportSkin(options)

        if self._hasRig() and options.get("emitrig"):
            self._exportSkinWeights()
            self._exportBones()
            self._exportBoneAnim(options)
        
        import json
        
        of = file(fileName, "w")
        
        metadata = { "faces": self._meshShape.numFaces(),
                     "vertices": self._meshShape.numVertices() }

        data = {"vertices": self._vertices,
                "uvs": [self._uvs],
                "normals": self._normals,
                "faces": self._faces,
                "metadata": metadata }

        if self._hasRig() and options.get("emitrig"):
            metadata.update({
                "bones": len(self._bones) })

            data.update({
                "bones": self._bones,
                "animations": self._boneAnim,
                "skinWeights": self._skinWeights,
                "skinIndices": self._skinIndices,
                "influencesPerVertex": 4,
                "metadata": metadata })

        material_uuid = generateUUID()
        geometry_uuid = generateUUID()

        geom = { "type": "Geometry",
                 "uuid": geometry_uuid,
                 "data": data }

        object = {"name": "link",
                  "uuid": "A04F2C03-47F5-369D-9DE6-06952C19507E",
                  "geometry": geometry_uuid,
                  "matrix":[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],
                  "material": [mtl.get("uuid") for mtl in self._materials],
                  "type":"Mesh"}

        scene = { "type": "Scene",
                  "matrix":[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],
                  "uuid":"8356ADC1-49AB-4717-96F1-73DFFE8B4236",
                  "children": [ object ] }

        meta = {"sourceFile": "abc.mb",
                "generator": "maya2three",
                "type": "Object",
                "version": 4.4}

        script = {"geometries": [ geom ],
                  "materials": self._materials,
                  "images": self._images,
                  "textures": self._textures,
                  "metadata": meta,
                  "object": scene }
  
        json.dump(script, of, indent=3)
        
        of.close()

class THREEexportDialog(object):
    def __init__(self):
        self._top = 'threewin'
        self._setupUi()

    def _setupUi(self):

        items = pm.cmds.ls(sl=True)
        if len(items) == 1:
            node = pm.PyNode(items[0])
            if node.type() == 'transform':
                node = node.getShape()
            if node.type() != 'mesh':
                mc.confirmDialog(title='Confirm', message='You must select a polygon mesh',
                    button="Ok", cancelButton="Ok", dismissString="Ok")
                return
        else:
            mc.confirmDialog(title='Confirm', message='You must select a polygon mesh',
                button="Ok", cancelButton="Ok", dismissString="Ok")
            return

        if mc.window(self._top, ex=True):
            mc.deleteUI(self._top)

        win = mc.window(self._top, title='Export THREEJS', w=200, rtf=True, sizeable=False)
        mc.columnLayout(adj=1, rs=5)
        mc.separator()
        mc.text("Options")
        mc.separator()
        mc.rowColumnLayout(numberOfColumns=2)
        firstFrame = int( pm.cmds.playbackOptions(minTime=True, query=True) )
        lastFrame = int( pm.cmds.playbackOptions(maxTime=True, query=True) )
        mc.text("Start frame")
        self._startFrame = mc.intField(minValue=firstFrame, maxValue=lastFrame, value=firstFrame)
        mc.text("End frame")

        self._endFrame = mc.intField(minValue=firstFrame, maxValue=lastFrame, value=lastFrame)
        self._emitRig = mc.checkBox(label="Emit Rig", value=True);

        mc.setParent("..")
        mc.separator()
        mc.button("Export..", c=self._on_do_export)

        mc.showWindow(self._top)

    def _on_do_export(self, e):
        dialog = mc.fileDialog2(fileFilter="JSON Files (*.json)", dialogStyle=0)
        if dialog:
            fileName = dialog[0];
            a = SkelExporter("Link:Mesh")
            firstFrame = mc.intField(self._startFrame, q=True, v=True)
            lastFrame = mc.intField(self._endFrame, q=True, v=True)
            options = {
                "emitrig": mc.checkBox(self._emitRig, q=True, v=True),
                "startFrame": firstFrame,
                "endFrame": lastFrame
            }
            a._export(fileName, options)
            mc.deleteUI(self._top)

if __name__ == "__main__":
    dialog = THREEexportDialog()
