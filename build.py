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
# This script builds an installer file (KioskForge-x.yy-Setup.exe) using "Inno Setup" and publishes it on the web.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import glob
import os
import shutil
import sys

import pyinstaller_versionfile

from toolbox.builder import TextBuilder
from toolbox.driver import KioskDriver
from toolbox.errors import CommandError, KioskError
from toolbox.invoke import invoke_list_safe
from toolbox.logger import Logger
from toolbox.various import ramdisk_get
from toolbox.version import Version


# Delete all items IN the specified folder, without removing or altering the folder itself.
def folder_delete_contents(path : str) -> None:
	for item in glob.glob(path + os.sep + "*"):
		if os.path.isdir(item):
			shutil.rmtree(item)
		else:
			os.unlink(item)


class Settings:
	"""Used parse and query the command-line options given to the script when invoked."""

	def __init__(self) -> None:
		self.__clean = False
		self.__debug = False
		self.__ship = False

	@property
	def clean(self) -> bool:
		return self.__clean

	@property
	def debug(self) -> bool:
		return self.__debug

	@property
	def ship(self) -> bool:
		return self.__ship

	def parse(self, arguments : List[str]) -> None:
		for argument in arguments:
			if argument == "--clean":
				self.__clean = True
			elif argument == "--debug":
				self.__debug = True
			elif argument == "--ship":
				self.__ship = True
			else:
				raise CommandError('"build.py" [--clean] [--debug] [--ship]')


