#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventaire du site Wix public : textes, images, liens, structure."""
import json, os, re, sys, time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

BASE = "https://therabbittreegilim.wixsite.com"
START = BASE + "/home"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "scrape")
HDRS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

sess = requests.Session()
sess.headers.update(HDRS)


def norm(href):
    if not href:
        return None
    u = urlparse(urljoin(START, href))
    if u.netloc and "wixsite.com" not in u.netloc:
        return None
    p = u.path.rstrip("/")
    if not p:
        return None
    if not p.startswith("/home"):
        return None
    return p


def fetch(path):
    fname = os.path.join(OUT, "html", path.strip("/").replace("/", "__") + ".html")
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    if os.path.exists(fname):
        return open(fname, encoding="utf-8", errors="ignore").read()
    try:
        r = sess.get(BASE + path, timeout=45, allow_redirects=True)
    except Exception as e:
        print("  !! erreur", path, e, file=sys.stderr)
        return None
    if r.status_code != 200:
        print("  !! HTTP", r.status_code, path, file=sys.stderr)
        return None
    with open(fname, "w", encoding="utf-8") as fh:
        fh.write(r.text)
    time.sleep(1.0)
    return r.text


def clean(s):
    return " ".join((s or "").split())


def extract(path, html):
    soup = BeautifulSoup(html, "lxml")
    page = {
        "path": path,
        "title": clean(soup.title.string) if soup.title else "",
        "meta_description": "",
        "headings": [],
        "texts": [],
        "images": [],
        "links": [],
    }
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        page["meta_description"] = clean(md["content"])

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    seen_text = set()
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "li", "span", "div", "a", "button"]):
        did = el.get("data-id") or el.get("id") or ""
        txt = clean(el.get_text(" ", strip=True))
        if not txt or len(txt) < 2:
            continue
        # ne garder que le noeud le plus externe d'un bloc de texte
        parent = el.find_parent(["h1", "h2", "h3", "h4", "h5", "p", "li", "span", "div", "a", "button"])
        key = txt[:120]
        if key in seen_text or (parent is not None and el.name not in ("h1", "h2", "h3", "h4", "h5", "p")):
            continue
        seen_text.add(key)
        rec = {"data_id": did, "tag": el.name, "text": txt}
        if el.name in ("h1", "h2", "h3", "h4", "h5"):
            page["headings"].append(rec)
        else:
            page["texts"].append(rec)

    imgs = {}
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if "wixstatic" in src:
            imgs.setdefault(src, {"alt": clean(img.get("alt", "")), "w": img.get("width", "")})
    for m in re.finditer(r"url\(([^)]*?)\)", html):
        u = m.group(1).strip("'\"")
        if "wixstatic" in u:
            imgs.setdefault(u, {"alt": "(fond)", "w": ""})
    page["images"] = [{"url": k, "alt": v["alt"], "width": v["w"]} for k, v in imgs.items()]

    for a in soup.find_all("a", href=True):
        page["links"].append({
            "text": clean(a.get_text(" ", strip=True)),
            "href": a["href"],
            "internal": ("wixsite.com" in a["href"]) or a["href"].startswith("/"),
        })
    return page


def main():
    print("1) accueil...")
    home = fetch("/home")
    if not home:
        print("ECHEU: /home inaccessible")
        return 1

    soup = BeautifulSoup(home, "lxml")
    paths = {"/home"}
    for a in soup.find_all("a", href=True):
        n = norm(a["href"])
        if n:
            paths.add(n)
    paths = sorted(paths)
    print("2) {} pages:\n   {}".format(len(paths), "\n   ".join(paths)))

    inventory = {}
    for p in paths:
        print("3) extraction", p)
        h = fetch(p)
        if h:
            inventory[p] = extract(p, h)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "inventory.json"), "w", encoding="utf-8") as fh:
        json.dump(inventory, fh, ensure_ascii=False, indent=1)

    lines = []
    bar = "=" * 72
    for p, d in inventory.items():
        lines.append(bar)
        lines.append("PAGE: " + p)
        lines.append("TITRE: " + d["title"])
        if d["meta_description"]:
            lines.append("META: " + d["meta_description"])
        lines.append(bar)
        if d["headings"]:
            lines.append("-- TITRES --")
            for h in d["headings"]:
                lines.append("  [{}] {}".format(h["tag"], h["text"]))
        if d["texts"]:
            lines.append("-- TEXTES --")
            for t in d["texts"]:
                lines.append("  ({}) {}".format(t["data_id"], t["text"]))
        lines.append("-- IMAGES ({}) --".format(len(d["images"])))
        for i in d["images"]:
            lines.append("  {} | alt={}".format(i["url"], i["alt"]))
        lines.append("-- LIENS ({}) --".format(len(d["links"])))
        for l in d["links"]:
            lines.append("  {!r} -> {}".format(l["text"], l["href"]))
        lines.append("")
    with open(os.path.join(OUT, "rapport.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("\nOK -> scrape/inventory.json + scrape/rapport.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
