#!/usr/bin/env python3
"""Remove the printed-book footer blocks from all reader pages."""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# These paired, empty data IDs were generated for the left and right sides of
# the original printed footer. Their nearest shared wrapper is the footer.
FOOTER_ID_PAIRS = (
    ("pg003_n0027", "pg003_n0028"),
    ("pg005_n0010", "pg005_n0011"),
    ("pg006_n0016", "pg006_n0017"),
    ("pg007_n0023", "pg007_n0024"),
    ("pg008_n0023", "pg008_n0024"),
    ("pg009_n0038", "pg009_n0039"),
    ("pg010_n0017", "pg010_n0018"),
    ("pg015_n0030", "pg015_n0031"),
    ("pg019_n0044", "pg019_n0045"),
    ("pg020_n0016", "pg020_n0017"),
    ("pg021_n0024", "pg021_n0025"),
    ("pg023_n0024", "pg023_n0025"),
    ("pg024_n0022", "pg024_n0023"),
    ("pg025_n0018", "pg025_n0019"),
    ("pg026_n0019", "pg026_n0020"),
    ("pg028_n0017", "pg028_n0018"),
    ("pg029_n0019", "pg029_n0020"),
    ("pg030_n0022", "pg030_n0023"),
    ("pg031_n0018", "pg031_n0019"),
    ("pg032_n0035", "pg032_n0036"),
    ("pg034_n0024", "pg034_n0025"),
    ("pg037_n0018", "pg037_n0019"),
    ("pg038_n0029", "pg038_n0030"),
    ("pg040_n0038", "pg040_n0039"),
    ("pg044_n0029", "pg044_n0030"),
    ("pg045_n0013", "pg045_n0014"),
    ("pg048_n0014", "pg048_n0015"),
    ("pg050_n0026", "pg050_n0027"),
    ("pg051_n0028", "pg051_n0029"),
    ("pg053_n0037", "pg053_n0038"),
    ("pg054_n0021", "pg054_n0022"),
    ("pg056_n0013", "pg056_n0014"),
    ("pg057_n0017", "pg057_n0018"),
    ("pg058_n0014", "pg058_n0015"),
    ("pg059_n0022", "pg059_n0023"),
    ("pg061_n0018", "pg061_n0019"),
    ("pg062_n0016", "pg062_n0017"),
    ("pg063_n0043", "pg063_n0044"),
    ("pg064_n0057", "pg064_n0058"),
    ("pg065_n0014", "pg065_n0015"),
    ("pg066_n0024", "pg066_n0025"),
    ("pg068_n0011", "pg068_n0012"),
    ("pg069_n0026", "pg069_n0027"),
    ("pg070_n0019", "pg070_n0021"),
    ("pg072_n0077", "pg072_n0078"),
    ("pg073_n0018", "pg073_n0019"),
    ("pg074_n0023", "pg074_n0024"),
    ("pg075_n0027", "pg075_n0028"),
    ("pg076_n0017", "pg076_n0018"),
    ("pg077_n0017", "pg077_n0018"),
    ("pg081_n0016", "pg081_n0017"),
    ("pg084_n0029", "pg084_n0030"),
    ("pg085_n0050", "pg085_n0051"),
    ("pg087_n0071", "pg087_n0072"),
)


@dataclass(eq=False)
class Node:
    tag: str
    attrs: dict[str, str | None]
    start: int
    end: int | None = None
    parent: "Node | None" = None
    children: list["Node"] = field(default_factory=list)


