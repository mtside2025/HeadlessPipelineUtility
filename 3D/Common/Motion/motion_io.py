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
import motion_util


# load motion-data (.npy or .npz)
def loadMotion(
    filepath,
    joint_names = None,
    joint_rotation_offsets = None
    ):
    
    _, ext = os.path.splitext(filepath)
    
    # from .npy (no keys): numpy(1, frames, joints, 3)
    if ext == ".npy":
        
        if joint_names is None:
            raise ValueError(f"Joint-names must be specified as an argument of loadMotion.")
        
        motion_data = np.load(filepath)
        print(f"\"{filepath}\" is loaded. The shape = {motion_data.shape}")
        
        dic_data = {}
        for i, name in enumerate(joint_names):
            if i >=  motion_data.shape[2]:
                break
                
            dic_data[name] = motion_data[0, :, i, :]
        
    
    # from .npz (with keys): dic{keys = joint_names, values = numpy(frames, 3)}
    elif ext == ".npz":
        dic_data = np.load(filepath)
        if joint_names is None:
            joint_names = dic_data.keys()
    
    else:
        raise ValueError(f"Invalid file format: {filepath}")
    
    
    # returns as rotation-data when the offsets are specified
    if joint_rotation_offsets is not None:
        
        kinetic_chain = motion_util.getBodyChain(len(dic_data.keys()))
        
        dic_data = motion_util.pos2grot(
            dic_data,
            kinetic_chain,
            joint_names
        )
        
        joint_rotation_offset_values = list(joint_rotation_offsets.values())
        for i, (key, value) in enumerate(dic_data.items()):
            joint_rotation_offset = np.array(joint_rotation_offset_values[i]).reshape(3)
            for frame_idx in range(dic_data[key].shape[0]):
                dic_data[key][frame_idx,:] -= joint_rotation_offset
        
    
    return dic_data



# save motion-data as npz
# motion_data: numpy array (1, #frames, #joints, 3)
def saveMotion(filepath, motion_data, joint_names):
    
    _, ext = os.path.splitext(filepath)
    if ext != ".npz":
        raise ValueError(f"File path {filepath} must be npz-format (.npz).")
    
    if len(motion_data) > len(joint_names):
        raise ValueError(f"In saveMotion({filepath}): {len(motion_data)} joints exceeds {len(joint_names)} input joint names.")
    
    dic_data = {name: motion_data[0, :, i, :] for i, name in enumerate(joint_names)}
    np.savez_compressed(filepath, **dic_data)
    
    


