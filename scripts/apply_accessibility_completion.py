#!/usr/bin/env python3
"""Add Standard 5-style audio-description hooks to every meaningful image."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"
IMAGE_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def attribute(tag: str, name: str) -> str:
    match = re.search(rf'\b{re.escape(name)}="([^"]*)"', tag, flags=re.IGNORECASE)
    return html.unescape(match.group(1)) if match else ""


def replace_attribute(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = rf'(\b{re.escape(name)}=")[^"]*(")'
    if re.search(pattern, tag, flags=re.IGNORECASE):
        return re.sub(pattern, rf"\g<1>{escaped}\g<2>", tag, count=1, flags=re.IGNORECASE)
    return tag[:-1] + f' {name}="{escaped}">'


def meaningful_image_ids(pages: list[dict], texts: dict) -> set[str]:
    ids: set[str] = set()
    for entry in pages:
        path = ROOT / entry["href"]
        source = path.read_text(encoding="utf-8")
        original = source

        def update(match: re.Match[str]) -> str:
            tag = match.group(0)
            image_id = attribute(tag, "data-id")
            classes = set(attribute(tag, "class").split())
            decorative = (
                attribute(tag, "role") == "presentation"
                or attribute(tag, "aria-hidden") == "true"
                or "hidden" in classes
                or not image_id
            )
            if decorative:
                if "hidden" in classes and image_id:
                    tag = replace_attribute(tag, "alt", "")
                    tag = replace_attribute(tag, "role", "presentation")
                    tag = replace_attribute(tag, "aria-hidden", "true")
                    tag = re.sub(r'\sdata-id="[^"]*"', "", tag, count=1)
                return tag

            description = str(texts.get(image_id, "")).strip()
            if not description:
                raise ValueError(f"{entry['href']}: {image_id} has no image description")
            ids.add(image_id)
            tag = replace_attribute(tag, "alt", description)
            hook_id = f"{image_id}_audio_description"
            if f'data-audio-description-for="{image_id}"' in original:
                return tag
            return (
                tag
                + f'<span class="sr-only" aria-hidden="true" '
                + f'data-audio-description-for="{image_id}" data-id="{hook_id}"></span>'
            )

        updated = IMAGE_RE.sub(update, source)
        if updated != source:
            path.write_text(updated, encoding="utf-8")
    return ids


def synchronize_localization(image_ids: set[str], texts: dict, audios: dict) -> tuple[int, int]:
    audio_dir = I18N / "audio"
    old_references = Counter(audios.values())
    retired_files: set[str] = set()

    for image_id in sorted(image_ids):
        hook_id = f"{image_id}_audio_description"
        description = texts[image_id]
        filename = audios.get(hook_id) or audios.get(image_id)
        if not filename:
            raise ValueError(f"{image_id} has no source narration file")
        if not (audio_dir / filename).is_file():
            raise FileNotFoundError(audio_dir / filename)
        texts[hook_id] = description
        audios[hook_id] = filename

        for key in (image_id, f"{image_id}_easy_read"):
            old = audios.pop(key, None)
            if old:
                old_references[old] -= 1
                if old_references[old] == 0:
                    retired_files.add(old)

    hidden_id = "pg044_im002"
    texts.pop(hidden_id, None)
    texts.pop(f"{hidden_id}_easy_read", None)
    for key in (hidden_id, f"{hidden_id}_easy_read"):
        old = audios.pop(key, None)
        if old:
            old_references[old] -= 1
            if old_references[old] == 0:
                retired_files.add(old)

    active_files = set(audios.values())
    removed = 0
    for filename in sorted(retired_files - active_files):
        path = audio_dir / filename
        if path.is_file():
            path.unlink()
            removed += 1
    return len(image_ids), removed


def main() -> None:
    pages = read_json(ROOT / "content" / "pages.json")
    texts_path = I18N / "texts.json"
    audios_path = I18N / "audios.json"
    texts = read_json(texts_path)
    audios = read_json(audios_path)

    image_ids = meaningful_image_ids(pages, texts)
    count, removed = synchronize_localization(image_ids, texts, audios)
    write_json(texts_path, texts)
    write_json(audios_path, audios)
    print(f"Added audio-description hooks for {count} images; removed {removed} retired files.")


if __name__ == "__main__":
    main()
