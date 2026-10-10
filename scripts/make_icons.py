"""PWA 아이콘 생성 (1회). python scripts/make_icons.py"""
from pathlib import Path

from PIL import Image, ImageDraw

WEB = Path(__file__).resolve().parent.parent / "web"
for size in (192, 512):
    img = Image.new("RGB", (size, size), "#0b7a3b")
    d = ImageDraw.Draw(img)
    s = size / 512
    # 확성기 모양 (안전영역 안쪽)
    d.polygon([(150 * s, 210 * s), (250 * s, 210 * s), (360 * s, 140 * s),
               (360 * s, 372 * s), (250 * s, 302 * s), (150 * s, 302 * s)], fill="white")
    d.rectangle([(180 * s, 302 * s), (230 * s, 372 * s)], fill="white")
    d.ellipse([(330 * s, 120 * s), (400 * s, 190 * s)], fill="#f5a623")
    img.save(WEB / ("icon-%d.png" % size))
print("ok")
