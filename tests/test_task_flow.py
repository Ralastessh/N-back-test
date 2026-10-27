"""모의 화면/키보드로 중단 규칙·전체 세트 수 검증. 하드웨어 타이밍 검사가 아님."""

import random
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from config import DIGIT_SPAN, READING_SPAN, ROOT
from tasks import reading_span
from tasks import digit_span
from utils.span_protocol import digit_plans, expected_recall, load_reading_materials


class Log:
    phase = "pretest"

    def __init__(self):
        self.rows = []

    def write(self, kind, **row):
        self.rows.append(dict(kind=kind, **row))


class Clock:
    def getTime(self):
        return 0

    def reset(self):
        pass


class Window:
    def callOnFlip(self, *args):
        pass


class Sound:
    def __init__(self, *args, **kwargs):
        pass

    def getDuration(self):
        return 0.5

    def play(self, **kwargs):
        pass

    def stop(self):
        pass


class TaskFlowTests(unittest.TestCase):
    def modules(self, kb):
        return {
            "psychopy": SimpleNamespace(
                core=SimpleNamespace(Clock=Clock), sound=SimpleNamespace(Sound=Sound)
            ),
            "psychopy.hardware": SimpleNamespace(
                keyboard=SimpleNamespace(Keyboard=lambda: kb)
            ),
            "psychtoolbox": SimpleNamespace(GetSecs=lambda: 100),
        }

    def test_reading_formal_mode_still_blocks_unreviewed_materials(self):
        with patch.dict(READING_SPAN, {"allow_draft_materials": False}), \
             patch.dict(sys.modules, self.modules(object())):
            with self.assertRaisesRegex(ValueError, "Unreviewed item"):
                reading_span.run(Window(), Log(), 42)

    def test_digit_stops_after_two_failures_at_same_length(self):
        for mode in ("forward", "backward"):
            log = Log()
            with patch.dict(sys.modules, self.modules(None)), patch.object(
                digit_span, "pause"
            ), patch.object(digit_span, "show"), patch.object(
                digit_span, "wait_until"
            ), patch.object(
                digit_span, "recall_digits", return_value=([], 1.0, [])
            ):
                digit_span.run(Window(), log, 42, mode)
            test = [
                r
                for r in log.rows
                if r["kind"] == "digit_trial" and r["stage"] == "test"
            ]
            practice = [
                r
                for r in log.rows
                if r["kind"] == "digit_trial" and r["stage"] == "practice"
            ]
            self.assertEqual(len(test), 2)
            self.assertEqual(len(practice), 2)
            self.assertEqual(test[0]["length"], 3 if mode == "forward" else 2)
            self.assertEqual(
                len([r for r in log.rows if r["kind"] == "digit_discontinue"]), 1
            )

    def test_digit_all_correct_reaches_last_span(self):
        for mode in ("forward", "backward"):
            log = Log()
            plans = digit_plans(42, DIGIT_SPAN)
            responses = [
                (expected_recall(seq, mode), 0.5, [])
                for stage in ("practice", "test")
                for seq in plans[("pretest", mode, stage)]
            ]
            with patch.dict(sys.modules, self.modules(None)), patch.object(
                digit_span, "pause"
            ), patch.object(digit_span, "show"), patch.object(
                digit_span, "wait_until"
            ), patch.object(
                digit_span, "recall_digits", side_effect=responses
            ):
                digit_span.run(Window(), log, 42, mode)
            summary = [
                r
                for r in log.rows
                if r["kind"] == "digit_summary" and r["stage"] == "test"
            ][0]
            self.assertEqual(summary["maximum_span"], 9 if mode == "forward" else 8)
            self.assertEqual(summary["total_correct"], 14)

    def test_reading_timeouts_do_not_stop_sets(self):
        material = load_reading_materials(
            ROOT / READING_SPAN["sentence_file"],
            READING_SPAN,
            ROOT / READING_SPAN["review_file"],
            False,
        )
        answers = [r["truth"] for group in material["P"].values() for r in group]

        class Keyboard:
            clock = Clock()

            def clearEvents(self):
                pass

            def waitKeys(self, **kwargs):
                if answers:
                    return [
                        SimpleNamespace(name="y" if answers.pop(0) else "n", rt=0.5)
                    ]
                return None

        log = Log()
        with patch.dict(sys.modules, self.modules(Keyboard())), patch.object(
            reading_span, "pause"
        ), patch.object(
            reading_span, "show"
        ), patch.object(
            reading_span, "recall_words", return_value=([], 0.5)
        ):
            reading_span.run(Window(), log, 42)
        judgments = [
            r
            for r in log.rows
            if r["kind"] == "sentence_judgment" and r["stage"] == "test"
        ]
        recalls = [
            r
            for r in log.rows
            if r["kind"] == "reading_recall" and r["stage"] == "test"
        ]
        self.assertEqual(len(judgments), 42)
        self.assertEqual(len(recalls), 12)
        self.assertTrue(all(r["material_status"] == "draft" for r in judgments + recalls))
        self.assertTrue(all(r["timed_out"] for r in judgments))
        summary = [
            r
            for r in log.rows
            if r["kind"] == "reading_summary" and r["stage"] == "test"
        ][0]
        self.assertEqual(summary["processing_accuracy"], 0)
        self.assertTrue(summary["processing_below_threshold"])
        order = [r for r in log.rows if r["kind"] == "reading_order"][0]["set_order"]
        self.assertNotEqual(order, list(material["A"]))


if __name__ == "__main__":
    unittest.main()
