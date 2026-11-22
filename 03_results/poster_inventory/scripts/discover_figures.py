"""Read-only discovery of every tracked figure file (PNG, SVG, PDF) in the repository.

For each file: path, format, pixel or vector size, aspect ratio, SHA-256 and the metadata already recorded about it by
the repository's own manifests (figure-system FIGURE_MANIFEST, PUBLICATION_MANIFEST, v1 Q1/H1/AV manifests, v2
manifest) and by the v1 historical FIGURE_INVENTORY (status, Q1 replacement, duplication, known defects). Nothing is
modified. Writes 03_results/poster_inventory/data/figure_files_raw.csv.
Usage (repository root): python 03_results/poster_inventory/scripts/discover_figures.py
"""
import hashlib
import re
import struct
import subprocess
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "03_results/poster_inventory/data"
V1 = "03_results/integrated_validation_v1"


def png_size(b):
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None, None, None
    w, h = struct.unpack(">II", b[16:24])
    dpi = None
    i = 8
    while i < len(b) - 12:
        n = struct.unpack(">I", b[i:i + 4])[0]
        t = b[i + 4:i + 8]
        if t == b"pHYs":
            px, _, unit = struct.unpack(">IIB", b[i + 8:i + 17])
            dpi = round(px * 0.0254) if unit == 1 else None
        if t in (b"IDAT", b"IEND"):
            break
        i += 12 + n
    return w, h, dpi


def svg_size(b):
    head = b[:4000].decode("utf-8", "replace")
    vb = re.search(r'viewBox="([\d.\-\s]+)"', head)
    w = re.search(r'<svg[^>]*\swidth="([\d.]+)(\w*)"', head, re.S)
    h = re.search(r'<svg[^>]*\sheight="([\d.]+)(\w*)"', head, re.S)
    if w and h:
        return float(w.group(1)), float(h.group(1)), w.group(2) or "px"
    if vb:
        x = [float(v) for v in vb.group(1).split()]
        return x[2], x[3], "viewBox"
    return None, None, None


def pdf_size(b):
    m = re.search(rb"/MediaBox\s*\[\s*([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s*\]", b[:400000])
    if not m:
        return None, None, None
    x0, y0, x1, y1 = map(float, m.groups())
    return x1 - x0, y1 - y0, "pt"


def text_count(b):
    return len(re.findall(rb"<text\b", b))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "*.png", "*.svg", "*.pdf"], cwd=REPO,
                           capture_output=True, text=True, check=True).stdout.splitlines()
    rows = []
    for f in files:
        p = REPO / f
        b = p.read_bytes()
        ext = p.suffix.lower()[1:]
        if ext == "png":
            w, h, dpi = png_size(b)
            unit = "px"
        elif ext == "svg":
            w, h, unit = svg_size(b)
            dpi = None
        else:
            w, h, unit = pdf_size(b)
            dpi = None
        rows.append(dict(path=f, filename=p.name, stem=p.stem, folder=str(Path(f).parent).replace("\\", "/"), format=ext.upper(),
                         width=w, height=h, size_unit=unit, dpi=dpi, aspect_w_over_h=round(w / h, 4) if w and h else None,
                         bytes=len(b), svg_text_elements=text_count(b) if ext == "svg" else None,
                         svg_embeds_raster=(b"<image" in b) if ext == "svg" else None,
                         sha256=hashlib.sha256(b).hexdigest()))
    df = pd.DataFrame(rows)
    # --- join recorded metadata ---------------------------------------------------------------
    inv = pd.read_csv(REPO / V1 / "publication_q1/quality_control/FIGURE_INVENTORY.csv").set_index("path")
    for c in ("study", "family", "scientific_question", "source_data", "eligibility", "q1_replacement", "action", "duplication",
              "known_defects"):
        df[f"v1inv_{c}"] = df.path.map(inv[c]) if c in inv else None
    mans = []
    for m, kind in ((f"{V1}/publication_q1/quality_control/Q1_FIGURE_MANIFEST.csv", "Q1"),
                    (f"{V1}/h1_validation/quality_control/H1_FIGURE_MANIFEST.csv", "H1"),
                    (f"{V1}/advanced_validation/quality_control/AV_FIGURE_MANIFEST.csv", "AV"),
                    ("03_results/integrated_validation_v2/05_figures/V2_FIGURE_MANIFEST.csv", "V2")):
        t = pd.read_csv(REPO / m)
        for r in t.itertuples():
            for col in ("png", "svg"):
                mans.append(dict(path=getattr(r, col), man_package=kind, man_figure_id=r.figure_id, man_title=r.title,
                                 man_question=r.scientific_question, man_sources=r.source_tables, man_caption=r.caption,
                                 man_qa_status=r.qa_status, man_study=getattr(r, "study", kind)))
    for m in subprocess.run(["git", "ls-files", "03_results/figures/*FIGURE_MANIFEST.csv"], cwd=REPO, capture_output=True,
                            text=True).stdout.split():
        t = pd.read_csv(REPO / m)
        for r in t.itertuples():
            mans.append(dict(path=r.output_file, man_package="figure_system:" + m.split("/")[-2], man_figure_id=r.figure_id,
                             man_title=r.title, man_question=r.research_question, man_sources=r.input_file,
                             man_caption=r.caption, man_qa_status=" / ".join(str(getattr(r, k, "")) for k in ("status", "lifecycle_status", "evidence_status")),
                             man_study="R2 (H2-SimNet)"))
    M = pd.DataFrame(mans).drop_duplicates("path")
    df = df.merge(M, on="path", how="left")
    pub = pd.read_csv(REPO / "03_results/PUBLICATION_MANIFEST.csv")
    df["in_publication_manifest"] = df.path.isin(pub.output_file)
    df.to_csv(OUT / "figure_files_raw.csv", index=False, lineterminator="\n")
    print(len(df), "files;", df.format.value_counts().to_dict())
    print(df.groupby("folder").size().sort_values(ascending=False).head(40).to_string())
    print("with manifest:", df.man_package.notna().sum(), "| with v1 inventory:", df.v1inv_action.notna().sum())


if __name__ == "__main__":
    main()
