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

import shlex
import subprocess

class Result(object):
	"""The result (status code, output) of an action."""

	def __init__(self, status : int = 0, output : str = "") -> None:
		self.__status = status
		self.__output = output

	@property
	def status(self) -> int:
		return self.__status

	@property
	def output(self) -> str:
		return self.__output


# Global function to invoke an external program and return a 'Result' instance with the program's exit code and output.
def invoke_list(command : List[str]) -> Result:
	# Capture stderr and stdout interleaved in the same output string by using stderr=...STDOUT and stdout=...PIPE.
	result = subprocess.run(command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, check=False, shell=False, text=False)
	output = result.stdout.decode('utf-8')
	return Result(result.returncode, output)

# Alias for 'invoke_list' that asks 'shlex.split()' to split a single string command into its equivalent list of tokens.
def invoke_text(command : str) -> Result:
	return invoke_list(shlex.split(command))

