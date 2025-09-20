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
import torch 
import matplotlib.pyplot as plt
import numpy as np
import io
import matplotlib
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import mpl_toolkits.mplot3d.axes3d as p3
from textwrap import wrap
import imageio
import skeleton_util
from np2bvh import loadPositionalMotions


def init(ax, limits):
    ax.set_xlim(-limits, limits)
    ax.set_ylim(-limits, limits)
    ax.set_zlim(0, limits)
    ax.grid(b=False)
    


def plot_xzPlane(ax, minx, maxx, miny, minz, maxz):
    ## Plot a plane XZ
    verts = [
        [minx, miny, minz],
        [minx, miny, maxz],
        [maxx, miny, maxz],
        [maxx, miny, minz]
    ]
    xz_plane = Poly3DCollection([verts])
    xz_plane.set_facecolor((0.5, 0.5, 0.5, 0.5))
    ax.add_collection3d(xz_plane)
    

# plot single-frame
def update(index, trajec, joint_chains, nb_joints, title, limits, MINS, MAXS, colors, data, out_name):

    fig = plt.figure(figsize=(480/96., 320/96.), dpi=96) if nb_joints == 21 else plt.figure(figsize=(10, 10), dpi=96)
    if title is not None :
        wraped_title = '\n'.join(wrap(title, 40))
        fig.suptitle(wraped_title, fontsize=16)
    ax = p3.Axes3D(fig)
    
    
    # "fig.add_axes(ax)" is required after matplotlib ver.3.4.0
    # https://matplotlib.org/stable/api/prev_api_changes/api_changes_3.4.0.html
    fig.add_axes(ax)
    
    
    ax.cla()
    init(ax, limits)
    
    ax.view_init(elev=110, azim=-90)
    ax.dist = 7.5
    #         ax =
    plot_xzPlane(
        ax,
        MINS[0] - trajec[index, 0],
        MAXS[0] - trajec[index, 0],
        0,
        MINS[2] - trajec[index, 1],
        MAXS[2] - trajec[index, 1]
        )
    #         ax.scatter(data[index, :22, 0], data[index, :22, 1], data[index, :22, 2], color='black', s=3)

    if index > 1:
        ax.plot3D(
            trajec[:index, 0] - trajec[index, 0],
            np.zeros_like(trajec[:index, 0]),
            trajec[:index, 1] - trajec[index, 1],
            linewidth=1.0,
            color='blue'
            )
    #             ax = plot_xzPlane(ax, MINS[0], MAXS[0], 0, MINS[2], MAXS[2])

    for i, (chain, color) in enumerate(zip(joint_chains, colors)):
        #             print(color)
        if i < 5:
            linewidth = 4.0
        else:
            linewidth = 2.0
        
        ax.plot3D(
            data[index, chain, 0],
            data[index, chain, 1],
            data[index, chain, 2],
            linewidth=linewidth,
            color=color
            )
    #         print(trajec[:index, 0].shape)

    plt.axis('off')
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])

    if out_name is not None : 
        plt.savefig(out_name, dpi=96)
        plt.close()
        
    else : 
        io_buf = io.BytesIO()
        fig.savefig(io_buf, format='raw', dpi=96)
        io_buf.seek(0)
        # print(fig.bbox.bounds)
        arr = np.reshape(
            np.frombuffer(io_buf.getvalue(), dtype=np.uint8),
            (int(fig.bbox.bounds[3]), int(fig.bbox.bounds[2]), -1)
            )
        io_buf.close()
        plt.close()
        return arr


def plot_3d_motion(
    data_pos,
    out_name,
    title,
    figsize=(10, 10),
    fps=120,
    radius=4
    ):
    
    matplotlib.use('Agg')
    
    data = data_pos #.copy().reshape(len(data_pos), -1, 3)
    
    nb_joints = data_pos.shape[1]
    
    joint_chains, junction_nodes = skeleton_util.getJointChains(nb_joints)
    
    
    limits = 1000 if nb_joints == 21 else 2
    MINS = data.min(axis=0).min(axis=0)
    MAXS = data.max(axis=0).max(axis=0)
    colors = ['red', 'blue', 'black', 'red', 'blue',
              'darkblue', 'darkblue', 'darkblue', 'darkblue', 'darkblue',
              'darkred', 'darkred', 'darkred', 'darkred', 'darkred']
    frame_number = data.shape[0]
    #     print(data.shape)

    height_offset = MINS[1] # Y-up
    data[:, :, 1] -= height_offset
    trajec = data[:, 0, [0, 2]] # (frames, Root, [X,Z]) -> Root(0) has the location-data

    data[..., 0] -= data[:, 0:1, 0]
    data[..., 2] -= data[:, 0:1, 2]


    out = []
    for i in range(frame_number) : 
        out.append(update(i, trajec, joint_chains, nb_joints, title, limits, MINS, MAXS, colors, data, out_name))
    out = np.stack(out, axis=0)
    return torch.from_numpy(out)


def plotPositionalMotions(
    data_pos_list,
    fps,
    titles = None,
    output_dir = None
    ):
    
    batch_size = len(data_pos_list)
    out = []
    
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(batch_size) : 
        
        print(f"[{i+1}/{batch_size}]")
        
        print("Plotting...")
        out.append(
            plot_3d_motion(
                data_pos_list[i],
                None,
                titles[i] if titles is not None else None
            )
        )
        
        output_animgif_path = output_dir + f"/{i:03d}.gif"
        print("Saving as animation-gif \"{output_animgif_path}\"...")
        
        imageio.mimsave(
            output_animgif_path,
            np.asarray(out[-1]),
            fps = fps
            )
            
        
    print("Done")
    out = torch.stack(out, axis=0)
    return out
    


if __name__ == "__main__":
    
    #input_np_path = "samples/motion_smpl_sample_T2M-GPT.npy"
    input_np_path = "samples/motion_smpl_sample_LoRA-MDM.npy"
    
    # load ndarray from file
    data_pos_list, data_rot_list = loadPositionalMotions(input_np_path)
    
    # load text-list from text-file
    text_file_path = os.path.splitext(input_np_path)[0] + ".txt"
    if os.path.exists(text_file_path):
        with open(text_file_path, 'r', encoding='utf-8') as f:
            texts = [line.strip() for line in f]
    else:
        texts = None
    
    name = os.path.splitext(os.path.basename(input_np_path))[0]
    output_dir = f"results/{name}"
    
    plotPositionalMotions(
        data_pos_list,
        fps = 20,
        titles = texts,
        output_dir = output_dir
        )

