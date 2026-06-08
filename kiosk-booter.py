#!/usr/bin/env python3
# This script runs at every boot and checks for the presence of 'KioskForge.zip' and 'Application.zip' in these places:
#
# 1. /home/kiosk    (This is for quickly upgrading a kiosk using the OpenSSH scp command.)
# 2. /boot/firmware (The FAT32 partition created by Raspberry Pi Imager during preparation of the installation medium.)
# 3. /dev/sd?1      (These are mounted in turn, checked, possibly used, and then unmounted again.)
#
# If either archive is found, it is unzipped, by this script (not InfoZip), to the apppropriate target location in /home/kiosk.
#
# NOTE:
# This may only use the standard Python library.  It cannot use any kiosk library functions as it runs before KioskForge has been
# installed.  Also, it is intended to remain fairly stable once it is completed so no external dependencies whatsoever.

import glob
import os
from pathlib import Path
import subprocess
import sys
from typing import List
import zipfile


class BooterError(Exception):
	"""Local exception instance used to avoid using Exception directly."""


def glob_unique(folders : List[str], pattern : str) -> str:
	"""Finds at most one occurence of the glob pattern 'pattern' in the list of folders.  Fails if multiple files were found."""
	result = []

	# Scan through all folders and find as many occurences of pattern as we can.
	for folder in folders:
		result += glob.glob(folder + os.sep + pattern)

	# Raise an exception if more than one occurence found.
	if len(result) > 1:
		raise BooterError(f"Multiple files matching '{pattern}' found")

	return result[0] if len(result) == 1 else ""


