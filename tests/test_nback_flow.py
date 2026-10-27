"""소리 확인 건너뛰기와 실제 시간 기반 자동 휴식의 동작 검증."""
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from stimuli.auditory import AuditoryStimuli
from stimuli.nback_ui import ParticipantScreens


class FlowTests(unittest.TestCase):
    def test_audio_space_stops_remaining_letters_without_confirming(self):
        self.audio_exit("space")

    def test_audio_escape_stops_playback(self):
        self.audio_exit("escape")

    def audio_exit(self, key):
        audio = object.__new__(AuditoryStimuli)
        audio.settings = dict(check_before_session=True)
        audio.speaker = SimpleNamespace(name="test speaker")
        audio.consonants = tuple("BFHJMQRW")
        scheduled, stops, rows = [], [], []
        audio.prepare_block = lambda letters: None
        audio.schedule = lambda index, when: scheduled.append(index)
        audio.stop = lambda: stops.append(True)
        keyboard = SimpleNamespace(clearEvents=lambda: None,
            getKeys=lambda **kwargs: [SimpleNamespace(name=key)])
        win = SimpleNamespace(getFutureFlipTime=lambda **kwargs: 1)
        psychopy = SimpleNamespace(core=SimpleNamespace(
            Clock=lambda: SimpleNamespace(getTime=lambda: 0)), gui=None)
        with patch.dict(sys.modules, {"psychopy": psychopy}):
            if key == "escape":
                with self.assertRaises(KeyboardInterrupt):
                    audio.check(win, keyboard, SimpleNamespace(write=lambda *a, **kw: rows.append(kw)), screens=object())
            else:
                audio.check(win, keyboard, SimpleNamespace(write=lambda *a, **kw: rows.append(kw)), screens=object())
                self.assertTrue(rows[0]["skipped"])
                self.assertFalse(rows[0]["confirmed"])
                self.assertEqual(rows[0]["reason"], "participant_space")
        self.assertEqual(scheduled, [0])
        self.assertEqual(len(stops), 1)

    def test_rest_waits_ten_seconds_despite_space_and_remains_abortable(self):
        for abort in (False, True):
            now, callbacks, shown, polls = [0.0], [], [], []
            clock = SimpleNamespace(getTime=lambda: now[0], reset=lambda: now.__setitem__(0, 0.0))

            def flip():
                now[0] += .25
                pending = list(callbacks)
                callbacks.clear()
                for callback in pending:
                    callback()

            def keys(**kwargs):
                polls.append(kwargs["keyList"])
                return [SimpleNamespace(name="escape")] if abort else []

            screens = object.__new__(ParticipantScreens)
            screens.win = SimpleNamespace(callOnFlip=lambda f: callbacks.append(f), flip=flip)
            screens.draw_summary = lambda *args, **kwargs: shown.append(args[-1])
            kb = SimpleNamespace(clearEvents=lambda: None, getKeys=keys)
            psychopy = SimpleNamespace(core=SimpleNamespace(Clock=lambda: clock))
            with patch.dict(sys.modules, {"psychopy": psychopy}):
                if abort:
                    with self.assertRaises(KeyboardInterrupt):
                        screens.inter_block_rest(kb, 1, 2, 3, {})
                else:
                    elapsed = screens.inter_block_rest(kb, 1, 2, 3, {})
                    self.assertEqual(elapsed, 10.0)
                    self.assertEqual(set(shown), set(range(1, 11)))
            # SPACE는 휴식을 줄이는 키 목록에 포함하지 않는다.
            self.assertTrue(all(keys == ["escape"] for keys in polls))


if __name__ == "__main__":
    unittest.main()
