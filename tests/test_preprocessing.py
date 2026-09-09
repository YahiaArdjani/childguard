import csv
from io import StringIO
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from app.services.preprocessing import load_dataset, normalize_label, parse_multilabel


class PreprocessingUnitTests(unittest.TestCase):
    def test_normalizes_known_labels_and_known_typo(self) -> None:
        self.assertEqual(normalize_label("Vilence"), "Violence")
        self.assertEqual(normalize_label("Not"), "NOT")
        self.assertIsNone(normalize_label("Unknown"))

    def test_parses_comma_separated_labels(self) -> None:
        self.assertEqual(
            parse_multilabel("Cussing, Sexual"),
            (("Cussing", "Sexual"), ()),
        )
        self.assertEqual(
            parse_multilabel("Vilence, Unknown"),
            (("Violence",), ("Unknown",)),
        )

    def test_loads_train_and_test_formats_and_reports_quality(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "dataset.zip"
            with ZipFile(archive_path, "w") as archive:
                train_rows = [
                    {"Appearance": "0", "Cussing": "1", "Hatred": "0", "NOT": "0", "Racial": "0", "Sexual": "0", "Violence": "0", "Text": "شتيمة", "WordCount": "1", "WordCountGroup": "Very Short"},
                    {"Appearance": "0", "Cussing": "0", "Hatred": "0", "NOT": "1", "Racial": "0", "Sexual": "0", "Violence": "0", "Text": "رسالة عادية", "WordCount": "2", "WordCountGroup": "Very Short"},
                    {"Appearance": "0", "Cussing": "0", "Hatred": "0", "NOT": "1", "Racial": "0", "Sexual": "0", "Violence": "0", "Text": "رسالة عادية", "WordCount": "2", "WordCountGroup": "Very Short"},
                    {"Appearance": "0", "Cussing": "0", "Hatred": "0", "NOT": "0", "Racial": "0", "Sexual": "0", "Violence": "0", "Text": "", "WordCount": "0", "WordCountGroup": "Very Short"},
                ]
                fieldnames = list(train_rows[0])
                train_buffer = StringIO()
                writer = csv.DictWriter(train_buffer, fieldnames=fieldnames, delimiter="\t")
                writer.writeheader()
                writer.writerows(train_rows)
                archive.writestr("folder/aratox_train.tsv", train_buffer.getvalue())

                test_rows = [
                    {"index": "1", "text": "تهديد", "true_label": "Vilence, Unknown"},
                    {"index": "2", "text": "رسالة عادية", "true_label": "Not"},
                ]
                test_buffer = StringIO()
                writer = csv.DictWriter(test_buffer, fieldnames=list(test_rows[0]))
                writer.writeheader()
                writer.writerows(test_rows)
                archive.writestr("folder/aratox_test.csv", test_buffer.getvalue())

            dataset = load_dataset(archive_path)

        self.assertEqual(len(dataset.train), 2)
        self.assertEqual(len(dataset.test), 2)
        self.assertEqual(dataset.train[0].labels, ("Cussing",))
        self.assertEqual(dataset.test[0].labels, ("Violence",))
        self.assertEqual(dataset.test[1].labels, ("NOT",))
        self.assertEqual(dataset.stats.duplicate_texts, 1)
        self.assertEqual(dataset.stats.missing_text_rows, 1)
        self.assertEqual(dataset.stats.train_test_overlaps, 1)
        self.assertEqual(dataset.stats.invalid_or_unknown_labels, 1)


if __name__ == "__main__":
    unittest.main()
