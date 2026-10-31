# -*- coding: utf-8 -*-
"""Genere le site statique The Rabbit Tree Hostel (content.py + inventory.json -> HTML)."""
import json, os, re, shutil, sys
from content import HOSTEL, INTRO, MAP_SPOTS, ROOMS, TREE_EXTRA, BOOKING_NOTE, PAGE_MEDIA, NAV, INFO_LINKS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INV = json.load(open(os.path.join(ROOT, "scrape", "inventory.json"), encoding="utf-8"))
MAN = json.load(open(os.path.join(HERE, "images_manifest.json"), encoding="utf-8"))
_MAN_BY_FILE = {v["file"]: (v["orig_w"], v["orig_h"]) for v in MAN.values()}
DIST = os.path.join(HERE, "dist")
FAVICON = "tree-home.webp"

# ------------------------------------------------------------------ helpers
def stem(url):
    return url.split("/v1/")[0].split("/fill/")[0].split("/crop/")[0].rsplit("/", 1)[-1]


_EXCLUDE_PHOTOS = {"old-fashion-boat.webp"}


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
        if not m or m["file"] in seen or m["kind"] != "photo" or m["bytes"] < min_bytes:
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


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para(text, cls=""):
    parts = [p.strip() for p in str(text).split("\n\n") if p.strip()]
    return "".join('<p class="{}">{}</p>'.format(cls, esc(p)) if cls else "<p>{}</p>".format(esc(p)) for p in parts)


def ul(items):
    return "<ul>" + "".join("<li>{}</li>".format(i if i.startswith("<") else esc(i)) for i in items) + "</ul>"


def banner_of(key):
    b = PAGE_MEDIA.get(key, {}).get("banner")
    if not b:
        return ""
    f, a = b[0], b[1]
    keep = b[2] if len(b) > 2 else 1.0
    if keep and keep < 1.0:
        dims = _MAN_BY_FILE.get(f)
        if dims:
            nw, nh = dims
            style = ' style="aspect-ratio:{w}/{h};object-fit:cover;object-position:center;height:auto"'.format(
                w=nw, h=int(round(nh * keep)))
            return '<div class="banner"><img src="images/{f}" alt="{a}" loading="eager"{s}></div>'.format(f=f, a=esc(a), s=style)
    return '<div class="banner"><img src="images/{f}" alt="{a}" loading="eager"></div>'.format(f=f, a=esc(a))


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
            out.append('<a href="images/{f}" data-lb><img src="images/{f}" alt="{a}" loading="lazy"></a>'.format(f=f, a=esc(a)))
    return '<div class="strip">' + "".join(out) + "</div>"


def table(headers, rows):
    h = "".join("<th>{}</th>".format(esc(c)) for c in headers)
    b = "".join("<tr>" + "".join("<td{}>{}</td>".format(' class="price"' if isinstance(c, tuple) else "",
                  c[0] if isinstance(c, tuple) else esc(c)) for c in r) + "</tr>" for r in rows)
    return '<table><thead><tr>{}</tr></thead><tbody>{}</tbody></table>'.format(h, b)


# ------------------------------------------------------------------ gabarit
HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Chelsea+Market&family=Amatic+SC:wght@400;700&family=Kalam:wght@300;400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css}">
<link rel="icon" href="{fav}" type="image/webp">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#f2d98c">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="nav" id="nav">
  <a class="nav-brand" href="{brand}">The Rabbit Tree<span>Gili Meno</span></a>
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
      <a href="{ta}" aria-label="Tripadvisor">TA</a><a href="{wa}" aria-label="WhatsApp">WA</a></div></div>
    <div><h3>Good to know</h3><p>{info}</p></div>
  </div>
  <div class="foot-note"><span>&copy;2017&ndash;2026 The Rabbit Tree Hostel</span><span>Gili Meno &mdash; {phone}</span></div>
