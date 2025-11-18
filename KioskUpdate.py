#!/usr/bin/env python3
#**********************************************************************************************************************************
# BSD 3-Clause License for KioskForge - https://kioskforge.org:
#
# Copyright © 2024-2025 The KioskForge Team.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#**********************************************************************************************************************************

# This script is responsible for updating, upgrading, and cleaning the system (only if there is an active internet connection).

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import glob
import os
import sys
import time

from kiosklib.actions import AptAction
from kiosklib.driver import KioskDriver
from kiosklib.errors import CommandError, KioskError
from kiosklib.invoke import invoke_text, invoke_text_safe
from kiosklib.kiosk import Kiosk
from kiosklib.logger import Logger
from kiosklib.network import internet_active
from kiosklib.signal import Signal


class KioskUpdate(KioskDriver):
	"""This class implements the KioskUpdate.py script, which updates the system if and only if it is on the internet."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)

	def snap_cleanup(self, logger : Logger) -> None:
		"""Removes all revisions of snaps to keep disk usage to the bare minimum."""
		result = invoke_text("snap list --all --color=never --unicode=never")
		if result.status != 0:
			raise KioskError("Unable to get list of all snaps in system")

		# Split the output of 'snap list --all' into lines
		lines = result.output.strip().split(os.linesep)
		del result

		# Parse each line into six fields and remove all revisions of disabled snaps.
		# NOTE: Logic borrowed from https://www.debugpoint.com/clean-up-snap/
		for line in lines[1:]:
			(name, version, revision, tracking, publisher, notes) = line.split()
			del version
			del tracking
			del publisher

			# The 'notes' field is a comma-separated list of flags, parse them.
			flags = notes.split(",")
			del notes

			# We're only interested in disabled snaps - the rest are used by the system.
			if "disabled" not in flags:
				logger.write(f"Skipping active snap {name} revision {revision}.")
				continue

			# Remove the old revision of the current snap.
			logger.write(f"Removing snap {name} revision {revision}.")
			invoke_text_safe(f'snap remove "{name}" --revision="{revision}"')

		# Empty the snapd cache as this may grow to MANY gigabytes over time.
		for file in glob.glob("/var/lib/snapd/cache/*"):
			if os.path.isfile(file):
				logger.write(f"Removing snapd cache item {os.path.basename(file)}.")
				os.unlink(file)

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Check that we're running on Linux.
		if sys.platform != "linux":
			raise KioskError("This script can only be run on a Linux kiosk machine")

		# Check that we've got root privileges.
		# pylint: disable-next=no-member
		if os.geteuid() != 0:			# pyrefly: ignore[missing-attribute]
			raise KioskError("You must be root (use 'sudo') to run this script")

		# Parse command-line arguments.
		initial = False
		if len(arguments) > 1:
			raise CommandError('"KioskUpdate.py" [--initial]')
		if len(arguments) == 1:
			# 'KioskSetup.py' invokes this script with the '--initial' option to disable the signal synchronization code.
			if arguments[0] != "--initial":
				raise KioskError("Invalid argument: " + arguments[0])
			initial = True

		logger.write("Kiosk updater starting.")

		# Load settings generated by KioskForge on the desktop machine.
		kiosk = Kiosk(self.version)
		kiosk.load_safe(logger, origin + os.sep + "KioskForge.kiosk")

		# Vacuum system logs every time we maintain the system if a maximum log size has been specified.
		if kiosk.vacuum_size.data != 0:
			invoke_text_safe(f"/usr/bin/journalctl --vacuum-size={kiosk.vacuum_size.data}M")

		# Not all kiosks are online so we need to handle the case that there's no internet gracefully.
		if internet_active():
			# Don't execute the code below if this script was invoked from the 'KioskSetup.py' script (to increase code sharing).
			if not initial:
				# Stop Chromium and automatic respawns of it by creating a signal, which is watched for by 'KioskOpenbox.py'.
				signal = Signal("KioskOpenbox-shutdown-Chromium", "kiosk")
				signal.create()
				logger.write("Signaled KioskOpenbox.py to shut down Chromium and then exit.")

				# Wait for KioskOpenbox.py to shut down, which means waiting until the signal has been removed.
				while signal.exists:
					time.sleep(1)
				logger.write("KioskOpenbox.py has shut down Chromium and exited.")
				del signal

				# NOTE: We don't start Chromium using 'snap run chromium', so don't use 'snap stop chromium'.
				# invoke_text_safe("snap stop chromium")

				# Stop X11 using "killall", the only way we have (we cannot kill the Python interpreter running this script...).
				invoke_text_safe("killall Xorg")

			# Ask snap to upgrade (refresh) all snaps.
			logger.write("Upgrading all snaps.")
			invoke_text_safe("snap refresh")

			# Try to uninstall cups in case it got installed again by a refresh of the Chromium snap.
			# NOTE: We simply ignore the return value, an instance of 'Result', as we're happy whether it fails or it succeeds.
			logger.write("Purging Common Unix Printing System (CUPS) installed when Chromium is installed or upgraded.")
			invoke_text("snap remove --purge cups")

			# Remove all disabled snaps (prior snap versions) and empty the snap cache.
			logger.write("Removing outdated snaps and clearing the snap cache.")
			self.snap_cleanup(logger)

			# Keep track of failures.
			failed = False

			# Purge all unused packages.
			# NOTE: We purge unused packages PRIOR to updating to ensure we've rebooted before doing this so as to not accidentally
			# NOTE: purge a running kernel, which may have catastrophic consequences as far as I know.
			# NOTE: Using 'AptAction' to get automatic waiting for the 'apt' lock file to be released.
			logger.write("Purging all unused packages.")
			result = AptAction("Purging all unused packages.", "apt-get autoremove --purge").execute()
			if result.status != 0:
				logger.error("Unable to purge all unused packages.")
				failed = True
			del result

			# Update all package lists.
			logger.write("Updating package lists.")
			result = AptAction("Updating package lists.", "apt-get update").execute()
			if result.status != 0:
				logger.error("Unable to update package lists.")
				failed = True
			del result

			# Upgrade all packages.
			# NOTE: Use "apt upgrade -y", not "apt-get dist-upgrade -y", to ensure that the system doesn't suddenly break down.
			# NOTE: Use "apt upgrade -y", not "apt-get upgrade -y", because "apt-get" doesn't install new packages (incl. kernels).
			logger.write("Upgrading all packages.")
			result = AptAction("Upgrading all packages.", "apt upgrade -y").execute()
			if result.status != 0:
				logger.error("Unable to upgrade all packages.")
				failed = True
			del result

			# Clean the apt cache (which may grow to many gigabytes in size).
			logger.write("Cleaning the package cache.")
			result = AptAction("Cleaning the package cache.", "apt-get clean").execute()
			if result.status != 0:
				logger.error("Unable to clean package cache.")
				failed = True
			del result

			if not failed:
				logger.write("Successfully vacuumed, purged, updated, upgraded, and cleaned all packages and all snaps.")
			else:
				logger.write("Unable to purge, vacuum, update, upgrade, and clean system.")

		logger.write("Kiosk updater stopping.")

		# Execute the requested post-upgrade action (only if not invoked from 'KioskSetup.py').
		if not initial:
			match kiosk.upgrade_post.data:
				case "reboot":
					invoke_text_safe("reboot")
				case "poweroff":
					invoke_text_safe("poweroff")
				case _:
					raise KioskError(f"Invalid value in 'upgrade_post' option: {kiosk.upgrade_post.data}")


if __name__ == "__main__":
	sys.exit(KioskUpdate().main(sys.argv))
