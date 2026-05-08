# Wobble Viewer

This directory contains the image processing and Blender automation pipeline for the `wobble` feature in the Wayfair Studio webapp.

## ⚠️ Development Note

This implementation is **not yet integrated into the backend** of the webapp. Currently:

- Images are processed from the local `wobble/images/` directory, not from the database
- Generated GLB files are stored locally, which would consume significant storage if scaled to production

**For backend integration**, the following approach is recommended:

1. Store the final cleaned and depth images for each assembly step in the database
2. Modify `blender.py` to fetch these images directly from the database instead of the local filesystem
3. Stream or generate GLB files on-demand to avoid excessive storage overhead

**Performance Note:** Blender is able to generate 3D meshes quickly from the cleaned image and depth map using the zForm addon. This means users will not have to wait long for the mesh to be constructed, enabling responsive real-time visualization in the webapp.

## Contents

- `wobble.py` - Batch image processing script that uses `replicate`, `numpy`, `Pillow`, and `OpenCV`.
- `blender.py` - Blender automation script that imports `bpy`, loads processed images, applies depth mapping, and exports a GLB.
- `config.py` - legacy configuration file (not required when using `BLENDER_PATH`).
- `run_all.sh` - Shell wrapper that starts `wobble.py` and `blender.py` in parallel.
- `requirements.txt` - Python dependency list for the image pipeline.

## Requirements

- Python 3.10+ (or compatible Python 3 environment)
- Blender installed on your system
- Blender `zForm` addon installed and available to Blender
- A valid `replicate` account / API key if the `replicate` library is used

## Setup

1. Create a Python virtual environment:

```bash
python3 -m venv venv
```

2. Activate the virtual environment:

```bash
source venv/bin/activate
```

3. Upgrade pip and install the required Python libraries from `requirements.txt`:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Create the required directories:

```bash
mkdir -p images meshes
```

## Install Blender zForm Addon

The `blender.py` script requires the zForm addon for Blender. Download and install it from:

**https://superhivemarket.com/products/zform**

Follow the installation instructions provided on that page to add the addon to your Blender installation.

## Configure Blender Path

Set the `BLENDER_PATH` environment variable before running the scripts.

- macOS / Linux:
  ```bash
  export BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"
  ```
- Windows PowerShell:
  ```powershell
  $env:BLENDER_PATH = "C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
  ```
- Windows CMD:
  ```cmd
  set BLENDER_PATH="C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
  ```

## How to Run

### Run the image pipeline only

This script processes all eligible images in the `images/` folder, excluding files named:

- `preprocessed.png`
- `colored.png`
- `greenscreen.png`
- `cleaned.png`
- `depth.png`

Run the image pipeline with:

```bash
python wobble.py
```

### Run Blender automation

Because `blender.py` depends on Blender's `bpy` module, run it from Blender like this:

```bash
$BLENDER_PATH -b -P blender.py
```

Make sure `BLENDER_PATH` is set to your Blender executable path.

### Run the full pipeline using `run_all.sh`

`run_all.sh` is intended to run the image pipeline and Blender in succession.

```bash
chmod +x run_all.sh
./run_all.sh
```

> Note: `run_all.sh` uses the `BLENDER_PATH` environment variable. If it does not work in your shell, make sure the variable is exported correctly and the path points to your Blender executable.

## Notes

- Add your raw input images to the `images/` directory.
- The script will create processed outputs alongside input files using suffixes like `_preprocessed.png`, `_colored.png`, `_greenscreen.png`, `_cleaned.png`, and `_depth.png`.
- `blender.py` exports a final `full_scene_export.glb` file in the `meshes/` directory.
