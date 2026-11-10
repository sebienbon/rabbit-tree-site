# -*- coding: utf-8 -*-
"""Genere le site statique The Rabbit Tree Hostel (content.py + inventory.json -> HTML)."""
import json, os, re, shutil, sys
from content import (HOSTEL, INTRO, MAP_SPOTS, MAP_W, MAP_H, MAP_MW, MAP_MH, MAP_TITLE, ROOMS, TREE_EXTRA,
                     BOOKING_NOTE, PAGE_MEDIA, NAV, INFO_LINKS, BEDS24_PROP, BEDS24_ROOM)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INV = json.load(open(os.path.join(ROOT, "scrape", "inventory.json"), encoding="utf-8"))
MAN = json.load(open(os.path.join(HERE, "images_manifest.json"), encoding="utf-8"))
_MAN_BY_FILE = {v["file"]: (v["orig_w"], v["orig_h"]) for v in MAN.values()}
DIST = os.path.join(HERE, "dist")
FAVICON = "tree-home.webp"
# Adresse publique du site : sert aux balises de partage (og:image doit etre une URL absolue).
# A remplacer par le vrai nom de domaine le jour de la mise en ligne.
SITE_URL = "https://therabbittree.page/"
OG_IMAGE = "og-share.jpg"
# Visuels charges par le JavaScript (vortex) : a garder meme si aucun HTML ne les cite.
KEEP_IMAGES = set()

# ------------------------------------------------------------------ helpers
def stem(url):
    return url.split("/v1/")[0].split("/fill/")[0].split("/crop/")[0].rsplit("/", 1)[-1]


_EXCLUDE_PHOTOS = {"old-fashion-boat.webp"}

# optimize.py classe "art" tout fichier qui ne depasse pas strictement 1200x900,
# or plusieurs vraies photos de chambres font exactement 1200x900 cote Wix :
# elles etaient donc filtrees par photos_of (ecart E de la revue T-20261031-01).
# Liste etablie visuellement une par une (vraies photos ; dessins, plans et
# logos comme pillow-room-on-pillow-png ou bird-nest-room-png en restent exclus).
ART_PHOTOS = {"birdnest1.webp", "birdnest2.webp", "flyboat.webp", "flying-boat.webp",
              "family1.webp", "family2.webp", "twin-rabbit-cave.webp", "toilet-white-house.webp"}


def photos_of(path, min_bytes=25000, limit=30):
    if path not in INV:
        return []
    out, seen = [], set()
    for i in INV[path]["images"]:
        u = i["url"]
        if "wixstatic" not in u:
            continue
        s = stem(u)
        m = MAN.get(s)
        if not m or m["file"] in seen or (m["kind"] != "photo" and m["file"] not in ART_PHOTOS) or m["bytes"] < min_bytes:
            continue
        if m["file"] in _EXCLUDE_PHOTOS or m.get("opaque", 1.0) < 0.9:
            continue
        seen.add(m["file"])
        out.append({"file": m["file"], "alt": (i["alt"] or "The Rabbit Tree Hostel, Gili Meno").strip()})
        if len(out) >= limit:
            break
    return out


# Les vraies photos de la collection "Gallery" de Wix (chargees cote client, hors SSR).
GALLERY_KEYS = [
    "06d726_af2ed40fa79340e1b4022a04b217d498~mv2.jpg",
    "06d726_3e4abde7f5694401afbc50b66a9e4795~mv2.jpg",
    "06d726_168d0698e35c4598a6aa07d0d9083df4~mv2.jpg",
    "06d726_39a4416b43d642b980e6c5eceaacc867~mv2.jpg",
    "06d726_0750fa7ccf7a4ec78688d3f66ef13ab4~mv2.jpg",
    "06d726_4c4db81b6f3d41458b50797cfb416657~mv2.jpg",
]


def _by_file(file):
    for k, v in MAN.items():
        if v["file"] == file:
            return {"file": file, "alt": (v.get("alt") or "The Rabbit Tree Hostel, Gili Meno").strip()}
    return None


def all_photos(include_activities=True):
    """Union de toutes les vraies photos : galerie dediee + chambres (+ activites)."""
    out, seen = [], set()
    for k in GALLERY_KEYS:
        m = MAN.get(k)
        if m and m["file"] not in seen:
            seen.add(m["file"])
            out.append({"file": m["file"], "alt": (m.get("alt") or "The Rabbit Tree Hostel, Gili Meno").strip()})
    for r in ROOMS:
        src = {"pillow-room": "copy-of-bola-bola", "passion-room": "lapassion", "rabbit-dream": "rabbitdream", "monk": None}.get(r["slug"], r["slug"])
        path = "/home/" + (src or r["slug"]) if src else None
        for p in photos_of(path, limit=9) if path and path in INV else []:
            if p["file"] not in seen:
                seen.add(p["file"])
                out.append(p)
    if include_activities:
        for f, a in PAGE_MEDIA.get("activities", {}).get("gallery", []):
            if f not in seen:
                seen.add(f)
                out.append({"file": f, "alt": a})
    return out


import re as _re
PRICE_TOKEN = _re.compile(r"\[\[\$([^|\]]+)\|([^\]]+)\]\]")


def price_spans(html):
    """[[$-Horse Riding|400K]] -> un prix que main.js remplace par celui de la feuille Data activities.
    La valeur de repli reste dans la page (Google, visiteurs sans JavaScript)."""
    def sub(m):
        key, fallback = m.group(1), m.group(2)
        div = "1"
        if "/" in key and key.rsplit("/", 1)[1].isdigit():
            key, div = key.rsplit("/", 1)
        return '<span class="px" data-price="{}" data-div="{}">{}</span>'.format(
            key.replace('"', "&quot;"), div, fallback)
    return PRICE_TOKEN.sub(sub, html)


def esc(s):
    # les entites deja ecrites (&rarr;, &harr;...) restent telles quelles
    return re.sub(r"&(?![a-zA-Z]+;|#\d+;)", "&amp;", str(s)).replace("<", "&lt;").replace(">", "&gt;")


def para(text, cls=""):
    parts = [p.strip() for p in str(text).split("\n\n") if p.strip()]
    return "".join('<p class="{}">{}</p>'.format(cls, esc(p)) if cls else "<p>{}</p>".format(esc(p)) for p in parts)


def fiche(kicker, title, img, price, chips, text, links=()):
    """Une fiche d'activite : photo ronde, titre, etiquette de prix, reperes rapides, texte (avec **surlignage**)."""
    hl = lambda s: re.sub(r"\*\*(.+?)\*\*", r'<mark>\1</mark>', esc(s))
    tag = '<span class="tag">{}{}</span>'.format(price[0], '<small>{}</small>'.format(esc(price[1])) if price[1] else "")
    return ('<article class="fiche"><img class="fiche-img" src="images/{}" alt="{}" loading="lazy">'
            '<div class="fiche-body"><p class="kicker">{}</p><h3>{}</h3>{}'
            '<ul class="chips">{}</ul><p>{}</p>{}</div></article>').format(
        img, esc(title), esc(kicker), esc(title), tag, "".join("<li>{}</li>".format(c) for c in chips), hl(text),
        ('<p class="fiche-links">' + "".join('<a href="{}"{}>{}</a>'.format(
            u, ' target="_blank" rel="noopener"' if u.startswith("http") else "", esc(t)) for t, u in links) + "</p>") if links else "")


def ul(items):
    return "<ul>" + "".join("<li>{}</li>".format(i if i.startswith("<") else esc(i)) for i in items) + "</ul>"


def banner_of(key):
    """Photo pleine largeur, toujours montree en entier (jamais rognee).
    Hauteur limitee a ~560 px : une photo haute est simplement moins large."""
    b = PAGE_MEDIA.get(key, {}).get("banner")
    if not b:
        return ""
    f, a = b[0], b[1]
    from PIL import Image
    with Image.open(os.path.join(HERE, "images", f)) as im:
        w, h = im.size
    maxw = min(1080, int(560 * w / h))
    return ('<div class="banner" style="max-width:{m}px"><img src="images/{f}" alt="{a}" width="{w}" height="{h}" '
            'loading="eager"></div>').format(m=maxw, f=f, a=esc(a), w=w, h=h)


def gal_of(key, title="In pictures"):
    items = PAGE_MEDIA.get(key, {}).get("gallery", [])
    if not items:
        return ""
    h = "<h2>{}</h2>".format(title) if title else ""
    return "<section>" + h + strip_html(items) + "</section>"


def figs_of(key, title=""):
    items = PAGE_MEDIA.get(key, {}).get("gallery", [])
    if not items:
        return ""
    h = "<h2>{}</h2>".format(title) if title else ""
    return ("<section>" + h + '<div class="figs">' + "".join(
        '<figure><a href="images/{f}" data-lb><img src="images/{f}" alt="{a}" loading="lazy"></a>'
        '<figcaption>{a}</figcaption></figure>'.format(f=f, a=esc(a)) for f, a in items) + "</div></section>")


def deco_of(key):
    items = PAGE_MEDIA.get(key, {}).get("deco", [])
    if not items:
        return ""
    return ('<div class="deco">' + "".join(
        '<span class="deco-item"><img src="images/{f}" alt="{a}" loading="lazy"><em>{a}</em></span>'.format(f=f, a=esc(a))
        for f, a in items) + "</div>")


def strip_html(items, swap=False):
    out = []
    for i, p in enumerate(items):
        f, a = (p["file"], p["alt"]) if isinstance(p, dict) else p
        if swap:
            out.append('<a href="images/{f}" data-full="images/{f}" class="{c}">'
                       '<img src="images/{f}" alt="{a}" loading="lazy"></a>'.format(
                           f=f, a=esc(a), c="active" if i == 0 else ""))
        else:
            w, h = img_size(f)
            out.append('<a href="images/{f}" data-lb><img src="images/{f}" alt="{a}" width="{w}" height="{h}" loading="lazy"></a>'.format(
                f=f, a=esc(a), w=w, h=h))
    return '<div class="strip"{}>'.format("" if swap else " data-cflow") + "".join(out) + "</div>"


