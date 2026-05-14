#!/usr/bin/env python3
#**********************************************************************************************************************************
# BSD 3-Clause License for KioskForge - https://kioskforge.org:
#
# Copyright © 2024-2026 The KioskForge Team.
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
#
# This script is responsible for launching Chromium, monitoring it, and restarting after a certain period of inactivity.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import os
import shlex
import shutil
import subprocess
import sys
import time

from kiosklib.builder import TextBuilder
from kiosklib.driver import KioskDriver
from kiosklib.errors import CommandError, KioskError
from kiosklib.invoke import invoke_list_safe, invoke_text, invoke_text_safe
from kiosklib.kiosk import Kiosk
from kiosklib.logger import Logger
from kiosklib.signal import Signal

KIOSKFORGE_TO_XRANDR_ROTATIONS = {
	'none'  : 'normal',
	'left'  : 'left',
	'flip'  : 'inverted',
	'right' : 'right'
}


class Program:
	"""An abstraction of a program that can be invoked and monitored by the Monitor class."""

	def __init__(self, kiosk : Kiosk):
		self._kiosk = kiosk

	@property
	def command(self) -> List[str]:
		raise TypeError("Abstract method called")

	@property
	def description(self) -> str:
		raise TypeError("Abstract method called")


class ChromiumProgram(Program):
	"""A concrete implemention of the Chromium browser."""

	@property
	def command(self) -> List[str]:
		"""Builds the Chromium command-line."""
		# Build the Chromium command line with a horde of options (I don't know which ones work and which don't...).
		# NOTE: Chromium does not complain about any of the options listed below!
		command  = TextBuilder()
		command += shutil.which("chromium") or "chromium"
		command += "--kiosk"
		command += "--fast"
		command += "--fast-start"
		command += "--start-maximised"
		command += "--noerrdialogs"
		command += "--no-first-run"
		command += "--enable-pinch"
		command += "--touch-events=enabled"
		command += "--overscroll-history-navigation=disabled"
		command += "--disable-features=TouchpadOverscrollHistoryNavigation"
		command += "--overscroll-history-navigation=0"
		command += "--disable-restore-session-state"
		command += "--disable-infobars"
		command += "--disable-crashpad"

		# Enable automatic autoplay of videos, if requested by the user.
		if self._kiosk.chromium_autoplay.data:
			command += "--autoplay-policy=no-user-gesture-required"

		# Use the /tmp folder for the disk cache, if kiosk wear reduction has been enabled.
		if self._kiosk.wear_reduction.data:
			command += "--disk-cache-dir=/tmp/Chromium"

		# Append the URL of the website, local or online, to be browsed.
		command += self._kiosk.command.data

		return command.list

	@property
	def description(self) -> str:
		return "Chromium web browser"


class CustomProgram(Program):
	"""A concrete implementation of a user-specified program (command=)."""

	@property
	def command(self) -> List[str]:
		"""Builds the user-specified command's command-line."""
		strings = shlex.split(self._kiosk.command.data)
		return [os.path.normpath(os.path.join("/home/kiosk/", strings[0]))] + strings[1:]

	@property
	def description(self) -> str:
		return "user-defined program"


