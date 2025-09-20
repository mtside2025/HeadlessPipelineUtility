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
from mathutils import Matrix, Vector, Quaternion, Euler
from scipy.spatial.transform import Rotation as R


# https://meshcapade.wiki/SMPL#related-models-the-smpl-family
joint_names_smpl = [
    "pelvis",   # 0
    "left_hip", # 1
    "right_hip",    #2
    "spine1",       #3
    "left_knee",    #4
    "right_knee",   #5
    "spine2",       #6
    "left_ankle",   #7
    "right_ankle",  #8
    "spine3",       #9
    "left_foot",    #10
    "right_foot",   #11
    "neck",     #12
    "left_collar",  #13
    "right_collar", #14
    "head",     #15
    "left_shoulder",    #16
    "right_shoulder",   #17
    "left_elbow",   #18
    "right_elbow",  #19
    "left_wrist",   #20
    "right_wrist",  #21
    "left_hand",    #22
    "right_hand"    #23
]


joint_names_mixamo = [
    "Hips",                #  0: pelvis
    "LeftUpLeg",           #  1: left_hip
    "RightUpLeg",          #  2: right_hip
    "Spine",               #  3: spine1
    "LeftLeg",             #  4: left_knee
    "RightLeg",            #  5: right_knee
    "Spine1",              #  6: spine2
    "LeftFoot",            #  7: left_ankle
    "RightFoot",           #  8: right_ankle
    "Spine2",              #  9: spine3
    "LeftToeBase",         # 10: left_foot
    "RightToeBase",        # 11: right_foot
    "Neck",                # 12: neck
    "LeftShoulder",        # 13: left_collar
    "RightShoulder",       # 14: right_collar
    "Head",                # 15: head
    "LeftArm",             # 16: left_shoulder
    "RightArm",            # 17: right_shoulder
    "LeftForeArm",         # 18: left_elbow
    "RightForeArm",        # 19: right_elbow
    "LeftHand",            # 20: left_wrist
    "RightHand",           # 21: right_wrist
    "LeftHandMiddle1",     # 22: left_hand (representative finger-bone is chosen)
    "RightHandMiddle1"     # 23: right_hand
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
def getJointChains(num_joints):
    
    junction_nodes = []
    
    if num_joints == 21:
        joint_chains = [
            [0, 11, 12, 13, 14, 15],
            [0, 16, 17, 18, 19, 20],
            [0, 1, 2, 3, 4],
            [3, 5, 6, 7],
            [3, 8, 9, 10]
        ]
    elif num_joints == 22:
        joint_chains = [
            [0, 2, 5, 8, 11],       # right-lower-body
            [0, 1, 4, 7, 10],       # left-lower-body
            [0, 3, 6, 9, 12, 15],   # body-axis
            [9, 14, 17, 19, 21],    # right-upper-body
            [9, 13, 16, 18, 20]     # left-upper-body
        ]
    elif num_joints == 24:
        joint_chains = [
            [0, 2, 5, 8, 11],       # right-lower-body
            [0, 1, 4, 7, 10],       # left-lower-body
            [0, 3, 6, 9, 12, 15],   # body-axis
            [9, 14, 17, 19, 21, 23],    # right-upper-body
            [9, 13, 16, 18, 20, 22]     # left-upper-body
        ]
    else:
        raise NotImplementedError(f"This joint-type (num_joints={num_joints}) is not implemented.")
    
    for chain in joint_chains:
        if chain[0] not in junction_nodes:
            junction_nodes.append(chain[0])
    
    return joint_chains, junction_nodes
    

