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
from typing import Any, List

from toolbox.actions import Action
from toolbox.errors import ArgumentError, InternalError, KioskError
from toolbox.invoke import Result
from toolbox.logger import Logger

class Script(object):
	"""Simple abstraction of a sequence of actions that can be resumed from any point in the list of actions."""

	def __init__(self, logger : Logger, resume : int) -> None:
		self.__actions : List[Action] = []
		self.__logger = logger
		self.__resume = resume

	def __iadd__(self, action : Action) -> Any:
		"""Overload the += operator to make it convenient to add new script actions (cannot use '-> Script' so '-> Any' it is)."""

		# Check that the action hasn't already been added to the script.
		if action in self.__actions:
			raise InternalError("Action was added twice: %s" % action)

		# Add the action to the script to be executed.
		self.__actions.append(action)

		return self

	def execute(self) -> Result:
		result = Result()

		if self.__resume >= len(self.__actions):
			raise ArgumentError(0, "Resume offset greater than total number of actions")

		# Execute each action in turn while handling exceptions and failures.
		index = self.__resume
		for action in self.__actions[self.__resume:]:
			try:
				self.__logger.write("%4d %s" % (index, action.title))
				index += 1

				result = action.execute()
				if result.status != 0:
					self.__logger.error(result.output)
					self.__logger.error("**** SCRIPT ABORTED DUE TO ABOVE ERROR ****")
					break
			except (KioskError, InternalError) as that:
				result = Result(1, that.text)

		return result



