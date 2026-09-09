"""Temporary deterministic analyzer used only to demonstrate the MVP flow."""
import re

from app.models.schemas import AnalyzeResponse


THREAT_PATTERNS = (
    "kill you",
    "hurt you",
    "threat",
    "سوف أقتلك",
    "سأقتلك",
    "سوف اقتلك",
    "ساقتلك",
    "سوف أؤذيك",
    "سأؤذيك",
    "سوف اوذيك",
    "ساؤذيك",
)
INSULT_PATTERNS = (
    "stupid",
    "idiot",
    "loser",
    "ugly",
    "أنت غبي",
    "انت غبي",
    "غبي",
    "أنت أحمق",
    "انت احمق",
    "أحمق",
    "احمق",
)
HARASSMENT_PATTERNS = (
    "nobody likes you",
    "i hate you",
    "go away",
)


def _normalize(text: str) -> str:
    """Normalize case and Arabic diacritics for stable demo matching."""
    without_diacritics = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    return without_diacritics.casefold()


def analyze_message(text: str) -> AnalyzeResponse:
    """Produce demo data only. Submitted text is neither logged nor stored."""
    normalized = _normalize(text)
    if any(phrase in normalized for phrase in THREAT_PATTERNS):
        return AnalyzeResponse(is_harmful=True, category="threat", severity="high", confidence=0.96, explanation="The message matches a temporary demo pattern for threatening language.")
    if any(word in normalized for word in INSULT_PATTERNS):
        return AnalyzeResponse(is_harmful=True, category="insult", severity="medium", confidence=0.90, explanation="The message matches a temporary demo pattern for an insult directed at another person.")
    if any(phrase in normalized for phrase in HARASSMENT_PATTERNS):
        return AnalyzeResponse(is_harmful=True, category="harassment", severity="medium", confidence=0.88, explanation="The message matches a temporary demo pattern for targeted harmful language.")
    return AnalyzeResponse(is_harmful=False, category="safe", severity="low", confidence=0.96, explanation="This message does not match any temporary harmful-content demo patterns.")
