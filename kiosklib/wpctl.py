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
# This script provides a function to parse the output of 'wpctl status': It is very primitive, but it gets the job done.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

from kiosklib.errors import KioskError


def wpctl_status_parse_sinks(value : str) -> List[int]:
	# Strip out lame UTF-8 graphics characters by converting to ASCII and back to UTF-8 (while ignoring non-ASCII characters).
	clean = value.encode("ascii", "ignore")
	value = clean.decode("utf-8")
	del clean

	lines = value.split('\n')
	found = False
	sinks = []
	for line in lines:
		# Strip leading and trailing whitespice, and then split the line into individual tokens.
		line = line.strip()
		tokens = line.split()

		# Execute a tiny two-state state machine.
		if not found:
			# Any line up to and including the 'Sinks:' header.
			if len(tokens) > 0 and tokens[0] == "Sinks:":
				found = True
		else:
			# Just after the 'Sinks:' header.

			# If at the end of the list of sinks, simply exit the 'for' loop as we're done.
			if len(line) == 0:
				break

			# Discard optional "Default sink" indicator (an asterisk).
			if len(tokens) > 0 and tokens[0] == "*":
				del tokens[0]

			# If there only was an asterisk, something's definitely off, give up.
			if len(tokens) == 0:
				raise KioskError("Unknown syntax of 'wpctl status' command")

			# Convert the sink id into a number by stripping the trailing dot and appending it to 'sinks'.
			item = int(tokens[0].replace('.', ''))
			sinks.append(item)
			del item

	return sinks
