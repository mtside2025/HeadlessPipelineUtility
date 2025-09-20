# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import numpy as np
import pickle
import skeleton_util
from pos2rotation import pos2rot


# load positional motion-data (.npy) as list of ndarray(frames, joints, 3) and compute corresponding rotations
def loadPositionalMotions(
    filepath,
    rotation_order="XYZ"
    ):
    
    _, ext = os.path.splitext(filepath)
    
    if ext == ".npy":
        
        motion_data = np.load(filepath, allow_pickle=True)
        if motion_data.size == 1:
            motion_data = motion_data.item()
        
        # dict{"motion", "text", ..."}
        if isinstance(motion_data, dict):
            print(f"\"{filepath}\" is loaded. Following keys exist:")
            for key in motion_data:
                print(key)
                
            data_pos = motion_data["motion"]
            print(f"Shape of motion-data: {motion_data.shape}") # ndarray(N, joints, 3, frames)
            
            ##
            ## TODO: 次元の入れ替え
            ##
            
        
        # ndarray(N, frames, joints, 3)
        elif isinstance(motion_data, np.ndarray):
            print(f"\"{filepath}\" is loaded. The shape = {motion_data.shape}")
            data_pos = motion_data
            
            
        # others
        else:
            print(motion_data)
            raise ValueError(f"{filepath} is invalid format.")
            
        
    elif ext == ".npz":
        raise NotImplementedError(f"Invalid file format: {filepath}")
    
    else:
        raise ValueError(f"Invalid file format: {filepath}")
    
    
    data_pos_list = []
    data_rot_list = []
    
    for i in range(data_pos.shape[0]):
        data_rot = pos2rot(data_pos[i], rotation_order)
        data_pos_list.append(data_pos[i])
        data_rot_list.append(data_rot)
    
    return data_pos_list, data_rot_list






def exportToBvh(
    filename,
    data_pos,
    data_rot,
    joint_names,
    rotation_order,
    outputPosition=True,
    outputRotation=True,
    frame_time=1/30.0,
    base_indent="    "
    ):
    
    assert(outputPosition or outputRotation)
    
    frames, joints, _ = data_pos.shape
    joint_chains = skeleton_util.getJointChains(joints)
    
    data_pos *= 100.0 # m -> cm
    
    with open(filename, 'w') as f:
        
        #
        # Write BVH hierarchy
        #
        
        f.write("HIERARCHY\n")
        f.write(f"ROOT {joint_names[0]}\n") # joint[0] must be ROOT
        f.write("{\n")
        
        # set root-position as OFFSET from 1st-frame
        root_pos = data_pos[0, 0]
        f.write(f"{base_indent}OFFSET {root_pos[0]} {root_pos[1]} {root_pos[2]}\n")
        f.write(f"{base_indent}CHANNELS 6 Xposition Yposition Zposition {rotation_order[0]}rotation {rotation_order[1]}rotation {rotation_order[2]}rotation\n\n")
        
        
        # write hierarchy of each joint and save the order as list
        joint_order = [0]
        parent_order = [-1]
        _writeChildChains(
            f,
            0, # parent_index (root)
            1, # indent_depth
            joint_chains,
            joint_names,
            joint_order,
            parent_order,
            outputPosition,
            outputRotation,
            rotation_order,
            base_indent
        )
        
        f.write("}\n")
        
        
        #
        # Write motion data
        #
        
        f.write("\nMOTION\n")
        f.write(f"Frames: {frames}\n")
        f.write(f"Frame Time: {frame_time:.6f}\n")
        
        rotation_order_index = [
            ord(rotation_order[0]) - ord('X'),
            ord(rotation_order[1]) - ord('X'),
            ord(rotation_order[2]) - ord('X')
        ]
        
        for f_idx in range(frames):
            line = []
            for i, j in enumerate(joint_order):
                    
                if j == 0 or outputPosition:
                    if j == 0:
                        pos = data_pos[f_idx, j]
                    else:
                        pos = data_pos[f_idx, j] - data_pos[f_idx, parent_order[i]]
                    line.extend([f"{p:.6f}" for p in pos])
                
                if j == 0 or outputRotation:
                    for rot_order in rotation_order_index:
                        rot = data_rot[f_idx, j, rot_order]
                        line.append(f"{rot:.6f}")
                
            if f_idx == 0:
                print(f"{filename}: {len(line)} motion-data of {len(joint_order)} joints per frame (totally {frames} frames) are being exported.")
                
            f.write(" ".join(line) + "\n")



def _writeChildChains(
    file,
    parent_index,
    indent_depth,
    joint_chains,
    joint_names,
    joint_order,
    parent_order,
    outputPosition,
    outputRotation,
    rotation_order,
    base_indent
):
    for i, chain in enumerate(joint_chains):
        
        if chain[0] != parent_index:
            continue
        
        for j in range(1, len(chain)):
            
            joint_idx  = chain[j]
            parent_idx = chain[j-1]
            joint_order.append(joint_idx)
            parent_order.append(parent_idx)
            
            indent = base_indent * (indent_depth + j-1)
            file.write(f"{indent}JOINT {joint_names[joint_idx]}\n")
            file.write(f"{indent}{{\n")
            
            # set joint-position as OFFSET from 1st-frame
            joint_pos = data_pos[0, joint_idx] - data_pos[0, parent_idx]
            indent = base_indent * (indent_depth + j)
            file.write(f"{indent}OFFSET {joint_pos[0]} {joint_pos[1]} {joint_pos[2]}\n")
            
            if outputPosition and outputRotation:
                file.write(f"{indent}CHANNELS 6 Xposition Yposition Zposition {rotation_order[0]}rotation {rotation_order[1]}rotation {rotation_order[2]}rotation\n\n")
            elif outputPosition:
                file.write(f"{indent}CHANNELS 3 Xposition Yposition Zposition\n\n")
            else:
                file.write(f"{indent}CHANNELS 3 {rotation_order[0]}rotation {rotation_order[1]}rotation {rotation_order[2]}rotation\n\n")
            
            # write hierarchy recursively
            _writeChildChains(
                file,
                joint_idx, # parent_index
                indent_depth + j, # indent_depth
                joint_chains[i+1:],
                joint_names,
                joint_order,
                parent_order,
                outputPosition,
                outputRotation,
                rotation_order,
                base_indent
            )
            
        
        indent = base_indent * (indent_depth + len(chain)-1)
        file.write(f"{indent}End Site\n")
        file.write(f"{indent}{{\n")
        indent = base_indent * (indent_depth + len(chain))
        file.write(f"{indent}OFFSET 0 0 0\n")
        indent = base_indent * (indent_depth + len(chain)-1)
        file.write(f"{indent}}}\n")
        
        
        for j in range(len(chain) - 1, 0, -1):
            indent = base_indent * (indent_depth + j-1) # j-1: len(chain)-2 to 0
            file.write(f"{indent}}}\n")
            
        indent = base_indent * indent_depth
        file.write("\n")



if __name__ == "__main__":
    
    data_pos_list, data_rot_list = loadPositionalMotions(
        #"D:/Project/Motion/LoRA-MDM/save/out/results.npy"
        "motion_smpl_sample.npy"
    )
    
    
    rotation_order_bvh = "ZXY"
    
    for i, data_pos in enumerate(data_pos_list):
        exportToBvh(
            f"test{i}.bvh",
            data_pos,
            data_rot_list[i],
            skeleton_util.joint_names_smpl[:data_pos.shape[1]],
            rotation_order = rotation_order_bvh,
            frame_time=1/30.0
        )