_SIZES = {}
def img_size(f):
    """Dimensions reelles d'une image (pour le carrousel : jamais de photo coupee)."""
    if f not in _SIZES:
        try:
            from PIL import Image
            _SIZES[f] = Image.open(os.path.join(HERE, "images", f)).size
        except Exception:
            _SIZES[f] = (4, 3)
    return _SIZES[f]


def table(headers, rows):
    h = "".join("<th>{}</th>".format(esc(c)) for c in headers)
    b = "".join("<tr>" + "".join("<td{}>{}</td>".format(' class="price"' if isinstance(c, tuple) else "",
                  c[0] if isinstance(c, tuple) else esc(c)) for c in r) + "</tr>" for r in rows)
    return '<div class="table-wrap"><table><thead><tr>{}</tr></thead><tbody>{}</tbody></table></div>'.format(h, b)


# ------------------------------------------------------------------ gabarit
HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preload" href="{font}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{css}">
<link rel="icon" href="{fav}" type="image/webp">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Rabbit Tree Hostel">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Rabbit Tree Hostel, Gili Meno: the hand drawn tree">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{og}">
<meta name="theme-color" content="#f2d98c">
<script>try{{var v=JSON.parse(sessionStorage.getItem("rt-vortex")||"null");var nv=performance.getEntriesByType&&performance.getEntriesByType("navigation")[0];if(nv&&nv.type==="back_forward")v=null;if(v&&Date.now()-v.t<4000&&!(window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches)){{document.documentElement.className+=" rt-arrive";setTimeout(function(){{document.documentElement.classList.remove("rt-arrive")}},2500)}}}}catch(e){{}}</script>
</head>
<body class="{bodyclass}">
<a class="skip" href="#main">Skip to content</a>
<header class="nav" id="nav">
  <a class="nav-brand" href="{brand}" data-vortex>The Rabbit Tree<span>Gili Meno</span></a>
  <button class="nav-toggle" aria-expanded="false" aria-controls="navlinks">Menu</button>
  <ul class="nav-links" id="navlinks">{nav}</ul>
  <a class="nav-cta" href="{cta}">Book a room</a>
</header>
<main id="main">
"""

FOOT = """</main>
<footer>
  <div class="foot-in">
    <div><h3>Call us</h3><p><a href="tel:{tel}">{phone}</a><br><a href="{wa}">WhatsApp us</a></p></div>
    <div><h3>Find us</h3><p><a href="{maps}">{addr}</a></p></div>
    <div><h3>Email us</h3><p><a href="mailto:{mail}">{mail}</a></p>
      <div class="socials"><a href="{ig}" aria-label="Instagram">IG</a><a href="{fb}" aria-label="Facebook">FB</a>
      <a href="{ta}" aria-label="Tripadvisor">TA</a><a href="{wa}" aria-label="WhatsApp">WA</a>
      <a href="{bk}" aria-label="Booking.com">B.</a><a href="{hw}" aria-label="Hostelworld">HW</a></div></div>
    <div><h3>Good to know</h3><p>{info}</p></div>
  </div>
  <div class="foot-note"><span>&copy;2017&ndash;2026 The Rabbit Tree Hostel</span><span>Gili Meno &mdash; {phone}</span></div>
</footer>
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Photo"><button class="x" aria-label="Close">&times;</button><img alt=""></div>
<script src="{js}"></script>
</body>
</html>"""


def render(rel_path, title, body, desc="", bodyclass="page"):
    depth = rel_path.count("/")
    pre = "../" * depth
    cur = "/" + rel_path.rsplit("index.html", 1)[0]
    items = []
    for slug, label, href in NAV:
        on = ' aria-current="page"' if href == cur else ""
        items.append('<li><a href="{}{}"{}>{}</a></li>'.format(pre, href.lstrip("/"), on, label))
    info = " &middot; ".join('<a href="{}{}">{}</a>'.format(pre, h.lstrip("/"), t) for _, t, h in INFO_LINKS)
    hrefs = {s: h for s, _, h in NAV}
    hrefs.update({s: h for s, _, h in INFO_LINKS})
    hrefs["home"] = "/"
    body = re.sub(r"\[\[([\w-]+)\]\]",
                  lambda m: pre + hrefs[m.group(1)].lstrip("/") if m.group(1) in hrefs else "#",
                  body)
    if pre:
        body = body.replace('src="images/', 'src="' + pre + 'images/')
        body = body.replace('href="images/', 'href="' + pre + 'images/')
    head = HEAD.format(title=esc(title), desc=esc(desc or DEFAULT_DESC), css=pre + "css/style.css?v=38",
                       fav=pre + "images/" + FAVICON, brand=pre, nav="".join(items),
                       cta=pre + "reservations/", bodyclass=bodyclass, font=pre + "fonts/alice-in-wonderland.woff2",
                       og=SITE_URL + "images/" + OG_IMAGE,
                       url=SITE_URL + rel_path.rsplit("index.html", 1)[0].replace("404.html", ""))
    foot = FOOT.format(tel=HOSTEL["phone_tel"], phone=esc(HOSTEL["phone_display"]), wa=HOSTEL["whatsapp"],
                       maps=HOSTEL["maps"], addr=esc(HOSTEL["address"]), mail=HOSTEL["email"],
                       ig=HOSTEL["instagram"], fb=HOSTEL["facebook"], ta=HOSTEL["tripadvisor"],
                       info=info, js=pre + "js/main.js?v=34", bk=HOSTEL["booking"], hw=HOSTEL["hostelworld"])
    return head + body + foot


DEFAULT_DESC = ("The Rabbit Tree Hostel, Gili Meno: creative rooms, a ball pit bedroom, cheap boats "
                "to and from Bali and Lombok, daily activities and Komodo or Rinjani adventures.")


STATIC_PRICE = re.compile(r"(?<![\w.,/-])(\d{1,3}(?:[.,]\d{3})*\s?(?:K|IDR)|Rp\s?\d{1,3}(?:[.,]\d{3})+)(?![\w])")


def static_prices(html):
    """Les prix ecrits en dur (40K, 25K, 150,000 IDR...) prennent aussi l'etiquette verte, dans <main> seulement."""
    a = html.find("<main"); z = html.find("</main>")
    if a < 0 or z < 0:
        return html
    main = html[a:z]
    out, depth = [], 0
    for part in re.split(r"(<[^>]+>)", main):
        if part.startswith("<"):
            if re.match(r'<span class="px"', part): depth += 1
            elif depth and part == "</span>": depth -= 1
            if re.match(r"<(script|style|title)", part): depth += 100
            if re.match(r"</(script|style|title)", part): depth -= 100
            out.append(part)
        elif depth:
            out.append(part)
        else:
            out.append(STATIC_PRICE.sub(r'<span class="px">\1</span>', part))
    return html[:a] + "".join(out) + html[z:]


