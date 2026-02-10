# Author: Phillip Graham
# Description: Defines methods used for general tasks
# Last Modified: Wed. Feb. 02, 2026

################################################################################
# Imports
################################################################################

################################################################################
# Functions
################################################################################

def is_kana(ch: str) -> bool:
    if len(ch) != 1:
        return False

    code = ord(ch)

    # Hiragana
    if 0x3040 <= code <= 0x309F:
        return True

    # Katakana
    if 0x30A0 <= code <= 0x30FF:
        return True

    # Katakana Phonetic Extensions (rare but legit)
    #if 0x31F0 <= code <= 0x31FF:
    #    return True

    return False

def is_kanji(ch: str) -> bool:
    if len(ch) != 1:
        return False

    code = ord(ch)

    # CJK Unified Ideographs
    if 0x4E00 <= code <= 0x9FFF:
        return True

    # CJK Unified Ideographs Extension A (rare but valid)
    if 0x3400 <= code <= 0x4DBF:
        return True

    return False