class PositionParser(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=False)
        self.source = source
        self.line_starts = [0]
        for match in re.finditer("\n", source):
            self.line_starts.append(match.end())
        self.roots: list[Node] = []
        self.stack: list[Node] = []
        self.by_data_id: dict[str, Node] = {}

    def absolute_position(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def add_node(self, tag: str, attrs: list[tuple[str, str | None]], end: int | None) -> Node:
        start = self.absolute_position()
        values = dict(attrs)
        parent = self.stack[-1] if self.stack else None
        node = Node(tag.lower(), values, start, end=end, parent=parent)
        if parent:
            parent.children.append(node)
        else:
            self.roots.append(node)
        data_id = values.get("data-id")
        if data_id:
            self.by_data_id[data_id] = node
        return node

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self.absolute_position()
        end = start + len(self.get_starttag_text())
        node = self.add_node(tag, attrs, end if tag.lower() in VOID_TAGS else None)
        if tag.lower() not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self.absolute_position()
        self.add_node(tag, attrs, start + len(self.get_starttag_text()))

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        position = self.absolute_position()
        close = self.source.find(">", position)
        end = len(self.source) if close < 0 else close + 1
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag.lower():
                node = self.stack[index]
                node.end = end
                del self.stack[index:]
                return


def descendants(node: Node):
    yield node
    for child in node.children:
        yield from descendants(child)


def data_ids(node: Node) -> set[str]:
    return {item.attrs["data-id"] for item in descendants(node) if item.attrs.get("data-id")}


def lowest_common_ancestor(first: Node, second: Node) -> Node:
    second_ancestors: set[Node] = set()
    cursor: Node | None = second
    while cursor:
        second_ancestors.add(cursor)
        cursor = cursor.parent
    cursor = first
    while cursor not in second_ancestors:
        if cursor.parent is None:
            raise ValueError("Could not find a shared footer ancestor")
        cursor = cursor.parent
    return cursor


def printed_page_seven_range(parser: PositionParser, source: str) -> tuple[int, int] | None:
    """Find the decorative footer whose only visible content is printed page 7."""
    for root in parser.roots:
        for node in descendants(root):
            if node.tag != "section":
                continue
            for child in node.children:
                if child.end is None or "relative h-28" not in (child.attrs.get("class") or ""):
                    continue
                fragment = source[child.start:child.end]
                text = html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()
                if text == "7":
                    return child.start, child.end
    return None


def ranges_for_file(path: Path, pairs: list[tuple[str, str]]) -> list[tuple[int, int]]:
    source = path.read_text(encoding="utf-8")
    parser = PositionParser(source)
    parser.feed(source)
    ranges: list[tuple[int, int]] = []

    for first_id, second_id in pairs:
        first = parser.by_data_id.get(first_id)
        second = parser.by_data_id.get(second_id)
        if first is None and second is None:
            continue
        if first is None or second is None:
            raise ValueError(f"Only one footer ID from {first_id}, {second_id} remains in {path.name}")

        pair = {first_id, second_id}
        common = lowest_common_ancestor(first, second)
        if data_ids(common) == pair:
            candidate = common
            while (
                candidate.parent
                and candidate.parent.tag not in {"section", "body", "html"}
                and data_ids(candidate.parent) == pair
            ):
                candidate = candidate.parent
            if candidate.end is None:
                raise ValueError(f"Unclosed footer wrapper in {path.name}")
            ranges.append((candidate.start, candidate.end))
        else:
            # On page 24 the two empty footer placeholders are direct siblings
            # of real content, so only the placeholders themselves are removed.
            for node in (first, second):
                if node.end is None:
                    raise ValueError(f"Unclosed footer placeholder in {path.name}")
                ranges.append((node.start, node.end))

    if path.name == "pg013_sec004.html":
        page_seven = printed_page_seven_range(parser, source)
        if page_seven:
            ranges.append(page_seven)

    return sorted(set(ranges))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    pairs_by_file: dict[Path, list[tuple[str, str]]] = {}
    html_files = list(ROOT.glob("*.html"))
    for pair in FOOTER_ID_PAIRS:
        matches = [path for path in html_files if all(f'data-id="{item}"' in path.read_text(encoding="utf-8") for item in pair)]
        if len(matches) > 1:
            raise ValueError(f"Footer pair {pair} appears in multiple files")
        if matches:
            pairs_by_file.setdefault(matches[0], []).append(pair)

    changed_files = 0
    removed_blocks = 0
    candidates = set(pairs_by_file)
    candidates.add(ROOT / "pg013_sec004.html")
    for path in sorted(candidates):
        source = path.read_text(encoding="utf-8")
        ranges = ranges_for_file(path, pairs_by_file.get(path, []))
        if not ranges:
            continue
        for start, end in sorted(ranges, reverse=True):
            source = source[:start] + source[end:]
        changed_files += 1
        removed_blocks += len(ranges)
        if not args.dry_run:
            path.write_text(source, encoding="utf-8")

    action = "Would remove" if args.dry_run else "Removed"
    print(f"{action} {removed_blocks} printed footer blocks from {changed_files} pages.")


if __name__ == "__main__":
    main()
