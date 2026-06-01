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

from typing import Dict

def pi_model_get() -> str:
	"""Returns the full model name, from /proc/cpuinfo, of the currently running Pi's board or an empty string if unknown."""
	try:
		with open('/proc/cpuinfo', 'rt', encoding="utf-8") as file:
			for line in file:
				if not line.startswith('Model'):
					continue

				colon = line.index(':')
				return line[colon + 1:].strip()
	except IOError:
		pass

	return ""


def pi_board_get() -> str:
	"""Returns 'Pi 4B' if the host is a Raspberry Pi 4B and 'Pi 5' for a Raspberry Pi 5, otherwise it returns an empty string."""
	model = pi_model_get()

	if 'Raspberry Pi 4B' in model:
		return "Pi 4B"

	if 'Raspberry Pi 5' in model:
		return "Pi 5"

	return ""


def unquote(value : str) -> str:
	assert value[0] == '"'
	assert value[-1] == '"'
	return value[1:-1]


def pactl_parse_sinks_list(value : str) -> Dict[str, int]:
	"""Returns a dictionary that maps the sink nick name (vc4-hdmi-N, where N is 0 or 1) to a pactl/wpctl sink id."""
	result = {}

	lines = value.split("\n")
	tag = 0
	nick = ""
	for line in lines:
		# Strip leading and trailing whitespace.
		line = line.strip()

		# Extract the few pieces of information that we need.
		if line[:6] == "Sink #":
			tag = int(line[6:])
		elif line.startswith("device.nick = "):
			nick = unquote(line[14:])

			result[nick] = tag

			tag = 0
			nick = ""

	return result
