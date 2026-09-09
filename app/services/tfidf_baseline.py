"""TF-IDF + One-vs-Rest Logistic Regression baseline for AraTox."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from app.services.preprocessing import LABELS, ProcessedSample, default_archive_path, load_dataset

RANDOM_STATE = 42


@dataclass(frozen=True)
class BaselineMetrics:
    micro_precision: float
    micro_recall: float
    micro_f1: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    exact_match_accuracy: float
    per_label: dict[str, dict[str, float]]


@dataclass(frozen=True)
class BaselineResult:
    metrics: BaselineMetrics
    training_time_seconds: float
    prediction_time_seconds: float
    training_samples: int
    test_samples: int
    number_of_labels: int
    vectorizer: TfidfVectorizer
    classifier: OneVsRestClassifier


def _texts(samples: tuple[ProcessedSample, ...]) -> list[str]:
    return [sample.text for sample in samples]


def _label_matrix(
    samples: tuple[ProcessedSample, ...], binarizer: MultiLabelBinarizer
):
    return binarizer.transform([sample.labels for sample in samples])


def train_and_evaluate(
    train: tuple[ProcessedSample, ...],
    test: tuple[ProcessedSample, ...],
) -> BaselineResult:
    """Fit on train only and evaluate on test only; no model is persisted."""
    if not train:
        raise ValueError("Training split must not be empty")
    if not test:
        raise ValueError("Test split must not be empty")

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    binarizer = MultiLabelBinarizer(classes=LABELS)
    binarizer.fit([LABELS])
    y_train = _label_matrix(train, binarizer)
    y_test = _label_matrix(test, binarizer)

    start = time.perf_counter()
    x_train = vectorizer.fit_transform(_texts(train))
    classifier = OneVsRestClassifier(
        LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    )
    classifier.fit(x_train, y_train)
    training_time = time.perf_counter() - start

    start = time.perf_counter()
    predictions = classifier.predict(vectorizer.transform(_texts(test)))
    prediction_time = time.perf_counter() - start

    micro_precision, micro_recall, micro_f1, _ = precision_recall_fscore_support(
        y_test, predictions, average="micro", zero_division=0
    )
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        y_test, predictions, average="macro", zero_division=0
    )
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, predictions, average=None, labels=range(len(LABELS)), zero_division=0
    )

    metrics = BaselineMetrics(
        micro_precision=micro_precision,
        micro_recall=micro_recall,
        micro_f1=micro_f1,
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        exact_match_accuracy=accuracy_score(y_test, predictions),
        per_label={
            label: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
            }
            for index, label in enumerate(LABELS)
        },
    )
    return BaselineResult(
        metrics=metrics,
        training_time_seconds=training_time,
        prediction_time_seconds=prediction_time,
        training_samples=len(train),
        test_samples=len(test),
        number_of_labels=len(LABELS),
        vectorizer=vectorizer,
        classifier=classifier,
    )


def run_default_baseline(project_root: str | Path = ".") -> BaselineResult:
    dataset = load_dataset(default_archive_path(project_root))
    return train_and_evaluate(dataset.train, dataset.test)


def print_report(result: BaselineResult) -> None:
    metrics = result.metrics
    print(f"Training samples: {result.training_samples}")
    print(f"Test samples: {result.test_samples}")
    print(f"Labels: {result.number_of_labels}")
    print(f"Training time (s): {result.training_time_seconds:.3f}")
    print(f"Prediction time (s): {result.prediction_time_seconds:.3f}")
    print(f"Micro precision: {metrics.micro_precision:.4f}")
    print(f"Micro recall: {metrics.micro_recall:.4f}")
    print(f"Micro F1: {metrics.micro_f1:.4f}")
    print(f"Macro precision: {metrics.macro_precision:.4f}")
    print(f"Macro recall: {metrics.macro_recall:.4f}")
    print(f"Macro F1: {metrics.macro_f1:.4f}")
    print(f"Exact-match accuracy: {metrics.exact_match_accuracy:.4f}")
    print("Per-label metrics:")
    for label, values in metrics.per_label.items():
        print(
            f"  {label}: precision={values['precision']:.4f} "
            f"recall={values['recall']:.4f} f1={values['f1']:.4f}"
        )


if __name__ == "__main__":
    print_report(run_default_baseline())