class KioskBuild(KioskDriver):
	"""Defines the build.py script, which is responsible for building a platform-dependent executable using PyInstaller."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)
		self.version = Version("build")

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Delete two standard arguments that we don't currently use for anything.
		del logger
		del origin

		# Parse command-line arguments.
		settings = Settings()
		settings.parse(arguments)

		# Check that all required tools are installed and accessible.
		for tool in ["git", "pyinstaller", "pandoc"]:
			if not shutil.which(tool):
				raise KioskError(f"Unable to locate '{tool}' in PATH")

		# Check that Inno Setup v6.x is in its expected location.
		if sys.platform == "win32":
			innopath = r"c:\Program Files (x86)\Inno Setup 6\Compil32.exe"
			if not os.path.isfile(innopath):
				raise KioskError("Cannot find Inno Setup 6 (Compil32.exe) on this PC")

		# Check that the user has set up the RAMDISK environment variable and make sure it is normalized while we're at it.
		ramdisk = ramdisk_get()

		#************************** Set up paths and clean out distribution path *************************************************

		rootpath = ramdisk + "KioskForge"
		distpath = "../tmp"
		os.makedirs(distpath, mode=0o664, exist_ok=True)
		workpath = rootpath + os.sep + "PyInstaller"
		os.makedirs(workpath, mode=0o664, exist_ok=True)

		# Make sure we don't accidentally ship artifacts from earlier builds.
		folder_delete_contents(distpath)

		#*************************** Ask MyPy and pylint if the product is ready for distribution ********************************

		# NOTE: Check.py fails if MyPy or pylint reports ERRORS, not if pylint only reports warnings.
		words  = TextBuilder()
		words += "python"
		words += "check.py"
		invoke_list_safe(words.list)

		#*************************** Make a Git release tag for the target version ***********************************************

		if settings.ship:
			words  = TextBuilder()
			words += "git"
			words += "tag"
			words += "-a"
			words += self.version.version
			words += "-m"
			words += "Release v" + self.version.version + "."
			invoke_list_safe(words.list)

		#************************** Create 'version.txt' (consumed by PyInstaller) ***********************************************

		# Write 'version.txt' needed to fill out the details that can be viewed in Windows Explorer.
		pyinstaller_versionfile.create_versionfile(
			output_file=rootpath + os.sep + "version.txt",
			version=self.version.version,
			company_name=self.version.company,
			file_description="Tool to forge a complete Linux kiosk machine from scratch.",
			internal_name=self.version.product,
			legal_copyright="Copyright © " + self.version.company + ". All Rights Reserved.",
			original_filename=self.version.product + ".exe",
			product_name=self.version.product,
			#translations=[1033, 437]			# TODO: 65001]
		)

		#************************** Create 'KioskForge.exe' (created by PyInstaller, consumed by Inno Setup 6+) ******************

		# Build the (pretty long) command line for PyInstaller.
		words  = TextBuilder()
		words += "pyinstaller"

		if settings.debug:
			words += "--debug"
			words += "all"

		if settings.clean:
			words += "--clean"

		words += "--console"
		words += "--noupx"
		words += "--onefile"

		words += "--distpath"
		words += distpath

		words += "--workpath"
		words += workpath

		# NOTE: The --specpath option also affects the default location of data files, something I think is pretty bizarre.
		if False:
			words += "--specpath"
			words += distpath

		words += "--upx-exclude"
		words += "python3.dll"

		words += "--icon"
		words += "../pic/logo.ico"

		words += "--version-file"
		words += rootpath + os.sep + "version.txt"

		for item in ["KioskForge.py", "KioskOpenbox.py", "KioskSetup.py", "KioskStart.py", "KioskUpdate.py", "toolbox"]:
			words += "--add-data"
			if os.path.isfile(item):
				words += item + ":."
			else:
				words += item + ":" + item

		words += "KioskForge.py"

		invoke_list_safe(words.list)

		# Remove the 'KioskForge.spec' file as it is automatically re-generated whenever PyInstaller is invoked.
		if os.path.isfile("KioskForge.spec"):
			os.unlink("KioskForge.spec")

		# Generate other artifacts consumed by Inno Setup 6 (README.html, etc.).
		files = {
			"CHANGES.md" : f"KioskForge v{self.version.version} Change Log",
			"FAQ.md"     : f"KioskForge v{self.version.version} Frequently Asked Questions",
			"GUIDE.md"   : f"KioskForge v{self.version.version} Usage Scenarios Guide",
			"README.md"  : f"KioskForge v{self.version.version} Readme File"
		}
		for file, title in files.items():
			words = TextBuilder()
			words += "pandoc"

			# Source is GitHub flavored Markdown.
			words += "--from=gfm"

			# Output is HTML5/CSS3.
			words += "--to=html5"

			# Include metadata in the generated files.
			words += "--standalone"

			# Specify CSS file to use for the conversion.
			words += "--include-before-body=build/pandoc.css"

			# Specify title as Pandoc requires this.
			words += "--metadata"
			words += "title=" + title

			# Create a table of contents (TOC).
			words += "--toc"

			# Output to this path.
			words += "-o"
			words += distpath + os.sep + os.path.splitext(file)[0] + ".html"

			# Input is this file.
			words += file

			invoke_list_safe(words.list)

		shutil.copyfile("LICENSE", distpath + os.sep + "LICENSE.txt")

		#************************** Create 'KioskForge-x.yy-Setup.exe' (created by Inno Setup 6+) ********************************

		# Only build the Windows setup program on Windows as Inno Setup v6 does not run on Linux.
		if sys.platform == "win32":
			# Expand $$RAMDISK$$ and $$VERSION$$ macros in source .iss file and store the output in ../tmp.
			with open("build/KioskForge.iss", "rt", encoding="utf8") as stream:
				script = stream.read()
			script = script.replace("$$RAMDISK$$", ramdisk)
			script = script.replace("$$VERSION$$", self.version.version)
			with open("../tmp/KioskForge.iss", "wt", encoding="utf8") as stream:
				stream.write(script)

			# Build command-line for Inno Setup 6 and call it to build the final KioskForge-x.yy-Setup.exe install program.
			words  = TextBuilder()
			words += innopath
			words += "/cc"
			words += "../tmp/KioskForge.iss"
			invoke_list_safe(words.list)

			# Copy output from RAM disk to local work tree.
			exename = f"KioskForge-{self.version.version}-Setup.exe"
			shutil.copyfile(ramdisk + exename, "../bin/" + exename)
			del exename

		#************************** Copy the new 'KioskForge-x.yy-Setup.exe' via SSH to the web server hosting kioskforge.org.

		# Only ship if explicitly requested as this will fail on all systems but my own PCs.
		home_env = os.environ.get("HOME")
		if settings.ship and home_env:
			words  = TextBuilder()
			# Use hard-coded path to avoid invoking Microsoft's OpenSSH, if present, as I always use the Git version because
			# Microsoft's version does not honor the HOME environment variable, something which the Git version does.
			words += r"C:\Program Files\Git\usr\bin\scp.exe"
			words += "-F"
			words += home_env + ".ssh/config"
			words += "-p"
			words += ramdisk + f"KioskForge-{self.version.version}-Setup.exe"
			words += "web:web/pub/kioskforge.org/downloads"
			invoke_list_safe(words.list)
		del home_env


if __name__ == "__main__":
	sys.exit(KioskBuild().main(sys.argv))

