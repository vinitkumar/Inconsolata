#!/usr/bin/env python3
"""Build a PragmataPro-like narrow Inconsolata variable font."""

from __future__ import annotations

import subprocess
from pathlib import Path

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


SOURCE = Path("fonts/variable/Inconsolata[wdth,wght].ttf")
OUT_DIR = Path("fonts/pragmatic-narrow")
OUT = OUT_DIR / "InconsolataPragmaticNarrow[wght].ttf"
WOFF2_OUT = OUT_DIR / "InconsolataPragmaticNarrow[wght].woff2"
FAMILY = "Inconsolata Pragmatic Narrow"
PS_FAMILY = "InconsolataPragmaticNarrow"
CELL_WIDTH = 425

LIGATURES = [
    ("exclam_equal.dlig", ["exclam", "equal"], "sub exclam equal by exclam_equal.dlig;"),
    ("equal_equal.dlig", ["equal", "equal"], "sub equal equal by equal_equal.dlig;"),
    ("hyphen_hyphen.dlig", ["hyphen", "hyphen"], "sub hyphen hyphen by hyphen_hyphen.dlig;"),
    ("plus_plus.dlig", ["plus", "plus"], "sub plus plus by plus_plus.dlig;"),
    ("colon_colon.dlig", ["colon", "colon"], "sub colon colon by colon_colon.dlig;"),
    ("ampersand_ampersand.dlig", ["ampersand", "ampersand"], "sub ampersand ampersand by ampersand_ampersand.dlig;"),
    ("bar_bar.dlig", ["bar", "bar"], "sub bar bar by bar_bar.dlig;"),
    ("slash_slash.dlig", ["slash", "slash"], "sub slash slash by slash_slash.dlig;"),
    ("slash_asterisk.dlig", ["slash", "asterisk"], "sub slash asterisk by slash_asterisk.dlig;"),
    ("asterisk_slash.dlig", ["asterisk", "slash"], "sub asterisk slash by asterisk_slash.dlig;"),
    ("less_greater.dlig", ["less", "greater"], "sub less greater by less_greater.dlig;"),
    ("less_less.dlig", ["less", "less"], "sub less less by less_less.dlig;"),
    ("greater_greater.dlig", ["greater", "greater"], "sub greater greater by greater_greater.dlig;"),
    ("bar_greater.dlig", ["bar", "greater"], "sub bar greater by bar_greater.dlig;"),
    ("less_bar.dlig", ["less", "bar"], "sub less bar by less_bar.dlig;"),
]


def set_name(font: TTFont, name_id: int, value: str) -> None:
    for record in font["name"].names:
        if record.nameID == name_id:
            record.string = value.encode(record.getEncoding())


def patch_names(path: Path) -> None:
    font = TTFont(path)
    set_name(font, 1, FAMILY)
    set_name(font, 3, f"{PS_FAMILY};3.100")
    set_name(font, 4, FAMILY)
    set_name(font, 6, f"{PS_FAMILY}-Regular")
    set_name(font, 16, FAMILY)
    set_name(font, 17, "Regular")
    font.save(path)


def add_component_ligature(font: TTFont, glyph_set, glyph_name: str, components: list[str]) -> None:
    if glyph_name in font.getGlyphOrder():
        return

    glyph_order = font.getGlyphOrder()
    glyph_order.append(glyph_name)
    font.setGlyphOrder(glyph_order)

    pen = TTGlyphPen(glyph_set)
    for index, component in enumerate(components):
        pen.addComponent(component, (1, 0, 0, 1, index * CELL_WIDTH, 0))

    font["glyf"][glyph_name] = pen.glyph()
    font["hmtx"][glyph_name] = (len(components) * CELL_WIDTH, font["hmtx"].metrics[components[0]][1])
    font["maxp"].numGlyphs = len(glyph_order)


def add_ligatures(path: Path) -> None:
    font = TTFont(path)
    glyph_order = set(font.getGlyphOrder())
    if all(glyph_name in glyph_order for glyph_name, _, _ in LIGATURES) and has_ligature_rules(font):
        font.save(path)
        return

    glyph_set = font.getGlyphSet()
    for glyph_name, components, _ in LIGATURES:
        add_component_ligature(font, glyph_set, glyph_name, components)

    feature_rules = "\n".join(rule for _, _, rule in LIGATURES)
    addOpenTypeFeaturesFromString(font, f"feature dlig {{\n{feature_rules}\n}} dlig;\n")
    font.save(path)


def has_ligature_rules(font: TTFont) -> bool:
    if "GSUB" not in font:
        return False

    expected = {glyph_name for glyph_name, _, _ in LIGATURES}
    found = set()
    feature_list = font["GSUB"].table.FeatureList
    lookup_list = font["GSUB"].table.LookupList
    if feature_list is None or lookup_list is None:
        return False

    for record in feature_list.FeatureRecord:
        if record.FeatureTag != "dlig":
            continue
        for lookup_index in record.Feature.LookupListIndex:
            lookup = lookup_list.Lookup[lookup_index]
            for subtable in lookup.SubTable:
                for entries in getattr(subtable, "ligatures", {}).values():
                    for ligature in entries:
                        if ligature.LigGlyph in expected:
                            found.add(ligature.LigGlyph)
    return expected <= found


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source variable font: {SOURCE}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "fonttools",
            "varLib.instancer",
            str(SOURCE),
            "wdth=85",
            "-o",
            str(OUT),
        ],
        check=True,
    )
    add_ligatures(OUT)
    patch_names(OUT)
    subprocess.run(["fonttools", "ttLib.woff2", "compress", "-o", str(WOFF2_OUT), str(OUT)], check=True)
    print(f"Built {OUT}")
    print(f"Built {WOFF2_OUT}")


if __name__ == "__main__":
    main()
