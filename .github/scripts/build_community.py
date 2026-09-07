"""Build responsive, outlined SVG community cards from the README text.

Requires Python and fonttools, as does build_ai_philosophy.py. Run:
    python .github/scripts/build_community.py --font-dir C:/Windows/Fonts

The README's community-text block is the source for the name, rank, and work.
The logo is the upstream SVG preserved in assets, with attribution alongside it.
Rank and total are intentionally manual, not fetched from an API by this script.
"""

import argparse
from html import escape
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from build_ai_philosophy import PALETTES, ROOT, Typeface, number, wrap


def source():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"<!--START_SECTION:community-text-->\s*(.*?)\s*<!--END_SECTION:community-text-->", readme, re.S)
    if not match:
        raise ValueError("README community markers are missing")
    passage = match.group(1)
    project = re.search(r"^### \[([^\]]+)\]\((https://github.com/[^)]+)\)$", passage, re.M)
    rank = re.search(r"\*\*Human contributor rank: (#[0-9]+ / [0-9]+)\*\*", passage)
    items = re.findall(r"^- \*\*(.+?)\.\*\* (.+)$", passage, re.M)
    if not project or not rank or len(items) != 4:
        raise ValueError("Expected a project link, manual rank, and four contribution items")
    return project.group(1), project.group(2).removeprefix("https://github.com/"), rank.group(1), items


def logo_path():
    root = ET.parse(ROOT / "assets" / "open-code-review-logo.svg").getroot()
    path = root.find("{http://www.w3.org/2000/svg}path")
    if path is None or root.get("viewBox") != "0 0 64 64":
        raise ValueError("Unexpected upstream logo structure")
    return ('<path d="' + escape(path.attrib["d"], quote=True)
            + '" fill="' + escape(path.attrib["fill"], quote=True)
            + '" fill-rule="' + escape(path.attrib["fill-rule"], quote=True) + '"/>')


def render(font_dir, theme, mobile):
    regular = Typeface(font_dir / "georgia.ttf", "r")
    italic = Typeface(font_dir / "georgiai.ttf", "i")
    brand = Typeface(font_dir / "seguisb.ttf", "b")
    label = Typeface(font_dir / "segoeui.ttf", "s")
    title, repository, rank, items = source()
    colors = PALETTES[theme]
    width = 440 if mobile else 960
    margin = 28 if mobile else 48
    usable = width - 2 * margin
    elements = []

    def centered(text, face, size, baseline, color):
        measured = face.measure(text, size)
        if measured > usable:
            raise ValueError(f"Centered text does not fit: {text}")
        elements.append(face.line(text, (width - measured) / 2, baseline, size, color))

    def paragraph(text, face, size, leading, x, top, available, color):
        lines = wrap(text, face, size, available)
        for index, line in enumerate(lines):
            elements.append(face.line(line, x, top + size + index * leading, size, color))
        return top + len(lines) * leading

    # Keep the official symbol intact, including its colour and proportions.
    # A cropped viewBox removes only the original canvas's empty margins.
    logo_size = 84 if mobile else 88
    elements.append(f'<svg x="{(width - logo_size) / 2}" y="32" width="{logo_size}" height="{logo_size}" viewBox="10 12 44 44">{logo_path()}</svg>')
    centered(title, brand, 34 if mobile else 40, 162 if mobile else 170, colors["ink"])
    centered(repository, label, 16 if mobile else 18, 191 if mobile else 201, colors["muted"])

    # Separate human rank from the total-contributor denominator in the README note.
    centered("Human contributor rank", label, 16 if mobile else 18, 234 if mobile else 244, colors["body"])
    centered(rank, regular, 36 if mobile else 40, 280 if mobile else 295, colors["ink"])
    y = 311 if mobile else 328
    elements.append(f'<path d="M{margin} {y}H{width - margin}" stroke="{colors["rule"]}"/>')
    y += 27
    y = paragraph("My contributions", regular, 26 if mobile else 30, 40, margin, y, usable, colors["ink"])
    y += 24

    gap = 48
    column_width = usable if mobile else (usable - gap) / 2
    columns = 1 if mobile else 2
    for index in range(0, len(items), columns):
        bottom = y
        for column, (heading, body) in enumerate(items[index:index + columns]):
            x = margin + column * (column_width + gap)
            end = paragraph(heading, italic, 22 if mobile else 24, 34, x, y, column_width, colors["accent"])
            end += 8
            end = paragraph(body, regular, 20 if mobile else 22, 31 if mobile else 33, x, end, column_width, colors["body"])
            bottom = max(bottom, end)
        y = bottom + (26 if mobile else 32)
    height = round(y + 14)
    description = f"{title}. Human contributor rank {rank}. " + " ".join(body for _, body in items)
    definitions = "\n".join(face.definitions() for face in (regular, italic, brand, label))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
           f'<title id="title">{escape(title)} — my open-source contributions</title>\n'
           f'<desc id="desc">{escape(description)}</desc>\n'
           '<!-- Generated by .github/scripts/build_community.py. Work text uses outlined Georgia. -->\n'
           '<!-- OpenCodeReview logo: Copyright 2026 Alibaba; Apache-2.0. See assets/open-code-review-NOTICE.md. -->\n'
           f'<defs>\n{definitions}\n</defs>\n'
           f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="4" fill="{colors["paper"]}" stroke="{colors["rule"]}"/>\n'
           + "\n".join(elements) + "\n</svg>\n")
    suffix = f"mobile-{theme}" if mobile else theme
    target = ROOT / "assets" / f"community-open-code-review-{suffix}.svg"
    target.write_text(svg, encoding="utf-8", newline="\n")
    print(f"{target.name}: {width}x{height}, {target.stat().st_size} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-dir", type=Path, default=Path("C:/Windows/Fonts"))
    args = parser.parse_args()
    for is_mobile in (False, True):
        for mode in ("light", "dark"):
            render(args.font_dir, mode, is_mobile)
