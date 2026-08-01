#!/usr/bin/env python3
"""Place the printed-book Activity badge before every visible Activity heading."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICON_LARGE = '<img src="images/activity_icon.png" alt="" role="presentation" aria-hidden="true" class="h-16 w-16 shrink-0 rounded-full object-cover max-sm:h-12 max-sm:w-12">'
ICON_MEDIUM = '<img src="images/activity_icon.png" alt="" role="presentation" aria-hidden="true" class="h-14 w-14 shrink-0 rounded-full object-cover max-sm:h-11 max-sm:w-11">'
ICON_SMALL = '<img src="images/activity_icon.png" alt="" role="presentation" aria-hidden="true" class="h-12 w-12 shrink-0 rounded-full object-cover max-sm:h-10 max-sm:w-10">'


def replace(filename: str, old: str, new: str) -> None:
    path = ROOT / filename
    source = path.read_text(encoding="utf-8")
    if old in source:
        path.write_text(source.replace(old, new, 1), encoding="utf-8")
    elif new not in source:
        raise ValueError(f"Expected Activity header not found in {filename}: {old[:100]!r}")


def main() -> None:
    replace(
        "pg010_sec001.html",
        '<div class="mr-4 flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-[6px] border-[#d96678] bg-white text-2xl text-stone-700 shadow-[0_0_0_6px_rgba(122,118,188,0.45)] max-sm:h-14 max-sm:w-14"><i class="fa-solid fa-pen-to-square" aria-hidden="true"></i></div>',
        ICON_LARGE.replace('class="', 'class="mr-4 '),
    )
    replace(
        "pg012_sec001.html",
        '<div class="bg-gradient-to-r from-amber-700 via-orange-700 to-pink-500 px-6 py-3 w-full max-w-[44rem] rounded-r-3xl"><span class="text-white text-4xl font-bold" data-id="pg012_n0004">Activity 3</span>',
        f'<div class="flex items-center gap-4 bg-gradient-to-r from-amber-700 via-orange-700 to-pink-500 px-6 py-3 w-full max-w-[44rem] rounded-r-3xl">{ICON_LARGE}<span class="text-white text-4xl font-bold" data-id="pg012_n0004">Activity 3</span>',
    )
    replace(
        "pg013_sec003.html",
        '<div class="relative z-10 flex h-full items-center px-6 max-sm:px-4">\n          <h1 class="adt-h1 font-bold leading-none text-white" data-id="pg013_n0013">Activity 4</h1>',
        f'<div class="relative z-10 flex h-full items-center gap-4 px-6 max-sm:px-4">\n          {ICON_LARGE}\n          <h1 class="adt-h1 font-bold leading-none text-white" data-id="pg013_n0013">Activity 4</h1>',
    )
    replace(
        "pg014_sec002.html",
        '<div class="bg-gradient-to-r from-orange-700 via-orange-600 to-pink-500 px-6 py-3 max-sm:px-4">\n        <h1 class="adt-h1 font-bold text-white leading-none" data-id="pg014_n0009">Activity 5</h1>',
        f'<div class="flex items-center gap-4 bg-gradient-to-r from-orange-700 via-orange-600 to-pink-500 px-6 py-3 max-sm:px-4">\n        {ICON_LARGE}\n        <h1 class="adt-h1 font-bold text-white leading-none" data-id="pg014_n0009">Activity 5</h1>',
    )
    replace(
        "pg022_sec001.html",
        '<div class="h-12 bg-gradient-to-r from-[#c55d00] via-[#c55d00] via-65% to-[#d85b91] to-100% flex items-center px-8 max-sm:px-5"><h1 class="font-bold text-white drop-shadow-sm" data-id="pg022_n0002">Activity 1</h1>',
        f'<div class="min-h-16 bg-gradient-to-r from-[#c55d00] via-[#c55d00] via-65% to-[#d85b91] to-100% flex items-center gap-4 px-8 py-2 max-sm:px-5">{ICON_MEDIUM}<h1 class="font-bold text-white drop-shadow-sm" data-id="pg022_n0002">Activity 1</h1>',
    )
    replace(
        "pg022_sec002.html",
        '<div class="absolute left-4 top-1/2 -translate-y-1/2 h-20 w-20 max-sm:h-16 max-sm:w-16 rounded-full bg-gradient-to-br from-pink-400 via-purple-400 to-orange-400 p-1 shadow-md">\n          <div class="flex h-full w-full items-center justify-center rounded-full bg-white">\n            <i aria-hidden="true" class="fa-solid fa-magnifying-glass text-3xl max-sm:text-2xl text-stone-700"></i>\n          </div>\n        </div>',
        '<img src="images/activity_icon.png" alt="" role="presentation" aria-hidden="true" class="absolute left-4 top-1/2 h-20 w-20 -translate-y-1/2 rounded-full object-cover shadow-md max-sm:h-16 max-sm:w-16">',
    )
    replace(
        "pg024_sec001.html",
        '<div class="absolute left-4 top-1/2 flex -translate-y-1/2 items-center justify-center w-16 h-16 rounded-full bg-white border-[6px] border-pink-300 text-2xl text-stone-700 shadow"><i class="fa-solid fa-book-open-reader" aria-hidden="true"></i></div>',
        '<img src="images/activity_icon.png" alt="" role="presentation" aria-hidden="true" class="absolute left-4 top-1/2 h-16 w-16 -translate-y-1/2 rounded-full object-cover shadow">',
    )
    replace(
        "pg036_sec001.html",
        '<div class="rounded-t-[1.25rem] bg-gradient-to-r from-orange-700 via-amber-700 to-pink-400 px-6 py-3 max-sm:px-4 max-sm:py-3">\n            <span class="adt-h2 font-bold text-white" data-id="pg036_n0005">Activity 1</span>',
        f'<div class="flex items-center gap-4 rounded-t-[1.25rem] bg-gradient-to-r from-orange-700 via-amber-700 to-pink-400 px-6 py-3 max-sm:px-4 max-sm:py-3">\n            {ICON_MEDIUM}\n            <span class="adt-h2 font-bold text-white" data-id="pg036_n0005">Activity 1</span>',
    )
    replace(
        "pg038_sec002.html",
        '<div class="inline-block bg-gradient-to-r from-orange-700 to-amber-500 text-white rounded-2xl px-6 py-2 shadow-sm mb-2 adt-h2 leading-none"\n                                data-id="pg038_n0013">Activity 3</div>',
        f'<div class="inline-flex items-center gap-3 bg-gradient-to-r from-orange-700 to-amber-500 text-white rounded-2xl px-4 py-2 shadow-sm mb-2">{ICON_SMALL}<div class="adt-h2 leading-none" data-id="pg038_n0013">Activity 3</div></div>',
    )
    replace(
        "pg039_sec001.html",
        '<p class="inline-block bg-gradient-to-b from-[#d97a18] to-[#b85700] text-white font-bold rounded-2xl px-8 py-3 mb-5 shadow" data-id="pg039_n0006">Activity 4</p>',
        f'<div class="inline-flex items-center gap-3 bg-gradient-to-b from-[#d97a18] to-[#b85700] text-white font-bold rounded-2xl px-4 py-2 mb-5 shadow">{ICON_SMALL}<p data-id="pg039_n0006">Activity 4</p></div>',
    )
    replace(
        "pg041_sec001.html",
        '<div class="flex items-center bg-gradient-to-r from-[#c55b08] via-[#cf6a18] to-[#d85f9b] px-6 py-4 max-sm:px-4 max-sm:py-3"><h1 class="adt-h1 font-bold text-white leading-none" data-id="pg041_n0002">Activity 5</h1>',
        f'<div class="flex items-center gap-4 bg-gradient-to-r from-[#c55b08] via-[#cf6a18] to-[#d85f9b] px-6 py-4 max-sm:px-4 max-sm:py-3">{ICON_LARGE}<h1 class="adt-h1 font-bold text-white leading-none" data-id="pg041_n0002">Activity 5</h1>',
    )
    replace(
        "pg041_sec002.html",
        '<div class="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-white ring-4 ring-pink-300 shadow-inner max-sm:h-16 max-sm:w-16">\n          <div class="h-12 w-12 rounded-full border-2 border-orange-300 bg-gradient-to-br from-pink-100 to-orange-100"></div>\n        </div>',
        '<img src="images/activity_icon.png" alt="" role="presentation" aria-hidden="true" class="h-20 w-20 shrink-0 rounded-full object-cover shadow-inner max-sm:h-16 max-sm:w-16">',
    )
    replace(
        "pg043_sec001.html",
        '<h1 class="mb-4 text-left font-bold text-[#b95400] adt-h1 leading-tight">\n      <span data-id="pg043_n0004">Activity 7</span>\n    </h1>',
        '<h1 class="sr-only"><span data-id="pg043_n0004">Activity 7</span></h1>',
    )
    replace(
        "pg044_sec001.html",
        '<div class="mr-4 flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-white ring-4 ring-[#d86da0] max-lg:h-14 max-lg:w-14 max-sm:h-12 max-sm:w-12">\n        <i class="fa-solid fa-pen-to-square text-3xl text-[#7a5a63] max-sm:text-2xl" aria-hidden="true"></i>\n      </div>',
        ICON_LARGE.replace('class="', 'class="mr-4 '),
    )
    replace(
        "pg047_sec001.html",
        '<div data-id="pg047_n0005" class="adt-h3 absolute left-8 top-0 z-10 rounded-2xl bg-gradient-to-b from-orange-500 to-orange-700 px-6 py-3 font-bold text-white shadow-md max-sm:left-5 max-sm:px-4">Activity 10</div>',
        f'<div class="absolute left-8 top-0 z-10 flex items-center gap-3 rounded-2xl bg-gradient-to-b from-orange-500 to-orange-700 px-4 py-2 font-bold text-white shadow-md max-sm:left-5">{ICON_SMALL}<div data-id="pg047_n0005" class="adt-h3">Activity 10</div></div>',
    )

    for filename, old in {
        "pg049_sec001.html": '<i class="fa-solid fa-eye text-3xl" aria-hidden="true"></i>',
        "pg050_sec002.html": '<i class="fa-solid fa-pen-to-square text-3xl" aria-hidden="true"></i>',
        "pg055_sec001.html": '<i class="fa-solid fa-pen-to-square text-3xl" aria-hidden="true"></i>',
        "pg059_sec002.html": '<i class="fa-solid fa-people-arrows-left-right text-3xl" aria-hidden="true"></i>',
        "pg079_sec002.html": '<i class="fa-solid fa-pen-to-square text-2xl text-white" aria-hidden="true"></i>',
    }.items():
        replace(filename, old, ICON_SMALL)

    print("Applied printed-book Activity badges to all semantic Activity headers.")


if __name__ == "__main__":
    main()
