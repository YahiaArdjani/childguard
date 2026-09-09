from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FrontendContractTests(unittest.TestCase):
    def test_result_markup_supports_categories_and_severity(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="result-categories"', html)
        self.assertIn('id="result-language"', html)
        self.assertIn('class="severity-badge"', html)
        self.assertIn('id="error-state"', html)

    def test_javascript_supports_multi_label_and_request_states(self) -> None:
        javascript = (ROOT / "js/app.js").read_text(encoding="utf-8")
        for expected in (
            "apiResult.categories",
            "result-categories",
            "result.language",
            "severity-${result.severityClass",
            "elements.input.disabled = true",
            "Unable to reach the analysis service",
        ):
            self.assertIn(expected, javascript)

    def test_styles_define_severity_states(self) -> None:
        css = (ROOT / "css/style.css").read_text(encoding="utf-8")
        for expected in (".severity-safe", ".severity-medium", ".severity-high", ".category-tag"):
            self.assertIn(expected, css)


if __name__ == "__main__":
    unittest.main()
