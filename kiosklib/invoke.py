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

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Dict, List, Optional

import shlex
import subprocess

from kiosklib.errors import KioskError


class Result:
	"""The result (status code, output) of an action."""

	def __init__(self, status : int = 0, output : str = "") -> None:
		self.__output = output
		self.__status = status

	@property
	def output(self) -> str:
		return self.__output

	@property
	def status(self) -> int:
		return self.__status


# Global function to invoke an external program and return a 'Result' instance with the program's exit code and output.
def invoke_list(command : List[str], environment : Optional[Dict[str, str]] = None) -> Result:
	# Capture stderr and stdout interleaved in the same output string by using stderr=...STDOUT and stdout=...PIPE.
	result = subprocess.run(
		command,
		stderr=subprocess.STDOUT,
		stdout=subprocess.PIPE,
		check=False,
		shell=False,
		text=False,
		env=environment
	)

	# Convert bytes from command into a UTF-8 text string.
	try:
		output = result.stdout.decode('utf-8').strip()
	except UnicodeDecodeError:
		print(result.stdout.strip())
		raise

	return Result(result.returncode, output)

# Variant of 'invoke_list()' that checks the status code and throws a KioskError exception if it is non-zero.
def invoke_list_safe(command : List[str], environment : Optional[Dict[str, str]] = None) -> None:
	result = invoke_list(command, environment)
	if result.status != 0:
		raise KioskError(result.output)

# Variant of 'invoke_list()' that asks 'shlex.split()' to split a single string command into its equivalent list of tokens.
def invoke_text(command : str, environment : Optional[Dict[str, str]] = None) -> Result:
	return invoke_list(shlex.split(command), environment)

# Variant of 'invoke_list()' that splits a string and checks the status code and throws a KioskError exception if it is non-zero.
def invoke_text_safe(command : str, environment : Optional[Dict[str, str]] = None) -> None:
	result = invoke_text(command, environment)
	if result.status != 0:
		raise KioskError(result.output)
