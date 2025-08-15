import bpy
import os
import sys
import json

# print animation information of the specified object
def printAnimationInfo(obj):
    
    print(f"\nAnimation Information of object \"{obj.name}\":\n")
    
    # check if the object has animation data
    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        print(f"[Action Name: {action.name}]\n")
        
        # print each F-curve infomration
        for fcurve in action.fcurves:
            print(f"Datapath: {fcurve.data_path}, Index: {fcurve.array_index}")
            
            # print each key-frame information
            for i, keyframe in enumerate(fcurve.keyframe_points):
                print(f"Frame: {int(keyframe.co.x):5d}, Value: {keyframe.co.y}")
            
            print()
        
    else:
        print(f"No animation for this object.")
    


def setAnimations(
    asset_name,
    objects,
    verbose = True
    ):
    
    json_path = f"./scene/anim_{asset_name}.json"
    if not os.path.isfile(json_path):
        # finish if json-file does not exist
        return False
    
    with open(json_path) as f:
        animations = json.load(f)
    
    # set 1-action to 1-object
    for obj_name, action_data in animations.items():
        
        if obj_name == "Variables":
            continue
        
        obj = objects[obj_name]
        
        obj.animation_data_create()
        action = bpy.data.actions.new(name = action_data["action_name"])
        
        # set f-curves
        for fcurve_data in action_data["fcurves"]:
            
            axis  = fcurve_data["property"][1].upper()
            index = 0 if axis == "X" else 1 if axis == "Y" else 2
            data_path = fcurve_data["property"][0]
            
            fcurve = action.fcurves.new(
                data_path = data_path,
                index = index
            )
            
            # set mofifiers
            if "modifiers" in fcurve_data:
                for mod_data in fcurve_data["modifiers"]:
                    mod_type = mod_data[0].upper()
                    mod = fcurve.modifiers.new(type = mod_type)
                    if mod_type == "CYCLES":
                        # REPEAT/MIRROR
                        mod.mode_before = mod_data[1].upper()
                        mod.mode_after  = mod_data[2].upper()
                    elif mod_type == "NOISE":
                        mod.strength = mod_data[1]
                        mod.scale = mod_data[2]
                    elif mod_type == "ENVELOPE":
                        pass
                    elif mod_type == "LIMITS":
                        pass
                    elif mod_type == "GENERATOR":
                        pass
                    else:
                        print(f"Error: unknown modifier-type {mod_type} of F-curve \"{data_path}\" for the object \"{obj_name}\".")
                        exit()
            
            # add key-frames
            fcurve.keyframe_points.add(count = len(fcurve_data["keyframe_points"]))
            
            for i, keyframe_data in enumerate(fcurve_data["keyframe_points"]):
                
                keyframe_point = []
                
                # set key-frame index
                if isinstance(keyframe_data["frame"], str):
                    # relace variable to the value
                    keyframe_point.append(animations["Variables"][keyframe_data["frame"]])
                else:
                    keyframe_point.append(keyframe_data["frame"])
                
                
                # set key-frame value
                if isinstance(keyframe_data["value"], str):
                    # replace variable to the value
                    keyframe_point.append(animation["Variables"][keyframe_data["value"]])
                else:
                    keyframe_point.append(keyframe_data["value"])
                
                
                # update key-frame
                print(keyframe_point)
                fcurve.keyframe_points[i].co = keyframe_point
                
                
                # set key-frame interpolation
                if "interpolation" in keyframe_data:
                    interpolation_type = keyframe_data["interpolation"].upper()
                elif "InterpolationGlobal" in animations["Variables"]:
                    interpolation_type = animations["Variables"]["InterpolationGlobal"].upper()
                else:
                    interpolation_type = None
                
                if interpolation_type is not None:
                    fcurve.keyframe_points[i].interpolation = interpolation_type
                
            
        
        # set action to the object
        obj.animation_data.action = action
    
    
    # print animation information
    if verbose:
        for obj in bpy.data.objects:
            printAnimationInfo(obj)
    
    
    
