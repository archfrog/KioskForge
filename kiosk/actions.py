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

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import abc
import os
import shutil
import stat
import time

from kiosk.errors import *
from kiosk.invoke import invoke_text, Result

class Action(object):
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

	def __init__(self, title : str) -> None:
		Action.__init__(self, title)


class DeleteFileAction(InternalAction):
	"""Deletes an external file and return a failure status if unsuccessful."""

	def __init__(self, title : str, path : str) -> None:
		InternalAction.__init__(self, title)
		self.__path = path

	@property
	def path(self) -> str:
		return self.__path

	def execute(self) -> Result:
		try:
			os.unlink(self.path)
		except OSError as that:
			return Result(1, that.strerror)

		return Result()


class TryDeleteFileAction(DeleteFileAction):
	"""Attempt to delete a file, but don't fail if it doesn't exist, hence the 'Try' prefix in the class name."""

	def __init__(self, title : str, path : str) -> None:
		DeleteFileAction.__init__(self, title, path)

	def execute(self) -> Result:
		path = self.path
		result = Result()
		if os.path.isfile(path):
			result = DeleteFileAction.execute(self)
		return result


class RemoveFolderAction(InternalAction):
	"""Removes the specified folder."""

	def __init__(self, title : str, path : str) -> None:
		InternalAction.__init__(self, title)
		self.__path = path

	@property
	def path(self) -> str:
		return self.__path

	def execute(self) -> Result:
		try:
			shutil.rmtree(self.path)
			result = Result()
		except FileNotFoundError as that:
			result = Result(1, that.strerror)
		return result


class ModifyTextAction(InternalAction):
	"""Modifies an existing file to contain the given 'text' string."""

	def __init__(self, title : str, mode : str, path : str, text : str) -> None:
		InternalAction.__init__(self, title)
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
			result = Result(1, "Unable to modify file: %s" % self.__path)
		return result


class CreateTextAction(ModifyTextAction):
	"""Creates a text file from a given string."""

	def __init__(self, title : str, path : str, text : str) -> None:
		ModifyTextAction.__init__(self, title, "wt", path, text)

	def execute(self) -> Result:
		return ModifyTextAction.execute(self)


class CreateTextWithUserAndModeAction(CreateTextAction):
	"""Creates a text file from a given string with the specified owner and access bits."""

	def __init__(self, title : str, path : str, user : str, access : int, text : str) -> None:
		CreateTextAction.__init__(self, title, path, text)
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
		ModifyTextAction.__init__(self, title, "at", path, text)


class ReplaceTextAction(InternalAction):
	"""Replaces a given string with another given string in an existing text file."""

	def __init__(self, title : str, path : str, source_text : str, target_text : str) -> None:
		InternalAction.__init__(self, title)
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
			# Make properties locally accessible with requiring an accessor lookup on each use.
			path = self.path
			source_text = self.source_text
			target_text = self.target_text

			# Grab original file's stats so we can check them meticulously and also use them when creating a new file.
			stats = os.stat(path)

			# Check that the path designates a file and that it is readable and writable.
			st_mode = stats.st_mode
			if not stat.S_ISREG(st_mode):
				raise KioskError("Disk item '%s' is not a file" % path)
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
			result = Result(1, that.strerror)

		return result


class ExternalAction(Action):
	"""An action that represents an invokation of an external program or script."""

	def __init__(self, title : str, line : str) -> None:
		Action.__init__(self, title)
		self.__line = line

	@property
	def line(self) -> str:
		return self.__line

	def execute(self) -> Result:
		return invoke_text(self.__line)


class RebootSystemAction(ExternalAction):
	"""Action to IMMEDIATELY reboot the system."""

	def __init__(self) -> None:
		ExternalAction.__init__(self, "Rebooting system NOW!", "reboot")


class ExternalAptAction(ExternalAction):
	"""Base class for 'apt' actions."""

	def __init__(self, title : str, line : str) -> None:
		ExternalAction.__init__(self, title, line)

	def execute(self) -> Result:
		# Wait for 'apt' to release its lock, it sometimes runs in the background even if 'unattended-updates' is removed.
		while invoke_text("lsof /var/lib/dpkg/lock-frontend").status == 0 or invoke_text("lsof /var/lib/dpkg/lock").status == 0:
			print("ALERT: Waiting 5 seconds for 'apt' lock to be released - 'apt' is running in the background...")
			time.sleep(5)

		return super().execute()


class CleanPackageCacheAction(ExternalAptAction):
	"""Apt action to clean the package cache (which can easily grow to gigabytes in size)."""

	def __init__(self) -> None:
		ExternalAptAction.__init__(self, "Cleaning package cache", "apt-get clean")


class InstallPackagesAction(ExternalAptAction):
	"""Apt action to install one or more packages."""

	def __init__(self, title : str, packages : List[str]) -> None:
		names = ' '.join(packages)
		ExternalAptAction.__init__(self, title, "apt-get install -y " + names)


class InstallPackagesNoRecommendsAction(ExternalAptAction):
	"""Apt action to install one or more packages without installing recommended packages."""

	def __init__(self, title : str, packages : List[str]) -> None:
		names = ' '.join(packages)
		ExternalAptAction.__init__(self, title, "apt-get install --no-install-recommends -y " + names)


class PurgePackagesAction(ExternalAptAction):
	"""Apt action to purge all unused/useless packages in the system."""

	def __init__(self, title : str, packages : List[str]) -> None:
		names = ' '.join(packages)
		ExternalAptAction.__init__(self, title, "apt-get autoremove --purge -y " + names)


class UpdateSystemAction(ExternalAptAction):
	"""Apt action to update the system-wide package indices."""

	def __init__(self) -> None:
		ExternalAptAction.__init__(self, "Updating system package indices", "apt-get update")


class UpgradeSystemAction(ExternalAptAction):
	"""Apt action to upgrade all packages in the system."""

	def __init__(self) -> None:
		ExternalAptAction.__init__(self, "Upgrading all installed packages", "apt-get upgrade -y")


class UpgradeSnapsAction(ExternalAction):
	"""Snap action to upgrade all snaps in the system."""

	def __init__(self) -> None:
		ExternalAction.__init__(self, "Upgrading snaps", "snap refresh")

