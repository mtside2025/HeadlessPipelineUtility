# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import skeleton_util
from scipy.spatial.transform import Rotation as R


#
# compute rotation-differences between quaternion ndarrays
# input-data format: ndarray(num, 4)
#
def computeRotationDifference(
    quats_target,
    quats_source,
    is_euler = False, # True: Euler, False: Quaternion
    rotation_order = "XYZ", # only for euler-angle
    is_degree = True       # only for euler-angle
    ):
    
    num = quats_target.shape[0]
    assert(num == quats_source.shape[0])
    
    if is_euler:
        output_delta = np.zeros((num, 3)) # output as euler
    else:
        output_delta = np.zeros((num, 4)) # output as quaternion
        output_delta[:,3] = 1.0
    
    
    for i in range(num):
        # convert to rotation-object
        rot_src = R.from_quat(quats_source[i])
        rot_tgt = R.from_quat(quats_target[i])

        # align source to target
        delta_rot = rot_src.inv() * rot_tgt

        # convert to rotation-angle
        if is_euler:
            output_delta[i] = delta_rot.as_euler(rotation_order, degrees=is_degree)
        else:
            output_delta[i] = delta_rot.as_quat()
    
    return output_delta
    



#
# convert posiotional data to global rotation data
# input-data format: ndarray(joints, 3)
#
def computeGlobalRotations (
    global_positions, # ndarray(joints, 3)
    is_euler = False, # True: Euler, False: Quaternion
    rotaton_order = "XYZ", # only for euler-angle
    is_degree = True,      # only for euler-angle
    frontal_direction = [0, 0, -1] # frontal direction of loaded skeleton
    ):
    
    joints, _ = global_positions.shape
    joint_chains, junction_nodes = skeleton_util.getJointChains(joints)
    
    if is_euler:
        global_rotations = np.zeros(global_positions.shape)
    else:
        global_rotations = np.zeros((global_positions.shape[0], 4)) # quaternion
        global_rotations[:,3] = 1.0
    
    for chain in joint_chains:
        for i in range(1, len(chain)-1):
            joint_idx = chain[i]
            if joint_idx in junction_nodes: # rotation of branched-bones cannot be estimated
                continue
            
            child_idx = chain[i+1]
            joint_pos = global_positions[joint_idx, :]
            child_pos = global_positions[child_idx, :]
            vec       = child_pos - joint_pos
            
            # compute angle from frontal-direction
            rot = R.align_vectors([vec], [frontal_direction])[0] # (target, source)
            
            if is_euler:
                global_rotations[joint_idx, :] = rot.as_euler(rotation_order, degrees=is_degree)
            else:
                global_rotations[joint_idx, :] = rot.as_quat()
            
        
    return global_rotations
    



#
# convert posiotional data to local rotation data whose axis is the parent-bone
# input-data format: ndarray(joints, 3)
#
def computeLocalRotations (
    global_positions, # ndarray(joints, 3)
    is_euler = False, # True: Euler, False: Quaternion
    rotaton_order = "XYZ", # only for euler-angle
    is_degree = True,      # only for euler-angle
    frontal_direction = [0, 0, -1] # frontal direction of loaded skeleton
    ):
    
    # compute global-rotations at first
    global_rotations = computeGlobalRotations(
        global_positions,
        is_euler = False,
        frontal_direction = frontal_direction
    )
    
    
    joints, _ = global_positions.shape
    joint_chains, junction_nodes = skeleton_util.getJointChains(joints)
    
    if is_euler:
        local_rotations = np.zeros(global_positions.shape)
    else:
        local_rotations = np.zeros((global_positions.shape[0], 4)) # quaternion
        local_rotations[:,3] = 1.0
    
    for chain in joint_chains:
        for i in range(1, len(chain)-1):
            bone_idx = chain[i]
            if bone_idx in junction_nodes: # rotation of branched-bones cannot be estimated
                continue
                
            parent_bone_idx = chain[i-1]
            
            rot_bone        = R.from_quat(global_rotations[bone_idx])
            rot_parent_bone = R.from_quat(global_rotations[parent_bone_idx])
            
            # compute angle-difference
            delta_rot = rot_parent_bone.inv() * rot_bone
            
            if is_euler:
                local_rotations[bone_idx, :] = delta_rot.as_euler(rotation_order, degrees=is_degree)
            else:
                local_rotations[bone_idx, :] = delta_rot.as_quat()
            
        
    return local_rotations
    



#
# convert posiotional data to local rotation-euler data from the 1st frame pose
# input-data format: ndarray(frames, joints, 3)
#
def pos2rot(
    data_pos,  # ndarray(frames, joints, 3)
    rotation_order="XYZ"
     ):
     
    frames, joints, _ = data_pos.shape
    joint_chains, junction_nodes = skeleton_util.getJointChains(joints)
    
    # compute global-rotation angles of the 1st frame
    initial_rotations = computeLocalRotations(data_pos[0,:,:]) # compute as quaternion
    
    
    # compute local-rotation angles from the 1st frame
    data_rot = np.zeros(data_pos.shape)
    for f in range(1, frames):
        rotations = computeLocalRotations(data_pos[f,:,:]) # compute as quaternion
        data_rot[f,:,:] = computeRotationDifference(
            rotations,
            initial_rotations,
            is_euler = True,
            rotation_order = rotation_order,
            is_degree = True
            )
        
        """
        debug_joint_index = 4
        print(f"Frame-{f+1:03d}: (", end="")
        for i, r in enumerate(data_rot[f, debug_joint_index, :]):
            print(f"{r:.1f}", end="")
            if i != 2:
                print(",\t", end="")
            
        print(")")
        """
        
        
    return data_rot



