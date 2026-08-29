"""Temporary deterministic analyzer used only to demonstrate the MVP flow."""
from app.models.schemas import AnalyzeResponse

def analyze_message(text: str) -> AnalyzeResponse:
    """Produce demo data only. Submitted text is neither logged nor stored."""
    normalized = text.casefold()
    if any(phrase in normalized for phrase in ("kill you", "hurt you", "threat")):
        return AnalyzeResponse(is_harmful=True, category="threat", severity="high", confidence=0.96, explanation="The message matches a temporary demo pattern for threatening language.")
    if any(word in normalized for word in ("stupid", "idiot", "loser", "ugly")):
        return AnalyzeResponse(is_harmful=True, category="insult", severity="medium", confidence=0.90, explanation="The message matches a temporary demo pattern for an insult directed at another person.")
    if any(phrase in normalized for phrase in ("nobody likes you", "i hate you", "go away")):
        return AnalyzeResponse(is_harmful=True, category="harassment", severity="medium", confidence=0.88, explanation="The message matches a temporary demo pattern for targeted harmful language.")
    return AnalyzeResponse(is_harmful=False, category="safe", severity="low", confidence=0.96, explanation="This message does not match any temporary harmful-content demo patterns.")
