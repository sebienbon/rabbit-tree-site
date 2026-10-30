#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optimise les medias Wix (WebP + redimensionne) et produit un manifeste nom->fichier."""
import json, os, re, io
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "scrape", "media")
DST = os.path.join(HERE, "site", "images")
os.makedirs(DST, exist_ok=True)

inv = json.load(open(os.path.join(HERE, "scrape", "inventory.json"), encoding="utf-8"))

# alt text -> nom de fichier lisible
alts = {}
for p, d in inv.items():
    for i in d["images"]:
        u = i["url"].split("/v1/")[0].split("/fill/")[0].split("/crop/")[0]
        stem = u.rsplit("/", 1)[-1]
        a = (i["alt"] or "").strip()
        if a and stem not in alts and "(fond)" not in a:
            alts[stem] = a

MAXW = {"bg": 1600, "art": 900, "photo": 1200, "icon": 128}


def slug(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return s[:42] or "img"


def kind_of(fn, w, h, size):
    if size < 25000 and w <= 200:
        return "icon"
    if "2668bb99f38848beb3cf1f770737312f" in fn:
        return "bg"
    if w * h > 1200 * 900:
        return "photo"
    return "art"


manifest = {}
report = []
for fn in sorted(os.listdir(SRC)):
    src = os.path.join(SRC, fn)
    if not fn.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        continue
    try:
        im = Image.open(src)
        im.load()
    except Exception as e:
        report.append("SKIP {} ({})".format(fn, e))
        continue
    w, h = im.size
    size = os.path.getsize(src)
    k = kind_of(fn, w, h, size)
    limit = MAXW[k]
    if w > limit:
        im = im.resize((limit, int(h * limit / w)), Image.LANCZOS)
    has_alpha = im.mode in ("RGBA", "LA", "P") and (im.mode != "P" or "transparency" in im.info)
    im = im.convert("RGBA" if has_alpha else "RGB")
    alt = alts.get(fn, "")
    base = slug(alt) if alt else "img-" + slug(fn.replace("~mv2", "").rsplit(".", 1)[0])[-14:]
    name = base + ".webp"
    n, i = name, 2
    while n in manifest:
        n = "{}-{}.webp".format(base, i)
        i += 1
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=80 if not has_alpha else 84, method=6)
    if buf.tell() > size:  # ne pas alourdir
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=68, method=6)
    open(os.path.join(DST, n), "wb").write(buf.getvalue())
    manifest[fn] = {"file": n, "kind": k, "orig_w": w, "orig_h": im.size[0], "disp_h": im.size[1],
                    "alpha": has_alpha, "alt": alt, "bytes": buf.tell(), "orig_bytes": size}
    report.append("{:8.0f}K -> {:6.0f}K  {:22} {}  [{}]".format(size / 1024, buf.tell() / 1024, k, n, im.size))

json.dump(manifest, open(os.path.join(HERE, "site", "images_manifest.json"), "w"), ensure_ascii=False, indent=1)
tot = sum(v["bytes"] for v in manifest.values())
print("images optimisees:", len(manifest), "| poids total: {:.1f} Mo".format(tot / 1048576))
print("\nTOP 15 les plus lourdes:")
for fn, v in sorted(manifest.items(), key=lambda x: -x[1]["bytes"])[:15]:
    print("  {:7.0f}K  {}  alt={!r}".format(v["bytes"] / 1024, v["file"], v["alt"][:40]))
open(os.path.join(HERE, "scrape", "optimize_report.txt"), "w").write("\n".join(report))
