#!/usr/bin/env python3
# This script checks for incoming `KioskForge-x.yy.zip` and `KioskForge.kiosk` files and installs them if found.  The script is
# run once at every boot and launches the `KioskStart.py` script when the upgrade is complete.

import glob
import os
import sys
from typing import List
import zipfile

from kiosklib.driver import KioskDriver
from kiosklib.errors import KioskError
from kiosklib.invoke import invoke_text_safe
from kiosklib.logger import Logger

class KioskUpgrade(KioskDriver):
	"""The KioskForge self-upgrade tool, which run as the very first step and then transfers control to KioskStart.py."""

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		del arguments
		del origin

		# Search for upgrade candidates.
		files = list(glob.glob("/home/kiosk/KioskForge*.zip"))
		if len(files) > 1:
			raise KioskError("Multiple KioskForge upgrade files detected")

		if files:
			source = files[0]

			logger.write("Upgrading KioskForge...")

			# Remove the /home/kiosk/KioskForge.new folder, if it exists.
			invoke_text_safe("rm -fr /home/kiosk/KioskForge.new")

			# Unpack the new version of KioskForge to /home/kiosk/KioskForge.new.
			os.makedirs("/home/kiosk/KioskForge.new", 0o766, exist_ok=False)
			with zipfile.ZipFile(source, "r") as archive:
				archive.extractall(path="/home/kiosk/KioskForge.new")

			# Remove the folder KioskForge.old, whether or not it exists.
			invoke_text_safe("rm -fr /home/kiosk/KioskForge.old")

			# Rename the folder KioskForge folder to KioskForge.old.
			os.rename("/home/kiosk/KioskForge", "/home/kiosk/KioskForge.old")

			# Rename the folder KioskForge.new to KioskForge.
			os.rename("/home/kiosk/KioskForge.new", "/home/kiosk/KioskForge")

			# Make all KioskForge scripts executable.
			for target in glob.glob("/home/kiosk/KioskForge/*.py"):
				invoke_text_safe("chmod u+x " + target)

			# Copy over the .kiosk file from the current kiosk to the new kiosk.
			# TODO: Eliminate this step by moving the .kiosk file to /home/kiosk.
			invoke_text_safe("cp -p /home/kiosk/KioskForge.old/KioskForge.kiosk /home/kiosk/KioskForge")

			# TODO: Attempt to upgrade the .kiosk file using the new version of KioskForge (what happens if this fails?).
			# TODO: The KioskForge 'upgrade' command MUST handle new and renamed options silently.

			# Remove the upgrade archive so we don't process it again on the next boot.
			os.unlink(source)
			del source

			logger.write("KioskForge successfully upgraded")

		# The new KioskForge has been installed, launch KioskStart.py so that it replaces this process.
		# NOTE: The execX() requires the name of the command as the first argument so it requires the command name twice.
		script = "/home/kiosk/KioskForge/KioskStart.py"
		os.execl(script, script)

if __name__ == "__main__":
	sys.exit(KioskUpgrade().main(sys.argv))
