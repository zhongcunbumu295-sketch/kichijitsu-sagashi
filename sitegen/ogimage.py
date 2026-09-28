"""SNSでシェアされたときのサムネイル（1200×630のPNG）を標準ライブラリだけで描く。

図柄: 生成り色の背景に、金色の太陽と朱色の鳥居。
"""
import struct
import zlib
from pathlib import Path

W, H = 1200, 630
BG = (247, 239, 226)
SUN = (238, 180, 68)
VERMILION = (200, 55, 45)
INK = (43, 37, 34)


def _pixel(x: float, y: float) -> tuple[int, int, int]:
    cx = 600
    dx = x - cx
    # 笠木（上の横木）: 両端が反り上がる
    t = min(abs(dx) / 300, 1.25)
    top = 148 - 34 * t ** 3
    if abs(dx) <= 330 and top <= y <= top + 12:
        return INK
    if abs(dx) <= 318 and top + 12 < y <= top + 44:
        return VERMILION
    # 島木（笠木の下）
    if abs(dx) <= 290 and 192 <= y <= 214:
        return VERMILION
    # 額束（中央の短い柱）
    if abs(dx) <= 16 and 214 <= y <= 262:
        return VERMILION
    # 貫（二本目の横木）
    if abs(dx) <= 270 and 262 <= y <= 288:
        return VERMILION
    # 柱（わずかに内側へ傾く）
    for side in (-1, 1):
        center = cx + side * (175 + (y - 214) * 0.045)
        if 214 <= y <= 560 and abs(x - center) <= 22:
            return VERMILION
    # 地面の線
    if 560 <= y <= 566 and abs(dx) <= 380:
        return INK
    # 太陽
    if (x - cx) ** 2 + (y - 330) ** 2 <= 175 ** 2:
        return SUN
    return BG


def _png(width: int, height: int, rows: list[bytes]) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + r for r in rows)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def write_og_image(path: Path) -> None:
    rows = []
    for y in range(H):
        row = bytearray()
        for x in range(W):
            row.extend(_pixel(x + 0.5, y + 0.5))
        rows.append(bytes(row))
    path.write_bytes(_png(W, H, rows))
