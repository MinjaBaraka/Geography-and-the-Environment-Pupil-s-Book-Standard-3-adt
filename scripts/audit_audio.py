#!/usr/bin/env python3
"""Deep-audit all narration mappings and MP3 files used by the ADT."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from validate_adt import I18N, ROOT, parse_page, read_json


AUDIO_DIR = I18N / "audio"
ROMAN_RE = re.compile(r"^\s*\(([ivxl]+)\)\s*$", re.IGNORECASE)
SPACE_RE = re.compile(r"\s+")

BITRATES = {
    (1, 1): [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0],
    (1, 2): [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, 0],
    (1, 3): [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 0],
    (2, 1): [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0],
    (2, 2): [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0],
    (2, 3): [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, 0],
}
BASE_SAMPLE_RATES = [44100, 48000, 32000]


@dataclass
class Mp3Info:
    duration: float
    frames: int
    audio_bytes: int
    junk_bytes: int


def normalize_text(value: object) -> str:
    return SPACE_RE.sub(" ", str(value)).strip()


def parse_mp3(path: Path) -> Mp3Info:
    data = path.read_bytes()
    position = 0
    duration = 0.0
    frames = 0
    audio_bytes = 0
    junk_bytes = 0

    if data.startswith(b"ID3") and len(data) >= 10:
        tag_size = (
            ((data[6] & 0x7F) << 21)
            | ((data[7] & 0x7F) << 14)
            | ((data[8] & 0x7F) << 7)
            | (data[9] & 0x7F)
        )
        position = 10 + tag_size
        junk_bytes = position

    while position + 4 <= len(data):
        header = int.from_bytes(data[position : position + 4], "big")
        if (header >> 21) & 0x7FF != 0x7FF:
            position += 1
            junk_bytes += 1
            continue

        version_bits = (header >> 19) & 0x3
        layer_bits = (header >> 17) & 0x3
        bitrate_index = (header >> 12) & 0xF
        sample_index = (header >> 10) & 0x3
        padding = (header >> 9) & 0x1
        if version_bits == 1 or layer_bits == 0 or sample_index == 3:
            position += 1
            junk_bytes += 1
            continue

        version = 1 if version_bits == 3 else 2
        layer = 4 - layer_bits
        bitrate = BITRATES[(version, layer)][bitrate_index]
        if bitrate == 0:
            position += 1
            junk_bytes += 1
            continue

        sample_rate = BASE_SAMPLE_RATES[sample_index]
        if version_bits == 2:
            sample_rate //= 2
        elif version_bits == 0:
            sample_rate //= 4

        if layer == 1:
            frame_length = ((12 * bitrate * 1000 // sample_rate) + padding) * 4
            samples = 384
        elif layer == 2:
            frame_length = (144 * bitrate * 1000 // sample_rate) + padding
            samples = 1152
        else:
            coefficient = 144 if version == 1 else 72
            frame_length = (coefficient * bitrate * 1000 // sample_rate) + padding
            samples = 1152 if version == 1 else 576

        if frame_length <= 4 or position + frame_length > len(data):
            position += 1
            junk_bytes += 1
            continue

        frames += 1
        duration += samples / sample_rate
        audio_bytes += frame_length
        position += frame_length

    if frames == 0:
        raise ValueError("contains no decodable MPEG audio frames")
    return Mp3Info(duration=duration, frames=frames, audio_bytes=audio_bytes, junk_bytes=junk_bytes)


def collect_required_audio(pages: list[dict]) -> tuple[set[str], set[str], set[str], dict[str, set[str]]]:
    used_ids: set[str] = set()
    used_image_ids: set[str] = set()
    ignored_ids: set[str] = set()
    pages_by_id: dict[str, set[str]] = defaultdict(set)
    for position, entry in enumerate(pages, 1):
        page = parse_page(ROOT / entry["href"])
        for data_id in page.data_ids:
            used_ids.add(data_id)
            pages_by_id[data_id].add(str(position))
        used_image_ids.update(image.get("data-id", "") for image in page.images if image.get("data-id"))
        ignored_ids.update(page.tts_ignored_ids)
    return used_ids, used_image_ids, ignored_ids, pages_by_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-duration", action="store_true")
    args = parser.parse_args()

    pages = read_json(ROOT / "content" / "pages.json")
    texts = read_json(I18N / "texts.json")
    audios = read_json(I18N / "audios.json")
    used_ids, used_image_ids, ignored_ids, pages_by_id = collect_required_audio(pages)
    required_ids = {
        key
        for data_id in used_ids - used_image_ids - ignored_ids
        for key in (data_id, f"{data_id}_easy_read")
        if key in texts
    }

    errors: list[str] = []
    warnings: list[str] = []

    missing_mappings = sorted(required_ids - set(audios))
    for key in missing_mappings:
        errors.append(f"missing mapping: {key} (page {','.join(sorted(pages_by_id.get(key.removesuffix('_easy_read'), set())))})")

    mapped_files = set(audios.values())
    disk_files = {path.name for path in AUDIO_DIR.glob("*.mp3")}
    for filename in sorted(mapped_files - disk_files):
        errors.append(f"mapped file is missing: {filename}")
    for filename in sorted(disk_files - mapped_files):
        warnings.append(f"unmapped MP3: {filename}")

    for key in sorted(required_ids):
        if not normalize_text(texts.get(key, "")):
            errors.append(f"spoken ID has empty text: {key}")

    files_to_keys: dict[str, list[str]] = defaultdict(list)
    for key, filename in audios.items():
        files_to_keys[filename].append(key)
        if key not in texts:
            errors.append(f"audio mapping has no text entry: {key}")

    for filename, keys in sorted(files_to_keys.items()):
        values = {normalize_text(texts.get(key, "")).casefold() for key in keys}
        if len(values) > 1:
            errors.append(f"{filename} is shared by different text: {keys}")

    infos: dict[str, Mp3Info] = {}
    hashes: dict[str, list[str]] = defaultdict(list)
    for filename in sorted(mapped_files & disk_files):
        path = AUDIO_DIR / filename
        try:
            info = parse_mp3(path)
            infos[filename] = info
        except Exception as error:
            errors.append(f"invalid MP3 {filename}: {error}")
            continue
        if not math.isfinite(info.duration) or info.duration <= 0:
            errors.append(f"invalid duration for {filename}: {info.duration}")
        if info.junk_bytes > max(1024, int(path.stat().st_size * 0.02)):
            errors.append(f"excess non-audio data in {filename}: {info.junk_bytes} bytes")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[digest].append(filename)

    for filenames in hashes.values():
        if len(filenames) < 2:
            continue
        values: set[str] = set()
        keys: list[str] = []
        for filename in filenames:
            for key in files_to_keys[filename]:
                keys.append(key)
                values.add(normalize_text(texts.get(key, "")).casefold())
        if len(values) > 1:
            errors.append(f"byte-identical MP3s contain different text: {filenames} ({keys})")

    duration_outliers: list[str] = []
    required_files = {audios[key] for key in required_ids if key in audios}
    for filename in sorted(required_files & set(infos)):
        keys = [key for key in files_to_keys[filename] if key in required_ids]
        if not keys:
            continue
        text = normalize_text(texts[keys[0]])
        duration = infos[filename].duration
        characters_per_second = len(text) / duration
        # Synthetic speech varies considerably by punctuation and prosody. These
        # bounds deliberately flag only clips that are effectively silent or
        # truncated, rather than reporting normal variation in speaking rate.
        if len(text) >= 12 and (characters_per_second < 2.0 or characters_per_second > 80.0):
            duration_outliers.append(
                f"{filename}: {characters_per_second:.1f} chars/s, {duration:.2f}s, text={text[:90]!r}"
            )
    if duration_outliers:
        target = errors if args.strict_duration else warnings
        target.extend(f"duration outlier: {message}" for message in duration_outliers)

    roman_ids = {
        key
        for key, value in texts.items()
        if not key.endswith("_easy_read") and ROMAN_RE.fullmatch(str(value)) and key in used_ids
    }
    for key in sorted(roman_ids):
        filename = audios.get(key, "")
        if not filename.startswith("roman_"):
            errors.append(f"Roman numeral {key} does not use contextual narration: {filename}")

    image_hook_ids = {data_id for data_id in used_ids if data_id.endswith("_audio_description")}
    for key in sorted(image_hook_ids):
        if key not in audios:
            errors.append(f"image description lacks narration: {key}")

    total_duration = sum(infos[filename].duration for filename in required_files if filename in infos)
    print(
        "Audio summary: "
        f"{len(pages)} pages, {len(required_ids)} required narration IDs, "
        f"{len(required_files)} required MP3s, {len(infos)} total decoded MP3s, "
        f"{total_duration / 60:.1f} required audio minutes, "
        f"{len(image_hook_ids)} image descriptions, {len(roman_ids)} Roman-numeral labels."
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAILED with {len(errors)} error(s) and {len(warnings)} warning(s).")
        return 1
    print(f"PASS with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
