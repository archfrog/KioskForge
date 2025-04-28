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


class Error(Exception):
	"""The base class for all exceptions."""

	def __init__(self, text : str) -> None:
		Exception.__init__(self)
		self.__text = text

	@property
	def text(self) -> str:
		return self.__text


class CommandError(Error):
	"""Exception used to signal that a syntax error, when invoking a KioskForge script, has been detected."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class InputError(Error):
	"""Base exception thrown if an error not related to a field occurs during input or output, otherwise a FieldError is thrown."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class TextFileError(InputError):
	"""Exception used to report an error in a specific line of a specific file."""

	def __init__(self, file : str, line : int, text : str) -> None:
		InputError.__init__(self, text)
		self.__file = file
		self.__line = line

	@property
	def file(self) -> str:
		return self.__file

	@property
	def line(self) -> int:
		return self.__line

	def __str__(self) -> str:
		result = "(" + self.__file
		if self.__line:
			result += ":" + str(self.__line)
		result += ") Error: " + self.text
		return result


class FieldError(InputError):
	"""Exception thrown if an input/output error is related to a particular option ("field")."""

	def __init__(self, field : str, text : str) -> None:
		InputError.__init__(self, text)
		self.__field = field

	@property
	def field(self) -> str:
		return self.__field


class KioskError(Error):
	"""Generic exception used for all kinds of errors while running this script."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class InternalError(Error):
	"""Exception used to signal that an internal error has been discovered."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)

