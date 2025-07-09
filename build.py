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
from toolbox.kiosk import Kiosk
from toolbox.sources import SOURCES
from toolbox.various import ramdisk_get
from toolbox.version import Version


# Delete all items IN the specified folder, without removing or altering the folder itself.
def folder_delete_contents(path : str) -> None:
	for item in glob.glob(path + os.sep + "*"):
		if os.path.isdir(item):
			shutil.rmtree(item)
		else:
			os.unlink(item)

class Paths:
	"""Simple class, which is used to easily pass around the four intermediate paths that this script uses internally."""

	def __init__(self, ramdisk : str, rootpath : str, shippath : str, temppath : str) -> None:
		self.__ramdisk  = ramdisk
		self.__rootpath = rootpath
		self.__shippath = shippath
		self.__temppath = temppath

		# Ensure all directories exist.
		os.makedirs(self.__ramdisk, mode=0o664, exist_ok=True)
		os.makedirs(self.__rootpath, mode=0o664, exist_ok=True)
		os.makedirs(self.__shippath, mode=0o664, exist_ok=True)
		os.makedirs(self.__temppath, mode=0o664, exist_ok=True)

	@property
	def ramdisk(self) -> str:
		"""Returns the absolute path of the RAM disk (or a similar, temporary, disk directory)."""
		return self.__ramdisk

	@property
	def rootpath(self) -> str:
		"""Returns the """
		return self.__rootpath

	@property
	def shippath(self) -> str:
		"""Returns a LOCAL directory where all built KioskForge-x.yy-Setup.exe files are copied to once built."""
		return self.__shippath

	@property
	def temppath(self) -> str:
		"""Returns the path to a RAM disk (or other temporary folder) that can be erased completely on every invocation."""
		return self.__temppath

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
				if sys.platform != "win32":
					raise KioskError("The --ship option can only be used on Windows")
				self.__ship = True
			else:
				raise CommandError('"build.py" [--clean] [--debug] [--ship]')


