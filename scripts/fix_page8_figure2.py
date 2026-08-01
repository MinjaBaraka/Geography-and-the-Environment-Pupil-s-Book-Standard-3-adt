#!/usr/bin/env python3
"""Keep the page 8 sentence together and narrate Figure 2 as a diagram."""

from __future__ import annotations

import asyncio
import json
import re
from collections import Counter
from pathlib import Path

import edge_tts


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"
AUDIO_DIR = I18N / "audio"
VOICE = "en-TZ-ImaniNeural"
SENTENCE = "Information about the components that form the environment is summarised in Figure 2."
EASY_SENTENCE = "Figure 2 summarises the parts of the environment."
DIAGRAM_ID = "pg009_fig002_audio_description"
DIAGRAM_DESCRIPTION = (
    "A flow diagram is arranged from left to right. One box on the left connects to two branches. "
    "The upper arrow points to a box for the natural part of the surroundings, followed by another "
    "arrow to things occurring in nature. The lower arrow points to a box for the human-created part "
    "of the surroundings, followed by another arrow to objects made by people."
)
BOX_IDS = {"pg009_n0004", "pg009_n0005", "pg009_n0006", "pg009_n0007", "pg009_n0008"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_html() -> None:
    page8 = ROOT / "pg008_sec001.html"
    source8 = page8.read_text(encoding="utf-8")
    updated8, count = re.subn(
        r'(<span data-id="pg008_n0021">)[^<]*(</span>)',
        rf"\g<1>{SENTENCE}\g<2>",
        source8,
        count=1,
    )
    if count != 1:
        raise ValueError("Could not update the split sentence on page 8")
    page8.write_text(updated8, encoding="utf-8")

    page9 = ROOT / "pg009_sec001.html"
    source9 = page9.read_text(encoding="utf-8")
    updated9, count = re.subn(
        r'<p class="adt-body mb-8 leading-relaxed text-left"><span data-id="pg009_n0002">.*?</span></p>',
        "",
        source9,
        count=1,
    )
    if count != 1:
        raise ValueError("Could not remove the sentence fragment from page 9")

    for box_id in sorted(BOX_IDS):
        pattern = rf'(<[^>]+data-id="{box_id}"[^>]*)(>)'

        def mark_box(match: re.Match[str]) -> str:
            tag = match.group(1)
            if 'data-tts-ignore="true"' not in tag:
                tag += ' data-tts-ignore="true"'
            if 'aria-hidden="true"' not in tag:
                tag += ' aria-hidden="true"'
            return tag + match.group(2)

        updated9, count = re.subn(pattern, mark_box, updated9, count=1)
        if count != 1:
            raise ValueError(f"Could not mark diagram box {box_id}")

    hook = f'<span class="sr-only" aria-hidden="true" data-id="{DIAGRAM_ID}"></span>'
    if f'data-id="{DIAGRAM_ID}"' not in updated9:
        marker = '<div class="mb-8"><div class="flex items-center justify-center'
        if marker not in updated9:
            raise ValueError("Could not locate the Figure 2 diagram")
        updated9 = updated9.replace(
            marker,
            f'<div class="mb-8">{hook}<div class="flex items-center justify-center',
            1,
        )
    page9.write_text(updated9, encoding="utf-8")


def update_localization() -> set[str]:
    texts_path = I18N / "texts.json"
    audios_path = I18N / "audios.json"
    texts = read_json(texts_path)
    audios = read_json(audios_path)
    old_references = Counter(audios.values())
    retired: set[str] = set()

    texts["pg008_n0021"] = SENTENCE
    texts["pg008_n0021_easy_read"] = EASY_SENTENCE
    texts[DIAGRAM_ID] = DIAGRAM_DESCRIPTION
    for key in ("pg009_n0002", "pg009_n0002_easy_read"):
        texts.pop(key, None)

    excluded = BOX_IDS | {f"{key}_easy_read" for key in BOX_IDS}
    excluded.update({"pg009_n0002", "pg009_n0002_easy_read"})
    for key in sorted(excluded):
        filename = audios.pop(key, None)
        if filename:
            old_references[filename] -= 1
            if old_references[filename] == 0:
                retired.add(filename)

    audios["pg008_n0021"] = "pg008_n0021.mp3"
    audios["pg008_n0021_easy_read"] = "pg008_n0021_easy_read.mp3"
    audios[DIAGRAM_ID] = f"{DIAGRAM_ID}.mp3"
    write_json(texts_path, texts)
    write_json(audios_path, audios)

    active = set(audios.values())
    return retired - active


async def synthesize(key: str, text: str) -> None:
    destination = AUDIO_DIR / f"{key}.mp3"
    temporary = destination.with_suffix(".tmp.mp3")
    await edge_tts.Communicate(text, VOICE).save(str(temporary))
    temporary.replace(destination)


async def main() -> None:
    update_html()
    retired = update_localization()
    await asyncio.gather(
        synthesize("pg008_n0021", SENTENCE),
        synthesize("pg008_n0021_easy_read", EASY_SENTENCE),
        synthesize(DIAGRAM_ID, DIAGRAM_DESCRIPTION),
    )
    removed = 0
    for filename in sorted(retired):
        path = AUDIO_DIR / filename
        if path.is_file():
            path.unlink()
            removed += 1
    print(f"Fixed page 8 sentence and Figure 2 narration; removed {removed} retired files.")


if __name__ == "__main__":
    asyncio.run(main())
