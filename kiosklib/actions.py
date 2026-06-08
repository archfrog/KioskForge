#!/usr/bin/env python3
#**********************************************************************************************************************************
# BSD 3-Clause License for KioskForge - https://kioskforge.org:
#
# Copyright © 2024-2026 The KioskForge Team.
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

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Callable, List

import abc
import glob
import os
import shutil
import stat
import time
import zipfile

from kiosklib.errors import InternalError, KioskError
from kiosklib.invoke import invoke_text, Result
from kiosklib.network import internet_active
from kiosklib.various import custom_fonts_get


class Action:
	"""An action is something that must be done during the execution of a script.

	   A prefix of 'Try' indicates that the command does not fail if it cannot perform the requested operation (rare).
	"""

	def __init__(self, title : str) -> None:
		self.__title = title

	@property
	def title(self) -> str:
		return self.__title

	@abc.abstractmethod
	def execute(self) -> Result:
		raise NotImplementedError("Abstract method called")


class InternalAction(Action):
	"""An internal action is derived from this class and is a single Python instance that is executed by a script."""

	@abc.abstractmethod
	def execute(self) -> Result:
		raise NotImplementedError("Abstract method called")


class CustomAction(InternalAction):
	"""Calls a supplied function to perform whatever task needs performed."""

	def __init__(self, title : str, callback : Callable[[], None]) -> None:
		super().__init__(title)
		self.__callback = callback

	def execute(self) -> Result:
		try:
			self.__callback()
		except Exception as that:		# pylint: disable=broad-exception-caught
			return Result(1, str(that))

		return Result()


class DeleteFileAction(InternalAction):
	"""Deletes an external file and return a failure status if unsuccessful."""

	def __init__(self, title : str, path : str) -> None:
		super().__init__(title)
		self.__path = path

	@property
	def path(self) -> str:
		return self.__path

	def execute(self) -> Result:
		try:
			os.unlink(self.path)
		except OSError:
			return Result(1, f"Could not delete file '{self.path}'")

		return Result()


class TryDeleteFileAction(DeleteFileAction):
	"""Attempt to delete a file, but don't fail if it doesn't exist, hence the 'Try' prefix in the class name."""

	def execute(self) -> Result:
		path = self.path
		result = Result()
		if os.path.isfile(path):
			result = DeleteFileAction.execute(self)
		return result

class RemoveFolderAction(InternalAction):
	"""Removes the specified folder."""

	def __init__(self, title : str, path : str) -> None:
		super().__init__(title)
		self.__path = path

	@property
	def path(self) -> str:
		return self.__path

	def execute(self) -> Result:
		try:
			shutil.rmtree(self.path)
			result = Result()
		except FileNotFoundError:
			result = Result(1, f"Could not remove directory '{self.path}'")
		return result


class ModifyTextAction(InternalAction):
	"""Modifies an existing file to contain the given 'text' string."""

	def __init__(self, title : str, mode : str, path : str, text : str) -> None:
		super().__init__(title)
		self.__path = path
		self.__text = text
		self.__mode = mode

	@property
	def path(self) -> str:
		return self.__path

	def execute(self) -> Result:
		try:
			# TODO: Fetch mode and owner from previous file, if any, so that they can be restored.
			with open(self.__path, self.__mode, encoding="utf-8") as stream:
				stream.write(self.__text)
			result = Result()
		except PermissionError:
			result = Result(1, f"Unable to modify file: {self.__path}")
		return result


class CreateTextAction(ModifyTextAction):
	"""Creates a text file from a given string."""

	def __init__(self, title : str, path : str, text : str) -> None:
		super().__init__(title, "wt", path, text)

	def execute(self) -> Result:
		return ModifyTextAction.execute(self)


class CreateTextWithUserAndModeAction(CreateTextAction):
	"""Creates a text file from a given string with the specified owner and access bits."""

	def __init__(self, title : str, path : str, user : str, access : int, text : str) -> None:
		super().__init__(title, path, text)
		self.__user = user
		self.__access = access

	def execute(self) -> Result:
		result = Result()
		try:
			# Create the containing directories, if they don't exist.
			folder = os.path.dirname(self.path)
			if not os.path.isdir(folder):
				os.makedirs(folder, mode=self.__access)
				shutil.chown(folder, user=self.__user, group=self.__user)
				os.chmod(folder, self.__access | stat.S_IXUSR)
			del folder

			# Call base class' 'execute' method.
			result = CreateTextAction.execute(self)
			if result.status != 0:
				return result

			# Change the owner and mode to the user-specified values.
			shutil.chown(self.path, user=self.__user, group=self.__user)
			os.chmod(self.path, self.__access)
		except (InternalError, KioskError) as that:
			result = Result(1, that.text)
		return result


