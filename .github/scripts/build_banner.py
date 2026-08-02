"""Build the self-contained animated profile banner from its JPEG artwork."""

from __future__ import annotations

import base64
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets" / "banner-background.jpg"
OUTPUT = ROOT / "assets" / "banner.svg"


def main() -> None:
    encoded = base64.b64encode(SOURCE.read_bytes()).decode("ascii")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="320" viewBox="0 0 1280 320" role="img" aria-labelledby="title desc">
  <title id="title">Qiyuanqiii</title>
  <desc id="desc">Go, AI Agents and Cybersecurity — animated ink-wave banner</desc>
  <defs>
    <linearGradient id="shade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#071521" stop-opacity=".64"/>
      <stop offset=".42" stop-color="#071521" stop-opacity=".18"/>
      <stop offset="1" stop-color="#071521" stop-opacity=".12"/>
    </linearGradient>
    <linearGradient id="paperWave" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F7FAF8" stop-opacity=".48"/>
      <stop offset="1" stop-color="#FAFAF7" stop-opacity=".94"/>
    </linearGradient>
    <filter id="textShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#071521" flood-opacity=".62"/>
    </filter>
  </defs>

  <image width="1280" height="320" preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{encoded}"/>
  <rect width="1280" height="320" fill="url(#shade)"/>

  <g fill="#FFFFFF" filter="url(#textShadow)" opacity="0">
    <text x="82" y="132" font-family="Segoe UI,Arial,sans-serif" font-size="62" font-weight="800" letter-spacing="1">Qiyuanqiii</text>
    <text x="86" y="174" font-family="Segoe UI,Arial,sans-serif" font-size="21" font-weight="600" letter-spacing="1.2">GO  ·  AI AGENTS  ·  CYBERSECURITY</text>
    <animate attributeName="opacity" from="0" to="1" dur="1.2s" fill="freeze"/>
  </g>

  <g opacity=".62">
    <path fill="#DDEBF0" d="M-1280 269 C-1120 239 -800 239 -640 269 C-480 299 -160 299 0 269 C160 239 480 239 640 269 C800 299 1120 299 1280 269 C1440 239 1760 239 1920 269 C2080 299 2400 299 2560 269 V320 H-1280 Z">
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-1280 0" dur="13s" repeatCount="indefinite"/>
    </path>
  </g>
  <g opacity=".86">
    <path fill="url(#paperWave)" d="M-1280 282 C-1120 258 -800 258 -640 282 C-480 306 -160 306 0 282 C160 258 480 258 640 282 C800 306 1120 306 1280 282 C1440 258 1760 258 1920 282 C2080 306 2400 306 2560 282 V320 H-1280 Z">
      <animateTransform attributeName="transform" type="translate" from="-1280 0" to="0 0" dur="17s" repeatCount="indefinite"/>
    </path>
  </g>
</svg>
'''
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Built {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
