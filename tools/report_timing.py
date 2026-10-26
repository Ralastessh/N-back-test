"""JSONL 파일에서 소프트웨어 flip 기록을 요약한다. 물리적 AV onset 검사가 아니다."""

import argparse
import json
from pathlib import Path
from statistics import mean

parser = argparse.ArgumentParser()
parser.add_argument("log", type=Path)
args = parser.parse_args()
rows = [json.loads(line) for line in args.log.read_text(encoding="utf-8").splitlines()]
trials = [r for r in rows if r["kind"] == "trial" and r.get("complete")]
blocks = sorted({r["block"] for r in trials})
for block in blocks:
    group = [r for r in trials if r["block"] == block]
    durations = [r["offset"] - r["onset"] for r in group if r["offset"] is not None]
    intervals = [b["onset"] - a["onset"] for a, b in zip(group, group[1:])]
    print("block", block, "completed trials", len(group))
    for name, values in [("visual_s", durations), ("onset_interval_s", intervals)]:
        if values:
            print(name, dict(min=min(values), mean=mean(values), max=max(values)))
    frame = next(
        (r for r in rows if r["kind"] == "frame_intervals" and r["block"] == block),
        None,
    )
    if frame:
        print("delayed_frames", frame["delayed_frames"])
