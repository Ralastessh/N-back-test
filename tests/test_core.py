import json
import csv
import tempfile
import unittest
from utils.sequence import generate_block
from utils.scoring import adapt_n, classify, score_recall
from utils.data_logger import DataLogger

LETTERS = tuple("BFHJ MQRW".replace(" ", ""))


class SequenceTests(unittest.TestCase):
    def test_exact_targets_and_no_accidental_matches(self):
        for n in (1, 2, 3, 8, 25):
            for seed in range(100):
                block = generate_block(n, LETTERS, seed)
                self.assertEqual(len(block), 20 + n)
                self.assertEqual(sum(t.visual_target for t in block), 6)
                self.assertEqual(sum(t.auditory_target for t in block), 6)
                self.assertEqual(
                    sum(t.visual_target and t.auditory_target for t in block), 2
                )
                for i, t in enumerate(block):
                    self.assertEqual(t.warmup, i < n)
                    if i >= n:
                        self.assertEqual(
                            t.visual_target, t.visual == block[i - n].visual
                        )
                        self.assertEqual(
                            t.auditory_target, t.auditory == block[i - n].auditory
                        )

    def test_seed(self):
        self.assertEqual(generate_block(2, LETTERS, 13), generate_block(2, LETTERS, 13))

    def test_invalid(self):
        for n in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                generate_block(n, LETTERS)
        with self.assertRaises(ValueError):
            generate_block(2, tuple("AAAAAAAA"))
        with self.assertRaises(ValueError):
            generate_block(2, LETTERS, simultaneous_targets=7)


class ScoringTests(unittest.TestCase):
    def test_outcomes(self):
        self.assertEqual(
            [classify(t, r) for t, r in [(1, 1), (1, 0), (0, 1), (0, 0)]],
            ["hit", "miss", "false_alarm", "correct_rejection"],
        )

    def test_adaptation_boundaries(self):
        for v, a, expected in [
            (2, 2, 3),
            (3, 0, 2),
            (5, 5, 2),
            (6, 0, 1),
            (0, 6, 1),
            (2, 6, 1),
            (6, 2, 1),
            (2, 3, 2),
        ]:
            self.assertEqual(
                adapt_n(2, v, a, min_n=1, decrease_rule="either"), expected
            )
        self.assertEqual(adapt_n(1, 6, 6, min_n=1, decrease_rule="either"), 1)

    def test_order_and_extra_recall(self):
        self.assertEqual(score_recall(["1", "2"], ["2", "1"])["items_correct"], 0)
        self.assertFalse(score_recall(["1"], ["1", "2"])["exact"])

    def test_logger_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            a = DataLogger(directory, "test", "dual_nback", "training", {})
            b = DataLogger(directory, "test", "dual_nback", "training", {})
            from tests.test_data_logging import trial
            a.write("trial", **trial())
            a.close()
            b.close()
            self.assertNotEqual(a.path, b.path)
            with a.path.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(list(csv.DictReader(handle))[0]["n"], "2")


class NbackSummaryTests(unittest.TestCase):
    def test_overall_accuracy_is_per_modality(self):
        from utils.scoring import nback_summary
        result = nback_summary(dict(visual=2, auditory=5), 20)
        self.assertEqual(result["visual"], dict(correct=18, incorrect=2, total=20, accuracy=.9))
        self.assertEqual(result["auditory"]["accuracy"], .75)
        self.assertEqual(nback_summary(dict(visual=0, auditory=20), 20)["auditory"]["correct"], 0)

    def test_warmup_scored_total_and_invalid_counts(self):
        from utils.scoring import nback_summary
        self.assertEqual(nback_summary(dict(visual=2), 22)["visual"]["correct"], 20)
        for errors, total in ((dict(visual=0), 0), (dict(visual=21), 20), (dict(visual=-1), 20)):
            with self.assertRaises(ValueError):
                nback_summary(errors, total)


if __name__ == "__main__":
    unittest.main()
