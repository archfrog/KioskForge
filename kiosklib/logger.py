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
from typing import Any

import os
import sys
import types

from kiosklib.errors import InternalError

# Try to import syslog (Linux only).
if sys.platform == "linux":
	import syslog				# pylint: disable=E0401
	SYSLOG_LOG_ERR = syslog.LOG_ERR
	SYSLOG_LOG_INFO = syslog.LOG_INFO
else:
	# NOTE: Dummy values used to make the code simpler on Windows and MyPy stop choking.
	SYSLOG_LOG_ERR = 1
	SYSLOG_LOG_INFO = 2

class TextWriter:
	"""Simple text stream writer class that supports 'with' and indentation."""

	def __init__(self, path : str, tabs : str = "  ") -> None:
		self.__path = path
		# The size, in levels, of the indentation.
		self.__size = 0
		# The output stream.
		self.__stream = open(self.__path, "wt", encoding="utf-8")		# pylint: disable=consider-using-with
		# The string that makes up one level of indentation.
		self.__tabs = tabs

	@property
	def path(self) -> str:
		return self.__path

	def __enter__(self) -> Any:
		"""Required to support the 'with instance as name: ...' exception wrapper syntactic sugar."""
		return self

	def __exit__(
		self,
		exception_type : type[BaseException] | None,
		exception_value : BaseException | None,
		traceback : types.TracebackType | None
	) -> None:
		"""Required to support the 'with instance as name: ...' exception wrapper syntactic sugar."""
		self.__stream.close()

	def indent(self, size : int = 1) -> None:
		self.__size += size

	def dedent(self, size : int = 1) -> None:
		if self.__size - size < 0:
			raise InternalError("Attempt to dedent below level of indent")
		self.__size -= size

	def _write(self, text : str) -> None:
		self.__stream.write(text + "\n")
		self.__stream.flush()

	def write(self, text : str = "") -> None:
		"""Writes one or more complete lines to the output device."""
		lines = text.split(os.linesep)
		for line in lines:
			self._write(self.__size * self.__tabs + line)


class Logger:
	"""Class that implements the multi-line logging functionality required by the script (Linux only)."""

	def __init__(self) -> None:
		# Prepare syslog() for our messages.
		if sys.platform == "linux":
			syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_LOCAL0)

	def __del__(self) -> None:
		if sys.platform == "linux":
			syslog.closelog()

	def __enter__(self) -> Any:
		"""Required to support the 'with instance as name: ...' exception wrapper syntactic sugar."""
		return self

	def __exit__(
		self,
		exception_type : type[BaseException] | None,
		exception_value : BaseException | None,
		traceback : types.TracebackType | None
	) -> None:
		"""Required to support the 'with instance as name: ...' exception wrapper syntactic sugar."""
		pass							# pylint: disable=unnecessary-pass

	def _write(self, kind : int, text : str) -> None:
		"""Writes one or more lines to the output device."""
		lines = text.split(os.linesep)
		for line in lines:
			# NOTE: Always output status to the console to allow the user to see what is happening.
			print(line)

			if sys.platform == "linux":
				syslog.syslog(kind, line)

	def error(self, text : str = "") -> None:
		self._write(SYSLOG_LOG_ERR, text)

	def write(self, text : str = "") -> None:
		self._write(SYSLOG_LOG_INFO, text)
