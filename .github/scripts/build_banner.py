"""Convert the source MP4 into a high-quality animated WebP profile banner."""

from __future__ import annotations

from pathlib import Path

import cv2
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets" / "banner-source.mp4"
OUTPUT = ROOT / "assets" / "banner.webp"
TARGET_FPS = 18
QUALITY = 92
LOOP_START_FRAME = 12
LOOP_FRAME_COUNT = 120


def read_frames() -> tuple[list[Image.Image], float]:
    capture = cv2.VideoCapture(str(SOURCE))
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open {SOURCE}")

    source_fps = capture.get(cv2.CAP_PROP_FPS)
    if source_fps <= 0:
        raise RuntimeError("Video reports an invalid frame rate")

    sample_step = source_fps / TARGET_FPS
    next_sample = 0.0
    source_index = 0
    frames: list[Image.Image] = []
    try:
        while True:
            ok, bgr = capture.read()
            if not ok:
                break
            if source_index < LOOP_START_FRAME:
                source_index += 1
                continue
            loop_index = source_index - LOOP_START_FRAME
            if loop_index >= LOOP_FRAME_COUNT:
                break
            if loop_index + 0.5 >= next_sample:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(rgb))
                next_sample += sample_step
            source_index += 1
    finally:
        capture.release()

    if not frames:
        raise RuntimeError("No frames were decoded")
    return frames, source_fps


def main() -> None:
    frames, source_fps = read_frames()
    duration_ms = round(1000 / TARGET_FPS)
    frames[0].save(
        OUTPUT,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        quality=QUALITY,
        method=4,
        lossless=False,
        minimize_size=True,
    )
    print(
        f"Built {OUTPUT.relative_to(ROOT)}: {frames[0].width}x{frames[0].height}, "
        f"{len(frames)} frames at {TARGET_FPS} FPS "
        f"from a {LOOP_FRAME_COUNT / source_fps:.2f}s seamless loop "
        f"(source {source_fps:g} FPS), {OUTPUT.stat().st_size:,} bytes"
    )


if __name__ == "__main__":
    main()
