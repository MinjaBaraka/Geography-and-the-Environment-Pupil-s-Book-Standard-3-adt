#!/usr/bin/env python3
"""Regenerate narration for every term and definition in Chapter One vocabulary."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import edge_tts


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"
AUDIO_DIR = I18N / "audio"
VOICE = "en-TZ-ImaniNeural"
VOCABULARY_IDS = (
    "pg019_n0016",
    "pg019_n0020", "pg019_n0022",
    "pg019_n0025", "pg019_n0027",
    "pg019_n0030", "pg019_n0032",
    "pg019_n0035", "pg019_n0037",
    "pg019_n0040", "pg019_n0042",
    "pg020_n0003", "pg020_n0004",
    "pg020_n0006", "pg020_n0007",
    "pg020_n0009", "pg020_n0010",
    "pg020_n0012", "pg020_n0013", "pg020_n0014",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def synthesize(key: str, speech: str, semaphore: asyncio.Semaphore) -> None:
    destination = AUDIO_DIR / f"{key}.mp3"
    temporary = destination.with_suffix(".tmp.mp3")
    async with semaphore:
        await edge_tts.Communicate(speech, VOICE).save(str(temporary))
    temporary.replace(destination)


async def main() -> None:
    texts = read_json(I18N / "texts.json")
    audios_path = I18N / "audios.json"
    audios = read_json(audios_path)
    tasks: list[tuple[str, str]] = []
    for base_id in VOCABULARY_IDS:
        for key in (base_id, f"{base_id}_easy_read"):
            if key not in texts:
                raise ValueError(f"Missing vocabulary narration text: {key}")
            audios[key] = f"{key}.mp3"
            tasks.append((key, texts[key]))

    semaphore = asyncio.Semaphore(4)
    await asyncio.gather(*(synthesize(key, speech, semaphore) for key, speech in tasks))
    write_json(audios_path, audios)
    print(f"Regenerated {len(tasks)} vocabulary narration files with {VOICE}.")


if __name__ == "__main__":
    asyncio.run(main())
