#!/usr/bin/env python3
"""Move short-answer questions 9–11 from reader page 24 to page 23."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_23 = ROOT / "pg018_sec002.html"
PAGE_24 = ROOT / "pg019_sec001.html"


PAGE_23_OLD = '''    <p class="adt-body text-neutral-900 leading-relaxed mb-6">
      <span class="mr-3" data-id="pg018_n0045">8.</span>
      <span data-id="pg018_n0046">What benefits do we get from planting trees in the school environment?</span>
    </p>

    <div class="relative rounded-md border border-neutral-300 bg-white overflow-hidden">
      <div class="pointer-events-none absolute inset-0 z-0 px-3 py-3">
        <div class="h-6 border-b border-dotted border-neutral-300"></div>
        <div class="h-7 border-b border-dotted border-neutral-300"></div>
        <div class="h-7 border-b border-dotted border-neutral-300"></div>
        <div class="h-7 border-b border-dotted border-neutral-300"></div>
        <div class="h-7"></div>
      </div>
      <textarea class="relative z-10 w-full h-36 resize-none bg-transparent px-3 py-3 text-transparent caret-neutral-900 outline-none" data-aria-id="aria-1-0-0" aria-label="Answer to question 8 about the benefits of planting trees in the school environment" tabindex="0"></textarea>
    </div>'''

PAGE_23_NEW = '''    <div class="space-y-8">
      <div>
        <label for="short-answer-8" class="adt-body text-neutral-900 leading-relaxed mb-3 block">
          <span class="mr-3" data-id="pg018_n0045">8.</span>
          <span data-id="pg018_n0046">What benefits do we get from planting trees in the school environment?</span>
        </label>
        <textarea id="short-answer-8" class="w-full min-h-28 resize-none rounded-md border border-neutral-300 bg-white px-3 py-3 text-neutral-900 leading-7 shadow-inner focus:border-2 focus:border-blue-600 focus:outline-none" style="background-image: repeating-linear-gradient(to bottom, transparent 0, transparent 29px, #d4d4d4 30px);" data-aria-id="aria-1-0-0" aria-label="Answer to question 8 about the benefits of planting trees in the school environment" tabindex="0"></textarea>
      </div>

      <div>
        <label for="short-answer-9" class="adt-body text-neutral-900 leading-relaxed mb-3 block">
          <span class="mr-3" data-id="pg019_n0003">9.</span>
          <span data-id="pg019_n0005">If your parents or guardians bought a big piece of land with a forest on it, what kind of activity would you advise them to undertake in that land?</span>
        </label>
        <textarea id="short-answer-9" class="w-full min-h-28 resize-none rounded-md border border-neutral-300 bg-white px-3 py-3 text-neutral-900 leading-7 shadow-inner focus:border-2 focus:border-blue-600 focus:outline-none" style="background-image: repeating-linear-gradient(to bottom, transparent 0, transparent 29px, #d4d4d4 30px);" data-aria-id="aria-1-0-1" aria-label="Answer to question 9 about an appropriate activity on forested land" tabindex="0"></textarea>
      </div>

      <div>
        <label for="short-answer-10" class="adt-body text-neutral-900 leading-relaxed mb-3 block">
          <span class="mr-3" data-id="pg019_n0007">10.</span>
          <span data-id="pg019_n0009">What are the geographical and environmental factors that might guide you in selecting an area for undertaking agriculture?</span>
        </label>
        <textarea id="short-answer-10" class="w-full min-h-28 resize-none rounded-md border border-neutral-300 bg-white px-3 py-3 text-neutral-900 leading-7 shadow-inner focus:border-2 focus:border-blue-600 focus:outline-none" style="background-image: repeating-linear-gradient(to bottom, transparent 0, transparent 29px, #d4d4d4 30px);" data-aria-id="aria-1-0-2" aria-label="Answer to question 10 about factors for selecting an agricultural area" tabindex="0"></textarea>
      </div>

      <div>
        <label for="short-answer-11" class="adt-body text-neutral-900 leading-relaxed mb-3 block">
          <span class="mr-3" data-id="pg019_n0011">11.</span>
          <span data-id="pg019_n0013">Using the knowledge gained from Geography and the Environment, identify the appropriate land use in the environment you live in.</span>
        </label>
        <textarea id="short-answer-11" class="w-full min-h-28 resize-none rounded-md border border-neutral-300 bg-white px-3 py-3 text-neutral-900 leading-7 shadow-inner focus:border-2 focus:border-blue-600 focus:outline-none" style="background-image: repeating-linear-gradient(to bottom, transparent 0, transparent 29px, #d4d4d4 30px);" data-aria-id="aria-1-0-3" aria-label="Answer to question 11 about appropriate land use in the local environment" tabindex="0"></textarea>
      </div>
    </div>'''

PAGE_24_QUESTIONS = '''<div class="space-y-7 max-sm:space-y-5"><div class="flex items-start gap-6 max-sm:gap-3"><div data-id="pg019_n0003" class="adt-body font-medium w-14 shrink-0 text-left">9.</div><p class="adt-body leading-relaxed text-left flex-1"><span data-id="pg019_n0005">If your parents or guardians bought a big piece of land with a forest on it, what kind of activity would you advise them to undertake in that land?</span></p></div><div class="flex items-start gap-6 max-sm:gap-3"><div data-id="pg019_n0007" class="adt-body font-medium w-14 shrink-0 text-left">10.</div><p class="adt-body leading-relaxed text-left flex-1"><span data-id="pg019_n0009">What are the geographical and environmental factors that might guide you in selecting an area for undertaking agriculture?</span></p></div><div class="flex items-start gap-6 max-sm:gap-3"><div data-id="pg019_n0011" class="adt-body font-medium w-14 shrink-0 text-left">11.</div><p class="adt-body leading-relaxed text-left flex-1"><span data-id="pg019_n0013">Using the knowledge gained from Geography and the Environment, identify the appropriate land use in the environment you live in.</span></p></div></div>'''


def replace_once(source: str, old: str, new: str, description: str) -> str:
    count = source.count(old)
    if count == 0 and new in source:
        return source
    if count != 1:
        raise ValueError(f"Could not uniquely locate {description}; found {count}")
    return source.replace(old, new, 1)


def main() -> None:
    page_23 = PAGE_23.read_text(encoding="utf-8")
    page_23 = replace_once(page_23, PAGE_23_OLD, PAGE_23_NEW, "question 8 on reader page 23")
    PAGE_23.write_text(page_23, encoding="utf-8")

    page_24 = PAGE_24.read_text(encoding="utf-8")
    page_24 = replace_once(page_24, PAGE_24_QUESTIONS, "", "questions 9–11 on reader page 24")
    PAGE_24.write_text(page_24, encoding="utf-8")

    print("Moved questions 9–11 to reader page 23 and added four visible answer fields.")


if __name__ == "__main__":
    main()
