#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Image de partage (reseaux sociaux, WhatsApp...) 1200 x 630 : le logo dessine sur le parchemin.

Usage : python3 og_image.py chemin/vers/alice.ttf
(la police Alice in Wonderland en TTF ; fonts/ ne contient que le woff2 du site,
 la conversion se fait avec fontTools : TTFont(woff2).flavor = None ; save(ttf)).
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
W, H = 1200, 630
INK = (59, 56, 43)


def main(ttf):
    paper = Image.open(os.path.join(IMG, "paper-bg.webp")).convert("RGB")
    # le parchemin d'origine est vertical : on le recadre en paysage en gardant ses bords plus sombres
    pw, ph = paper.size
    scale = max(W / pw, H / ph)
    paper = paper.resize((int(pw * scale) + 1, int(ph * scale) + 1), Image.LANCZOS)
    x0, y0 = (paper.width - W) // 2, (paper.height - H) // 2
    bg = paper.crop((x0, y0, x0 + W, y0 + H))
    # vignette douce, comme les bords du fond Wix
    vign = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(vign)
    d.rectangle((60, 50, W - 60, H - 50), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(70))
    dark = Image.new("RGB", (W, H), (200, 160, 70))
    bg = Image.composite(bg, Image.blend(bg, dark, 0.35), vign)

    logo = Image.open(os.path.join(IMG, "logo-dessin-png.webp")).convert("RGBA")
    lh = 500
    logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)
    bg.paste(logo, (120, (H - lh) // 2 + 6), logo)

    draw = ImageDraw.Draw(bg)
    big = ImageFont.truetype(ttf, 104)
    mid = ImageFont.truetype(ttf, 78)
    small = ImageFont.truetype(ttf, 40)
    tx = 120 + logo.width + 70
    draw.text((tx, 150), "The Rabbit Tree", font=big, fill=INK)
    draw.text((tx + 4, 270), "Hostel", font=mid, fill=INK)
    draw.line((tx + 6, 382, tx + 520, 378), fill=INK, width=3)
    draw.text((tx + 6, 404), "Gili Meno  ~  Lombok", font=small, fill=INK)
    out = os.path.join(IMG, "og-share.jpg")
    bg.save(out, "JPEG", quality=86, optimize=True, progressive=True)
    print(out, os.path.getsize(out) // 1024, "Ko")


if __name__ == "__main__":
    main(sys.argv[1])
