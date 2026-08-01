#!/usr/bin/env python3
"""Give parenthesized Roman numerals clear, contextual narration."""

from __future__ import annotations

import asyncio
import html
import json
import re
from pathlib import Path

import edge_tts


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"
AUDIO_DIR = I18N / "audio"
VOICE = "en-TZ-ImaniNeural"
ROMAN_RE = re.compile(r"^\s*\(([ivxl]+)\)\s*$", re.IGNORECASE)
IMAGE_PREFIXES = ("pg009_", "pg012_", "pg014_")
NUMBER_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def roman_to_int(value: str) -> int:
    values = {"i": 1, "v": 5, "x": 10, "l": 50}
    total = 0
    previous = 0
    for character in reversed(value.lower()):
        current = values[character]
        if current < previous:
            total -= current
        else:
            total += current
            previous = current
    return total


def spoken_label(label_id: str, roman: str) -> tuple[str, str]:
    number = roman_to_int(roman)
    word = NUMBER_WORDS.get(number, str(number))
    kind = "image" if label_id.startswith(IMAGE_PREFIXES) else "item"
    return kind, f"{kind.capitalize()} {word}"


def set_attribute(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = rf'(\b{re.escape(name)}=")[^"]*(")'
    if re.search(pattern, tag, flags=re.IGNORECASE):
        return re.sub(pattern, rf"\g<1>{escaped}\g<2>", tag, count=1, flags=re.IGNORECASE)
    return tag[:-1] + f' {name}="{escaped}">'


def restore_html(pages: list[dict], labels: dict[str, tuple[str, str]]) -> int:
    restored: set[str] = set()
    for entry in pages:
        path = ROOT / entry["href"]
        source = path.read_text(encoding="utf-8")
        updated = source
        for label_id, (_, speech) in labels.items():
            pattern = re.compile(
                rf'<[^>]+\bdata-id="{re.escape(label_id)}"[^>]*>', re.IGNORECASE
            )

            def replace(match: re.Match[str]) -> str:
                restored.add(label_id)
                tag = re.sub(r'\sdata-tts-ignore="true"', "", match.group(0), flags=re.IGNORECASE)
                tag = re.sub(r'\saria-hidden="true"', "", tag, flags=re.IGNORECASE)
                return set_attribute(tag, "aria-label", speech)

            updated = pattern.sub(replace, updated, count=1)
        if updated != source:
            path.write_text(updated, encoding="utf-8")

    missing = set(labels) - restored
    if missing:
        raise ValueError(f"Roman-numeral labels not found in HTML: {sorted(missing)}")
    return len(restored)


async def synthesize(filename: str, speech: str, semaphore: asyncio.Semaphore) -> None:
    destination = AUDIO_DIR / filename
    temporary = destination.with_suffix(".tmp.mp3")
    async with semaphore:
        await edge_tts.Communicate(speech, VOICE).save(str(temporary))
    temporary.replace(destination)


async def main() -> None:
    pages = read_json(ROOT / "content" / "pages.json")
    texts = read_json(I18N / "texts.json")
    audios_path = I18N / "audios.json"
    audios = read_json(audios_path)

    labels: dict[str, tuple[str, str]] = {}
    audio_phrases: dict[str, str] = {}
    for key, value in texts.items():
        if key.endswith("_easy_read"):
            continue
        match = ROMAN_RE.fullmatch(str(value))
        if not match:
            continue
        kind, speech = spoken_label(key, match.group(1))
        number = roman_to_int(match.group(1))
        filename = f"roman_{kind}_{number}.mp3"
        labels[key] = (filename, speech)
        audio_phrases[filename] = speech
        audios[key] = filename
        audios[f"{key}_easy_read"] = filename

    restored = restore_html(pages, labels)
    semaphore = asyncio.Semaphore(4)
    await asyncio.gather(
        *(synthesize(filename, speech, semaphore) for filename, speech in sorted(audio_phrases.items()))
    )
    write_json(audios_path, audios)
    print(
        f"Restored narration for {restored} Roman-numeral labels using "
        f"{len(audio_phrases)} contextual audio files."
    )


if __name__ == "__main__":
    asyncio.run(main())
