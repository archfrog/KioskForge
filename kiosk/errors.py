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

class Error(Exception):
	"""The base class for all exceptions."""

	def __init__(self, text : str) -> None:
		Exception.__init__(self)
		self.__text = text

	@property
	def text(self) -> str:
		return self.__text


class InputError(Error):
	"""Exception thrown if the user enters invalid input."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class KioskError(Error):
	"""Generic exception used for all kinds of errors while running this script."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class InternalError(Error):
	"""Exception used to signal that an internal error has been discovered."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class SyntaxError(Error):
	"""Exception used to signal that a syntax error, in a configuration file, has been detected."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class ArgumentError(Error):
	"""Exception used to signal that an argument to the script was invalid or missing."""

	def __init__(self, index : int, text : str) -> None:
		Error.__init__(self, text)
		self.__index = index

	@property
	def index(self) -> int:
		return self.__index

