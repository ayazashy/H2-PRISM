"""Shared Q1 figure style, export and per-figure bookkeeping for H2-PRISM.

* Times New Roman for all text, resolved through Matplotlib's font manager with no fallback.
  The font is used for rendering only; it is never copied, embedded or distributed
  (SVG keeps text as text, ``svg.fonttype = "none"``).
* Pure white (#FFFFFF) figure, axes, legend and saved backgrounds.
* Deterministic output: fixed SVG hash salt, no creation date, Agg rasteriser.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
Q1 = Path(__file__).resolve().parents[1]

C = {
    "navy": "#17324D", "teal": "#087E8B", "blue": "#3B6F9C", "burgundy": "#A44A4A",
    "ochre": "#BA8A28", "slate": "#64748B", "grid": "#E5E7EB", "text": "#20252B", "white": "#FFFFFF",
}
# Paired encodings so that categories survive grayscale printing: colour + marker + line style.
MODEL = {
    "persistence": dict(color=C["navy"], marker="o", ls="-", label="Persistence"),
    "ridge": dict(color=C["ochre"], marker="s", ls="--", label="Ridge"),
}
STATUS = {  # formal D(Y) cell status
    "EXCLUDED": dict(color=C["navy"], hatch=None, label="Excluded"),
    "CONSISTENT": dict(color=C["teal"], hatch=None, label="Consistent"),
    "INDETERMINATE": dict(color=C["ochre"], hatch=None, label="Indeterminate"),
    "UNSUPPORTED": dict(color=C["white"], hatch="////", label="Unsupported (no adapter)"),
}
DECISION = {
    "SPECIFIC": dict(color=C["teal"], hatch=None),
    "AMBIGUOUS": dict(color=C["ochre"], hatch="..."),
    "UNRESOLVED": dict(color=C["slate"], hatch="///"),
}
FONT = "Times New Roman"
FIG_W, FIG_H, DPI = 9.6, 5.4, 400  # 3840 x 2160 px


def font_path():
    """Return the file Matplotlib resolves for Times New Roman, refusing any fallback font."""
    return font_manager.findfont(font_manager.FontProperties(family=FONT), fallback_to_default=False)


def setup():
    path = font_path()
    if "times" not in Path(path).name.lower():
        raise RuntimeError(f"Times New Roman resolved to unexpected file {path}")
    plt.rcParams.update({
        "font.family": "serif", "font.serif": [FONT], "mathtext.fontset": "custom",
        "mathtext.rm": FONT, "mathtext.it": f"{FONT}:italic", "mathtext.bf": f"{FONT}:bold",
        "mathtext.default": "regular",
        "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 12, "xtick.labelsize": 10,
        "ytick.labelsize": 10, "legend.fontsize": 10, "legend.title_fontsize": 10, "figure.titlesize": 15,
        "text.color": C["text"], "axes.labelcolor": C["text"], "axes.edgecolor": C["text"],
        "xtick.color": C["text"], "ytick.color": C["text"], "axes.titlecolor": C["text"],
        "axes.linewidth": 0.8, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "grid.color": C["grid"], "grid.linewidth": 0.8,
        "figure.facecolor": C["white"], "axes.facecolor": C["white"], "savefig.facecolor": C["white"],
        "savefig.edgecolor": C["white"], "legend.facecolor": C["white"], "legend.edgecolor": C["grid"],
        "legend.framealpha": 1.0, "legend.frameon": False,
        "svg.fonttype": "none", "svg.hashsalt": "h2prism-q1", "hatch.linewidth": 0.8,
        "hatch.color": C["text"], "figure.dpi": 100, "path.simplify": False,
        "axes.unicode_minus": True, "figure.constrained_layout.use": False,
    })
    return path


def figure(w=FIG_W, h=FIG_H, **kw):
    fig = plt.figure(figsize=(w, h), layout="constrained", **kw)
    fig.get_layout_engine().set(w_pad=0.08, h_pad=0.08, wspace=0.04, hspace=0.04)
    return fig


def title(fig, text):
    fig.suptitle(text, fontsize=15, fontweight="bold", color=C["text"])


def ygrid(ax):
    ax.yaxis.grid(True, color=C["grid"], lw=0.8, zorder=0)
    ax.set_axisbelow(True)


def xgrid(ax):
    ax.xaxis.grid(True, color=C["grid"], lw=0.8, zorder=0)
    ax.set_axisbelow(True)


def save(fig, stem, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    png, svg = out_dir / f"{stem}.png", out_dir / f"{stem}.svg"
    fig.savefig(png, dpi=DPI, facecolor=C["white"], metadata={"Software": None})
    fig.savefig(svg, facecolor=C["white"], metadata={"Date": None, "Creator": None})
    # LF line endings on every platform, so recorded hashes survive Git's eol=lf normalisation
    svg.write_bytes(svg.read_bytes().replace(b"\r\n", b"\n"))
    return png, svg


def rel(path):
    return Path(path).resolve().relative_to(REPO).as_posix()
