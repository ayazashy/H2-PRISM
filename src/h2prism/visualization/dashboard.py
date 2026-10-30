"""
H2-PRISM Visualization Engine — Interactive HTML Dashboard Generator
Owner: Research & Visualization Lead
Builds a standalone, responsive single-page HTML report summarizing models and results.
"""

import base64
from pathlib import Path
from typing import Dict, List, Optional, Union
import time


def encode_image_base64(image_path: Union[str, Path]) -> str:
    """Encodes an image file to base64 data URI."""
    p = Path(image_path)
    if not p.exists():
        return ""
    with open(p, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = p.suffix.lower().replace(".", "")
    mime = "image/png" if ext == "png" else f"image/{ext}"
    return f"data:{mime};base64,{data}"


def generate_html_report(
    figures_dict: Dict[str, Union[str, Path]],
    metrics_summary: Dict[str, Any],
    output_html_path: Union[str, Path] = "03_results/dashboard.html",
    title: str = "H2-PRISM Stage 2: Experimental Evaluation Dashboard",
) -> Path:
    """
    Generates a high-resolution, self-contained HTML report with embedded figures and KPI cards.
    """
    out_p = Path(output_html_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Encode all figures
    encoded_figs = {}
    for name, path in figures_dict.items():
        encoded_figs[name] = encode_image_base64(path)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    # Build KPI cards HTML
    kpi_cards_html = ""
    for k, v in metrics_summary.items():
        val_str = f"{v:.1%}" if isinstance(v, float) and 0.0 <= v <= 1.0 else str(v)
        kpi_cards_html += f"""
        <div class="kpi-card">
            <div class="kpi-title">{k.replace('_', ' ').title()}</div>
            <div class="kpi-value">{val_str}</div>
        </div>
        """

    # Build Figures Grid HTML
    fig_sections_html = ""
    for name, uri in encoded_figs.items():
        if uri:
            fig_sections_html += f"""
            <div class="figure-container">
                <h3>{name.replace('_', ' ').title()}</h3>
                <img src="{uri}" alt="{name}">
            </div>
            """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --primary: #1E3A8A;
            --secondary: #0284C7;
            --accent: #D97706;
            --bg: #F8FAFC;
            --card-bg: #FFFFFF;
            --text-dark: #0F172A;
            --text-muted: #64748B;
            --border: #E2E8F0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--bg);
            color: var(--text-dark);
            line-height: 1.5;
        }}
        .header {{
            background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
            color: #FFFFFF;
            padding: 2.5rem 2rem;
            border-bottom: 3px solid var(--secondary);
        }}
        .header h1 {{
            margin: 0 0 0.5rem 0;
            font-size: 1.8rem;
            letter-spacing: -0.5px;
        }}
        .header p {{
            margin: 0;
            color: #94A3B8;
            font-size: 0.95rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1.5rem;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
        }}
        .kpi-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .kpi-title {{
            font-size: 0.8rem;
            text-transform: uppercase;
            font-weight: 600;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }}
        .kpi-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--primary);
            margin-top: 0.25rem;
        }}
        .figures-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 2rem;
        }}
        .figure-container {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .figure-container h3 {{
            margin: 0 0 1rem 0;
            font-size: 1.1rem;
            color: var(--primary);
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }}
        .figure-container img {{
            width: 100%;
            height: auto;
            border-radius: 4px;
            display: block;
        }}
        .footer {{
            text-align: center;
            margin: 3rem 0;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>H2-PRISM Research & Engineering Framework | Generated: {timestamp}</p>
    </div>
    <div class="container">
        <h2>Executive Scorecard & Key Metrics</h2>
        <div class="kpi-grid">
            {kpi_cards_html}
        </div>

        <h2>Research Visualizations & Experimental Evidence</h2>
        <div class="figures-grid">
            {fig_sections_html}
        </div>

        <div class="footer">
            H2-PRISM — Identifiability-Aware Event Attribution and Selective Diagnosis in Hydrogen-Blend Pipeline Networks
        </div>
    </div>
</body>
</html>
"""
    with open(out_p, "w", encoding="utf-8") as f:
        f.write(html_content)
    return out_p
