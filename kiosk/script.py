# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Any, List

from kiosk.actions import Action
from kiosk.errors import ArgumentError, InternalError, KioskError
from kiosk.invoke import Result
from kiosk.logger import Logger

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



