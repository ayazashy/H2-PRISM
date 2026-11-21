"""Automated figure QA: layout (clipping, overlap, minimum font size, font family) on the live
Matplotlib figure, and export checks (size, DPI, white background, SVG parse/font) on the files."""
import hashlib
import itertools
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from matplotlib.text import Text
from PIL import Image

from q1style import DPI, FONT

MIN_PT = 8.0
LEGACY_BG = (0xF4, 0xF4, 0xE9)


def _texts(fig):
    """Visible, non-empty text artists that are actually drawn. Tick labels of ticks outside the
    view interval exist as artists but are never rendered, so only drawn ticks are kept."""
    tick_all, tick_drawn = set(), set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            for tk in axis.get_major_ticks() + axis.get_minor_ticks():
                tick_all.update((id(tk.label1), id(tk.label2)))
            if not ax.axison or not axis.get_visible():
                continue  # hidden axis: no tick label is rendered
            for tk in axis._update_ticks():  # the ticks Matplotlib will draw
                tick_drawn.update((id(tk.label1), id(tk.label2)))
    out = []
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        if id(t) in tick_all and id(t) not in tick_drawn:
            continue
        out.append(t)
    return out


def layout_checks(fig):
    """Return a list of human-readable issues; empty when the layout passes."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.bbox.width, fig.bbox.height
    issues, boxes = [], []
    for t in _texts(fig):
        bb = t.get_window_extent(r)
        if bb.width == 0 or bb.height == 0:
            continue
        label = t.get_text()[:40].replace("\n", " ")
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > W + 1 or bb.y1 > H + 1:
            issues.append(f"clipped text: '{label}'")
        if t.get_fontsize() < MIN_PT - 1e-9:
            issues.append(f"font below {MIN_PT} pt ({t.get_fontsize():.1f}): '{label}'")
        fam = t.get_fontfamily()
        names = [f for f in fam if f not in ("serif",)]
        if names and FONT not in names:
            issues.append(f"font family {fam}: '{label}'")
        boxes.append((t, bb, label))
    for (t1, b1, l1), (t2, b2, l2) in itertools.combinations(boxes, 2):
        if getattr(t1, "_q1_allow_overlap", False) or getattr(t2, "_q1_allow_overlap", False):
            continue
        ix = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
        iy = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
        if ix > 1.5 and iy > 1.5:
            issues.append(f"overlap: '{l1}' x '{l2}'")
    return issues


def file_checks(png, svg):
    issues = []
    with Image.open(png) as im:
        w, h = im.size
        dpi = im.info.get("dpi", (0, 0))[0]
        a = np.asarray(im.convert("RGB"))
    if max(w, h) < 3200:
        issues.append(f"PNG long side {max(w, h)} < 3200")
    if round(dpi) < DPI - 1:
        issues.append(f"PNG dpi {dpi}")
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    if not (border == 255).all():
        issues.append("PNG border not pure white")
    if (a == np.array(LEGACY_BG)).all(axis=2).any():
        issues.append("legacy #F4F4E9 pixels present")
    tree = ET.parse(svg)
    ns = "{http://www.w3.org/2000/svg}"
    fams = set()
    for el in tree.iter():
        st = el.get("style") or ""
        for part in st.split(";"):
            if part.strip().startswith("font-family"):
                fams.add(part.split(":", 1)[1].strip())
        if el.get("font-family"):
            fams.add(el.get("font-family"))
    bad = [f for f in fams if FONT not in f]
    if bad:
        issues.append(f"SVG font families {bad}")
    if not fams:
        issues.append("SVG has no live text")
    if tree.getroot().find(f".//{ns}image") is not None:
        issues.append("SVG embeds a raster image")
    txt = Path(svg).read_text(encoding="utf-8")
    if "#f4f4e9" in txt.lower():
        issues.append("SVG contains #F4F4E9")
    return issues, {"width_px": w, "height_px": h, "dpi": round(dpi), "svg_font_families": "; ".join(sorted(fams))}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
