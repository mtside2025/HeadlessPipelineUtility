import bpy
import os
import sys
import json

# obtain list of conntected nodes and sockets
def get_connected_output_nodes(node):
    
    connected_nodes = []
    connected_sockets = []
    
    for output in node.outputs:
        if output.is_linked:
            for link in output.links:
                connected_nodes.append(link.to_node)
                connected_sockets.append(link.to_socket)
    
    return connected_nodes, connected_sockets


# print specified node information
def printNodeInfo(node, connected_nodes, connected_sockets):
    
    print(f"- Node Name:  {node.name}")
    print(f"- Node Label: {node.label}")
    print(f"- Node ID:    {node.bl_idname}")
    
    if len(connected_nodes) > 0:
        print(f"- Connected Nodes and Sockets:")
        for i, cnode in enumerate(connected_nodes):
            print(f"\tnode-name:   {cnode.name}")
            print(f"\tnode-type:   {cnode.type}")
            print(f"\tnode-id:     {cnode.bl_idname}")
            print(f"\tsocket_name: {connected_sockets[i].name}")
            print()
        
    return


# print specified texture-image information
def printImageInfo(image):
    print(f"- image-name:        {image.name}")
    print(f"- image-size:        (width={image.size[0]}, height={image.size[1]})")
    print(f"- image-channel:     {image.channels}")
    print(f"- image-color-space: {image.colorspace_settings.name}")
    print(f"- image-file-path:   {image.filepath}")



# set image instance to TEX_IMAGE node which has the path to the image-file
def setUnpackedTextures(
    texture_dir,
    materials,
    verbose = False
):
    for mat in materials:
        
        # obtain TEX_IMAGE node
        if mat.use_nodes:
            tex_nodes = [node for node in mat.node_tree.nodes if node.type == 'TEX_IMAGE']
        
        # skip non-node structure matrials
        # (need to create json-file which has the corresponding paths and call "setSpecifiedTextures")
        if not mat.use_nodes or len(tex_nodes) == 0:
            print(f"Warning: Material \"{mat.name}\" does not have any nodes: texture-mapping is skipped.")
            continue
        
        print(f"\nMaterial \"{mat.name}\" has {len(tex_nodes)} texture-nodes:")
        
        for i, tex_node in enumerate(tex_nodes):
            
            # obtain connected nodes and sockets
            connected_nodes, connected_sockets = get_connected_output_nodes(tex_node)
            
            # skip if the TEX_IMAGE node does not connect to any nodes
            if len(connected_nodes) == 0:
                printNodeInfo(tex_node, connected_nodes, connected_sockets)
                print("Warning: The node is not connected to any nodes. (skipped)")
                continue
            
            # the 1st node is selected if the TEX_IMAGE node is connected to multiple nodes
            if len(connected_nodes) >= 2:
                printNodeInfo(tex_node, connected_nodes, connected_sockets)
                print("Warning: The node is connected to multiple nodes. The 1st one is selected.")
            
            conntected_node = connected_nodes[0]
            connected_socket = connected_sockets[0]
            
            # skip if the TEX_IMAGE node has no image information
            if tex_node.image is None or (not tex_node.image.has_data and not tex_node.image.filepath):
                printNodeInfo(tex_node, connected_nodes, connected_sockets)
                print(f"No image information (skipped)")
                continue
                
            
            # load image from the path when the TEX_IMAGE does not have the image binary
            if not tex_node.image.has_data:
                
                if verbose:
                    printNodeInfo(tex_node, connected_nodes, connected_sockets)
                
                image_name = os.path.basename(tex_node.image.filepath)
                image_path = f"{texture_dir}/{image_name}"
                
                try:
                    loaded_image = bpy.data.images.load(str(image_path), check_existing=True)
                except RuntimeError as e:
                    printNodeInfo(tex_node, connected_nodes, connected_sockets)
                    print(f"Preset image \"{image_name}\" does not exist in \"{texture_dir}\". Texture-paths specification file (.json) is needed.")
                    continue
                
                original_image = tex_node.image
                tex_node.image = loaded_image
                tex_node.image.colorspace_settings.name = original_image.colorspace_settings.name
                
                if verbose:
                    printImageInfo(tex_node.image)
                    print(f"Texture-image \"{image_path}\" is loaded and set.\n")
                
            elif verbose:
                print("\n[Preset image and the node information]")
                printNodeInfo(tex_node, connected_nodes, connected_sockets)
                printImageInfo(tex_node.image)
        
    return



