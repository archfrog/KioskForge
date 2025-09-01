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
# This script is a tiny UDP broadcast discovery client, which allows us to discover all KioskForge kiosks on the LAN.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import sys
import socket

from kiosklib.discovery import COMMAND, SERVICE
from kiosklib.driver import KioskDriver
from kiosklib.errors import CommandError
from kiosklib.logger import Logger
from kiosklib.network import lan_address, lan_broadcast_address


class KioskDiscoveryClient(KioskDriver):
	"""Defines the KioskDiscoveryClient class, sends an UDP broadcast packet on the LAN to discover kiosks on it."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Parse command-line arguments.
		if len(arguments) != 0:						# pylint: disable=duplicate-code
			raise CommandError('"KioskDiscoveryClient.py"')

		# Compute the x.y.z prefix of our own LAN address to filter out packets NOT originating from the LAN.
		lan_subnet = '.'.join(lan_address().split('.')[:3])

		# Create an UDP socket.
		client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

		# Set a timeout so the socket does not block indefinitely when trying to receive data.
		client.settimeout(5)

		found = {}
		try:
			# Broadcast request to all the kiosks on the local area network (LAN) to send us their IP addresses by replying.
			client.sendto(COMMAND.encode('utf-8'), (lan_broadcast_address(), SERVICE))

			while True:
				try:
					# Wait for a message from a KioskForge client.
					(message, remote)  = client.recvfrom(1024)
					(address, service) = remote

					# Convert the message from bytes into UTF-8.
					command = message.decode('utf-8')
					del message

					# Ensure we only accept replies from the current LAN.
					if '.'.join(address.split('.')[:3]) != lan_subnet:
						logger.error(f"({address}:{service}) Ignoring packet from outside LAN")
						continue

					# Compute prefix and length of prefix of reply from broadcast server.
					prefix_data = f"{COMMAND}: "
					prefix_size = len(prefix_data)
					suffix_data = command[prefix_size:]

					# Ignore malformed packets.
					if command[:prefix_size] != prefix_data:
						logger.error(f"({address}:{service}) Ignoring invalid packet")
						continue

					# Record the kiosk as found (to be reported below).
					found[address] = tuple(suffix_data.split("|"))
				except TimeoutError:
					break
		finally:
			client.close()

		# Print out the found addresses and their host names.
		for address, hostname_and_comment in found.items():
			(hostname, comment) = hostname_and_comment
			print(f"{address}  {hostname}  {comment}")


if __name__ == "__main__":
	sys.exit(KioskDiscoveryClient().main(sys.argv))
