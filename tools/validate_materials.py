"""--draft는 구조만 검증. 기본 실행은 문항 검토 승인까지 검증한다. 파일을 수정하지 않는다."""

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import ROOT, READING_SPAN
from utils.span_protocol import load_reading_materials

parser = argparse.ArgumentParser()
parser.add_argument("--draft", action="store_true")
args = parser.parse_args()
path = ROOT / READING_SPAN["sentence_file"]
groups = load_reading_materials(
    path, READING_SPAN, ROOT / READING_SPAN["review_file"], not args.draft
)
for form, sets in groups.items():
    print(form, len(sets), "sets", sum(map(len, sets.values())), "sentences")
print("SHA256:", hashlib.sha256(path.read_bytes()).hexdigest())
print("DRAFT ONLY: review not approved" if args.draft else "Review gate passed")
