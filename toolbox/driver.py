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

import abc
import os
import platform
import sys
import traceback

from toolbox.errors import CommandError, Error, InternalError, KioskError
from toolbox.logger import Logger

# Standard, C-like exit code definitions.
EXIT_SUCCESS = os.EX_OK
EXIT_FAILURE = 1

class KioskDriver:
	"""Base class for the classes that implement the respective script features."""

	@property
	def project(self) -> str:
		"""Returns the class name of an instance of 'KioskDriver'."""
		return type(self).__name__

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
				origin = sys._MEIPASS

			try:
				# Call the derived class' _main() function.
				self._main(logger, origin, argv[1:])

				# Signal success to the client (caller).
				status = EXIT_SUCCESS
			except CommandError as that:
				logger.error(f"Syntax: {that.text}")
			except InternalError as that:
				logger.error(f"Internal error: {that.text}")
			except KioskError as that:
				logger.error(f"Error: {that.text}")
			except Error as that:
				logger.error(f"Unknown error: {that.text}")
			except Exception as that:				# pylint: disable=broad-exception-caught
				# Attempt to get the exception text, if any, through a number of Python-supported means.
				if hasattr(that, "message"):
					text = that.message
				elif hasattr(that, "strerror"):
					text = that.strerror
				elif hasattr(that, "text"):
					text = that.text
				else:
					text = str(that)
				logger.error(f"Fatal error: {text}")
				logger.write(traceback.format_exc())

		# If not running from a console, wait for a keypress so that the user can read the output.
		if platform.system() == "Windows" and not "PROMPT" in os.environ:
			print()
			input("Press ENTER to continue and close this window")

		return status

