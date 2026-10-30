#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cree les petits assets que le site nest pas en train de telecharger."""
import os, random, json
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
SRC = os.path.join(HERE, "..", "scrape", "media")
os.makedirs(IMG, exist_ok=True)
random.seed(7)

# 1) texture papier tileable, recoupe dans le fond original
bg = Image.open(os.path.join(SRC, "06d726_2668bb99f38848beb3cf1f770737312f~mv2.jpg")).convert("RGB")
w, h = bg.size
side = min(w, h) // 3
box = (int(w * 0.05), int(h * 0.05), int(w * 0.05) + side, int(h * 0.05) + side)
tile = bg.crop(box).resize((520, 520), Image.LANCZOS)
tile = tile.filter(ImageFilter.GaussianBlur(0.6))
tile.save(os.path.join(IMG, "paper.webp"), "WEBP", quality=72, method=6)
print("paper.webp", tile.size)

# 2) trait souligne dessine a la main
im = Image.new("RGBA", (400, 26), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
pts = [(6, 15 + random.uniform(-3, 3))]
for x in range(10, 396, 8):
    pts.append((x, 13 + random.uniform(-4, 4) + 2 * (x / 400.0)))
d.line(pts, fill=(28, 26, 23, 210), width=3, joint="curve")
d.line([(p[0], p[1] + 5) for p in pts][::3], fill=(28, 26, 23, 90), width=1)
im.save(os.path.join(IMG, "underline.webp"), "WEBP", quality=90)
print("underline.webp", im.size)

# 3) arbre de la page Rooms (copie renomme de loriginal)
mfile = os.path.join(HERE, "images_manifest.json")
man = json.load(open(mfile, encoding="utf-8")) if os.path.exists(mfile) else {}
src_tree = os.path.join(IMG, "img-d6c5f97fea97cf.webp")
if os.path.exists(src_tree):
    Image.open(src_tree).save(os.path.join(IMG, "tree-rooms.webp"), "WEBP", quality=84, method=6)
    print("tree-rooms.webp ok")

# 4) visuel Rinjani : la plus grande photo de la page du trek
inv = json.load(open(os.path.join(HERE, "..", "scrape", "inventory.json"), encoding="utf-8"))
cands = []
for path in ("/home/tours/rinjanitrek", "/home/tours", "/home/tours/komodotrip", "/home/gallery"):
    for i in inv.get(path, {}).get("images", []):
        u = i["url"]
        s = u.split("/v1/")[0].split("/fill/")[0].split("/crop/")[0].rsplit("/", 1)[-1]
        m = man.get(s)
        if m and m["kind"] in ("photo", "art") and m["bytes"] > 40000:
            cands.append((m["bytes"], m["file"]))
if cands:
    cands.sort(reverse=True)
    best = cands[0][1]
    Image.open(os.path.join(IMG, best)).save(os.path.join(IMG, "rinjani.webp"), "WEBP", quality=80, method=6)
    print("rinjani.webp <-", best)
else:
    print("rinjani.webp AUCUNE PHOTO (a verifier)")

tot = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
print("dossier images: {} fichiers, {:.1f} Mo".format(len(os.listdir(IMG)), tot / 1048576))
