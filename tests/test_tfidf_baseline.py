import unittest

import numpy as np

from app.services.preprocessing import LABELS, ProcessedSample
from app.services.optimized_baseline import apply_logical_rules, calibrate_thresholds, train_and_evaluate_optimized
from app.services.tfidf_baseline import train_and_evaluate


class TfidfBaselineTests(unittest.TestCase):
    def test_trains_multilabel_baseline_and_reports_all_metrics(self) -> None:
        train = tuple(
            ProcessedSample(f"message label {index}", (label,), "train")
            for index, label in enumerate(LABELS)
        ) + (
            ProcessedSample("message cussing sexual", ("Cussing", "Sexual"), "train"),
            ProcessedSample("message safe", ("NOT",), "train"),
        )
        test = (
            ProcessedSample("message cussing sexual", ("Cussing", "Sexual"), "test"),
            ProcessedSample("message safe", ("NOT",), "test"),
        )

        result = train_and_evaluate(train, test)

        self.assertEqual(result.training_samples, 9)
        self.assertEqual(result.test_samples, 2)
        self.assertEqual(result.number_of_labels, len(LABELS))
        self.assertEqual(set(result.metrics.per_label), set(LABELS))
        for name in (
            "micro_precision",
            "micro_recall",
            "micro_f1",
            "macro_precision",
            "macro_recall",
            "macro_f1",
            "exact_match_accuracy",
        ):
            self.assertGreaterEqual(getattr(result.metrics, name), 0.0)
            self.assertLessEqual(getattr(result.metrics, name), 1.0)

    def test_vectorizer_is_fit_on_training_text_only(self) -> None:
        train = tuple(
            ProcessedSample(f"كلمة تدريب {label}", (label,), "train")
            for label in LABELS
        )
        test = (
            ProcessedSample("كلمة اختبار جديدة", ("NOT",), "test"),
            ProcessedSample("كلمة أخرى", ("Cussing",), "test"),
        )

        result = train_and_evaluate(train, test)

        self.assertNotIn("اختبار", result.vectorizer.vocabulary_)
        self.assertNotIn("جديدة", result.vectorizer.vocabulary_)

    def test_calibrates_a_threshold_per_label(self) -> None:
        probabilities = np.full((4, len(LABELS)), 0.1)
        expected = np.zeros((4, len(LABELS)), dtype=int)
        probabilities[:, LABELS.index("Racial")] = (0.2, 0.4, 0.8, 0.9)
        expected[2:, LABELS.index("Racial")] = 1

        thresholds = calibrate_thresholds(probabilities, expected)

        self.assertEqual(set(thresholds), set(LABELS))
        self.assertLessEqual(thresholds["Racial"], 0.8)

    def test_logical_rules_make_not_mutually_exclusive_with_harm(self) -> None:
        probabilities = np.zeros((2, len(LABELS)))
        probabilities[0, LABELS.index("Racial")] = 0.8
        probabilities[0, LABELS.index("Hatred")] = 0.7
        probabilities[0, LABELS.index("NOT")] = 0.99
        probabilities[1, LABELS.index("NOT")] = 0.6
        thresholds = {label: 0.5 for label in LABELS}

        predictions = apply_logical_rules(probabilities, thresholds)

        self.assertEqual(predictions[0, LABELS.index("Racial")], 1)
        self.assertEqual(predictions[0, LABELS.index("Hatred")], 1)
        self.assertEqual(predictions[0, LABELS.index("NOT")], 0)
        self.assertEqual(predictions[1, LABELS.index("NOT")], 1)
        self.assertEqual(predictions[1, :-1].sum(), 0)

    def test_optimized_training_returns_calibrated_result(self) -> None:
        train = tuple(
            ProcessedSample(f"message label {label} {index}", (label,), "train")
            for label in LABELS
            for index in range(4)
        ) + tuple(
            ProcessedSample(f"message cussing sexual {index}", ("Cussing", "Sexual"), "train")
            for index in range(8)
        )
        test = (
            ProcessedSample("message cussing sexual 0", ("Cussing", "Sexual"), "test"),
            ProcessedSample("message label NOT", ("NOT",), "test"),
        )

        result = train_and_evaluate_optimized(train, test)

        self.assertEqual(result.training_samples, len(train))
        self.assertEqual(result.test_samples, len(test))
        self.assertEqual(set(result.thresholds), set(LABELS))


if __name__ == "__main__":
    unittest.main()
