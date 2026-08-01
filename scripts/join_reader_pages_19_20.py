#!/usr/bin/env python3
"""Merge reader page 20's continuation into reader page 19."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES_PATH = ROOT / "content" / "pages.json"
SOURCE_SECTION = "pg016_sec001"
SOURCE_FILE = ROOT / "pg016_sec001.html"
TARGET_FILE = ROOT / "pg015_sec002.html"


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def merge_content() -> None:
    source = TARGET_FILE.read_text(encoding="utf-8")
    marker = (
        '<span data-id="pg015_n0027">In addition, mountainous areas may have cooler weather due to the high altitude; '
        'thus people need to wear thick</span>'
    )
    continuation = (
        marker
        + ' <span data-id="pg016_n0002">clothes like sweaters when they are in such areas.</span>'
        + ' <span data-id="pg016_n0003">Coastal areas often have warmer weather than inland areas.</span>'
        + ' <span data-id="pg016_n0004">Therefore, those in warm coastal areas can wear lighter clothing to avoid or reduce the effects of heat.</span>'
        + ' <span data-id="pg016_n0005">However, the temperature in coastal areas can vary depending on the elevation of land and the direction of winds.</span>'
        + ' <span data-id="pg016_n0006">Geography and the Environment helps us to identify natural hazards such as floods, earthquakes and hurricanes, and how to avoid their effects on people and their property.</span>'
        + ' <span data-id="pg016_n0007">Geography and the Environment also assists us in planning and building infrastructure and social services.</span>'
        + ' <span data-id="pg016_n0008">Examples of infrastructure and providing social services include roads, hospitals and schools.</span>'
        + ' <span data-id="pg016_n0009">Thus, learning Geography and the Environment enables human beings to identify areas in need of such services.</span>'
        + ' <span data-id="pg016_n0010">Generally, it is important to learn Geography and the Environment so as to plan for appropriate and sustainable use of the resources found in the environment.</span>'
        + ' <span data-id="pg016_n0011">The resources can be water, forests and land.</span>'
    )
    if marker not in source:
        if all(f'data-id="pg016_n{number:04d}"' in source for number in range(2, 12)):
            return
        raise ValueError("Could not locate the page 19 sentence ending")
    TARGET_FILE.write_text(source.replace(marker, continuation, 1), encoding="utf-8")


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
    line = '      <file href="pg016_sec001.html"/>\n'
    if source.count(line) != 1:
        raise ValueError("Could not uniquely locate pg016_sec001.html in imsmanifest.xml")
    path.write_text(source.replace(line, "", 1), encoding="utf-8")


def main() -> None:
    merge_content()
    pages = update_spine()
    renumber_pages(pages)
    update_manifest()
    if SOURCE_FILE.is_file():
        SOURCE_FILE.unlink()
    print(f"Joined reader pages 19 and 20; spine now contains {len(pages)} pages.")


if __name__ == "__main__":
    main()
