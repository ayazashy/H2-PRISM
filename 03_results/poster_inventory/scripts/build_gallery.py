"""Indexed visual gallery of existing figures (read-only): labelled contact sheets of downscaled thumbnails plus an HTML
index that links every logical figure to its original files. Source figures are opened read-only and never modified.
Writes 03_results/poster_inventory/gallery/CONTACT_<group>.png and GALLERY.html.
"""
import html
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[3]
INV = REPO / "03_results/poster_inventory"
G = INV / "gallery"
TW, TH, COLS = 640, 380, 3


def font(n):
    for f in ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, n)
    return ImageFont.load_default()


def sheet(rows, name):
    n = len(rows)
    H = ((n + COLS - 1) // COLS) * (TH + 70) + 20
    img = Image.new("RGB", (COLS * (TW + 20) + 20, H), "#FFFFFF")
    d = ImageDraw.Draw(img)
    for i, r in enumerate(rows.itertuples()):
        x, y = 20 + (i % COLS) * (TW + 20), 20 + (i // COLS) * (TH + 70)
        with Image.open(REPO / r.png) as im:
            im = im.convert("RGB")
            im.thumbnail((TW, TH))
            img.paste(im, (x, y))
        d.rectangle([x - 1, y - 1, x + TW, y + TH], outline="#BBBBBB")
        d.text((x, y + TH + 6), f"{r.asset_id}", fill="#0E3F3C", font=font(18))
        d.text((x, y + TH + 30), r.png.split("/")[-1][:70], fill="#444444", font=font(14))
    G.mkdir(parents=True, exist_ok=True)
    img.save(G / f"CONTACT_{name}.png", optimize=True)


def main():
    f = pd.read_csv(INV / "01_COMPLETE_FIGURE_INVENTORY.csv")
    f = f[f.png.notna()]
    for grp, g in f.groupby("gallery_group"):
        for k in range(0, len(g), 12):
            sheet(g.iloc[k:k + 12], f"{grp}_{k // 12 + 1}")
    out = ["<!doctype html><meta charset='utf-8'><title>H2-PRISM figure gallery</title>",
           "<style>body{font-family:Arial,sans-serif;background:#F4F4E9;color:#0E3F3C;margin:16px}"
           "figure{display:inline-block;width:300px;margin:8px;vertical-align:top}img{width:300px;border:1px solid #ccc;background:#fff}"
           "figcaption{font-size:12px}</style><h1>H₂-PRISM figure gallery (existing figures, unmodified)</h1>"]
    for grp, g in f.groupby("gallery_group"):
        out.append(f"<h2>{html.escape(grp)} ({len(g)})</h2>")
        for r in g.itertuples():
            rel = "../../../" + r.png
            out.append(f"<figure><a href='{rel}'><img loading='lazy' src='{rel}'></a><figcaption><b>{html.escape(r.asset_id)}</b> · "
                       f"{html.escape(str(r.evidence_status))} · {html.escape(str(r.lifecycle))}<br>{html.escape(str(r.title))[:120]}"
                       f"</figcaption></figure>")
    (G / "GALLERY.html").write_text("\n".join(out), encoding="utf-8", newline="\n")
    print("sheets:", len(list(G.glob("CONTACT_*.png"))))


if __name__ == "__main__":
    main()
