"""Render the README's AI philosophy as portable, outlined serif SVGs.

Requires Python and fonttools. Run from any directory:
    python .github/scripts/build_ai_philosophy.py --font-dir C:/Windows/Fonts

Georgia is used locally to outline the lettering; no font files are embedded
or distributed. The marked README passage is the canonical editable text.
"""

import argparse
from html import escape
from pathlib import Path
import re

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[2]
PALETTES = {
    "light": {"paper": "#FAF9F6", "ink": "#272A2B", "body": "#454542", "muted": "#77736B", "rule": "#DAD5CC", "accent": "#875641"},
    "dark": {"paper": "#15191F", "ink": "#F0ECE4", "body": "#D0CCC5", "muted": "#ADA79D", "rule": "#3D4146", "accent": "#D6AB8C"},
}


def number(value):
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


class Typeface:
    def __init__(self, path, prefix):
        self.font = TTFont(path)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.units = self.font["head"].unitsPerEm
        self.prefix = prefix
        self.used = {}
        self.kern = {}
        if "kern" in self.font:
            for table in self.font["kern"].kernTables:
                if table.format == 0:
                    self.kern.update(table.kernTable)

    def positions(self, text):
        x = 0
        previous = None
        for char in text:
            glyph = self.cmap.get(ord(char))
            if glyph is None:
                raise ValueError(f"Missing character: {char!r}")
            x += self.kern.get((previous, glyph), 0)
            yield x, char, glyph
            x += self.font["hmtx"].metrics[glyph][0]
            previous = glyph

    def measure(self, text, size):
        advance = 0
        for x, _, glyph in self.positions(text):
            advance = x + self.font["hmtx"].metrics[glyph][0]
        return advance * size / self.units

    def line(self, text, x, baseline, size, color):
        scale = size / self.units
        uses = []
        for advance, char, glyph in self.positions(text):
            if char == " ":
                continue
            glyph_id = f"{self.prefix}{ord(char):x}"
            self.used[glyph_id] = glyph
            uses.append(f'<use href="#{glyph_id}" x="{number(advance)}"/>')
        return (f'<g aria-label="{escape(text, quote=True)}" fill="{color}" '
                f'transform="translate({number(x)} {number(baseline)}) scale({number(scale)} -{number(scale)})">'
                + "".join(uses) + "</g>")

    def definitions(self):
        paths = []
        for glyph_id, glyph in sorted(self.used.items()):
            pen = SVGPathPen(self.glyphs, ntos=number)
            self.glyphs[glyph].draw(pen)
            paths.append(f'<path id="{glyph_id}" d="{pen.getCommands()}"/>')
        return "\n".join(paths)


def wrap(text, face, size, width):
    lines = []
    line = ""
    for word in text.split():
        trial = f"{line} {word}" if line else word
        if face.measure(trial, size) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
        if face.measure(line, size) > width:
            raise ValueError(f"Word does not fit: {line}")
    if line:
        lines.append(line)
    # Avoid a short final line when a word can move from the preceding line.
    if len(lines) > 1 and face.measure(lines[-1], size) < width * .2:
        words = lines[-2].split()
        candidate = words[-1] + " " + lines[-1]
        if len(words) > 1 and face.measure(candidate, size) <= width:
            lines[-2] = " ".join(words[:-1])
            lines[-1] = candidate
    return lines


def source():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"<!--START_SECTION:ai-philosophy-text-->\s*(.*?)\s*<!--END_SECTION:ai-philosophy-text-->", readme, re.S)
    if not match:
        raise ValueError("README philosophy markers are missing")
    blocks = match.group(1).split("\n\n")
    title = blocks[0].removeprefix("## ")
    paragraphs = blocks[1:6]
    quote = [line.removeprefix("> ") for line in blocks[6].splitlines() if line.startswith("> ")]
    return title, paragraphs, quote[:2], quote[2].replace("*", ""), blocks[7].strip("*")


def render(font_dir, theme, mobile):
    regular = Typeface(font_dir / "georgia.ttf", "r")
    italic = Typeface(font_dir / "georgiai.ttf", "i")
    title, paragraphs, quote, attribution, motto = source()
    colors = PALETTES[theme]
    width = 440 if mobile else 960
    margin = 24 if mobile else 48
    content_width = width - 2 * margin
    elements = []
    line_count = 0

    def paragraph(text, face, size, leading, top, color, x=margin, available=content_width):
        nonlocal line_count
        lines = wrap(text, face, size, available)
        for index, line in enumerate(lines):
            elements.append(face.line(line, x, top + size + index * leading, size, color))
        line_count += len(lines)
        return top + len(lines) * leading

    title_size = 31 if mobile else 42
    y = paragraph(title, regular, title_size, title_size * 1.25, 32 if mobile else 38, colors["ink"])
    y += 20
    elements.append(f'<path d="M{margin} {number(y)}h48" stroke="{colors["accent"]}" stroke-width="2"/>')
    y += 24
    for index, text in enumerate(paragraphs):
        size = (21 if mobile else 24) if index == 0 else (20 if mobile else 22)
        leading = 31 if mobile else 34
        y = paragraph(text, regular, size, leading, y, colors["ink"] if index == 0 else colors["body"])
        y += 22 if mobile else 24

    y += 4
    elements.append(f'<path d="M{margin} {number(y)}H{width - margin}" stroke="{colors["rule"]}"/>')
    y += 26
    for line in quote:
        y = paragraph(line, italic, 20 if mobile else 25, 31 if mobile else 37, y, colors["ink"])
    y += 12
    y = paragraph(attribution, regular, 15 if mobile else 17, 24, y, colors["muted"])
    y += 28
    y = paragraph(motto, italic, 23 if mobile else 28, 37, y, colors["accent"])
    height = round(y + 36)
    body = "\n".join(elements)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
           f'<title id="title">{escape(title)}</title>\n'
           '<desc id="desc">A personal philosophy of planning, collaboration between agents, independent review, and human responsibility. Full selectable text is in the README.</desc>\n'
           '<!-- Generated from README.md by .github/scripts/build_ai_philosophy.py. Lettering is outlined Georgia. -->\n'
           f'<defs>\n{regular.definitions()}\n{italic.definitions()}\n</defs>\n'
           f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="4" fill="{colors["paper"]}" stroke="{colors["rule"]}"/>\n'
           f'{body}\n</svg>\n')
    suffix = f"mobile-{theme}" if mobile else theme
    target = ROOT / "assets" / f"ai-philosophy-{suffix}.svg"
    target.write_text(svg, encoding="utf-8", newline="\n")
    print(f"{target.name}: {width}x{height}, {line_count} lines, {target.stat().st_size} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-dir", type=Path, default=Path("C:/Windows/Fonts"))
    args = parser.parse_args()
    for is_mobile in (False, True):
        for mode in ("light", "dark"):
            render(args.font_dir, mode, is_mobile)
