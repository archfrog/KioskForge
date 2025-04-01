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

import re
import time

from toolbox.convert import BOOLEANS, KEYBOARD_REGEX
from toolbox.errors import *
from toolbox.logger import TextWriter
from toolbox.version import Version


class Field(object):
	"""Base class for configuration fields; these are name/data pairs."""

	def __init__(self, name : str, hint : str) -> None:
		self.__name = name
		self.__hint = hint

	@property
	def hint(self) -> str:
		return self.__hint

	@property
	def name(self) -> str:
		return self.__name

	def parse(self, data : str) -> None:
		raise NotImplementedError("Abstract method called")


class BooleanField(Field):
	"""Derived class that implements a boolean field."""

	def __init__(self, name : str, hint : str) -> None:
		Field.__init__(self, name, hint)
		self.__data = False

	@property
	def data(self) -> bool:
		return self.__data

	def parse(self, data : str) -> None:
		if len(data) == 0:
			raise FieldError(self.name, "Field cannot be blank")

		try:
			self.__data = BOOLEANS[data.lower()]
		except KeyError:
			raise FieldError(self.name, "Invalid value entered")
		except ValueError as that:
			raise FieldError(self.name, str(that))


class NaturalField(Field):
	"""Derived class that implements a natural (unsigned integer) field."""

	def __init__(self, name : str, hint : str, lower : int, upper : int) -> None:
		Field.__init__(self, name, hint)
		self.__data = 0
		self.__lower = lower
		self.__upper = upper

	@property
	def data(self) -> int:
		return self.__data

	def parse(self, data : str) -> None:
		if not data or data[0] == '-':
			raise FieldError(self.name, "Invalid value entered: %s " % data)

		try:
			value = int(data)

			if value < self.__lower or value > self.__upper:
				raise FieldError(self.name, "Value outside bounds (%d through %d)" % (self.__lower, self.__upper))

			self.__data = value
		except ValueError as that:
			raise FieldError(self.name, str(that))


class StringField(Field):
	"""Derived class that implements a string field."""

	def __init__(self, name : str, hint : str) -> None:
		Field.__init__(self, name, hint)
		self.__data = ""

	@property
	def data(self) -> str:
		return self.__data

	def parse(self, data : str) -> None:
		self.__data = data


class PasswordField(StringField):
	"""Derived class that checks a Linux password."""

	def __init__(self, name : str, hint : str) -> None:
		StringField.__init__(self, name, hint)

	def parse(self, data : str) -> None:
		# Report error if the password string is empty.
		if data == "":
			raise FieldError(self.name, "Password cannot be empty")

		# Disallow passwords starting with a dollar sign, including encrypted passwords.
		if data[0] == '$':
			raise FieldError(self.name, "Password cannot begin with a dollar sign ($)")

		# Apparently, the maximum length of an input password to 'bcrypt' is 72 characters.
		if len(data) > 72:
			raise FieldError(self.name, "Password too long - cannot exceed 72 characters")

		# Finally, store the encrypted password.
		StringField.parse(self, data)


class RegexField(StringField):
	"""Derived class that implements a string field validated by a regular expression."""

	def __init__(self, name : str, hint : str, regex : str) -> None:
		StringField.__init__(self, name, hint)
		self.__regex = regex

	@property
	def regex(self) -> str:
		return self.__regex

	def parse(self, data : str) -> None:
		if not re.fullmatch(self.__regex, data):
			raise FieldError(self.name, "Value does not match validating regular expression: %s" % data)
		StringField.parse(self, data)


class TimeField(StringField):
	"""Derived class that implements a time (HH:MM) field."""

	def __init__(self, name : str, hint : str) -> None:
		StringField.__init__(self, name, hint)

	def parse(self, data : str) -> None:
		if data == "":
			StringField.parse(self, data)
			return

		try:
			# Let time.strptime() validate the time value.
			time.strptime(data, "%H:%M")
			StringField.parse(self, data)
		except ValueError:
			raise FieldError(self.name, "Invalid time specification: %s" % data)


