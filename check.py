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

# This script invokes MyPy to statically analyze the KioskForge Python source files.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import os
import shutil
import sys

from kiosklib.builder import TextBuilder
from kiosklib.driver import KioskDriver
from kiosklib.errors import CommandError, KioskError
from kiosklib.invoke import invoke_list
from kiosklib.logger import Logger
from kiosklib.sources import SOURCES
from kiosklib.various import ramdisk_get


def which(name : str) -> str:
	found = shutil.which(name)
	if not found:
		raise KioskError(f"Cannot find program '{name}' in PATH")
	return found


class KioskCheck(KioskDriver):
	"""Defines the check.py script, which is responsible for invoking MyPy (portably) to check all Python source files."""

	def __init__(self) -> None:
		KioskDriver.__init__(self, "check")

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Delete two standard arguments that we don't currently use for anything.
		del logger
		del origin

		sources = SOURCES + ["build.py", "check.py"]

		# Parse command-line arguments.
		if arguments:
			raise CommandError('"check.py"')
		del arguments

		# Check that all required tools are installed and accessible.
		for tool in ["mypy", "pylint", "pyrefly"]:
			if not shutil.which(tool):
				raise KioskError(f"Unable to locate '{tool}' in PATH")

		# Check that the user has set up the RAMDISK environment variable and make sure it is normalized while we're at it.
		ramdisk = ramdisk_get()

		#***** Ask MyPy to statically check all Python source files in the current folder and in the 'kiosklib' folder. ***********
		words  = TextBuilder()
		words += which("mypy")
		words += "--cache-dir"
		words += ramdisk + self.version.product + os.sep + "MyPy"
		words += "--strict"
		for source in sources:
			words += source

		result = invoke_list(words.list)
		if result.status != 0:
			print("MyPy messages:")
			print()
			print(result.output)
			raise KioskError("MyPy failed its static checks")
		del result
		del words

		#************************* Ask pylint to statically check all Python source files in the current folder. *****************
		words  = TextBuilder()
		words += which("pylint")
		words += "-j"
		words += "0"

		for word in sources:
			words += word

		# Create PYLINTHOME environment variable as this seems the only way to move the pylint persistent data to my RAM disk.
		# A command-line option to specify the persistent directory path would have been pretty nifty.
		# NOTE: Yes, I do prefer that my tools' persistent files are rebuilt once in a while (whenever I reboot).
		environment = os.environ | {"PYLINTHOME" : ramdisk + self.version.product + os.sep + "pylint"}

		result = invoke_list(words.list, environment)
		output = result.output.strip()
		if output:
			print("pylint messages:")
			print()
			print(output)
		del output
		# If any fatal errors (1) or any errors (2), fail the 'check.py' script entirely.
		if result.status & 3:
			raise KioskError("Pylint failed its static checks")
		del environment
		del result
		del words

		#************************* Ask Pyrefly to statically check all files in the current folder tree. *************************
		if False:
			# NOTE: Pyrefly is disabled for now: It has virtually no value to me and reports numerous errors on code I need.
			words  = TextBuilder()
			words += which("pyrefly")
			words += "check"

			result = invoke_list(words.list)
			if result.status != 0:
				print("Pyrefly message:")
				print()
				print(result.output)
				raise KioskError("Pyrefly failed its static checks")
			del result
			del words


if __name__ == "__main__":
	sys.exit(KioskCheck().main(sys.argv))
