"""3초 창, 경계 시각, 즉시 피드백 및 반응과 무관한 시행 일정을 검증한다."""

import unittest
from types import SimpleNamespace
from utils.sequence import Trial
from utils.nback_response import record_response, trial_outcomes, current_feedback
from tasks.dual_nback import run_block

KEYS = {"a": "visual", "l": "auditory"}


def records():
    return [dict(onset=0.0, responses=[]), dict(onset=3.0, responses=[])]


class ResponseTests(unittest.TestCase):
    def test_match_only_and_no_response_outcomes(self):
        trial = Trial(0, 0, "B", True, False, False)
        row = records()[0]
        self.assertEqual(trial_outcomes(trial, row, KEYS)["visual"]["outcome"], "miss")
        self.assertEqual(
            trial_outcomes(trial, row, KEYS)["auditory"]["outcome"], "correct_rejection"
        )
        data = records()
        record_response(data, "a", 2.7, KEYS, 3)
        record_response(data, "l", 2.8, KEYS, 3)
        self.assertEqual(
            trial_outcomes(trial, data[0], KEYS)["visual"]["outcome"], "hit"
        )
        self.assertEqual(
            trial_outcomes(trial, data[0], KEYS)["auditory"]["outcome"], "false_alarm"
        )

    def test_delayed_poll_keeps_previous_trial_response(self):
        data = records()
        self.assertEqual(record_response(data, "a", 2.999, KEYS, 3)[0], 0)
        self.assertEqual(record_response(data, "l", 3.0, KEYS, 3)[0], 1)
        self.assertEqual(data[0]["responses"][0]["rt"], 2.999)

    def test_deadline_is_exclusive_and_no_answer_leak(self):
        data = records()[:1]
        self.assertIsNone(record_response(data, "a", 3.0, KEYS, 3))
        self.assertIsNone(record_response(data, "a", -0.01, KEYS, 3))
        trial = Trial(0, 0, "B", True, True, False)
        self.assertEqual(current_feedback(trial, data[0], KEYS), {})
        record_response(data, "a", 2.7, KEYS, 3)
        self.assertEqual(
            current_feedback(trial, data[0], KEYS), {"visual": "Correct"}
        )

    def test_repeat_does_not_change_first_rt(self):
        data = records()
        trial = Trial(0, 0, "B", True, True, False)
        self.assertTrue(record_response(data, "a", 0.6, KEYS, 3)[2])
        self.assertFalse(record_response(data, "a", 2.7, KEYS, 3)[2])
        self.assertEqual(trial_outcomes(trial, data[0], KEYS)["visual"]["rt"], 0.6)


class FakeWindow:
    def __init__(self):
        self.now = 0.0
        self.callbacks = []
        self.frameIntervals = []
        self.recordFrameIntervals = False

    def getFutureFlipTime(self, **kwargs):
        return self.now + 1 / 60

    def callOnFlip(self, func):
        self.callbacks.append(func)

    def flip(self):
        self.now += 1 / 60
        callbacks, self.callbacks = self.callbacks, []
        for func in callbacks:
            func()
        if self.recordFrameIntervals:
            self.frameIntervals.append(1 / 60)
        return self.now


class FakeKeyboard:
    def __init__(self, win, events):
        self.win = win
        self.events = list(events)
        self.zero = 0.0
        self.armed = False
        self.clock = SimpleNamespace(reset=self.reset)

    def reset(self):
        self.zero = self.win.now
        self.armed = True

    def clearEvents(self):
        pass

    def getKeys(self, **kwargs):
        if not self.armed:
            return []
        result = []
        while self.events and self.events[0][1] <= self.win.now - self.zero + 1e-9:
            key, rt = self.events.pop(0)
            result.append(SimpleNamespace(name=key, rt=rt))
        return result


class FakeAudio:
    def __init__(self):
        self.scheduled = {}

    def prepare_block(self, letters):
        self.letters = letters

    def schedule(self, index, when):
        self.scheduled[index] = when

    def status(self, index):
        return {"StartTime": self.scheduled[index]}

    def stop(self):
        pass


class FakeFeedback:
    def __init__(self, win):
        self.win = win
        self.frames = []

    def draw(self, header, current):
        self.frames.append((self.win.now, dict(current)))


class TimingTests(unittest.TestCase):
    def execute(self, events):
        win = FakeWindow()
        kb = FakeKeyboard(win, events)
        audio = FakeAudio()
        feedback = FakeFeedback(win)
        logger = SimpleNamespace(write=lambda *a, **k: None)
        trials = [
            Trial(0, 0, "B", True, False, False),
            Trial(1, 1, "F", False, True, False),
        ]
        data, errors = run_block(
            win, kb, SimpleNamespace(draw=lambda *a: None), feedback,
            audio, trials, 0, 1, logger, 1 / 60,
        )
        return data, errors, feedback, audio, kb.zero

    def test_27_second_key_feedback_does_not_move_next_onset(self):
        baseline = self.execute([])[0]
        data, errors, feedback, audio, zero = self.execute([("a", 2.7)])
        self.assertAlmostEqual(data[0]["offset"], 0.5)
        self.assertAlmostEqual(data[1]["onset"], 3.0)
        self.assertEqual([r["onset"] for r in data], [r["onset"] for r in baseline])
        self.assertEqual(errors, {"visual": 0, "auditory": 1})
        shown = data[0]["feedback_events"][0]["display_onset"]
        self.assertGreaterEqual(shown, 2.7)
        self.assertLess(shown, 2.74)
        self.assertTrue(
            any(row[1].get("visual") == "Correct" for row in feedback.frames)
        )
        self.assertFalse(any(row[1].get("auditory") for row in feedback.frames))
        for i in range(2):
            self.assertAlmostEqual(audio.scheduled[i] - zero, data[i]["onset"])

    def test_both_keys_have_independent_feedback(self):
        data, _, feedback, _, _ = self.execute([("a", 2.7), ("l", 2.7)])
        self.assertEqual(
            [e["outcome"] for e in data[0]["feedback_events"]], ["hit", "false_alarm"]
        )
        self.assertTrue(
            any("Incorrect" in row[1].get("auditory", "") for row in feedback.frames)
        )

    def test_no_response_is_never_shown_but_is_scored(self):
        data, errors, feedback, _, _ = self.execute([])
        self.assertTrue(all(not row[1] for row in feedback.frames))
        self.assertEqual(errors, {"visual": 1, "auditory": 1})
        self.assertEqual(trial_outcomes(
            Trial(0, 0, "B", True, False, False), data[0], KEYS)["visual"]["outcome"],
            "miss")
        self.assertEqual(trial_outcomes(
            Trial(0, 0, "B", True, False, False), data[0], KEYS)["auditory"]["outcome"],
            "correct_rejection")

    def test_near_deadline_response_remains_valid_without_omission_feedback(self):
        data, errors, feedback, _, _ = self.execute([("a", 2.99)])
        self.assertAlmostEqual(data[0]["responses"][0]["rt"], 2.99)
        self.assertEqual(errors["visual"], 0)
        self.assertEqual(data[0]["feedback_events"][0]["outcome"], "hit")
        self.assertTrue(all(not row[1] for row in feedback.frames))
        self.assertFalse(any(row[1].get("auditory") for row in feedback.frames))



if __name__ == "__main__":
    unittest.main()