</footer>
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Photo"><button class="x" aria-label="Close">&times;</button><img alt=""></div>
<script src="{js}"></script>
</body>
</html>"""


def render(rel_path, title, body, desc=""):
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
    head = HEAD.format(title=esc(title), desc=esc(desc or DEFAULT_DESC), css=pre + "css/style.css?v=16",
                       fav=pre + "images/" + FAVICON, brand=pre, nav="".join(items),
                       cta=pre + "reservations/")
    foot = FOOT.format(tel=HOSTEL["phone_tel"], phone=esc(HOSTEL["phone_display"]), wa=HOSTEL["whatsapp"],
                       maps=HOSTEL["maps"], addr=esc(HOSTEL["address"]), mail=HOSTEL["email"],
                       ig=HOSTEL["instagram"], fb=HOSTEL["facebook"], ta=HOSTEL["tripadvisor"],
                       info=info, js=pre + "js/main.js?v=16")
    return head + body + foot


DEFAULT_DESC = ("The Rabbit Tree Hostel, Gili Meno: creative rooms, a ball pit bedroom, cheap boats "
                "to and from Bali and Lombok, daily activities and Komodo or Rinjani adventures.")


def write(rel_path, title, body, desc=""):
    out = os.path.join(DIST, rel_path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(render(rel_path, title, body, desc))
    return rel_path


def head(title, sub=""):
    return ('<div class="page-head"><h1>{}</h1>'.format(title) +
            ('<div class="lead">{}</div>'.format(sub) if sub else "") +
            '<div class="rule"></div></div>')


# ============================================================ ACCUEIL
def build_home():
    spots = []
    for s in MAP_SPOTS:
        spots.append(
            '<a class="spot" href="[[{slug}]]" style="left:{x}%;top:{y}%;width:{w}%" title="{label}">'
            '<img src="images/{art}" alt="{label}" loading="eager" width="400" height="300">'
            '<span class="cap">{label}</span></a>'.format(**s))
    cards = "".join(
        '<a class="card" href="[[{slug}]]"><div class="thumb"><img src="images/{art}" alt="{label}" loading="lazy"></div>'
        '<h3>{label}</h3><p>{blurb}</p></a>'.format(**s) for s in MAP_SPOTS)
    body = head("The Rabbit Tree Hostel", "Welcome to the edge of reality") + """
<div class="hero">
  <div class="map">
    """ + "".join(spots) + """
  </div>
  <div class="grid c2 map-fallback">""" + cards + """</div>
  <div class="btn-row"><a class="btn primary" href="[[rooms]]">See the rooms</a>
  <a class="btn" href="[[reservations]]">Reservations</a>
  <a class="btn ghost" href="[[how-to-get-here]]">How to get here</a></div>
</div>
<section class="narrow center">
""" + para(INTRO, "lead") + """
</section>
<section>
  <h2>Everything on the map</h2>
  <p class="lead">Click a drawing, or use these if the map is too small on your screen.</p>
  <div class="grid c2">""" + cards + """</div>
</section>
<section class="center">
  <h2>10% cheaper than the booking websites</h2>
  <p class="lead">Write to us with your dates and we will sort out your room, your boat from Bali or Lombok,
  and everything you will do on the island.</p>
  <div class="btn-row"><a class="btn hot" href="mailto:THERABBITTREEGILIMENO@GMAIL.COM?subject=Room%20enquiry">Email us</a>
  <a class="btn primary" href="https://wa.me/62881037092855">WhatsApp us</a>
  <a class="btn" href="[[reservations]]">Booking form</a></div>
