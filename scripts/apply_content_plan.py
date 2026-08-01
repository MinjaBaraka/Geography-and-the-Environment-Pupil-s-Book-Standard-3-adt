#!/usr/bin/env python3
"""Apply matrix content, inclusivity, deduplication, and watermark corrections."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"

TEXT_CHANGES = {
    "pg003_n0005": "Acknowledgements",
    "pg003_n0007": "Introduction",
    "pg003_n0009": "Chapter One",
    "pg003_n0011": "The concepts of Geography and the Environment",
    "pg003_n0013": "Chapter Two",
    "pg003_n0015": "Earth’s relief",
    "pg003_n0017": "Chapter Three",
    "pg003_n0019": "Environmental conservation",
    "pg003_n0021": "Chapter Four",
    "pg003_n0023": "Environmental degradation",
    "pg003_n0025": "Bibliography",
    "pg011_n0003": "Listen to the audio description of Figure 4 or observe Figure 4, then answer the questions that follow.",
    "pg011_n0007": "1. What are the things found in the school environment?",
    "pg011_n0008": "2. What essential things, if removed from the school environment presented in Figure 4, would affect that environment? Give reasons.",
    "pg012_n0005": "Listen to the audio descriptions of Figure 5 or observe Figure 5, then answer the questions that follow.",
    "pg012_n0014": "1. What are the things found in the home environment?",
    "pg013_n0016": "2. Identify the things you observed.",
    "pg021_n0014": "Various features of the earth’s relief you have observed",
    "pg022_n0011": "Search for video or audio resources on the earth’s major relief features in Tanzania on the Internet.",
    "pg022_n0012": "Listen to or watch the resources you have found, and then explain your findings.",
    "pg049_n0009": "Observe online sources, books and newsletters about how to maintain clean air in the environment.",
    "pg079_n0017": "1. What do you observe in Figure 13?",
    "pg079_n0019": "2. What do you think caused what you observed in Figure 13?",
}

WATERMARK_IDS = {
    "pg003_n0029", "pg005_n0008", "pg015_n0028", "pg024_n0024",
    "pg028_n0001", "pg030_n0021", "pg056_n0001", "pg063_n0045",
    "pg066_n0022", "pg072_n0067", "pg086_n0049", "pg087_n0073",
}

WATERMARK_FILES = {
    "pg003_sec001.html": "pg003_n0029",
    "pg005_sec001.html": "pg005_n0008",
    "pg015_sec002.html": "pg015_n0028",
    "pg024_sec002.html": "pg024_n0024",
    "pg028_sec001.html": "pg028_n0001",
    "pg030_sec001.html": "pg030_n0021",
    "pg056_sec001.html": "pg056_n0001",
    "pg063_sec001.html": "pg063_n0045",
    "pg066_sec001.html": "pg066_n0022",
    "pg072_sec001.html": "pg072_n0067",
    "pg086_sec002.html": "pg086_n0049",
    "pg087_sec001.html": "pg087_n0073",
}


def replace(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    if old in source:
        path.write_text(source.replace(old, new, 1), encoding="utf-8")
    elif new not in source:
        raise ValueError(f"Expected content not found in {path.name}: {old[:80]!r}")


def regex_replace(path: Path, pattern: str, replacement: str) -> None:
    source = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.DOTALL)
    if count:
        path.write_text(updated, encoding="utf-8")
    elif not re.search(re.escape(replacement), source, flags=re.DOTALL):
        raise ValueError(f"Expected pattern not found in {path.name}: {pattern[:80]!r}")


def update_inline_content() -> None:
    page12 = ROOT / "pg012_sec001.html"
    replace(page12, "Observe Figure 5 and answer the questions that follow:", TEXT_CHANGES["pg012_n0005"])
    replace(page12, "1. What do you see in Figure 5?", TEXT_CHANGES["pg012_n0014"])
    replace(page12, "Answer to question 1 about what is seen in Figure 5", "Answer about things found in the home environment")

    page21 = ROOT / "pg021_sec001.html"
    regex_replace(
        page21,
        r'<div class="mt-8 max-sm:mt-6"><img data-id="pg021_im005".*?<div data-id="pg021_n0014" class="sr-only">.*?</div></div>',
        '<div class="mt-8 overflow-hidden rounded-[1.75rem] border-[3px] border-cyan-400 bg-pink-50 shadow-md max-sm:mt-6"><div class="flex items-center bg-gradient-to-r from-sky-700 via-lime-100 to-cyan-200 px-4 py-1.5"><div data-id="pg021_n0013" class="adt-h3 rounded-xl bg-sky-700 px-6 py-1 font-bold text-white shadow">Think</div></div><div class="flex items-center gap-4 px-5 py-4"><img src="images/pg054_im001.png" alt="" class="h-24 w-auto shrink-0" role="presentation" aria-hidden="true"><p data-id="pg021_n0014" class="adt-body leading-relaxed">Various features of the earth’s relief you have observed</p></div></div>',
    )

    dedup_patterns = {
        "pg013_sec002.html": r'<div class="mb-6 flex justify-center"><img src="images/pg013_im003\.png".*?</div>',
        "pg038_sec001.html": r'<div class="bg-amber-50/60 rounded-2xl p-4 max-sm:p-3 mb-8"><img src="images/pg038_im002\.png".*?</div>',
        "pg047_sec002.html": r'<div class="mb-6"><img src="images/pg047_im003\.png".*?</div>',
    }
    for filename, pattern in dedup_patterns.items():
        path = ROOT / filename
        source = path.read_text(encoding="utf-8")
        updated, count = re.subn(pattern, "", source, count=1, flags=re.DOTALL)
        if count:
            path.write_text(updated, encoding="utf-8")
        elif re.search(r"pg(?:013_im003|038_im002|047_im003)", source):
            raise ValueError(f"Could not remove duplicated exercise graphic from {filename}")

    page32 = ROOT / "pg032_sec002.html"
    regex_replace(page32, r'\s*<div class="mb-8">\s*<img src="images/pg032_im002\.png".*?</div>', "")
    regex_replace(
        page32,
        r'<div class="sr-only">\s*<span data-id="pg032_n0006">Exercise 2</span>\s*</div>',
        '<h1 class="adt-h2 mb-6 font-bold text-amber-700"><span data-id="pg032_n0006">Exercise 2</span></h1>',
    )

    page38 = ROOT / "pg038_sec002.html"
    regex_replace(
        page38,
        r'\s*<p class="adt-body leading-relaxed text-neutral-800"><span data-id="pg038_n0016">.*?</span></p>',
        "",
    )

    page55 = ROOT / "pg055_sec001.html"
    regex_replace(
        page55,
        r'<div class="sr-only" data-id="pg055_n0003">Activity 1</div><div class="mb-12 rounded-3xl.*?</div>',
        '<div class="mb-8 overflow-hidden rounded-[1.75rem] border border-orange-200 bg-orange-50 shadow-sm"><div class="flex items-center gap-4 bg-gradient-to-r from-orange-700 via-orange-600 to-pink-500 px-5 py-3 text-white"><i class="fa-solid fa-pen-to-square text-3xl" aria-hidden="true"></i><h1 data-id="pg055_n0003" class="adt-h2 font-bold">Activity 1</h1></div></div>',
    )

    toc = ROOT / "pg003_sec001.html"
    for data_id, value in {key: value for key, value in TEXT_CHANGES.items() if key.startswith("pg003_")}.items():
        source = toc.read_text(encoding="utf-8")
        pattern = rf'(<span data-id="{re.escape(data_id)}"[^>]*>).*?(</span>)'
        updated, count = re.subn(pattern, rf"\g<1>{value}\g<2>", source, count=1, flags=re.DOTALL)
        if count:
            toc.write_text(updated, encoding="utf-8")
        elif value not in source:
            raise ValueError(f"Could not update TOC value {data_id}")

    replace(ROOT / "pg002_sec001.html", "without prior written permission", "without a prior written permission")
    replace(
        ROOT / "pg004_sec001.html",
        "who participated in designing and developing this textbook.",
        "who participated in the designing and development of this textbook.",
    )


def remove_watermarks() -> None:
    for filename, data_id in WATERMARK_FILES.items():
        path = ROOT / filename
        source = path.read_text(encoding="utf-8")
        pattern = rf'<(?P<tag>div|p|span)\b[^>]*data-id="{re.escape(data_id)}"[^>]*>.*?</(?P=tag)>'
        updated, count = re.subn(pattern, "", source, count=1, flags=re.DOTALL)
        if count:
            path.write_text(updated, encoding="utf-8")
        elif data_id in source:
            raise ValueError(f"Could not remove watermark node {data_id} from {filename}")


def update_localization() -> None:
    texts_path = I18N / "texts.json"
    texts = json.loads(texts_path.read_text(encoding="utf-8"))
    for key, value in TEXT_CHANGES.items():
        texts[key] = value
        texts[f"{key}_easy_read"] = value
    for key in WATERMARK_IDS:
        texts.pop(key, None)
        texts.pop(f"{key}_easy_read", None)
    texts_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    for key in WATERMARK_IDS:
        audios.pop(key, None)
        audios.pop(f"{key}_easy_read", None)
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    update_inline_content()
    remove_watermarks()
    update_localization()
    print("Content plan applied.")


if __name__ == "__main__":
    main()
