"""Build the animated GIF profile banner from its JPEG artwork."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets" / "banner-background.jpg"
OUTPUT = ROOT / "assets" / "banner.gif"
WIDTH = 1280
HEIGHT = 320
FRAMES = 32


def font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


def cover_crop(image: Image.Image) -> Image.Image:
    scale = max(WIDTH / image.width, HEIGHT / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - WIDTH) // 2
    top = (resized.height - HEIGHT) // 2
    return resized.crop((left, top, left + WIDTH, top + HEIGHT))


def add_left_shade(image: Image.Image) -> None:
    shade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = shade.load()
    for x in range(WIDTH):
        ratio = x / (WIDTH - 1)
        alpha = round(150 * max(0.0, 1.0 - ratio / 0.62) + 24)
        for y in range(HEIGHT):
            pixels[x, y] = (7, 21, 33, alpha)
    image.alpha_composite(shade)


def wave_polygon(base_y: float, amplitude: float, period: float, phase: float) -> list[tuple[int, int]]:
    points = []
    for x in range(-8, WIDTH + 9, 8):
        y = base_y + amplitude * math.sin(2 * math.pi * (x / period + phase))
        points.append((x, round(y)))
    return points + [(WIDTH + 8, HEIGHT), (-8, HEIGHT)]


def main() -> None:
    background = cover_crop(Image.open(SOURCE).convert("RGB")).convert("RGBA")
    background = ImageEnhance.Contrast(background).enhance(1.04)
    add_left_shade(background)

    title_font = font(True, 62)
    subtitle_font = font(True, 21)
    frames: list[Image.Image] = []
    for index in range(FRAMES):
        phase = index / FRAMES
        frame = background.copy()
        draw = ImageDraw.Draw(frame, "RGBA")

        draw.text((83, 77), "Qiyuanqiii", font=title_font, fill=(4, 15, 24, 150), stroke_width=5, stroke_fill=(4, 15, 24, 110))
        draw.text((82, 74), "Qiyuanqiii", font=title_font, fill=(255, 255, 255, 255))
        draw.text((87, 153), "GO  ·  AI AGENTS  ·  CYBERSECURITY", font=subtitle_font, fill=(4, 15, 24, 170), stroke_width=3, stroke_fill=(4, 15, 24, 110))
        draw.text((86, 151), "GO  ·  AI AGENTS  ·  CYBERSECURITY", font=subtitle_font, fill=(255, 255, 255, 245))

        draw.polygon(wave_polygon(266, 13, 760, phase), fill=(221, 235, 240, 158))
        draw.polygon(wave_polygon(282, 11, 690, -phase), fill=(250, 250, 247, 232))
        frames.append(frame.convert("RGB"))

    palette = frames[0].quantize(colors=224, method=Image.Quantize.MEDIANCUT)
    indexed = [palette]
    indexed.extend(
        frame.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
        for frame in frames[1:]
    )
    indexed[0].save(
        OUTPUT,
        save_all=True,
        append_images=indexed[1:],
        duration=95,
        loop=0,
        optimize=True,
        disposal=1,
    )
    print(f"Built {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size:,} bytes, {FRAMES} frames)")


if __name__ == "__main__":
    main()
