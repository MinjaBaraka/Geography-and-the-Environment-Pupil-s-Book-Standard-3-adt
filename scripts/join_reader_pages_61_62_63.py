#!/usr/bin/env python3
"""Redistribute reader pages 61–63 into two balanced pages."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES_PATH = ROOT / "content" / "pages.json"
FIRST_PAGE = ROOT / "pg044_sec002.html"
SECOND_PAGE = ROOT / "pg045_sec001.html"
REMOVED_SECTION = "pg046_sec001"
REMOVED_FILE = ROOT / "pg046_sec001.html"


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def complete_first_page() -> None:
    source = FIRST_PAGE.read_text(encoding="utf-8")
    marker = '<span data-id="pg044_n0028">Choosing appropriate</span>'
    continuation = (
        marker
        + ' <span data-id="pg045_n0002">trees, grass and flowers depends on the area where they will be planted.</span>'
        + ' <span data-id="pg045_n0003">It is better to include some fruit trees.</span>'
    )
    if marker in source:
        source = source.replace(marker, continuation, 1)
    elif 'data-id="pg045_n0002"' not in source or 'data-id="pg045_n0003"' not in source:
        raise ValueError("Could not locate the incomplete sentence on reader page 61")
    FIRST_PAGE.write_text(source, encoding="utf-8")


def complete_second_page() -> None:
    source = SECOND_PAGE.read_text(encoding="utf-8")
    moved_paragraph = (
        '    <p class="adt-body leading-relaxed text-left"><span data-id="pg045_n0002">trees, grass and flowers depends on the area where they will be planted.</span> '
        '<span data-id="pg045_n0003">It is better to include some fruit trees.</span></p>\n'
    )
    if moved_paragraph in source:
        source = source.replace(moved_paragraph, "", 1)
    elif 'data-id="pg045_n0002"' in source or 'data-id="pg045_n0003"' in source:
        raise ValueError("Could not uniquely remove the moved paragraph from reader page 62")

    marker = "  </figure>"
    added_content = """  </figure>

  <div class="mt-8 rounded-2xl border-l-8 border-teal-500 bg-teal-50/60 px-6 py-5 max-sm:px-4">
    <p class="adt-body text-left text-stone-800 leading-relaxed">
      <span data-id="pg046_n0002">Third, select seedlings which are healthier and free from disease for planting.</span>
      <span data-id="pg046_n0003">Fourth, it is important to care for the seedlings by watering them, if there is a shortage of soil moisture and by weeding whenever necessary.</span>
      <span data-id="pg046_n0004">Furthermore, to prevent pests and diseases, use environment-friendly pests and disease control methods.</span>
      <span data-id="pg046_n0005">For example, plant insect-repelling plants such as marigolds and calendula.</span>
    </p>
  </div>"""
    if 'data-id="pg046_n0002"' not in source:
        if source.count(marker) != 1:
            raise ValueError("Could not locate Figure 4 on reader page 62")
        source = source.replace(marker, added_content, 1)
    SECOND_PAGE.write_text(source, encoding="utf-8")


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
    line = '      <file href="pg046_sec001.html"/>\n'
    if source.count(line) != 1:
        raise ValueError("Could not uniquely locate pg046_sec001.html in imsmanifest.xml")
    path.write_text(source.replace(line, "", 1), encoding="utf-8")


def main() -> None:
    complete_first_page()
    complete_second_page()
    pages = update_spine()
    renumber_pages(pages)
    update_manifest()
    if REMOVED_FILE.is_file():
        REMOVED_FILE.unlink()
    print(f"Redistributed reader pages 61–63 into two pages; spine now contains {len(pages)} pages.")


if __name__ == "__main__":
    main()
