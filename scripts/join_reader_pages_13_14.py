#!/usr/bin/env python3
"""Merge reader page 14's continuation into reader page 13."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES_PATH = ROOT / "content" / "pages.json"
SOURCE_SECTION = "pg013_sec001"
SOURCE_FILE = ROOT / "pg013_sec001.html"
TARGET_FILE = ROOT / "pg012_sec001.html"


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def merge_content() -> None:
    source = TARGET_FILE.read_text(encoding="utf-8")
    marker = '<span data-id="pg012_n0023">Therefore, it is not</span></p>'
    replacement = (
        '<span data-id="pg012_n0023">Therefore, it is not</span> '
        '<span data-id="pg013_n0002">necessary for one&#x2019;s home environment to be the same as another&#x2019;s.</span> '
        '<span data-id="pg013_n0003">Similarly, the environment of a particular area does not necessarily have to be the same as that of another.</span></p>'
    )
    if marker not in source:
        if 'data-id="pg013_n0002"' in source and 'data-id="pg013_n0003"' in source:
            return
        raise ValueError("Could not locate the page 13 sentence ending")
    TARGET_FILE.write_text(source.replace(marker, replacement, 1), encoding="utf-8")


def update_spine() -> list[dict]:
    pages = json.loads(PAGES_PATH.read_text(encoding="utf-8"))
    original_count = len(pages)
    pages = [entry for entry in pages if entry["section_id"] != SOURCE_SECTION]
    if len(pages) != original_count - 1:
        raise ValueError(f"Expected to remove exactly one {SOURCE_SECTION} entry")
    write_json(PAGES_PATH, pages)
    return pages


def renumber_pages(pages: list[dict]) -> None:
    pattern = re.compile(r'(<meta\s+name="page-section-id"\s+content=")[^"]*(")')
    for position, entry in enumerate(pages, 1):
        path = ROOT / entry["href"]
        source = path.read_text(encoding="utf-8")
        updated, count = pattern.subn(rf"\g<1>{position}\g<2>", source, count=1)
        if count != 1:
            raise ValueError(f"Could not renumber {entry['href']}")
        path.write_text(updated, encoding="utf-8")


def update_manifest() -> None:
    path = ROOT / "imsmanifest.xml"
    source = path.read_text(encoding="utf-8")
    line = '      <file href="pg013_sec001.html"/>\n'
    if source.count(line) != 1:
        raise ValueError("Could not uniquely locate pg013_sec001.html in imsmanifest.xml")
    path.write_text(source.replace(line, "", 1), encoding="utf-8")


def main() -> None:
    merge_content()
    pages = update_spine()
    renumber_pages(pages)
    update_manifest()
    if SOURCE_FILE.is_file():
        SOURCE_FILE.unlink()
    print(f"Joined reader pages 13 and 14; spine now contains {len(pages)} pages.")


if __name__ == "__main__":
    main()
