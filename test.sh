#!/usr/bin/bash
set -e

project=KioskForge
mypy --cache-dir $RAMDISK/$project --strict $project.py
