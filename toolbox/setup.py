1#!/usr/bin/env python3
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

from toolbox.convert import BOOLEANS, KEYBOARDS, KEYBOARD_REGEX
from toolbox.errors import FieldError, InputError
from toolbox.locales import LOCALES
from toolbox.logger import TextWriter
from toolbox.timezones import TIMEZONES
from toolbox.version import Version


class Field:
	"""Base class for configuration fields; these are help/name/data triplets."""

	def __init__(self, name : str, help : str) -> None:
		self.__name = name
		self.__help = help

	@property
	def help(self) -> str:
		return self.__help

	@property
	def name(self) -> str:
		return self.__name

	def parse(self, data : str) -> None:
		raise NotImplementedError("Abstract method called")


class BooleanField(Field):
	"""Derived class that implements a boolean field."""

	def __init__(self, name : str, data : bool, help : str) -> None:
		Field.__init__(self, name, help)
		self.__data = data

	@property
	def data(self) -> bool:
		return self.__data

	@property
	def text(self) -> str:
		return "true" if self.__data else "false"

	@property
	def type(self) -> str:
		return "boolean"

	def parse(self, data : str) -> None:
		if len(data) == 0:
			raise FieldError(self.name, "Field cannot be blank")

		try:
			self.__data = BOOLEANS[data.lower()]
		except KeyError as that:
			raise FieldError(self.name, "Invalid value entered") from that
		except ValueError as that:
			raise FieldError(self.name, str(that)) from that


class NaturalField(Field):
	"""Derived class that implements a natural (unsigned integer) field."""

	def __init__(self, name : str, data : int, help : str, lower : int, upper : int) -> None:
		Field.__init__(self, name, help)
		self.__data = data
		self.__lower = lower
		self.__upper = upper

	@property
	def data(self) -> int:
		return self.__data

	@property
	def text(self) -> str:
		return str(self.__data)

	@property
	def type(self) -> str:
		return "natural"

	def parse(self, data : str) -> None:
		if not data or data[0] == '-':
			raise FieldError(self.name, f"Invalid value entered: {data}")

		try:
			value = int(data)

			if value < self.__lower or value > self.__upper:
				raise FieldError(self.name, f"Value outside bounds ({self.__lower} through {self.__upper})")

			self.__data = value
		except ValueError as that:
			raise FieldError(self.name, str(that)) from that


class OptionalStringField(Field):
	"""Derived class that implements an optional string field."""

	def __init__(self, name : str, data : str, help : str) -> None:
		Field.__init__(self, name, help)
		self.__data = data

	@property
	def data(self) -> str:
		return self.__data

	@property
	def text(self) -> str:
		return self.__data

	@property
	def type(self) -> str:
		return "optional string"

	def parse(self, data : str) -> None:
		self.__data = data


class StringField(OptionalStringField):
	"""Derived class that implements a mandatory string field."""

	def __init__(self, name : str, data : str, help : str) -> None:
		OptionalStringField.__init__(self, name, data, help)

	@property
	def type(self) -> str:
		return "optional string"

	def parse(self, data : str) -> None:
		if data == "":
			raise FieldError(self.name, "Field cannot be blank")

		self.__data = data


class OptionalMultilineStringField(OptionalStringField):
	"""Derived class that implements an optional multi-line string field."""

	def __init__(self, name : str, data : str, help : str) -> None:
		OptionalStringField.__init__(self, name, data, help)

	@property
	def text(self) -> str:
		return base().text.replace("\n", "|")

	def parse(self, data : str) -> None:
		data = data.replace("|", "\n")
		OptionalStringField.parse(self, data)


class PasswordField(StringField):
	"""Derived class that checks a Linux password."""

	def __init__(self, name : str, data : str, help : str) -> None:
		StringField.__init__(self, name, data, help)

	@property
	def type(self) -> str:
		return "password"

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

	def __init__(self, name : str, data : str, help : str, regex : str) -> None:
		StringField.__init__(self, name, data, help)
		self.__regex = regex

	@property
	def regex(self) -> str:
		return self.__regex

	@property
	def type(self) -> str:
		return "regular expression"

	def parse(self, data : str) -> None:
		if not re.fullmatch(self.__regex, data):
			raise FieldError(self.name, f"Value does not match validating regular expression: {data}")
		StringField.parse(self, data)


