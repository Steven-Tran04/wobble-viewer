"""
Blender Automation Script for 3D Model Generation

This script automates the process of creating 3D models from 2D images in Blender
using the zform addon. It loads cleaned RGB images and depth maps, applies depth
information to create 3D geometry, handles material transparency, and exports the
result as a GLB file for use in 3D applications or web viewers.

Workflow:
1. Enables the zform addon if not already active
2. Clears the existing scene
3. Loads a cleaned (transparent) image as the base
4. Applies depth mapping to create 3D geometry
5. Converts modifiers to mesh for export stability
6. Configures material transparency using alpha channels
7. Exports the scene as a GLB file

Requirements:
- Blender with zform addon installed
- Input files: images/cleaned.png (transparent image) and images/depth.png (depth map)
- Output: full_scene_export.glb
- Configuration: Set the `BLENDER_PATH` environment variable to your Blender executable path

Usage:
    Run in Blender: blender -b -P blender.py
    Or from within Blender's Python console/script editor.
    Ensure the `BLENDER_PATH` environment variable is set before running `run_all.sh` or Blender commands.
"""

import bpy
import glob
import os

# Get absolute paths
dir_path = os.path.dirname(os.path.realpath(__file__))
images_dir = os.path.join(dir_path, "images")

cleaned_candidates = glob.glob(os.path.join(images_dir, "*_cleaned.png"))
depth_candidates = glob.glob(os.path.join(images_dir, "*_depth.png"))

if not cleaned_candidates:
    raise FileNotFoundError(
        "No cleaned image found. Expected at least one file matching '*_cleaned.png' in the images/ folder."
    )
if not depth_candidates:
    raise FileNotFoundError(
        "No depth image found. Expected at least one file matching '*_depth.png' in the images/ folder."
    )
if len(cleaned_candidates) > 1:
    raise RuntimeError(
        "Multiple cleaned images found in images/. Please keep only one '*_cleaned.png' file or update blender.py to select the correct one."
    )
if len(depth_candidates) > 1:
    raise RuntimeError(
        "Multiple depth images found in images/. Please keep only one '*_depth.png' file or update blender.py to select the correct one."
    )

cleaned_path = cleaned_candidates[0]
depth_path = depth_candidates[0]
export_path = os.path.join(dir_path, "meshes/full_scene_export.glb")

# Enable the addon
if "zform" not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module="zform")

# Clear existing mesh data
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Load the primary RGB image
bpy.ops.zform.load_image(filepath=cleaned_path)

# Grab the newly created object
target_obj = bpy.context.active_object 

if target_obj:
    # Load depth and Apply
    bpy.data.scenes["Scene"].zform_depth_image_path = depth_path
    bpy.data.scenes["Scene"].zform_smooth_factor = 2.0
    bpy.ops.zform.apply_depth()

    # Convert to mesh to "freeze" the 3D shape
    # This turns the modifiers into actual geometry for the GLB
    bpy.ops.object.convert(target='MESH')

    # Handle Material Transparency
    material = target_obj.active_material # More robust than .get("cleaned")
    if material and material.use_nodes:
        material.blend_method = 'BLEND'
        material.use_backface_culling = True
        
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        principled = nodes.get("Principled BSDF")
        # Try to find the texture node dynamically
        tex_node = next((n for n in nodes if n.type == 'TEX_IMAGE'), None)
        
        if principled and tex_node:
            links.new(tex_node.outputs['Alpha'], principled.inputs['Alpha'])

    # Export
    # We use 'use_selection=True' since we've ensured target_obj is selected
    bpy.ops.export_scene.gltf(
        filepath=export_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_image_format='AUTO'
    )
    print(f"Exported successfully to: {export_path}")

else:
    print("Error: No object was created/selected after load_image.")
