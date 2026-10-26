"""참가자 화면·오류 메시지와 활성 Reading Span 자극의 영어 설정 회귀 검사."""

import ast
import csv
import unittest
from pathlib import Path
from config import ROOT, READING_SPAN


class LanguageTests(unittest.TestCase):
    def test_no_korean_runtime_literals(self):
        paths = [ROOT / "main.py", ROOT / "config.py"]
        for folder in ("tasks", "utils", "stimuli"):
            paths.extend((ROOT / folder).glob("*.py"))
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            docstrings = {
                id(node.body[0].value)
                for node in ast.walk(tree)
                if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef))
                and node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
            }
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and id(node) not in docstrings
                ):
                    self.assertFalse(
                        any("\uac00" <= c <= "\ud7a3" for c in node.value),
                        f"{path.name}:{node.lineno}: {node.value}",
                    )

    def test_active_materials_use_english_words(self):
        with (ROOT / READING_SPAN["sentence_file"]).open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 90)
        self.assertTrue(
            all(
                row["sentence"].isascii() and row["recall_word"].isascii()
                for row in rows
            )
        )


if __name__ == "__main__":
    unittest.main()
