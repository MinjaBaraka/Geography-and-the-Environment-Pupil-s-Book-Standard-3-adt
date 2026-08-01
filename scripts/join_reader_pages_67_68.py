#!/usr/bin/env python3
"""Remove former reader page 68 after its content was merged into page 67."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES_PATH = ROOT / "content" / "pages.json"
REMOVED_SECTION = "pg048_sec001"
REMOVED_FILE = ROOT / "pg048_sec001.html"


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_spine() -> list[dict]:
    pages = json.loads(PAGES_PATH.read_text(encoding="utf-8"))
    original_count = len(pages)
    pages = [entry for entry in pages if entry["section_id"] != REMOVED_SECTION]
    if len(pages) != original_count - 1:
        raise ValueError(f"Expected to remove exactly one {REMOVED_SECTION} entry")
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
    line = '      <file href="pg048_sec001.html"/>\n'
    if source.count(line) != 1:
        raise ValueError("Could not uniquely locate pg048_sec001.html in imsmanifest.xml")
    path.write_text(source.replace(line, "", 1), encoding="utf-8")


def main() -> None:
    pages = update_spine()
    renumber_pages(pages)
    update_manifest()
    if REMOVED_FILE.is_file():
        REMOVED_FILE.unlink()
    print(f"Joined reader pages 67 and 68; spine now contains {len(pages)} pages.")


if __name__ == "__main__":
    main()
