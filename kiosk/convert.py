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
from typing import Any, Dict


# Converts the keys of the specified dictionary into a regular expression that validates the given set of keys.
def dict_to_regex(dictionary : Dict[str, Any]) -> str:
	return "(" + "|".join(dictionary.keys()) + ")"


# Dictionary of valid responses in various prompts and their mappings to the corresponding boolean values.
BOOLEANS = {
	'0'     : False,
	'f'     : False,
	'false' : False,
	'n'     : False,
	'1'     : True,
	't'     : True,
	'true'  : True,
	'y'     : True
}

BOOLEAN_REGEX = dict_to_regex(BOOLEANS)

# The complete list of layouts supported by Ubuntu Server (from July, 2024).
KEYBOARDS = {
	"af"    : "Dari",
	"al"    : "Albanian",
	"am"    : "Armenian",
	"ara"   : "Arabic",
	"at"    : "German (Austria)",
	"au"    : "English (Australia)",
	"az"    : "Azerbaijani",
	"ba"    : "Bosnian",
	"bd"    : "Bangla",
	"be"    : "Belgian",
	"bg"    : "Bulgarian",
	"br"    : "Portuguese (Brazil)",
	"brai"  : "Braille",
	"bt"    : "Dzongkha",
	"bw"    : "Tswana",
	"by"    : "Belarusian",
	"ca"    : "French (Canada)",
	"cd"    : "French (Democratic Republic of the Congo)",
	"ch"    : "German (Switzerland)",
	"cm"    : "English (Cameroon)",
	"cn"    : "Chinese",
	"cz"    : "Czech",
	"de"    : "German",
	"dk"    : "Danish",
	"dz"    : "Berber (Algeria, Latin)",
	"ee"    : "Estonian",
	"eg"    : "Arabic (Egypt)",
	"epo"   : "Esperanto",
	"es"    : "Spanish",
	"et"    : "Amharic",
	"fi"    : "Finnish",
	"fo"    : "Faroese",
	"fr"    : "French",
	"gb"    : "English (UK)",
	"ge"    : "Georgian",
	"gh"    : "English (Ghana)",
	"gn"    : "N'Ko (AZERTY)",
	"gr"    : "Greek",
	"hr"    : "Croatian",
	"hu"    : "Hungarian",
	"id"    : "Indonesian (Latin)",
	"ie"    : "Irish",
	"il"    : "Hebrew",
	"in"    : "Indian",
	"iq"    : "Arabic (Iraq)",
	"ir"    : "Persian",
	"is"    : "Icelandic",
	"it"    : "Italian",
	"jp"    : "Japanese",
	"ke"    : "Swahili (Kenya)",
	"kg"    : "Kyrgyz",
	"kh"    : "Khmer (Cambodia)",
	"kr"    : "Korean",
	"kz"    : "Kazakh",
	"la"    : "Lao",
	"latam" : "Spanish (Latin American)",
	"lk"    : "Sinhala (phonetic)",
	"lt"    : "Lithuanian",
	"lv"    : "Latvian",
	"ma"    : "Arabic (Morocco)",
	"md"    : "Moldavian",
	"me"    : "Montenegrin",
	"mk"    : "Macedonian",
	"ml"    : "Bambara",
	"mm"    : "Burmese",
	"mn"    : "Mongolian",
	"mt"    : "Maltese",
	"mv"    : "Dhivehi",
	"my"    : "Malay (Jawi, Arabic Keyboard)",
	"ng"    : "English (Nigeria)",
	"nl"    : "Dutch",
	"no"    : "Norwegian",
	"np"    : "Nepali",
	"nz"    : "English (New Zealand)",
	"ph"    : "Filipino",
	"pk"    : "Urdu (Pakistan)",
	"pl"    : "Polish",
	"pt"    : "Portuguese",
	"ro"    : "Romanian",
	"rs"    : "Serbian",
	"ru"    : "Russian",
	"se"    : "Swedish",
	"si"    : "Slovenian",
	"sk"    : "Slovak",
	"sn"    : "Wolof",
	"sy"    : "Arabic (Syria)",
	"tg"    : "French (Togo)",
	"th"    : "Thai",
	"tj"    : "Tajik",
	"tm"    : "Turkmen",
	"tr"    : "Turkish",
	"tw"    : "Taiwanese",
	"tz"    : "Swahili (Tanzania)",
	"ua"    : "Ukrainian",
	"us"    : "English (US)",
	"uz"    : "Uzbek",
	"vn"    : "Vietnamese",
	"za"    : "English (South Africa)",
}

# Build the global variable 'KEYBOARD_REGEX', which represents the 'KEYBOARDS' dictionary as a regular expression.
KEYBOARD_REGEX = dict_to_regex(KEYBOARDS)