class KioskBooter:
	"""The implementation of the kiosk booter script.  It installs any upgrades and then launches the specified script."""

	def main(self, arguments : List[str]) -> int:
		# Assume failure to simplify the exception handlers below.
		status = 1

		mounted = []
		try:
			# Mount source USB storage devices, if any.
			sources = glob.glob("/dev/sd[a-z]1")
			for source in sources:
				# If not a block device, ignore it.
				path = Path(source)
				if not path.is_block_device():
					continue
				del path

				# Create mount point in /media.
				basename = os.path.basename(source)
				target = "/media/" + basename
				# We need to read, delete, and glob so permission 0o700 it is.
				os.makedirs(target, mode=0o700, exist_ok=False)
				del basename

				# Try to mount storage device.
				result = subprocess.run(["/usr/bin/mount", source, target], check=False)
				del source

				# Ignore the drive if it fails to mount: It may be the /boot/firmware partition on an USB key.
				if result.returncode != 0:
					del target
					continue

				# Ensure the device is unmounted in the finally clause.
				mounted.append(target)
				del target
			del sources

			# The list of glob patterns of where to search for archives.  Please notice that all USB keys are mounted above.
			patterns = [
				"/home/kiosk",
				"/boot/firmware",
				# NOTE: We currently only look at the first partition (/dev/sdX1).  This is intentional to avoid pulling in files
				# NOTE: from all sorts of bizarre partitions and to ensure this sequence of checks is done fairly fast.
				"/media/sd[a-z]1"
			]

			# Expand the list of patterns into a list of concrete folder names, if any.
			locations = []
			for pattern in patterns:
				locations += list(sorted(glob.glob(pattern)))
			# NOTE: Don't sort the entire list as we want to keep the input search order.

			# Find at most one "firmware" (KioskForge) archive (glob_unique raises an exception if multiple files are matched).
			firmware = glob_unique(locations, "KioskForge*.zip")
			if firmware:
				self.unzip_safely_and_delete(firmware, "/home/kiosk/KioskForge")

				# Copy the .kiosk file from the outdated kiosk, if any, to the new kiosk.
				if os.path.isdir("/home/kiosk/KioskForge.old"):
					subprocess.run(["cp", "-p", "/home/kiosk/KioskForge.old/KioskForge.kiosk", "/home/kiosk/KioskForge"], check=True)
			del firmware

			# Find at most one "software" (Application) archive (glob_unique raises an exception if multiple files are matched).
			software = glob_unique(locations, "Application.zip")
			if software:
				self.unzip_safely_and_delete(software, "/home/kiosk/Application")
			del software

			# Find at most one "settings" (KioskForge.kiosk) file (glob_unique raises an exception if multiple files are matched).
			settings = glob_unique(locations, "KioskForge.kiosk")
			if settings:
				subprocess.run(["cp", "-p", settings, "/home/kiosk/KioskForge"], check=True)
				os.unlink(settings)
			del settings

			# Signal success to the caller.
			status = 0
		except Exception as that:			# pylint: disable=broad-exception-caught
			print("Error: " + str(that))
			with open("/home/kiosk/kiosk-booter.err", "wt", encoding="utf-8") as stream:
				stream.write("Error: " + str(that))
		finally:
			# Unmount all mounted drives.
			for mount in mounted:
				subprocess.run(["/usr/bin/umount", mount], check=True)
				os.rmdir(mount)

		del mounted

		# Signal that we're done upgrading the kiosk and the application.  ~kiosk/.bash_login waits for the presence of this file.
		flag = "/home/kiosk/.signals/kiosk-booter-finish.flag"
		Path(flag + ".new").touch()
		subprocess.run(["/usr/bin/chown", "kiosk:kiosk", flag + ".new"], check=True)
		subprocess.run(["/usr/bin/mv", flag + ".new", flag], check=True)

		# Chain to the specified script so that it replaces this Python process in memory (i.e., never returns).
		if len(arguments) >= 2:
			command = arguments[1]
			os.execv(command, [command] + arguments[2:])

		return status

	def unzip_safely_and_delete(self, source_archive : str, target_folder : str) -> None:
		try:
			# Create the target folder.
			os.makedirs(target_folder + ".new", 0o766, exist_ok=False)

			# Unpack the archive to the specified target folder.
			with zipfile.ZipFile(source_archive, "r") as archive:
				archive.extractall(path=target_folder + ".new")

			# Fix Windows Explorer archives where the archive name is typically used as the topmost folder in the zip file.
			# NOTE: Such archives are made by right-clicking a folder and selecting "Send to Compressed (zipped) folder".
			basename = os.path.basename(target_folder)
			if os.path.isdir(target_folder + ".new" + os.sep + basename):
				# Move Archive.new/Archive to Archive.tmp.
				subprocess.run(["/usr/bin/mv", target_folder + ".new" + os.sep + basename, target_folder + ".tmp"], check=True)
				# Remove the Archive.new folder, which we don't need anymore (use "rm -fr" to handle possible extraneous files).
				subprocess.run(["/usr/bin/rm", "-fr", target_folder + ".new"], check=True)
				# Rename Archive.tmp to Archive.new before continuing as if nothing had happened.
				subprocess.run(["/usr/bin/mv", target_folder + ".tmp", target_folder + ".new"], check=True)
			del basename

			# Set ownership of all new files to kiosk:kiosk (we're running as root).
			subprocess.run(["/usr/bin/chown", "-R", "kiosk:kiosk", target_folder + ".new"], check=True)

			# Make all files in the target folder executable.
			# (KioskForge: We use most of them.  Application: We don't know what scripts/binaries the application uses.)
			subprocess.run(["/usr/bin/chmod", "-R", "u+x", target_folder + ".new"], check=True)

			# Remove the folder KioskForge.old, whether or not it exists.
			subprocess.run(["/usr/bin/rm", "-fr", target_folder + ".old"], check=True)

			# Rename the target folder to .old.
			if os.path.exists(target_folder):
				os.rename(target_folder, target_folder + ".old")

			# Rename the .new folder to the target folder.
			os.rename(target_folder + ".new", target_folder)

			# Remove the source archive so we don't process it again on the next boot.
			subprocess.run(["/usr/bin/rm", "-f", source_archive], check=True)

		finally:
			# Clean up any leftovers in case an exception occured.
			subprocess.run(["/usr/bin/rm", "-fr", target_folder + ".new"], check=True)


if __name__ == "__main__":
	sys.exit(KioskBooter().main(sys.argv))
