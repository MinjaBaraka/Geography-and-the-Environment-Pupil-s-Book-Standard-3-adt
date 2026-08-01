#!/usr/bin/env python3
"""Join the two reader pages that contain the Chapter One vocabulary list."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES_PATH = ROOT / "content" / "pages.json"
TOC_PATH = ROOT / "content" / "toc.json"
SOURCE_SECTION = "pg020_sec001"
SOURCE_FILE = ROOT / "pg020_sec001.html"
TARGET_FILE = ROOT / "pg019_sec001.html"

INFRASTRUCTURE_ROW = '''<div class="grid grid-cols-[250px_1fr] gap-x-10 items-start max-sm:grid-cols-1 max-sm:gap-x-0 max-sm:gap-y-1"><div data-id="pg019_n0040" class="adt-body font-bold text-left">Infrastructure</div><p class="adt-body leading-relaxed text-left"><span data-id="pg019_n0042">basic systems and structures such as roads, railways, banks or an hospitals that a country or an organisation needs to function properly</span></p></div>'''

CONTINUATION_ROWS = '''<div class="grid grid-cols-[250px_1fr] gap-x-10 items-start max-sm:grid-cols-1 max-sm:gap-x-0 max-sm:gap-y-1"><div data-id="pg020_n0003" class="adt-body font-bold text-left">Land</div><p class="adt-body leading-relaxed text-left"><span data-id="pg020_n0004">the hard part of the earth that is not covered by water</span></p></div><div class="grid grid-cols-[250px_1fr] gap-x-10 items-start max-sm:grid-cols-1 max-sm:gap-x-0 max-sm:gap-y-1"><div data-id="pg020_n0006" class="adt-body font-bold text-left">Ocean</div><p class="adt-body leading-relaxed text-left"><span data-id="pg020_n0007">a large body of salt water that covers most of the earth&#x2019;s surface and surrounds its land masses</span></p></div><div class="grid grid-cols-[250px_1fr] gap-x-10 items-start max-sm:grid-cols-1 max-sm:gap-x-0 max-sm:gap-y-1"><div data-id="pg020_n0009" class="adt-body font-bold text-left">Resource</div><p class="adt-body leading-relaxed text-left"><span data-id="pg020_n0010">a substance which provides products that are essential for human life</span></p></div><div class="grid grid-cols-[250px_1fr] gap-x-10 items-start max-sm:grid-cols-1 max-sm:gap-x-0 max-sm:gap-y-1"><div data-id="pg020_n0012" class="adt-body font-bold text-left">Weather</div><p class="adt-body leading-relaxed text-left"><span data-id="pg020_n0013">the atmospheric condition experienced over a short period of time.</span> <span data-id="pg020_n0014">It may be an hour, a day or a week</span></p></div>'''


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def merge_content() -> None:
    source = TARGET_FILE.read_text(encoding="utf-8")
    if 'data-id="pg020_n0003"' in source:
        return
    if source.count(INFRASTRUCTURE_ROW) != 1:
        raise ValueError("Could not uniquely locate the final vocabulary row on reader page 24")
    TARGET_FILE.write_text(
        source.replace(INFRASTRUCTURE_ROW, INFRASTRUCTURE_ROW + CONTINUATION_ROWS, 1),
        encoding="utf-8",
    )


def update_spine() -> list[dict]:
    pages = json.loads(PAGES_PATH.read_text(encoding="utf-8"))
    original_count = len(pages)
    pages = [entry for entry in pages if entry["section_id"] != SOURCE_SECTION]
    if len(pages) != original_count - 1:
        raise ValueError(f"Expected to remove exactly one {SOURCE_SECTION} entry")
    write_json(PAGES_PATH, pages)
    return pages


def update_toc() -> None:
    toc = json.loads(TOC_PATH.read_text(encoding="utf-8"))
    original_count = len(toc)
    toc = [entry for entry in toc if entry["section_id"] != SOURCE_SECTION]
    if len(toc) != original_count - 1:
        raise ValueError(f"Expected to remove exactly one {SOURCE_SECTION} TOC entry")
    write_json(TOC_PATH, toc)


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
    line = '      <file href="pg020_sec001.html"/>\n'
    if source.count(line) != 1:
        raise ValueError("Could not uniquely locate pg020_sec001.html in imsmanifest.xml")
    path.write_text(source.replace(line, "", 1), encoding="utf-8")


def main() -> None:
    merge_content()
    pages = update_spine()
    update_toc()
    renumber_pages(pages)
    update_manifest()
    if SOURCE_FILE.is_file():
        SOURCE_FILE.unlink()
    print(f"Joined reader pages 24 and 25; spine now contains {len(pages)} pages.")


if __name__ == "__main__":
    main()
