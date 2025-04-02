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
#
# This script is responsible for updating, upgrading, and cleaning the system (only if there is an active internet connection).

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import platform
import sys

from toolbox.driver import KioskDriver
from toolbox.errors import KioskError
from toolbox.internet import internet_active
from toolbox.logger import Logger
from toolbox.invoke import invoke_text_safe
from toolbox.version import *


class KioskUpdate(KioskDriver):
	"""This class implements the KioskUpdate.py script, which updates the system if and only if it is on the internet."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)
		self.version = Version("KioskUpdate", VERSION, COMPANY, CONTACT, TESTING)

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Check that we're running on Linux.
		if platform.system() != "Linux":
			raise KioskError("This script is can only be run on a Linux kiosk machine")

		# Parse command-line arguments.
		if len(arguments) != 0:
			raise SyntaxError('"KioskUpdate.py"')

		if not internet_active():
			logger.write("Not connected to the internet: Skipping system update, upgrade, and clean task.")
			return

		invoke_text_safe("apt-get update")

		invoke_text_safe("apt-get upgrade -y")

		invoke_text_safe("apt-get clean")

		logger.write("Successfully updated, upgraded, and cleaned system.  Will reboot now.")

		invoke_text_safe("reboot")


if __name__ == "__main__":
	app = KioskUpdate()
	code = app.main(sys.argv)
	sys.exit(code)

