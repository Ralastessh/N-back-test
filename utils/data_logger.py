"""JSONL 원자료 + 이벤트 종류별 CSV. UTF-8 BOM, 매 행 flush, 기존 파일 덮어쓰기 방지."""

from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import uuid


def flatten(mapping, prefix=""):
    result = {}
    for key, value in mapping.items():
        name = f"{prefix}_{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten(value, name))
        elif isinstance(value, (list, tuple)):
            result[name] = json.dumps(value, ensure_ascii=False)
        else:
            result[name] = value
    return result


class DataLogger:
    def __init__(self, directory, participant, task, phase, metadata):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.stem = (
            f"{task}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}_{uuid.uuid4().hex[:8]}"
        )
        self.path = directory / (self.stem + ".jsonl")
        self.phase = phase
        self.common = dict(participant=participant, task=task, phase=phase)
        self.file = self.path.open("x", encoding="utf-8")
        self.csv_files = {}
        self.write("session", metadata=metadata)

    def write(self, kind, **fields):
        record = dict(
            self.common, kind=kind, utc=datetime.now(timezone.utc).isoformat(), **fields
        )
        self.file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        self.file.flush()
        row = flatten(record)
        if kind not in self.csv_files:
            path = self.path.parent / f"{self.stem}_{kind}.csv"
            handle = path.open("x", encoding="utf-8-sig", newline="")
            names = list(row) + ["extra_json"]
            writer = csv.DictWriter(handle, fieldnames=names)
            writer.writeheader()
            self.csv_files[kind] = (handle, writer, names)
        handle, writer, names = self.csv_files[kind]
        extra = {k: v for k, v in row.items() if k not in names}
        row = {k: v for k, v in row.items() if k in names}
        row["extra_json"] = (
            json.dumps(extra, ensure_ascii=False, default=str) if extra else ""
        )
        writer.writerow(row)
        handle.flush()

    def close(self):
        self.file.close()
        for handle, _, _ in self.csv_files.values():
            handle.close()
