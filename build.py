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
# This script is responsible for building a stand-alone .exe file (KioskForge.exe) using PyInstaller.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import glob
import os
import platform
import shutil
import sys
import time

import pyinstaller_versionfile

from toolbox.builder import TextBuilder
from toolbox.driver import KioskDriver
from toolbox.errors import *
from toolbox.invoke import invoke_list_safe
from toolbox.logger import Logger
from toolbox.setup import *
from toolbox.version import *


# Delete all items IN the specified folder, without removing or altering the folder itself.
def folder_delete_contents(path : str) -> None:
	for item in glob.glob(path + os.sep + "*"):
		if os.path.isdir(item):
			shutil.rmtree(item)
		else:
			os.unlink(item)


class KioskBuild(KioskDriver):
	"""Defines the build.py script, which is responsible for building a platform-dependent executable using PyInstaller."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)
		self.version = Version("build", VERSION, COMPANY, CONTACT, TESTING)

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Parse command-line arguments.
		clean = False
		if len(arguments) >= 1 and arguments[0] == "--clean":
			clean = True
		elif len(arguments) != 0:
			raise SyntaxError('"build.py" [--clean]')

		RAMDISK = os.environ.get("RAMDISK")
		if not RAMDISK:
			raise KioskError("No RAMDISK environment variable found.  Please define it and rerun this script.")

		rootpath = RAMDISK + os.sep + "KioskForge"
		distpath = rootpath + os.sep + "Inno Setup"
		os.makedirs(distpath, mode=0o664, exist_ok=True)
		workpath = rootpath + os.sep + "PyInstaller"
		os.makedirs(workpath, mode=0o664, exist_ok=True)

		# Write 'version.txt' needed to fill out the details that can be viewed in Windows Explorer.
		pyinstaller_versionfile.create_versionfile(
			output_file=rootpath + os.sep + "version.txt",
			version=VERSION,
			company_name=COMPANY,
			file_description="Tool to forge a complete Linux kiosk machine from scratch.",
			internal_name=PRODUCT,
			legal_copyright="Copyright © " + COMPANY + ". All Rights Reserved.",
			original_filename=PRODUCT + ".exe",
			product_name=PRODUCT,
			#translations=[1033, 437]			# TODO: 65001]
		)

		# Build the (pretty long) command line for PyInstaller.
		words  = TextBuilder()
		words += "pyinstaller"

		if False:
			words += "--debug"
			words += "all"

		if clean:
			words += "--clean"

		words += "--console"
		words += "--noupx"
		words += "--onefile"

		words += "--distpath"
		words += distpath

		words += "--workpath"
		words += workpath

		words += "--upx-exclude"
		words += "python3.dll"

		words += "--icon"
		words += "../pic/logo.ico"

		words += "--version-file"
		words += rootpath + os.sep + "version.txt"

		for item in ["KioskForge.py", "KioskOpenbox.py", "KioskSetup.py", "KioskStartX11.py", "KioskUpdate.py", "toolbox"]:
			words += "--add-data"
			if os.path.isfile(item):
				words += item + ":."
			else:
				words += item + ":" + item

		words += "KioskForge.py"

		invoke_list_safe(words.list)


if __name__ == "__main__":
	app = KioskBuild()
	code = app.main(sys.argv)
	sys.exit(code)