class KioskBuild(KioskDriver):
	"""Defines the build.py script, which is responsible for building a platform-dependent executable using PyInstaller."""

	def __init__(self) -> None:
		KioskDriver.__init__(self, "build")

	def build_exe(self, settings : Settings, paths : Paths, version : Version) -> None:
		workpath = paths.rootpath + os.sep + "PyInstaller"
		os.makedirs(workpath, mode=0o664, exist_ok=True)

		# Write 'version.txt' needed to fill out the details that can be viewed in the Details pane of Windows Explorer.
		pyinstaller_versionfile.create_versionfile(
			output_file=paths.rootpath + os.sep + "version.txt",
			version=version.version,
			company_name=version.company,
			file_description=version.product,
			internal_name=version.product,
			legal_copyright="Copyright © " + version.company + ". All rights reserved.",
			original_filename=version.product + ".exe",
			product_name=version.product,
			translations=[1033, 65001]
		)

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
		words += paths.temppath

		words += "--workpath"
		words += workpath

		# NOTE: The --specpath option also affects the default location of data files, something which I think is pretty bizarre.
		# words += "--specpath"
		# words += paths.temppath

		words += "--upx-exclude"
		words += "python3.dll"

		words += "--icon"
		words += "../pic/logo.ico"

		words += "--version-file"
		words += paths.rootpath + os.sep + "version.txt"

		for item in SOURCES:
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
			"Changes.md"      : f"KioskForge v{version.version} Changes",
			"Contributing.md" : f"KioskForge v{version.version} Contributing",
			"FAQ.md"          : f"KioskForge v{version.version} FAQ",
			"Guide.md"        : f"KioskForge v{version.version} Guide",
			"Manual.md"       : f"KioskForge v{version.version} Manual",
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

			# Specify HTML file with CSS to use for the conversion.
			words += "--include-before-body=build/pandoc-styles.html"

			# Add a <br> tag after the body to stop Pandoc from terminating the page right after the last sentence (looks ugly).
			words += "--include-after-body=build/pandoc-footer.html"

			# Specify title as Pandoc requires this.
			words += "--metadata"
			words += "title=" + title

			# Create a table of contents (TOC).
			words += "--toc"

			# Output to this path.
			words += "-o"
			words += paths.temppath + os.sep + os.path.splitext(file)[0] + ".html"

			# Input is the file, which is located in the 'docs' folder.
			words += "docs" + os.sep + file

			invoke_list_safe(words.list)

		# Simply copy the LICENSE.txt file to the temporary directory.
		shutil.copyfile("LICENSE.txt", paths.temppath + os.sep + "LICENSE.txt")

		# Generate a brand new, up-to-date template kiosk by saving an empty, blank kiosk.
		Kiosk(version).save(paths.temppath + os.sep + "Template.kiosk")

	def build_installer(self, paths : Paths, version : str) -> None:
		innopath = r"C:\Program Files (x86)\Inno Setup 6\Compil32.exe"

		# Expand $$RAMDISK$$ and $$VERSION$$ macros in source .iss file and store the output in ../tmp.
		with open("build/KioskForge.iss", "rt", encoding="utf8") as stream:
			script = stream.read()
		script = script.replace("$$RAMDISK$$", paths.ramdisk)
		script = script.replace("$$VERSION$$", version)
		with open(paths.temppath + os.sep + "KioskForge.iss", "wt", encoding="utf8") as stream:
			stream.write(script)

		# Build command-line for Inno Setup 6 and call it to build the final KioskForge-x.yy-Setup.exe install program.
		words  = TextBuilder()
		words += innopath
		words += "/cc"
		words += paths.temppath + os.sep + "KioskForge.iss"
		invoke_list_safe(words.list)

		# Copy output from RAM disk to local work tree.
		exename = f"KioskForge-{version}-Setup.exe"
		shutil.copyfile(paths.ramdisk + exename, paths.shippath + os.sep + exename)
		del exename

	def check(self) -> None:
		# NOTE: Check.py fails if MyPy or pylint reports ERRORS, not if pylint only reports warnings.
		words  = TextBuilder()
		words += "python"
		words += "check.py"
		invoke_list_safe(words.list)

	def ship(self, paths : Paths, version : str) -> None:
		scp = shutil.which("scp")
		if not scp:
			raise KioskError("SCP not found, cannot ship built KioskForge installer.")

		words  = TextBuilder()
		words += scp

		# Use the .ssh/config file found at HOME, not at some idiotic Windows-style "C:\Users\Foo\.ssh\config".
		words += "-F"
		words += os.environ["HOME"] + ".ssh/config"

		# Preserve file date when copying to the web server.
		words += "-p"

		# Specify source file and target directory.
		# TODO: Change SCP target directory to the real one once we go public.
		words += paths.ramdisk + f"KioskForge-{version}-Setup.exe"
		words += "web:web/pub/egevig.org/vhm"

		invoke_list_safe(words.list)

	def tag(self, version : str) -> None:
		words  = TextBuilder()
		words += "git"
		words += "tag"
		words += "-a"
		words += version
		words += "-m"
		words += f"Release v{version}."
		invoke_list_safe(words.list)

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Delete two standard arguments that we don't currently use for anything.
		del logger
		del origin

		# Check that we're running on Windows, this script has not yet been ported to and tested on Linux.
		if sys.platform != "win32":
			raise KioskError("The build.py script currently only works on Windows")

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

		#*** Set up paths and clean out distribution path.
		# Create object to easily pass around the output paths.
		paths = Paths(ramdisk, ramdisk + "KioskForge", "../bin", "../tmp")

		# Make sure we don't accidentally ship artifacts from earlier builds.
		folder_delete_contents(paths.temppath)

		#*** Perform the actual build steps.
		# Ask MyPy and pylint if the product is ready for distribution.
		self.check()

		# Make a Git release tag for the target version, which will fail if already defined, this is intentional.
		if settings.ship:
			self.tag(self.version.version)

		# Create 'KioskForge.exe' (created by PyInstaller, consumed by Inno Setup 6+).
		self.build_exe(settings, paths, self.version)

		# Create 'KioskForge-x.yy-Setup.exe' (created by Inno Setup 6+).
		# NOTE: Only build the Windows setup program on Windows as Inno Setup v6 does not run on Linux.
		if sys.platform == "win32":
			self.build_installer(paths, self.version.version)

		# Copy the new 'KioskForge-x.yy-Setup.exe' via SSH to the web server hosting kioskforge.org.
		# NOTE: Only ship if explicitly requested as this will fail on all systems but my own PCs.
		if settings.ship and os.environ.get("HOME"):
			self.ship(paths, self.version.version)


if __name__ == "__main__":
	sys.exit(KioskBuild().main(sys.argv))
