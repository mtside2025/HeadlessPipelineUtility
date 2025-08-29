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


# https://meshcapade.wiki/SMPL#related-models-the-smpl-family
joint_names_smpl = [
    "pelvis",
    "left_hip",
    "right_hip",
    "spine1",
    "left_knee",
    "right_knee",
    "spine2",
    "left_ankle",
    "right_ankle",
    "spine3",
    "left_foot",
    "right_foot",
    "neck",
    "left_collar",
    "right_collar",
    "head",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hand",
    "right_hand"
]



# load motion-data (.npy or .npz)
def loadMotion(filepath, joint_names = None):
    
    _, ext = os.path.splitext(filepath)
    
    # from .npy (no keys)
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
        
    
    # from .npz (with keys)
    elif ext == ".npz":
        dic_data = np.load(filepath)
    
    else:
        raise ValueError(f"Invalid file format: {filepath}")
    
    return dic_data



# save SMPL data as npz
# motion_data: numpy array (1, #frames, #joints, 3)
def saveMotion(filepath, motion_data, joint_names):
    
    _, ext = os.path.splitext(filepath)
    if ext != ".npz":
        raise ValueError(f"File path {filepath} must be npz-format (.npz).")
    
    if len(motion_data) > len(joint_names):
        raise ValueError(f"In saveMotion({filepath}): {len(motion_data)} joints exceeds {len(joint_names)} input joint names.")
    
    dic_data = {name: motion_data[0, :, i, :] for i, name in enumerate(joint_names)}
    np.savez_compressed(filepath, **dic_data)
    
    


#
# get kinetic chains as follows:
#
# [
#   [right-lower-body],
#   [left-lower-body],
#   [body-axis],
#   [right-upper-body],
#   [left-upper-body]
# ]
#
# https://www.researchgate.net/figure/Layout-of-23-joints-in-the-SMPL-models_fig2_351179264
#
def getKineticChainSMPL(num_joints):

    if nb_joints == 21:
        kinetic_chain = [
            [0, 11, 12, 13, 14, 15],
            [0, 16, 17, 18, 19, 20],
            [0, 1, 2, 3, 4],
            [3, 5, 6, 7],
            [3, 8, 9, 10]
        ]
    elif nb_joints == 22:
        kinetic_chain = [
            [0, 2, 5, 8, 11],       # right-lower-body
            [0, 1, 4, 7, 10],       # left-lower-body
            [0, 3, 6, 9, 12, 15],   # body-axis
            [9, 14, 17, 19, 21],    # right-upper-body
            [9, 13, 16, 18, 20]     # left-upper-body
        ]
    elif nb_joints == 24:
        kinetic_chain = [
            [0, 2, 5, 8, 11],       # right-lower-body
            [0, 1, 4, 7, 10],       # left-lower-body
            [0, 3, 6, 9, 12, 15],   # body-axis
            [9, 14, 17, 19, 21, 23],    # right-upper-body
            [9, 13, 16, 18, 20, 22]     # left-upper-body
        ]
    else:
        raise NotImplementedError(f"This jointstype (nb_joints={nb_joints}) is not implemented.")
        
    return kinetic_chain
    
