"""macOS 사전 합성 WAV 생성. 원논문 녹음이 아님. N-back 500ms, 숫자 최대950ms."""

from pathlib import Path
import array
import json
import subprocess
import sys
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import ASSUMPTIONS, AUDIO_DIR, DIGIT_SPAN, AUDIO_GENERATION


def generate():
    manifest = []
    sample_rate = AUDIO_GENERATION["sample_rate"]
    jobs = [
        (letter, letter, AUDIO_DIR, AUDIO_GENERATION["nback_file_s"])
        for letter in ASSUMPTIONS["consonants"]
    ]
    names = "one two three four five six seven eight nine".split()
    jobs += [
        (
            str(i),
            name,
            AUDIO_DIR / DIGIT_SPAN["audio_subdir"],
            AUDIO_GENERATION["digit_file_s"],
        )
        for i, name in enumerate(names, 1)
    ]
    with tempfile.TemporaryDirectory() as temp:
        for name, text, directory, duration in jobs:
            directory.mkdir(parents=True, exist_ok=True)
            source = Path(temp) / "source.aiff"
            wavpath = Path(temp) / "source.wav"
            subprocess.run(
                [
                    "/usr/bin/say",
                    "-v",
                    AUDIO_GENERATION["voice"],
                    "-r",
                    str(AUDIO_GENERATION["words_per_minute"]),
                    "-o",
                    str(source),
                    text,
                ],
                check=True,
            )
            subprocess.run(
                [
                    "/usr/bin/afconvert",
                    "-f",
                    "WAVE",
                    "-d",
                    f"LEI16@{sample_rate}",
                    str(source),
                    str(wavpath),
                ],
                check=True,
            )
            with wave.open(str(wavpath)) as wav:
                if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                    raise ValueError("mono PCM16 required")
                samples = array.array("h", wav.readframes(wav.getnframes()))
            if sys.byteorder != "little":
                samples.byteswap()
            voiced = [i for i, x in enumerate(samples) if abs(x) > 120]
            if not voiced:
                raise ValueError(f"{name}: 무음")
            samples = samples[
                max(0, voiced[0] - round(0.005 * sample_rate)) : min(
                    len(samples), voiced[-1] + round(0.01 * sample_rate) + 1
                )
            ]
            original_duration = len(samples) / sample_rate
            limit = round((duration - 0.02) * sample_rate)
            if len(samples) > limit:
                ratio = (len(samples) - 1) / (limit - 1)
                samples = array.array(
                    "h", (int(samples[int(i * ratio)]) for i in range(limit))
                )
            peak = max(abs(x) for x in samples)
            samples = array.array(
                "h",
                (
                    int(x * AUDIO_GENERATION["peak_level"] * 32767 / peak)
                    for x in samples
                ),
            )
            samples.extend([0] * (round(duration * sample_rate) - len(samples)))
            if sys.byteorder != "little":
                samples.byteswap()
            with wave.open(str(directory / f"{name}.wav"), "wb") as wav:
                wav.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
                wav.writeframes(samples.tobytes())
            manifest.append(
                dict(
                    file=str((directory / f"{name}.wav").relative_to(AUDIO_DIR)),
                    text=text,
                    voice=AUDIO_GENERATION["voice"],
                    rate=AUDIO_GENERATION["words_per_minute"],
                    trimmed_source_s=original_duration,
                    duration_s=duration,
                    compressed=original_duration > duration - 0.02,
                    source="macOS say; reproduction assumption",
                )
            )
    (AUDIO_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    generate()
