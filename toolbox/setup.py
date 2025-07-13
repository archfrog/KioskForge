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

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Any, Dict, List

import re
import secrets
import time

from toolbox.convert import BOOLEANS
from toolbox.errors import Error, FieldError, InputError, InternalError, KioskError, TextFileError
from toolbox.logger import Logger, TextWriter
from toolbox.version import Version


class Field:
	"""Base class for configuration fields; these are name/data/hint triplets."""

	def __init__(self, name : str, hint : str) -> None:
		self.__name = name
		self.__hint = hint

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
		if not data:
			raise FieldError(self.name, f"Missing value in field '{self.name}'")

		try:
			self.__data = BOOLEANS[data.lower()]
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
		return "optional string"

	def parse(self, data : str) -> None:
		self.__data = data


class StringField(OptionalStringField):
	"""Derived class that implements a mandatory string field."""

	def __init__(self, name : str, data : str, hint : str) -> None:
		OptionalStringField.__init__(self, name, data, hint)

	@property
	def type(self) -> str:
		return "mandatory, non-empty string"

	def parse(self, data : str) -> None:
		if not data:
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
		if not data:
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
		return "optional regular expression"

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
		return "optional time string of the form HH:MM"

	def parse(self, data : str) -> None:
		if not data:
			OptionalStringField.parse(self, data)
			return

		try:
			# Let time.strptime() validate the time value.
			time.strptime(data, "%H:%M")
			OptionalStringField.parse(self, data)
		except ValueError as that:
			raise FieldError(self.name, f"Invalid time specification: {data}") from that


class Fields:
	"""The new and improved(tm) fields manager, which uses a dictionary rather than 50+ data members."""

	def __init__(self, version : Version) -> None:
		self.__version = version
		self.__fields : Dict[str, Field] = {}
		self.__edited : Dict[str, bool] = {}

	# Make the class backwards compatible with the old 'Setup' class, which used a named data member for each option.
	def __getattr__(self, name : str) -> Field:
		if name not in self.__fields:
			raise InternalError(f"Unknown field: {name}")
		return self.__fields[name]

	# Make the += operator available to add new fields to the 'Fields' instance.
	def __iadd__(self, field : Field) -> Any:
		# Check that the field hasn't been created before.
		if field.name in self.__fields:
			raise InternalError(f"Field already exists: {field.name}")

		# Create the field.
		self.__fields[field.name] = field

		# Create an new, false entry in the 'self.__edited' dictionary.
		self.__edited[field.name] = False

		return self

	def assign(self, name : str, data : str) -> None:
		"""Attempts to assign a field by calling the 'parse()' method on it and then save the edit in 'self.__edited'."""
		self.__fields[name].parse(data)
		self.__edited[name] = True

	def edited(self) -> bool:
		result = False
		for value in self.__edited.values():
			result |= value
		return result

	def unedit(self) -> None:
		for name in self.__edited:
			self.__edited[name] = False

	def load_list(self, path : str, allow_redefinitions : bool = False) -> List[TextFileError]:
		# Returns a list of errors encountered while loading the .kiosk file.
		result = []

		# Clear the dictionary of edits so that we can detect unassigned fields.
		self.unedit()

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

				# Check that the field is known to us.
				if not name in self.__fields:
					raise InputError(f"Unknown field: {name}")

				# Check that the field has not already been assigned more than once (it is set first time by the constructor).
				if not allow_redefinitions and self.__edited[name]:
					raise InputError(f"Illegal redefinition of field '{name}'")

				# Attempt to assign the field and its new value, while keeping track of edits.
				self.assign(name, data)
			except Error as that:
				result.append(TextFileError(path, number, that.text))
			except AttributeError:
				result.append(TextFileError(path, number, f"Unknown field ignored: {name}"))

		# Check that all fields were assigned by the configuration files.
		for name in self.__fields:
			if not self.__edited[name]:
				result.append(TextFileError(path, 0, f"Field never assigned: {name}"))

		# From a client point of view, the kiosk is without edits just after having been loaded.
		self.unedit()

		return result

	def load_safe(self, logger : Logger, path : str) -> None:
		errors = self.load_list(path)
		if errors:
			for error in errors:
				logger.error(str(error))
			print()
			raise KioskError(f"{len(errors)} error(s) detected while reading file '{path}'")

	def save(self, path : str) -> None:
		# Generate KioskForge.cfg.
		with TextWriter(path) as stream:
			stream.write(f"# {self.__version.product} v{self.__version.version} kiosk definition file.")
			stream.write("# Please edit this file using your favorite text editor such as Notepad.")
			stream.write("")

			for name in self.__fields:
				# Fetch the next field to output.
				field = getattr(self, name)

				# Write a line of asterisks to indicate start of the field's help text.
				stream.write(f"#{78 * '*'}")

				# Write the field name and its type.
				stream.write(f"# Option '{field.name}' ({field.type})")
				stream.write("#")

				# Write the hint text.
				lines = field.hint.split("\n")
				for line in lines:
					stream.write(f"# {line}")
				del lines

				# Write a line of asterisks to indicate end of the field's help text.
				stream.write(f"#{78 * '*'}")

				# Write the field name and data.
				stream.write(f"{field.name}={field.text}")

				# Output an empty line between fields and after the last field.
				stream.write("")

		# The kiosk is pristine, unedited and without changes just after having been saved.
		self.unedit()


def hostname_create(basename : str) -> str:
	"""Creates a unique host name of the form '{basename}{number}', where number is an integer from zero to 2**16."""
	number = secrets.randbelow(2**16)
	return f"{basename}{number}"


# Source: https://stackoverflow.com/a/63160092
def password_create(length : int) -> str:
	return secrets.token_urlsafe(length)