class Monitor:
	"""A simple monitor that terminates the program if it times out and/or restarts the invoked program (also on crashes)."""

	# Returns the total number of seconds (with no fraction) of idle time since the X server was last busy.
	@staticmethod
	def x_idle_time() -> int:
		result = invoke_text("xprintidle")
		if result.status != 0:
			raise KioskError("Unable to get idle time from X11 window manager")
		return int(result.output) // 1000

	@staticmethod
	def invoke(logger : Logger, program : Program, timeout : int) -> None:
		# Timeout value is either 0 (disabled) or other (number of seconds).

		signal = Signal("KioskDesktop-shutdown", "kiosk")
		try:
			# Launch the program forever (until this script is asked to shut down), restarting it if terminated or crashed.
			while not signal.exists:
				# Launch the program in the background as a detached process.
				try:
					# pylint: disable-next=consider-using-with
					process = subprocess.Popen(program.command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				except subprocess.CalledProcessError as that:
					raise KioskError(program.description + " failed to start:" + that.output.decode('utf-8')) from that
				except subprocess.SubprocessError as that:
					raise KioskError("Unable to start " + program.description) from that
				except OSError as that:
					raise KioskError(that.strerror or "Unknown OS error") from that

				# Let the program start completely before we begin to check if it has been idle for too long.
				time.sleep(15)

				# Loop forever (until asked to shut down), launching the program and terminating it if it is idle for too long.
				while not signal.exists:
					# Wait one second between checking if the program should be restarted.
					time.sleep(1)

					# If the program has exited (crashed), exit to outer loop to restart it.
					if "process" in locals() and process.poll():
						logger.error("Restarting " + program.description + " after crash.")
						break

					# If the app has been idle for more than N seconds, terminate the program and exit to outer loop to restart it.
					if timeout and Monitor.x_idle_time() >= timeout:
						process.terminate()
						del process

						# Reset X11's idle timer to ensure that inaccuracies do not accumulate over time.
						invoke_text_safe("xset s reset")

						break
		finally:
			# Terminate the program if it is still running.
			if "process" in locals():
				if not process.poll():		# pyrefly: ignore[unbound-name]
					process.terminate()		# pyrefly: ignore[unbound-name]
				del process					# pyrefly: ignore[unbound-name]

			# Remove the signal once we've performed the requested task.
			signal.remove()
			del signal


class KioskDesktop(KioskDriver):
	"""Defines the KioskDesktop class, which starts the X11 desktop, and any app, monitors it, and restarts it if necessary.

	   The script can be shut down gracefully by creating the signal 'KioskDesktop-shutdown' as demonstrated below.
	"""

	def __init__(self) -> None:
		KioskDriver.__init__(self)

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Check that we're running on Linux.
		if sys.platform != "linux":					# pylint: disable=duplicate-code
			raise KioskError("This script can only be run on a Linux kiosk machine")

		# Check that we don't have root privileges.
		# pylint: disable-next=no-member
		if os.geteuid() == 0:		# pyrefly: ignore[missing-attribute]
			raise KioskError("You may not be root when running this script")

		# Parse command-line arguments.
		if len(arguments) != 0:
			raise CommandError('"KioskDesktop.py"')

		# Load settings generated by KioskForge on the desktop machine.
		kiosk = Kiosk(self.version)
		kiosk.load_safe(logger, origin + os.sep + "KioskForge.kiosk")

		# Fetch timeout value (0 = disabled, other = number of seconds) from configuration file.
		timeout = kiosk.idle_timeout.data

		# Disable all forms of X screen saver/screen blanking/power management.
		for command in [ "xset s off", "xset s noblank", "xset -dpms"]:
			invoke_text_safe(command)

		if kiosk.screen_rotation.data != "none":
			# Ask 'xrandr' to rotate the screen as per the `screen_rotation` setting.
			command  = TextBuilder()
			command += "xrandr"
			command += "--output"
			command += "HDMI-1"
			command += "--rotate"
			command += KIOSKFORGE_TO_XRANDR_ROTATIONS[kiosk.screen_rotation.data]
			invoke_list_safe(command.list)
			del command

		# Only launch Chromium if a 'web' type kiosk: the 'x11' type uses a custom application supplied by the user.
		if kiosk.type.data == "web":
			program = ChromiumProgram(kiosk)
		elif kiosk.type.data == "x11":
			program = CustomProgram(kiosk)
		else:
			raise KioskError("Kiosk type not supported by KioskDesktop.py: " + kiosk.type.data)

		# Start the program and keep restarting it on crashes until the signal 'KioskDesktop-shutdown' is signalled.
		Monitor().invoke(logger, program, timeout)


if __name__ == "__main__":
	sys.exit(KioskDesktop().main(sys.argv))
