#!/usr/bin/env python3
"""Create the shared Activity badge from the printed-book artwork."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "pg011_im003.png"
OUTPUT = ROOT / "images" / "activity_icon.png"


def main() -> None:
    source = Image.open(SOURCE).convert("RGBA")
    icon = source.crop((0, 0, 112, 112))

    scale = 4
    mask = Image.new("L", (icon.width * scale, icon.height * scale), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((2, 2, mask.width - 3, mask.height - 3), fill=255)
    mask = mask.resize(icon.size, Image.Resampling.LANCZOS)
    icon.putalpha(mask)
    icon.save(OUTPUT, optimize=True)
    print(f"Created {OUTPUT.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
