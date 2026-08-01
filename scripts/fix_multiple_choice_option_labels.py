#!/usr/bin/env python3
"""Remove redundant numeric markers from every lettered multiple-choice option."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECTION_MARKER = 'data-section-type="activity_multiple_choice"'
LABEL_PATTERN = re.compile(
    r'(?P<open><label\b[^>]*class="[^"]*\bactivity-option\b[^"]*"[^>]*>)'
    r'(?P<body>.*?)'
    r'(?P<close></label>)',
    re.DOTALL,
)
LETTER_PATTERN = re.compile(r'\(([a-d])\)', re.IGNORECASE)
NESTED_NUMBER_PATTERN = re.compile(
    r'\n[ \t]*<div class="[^"]*\bflex-shrink-0\b[^"]*">\s*'
    r'<div class="[^"]*(?:\boption-letter\b|\brounded-full\b)[^"]*">\s*[1-9][0-9]*\s*</div>\s*'
    r'</div>',
    re.DOTALL,
)
DIRECT_NUMBER_PATTERN = re.compile(
    r'\n[ \t]*<div class="[^"]*(?:\boption-letter\b|\brounded-full\b)[^"]*">\s*[1-9][0-9]*\s*</div>'
)
NUMERIC_ARIA_OPTION_PATTERN = re.compile(r'\b(option)\s+[1-4]\b', re.IGNORECASE)


def remove_gap_classes(open_tag: str) -> str:
    return re.sub(r'\s+(?:gap-4|max-sm:gap-3)', '', open_tag)


def lettered_aria(match: re.Match[str], letter: str) -> str:
    word = match.group(1)
    return f"{word} {letter.upper()}"


def fix_label(match: re.Match[str]) -> tuple[str, int, int]:
    open_tag = match.group("open")
    body = match.group("body")
    close_tag = match.group("close")
    letter_match = LETTER_PATTERN.search(body)
    if not letter_match:
        return match.group(0), 0, 0

    letter = letter_match.group(1)
    body, nested_count = NESTED_NUMBER_PATTERN.subn("", body)
    body, direct_count = DIRECT_NUMBER_PATTERN.subn("", body)
    marker_count = nested_count + direct_count
    if marker_count:
        open_tag = remove_gap_classes(open_tag)

    body, aria_count = NUMERIC_ARIA_OPTION_PATTERN.subn(
        lambda aria_match: lettered_aria(aria_match, letter), body
    )
    return open_tag + body + close_tag, marker_count, aria_count


def fix_file(path: Path) -> tuple[int, int]:
    source = path.read_text(encoding="utf-8")
    if SECTION_MARKER not in source:
        return 0, 0

    marker_total = 0
    aria_total = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal marker_total, aria_total
        updated, markers, aria_labels = fix_label(match)
        marker_total += markers
        aria_total += aria_labels
        return updated

    updated = LABEL_PATTERN.sub(replace, source)
    path.write_text(updated, encoding="utf-8")
    return marker_total, aria_total


def audit() -> None:
    failures: list[str] = []
    for path in sorted(ROOT.glob("*.html")):
        source = path.read_text(encoding="utf-8")
        if SECTION_MARKER not in source:
            continue
        for label in LABEL_PATTERN.finditer(source):
            body = label.group("body")
            if not LETTER_PATTERN.search(body):
                continue
            if NESTED_NUMBER_PATTERN.search(body) or DIRECT_NUMBER_PATTERN.search(body):
                failures.append(f"{path.name}: visible numeric option marker remains")
            if NUMERIC_ARIA_OPTION_PATTERN.search(body):
                failures.append(f"{path.name}: numeric option remains in aria-label")
    if failures:
        raise ValueError("\n".join(sorted(set(failures))))


def main() -> None:
    changed_files = 0
    marker_total = 0
    aria_total = 0
    for path in sorted(ROOT.glob("*.html")):
        markers, aria_labels = fix_file(path)
        if markers or aria_labels:
            changed_files += 1
            marker_total += markers
            aria_total += aria_labels
            print(f"{path.name}: removed {markers} markers; updated {aria_labels} aria labels")
    audit()
    print(
        f"Fixed {changed_files} multiple-choice files: removed {marker_total} numeric markers "
        f"and updated {aria_total} accessibility labels."
    )


if __name__ == "__main__":
    main()
