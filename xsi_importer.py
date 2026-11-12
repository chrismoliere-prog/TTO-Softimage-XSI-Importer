# TO DO:
# Add basepose to armature - SOLVED
# clear hooks
# Determine how to solve leg twists - SOLVED



import math
from math import radians
import os
from random import random
from typing import Any

import mathutils
from mathutils import Matrix, Euler, Vector


import bpy
from . import xsi_parser
from bpy_extras import anim_utils
from ast import literal_eval

boneTypes = ['Null', 'IK_Effector', 'IK_Root', 'IK_Joint']
fileName = ''



class Import:
    def __init__(self, context, filepath, animChoice):
        global xsiFile
        global fileName
        self.filepath = filepath
        fileName = bpy.path.display_name_from_filepath(filepath)
        self.animChoice = animChoice
        armName = ""
        boneList = {}
        xsiFile = self.read(self.filepath)
        mainCollection = bpy.data.collections.get('Collection')
        collectionA = bpy.data.collections.new('Basepose Empties')
        mainCollection.children.link(collectionA)
        collectionB = bpy.data.collections.new('Transforms Empties')
        mainCollection.children.link(collectionB)
        collectionC = bpy.data.collections.new('IK Empties')
        mainCollection.children.link(collectionC)
        collectionD = bpy.data.collections.new(fileName)
        mainCollection.children.link(collectionD)
        for key, value in xsiFile.items():
            parent = None
            print('Finding type of', key)
            if value.modelType == 'Mesh':
                print("Creating mesh", key)
                self.createMesh(key, value, armName, collectionD)
                print("Created mesh", key)
            elif not value.modelType and not value.hasParent:
                print("Creating Armature", key)
                obj = self.createArmature(key, value, collectionD)
                print("Created Armature", key)
                armName = key
                boneList[key] = value
            elif value.modelType in boneTypes or value.modelType == '':
                boneList[key] = value
                if value.hasParent:
                    parent = xsiFile[value.parentName]
                print("Creating Bone", key)
                self.generateBones(key, value, armName, collectionA, collectionC)
                print("Created bone", key)
        self.setHooks(armName)
        self.clearParents()
        self.createArm(armName)
        self.transformEmpties(xsiFile, collectionB)
        self.clearIKCons(xsiFile, boneList, armName)
        self.copyTrans(xsiFile, boneList, armName)
        self.fixIKPoles(xsiFile)
        self.setIK(boneList, armName)
        self.setBoneConstraints(boneList, armName)
        self.addIKTracking(boneList, armName)
        self.copyMeshTrans(xsiFile)
        self.setMeshParenting()
        self.removeTrans(xsiFile, armName)
        self.grouplessMesh(xsiFile, armName)
        self.clearAllHooks()
        for obj in collectionA.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collectionA)
        for obj in collectionB.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collectionB)
        for obj in collectionC.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collectionC)
        self.hookBones(xsiFile, armName)
        self.setArmBasePose(armName, xsiFile)
        self.clearIKTracks(armName, xsiFile)
        self.meshToArm(armName)
        bpy.ops.object.select_all(action='DESELECT')
        self.yToZ(armName)
        self.removeInheritRot(armName, xsiFile)

        self.buildAnims(armName, xsiFile)

    def buildAnims(self, armName, xsiFile):
        index = 0
        subtracted = 0.0
        armature = bpy.data.objects.get(armName)
        armature.select_set(True)
        action = bpy.data.actions.new(name=fileName)
        slot = action.slots.new(armature.id_type, armature.name)
        layer = action.layers.new("Base")
        strip = layer.strips.new(type='KEYFRAME')
        channelbag = strip.channelbag(slot, ensure=True)

        for key, value in xsiFile.items():
            counter = 0
            if value.animationFCurves:
                for name, frames in value.animationFCurves.items():
                    if name == 'SCALING-X':
                        subtracted = value.transforms[0]
                        index = 0
                        datapath = f'pose.bones["{key}"].scale'
                    if name == 'SCALING-Y':
                        subtracted = value.transforms[1]
                        index = 1
                        datapath = f'pose.bones["{key}"].scale'
                    if name == 'SCALING-Z':
                        subtracted = value.transforms[2]
                        index = 2
                        datapath = f'pose.bones["{key}"].scale'
                    if name == 'ROTATION-X':
                        subtracted = value.transforms[3]
                        index = 0
                        datapath = f'pose.bones["{key}"].rotation_euler'
                    if name == 'ROTATION-Y':
                        subtracted = value.transforms[4]
                        index = 1
                        datapath = f'pose.bones["{key}"].rotation_euler'
                    if name == 'ROTATION-Z':
                        subtracted = value.transforms[5]
                        index = 2
                        datapath = f'pose.bones["{key}"].rotation_euler'
                    if name == 'TRANSLATION-X':
                        subtracted = value.transforms[6]
                        index = 0
                        datapath = f'pose.bones["{key}"].location'
                    if name == 'TRANSLATION-Y':
                        subtracted = value.transforms[7]
                        index = 1
                        datapath = f'pose.bones["{key}"].location'
                    if name == 'TRANSLATION-Z':
                        subtracted = value.transforms[8]
                        index = 2
                        datapath = f'pose.bones["{key}"].location'
                    fcu_z = channelbag.fcurves.find(data_path=datapath, index=index)
                    if not fcu_z:
                        fcu_z = channelbag.fcurves.new(data_path=datapath, index=index)
                    fcu_z.keyframe_points.add(len(frames))
                    for i, frameList in enumerate(frames):
                        print(i)
                        keyFrame = fcu_z.keyframe_points[i]
                        if datapath == f'pose.bones["{key}"].scale':
                            keyFrame.co = (frameList[0], frameList[1]/subtracted)
                            print(name)
                            print('scale default:' + str(frameList[1]) + '\n' + 'scale first frame:' + str(subtracted))
                            print ('output value: ' + str(frameList[1]/subtracted))
                        if datapath == f'pose.bones["{key}"].rotation_euler':
                            keyFrame.co = (frameList[0], math.radians(frameList[1]-subtracted))
                            print(name)
                            print('rotation default:' + str(frameList[1]) + '\n' + 'rotation first frame:' + str(subtracted))
                        if datapath == f'pose.bones["{key}"].location':
                            keyFrame.co = (frameList[0], (frameList[1] - subtracted))
                    fcu_z.update()
                    bpy.context.view_layer.update()
                adt = armature.animation_data_create()
                adt.action = action
                adt.action_slot = slot

    def removeInheritRot(self, armName, xsiFile):
        armature = bpy.data.objects.get(armName)
        bpy.ops.object.mode_set(mode='POSE')
        for key, value in xsiFile.items():
            if value.modelType == 'IK_Joint':
                parent = xsiFile[value.parentName]
                if parent.modelType == 'IK_Root':
                    bone = armature.pose.bones.get(key)
                    bone.bone.use_inherit_rotation = False
        bpy.ops.object.mode_set(mode='OBJECT')

    def clearIKTracks(self, armName, xsiFile):
        armature = bpy.data.objects.get(armName)
        for bone in armature.pose.bones:
            targets = [c for c in bone.constraints if c.name == 'LOCKEDTRACK']
            for constraint in targets:
                bone.constraints.remove(constraint)
        bpy.ops.pose.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

    def meshToArm(self, armName):
        bpy.ops.object.select_all(action='DESELECT')
        armature = bpy.data.objects.get(armName)
        scene_meshes = [obj for obj in bpy.context.view_layer.objects if obj.type == 'MESH']
        for obj in scene_meshes:
            if len(obj.vertex_groups) != 0:
                obj.select_set(True)
                armature.select_set(True)
                bpy.context.view_layer.objects.active = armature
                bpy.ops.object.parent_set(type='ARMATURE')



    def setArmBasePose(self, armName, xsiFile):
        bpy.ops.object.select_all(action='DESELECT')
        armature = bpy.data.objects.get(armName)
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        # bpy.ops.pose.select_all(action='DESELECT')
        bpy.ops.pose.armature_apply(selected=False)

    def clearAllHooks(self):
        scene_meshes = [obj for obj in bpy.context.view_layer.objects if obj.type == 'MESH']
        if scene_meshes:
            # Select every mesh
            for obj in scene_meshes:
                obj.select_set(True)
                if obj.parent:
                    world_matrix_copy = obj.matrix_world.copy()
                    obj.parent = None
                    obj.matrix_world = world_matrix_copy

        # Set the active object flag required by the operator
            bpy.context.view_layer.objects.active = scene_meshes[0]

            bpy.ops.object.convert(target='MESH')

    def hookBones(self, xsiList, armName):
        armature = bpy.data.objects.get(armName)
        for key, value in xsiList.items():
            empty = bpy.data.objects.get(key)
            if bpy.data.objects.get(key) and empty.type != 'MESH':
                self.buildConstraint(empty, armature, 'COPY_TRANSFORMS', 'COPYTRANS')
                con = empty.constraints.get('COPYTRANS')
                con.subtarget = key

    def setIK(self, boneList, armName):
        armature = bpy.data.objects.get(armName)
        for key, value in boneList.items():
            if value.modelType == 'IK_Root':
                bone = armature.pose.bones.get(value.boneList[-2])
                pole = xsiFile[value.boneList[1]]
                chainLength = int(value.boneList[0])
                self.buildConstraint(bone, armature, 'IK', 'IK_CHAIN')
                con = bone.constraints.get('IK_CHAIN')
                con.subtarget = value.boneList[-1]
                con.chain_count = chainLength
                chainBone = armature.pose.bones.get(value.boneList[1])
                # if chainBone.rotation_euler.z >= 0:
                #     con.pole_angle = math.radians(180)
                if pole.constraints:
                    poleCons = pole.constraints
                    poleBone =list(poleCons)[0]
                    poleTarget = poleCons[poleBone][2]
                    con.pole_target = armature
                    con.pole_subtarget = poleTarget
                    self.buildConstraint(bone, armature, 'LOCKED_TRACK', 'LOCKEDTRACK')
                    lockCon = bone.constraints.get('LOCKEDTRACK')
                    lockCon.subtarget = poleTarget
                    lockCon.track_axis = 'TRACK_X'
                    lockCon.lock_axis = 'LOCK_Z'
                # with bpy.context.temp_override(active_pose_bone=bone, active_object=armature):
                #     bpy.ops.constraint.apply(
                #         constraint=lockCon.name,
                #         owner='BONE')

    def addIKTracking(self, boneList, armName):
        armature = bpy.data.objects.get(armName)
        for key, value in boneList.items():
            if value.modelType == 'IK_Root':
                if armature.pose.bones.get(value.boneList[-1]):
                    trackBone = armature.pose.bones.get(value.boneList[-1])
                    self.buildConstraint(trackBone, armature, 'TRACK_TO', 'LOCKED_TRACK')
                    trackCon = trackBone.constraints.get('LOCKED_TRACK')
                    trackCon.subtarget = value.boneList[-2]
                    trackCon.track_axis = 'TRACK_Y'
                    trackCon.up_axis = 'UP_Z'
                    trackCon.use_target_z = True

    def clearIKCons(self, xsiFile, boneList, armName):
        armature = bpy.data.objects.get(armName)
        for key, value in boneList.items():
            if value.modelType == 'IK_Joint':
                bpy.ops.object.mode_set(mode='POSE')
                bone = armature.pose.bones.get(key)
                if not armature.pose.bones.get(key):
                    print('Could not find bone ' + key)
                    item = key[:63]
                    print('Searching for ' + item)
                    bone = armature.pose.bones.get(item)
                con = bone.constraints.get("IKCOPY")
                with bpy.context.temp_override(active_pose_bone=bone, active_object=armature):
                    bpy.ops.constraint.apply(
                        constraint=con.name,
                        owner='BONE')
            else:
                bpy.ops.object.mode_set(mode='POSE')
                bone = armature.pose.bones.get(key)
                if not armature.pose.bones.get(key):
                    print('Could not find bone ' + key)
                    item = key[:63]
                    print('Searching for ' + item)
                    bone = armature.pose.bones.get(item)
                con = bone.constraints.get("TRANSFORMCOPY")
                with bpy.context.temp_override(active_pose_bone=bone, active_object=armature):
                    bpy.ops.constraint.apply(
                        constraint=con.name,
                        owner='BONE')

    def removeTrans(self, xsiFile, armName):
        armature = bpy.data.objects.get(armName)
        for key, value in xsiFile.items():
            if armature.pose.bones.get(key):
                bone = armature.pose.bones.get(key)
                for constraint in bone.constraints:
                    if constraint.name in ('TRANSFORMATIONS', 'TRANSFORMCOPY'):
                        with bpy.context.temp_override(active_pose_bone=bone, active_object=armature):
                            bpy.ops.constraint.apply(
                                constraint=constraint.name,
                                owner='BONE')

    def copyMeshTrans(self, xsiFile):
        for key, value in xsiFile.items():
            bpy.ops.object.mode_set(mode='OBJECT')
            if bpy.data.objects.get(key):
                empty = bpy.data.objects.get(key)
                if len(empty.vertex_groups) == 0 and empty.type != 'MESH':
                    target = bpy.data.objects.get(key + '_TRANSFORM')
                    self.buildConstraint(empty, target, 'COPY_TRANSFORMS', 'EMPTY_TRANSFORMS')
                    con = empty.constraints.get('EMPTY_TRANSFORMS')
                    bpy.ops.constraint.apply(constraint=con.name, owner='OBJECT')

    def grouplessMesh(self, xsiFile, armName):
        armature = bpy.data.objects.get(armName)
        for key, value in xsiFile.items():
            bpy.ops.object.mode_set(mode='OBJECT')
            empty = bpy.data.objects.get(key)
            if bpy.data.objects.get(key) and len(empty.vertex_groups) == 0 and empty.type == 'MESH':
                print ('found!!!!')
                self.buildConstraint(empty, armature, 'COPY_TRANSFORMS', 'MESH_TRANSFORMS')
                con = empty.constraints.get('MESH_TRANSFORMS')
                con.subtarget = key

    def copyTrans(self, xsiFile, boneList, armName):
        armature = bpy.data.objects.get(armName)
        isGood = False
        for key, value in boneList.items():
            isGood = True
            if value.modelType == 'IK_Joint':
                parent = xsiFile[value.parentName]
                if parent.modelType == 'IK_Joint':
                    parent = xsiFile[parent.parentName]
                if parent.modelType == 'IK_Root':
                    if int(parent.boneList[0]) < 2:
                        isGood = True
                    else:
                        isGood = False
            if isGood:
                bpy.ops.object.mode_set(mode='POSE')
                bone = armature.pose.bones.get(key)
                if not armature.pose.bones.get(key):
                    print('Could not find bone ' + key)
                    item = key[:63]
                    print('Searching for ' + item)
                    bone = armature.pose.bones.get(item)
                if value.modelType == 'IK_Joint':
                    target = bpy.data.objects.get(key + '_IKTRANSFORM')
                else:
                    target = bpy.data.objects.get(key + '_TRANSFORM')
                self.buildConstraint(bone, target, 'COPY_TRANSFORMS', 'TRANSFORMATIONS')
            else:
                if value.modelType == 'IK_Joint':
                    bone = armature.pose.bones.get(key)
                    if not armature.pose.bones.get(key):
                        print('Could not find bone ' + key)
                        item = key[:63]
                        print('Searching for ' + item)
                        bone = armature.pose.bones.get(item)
                    target = bpy.data.objects.get(key + '_IKTRANSFORM')
                    trans = value.transforms
                    bone.location = (trans[6], trans[7], trans[8])
                    bone.scale = target.scale

    def fixIKPoles(self, xsiFile):
        for key, value in xsiFile.items():
            if value.hasParent:
                parent = xsiFile[value.parentName]
                if parent.modelType == 'IK_Root':
                    pole = xsiFile[parent.boneList[1]]
                    if pole.constraints:
                        poleCons = pole.constraints
                        poleBone = list(poleCons)[0]
                        if bpy.data.objects.get(poleCons[poleBone][2] + '_TRANSFORM'):
                            empty = bpy.data.objects.get(key + '_TRANSFORM')
                            poleTarget = bpy.data.objects.get(poleCons[poleBone][2] + '_TRANSFORM')
                            print('aaaa + ' + poleCons[poleBone][2])
                            self.buildConstraint(empty, poleTarget, 'LOCKED_TRACK', 'LOCKEDTRACK')
                            lockCon = empty.constraints.get('LOCKEDTRACK')
                            lockCon.track_axis = 'TRACK_Y'
                            lockCon.lock_axis = 'LOCK_X'

                            if abs(int(value.transforms[3])) == 180 or int(value.transforms[5]) > 300:
                                lockCon.track_axis = 'TRACK_NEGATIVE_Y'
    def clearParents(self):
        bpy.ops.object.select_all(action='DESELECT')
        nulls_with_parent = [
            empty for empty in bpy.context.scene.objects
            if empty.type == 'EMPTY' and empty.parent is not None
        ]
        for empty in nulls_with_parent:
            empty.select_set(True)
        if nulls_with_parent:
            bpy.context.view_layer.objects.active = nulls_with_parent[0]
            # Clear parent and keep world transformation
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    def yToZ (self, armName):
        bpy.ops.object.mode_set(mode='OBJECT')
        armature = bpy.data.objects.get(armName)
        rot_matrix = Matrix.Rotation(math.radians(90), 4, 'X')
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                obj.matrix_world = rot_matrix @ obj.matrix_world
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    def createArm(self, armName):
        global xsiFile
        bpy.ops.object.select_all(action='DESELECT')
        armature = bpy.data.objects.get(armName)
        bpy.context.view_layer.objects.active = armature
        for key, value in xsiFile.items():
            if value.basepose:
                trans = value.basepose
            else:
                trans = value.transforms
            orientations = [trans[6], trans[7], trans[8]]
            rotations = [math.radians(trans[3]), math.radians(trans[4]), math.radians(trans[5])]
            scales = [trans[0], trans[1], trans[2]]
            bpy.ops.object.mode_set(mode='EDIT')
            empty = armature.data.edit_bones.new(key)
            print ('Created Bone ' + key)
            empty.head = (0,0,0)
            if value.modelType != 'IK_Joint':
                empty.tail = (0,1,0)
            else:
                if value.modelType == 'IK_Joint':
                    empty.tail = (1,0,0)
                    length = value.boneList[0]
                    empty.length = value.boneList[0]
            if (value.hasParent or (value.modelType == 'IK_Joint')) and value.modelType != 'IK_Effector':
                if armature.data.edit_bones.get(value.parentName):
                    parent = armature.data.edit_bones.get(value.parentName)
                    empty.parent = parent
                if xsiFile[value.parentName].modelType == 'IK_Joint' and value.modelType == 'IK_Joint':
                    empty.use_connect = True
                    empty.length = value.boneList[0]
            bpy.context.view_layer.update()
            bpy.ops.object.mode_set(mode='POSE')
            bone = armature.pose.bones.get(key)
            if not armature.pose.bones.get(key):
                print('Could not find bone ' + key)
                item = key[:63]
                print('Searching for ' + item)
                bone = armature.pose.bones.get(item)
            bone.location = orientations
            bone.scale = scales
            if value.modelType == 'IK_Joint':
                target = bpy.data.objects.get(key + '_IK')
                self.buildConstraint(bone, target, 'COPY_TRANSFORMS', 'IKCOPY')
                bone.bone.inherit_scale = 'ALIGNED'
            else:
                target = bpy.data.objects.get(key)
                self.buildConstraint(bone, target, 'COPY_TRANSFORMS', 'TRANSFORMCOPY')
                bone.bone.inherit_scale = 'ALIGNED'
            bone.rotation_mode = 'XYZ'

            # if value.modelType == 'IK_Effector':
            #     self.buildConstraint(bone, armature, 'CHILD_OF', 'EFFECTOR')
            #     con = bone.constraints.get('EFFECTOR')
            #     con.subtarget = value.parentName
            bone.rotation_euler = rotations

    def generateBones(self, key, value, armName, collection, collectionB):
        global xsiFile
        armature = bpy.data.objects.get(armName)
        if value.hasParent:
            parentType = xsiFile[value.parentName]
        if value.basepose:
            trans = value.basepose
            orientations = [trans[6], trans[7], trans[8]]
            rotations = [math.radians(trans[3]), math.radians(trans[4]), math.radians(trans[5])]
            scales = [trans[0], trans[1], trans[2]]

        else:
            trans = value.transforms
            orientations = [trans[6], trans[7], trans[8]]
            rotations = [math.radians(trans[3]), math.radians(trans[4]), math.radians(trans[5])]
            scales = [trans[0], trans[1], trans[2]]

        # else:
        new_bone = bpy.data.objects.new(key, None)
        collection.objects.link(new_bone)
        if value.modelType == 'IK_Joint':
            IK_bone = bpy.data.objects.new(key + '_IK', None)
            collectionB.objects.link(IK_bone)
            IK_bone.rotation_mode = 'XYZ'
            IK_bone.rotation_euler = (0,0,math.radians(-90))
            IK_bone.parent = new_bone



        if value.hasParent and not value.basepose:
            parent = value.parentName
            parentBone = bpy.data.objects.get(parent)
            bone_matrix = new_bone.matrix_world.copy()
            new_bone.parent = parentBone
            new_bone.matrix_parent_inverse = mathutils.Matrix.Identity(4)
            new_bone.matrix_local = parentBone.matrix_world.inverted() @ bone_matrix

        pBone = new_bone
        pBone.rotation_mode = 'XYZ'
        pBone.location = orientations
        pBone.scale = scales
        pBone.rotation_euler = rotations
        bpy.context.view_layer.update()

    def setHooks(self, armName):
        global xsiFile
        armature = bpy.data.objects.get(armName)
        for obj in bpy.data.objects:
            for vg in obj.vertex_groups:
                hook = obj.modifiers.new(name = ('Hook'+ '_' + vg.name), type = 'HOOK')
                hook.object = bpy.data.objects.get(vg.name)
                # if xsiFile[vg.name].modelType == 'IK_Joint':
                #     hook.object = armature
                #     hook.subtarget = vg.name
                hook.vertex_group = vg.name
                
    def transformEmpties(self, xsiFile, collection):
        for key, value in xsiFile.items():
            if value.hasParent:
                parent = xsiFile[value.parentName]
            trans = value.transforms
            orientations = [trans[6], trans[7], trans[8]]
            rotations = [math.radians(trans[3]), math.radians(trans[4]), math.radians(trans[5])]
            scales = [trans[0], trans[1], trans[2]]
            empty = bpy.data.objects.new(key + '_TRANSFORM', None)
            collection.objects.link(empty)
            if value.hasParent and bpy.data.objects.get(value.parentName):
                parentObj = bpy.data.objects.get(value.parentName + "_TRANSFORM")
                empty.parent = parentObj
            if value.modelType == 'IK_Joint':
                IK_bone = bpy.data.objects.new(key + '_IKTRANSFORM', None)
                collection.objects.link(IK_bone)
                IK_bone.rotation_mode = 'XYZ'
                IK_bone.rotation_euler = (0, 0, math.radians(-90))
                IK_bone.parent = empty

            pBone = empty
            pBone.rotation_mode = 'XYZ'
            pBone.location = orientations
            pBone.scale = scales
            pBone.rotation_euler = rotations
            if value.modelType == 'IK_Joint' and (int(value.transforms[4]) <= -179 or int(value.transforms[4]) >= 179):
                pBone.rotation_euler.x += math.radians(180)
            bpy.context.view_layer.update()

    def setConBonePoses(self, xsiFile, armName):
        armature = bpy.data.objects.get(armName)
        for key, value in xsiFile.items():
            if value.basepose != []:
                # if value.modelType == 'IK_Joint':
                #     bpy.ops.object.mode_set(mode='EDIT')
                #     empty = armature.data.edit_bones.get(key)
                # else:
                empty = bpy.data.objects.get(key)
                trans = value.transforms
                # if value.modelType == 'IK_Joint':
                #     orientations = [trans[7] * -1, trans[6], trans[8]]
                #     rotations = [math.radians(trans[4] * -1), math.radians(trans[3]), math.radians(trans[5])]
                #     scales = [trans[1], trans[0], trans[2]]
                orientations = [trans[6], trans[7], trans[8]]
                rotations = [math.radians(trans[3]), math.radians(trans[4]), math.radians(trans[5])]
                scales = [trans[0], trans[2], trans[1]]
                if value.hasParent:
                    parentObj = xsiFile[value.parentName]
                    # if value.modelType is in ('IK_Effector'. )
                    # # else:
                    parent = bpy.data.objects.get(value.parentName)
                        # if value.modelType == 'IK_Joint':
                        #     bpy.ops.object.mode_set(mode='POSE')
                        #     bone = armature.pose.bones.get(key)
                        #     self.buildConstraint(bone, parent, 'CHILD_OF', 'Child of Empty')
                        #     con = bone.constraints.get('Child of Empty')
                        #     con.inverse_matrix = Matrix.Identity(4)
                        # else:
                    empty.parent = parent
                # if value.modelType == 'IK_Joint':
                #     bpy.ops.object.mode_set(mode='POSE')
                #     bone = armature.pose.bones.get(key)
                #     bone.location = orientations
                #     bone.scale = scales
                #     bone.rotation_euler = rotations
                # else:
                    empty.location = orientations
                    empty.scale = scales
                    empty.rotation_euler = rotations
            # bpy.ops.object.mode_set(mode='OBJECT')

    def setBoneConstraints (self, boneList, armName):
        global xsiFile
        armature = bpy.data.objects.get(armName)
        isEffector = ''
        for key, value in xsiFile.items():
            const = xsiFile[key].constraints
            print ('making constraints for ' + key)
            for item, constraint in const.items():
                object = armature.pose.bones.get(constraint[0])
                if armature.pose.bones.get(constraint[0]):
                    print ('Found' + constraint[0])
                else:
                    print('Could not find bone ' + constraint[0])
                    item = key[:63]
                    print('Searching for ' + item)
                    bone = armature.pose.bones.get(item)
                target = armature
                print(constraint[1])
                self.buildConstraint(object, target, constraint[1], item)
                con = object.constraints.get(item)
                con.subtarget = constraint[2]

    def buildConstraint(self, object, target, conType, conName):
        if conType == 'UP_VECTOR':
            conType = 'LOCKED_TRACK'
        if conType == 'SCALING':
            conType = 'COPY_SCALE'
        if conType == 'ORIENTATION':
            conType = 'COPY_ROTATION'
        if conType == 'POSITION':
            conType = 'COPY_LOCATION'
        constraint = object.constraints.new(type = conType)
        constraint.target = target
        constraint.name = conName

    def setMeshParenting(self):
        global xsiFile
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                target = xsiFile[obj.name]
                trans = target.transforms
                if target.hasParent:
                    parent = bpy.data.objects.get(target.parentName + '_TRANSFORM')
                    if bpy.data.objects.get(target.parentName + '_TRANSFORM'):
                        print('Found object ' + obj.name)
                    obj.parent = parent
                    obj.location = (trans[6], trans[7], trans[8])
                    obj.rotation_euler = (math.radians(trans[3]), math.radians(trans[4]), math.radians(trans[5]))
                    obj.scale = (trans[0], trans[1], trans[2])
                    


    def makeParents(self, key, value):
        parentObj = bpy.data.objects[value.parentName]
        child = bpy.data.objects[key]
        parent = parentObj
        child.parent = parent

    def createArmature(self, armatureName, armatureData, collection):
        armatureInfo = bpy.data.armatures.new(name=armatureName)
        armature = self.makeObject(armatureName, armatureInfo)
        collection.objects.link(armature)
        return armature

    def createMesh(self, modelName, obProp, armature, collection):
        arm = bpy.data.objects.get(armature)
        armatureData = arm.data
        new_mesh = bpy.data.meshes.new(name=modelName + "_OBJ")
        vertexCords = obProp.vertices['POSITION']
        new_mesh.from_pydata(vertexCords, [], obProp.polygons)
        new_mesh.update()
        if 'TEX_COORD_UV0' in obProp.vertices:
            vertList = obProp.vertices['TEX_COORD_UV0']
            uv_layer = new_mesh.uv_layers.new(name=modelName + "_UV")
            new_mesh.uv_layers.active = uv_layer
            uv_index = 0
            for polygon in new_mesh.polygons:
                for vertex in polygon.loop_indices:
                    uv_layer.data[vertex].uv = vertList[uv_index]
                    uv_index += 1
        if obProp.clusterWeights:
            newObject = self.makeObject(modelName, new_mesh)
        else:
            newObject = self.makeObject(modelName, new_mesh)
        if obProp.basepose:
            newObject = self.setTransformations(newObject, obProp.basepose)
        else:
            newObject = self.setTransformations(newObject, obProp.transforms)
        newObject = self.makeVertexGroups(newObject, obProp.clusterWeights)
        collection.objects.link(newObject)
        bpy.context.view_layer.update()



    def setTransformations(self, obj, transformations):
        locations = transformations[-3:]
        obj.location = (locations[0], (locations[1]), locations[2])
        rotations = transformations[3:6]
        obj.rotation_euler = (math.radians(rotations[0]), math.radians(rotations[1]), math.radians(rotations[2]))
        obj.scale = (transformations[0], transformations[1], transformations[2])
        return obj

    def makeVertexGroups(self, obj, clusterDict):
        for (group, values) in clusterDict.items():
            v_group = obj.vertex_groups.new(name=group)
            valuesList = values
            for index, weight in valuesList:
                v_group.add([int(index)], (weight / 100), 'REPLACE')
        return obj

    def makeObject(self, fileName, fileData):
        newObject = bpy.data.objects.new(name=fileName, object_data=fileData)
        return newObject

    def read(self, filepath):
        return xsi_parser.importXSI(filepath)



def load(context, filepath="", animProp=False):
    Import(context, filepath, animProp)
    print("IMPORTED")
    return {"FINISHED"}