</section>
""".replace("THERABBITTREEGILIMENO@GMAIL.COM", HOSTEL["email"])
    return write("index.html", "The Rabbit Tree Hostel | Gili Meno, Lombok", body)


# ============================================================ CHAMBRES
def build_rooms():
    nodes = []
    for r in ROOMS + TREE_EXTRA:
        cap = '<span class="cap">{name}{}</span>'.format(
            ' <em>&middot; coming soon</em>' if r.get("soon") else "", **r)
        logo = '<img class="logo" src="images/{badge}" alt="{name}" loading="lazy">'.format(**r)
        if r.get("slug"):
            hit = '<a class="hit" href="[[rooms]]{}/" title="{name}">{}</a>'.format(r["slug"], logo + cap, **r)
        else:
            hit = '<span class="hit static" title="{name} {}">{}</span>'.format(r.get("soon", ""), logo + cap, **r)
        disc = ""
        if r.get("spiral") and r.get("spiral_on"):
            disc = ('<button class="disc" type="button" aria-label="Open {name}" title="{name}">'
                    '<img src="images/{spiral}" alt="" loading="lazy"></button>').format(**r)
        nodes.append('<div class="node" style="left:{x}%;top:{y}%;width:{w}%">'.format(**r)
                     + hit + disc + '</div>')
    cards = "".join(
        '<a class="card" href="[[rooms]]{slug}/"><div class="thumb"><img src="images/{badge}" alt="{name}" loading="lazy"></div>'
        '<span class="cat">{cat}</span><h3>{name}</h3><p>{beds} &middot; {air} &middot; {bath}</p></a>'.format(**r)
        for r in ROOMS)
    body = """<p class="crumb"><a href="[[home]]">Home</a> &rsaquo; Rooms</p>
<div class="page-head"><h1>The Rooms</h1><div class="lead">Eleven rooms, none of them ordinary. Click a branch.</div>
<div class="rule"></div></div>
<div class="tree-wrap">
  <img class="trunk" src="images/tree-rooms.webp" alt="Hand drawn tree holding the hostel rooms" width="1000" height="800">
  """ + "".join(nodes) + """
</div>
<section>
  <h2>All the rooms</h2>
  <div class="grid c3">""" + cards + """</div>
</section>
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
    specs = table(["Sleeps", "Beds", "Cooling", "Bathroom"],
                  [[r["sleeps"], r["beds"], r["air"], r["bath"]]])
    body = """<p class="crumb"><a href="[[home]]">Home</a> &rsaquo; <a href="[[rooms]]">Rooms</a> &rsaquo; {name}</p>
<div class="room-hero">
  <img class="room-badge" src="images/{badge}" alt="{name} room badge">
  <div>
    <span class="cat" style="font-family:var(--f-hand);font-weight:700;font-size:1.4rem;letter-spacing:.1em">{cat}</span>
    <h1>{name}</h1>
    {specs}
    {desc}
    <div class="btn-row" style="justify-content:flex-start">
      <a class="btn primary" href="[[reservations]]">Book this room</a>
      <a class="btn" href="[[rooms]]">Back to the tree</a>
    </div>
  </div>
</div>
""".format(name=esc(r["name"]), cat=esc(r["cat"]), badge=r["badge"], specs=specs,
           desc=para(" ".join(r["desc"])))
    if photos_block:
        body += photos_block
    body += '<div class="note">' + esc(BOOKING_NOTE) + "</div>"
    return write("rooms/{}/index.html".format(r["slug"]),
                 "{} | Rooms | The Rabbit Tree Hostel".format(r["name"]), body,
                 "{} at The Rabbit Tree Hostel, Gili Meno: {}. {}, {}.".format(
                     r["name"], r["beds"], r["air"], r["bath"]))


