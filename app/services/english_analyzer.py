"""Small local English baseline for the multilingual demo API."""

from __future__ import annotations

import re

from app.services.preprocessing import LABELS

_WORD = re.compile(r"[a-z]+(?:'[a-z]+)?", re.IGNORECASE)

_KEYWORDS = {
    "Appearance": {"ugly", "fat", "bald", "appearance", "looks"},
    "Cussing": {"damn", "hell", "idiot", "stupid", "loser", "moron", "jerk", "fool"},
    "Hatred": {"hate", "hateful", "despise", "vermin", "disgusting"},
    "Racial": {"racist", "racism", "racial", "ethnicity", "immigrant"},
    "Sexual": {"sex", "sexual", "rape", "nude", "naked", "porn"},
    "Violence": {"kill", "murder", "hurt", "attack", "shoot", "threat"},
}

_SEVERITY = {
    "Violence": "high",
    "Sexual": "high",
    "Hatred": "high",
    "Cussing": "medium",
    "Appearance": "medium",
    "Racial": "medium",
}


def analyze_message(text: str) -> dict[str, object]:
    """Classify English text with deterministic keyword matching."""
    normalized = text.casefold()
    words = set(_WORD.findall(normalized))
    categories = []
    for label in LABELS:
        if label == "NOT":
            continue
        keywords = _KEYWORDS[label]
        if any(keyword.strip() in normalized if keyword.startswith(" ") else keyword in words for keyword in keywords):
            categories.append(label)

    if not categories:
        return {
            "is_harmful": False,
            "category": "safe",
            "categories": [],
            "severity": "safe",
            "confidence": 0.98,
            "explanation": "The English demo analyzer did not detect a configured harmful keyword.",
        }

    severity = "high" if any(_SEVERITY[label] == "high" for label in categories) else "medium"
    confidence = min(0.97, 0.84 + (0.04 * min(len(categories), 3)))
    return {
        "is_harmful": True,
        "category": categories[0],
        "categories": categories,
        "severity": severity,
        "confidence": confidence,
        "explanation": "The English demo analyzer matched one or more configured harmful keywords.",
    }
