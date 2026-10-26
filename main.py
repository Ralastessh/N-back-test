"""Coder에서 이 파일을 실행. 터미널에서는 --task로 과제 선택."""

import argparse
import importlib
import platform
import secrets
import hashlib
import sys
from config import (
    ROOT,
    PROTOCOL_VERSION,
    DATA_DIR,
    DISPLAY,
    NBACK,
    ASSUMPTIONS,
    AUDIO_DIR,
    AUDIO_GENERATION,
    AUDIO_PLAYBACK,
    NBACK_FEEDBACK,
    DIGIT_SPAN,
    READING_SPAN,
    require_decisions,
)
from utils.data_logger import DataLogger


def main(default_task=None):
    parser = argparse.ArgumentParser(description="Jaeggi 2008 PsychoPy replication")
    parser.add_argument(
        "--task",
        choices=["dual_nback", "digit_span", "reading_span"],
        default=default_task,
    )
    parser.add_argument("--participant")
    parser.add_argument("--phase", choices=["training", "pretest", "posttest"])
    parser.add_argument("--mode", choices=["forward", "backward"], default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    # sound 모듈을 불러오기 전에 PTB를 선택한다.
    from psychopy import prefs

    prefs.hardware["audioLib"] = ["ptb", "PTB"]
    from psychopy import gui, visual, __version__

    info = dict(
        participant=args.participant or "P001",
        task=[args.task] if args.task else ["dual_nback", "digit_span", "reading_span"],
        phase=[args.phase] if args.phase else ["training", "pretest", "posttest"],
        mode=[args.mode] if args.mode else ["forward", "backward"],
    )
    if not args.participant or not args.task or not args.phase:
        if not gui.DlgFromDict(info, title="Jaeggi 2008").OK:
            return
    task = args.task or info["task"]
    phase = args.phase or info["phase"]
    if task != "dual_nback" and phase == "training":
        raise ValueError("Choose pretest or posttest for a span task.")
    settings = {
        "dual_nback": ASSUMPTIONS,
        "digit_span": DIGIT_SPAN,
        "reading_span": READING_SPAN,
    }[task]
    require_decisions(settings, task)
    info["participant"] = info["participant"].strip()
    if not info["participant"]:
        raise ValueError("Enter a participant ID.")
    # 동일 참가자 Pre/Post는 동일 기반 seed에서 겹치지 않는 두 form을 생성한다.
    participant_seed = int.from_bytes(
        hashlib.sha256(info["participant"].strip().encode()).digest()[:8], "big"
    )
    seed = (
        args.seed
        if args.seed is not None
        else (participant_seed if task != "dual_nback" else secrets.randbits(32))
    )
    if isinstance(info["mode"], list):
        info["mode"] = args.mode or "forward"
    logger = DataLogger(
        DATA_DIR,
        info["participant"],
        task,
        phase,
        dict(
            seed=seed,
            protocol_version=PROTOCOL_VERSION,
            psychopy=__version__,
            python=sys.version,
            platform=platform.platform(),
            paper=NBACK,
            assumptions=ASSUMPTIONS,
            audio_generation=AUDIO_GENERATION,
            audio_playback=AUDIO_PLAYBACK,
            nback_feedback=NBACK_FEEDBACK,
            stimulus_hashes={
                str(path.relative_to(ROOT)): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in list(AUDIO_DIR.rglob("*.wav"))
                + [ROOT / READING_SPAN["sentence_file"]]
                if path.is_file()
            },
            display=DISPLAY,
            digit_span=DIGIT_SPAN,
            reading_span=READING_SPAN,
            mode=info["mode"],
        ),
    )
    win = None
    try:
        win = visual.Window(
            **{k: DISPLAY[k] for k in ("size", "fullscr", "units", "color")},
            allowGUI=True,
        )
        module = importlib.import_module("tasks." + task)
        kwargs = dict(mode=info["mode"]) if task == "digit_span" else {}
        module.run(win, logger, seed, **kwargs)
        logger.write("session_end", status="completed")
    except KeyboardInterrupt:
        logger.write("session_end", status="aborted")
    except Exception as error:
        logger.write("session_end", status="error", error=repr(error))
        raise
    finally:
        if win is not None:
            win.close()
        logger.close()
        print(f"Data saved: {logger.path}")


if __name__ == "__main__":
    main()
