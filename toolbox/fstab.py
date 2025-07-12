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
# This script defines the class 'Filesystems', which handles parsing and writing of the '/etc/fstab' file.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List, TextIO

from toolbox.errors import KioskError


class Empty:
	"""An empty line in /etc/fstab."""

	def __init__(self) -> None:
		pass

	def write(self, stream : TextIO) -> None:
		stream.write("\n")


class Comment(Empty):
	"""A comment line in /etc/fstab (starts with ';' or '#')."""

	def __init__(self, text : str) -> None:
		super().__init__()
		self.__text = text

	def write(self, stream : TextIO) -> None:
		stream.write(self.__text)
		stream.write("\n")


class Mount(Comment):
	"""A mount line in /etc/fstab (made up of four to six fields)."""

	def __init__(self, text : str) -> None:
		super().__init__(text)

		fields = text.split()
		if len(fields) < 4 or len(fields) > 6:
			raise KioskError(f"Invalid line encountered: {' '.join(fields)}")

		self.__file_system = fields[0]
		self.__mount_point = fields[1]
		self.__type        = fields[2]
		self.__options     = fields[3]
		self.__dump        = -1 if len(fields) < 5 else int(fields[4])
		self.__pass        = -1 if len(fields) < 6 else int(fields[5])

	@property
	def file_system(self) -> str:
		return self.__file_system

	@file_system.setter
	def file_system(self, value : str) -> None:
		self.__file_system = value

	@property
	def mount_point(self) -> str:
		return self.__mount_point

	@mount_point.setter
	def mount_point(self, value : str) -> None:
		self.__mount_point = value

	@property
	def type(self) -> str:
		return self.__type

	@type.setter
	def type(self, value : str) -> None:
		self.__type = value

	@property
	def options(self) -> List[str]:
		return self.__options.split(",")

	@options.setter
	def options(self, value : List[str]) -> None:
		self.__options = ",".join(value)

	@property
	def dump(self) -> int:
		return self.__dump

	@dump.setter
	def dump(self, value : int) -> None:
		self.__dump = value

	@property
	def pass_(self) -> int:
		return self.__pass

	@pass_.setter
	def pass_(self, value : int) -> None:
		self.__pass = value

	def write(self, stream : TextIO) -> None:
		stream.write(self.__file_system)

		stream.write("\t")
		stream.write(self.__mount_point)

		stream.write("\t")
		stream.write(self.__type)

		stream.write("\t")
		stream.write(self.__options)

		if self.__dump != -1:
			stream.write("\t")
			stream.write(str(self.__dump))

		if self.__pass != -1:
			stream.write("\t")
			stream.write(str(self.__pass))

		stream.write("\n")


class Filesystems:
	"""A complete /etc/fstab file, which preserves empty lines, comments, and the actual mount lines."""

	def __init__(self) -> None:
		self.__lines : List[Empty] = []

	@property
	def lines(self) -> List[Empty]:
		return self.__lines

	@lines.setter
	def lines(self, value : List[Empty]) -> None:
		self.__lines = value

	def load(self, path : str) -> None:
		# NOTE: Open as utf-8 in case there is UTF-8 text in comments.
		with open(path, "rt", encoding="utf-8") as reader:
			lines = reader.read().split("\n")

		for line in lines:
			if len(line) == 0:
				child = Empty()
			elif line[0] in "#;":
				child = Comment(line)
			else:
				child = Mount(line)
			self.__lines.append(child)

	def save(self, path : str) -> None:
		with open(path, "wt", encoding="utf-8") as writer:
			for line in self.__lines:
				line.write(writer)