def write(rel_path, title, body, desc="", bodyclass="page"):
    out = os.path.join(DIST, rel_path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(static_prices(price_spans(render(rel_path, title, body, desc, bodyclass))))
    return rel_path


def head(title, sub=""):
    return ('<div class="page-head"><h1>{}</h1>'.format(title) +
            ('<div class="lead">{}</div>'.format(sub) if sub else "") +
            '<div class="rule"></div></div>')


# ============================================================ ACCUEIL
def _box(d, W, H):
    l, t, w, h = d
    return "{:.3f}".format(100.0 * l / W), "{:.3f}".format(100.0 * t / H), \
           "{:.3f}".format(100.0 * w / W), "{:.3f}".format(100.0 * h / H)


def _vars(spot):
    l, t, w, h = _box(spot["d"], MAP_W, MAP_H)
    ml, mt, mw, mh = _box(spot["m"], MAP_MW, MAP_MH)
    cx, cy = spot.get("cap", (50, 100))
    mcx, mcy = spot.get("mcap", (50, 100))
    return ("--l:{};--t:{};--w:{};--h:{};--ml:{};--mt:{};--mw:{};--mh:{};--cx:{}%;--cy:{}%;"
            "--mcx:{}%;--mcy:{}%").format(l, t, w, h, ml, mt, mw, mh, cx, cy, mcx, mcy)


def build_home():
    """L'accueil d'origine : une seule scene dessinee, le titre en haut, le texte en bas. Pas de menu."""
    spots = []
    for s in MAP_SPOTS:
        fx = (" fx-" + s["fx"]) if s.get("fx") else ""
        img = '<img src="images/{art}" alt="{alt}" loading="eager" draggable="false">'.format(
            art=s["art"], alt=esc(s["label"]) if s["slug"] else "")
        if s["slug"]:
            spots.append('<a class="spot{fx}" href="[[{slug}]]" style="{v}" data-vortex>'
                         '{img}<span class="cap">{label}</span></a>'.format(
                             fx=fx, slug=s["slug"], v=_vars(s), img=img, label=esc(s["label"])))
        else:
            spots.append('<span class="spot deco{fx}" style="{v}" aria-hidden="true">{img}</span>'.format(
                fx=fx, v=_vars(s), img=img))
    title = '<h1 class="map-title" style="{v}">The Rabbit Tree<span>Hostel</span></h1>'.format(v=_vars(MAP_TITLE))
    body = """
<div class="scene" style="--ratio:{r};--mratio:{mr}">
  {title}
  {spots}
</div>
<section class="scene-text">
{intro}
</section>
""".format(r="{}/{}".format(MAP_W, MAP_H), mr="{}/{}".format(MAP_MW, MAP_MH), title=title,
           spots="\n  ".join(spots), intro=para(INTRO, "intro"))
    return write("index.html", "Hostel Gili Meno | The Rabbit Tree Hostel, Lombok", body,
                 "A unique and creative hostel on Gili Meno, Lombok: a ball pit bedroom, an escape room, daily "
                 "activities, cheap boats from Bali and Lombok. 10% cheaper when you book with us.",
                 bodyclass="home")


# ============================================================ CHAMBRES
def build_rooms():
    nodes = []
    for r in ROOMS + TREE_EXTRA:
        cap = '<span class="cap">{name}{}</span>'.format(
            ' <em>&middot; coming soon</em>' if r.get("soon") else "", **r)
        logo = '<img class="logo" src="images/{badge}" alt="{name}" loading="lazy">'.format(**r)
        swirl = ""
        if r.get("spiral"):
            swirl = '<img class="swirl" src="images/{spiral}" alt="" aria-hidden="true" loading="lazy">'.format(**r)
        if r.get("slug"):
            hit = '<a class="hit" href="[[rooms]]{}/" title="{name}" data-vortex>{}</a>'.format(
                r["slug"], logo + swirl + cap, **r)
        else:
            hit = '<span class="hit static" title="{name} {}">{}</span>'.format(r.get("soon", ""), logo + cap, **r)
        # les positions (x, y) ont ete placees sur l'ancien dessin de 1200 x 972 ; le nouveau fait 1200 x 1428 (racines)
        nodes.append('<div class="node" style="left:{}%;top:{:.2f}%;width:{}%">'.format(r["x"], r["y"] * 972 / 1428, r["w"]) + hit + '</div>')
    cards = "".join(
        '<a class="card" href="[[rooms]]{slug}/"><div class="thumb"><img src="images/{badge}" alt="{name}" loading="lazy"></div>'
        '<span class="cat">{cat}</span><h3>{name}</h3><p>{beds} &middot; {air} &middot; {bath}</p></a>'.format(**r)
        for r in ROOMS)
    body = """<p class="crumb"><a href="[[home]]">Home</a> &rsaquo; Rooms</p>
<div class="page-head"><h1>The Rooms</h1><div class="lead">Every room has its own story. Pick a branch.</div>
<div class="rule"></div></div>
<div class="rooted">
<div class="tree-wrap">
  <img class="trunk" src="images/tree-rooms.webp" alt="Hand drawn tree holding the hostel rooms, its roots reaching down to the rooms" width="1200" height="1428">
  """ + "".join(nodes) + """
</div>
<section>
  <h2>All the rooms</h2>
  <div class="grid c3">""" + cards + """</div>
</section>
</div>
<div class="note">""" + esc(BOOKING_NOTE) + """</div>
<div class="btn-row"><a class="btn primary" href="[[reservations]]">Reservations</a>
<a class="btn" href="[[gallery]]">See the photos</a></div>
"""
    return write("rooms/index.html", "Rooms | The Rabbit Tree Hostel, Gili Meno", body,
                 "Tree House dorm, Bola Bola ball pit room, Pillow Room escape game, Bird Nest with the best "
                 "views, Bamboo Forest deluxe doubles and more, all on Gili Meno.")


def build_room(r):
    src = {"pillow-room": "copy-of-bola-bola", "passion-room": "lapassion", "rabbit-dream": "rabbitdream", "monk": None}.get(r["slug"], r["slug"])
    path = "/home/" + (src or r["slug"]) if src else None
    ph = photos_of(path, limit=9) if path and path in INV else []
    if ph:
        slides = "".join('<img class="slide" src="images/{f}" alt="{a}" loading="lazy">'.format(f=p["file"], a=esc(p["alt"])) for p in ph)
        photos_block = ('<section><h2>Inside the room</h2>'
                        '<div class="stage" tabindex="0" role="group" aria-label="Room photos, swipe to browse">'
                        + slides + '</div>' + strip_html(ph, swap=True) + "</section>")
    else:
        photos_block = ""
    specs = '<dl class="room-specs">' + "".join(
        '<div><dt>{}</dt><dd>{}</dd></div>'.format(k, esc(v)) for k, v in
        (("Sleeps", r["sleeps"]), ("Beds", r["beds"]), ("Cooling", r["air"]), ("Bathroom", r["bath"]))) + '</dl>'
    body = """<p class="crumb"><a href="[[home]]">Home</a> &rsaquo; <a href="[[rooms]]">Rooms</a> &rsaquo; {name}</p>
<div class="room-hero">
  <img class="room-badge" src="images/{badge}" alt="{name} room badge" data-portal>
  <div>
    <span class="cat" style="font-family:var(--f-hand);font-weight:700;font-size:1.4rem;letter-spacing:.1em">{cat}</span>
    <h1>{name}</h1>
    {specs}
    {desc}
    <div class="btn-row" style="justify-content:flex-start">
      <a class="btn primary" href="{book_href}">Book this room</a>
      <a class="btn" href="[[rooms]]">Back to the tree</a>
    </div>
  </div>
</div>
""".format(name=esc(r["name"]), cat=esc(r["cat"]), badge=r["badge"], specs=specs,
           desc=para(" ".join(r["desc"])), book_href="#book" if r.get("beds24") else "[[reservations]]")
    if photos_block:
        body += photos_block
    if r.get("beds24"):
        body += '<section id="book" class="book"><h2>Book this room</h2>'
        body += '<div class="note">' + esc(BOOKING_NOTE) + "</div>"
        for label, rid in r["beds24"]:
            if label:
                body += "<h3>{}</h3>".format(esc(label))
            body += ('<div class="beds24"><iframe src="{}" title="Book {} with Beds24" loading="lazy" '
                     'height="720"></iframe></div>').format(BEDS24_ROOM.format(rid), esc(label or r["name"]))
        body += '<p class="center">Check-in is guaranteed from 2pm; arrive earlier if you like, your room may just not be ready yet.</p>'
        body += ('<p class="center">Booking directly with us is about 10% cheaper than the booking websites. '
                 'A question first? <a href="{}">WhatsApp us</a>.</p></section>').format(HOSTEL["whatsapp"])
    else:
        body += '<div class="note">' + esc(BOOKING_NOTE) + "</div>"
    return write("rooms/{}/index.html".format(r["slug"]),
                 "{} | Rooms | The Rabbit Tree Hostel".format(r["name"]), body,
                 "{} at The Rabbit Tree Hostel, Gili Meno: {}. {}, {}.".format(
                     r["name"], r["beds"], r["air"], r["bath"]))


# ============================================================ RESERVATIONS
def build_reservations():
    rows = [[r["name"], r["cat"], r["sleeps"]] for r in ROOMS]
    body = head("Reservations", "10% cheaper than the booking websites") + """
<section class="narrow">
""" + para("Booking directly with us is cheaper than the big booking websites, and it is the only way to "
           "ask for one of the specific rooms you have fallen for. Choose your dates below.") + """
<div class="note">""" + esc(BOOKING_NOTE) + """</div>
<div class="note">Check-in is guaranteed from 2pm. You are welcome to arrive earlier and relax with us, but your room may not be ready yet.</div>
</section>
<section id="book" class="book">
<div class="beds24 tall"><iframe src="{b24}" title="Book The Rabbit Tree with Beds24" height="2000"></iframe></div>
</section>
<section class="narrow">
<p class="center">A question before you book? Write to us.</p>
<div class="btn-row">
  <a class="btn hot" href="mailto:{mail}?subject=Booking%20request%20%E2%80%94%20The%20Rabbit%20Tree">Email us your dates</a>
  <a class="btn primary" href="{wa}">WhatsApp us</a>
  <a class="btn" href="{phone_link}">Call {phone}</a>
</div>
</section>
<section>
  <h2>The rooms at a glance</h2>
  <p>The booking form above shows the live prices for your dates. Here is what each room holds:</p>
  """ + table(["Room", "Category", "Sleeps"], rows) + """
  <div class="btn-row"><a class="btn" href="[[rooms]]">Open the tree</a></div>
</section>
<section>
  <h2>Prefer a booking website?</h2>
  <p>We are listed on both, but remember that booking here directly is about 10% cheaper.</p>
  <div class="btn-row">
    <a class="btn" href="{booking}">Booking.com</a>
    <a class="btn" href="{hostelworld}">Hostelworld</a>
    <a class="btn" href="{ta}">Tripadvisor</a>
  </div>
</section>
"""
    for k, v in {"mail": HOSTEL["email"], "wa": HOSTEL["whatsapp"], "phone": HOSTEL["phone_display"],
                 "phone_link": "tel:" + HOSTEL["phone_tel"], "booking": HOSTEL["booking"],
                 "hostelworld": HOSTEL["hostelworld"], "ta": HOSTEL["tripadvisor"], "b24": BEDS24_PROP}.items():
        body = body.replace("{" + k + "}", v)
    return write("reservations/index.html", "Reservations | The Rabbit Tree Hostel, Gili Meno", body,
                 "Book The Rabbit Tree Hostel directly and pay about 10% less than the booking websites.")


# ============================================================ GALLERY
def build_gallery():
    items = all_photos()
    gal = strip_html(items)
    logos = '<div class="strip">' + "".join(
        '<a href="[[rooms]]{slug}/" title="{name}"><img src="images/{badge}" alt="{name}" loading="lazy"></a>'.format(**r)
        for r in ROOMS) + "</div>"
    body = head("Gallery", "Pockets of dreams made into a reality") + """
<section class="narrow">
""" + para("In the heart of Gili Meno's paradise you'll find The Rabbit Tree, a unique hostel oozing creativity "
           "and pockets of dreams made into a reality. Every square inch of the property has been intricately "
           "designed to provide guests with a playful and thought provoking experience.\n\n"
           "Since opening in January 2017 the hostel has continued to grow and new details are added all the "
           "time. The Rabbit Tree provides comfortable and weather-proof rooms, fresh water showers, wifi, a long "
           "list of entertainment facilities, drinking water, tea, coffee and breakfast. You can also explore the "
           "secret passageways and hangout spots hidden around the facility.") + """
</section>
<section>""" + gal + """</section>
<section><h2>The rooms, one by one</h2>""" + logos + """</section>
<div class="btn-row"><a class="btn" href="[[our-story]]">Now, see our story</a><a class="btn primary" href="[[rooms]]">The rooms</a></div>
""".replace("[[our-story]]", "../our-story/")
    return write("gallery/index.html", "Gallery | The Rabbit Tree Hostel, Gili Meno", body,
                 "Photos of The Rabbit Tree Hostel on Gili Meno: the rooms, the ball pit, the common areas and the secret spots.")


# ============================================================ OUR STORY
def build_story():
    gal = strip_html(all_photos(include_activities=False))
    body = head("Our Story", "It all started with a silence") + """
<section class="narrow">
""" + para("Are you having the best time of your life traveling freely from one place to another, creating "
           "unforgettable experiences while meeting new people and exploring new cultures? Come and stay at The "
           "Rabbit Tree Hostel and add an extraordinary experience to your trip. 'Cause life is awesome, isn't it?\n\n"
           "It is our greatest pleasure to welcome you into your new home on Gili Meno. The Rabbit Tree is the most "
           "creative building in the Gilis and still changes organically every day. We attract artists, happiness "
           "chasers and creative minds looking for an experience that will last for the rest of their lives.\n\n"
           "The atmosphere here is at the very least surprising, nothing is what it seems. Be prepared to get lost "
           "between the future and now. The rooms are all part of The Rabbit Tree story, which we will tell you as "
           "soon as you arrive...\n\n"
           "Your stay at our hostel is one to remember. Have you ever slept in a ball pit bedroom, a room that feels "
           "like a flying boat, or in one filled with hundreds of pillows? And what would you do if the main sitting "
           "area suddenly becomes a pool in front of your eyes? You might lose yourself in the maize and find a "
           "secret passage to gaze at the stars...\n\n"
           "Through those experiences you will find something you've always been looking for: your dreams. Because, "
           "believe it or not, at the edge of imagination and reality, dreams can come true.") + """
</section>
<section>""" + gal + """</section>
<div class="btn-row"><a class="btn primary" href="[[rooms]]">Sleep inside the story</a><a class="btn" href="[[gallery]]">More photos</a></div>
"""
    return write("our-story/index.html", "Our Story | The Rabbit Tree Hostel, Gili Meno", body)


# ============================================================ HOW TO GET HERE
def build_howto():
    body = head("How To Get Here", "And how to find us once you are on the island") + """
<section class="narrow">
<div class="note">The Rabbit Tree team works hard to get you the best prices and keep you away from scams.
Check our offers and contact us, we will make the booking for you.</div>
<h2>Coming to Gili Meno</h2>
<h3>From Bali (South Bali, Amed, Sanur, Nusa Penida...)</h3>
""" + ul(["Every day: a minibus picks you up in the biggest cities of Bali to reach Padang Bai.",
          "Then a daily ferry to Gili Trawangan (or Gili Air), and a local boat on to Gili Meno.",
          "We have the cheapest prices possible, have a look and ask us."]) + """
<h3>From Gili Trawangan</h3>
""" + ul(["Daily public boat at 09:30 and 16:00 — 40,000 IDR.",
          "Every hour by fast boat — 85,000 IDR."]) + """
<h3>From Lombok (Bangsal)</h3>
""" + ul(["Public boat at 10:00, 14:00 and 17:00 — 25,000 IDR.",
          "Every hour by fast boat — 85,000 IDR."]) + """
<h2>How to find The Rabbit Tree</h2>
<h3>Once on Gili Meno</h3>
""" + para("Once arrived at the Gili Meno harbour, turn right and follow the coast road until you reach "
           "'Karma Reef' restaurant. Go left and then right leading towards the back of the restaurant, briefly "
           "follow this until you reach a tree with many signs on it. You should see a sign pointing left for "
           "The Rabbit Tree. Follow the road on the left for about 5 minutes and you will find our hostel on the "
           "left side of the road just past Amigos Bungalows.\n\n"
           "If you need any help, give us a call or ask any local!") + """
<div class="btn-row"><a class="btn hot" href="{maps}">Open in Google Maps</a>
<a class="btn primary" href="{phone_link}">Call {phone}</a></div>
</section>
""" + figs_of("how-to-get-here", "The island, drawn by hand") + """
<section>
  <h2>The short version</h2>
  <div class="grid c3">
    <div class="card"><h3>Gili Meno harbour</h3><p>Arrive by boat, then turn right along the coast road.</p></div>
    <div class="card"><h3>Karma Reef</h3><p>Follow the coast until Karma Reef restaurant, then left and right behind it.</p></div>
    <div class="card"><h3>The signposted tree</h3><p>Reach the tree covered in signs; take the left for The Rabbit Tree, 5 minutes on foot.</p></div>
  </div>
  <div class="btn-row"><a class="btn" href="[[transports]]">All the boats and prices</a>
  <a class="btn" href="[[activities]]">What to do here</a></div>
</section>
"""
    body = body.format(maps=HOSTEL["maps"], phone=HOSTEL["phone_display"], phone_link="tel:" + HOSTEL["phone_tel"])
    return write("how-to-get-here/index.html", "How To Get Here | The Rabbit Tree Hostel, Gili Meno", body,
                 "Boats from Bali, Lombok and Gili Trawangan to Gili Meno, and walking directions from the harbour to The Rabbit Tree.")


# ============================================================ TRANSPORTS
TRANSPORT = {
    "hop": table(["Route", "Public boat (40K)", "Private boat"],
        [["Gili Meno &rarr; Gili Trawangan", "8.50am, 3.20pm", ("85K, every hour",)],
         ["Gili Trawangan &rarr; Gili Meno", "9.30am, 4.00pm", ("85K, every hour",)],
         ["Gili Meno &rarr; Gili Air", "9.50am, 4.20pm", ("85K, every hour",)],
         ["Gili Air &rarr; Gili Meno", "8.30am, 3.00pm", ("85K, every hour",)]]),
    "lombok": table(["From / to", "Option", "Price"],
        [["Gili Meno &harr; Bangsal (Lombok)", "Public boat: from Gili Meno 8am, 3.30pm; from Bangsal 10am, 2pm, 5pm", ("25K",)],
         ["Bangsal &harr; Lombok Airport", "Shuttle per person", ("[[$-Shuttle bangsal Airport|170K]]",)],
         ["Bangsal &harr; Lombok Airport", "Private taxi", ("[[$-Taxi Bangsal / Airport|500K]]",)],
         ["Bangsal &harr; Kuta Lombok", "Shuttle per person", ("[[$-Shuttle Bangsal / Kuta|160K]]",)],
         ["Bangsal &harr; Kuta Lombok", "Private taxi", ("[[$-Taxi Bangsal / Kuta|500K]]",)],
         ["Bangsal &harr; Senggigi or Mataram", "Shuttle per person", ("[[$-Shuttle Senggigi or Mataram|115K]]",)],
         ["Bangsal &harr; Senggigi", "Private taxi", ("[[$-Taxi Bangsal / Senggigi|250K]]",)],
         ["Bangsal &harr; Tetebatu", "Private taxi", ("[[$-Taxi Tetebatu|450K]]",)],
         ["Bangsal &harr; Selong Belanak", "Private taxi", ("[[$-Taxi bangsal to selong belanak|500K]]",)]]),
    "bali": table(["Ticket", "Price", "Notes"],
        [["Fast boat Bali &harr; Gili Meno (Semaya)", ("[[$-Semaya Bali (no pick up)|430K]]",), "One way, boat only"],
         ["Fast boat Bali &harr; Gili Meno (Semaya)", ("[[$-Semaya Bali + Pick up|530K]]",), "One way, with pick up in Bali"],
         ["Fast boat Bali &harr; Gili Meno (Wijaya)", ("[[$-Wijaya bali(no pick,mn boat)|450K]]",), "One way, boat only"],
         ["Fast boat Bali &harr; Gili Meno (Wijaya)", ("[[$-Wijaya bali +Pick up (P&S)|550K]]",), "One way, with pick up in Bali"]]),
    "elsewhere": table(["Destination", "Price", "How"],
        [["Sanur (Bali) or Nusa Penida", ("[[$-Wijaya Meno/ Nusa Penida/Sanur|550K]]",), "Fast boat from Gili Meno"],
         ["Amed", "Not available now", ""]]),
}


def wijaya_table():
    """Horaires Wijaya Perkasa (data/wijaya.json, mis a jour chaque nuit par tools/wijaya.py)."""
    try:
        d = json.load(open(os.path.join(HERE, "data", "wijaya.json")))
    except Exception:
        return ""
    def rows(sel, other):
        out = {}
        for r in d["rows"]:
            if sel(r):
                out.setdefault(r[other], []).append("{}&nbsp;&rarr;&nbsp;{}".format(r["dep"], r["arr"]))
        return out
    def block(title, data, col):
        if not data:
            return ""
        return ('<div class="tt"><h3>{}</h3>'.format(title) + table([col, "Departure → arrival"],
                [[k, ("<br>".join(v),)] for k, v in sorted(data.items())]) + "</div>")
    y, m, dd = d["updated"].split("-")
    return ('<h3 class="tt-title">Fast boat timetable (Wijaya Perkasa)</h3><div class="tt-grid">' +
            block("Leaving Gili Meno", rows(lambda r: r["from"] == "Gili Meno", "to"), "To") +
            block("Coming to Gili Meno", rows(lambda r: r["to"] == "Gili Meno", "from"), "From") +
            '</div><p class="tt-src">Checked every night on <a href="{}" target="_blank" rel="noopener">the boat company\'s website</a>, '
            'last change {}/{}/{}. Times can move with the weather: we confirm yours when you book.</p>'.format(d["source"], dd, m, y))


def build_transports():
    body = head("Transports", "Boats to and from the Gili Islands") + banner_of("transports") + """
<section class="narrow">
""" + para("It is very easy to travel between the Gilis, and we have bargained for you to get cheaper "
           "transportation, or at least the same price as anybody else here. So do not hesitate to contact us "
           "to book your ticket. It would be a shame to miss it.") + """
<div class="note">Fast boats link Gili Meno and Bali (Padang Bai, Sanur, Nusa Penida) several times a day: see the
timetable below, updated every night.</div>
</section>
""" + deco_of("transports") + gal_of("transports", "") + """
<section><h2>Gili island hopping</h2>
<p>Public boats run twice a day in each direction for 40K; private boats run every hour for 85K.</p>
""" + TRANSPORT["hop"] + """</section>
<section><h2>To and from Lombok</h2>
<p>Public boats link Gili Meno and Bangsal every day for 25K: from Gili Meno at 8am and 3.30pm, from Bangsal at 10am, 2pm and 5pm.
To go to or leave Bangsal we have special prices for shuttles and taxis.</p>
""" + TRANSPORT["lombok"] + """</section>
<section><h2>To and from Bali</h2>
<p><b>Send us a WhatsApp, your ticket is booked in two minutes</b> (or just ask at the reception), and we handle the rest: pick-up, check-in at the harbour, and a phone
call to the boat company if anything is late or cancelled. Same price as on the boat company's own website. The two-way
ticket is cheaper if you already know you will come back to Bali, and it is an open date return, so you do not need to
decide when you leave us.</p>
""" + TRANSPORT["bali"] + wijaya_table() + """
<p>You can also go directly to and from other places in Bali:</p>
""" + TRANSPORT["elsewhere"] + """
<form class="wa-form" id="book-boat" data-wa="{wa}">
  <h3>Book your boat on WhatsApp</h3>
  <p>Fill in what you know, press the button: WhatsApp opens with your message ready, you just hit send.</p>
  <div class="wa-grid">
    <label>Your name<input name="name" autocomplete="name" placeholder="Alex"></label>
    <label>Date<input name="date" type="date"></label>
    <label>From<select name="from"><option>Gili Meno</option><option>Padang Bai (Bali)</option><option>Sanur (Bali)</option><option>Nusa Penida</option><option>Gili Trawangan</option><option>Gili Air</option><option>Bangsal (Lombok)</option><option>Lombok Airport</option><option>Kuta Lombok</option><option>Senggigi</option></select></label>
    <label>To<select name="to"><option>Padang Bai (Bali)</option><option>Sanur (Bali)</option><option>Nusa Penida</option><option>Gili Meno</option><option>Gili Trawangan</option><option>Gili Air</option><option>Bangsal (Lombok)</option><option>Lombok Airport</option><option>Kuta Lombok</option><option>Senggigi</option></select></label>
    <label>People<input name="people" type="number" min="1" max="30" value="1"></label>
    <label>Ticket<select name="trip"><option>One way</option><option>Return (open date)</option></select></label>
    <label>Pick-up / drop-off on the mainland<select name="pick"><option>Yes please</option><option>No, boat only</option></select></label>
    <label>Preferred time<select name="time"><option>Morning</option><option>Afternoon</option><option>Whatever is best</option></select></label>
  </div>
  <label class="wa-wide">Anything else (hotel in Bali, flight time…)<input name="note" placeholder="Hotel name, flight at 6pm…"></label>
  <div class="btn-row"><button class="btn primary" type="submit">Send on WhatsApp</button>
  <a class="btn" href="mailto:{mail}?subject=Transport%20booking">Or by email</a></div>
</form>
</section>
"""
    body = body.format(mail=HOSTEL["email"], wa=HOSTEL["whatsapp"])
    return write("transports/index.html", "Transports to and from the Gilis | The Rabbit Tree Hostel", body,
                 "Public and fast boat timetables and prices between Gili Meno, Gili Trawangan, Gili Air, Bangsal (Lombok) and Bali.")


# ============================================================ ACTIVITIES
def build_activities():
    body = head("What To Do In Gili Meno?", "Who said there was nothing to do on this island?") + banner_of("activities") + """
<section class="narrow">
""" + para("Before, you must know that there are activities every day at the Rabbit Tree! It would be hard to "
           "include everything we do together at the Rabbit Tree, but let's give a few examples...") + """
""" + para("In Gili Meno, many things to do! Go to walk around the island — it only takes one hour... or one day "
           "if you slow down and take your time to enjoy the wonderful places that Gili Meno offers you.") + """
""" + ul(["Discover the lake and mangroves",
          "Relax on the most lovely beach of the 3 Gilis",
          "Admire the sunrise or the sunset"]) + """
</section>
<section><h2>At the hostel, every day</h2>
<p>Something happens every evening at the Rabbit Tree, and most of it is free. <a href="../hostel-life/">See life at the hostel</a>.</p>
<div class="daily">
""" + "".join('<figure><img src="images/{}" alt="{}" style="object-position:{}" loading="lazy"><figcaption>{}</figcaption></figure>'.format(
        f, esc(t), pos, esc(t)) for f, t, pos in [
        # (photo, legende, point de cadrage : on garde les visages dans le cercle)
        ("img-f2325222481be5.webp", "Movie night", "50% 55%"),
        ("img-f6b5ed21da9b09.webp", "Yoga & workout", "45% 40%"),
        ("img-b78e3e3fd11cef.webp", "Sunset on the beach", "70% 60%"),
        ("img-baeed1388d8c8b.webp", "Traditional dinner", "60% 40%"),
        ("img-08f0dcfb127468.webp", "Games night", "50% 40%"),
    ]) + """
</div></section>
<section><h2>You would like to do some good things?</h2>
<div class="fiches">
""" + "".join(fiche(*f) for f in [
        ("Good things to do", "Visit the turtle sanctuary", "img-91d2743badcb18.webp", ("Small donation", ""), ["Near the beach", "4 pools", "Baby turtles"],
         "It's a place near the beach with 4 small pools. The aim is to collect the eggs from the shore before predators eat them, **grow the little turtles until they are about 1 year old, and release them** in their natural environment. Thanks to this work, we still have a lot of turtles around Gili Meno. You can support this with a small donation.",
         [("Turtle ID workshop with Divine Divers", "https://divinedivers.com/product/turtle-identification-workshop/")]),
        ("Good things to do", "Join the Trash Heroes", "img-a0bea03d339020.webp", ("Free", ""), ["Every Sunday", "3.30pm", "At the Brotherhood"],
         "Meet locals and tourists **every Sunday around 3.30pm** at the Brotherhood and walk together to collect the trash. It will be an unforgettable moment to share with locals! They also take care of the trash bins around the island, so be sure to throw your waste in one of those.",
         [("Clean the reef too: underwater cleanup", "https://divinedivers.com/product/underwater-cleanup/")]),
    ]) + """
</div></section>
<section><h2>On the water, under the water</h2>
<div class="fiches">
""" + "".join(fiche(*f) for f in [
        ("The main activity on the island", "Snorkelling", "img-642eb4c7a81abb.webp", ("[[$-Snorkeling Trip|150K]]", "boat trip"), ["3 hours", "Max 15 people", "4 spots", "Mask [[$Snorkeling Mask|30K]]"],
         "Good news! All the best snorkelling spots are around Gili Meno. You can rent a mask from us at the "
         "reception for [[$Snorkeling Mask|30K]] and go to swim with the turtles. We will help you to find the best spots on the "
         "surrounding reefs, including the famous underwater statues. Or for only [[$-Snorkeling Trip|150K]] "
         "you can book a 3 hours boat trip. With a maximum of 15 people per boat, a local "
         "expert will guide you through **4 locations including the statues, the wreck and 2 turtles spots**."),
        ("You liked snorkelling? Let's go deeper", "Diving", "img-a547bb719d71a2.webp", ("Club prices", ""), ["Discovery dives", "Fun dives", "Certificates"],
         "The Gilis are part of the best spots in the world for diving, with an exceptionally warm and clear "
         "water, and slow current. Don't miss that! You can book through us for a dive with Divine Divers. They "
         "offer the best services quality, and work in a good atmosphere. They organize discovery dives, fun "
         "dives and diving certificate. Let us know if you want to book in advance. (we offer the same prices "
         "as the club)", [("Divine Divers", "https://divinedivers.com/"), ("First dive", "https://divinedivers.com/product/introduction-dive-1/"),
                         ("Open Water course", "https://divinedivers.com/product/open-water-diver-course/"), ("Fun dives", "https://divinedivers.com/fun-diving/"),
                         ("Dive sites", "https://divinedivers.com/dive-sites/"), ("All courses", "https://divinedivers.com/courses/")]),
        ("An unforgettable ride", "Horse riding", "img-b56438840f5c97.webp", ("[[$-Horse Riding|400K]]", "per person"), ["1h – 1h30", "Morning or sunset", "From the hostel"],
         "For [[$-Horse Riding|400K]] per person, enjoy a 1h~1h30 ride around the island, going through the paths and the beach. "
         "You can go in the morning or in the afternoon to **admire the sunset**. In both cases, you will stop at "
         "some lovely points to take incredible pictures. Departure and arrival at Rabbit Tree."),
        ("Fishing, option 1", "Private fishing trip", "img-b53dddc746eb67.webp", ("[[$-Private Fishing Trip (2 people)/2|350K]]", "per person"), ["3 hours", "2 people", "2 techniques"],
         "Private fishing trip: for [[$-Private Fishing Trip (2 people)/2|350K]] per person (2 people), go for a 3 hours boat trip and try two fishing techniques "
         "— bottom fishing (to catch groupers, snappers, and more) and crowling fishing (to catch **barracudas, "
         "giant trevally, even sometimes tunas**)."),
        ("Fishing, option 2", "Spearfishing", "img-138645e042cd2d.webp", ("[[$-Spearfishing|380K]]", "per person"), ["3 hours", "With a guide", "From the beach"],
         "Spearfishing: for [[$-Spearfishing|380K]] per person, go with a guide who will **teach you spearfishing** during 3 hours. "
         "You will leave directly from the beach to catch different kinds of local fish, or maybe octopus."),
    ]) + """
</div>
<h2>More trips from the reception</h2>
""" + table(["Trip", "Price"], [
        ["Sunset boat", ("[[$-Sunset Boat|250K]]",)],
        ["Night boat to Gili Trawangan", ("[[$-Gili T Night Boat|170K]]",)],
        ["Senaru waterfall (2 people minimum)", ("[[$-Senaru Waterfall (2pax min)|400K]]",)],
    ]) + """
</section>
<section class="narrow center">
<h2>Who said there was nothing to do on this island?</h2>
</section>
""" + gal_of("activities", "In pictures") + """
<section>
<div class="btn-row"><a class="btn primary" href="[[tours]]">Also, you want to go into an adventure? Click here!</a></div>
</section>
""".replace("[[tours]]", "../tours/")
    return write("activities/index.html", "Activities in Gili Meno | The Rabbit Tree Hostel", body,
                 "Snorkelling with turtles, the underwater statues, diving, horse riding, fishing, movie nights, yoga and the Trash Heroes on Gili Meno.")


# ============================================================ SERVICES / CULTURE / INFOS
def build_services():
    body = head("Services We Provide", "We take care of everything") + """
<section class="narrow">
""" + para("We provide several services, just come to the reception to ask what you need.") + """
</section>
<section>
""" + table(["Service", "Price", "Details"], [
        ["Laundry", ("[[$Laundry|30K]] / kg",), "We take care of your clothes"],
        ["Towels", ("Free / [[$Towel|50K]] deposit",), "Free for guests in the couple bedrooms. Otherwise a deposit, partly given back after use"],
        ["Snorkelling mask", ("[[$Snorkeling Mask|30K]] / day",), "We indicate the spots on a map: turtles point, best corals, Bounty wreck. We do not rent fins, but shops next to the beach do"],
        ["Bike rental", ("[[$Rabbit bike|50K]] / day",), "To go faster around the island"],
        ["Transport booking", ("Our rates",), "Partnerships for boats from Bali or Lombok, shuttles and taxis"],
    ]) + """
</section>
""" + deco_of("services") + """
<section>
<div class="btn-row"><a class="btn" href="[[transports]]">All the transport options</a>
<a class="btn" href="[[activities]]">Snorkelling and diving</a></div>
</section>
""".replace("[[transports]]", "../transports/").replace("[[activities]]", "../activities/")
    return write("services/index.html", "Services | The Rabbit Tree Hostel, Gili Meno", body)


def build_culture():
    body = head("Cultural Tips", "A quiet Muslim island that has hosted travellers for a long time") + """
<section class="narrow">
<h2>Muslim island</h2>
""" + para("Indonesia has the world's largest Muslim population, including the people of Gili Meno. There is a "
           "mosque on the island, and because it is very small you can easily hear the prayers sung five times a "
           "day. As long as you accept it as part of your travel experience, being in contact with different ways "
           "of life, you will get used to it.") + """
<h2>Tourist behaviour</h2>
""" + para("People here are used to seeing tourists sunbathing on the beach in only a swimsuit, drinking and "
           "partying. Even if tourism is a big part of the economy, it is important to respect the inhabitants, "
           "their beliefs and lifestyle, the nature and the animals. Gili Meno is still a quiet island where the "
           "locals have lived in the same way for a long time.\n\n"
           "If you are interested, we can show you how to make a difference by helping collect trash or supporting "
           "the locals who take care of the environment.") + """
<h2>Indonesian people</h2>
""" + para("Indonesian people are very friendly. They are raised not to show anger and to solve their problems "
           "peacefully, so be like them. Do not get angry when something annoys you: just breathe, explain the "
           "problem with polite communication, and everything will be alright. Also remember that not everyone "
           "speaks English, so maybe you can find other creative ways to communicate. In general, just use common "
           "sense while you are travelling and talking to people.") + """
<h2>Some useful words</h2>
""" + table(["Indonesian", "English", "Tip"], [
        ["Terima kasih", "Thank you", "Say it often, it opens every door"],
        ["Selamat pagi / siang / malam", "Good morning / afternoon / evening", ""],
        ["Berapa harga?", "How much?", "Ask before you sit down on a boat"],
        ["Tidak, terima kasih", "No, thank you", "The most useful sentence against a hard sell"],
        ["Pelahan", "Slowly", "Handy on a bumpy boat"],
        ["Air minum", "Drinking water", "Refill at the reception"],
    ]) + """
</section>
""" + '<section><h2>The words, the hostel way</h2>' + deco_of("culture") + "</section>" + """
<section class="narrow">
<div class="btn-row"><a class="btn" href="[[useful-information]]">Visa, money and blackouts</a></div>
</section>
""".replace("[[useful-information]]", "../useful-information/")
    return write("culture/index.html", "Culture and useful words | The Rabbit Tree Hostel", body)


def build_useful():
    body = head("Useful Information", "Before you arrive") + """
<section class="narrow">
<h2>About the visa</h2>
""" + para("You do not need to do anything before your arrival in Indonesia. When you land, apply for a Visa on "
           "Arrival (35 USD) which allows a stay of up to 30 days. To stay 30 more days you need an extension "
           "(again 35 USD, requested at least one week before your VoA expires). The extension is done in "
           "Mataram, the capital of Lombok, within the week preceding the end of your 30 days; you will be asked "
           "to come back a second time for your fingerprints. You need to wear long pants when you go there.") + """
<h2>About money</h2>
""" + para("The Indonesian currency is very low: 1 USD is around 15,000 IDR. Be careful to count the money when "
           "you pay and when you get change, because it is easy to make mistakes.") + """
<h3>ATM</h3>
""" + para("There are a couple of ATMs on the island, but if you need to exchange currency you may prefer to do "
           "it on the mainland, because here they could charge you more.") + """
<h3>Shops</h3>
""" + para("Gili Meno is a very small island. There are small shops and supermarkets with basic stuff, usually a "
           "little more expensive than normal, so if you need something in particular bring it with you from the "
           "mainland.") + """
<h3>Electricity</h3>
""" + para("As in many South East Asian countries, blackouts can happen for a few minutes or a few hours, "
           "especially at night. We cannot do anything about it. Just be patient, light some candles, or go out "
           "and enjoy the sea and the stars.") + """
</section>
""" + gal_of("useful-information", "") + """
<section class="narrow">
<div class="btn-row"><a class="btn primary" href="[[reservations]]">Book a room</a>
<a class="btn" href="[[how-to-get-here]]">How to get here</a></div>
</section>
""".replace("[[reservations]]", "../reservations/").replace("[[how-to-get-here]]", "../how-to-get-here/")
    return write("useful-information/index.html", "Useful information before your arrival | The Rabbit Tree Hostel", body)


# ============================================================ TOURS
def build_tours():
    body = head("Adventures", "Go on an adventure") + banner_of("tours") + """
<section class="narrow">
""" + para("We offer different tours, for all tastes... Don't hesitate to come to the reception to book what you want.") + """
</section>
<section>
<div class="grid c2">
  <div>
    <a class="card" href="[[tours]]komodo/"><div class="thumb"><img src="images/img-3470ae751e2dd7.webp" alt="Komodo dragon" loading="lazy"></div>
      <h3>Komodo Tour</h3><p>Have you ever thought about seeing the dragons and the famous pink beach for real?
      You will go around Lombok, north Sumbawa and the Komodo Islands, not only to meet the dragons, but also to
      visit intact areas where the coral reef offers its best colors and wildlife... and the amazing whale sharks!
      For [[$-Komodo share Deck|3,700K]] per person, it includes 3 days, 4 nights sleeping on the deck, the entrance fees to the Komodo
      National Park, transportations, food and snorkelling material. If you need more comfort, you can choose a private
      cabin: [[$-Komodo private cabin(fan)|4,200K]] with a fan, [[$-Komodo private Cabin(AC)|4,800K]] with air conditioning. It doesn't include the way back from Labuan Bajo (Flores).
      Departures usually on Monday, Wednesday and Saturday.</p></a>
    <div class="btn-row"><a class="btn" href="[[tours]]komodo/">Check all infos and options</a></div>
  </div>
  <div>
    <a class="card" href="[[tours]]rinjani/"><div class="thumb"><img src="images/rinj-jpg.webp" alt="Mount Rinjani trek" loading="lazy"></div>
      <h3>Rinjani Trek</h3><p>You are rather sporty and you like hiking? This one is for you! For [[$-Rinjani 2D/1N  (1N in tent +1 in hotel)|2,450K]] per person,
      go on a 2 days, 1 night trek to reach the Rinjani, the famous volcano in Lombok. It will be sporty but you
      will admire exceptional landscapes! It includes the transportation from Gili Meno, food, tent, porters, and
      a first night prior to departure.</p></a>
    <div class="btn-row"><a class="btn" href="[[tours]]rinjani/">Check all infos and options</a></div>
  </div>
</div>
<div class="btn-row"><a class="btn primary" href="[[activities]]">Check the activities you will have with us</a>
<a class="btn" href="[[rooms]]">Or Explore the Rooms</a></div>
</section>
""".replace("[[tours]]komodo/", "../tours/komodo/").replace("[[tours]]rinjani/", "../tours/rinjani/") \
   .replace("[[activities]]", "../activities/").replace("[[rooms]]", "../rooms/")
    body += gal_of("tours", "The adventures in pictures")
    return write("tours/index.html", "Adventures from Gili Meno | The Rabbit Tree Hostel", body)


def build_komodo():
    body = head("Komodo Trip", "4 days, 3 nights on a wooden boat through north Sumbawa and the Komodo Islands") + banner_of("komodo") + """
<section class="narrow">
""" + para("The tour is a full live-on-board sailing experience with many activities such as snorkelling, hiking, "
           "hunting for the Komodo dragons and searching for the whale sharks. There is loads of time for sunbathing, "
           "sharing stories, watching endless panorama views, seeing multiple sunrises and sunsets, lots of sailing "
           "and swimming. Every boat includes its own tour guide who will take you to the amazing spots.") + """
<div class="note">Departures on Wednesdays and Saturdays. Check-in between 8.30 and 10.00 at Bangsal Harbour.</div>
<h2>Program</h2>
<h3>Day 1 — Bangsal, Kayangan Harbour, Kenawa Island</h3>
""" + para("After a briefing we have a 2 hour bus drive (depending on traffic) to east Lombok where the boat departs. Activities: swimming, sailing, hiking.") + """
<h3>Day 2 — Whale shark point (Saleh Bay, Sumbawa)</h3>
""" + para("On the hunt for the whale sharks during snorkelling. Activities: swimming, sailing, sunbathing.") + """
<h3>Day 3 — Komodo Park, Pink Beach, Long Beach, Padar Island</h3>
""" + para("Visiting the legendary Komodo dragons during a guided hike at Komodo Park. Watch out, before you know it "
           "you are standing eye to eye with a Komodo dragon. Hiking the hills on Padar Island for sunset and sunrise on the boat.") + """
<h3>Day 4 — Manjarite, Kelor Island, Labuan Bajo</h3>
""" + para("Sailing towards the islands, island hopping for snorkelling, sunbathing, beach games and relaxing. "
           "Arriving in Labuan Bajo between 14.00 and 15.00, depending on the weather and the current.") + """
</section>
""" + gal_of("komodo", "The trip in pictures") + """
<section><h2>Price and options</h2>
""" + table(["Class", "Price", "Sleeping"], [
        ["Deck class", ("[[$-Komodo share Deck|3,700,000 IDR]]",), "A mattress, pillow and blanket per person on a shared deck"],
        ["Cabin class, fan", ("[[$-Komodo private cabin(fan)|4,200,000 IDR]]",), "A private cabin for two with a fan, a double mattress, a pillow and a blanket per person"],
        ["Cabin class, air conditioning", ("[[$-Komodo private Cabin(AC)|4,800,000 IDR]]",), "A private air conditioned cabin for two"],
    ]) + """
<p>The way back from Labuan Bajo (Flores) is not included.</p>
<h2>Two companies, the same trip</h2>
<p>Both companies offer the same program and service in a similar boat. The only real difference is their
communication skills and clarity of organisation. And also the price.</p>
<div class="grid c2">
<div class="card"><h3>Kareem The Explorer &middot; the most reliable</h3>
<p class="price-line">from [[$-Komodo share Deck|3,700,000 IDR]]</p>
""" + para("Kareem travels with boats that have the capacity for 30 to 40 people, depending on the size of the boat. "
           "All the boats have a simple fresh water shower, although a dip in the ocean is preferred by most guests.\n\n"
           "They cannot always know beforehand which boat will sail: it depends on which boat is where and on the "
           "number of guests. Sometimes they sail with two or more boats at the same time.\n\n"
           "All the boats are equipped with lifejackets and lifeboats for your safety in the unlikely event of an "
           "emergency. Joining the boat trip is still at your own risk.") + """
<h4>Included</h4>
""" + ul(["Three Indonesian meals a day (vegetarian and vegan options available) and snacks*",
          "Unlimited coffee, tea and mineral water",
          "Beanbags",
          "Charging points for electronic devices (solar energy)",
          "Mask, snorkel and traditional simple fishing gear",
          "Deck class: a mattress, pillow and blanket per person",
          "Cabin class: a private cabin for two with a double mattress"]) + """
</div>
<div class="card"><h3>Explore Komodo &middot; the easiest to book</h3>
<p class="price-line">from [[$-Komodo share Deck|3,700,000 IDR]]</p>
<h4>Their boat</h4>
""" + ul(["Wifi connection",
          "AIS (automatic identification system), radio, GPS, compass",
          "Maximum 60 passengers",
          "Safety equipment: life raft, life jackets, ring lifebuoy",
          "Fresh water and a simple shower",
          "Snorkelling gear (mask and snorkel, no fins) and traditional simple fishing gear",
          "Charging points for electronic devices",
          "A small motor boat to reach the beaches",
          "Lockers for your valuables, a cool box with ice for your extra drinks",
          "Deck class: a mattress, pillow and blanket per person on a shared deck",
          "Cabin class: a private cabin with a fan for two, a double mattress, a pillow and a blanket each"]) + """
<h4>Included</h4>
""" + ul(["A fruit plate for breakfast, fresh fruit juice once a day",
          "Unlimited coffee, tea and mineral water",
          "Entrance fee to Komodo National Park and an English speaking guide",
          "Bus to the departure port, boat ticket from Gili Trawangan and Gili Air",
          "Pick up from Senggigi or Mataram to the meeting point (not from Kuta Lombok: arrange it with the agent you book with)"]) + """
</div>
</div>
<div class="note">Please tell your tour guide about any dietary requirement. Guests with food allergies should be
aware that the food may contain or come into contact with common allergens such as dairy, eggs, wheat, soybeans,
tree nuts, peanuts, fish and shellfish, and that cross-contamination may occur.</div>
<div class="btn-row"><a class="btn hot" href="mailto:{mail}?subject=Komodo%20trip">Book the Komodo trip</a>
<a class="btn primary" href="{wa}">WhatsApp us</a><a class="btn" href="[[tours]]">Other adventures</a></div>
</section>
"""
    body = body.format(mail=HOSTEL["email"], wa=HOSTEL["whatsapp"]).replace("[[tours]]", "../")
    return write("tours/komodo/index.html", "Komodo Trip 4D3N | The Rabbit Tree Hostel", body,
                 "Four day live-on-board sailing trip to the Komodo islands from Gili Meno: whale sharks, Pink Beach, Padar and the dragons. Deck or private cabin.")


def build_rinjani():
    body = head("Rinjani Trek", "Summit Mount Rinjani via Sembalun village") + banner_of("rinjani") + """
<section class="narrow">
<h2>2 days &amp; 1 night — Summit trek</h2>
""" + para("Trekking the summit of Mount Rinjani via Sembalun village, 2 days 1 night. Starting at 1,156 m above "
           "sea level to the Sembalun crater rim at 2,639 m where we camp, then an early morning next day climb to "
           "the summit at 3,726 m and back down to the crater rim and Sembalun village.") + """
<h3>Day 1</h3>
""" + para("After an early breakfast we depart Senaru and travel by 4WD vehicle to Sembalun. We register at the "
           "Rinjani Information Centre in Sembalun (1,156 m) before commencing our trek. The trail initially passes "
           "through undulating open grasslands as it winds up the mountain. We stop at Pos 1 and Pos 2 for rest "
           "breaks and snacks. At Pos 3 (1,800 m) we stop for a longer break and lunch. After lunch we commence the "
           "steep climb up the crater rim. We camp the night at Sembalun Crater Rim (2,639 m) with amazing views of "
           "the sunset, Lake Segara Anak, the summit of Mount Rinjani and northern Lombok.") + """
<h3>Day 2</h3>
""" + para("We wake at 3am for a light breakfast before commencing the challenging three hour trek to the summit "
           "(3,726 m). We arrive in time for sunrise, the best time to enjoy the spectacular views. Returning to our "
           "campsite on the crater rim we stop for a hot breakfast and a rest before commencing our return trek to "
           "Sembalun. We pause for lunch at Pos 2 or 3 and arrive in Sembalun in the early afternoon, from where you "
           "will be transported to your next destination.") + """
<h2>3 days &amp; 2 nights — Summit, lake and hot springs</h2>
""" + para("The 3 days 2 nights program starts at 1,156 m at Sembalun village and goes to the crater rim, the "
           "summit, the lake, the hot spring, the Senaru crater rim and down to Senaru village.") + """
<h3>Day 1</h3>
""" + para("The same as the 2 day trek: from Sembalun (1,156 m) through the grasslands, Pos 1, 2 and 3, and the steep "
           "climb to camp on the Sembalun Crater Rim (2,639 m), with the sunset over Lake Segara Anak.") + """
<h3>Day 2</h3>
""" + para("We wake at 3am for a light breakfast before commencing the challenging three hour trek to the summit "
           "(3,726 m). We arrive in time for sunrise, the best time to enjoy the spectacular views. Returning to our "
           "campsite on the crater rim we pause for a hot breakfast and a rest before continuing our descent into "
           "the crater. We stop for lunch on the shore of Lake Segara Anak (2,000 m) where we can swim in the hot "
           "springs. After lunch we continue our trek around the lakeshore before commencing our climb out of the "
           "crater. The trail is steep and rocky and passes through dense forest. At the Senaru Crater Rim (2,641 m) "
           "we stop for dinner and camp for the night. The crater rim offers views across the lake back toward the "
           "summit and a good vantage point of Gunung Baru, the small volcanic cone within the crater of Mount "
           "Rinjani. Mount Agung in Bali and the Gili Islands can also be seen from here.") + """
<h3>Day 3</h3>
""" + para("After breakfast we commence our descent of the mountain, using the rest spots of Pos 3, Pos 2 and Pos 1 "
           "and stopping for a longer break for lunch along the way. As we descend the mountain the forest becomes "
           "thicker and increasingly lush. We arrive in Senaru (601 m) at approximately 1 pm, from where you will be "
           "transported to your next destination.") + """
</section>
""" + gal_of("rinjani", "The trek in pictures") + """
<section><h2>Prices</h2>
""" + table(["Trek", "Price per person", "Notes"], [
        ["Rinjani 2D/1N summit", ("[[$-Rinjani 2D/1N  (1N in tent +1 in hotel)|2,450,000 IDR]]",), "One night in a tent, plus one night in a hotel before the trek"],
        ["Rinjani 3D/2N summit, lake and hot springs", ("[[$-Rinjani 3D/2N (2N in tent +1 in hotel)|2,700,000 IDR]]",), "Two nights in a tent, plus one night in a hotel before the trek"],
    ]) + """
<h2>Included</h2>
""" + ul(["Pick up from your designated location within Lombok and transfer to Senaru",
          "Accommodation in a comfortable hotel in Senaru for one night before the trek",
          "Quality camping equipment: tents, sleeping mats, sleeping bags, toilet tents and ground sheets",
          "An experienced English speaking guide and professional porters",
          "Entrance fee to the national park",
          "All meals, snacks and drinks during the trek",
          "Transfer at the end of your trek to your next destination within Lombok"]) + """
<div class="btn-row"><a class="btn hot" href="mailto:{mail}?subject=Rinjani%20trek">Book the trek</a>
<a class="btn primary" href="{wa}">WhatsApp us</a><a class="btn" href="[[tours]]">Other adventures</a></div>
</section>
"""
    body = body.format(mail=HOSTEL["email"], wa=HOSTEL["whatsapp"]).replace("[[tours]]", "../")
    return write("tours/rinjani/index.html", "Rinjani Trek 2D1N and 3D2N | The Rabbit Tree Hostel", body,
                 "Trek Mount Rinjani to the 3,726 m summit from Gili Meno: 2 days 1 night or 3 days 2 nights with the lake and hot springs.")


# ============================================================ WELCOME
def build_welcome():
    body = head("Welcome", "It all started with a silence") + banner_of("welcome") + """
<section class="narrow center">
""" + para("It all started with a silence. A blank that your memory cannot recall. You lost us, you do not remember "
           "when it happened. Only our tracks are left. Silent.\n\nThank you for your booking, we are looking "
           "forward to meeting you!") + """
</section>
""" + deco_of("welcome") + gal_of("welcome", "") + """
<section><h2>Now, let us help you travel</h2>
<div class="grid c3">
  <a class="card" href="[[transports]]"><h3>From and to Bali</h3><p>Fast boats from [[$-Semaya Bali (no pick up)|430K]] one way.</p></a>
  <a class="card" href="[[transports]]"><h3>From and to Lombok</h3><p>Bangsal boats and shuttle rates.</p></a>
  <a class="card" href="[[transports]]"><h3>Between the Gilis</h3><p>Public boats 40K, fast boats 85K.</p></a>
</div></section>
<section class="narrow">
<h2>You are already at the harbour of Gili Meno?</h2>
""" + para("Just follow the coast road on the map and you will reach us in five minutes on foot.") + """
<div class="btn-row"><a class="btn hot" href="{maps}">Open the map</a>
<a class="btn" href="[[how-to-get-here]]">The walking directions</a></div>
</section>
<section><h2>Once you have arrived</h2>
<div class="grid c2">
  <a class="card" href="[[activities]]"><h3>Discover the wonders of the island</h3><p>A myriad of activities at the hostel and around Gili Meno. We take care of everything.</p></a>
  <a class="card" href="[[tours]]"><h3>See, old friend, dreams come true</h3><p>Komodo by boat, Rinjani on foot. When it will be time to continue your trip, we will still be here for you.</p></a>
  <a class="card" href="[[culture]]"><h3>Cultural tips</h3><p>A few precious tips and Indonesian words before you walk into town.</p></a>
  <a class="card" href="[[useful-information]]"><h3>Before you arrive</h3><p>Visa, money, ATMs and blackouts.</p></a>
</div>
<div class="note">Do not hesitate to contact us for any further information.</div>
</section>
"""
    body = body.format(maps=HOSTEL["maps"])
    return write("welcome/index.html", "Welcome to the edge of reality | The Rabbit Tree Hostel", body)


def build_404():
    body = head("Upside down", "This branch does not exist") + """
<section class="narrow center">
""" + para("You have found a secret passage that leads nowhere. Turn back, the tree is that way.") + """
<div class="btn-row"><a class="btn primary" href="[[home]]">Back home</a><a class="btn" href="[[rooms]]">The rooms</a></div>
</section>
"""
    return write("404.html", "Page not found | The Rabbit Tree Hostel", body)


# ============================================================ assemblage
def build_hostel_life():
    body = head("Life at the Rabbit Tree", "Every evening something happens. Most of it is free.") + """
<section class="narrow">
""" + para("The Rabbit Tree is more than a bed in a tree. Every evening, our staff and volunteers get everyone together: "
           "we meet at the reception, go and watch the sunset, then come back for dinner and games. You don't need to "
           "book anything, just follow the group, or the hostel's WhatsApp group where every plan is posted.") + """
<ol class="evening">
  <li><b>4pm</b><span>Sunset boat days: meet at the hostel</span></li>
  <li><b>5pm</b><span>Meet at the reception, off to the beach</span></li>
  <li><b>7pm</b><span>Back at the hostel: dinner and games</span></li>
  <li><b>Late</b><span>Movie, poker, or the ball pit…</span></li>
</ol>
</section>
<section><h2>Out at sunset</h2>
<div class="fiches">
""" + "".join(fiche(*f) for f in [
        ("Our favourite evening", "Sunset boat", "life-sunset-boat.webp", ("[[$-Sunset Boat|250K]]", "per person"),
         ["Meet 4pm at the hostel", "Snorkelling", "Plankton swim", "Dinner included"],
         "We meet at the hostel at 4pm, take a crew picture with bunny ears and walk together to the harbour. The boat "
         "takes us out for a snorkel before sunset (masks provided), the sun goes down behind Bali, and after dark we jump "
         "in again to **swim with the glowing plankton**. Back at the hostel, a plate of nasi goreng is waiting for "
         "everyone. Drinks are available on board."),
        ("Every evening", "Sunset on the beach", "life-sunset-beach.webp", ("Free", ""),
         ["Meet 5pm at reception", "Blankets & music", "Cold drinks"],
         "Every evening we meet at the reception around 5pm and walk to the beach with blankets, music and a cooler of "
         "cold drinks. Find a spot in the sand, swim, and **watch the sun go down** with the whole hostel. We always "
         "leave the beach as clean as we found it."),
        ("Before the sunset", "Beach volleyball", "life-volley.webp", ("Free", ""),
         ["5pm", "All levels", "On the beach"],
         "A friendly game on the beach court, until nobody can see the ball any more or everyone stops to watch the "
         "sunset. Nobody takes it seriously: **the losing team crawls between the legs of the winners**."),
    ]) + """
</div></section>
<section><h2>Back at the hostel</h2>
<div class="fiches">
""" + "".join(fiche(*f) for f in [
        ("Around the big table", "Family dinner", "life-dinner.webp", ('<span class="px" data-pos="Family Dinner">70K</span>', "per person"),
         ["Buffet", "Vegetarian", "Indonesian home cooking"],
         "A buffet of Indonesian home cooking laid out on the bar: corn fritters, yellow tofu curry, gado-gado, "
         "shredded carrots with fried tempeh. Everyone sits together at the big table: **the best way to meet the "
         "whole hostel**."),
        ("After the sunset", "Games night", "life-games.webp", ("Free", ""),
         ["7pm", "Everybody plays", "Silly rules"],
         "Back from the beach, the games start while people order their food: Happy Salmon, charades, a quiz that gets "
         "everyone moving, sardines (hide-and-seek the other way round), the Black Ball treasure hunt hidden all over "
         "the hostel… **Nobody stays on the bean bags for long.**"),
        ("Dress up", "Gala night: gender bender", "life-gala.webp", ("Free", ""),
         ["Fancy dress", "Limbo", "Giant Twister"],
         "Everybody digs the fanciest outfit out of the bottom of their backpack, with a twist: **the boys dress as "
         "girls and the girls as boys**. Then limbo, Bang! and giant Twister, with the music turned up."),
        ("Slow night", "Movie & poker night", "life-movie.webp", ("Free", ""),
         ["Cinema corner", "Movie voted by guests", "Poker table"],
         "The cinema corner fills up with cushions and bean bags, and the film is **chosen by a poll** in the hostel's "
         "WhatsApp group. Order from the bar and your food is served while the movie plays. Card players set up a "
         "poker table next door."),
    ]) + """
</div>
<div class="note">Drinking water, Lombok coffee and black tea are free for everyone, all day, in the common area.</div>
</section>
<section class="menu-live" id="menu" data-menu hidden>
<h2>From our bar &amp; kitchen</h2>
<p>Straight from our till, so the prices are always the right ones. Order at the bar, or put it on your room.</p>
<div class="menu-cols"></div>
</section>
""" + gal_of("hostel-life", "In pictures") + """
<section>
<div class="btn-row"><a class="btn primary" href="../reservations/">Book your bed</a><a class="btn" href="../activities/">More things to do on Gili Meno</a></div>
</section>
"""
    return write("hostel-life/index.html", "Life at the Rabbit Tree: sunset boat, family dinner, games | Gili Meno", body,
                 "Every evening at the Rabbit Tree Hostel on Gili Meno: sunset on the beach, sunset boat with plankton swim, family dinner, games night, gala night and movie nights. Most of it is free.")


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    made = [build_home(), build_rooms()]
    for r in ROOMS:
        made.append(build_room(r))
    made += [build_reservations(), build_gallery(), build_story(), build_howto(), build_transports(),
             build_activities(), build_services(), build_culture(), build_useful(), build_tours(),
             build_komodo(), build_rinjani(), build_welcome(), build_hostel_life(), build_404()]
    shutil.copytree(os.path.join(HERE, "images"), os.path.join(DIST, "images"))
    shutil.copytree(os.path.join(HERE, "css"), os.path.join(DIST, "css"))
    shutil.copytree(os.path.join(HERE, "js"), os.path.join(DIST, "js"))
    shutil.copytree(os.path.join(HERE, "fonts"), os.path.join(DIST, "fonts"))

    # menage : ne garder que les visuels reellement utilises (HTML src/href + CSS url())
    used = set()
    for root, _, files in os.walk(DIST):
        for f in files:
            if f.endswith(".html"):
                h = open(os.path.join(root, f), encoding="utf-8").read()
                used |= set(re.findall(r"(?:src|href)=\"[^\"]*?images/([\w.\-]+\.webp)\"", h))
    cssp = os.path.join(DIST, "css", "style.css")
    if os.path.exists(cssp):
        used |= set(re.findall(r"url\([\"']?[^)\"']*?images/([\w.\-]+\.webp)",
                               open(cssp, encoding="utf-8").read()))
    used.add(FAVICON)
    used |= KEEP_IMAGES
    imgdir = os.path.join(DIST, "images")
    dropped = 0
    for f in sorted(os.listdir(imgdir)):
        if f.endswith(".webp") and f not in used:
            os.remove(os.path.join(imgdir, f))
            dropped += 1
    kb = sum(os.path.getsize(os.path.join(r, x)) for r, _, xs in os.walk(DIST) for x in xs) / 1024
    print("images conservees:", len(os.listdir(imgdir)), "| retirees:", dropped, "| site: {:.1f} Mo".format(kb / 1024))
    print("pages generees:", len(made))
    # GitHub Pages publie le dossier docs/ : on le remplace par la version fraiche
    # nom de domaine (GitHub Pages lit ce fichier) ; DNS chez Cloudflare, en "DNS only"
    open(os.path.join(DIST, "CNAME"), "w").write("therabbittree.page\n")
    docs = os.path.join(ROOT, "docs")
    if os.path.isdir(docs):
        shutil.rmtree(docs)
    shutil.copytree(DIST, docs)
    print("docs/ mis a jour")
    for m in sorted(made):
        print("  ", m)


if __name__ == "__main__":
    main()
