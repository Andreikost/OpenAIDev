"""Add timed narration and encode the captured ColonyMind demo as MP4."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "prompts" / "colonymind-build-week-video.prompt.json"
SOURCE = ROOT / "output" / "video" / "colonymind-build-week-silent.webm"
OUTPUT_DIR = ROOT / "output" / "video"
TTS_DIR = ROOT / "tmp" / "colonymind-tts"
FINAL = OUTPUT_DIR / "colonymind-build-week-final.mp4"
SRT = OUTPUT_DIR / "colonymind-build-week-captions.srt"
NARRATION = TTS_DIR / "narration.wav"


def to_seconds(value: str) -> int:
    minutes, seconds = value.split(":")
    return int(minutes) * 60 + int(seconds)


def ffmpeg_duration(ffmpeg: str, path: Path) -> float:
    probe = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", probe.stderr)
    if not match:
        raise RuntimeError(f"Unable to read duration for {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def atempo_chain(factor: float) -> str:
    factors: list[float] = []
    while factor > 2.0:
        factors.append(2.0)
        factor /= 2.0
    while factor < 0.5:
        factors.append(0.5)
        factor /= 0.5
    factors.append(factor)
    return ",".join(f"atempo={value:.6f}" for value in factors)


def srt_time(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    shots = spec["shot_plan"]
    target_duration = int(spec["project"]["target_duration_seconds"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TTS_DIR.mkdir(parents=True, exist_ok=True)

    run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "video" / "generate_narration.ps1"),
            "-SpecPath",
            str(SPEC),
            "-OutputDirectory",
            str(TTS_DIR),
        ]
    )

    srt_blocks: list[str] = []
    adjusted: list[Path] = []
    for index, shot in enumerate(shots, start=1):
        start_text, end_text = shot["timecode"].split("-")
        start = to_seconds(start_text)
        end = to_seconds(end_text)
        scene_duration = end - start
        raw = TTS_DIR / f"scene-{index:02d}.wav"
        fitted = TTS_DIR / f"scene-{index:02d}-fitted.wav"
        raw_duration = ffmpeg_duration(ffmpeg, raw)
        spoken_window = max(scene_duration - 0.7, 1.0)
        tempo = raw_duration / spoken_window
        fade_out_start = max(scene_duration - 0.25, 0.0)
        audio_filter = (
            f"{atempo_chain(tempo)},adelay=350|350,apad,"
            f"atrim=0:{scene_duration},afade=t=in:st=0:d=0.12,"
            f"afade=t=out:st={fade_out_start:.3f}:d=0.22"
        )
        run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(raw),
                "-af",
                audio_filter,
                "-ar",
                "48000",
                "-ac",
                "2",
                "-c:a",
                "pcm_s16le",
                str(fitted),
            ]
        )
        adjusted.append(fitted)
        srt_blocks.append(
            f"{index}\n{srt_time(start)} --> {srt_time(end)}\n{shot['voiceover']}\n"
        )

    SRT.write_text("\n".join(srt_blocks), encoding="utf-8")
    concat_file = TTS_DIR / "narration-concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in adjusted),
        encoding="utf-8",
    )
    run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:a",
            "pcm_s16le",
            str(NARRATION),
        ]
    )

    source_duration = ffmpeg_duration(ffmpeg, SOURCE)
    lead_in = max(source_duration - target_duration, 0.0)
    run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{lead_in:.3f}",
            "-i",
            str(SOURCE),
            "-i",
            str(NARRATION),
            "-t",
            str(target_duration),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-r",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-af",
            "loudnorm=I=-14:TP=-1:LRA=11",
            "-b:a",
            "256k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(FINAL),
        ]
    )
    print(FINAL)
    print(SRT)


if __name__ == "__main__":
    main()
