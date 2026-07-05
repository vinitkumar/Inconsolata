#!/usr/bin/env python3
"""Build slanted Italic and Bold Italic TTF/WOFF2 artifacts.

The Glyphs source in this fork has upright masters only. This script creates
app-visible Italic and Bold Italic faces by applying a modest oblique transform
to the rebuilt static Regular and Bold TTFs, then fixing OpenType names and
style flags.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
TTF_DIR = ROOT / "fonts" / "ttf"
WEBFONT_DIR = ROOT / "fonts" / "webfonts"

ITALIC_ANGLE = -11.0
SLANT = math.tan(math.radians(abs(ITALIC_ANGLE)))


def set_name(font: TTFont, name_id: int, value: str) -> None:
    name_table = font["name"]
    for record in name_table.names:
        if record.nameID == name_id:
            record.string = value.encode(record.getEncoding())


def add_name(font: TTFont, name_id: int, value: str) -> None:
    name_table = font["name"]
    if any(record.nameID == name_id for record in name_table.names):
        set_name(font, name_id, value)
        return
    name_table.setName(value, name_id, 3, 1, 0x409)


def update_names(font: TTFont, style: str, postscript_style: str) -> None:
    family = "Inconsolata"
    full_name = f"{family} {style}"
    postscript_name = f"{family}-{postscript_style}"

    add_name(font, 1, family)
    add_name(font, 2, style)
    add_name(font, 4, full_name)
    add_name(font, 6, postscript_name)
    add_name(font, 16, family)
    add_name(font, 17, style)

    version = next(
        (record.toUnicode() for record in font["name"].names if record.nameID == 5),
        "Version 3.100",
    )
    add_name(font, 3, f"{version};CYRE;{postscript_name}")


def slant_glyphs(font: TTFont) -> None:
    glyf = font["glyf"]
    hmtx = font["hmtx"]

    for glyph_name in font.getGlyphOrder():
        glyph = glyf[glyph_name]
        if glyph.isComposite():
            for component in glyph.components:
                component.x = int(round(component.x + SLANT * component.y))
        elif glyph.numberOfContours:
            coordinates, _, _ = glyph.getCoordinates(glyf)
            for index, (x, y) in enumerate(coordinates):
                coordinates[index] = (int(round(x + SLANT * y)), y)
            glyph.coordinates = coordinates

        if glyph_name in hmtx.metrics:
            try:
                glyph.recalcBounds(glyf)
                advance_width, _ = hmtx[glyph_name]
                hmtx[glyph_name] = (advance_width, getattr(glyph, "xMin", 0))
            except Exception:
                pass


def update_style_flags(font: TTFont, bold: bool) -> None:
    font["post"].italicAngle = ITALIC_ANGLE
    font["head"].macStyle = 0x02 | (0x01 if bold else 0)

    os2 = font["OS/2"]
    os2.fsSelection &= ~0x61
    os2.fsSelection |= 0x01
    if bold:
        os2.fsSelection |= 0x20


def build_face(source_name: str, output_name: str, style: str, postscript_style: str, bold: bool) -> None:
    source = TTF_DIR / source_name
    output = TTF_DIR / output_name
    webfont = WEBFONT_DIR / output_name.replace(".ttf", ".woff2")

    font = TTFont(source, recalcBBoxes=True, recalcTimestamp=False)
    slant_glyphs(font)
    update_names(font, style, postscript_style)
    update_style_flags(font, bold)
    font.save(output)

    WEBFONT_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["fonttools", "ttLib.woff2", "compress", "-o", str(webfont), str(output)],
        check=True,
    )

    print(f"Built {output.relative_to(ROOT)}")
    print(f"Built {webfont.relative_to(ROOT)}")


def main() -> None:
    build_face("Inconsolata-Regular.ttf", "Inconsolata-Italic.ttf", "Italic", "Italic", False)
    build_face("Inconsolata-Bold.ttf", "Inconsolata-BoldItalic.ttf", "Bold Italic", "BoldItalic", True)


if __name__ == "__main__":
    main()
