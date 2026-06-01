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

# This script is a tiny UDP broadcast discovery client, which allows us to discover all KioskForge kiosks on the LAN.

import sys
import socket
from time import perf_counter
from typing import List

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

		# Compute the x.y.?.? prefix of our own LAN address to filter out packets NOT originating from the LAN.
		lan_subnet = '.'.join(lan_address().split('.')[:2])

		# Create an UDP socket.
		client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

		# Set a timeout so the socket does not block indefinitely when trying to receive data.
		client.settimeout(5)

		# Precompute a few variables to speed up things marginally.
		prefix_data = f"{COMMAND}: "
		prefix_size = len(prefix_data)

		found = {}
		timeout = perf_counter() + 15.0
		try:
			# Broadcast request to all the kiosks on the LAN to send us their info by replying.
			client.sendto(COMMAND.encode('utf-8'), (lan_broadcast_address(), SERVICE))

			while perf_counter() < timeout:
				# TODO: Make this multi-threaded or something.  The current approach is very naive and even lame.
				# TODO: A queue should be used to enqueue requests so that background threads could process the queue.
				try:
					# Wait for a message from a KioskForge client (an ordinary desktop or laptop computer).
					try:
						(message, remote) = client.recvfrom(1024)
					except TimeoutError:
						continue

					# Extract the server's IP and port number.
					(address, service) = remote
					del remote

					# Convert the message from bytes into UTF-8.
					try:
						command = message.decode('utf-8')
					except UnicodeError:
						print(f"({address}:{service}) Warning: Received malformed UTF-8 string")
						continue
					del message

					# Ensure we only accept replies from the current LAN.
					if '.'.join(address.split('.')[:2]) != lan_subnet:
						logger.error(f"({address}:{service}) Ignoring packet from outside LAN segment")
						continue

					# Ignore malformed packets.
					if command[:prefix_size] != prefix_data:
						logger.error(f"({address}:{service}) Ignoring malformed packet")
						continue

					# Extract data portion of reply from broadcast server.
					suffix_data = command[prefix_size:]

					# Split the received data into separate fields.
					fields = suffix_data.split("|")

					# Convert old formats to newest format and ignore invalid packets.
					match len(fields):
						case 3:
							# Silently convert from old three-field format into current four-field format.
							fields.append("unknown")
						case 4:
							pass
						case _:
							logger.error(f"({address}:{service}) Ignoring invalid packet")

					# Record the kiosk as found (to be reported below).
					found[address] = fields
					del fields
				except TimeoutError:
					break
		finally:
			client.close()

		# Print out the found addresses and their host names.
		for address, fields in found.items():
			[hostname, version, comment, board] = fields
			print(f"{address}  {hostname}  {board}  {version}  {comment}")


if __name__ == "__main__":
	sys.exit(KioskDiscoveryClient().main(sys.argv))
