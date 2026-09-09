"""Train and persist the ChildGuard optimized TF-IDF model."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from app.services.optimized_baseline import (
    RANDOM_STATE,
    VALIDATION_SIZE,
    _texts,
    calibrate_thresholds,
)
from app.services.preprocessing import LABELS, default_archive_path, load_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "childguard_model.joblib"
VECTORIZER_PATH = MODEL_DIR / "childguard_vectorizer.joblib"
THRESHOLDS_PATH = MODEL_DIR / "childguard_thresholds.joblib"


def train_and_save() -> dict[str, object]:
    dataset = load_dataset(default_archive_path(PROJECT_ROOT))
    train = dataset.train
    train_indices, validation_indices = train_test_split(
        np.arange(len(train)), test_size=VALIDATION_SIZE, random_state=RANDOM_STATE
    )
    fitting_samples = tuple(train[index] for index in train_indices)
    validation_samples = tuple(train[index] for index in validation_indices)

    binarizer = MultiLabelBinarizer(classes=LABELS)
    binarizer.fit([LABELS])
    y_fitting = binarizer.transform([sample.labels for sample in fitting_samples])
    y_validation = binarizer.transform([sample.labels for sample in validation_samples])
    y_train = binarizer.transform([sample.labels for sample in train])

    validation_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    x_fitting = validation_vectorizer.fit_transform(_texts(fitting_samples))
    validation_classifier = OneVsRestClassifier(
        LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=RANDOM_STATE,
        )
    )
    validation_classifier.fit(x_fitting, y_fitting)
    thresholds = calibrate_thresholds(
        validation_classifier.predict_proba(
            validation_vectorizer.transform(_texts(validation_samples))
        ),
        y_validation,
    )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    classifier = OneVsRestClassifier(
        LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=RANDOM_STATE,
        )
    )
    classifier.fit(vectorizer.fit_transform(_texts(train)), y_train)

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(classifier, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(thresholds, THRESHOLDS_PATH)
    return {
        "training_samples": len(train),
        "validation_samples": len(validation_samples),
        "labels": LABELS,
        "thresholds": thresholds,
        "paths": (MODEL_PATH, VECTORIZER_PATH, THRESHOLDS_PATH),
    }


if __name__ == "__main__":
    report = train_and_save()
    print(f"Training samples: {report['training_samples']}")
    print(f"Validation samples: {report['validation_samples']}")
    print(f"Thresholds: {report['thresholds']}")
    for path in report["paths"]:
        print(f"Saved: {path}")
