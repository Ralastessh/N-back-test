import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import wave
from config import ROOT, DIGIT_SPAN, READING_SPAN, AUDIO_DIR
from utils.span_protocol import (
    digit_plans,
    expected_recall,
    span_summary,
    practice_timeout,
    reading_summary,
    load_reading_materials,
)
from utils.scoring import score_recall
from utils.data_logger import DataLogger


class DigitTests(unittest.TestCase):
    def test_forms_modes_and_adjacent_constraints(self):
        for seed in range(25):
            plans = digit_plans(seed, DIGIT_SPAN)
            all_sequences = []
            for (phase, mode, stage), sequences in plans.items():
                self.assertEqual(len(sequences), 2 if stage == "practice" else 14)
                if stage == "test":
                    expected = [
                        n for n in DIGIT_SPAN[mode + "_lengths"] for _ in range(2)
                    ]
                    self.assertEqual(list(map(len, sequences)), expected)
                for sequence in sequences:
                    self.assertTrue(set(sequence) <= set("123456789"))
                    self.assertTrue(all(a != b for a, b in zip(sequence, sequence[1:])))
                    all_sequences.append(tuple(sequence))
            self.assertEqual(len(all_sequences), len(set(all_sequences)))
        self.assertEqual(digit_plans(17, DIGIT_SPAN), digit_plans(17, DIGIT_SPAN))

    def test_backward_and_summary(self):
        self.assertEqual(expected_recall(list("129"), "backward"), list("921"))
        result = span_summary(
            [
                dict(length=3, exact=True),
                dict(length=3, exact=False),
                dict(length=4, exact=True),
            ]
        )
        self.assertEqual(result["maximum_span"], 4)
        self.assertEqual(result["total_correct"], 2)
        self.assertAlmostEqual(result["exact_serial_accuracy"], 2 / 3)


class ReadingTests(unittest.TestCase):
    def test_timeout_sample_sd(self):
        self.assertAlmostEqual(practice_timeout([1, 2, 3]), 4.5)
        with self.assertRaises(ValueError):
            practice_timeout([1])

    def test_missing_position_and_partial_credit(self):
        score = score_recall(["a", "b", "c"], ["a", "_", "c"])
        self.assertEqual(score["items_correct"], 2)
        self.assertFalse(score["exact"])
        rows = [
            score_recall(["a", "b"], ["a", "b"]),
            score_recall(["a", "b", "c", "d"], []),
        ]
        result = reading_summary(rows, [True] * 84 + [False] * 16, 0.85)
        self.assertEqual(result["position_correct_partial_credit"], 0.5)
        self.assertAlmostEqual(result["item_accuracy"], 1 / 3)
        self.assertTrue(result["processing_below_threshold"])
        self.assertFalse(
            reading_summary(rows, [True] * 85 + [False] * 15, 0.85)[
                "processing_below_threshold"
            ]
        )

    def test_draft_structure_and_review_gate(self):
        groups = load_reading_materials(
            ROOT / READING_SPAN["sentence_file"],
            READING_SPAN,
            ROOT / READING_SPAN["review_file"],
            False,
        )
        self.assertEqual(sum(map(len, groups["A"].values())), 42)
        self.assertEqual(sum(map(len, groups["B"].values())), 42)
        self.assertEqual(sum(map(len, groups["P"].values())), 6)
        # 사용자가 실제 문항을 승인한 후에도, 미승인 fixture의 차단을 독립 검사한다.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unreviewed.csv"
            with (ROOT / READING_SPAN["sentence_file"]).open(
                encoding="utf-8-sig", newline=""
            ) as handle:
                reader = csv.DictReader(handle)
                names, rows = reader.fieldnames, list(reader)
            rows[0]["reviewed"] = "no"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=names)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(ValueError):
                load_reading_materials(
                    path, READING_SPAN, ROOT / READING_SPAN["review_file"]
                )

    def test_review_hash_invalidates_changed_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sentences.csv"
            review = Path(directory) / "review.json"
            with (ROOT / READING_SPAN["sentence_file"]).open(
                encoding="utf-8-sig", newline=""
            ) as f:
                reader = csv.DictReader(f)
                names = reader.fieldnames
                rows = list(reader)
            for row in rows:
                row["reviewed"] = "yes"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=names)
                writer.writeheader()
                writer.writerows(rows)
            review.write_text(
                json.dumps(
                    dict(
                        forms_difficulty_reviewed=True,
                        reviewer="unit test fixture",
                        approved_csv_sha256=hashlib.sha256(
                            path.read_bytes()
                        ).hexdigest(),
                    )
                )
            )
            self.assertIn("A", load_reading_materials(path, READING_SPAN, review))
            path.write_text(
                path.read_text(encoding="utf-8-sig") + "\n", encoding="utf-8-sig"
            )
            with self.assertRaises(ValueError):
                load_reading_materials(path, READING_SPAN, review)


class ArtifactTests(unittest.TestCase):
    def test_audio_duration_and_non_silence(self):
        files = [AUDIO_DIR / f"{x}.wav" for x in "BFHJMQRW"] + [
            AUDIO_DIR / "digits" / f"{x}.wav" for x in "123456789"
        ]
        for path in files:
            with wave.open(str(path)) as wav:
                self.assertEqual(wav.getframerate(), 48000)
                self.assertEqual(wav.getnchannels(), 1)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertLessEqual(
                    wav.getnframes() / wav.getframerate(),
                    1 if path.parent.name == "digits" else 0.5,
                )
                self.assertTrue(any(wav.readframes(wav.getnframes())))

    def test_csv_stage_nested_outcomes_and_unicode(self):
        with tempfile.TemporaryDirectory() as directory:
            log = DataLogger(directory, "P001", "reading_span", "pretest", {})
            log.write(
                "trial",
                stage="practice",
                sentence='문장, "인용"',
                response=["가", "나"],
                rt=1.2,
                accuracy=0.5,
                outcomes=dict(visual=dict(correct=True, rt=0.2)),
            )
            log.write(
                "trial",
                stage="test",
                sentence="두 번째",
                response=[],
                rt=2,
                accuracy=0,
                new_field=123,
            )
            log.close()
            path = next(Path(directory).glob("*_trial.csv"))
            with path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["sentence"], '문장, "인용"')
            self.assertEqual(rows[0]["outcomes_visual_rt"], "0.2")
            self.assertEqual(json.loads(rows[0]["response"]), ["가", "나"])
            self.assertEqual(json.loads(rows[1]["extra_json"])["new_field"], 123)
            self.assertEqual(rows[1]["phase"], "pretest")


if __name__ == "__main__":
    unittest.main()
