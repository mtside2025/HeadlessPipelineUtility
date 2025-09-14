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



# convert FBX-motion to BVH
def fbx2bvh(
    fbx_path,
    bvh_path
):

    # create temporary scene for the load
    temp_scene = bpy.data.scenes.new("TempScene")
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = temp_scene
    
    try:
        # load FBX
        bpy.ops.import_scene.fbx(filepath=fbx_path)
        
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
        
        # export as BVH-format
        bpy.ops.export_anim.bvh(
            filepath=bvh_path,
            frame_start=1,
            frame_end=bpy.context.scene.frame_end
            )
    
    
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # recover original scene and remove temporary one
        bpy.context.window.scene = original_scene
        bpy.data.scenes.remove(temp_scene)



if __name__ == "__main__":
    
    fbx2bvh(
        "G:/3d/animation/general/Walking.fbx",
        "G:/3d/animation/general/Walking.bvh"
    )
    
    
