#!/usr/bin/env python3

VERSION = "0.13"
COMPANY = "Vendsyssel Historiske Museum"
CONTACT = "me@vhm.dk"
TESTING = True


class Version(object):
	"""A simple wrapper around everything related to version information about the running script."""

	def __init__(self, product : str, version : str, company : str, contact : str, testing : bool) -> None:
		self.product = product
		self.program = product + ".py"
		self.version = version
		self.company = company
		self.contact = contact
		self.testing = testing

	def banner(self) -> str:
		return "%s v%s%s - Copyright (c) 2024-2025 %s (%s).  All Rights Reserved." % (
			self.program,
			self.version,
			" (TEST)" if self.testing else "",
			self.company,
			self.contact
		)



