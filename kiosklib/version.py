#!/usr/bin/env python3
#**********************************************************************************************************************************
# BSD 3-Clause License for KioskForge - https://kioskforge.org:
#
# Copyright © 2024-2025 The KioskForge Team.
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

PRODUCT = "KioskForge"
VERSION = "0.26"
COMPANY = "The KioskForge Team"
CONTACT = ""
WEBSITE = "https://kioskforge.org/"

class Version:
	"""A simple wrapper around everything related to version information about the running script."""

	def __init__(self, basename : str) -> None:
		self.product = PRODUCT
		self.program = basename + ".py"
		self.version = VERSION
		self.company = COMPANY
		self.contact = CONTACT

	def banner(self) -> str:
		result  = f"{self.program} v{self.version} - {WEBSITE}"
		if CONTACT:
			result += f" - {CONTACT}"
		result += "\n"
		result += f"Copyright (c) 2024-2025 {self.company}."
		return result
