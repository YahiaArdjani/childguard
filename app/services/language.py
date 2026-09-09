"""Lightweight language detection for Arabic and Latin-script input."""

from __future__ import annotations

import re

ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def detect_language(text: str) -> str:
    """Return ``ar`` when Arabic script is present, otherwise ``en``."""
    return "ar" if ARABIC_SCRIPT.search(text) else "en"
