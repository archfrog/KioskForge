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
from typing import Any, Dict, List

import re
import secrets
import time

from toolbox.convert import BOOLEANS, KEYBOARDS
from toolbox.errors import Error, FieldError, InputError, InternalError, KioskError, TextFileError
from toolbox.locales import LOCALES
from toolbox.logger import Logger, TextWriter
from toolbox.timezones import TIMEZONES
from toolbox.version import Version


class Field:
	"""Base class for configuration fields; these are name/data/hint triplets."""

	def __init__(self, name : str, hint : str) -> None:
		self.__name = name
		self.__hint = hint
		self._set   = False

	@property
	def data(self) -> Any:
		raise NotImplementedError("Abstract method called")

	@property
	def hint(self) -> str:
		return self.__hint

	@property
	def name(self) -> str:
		return self.__name

	@property
	def changed(self) -> bool:
		return self._set

	@property
	def text(self) -> str:
		raise NotImplementedError("Abstract method called")

	def parse(self, data : str) -> None:
		raise NotImplementedError("Abstract method called")


class BooleanField(Field):
	"""Derived class that implements a boolean field."""

	def __init__(self, name : str, data : str, hint : str) -> None:
		self.__data = False
		Field.__init__(self, name, hint)

		self.parse(data)

	@property
	def data(self) -> bool:
		return self.__data

	@property
	def text(self) -> str:
		return "true" if self.__data else "false"

	@property
	def type(self) -> str:
		return "boolean value: 'true' or 'false'"

	def parse(self, data : str) -> None:
		if len(data) == 0:
			raise FieldError(self.name, f"Missing value in field '{self.name}'")

		try:
			self.__data = BOOLEANS[data.lower()]
			self._set = True
		except KeyError as that:
			raise FieldError(self.name, f"Invalid value in field '{self.name}': {data}") from that
		except ValueError as that:
			raise FieldError(self.name, str(that)) from that


class NaturalField(Field):
	"""Derived class that implements a natural (unsigned integer) field."""

	def __init__(self, name : str, data : str, hint : str, lower : int, upper : int) -> None:
		self.__data  = 0
		self.__lower = lower
		self.__upper = upper
		Field.__init__(self, name, hint)

		self.parse(data)

	@property
	def data(self) -> int:
		return self.__data

	@property
	def text(self) -> str:
		return str(self.__data)

	@property
	def type(self) -> str:
		return "natural number: integer without a sign"

	def parse(self, data : str) -> None:
		if not data:
			raise FieldError(self.name, f"Missing value in field '{self.name}'")
		if data[0] == '-':
			raise FieldError(self.name, f"Invalid positive integer in field '{self.name}': {data}")

		try:
			try:
				value = int(data)
			except Exception as that:
				raise FieldError(self.name, f"Invalid integer in field '{self.name}': {data}") from that

			if value < self.__lower or value > self.__upper:
				raise FieldError(self.name, f"Value outside bounds ({self.__lower}..{self.__upper}) in field '{self.name}': {data}")

			self.__data = value

			self._set = True
		except ValueError as that:
			raise FieldError(self.name, str(that)) from that


class OptionalStringField(Field):
	"""Derived class that implements an optional string field."""

	def __init__(self, name : str, data : str, hint : str) -> None:
		self.__data = ""
		Field.__init__(self, name, hint)

		self.parse(data)

	@property
	def data(self) -> str:
		return self.__data

	@property
	def text(self) -> str:
		return self.__data

	@property
	def type(self) -> str:
		return "optional, possibly empty string"

	def parse(self, data : str) -> None:
		self.__data = data
		self._set = True


class StringField(OptionalStringField):
	"""Derived class that implements a mandatory string field."""

	def __init__(self, name : str, data : str, hint : str) -> None:
		OptionalStringField.__init__(self, name, data, hint)

	@property
	def type(self) -> str:
		return "mandatory, non-empty string"

	def parse(self, data : str) -> None:
		if data == "":
			raise FieldError(self.name, f"Missing value in field '{self.name}'")
		OptionalStringField.parse(self, data)


class ChoiceField(StringField):
	"""Derived class that implements a choice from a predefined list of valid choices."""

	def __init__(self, name : str, data : str, hint : str, choices : List[str]) -> None:
		self.__choices = choices
		StringField.__init__(self, name, data, hint)

	@property
	def type(self) -> str:
		return "mandatory value from list of valid values"

	def parse(self, data : str) -> None:
		if data not in self.__choices:
			raise FieldError(self.name, f"Invalid value in field '{self.name}': {data}")

		StringField.parse(self, data)


