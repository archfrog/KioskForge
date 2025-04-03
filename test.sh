#!/usr/bin/bash
set -e

if [ -z "$RAMDISK" ]; then
	echo Error: RAMDISK environment variable not defined
	exit 1
fi

project=KioskForge
mypy --cache-dir $RAMDISK/$project --strict KioskForge.py KioskOpenbox.py KioskSetup.py KioskStartX11.py KioskUpdate.py

