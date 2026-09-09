import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import MAX_TEXT_LENGTH

client = TestClient(app)

class AnalyzeEndpointTests(unittest.TestCase):
    def test_health_reports_loaded_model(self) -> None:
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "model_loaded": True})

    def test_model_info_reports_multilingual_architecture(self) -> None:
        response = client.get("/model-info")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["languages_supported"], ["ar", "en"])
        self.assertIn("TF-IDF", response.json()["architecture"])
        self.assertIn("Cussing", response.json()["active_categories"])

    def test_valid_request_returns_expected_schema(self) -> None:
        response = client.post("/analyze", json={"text": "و ليش هالصورة المقرفة متل وجك يا ابن الكلب يلعن ابوك المجرم"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"is_harmful", "category", "categories", "severity", "confidence", "explanation", "language"})
        self.assertTrue(response.json()["is_harmful"])
        self.assertTrue(response.json()["categories"])
        self.assertIn(response.json()["language"], {"ar", "en"})

    def test_analyze_response_always_contains_valid_language(self) -> None:
        for text in ("مرحبا كيف حالك", "Hello, how are you?"):
            response = client.post("/analyze", json={"text": text})
            self.assertEqual(response.status_code, 200)
            self.assertIn(response.json().get("language"), {"ar", "en"})

    def test_safe_message_returns_safe_category(self) -> None:
        response = client.post("/analyze", json={"text": "مرحبا كيف حالك"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_harmful"])
        self.assertEqual(response.json()["category"], "safe")
        self.assertEqual(response.json()["categories"], [])
        self.assertEqual(response.json()["severity"], "safe")
        self.assertEqual(response.json()["language"], "ar")

    def test_arabic_insult_returns_medium_cussing(self) -> None:
        response = client.post("/analyze", json={"text": "و ليش هالصورة المقرفة متل وجك يا ابن الكلب يلعن ابوك المجرم"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_harmful"])
        self.assertEqual(response.json()["categories"], ["Cussing"])
        self.assertEqual(response.json()["severity"], "medium")
        self.assertEqual(response.json()["language"], "ar")

    def test_arabic_multi_label_cussing_hatred_returns_high_severity(self) -> None:
        response = client.post("/analyze", json={"text": "اعرف انه نجس اما خسيسا فهذه جديده"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_harmful"])
        self.assertEqual(response.json()["categories"], ["Cussing", "Hatred"])
        self.assertEqual(response.json()["severity"], "high")

    def test_english_harmful_text_uses_english_pipeline(self) -> None:
        response = client.post("/analyze", json={"text": "I hate you, idiot."})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_harmful"])
        self.assertEqual(response.json()["language"], "en")
        self.assertIn("Cussing", response.json()["categories"])
        self.assertIn("Hatred", response.json()["categories"])
        self.assertEqual(response.json()["severity"], "high")

    def test_english_safe_text_uses_safe_contract(self) -> None:
        response = client.post("/analyze", json={"text": "Hello, how are you?"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_harmful"])
        self.assertEqual(response.json()["language"], "en")
        self.assertEqual(response.json()["categories"], [])
        self.assertEqual(response.json()["severity"], "safe")

    def test_empty_text_is_rejected(self) -> None:
        self.assertEqual(client.post("/analyze", json={"text": ""}).status_code, 422)

    def test_whitespace_text_is_rejected(self) -> None:
        self.assertEqual(client.post("/analyze", json={"text": "   \n"}).status_code, 422)

    def test_overlong_text_is_rejected(self) -> None:
        self.assertEqual(client.post("/analyze", json={"text": "a" * (MAX_TEXT_LENGTH + 1)}).status_code, 422)
