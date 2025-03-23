class Error(Exception):
	"""The base class for all exceptions."""

	def __init__(self, text : str) -> None:
		Exception.__init__(self)
		self.__text = text

	@property
	def text(self) -> str:
		return self.__text


class InputError(Error):
	"""Exception thrown if the user enters invalid input."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class KioskError(Error):
	"""Generic exception used for all kinds of errors while running this script."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class InternalError(Error):
	"""Exception used to signal that an internal error has been discovered."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class SyntaxError(Error):
	"""Exception used to signal that a syntax error, in a configuration file, has been detected."""

	def __init__(self, text : str) -> None:
		Error.__init__(self, text)


class ArgumentError(Error):
	"""Exception used to signal that an argument to the script was invalid or missing."""

	def __init__(self, index : int, text : str) -> None:
		Error.__init__(self, text)
		self.__index = index

	@property
	def index(self) -> int:
		return self.__index