# obtain paths from json-file and set image to the specified material
def setSpecifiedTextures(
    asset_name,
    texture_dir,
    materials,
    verbose = False
    ):
    
    json_path = f"./scene/texture_{asset_name}.json"
    if not os.path.isfile(json_path):
        # finish if json-file does not exist
        return False
    
    with open(json_path) as f:
        texture_paths = json.load(f)
    
    for mat_name, dic_paths in texture_paths.items():
        
        if mat_name == "":
            continue
            
        # search the material
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            print(f"Specified material \"{mat_name}\" in {json_path} is not found.")
            exit()
        
        mat.use_nodes = True
        
        # search connected nodes of the TEX_IMAGE node (create new if not exist)
        for key, tex_path in dic_paths.items():
            
            if key == "" or tex_path == "":
                continue
            
            # difrerent process is needed when the texture is normal-map
            if key == "Normal":
                
                normal_nodes = [n for n in mat.node_tree.nodes if n.type == "NORMAL_MAP"]
                
                # obtain connected nodes when the material has a normal-map node
                if len(normal_nodes) >= 1:
                    if len(normal_nodes) >= 2:
                        print(f"Warning: Material {mat_name} has multiple NORMAL_MAP nodes. The 1st one is selected.")
                    
                    target_node = normal_nodes[0]
                    
                # create new node when the material does not have normal-map node
                else:
                    print(f"Error: Node-creation of NORMAL_MAP is to be implemented.")
                    exit()
                
                base_input = target_node.inputs.get("Color")
                if base_input is None:
                    print(f"Error: Material {mat_name} has NORMAL_MAP node, but does not have the input \"Color\.")
                    exit()
                
            
            # common process without non normal-map textures
            else:
                
                principled_nodes = [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
                
                # obtain connected nodes when the material has BSDF_PRINCIPLED node
                if len(principled_nodes) >= 1:
                    if len(principled_nodes) >= 2:
                        print("Warning: material {mat_name} has multiple BSDF_PRINCIPLED nodes. The 1st one is selected.")
                    
                    target_node = principled_nodes[0]
                    
                # create new node when the material does not have BSDF_PRINCIPLED node
                else:
                    target_node = nodes.new('ShaderNodeBsdfPrincipled')
                    target_node.location = (0, 0)
                
                base_input = target_node.inputs.get(key)
                if base_input is None:
                    print(f"Error: Material {mat_name} has BSDF_PRINCIPLED node, but does not have the input \"{key}\".")
                    exit()
            
            
            # obtain TEX_IMAGE node (create new when no node exists)
            if base_input.is_linked and base_input.links[0].from_node == "TEX_IMAGE":
                tex_node = base_input.links[0].from_node
            else:
                tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
                tex_node.label = "Base Color"
                tex_node.location = (-400, 0)
                
                # disconnect non TEX_IMAGE node if exists
                if base_input.is_linked:
                    print(f"Warning: Target-node of material {mat_name} is connected to non TEX_IMAGE node (disconnect).")
                    mat.node_tree.links.remove(base_input.links[0])
                
                # connect created TEX_IMAGE node to the input of the target node
                mat.node_tree.links.new(tex_node.outputs.get("Color"), base_input)
            
            
            image_path = f"{texture_dir}/{tex_path}"
            
            try:
                loaded_image = bpy.data.images.load(str(image_path), check_existing=True)
            except RuntimeError as e:
                raise FileNotFoundError(f"Loading image failed: {image_path}") from e
            
            
            # set color-space
            if key == "Base Color" or key == "Emission Color":
                loaded_image.colorspace_settings.name = "sRGB"
            else:
                loaded_image.colorspace_settings.name = "Non-Color"
            
            # set image to the TEX_IMAGE node
            tex_node.image = loaded_image
            
            # print node and image information
            print(f"\nTexture \"{tex_path}\" is loaded and set as {key} to the node of material {mat_name}.")
            if verbose:
                connected_nodes, connected_sockets = get_connected_output_nodes(tex_node)
                printNodeInfo(tex_node, connected_nodes, connected_sockets)
                printImageInfo(tex_node.image)
                print()
    
    return True


