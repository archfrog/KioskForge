# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Any, Dict, List, Optional, TextIO, Tuple

import abc
import os
import platform
import sys

from kiosk.errors import *
from kiosk.logger import Logger

# Standard, C-like exit code definitions.
EXIT_SUCCESS = os.EX_OK
EXIT_FAILURE = 1

class KioskClass(object):
	"""Base class for the class that implement the respective script features."""

	@abc.abstractmethod
	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		raise InternalError("Abstract method called")

	def main(self, argv : List[str]) -> int:
		# Assume failure until success has been achieved.
		status = EXIT_FAILURE

		with Logger() as logger:
			# Compute full path of this script.
			(origin, filename) = os.path.split(os.path.abspath(argv[0]))

			# Extract the base name and extension (the latter can be '.py' or '.exe').
			(basename, extension) = os.path.splitext(filename)

			try:
				# Call the derived class' _main() function.
				self._main(logger, origin, argv[1:])

				# Signal success to the client (caller).
				status = EXIT_SUCCESS
			except ArgumentError as that:
				text = ""
				if that.index != -1:
					text += "(#%d) " % that.index
				text += "Error: "
				text += that.text
				logger.error("%s" % text)
			except SyntaxError as that:
				logger.error("Syntax: %s" % that.text)
			except InternalError as that:
				logger.error("Internal Error: %s" % that.text)
			except KioskError as that:
				logger.error("Error: %s" % that.text)
			except Exception as that:
				text = ""
				if hasattr(that, "message"):
					text = that.message
				elif hasattr(that, "strerror"):
					text = that.strerror
				if text == "":
					text = str(that)
				logger.error("Unknown Error: %s" % text)
				raise

		# If not running from a console, wait for a keypress so that the user can read the output.
		if platform.system() == "Windows" and not "PROMPT" in os.environ:
			print()
			input("Press ENTER to continue and close this window")

		return status

