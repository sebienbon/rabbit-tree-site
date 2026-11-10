"""Prepare le petit jeu des oreilles de lapin de l'accueil (lance par build.py, rien au chargement de la page).
1. images/rabbit-ears.webp : les oreilles, a l'encre, fond transparent.
2. pour chaque dessin de l'accueil : des points sur le contour exterieur du trait noir, avec la direction
   « vers l'exterieur » ; les oreilles sortiront de derriere le trait a l'un de ces points, tire au hasard."""
import json, math, os
import numpy as np
from PIL import Image
from scipy import ndimage
import cv2

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_ears(src, out):
    im = np.array(Image.open(src).convert("RGB")).astype(float)
    g = im.mean(2)
    ys, xs = np.where(g > 30)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    g = g[y0 - 4:y1 + 5, x0 - 4:x1 + 5]
    a = np.clip((g - 18) / 14, 0, 1) * 255          # trait plein, a l encre
    rgba = np.zeros(g.shape + (4,), np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = 0x1c, 0x1a, 0x17
    rgba[..., 3] = a.astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    img.thumbnail((120, 120), Image.LANCZOS)
    img.save(out, quality=90)


def candidates(path, n=14):
    im = Image.open(path).convert("RGBA")
    W, H = im.size
    a = np.array(im)[..., 3] > 90
    sil = ndimage.binary_closing(a, iterations=6)
    sil = ndimage.binary_fill_holes(sil)
    cs, _ = cv2.findContours(sil.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return []
    big = max(len(c) for c in cs)
    c = np.concatenate([c[:, 0, :] for c in cs if len(c) > big * .25])   # toutes les silhouettes notables
    blur = ndimage.gaussian_filter(sil.astype(float), 6)
    gy, gx = np.gradient(blur)
    pts, L = [], len(c)
    for k in range(n * 6):
        x, y = c[int(k * L / (n * 6))]
        nx, ny = -gx[y, x], -gy[y, x]                    # vers l'exterieur
        norm = math.hypot(nx, ny)
        if norm < 1e-4:
            continue
        ang = math.degrees(math.atan2(nx, -ny))          # 0 = vers le haut, 90 = vers la droite
        if abs(ang) > 115:                               # pas d'oreilles qui pendent vers le bas
            continue
        pts.append((round(100 * x / W, 1), round(100 * y / H, 1), round(ang)))
    # garder des points bien repartis
    step = max(1, len(pts) // n)
    return pts[::step][:n]


def all_candidates(arts):
    return {art: [(float(x), float(y), int(g)) for x, y, g in candidates(os.path.join(HERE, "images", art))] for art in arts}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        make_ears(sys.argv[1], sys.argv[2])
