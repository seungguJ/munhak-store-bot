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
# 안드로이드 상태바용 배지: 투명 배경 + 흰 실루엣 (컬러 아이콘은 흰 네모로 보임)
b = 96
img = Image.new("RGBA", (b, b), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
s = b / 512
d.polygon([(110 * s, 200 * s), (230 * s, 200 * s), (380 * s, 110 * s),
           (380 * s, 402 * s), (230 * s, 312 * s), (110 * s, 312 * s)], fill="white")
d.rectangle([(150 * s, 312 * s), (210 * s, 400 * s)], fill="white")
img.save(WEB / "badge-96.png")
print("ok")
