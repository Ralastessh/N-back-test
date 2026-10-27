"""참가자 행동 CSV 하나에서 원반응·재채점 정보가 보존되는지 검증한다."""
import csv
import tempfile
import unittest
from pathlib import Path
from utils.data_logger import DataLogger


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def trial(index=0, complete=True):
    return dict(block=1, n=2, index=index, visual=6, auditory="B", visual_target=True,
                auditory_target=False, warmup=False, scored=complete, complete=complete,
                onset=0., offset=.5, responses=[
                    dict(key="a", rt=.4, first_for_modality=True),
                    dict(key="l", rt=.4, first_for_modality=True),
                    dict(key="a", rt=.7, first_for_modality=False)],
                outcomes=dict(visual=dict(rt=.4, correct=True, outcome="hit"),
                              auditory=dict(rt=.4, correct=False, outcome="false_alarm")))


class BehaviorCSVTests(unittest.TestCase):
    def test_one_csv_retains_both_keys_repeat_rt_stimuli_and_block_accuracy(self):
        with tempfile.TemporaryDirectory() as directory:
            log = DataLogger(directory, "P001", "dual_nback", "training", dict(system_secret="hidden"))
            log.write("trial", **trial())
            log.write("block_summary", block=1, next_n=2, statistics=dict(
                visual=dict(total=1, correct=1, incorrect=0, accuracy=1),
                auditory=dict(total=1, correct=0, incorrect=1, accuracy=0)))
            log.write("display_runtime", system_secret="hidden")
            log.write("frame_intervals", system_secret="hidden")
            log.write("session_end", status="completed")
            log.close()
            self.assertEqual(list(Path(directory).iterdir()), [log.path])
            self.assertEqual(log.path.suffix, ".csv")
            row = read_rows(log.path)[0]
            self.assertEqual(row["auditory_letter"], "B")
            self.assertEqual(row["visual_position"], "6")
            self.assertEqual(row["visual_rt_s"], "0.4")
            self.assertEqual(row["response_keys"], "a;l;a")
            self.assertEqual(row["response_rts_s"], "0.4;0.4;0.7")
            self.assertEqual(row["response_first_flags"], "1;1;0")
            self.assertEqual(row["visual_outcome"], "hit")
            self.assertEqual(row["auditory_outcome"], "false_alarm")
            self.assertEqual(row["block_visual_accuracy_pct"], "100")
            self.assertEqual(row["block_auditory_accuracy_pct"], "0")
            self.assertEqual(row["session_status"], "completed")
            self.assertNotIn("hidden", log.path.read_text())

    def test_no_response_warmup_and_aborted_incomplete_trial_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            log = DataLogger(directory, "test", "dual_nback", "training", {})
            row = trial()
            row.update(responses=[], warmup=True, scored=False, outcomes=dict(
                visual=dict(rt=None, correct=False, outcome="miss"),
                auditory=dict(rt=None, correct=True, outcome="correct_rejection")))
            log.write("trial", **row)
            log.write("trial", **trial(1, complete=False))
            log.write("session_end", status="aborted")
            log.close()
            rows = read_rows(log.path)
            self.assertEqual(rows[0]["visual_rt_s"], "")
            self.assertEqual(rows[0]["visual_responded"], "False")
            self.assertEqual(rows[0]["visual_outcome"], "miss")
            self.assertEqual(rows[0]["auditory_outcome"], "correct_rejection")
            self.assertEqual(rows[0]["scored"], "False")
            self.assertEqual(rows[1]["complete"], "False")
            self.assertEqual(rows[1]["visual_correct"], "")
            self.assertEqual(rows[1]["visual_rt_s"], "0.4")
            self.assertEqual(rows[1]["block_visual_accuracy_pct"], "")
            self.assertTrue(all(row["session_status"] == "aborted" for row in rows))

    def test_span_responses_and_unfinished_stimulus_share_single_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            log = DataLogger(directory, "test", "reading_span", "pretest", {})
            log.write("sentence_start", stage="test", item_id="1", sentence="A fish can swim.")
            log.write("sentence_judgment", stage="test", item_id="1", sentence="A fish can swim.",
                      expected="True", response="y", rt=.8, correct=True)
            log.write("reading_recall", stage="test", expected=["swim"], response=["swim"], rt=1.2, exact=True)
            log.write("sentence_start", stage="test", item_id="2", sentence="Unfinished sentence.")
            log.write("session_end", status="aborted")
            log.close()
            rows = read_rows(log.path)
            self.assertEqual(len(list(Path(directory).iterdir())), 1)
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["rt_s"], "0.8")
            self.assertEqual(rows[1]["expected"], '["swim"]')
            self.assertTrue(rows[2]["event_type"].endswith("_incomplete"))
            self.assertEqual(rows[2]["item_id"], "2")

    def test_empty_session_is_header_only_and_close_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            log = DataLogger(directory, "test", "dual_nback", "training", {})
            log.close()
            log.close()
            self.assertEqual(read_rows(log.path), [])
            self.assertEqual(len(list(Path(directory).iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
