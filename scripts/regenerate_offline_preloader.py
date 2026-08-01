#!/usr/bin/env python3
"""Regenerate the JSON/HTML payload embedded in offline-preloader.js."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRELOADER = ROOT / "assets" / "offline-preloader.js"


def load_payload(path: Path):
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def main() -> None:
    pages_path = ROOT / "content" / "pages.json"
    pages = json.loads(pages_path.read_text(encoding="utf-8"))

    relative_paths = [
        "assets/config.json",
        "content/pages.json",
        "content/toc.json",
        "content/navigation/nav.html",
        *[entry["href"] for entry in pages],
        "assets/interface_translations/en-GB/interface_translations.json",
        "content/i18n/en-GB/texts.json",
        "content/i18n/en-GB/audios.json",
        "content/i18n/en-GB/videos.json",
        "content/i18n/en-GB/images.json",
        "content/i18n/en-GB/glossary.json",
        "content/i18n/en-GB/timecode/timecode_output.json",
    ]

    payload = {}
    for relative in dict.fromkeys(relative_paths):
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Offline payload source is missing: {relative}")
        payload[f"./{relative.replace('\\', '/')}"] = load_payload(path)

    source = PRELOADER.read_text(encoding="utf-8")
    marker = "  var INLINE = "
    start = source.index(marker) + len(marker)
    _, length = json.JSONDecoder().raw_decode(source[start:])
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    PRELOADER.write_text(source[:start] + encoded + source[start + length :], encoding="utf-8")
    print(f"Regenerated {PRELOADER.name} with {len(payload)} embedded resources.")


if __name__ == "__main__":
    main()