# ============================================================ RESERVATIONS
def build_reservations():
    rows = [[r["name"], r["cat"], r["sleeps"]] for r in ROOMS]
    body = head("Reservations", "10% cheaper than the booking websites") + banner_of("reservations") + """
<section class="narrow">
""" + para("Booking directly with us is cheaper than the big booking websites, and it is the only way to "
           "ask for one of the specific rooms you have fallen for. Tell us your dates and we will confirm "
           "straight away.") + """
<div class="note">""" + esc(BOOKING_NOTE) + """</div>
<div class="btn-row">
  <a class="btn hot" href="mailto:{mail}?subject=Booking%20request%20%E2%80%94%20The%20Rabbit%20Tree">Email us your dates</a>
  <a class="btn primary" href="{wa}">WhatsApp us</a>
  <a class="btn" href="{phone_link}">Call {phone}</a>
</div>
</section>
<section>
  <h2>The rooms at a glance</h2>
  <p>Prices change with the season, so ask us for an exact quote for your dates. Here is what each room holds:</p>
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
                 "hostelworld": HOSTEL["hostelworld"], "ta": HOSTEL["tripadvisor"]}.items():
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
<h3>From Bali (South Bali, Amed, Sanur, Nusa Penida/Lembongan...)</h3>
""" + ul(["Every day: a minibus picks you up in the biggest cities of Bali to reach Padang Bai.",
          "Then a daily ferry to Gili Trawangan (or Gili Air), and a local boat on to Gili Meno.",
          "We have the cheapest prices possible, have a look and ask us."]) + """
<h3>From Gili Trawangan</h3>
""" + ul(["Daily public boat at 09:30 and 16:00 — 40,000 IDR.",
          "Every hour by fast boat — 85,000 IDR."]) + """
<h3>From Lombok (Bangsal)</h3>
""" + ul(["Public boat at 10:00, 14:00 and 17:00 — 25,000 IDR."]) + """
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
    "hop": table(["Between", "Public boat", "Private / fast boat"],
        [["Gili Trawangan &harr; Gili Meno", ("40K",), ("85K, every hour",)],
         ["Gili Meno &harr; Gili Air", ("40K",), ("85K, every hour",)],
         ["Gili Air &harr; Gili Trawangan", ("40K",), ("85K, every hour",)]]),
    "lombok": table(["From / to", "Option", "Price"],
        [["Gili Meno &harr; Bangsal (Lombok)", "Public boat, 8am and 3.30pm", ("25K",)],
         ["Bangsal &harr; Mataram Airport", "Shuttle per person", ("140K",)],
         ["Bangsal &harr; Mataram Airport", "Taxi, up to 3 people", ("350K",)],
         ["Bangsal &harr; Kuta Lombok", "Shuttle per person", ("140K",)],
         ["Bangsal &harr; Senggigi", "Shuttle per person", ("110K",)],
         ["Bangsal &harr; Senggigi", "Taxi, up to 3 people", ("180K",)]]),
    "bali": table(["Ticket", "Price", "Notes"],
        [["Return Bali &harr; Gili Meno", ("630K",), "Open date return, two departures a day"],
         ["One way from Bali", ("325K",), "Pick up from 7am, boat around 9:30am"],
         ["One way from the Gilis", ("350K",), "Second departure around 13:00, pick up 10am"],
         ["Shuttle in Bali (Kuta, Seminyak, Canggu, Ubud, Jimbaran, Sanur Airport)", ("+100K",), "Per way"]]),
    "elsewhere": table(["Destination", "Price", "How"],
        [["Sanur (Bali)", ("400K",), "Fast boat from Gili Trawangan or Bangsal"],
         ["Lembongan", ("375K",), "Fast boat"],
         ["Nusa Penida", ("350K",), "Fast boat"],
         ["Amed", "Not available now", ""],
         ["Flores (Labuan Bajo)", ("850K",), "26 hours, bus and ferries"]]),
}


def build_transports():
    body = head("Transports", "Boats to and from the Gili Islands") + banner_of("transports") + """
<section class="narrow">
""" + para("It is very easy to travel between the Gilis, and we have bargained for you to get cheaper "
           "transportation, or at least the same price as anybody else here. So do not hesitate to contact us "
           "to book your ticket. It would be a shame to miss it.") + """
