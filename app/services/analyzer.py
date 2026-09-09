"""Persisted optimized NLP analyzer loaded once for the FastAPI process."""

from __future__ import annotations

from pathlib import Path

import joblib

from app.services.optimized_baseline import apply_logical_rules
from app.services.preprocessing import LABELS
from app.services.english_analyzer import analyze_message as analyze_english_message
from app.services.language import detect_language

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "childguard_model.joblib"
VECTORIZER_PATH = MODEL_DIR / "childguard_vectorizer.joblib"
THRESHOLDS_PATH = MODEL_DIR / "childguard_thresholds.joblib"

_classifier = joblib.load(MODEL_PATH)
_vectorizer = joblib.load(VECTORIZER_PATH)
_thresholds = joblib.load(THRESHOLDS_PATH)

_HARMFUL_LABELS = tuple(label for label in LABELS if label != "NOT")
_SEVERITY = {
	"Violence": "high",
	"Sexual": "high",
	"Hatred": "high",
	"Cussing": "medium",
	"Appearance": "medium",
	"Racial": "medium",
}


def analyze_message(text: str) -> dict[str, object]:
	"""Analyze one message using the Arabic or English local pipeline."""
	language = detect_language(text)
	if language not in {"ar", "en"}:
		language = "ar"
	if language == "en":
		result = analyze_english_message(text)
		result["language"] = language
		return result

	probabilities = _classifier.predict_proba(_vectorizer.transform([text]))
	predictions = apply_logical_rules(probabilities, _thresholds)
	predicted_indices = [index for index, value in enumerate(predictions[0]) if value]
	categories = [
		LABELS[index]
		for index in predicted_indices
		if LABELS[index] in _HARMFUL_LABELS
	]

	if categories:
		confidence = max(
			float(probabilities[0][LABELS.index(category)]) for category in categories
		)
		severity = max((_SEVERITY[category] for category in categories), key=lambda value: value == "high")
		category = categories[0]
		explanation = "The optimized TF-IDF demo model detected one or more harmful content patterns."
	else:
		confidence = float(probabilities[0][LABELS.index("NOT")])
		severity = "safe"
		category = "safe"
		explanation = "The optimized TF-IDF demo model did not detect a harmful label above its calibrated threshold."

	return {
		"is_harmful": bool(categories),
		"category": category,
		"categories": categories,
		"severity": severity,
		"confidence": min(max(confidence, 0.0), 1.0),
		"explanation": explanation,
		"language": language,
	}