class AppendTextAction(ModifyTextAction):
	"""Appends a text string to a text file."""

	def __init__(self, title : str, path : str, text : str) -> None:
		super().__init__(title, "at", path, text)


class ReplaceTextAction(InternalAction):
	"""Replaces a given string with another given string in an existing text file."""

	def __init__(self, title : str, path : str, source_text : str, target_text : str) -> None:
		super().__init__(title)
		self.__path = path
		self.__source_text = source_text
		self.__target_text = target_text

	@property
	def path(self) -> str:
		return self.__path

	@property
	def source_text(self) -> str:
		return self.__source_text

	@property
	def target_text(self) -> str:
		return self.__target_text

	def execute(self) -> Result:
		result = Result()
		try:
			# Make properties locally accessible without requiring an accessor lookup on each use.
			path = self.path
			source_text = self.source_text
			target_text = self.target_text

			# Grab original file's stats so we can check them meticulously and also use them when creating a new file.
			stats = os.stat(path)

			# Check that the path designates a file and that it is readable and writable.
			st_mode = stats.st_mode
			if not stat.S_ISREG(st_mode):
				raise KioskError(f"Disk item '{path}' is not a file")
			#if not st_mode & stat.S_IROTH:
			#	raise KioskError("File '%s' is not readable" % path)
			#if not st_mode & stat.S_IWOTH:
			#	raise KioskError("File '%s' is not writable" % path)
			del st_mode

			# Check that the request is sensible - that it will change something.
			if target_text == source_text:
				raise InternalError("Attempt to replace a string with an identical string")

			# Read in the source text from the source file.
			with open(path, "rt", encoding="utf-8") as stream:
				actual_text = stream.read()

			# Perform the replacement and verify that it did indeed change something.
			output_text = actual_text.replace(source_text, target_text)
			if output_text == source_text:
				raise KioskError("Unable to replace string, no occurences of the source string found")

			# Write the result to disk.
			with open(path, "wt", encoding="utf-8") as stream:
				stream.write(output_text)

			# TODO: Fix owner, etc.

		except OSError as that:
			if not that.strerror:
				raise InternalError("Attribute 'strerror' of OSError instance is empty") from that
			result = Result(1, that.strerror)

		return result


class CreateZipAction(InternalAction):
	"""Creates a Zip archive containing all the files in the specified source folder."""

	def __init__(self, title : str, owner : str, source_folder : str, target_file : str, method : int = zipfile.ZIP_STORED):
		"""Compresses the target Zip archive from the source folder."""
		super().__init__(title)
		self._owner = owner
		self._source_folder = os.path.abspath(source_folder)
		self._target_file = target_file
		self._method = method

	def execute(self) -> Result:
		try:
			# Get a list of all files in the source folder.
			files = glob.glob(self._source_folder + os.sep + "**" + os.sep + "*", recursive=True)
			if not files:
				raise KioskError("User folder (user_folder) is empty")

			# Zip up all the files in the source folder except dot files.
			with zipfile.ZipFile(self._target_file, "w", self._method) as archive:
				for file in files:
					# Ignore hidden files.
					if file[0] == '.':
						continue

					# Make the name relative to the absolute 'source' folder (D:\Foo\App\file1.txt => file1.txt).
					name = file[len(self._source_folder) + 1:]

					# Add the file to the archive, which puts the archive into UTF-8 mode if non-ASCII (CP437) chars are detected.
					archive.write(file, name)

			# Change owner to user:user.
			shutil.chown(self._target_file, user=self._owner, group=self._owner)

			# Signal success to the client.
			result = Result()
		except OSError as that:
			if not that.strerror:
				raise InternalError("Attribute 'strerror' of OSError instance is empty") from that
			result = Result(1, that.strerror)

		return result


