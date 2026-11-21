"""Finish one figure: layout QA on the live figure, export PNG + SVG, export QA, caption file,
manifest record. Every figure function in the fig_* modules ends by calling ``finish``."""
from pathlib import Path

import matplotlib.pyplot as plt

import q1qa
from q1style import FONT, Q1, font_path, rel, save


def finish(fig, meta, output_dir):
    """meta keys: id, stem, function, module, question, sources (list), caption, limitation, study."""
    layout = q1qa.layout_checks(fig)
    png, svg = save(fig, meta["stem"], output_dir)
    plt.close(fig)
    files, info = q1qa.file_checks(png, svg)
    issues = layout + files
    cap_dir = Path(meta.get("caption_dir", Q1 / "captions"))
    cap_dir.mkdir(parents=True, exist_ok=True)
    cap = cap_dir / f"{meta['stem']}.md"
    src = "\n".join(f"- `{s}`" for s in meta["sources"])
    cap.write_text(
        f"# {meta['id']} — {meta['title']}\n\n"
        f"**Scientific question.** {meta['question']}\n\n"
        f"**Caption.** {meta['caption']}\n\n"
        f"**Interpretation limit.** {meta['limitation']}\n\n"
        f"**Source data.**\n{src}\n\n"
        f"**Code.** `scripts/{meta['module']}.py::{meta['function']}` · "
        f"Files: `figures/{meta['stem']}.png`, `figures/{meta['stem']}.svg`\n",
        encoding="utf-8", newline="\n")
    return {
        "figure_id": meta["id"], "study": meta["study"], "title": meta["title"],
        "scientific_question": meta["question"], "source_tables": "; ".join(meta["sources"]),
        "script": f"{meta.get('script_dir', 'publication_q1/scripts')}/{meta['module']}.py::{meta['function']}",
        "png": rel(png), "svg": rel(svg), "caption": rel(cap),
        "width_px": info["width_px"], "height_px": info["height_px"], "dpi": info["dpi"],
        "font": FONT, "font_file": Path(font_path()).name, "svg_font_families": info["svg_font_families"],
        "background": "#FFFFFF", "data_verification": meta.get("verification", "values read from source tables"),
        "qa_issues": " | ".join(issues), "qa_status": "APPROVED" if not issues else "REVISE",
        "png_sha256": q1qa.sha256(png), "svg_sha256": q1qa.sha256(svg),
    }
