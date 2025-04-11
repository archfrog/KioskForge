#!/usr/bin/env python3
# KioskForge - https://kioskforge.org
# Copyright (c) 2024-2025 Vendsyssel Historiske Museum (me@vhm.dk). All Rights Reserved.
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
# This script invokes MyPy to statically analyze the KioskForge Python source files.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import os
import shutil
import sys

from toolbox.builder import TextBuilder
from toolbox.driver import KioskDriver
from toolbox.errors import KioskError, SyntaxError
from toolbox.invoke import invoke_list
from toolbox.logger import Logger
from toolbox.version import *


class KioskCheck(KioskDriver):
	"""Defines the check.py script, which is responsible for invoking MyPy (portably) to check all Python source files."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)
		self.version = Version("check", VERSION, COMPANY, CONTACT, TESTING)

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Delete two standard arguments that we don't currently use for anything.
		del logger
		del origin

		# Parse command-line arguments.
		if arguments:
			raise SyntaxError('"check.py"')
		del arguments

		# Check that the user has set up the RAMDISK environment variable.
		RAMDISK = os.environ.get("RAMDISK")
		if not RAMDISK:
			raise KioskError("No RAMDISK environment variable found.  Please define it and rerun this script.")

		# Check that all required tools are installed and accessible.
		for tool in ["mypy", "pylint"]:
			if not shutil.which(tool):
				raise KioskError("Unable to locate '%s' in PATH" % tool)

		#*************************** Ask MyPy to statically check all Python source files in the current folder. *****************

		words  = TextBuilder()
		words += "mypy"
		words += "--cache-dir"
		words += RAMDISK + os.sep + PRODUCT + os.sep + "MyPy"
		words += "--strict"
		# NOTE: This option is no longer necessary as PyInstaller-VersionFile has been updated to provide type hints.
		#words += "--follow-untyped-imports"
		words += "KioskForge.py"
		words += "KioskOpenbox.py"
		words += "KioskSetup.py"
		words += "KioskStart.py"
		words += "KioskUpdate.py"
		words += "build.py"
		words += "check.py"

		result = invoke_list(words.list)
		if result.status != 0:
			print(result.output)
			raise KioskError("MyPy failed its static checks")
		del result
		del words

		#************************* Ask pylint to statically check all Python source files in the current folder. *****************

		words  = TextBuilder()
		words += "pylint"
		# TODO: Remove --errors-only option once the errors have been fixed.
		words += "--errors-only"
		words += "KioskForge.py"
		words += "KioskOpenbox.py"
		words += "KioskSetup.py"
		words += "KioskStart.py"
		words += "KioskUpdate.py"
		words += "build.py"
		words += "check.py"
		words += "toolbox"

		result = invoke_list(words.list)
		if result.status != 0:
			print(result.output)
			raise KioskError("Pylint failed its static checks")
		del result
		del words


if __name__ == "__main__":
	app = KioskCheck()
	code = app.main(sys.argv)
	sys.exit(code)

