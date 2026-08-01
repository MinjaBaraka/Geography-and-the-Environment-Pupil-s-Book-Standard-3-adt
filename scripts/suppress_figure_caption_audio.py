#!/usr/bin/env python3
"""Keep figure captions visible while excluding them from spoken narration."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"
CAPTION_RE = re.compile(r"^Figure\s+\d+\s*:", re.IGNORECASE)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_attribute(tag: str, name: str, value: str) -> str:
    pattern = rf'(\b{re.escape(name)}=")[^"]*(")'
    if re.search(pattern, tag, flags=re.IGNORECASE):
        return re.sub(pattern, rf"\g<1>{value}\g<2>", tag, count=1, flags=re.IGNORECASE)
    return tag[:-1] + f' {name}="{value}">'


def mark_caption_elements(pages: list[dict], caption_ids: set[str]) -> int:
    marked: set[str] = set()
    for entry in pages:
        path = ROOT / entry["href"]
        source = path.read_text(encoding="utf-8")
        updated = source
        for caption_id in sorted(caption_ids):
            pattern = re.compile(
                rf'<[^>]+\bdata-id="{re.escape(caption_id)}"[^>]*>', re.IGNORECASE
            )

            def replace(match: re.Match[str]) -> str:
                marked.add(caption_id)
                tag = add_attribute(match.group(0), "data-tts-ignore", "true")
                return add_attribute(tag, "aria-hidden", "true")

            updated = pattern.sub(replace, updated, count=1)
        if updated != source:
            path.write_text(updated, encoding="utf-8")

    missing = caption_ids - marked
    if missing:
        raise ValueError(f"Figure captions not found in HTML: {sorted(missing)}")
    return len(marked)


def remove_caption_audio(caption_ids: set[str], audios: dict[str, str]) -> tuple[int, int]:
    references = Counter(audios.values())
    retired: set[str] = set()
    removed_mappings = 0
    for caption_id in sorted(caption_ids):
        for key in (caption_id, f"{caption_id}_easy_read"):
            filename = audios.pop(key, None)
            if not filename:
                continue
            removed_mappings += 1
            references[filename] -= 1
            if references[filename] == 0:
                retired.add(filename)

    active = set(audios.values())
    removed_files = 0
    for filename in sorted(retired - active):
        path = I18N / "audio" / filename
        if path.is_file():
            path.unlink()
            removed_files += 1
    return removed_mappings, removed_files


def main() -> None:
    pages = read_json(ROOT / "content" / "pages.json")
    texts = read_json(I18N / "texts.json")
    audios_path = I18N / "audios.json"
    audios = read_json(audios_path)
    caption_ids = {
        key
        for key, value in texts.items()
        if re.fullmatch(r"pg\d+_n\d+", key) and CAPTION_RE.match(str(value).strip())
    }
    marked = mark_caption_elements(pages, caption_ids)
    removed_mappings, removed_files = remove_caption_audio(caption_ids, audios)
    write_json(audios_path, audios)
    print(
        f"Excluded {marked} figure captions from narration; "
        f"removed {removed_mappings} mappings and {removed_files} retired files."
    )


if __name__ == "__main__":
    main()
