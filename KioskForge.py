#!/usr/bin/env python3
# Script that converts an Ubuntu Server box into a kiosk machine that displays the specified URL in kiosk mode using Chromium.
#
# Notes:
#   1. This script is in fact THREE scripts!  This to avoid duplicating code and maintaining identical code in three files.
#      The script is invoked as 'KioskForge.py' and then copies itself to the installation medie and customizes cloud-init in such
#      a way that the script is automatically invoked as 'KioskSetup.py' very late in the installation process, after which it
#      creates a symbolic link to itself with the name 'KioskStart.py', which launches Chrome and monitors its execution.
#	2. This script assumes a clean installation with no modifications whatsoever prior to it being invoked.  As such, it can
#	   "safely" abort upon errors as the user can simply re-flash his system using Raspberry Pi Imager once again.  There are no
#	   features to safely roll back the changes made during the customization of the system for kiosk mode usage!

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Any, Dict, List, Optional, TextIO, Tuple

import abc
import glob
import hashlib
import http.client as httplib
import os
import platform
import shlex
import shutil
import stat
import string
import subprocess
import sys
import time
import types


# Try to import syslog (non-Windows platforms) or create a dummy stub.
try:
	import syslog
	SYSLOG_LOG_ERR = syslog.LOG_ERR
	SYSLOG_LOG_INFO = syslog.LOG_INFO
except ModuleNotFoundError:
	# NOTE: Dummy values used to make the code simpler (and MyPy choke a bit less).
	SYSLOG_LOG_ERR = 1
	SYSLOG_LOG_INFO = 2

# Try to import bcrypt.  If not found, try to silently install it and try to import it once more.
try:
	import bcrypt
except ModuleNotFoundError:
	subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	import bcrypt

VERSION = "0.12"
COMPANY = "Vendsyssel Historiske Museum"
CONTACT = "me@vhm.dk"
TESTING = True

# AUTOSTART: If True, the system will be installed without user intervention, otherwise, the user must start KioskSetup.py.
AUTOSTART = True

# Standard, C-like exit code definitions.
EXIT_SUCCESS = os.EX_OK
EXIT_FAILURE = 1

# Dictionary of valid responses in various prompts and their mappings to the corresponding boolean values.
STRING_TO_BOOLEAN = {'y' : True, '1' : True, 't' : True, 'true' : True, 'n' : False, '0' : False, 'f' : False, 'false' : False}


def password_crypt(text : str) -> str:
	assert(len(text) >= 1 and len(text) <= 72)
	data = value.encode('utf-8')
	hash = bcrypt.pwhash(data, bcrypt.gensalt(14))
	return hash


class Error(Exception):
	"""The base class for all exceptions."""

	def __init__(self, text : str) -> None:
		Exception.__init__(self)
		self.__text = text

	@property
	def text(self) -> str:
		return self.__text


class InputError(Error):
	"""Exception thrown if the user enters invalid input."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class KioskError(Error):
	"""Generic exception used for all kinds of errors while running this script."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class InternalError(Error):
	"""Exception used to signal that an internal error has been discovered."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class SyntaxError(Error):
	"""Exception used to signal that a syntax error, in a configuration file, has been detected."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class ArgumentError(Error):
	"""Exception used to signal that an argument to the script was invalid or missing."""

	def __init__(self, index : int, text : str) -> None:
		Error.__init__(self, text)
		self.__index = index

	@property
	def index(self) -> int:
		return self.__index


# Source: https://stackoverflow.com/questions/3764291/how-can-i-see-if-theres-an-available-and-active-network-connection-in-python
def internet_active() -> bool:
	connection = httplib.HTTPSConnection("8.8.8.8", timeout=5)
	try:
		connection.request("HEAD", "/")
		return True
	except Exception:
		return False
	finally:
		connection.close()


class Version(object):
	"""A simple wrapper around everything related to version information about the running script."""

	def __init__(self, product : str, version : str, company : str, contact : str, testing : bool) -> None:
		self.product = product
		self.program = product + ".py"
		self.version = version
		self.company = company
		self.contact = contact
		self.testing = testing

	def banner(self) -> str:
		return "%s v%s%s - Copyright (c) 2024-2025 %s (%s).  All Rights Reserved." % (
			self.program,
			self.version,
			" (TEST)" if self.testing else "",
			self.company,
			self.contact
		)


class Target(object):
	"""Simple class that encapsulates all information about the target system."""

	def __init__(self, kind : str, basedir : str, product : str, edition : str, version : str, cpukind : str, install : str) -> None:
		# Check arguments (mostly for the sake of documenting the valid values).
		assert(kind in ["PC", "PI"])
		assert(cpukind in ["amd64", "arm64"])
		assert(install in ["cloud-init", "subiquity"])

		# Initialize instance.
		self.__kind = kind
		self.__basedir = basedir
		self.__product = product
		self.__edition = edition
		self.__version = version
		self.__cpukind = cpukind
		self.__install = install

	@property
	def basedir(self) -> str:
		return self.__basedir

	@property
	def cpukind(self) -> str:
		return self.__cpukind

	@property
	def edition(self) -> str:
		return self.__edition

	@property
	def install(self) -> str:
		return self.__install

	@property
	def kind(self) -> str:
		return self.__kind

	@property
	def product(self) -> str:
		return self.__product

	@property
	def version(self) -> str:
		return self.__version


class Recognizer(object):
	"""Simple base class that defines the layout of a recognizer that recognizes one or more target systems."""

	def __init__(self) -> None:
		pass

	def _identify(self, path : str) -> Optional[Target]:
		raise NotImplementedError("Abstract method called")

	def identify(self) -> Target:
		if platform.system() != "Windows":
			raise KioskError("KioskForge.py only runs on Windows")

		# Scan all mount points/drives and see if there are any of the reserved files we're looking for.
		targets : List[Target] = []
		while True:
			if platform.system() == "Windows":
				mounts = os.listdrives()
			elif platform.system() == "Linux":
				raise InternalError("Feature not finished")
				mounts = 'df -a -T -h -t vfat | grep -Fv "/boot/efi" | grep -Fv "Use%"'

			# Check each mount point/Windows drive for a recognizable installation media.
			for mount in mounts:
				for recognizer in RECOGNIZERS:
					target = recognizer._identify(mount)
					if target:
						targets.append(target)

			# If no kiosk images were found, let the user fix the error and try again.
			if len(targets) == 0:
				# NOTE: Windows takes a little while to discover the written image, so we try once more if we fail at first.
				print("ALERT: Waiting three seconds for installation media to be discovered by the host operating system...")
				print("ALERT: If you have not already done so, please insert the installation media to proceed.")
				time.sleep(3)
				continue

			# Handle incorrect number of target drives in the target (zero or more than one).
			if len(targets) >= 2:
				raise KioskError("More than one USB key or MicroSD card found")

			break

		assert(len(targets) == 1)
		return targets[0]


class PcRecognizer(Recognizer):
	"""Derived class which recognizes Ubuntu Server 24.04.1 in a PC install image."""

	def __init__(self) -> None:
		Recognizer.__init__(self)

	def _identify(self, path : str) -> Optional[Target]:
		info_name = path + ".disk" + os.sep + "info"

		if not os.path.isfile(info_name):
			return None

		# Parse the /.disk/info file to get the information we're looking for.
		info_data = open(info_name, "rt").read().strip()
		fields = shlex.split(info_data)
		if len(fields) != 8:
			return None
		(product, version, support, codename, dash, release, cpukind, date_num) = fields

		# Check the info file and report one or more errors if we don't support the found target.
		errors = []
		if product != "Ubuntu-Server":
			errors.append("Error: Unsupported operating system: %s" % product)
		if version != "24.04.1":
			errors.append("Error: Unsupported version: %s" % version)
		if support != "LTS":
			errors.append("Error: Unsupported support lifetime: %s" % support)
		if cpukind != "amd64":
			errors.append("Error: Unsupported CPU kind: %s" % cpukind)

		# If one or more errors were found, report them and don't recognize this target.
		if errors:
			for error in errors:
				print("%s: %s" % (path, error))
			return None

		return Target("PC", path, "Ubuntu", "Server", "24.04.1", "amd64", "subiquity")


SHA512_UBUNTU_SERVER_24_04_1_ARM64 = '1d6c8d010c34f909f062533347c91f28444efa6e06cd55d0bdb39929487d17a8be4cb36588a9cbfe0122ad72fee72086d78cbdda6d036a8877e2c9841658d4ca'
SHA512_UBUNTU_DESKTOP_24_04_1_ARM64 = 'ce3eb9b96c3e458380f4cfd731b2dc2ff655bdf837cad00c2396ddbcded64dbc1d20510c22bf211498ad788c8c81ba3ea04c9e33d8cf82538be0b1c4133b2622'
SHA512_UBUNTU_SERVER_24_04_2_ARM64 = '5c62b93b8d19e8d7ac23aa9759a23893af5dd1ab5f80e4fb71f7b4fd3ddd0f84f7c82f9342ea4c9fdba2c350765c2c83eaaa6dcaac236f9a13f6644386e6a1d2'
SHA512_UBUNTU_DESKTOP_24_04_2_ARM64 = 'TODO: fill in Ubuntu Desktop 24.04.2 SHA512 sum'

