#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valide le site genere : liens internes, images, poids, titles, hrefs vides."""
import os, re, sys
from urllib.parse import urlparse, unquote
from html.parser import HTMLParser

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.title = ""
        self.in_title = False
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.refs.append(("href", a["href"]))
        if tag in ("img", "source", "link") and a.get("src"):
            self.refs.append(("src", a["src"]))
        if tag == "link" and a.get("href") and a.get("rel") != "stylesheet":
            self.refs.append(("src", a["href"]))
        if tag == "link" and a.get("href") and "stylesheet" in (a.get("rel") or ""):
            self.refs.append(("src", a["href"]))
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1 += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


pages, problems = [], []
for root, _, files in os.walk(DIST):
    for f in files:
        if f.endswith(".html"):
            pages.append(os.path.join(root, f))

for pg in sorted(pages):
    rel = os.path.relpath(pg, DIST)
    html = open(pg, encoding="utf-8").read()
    s = Scan()
    s.feed(html)
    if s.h1 != 1:
        problems.append("{} : {} <h1>".format(rel, s.h1))
    if not s.title.strip():
        problems.append("{} : title vide".format(rel))
    for kind, ref in s.refs:
        r = unquote(ref.strip())
        if r.startswith(("http:", "https:", "mailto:", "tel:", "#", "data:", "//")):
            continue
        if r in ("", "/"):
            problems.append("{} : {} vide".format(rel, kind))
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(pg), r.split("#")[0].split("?")[0]))
        if os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.exists(target):
            problems.append("{} : {} manquant -> {}".format(rel, kind, r))
        elif target.endswith(".html") and os.path.isdir(os.path.join(DIST, r.split("#")[0].strip("/"))) and not r.endswith("/"):
            problems.append("{} : lien sans / final -> {}".format(rel, r))

# assets non utilises
used = set()
for pg in pages:
    html = open(pg, encoding="utf-8").read()
    for m in re.finditer(r"(?:src|href)=\"([^\"]+)\"", html):
        used.add(os.path.basename(m.group(1).split("?")[0]))
cssp = os.path.join(DIST, "css", "style.css")
if os.path.exists(cssp):
    for m in re.finditer(r"url\([\"']?[^)\"']*?images/([\w.\-]+\.webp)", open(cssp, encoding="utf-8").read()):
        used.add(m.group(1))
imgdir = os.path.join(DIST, "images")
allimg = set(os.listdir(imgdir))
unused = sorted(allimg - used)
unused_big = [f for f in unused if os.path.getsize(os.path.join(imgdir, f)) > 60000]

tot = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(DIST) for f in fs)
print("pages:", len(pages), "| poids total du site: {:.1f} Mo".format(tot / 1048576))
print("images dans dist:", len(allimg), "| non referencees:", len(unused), "(dont >60Ko: {})".format(len(unused_big)))
print("\nPROBLEMES ({}):".format(len(problems)))
for p in problems[:60]:
    print("  -", p)
if unused_big:
    print("\nGROS FICHIERS INUTILES (a retirer du depot):")
    for f in unused_big[:25]:
        print("   {:6.0f}K  {}".format(os.path.getsize(os.path.join(imgdir, f)) / 1024, f))
