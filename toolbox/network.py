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
# Contains various utility functions that are used for querying and controlling the network and detecting if the internet is up.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import http.client as httplib
import os
import socket
import time

from toolbox.errors import Error
from toolbox.invoke import invoke_text, invoke_text_safe


def wifi_boost(state : bool) -> None:
	# Get all network cards and extract those that are Wi-Fi cards (those that begin with 'w').
	netcards = filter(lambda x: x[0] == 'w', get_network_cards())

	# Invert the logic and use 'iw's symbolic names.
	flag = { False : 'on', True : 'off' }[state]

	# Ask 'iw' to disable power-saving on all found wireless cards.
	for netcard in netcards:
		invoke_text_safe(f"/sbin/iw {netcard} set power_save {flag}")


def get_network_cards() -> List[str]:
	result = invoke_text("netstat -i")
	if result.status != 0:
		raise Error("Unable to get list of network cards using 'netstat -i'")

	# Parse output from netstat.
	lines = result.output.split(os.linesep)
	assert len(lines) >= 3, "Unexpected output from 'netstat -i'"
	assert lines[0].strip() == "Kernel Interface table", "First line of 'netstat -i' output not as expected"
	assert lines[1].strip() == "Iface             MTU    RX-OK RX-ERR RX-DRP RX-OVR    TX-OK TX-ERR TX-DRP TX-OVR Flg", "Second line of 'netstat -i' output not as expected"

	# Extact the list of network cards (column 1) from the 'netstat -i' output.
	cards = []
	for line in lines[2:]:
		assert line != "", "Empty line found in 'netstat -i' output"
		fields = list(filter(lambda x: x != "", line.split(" ")))
		assert len(fields) == 11, "Malformed interface line found in 'netstat -i' output"
		cards.append(fields[0])

	return cards


# Source: https://stackoverflow.com/questions/3764291/how-can-i-see-if-theres-an-available-and-active-network-connection-in-python
def internet_active() -> bool:
	connection = httplib.HTTPSConnection("8.8.8.8", timeout=5)
	try:
		connection.request("HEAD", "/")
		return True
	except:								# pylint: disable=bare-except
		return False
	finally:
		connection.close()


def lan_address() -> str:
	"""Returns the LAN address for the active LAN."""
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		s.connect(('<broadcast>', 12345))  # 12345 is random port. 0 fails on Mac.
		return str(s.getsockname()[0])
	finally:
		s.close()


def lan_broadcast_address() -> str:
	"""Returns the LAN broadcast address (x.y.z.255) for the active LAN."""
	lan_subnet = '.'.join(lan_address().split('.')[:3])
	return lan_subnet + '.255'


def wait_for_internet_active(duration : int = 60) -> None:
	for index in range(duration):		# pylint: disable=unused-variable
		time.sleep(1)
		if internet_active():
			break
