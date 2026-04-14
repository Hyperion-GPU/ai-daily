from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "assets" / "branding"
PNG_PATH = BRAND_DIR / "ai-daily-icon.png"
ICO_PATH = BRAND_DIR / "ai-daily.ico"

SIZE = 256
TRANSPARENT = (0, 0, 0, 0)
PAPER = (244, 235, 220, 255)
PAPER_DARK = (238, 217, 200, 255)
CARD = (255, 253, 248, 255)
INK = (64, 49, 42, 255)
INK_SOFT = (122, 94, 82, 255)
ACCENT = (202, 115, 78, 255)


def blank_canvas() -> list[list[tuple[int, int, int, int]]]:
    return [[TRANSPARENT for _ in range(SIZE)] for _ in range(SIZE)]


def set_pixel(canvas, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if 0 <= x < SIZE and 0 <= y < SIZE:
        canvas[y][x] = color


def fill_rect(canvas, x: int, y: int, width: int, height: int, color: tuple[int, int, int, int]) -> None:
    for py in range(y, y + height):
        for px in range(x, x + width):
            set_pixel(canvas, px, py, color)


def fill_rounded_rect(canvas, x: int, y: int, width: int, height: int, radius: int, color):
    for py in range(y, y + height):
        for px in range(x, x + width):
            dx = min(px - x, x + width - 1 - px)
            dy = min(py - y, y + height - 1 - py)
            if dx >= radius or dy >= radius:
                set_pixel(canvas, px, py, color)
                continue
            cx = radius - dx - 1
            cy = radius - dy - 1
            if cx * cx + cy * cy <= radius * radius:
                set_pixel(canvas, px, py, color)


def fill_circle(canvas, cx: int, cy: int, radius: int, color) -> None:
    for py in range(cy - radius, cy + radius + 1):
        for px in range(cx - radius, cx + radius + 1):
            if (px - cx) ** 2 + (py - cy) ** 2 <= radius ** 2:
                set_pixel(canvas, px, py, color)


def fill_triangle(canvas, points: list[tuple[int, int]], color) -> None:
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    (x1, y1), (x2, y2), (x3, y3) = points

    def sign(px: int, py: int, ax: int, ay: int, bx: int, by: int) -> int:
        return (px - bx) * (ay - by) - (ax - bx) * (py - by)

    for py in range(min_y, max_y + 1):
        for px in range(min_x, max_x + 1):
            b1 = sign(px, py, x1, y1, x2, y2) < 0
            b2 = sign(px, py, x2, y2, x3, y3) < 0
            b3 = sign(px, py, x3, y3, x1, y1) < 0
            if b1 == b2 == b3:
                set_pixel(canvas, px, py, color)


def draw_icon() -> bytes:
    canvas = blank_canvas()
    fill_rounded_rect(canvas, 20, 20, 216, 216, 48, PAPER)
    fill_rounded_rect(canvas, 60, 46, 124, 166, 22, CARD)
    fill_triangle(canvas, [(146, 46), (184, 46), (184, 84)], ACCENT)
    fill_rect(canvas, 84, 92, 80, 10, INK)
    fill_rect(canvas, 84, 118, 62, 10, INK_SOFT)
    fill_rect(canvas, 84, 144, 70, 10, INK_SOFT)
    fill_rect(canvas, 84, 170, 52, 10, ACCENT)
    fill_circle(canvas, 74, 74, 9, ACCENT)
    fill_rect(canvas, 71, 55, 6, 10, ACCENT)
    fill_rect(canvas, 71, 84, 6, 10, ACCENT)
    fill_rect(canvas, 55, 71, 10, 6, ACCENT)
    fill_rect(canvas, 84, 71, 10, 6, ACCENT)
    return png_bytes(canvas)


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def png_bytes(canvas: list[list[tuple[int, int, int, int]]]) -> bytes:
    raw = bytearray()
    for row in canvas:
        raw.append(0)
        for red, green, blue, alpha in row:
            raw.extend((red, green, blue, alpha))
    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            png_chunk(b"IHDR", ihdr),
            png_chunk(b"IDAT", zlib.compress(bytes(raw), level=9)),
            png_chunk(b"IEND", b""),
        ]
    )


def ico_bytes(png_data: bytes) -> bytes:
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack(
        "<BBBBHHII",
        0,
        0,
        0,
        0,
        1,
        32,
        len(png_data),
        22,
    )
    return header + entry + png_data


def main() -> None:
    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    png_data = draw_icon()
    PNG_PATH.write_bytes(png_data)
    ICO_PATH.write_bytes(ico_bytes(png_data))
    print(f"Generated {PNG_PATH}")
    print(f"Generated {ICO_PATH}")


if __name__ == "__main__":
    main()

