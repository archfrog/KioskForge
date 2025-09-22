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

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Any, List

import timeit

from kiosklib.actions import Action
from kiosklib.errors import InternalError, KioskError
from kiosklib.invoke import Result
from kiosklib.logger import Logger

class Script:
	"""Simple abstraction of a sequence of actions that can be resumed from any point in the list of actions."""

	def __init__(self, logger : Logger, resume : int = 1) -> None:
		self.__actions : List[Action] = []
		self.__logger = logger
		self.__resume = resume

	def __iadd__(self, action : Action) -> Any:
		"""Overload the += operator to make it convenient to add new script actions (cannot use '-> Script' so '-> Any' it is)."""

		# Check that the action hasn't already been added to the script.
		if action in self.__actions:
			raise InternalError(f"Action was added twice: {action}")

		# Add the action to the script to be executed.
		self.__actions.append(action)

		return self

	def execute(self) -> Result:
		result = Result()

		# Check that the given resume value is valid.
		if self.__resume == 0 or self.__resume > len(self.__actions):
			raise KioskError(f"Resume offset outside valid range of one through {len(self.__actions)}")

		# Fetch current time to be able to show the delta for each script action.
		start = timeit.default_timer()

		# Execute each action in turn while handling exceptions and failures.
		self.__logger.write("STEP ELAPSED  ACTION")
		index = self.__resume
		for action in self.__actions[self.__resume - 1:]:
			# Compute and display total running time until now.
			total              = int(timeit.default_timer() - start)
			(minutes, seconds) = divmod(total, 60)
			(hours, minutes)   = divmod(minutes, 60)
			self.__logger.write(f"{index:4d} {hours:02d}:{minutes:02d}:{seconds:02d} {action.title}")

			# Increment step index.
			index += 1

			# Execute the action while propagating the status code, if possible.
			try:
				# Execute the current action.
				result = action.execute()

				# Report error and abort if the action failed.
				if result.status != 0:
					self.__logger.error(result.output)
					self.__logger.error("*** SCRIPT ABORTED DUE TO ABOVE ERROR")
					break
			except KioskError as that:
				result = Result(result.status, that.text)
			except InternalError as that:
				# Handle detected runtime errors, etc.
				result = Result(1, that.text)

		# Output the total time it took to forge the kiosk.
		total              = int(timeit.default_timer() - start)
		(minutes, seconds) = divmod(total, 60)
		(hours, minutes)   = divmod(minutes, 60)
		self.__logger.write(f"{index:4d} {hours:02d}:{minutes:02d}:{seconds:02d} FORGE PROCESS FINISHED")
		del index

		return result
