import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import MAX_TEXT_LENGTH

client = TestClient(app)

class AnalyzeEndpointTests(unittest.TestCase):
    def test_valid_request_returns_expected_schema(self) -> None:
        response = client.post("/analyze", json={"text": "You are stupid."})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"is_harmful", "category", "severity", "confidence", "explanation"})
        self.assertTrue(response.json()["is_harmful"])
        self.assertEqual(response.json()["category"], "insult")

    def test_empty_text_is_rejected(self) -> None:
        self.assertEqual(client.post("/analyze", json={"text": ""}).status_code, 422)

    def test_whitespace_text_is_rejected(self) -> None:
        self.assertEqual(client.post("/analyze", json={"text": "   \n"}).status_code, 422)

    def test_overlong_text_is_rejected(self) -> None:
        self.assertEqual(client.post("/analyze", json={"text": "a" * (MAX_TEXT_LENGTH + 1)}).status_code, 422)
