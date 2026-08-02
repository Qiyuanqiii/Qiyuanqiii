"""Apply the profile's rice-paper ink-wash palette to Metrics isocalendar SVGs."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PAPER = "#FAFAF7"

PALETTE = {
    # GitHub contribution levels: empty paper grain -> four depths of ink.
    "#ebedf0": "#EEECE6",
    "#9be9a8": "#D8D5CC",
    "#40c463": "#B8B3A7",
    "#30a14e": "#7E817D",
    "#216e39": "#3A3D40",
    # Titles, links, icons, and body copy.
    "#0366d6": "#2B2D30",
    "#0969da": "#3A3D40",
    "#0a3069": "#5B5E61",
    "#959da5": "#8B8D90",
    "#777": "#5B5E61",
    # Seasonal/rainbow fallbacks must not reintroduce saturated colors.
    "#ffee4a": "#D8D5CC",
    "#ffc501": "#B8B3A7",
    "#fe9600": "#7E817D",
    "#03001c": "#3A3D40",
    "#54aeff": "#B8B3A7",
    "#b6e3ff": "#D8D5CC",
    "#7f00ff": "#B8B3A7",
    "#a933ff": "#8B8D90",
    "#007fff": "#7E817D",
    "#00ff7f": "#667268",
    "#ff7f00": "#A33A2B",
    "#ff0": "#B4A47F",
    "red": "#A33A2B",
}


def recolor(svg: str) -> str:
    if "<svg" not in svg or "</svg>" not in svg:
        raise ValueError("input is not a complete SVG")

    # The rect sits below the foreignObject and makes the canvas reliably paper-white.
    if 'data-ink-paper="true"' not in svg:
        svg = re.sub(
            r"(<svg\b[^>]*>)",
            rf'\1\n    <rect data-ink-paper="true" width="100%" height="100%" fill="{PAPER}"/>',
            svg,
            count=1,
            flags=re.IGNORECASE,
        )

    for source, target in sorted(PALETTE.items(), key=lambda item: -len(item[0])):
        svg = re.sub(re.escape(source), target, svg, flags=re.IGNORECASE)

    return svg


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "metrics.plugin.isocalendar.svg")
    if not path.exists():
        matches = list(Path.cwd().rglob(path.name))
        if len(matches) != 1:
            raise FileNotFoundError(f"could not locate generated {path.name}")
        source = matches[0]
        svg = source.read_text(encoding="utf-8")
    else:
        svg = path.read_text(encoding="utf-8")

    styled = recolor(svg)
    path.write_text(styled, encoding="utf-8")
    print(f"Styled {path} ({len(styled):,} characters)")


if __name__ == "__main__":
    main()
