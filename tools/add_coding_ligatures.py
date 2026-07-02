#!/usr/bin/env python3
"""Add component-based coding ligatures to the Glyphs source."""

from __future__ import annotations

from pathlib import Path


SOURCE = Path("sources/Inconsolata.glyphs")

LAYER_WIDTHS = {
    "051EFAE4-8BBE-4FBB-A016-4335C3E52F59": 500,
    "4196E4A4-01D0-4BE0-B812-9D3AF152A0E4": 500,
    "37FE174D-E85B-4C4C-A1AE-51D7E67A9FC9": 500,
    "7EB90DB1-9188-465D-93C7-E6C577A18003": 250,
    "0E826D2B-F2D1-4058-A5E0-936DF7ED7520": 250,
    "16CD5438-0A7A-495F-951A-DBB915DF0BEC": 1000,
    "E49A0581-9397-4BB7-ADB1-45D6EDC9C316": 250,
    "382F13D7-0CC9-4B85-A585-CBE12F4435D4": 1000,
    "CC486EF6-6464-4B93-9956-4F2B932959EA": 1000,
}

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

EXISTING_LIGATURE_RULES = [
    "sub exclam equal equal by exclam_equal_equal.dlig;",
    "sub equal equal equal by equal_equal_equal.dlig;",
    "sub hyphen greater by hyphen_greater.dlig;",
    "sub equal greater by equal_greater.dlig;",
    "sub greater equal by greater_equal.dlig;",
    "sub less hyphen by less_hyphen.dlig;",
    "sub less equal by less_equal.dlig;",
]


def layer_block(layer_id: str, components: list[str], cell_width: int) -> str:
    component_lines = []
    offset = 0
    for name in components:
        if offset:
            component_lines.append(
                "{\n"
                f"name = {name};\n"
                f'transform = "{{1, 0, 0, 1, {offset}, 0}}";\n'
                "}"
            )
        else:
            component_lines.append("{\n" f"name = {name};\n" "}")
        offset += cell_width

    return (
        "{\n"
        "components = (\n"
        + ",\n".join(component_lines)
        + "\n);\n"
        f'layerId = "{layer_id}";\n'
        f"width = {offset};\n"
        "}"
    )


def glyph_block(glyph_name: str, components: list[str]) -> str:
    layers = [layer_block(layer_id, components, width) for layer_id, width in LAYER_WIDTHS.items()]
    return (
        "{\n"
        f"glyphname = {glyph_name};\n"
        "layers = (\n"
        + ",\n".join(layers)
        + "\n);\n"
        "}"
    )


def update_dlig_feature(text: str) -> str:
    marker = (
        'code = "sub exclam equal equal by exclam_equal_equal.dlig;\n'
        "sub equal equal equal by equal_equal_equal.dlig;\n"
    )
    if marker not in text:
        raise SystemExit("Could not find the dlig feature block.")

    additions = "".join(line + "\n" for _, _, line in LIGATURES if line not in text)
    if not additions:
        return text
    return text.replace(marker, marker + additions, 1)


def update_liga_feature(text: str) -> str:
    liga_rules = EXISTING_LIGATURE_RULES + [line for _, _, line in LIGATURES]
    if "name = liga;" in text:
        updated = text
        for rule in liga_rules:
            liga_name = "\nname = liga;\n"
            if rule in updated[updated.rfind('code = "', 0, updated.find(liga_name)) : updated.find(liga_name)]:
                continue
            insertion_point = updated.find('";\nname = liga;\n')
            if insertion_point == -1:
                raise SystemExit("Could not find the liga feature code block.")
            updated = updated[:insertion_point] + rule + "\n" + updated[insertion_point:]
        return updated

    dlig_end = '";\nname = dlig;\n},\n'
    if dlig_end not in text:
        raise SystemExit("Could not find where to insert the liga feature block.")

    rules = "".join(line + "\n" for line in liga_rules)
    block = (
        "{\n"
        "automatic = 1;\n"
        f'code = "{rules}";\n'
        "name = liga;\n"
        "},\n"
    )
    return text.replace(dlig_end, dlig_end + block, 1)


def insert_glyphs(text: str) -> str:
    blocks = []
    for glyph_name, components, _ in LIGATURES:
        if f"glyphname = {glyph_name};" not in text:
            blocks.append(glyph_block(glyph_name, components))

    if not blocks:
        return text

    marker = "\n);\ninstances = (\n"
    if marker not in text:
        raise SystemExit("Could not find the end of the glyph list.")

    insertion = ",\n" + ",\n".join(blocks)
    return text.replace(marker, insertion + marker, 1)


def main() -> None:
    text = SOURCE.read_text()
    updated = insert_glyphs(update_liga_feature(update_dlig_feature(text)))
    if updated == text:
        print("No changes needed.")
        return
    SOURCE.write_text(updated)
    print("Updated sources/Inconsolata.glyphs with coding ligatures.")


if __name__ == "__main__":
    main()