class PiRecognizer(Recognizer):
	"""Derived class that recognizes Ubuntu Desktop or Server 24.04.x in a Raspberry Pi 4B install image."""

	def __init__(self) -> None:
		Recognizer.__init__(self)

	def _identify(self, path : str) -> Optional[Target]:
		if not os.path.isfile(path + "cmdline.txt"):
			return None

		if not os.path.isfile(path + "initrd.img"):
			return None

		hash = hashlib.sha512(open(path + "initrd.img", "rb").read()).hexdigest()
		if hash == SHA512_UBUNTU_SERVER_24_04_1_ARM64:
			return Target("PI", path, "Ubuntu", "Server", "24.04.1", "arm64", "cloud-init")
		elif hash == SHA512_UBUNTU_SERVER_24_04_2_ARM64:
			return Target("PI", path, "Ubuntu", "Server", "24.04.2", "arm64", "cloud-init")
		elif hash == SHA512_UBUNTU_DESKTOP_24_04_1_ARM64:
			return Target("PI", path, "Ubuntu", "Desktop", "24.04.1", "arm64", "cloud-init")

		return None


# List of systems that can be recognized and thus are supported.
RECOGNIZERS = [
	PiRecognizer(),
	PcRecognizer()
]


class TextWriter(object):
	"""Simple text stream writer class that supports 'with' and indentation."""

	def __init__(self, path : str, tabs : str = "  ") -> None:
		self.__path = path
		# The size, in levels, of the indentation.
		self.__size = 0
		# The string that makes up one level of indentation.
		self.__tabs = tabs

	@property
	def path(self) -> str:
		return self.__path

	def __enter__(self) -> Any:
		"""Required to support the 'with instance as name: ...' exception wrapper syntactic sugar."""
		self.__stream = open(self.__path, "wt")
		return self

	def __exit__(self, exception_type : type, exception_value : Exception, traceback : types.TracebackType) -> None:
		"""Required to support the 'with instance as name: ...' exception wrapper syntactic sugar."""
		self.__stream.close()

	def indent(self, size : int = 1) -> None:
		self.__size += size

	def dedent(self, size : int = 1) -> None:
		assert(self.__size - size >= 0)
		self.__size -= size

	def _write(self, text : str) -> None:
		self.__stream.write(text + "\n")
		self.__stream.flush()

	def write(self, text : str = "") -> None:
		"""Writes one or more complete lines to the output device."""
		lines = text.split(os.linesep)
		for line in lines:
			self._write(self.__size * self.__tabs + line)


class Logger(object):
	"""Class that implements the multi-line logging functionality required by the script (Linux only)."""

	def __init__(self) -> None:
		# Prepare syslog() for our messages.
		if 'syslog' in sys.modules:
			syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_LOCAL0)

	def __enter__(self) -> Any:
		"""Required to support the 'with instance as name: ...' exception wrapper syntactic sugar."""
		return self

	def __exit__(self, exception_type : type, exception_value : Exception, traceback : types.TracebackType) -> None:
		"""Required to support the 'with instance as name: ...' exception wrapper syntactic sugar."""
		pass

	def _write(self, kind : int, text : str) -> None:
		"""Writes one or more lines to the output device."""
		lines = text.split(os.linesep)
		for line in lines:
			# NOTE: Always output status to the console, even when AUTOSTART is True, to allow the user to see what is happening.
			print(line)

			if 'syslog' in sys.modules:
				syslog.syslog(kind, line)

	def error(self, text : str = "") -> None:
		self._write(SYSLOG_LOG_ERR, text)

	def write(self, text : str = "") -> None:
		self._write(SYSLOG_LOG_INFO, text)


class Result(object):
	"""The result (status code, output) of an action."""

	def __init__(self, status : int = 0, output : str = "") -> None:
		self.__status = status
		self.__output = output

	@property
	def status(self) -> int:
		return self.__status

	@property
	def output(self) -> str:
		return self.__output


# Global function to invoke an external program and return a 'Result' instance with the program's exit code and output.
def invoke(line : str) -> Result:
	# Capture stderr and stdout interleaved in the same output string by using stderr=...STDOUT and stdout=...PIPE.
	result = subprocess.run(
		shlex.split(line), stderr=subprocess.STDOUT, stdout=subprocess.PIPE, check=False, shell=False, text=False
	)
	output = result.stdout.decode('utf-8')
	return Result(result.returncode, output)


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
			with open(self.__path, self.__mode) as stream:
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
			with open(path, "rt") as stream:
				actual_text = stream.read()

			# Perform the replacement and verify that it did indeed change something.
			output_text = actual_text.replace(source_text, target_text)
			if output_text == source_text:
				raise KioskError("Unable to replace string, no occurences of the source string found")

			# Write the result to disk.
			with open(path, "wt") as stream:
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
		return invoke(self.__line)


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
		while invoke("lsof /var/lib/dpkg/lock-frontend").status == 0 or invoke("lsof /var/lib/dpkg/lock").status == 0:
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


class Script(object):
	"""Simple abstraction of a sequence of actions that can be resumed from any point in the list of actions."""

	def __init__(self, logger : Logger, resume : int) -> None:
		self.__actions : List[Action] = []
		self.__logger = logger
		self.__resume = resume

	def __iadd__(self, action : Action) -> Any:
		"""Overload the += operator to make it convenient to add new script actions (cannot use '-> Script' so '-> Any' it is)."""

		# Check that the action hasn't already been added to the script.
		if action in self.__actions:
			raise InternalError("Action was added twice: %s" % action)

		# Add the action to the script to be executed.
		self.__actions.append(action)

		return self

	def execute(self) -> Result:
		result = Result()

		if self.__resume >= len(self.__actions):
			raise ArgumentError(0, "Resume offset greater than total number of actions")

		# Execute each action in turn while handling exceptions and failures.
		index = self.__resume
		for action in self.__actions[self.__resume:]:
			try:
				self.__logger.write("%4d %s" % (index, action.title))
				index += 1

				result = action.execute()
				if result.status != 0:
					self.__logger.error(result.output)
					self.__logger.error("**** SCRIPT ABORTED DUE TO ABOVE ERROR ****")
					break
			except (KioskError, InternalError) as that:
				result = Result(1, that.text)

		return result


class TextBuilder(object):
	"""Used to build a multi-line text concatened from individual lines using += or a list of tokens concatenated using +=."""

	def __init__(self) -> None:
		self.__lines : List[str] = []

	@property
	def list(self) -> List[str]:
		return self.__lines

	@property
	def text(self) -> str:
		return '\n'.join(self.__lines) + '\n'

	def __iadd__(self, line : str) -> Any:
		self.__lines.append(line)
		return self


class Record(object):
	"""Simple class that allows constructing a tree of records to represent a configuration file."""

	def __init__(self) -> None:
		pass


class Field(object):
	"""Base class for configuration fields; these are title/value pairs."""

	def __init__(self, text : str) -> None:
		self.__text = text

	@property
	def text(self) -> str:
		return self.__text

	def parse(self, data : str) -> None:
		raise NotImplementedError("Abstract method called")


class BooleanField(Field):
	"""Derived class that implements a boolean field."""

	def __init__(self, text : str) -> None:
		Field.__init__(self, text)
		self.__data = False

	@property
	def data(self) -> bool:
		return self.__data

	def parse(self, data : str) -> None:
		if len(data) == 0:
			raise InputError("Invalid value entered: %s " % data)

		try:
			self.__data = STRING_TO_BOOLEAN[data.lower()]
		except KeyError:
			raise InputError("Invalid value entered")
		except ValueError as that:
			raise InputError(str(that))


class NaturalField(Field):
	"""Derived class that implements a natural (unsigned integer) field."""

	def __init__(self, text : str, lower : int, upper : int) -> None:
		Field.__init__(self, text)
		self.__data = 0
		self.__lower = lower
		self.__upper = upper

	@property
	def data(self) -> int:
		return self.__data

	def parse(self, data : str) -> None:
		if not data or data[0] == '-':
			raise InputError("Invalid value entered: %s " % data)

		try:
			value = int(data)

			if value < self.__lower or value > self.__upper:
				raise ValueError("Value outside bounds (%d through %d)" % (self.__lower, self.__upper))

			self.__data = value
		except ValueError as that:
			raise InputError(str(that))


class StringField(Field):
	"""Derived class that implements a string field."""

	def __init__(self, text : str) -> None:
		Field.__init__(self, text)
		self.__data = ""

	@property
	def data(self) -> str:
		return self.__data

	def parse(self, data : str) -> None:
		self.__data = data


class PasswordField(StringField):
	"""Derived class that checks a Linux password."""

	def __init__(self, text : str) -> None:
		StringField.__init__(self, text)

	def parse(self, data : str) -> None:
		# Report error if the password string is empty.
		if data == "":
			raise KioskError("Password cannot be empty")

		# Disallow passwords starting with a dollar sign, including encrypted passwords.
		if data[0] == '$':
			raise KioskError("Password cannot begin with a dollar sign ($)")

		# Apparently, the maximum length of an input password to 'bcrypt' is 72 characters.
		if len(data) > 72:
			raise KioskError("Password too long - cannot exceed 72 characters")

		# Finally, store the encrypted password.
		StringField.parse(self, data)