class PasswordField(StringField):
	"""Derived class that checks a Linux password."""

	def __init__(self, name : str, data : str, hint : str) -> None:
		StringField.__init__(self, name, data, hint)

	@property
	def type(self) -> str:
		return "mandatory, non-empty password"

	def parse(self, data : str) -> None:
		# Report error if the password string is empty.
		if data == "":
			raise FieldError(self.name, "Password cannot be empty")

		# Disallow passwords starting with a dollar sign, including encrypted passwords.
		if data[0] == '$':
			raise FieldError(self.name, "Password cannot begin with a dollar sign ($)")

		# Apparently, the maximum length of a password input to 'bcrypt' is 72 characters.
		if len(data) > 72:
			raise FieldError(self.name, "Password too long - cannot exceed 72 characters")

		# Finally, store the encrypted password.
		StringField.parse(self, data)


class RegexField(StringField):
	"""Derived class that implements a string field validated by a regular expression."""

	def __init__(self, name : str, data : str, hint : str, regex : str) -> None:
		self.__regex = regex
		StringField.__init__(self, name, data, hint)

	@property
	def regex(self) -> str:
		return self.__regex

	@property
	def type(self) -> str:
		return "mandatory regular expression: a valid pattern"

	def parse(self, data : str) -> None:
		if not data:
			raise FieldError(self.name, f"Missing value in field '{self.name}'")

		if not re.fullmatch(self.__regex, data):
			raise FieldError(self.name, f"Invalid value in field '{self.name}': {data}")

		StringField.parse(self, data)


class OptionalRegexField(RegexField):
	"""Derived class that implements an optional string field validated by a regular expression."""

	def __init__(self, name : str, data : str, hint : str, regex : str) -> None:
		RegexField.__init__(self, name, data, hint, regex)

	@property
	def type(self) -> str:
		return "optional, possibly empty regular expression"

	def parse(self, data : str) -> None:
		if not data:
			OptionalStringField.parse(self, data)
			return

		RegexField.parse(self, data)


class OptionalTimeField(OptionalStringField):
	"""Derived class that implements an optional time (HH:MM) field."""

	def __init__(self, name : str, data : str, hint : str) -> None:
		OptionalStringField.__init__(self, name, data, hint)

	@property
	def type(self) -> str:
		return "optional, possibly empty time string of the form HH:MM"

	def parse(self, data : str) -> None:
		if data == "":
			OptionalStringField.parse(self, data)
			return

		try:
			# Let time.strptime() validate the time value.
			time.strptime(data, "%H:%M")
			OptionalStringField.parse(self, data)
		except ValueError as that:
			raise FieldError(self.name, f"Invalid time specification: {data}") from that


COMMAND_HELP = """
This is the action that the kiosk should take when it starts up.

For 'web' type kiosks (see 'type'), this option specifies the local or
remote URL to display in Chromium.

For 'x11' and 'cli' type kiosks, this option specifies an actual Linux
command (script or binary) that is launched upon starting up.  The latter
two types are used for custom solutions that do not necessarily require a
web browser, such as a Pi kiosk that detects motion and then plays a sound.
""".strip()


COMMENT_HELP = """
A comment for your records about the kiosk machine.

Please describe the kiosk's intended usage and other important notes.

You should probably record the permanent LAN IP address, if any, here.
Talk to your network administrator to get a static DCHP lease.

A vertical bar (|) indicates a new line, this way you can write multiple
lines of text in a single line in the 'comment' field.
""".strip()


CPU_BOOST_HELP = """
If the CPU should be overclocked.

This option currently only works with Raspberry Pi 4B targets.

Enabling the option will increase the processing speed (CPU clock rate) of
the target kiosk by 20 percent from 1.5 gigahertz to 1.8 gigahertz.  This
translates to extra performance at the cost of a signficantly hotter CPU.
If processor speed matters, and cooling is good or heat is not a
significant issue, then you should enable this setting.

This setting is most useful with 'web' type kiosks as these need lots of
power to process complex websites and display these.
""".strip()


DEVICE_HELP = """
Specifies the hardware type of the kiosk.  Valid values are:

1. pi4b: Raspberry Pi 4B with at least 2 GB RAM.
2. pi5 : Raspberry Pi 5 with at least 2 GB RAM.
3. pc  : IBM PC compatible machine with at least 4 GB RAM.

This setting affects the 'sound_card' and 'cpu_boost' options as follows:

1. 'sound_card' depends entirely on the target device type.  See the
   'sound_card' option for more information.
2. 'cpu_boost' can only be activated for Raspberry Pi 4B kiosks.  PCs
    commonly adjust their CPU's speed dynamically depending on load.
""".strip()


