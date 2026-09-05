# -*- coding: utf-8 -*-
"""生成应用图标：渐变圆角底 + 胶片齿孔 + 「舞」字"""
from PIL import Image, ImageDraw, ImageFont
import os

def make_icon(size):
    S = 4
    W = size * S
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = W // 5
    grad = Image.new('RGBA', (W, W))
    gd = ImageDraw.Draw(grad)
    c1, c2 = (255, 77, 141), (124, 92, 255)
    for y in range(W):
        t = y / W
        gd.line([(0, y), (W, y)], fill=(int(c1[0] + (c2[0]-c1[0])*t),
                                        int(c1[1] + (c2[1]-c1[1])*t),
                                        int(c1[2] + (c2[2]-c1[2])*t), 255))
    mask = Image.new('L', (W, W), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, W-1, W-1], radius=r, fill=255)
    img.paste(grad, (0, 0), mask)
    hole = max(2, int(W * 0.018))
    n = 7
    for i in range(n):
        x = int(W * (i + 0.5) / n) - hole // 2
        for yy in (int(W * 0.045), int(W * 0.955 - hole)):
            d.rounded_rectangle([x, yy, x + hole, yy + hole], radius=hole // 3, fill=(255, 255, 255, 190))
    font = None
    for p in (r'C:\Windows\Fonts\msyhbd.ttc', r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf'):
        try:
            font = ImageFont.truetype(p, int(W * 0.52))
            break
        except Exception:
            pass
    if font:
        bbox = d.textbbox((0, 0), '舞', font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((W - tw) / 2 - bbox[0], (W - th) / 2 - bbox[1] + W * 0.015), '舞',
               font=font, fill=(255, 255, 255, 255))
    else:
        d.ellipse([W*0.3, W*0.3, W*0.7, W*0.7], fill=(255, 255, 255, 255))
    return img.resize((size, size), Image.LANCZOS)

os.makedirs('icons', exist_ok=True)
make_icon(512).save('icons/icon-512.png')
make_icon(192).save('icons/icon-192.png')
print('icons done:', os.listdir('icons'))
