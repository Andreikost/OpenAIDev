"""Validate the competition delivery's basic technical constraints."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--max-seconds", type=float, default=179.0)
    args = parser.parse_args()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(args.video)],
        capture_output=True,
        text=True,
        check=False,
    )
    metadata = result.stderr
    duration_match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", metadata)
    video_match = re.search(r"Video: ([^,]+).*?, (\d+)x(\d+).*?, ([\d.]+) fps", metadata)
    audio_match = re.search(r"Audio: ([^,]+), (\d+) Hz, ([^,]+)", metadata)
    if not (duration_match and video_match and audio_match):
        raise RuntimeError(f"Unable to parse media metadata for {args.video}")
    hours, minutes, seconds = duration_match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    video_codec, width, height, fps = video_match.groups()
    audio_codec, sample_rate, channel_layout = audio_match.groups()
    streams = {
        "video": {"codec": video_codec, "width": int(width), "height": int(height), "fps": float(fps)},
        "audio": {"codec": audio_codec, "sample_rate": int(sample_rate), "layout": channel_layout},
    }
    checks = {
        "duration_below_limit": duration < args.max_seconds,
        "resolution_1920x1080": int(width) == 1920 and int(height) == 1080,
        "h264_video": "h264" in video_codec,
        "aac_audio": "aac" in audio_codec,
        "audio_48khz": sample_rate == "48000",
        "stereo_audio": "stereo" in channel_layout,
    }
    report = {"file": str(args.video), "duration": duration, "checks": checks, "streams": streams}
    print(json.dumps(report, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