class TimeField(OptionalStringField):
	"""Derived class that implements a time (HH:MM) field."""

	def __init__(self, name : str, data : str, help : str) -> None:
		OptionalStringField.__init__(self, name, data, help)

	@property
	def type(self) -> str:
		return "time string"

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
A descriptive comment for the kiosk machine, which describes its intended
usage as well as important notes about the kiosk.

You should probably record the permanent LAN IP address, if any, here.
Talk to your network administrator to get a static DCHP lease.
""".strip()


CPU_BOOST_HELP = """
If the CPU should be overclocked.

This option depends on the target Raspberry Pi system.  For Raspberry Pi
4Bs, it will increase the processing speed (CPU clock rate) of the target
kiosk by 20 percent from 1.5 gigahertz to 1.8 gigahertz.  This translates to
considerable extra performance at the cost of a signficicantly hotter CPU.
If processor speed matters, and cooling is good or heat is not a significant
issue, then you should enable this setting.

This setting is most useful with 'web' type kiosks as these need lots of
power to process complex websites and display these.

This option only has an effect on Raspberry Pi kiosks!  PCs are not easily
overclocked beyond what happens automatically.
""".strip()


DEVICE_HELP = """
Specifies the hardware type of the kiosk.  Valid values are:

1. pi4b: Raspberry Pi 4B with at least 2 gigabytes of RAM.
2. pc  : IBM PC compatible machine with at least 4 gigabytes of RAM.

This setting affects the 'sound_card' and 'cpu_boost' options as follows:

1. 'sound_card' depends entirely on the target device type.  See the
   'sound_card' option for more information.
2. 'cpu_boost' can only be activated for Raspberry Pi kiosks.  PCs commonly
    adjust their CPU's speed dynamically depending on load.
""".strip()


HOSTNAME_HELP = """
The unqualified host name, which may consists of US English letters, digits,
and dashes (-).  It must be 1 to 63 characters long.

If this field is left blank, KioskForge will generate a random name of the
form 'kiosk-NNNNNNNNN', where 'NNNNNNNNN' is a decimal number.

Most commonly, you don't need to worry about the kiosk host name at all.
""".strip()


IDLE_TIMEOUT_HELP = """
The number of seconds of idle time before Chromium is restarted.  A value
between 0 (disabled) and 86.400 (one full day).

This option has no effect for kiosk types other than 'web'.

Some visitors to kiosks like to sabotage the kiosk, which is the primary
reason why this option exists.  Also, it is nice to be able to reset a web
 kiosk back to its home page after a given period of no activity from users.
""".strip()


KEYBOARD_HELP = """
The keyboard layout.  This is primarily important to those who access the
kiosk remotely using SSH and also the web browser, if any.

The complete list of valid keyboard layouts is as follows:
""".strip()
KEYBOARD_HELP += 2 * "\n"
for layout, region in KEYBOARDS.items():
	KEYBOARD_HELP += f"    {layout:5}  {region}\n"


LOCALE_HELP = """
The locale to use on the kiosk machine.

The locale affects the display of dates, currencies, the default sorting
order, etc.

You should pick the most narrow match, say "fr_CA" over "fr" if you're a
Canadian living in a region of Canada where French is the main language.

The complete list of valid locales is as follows:
""".strip()
LOCALE_HELP += 2 * "\n"
for locale in LOCALES:
	LOCALE_HELP += f"    {locale}\n"


MOUSE_HELP = """
If the mouse should be enabled.

Valid values are 'true' (enabled) and 'false' (disabled).

You generally want to avoid enabling the mouse on kiosks with touch screens
as this makes the mouse cursor visible to the user.
""".strip()


POWEROFF_TIME_HELP = """
The time of day to power off the system.

The value blank disables this option, otherwise it must be a time string of
the form HH:MM, which is the hour and minute of when the operation is done.

This option is primarily intended for environments where there are no
visitors to the kiosk during the night.  In such cases, the kiosk needs to be
power on by a time switch.

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

