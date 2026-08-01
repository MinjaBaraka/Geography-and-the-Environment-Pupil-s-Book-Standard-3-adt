#!/usr/bin/env python3
"""Validate the ADT spine, page metadata, localization, media, and offline payload."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"
QUIZ_RE = re.compile(r"^qz\d{3}")
WATERMARK = "FOR ONLINE READING ONLY"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.section_ids: list[str] = []
        self.data_ids: list[str] = []
        self.tts_ignored_ids: list[str] = []
        self.images: list[dict[str, str]] = []
        self.audio_description_hooks: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag == "meta" and values.get("name"):
            self.meta[values["name"]] = values.get("content", "")
        if tag == "section" and values.get("data-section-id"):
            self.section_ids.append(values["data-section-id"])
        if values.get("data-id"):
            self.data_ids.append(values["data-id"])
            if values.get("data-tts-ignore") == "true":
                self.tts_ignored_ids.append(values["data-id"])
        if values.get("data-audio-description-for"):
            self.audio_description_hooks[values["data-audio-description-for"]] = values.get(
                "data-id", ""
            )
        if tag == "img":
            self.images.append(values)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def load_inline_payload():
    source = (ROOT / "assets" / "offline-preloader.js").read_text(encoding="utf-8")
    marker = "  var INLINE = "
    start = source.index(marker) + len(marker)
    payload, _ = json.JSONDecoder().raw_decode(source[start:])
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-offline", action="store_true")
    parser.add_argument("--require-matrix-clean", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    pages = read_json(ROOT / "content" / "pages.json")
    toc = read_json(ROOT / "content" / "toc.json")
    texts = read_json(I18N / "texts.json")
    audios = read_json(I18N / "audios.json")

    hrefs = [entry.get("href", "") for entry in pages]
    section_ids = [entry.get("section_id", "") for entry in pages]
    for label, values in (("href", hrefs), ("section_id", section_ids)):
        duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
        if duplicates:
            errors.append(f"Duplicate page {label}s: {duplicates}")

    used_ids: set[str] = set()
    used_image_ids: set[str] = set()
    tts_ignored_ids: set[str] = set()
    parsed_pages: dict[str, PageParser] = {}
    for position, entry in enumerate(pages, 1):
        href = entry["href"]
        path = ROOT / href
        if not path.is_file():
            errors.append(f"Spine entry {position} is missing: {href}")
            continue
        page = parse_page(path)
        parsed_pages[href] = page
        if page.meta.get("title-id") != entry["section_id"]:
            errors.append(
                f"{href}: title-id {page.meta.get('title-id')!r} != {entry['section_id']!r}"
            )
        if page.meta.get("page-section-id") != str(position):
            errors.append(
                f"{href}: page-section-id {page.meta.get('page-section-id')!r} != {position}"
            )
        if entry["section_id"] not in page.section_ids:
            errors.append(f"{href}: section data-section-id does not include {entry['section_id']}")
        used_ids.update(page.data_ids)
        tts_ignored_ids.update(page.tts_ignored_ids)

        for image in page.images:
            source = image.get("src", "")
            if source and not (ROOT / source).is_file():
                errors.append(f"{href}: missing image {source}")
            image_id = image.get("data-id", "")
            decorative = image.get("role") == "presentation" or image.get("aria-hidden") == "true"
            if image_id:
                used_image_ids.add(image_id)
            if not decorative:
                description = texts.get(image_id, image.get("alt", "")).strip()
                if not description:
                    errors.append(f"{href}: non-decorative image {image_id or source} lacks a description")
                if image_id:
                    hook_id = page.audio_description_hooks.get(image_id, "")
                    expected_hook = f"{image_id}_audio_description"
                    if hook_id != expected_hook:
                        errors.append(
                            f"{href}: image {image_id} lacks its {expected_hook} audio-description hook"
                        )
                    elif hook_id not in audios:
                        errors.append(f"{href}: image description {hook_id} lacks audio mapping")

    missing_texts = sorted(data_id for data_id in used_ids if data_id not in texts)
    if missing_texts:
        errors.append(f"{len(missing_texts)} used data IDs are missing from texts.json: {missing_texts[:12]}")

    required_audio_ids = {
        key
        for data_id in used_ids - used_image_ids - tts_ignored_ids
        for key in (data_id, f"{data_id}_easy_read")
        if key in texts
    }
    missing_audio_mappings = sorted(required_audio_ids - set(audios))
    if missing_audio_mappings:
        errors.append(
            f"{len(missing_audio_mappings)} used localization entries lack audio mappings: "
            f"{missing_audio_mappings[:12]}"
        )

    ignored_audio_mappings = sorted(tts_ignored_ids & set(audios))
    if ignored_audio_mappings:
        errors.append(
            f"{len(ignored_audio_mappings)} narration-excluded entries still have audio mappings: "
            f"{ignored_audio_mappings[:12]}"
        )

    for data_id in sorted(required_audio_ids & set(audios)):
        audio_path = I18N / "audio" / audios[data_id]
        if not audio_path.is_file():
            errors.append(f"Missing audio file for {data_id}: {audios[data_id]}")

    page_sections = set(section_ids)
    for item in toc:
        if item.get("section_id") not in page_sections:
            errors.append(f"TOC section is not in pages.json: {item.get('section_id')}")
        if item.get("href") not in hrefs:
            errors.append(f"TOC href is not in pages.json: {item.get('href')}")
        chapter_id = item.get("chapter_id")
        if chapter_id and chapter_id not in texts:
            errors.append(f"TOC chapter_id is missing from texts.json: {chapter_id}")

    manifest = ET.parse(ROOT / "imsmanifest.xml")
    manifest_hrefs = {
        node.attrib["href"]
        for node in manifest.iter()
        if node.tag.endswith("file") and "href" in node.attrib
    }
    for href in hrefs:
        if href not in manifest_hrefs:
            errors.append(f"Manifest does not package spine page: {href}")

    watermark_files = sorted(
        path.name for path in ROOT.glob("*.html") if WATERMARK in path.read_text(encoding="utf-8")
    )
    quiz_files = sorted(path.name for path in ROOT.glob("qz*.html"))
    quiz_spine = sorted(href for href in hrefs if QUIZ_RE.match(Path(href).stem))

    if args.require_matrix_clean:
        if watermark_files:
            errors.append(f"Watermark text remains in: {watermark_files}")
        if quiz_files or quiz_spine:
            errors.append(f"Quiz content remains (files={quiz_files}, spine={quiz_spine})")
        quiz_text_keys = sorted(key for key in texts if QUIZ_RE.match(key))
        quiz_audio_keys = sorted(key for key in audios if QUIZ_RE.match(key))
        if quiz_text_keys or quiz_audio_keys:
            errors.append(
                f"Quiz localization remains (text={len(quiz_text_keys)}, audio={len(quiz_audio_keys)})"
            )
        scorm = (ROOT / "assets" / "scorm.js").read_text(encoding="utf-8")
        if re.search(r"\bqz\d{3}\b", scorm):
            errors.append("Quiz IDs remain in assets/scorm.js")
    elif watermark_files:
        warnings.append(f"Watermark text remains in {len(watermark_files)} HTML files")

    if args.check_offline:
        payload = load_inline_payload()
        expected_keys = {
            "./assets/config.json",
            "./content/pages.json",
            "./content/toc.json",
            "./content/navigation/nav.html",
            *{f"./{href}" for href in hrefs},
            "./assets/interface_translations/en-GB/interface_translations.json",
            "./content/i18n/en-GB/texts.json",
            "./content/i18n/en-GB/audios.json",
            "./content/i18n/en-GB/videos.json",
            "./content/i18n/en-GB/images.json",
            "./content/i18n/en-GB/glossary.json",
            "./content/i18n/en-GB/timecode/timecode_output.json",
        }
        payload_keys = set(payload)
        if payload_keys != expected_keys:
            errors.append(
                f"Offline payload key mismatch: missing={sorted(expected_keys-payload_keys)}, "
                f"extra={sorted(payload_keys-expected_keys)}"
            )
        for key in sorted(expected_keys & payload_keys):
            path = ROOT / key[2:]
            actual = read_json(path) if path.suffix == ".json" else path.read_text(encoding="utf-8")
            if payload[key] != actual:
                errors.append(f"Offline payload is stale: {key}")

    print(
        f"ADT summary: {len(pages)} spine entries, {len(used_ids)} used data IDs, "
        f"{len(used_image_ids)} described images."
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAILED with {len(errors)} error(s).")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
