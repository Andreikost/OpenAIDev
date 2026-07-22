"""Create a more fluid ColonyMind edit while preserving authentic UI evidence."""

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
WORK_DIR = ROOT / "tmp" / "colonymind-video-v2"
FINAL = OUTPUT_DIR / "colonymind-build-week-dynamic-v2.mp4"
SRT = OUTPUT_DIR / "colonymind-build-week-dynamic-v2-captions.srt"
NARRATION = WORK_DIR / "narration-neural.wav"
ASSETS = OUTPUT_DIR / "colonymind-build-week-dynamic-v2-assets.txt"


def to_seconds(value: str) -> int:
    minutes, seconds = value.split(":")
    return int(minutes) * 60 + int(seconds)


def duration(ffmpeg: str, path: Path) -> float:
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Unable to read duration for {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def atempo_chain(factor: float) -> str:
    factors: list[float] = []
    while factor > 2.0:
        factors.append(2.0)
        factor /= 2.0
    factors.append(max(factor, 1.0))
    return ",".join(f"atempo={value:.6f}" for value in factors)


def srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    shots = spec["shot_plan"]
    target_duration = int(spec["project"]["target_duration_seconds"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    run(
        [
            "python",
            str(ROOT / "scripts" / "video" / "generate_neural_narration.py"),
            str(SPEC),
            str(WORK_DIR),
        ]
    )

    fitted_scenes: list[Path] = []
    srt_blocks: list[str] = []
    for index, shot in enumerate(shots, start=1):
        start_text, end_text = shot["timecode"].split("-")
        start = to_seconds(start_text)
        end = to_seconds(end_text)
        scene_duration = end - start
        raw = WORK_DIR / f"scene-{index:02d}.mp3"
        fitted = WORK_DIR / f"scene-{index:02d}-fitted.wav"
        raw_duration = duration(ffmpeg, raw)
        available = max(scene_duration - 0.55, 1.0)
        tempo = max(raw_duration / available, 1.0)
        spoken_duration = min(raw_duration / tempo, available)
        fade_out_start = max(scene_duration - 0.18, 0.0)
        audio_filter = (
            f"{atempo_chain(tempo)},adelay=260|260,apad,"
            f"atrim=0:{scene_duration},afade=t=in:st=0:d=0.08,"
            f"afade=t=out:st={fade_out_start:.3f}:d=0.16"
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
        fitted_scenes.append(fitted)
        caption_start = start + 0.18
        caption_end = min(start + 0.30 + spoken_duration, end - 0.1)
        srt_blocks.append(
            f"{index}\n{srt_time(caption_start)} --> {srt_time(caption_end)}\n"
            f"{shot['voiceover']}\n"
        )

    SRT.write_text("\n".join(srt_blocks), encoding="utf-8")
    concat_file = WORK_DIR / "narration-concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in fitted_scenes),
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

    # The bed is generated from pure tones during assembly. It is original,
    # deterministic, and kept deliberately quiet under the narration.
    source_duration = duration(ffmpeg, SOURCE)
    end_card_duration = 4.0
    main_end = target_duration - end_card_duration
    source_end_card_start = source_duration - end_card_duration
    camera_filter = (
        "scale=1968:1107:flags=lanczos,"
        "crop=1920:1080:x='24+10*sin(t*0.43)':y='13+8*cos(t*0.31)',"
        "eq=contrast=1.025:saturation=1.045"
    )
    video_filter = (
        f"[0:v]split=2[vmain0][vend0];"
        f"[vmain0]trim=start=0:end={main_end},setpts=PTS-STARTPTS,{camera_filter}[vmain];"
        f"[vend0]trim=start={source_end_card_start}:end={source_duration},"
        f"setpts=PTS-STARTPTS,{camera_filter}[vend];"
        "[vmain][vend]concat=n=2:v=1:a=0,"
        "fade=t=in:st=0:d=0.35,fade=t=out:st=169.2:d=0.8[vout]"
    )
    audio_filter = (
        "[1:a]loudnorm=I=-15:TP=-1.5:LRA=8[voice];"
        "[2:a]volume=0.045,tremolo=f=0.42:d=0.28,lowpass=f=420[bed1];"
        "[3:a]volume=0.028,tremolo=f=0.21:d=0.22,lowpass=f=520[bed2];"
        "[bed1][bed2]amix=inputs=2:normalize=0,"
        "afade=t=in:st=0:d=2,afade=t=out:st=166:d=4[bed];"
        "[voice][bed]amix=inputs=2:normalize=0,alimiter=limit=0.84[aout]"
    )
    filter_complex = f"{video_filter};{audio_filter}"
    run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(SOURCE),
            "-i",
            str(NARRATION),
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=55:sample_rate=48000:duration={target_duration}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=82.41:sample_rate=48000:duration={target_duration}",
            "-t",
            str(target_duration),
            "-filter_complex",
            filter_complex,
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "17",
            "-r",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(FINAL),
        ]
    )

    ASSETS.write_text(
        "Visuals: authentic ColonyMind deployed-application capture.\n"
        "Narration: AI-assisted neural voice generated from the entrant-approved "
        "script with edge-tts (en-US-AndrewMultilingualNeural).\n"
        "Music: original deterministic two-tone ambient bed synthesized during "
        "FFmpeg assembly; no external music or samples.\n"
        "No third-party stock footage, images, music, or sound effects.\n",
        encoding="utf-8",
    )
    print(FINAL)
    print(SRT)
    print(ASSETS)


if __name__ == "__main__":
    main()
