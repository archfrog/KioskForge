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
#
# This file implements the 'Signal' class, which is used for inter-process communication using a disk file in '/tmp'.
#
# NOTE: This module currently assumes that '/tmp' is located in a non-persistent RAM disk, which is true for Ubuntu (and others).

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Optional

import os
import shutil

SIGNAL_PREFIX  = "/tmp"
SIGNAL_SUFFIX  = ".signal"
TEMP_EXTENSION = ".tmp"


class Signal:
	"""A class that implements very simple inter-process signal communication.  Not very robust at present."""

	def __init__(self, name : str, owner : str, group : Optional[str] = None) -> None:
		"""Create a new Signal() instance with the specified name, owner, and group."""
		# Initialize the instance.
		self.__path  = SIGNAL_PREFIX + os.sep + name + SIGNAL_SUFFIX
		self.__owner = owner
		self.__group = group or owner

	@property
	def exists(self) -> bool:
		"""Return the boolean status of the signal."""
		return os.path.isfile(self.__path)

	def create(self) -> None:
		"""Signals an event by 'making a signal' (creating a signal file)."""
		# Create the file under another name, change ownership, and rename it to the signal file name.
		# NOTE: Don't create directly and change ownership as it is removed when received (which will fail with the wrong owner).
		temp = self.__path + TEMP_EXTENSION
		open(temp, "wb").close()		# pylint: disable=consider-using-with
		os.chmod(temp, 0o600)
		shutil.chown(temp, self.__owner, self.__group)
		os.rename(temp, self.__path)

	def remove(self) -> None:
		"""Remove the signal by deleting the signal file."""
		os.unlink(self.__path)
