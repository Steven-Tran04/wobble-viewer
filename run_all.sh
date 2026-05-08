#!/bin/zsh

python3 wobble_preprocessing.py

"$BLENDER_PATH" -b -P blender.py
