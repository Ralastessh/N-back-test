"""단계 제안·이메일 기반 Pretest 복원·키 선택 검증."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from utils.workflow import ask_continue, latest_completed_pretest, next_step


class WorkflowTests(unittest.TestCase):
    def test_next_step_uses_only_selected_span(self):
        self.assertEqual(next_step("reading_span", "pretest", "reading_span"),
                         ("dual_nback", "training"))
        self.assertEqual(next_step("dual_nback", "training", "reading_span"),
                         ("reading_span", "posttest"))
        self.assertIsNone(next_step("reading_span", "posttest", "reading_span"))

    def test_latest_completed_pretest_ignores_other_people_and_aborts(self):
        with tempfile.TemporaryDirectory() as directory:
            for index, (participant, task, status, when) in enumerate((
                ("same@hanyang.ac.kr", "digit_span", "completed", "2026-10-01T10:00:00+00:00"),
                ("other@hanyang.ac.kr", "reading_span", "completed", "2026-10-30T10:00:00+00:00"),
                ("same@hanyang.ac.kr", "reading_span", "aborted", "2026-10-29T10:00:00+00:00"),
                ("same@hanyang.ac.kr", "reading_span", "completed", "2026-10-20T10:00:00+00:00"),
            )):
                with (Path(directory) / f"{index}_responses.csv").open(
                        "w", encoding="utf-8-sig", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=[
                        "participant", "task", "phase", "session_status", "recorded_utc"])
                    writer.writeheader()
                    writer.writerow(dict(participant=participant, task=task,
                                         phase="pretest", session_status=status,
                                         recorded_utc=when))
            self.assertEqual(latest_completed_pretest(directory, "same@hanyang.ac.kr"),
                             "reading_span")
            self.assertIsNone(latest_completed_pretest(directory, "missing@hanyang.ac.kr"))
            with (Path(directory) / "new_kst_responses.csv").open(
                    "w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    "participant", "task", "phase", "session_status", "recorded_kst"])
                writer.writeheader()
                writer.writerow(dict(participant="same@hanyang.ac.kr", task="digit_span",
                                     phase="pretest", session_status="completed",
                                     recorded_kst="2026-10-20 20:00:00"))
            self.assertEqual(latest_completed_pretest(directory, "same@hanyang.ac.kr"),
                             "digit_span")

    def test_keyboard_choice_can_decline_or_continue(self):
        pressed = ["n", "space"]

        class Window:
            color = "black"

            def callOnFlip(self, callback):
                self.callback = callback

            def flip(self):
                self.callback()

        class Keyboard:
            def clearEvents(self):
                pass

            def waitKeys(self, **kwargs):
                self_keys = kwargs["keyList"]
                assert set(self_keys) == {"space", "n"}
                return [SimpleNamespace(name=pressed.pop(0))]

        class TextStim:
            def __init__(self, *args, **kwargs):
                pass

            def draw(self):
                pass

        Rect = TextStim

        psychopy = SimpleNamespace(visual=SimpleNamespace(TextStim=TextStim, Rect=Rect))
        hardware = SimpleNamespace(keyboard=SimpleNamespace(Keyboard=Keyboard))
        with patch.dict(sys.modules, {"psychopy": psychopy,
                                      "psychopy.hardware": hardware}):
            self.assertFalse(ask_continue(Window(), "digit_span", "pretest",
                                          "dual_nback", "training"))
            self.assertTrue(ask_continue(Window(), "digit_span", "pretest",
                                         "dual_nback", "training"))


if __name__ == "__main__":
    unittest.main()
