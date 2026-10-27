"""학교 이메일 입력과 참가자 ID 일치 여부."""
import csv
import tempfile
import unittest
from utils.participant import normalize_hanyang_email
from utils.data_logger import DataLogger
from tests.test_data_logging import trial


class HanyangEmailTests(unittest.TestCase):
    def test_normalizes_email_and_uses_it_in_participant_column(self):
        email = normalize_hanyang_email("  Student.01@HANYANG.AC.KR  ")
        self.assertEqual(email, "student.01@hanyang.ac.kr")
        with tempfile.TemporaryDirectory() as directory:
            log = DataLogger(directory, email, "dual_nback", "training", {})
            log.write("trial", **trial())
            log.close()
            with log.path.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(next(csv.DictReader(handle))["participant"], email)
            self.assertNotIn("student.01", log.path.name)

    def test_rejects_missing_and_other_domains(self):
        for value in ("", "P001", "student@gmail.com", "student@hyu.ac.kr",
                      "@hanyang.ac.kr", "student@hanyang.ac.kr.evil", "bad..id@hanyang.ac.kr",
                      "=cmd@hanyang.ac.kr", "a" * 65 + "@hanyang.ac.kr"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_hanyang_email(value)


if __name__ == "__main__":
    unittest.main()
