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
    size = (2000, 1600)
    useRetina = True
    color = "black"

    def __init__(self, **kwargs):
        pass

    def close(self):
        pass


class MainEmailTests(unittest.TestCase):
    def test_gui_email_becomes_participant_in_csv(self):
        seen = []

        def dialog(info, title):
            seen.append((title, info["email"]))
            info.update(email="  Student01@HANYANG.AC.KR  ",
                        task="dual_nback", phase="training", mode="forward")
            return SimpleNamespace(OK=True)

        psychopy = SimpleNamespace(prefs=SimpleNamespace(hardware={}),
                                    gui=SimpleNamespace(DlgFromDict=dialog),
                                    visual=SimpleNamespace(Window=FakeWindow), __version__="test")
        task = SimpleNamespace(run=lambda win, logger, seed: logger.write("trial", **trial()))
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(sys.modules, {"psychopy": psychopy}), \
             patch.object(main, "DATA_DIR", Path(directory)), \
             patch.object(main.importlib, "import_module", return_value=task), \
             patch.object(sys, "argv", ["main.py"]):
            main.main()
            self.assertEqual(seen[0][0], "Hanyang participant sign-in")
            paths = list(Path(directory).iterdir())
            self.assertEqual(len(paths), 1)
            with paths[0].open(encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["participant"], "student01@hanyang.ac.kr")
            self.assertEqual(row["session_status"], "completed")


if __name__ == "__main__":
    unittest.main()
