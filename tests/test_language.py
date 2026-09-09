import unittest

from app.services.language import detect_language


class LanguageDetectionTests(unittest.TestCase):
    def test_detects_arabic_script(self) -> None:
        self.assertEqual(detect_language("مرحبا كيف حالك"), "ar")

    def test_detects_latin_script_as_english(self) -> None:
        self.assertEqual(detect_language("Hello, how are you?"), "en")

    def test_mixed_text_prefers_arabic_when_arabic_script_is_present(self) -> None:
        self.assertEqual(detect_language("Hello مرحبا"), "ar")


if __name__ == "__main__":
    unittest.main()
