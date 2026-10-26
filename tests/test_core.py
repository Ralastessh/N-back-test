import json
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
            a.write("trial", rt=0.2)
            a.close()
            b.close()
            self.assertNotEqual(a.path, b.path)
            self.assertEqual(json.loads(a.path.read_text().splitlines()[1])["rt"], 0.2)


if __name__ == "__main__":
    unittest.main()