HOSTNAME_HELP = """
The unqualified host name, which may consists of US English letters, digits,
and dashes (-).  It must be 1 to 63 characters long.

Most commonly, you don't need to worry about the kiosk host name at all.

If this field is left empty, the forge process will automatically create a
host name of the form "kioskforge-NNNNNNNNN", where NNNNNNNNN is a number
in the range zero through 2,147,483,638.

IMPORTANT:
You should never have two machines with the same host name on a local area
network (LAN).  This may cause issues with Windows and other systems.
""".strip()


IDLE_TIMEOUT_HELP = """
The number of seconds of idle time before Chromium is restarted.  A value
in the range 0 (disabled) to 86.400 (one full day).

This option has no effect for kiosk types other than 'web'.

Some visitors to kiosks like to sabotage the kiosk, which is the primary
reason why this option exists.  Also, it is nice to be able to reset a web
kiosk back to its starting page after a given period of user inactivity.
""".strip()


KEYBOARD_HELP = """
The keyboard layout.  This is primarily important to those who access the
kiosk remotely using SSH and also the web browser, if any.

The complete list of valid keyboard layouts can be found at:

https://kioskforge.org/keyboards.html
""".strip()


LOCALE_HELP = """
The locale to use on the kiosk machine.

The locale affects the display of dates, currencies, the default sorting
order, etc.

You should pick the most narrow match, say "fr_CA" over "fr" if you're a
Canadian living in a region of Canada where French is the main language.

Please notice that KioskForge has only been tested with UTF-8 locales:
Those that end in '.UTF-8'.  No warranties are given for other locales.

A complete list of valid locales can be found at:

https://manpages.ubuntu.com/manpages/noble/man3/DateTime::Locale::Catalog.3pm.html
""".strip()


MOUSE_HELP = """
If the mouse should be enabled.

Valid values are 'true' (enabled) and 'false' (disabled).

You generally want to avoid enabling the mouse on kiosks with touch screens
as this makes the mouse cursor visible to the user.
""".strip()


POWEROFF_TIME_HELP = """
The time of day to power off the system.

An empty string disables this option, otherwise it must be a time string of
the form HH:MM, which is the hour and minute of when the operation is done.

This option is primarily intended for environments where there are no
visitors to the kiosk during the night.  In such cases, the kiosk needs to be
powered on by a time switch.

If you use a time switch, please remember to use this option to gracefully
shut down the kiosk.  Most computers benefit from being shut down gracefully
rather than abruptly by loss of power.

IMPORTANT:
Raspberry Pis do not normally have a built-in real-time clock (RTC) so they
need network access to set the system time after they have rebooted.
""".strip()


SCREEN_ROTATION_HELP = """
Specify rotation of screen and/or touch panel.

The valid values are:

1. none : The screen is mounted straight up and is not rotated in any way.
2. left : The screen has been rotated 90 degrees to the left.
3. flip : The screen has been mounted upside-down.
4. right: The screen has been rotated 90 degrees to the right.

Please notice that this setting affects both standard screens (without a
touch panel) and screens with a touch panel.
""".strip()


SOUND_CARD_HELP = """
The sound card to use, if any.

This depends entirely on the target system:

1. pi4b: none, jack, hdmi1, or hdmi2.
2. pi5 : none, hdmi1, or hdmi2.
3. pc  : none or ???.

If you don't need any audio in your kiosk, you should use the value 'none'.

Please notice that the jack stick on the Pi4B requires amplification.
""".strip()


SOUND_LEVEL_HELP = """
The logarithmic audio level ranging from 0 through 100.

This value is only valid if 'sound_card' is different from 'none'.

The value 0 should only be used when 'sound_card' has been set to 'none' as
it effectively disables audio altogether.

A good value to use, which should avoid clipping (reduction of audio
quality), is 80 if 'sound_card' has been set to something other than 'none'.
If 'sound_card' is 'none', this value will be completely ignored.
""".strip()


