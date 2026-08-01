#!/usr/bin/env python3
"""Regenerate narration changed by the matrix work and remove retired audio."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter
from pathlib import Path

import edge_tts

from apply_content_plan import TEXT_CHANGES, WATERMARK_IDS


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"
AUDIO_DIR = I18N / "audio"
NEW_PAGE_PREFIXES = ("pg002_", "pg004_", "pg088_")
STRUCTURAL_TEXT_CHANGES = {
    "pg050_n0007",
    "pg050_n0008",
    "pg059_n0004",
    "pg059_n0005",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def synthesize(key: str, text: str, voice: str, semaphore: asyncio.Semaphore) -> None:
    destination = AUDIO_DIR / f"{key}.mp3"
    temporary = destination.with_suffix(".tmp.mp3")
    async with semaphore:
        await edge_tts.Communicate(text, voice).save(str(temporary))
    temporary.replace(destination)


async def regenerate(voice: str, concurrency: int) -> tuple[int, int]:
    texts_path = I18N / "texts.json"
    audios_path = I18N / "audios.json"
    texts = read_json(texts_path)
    audios = read_json(audios_path)

    base_keys = {
        key
        for key in texts
        if key.startswith(NEW_PAGE_PREFIXES) and not key.endswith("_easy_read")
    }
    base_keys.update(TEXT_CHANGES)
    base_keys.update(STRUCTURAL_TEXT_CHANGES)
    base_keys = {key for key in base_keys if key in texts}

    semaphore = asyncio.Semaphore(concurrency)
    tasks = [synthesize(key, texts[key], voice, semaphore) for key in sorted(base_keys)]
    await asyncio.gather(*tasks)

    old_references = Counter(audios.values())
    retired_files: set[str] = set()
    for key in sorted(base_keys):
        target_file = f"{key}.mp3"
        for variant in (key, f"{key}_easy_read"):
            old_file = audios.get(variant)
            audios[variant] = target_file
            if old_file and old_file != target_file:
                old_references[old_file] -= 1
                if old_references[old_file] == 0:
                    retired_files.add(old_file)

    for key in WATERMARK_IDS:
        for variant in (key, f"{key}_easy_read"):
            old_file = audios.pop(variant, None)
            if old_file:
                old_references[old_file] -= 1
                if old_references[old_file] == 0:
                    retired_files.add(old_file)

    for key in [key for key in audios if key.startswith("qz")]:
        old_file = audios.pop(key)
        old_references[old_file] -= 1
        if old_references[old_file] == 0:
            retired_files.add(old_file)

    for path in AUDIO_DIR.glob("qz*.mp3"):
        retired_files.add(path.name)
    for key in WATERMARK_IDS:
        retired_files.update({f"{key}.mp3", f"{key}_easy_read.mp3"})

    write_json(audios_path, audios)
    removed = 0
    active_files = set(audios.values())
    for filename in sorted(retired_files - active_files):
        path = AUDIO_DIR / filename
        if path.is_file():
            path.unlink()
            removed += 1
    return len(base_keys), removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", default="en-TZ-ImaniNeural")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    generated, removed = asyncio.run(regenerate(args.voice, args.concurrency))
    print(f"Generated {generated} narration files with {args.voice}; removed {removed} retired files.")


if __name__ == "__main__":
    main()
