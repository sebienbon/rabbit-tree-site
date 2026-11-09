"""Recupere les horaires des bateaux rapides Wijaya Perkasa pour Gili Meno, sans IA.

Lit https://www.wijayaperkasa.com/schedule/ (tableaux HTML FROM | TO | PRICE | DEPARTURE | ARRIVAL ;
les cellules FROM / TO vides reprennent la valeur de la ligne au-dessus), garde les trajets qui
partent de Gili Meno ou y arrivent, et ecrit data/wijaya.json.
Si la page est injoignable ou si sa forme a change (trop peu de lignes trouvees), le script
s'arrete en erreur SANS toucher au fichier : le site garde les derniers horaires connus.
Lance chaque nuit par .github/workflows/wijaya.yml (serveurs de GitHub, gratuit).
"""
import json, os, re, sys, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

URL = "https://www.wijayaperkasa.com/schedule/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "wijaya.json")
TIME = re.compile(r"^\s*(\d{1,2})[:.](\d{2})\s*$")
HOME = "gili meno"
SKIP = ("lembongan",)   # destinations retirees du site


class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def parse(html):
    p = Rows()
    p.feed(html)
    out, frm, to = [], "", ""
    for r in p.rows:
        if len(r) < 5 or r[0].upper() == "FROM":
            continue
        frm = r[0] or frm
        to = r[1] or to
        dep, arr = TIME.match(r[3]), TIME.match(r[4])
        if not (frm and to and dep and arr):
            continue
        out.append({"from": frm, "to": to,
                    "dep": "{:02d}:{}".format(int(dep.group(1)), dep.group(2)),
                    "arr": "{:02d}:{}".format(int(arr.group(1)), arr.group(2))})
    return out


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (RabbitTreeHostel timetable)"})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    rows = parse(html)
    if "--debug" in sys.argv:
        print(len(html), html.count("<table"), html.count("<tr"), html.count("<td"))
        for k in ("admin-ajax", "tablepress", "data-tab", "elementor-tab", "e-n-tab", "jet-", "wpdt", "ninja_table"):
            print(k, html.count(k))
        i = html.find("<table"); print(html[i:i + 3000])
        j = html.find("<table", i + 10); print("SECOND", html[j - 800:j + 1500] if j > 0 else None)
        for r in Rows.__new__(Rows) and []: pass
    mine = [r for r in rows if HOME in (r["from"].lower(), r["to"].lower())
            and not any(s in (r["from"] + r["to"]).lower() for s in SKIP)]
    # dedoublonnage + tri par heure de depart
    seen, clean = set(), []
    for r in sorted(mine, key=lambda r: (r["from"] != "Gili Meno", r["dep"], r["to"])):
        k = (r["from"], r["to"], r["dep"], r["arr"])
        if k not in seen:
            seen.add(k)
            clean.append(r)
    if len(rows) < 20 or len(clean) < 4:
        sys.exit("Page changed or unreachable: {} rows, {} for Gili Meno. Keeping the old timetable.".format(len(rows), len(clean)))
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    if old.get("rows") == clean:
        print("Timetable unchanged.")
        return
    json.dump({"source": URL, "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "rows": clean},
              open(OUT, "w"), indent=1)
    print("Timetable updated: {} trips.".format(len(clean)))


if __name__ == "__main__":
    main()