SSH_KEY_HELP = """
The public SSH key for accessing the kiosk using the 'ssh' command.

If empty, SSH access is disabled and you'll need a monitor and a keyboard to
log into the kiosk machine.

The key can be generated using the 'ssh-keygen' command, which is part of
Linux but also available on numerous public websites that you can use to
generate an SSH key pair.  Just do a google of "ssh-keygen online".

To access the kiosk using SSH, you can use 'Putty' (GUI) or 'Windows OpenSSH'
(CLI/non-GUI).

IMPORTANT:
If you lose your private key, you cannot access the kiosk using SSH anymore.
""".strip()


SWAP_SIZE_HELP = """
The size in gigabytes of the system swap file, if any.

The value zero (0) disables the swap file altogether.  A typical size of the
swap file is twice that of the size of system RAM.  However, a value of 4
(gigabytes) should be sufficient for most kiosks.

You need to ensure that there is sufficient space on the installation medium
(MicroSD card or USB key) to store the swap file itself.  As a rule of thumb,
you can safely use 4 gigabytes on an installation medium that is 16 gigabytes
or larger.  The Linux operating system itself uses less than 8 gigabytes but
there must always be ample room for system logs, fetched upgrades, and so on.
""".strip()


TIMEZONE_HELP = """
The time zone of the kiosk.

This is typically the local time zone of where the kiosk is located.

Please be aware that the time zone affects time stamps in logs, the time
seen by the the web browser, and so on.

Use the most specific, precise time zone from the list below.  There are time
zones for all regions of Earth, just search for "Africa/" or "Europe/", etc.

The complete list of valid time zones can be found at:

https://kioskforge.org/timezones.html
""".strip()


TYPE_HELP = """
The type of kiosk.

The valid values are:

1. web: A "standard" kiosk that displays a given website.
2. x11: A custom, X11 app installed during forging of the kiosk.
3. cli: A custom, console app installed during forging of the kiosk.

The website URL or custom command is specified using the 'command' option.

The 'web' type is by far the most commonly used type, but the 'cli' type is
very useful for things like making a designated kiosk that starts playing a
given sound whenever somebody approaches the kiosk machine (using a motion
detector).
""".strip()


UPGRADE_TIME_HELP = """
The time of day to upgrade the system.

If empty, this option is disabled.

During upgrades, the following things take place:

1. System logs are reduced to the size given in the 'vacuum_size' option.
2. If there is no network access, the system maintenance ends here.
3. Snaps are upgraded.
4. Ubuntu packages are upgraded.
5. The system is rebooted.

Please notice that the maintenance process gracefully handles lack of
internet.  In that case, no upgrades will be attemped downloaded, etc.,
and the system will not be rebooted as there is no reason to do so.
""".strip()


USER_CODE_HELP = """
The password for the user whose name is given in the 'user_name' option.

There is technically no maximum limit to the length of the password, but you
should always use between 16 and 132 characters.

This setting is of very little signficance if you provide an SSH public key
using the 'ssh_key' option as this installs a key file on the kiosk so that
you can log into the kiosk using SSH without entering a password.  However,
the password will still be required to perform administrative commands on the
kiosk.  For this reason, you should use an SSH public key and a fairly safe
password.

If you opt to not enable the secure SSH access method, you should provide a
secure password of minimum 32 random characters so as to not allow hackers
into the kiosk.
""".strip()


USER_FOLDER_HELP = """
The path of a user folder to copy from the host to the kiosk.

If empty, nothing will be copied, otherwise the given folder is copied.

A "user folder" is a custom folder that may contain various files needed by
the kiosk, but which are not part of KioskForge.

For instance, a 'web' type kiosk that browses local files only, need these
files to be copied from the host to the kiosk.  Similarly, 'cli' or 'x11'
type kiosks also need the custom app to be copied to the kiosk.

The last part of the path specified, which is relative to the main '.kiosk'
file that contains the kiosk configuration, is used as the name of the folder
that's being created on the kiosk.

For instance, if you set 'user_folder' to 'Website', then the local folder
'Website', in the same folder as the main configuration file, will be copied
to the kiosk so that a new folder '/home/username/Website' is created and
populated by the files it contains on the host.

If you are creating a 'web' type kiosk that browses a remote website, you
generally don't need to specify a value for this setting.
""".strip()


USER_NAME_HELP = """
The user name of the non-root primary Linux user.

Technically, a user name can be from 1 to 256 characters, but most Linux
tools only a maximum of 32 characters, so this is the limit in KioskForge.
The user name may only consist of US letters, digits, and underscores (_).

This is the user who runs X11, Chromium and/or any custom user apps.

This user is very central to the kiosk as everything, but the forge process
itself, runs under this user.

For most users, though, you just need to specify a valid name and only worry
about it if you use SSH to access the kiosk.
""".strip()


