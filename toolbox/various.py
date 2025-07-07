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

import errno
import io
import os
import sys

from toolbox.errors import KioskError


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