class UnpackZipAction(InternalAction):
	"""Unpacks the source Zip archive to the target folder, making the target folder if it does not exist."""

	def __init__(self, title : str, owner : str, source_file : str, target_folder : str):
		super().__init__(title)
		self._owner = owner
		self._source_file = source_file
		self._target_folder = target_folder


	def execute(self) -> Result:
		try:
			# Create the target directory.
			os.makedirs(self._target_folder, 0o700, exist_ok=True)

			# Change owner to user:user.
			shutil.chown(self._target_folder, user=self._owner, group=self._owner)

			# Unzip all files in the archive in the target folder.
			with zipfile.ZipFile(self._source_file, "r") as archive:
				archive.extractall(path=self._target_folder)

			# Signal success to the client.
			result = Result()
		except OSError as that:
			if not that.strerror:
				raise InternalError("Attribute 'strerror' of OSError instance is empty") from that
			result = Result(1, that.strerror)

		return result


class ExternalAction(Action):
	"""An action that represents an invokation of an external program or script."""

	def __init__(self, title : str, line : str) -> None:
		super().__init__(title)
		self.__line = line

	@property
	def line(self) -> str:
		return self.__line

	def execute(self) -> Result:
		return invoke_text(self.__line)


class AptAction(ExternalAction):
	"""Base class for 'apt' actions."""

	def execute(self) -> Result:
		# I keep getting network errors when upgrading kiosks and it ruins the forge process, so make this crap a bit more robust.
		while not internet_active("ports.ubuntu.com"):
			print("ALERT: Waiting 5 seconds for Ubuntu servers to come online again...")
			time.sleep(5)

		# Wait for 'apt' to release its lock, it sometimes runs in the background even if 'unattended-updates' has been removed.
		while invoke_text("lsof /var/lib/dpkg/lock-frontend").status == 0 or invoke_text("lsof /var/lib/dpkg/lock").status == 0:
			print("ALERT: Waiting 5 seconds for 'apt' lock to be released - 'apt' is running in the background...")
			time.sleep(5)

		return super().execute()


class InstallPackagesAction(AptAction):
	"""Apt action to install one or more packages."""

	def __init__(self, title : str, packages : List[str]) -> None:
		names = ' '.join(packages)
		super().__init__(title, "apt-get install -y " + names)


class InstallPackagesNoRecommendsAction(AptAction):
	"""Apt action to install one or more packages without installing recommended packages."""

	def __init__(self, title : str, packages : List[str]) -> None:
		names = ' '.join(packages)
		super().__init__(title, "apt-get install --no-install-recommends -y " + names)


class PurgePackagesAction(AptAction):
	"""Apt action to purge all the specified packages from the system."""

	def __init__(self, title : str, packages : List[str]) -> None:
		super().__init__(title, "apt-get autoremove --purge -y " + ' '.join(packages))


class CreateTreeAction(ExternalAction):
	"""
		Creates the specified folder tree with the given privileges (use 'mkdir' because it creates the intermediate directories
		correctly, whereas os.makedirs() and shutil.chown() doesn't get the ownership right on those.
	"""
	def __init__(self, title : str, path : str, mode : int, user : str, group : str = "") -> None:
		super().__init__(title, f"sudo -u {user} -g {group or user} mkdir -m={oct(mode)[2:].zfill(3)} -p {path}")


class InstallFontsAction(Action):
	"""Installs an automatically discovered set of TrueType font files from the 'source' folder to the 'target' folder."""

	def __init__(self, title : str, source : str, target : str) -> None:
		super().__init__(title)
		self.__source = source
		self.__target = target

	def execute(self) -> Result:
		# Check that there are indeed custom fonts to be installed.
		fonts = custom_fonts_get(self.__source)
		if not fonts:
			raise KioskError("No fonts found")

		# Create the target folder.
		os.makedirs(self.__target, mode=0o700, exist_ok=True)
		shutil.chown(self.__target, user="kiosk", group="kiosk")

		# Install the found fonts.
		for font in fonts:
			basename = os.path.basename(font)
			shutil.copyfile(font, self.__target + os.sep + basename)
			os.chmod(self.__target + os.sep + basename, 0o600)
			shutil.chown(self.__target + os.sep + basename, user="kiosk", group="kiosk")
			del basename

		return Result()