Please notice that this setting affects both screens without a touch panel
and screens with a touch panel.
""".strip()


SOUND_CARD_HELP = """
The sound card to use, if any.

This depends entirely on the target system:

1. pi4b: none, jack, hdmi1, or hdmi2.
2. pi5 : none, jack, hdmi1, or hdmi2.
3. pc  : none or ???.

If you don't need any audio in your kiosk, you should use the value 'none'.

Please notice that the jack stick on the Pi4B and Pi5 requires amplification.
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

If blank, SSH access is disabled and you'll need a monitor and a keyboard to
log into the kiosk machine.

The key can be generated using the 'ssh-keygen' command, which is part of
Linux but also available on numerous public websites that you can use to
generate an SSH key pair.  Just do a google of "ssh-keygen online".

To access the kiosk using SSH, you can use 'Putty' (GUI) or 'Windows OpenSSH'
(CLI aka not GUI).

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

Please be aware that the time zone affects time stamps in logs, in the web
browser, and so on.

Use the most specific, precise time zone from the list below.  There are time
zones for all regions of Earth, just search for "Africa/" or "Europe/", etc.

A complete, valid list of the currently supported timezones is as follows:
""".strip()
TIMEZONE_HELP += 2 * "\n"
for timezone in TIMEZONES:
	TIMEZONE_HELP += f"    {timezone}\n"


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

If blank, this option is disabled.

During upgrades, the following things take place:

1. System logs are reduced to the size given in the 'vacuum_size' option.
2. If there is no network access, the system maintenance ends here.
3. Snaps are upgraded.
4. Ubuntu packages are upgraded.
5. The system is rebooted.
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

If set to blank, nothing will be copied.  Else the given folder is copied.

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
generally don't need to specify a non-blank value for this setting.
""".strip()


USER_NAME_HELP = """
The user name of the non-root primary Linux user.

This is the user who runs X11, Chromium and/or any custom user apps.

This user is very central to the kiosk as everything, but the forge process
itself, runs under this user.

For most users, though, you just need to specify a valid name and only worry
about it if you use SSH to access the kiosk.
""".strip()


USER_PACKAGES_HELP = """
A space-separated list of user packages to install when forging of the kiosk.

If blank, this feature is disabled.

This option is rarely necessary, but if you are forging a 'cli' or 'x11' type
kiosk, you may need to install additional Ubuntu packages while forging the
kiosk.
""".strip()


VACUUM_SIZE_HELP = """
The maximum size, in megabytes, of system log files.

This value ranges from 0 (= unlimited) through 4096 (4 gigabytes).

A good value that provides room for perhaps one month of logs is 256.

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

This setting is case sensitive so that "Pass" is different from "pass".

If left blank and the 'wifi_name' setting is non-blank, the Wi-Fi connection
will be assumed to be public and open to everybody (without a password).
""".strip()


WIFI_NAME_HELP = """
The Wi-Fi network name (SSID).

This setting is case sensitive so that "MyWiFi" is different from "mywifi".

If left blank, Wi-Fi is disabled altogether and a Wi-Fi network is not
configured.  In this case, 'wifi_code' will be ignored.
""".strip()


