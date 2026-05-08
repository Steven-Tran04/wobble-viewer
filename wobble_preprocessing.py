"""
Image Processing Module for Furniture Assembly Visualization

This module provides a suite of image processing functions designed to prepare
furniture assembly manual images for 3D rendering and animation effects. It leverages
AI-powered image generation and manipulation techniques to clean, color, and
segment images for use in creating interactive 3D models.

Key Features:
- Preprocessing: Removes annotations, labels, and unwanted elements from images
- Realistic Coloring: Applies natural colors to furniture components
- Depth Mapping: Generates depth information for 3D reconstruction
- Greenscreen Generation: Creates masks for background removal
- Background Removal: Produces transparent images with clean object isolation

Main Functions:
- preprocess_image(): Cleans input images by removing text and symbols
- color_image(): Adds realistic coloring to preprocessed images
- depth_map(): Creates depth maps for 3D modeling
- greenscreen(): Generates greenscreen versions for masking
- remove_green_screen(): Removes backgrounds to create transparent PNGs

Usage:
    Run as a script: python wobble_preprocessing.py
    This will process the image through all pipeline steps and save outputs
    to the 'images/' directory.
"""

import replicate
import sys
import os
import numpy as np
from PIL import Image
import cv2

### Preprocess the image ###
def preprocess_image(input_path: str, output_path: str):
    preprocessed_img = replicate.run(
        "google/nano-banana-pro",
        input={
            "prompt": "Remove all annotations, part labels (number or text), zoom-in diagrams, arrows, screwdrivers, wrenches, and symbols. Do not change the position or dimensions of the furniture and its pieces.",
            "resolution": "2K",
            "image_input": [open(input_path, "rb")],
            "aspect_ratio": "match_input_image",
            "output_format": "png",
            "safety_filter_level": "block_only_high",
            "allow_fallback_model": False
        }
    )

    with open(output_path, "wb") as file:
        file.write(preprocessed_img.read())

    print("Preprocessing complete. Saved to:", output_path)


### Realistically color the image ###
def color_image(input_path: str, output_path: str):
    colored_img = replicate.run(
        "google/nano-banana-pro",
        input={
            "prompt": "Do not change the dimensions or the placement of the furniture. Color the image so that it looks realistic. Include a minimalistic background. Make sure all objects are grounded.",
            "resolution": "2K",
            "image_input": [open(input_path, "rb")],
            "aspect_ratio": "match_input_image",
            "output_format": "png",
            "safety_filter_level": "block_only_high",
            "allow_fallback_model": False
        }
    )

    with open(output_path, "wb") as file:
        file.write(colored_img.read())

    print("Coloring complete. Saved to:", output_path)

### Generate depth map from colored image ###
def depth_map(input_path: str, output_path: str):
    depth_img = replicate.run(
        "chenxwh/depth-anything-v2:b239ea33cff32bb7abb5db39ffe9a09c14cbc2894331d1ef66fe096eed88ebd4",
        input={
            "image": open(input_path, "rb"),
            "model_size": "Large"
        }
    )

    with open(output_path, "wb") as f:
        f.write(depth_img['grey_depth'].read())

    print("Depth map generation complete. Saved to:", output_path)


### Generate greenscreen for clean image ###
def greenscreen(input_path: str, output_path: str):
    greenscreen = replicate.run(
        "google/nano-banana-pro",
        input={
            "prompt": "Color ONLY the background neon green. Keep outlines of objects black. Color in all objects white.",
            "resolution": "2K",
            "image_input": [open(input_path, "rb")],
            "aspect_ratio": "match_input_image",
            "output_format": "png",
            "safety_filter_level": "block_only_high",
            "allow_fallback_model": False
        }
    )

    with open(output_path, "wb") as file:
        file.write(greenscreen.read())

    print("Greenscreen generation complete. Saved to:", output_path)

