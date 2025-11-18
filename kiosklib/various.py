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

import errno
import io
import os
import secrets
from string import ascii_lowercase
import sys

# Import the bcrypt PyPi package, which is a dependency in the 'uv' 'pyproject.toml' file.
import bcrypt

from kiosklib.errors import KioskError


def file_wipe_once(path : str) -> None:
	"""Wipes a file once in-place by writing all zeroes to it.  This is adequate for non-professional snoopers only."""

	# Compute open mode and open the file while bypassing Python built-in 'open' function which creates or truncates the file.
	mode = os.O_WRONLY
	if sys.platform == "windows":
		mode |= os.O_BINARY
		mode |= os.O_SEQUENTIAL
	handle = os.open(path, mode)
	del mode
	if handle == -1:
		raise OSError(errno.errorcode, "Unable to open file for wiping: " + path, path)

	try:
		# Fetch stat bits from handle.
		status = os.fstat(handle)
		length = status.st_size

		# Linux only: Fetch the underlying block size to speed op the operation as much as possible.
		if sys.platform == "linux":
			buffer = bytearray(status.st_blksize)
		else:
			buffer = bytearray(io.DEFAULT_BUFFER_SIZE)
		del status

		offset = 0
		while offset < length:
			# Compute how many bytes we will write in this block.
			extent = min(len(buffer), length - offset)

			# Attempt to write 'extent' zero bytes to the output file.
			output = os.write(handle, buffer[:extent])
			if output < extent:
				raise OSError(errno.errorcode, "Unable to wipe file: " + path, path)

			# Flush the written zero bytes to disk before continuing.
			os.fsync(handle)

			# Advance to end or next block.
			offset += extent
	finally:
		os.close(handle)


def file_wipe_multiple(path : str, count : int = 10) -> None:
	"""Wipes a file, in-place, with all zeroes multiple times.  This is almost good enough to handle professional snoopers."""
	# pylint: disable-next=unused-variable
	for index in range(count):
		file_wipe_once(path)


def hostname_create(basename : str) -> str:
	"""Creates a random host name of the form '{basename}{number}', where number is an integer from zero to 99,999."""
	number = secrets.randbelow(100000)
	return f"{basename}{number}"


# Source: https://stackoverflow.com/a/63160092
def password_create(length : int) -> str:
	return secrets.token_urlsafe(length)


def password_hash(text : str) -> str:
	"""Hashes an unhashed password, already hashed passwords are returned unaltered."""

	# If the password is already hashed, simply return it unaltered.
	if password_hashed(text):
		return text

	# Verify the that the length of the password fits the constraints of bcrypt.
	if len(text) < 1 or len(text) > 72:
		raise ValueError("Argument 'text' must be between 1 and 72 charaters in length")

	# Convert UTF-8 string into a byte string.
	data = text.encode('utf-8')

	# Create and return a hashed password.
	return bcrypt.hashpw(data, bcrypt.gensalt()).decode('utf-8')


def password_hashed(text : str) -> bool:
	"""Returns True if a password APPEARS hashed already, otherwise False."""
	return len(text) >= 4 and text[:2] == "$2" and text[2] in ascii_lowercase and text[3] == "$"


def ramdisk_get() -> str:
	"""Returns the normalized value of the RAMDISK environment variable or raises a KioskError exception if not found."""
	# Check that the user has set up the RAMDISK environment variable.
	result = os.environ.get("RAMDISK")
	if not result:
		raise KioskError("No RAMDISK environment variable found.")

	# Ensure the ramdisk variable is terminated by a directory separator, this simplifies the code below.
	# NOTE: Adding a directory separator here also helps to eliminate double directory separators in generated paths.
	if result[-1] != os.sep:
		result += os.sep

	return result


def screen_clear() -> None:
	"""Clears the current Linux console window using escape sequences as the 'clear' command doesn't always work."""
	# NOTE: The 'clear' command has no effect for reasons unknown to me so I resorted to using an 'xterm' escape sequence.
	# Clear screen and move cursor to (1, 1).
	print("\033[2J\033[1;1H", end="")
