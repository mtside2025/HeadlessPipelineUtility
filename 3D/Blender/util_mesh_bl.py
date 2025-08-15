import bpy
import os
import sys
import json
import math

# change translation/scale/rotation of objects in the specified assets
def setAffines(
    asset_name,
    objects,
    verbose = True
    ):
    
    json_path = f"./scene/affine_{asset_name}.json"
    if not os.path.isfile(json_path):
        # finish if json-file does not exist
        return False
    
    with open(json_path) as f:
        affine = json.load(f)
    
    # set offsets to all objects
    for obj in objects:
        
        if "offset_scale" in affine:
            obj.scale.x *= affine["offset_scale"][0]
            obj.scale.y *= affine["offset_scale"][1]
            obj.scale.z *= affine["offset_scale"][2]
            obj.location.x *= affine["offset_scale"][0]
            obj.location.y *= affine["offset_scale"][1]
            obj.location.z *= affine["offset_scale"][2]
        
        if "offset_translation" in affine:
            obj.location.x += affine["offset_translation"][0]
            obj.location.y += affine["offset_translation"][1]
            obj.location.z += affine["offset_translation"][2]
        
        if "offset_rotation" in affine:
            obj.rotation_euler.x += affine["offset_rotation"][0] / 180.0 * math.pi
            obj.rotation_euler.y += affine["offset_rotation"][1] / 180.0 * math.pi
            obj.rotation_euler.z += affine["offset_rotation"][2] / 180.0 * math.pi
        
    
    
    # set offsets to specified objects (after the setting for all-objects)
    for i, obj in enumerate(objects):
        
        if obj.name in affine:
            if "scale" in affine[obj.name]:
                scale_factor = affine[obj.name]["scale"]
                if isinstance(scale_factor, list):
                    obj.delta_scale.x = scale_factor[0]
                    obj.delta_scale.y = scale_factor[1]
                    obj.delta_scale.z = scale_factor[2]
                elif isinstance(scale_factor, (int, float)):
                    obj.delta_scale.x = scale_factor
                    obj.delta_scale.y = scale_factor
                    obj.delta_scale.z = scale_factor
                else:
                    print(f"Format error at \"scale\" of object \"obj.name\" in {json_path}: the value must be number or list.")
                    exit()
                
                if verbose:
                    print(f"Object \"{obj.name}\" is scaled: {scale_factor}")
            
            if "translation" in affine[obj.name]:
                translation_factor = affine[obj.name]["translation"]
                if isinstance(translation_factor, list):
                    obj.delta_location.x = translation_factor[0]
                    obj.delta_location.y = translation_factor[1]
                    obj.delta_location.z = translation_factor[2]
                elif isinstance(translation_factor, (int, float)):
                    obj.delta_location.x = translation_factor
                    obj.delta_location.y = translation_factor
                    obj.delta_location.z = translation_factor
                else:
                    print(f"Format error at \"translation\" of object \"obj.name\" in {json_path}: the value must be number or list.")
                    exit()
                
                if verbose:
                    print(f"Object \"{obj.name}\" is translated: {translation_factor}")
            
            if "rotation" in affine[obj.name]:
                rotation_factor = affine[obj.name]["rotation"]
                if isinstance(rotation_factor, list):
                    obj.delta_rotation_euler.x = rotation_factor[0]
                    obj.delta_rotation_euler.y = rotation_factor[1]
                    obj.delta_rotation_euler.z = rotation_factor[2]
                elif isinstance(rotation_factor, (int, float)):
                    obj.delta_rotation_euler.x = rotation_factor
                    obj.delta_rotation_euler.y = rotation_factor
                    obj.delta_rotation_euler.z = rotation_factor
                else:
                    print(f"Format error at \"rotation\" of object \"obj.name\" in {json_path}: the value must be number or list.")
                    exit()
                
                if verbose:
                    print(f"Object \"{obj.name}\" is rotated: {rotation_factor}")
            
            
    