class Setup:					# pylint: disable=too-many-instance-attributes
	"""Class that defines, loads, and saves the configuration of a given kiosk machine."""

	def __init__(self) -> None:
		# NOTE: Only fields whose type begins with "Optional" are truly optional and can be blank.  All other fields must be set.
		self.comment         = OptionalMultilineStringField("comment", "", COMMENT_HELP)
		self.device          = RegexField("device", "pi4b", DEVICE_HELP, "(pi4b|pc)")
		self.type            = RegexField("type", "web", TYPE_HELP, "(cli|x11|web)")
		self.command         = StringField("command", "", COMMAND_HELP)
		self.hostname        = RegexField("hostname", "", HOSTNAME_HELP, r"[A-Za-z0-9-]{1,63}")
		self.timezone        = StringField("timezone", "UTC", TIMEZONE_HELP)
		self.keyboard        = RegexField("keyboard", "en", KEYBOARD_HELP, KEYBOARD_REGEX)
		self.locale          = StringField("locale", "en_US.UTF-8", LOCALE_HELP)
		self.sound_card      = RegexField("sound_card", "none", SOUND_CARD_HELP, "(none|jack|hdmi1|hdmi2)")
		self.sound_level     = NaturalField("sound_level", 80, SOUND_LEVEL_HELP, 0, 100)
		self.mouse           = BooleanField("mouse", False, MOUSE_HELP)
		self.user_name       = StringField("user_name", "kiosk", USER_NAME_HELP)
		self.user_code       = PasswordField("user_code", "", USER_CODE_HELP)
		self.ssh_key         = StringField("ssh_key", "", SSH_KEY_HELP)
		self.wifi_name       = OptionalStringField("wifi_name", "", WIFI_NAME_HELP)
		self.wifi_code       = OptionalStringField("wifi_code", "", WIFI_CODE_HELP)
		self.wifi_boost      = BooleanField("wifi_boost", True, WIFI_BOOST_HELP)
		self.cpu_boost       = BooleanField("cpu_boost", True, CPU_BOOST_HELP)
		self.swap_size       = NaturalField("swap_size", 4, SWAP_SIZE_HELP, 0, 128)
		self.vacuum_size     = NaturalField("vacuum_size", 256, VACUUM_SIZE_HELP, 0, 4096)
		self.upgrade_time    = TimeField("upgrade_time", "", UPGRADE_TIME_HELP)
		self.poweroff_time   = TimeField("poweroff_time", "", POWEROFF_TIME_HELP)
		self.idle_timeout    = NaturalField("idle_timeout", 0, IDLE_TIMEOUT_HELP, 0, 24 * 60 * 60)
		self.screen_rotation = RegexField("screen_rotation", "none", SCREEN_ROTATION_HELP, "(none|left|flip|right)")
		self.user_folder     = OptionalStringField("user_folder", "", USER_FOLDER_HELP)
		self.user_packages   = OptionalStringField("user_packages", "", USER_PACKAGES_HELP)

	def check(self) -> List[str]:
		result = []

		# TODO: Implement generic mechanism for checking all named fields without hard-coding the checks.
		if False:
			for name in vars(self):
				field = getattr(self, name)
				result += field.check()
		else:
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

		return result

	def load(self, path : str) -> None:
		# Read in the specified file and split it into individual lines.
		with open(path, "rt", encoding="utf-8") as stream:
			lines = stream.read().split('\n')

		# Process each line in turn.
		for line in lines:
			# Remove trailing whitespaces.
			line = line.rstrip()

			# Ignore empty lines and comment lines.
			if line == "" or line[0] in ['#', ';']:
				continue

			# Process unsupported section marker.
			if line[0] == '[' and line[-1] == ']':
				raise InputError("Sections not supported in kiosk files")

			# Parse name/data pair (name=data).
			index = line.find('=')
			if index == -1:
				raise InputError(f"Missing delimiter (=) in line: {line}")
			( name, data ) = ( line[:index].strip(), line[index + 1:].strip() )

			# Store the field.
			try:
				getattr(self, name).parse(data)
			except AttributeError as that:
				raise FieldError(name, f"Unknown option ignored: {name}") from that

	def save(self, path : str, version : Version) -> None:
		# Generate KioskForge.cfg.
		with TextWriter(path) as stream:
			stream.write(f"# {version.product} v{version.version} kiosk definition file.")
			stream.write("# Please feel free to edit this file using your favorite text editor.")
			stream.write("")

			names = list(vars(self))
			for name in names:
				# Fetcht the next field to output.
				field = getattr(self, name)

				# Write a line of stars/asterisk to indicate start of option.
				stream.write(f"#{78 * '*'}")

				# Write the field name and its type.
				stream.write(f"# Option '{field.name}' ({field.type}):")
				stream.write("#")

				# Write the help text.
				lines = field.help.split("\n")
				for line in lines:
					stream.write(f"# {line}")
				del lines

				# Write the field name and data.
				stream.write(f"{field.name}={field.text}")

				# Output a blank line before next option, if not the last option in the list.
				if name != names[-1]:
					stream.write("")

