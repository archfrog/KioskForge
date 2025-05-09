#!/usr/bin/env python3
# KioskForge - https://kioskforge.org
# Copyright (c) 2024-2025 Vendsyssel Historiske Museum (me@vhm.dk). All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following
# conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, this list of conditions and the disclaimer below.
#     * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided with the distribution.
#     * Neither the name of Vendsyssel Historiske Museum nor the names of its contributors may be used to endorse or promote
#       products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# This script prepares a ZIP archive with various redacted kiosk and log files that can be sent off to the KioskForge authors.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import os
import platform
import sys
import zipfile

from toolbox.driver import KioskDriver
from toolbox.errors import CommandError, KioskError
from toolbox.logger import Logger
from toolbox.invoke import invoke_text
from toolbox.setup import Setup
from toolbox.version import Version


def strip_and_unhide(path : str) -> str:
	"""Strips the path and removes any leading dots from the specified path."""
	path = os.path.basename(path)
	while path[0] == '.':
		path = path[1:]
	return path


class KioskZipper(KioskDriver):
	"""This class contains the 'KioskZipper' code, which prepares a ZIP file containing various logs useful for debugging."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)
		self.version = Version(self.project)

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Output copyright information, etc.
		print(self.version.banner())
		print()

		# Check that we're running on Linux.
		if platform.system() != "Linux":
			raise KioskError("This script can currently only be run on a Linux machine")

		# Check that we're running on a KioskForge kiosk machine.
		if not os.path.isdir("KioskForge") or not os.path.isfile("KioskForge/KioskForge.kiosk"):
			raise KioskError("This script can only be run on a KioskForge kiosk machine")

		# Parse command-line arguments.
		if len(arguments) != 0:
			raise CommandError('"KioskZipper.py"')

		# Create list of files that we want to include in the ZIP archive.
		include = [".xsession-errors", ".local/share/xorg/Xorg.0.log"]

		# Create the list of files to be removed before the script exits.
		cleanup = []

		# Use try-finally to delete the files that need to be removed.
		try:
			# Load the configuration, so that we can redact the sensitive/irrelevant information out of it.
			filename = "Kiosk.kiosk"
			setup = Setup()
			setup.load_safe(logger, "KioskForge/KioskForge.kiosk")
			for field in ["user_name", "user_code", "wifi_name", "wifi_code", "ssh_key"]:
				setup.assign(field, "REDACTED")
			setup.save(filename, self.version)
			include.append(filename)
			cleanup.append(filename)
			del field
			del filename

			# Create journalctl-kiosk-events.log by extracting kiosk-related information from journalctl.
			filename = "journalctl-kiosk-events.log"
			# NOTE: journalctl's -g and -u options are next to useless as we want everything related to
			# NOTE: KioskForge and its sibling scripts, not just everything relating to the systemd unit.
			# NOTE: The -g (grep) option only returns a subset of the syslog entries we want to save.
			result = invoke_text("journalctl -o short-iso")
			if result.status != 0:
				raise KioskError("Unable to query system log for kiosk-related events")
			#... Filter out irrelevant lines.
			lines = list(result.output.split(os.linesep))
			lines = list(filter(lambda x: "Kiosk" in x, lines))
			found = os.linesep.join(lines)
			with open(filename, "wt", encoding="utf-8") as stream:
				stream.write(found)
			include.append(filename)
			cleanup.append(filename)
			del lines
			del found
			del filename

			# Discard non-existent files from the list of files to ZIP.
			include = list(filter(os.path.isfile, include))

			# Zip up the existing files.
			filename = "kiosklogs.zip"
			print(f"Creating archive: {filename}")
			with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zipper:
				for file in include:
					name = strip_and_unhide(file)
					print(f"... Adding: {file} as {name}")
					zipper.write(file, name)
				del file
				del name
			print()
			del filename

			# Report success.
			print("Kiosk log archive created successfully - please attach it to your bug report.")
		finally:
			# Remove temporary files not of any use to the kiosk itself.
			for file in cleanup:
				if os.path.isfile(file):
					os.unlink(file)

if __name__ == "__main__":
	sys.exit(KioskZipper().main(sys.argv))