class TimeField(StringField):
	"""Derived class that implements a time (HH:MM) field."""

	def __init__(self, text : str) -> None:
		StringField.__init__(self, text)

	def parse(self, data : str) -> None:
		if data == "":
			StringField.parse(self, data)
			return

		try:
			# Let time.strptime() validate the time value.
			time.strptime(data, "%H:%M")
			StringField.parse(self, data)
		except ValueError:
			raise KioskError("Invalid time specification: %s" % data)


class KernelOptions(object):
	"""Small class that handles adding kernel options to the Raspberry PI 'cmdline.txt' file."""

	def __init__(self) -> None:
		self.__options : List[str] = []

	@property
	def options(self) -> List[str]:
		return self.__options

	def append(self, option : str) -> None:
		self.__options.append(option)

	def load(self, path : str) -> None:
		self.__options = open(path, "rt").read().strip().split(' ')

	def save(self, path : str) -> None:
		open(path, "wt").write(' '.join(self.__options))


class Setup(Record):
	"""Class that defines, loads, and saves the configuration of a given kiosk machine."""

	def __init__(self) -> None:
		Record.__init__(self)
		self.comment       = StringField("A descriptive comment for the kiosk machine.")
		self.hostname      = StringField("The unqualified host name (e.g., 'kiosk01').")
		self.timezone      = StringField("The time zone (e.g., 'Europe/Copenhagen').")
		self.keyboard      = StringField("The keyboard layout (e.g., 'dk').")
		self.locale        = StringField("The locale (e.g., 'da_DK.UTF-8').")
		self.website       = StringField("The URL (e.g., 'https://google.com').")
		self.audio         = NaturalField("The default audio level (0 = no audio).", 0, 100)
		self.mouse         = BooleanField("If the mouse should be enabled (y/n or 1/0).")
		self.user_name     = StringField("The user name of the non-root administrative user (e.g., 'user').")
		self.user_code     = PasswordField("The password for the user (e.g., 'dumsey3rumble').")
		self.ssh_key       = StringField("The public SSH key for accessing the kiosk using the 'ssh' command.")
		self.wifi_name     = StringField("The WiFi network (case sensitive!) (e.g., 'MyWiFi', blank = no WiFi).")
		self.wifi_code     = StringField("The password for WiFi access (case sensitive!) (e.g., 'stay4out!', blank = no password).")
		self.snap_time     = StringField("The daily period of time that snap updates software (e.g., '10:00-10:30').")
		self.swap_size     = NaturalField("The size in gigabytes of the swap file (0 = none).", 0, 128)
		self.vacuum_time   = TimeField("The time of day to vacuum system logs (blank = never)")
		self.vacuum_days   = NaturalField("The number of days to retain system logs for (1 through 365, only used if 'vacuum_time' is set)", 1, 365)
		self.upgrade_time  = TimeField("The time of day to upgrade the system (blank = never)")
		self.poweroff_time = TimeField("The time of day to power off the system (blank = never)")
		self.idle_timeout  = NaturalField("The number of seconds of idle time before Chromium is restarted (0 = never)", 0, 24 * 60 * 60)
		self.rotate_screen = NaturalField("0 = default, 1 = rotate left, 2 = flip upside-down, 3 = rotate right", 0, 3)

	def check(self) -> List[str]:
		result = []
		if self.comment.data == "":
			result.append("Error: 'comment' value is missing from configuration")
		if self.hostname.data == "":
			result.append("Error: 'hostname' value is missing from configuration")
		if self.timezone.data == "":
			result.append("Error: 'timezone' value is missing from configuration")
		if self.keyboard.data == "":
			result.append("Error: 'keyboard' value is missing from configuration")
		if self.locale.data == "":
			result.append("Error: 'locale' value is missing from configuration")
		if self.website.data == "":
			result.append("Error: 'website' value is missing from configuration")
		if self.user_name.data == "":
			result.append("Error: 'user_name' value is missing from configuration")
		if self.user_code.data == "":
			result.append("Error: 'user_code' value is missing from configuration")
		if self.ssh_key.data == "":
			result.append("Error: 'ssh_key' value is missing from configuration")
		if self.wifi_name.data != "" and self.wifi_code.data == "":
			result.append("Error: 'wifi_code' value is missing from configuration")
		if self.snap_time.data == "":
			result.append("Error: 'snap_time' value is missing from configuration")
		return result

	def load(self, path : str) -> None:
		# Read in the specified file and split it into individual lines.
		lines = open(path, "rt").read().split('\n')

		# Process each line in turn.
		for line in lines:
			# Remove trailing whitespaces.
			line = line.rstrip()

			# Ignore empty lines and comment lines.
			if line == "" or line[0] in ['#', ';']:
				continue

			# Process unsupported section marker.
			if line[0] == '[' and line[-1] == ']':
				raise KioskError("Sections not supported in configuration (.cfg) file")

			# Parse name/data pair (name=data).
			index = line.find('=')
			if index == -1:
				raise KioskError("Missing delimiter (=) in line: %s" % line)
			( name, data ) = ( line[:index].strip(), line[index + 1:].strip() )

			# Store the field.
			try:
				getattr(self, name).parse(data)
			except AttributeError:
				raise KioskError("Unknown setting in configuration file: %s" % name)

	def save(self, path : str, version : Version, edit : bool = True) -> None:
		# Generate KioskSetup.cfg.
		with TextWriter(path) as stream:
			stream.write(
				"# KioskSetup.py settings file generated by %s v%s.  %s" % (
					version.program,
					version.version,
					"EDIT AS YOU PLEASE!" if edit else "DO NOT EDIT!"
				)
			)

			# Output the list of supported fields.
			stream.write("# %s" % self.comment.text)
			stream.write("comment=%s" % self.comment.data)

			stream.write("# %s" % self.hostname.text)
			stream.write("hostname=%s" % self.hostname.data)

			stream.write("# %s" % self.timezone.text)
			stream.write("timezone=%s" % self.timezone.data)

			stream.write("# %s" % self.locale.text)
			stream.write("locale=%s" % self.locale.data)

			stream.write("# %s" % self.keyboard.text)
			stream.write("keyboard=%s" % self.keyboard.data)

			stream.write("# %s" % self.website.text)
			stream.write("website=%s" % self.website.data)

			stream.write("# %s" % self.audio.text)
			stream.write("audio=%d" % self.audio.data)

			stream.write("# %s" % self.mouse.text)
			stream.write("mouse=%s" % ("1" if self.mouse.data else "0"))

			stream.write("# %s" % self.user_name.text)
			stream.write("user_name=%s" % self.user_name.data)

			stream.write("# %s" % self.user_code.text)
			stream.write("user_code=%s" % self.user_code.data)

			stream.write("# %s" % self.ssh_key.text)
			stream.write("ssh_key=%s" % self.ssh_key.data)

			stream.write("# %s" % self.wifi_name.text)
			stream.write("wifi_name=%s" % self.wifi_name.data)

			stream.write("# %s" % self.wifi_code.text)
			stream.write("wifi_code=%s" % self.wifi_code.data)

			stream.write("# %s" % self.snap_time.text)
			stream.write("snap_time=%s" % self.snap_time.data)

			stream.write("# %s" % self.swap_size.text)
			stream.write("swap_size=%d" % self.swap_size.data)

			stream.write("# %s" % self.upgrade_time.text)
			stream.write("upgrade_time=%s" % self.upgrade_time.data)

			stream.write("# %s" % self.poweroff_time.text)
			stream.write("poweroff_time=%s" % self.poweroff_time.data)

			stream.write("# %s" % self.vacuum_time.text)
			stream.write("vacuum_time=%s" % self.vacuum_time.data)

			stream.write("# %s" % self.vacuum_days.text)
			stream.write("vacuum_days=%d" % self.vacuum_days.data)

			stream.write("# %s" % self.idle_timeout.text)
			stream.write("idle_timeout=%s" % self.idle_timeout.data)

			stream.write("# %s" % self.rotate_screen.text)
			stream.write("rotate_screen=%d" % self.rotate_screen.data)


class Editor(object):
	"""Very simple editor for selecting choices and editing configurations."""

	def confirm(self, question : str) -> bool:
		answer = ""
		while answer not in STRING_TO_BOOLEAN:
			answer = input(question + " (y/n)? ").strip().lower()
		return STRING_TO_BOOLEAN[answer]

	def edit(self, setup : Setup) -> bool:
		changed = False
		fields = vars(setup)
		names = {}
		while True:
			print()
			index = 0
			for name, field in fields.items():
				index += 1
				names[index] = name
				print("%2d) %-13s = %s" % (index, name, field.data))
			print()

			answer = input("Please enter number or ENTER to quit: ").strip()
			if answer == "":
				return changed

			if not answer.isdigit():
				print("Error: Enter a valid number")
				continue

			choice = int(answer)
			if choice == 0 or choice > index:
				print("Error: Enter a valid number in the range 1 through %d" % index)
				continue

			print("Hint: %s" % getattr(setup, names[choice]).text)
			value = input("Enter new value (ENTER to leave unchanged): ").strip()
			if value == "":
				continue

			try:
				getattr(setup, names[choice]).parse(value)
				changed = True
			except InputError as that:
				print(that.text)

		return changed

	def select(self, title : str, choices : List[str]) -> int:
		print(title + ":")

		while True:
			print()
			index = 0
			while index < len(choices):
				value = choices[index]
				index += 1
				print("%2d) %s" % (index, value))
			print()
			del index

			answer = input("Enter choice (ENTER to quit): ").strip()
			print()

			if answer == "":
				return -1

			if not answer.isdigit():
				print("Error: Invalid value entered")
				continue

			choice = int(answer) - 1
			if choice < 0 or choice >= len(choices):
				print("Error: Enter a valid number")
				continue

			break

		return choice