USER_PACKAGES_HELP = """
A space-separated list of user packages to install when forging of the kiosk.

If empty, this feature is disabled.

This option is rarely necessary, but if you are forging a 'cli' or 'x11' type
kiosk, you may need to install additional Ubuntu packages while forging the
kiosk.
""".strip()


VACUUM_SIZE_HELP = """
The maximum size, in megabytes, of system log files.

This value ranges from 0 (= unlimited) through 4096 (4 gigabytes).

A good value that provides room for weeks of logging of a kiosk is 256.

System logs are cleaned out as the first step of the mandatory daily
maintenance controlled by the 'upgrade_time' option.
""".strip()


WIFI_BOOST_HELP = """
If Wi-Fi power-saving should be enabled.

If 'true', the kiosk will be configured to NOT use power-saving on its Wi-Fi
network card.  This means two things: The kiosk will use slightly more power
and the kiosk will access the internet quite a bit faster.

If your kiosk is a 'web' type kiosk, you should probably enable this option.
In most other cases, this option has no significant effect and should be
disabled.
""".strip()


WIFI_CODE_HELP = """
The password to the Wi-Fi network, if any.

A Wi-Fi password may consist of 8 to 63 extended characters, but it is
advisable to only use printable ASCII characters to be able to enter
the password in various operating systems and/or tools.

This setting is case sensitive so that "Pass" is different from "pass".

If empty and the 'wifi_name' setting is non-empty, the Wi-Fi connection
will be assumed to be public and open to everybody (without a password).
""".strip()


WIFI_NAME_HELP = """
The Wi-Fi network name (SSID).

A Wi-Fi WPK (password) may consists of 1 to 32 characters of unspecified
value.  In other words, you can use pretty much anything.  However, it is
advisable to only use ASCII characters so as to make it practical to use
the password and also avoid breaking or confusing supporting tools.

This setting is case sensitive so that "MyWiFi" is different from "mywifi".

If empty, Wi-Fi is disabled altogether and no Wi-Fi network is configured.
In this case, 'wifi_code' will be ignored.
""".strip()


class Options:
	"""Class that loads and saves a client-defined configuration file."""

	def __init__(self) -> None:
		self.__options : Dict[str, Field] = {}

	# Make the class backwards compatible with the old 'Setup' class, which used a named data member for each option.
	def __getattr__(self, name : str) -> Field:
		if name not in self.__options:
			raise InternalError(f"Unknown option: {name}")
		return self.__options[name]

	# Make the += operator available to add new options to the 'Options' instance.
	def __iadd__(self, option : Field) -> Any:
		if option.name in self.__options:
			raise InternalError(f"Option already exists: {option.name}")
		self.__options[option.name] = option
		return self

	def load_list(self, path : str, allow_redefinitions : bool = False) -> List[TextFileError]:
		# Returns a list of errors encountered while loading the .kiosk file.
		result = []

		# Read in the specified file and split it into individual lines.
		with open(path, "rt", encoding="utf-8") as stream:
			lines = stream.read().split('\n')

		# Process each line in turn.
		number = 0
		for line in lines:
			# Increment the line number, used for error reporting.
			number += 1

			# Remove trailing whitespaces.
			line = line.rstrip()

			# Ignore empty lines and comment lines.
			if line == "" or line[0] in ['#', ';']:
				continue

			# Append some exceptions to the 'result' list of errors detected while parsing the file.
			try:
				# Process unsupported section marker.
				if line[0] == '[' and line[-1] == ']':
					raise InputError("Sections not supported in kiosk files")

				# Parse name/data pair (name=data).
				index = line.find('=')
				if index == -1:
					raise InputError("Missing delimiter (=) in line")
				( name, data ) = ( line[:index].strip(), line[index + 1:].strip() )

				# Fetch the named field or throw exception AttributeError if non-existent.
				field = getattr(self, name)

				# Check that the field has not already been assigned (set).
				if not allow_redefinitions and field.changed:
					raise InputError(f"Illegal redefinition of field '{name}'")

				# Attempt to parse the field's right-hand-side (its data).
				field.parse(data)
			except Error as that:
				result.append(TextFileError(path, number, that.text))
			except AttributeError:
				result.append(TextFileError(path, number, f"Unknown option ignored: {name}"))
		return result

	def load_safe(self, logger : Logger, path : str) -> None:
		errors = self.load_list(path)
		if errors:
			for error in errors:
				logger.error(str(error))
			print()
			raise KioskError(f"{len(errors)} error(s) detected while reading file '{path}'")

	def save(self, path : str, version : Version) -> None:
		# Generate KioskForge.cfg.
		with TextWriter(path) as stream:
			stream.write(f"# {version.product} v{version.version} kiosk definition file.")
			stream.write("# Please edit this file using your favorite text editor such as Notepad.")
			stream.write("")

			for name in self.__options:
				# Fetch the next field to output.
				field = getattr(self, name)

				# Write a line of asterisks to indicate start of option's help text.
				stream.write(f"#{78 * '*'}")

				# Write the field name and its type.
				stream.write(f"# Option '{field.name}' ({field.type}):")
				stream.write("#")

				# Write the hint text.
				lines = field.hint.split("\n")
				for line in lines:
					stream.write(f"# {line}")
				del lines

				# Write a line of asterisks to indicate end of of option's help text.
				stream.write(f"#{78 * '*'}")

				# Write the field name and data.
				stream.write(f"{field.name}={field.text}")

				# Output an empty line between options and after the last option.
				stream.write("")


