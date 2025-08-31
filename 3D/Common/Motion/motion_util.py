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
from scipy.spatial.transform import Rotation as R


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


joint_names_mixamo = [
    "Hips",                # pelvis
    "LeftUpLeg",           # left_hip
    "RightUpLeg",          # right_hip
    "Spine",               # spine1
    "LeftLeg",             # left_knee
    "RightLeg",            # right_knee
    "Spine1",              # spine2
    "LeftFoot",            # left_ankle
    "RightFoot",           # right_ankle
    "Spine2",              # spine3
    "LeftToeBase",         # left_foot
    "RightToeBase",        # right_foot
    "Neck",                # neck
    "LeftShoulder",        # left_collar
    "RightShoulder",       # right_collar
    "Head",                # head
    "LeftArm",             # left_shoulder
    "RightArm",            # right_shoulder
    "LeftForeArm",         # left_elbow
    "RightForeArm",        # right_elbow
    "LeftHand",            # left_wrist
    "RightHand",           # right_wrist
    "LeftHandMiddle1",     # left_hand (representative finger-bone is chosen)
    "RightHandMiddle1"     # right_hand
]



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
def getBodyChain(num_joints):

    if num_joints == 21:
        kinetic_chain = [
            [0, 11, 12, 13, 14, 15],
            [0, 16, 17, 18, 19, 20],
            [0, 1, 2, 3, 4],
            [3, 5, 6, 7],
            [3, 8, 9, 10]
        ]
    elif num_joints == 22:
        kinetic_chain = [
            [0, 2, 5, 8, 11],       # right-lower-body
            [0, 1, 4, 7, 10],       # left-lower-body
            [0, 3, 6, 9, 12, 15],   # body-axis
            [9, 14, 17, 19, 21],    # right-upper-body
            [9, 13, 16, 18, 20]     # left-upper-body
        ]
    elif num_joints == 24:
        kinetic_chain = [
            [0, 2, 5, 8, 11],       # right-lower-body
            [0, 1, 4, 7, 10],       # left-lower-body
            [0, 3, 6, 9, 12, 15],   # body-axis
            [9, 14, 17, 19, 21, 23],    # right-upper-body
            [9, 13, 16, 18, 20, 22]     # left-upper-body
        ]
    else:
        raise NotImplementedError(f"This joint-type (num_joints={num_joints}) is not implemented.")
        
    return kinetic_chain
    



#
# convert posiotional data to global rotation data
#
def pos2grot (
    dic_data_pos,
    kinetic_chain,
    joint_names
    ):
    
    num_frames = len(list(dic_data_pos.values())[0])
    dic_data_rot = dic_data_pos.copy()
    
    for chain in kinetic_chain:
        
        for frame_idx in range(num_frames):
            
            ref_direction = [0, 1, 0] # initial direction of reference
            
            for joint_idx in range(1, len(chain)):
                
                pos_data = dic_data_pos[joint_names[joint_idx]] # numpy(frames, 3)
                pos = pos_data[frame_idx, :]
                
                parent_pos_data = dic_data_pos[joint_names[joint_idx-1]] # numpy(frames, 3)
                parent_pos = parent_pos_data[frame_idx, :]
                
                direction = pos - parent_pos
                
                # compute difference from reference-direction
                rot, _ = R.align_vectors([direction], [ref_direction])
                
                rot_data = dic_data_rot[joint_names[joint_idx]] # numpy(frames, 3)
                rot_data[frame_idx, :] = rot.as_euler('XYZ', degrees=False)
                
                # update reference direction
                ref_direction = direction
            
        
    return dic_data_rot
    


