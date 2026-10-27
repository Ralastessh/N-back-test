"""입력창에서 받은 학교 이메일이 실행 CSV의 참가자 열까지 전달되는지 검증한다."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import main
from tests.test_data_logging import trial


class FakeWindow:
    fullscr = False
    winType = "pyglet"
    size = (2000, 1600)
    useRetina = True
    color = "black"
    last_kwargs = None

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs

    def close(self):
        pass


class MainEmailTests(unittest.TestCase):
    def test_pretest_training_posttest_chain_uses_same_participant(self):
        calls = []
        psychopy = SimpleNamespace(prefs=SimpleNamespace(hardware={}), gui=SimpleNamespace(),
                                    visual=SimpleNamespace(Window=FakeWindow), __version__="test")

        def task_module(name):
            return SimpleNamespace(run=lambda win, logger, seed, **kwargs:
                                   calls.append((name, logger.phase, logger.common["participant"])))

        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(sys.modules, {"psychopy": psychopy}), \
             patch.object(main, "DATA_DIR", Path(directory)), \
             patch.object(main.importlib, "import_module", side_effect=task_module), \
             patch.object(main, "enable_native_fullscreen", return_value=True), \
             patch.object(main, "ask_continue", side_effect=[True, True]) as ask, \
             patch.object(main, "choose_posttest_task") as choose, \
             patch.object(sys, "argv", ["main.py", "--email", "student01@hanyang.ac.kr",
                                       "--task", "reading_span", "--phase", "pretest"]):
            main.main()
            self.assertEqual(len(list(Path(directory).glob("*_responses.csv"))), 3)
        self.assertEqual([row[:2] for row in calls], [
            ("tasks.reading_span", "pretest"),
            ("tasks.dual_nback", "training"),
            ("tasks.reading_span", "posttest"),
        ])
        self.assertEqual({row[2] for row in calls}, {"student01@hanyang.ac.kr"})
        self.assertEqual(ask.call_count, 2)
        choose.assert_not_called()

    def test_training_alone_lets_participant_choose_posttest_task(self):
        calls = []
        psychopy = SimpleNamespace(prefs=SimpleNamespace(hardware={}), gui=SimpleNamespace(),
                                    visual=SimpleNamespace(Window=FakeWindow), __version__="test")

        def task_module(name):
            return SimpleNamespace(run=lambda win, logger, seed, **kwargs:
                                   calls.append((name, logger.phase)))

        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(sys.modules, {"psychopy": psychopy}), \
             patch.object(main, "DATA_DIR", Path(directory)), \
             patch.object(main.importlib, "import_module", side_effect=task_module), \
             patch.object(main, "enable_native_fullscreen", return_value=True), \
             patch.object(main, "ask_continue", return_value=True), \
             patch.object(main, "choose_posttest_task", return_value="digit_span"), \
             patch.object(sys, "argv", ["main.py", "--email", "student01@hanyang.ac.kr",
                                       "--task", "dual_nback", "--phase", "training"]):
            main.main()
            self.assertEqual(len(list(Path(directory).glob("*_responses.csv"))), 2)
        self.assertEqual(calls, [("tasks.dual_nback", "training"),
                                 ("tasks.digit_span", "posttest")])

    def test_invalid_task_phase_warns_and_reopens_selection(self):
        warnings, selections, selected_modes = [], [], []

        def dialog(info, title):
            selections.append((list(info["task"]), list(info["phase"])))
            info.update(email="student01@hanyang.ac.kr", task="digit_span",
                        phase="training" if len(selections) == 1 else "pretest")
            return SimpleNamespace(OK=True)

        class WarningDialog:
            def __init__(self, title):
                self.title = title

            def addText(self, message):
                warnings.append((self.title, message))

            def show(self):
                pass

        psychopy = SimpleNamespace(prefs=SimpleNamespace(hardware={}),
                                    gui=SimpleNamespace(DlgFromDict=dialog, Dlg=WarningDialog),
                                    visual=SimpleNamespace(Window=FakeWindow), __version__="test")
        task = SimpleNamespace(run=lambda win, logger, seed, mode: selected_modes.append(mode))
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(sys.modules, {"psychopy": psychopy}), \
             patch.object(main, "DATA_DIR", Path(directory)), \
             patch.object(main.importlib, "import_module", return_value=task), \
             patch.object(main, "enable_native_fullscreen", return_value=True), \
             patch.object(main, "ask_continue", return_value=False), \
             patch.object(sys, "argv", ["main.py"]):
            main.main()
            self.assertEqual(len(list(Path(directory).iterdir())), 1)
        self.assertEqual(len(selections), 2)
        self.assertIn("pretest", selections[1][1])
        self.assertEqual(warnings[0][0], "Check task and phase")
        self.assertIn("Pretest or Posttest", warnings[0][1])
        self.assertEqual(selected_modes, ["forward"])

    def test_dual_nback_requires_training(self):
        self.assertIsNotNone(main.task_phase_error("dual_nback", "posttest"))
        self.assertIsNone(main.task_phase_error("dual_nback", "training"))

    def test_gui_email_becomes_participant_in_csv(self):
        seen = []

        def dialog(info, title):
            seen.append((title, info["email"], tuple(info)))
            info.update(email="  Student01@HANYANG.AC.KR  ",
                        task="dual_nback", phase="training")
            return SimpleNamespace(OK=True)

        psychopy = SimpleNamespace(prefs=SimpleNamespace(hardware={}),
                                    gui=SimpleNamespace(DlgFromDict=dialog),
                                    visual=SimpleNamespace(Window=FakeWindow), __version__="test")
        task = SimpleNamespace(run=lambda win, logger, seed: logger.write("trial", **trial()))
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(sys.modules, {"psychopy": psychopy}), \
             patch.object(main, "DATA_DIR", Path(directory)), \
             patch.object(main.importlib, "import_module", return_value=task), \
             patch.object(main, "enable_native_fullscreen", return_value=True), \
             patch.object(main, "ask_continue", return_value=False), \
             patch.object(sys, "argv", ["main.py"]):
            main.main()
            self.assertEqual(seen[0][0], "Hanyang participant sign-in")
            self.assertNotIn("fullscreen", seen[0][2])
            self.assertNotIn("mode", seen[0][2])
            self.assertEqual(FakeWindow.last_kwargs["infoMsg"], "Waiting...")
            paths = list(Path(directory).iterdir())
            self.assertEqual(len(paths), 1)
            with paths[0].open(encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["participant"], "student01@hanyang.ac.kr")
            self.assertEqual(row["session_status"], "completed")

    def test_digit_span_dialog_has_no_direction_choice_and_runs_forward(self):
        shown, chosen = [], []

        def dialog(info, title):
            shown.append(tuple(info))
            info.update(email="student01@hanyang.ac.kr", task="digit_span", phase="pretest")
            return SimpleNamespace(OK=True)

        psychopy = SimpleNamespace(prefs=SimpleNamespace(hardware={}),
                                    gui=SimpleNamespace(DlgFromDict=dialog),
                                    visual=SimpleNamespace(Window=FakeWindow), __version__="test")
        task = SimpleNamespace(run=lambda win, logger, seed, mode: chosen.append(mode))
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(sys.modules, {"psychopy": psychopy}), \
             patch.object(main, "DATA_DIR", Path(directory)), \
             patch.object(main.importlib, "import_module", return_value=task), \
             patch.object(main, "enable_native_fullscreen", return_value=True), \
             patch.object(main, "ask_continue", return_value=False), \
             patch.object(sys, "argv", ["main.py"]):
            main.main()
        self.assertNotIn("mode", shown[0])
        self.assertEqual(chosen, ["forward"])


if __name__ == "__main__":
    unittest.main()
