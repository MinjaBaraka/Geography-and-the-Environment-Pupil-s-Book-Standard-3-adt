#!/usr/bin/env python3
"""Verify every reader page and narration clip is served by the local site."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en-GB"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check(base_url: str, resource: str, expected_type: str, timeout: float) -> str | None:
    url = f"{base_url.rstrip('/')}/{resource.lstrip('./')}"
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                return f"{resource}: HTTP {response.status}"
            length = response.headers.get("Content-Length")
            if length is not None and int(length) <= 0:
                return f"{resource}: empty response"
            content_type = response.headers.get_content_type()
            if content_type != expected_type:
                return f"{resource}: expected {expected_type}, received {content_type}"
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return f"{resource}: {error}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5500")
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    pages = load_json(ROOT / "content" / "pages.json")
    audios = load_json(I18N / "audios.json")
    page_files = sorted({str(entry["href"]).removeprefix("./") for entry in pages})
    audio_files = sorted({f"content/i18n/en-GB/audio/{name}" for name in audios.values()})
    resources = [(name, "text/html") for name in page_files]
    resources.extend((name, "audio/mpeg") for name in audio_files)

    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(check, args.base_url, resource, expected_type, args.timeout): resource
            for resource, expected_type in resources
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                failures.append(result)

    print(
        f"Live-server summary: {len(page_files)} pages and "
        f"{len(audio_files)} unique narration clips checked."
    )
    for failure in sorted(failures):
        print(f"ERROR: {failure}")
    if failures:
        print(f"FAILED with {len(failures)} error(s).")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
