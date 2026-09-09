"""Optimized TF-IDF + One-vs-Rest Logistic Regression baseline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from app.services.preprocessing import LABELS, ProcessedSample, default_archive_path, load_dataset
from app.services.tfidf_baseline import BaselineMetrics, RANDOM_STATE

HARMFUL_LABELS = tuple(label for label in LABELS if label != "NOT")
VALIDATION_SIZE = 0.2
THRESHOLD_GRID = np.linspace(0.05, 0.95, 19)


@dataclass(frozen=True)
class OptimizedResult:
    metrics: BaselineMetrics
    thresholds: dict[str, float]
    training_time_seconds: float
    prediction_time_seconds: float
    training_samples: int
    validation_samples: int
    test_samples: int
    number_of_labels: int
    vectorizer: TfidfVectorizer
    classifier: OneVsRestClassifier


def _texts(samples: tuple[ProcessedSample, ...]) -> list[str]:
    return [sample.text for sample in samples]


def _binarizer() -> MultiLabelBinarizer:
    binarizer = MultiLabelBinarizer(classes=LABELS)
    binarizer.fit([LABELS])
    return binarizer


def _label_matrix(
    samples: tuple[ProcessedSample, ...], binarizer: MultiLabelBinarizer
) -> np.ndarray:
    return binarizer.transform([sample.labels for sample in samples])


def calibrate_thresholds(
    probabilities: np.ndarray,
    expected: np.ndarray,
    labels: tuple[str, ...] = LABELS,
) -> dict[str, float]:
    """Choose one F1-maximizing threshold per label on validation predictions."""
    thresholds: dict[str, float] = {}
    for index, label in enumerate(labels):
        scores = [
            (f1_score(expected[:, index], probabilities[:, index] >= threshold, zero_division=0), -threshold)
            for threshold in THRESHOLD_GRID
        ]
        best_index = max(range(len(scores)), key=lambda index: scores[index])
        thresholds[label] = float(THRESHOLD_GRID[best_index])
    return thresholds


def apply_logical_rules(
    probabilities: np.ndarray,
    thresholds: dict[str, float],
    labels: tuple[str, ...] = LABELS,
) -> np.ndarray:
    """Apply per-label thresholds and make NOT mutually exclusive with harm."""
    predictions = np.zeros_like(probabilities, dtype=int)
    harmful_indices = [index for index, label in enumerate(labels) if label != "NOT"]
    not_index = labels.index("NOT")
    for index, label in enumerate(labels):
        predictions[:, index] = probabilities[:, index] >= thresholds[label]

    has_harmful_prediction = predictions[:, harmful_indices].any(axis=1)
    predictions[has_harmful_prediction, not_index] = 0
    safe_rows = np.flatnonzero(~has_harmful_prediction)
    predictions[np.ix_(safe_rows, harmful_indices)] = 0
    predictions[safe_rows, not_index] = 1
    return predictions


def _metrics(expected: np.ndarray, predictions: np.ndarray) -> BaselineMetrics:
    micro_precision, micro_recall, micro_f1, _ = precision_recall_fscore_support(
        expected, predictions, average="micro", zero_division=0
    )
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        expected, predictions, average="macro", zero_division=0
    )
    precision, recall, f1, _ = precision_recall_fscore_support(
        expected, predictions, average=None, labels=range(len(LABELS)), zero_division=0
    )
    return BaselineMetrics(
        micro_precision=float(micro_precision),
        micro_recall=float(micro_recall),
        micro_f1=float(micro_f1),
        macro_precision=float(macro_precision),
        macro_recall=float(macro_recall),
        macro_f1=float(macro_f1),
        exact_match_accuracy=float(accuracy_score(expected, predictions)),
        per_label={
            label: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
            }
            for index, label in enumerate(LABELS)
        },
    )


def train_and_evaluate_optimized(
    train: tuple[ProcessedSample, ...],
    test: tuple[ProcessedSample, ...],
) -> OptimizedResult:
    """Calibrate on train-only validation data and evaluate once on test data."""
    if len(train) < 2:
        raise ValueError("Training split must contain at least two samples")
    if not test:
        raise ValueError("Test split must not be empty")

    train_indices, validation_indices = train_test_split(
        np.arange(len(train)), test_size=VALIDATION_SIZE, random_state=RANDOM_STATE
    )
    fitting_samples = tuple(train[index] for index in train_indices)
    validation_samples = tuple(train[index] for index in validation_indices)
    binarizer = _binarizer()
    y_fit = _label_matrix(fitting_samples, binarizer)
    y_validation = _label_matrix(validation_samples, binarizer)
    y_train = _label_matrix(train, binarizer)
    y_test = _label_matrix(test, binarizer)

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    start = time.perf_counter()
    x_fit = vectorizer.fit_transform(_texts(fitting_samples))
    classifier = OneVsRestClassifier(
        LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=RANDOM_STATE,
        )
    )
    classifier.fit(x_fit, y_fit)
    validation_probabilities = classifier.predict_proba(
        vectorizer.transform(_texts(validation_samples))
    )
    thresholds = calibrate_thresholds(validation_probabilities, y_validation)

    x_train = vectorizer.fit_transform(_texts(train))
    classifier.fit(x_train, y_train)
    training_time = time.perf_counter() - start

    start = time.perf_counter()
    test_probabilities = classifier.predict_proba(vectorizer.transform(_texts(test)))
    predictions = apply_logical_rules(test_probabilities, thresholds)
    prediction_time = time.perf_counter() - start

    return OptimizedResult(
        metrics=_metrics(y_test, predictions),
        thresholds=thresholds,
        training_time_seconds=training_time,
        prediction_time_seconds=prediction_time,
        training_samples=len(train),
        validation_samples=len(validation_samples),
        test_samples=len(test),
        number_of_labels=len(LABELS),
        vectorizer=vectorizer,
        classifier=classifier,
    )


def run_default_optimized(project_root: str | Path = ".") -> OptimizedResult:
    dataset = load_dataset(default_archive_path(project_root))
    return train_and_evaluate_optimized(dataset.train, dataset.test)


def print_report(result: OptimizedResult) -> None:
    print(f"Training samples: {result.training_samples}")
    print(f"Validation samples: {result.validation_samples}")
    print(f"Test samples: {result.test_samples}")
    print(f"Training time (s): {result.training_time_seconds:.3f}")
    print(f"Prediction time (s): {result.prediction_time_seconds:.3f}")
    print(f"Thresholds: {result.thresholds}")
    for name in ("micro_precision", "micro_recall", "micro_f1", "macro_precision", "macro_recall", "macro_f1", "exact_match_accuracy"):
        print(f"{name}: {getattr(result.metrics, name):.4f}")


if __name__ == "__main__":
    print_report(run_default_optimized())
