#!/usr/bin/env python3
"""Regenerate selected narration keys from the current locale text."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import edge_tts


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"
AUDIO_DIR = I18N / "audio"


async def synthesize(key: str, text: str, filename: str, voice: str) -> None:
    destination = AUDIO_DIR / filename
    temporary = destination.with_suffix(".tmp.mp3")
    await edge_tts.Communicate(text, voice).save(str(temporary))
    temporary.replace(destination)


async def regenerate(keys: list[str], voice: str, concurrency: int) -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios = json.loads((I18N / "audios.json").read_text(encoding="utf-8"))
    missing = [key for key in keys if key not in texts or key not in audios]
    if missing:
        raise SystemExit(f"Unknown narration key(s): {', '.join(missing)}")
    empty = [key for key in keys if not str(texts[key]).strip()]
    if empty:
        raise SystemExit(f"Empty narration text for: {', '.join(empty)}")

    semaphore = asyncio.Semaphore(concurrency)

    async def guarded(key: str) -> None:
        async with semaphore:
            await synthesize(key, texts[key], audios[key], voice)

    await asyncio.gather(*(guarded(key) for key in keys))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("keys", nargs="+")
    parser.add_argument("--voice", default="en-TZ-ImaniNeural")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    asyncio.run(regenerate(args.keys, args.voice, args.concurrency))
    print(f"Regenerated {len(args.keys)} narration clip(s) with {args.voice}.")


if __name__ == "__main__":
    main()
