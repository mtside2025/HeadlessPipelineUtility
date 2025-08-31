# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
import csv
import json
import numpy as np
import math
from mathutils import Matrix, Vector, Quaternion, Euler

import sys
sys.path.append("../Common/Motion")
import motion_io
import motion_util


#
# obtain joint-positions at the rest-pose (i.e. T-pose)
# as dic_data{keys = joint_names, values = numpy(1, 3)}
#
def getJointDataAtRestPose(
    armature,
    joint_names,
    rotation = True
    ):
    
    # change to edit-mode to get rest-pose
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    
    # obtain head-position of each-bone
    dic_data = {}
    
    # get each global-joint-position
    for bone_name in joint_names:
        bone = armature.data.edit_bones.get(bone_name)
        if bone is None:
            print(f"Warning: Bone '{bone_name}' not found.")
            continue
        head_world = armature.matrix_world @ bone.head
        dic_data[bone_name] = np.array([head_world.x, head_world.y, head_world.z]).reshape(1, 3)
    
    
    bpy.ops.object.mode_set(mode='POSE')
    
    # change positions to rotations
    if rotation:
        
        kinetic_chain = motion_util.getBodyChain(len(joint_names))
        
        dic_data = motion_util.pos2grot(
            dic_data,
            kinetic_chain,
            joint_names
        )
    
    return dic_data
    



#
# set load motion and rigged armature from FBXs, and attach motion to armature as pose-sequence animation
#
def setMotion2Armature(
    input_armature_fbx_path,
    input_motion_path,
    output_armature_fbx_path,
    armature_joint_names,
    motion_joint_names,
    retarget_table_path = None,
    armature_name = "Armature",
    rename_bones_to_search = True,
    verbose = True
    ):
    
    # create temporary scene for the load
    temp_scene = bpy.data.scenes.new("TempScene")
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = temp_scene
    
    try:
        # load FBX of rigged-mesh
        bpy.ops.import_scene.fbx(filepath=input_armature_fbx_path)
        armature = bpy.data.objects[armature_name]
        if armature is None:
            print(f"No-armature named {armature_name} does not exist in {input_armature_fbx_path}. The scene includes:")
            for obj in  bpy.data.objects:
                print(obj.name)
            raise AttributeError()
        
        # print bone-info (if needed)
        if rename_bones_to_search:
            keywords = ["mixamorig:"]
            for keyword in keywords:
                for bone in armature.data.bones:
                    if keyword in bone.name:
                        original_bone_name = bone.name
                        bone.name = bone.name[len(keyword):]
                        print(f"Bone \"{original_bone_name}\" is replaced to \"{bone.name}\" to search.")
            
        elif verbose:
            print("Bone names:")
            for bone in armature.data.bones:
                print(f"- {bone.name}")
            print(f"Totally {len(armature.data.bones)} bones exist.\n")
        
        
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
        
        
        # reset animation
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            #for fcurve in action.fcurves:
            #    action.fcurves.remove(fcurve)
            bpy.data.actions.remove(action)
        
        # get joint-positions of rest-pose
        dic_joint_rotations_rest_pose = getJointDataAtRestPose(armature, armature_joint_names)
        
        
        # load motion-file (.npz)
        motion_data = motion_io.loadMotion(
            input_motion_path,
            joint_names = motion_joint_names,
            joint_rotation_offsets = dic_joint_rotations_rest_pose
            )
        
        if verbose:
            for key in motion_data:
                print(key)
        
        
        # load retarget-table
        with open(retarget_table_path) as f:
            rt_tbl = json.load(f)
        
        
        
        for i, pose_bone in enumerate(armature.pose.bones):
            pose_bone.rotation_mode = 'XYZ'
            pose_bone.rotation_euler = Euler([0, 0, 0], 'XYZ')
        
        
        # set motion to armature
        for i, (target, source) in enumerate(rt_tbl.items()):
            
            # root
            if i == 0:
                continue # location is to be implemented
            
            print(f"[{i+1}/{len(rt_tbl.items())}] {source} to {target}", flush=True)
            
            pose_bone = armature.pose.bones.get(target) # for pose-mode
            if not pose_bone:
                print(f"Bone \"{target}\" does not exist in {input_armature_fbx_path}.(skipped)")
                continue
            
            if source not in motion_data:
                print(f"Bone \"{source}\" does not exist in {input_motion_path}.(skipped)")
                continue
            
            motion = motion_data[source]
            num_frames = motion.shape[0]
            
            for frame_idx in range(num_frames):
                
                bpy.context.scene.frame_set(frame_idx + 1)
                
                euler_angles = motion[frame_idx]  # [x, y, z] in radians
                pose_bone.rotation_euler = Euler(euler_angles, 'XYZ')
                pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame_idx + 1)
                
            
        print()
        
        
        # save as FBX
        bpy.ops.export_scene.fbx(
            filepath=output_armature_fbx_path,
            use_selection=True,                        # export selected object only
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            bake_space_transform=True,
            object_types={'ARMATURE', 'MESH'},
            bake_anim=True,                            # includes animation
            bake_anim_use_all_bones=True,
            bake_anim_use_nla_strips=False,
            bake_anim_use_all_actions=False,
            bake_anim_force_startend_keying=True,
            add_leaf_bones=False,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
            armature_nodetype='NULL'
        )
        
        
    
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # recover original scene and remove temporary one
        bpy.context.window.scene = original_scene
        bpy.data.scenes.remove(temp_scene)




if __name__ == "__main__":
    
    setMotion2Armature(
        "G:/3d/humanoid/Mixamo/medea.fbx",
        "../Common/Motion/motion_smpl_sample.npy",
        "G:/3d/animation/generated/medea_animated.fbx",
        armature_joint_names = motion_util.joint_names_mixamo,
        motion_joint_names = motion_util.joint_names_smpl,
        retarget_table_path = "../Common/Motion/retarget_table/smpl_to_mixamo.json"
    )
    