class KioskClass(object):
	"""Base class for the multi-script classes that implement the respective script features."""

	def __init__(self, homedir : str) -> None:
		# Append terminating slash/backslash, if not terminated properly (eases expressions everywhere else).
		self.__homedir = homedir

	@property
	def homedir(self) -> str:
		return self.__homedir

	@abc.abstractmethod
	def main(self, logger : Logger, homedir : str, arguments : List[str]) -> None:
		raise NotImplementedError("Abstract method called")


class KioskForge(KioskClass):
	"""This class contains the 'KioskForge' code, which prepares a boot image for running 'KioskSetup' on a kiosk machine."""

	def __init__(self, homedir : str) -> None:
		KioskClass.__init__(self, homedir)
		self.version = Version("KioskForge", VERSION, COMPANY, CONTACT, TESTING)

	def saveCloudInitMetaData(self, setup : Setup, path : str) -> None:
		with TextWriter(path) as stream:
			# Write header to let the user know who generated this particular file.
			stream.write(
				"# Cloud-init meta-data file generated by %s v%s.  DO NOT EDIT!" % (self.version.program, self.version.version)
			)
			stream.write()

			# Write network-config values, copied verbatim from the Raspberry Pi 4B setup written by Raspberry Pi Imager.
			stream.write("dsmode: local")
			stream.write("instance_id: cloud-image")

	def saveCloudInitNetworkConfig(self, setup : Setup, path : str) -> None:
		with TextWriter(path) as stream:
			# Write header to let the user know who generated this particular file.
			stream.write(
				"# Cloud-init network-config file generated by %s v%s.  DO NOT EDIT!" % (
					self.version.program,
					self.version.version
				)
			)
			stream.write()

			# Write custom network-config, which uses the current target's configuration.
			stream.write("network:")
			stream.indent()
			stream.write("version: 2")
			stream.write()
			stream.write("ethernets:")
			stream.indent()
			stream.write("eth0:")
			stream.indent()
			stream.write("dhcp4: true")
			stream.write("optional: %s" % ("true" if setup.wifi_name.data else "false"))
			stream.write()
			stream.dedent(3)

			if setup.wifi_name.data:
				stream.indent()
				stream.write("wifis:")
				stream.indent()
				stream.write("renderer: networkd")
				stream.write("wlan0:")
				stream.indent()
				stream.write("dhcp4: true")
				stream.write("optional: false")
				stream.write("access-points:")
				stream.indent()
				stream.write('"%s":' % setup.wifi_name.data)
				stream.indent()
				stream.write('password: "%s"' % setup.wifi_code.data)
				stream.dedent(5)

	def saveCloudInitUserData(self, setup : Setup, target : Target, path : str) -> None:
		with TextWriter(path) as stream:
			# Compute locations of source, configuration, and output files.
			output = "/home/%s" % setup.user_name.data
			if target.kind == "PI":
				source = "/boot/firmware/KioskSetup.*"
			elif target.kind == "PC":
				source = "/cdrom/KioskSetup.*"
			else:
				raise InternalError("Unknown kiosk machine kind: %s" % target.kind)

			# Write header to let the user know who generated this particular file.
			stream.write("#cloud-config")
			stream.write(
				"# Cloud-init user-data file generated by %s v%s.  DO NOT EDIT!" % (self.version.program, self.version.version)
			)
			stream.write()

			# Write users: block, which lists the users to be created in the final kiosk system.
			stream.write("users:")
			stream.indent()
			stream.write("- name: %s" % setup.user_name.data)
			stream.indent()
			stream.write("gecos: Administrator")
			stream.write("groups: users,adm,dialout,audio,netdev,video,plugdev,cdrom,games,input,gpio,spi,i2c,render,sudo")
			stream.write("shell: /bin/bash")
			stream.write("lock_passwd: false")
			stream.write("passwd: %s" % password_crypt(setup.user_code.data))
			# NOTE: The line below is way too dangerous if somebody gets through to the shell.
			#stream.write("sudo: ALL=(ALL) NOPASSWD:ALL")
			stream.dedent()
			stream.dedent()
			stream.write()

			# Write timezone (to get date and time in logs correct).
			stream.write("timezone: %s" % setup.timezone.data)
			stream.write()

			# Write keyboard layout (I haven't found a reliable way to do this in any other way).
			stream.write("keyboard:")
			stream.indent()
			stream.write("layout: %s" % setup.keyboard.data)
			stream.write("model: pc105")
			stream.dedent()
			stream.write()

			if AUTOSTART:
				# Write commands to write a custom /usr/lib/systemd/system/KioskSetup.service file (it is enabled further below).
				stream.write("write_files:")
				stream.write("- path: /usr/lib/systemd/system/KioskSetup.service")
				stream.indent()
				stream.write("content: |")
				stream.indent()
				stream.write("[Unit]")
				stream.write("Description=KioskForge automatic configuration of new kiosk machine.")
				stream.write("After=network-online.target")
				stream.write("After=cloud-init.target")
				stream.write("After=multi-user.target")
				stream.write()
				stream.write("[Service]")
				stream.write("Type=simple")
				stream.write("ExecStart=%s/KioskSetup.py" % output)
				stream.write("StandardOutput=tty")
				stream.write("StandardError=tty")
				stream.write()
				stream.write("[Install]")
				stream.write("WantedBy=cloud-init.target")
				stream.dedent()
				stream.write("owner: 'root:root'")
				stream.write("permissions: '664'")
				stream.dedent()
				stream.write()

			# Write commands to copy and then make this script executable (this is done late in the boot process).
			stream.write("runcmd:")
			stream.indent()
			stream.write("- cp -p %s %s" % (source, output))
			stream.write("- chown %s:%s %s/KioskSetup.*" % (setup.user_name.data, setup.user_name.data, output))
			stream.write("- chmod u+x %s/KioskSetup.py" % output)
			stream.write("- chmod a-x %s/KioskSetup.cfg" % output)
			if AUTOSTART:
				stream.write("- systemctl daemon-reload")
				stream.write("- systemctl enable KioskSetup")
			stream.dedent()
			stream.write()
			del source

			# Write commands to reboot the machine once the dust settles for Cloud-Init.
			stream.write("power_state:")
			stream.indent()
			stream.write("delay: now")
			stream.write("mode: reboot")
			stream.write("message: Rebooting the system to set up the kiosk.")
			stream.dedent()
			stream.write()

			# Write commands to update and upgrade the system before we reboot the first time.
			if False:
				# TODO: Either reenable cloud-init updates or disable AutoInstall updates.
				# NOTE: Temporarily disabled it possibly causes an issue where cloud-init times out.
				# NOTE: We're rebooting with the "power_state" key above, not only in case of a kernel upgrade
				# NOTE: ("package_reboot_if_required").
				stream.write("package_update: true")
				stream.write("package_upgrade: true")
				stream.write()

			# Write commands to install and/or enable Network Time Protocol (NTP).
			stream.write("ntp:")
			stream.indent()
			stream.write("enabled: true")
			stream.dedent()
			stream.write()


	def saveAutoinstallYaml(self, setup : Setup, target : Target, path : str) -> None:
		with TextWriter(path) as stream:
			homedir = "/home/%s" % setup.user_name.data

			# Write header to let the user know who generated this particular file.
			stream.write("#cloud-config")
			stream.write(
				"# Cloud-init user-data file generated by %s v%s.  DO NOT EDIT!" % (self.version.program, self.version.version)
			)
			stream.write()

			# Write autoinstall.yaml opening tag and version info.
			stream.write("autoinstall:")
			stream.indent()
			stream.write("version: 1")

			stream.write("apt:")
			stream.indent()
			stream.write("disable_components: []")
			stream.write("fallback: offline-install")
			stream.write("geoip: true")
			stream.write("mirror-selection:")
			stream.indent()
			stream.write("primary:")
			stream.write("- country-mirror")
			stream.write("- arches: &id001")
			stream.indent()
			stream.write("- amd64")
			stream.write("- i386")
			stream.write("uri: http://archive.ubuntu.com/ubuntu/")
			stream.dedent()
			stream.write("- arches: &id002")
			stream.indent()
			stream.write("- s390x")
			stream.write("- arm64")
			stream.write("- armhf")
			stream.write("- powerpc")
			stream.write("- ppc64el")
			stream.write("- riscv64")
			stream.write("uri: http://ports.ubuntu.com/ubuntu-ports")
			stream.dedent()
			stream.dedent()
			stream.write("preserve_sources_list: false")
			stream.write("security:")
			stream.write("- arches: *id001")
			stream.indent()
			stream.write("uri: http://security.ubuntu.com/ubuntu/")
			stream.dedent()
			stream.write("- arches: *id002")
			stream.indent()
			stream.write("uri: http://ports.ubuntu.com/ubuntu-ports")
			stream.dedent()
			stream.dedent()
			stream.write("codecs:")
			stream.indent()
			stream.write("install: false")
			stream.dedent()
			stream.write("drivers:")
			stream.indent()
			stream.write("install: false")
			stream.dedent()
			stream.write("error-commands:")
			stream.indent()
			stream.write("- mkdir -p %s" % homedir)
			stream.write("- tar -czf %s/installer-logs.tar.gz /var/log/installer/" % homedir)
			stream.write("- journalctl -b > %s/installer-journal.log" % homedir)
			stream.dedent()
			stream.write("identity:")
			stream.indent()
			stream.write("hostname: %s" % setup.hostname.data)
			stream.write("realname: %s" % "Kiosk")
			stream.write("username: %s" % setup.user_name.data)
			stream.write("password: '%s'" % password_crypt(setup.user_code.data))
			stream.dedent()
			stream.write("kernel:")
			stream.indent()
			stream.write("package: linux-generic")
			stream.dedent()

			# Write keyboard configuration.
			stream.write("keyboard:")
			stream.indent()
			stream.write("layout: %s" % setup.keyboard.data)
			stream.write("toggle: null")
			stream.write("variant: ''")
			stream.dedent()

			# Write locale information.
			stream.write("locale: %s" % setup.locale.data)

			# Write network configuration.
			stream.write("network:")
			stream.indent()
			stream.write("version: 2")
			stream.write("ethernets:")
			stream.indent()
			stream.write("eth0:")
			stream.indent()
			stream.write("dhcp4: true")
			stream.write("optional: true")
			stream.dedent()
			stream.dedent()

			if setup.wifi_name.data:
				stream.write("wifis:")
				stream.indent()
				stream.write("wlp1s0:")
				stream.indent()
				stream.write("dhcp4: true")
				stream.write("optional: false")
				stream.write("access-points:")
				stream.indent()
				stream.write('"%s":' % setup.wifi_name.data)
				stream.indent()
				stream.write('password: "%s"' % setup.wifi_code.data)
				stream.dedent(4)

			stream.dedent()

			stream.write("oem:")
			stream.indent()
			stream.write("install: auto")
			stream.dedent()
			stream.write("refresh-installer:")
			stream.indent()
			stream.write("update: true")
			stream.dedent()
			stream.write("source:")
			stream.indent()
			stream.write("id: ubuntu-server")
			stream.write("search_drivers: false")
			stream.dedent()

			# Write SSH configuration settings.
			stream.write("ssh:")
			stream.indent()
			stream.write("allow-pw: false")
			stream.write("install-server: true")
			stream.write("authorized-keys:")
			stream.write("- '%s'" % setup.ssh_key.data)
			stream.dedent()

			stream.write("storage:")
			stream.indent()
			stream.write("layout:")
			stream.indent()
			stream.write("name: direct")
			stream.dedent()
			stream.dedent()

			stream.write("updates: all")

			stream.dedent()


	def main(self, logger : Logger, homedir : str, arguments : List[str]) -> None:
		# NOTE: No need for a logger in KioskForge as it does very few things and some of them interactively.

		# Output copyright information, etc.
		print(self.version.banner())
		print()

		# Check that we're running on Windows.
		if platform.system() != "Windows":
			raise KioskError("This script can currently only be run on a Windows machine")

		# Parse command-line arguments.
		if len(arguments) != 0:
			raise SyntaxError("\"KioskForge.py\"")

		# Show the main menu.
		# TODO: Warn the user against saving if the kiosk is blank.
		editor = Editor()
		setup = Setup()
		changed = False
		while True:
			try:
				# Present a menu of valid choices for the user to make.
				choices = [
					"Create new kiosk in memory",
					"Load existing kiosk from Kiosks folder",
					"Edit created or loaded kiosk",
					"Save kiosk to Kiosks folder",
					"Update Raspberry Pi Imager prepared installation media",
				]
				choice = editor.select("Select a menu choice", choices)

				# Process the requested menu command.
				kiosk = ""
				if choice == -1:
					if changed:
						print("Warning: Kiosk has unsaved changes, please save it before exiting the program")
						continue

					# Exit program.
					break
				elif choice == 0:
					# Create new kiosk.
					setup = Setup()
					changed = False
				elif choice == 1:
					# Load existing kiosks.

					# Find all kiosks in the Kiosks subfolder.
					files = glob.glob(self.homedir + os.sep + "Kiosks" + os.sep + "*" + os.sep + self.version.product + ".cfg")

					# Strip off the absolute part of the found path names, if any.
					# NOTE: MyPy kept reporting errors for perfectly valid 'map' code, so I rewrote it to classic imperative style.
					kiosks = []
					for file in files:
						kiosks.append(file[len(self.homedir + os.sep):])
					del files

					# Ask UI to let the user pick a kiosk to load.
					index = editor.select("Select kiosk to load", kiosks)
					if index == -1:
						continue

					kiosk = kiosks[index]
					setup.load(kiosk)
					changed = False
				elif choice == 2:
					# Edit kiosk.
					# Allow the user to re-edit the kiosk as long as there are errors.
					errors = []
					while True:
						changed |= editor.edit(setup)

						# Report errors detected after changing the selected kiosk.
						errors = setup.check()
						if not errors:
							break

						print()
						print("Errors(s) detected in kiosk (please correct or fill out all listed fields):")
						print()
						for error in errors:
							print("  " + error)
					del errors
				elif choice == 3:
					# Save kiosk.
					# Allow the user to save the kiosk.
					if changed:
						folder = ""
						while True:
							# Compute default for input of relative path.
							if kiosk:
								folder = os.path.dirname(kiosk)
							else:
								folder = "Kiosks" + os.sep + setup.hostname.data

							# Let the user enter his or her choice, ENTER means use default value.
							answer = input("Enter relative path (ENTER = %s): " % folder).strip()
							if answer:
								folder = answer
							del answer

							# Check that we're writing to a subfolder of 'Kiosks'.
							if not folder.startswith("Kiosks" + os.sep):
								print("Error: The relative path MUST start with 'Kiosks%s'" % os.sep)
								continue

							# Check if the output folder is a subfolder of 'Kiosks'.
							if len(folder.split(os.sep)) != 2:
								print("Error: The relative path must be a subdirectory of the 'Kiosks' folder")
								continue

							# Create new folder, if any, and save the configuration.
							os.makedirs(folder, exist_ok=True)
							setup.save(folder + os.sep + self.version.product + ".cfg", self.version)
							changed = False

							break
						del folder
					else:
						print("Kiosk not changed, no need to save it.")
				elif choice == 4:
					# Update installation media.
					# Identify the kind and path of the kiosk machine image (currently only works on Windows).
					target = Recognizer().identify()

					print()
					print(
						"Discovered %s kiosk %s %s v%s (%s) install image at %s." %
						(
							target.kind, target.product, target.edition, target.version, target.cpukind, target.basedir
						)
					)

					print()
					print("Preparing kiosk image for first boot.")

					if target.edition != "Server":
						raise KioskError("Only Ubuntu Server images are supported")

					# Append options to quiet both the kernel and systemd.
					if target.kind == "PI":
						kernel_options = KernelOptions()
						kernel_options.load(target.basedir + "cmdline.txt")
						#...Ask the kernel to shut up.
						kernel_options.append("quiet")
						#...Ask the kernel to only report errors, critical errors, alerts, and emergencies.
						kernel_options.append("log_level=3")
						#...Ask systemd to shut up.
						kernel_options.append("systemd.show_status=auto")
						kernel_options.save(target.basedir + "cmdline.txt")
					elif target.kind == "PC":
						# TODO: Figure out a way to provide kernel command-line options when targeting a PC (not done easily).
						pass
					else:
						raise InternalError("Unknown target kind: %s" % target.kind)

					# Write cloud-init or Subiquity configuration files to automate install completely.
					if target.install == "cloud-init":
						# Generate cloud-init's meta-data file from scratch (to be sure of what's in it).
						self.saveCloudInitMetaData(setup, target.basedir + "meta-data")

						# Generate cloud-init's network-config file from scratch (to be sure of what's in it).
						self.saveCloudInitNetworkConfig(setup, target.basedir + "network-config")

						# Generate Cloud-init's user-data file from scratch (to be sure of what's in it).
						self.saveCloudInitUserData(setup, target, target.basedir + "user-data")
					elif target.install == "subiquity":
						# Generate Subiquity's autoinstall.yaml file.
						self.saveAutoinstallYaml(setup, target, target.basedir + "autoinstall.yaml")
					else:
						raise KioskError("Unknown installer type: %s" % target.install)

					# Write configuration to the target.
					setup.save(target.basedir + os.sep + "KioskSetup.cfg", self.version, False)

					# Copy KioskForge.py to the target under a new name: KioskSetup.py.
					shutil.copyfile(self.homedir + os.sep + self.version.program, target.basedir + "KioskSetup.py")

					# Report success to the log.
					print()
					print("Preparation of boot image successfully completed - please eject/unmount %s safely." % target.basedir)
				else:
					raise KioskError("Unknown main menu choice: %d" % choice)
			except KioskError as that:
				print("Error: %s" % that.text)


