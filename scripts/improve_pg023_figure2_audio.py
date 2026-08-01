#!/usr/bin/env python3
"""Provide a detailed spatial audio description for the relief diagram."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import edge_tts


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"
TEXTS_PATH = I18N / "texts.json"
AUDIO_DIR = I18N / "audio"
HTML_PATH = ROOT / "pg023_sec001.html"
DESCRIPTION_ID = "pg023_im001_audio_description"
VOICE = "en-TZ-ImaniNeural"

SHORT_ALT = (
    "A side-view diagram comparing a mountain, valley, hill, plateau, plain and basin "
    "from left to right."
)

DESCRIPTION = (
    "The diagram is a side view of six connected landforms arranged from left to right. "
    "At the far left, a mountain rises much higher than all the other land. It has steep sides "
    "and a sharp, snow-covered peak. The Mountain arrow points to this highest peak. "
    "Immediately to its right, the land drops into a narrow V-shaped low area between the mountain "
    "and the next raised feature. The Valley arrow points to the bottom of this low gap. "
    "Next is a hill, which is lower than the mountain and has a gently rounded top. "
    "Farther right, the land rises gradually into a plateau. The plateau has a wide, nearly level top "
    "that stands above the surrounding land, then ends at a short, steep cliff. "
    "Beyond the cliff is a broad plain, shown as a long stretch of low, flat land. "
    "At the far right, the land curves downward into a shallow bowl-shaped basin before rising again "
    "at the outer edge. Each label is placed above its landform, with an arrow pointing to the exact feature."
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def synthesize() -> None:
    destination = AUDIO_DIR / "pg023_im001.mp3"
    temporary = destination.with_suffix(".tmp.mp3")
    await edge_tts.Communicate(DESCRIPTION, VOICE).save(str(temporary))
    temporary.replace(destination)


async def main() -> None:
    texts = read_json(TEXTS_PATH)
    texts["pg023_im001"] = SHORT_ALT
    texts[DESCRIPTION_ID] = DESCRIPTION
    write_json(TEXTS_PATH, texts)

    source = HTML_PATH.read_text(encoding="utf-8")
    old_alt = (
        'alt="Diagram of major relief features showing a high mountain beside a valley and hill, '
        'leading to a flat-topped plateau, a plain and a basin."'
    )
    new_alt = f'alt="{SHORT_ALT}"'
    if old_alt in source:
        source = source.replace(old_alt, new_alt, 1)
    elif new_alt not in source:
        raise ValueError("Could not locate the relief-diagram alt text")
    HTML_PATH.write_text(source, encoding="utf-8")

    await synthesize()
    print("Rebuilt the relief diagram audio with a detailed spatial description.")


if __name__ == "__main__":
    asyncio.run(main())
