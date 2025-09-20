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
import os
import glob
import json
import math

def retarget(
    input_motion_path,
    output_motion_path,
    rename_dict
):

    # create temporary scene for the load
    temp_scene = bpy.data.scenes.new("TempScene")
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = temp_scene
    
    try:
        #
        # load motion
        #
        
        input_ext = os.path.splitext(input_motion_path)[1].lower()
        
        # load FBX
        if input_ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=input_motion_path)
        # load BVH
        elif input_ext == ".bvh":
            bpy.ops.import_anim.bvh(
                filepath=input_motion_path,
                axis_forward="Y",
                axis_up="Z"
                )
            
            # load FPS from BVH (Frame Time)
            with open(input_motion_path) as f:
                for line in f:
                    if line.startswith("Frame Time:"):
                        frame_time = float(line.split(":")[1].strip())
                        bpy.context.scene.render.fps = round(1 / frame_time)
                        break
            
        else:
            raise NotImplementedError(f"{input_motion_path}: Unsupported input motion-file format.")
        
        
        
        # search armature
        armature = None
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break
            
        if armature is None:
            print(f"No-armature exist in {fbx_path}. The scene includes:")
            for obj in  bpy.data.objects:
                print(obj.name)
            raise AttributeError()
        
        # set armature active
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)
        
        
        # get frames
        action = armature.animation_data.action
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = int(action.frame_range[1]) - int(action.frame_range[0]) + 1
        
        
        #
        # rename joints and remove undefined ones
        #
        for bone in armature.data.bones:
            if bone.name in rename_dict:
                bone.name = rename_dict[bone.name]
            else:
                print(f"{bone.name} is not listed in rename-dict.")
        
        
        #
        # save motion
        #
        
        output_ext = os.path.splitext(output_motion_path)[1].lower()
        
        # save as FBX
        if input_ext == ".fbx":
            bpy.ops.export_scene.fbx(
                filepath=output_motion_path,
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
        
        # save as BVH
        elif input_ext == ".bvh":
            bpy.ops.export_anim.bvh(
                filepath=output_motion_path,
                frame_start=1,
                frame_end=bpy.context.scene.frame_end
                )
            
        else:
            raise NotImplementedError(f"{output_motion_path}: Unsupported output motion-file format.")
    
    
    finally:
        pass
        """
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # recover original scene and remove temporary one
        bpy.context.window.scene = original_scene
        bpy.data.scenes.remove(temp_scene)
        """


def retarget_dir(
    input_dir,
    output_dir,
    rename_json_path
):
    motion_ext = [".bvh", ".fbx"]
    
    # load renaming-rule from json
    with open(rename_json_path) as f:
        rename_dict = json.load(f)
    
    # list all files in "input_dir"
    filepaths = glob.glob(f"{input_dir}/**", recursive=True)
    relative_filepaths = [
        os.path.relpath(path, input_dir)
        for path in filepaths
        if os.path.isfile(path)
    ]
    
    print(f"{len(filepaths)} files exist in {input_dir}")
    
    # rename joints and save as motion-file per each file
    for relpath in relative_filepaths:
        
        ext = os.path.splitext(relpath)[1].lower()
        if ext not in motion_ext:
            continue
        
        input_filepath = f"{input_dir}/{relpath}"
        output_filepath = f"{output_dir}/{relpath}"
        
        # create output-directory (if necessary)
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        
        retarget(
            input_filepath,
            output_filepath,
            rename_dict
        )



if __name__ == "__main__":
    
    """
    input_dir = "G:/3d/animation/michael_bvh"
    output_dir = "G:/3d/animation/michael_bvh_smplx"
    rename_json_path = "G:/3d/animation/michael_bvh/conversion.json"
    """
    input_dir = "../Common/Motion"
    output_dir = "./tmp"
    rename_json_path = "../Common/Motion/retarget_table/smpl_to_mixamo.json"
    
    retarget_dir(
        input_dir,
        output_dir,
        rename_json_path
    )
    