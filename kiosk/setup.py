# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import time

from kiosk.convert import STRING_TO_BOOLEAN
from kiosk.errors import *
from kiosk.logger import TextWriter
from kiosk.version import Version


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


class Record(object):
	"""Simple class that allows constructing a tree of records to represent a configuration file."""

	def __init__(self) -> None:
		pass


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
			result.append("Warning: 'comment' value is missing from configuration")
		if self.hostname.data == "":
			result.append("Warning: 'hostname' value is missing from configuration")
		if self.timezone.data == "":
			result.append("Warning: 'timezone' value is missing from configuration")
		if self.keyboard.data == "":
			result.append("Warning: 'keyboard' value is missing from configuration")
		if self.locale.data == "":
			result.append("Warning: 'locale' value is missing from configuration")
		if self.website.data == "":
			result.append("Warning: 'website' value is missing from configuration")
		if self.user_name.data == "":
			result.append("Warning: 'user_name' value is missing from configuration")
		if self.user_code.data == "":
			result.append("Warning: 'user_code' value is missing from configuration")
		if self.ssh_key.data == "":
			result.append("Warning: 'ssh_key' value is missing from configuration")
		if self.wifi_name.data != "" and self.wifi_code.data == "":
			result.append("Warning: 'wifi_code' value is missing from configuration")
		if self.snap_time.data == "":
			result.append("Warning: 'snap_time' value is missing from configuration")
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



