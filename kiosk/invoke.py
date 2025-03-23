import shlex
import subprocess

class Result(object):
	"""The result (status code, output) of an action."""

	def __init__(self, status : int = 0, output : str = "") -> None:
		self.__status = status
		self.__output = output

	@property
	def status(self) -> int:
		return self.__status

	@property
	def output(self) -> str:
		return self.__output


# Global function to invoke an external program and return a 'Result' instance with the program's exit code and output.
def invoke(line : str) -> Result:
	# Capture stderr and stdout interleaved in the same output string by using stderr=...STDOUT and stdout=...PIPE.
	result = subprocess.run(
		shlex.split(line), stderr=subprocess.STDOUT, stdout=subprocess.PIPE, check=False, shell=False, text=False
	)
	output = result.stdout.decode('utf-8')
	return Result(result.returncode, output)

