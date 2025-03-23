# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Any, Dict, List, Optional, TextIO, Tuple

import os
import sys
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
		self.__stream = open(self.__path, "wt", encoding="utf-8")
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



