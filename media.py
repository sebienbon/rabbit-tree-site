#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telecharge les medias Wix en qualite d'origine + extrait palette et polices."""
import json, os, re, sys, time, hashlib
from collections import Counter
from urllib.parse import urlparse, unquote
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SCRAPE = os.path.join(HERE, "scrape")
MEDIA = os.path.join(SCRAPE, "media")
HTMLDIR = os.path.join(SCRAPE, "html")
os.makedirs(MEDIA, exist_ok=True)

HDRS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Referer": "https://therabbittreegilim.wixsite.com/"}

inv = json.load(open(os.path.join(SCRAPE, "inventory.json"), encoding="utf-8"))

# 1) recuperer toutes les URLs medias, y compris celles des CSS inline que bs4 ne voit pas
urls = set()
for p, d in inv.items():
    for i in d["images"]:
        urls.add(i["url"])
for fn in os.listdir(HTMLDIR):
    h = open(os.path.join(HTMLDIR, fn), encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"https?://static\.wixstatic\.com/media/[^\s\"'()\\]+", h):
        urls.add(m.group(0))
    for m in re.finditer(r"https?://static\.parastorage\.com/[^\s\"'()\\]+", h):
        urls.add(m.group(0))

print("references medias trouvees:", len(urls))


def original(u):
    """enleve le transform /v1/fill/w_..,h_.. -> retourne l'original pleine resolution"""
    m = re.match(r"(https?://static\.wixstatic\.com/media/[^/]+?~mv2\.(?:jpg|jpeg|png|gif|webp))(?:/.*)?$", u, re.I)
    if m:
        return m.group(1)
    m = re.match(r"(https?://static\.wixstatic\.com/media/[^/]+\.(?:jpg|jpeg|png|gif|webp|mp4|mp3|svg))(?:/.*)?$", u, re.I)
    if m:
        return m.group(1)
    return None


targets = {}
for u in sorted(urls):
    o = original(u)
    if o:
        targets[o] = u
print("originaux distincts:", len(targets))

manifest = []
sess = requests.Session()
sess.headers.update(HDRS)
skipped = 0
for n, (o, ref) in enumerate(sorted(targets.items()), 1):
    name = unquote(urlparse(o).path).rsplit("/", 1)[-1]
    ext = os.path.splitext(name)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".mp4", ".mp3"):
        name += ".jpg"
    dest = os.path.join(MEDIA, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        skipped += 1
    else:
        try:
            r = sess.get(o, timeout=60)
            if r.status_code == 200 and len(r.content) > 200:
                open(dest, "wb").write(r.content)
            else:
                print("  !!", r.status_code, len(r.content), name)
                continue
        except Exception as e:
            print("  !! err", name, e)
            continue
    manifest.append({"file": name, "original_url": o, "size": os.path.getsize(dest) if os.path.exists(dest) else 0,
                     "page_refs": [p for p, d in inv.items() if any(x["url"].startswith(o) for x in d["images"])]})
    if n % 10 == 0:
        print("  {}/{}".format(n, len(targets)))
    time.sleep(0.15)

json.dump(manifest, open(os.path.join(SCRAPE, "media_manifest.json"), "w"), ensure_ascii=False, indent=1)
print("media telecharges:", len(manifest), "(deja la:", skipped, ")")

# 2) palette + polices depuis tout le HTML
allh = ""
for fn in os.listdir(HTMLDIR):
    allh += open(os.path.join(HTMLDIR, fn), encoding="utf-8", errors="ignore").read()

colors = Counter(re.findall(r"#[0-9a-fA-F]{6}\b", allh))
fonts = Counter(re.findall(r"font-family\s*:\s*([^;{}\"]+)", allh))
print("\nCOULEURS les plus frequentes:")
for c, k in colors.most_common(25):
    print("  ", c, k)
print("\nPOLICES:")
for f, k in fonts.most_common(20):
    print("  ", f.strip()[:80], k)

# les variables de theme Wix (palette du site)
for m in re.finditer(r"--color-([a-zA-Z0-9]+)\s*:\s*([^;]+)", allh):
    print("  theme color", m.group(1), m.group(2))