def hostname_create(basename : str) -> str:
	"""Creates a unique host name of the form 'basename-number', where number is an integer in the range zero through 2**31."""
	number = secrets.randbelow(2**31)
	return f"{basename}-{number}"


# Source: https://stackoverflow.com/a/63160092
def password_create(length : int) -> str:
	return secrets.token_urlsafe(length)


class Setup(Options):
	"""The new and improved(tm) option manager, which uses a dictionary rather than 50+ data members."""

	def __init__(self) -> None:
		Options.__init__(self)

		# NOTE: Only fields whose type begins with "Optional" are truly optional and can be empty.  All other fields must be set.
		self += OptionalStringField("comment", "", COMMENT_HELP)
		self += ChoiceField("device", "pi4b", DEVICE_HELP, ["pi4b", "pi5", "pc"])
		self += ChoiceField("type", "web", TYPE_HELP, ["cli", "x11", "web"])
		self += StringField("command", "https://google.com", COMMAND_HELP)
		self += OptionalRegexField("hostname", "", HOSTNAME_HELP, r"[A-Za-z0-9-]{1,63}")
		self += ChoiceField("timezone", "America/Los_Angeles", TIMEZONE_HELP, TIMEZONES)
		self += ChoiceField("keyboard", "us", KEYBOARD_HELP, list(KEYBOARDS.keys()))
		self += ChoiceField("locale", "en_US.UTF-8", LOCALE_HELP, LOCALES)
		self += ChoiceField("sound_card", "none", SOUND_CARD_HELP, ["none", "jack", "hdmi1", "hdmi2"])
		self += NaturalField("sound_level", "80", SOUND_LEVEL_HELP, 0, 100)
		self += BooleanField("mouse", "false", MOUSE_HELP)
		self += RegexField("user_name", "kiosk", USER_NAME_HELP, r"[A-Za-z0-9_]{1,32}")
		self += PasswordField("user_code", password_create(32), USER_CODE_HELP)
		self += OptionalStringField("ssh_key", "", SSH_KEY_HELP)
		self += OptionalRegexField("wifi_name", "", WIFI_NAME_HELP, r".{1,32}")
		self += OptionalRegexField("wifi_code", "", WIFI_CODE_HELP, r"[\u0020-\u007e\u00a0-\u00ff]{8,63}")
		self += BooleanField("wifi_boost", "true", WIFI_BOOST_HELP)
		self += BooleanField("cpu_boost", "true", CPU_BOOST_HELP)
		self += NaturalField("swap_size", "4", SWAP_SIZE_HELP, 0, 128)
		self += NaturalField("vacuum_size", "256", VACUUM_SIZE_HELP, 0, 4096)
		self += OptionalTimeField("upgrade_time", "05:00", UPGRADE_TIME_HELP)
		self += OptionalTimeField("poweroff_time", "", POWEROFF_TIME_HELP)
		self += NaturalField("idle_timeout", "0", IDLE_TIMEOUT_HELP, 0, 24 * 60 * 60)
		self += ChoiceField("screen_rotation", "none", SCREEN_ROTATION_HELP, ["none", "left", "flip", "right"])
		self += OptionalStringField("user_folder", "", USER_FOLDER_HELP)
		self += OptionalStringField("user_packages", "", USER_PACKAGES_HELP)