class KioskSetup(KioskClass):
	"""This class contains the 'KioskSetup' code, which configures an Ubuntu Server 24.04.1 system to become a web kiosk."""

	def __init__(self, homedir : str) -> None:
		KioskClass.__init__(self, homedir)
		self.version = Version("KioskSetup", VERSION, COMPANY, CONTACT, TESTING)

	def main(self, logger : Logger, homedir : str, arguments : List[str]) -> None:
			# Output program banner and an empty line.
			logger.write(self.version.banner())
			logger.write()

			# Check that we're running on Linux.
			if platform.system() != "Linux":
				raise KioskError("This script is can only be run on a target Linux kiosk machine")

			# Check that we've got root privileges (instruct MyPy to ignore the Windows-only error in the next line).
			if os.name == "posix" and os.geteuid() != 0:		# type: ignore
				raise KioskError("You must be root (use 'sudo') to run this script")

			# Check that we have got an active, usable internet connection.
			index = 0
			while not internet_active() and index < 6:
				print("*** NETWORK DOWN: Waiting 5 seconds for the kiosk to come online")
				index += 1
				time.sleep(5)
			del index

			if not internet_active():
				print("*" * 78)
				print("*** FATAL ERROR: NO INTERNET CONNECTION AVAILABLE!")
				print("*** (Please check the wifi name and password - both are case-sensitive.)")
				print("*" * 78)

				raise KioskError("No active network connections detected")

			# Parse command-line arguments.
			if len(arguments) >= 2:
				raise SyntaxError("\"KioskSetup.py\" ?step\nWhere 'step' is an optional resume step from the log.")
			resume = 0
			if len(arguments) == 1:
				resume = int(arguments[0])

			# This script is launched by a systemd service, so we need to eradicate it and all traces of it (once only).
			if AUTOSTART and resume == 0:
				result = invoke("systemctl disable KioskSetup")
				if os.path.isfile("/usr/lib/systemd/system/KioskSetup.service"):
					os.unlink("/usr/lib/systemd/system/KioskSetup.service")
				if result.status != 0:
					raise KioskError("Unable to disable the KioskSetup service")

			# Load settings generated by KioskForge on the desktop machine.
			setup = Setup()
			setup.load(self.homedir + os.sep + "KioskSetup.cfg")

			# Build the script to execute.
			logger.write("Starting installation of kiosk system:")
			logger.write()
			logger.write("STEP ACTION")
			script = Script(logger, resume)

			# Set environment variable to stop dpkg from running interactively.
			os.environ["DEBIAN_FRONTEND"] = "noninteractive"

			# Set environment variable on every boot to stop dpkg from running interactively.
			lines  = TextBuilder()
			lines += 'DEBIAN_FRONTEND="noninteractive"'
			script += AppendTextAction(
				"Configuring 'apt', 'dpkg', etc. to never interact with the user.",
				"/etc/environment",
				lines.text
			)
			del lines

			# Disable interactive activity from needrestart (otherwise it could get stuck in a TUI dialogue during an upgrade).
			script += ReplaceTextAction(
				"Configuring 'needrestart' to NOT use interactive dialogues during upgrades",
				"/etc/needrestart/needrestart.conf",
				"$nrconf{restart} = 'i';",
				"$nrconf{restart} = 'a';"
			)

			# Configure 'apt' to never update package indices on its own.  We do this in a cron job below.
			script += ReplaceTextAction(
				"Configuring 'apt' to never update package indices on its own.",
				"/etc/apt/apt.conf.d/10periodic",
				'APT::Periodic::Update-Package-Lists "1";',
				'APT::Periodic::Update-Package-Lists "0";'
			)

			# Create file instructing 'apt' to never replace existing local configuration files during upgrades.
			lines  = TextBuilder()
			lines += '// Instruct dpkg to never replace existing local configuration files during upgrades.'
			lines += '// See https://raphaelhertzog.com/2010/09/21/debian-conffile-configuration-file-managed-by-dpkg/'
			lines += 'Dpkg::Options {'
			lines += '    "--force-confdef";'
			lines += '    "--force-confold";'
			lines += '}'
			script += CreateTextWithUserAndModeAction(
				"Creating 'apt' configuration file to keep existing configuration files during upgrades",
				"/etc/apt/apt.conf.d/00local",
				"root",
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines

			# Ensure NTP is enabled (already active in Ubuntu Server 24.04+).
			script += ExternalAction("Enabling Network Time Protocol (NTP)", "timedatectl set-ntp on")

			if setup.wifi_name.data != "":
				# Disable WIFI power-saving mode, which can cause WIFI instability and slow down the WIFI network a lot.
				# NOTE: I initially did this via a @reboot cron job, but it didn't work as cron was run too early.
				# NOTE: Package 'iw' is needed to disable power-saving mode on a specific network card.
				# NOTE: Package 'net-tools' contains the 'netstat' utility.
				script += InstallPackagesAction("Installing network tools to disable WiFi power-saving mode", ["iw", "net-tools"])
				lines  = TextBuilder()
				lines += "#!/usr/bin/bash"
				lines += "for netcard in `netstat -i | tail +3 | awk '{ print $1; }' | fgrep w`; do"
				lines += "    /sbin/iw $netcard set power_save off"
				lines += "done"
				script += CreateTextWithUserAndModeAction(
					"Creating script to disable power-saving on WiFi card",
					"%s/kiosk-disable-wifi-power-saving.sh" % self.homedir,
					setup.user_name.data,
					stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
					stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
					stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH,
					lines.text
				)
				del lines
				script += ExternalAction("Disabling WiFi power-saving mode", "%s/kiosk-disable-wifi-power-saving.sh" % self.homedir)

				# Create a systemd service to disable WiFi power saving on every boot.
				lines  = TextBuilder()
				lines += "[Unit]"
				lines += "Wants=network-online.target"
				lines += "After=network-online.target"
				lines += ""
				lines += "[Service]"
				lines += "Type=simple"
				lines += "ExecStart=%s/kiosk-disable-wifi-power-saving.sh" % self.homedir
				script += CreateTextWithUserAndModeAction(
					"Creating systemd unit to disable WiFi power saving on every boot",
					"/usr/lib/systemd/system/kiosk-disable-wifi-power-saving.service",
					"root",
					stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH,
					lines.text
				)
				del lines

				# Enable the new systemd unit.
				script += ExternalAction(
					"Enabling systemd service to disable WiFi power saving",
					"systemctl enable kiosk-disable-wifi-power-saving"
				)

			# TODO: Disable IPv6 as it apparently slows down Internet communication and is claimed to make the network stack unstable.
			if False:
				"""
					apt-get install -y net-tools
					TARGET=/etc/rc.local
					echo "#!/usr/bin/bash" >> $TARGET
					# NOTE: 'all' and 'default' do not always include all active network cards; apparently they are set up very early.
					echo "# Disable IPv6 on all active interfaces." >> $TARGET
					for netcard in all default `netstat -i | tail +3 | awk '{ print $1; }'`; do
						if [ -f /proc/sys/net/ipv6/conf/$netcard/disable_ipv6 ]; then
							echo sysctl -wq net.ipv6.conf.$netcard.disable_ipv6=1 >> $TARGET
						fi
					done
					chmod a+x $TARGET
					unset -v TARGET
				"""

			# Install and configure SSH server to require a key and disallow root access.
			#...Install OpenSSH server.
			script += InstallPackagesAction("Installing OpenSSH server", ["openssh-server"])

			# ...Install SSH public key so that the user can get into the box in case of errors or other issues.
			script += AppendTextAction(
				"Installing public SSH key in user's home directory",
				"%s/.ssh/authorized_keys" % self.homedir,
				setup.ssh_key.data + "\n"
			)
			#...Disable root login, if not alreadsy disabled.
			script += ReplaceTextAction(
				"Disabling root login using SSH if not already disabled.",
				"/etc/ssh/sshd_config",
				"#PermitRootLogin prohibit-password",
				"PermitRootLogin no"
			)
			#...Disable password-only authentication if not already disabled.
			script += ReplaceTextAction(
				"Requiring private SSH key to log in",
				"/etc/ssh/sshd_config",
				"#PasswordAuthentication yes",
				"PasswordAuthentication no"
			)
			#...Disable empty passwords (probably superflous, but it doesn't hurt).
			script += ReplaceTextAction(
				"Disabling empty SSH password login",
				"/etc/ssh/sshd_config",
				"#PermitEmptyPasswords no",
				"PermitEmptyPasswords no"
			)

			# Uninstall package unattended-upgrades as I couldn't get it to work even after spending many hours on it.
			# NOTE: Remove unattended-upgrades early on as it likes to interfere with APT and the package manager.
			script += PurgePackagesAction("Purging package unattended-upgrades", ["unattended-upgrades"])
			script += RemoveFolderAction("Removing remains of package unattended-upgrades", "/var/log/unattended-upgrades")

			# Assign hostname (affects logs and journals so we do it early on).
			script += ExternalAction("Setting host name", "hostnamectl set-hostname " + setup.hostname.data)

			# Install US English and user-specified locales (purge all others).
			script += ExternalAction("Configuring system locales", "locale-gen --purge en_US.UTF-8 %s" % setup.locale.data)

			# Configure system to use user-specified locale (keep messages and error texts in US English).
			script += ExternalAction(
				"Setting system locale",
				"update-locale LANG=%s LC_MESSAGES=en_US.UTF-8" % setup.locale.data
			)

			# Set timezone to use user's choice.
			script += ExternalAction("Setting timezone", "timedatectl set-timezone " + setup.timezone.data)

			# Configure and activate firewall, allowing only SSH at port 22.
			script += ExternalAction("Disabling firewall logging", "ufw logging off")
			script += ExternalAction("Allowing SSH through firewall", "ufw allow ssh")
			script += ExternalAction("Enabling firewall", "ufw --force enable")

			# Remove some packages that we don't need for kiosk mode to save some memory.
			script += PurgePackagesAction("Purging unwanted packages", ["modemmanager", "open-vm-tools"])

			# Update and upgrade the system.
			script += UpdateSystemAction()
			script += UpgradeSystemAction()
			script += UpgradeSnapsAction()

			# Install X Windows server and a window manager.
			script += InstallPackagesNoRecommendsAction(
				"Installing X Windows and OpenBox Window Manager",
				# NOTE: First element used to be 'xserver-xorg', then '"xserver-xorg-core', and no 'xorg'.
				# NOTE: Changed because of unmet dependencies; i.e. apt suddenly wouldn't install it anymore.
				["xserver-xorg", "x11-xserver-utils", "xinit", "openbox", "xdg-utils"]
			)

			# Install Pipewire audio system only if explicitly enabled.
			if setup.audio.data != 0:
				script += InstallPackagesNoRecommendsAction("Installing Pipewire audio subsystem", ["pipewire", "wireplumber"])

			# Install Chromium as we use its kiosk mode (also installs CUPS, see below).
			script += ExternalAction("Installing Chromium web browser", "snap install chromium")

			# ...Stop and disable the Common Unix Printing Server (cups) as we definitely won't be needing it on a kiosk machine.
			script += ExternalAction(
				"Purging Common Unix Printing System (cups) installed automatically with Chromium",
				"snap remove --purge cups"
			)

			# Write almost empty Chromium preferences file to disable translate.
			lines = TextBuilder()
			lines += '{"translate":{"enabled":false}}'
			script += CreateTextWithUserAndModeAction(
				"Disabling Translate feature in Chromium web browser",
				"%s/snap/chromium/common/chromium/Default/Preferences" % self.homedir,
				setup.user_name.data,
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines

			# Install 'xprintidle' used to detect X idle periods and restart the browser.
			script += InstallPackagesNoRecommendsAction(
				"Installing 'xprintidle' used to restart browser whenever idle timeout expires",
				["xprintidle"]
			)

			# Install 'xinput' used to detect touch panels and rotate them using a transformation matrix.
			if setup.screen_rotate.data != 0:
				script += InstallPackageNoRecommendsAction(
					"Installing 'xinput' to detect touch panel(s) and configure X11 to rotate them.",
					["xinput"]
				)

			# Create symbolic link from KioskSetup.py to KioskStart.py, the latter being used just below.
			script += ExternalAction("Create symlink from KioskSetup.py to KioskStart.py", "ln -s %s/KioskSetup.py %s/KioskStart.py" % (self.homedir, self.homedir))

			# Create fresh OpenBox autostart script (overwrite the existing autostart script, if any).
			# NOTE: OpenBox does not seem to honor the shebang (#!) as OpenBox always uses the 'dash' shell.
			lines  = TextBuilder()
			lines += "#!/usr/bin/dash"
			lines += "%s/KioskStart.py" % self.homedir
			script += CreateTextWithUserAndModeAction(
				"Creating OpenBox startup script",
				"%s/.config/openbox/autostart" % self.homedir,
				setup.user_name.data,
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR,
				lines.text
			)
			del lines

			# Create '~/.bash_startx.sh' script for starting X/Windows and OpenBox.
			lines  = TextBuilder()
			lines += "#!/usr/bin/bash"
			lines += "set -e"
			lines += ""
			if setup.audio.data != 0:
				lines += "# Set PipeWire audio level to user-specified percentage on a logarithmic scale."
				lines += "wpctl set-volume @DEFAULT_AUDIO_SINK@ %f" % (setup.audio.data / 100.0)
				lines += ""
			lines += "# Launch the X server into kiosk mode."
			lines += "[[ -z $DISPLAY && $XDG_VTNR -eq 1 ]] && startx -- %s" % ("-nocursor" if not setup.mouse.data else "")
			script += CreateTextWithUserAndModeAction(
				"Creating Bash startup script",
				"%s/.bash_startx" % self.homedir,
				setup.user_name.data,
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR,
				lines.text
			)
			del lines

			# Append lines to .bashrc to create 'kiosklog' function used for quickly viewing the Kiosk*.py log entries.
			lines  = TextBuilder()
			lines += ""
			lines += "# Function that displays all syslog entries made by Kiosk*.py."
			lines += "kiosklog() {"
			lines += "\t# Use 'kiosklog -p 3' only see kiosk-related errors, instead of all messages."
			lines += "\tjournalctl -o short-iso $* | grep -F Kiosk"
			lines += "}"
			script += AppendTextAction(
				"Creating kiosklog function for easier debugging of KioskSetup.py",
				"%s/.bashrc" % self.homedir,
				lines.text
			)

			# Append lines to .bashrc to run the custom startup script at automatic login.
			lines  = TextBuilder()
			lines += ""
			lines += "# Launch X11 and OpenBox into Kiosk mode."
			lines += "%s/.bash_startx" % self.homedir
			script += AppendTextAction(
				"Starting X11 startup script at automatic login",
				"%s/.bashrc" % self.homedir,
				lines.text
			)
			del lines

			# Set up automatic login for the named user.
			lines  = TextBuilder()
			lines += "[Service]"
			lines += "ExecStart="
			lines += "ExecStart=-/sbin/agetty --noissue --autologin %s %%I $TERM" % setup.user_name.data
			lines += "Type=simple"
			script += CreateTextWithUserAndModeAction(
				"Creating systemd auto-login script",
				"/etc/systemd/system/getty@tty1.service.d/override.conf",
				"root",
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines

			# Instruct snap to only upgrade at the user-specified interval.
			script += ExternalAction(
				"Instruct 'snap' to update every day at %s" % setup.snap_time.data,
				"snap set system refresh.timer=%s" % setup.snap_time.data,
			)

			# Create cron job to vacuum/compact the system logs every N days.
			if setup.vacuum_time.data != "":
				lines  = TextBuilder()
				lines += "# Cron job to vacuum (compact) the server logs every day so as to avoid the disk becoming full after years of use."
				lines += "%s %s * * *\troot\tjournalctl --vacuum-time=%dd" % (
					setup.vacuum_time.data[3:5], setup.vacuum_time.data[0:2], setup.vacuum_days.data
				)
				lines += ""
				script += CreateTextAction(
					"Creating cron job to vacuum/compact system logs every %d days" % setup.vacuum_days.data,
					"/etc/cron.d/kiosk-vacuum-logs",
					lines.text
				)
				del lines

			# Create cron job to update, upgrade, clean, and reboot the system every day at a given time.
			if setup.upgrade_time.data != "":
				lines  = TextBuilder()
				lines += "# Cron job to upgrade, clean, and reboot the system every day at %s." % setup.upgrade_time.data
				lines += '%s %s * * *\troot\tapt-get update; apt-get upgrade -y > %s/apt-upgrade.log; apt-get clean; reboot' % (
					setup.upgrade_time.data[3:5], setup.upgrade_time.data[0:2], self.homedir
				)
				lines += ""
				script += CreateTextAction(
					"Creating cron job to upgrade system every day at %s" % setup.vacuum_days.data,
					"/etc/cron.d/kiosk-upgrade-system",
					lines.text
				)
				del lines

			# Create cron job to power off the system at a given time (only usable when it is manually turned on again).
			if setup.poweroff_time.data != "":
				lines  = TextBuilder()
				lines += "# Cron job to shut down the kiosk machine nicely every day at %s." % setup.poweroff_time.data
				lines += "%s %s * * *\troot\tpoweroff" % (setup.poweroff_time.data[3:5], setup.poweroff_time.data[0:2])
				script += CreateTextAction(
					"Creating cron job to power off the system every day at %s." % setup.poweroff_time.data,
					"/etc/cron.d/kiosk-power-off",
					lines.text
				)
				del lines

			# Create swap file in case the system gets low on memory.
			if setup.swap_size.data > 0:
				script += ExternalAction(
					"Allocating swap file",
					"fallocate -l %dG /swapfile" % setup.swap_size.data,
				)
				script += ExternalAction(
					"Setting permissions (600) on new swap file",
					"chmod 600 /swapfile"
				)
				script += ExternalAction(
					"Formatting swap file",
					"mkswap /swapfile"
				)
				script += AppendTextAction(
					"Creating '/etc/fstab' entry for the new swap file",
					"/etc/fstab",
					"/swapfile\tnone\tswap\tsw\t0\t0"
				)

			# Change ownership of all files in the user's home dir to that of the user as we create a few files as sudo (root).
			script += ExternalAction(
				"Setting ownership of all files in %s's home directory to that user" % setup.user_name.data,
				"chown -R %s:%s %s" % (setup.user_name.data, setup.user_name.data, self.homedir)
			)

			# Free disk space by purging unused packages.
			script += PurgePackagesAction("Purge all unused packages to free disk space", [])

			# Free disk space by cleaning the apt cache.
			script += CleanPackageCacheAction()

			# Synchronize all changes to disk (may take a while on microSD cards).
			script += ExternalAction(
				"Flushing disk buffers before rebooting (may take a while on microSD cards)",
				"sync"
			)

			# Execute the script.
			result = script.execute()
			if result.status != 0:
				raise KioskError(result.output)

			# NOTE: The reboot takes place immediately, control probably never returns from the 'execute()' method below!
			logger.write("**** SUCCESS - REBOOTING SYSTEM INTO KIOSK MODE")
			RebootSystemAction().execute()


# Returns the total number of seconds (with a fraction) of idle time since the X server was last busy.
def x_idle_time() -> float:
	result = invoke("xprintidle")
	if result.status != 0:
		raise KioskError("Unable to get idle time from X Windows")
	return int(result.output) / 1000


# Discards all UTF-8 characters from the given string and returns the result.
def utf8_discard(text : str) -> str:
	result = ""
	for ch in text:
		if ord(ch) >= 0x80:
			continue
		result += ch
	return result


# Strips trailing part beginning with 'substring'.
def string_strip_from_substring(text : str, substring : str) -> str:
	pos = text.find(substring)
	if pos == -1:
		return text
	return text[:pos]


# NOTE: This function returns ALL xinput touch devices but a predefined list.  I haven't found a better method just yet.
def xinput_get_pointer_devices() -> List[str]:
	# Ask 'xinput' for a list of all known pointing and keyboard devices.
	result = invoke("xinput list")

	# Attempt to parse the lame 'xinput list' format, which uses non-ASCII characters.
	lines = output.split("\n")

	# Remove embedded UTF-8 characters.
	lines = list(map(utf8_discard, lines))

	# Remove trailing garbage.
	lines = list(map(lambda x: string_strip_from_substring(x, 'id='), lines))

	# Strip leading whitespace from each line.
	lines = list(map(lambda x: x.strip(" \t"), lines))

	# Filter out the stuff we don't need.
	store = False
	found = []
	for line in lines:
		if line == "Virtual core pointer":
			store = True
		elif line == "Virtual core keyboard":
			store = False
		elif store:
			found.append(line)

	# Discard the 'Virtual core XTEST pointer' entry.
	found = filter(lambda x: x != 'Virtual core XTEST pointer', found)

	# Discard Raspberry Pi's builtin HDMI devices.
	found = filter(lambda x: x[:9] != "vc4-hdmi-", found)

	# Convert to a list.
	found = list(found)

	return found


class KioskStart(KioskClass):
	"""This class contains the 'KioskStart' code, which starts Chromium, monitors it, and restarts it if necessary."""

	def __init__(self, homedir : str) -> None:
		KioskClass.__init__(self, homedir)
		self.version = Version("KioskStart", VERSION, COMPANY, CONTACT, TESTING)

	def main(self, logger : Logger, homedir : str, arguments : List[str]) -> None:
		# Check that we're running on Linux.
		if platform.system() != "Linux":
			raise KioskError("This script is can only be run on a target Linux kiosk machine")

		# Parse command-line arguments.
		if len(arguments) != 0:
			raise SyntaxError('"KioskStart.py"')

		# Load settings generated by KioskForge on the desktop machine.
		setup = Setup()
		setup.load(self.homedir + os.sep + "KioskSetup.cfg")

		# Fetch timeout value (0 = disabled, other = number of seconds) from configuration file.
		timeout = setup.idle_timeout.data

		process = None
		try:
			# Disable any form of X screen saver/screen blanking/power management.
			for xset in [ "xset s off", "xset s noblank", "xset -dpms"]:
				subprocess.check_call(shlex.split(xset), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			del xset

			# Rotate the screen, if applicable (TODO: This may possibly depend on whether we're doing a PI or PC build).
			if setup.rotate_screen.data != 0:
				command  = TextBuilder()
				command += "xrandr"
				command += "--output"
				command += "HDMI-1"
				command += "--rotate"
				command += { 0 : 'normal', 1 : 'left', 2 : 'inverted', 3 : 'right' }[setup.rotate_screen.data]
				subprocess.check_call(command.list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				del command

				# Identify and configure all non-reserved pointing devices using 'xinput'.
				matrices = {
					0 : '1 0 0 0 1 0 0 0 1',
					1 : '0 -1 1 1 0 0 0 0 1',
					2 : '-1 0 1 0 -1 1 0 0 1',
					3 : '0 1 0 -1 0 1 0 0 1'
				}
				devices = xinput_get_devices()
				for device in devices:
					command  = TextBuilder()
					command += "xinput"
					command += "set-prop"
					command += "'%s'" % device
					command += "'Coordinate Transformation Matrix'"
					command += "'%s'" % matrices[setup.rotate_screen.data]
					subprocess.check_call(command.list)
				del command

			# Build the Chromium command line with a horde of options (I don't know which ones work and which don't...).
			# NOTE: Chromium does not complain about any of the options listed below!
			command  = TextBuilder()
			command += shutil.which("chromium") or "chromium"
			command += "--kiosk"
			command += "--fast"
			command += "--fast-start"
			command += "--start-maximised"
			command += "--noerrdialogs"
			command += "--no-first-run"
			command += "--enable-pinch"
			command += "--overscroll-history-navigation=disabled"
			command += "--disable-features=TouchpadOverscrollHistoryNavigation"
			command += "--overscroll-history-navigation=0"
			command += "--disable-restore-session-state"
			command += "--disable-infobars"
			command += "--disable-crashpad"
			command += "%s" % setup.website.data
			cmdlist  = command.list
			del command

			# Forever launch Chromium, possibly terminate it, and restart it again if terminated or crashed.
			while True:
				# Launch Chromium in the background as a detached process.
				try:
					process = subprocess.Popen(cmdlist, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				except subprocess.SubprocessError:
					raise KioskError("Unable to launch Chromium")
				except OSError as that:
					raise KioskError(that.strerror)

				# Let Chromium start before we begin to check if it has been idle for too long.
				time.sleep(15)

				# Loop forever, launching Chromium and terminating it if it "times out" (becomes idle for N seconds).
				while True:
					# Wait one second between checking if Chromium should be restarted.
					time.sleep(1)

					# If Chromium has exited (crashed), exit to outer loop to restart it.
					if process.poll():
						logger.error("Restarting Chromium after crash.")
						break

					# If X has been idle for more than N seconds, terminate Chromium and exit to outer loop to restart it.
					current = x_idle_time()
					if timeout and current >= timeout:
						process.terminate()
						process = None

						if TESTING:
							logger.write("Restarting Chromium after idle timeout: timeout=%f, current=%f." % (timeout, current))

						# Reset X's idle timer to ensure that inaccuracies do not accumulate over time.
						subprocess.check_call(shlex.split("xset s reset"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

						break
		finally:
			# Terminate Chromium if it is still running.
			if process and not process.poll():
				process.terminate()


if __name__ == "__main__":
	# NOTE: This script can be invoked as 'KioskForge.py' (Windows only), as 'KioskSetup.py', or as 'KioskStart.py'.
	# NOTE: 'KioskForge.py' copies itself to 'KioskSetup.py' on the kiosk machine and then uses cloud-init to launch it.
	# NOTE: 'KioskSetup.py' creates a symbolic link between 'KioskStart.py' and 'KioskSetup.py' so OpenBox:autostart can launch it.
	# NOTE: 'KioskStart.py' launches Chrome, monitors it, and restarts it if necessary.

	# Assume failure until success has been achieved.
	status = EXIT_FAILURE

	with Logger() as logger:
		# Compute full path of this script, which we pass into the constructor of the KioskXxx class.
		(origin, basename) = os.path.split(os.path.abspath(sys.argv[0]))

		# Extract the name of the class to create an instance of, by stripping the extension (could be either '.py' or '.pyc').
		(class_, extension) = os.path.splitext(basename)

		try:
			# Exit gracefully if the extension is not .py - we need this to be a true Python script on Linux to execute it.
			if extension != ".py":
				raise KioskError("This script must end in '.py'")

			try:
				# Create an instance of the class whose name matches the basename, without extension, of this script.
				instance = globals()[class_](origin)

				# Attempt to invoke the main() method on the newly created instance.
				instance.main(logger, origin, sys.argv[1:])

				# Signal success to the client (caller).
				status = EXIT_SUCCESS
			except (AttributeError, KeyError):
				# We get here if there's no class named X or the instantiated class does not have a main() method.
				logger.error("This script must be called 'KioskForge.py', 'KioskSetup.py', or 'KioskStart.py'")
		except ArgumentError as that:
			text = ""
			if that.index != -1:
				text += "(#%d) " % that.index
			text += "Error: "
			text += that.text
			logger.error("%s" % text)
		except SyntaxError as that:
			logger.error("Syntax: %s" % that.text)
		except InternalError as that:
			logger.error("Internal Error: %s" % that.text)
		except KioskError as that:
			logger.error("Error: %s" % that.text)
		except Exception as that:
			text = ""
			if hasattr(that, "message"):
				text = that.message
			elif hasattr(that, "strerror"):
				text = that.strerror
			logger.error("Unknown Error: %s" % text)
			raise

	# If not running from a console, wait for a keypress so that the user can read the output.
	if platform.system() == "Windows" and not "PROMPT" in os.environ:
		print()
		input("Press ENTER to continue and close this window")

	sys.exit(status)

