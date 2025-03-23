# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Any, List

class TextBuilder(object):
	"""Used to build a multi-line text concatened from individual lines using += or a list of tokens concatenated using +=."""

	def __init__(self) -> None:
		self.__lines : List[str] = []

	@property
	def list(self) -> List[str]:
		return self.__lines

	@property
	def text(self) -> str:
		return '\n'.join(self.__lines) + '\n'

	def __iadd__(self, line : str) -> Any:
		self.__lines.append(line)
		return self



