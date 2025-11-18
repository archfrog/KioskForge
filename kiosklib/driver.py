#!/usr/bin/env python3
#**********************************************************************************************************************************
# BSD 3-Clause License for KioskForge - https://kioskforge.org:
#
# Copyright © 2024-2025 The KioskForge Team.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#**********************************************************************************************************************************

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import abc
import os
import platform
import sys
import traceback

from kiosklib.errors import CommandError, Error, FieldError, InternalError, KioskError, TextFileError
from kiosklib.logger import Logger
from kiosklib.version import Version

# Standard, C-like exit code definitions.
EXIT_SUCCESS = os.EX_OK
EXIT_FAILURE = 1

class KioskDriver:
	"""Base class for the classes that implement the respective script features."""

	def __init__(self, app_name : str = "") -> None:
		if not app_name:
			app_name = self.project
		self.__version = Version(app_name)

	@property
	def project(self) -> str:
		"""Returns the class name of an instance of 'KioskDriver'."""
		return type(self).__name__

	@property
	def version(self) -> Version:
		return self.__version

	@abc.abstractmethod
	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		raise InternalError("Abstract method called")

	def main(self, argv : List[str]) -> int:
		# Assume failure until success has been achieved.
		status = EXIT_FAILURE

		with Logger() as logger:
			# Compute full path of this script.
			origin = os.path.dirname(os.path.abspath(argv[0]))

			# NOTE: Handle the temporary working directory created by PyInstaller in a transparent fashion for all scripts.
			if hasattr(sys, "_MEIPASS"):
				# pyrefly: ignore[missing-attribute]
				origin = sys._MEIPASS

			try:
				# Call the derived class' _main() function.
				self._main(logger, origin, argv[1:])

				# Signal success to the client (caller).
				status = EXIT_SUCCESS
			except CommandError as that:
				logger.error(f"Syntax: {that.text}")
			except FieldError as that:
				logger.error(str(that))
			except InternalError as that:
				logger.error(f"Internal error: {that.text}")
			except KioskError as that:
				logger.error(f"Error: {that.text}")
			except TextFileError as that:
				logger.error(str(that))
			except Error as that:
				logger.error(f"Unknown error: {that.text}")
			except KeyboardInterrupt:
				logger.error("Break error: The user hit Ctrl-C to abort the script")
			except Exception as that:				# pylint: disable=broad-exception-caught
				# Attempt to get the exception text, if any, through a number of Python-supported means.
				if hasattr(that, "message"):
					# pyrefly: ignore[missing-attribute]
					text = that.message
				elif hasattr(that, "strerror"):
					# pyrefly: ignore[missing-attribute]
					text = that.strerror
				elif hasattr(that, "text"):
					# pyrefly: ignore[missing-attribute]
					text = that.text
				else:
					text = str(that)
				logger.error(f"Fatal error: {text}")
				logger.error(traceback.format_exc())

		# If not running from a console, wait for a keypress so that the user can read the output.
		if platform.system() == "Windows" and not "PROMPT" in os.environ:
			print()
			input("*** Press ENTER to continue and close this window")

		return status