class Setup(object):
	"""Class that defines, loads, and saves the configuration of a given kiosk machine."""

	def __init__(self) -> None:
		self.comment       = StringField("comment", "A descriptive comment for the kiosk machine.")
		self.device        = RegexField("device", "The target device type (pi4, pi4b, pc).", "(pi4|pi4b|pc)")
		self.type          = RegexField("type", "The type of kiosk to make: cli, x11 or web.", "(cli|x11|web)")
		self.command       = StringField("command", "An URL to display (type: web) or a command to run upon login (type: cli or x11).")
		self.hostname      = RegexField("hostname", "The unqualified host name (e.g., 'kiosk01').", r"[A-Za-z0-9-]{1,63}")
		self.timezone      = StringField("timezone", "The time zone (e.g., 'Europe/Copenhagen').")
		self.keyboard      = RegexField("keyboard", "The keyboard layout (e.g., 'dk').", KEYBOARD_REGEX)
		self.locale        = StringField("locale", "The locale (e.g., 'da_DK.UTF-8').")
		self.sound_card    = RegexField("sound_card", "The sound card to use (pi4+: none, jack, hdmi1, or hdmi2).", "(none|jack|hdmi1|hdmi2)")
		self.sound_level   = NaturalField("sound_level", "The logarithmic audio level (0 through 100, only valid if 'sound_card' is not 'none').", 0, 100)
		self.mouse         = BooleanField("mouse", "If the mouse should be enabled (y/n or 1/0).")
		self.user_name     = StringField("user_name", "The user name of the non-root administrative user (e.g., 'user').")
		self.user_code     = PasswordField("user_code", "The password for the user (e.g., 'dumsey3rumble').")
		self.ssh_key       = StringField("ssh_key", "The public SSH key for accessing the kiosk using the 'ssh' command.")
		self.wifi_name     = StringField("wifi_name", "The WiFi network (case sensitive!) (e.g., 'MyWiFi', blank = no WiFi).")
		self.wifi_code     = StringField("wifi_code", "The password for WiFi access (case sensitive!) (e.g., 'stay4out!', blank = no password).")
		self.snap_time     = StringField("snap_time", "The daily period of time that snap updates software (e.g., '10:00-10:30').")
		self.swap_size     = NaturalField("swap_size", "The size in gigabytes of the swap file (0 = none).", 0, 128)
		self.vacuum_time   = TimeField("vacuum_time", "The time of day to vacuum system logs (blank = never)")
		self.vacuum_days   = NaturalField("vacuum_days", "The number of days to retain system logs for (1 through 365, only used if 'vacuum_time' is set)", 1, 365)
		self.upgrade_time  = TimeField("upgrade_time", "The time of day to upgrade the system (blank = never)")
		self.poweroff_time = TimeField("poweroff_time", "The time of day to power off the system (blank = never)")
		self.idle_timeout  = NaturalField("idle_timeout", "The number of seconds of idle time before Chromium is restarted (0 = never)", 0, 24 * 60 * 60)
		self.orientation   = NaturalField("orientation", "Screen orientation: 0 = default, 1 = rotate left, 2 = flip upside-down, 3 = rotate right", 0, 3)
		self.user_folder   = StringField("user_folder", "A folder that is copied to ~ on the kiosk (for websites, etc.) (blank = none)")
		self.user_packages = StringField("user_packages", "A space-separated list of extra packages to install while forging of the kiosk (blank = none)")

	def check(self) -> List[str]:
		result = []

		if False:
			for name in vars(self):
				field = getattr(self, name)
				result += field.check()

		if self.comment.data == "":
			result.append("Warning: 'comment' value not specified")
		if self.device.data == "":
			result.append("Warning: 'device' value not specified")
		if self.type.data == "":
			result.append("Warning: 'type' value not specified")
		if self.command.data == "":
			result.append("Warning: 'command' value not specified")
		if self.hostname.data == "":
			result.append("Warning: 'hostname' value not specified")
		if self.timezone.data == "":
			result.append("Warning: 'timezone' value not specified")
		if self.keyboard.data == "":
			result.append("Warning: 'keyboard' value not specified")
		if self.locale.data == "":
			result.append("Warning: 'locale' value not specified")
		if self.sound_card.data == "":
			result.append("Warning: 'sound_card' value not specified")
		if self.user_name.data == "":
			result.append("Warning: 'user_name' value not specified")
		if self.user_code.data == "":
			result.append("Warning: 'user_code' value not specified")
		if self.ssh_key.data == "":
			result.append("Warning: 'ssh_key' value not specified")
		if self.wifi_name.data != "" and self.wifi_code.data == "":
			result.append("Warning: 'wifi_code' value not specified")
		if self.snap_time.data == "":
			result.append("Warning: 'snap_time' value not specified")
		return result

	def load(self, path : str) -> None:
		# Read in the specified file and split it into individual lines.
		lines = open(path, "rt", encoding="utf-8").read().split('\n')

		# Process each line in turn.
		for line in lines:
			# Remove trailing whitespaces.
			line = line.rstrip()

			# Ignore empty lines and comment lines.
			if line == "" or line[0] in ['#', ';']:
				continue

			# Process unsupported section marker.
			if line[0] == '[' and line[-1] == ']':
				raise InputError("Sections not supported in configuration (.cfg) file")

			# Parse name/data pair (name=data).
			index = line.find('=')
			if index == -1:
				raise InputError("Missing delimiter (=) in line: %s" % line)
			( name, data ) = ( line[:index].strip(), line[index + 1:].strip() )

			# Store the field.
			try:
				getattr(self, name).parse(data)
			except AttributeError:
				raise FieldError(name, "Unknown setting in configuration file: %s" % name)

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

			for name in vars(self):
				field = getattr(self, name)
				stream.write("# %s" % field.hint)
				stream.write("%s=%s" % (field.name, field.data))

