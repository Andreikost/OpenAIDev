"""Generate natural English scene narration with a neural conversational voice."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import edge_tts


DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"


async def generate(spec_path: Path, output_directory: Path, voice: str) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    output_directory.mkdir(parents=True, exist_ok=True)
    for index, shot in enumerate(spec["shot_plan"], start=1):
        target = output_directory / f"scene-{index:02d}.mp3"
        communicate = edge_tts.Communicate(
            text=shot["voiceover"],
            voice=voice,
            rate="-2%",
            pitch="-2Hz",
            volume="+0%",
        )
        await communicate.save(str(target))
        print(target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    args = parser.parse_args()
    asyncio.run(generate(args.spec, args.output_directory, args.voice))


if __name__ == "__main__":
    main()