### Remove background from greenscreen image ###
def remove_green_screen(input_path: str, output_path: str,
                        background_path: str = None,
                        fact: float = 1.05,
                        thresh: int = 80,
                        edge_erode: int = 3,
                        edge_blur: int = 5):
    """
    edge_erode: how many pixels to shrink the mask inward (removes green fringe)
    edge_blur:  feathering radius for soft alpha edges (reduces spike artifacts)
    """

    img = np.array(Image.open(input_path).convert("RGBA"))

    gs_mask = img[:, :, 1] < fact * img[:, :, 0]
    gs_mask = np.logical_or(gs_mask, img[:, :, 1] < fact * img[:, :, 2])
    gs_mask = np.logical_or(gs_mask, img[:, :, 1] < thresh)
    bg_mask = ~gs_mask

    # --- Erode the subject mask to eat away green fringe pixels ---
    subject_mask = gs_mask.astype(np.uint8) * 255
    kernel = np.ones((edge_erode, edge_erode), np.uint8)
    subject_mask = cv2.erode(subject_mask, kernel, iterations=1)

    # --- Feather the edges for a soft alpha transition ---
    if edge_blur > 0:
        blurred = cv2.GaussianBlur(subject_mask, (edge_blur * 2 + 1, edge_blur * 2 + 1), 0)
        alpha = blurred
    else:
        alpha = subject_mask

    if not output_path.lower().endswith(".png"):
        output_path = output_path.rsplit(".", 1)[0] + ".png"

    img_out = img.copy()
    img_out[:, :, 3] = alpha  # replace alpha channel with cleaned mask
    Image.fromarray(img_out).save(output_path)
    print(f"Saved masked image: {output_path}")

    if background_path:
        bg = np.array(Image.open(background_path).convert("RGBA"))
        if bg.shape[:2] != img.shape[:2]:
            raise ValueError(
                f"Background image dimensions {bg.shape[:2]} do not match "
                f"input image dimensions {img.shape[:2]}."
            )
        bg_out = bg.copy()
        bg_out[:, :, 3] = alpha
        bg_output_path = output_path.rsplit(".", 1)[0] + "_bg_masked.png"
        Image.fromarray(bg_out).save(bg_output_path)
        print(f"Saved background-masked image: {bg_output_path}")

def remove_green_screen(input_path: str, output_path: str,
                        background_path: str = None,
                        fact: float = 1.05,
                        thresh: int = 80):
    """
    Remove green screen background and make it transparent.
    Optionally, apply the same mask to a different background image.

    Args:
        input_path:      Path to the input (green screen) image.
        output_path:     Path to save the output PNG (must be .png).
        background_path: Optional path to a second image to apply the mask to.
                         Must have the same dimensions as input.
        fact:            How much brighter green must be vs red/blue to be masked.
                         Higher = stricter (less green removed).
        thresh:          Minimum green value to be considered green screen.
                         Lower = stricter (less green removed).
    """

    img = np.array(Image.open(input_path).convert("RGBA"))

    # Green screen mask: True where pixel IS the subject (not green)
    gs_mask = img[:, :, 1] < fact * img[:, :, 0]
    gs_mask = np.logical_or(gs_mask, img[:, :, 1] < fact * img[:, :, 2])
    gs_mask = np.logical_or(gs_mask, img[:, :, 1] < thresh)

    # bg_mask is True where pixels ARE green (background to remove)
    bg_mask = ~gs_mask

    if not output_path.lower().endswith(".png"):
        output_path = output_path.rsplit(".", 1)[0] + ".png"
        print(f"Output renamed to {output_path} (PNG required for transparency)")

    # --- Output 1: original image with green pixels made transparent ---
    img_out = img.copy()
    img_out[bg_mask, 3] = 0
    Image.fromarray(img_out).save(output_path)
    print(f"Saved masked image: {output_path}")

    # --- Output 2: apply the same mask to a different image ---
    if background_path:
        bg = np.array(Image.open(background_path).convert("RGBA"))

        if bg.shape[:2] != img.shape[:2]:
            raise ValueError(
                f"Background image dimensions {bg.shape[:2]} do not match "
                f"input image dimensions {img.shape[:2]}."
            )

        bg_out = bg.copy()
        bg_out[bg_mask, 3] = 0

        bg_output_path = output_path.rsplit(".", 1)[0] + "_bg_masked.png"
        Image.fromarray(bg_out).save(bg_output_path)
        print(f"Saved background-masked image: {bg_output_path}")

# Run on all images in the "images/" directory besides ones already generated by the pipeline
if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("Usage: python wobble_preprocessing.py")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.realpath(__file__))
    images_dir = os.path.join(script_dir, "images")

    exclusions = {
        "preprocessed.png",
        "colored.png",
        "greenscreen.png",
        "cleaned.png",
        "depth.png",
    }
    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}

    for filename in sorted(os.listdir(images_dir)):
        if filename.lower() in exclusions:
            continue

        root, ext = os.path.splitext(filename)
        if ext.lower() not in valid_exts:
            continue

        input_image_path = os.path.join(images_dir, filename)
        preprocessed_path = os.path.join(images_dir, f"{root}_preprocessed.png")
        colored_path = os.path.join(images_dir, f"{root}_colored.png")
        greenscreen_path = os.path.join(images_dir, f"{root}_greenscreen.png")
        cleaned_path = os.path.join(images_dir, f"{root}_cleaned.png")
        depth_path = os.path.join(images_dir, f"{root}_depth.png")

        print(f"Processing image: {filename}")
        preprocess_image(input_image_path, preprocessed_path)
        color_image(preprocessed_path, colored_path)
        greenscreen(preprocessed_path, greenscreen_path)
        remove_green_screen(greenscreen_path, cleaned_path)
        depth_map(colored_path, depth_path)

    print("Batch processing complete.")
