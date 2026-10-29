import csv
from pathlib import Path
from config import ROOT, RAPM, BOMAT
from PIL import Image
from psychopy import core, visual
from psychopy.hardware import keyboard
from stimuli.nback_ui import ParticipantScreens

SETTINGS = {"rapm": RAPM, "bomat": BOMAT}

def load_items(test="rapm"):
    settings = SETTINGS[test]
    path = ROOT / settings["item_file"]
    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"No {test.upper()} examples are registered.")
    ids = set()
    for row in rows:
        if not row["item_id"] or row["item_id"] in ids:
            raise ValueError(f"Duplicate or missing {test.upper()} example ID.")
        ids.add(row["item_id"])
        row["answer"] = row["answer"].strip()
        if row["answer"] not in [str(n) for n in range(1, settings["choices"] + 1)]:
            raise ValueError(f"Invalid {test.upper()} answer: " + row["item_id"])
        image = Path(row["image"])
        row["image"] = str(image if image.is_absolute() else path.parent / image)
        if not Path(row["image"]).is_file():
            raise ValueError(f"Missing {test.upper()} example image: " + row["image"])
    return rows


def draw_screen(screens, title, message, detail="", image=None, choices=0):
    theme = screens.theme
    screens.win.color = "#FFFFFF"
    screens.panel("gf_background", (0, 0), (3, 1), "#FFFFFF")
    screens.text("gf_title", title, (0, .435), .040)
    screens.text("gf_message", message, (0, .365), .024, theme["flow_muted"])
    if image is None:
        screens.text("gf_detail", detail, (0, .075), .030, width=1.1)
        screens.panel("gf_begin", (0, -.29), (.50, .075), theme["flow_accent"])
        screens.text("gf_begin_label", "SPACE   Continue", (0, -.29), .025, "white")
    else:
        width, height = image._gf_size
        scale = min(1.12 / width, .59 / height)
        image.size, image.pos = (width * scale, height * scale), (0, .015)
        image.draw()
        screens.text("gf_keys", f"1-{choices}   Answer       SPACE   Skip", (0, -.35), .024)
    screens.text("gf_exit", "ESC   Exit", (0, -.445), .019, theme["flow_muted"])


def run(win, logger, seed):
    settings = SETTINGS[logger.task]
    items = load_items(logger.task)
    kb = keyboard.Keyboard()
    screens = ParticipantScreens(win)
    title, limit, choices = logger.task.upper() + " examples", settings["time_limit_s"], settings["choices"]
    if limit <= 0:
        raise ValueError("Gf time limit must be positive.")
    images = []
    for row in items:
        image = visual.ImageStim(win, image=row["image"], units="height", autoLog=False)
        with Image.open(row["image"]) as source:
            image._gf_size = source.size
        images.append(image)
    screens.wait(kb, draw_screen, screens, title, f"{limit / 60:g} minutes total | Public examples only",
                 f"Illustrative examples, not the standardized test.\nThe same examples appear in Pretest and Posttest.\nChoose the missing pattern using keys 1-{choices}.\n"
                 "SPACE skips an item. You cannot return to previous items.")
    clock = core.Clock()
    score = answered = 0
    expired = False
    try:
        for index, (row, image) in enumerate(zip(items, images)):
            info = dict(stage="test", trial_index=index, form="public_examples",
                        item_id=row["item_id"], stimuli=row["image"],
                        expected=row["answer"], timeout_s=limit)
            if expired or (index > 0 and clock.getTime() >= limit):
                expired = True
                logger.write("gf_trial", **info, response=None, rt=None, correct=False,
                             outcome="not_reached", timed_out=False)
                continue
            remaining = limit if index == 0 else max(0, limit - clock.getTime())
            win._resize_draw = lambda: draw_screen(
                screens, title, f"Item {index + 1} / {len(items)}   |   {remaining:.0f}s remaining",
                image=image, choices=choices)
            win._resize_draw()
            logger.write("gf_trial_start", **info)
            if index == 0:
                win.callOnFlip(clock.reset)
            onset = []
            win.callOnFlip(lambda: onset.append(clock.getTime()))
            win.callOnFlip(kb.clearEvents)
            win.callOnFlip(kb.clock.reset)
            win.flip()
            remaining = max(0, limit - onset[0])
            keys = kb.waitKeys(maxWait=remaining, keyList=[str(n) for n in range(1, choices + 1)]
                               + ["space", "escape"], waitRelease=False, clear=False) if remaining else None
            key = keys[0] if keys else None
            if key and key.name == "escape":
                raise KeyboardInterrupt
            if key is not None and not 0 <= key.rt < remaining:
                key = None
            expired = key is None
            response = key.name if key and key.name != "space" else None
            correct = response == row["answer"]
            score += correct
            answered += response is not None
            logger.write("gf_trial", **info, response=response, rt=key.rt if key else None,
                         correct=correct, timed_out=expired, onset_s=onset[0],
                         outcome="timed_out" if expired else "skipped" if response is None else "answered")
        logger.write("gf_summary", stage="test", form="public_examples", raw_score=score,
                     items_total=len(items), answered=answered, timeout_s=limit,
                     elapsed_s=min(clock.getTime(), limit), end_reason="time_limit" if expired else "all_items")
        screens.wait(kb, draw_screen, screens, title, "Test complete",
                     f"Correct: {score} / {len(items)}\nAnswered: {answered} / {len(items)}")
    finally:
        win._resize_draw = None
