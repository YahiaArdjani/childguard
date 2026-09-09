"""Deterministic AraTox preprocessing utilities; no model training is performed."""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

LABELS = (
    "Appearance",
    "Cussing",
    "Hatred",
    "Racial",
    "Sexual",
    "Violence",
    "NOT",
)
TRAIN_TEXT_COLUMN = "Text"
TEST_TEXT_COLUMN = "text"
TEST_LABEL_COLUMN = "true_label"
TRAIN_FILE = "aratox_train.tsv"
TEST_FILE = "aratox_test.csv"

_LABEL_ALIASES = {label.casefold(): label for label in LABELS}
_LABEL_ALIASES["not"] = "NOT"
_LABEL_ALIASES["vilence"] = "Violence"


@dataclass(frozen=True)
class ProcessedSample:
    """One preserved text and its normalized multi-label representation."""

    text: str
    labels: tuple[str, ...]
    split: str


@dataclass(frozen=True)
class PreprocessingStats:
    train_samples: int
    test_samples: int
    label_distribution: dict[str, int]
    invalid_or_unknown_labels: int
    duplicate_texts: int
    train_test_overlaps: int
    missing_text_rows: int

    @property
    def total_samples(self) -> int:
        return self.train_samples + self.test_samples


@dataclass(frozen=True)
class PreprocessedDataset:
    train: tuple[ProcessedSample, ...]
    test: tuple[ProcessedSample, ...]
    stats: PreprocessingStats


def _archive_member(zf: ZipFile, filename: str) -> str:
    for member in zf.namelist():
        if Path(member).name == filename:
            return member
    raise FileNotFoundError(f"{filename} was not found in the AraTox archive")


def normalize_label(label: str) -> str | None:
    """Return the canonical label, or None for an unknown/blank label."""
    return _LABEL_ALIASES.get(label.strip().casefold())


def parse_multilabel(value: str | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Parse comma-separated labels and return (known, unknown) labels."""
    if value is None:
        return (), ()

    known: list[str] = []
    unknown: list[str] = []
    for raw_label in value.split(","):
        stripped = raw_label.strip()
        if not stripped:
            continue
        canonical = normalize_label(stripped)
        if canonical is None:
            unknown.append(stripped)
        elif canonical not in known:
            known.append(canonical)
    return tuple(known), tuple(unknown)


def _read_rows(zf: ZipFile, filename: str, delimiter: str) -> list[dict[str, str]]:
    with zf.open(_archive_member(zf, filename)) as raw_file:
        text_file = (line.decode("utf-8-sig") for line in raw_file)
        return list(csv.DictReader(text_file, delimiter=delimiter))


def _train_labels(row: dict[str, str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    labels = []
    invalid = []
    for label in LABELS:
        value = row.get(label, "").strip()
        if value == "1":
            labels.append(label)
        elif value not in ("", "0"):
            invalid.append(f"{label}={value}")
    return tuple(labels), tuple(invalid)


def _clean_rows(
    rows: Iterable[dict[str, str]],
    split: str,
    text_column: str,
    label_column: str | None,
) -> tuple[list[ProcessedSample], int, int, Counter[str]]:
    samples: list[ProcessedSample] = []
    seen: set[str] = set()
    duplicate_texts = 0
    missing_text_rows = 0
    unknown_labels: Counter[str] = Counter()

    for row in rows:
        raw_text = row.get(text_column)
        if raw_text is None or not raw_text.strip():
            missing_text_rows += 1
            continue
        text = raw_text.strip()
        if text in seen:
            duplicate_texts += 1
            continue
        seen.add(text)

        if label_column is None:
            labels, invalid = _train_labels(row)
            unknown_labels.update(invalid)
        else:
            labels, unknown = parse_multilabel(row.get(label_column))
            unknown_labels.update(unknown)
        samples.append(ProcessedSample(text=text, labels=labels, split=split))

    return samples, duplicate_texts, missing_text_rows, unknown_labels


def load_dataset(archive_path: str | Path) -> PreprocessedDataset:
    """Load and normalize the AraTox train and test files from a zip archive."""
    with ZipFile(archive_path) as archive:
        train_rows = _read_rows(archive, TRAIN_FILE, "\t")
        test_rows = _read_rows(archive, TEST_FILE, ",")

    train, train_duplicates, train_missing, train_unknown = _clean_rows(
        train_rows, "train", TRAIN_TEXT_COLUMN, None
    )
    test, test_duplicates, test_missing, test_unknown = _clean_rows(
        test_rows, "test", TEST_TEXT_COLUMN, TEST_LABEL_COLUMN
    )

    distribution: Counter[str] = Counter(
        label for sample in (*train, *test) for label in sample.labels
    )
    stats = PreprocessingStats(
        train_samples=len(train),
        test_samples=len(test),
        label_distribution=dict(sorted(distribution.items())),
        invalid_or_unknown_labels=sum(train_unknown.values()) + sum(test_unknown.values()),
        duplicate_texts=train_duplicates + test_duplicates,
        train_test_overlaps=len({sample.text for sample in train} & {sample.text for sample in test}),
        missing_text_rows=train_missing + test_missing,
    )
    return PreprocessedDataset(tuple(train), tuple(test), stats)


def default_archive_path(project_root: str | Path) -> Path:
    return Path(project_root) / "data" / "AraTox A Multi-Dialect, Multi-Label Arabic Dataset.zip"


if __name__ == "__main__":
    dataset = load_dataset(default_archive_path(Path(__file__).resolve().parents[2]))
    print(dataset.stats)