<div class="note">Two departures per day from Padang Bai to Gili Meno, around 9:30am (pick up 7am) and around
1pm (pick up 10am). From Gili Meno, two departures a day at about the same times. The boat also stops at
Gili Air, Gili Trawangan and Bangsal.</div>
</section>
""" + deco_of("transports") + gal_of("transports", "") + """
<section><h2>Gili island hopping</h2>
<p>Public boats run twice a day for 40K (8.50am / 3.20pm from Gili T, 9.30am / 4.00pm and 9.50am / 4.20pm
between the other pairs); private boats run every hour for 85K.</p>
""" + TRANSPORT["hop"] + """</section>
<section><h2>To and from Lombok</h2>
<p>Public boats link Gili Meno and Bangsal every day for 25K, at 8am and 3.30pm (10am, 2pm and 5pm the other way).
To go to or leave Bangsal we have special prices for shuttles and taxis.</p>
""" + TRANSPORT["lombok"] + """</section>
<section><h2>To and from Bali</h2>
<p>Our option is the cheapest one. It is cheaper to take the two-way ticket if you already know you will come
back to Bali, and it is an open date return, so you do not need to decide when you leave us.</p>
""" + TRANSPORT["bali"] + """
<p>You can also go directly to and from other places in Bali:</p>
""" + TRANSPORT["elsewhere"] + """
<div class="note">You are adventurous? A cheap way to reach Flores: a 26 hour trip including bus and ferries for 850K.</div>
<div class="btn-row"><a class="btn hot" href="mailto:{mail}?subject=Transport%20booking">Ask us to book a ticket</a>
<a class="btn primary" href="{wa}">WhatsApp us</a></div>
</section>
"""
    body = body.format(mail=HOSTEL["email"], wa=HOSTEL["whatsapp"])
    return write("transports/index.html", "Transports to and from the Gilis | The Rabbit Tree Hostel", body,
                 "Public and fast boat timetables and prices between Gili Meno, Gili Trawangan, Gili Air, Bangsal (Lombok) and Bali.")


# ============================================================ ACTIVITIES
def build_activities():
    body = head("What To Do In Gili Meno?", "Who said there was nothing to do on this island?") + banner_of("activities") + """
<section class="narrow">
""" + para("There are activities every day at the Rabbit Tree. It would be hard to include everything we do "
           "together, but let's give a few examples... In Gili Meno there is a lot to do, and it only takes one "
           "hour — or one day if you slow down and take your time to enjoy the wonderful places the island offers.") + """
</section>
<section><h2>At the hostel, every day</h2>
<div class="grid c3">
""" + "".join('<div class="card"><h3>{}</h3><p>{}</p></div>'.format(esc(a), esc(b)) for a, b in [
        ("Movie night", "The main sitting area turns into a cinema."),
        ("Yoga &amp; workout", "Start the day moving with the group."),
        ("Sunset on the beach", "Five minutes walk from the dorm."),
        ("Traditional dinner", "Eat with the staff and the locals."),
        ("Games night", "Board games, cards and silly challenges."),
        ("Walk around the island", "One hour by bike, a day if you stop often."),
    ]).replace("&amp;amp;", "&amp;") + """
</div></section>
<section><h2>On the island</h2>
<div class="grid c2">
""" + "".join('<div class="card"><h3>{}</h3>{}</div>'.format(esc(t), para(b)) for t, b in [
        ("Discover the lake and the mangroves", "Relax on the most lovely beach of the three Gilis, admire the sunrise or the sunset, and follow the lake path through the mangroves."),
        ("Visit the turtle sanctuary", "A place near the beach with four small pools. The aim is to collect the eggs from the shore before predators eat them, grow the little turtles until they are about a year old, and release them in their natural environment. Thanks to this work there are still a lot of turtles around Gili Meno. You can support it with a small donation."),
        ("Join the Trash Heroes", "Meet locals and travellers every Sunday around 3.30pm at the Brotherhood and walk together to collect the trash. It is an unforgettable moment to share with locals. They also take care of the trash bins around the island, so be sure to throw your waste in one of those."),
    ]) + """
