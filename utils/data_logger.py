"""참가자의 시행별 자극·반응만 세션당 CSV 하나에 저장한다."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv
import json
import uuid

# 시스템·장치·백엔드 설정은 포함하지 않는다.
KST = timezone(timedelta(hours=9), "KST")
COMMON = ["session_id", "participant", "task", "phase", "stage", "session_status", "recorded_kst", "event_type"]
NBACK_COLUMNS = [
    "block", "n", "trial_number", "warmup", "scored", "complete",
    "visual_position", "visual_x", "visual_y", "auditory_letter",
    "visual_target", "auditory_target", "visual_key", "auditory_key", "response_window_s",
    "onset_s", "offset_s", "visual_responded", "auditory_responded",
    "visual_rt_s", "auditory_rt_s", "visual_correct", "auditory_correct",
    "visual_outcome", "auditory_outcome", "response_keys", "response_rts_s", "response_first_flags",
    "block_scored_trials", "block_visual_correct", "block_visual_incorrect", "block_visual_accuracy_pct",
    "block_auditory_correct", "block_auditory_incorrect", "block_auditory_accuracy_pct", "next_n",
]
SPAN_COLUMNS = [
    "trial_number", "mode", "length", "form", "attempt", "set_id", "item_id",
    "stimuli", "sentence", "recall_word", "expected", "response", "rt_s",
    "correct", "timed_out", "timeout_s", "items_correct", "items_total", "accuracy", "exact",
    "key_events",
]


class DataLogger:
    def __init__(self, directory, participant, task, phase, metadata):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.stem = f"{task}_{datetime.now(KST):%Y-%m-%d_%H-%M-%S}_{uuid.uuid4().hex[:8]}"
        self.path = directory / f"{self.stem}_responses.csv"
        self.phase = phase
        self.task = task
        self.common = dict(session_id=self.stem, participant=participant, task=task, phase=phase)
        self.names = COMMON + (
            NBACK_COLUMNS if task == "dual_nback" else
            SPAN_COLUMNS + (["material_status"] if task == "reading_span" else [])
        )
        self.file = self.path.open("x+", encoding="utf-8-sig", newline="")
        self.rows = []
        self.pending = {}
        self.status = "running"
        self.closed = False
        # 채점에 필요한 행동 조건만 사용하며 전체 metadata는 기록하지 않는다.
        from config import NBACK, ASSUMPTIONS
        settings = metadata.get("paper", NBACK)
        assumptions = metadata.get("assumptions", ASSUMPTIONS)
        self.behavior = dict(visual_key=settings["visual_key"], auditory_key=settings["auditory_key"],
                             response_window_s=assumptions["response_window_s"])
        self._rewrite()

    def _rewrite(self):
        self.file.seek(0)
        self.file.truncate()
        writer = csv.DictWriter(self.file, fieldnames=self.names)
        writer.writeheader()
        writer.writerows(self.rows)
        self.file.flush()

    def _append(self, event_type, fields):
        row = dict(self.common, session_status=self.status,
                   recorded_kst=datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
                   event_type=event_type, **fields)
        row = {key: (json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list, tuple)) else value)
               for key, value in row.items() if key in self.names}
        self.rows.append(row)
        csv.DictWriter(self.file, fieldnames=self.names).writerow(row)
        self.file.flush()

    def write(self, kind, **fields):
        if self.closed:
            raise ValueError("Logger is closed.")
        if kind == "trial" and self.task == "dual_nback":
            self._nback_trial(fields)
        elif kind == "block_summary" and self.task == "dual_nback":
            # 별도 요약 행/파일 없이 해당 블록의 시행 행들에 정확도를 붙인다.
            for row in self.rows:
                if row.get("block") != fields["block"]:
                    continue
                row["next_n"] = fields.get("next_n", "")
                for modality, stats in fields.get("statistics", {}).items():
                    row["block_scored_trials"] = stats["total"]
                    row[f"block_{modality}_correct"] = stats["correct"]
                    row[f"block_{modality}_incorrect"] = stats["incorrect"]
                    row[f"block_{modality}_accuracy_pct"] = stats["accuracy"] * 100
            self._rewrite()
        elif kind in {"digit_trial_start", "sentence_start"} and self.task != "dual_nback":
            self.pending[self._span_id(fields)] = (kind, dict(fields))
        elif kind in {"digit_trial", "sentence_judgment", "reading_recall"} and self.task != "dual_nback":
            self.pending.pop(self._span_id(fields), None)
            self._span_row(kind, fields)
        elif kind == "session_end":
            self._finish(fields.get("status", "unknown"))
        # session/settings/frame/audio/summary 등 비반응 이벤트는 저장하지 않는다.

    def _nback_trial(self, fields):
        from stimuli.visual import POSITIONS
        from config import DISPLAY
        x, y = POSITIONS[fields["visual"]]
        responses = fields.get("responses", [])
        complete = fields["complete"]
        row = dict(stage=fields.get("stage", "test"), block=fields["block"], n=fields["n"],
                   trial_number=fields["index"] + 1, warmup=fields["warmup"], scored=fields["scored"],
                   complete=complete, visual_position=fields["visual"], visual_x=x * DISPLAY["spacing"],
                   visual_y=y * DISPLAY["spacing"], auditory_letter=fields["auditory"],
                   visual_target=fields["visual_target"], auditory_target=fields["auditory_target"],
                   onset_s=fields["onset"], offset_s=fields["offset"], **self.behavior,
                   response_keys=";".join(r["key"] for r in responses),
                   response_rts_s=";".join(str(r["rt"]) for r in responses),
                   response_first_flags=";".join(str(int(r["first_for_modality"])) for r in responses))
        for modality, outcome in fields["outcomes"].items():
            row[f"{modality}_rt_s"] = outcome["rt"]
            row[f"{modality}_responded"] = outcome["rt"] is not None
            row[f"{modality}_correct"] = outcome["correct"] if complete else None
            row[f"{modality}_outcome"] = outcome["outcome"] if complete else None
        self._append("nback_trial", row)

    @staticmethod
    def _span_id(fields):
        return (fields.get("stage"), fields.get("attempt"), fields.get("mode"),
                fields.get("trial_index"), fields.get("set_id"), fields.get("item_id"))

    def _span_row(self, kind, fields):
        row = dict(fields)
        if "trial_index" in row:
            row["trial_number"] = row.pop("trial_index") + 1
        if "rt" in row:
            row["rt_s"] = row.pop("rt")
        self._append(kind, row)

    def _finish(self, status):
        # 중단된 Span 자극도 응답이 완료된 시행과 구분해 남긴다.
        for kind, fields in self.pending.values():
            self._span_row(kind + "_incomplete", fields)
        self.pending.clear()
        self.status = status
        for row in self.rows:
            row["session_status"] = status
        self._rewrite()

    def close(self):
        if self.closed:
            return
        if self.status == "running":
            self._finish("closed_without_status")
        self.file.close()
        self.closed = True