</div></section>
<section><h2>Bookable activities, with us</h2>
""" + table(["Activity", "Price", "What you get"], [
        ["Snorkelling gear rental", ("30K",), "Mask for a day, and we mark the best spots on a map: turtles point, coral, the Bounty wreck"],
        ["Snorkelling boat trip, 3 hours", ("150K",), "4 spots including the underwater statues, the wreck and two turtle points. Max 15 people. 175K if fewer than 3 people on the boat"],
        ["Diving with Divine Divers", ("Club price",), "Discovery dives, fun dives and certificates. We offer the same prices as the club"],
        ["Horse riding around the island", ("400K",), "1h to 1h30 through the paths and the beach, morning or sunset. Departure and arrival at the Rabbit Tree"],
        ["Private fishing trip, 3 hours", ("350K",), "Bottom fishing for groupers and snappers, or crowling fishing for barracudas, giant trevally and sometimes tuna"],
        ["Spearfishing with a guide, 3 hours", ("380K",), "Leave straight from the beach; different local fish, maybe octopus"],
    ]) + """
</section>
""" + gal_of("activities", "Life at the tree, in pictures") + """
<section>
<div class="note">You would like to do some good things while you are here? The turtle sanctuary and the Trash
Heroes are two easy ways. Ask at the reception and we will take you.</div>
<div class="btn-row"><a class="btn primary" href="[[tours]]">Now go on a real adventure</a>
<a class="btn" href="[[services]]">What we rent at the reception</a></div>
</section>
""".replace("[[tours]]", "../tours/").replace("[[services]]", "../services/")
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
        ["Laundry", ("30K / kg",), "We take care of your clothes"],
        ["Towels", ("Free / 50K deposit",), "Free for guests in the couple bedrooms. Otherwise a 50K deposit, 30K given back after use"],
        ["Snorkelling mask", ("30K / day",), "We indicate the spots on a map: turtles point, best corals, Bounty wreck. We do not rent fins, but shops next to the beach do"],
        ["Bike rental", ("50K / day",), "To go faster around the island"],
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
""" + para("We offer different tours for all tastes. Do not hesitate to come to the reception to book what you want.") + """
</section>
<section>
<div class="grid c2">
  <a class="card" href="[[tours]]komodo/"><div class="thumb"><img src="images/img-3470ae751e2dd7.webp" alt="Komodo dragon" loading="lazy"></div>
    <h3>Komodo Tour</h3><p>Have you ever thought about seeing the dragons and the famous pink beach for real?
    3 days, 4 nights sailing around Lombok, north Sumbawa and the Komodo Islands, from 3,500,000 IDR.</p></a>
  <a class="card" href="[[tours]]rinjani/"><div class="thumb"><img src="images/rinj-jpg.webp" alt="Mount Rinjani trek" loading="lazy"></div>
    <h3>Rinjani Trek</h3><p>You are rather sporty and you like hiking? This one is for you. A 2 days 1 night trek
    to the summit of the famous volcano in Lombok, from 2,100,000 IDR.</p></a>
</div>
<div class="btn-row"><a class="btn primary" href="[[activities]]">Everything to do on the island</a></div>
</section>
""".replace("[[tours]]komodo/", "../tours/komodo/").replace("[[tours]]rinjani/", "../tours/rinjani/") \
   .replace("[[activities]]", "../activities/")
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
        ["Deck class", ("3,500,000 IDR",), "A mattress, pillow and blanket per person on a shared deck"],
        ["Cabin class", ("4,000,000 IDR",), "A private cabin for two with a fan, a double mattress, a pillow and a blanket per person"],
    ]) + """
<p>The return from Labuan Bajo (Flores) is not included. Two companies offer the same program and service in a
similar boat; the real difference is their communication skills, clarity of organisation, and the price.</p>
<h2>Included</h2>
""" + ul(["Three Indonesian meals a day (vegetarian and vegan options available) and snacks",
          "Unlimited coffee, tea and mineral water; a fruit plate for breakfast and fresh fruit juice once a day",
          "Entrance fee to Komodo National Park and an English speaking guide",
          "Bus to the departure port, and boat tickets from Gili Trawangan and Gili Air",
          "Mask and snorkel, plus traditional simple fishing gear",
          "Beanbags, and charging points for electronic devices (solar energy)",
          "Fresh water and a simple shower, lockers for your valuables, a cool box with ice for your extra drinks",
          "Safety equipment: lifejackets, life raft and ring lifebuoy"]) + """
<h2>Not included</h2>
""" + ul(["Wifi connection", "Fins", "Pick up from Kuta Lombok (negotiate transport with the agent you book from)",
          "The way back from Labuan Bajo"]) + """
<div class="note">Please tell your tour guide about any dietary requirement. Guests with food allergies should be
aware that the food may contain or come into contact with common allergens such as dairy, eggs, wheat, soybeans,
tree nuts, peanuts, fish and shellfish, and that cross-contamination may occur.</div>
<div class="btn-row"><a class="btn hot" href="mailto:{mail}?subject=Komodo%20trip">Book the Komodo trip</a>
<a class="btn primary" href="{wa}">WhatsApp us</a><a class="btn" href="[[tours]]">Other adventures</a></div>
</section>
"""
    body = body.format(mail=HOSTEL["email"], wa=HOSTEL["whatsapp"]).replace("[[tours]]", "../")
    return write("tours/komodo/index.html", "Komodo Trip 4D3N | The Rabbit Tree Hostel", body,
                 "Four day live-on-board sailing trip to the Komodo islands from Gili Meno: whale sharks, Pink Beach, Padar and the dragons. From 3,500,000 IDR.")


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
           "summit, the lake, the hot spring, the Senaru crater rim and down to Senaru village. Day 1 follows the "
           "same route as the 2 day trek. On the final day, after breakfast we commence our descent of the mountain, "
           "using the rest spots of Pos 3, Pos 2 and Pos 1 and stopping for lunch along the way. As we descend, the "
           "forest becomes thicker and increasingly lush. We arrive in Senaru (601 m) at approximately 1 pm, from "
           "where you will be transported to your next destination.") + """
</section>
""" + gal_of("rinjani", "The trek in pictures") + """
<section><h2>Prices</h2>
""" + table(["Trek", "Price per person", "Notes"], [
        ["Rinjani 2D/1N summit", ("2,100,000 IDR",), "Includes one night in a homestay prior to departure"],
        ["Rinjani 2D/1N summit", ("2,150,000 IDR",), "The option sold from the hostel, transport from Gili Meno included"],
        ["Rinjani 3D/2N summit, lake and hot springs", ("2,350,000 IDR",), "The longer route down through Senaru"],
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
  <a class="card" href="[[transports]]"><h3>From and to Bali</h3><p>Two departures a day, return ticket 630K.</p></a>
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
def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    made = [build_home(), build_rooms()]
    for r in ROOMS:
        made.append(build_room(r))
    made += [build_reservations(), build_gallery(), build_story(), build_howto(), build_transports(),
             build_activities(), build_services(), build_culture(), build_useful(), build_tours(),
             build_komodo(), build_rinjani(), build_welcome(), build_404()]
    shutil.copytree(os.path.join(HERE, "images"), os.path.join(DIST, "images"))
    shutil.copytree(os.path.join(HERE, "css"), os.path.join(DIST, "css"))
    shutil.copytree(os.path.join(HERE, "js"), os.path.join(DIST, "js"))

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
    imgdir = os.path.join(DIST, "images")
    dropped = 0
    for f in sorted(os.listdir(imgdir)):
        if f.endswith(".webp") and f not in used:
            os.remove(os.path.join(imgdir, f))
            dropped += 1
    kb = sum(os.path.getsize(os.path.join(r, x)) for r, _, xs in os.walk(DIST) for x in xs) / 1024
    print("images conservees:", len(os.listdir(imgdir)), "| retirees:", dropped, "| site: {:.1f} Mo".format(kb / 1024))
    print("pages generees:", len(made))
    for m in sorted(made):
        print("  ", m)


if __name__ == "__main__":
    main()
