"""Integrated cross-study Q1 figures (Center, MHC, HY2RES and the registered R2 experiment).

Figures that would duplicate a study-level or H1 figure are not redrawn; the Results document references them:
localization (Q1_C09, Q1_C10), restricted-universe false specificity (Q1_C14, H1-F06), RQ1 estimability (H1-F01) and
the RQ2 ablation (H1-F04a).
"""
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch

from q1fig import finish
from q1style import C, DECISION, MODEL, REPO, figure, title, xgrid, ygrid

MOD = "fig_integrated"
R2 = REPO / "03_results/primary_protocol/PRIMARY"
H1A = REPO / "03_results/integrated_validation_v1/h1_validation/analysis"
CEN = REPO / "03_results/validation/center_evidence_enhancement/tables"
MHC = REPO / "study_b/evidence_enhancement/results/analysis"
HY = REPO / "03_results/hy2res_external_validation/evidence_enhancement/results/analysis"
LIM = ("Studies differ in system, data type and evidence level and are not pooled; simulated (Center, H2-SimNet), "
       "experimental (MHC) and operational (HY2RES) evidence is reported side by side only.")
CLS = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
SHORT = {"NORMAL": "Normal", "LEAK": "Leak", "COMPRESSOR_FAULT": "Comp. fault", "COMPRESSOR_DELAY": "Comp. delay"}


def meta(fid, stem, fn, ttl, q, sources, cap, lim=LIM, ver="values read from accepted study tables"):
    return dict(id=fid, stem=f"{fid}_{stem}", function=fn, module=MOD, title=ttl, question=q, sources=sources,
                caption=cap, limitation=lim, study="Integrated", verification=ver)


def load():
    return {"res": pd.read_csv(MHC / "resolution.csv"), "quant": pd.read_csv(HY / "quantization_comparison.csv"),
            "c07": pd.read_csv(CEN / "TAB_C07.csv"), "conf": pd.read_csv(R2 / "confusion_matrix.csv"),
            "iu": pd.read_csv(H1A / "h1_02_independence_units_check.csv"), "rq2": pd.read_csv(R2 / "rq2.csv")}


def plot_integrated_evidence_architecture(d, out):
    fig = figure(h=6.0)
    title(fig, "H2-PRISM evidence architecture: four evidence sources, three layers")
    ax = fig.add_subplot()
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")
    cols = [("Center\ncontrolled simulation\n(air-like gas model)", C["navy"]),
            ("H2-SimNet / R2\nsimulated topologies\n(registered H1 test)", C["blue"]),
            ("MHC\nexperimental hydrogen\ncompressor", C["teal"]),
            ("HY2RES\noperational hydrogen\nsystem", C["ochre"])]
    layers = [("Layer I\nsource and\nmeasurement", ["12 captures re-verified;\n13 sensors", "27,993 windows; 36/57 runs\nattribution disputed",
                                                    "bit-identical replay;\n0.2 barg / 0.01 ln/min grid", "MD5-verified source;\n0.1 bar grid"]),
              ("Layer II\nreference and\nevidence validity", ["mechanism contrasts;\nsensor observability", "attainable coverage 0.258;\nflags block SPECIFIC",
                                                              "persistence MAE wins;\nRidge RMSE gain tiny", "drift out of support;\n97.8 % of abstentions"]),
              ("Layer III\ndiagnostic\ndecision", ["D(Y), conditional bounds:\n48 correct, 11 wrong\nSPECIFIC (restricted)", "RQ1 NOT_ESTIMABLE;\nH1 not established",
                                                   "no labels:\nblocked", "no fault labels:\nblocked"])]
    for j, (lab, c) in enumerate(cols):
        x = 2.3 + j * 2.4
        ax.add_patch(FancyBboxPatch((x, 6.55), 2.2, 1.25, boxstyle="round,pad=0.02,rounding_size=0.06", fc=C["white"], ec=c, lw=1.6))
        ax.text(x + 1.1, 7.17, lab, ha="center", va="center", fontsize=10, color=c, fontweight="bold")
    for i, (lab, cells) in enumerate(layers):
        y = 4.75 - i * 2.05
        ax.text(1.05, y + 0.75, lab, ha="center", va="center", fontsize=10.5, fontweight="bold", color=C["text"])
        for j, t in enumerate(cells):
            x = 2.3 + j * 2.4
            blocked = "blocked" in t
            ax.add_patch(FancyBboxPatch((x, y), 2.2, 1.5, boxstyle="round,pad=0.02,rounding_size=0.06",
                                        fc=C["white"], ec=C["slate"] if not blocked else C["burgundy"], lw=1.0,
                                        ls="-" if not blocked else "--"))
            ax.text(x + 1.1, y + 0.75, t, ha="center", va="center", fontsize=9.5, color=C["text"])
    cap = ("Evidence sources (columns) and evidence layers (rows) of the integrated package. Layer I: source identity, "
           "measurement and recording qualification. Layer II: reference behaviour and evidence validity. Layer III: "
           "diagnostic decisions. Dashed boxes: blocked by evidence (no qualified labels, bounds or locations). Numbers are "
           "taken from T01–T10 and the H1 report; studies are never pooled.")
    return finish(fig, meta("Q1_I01", "integrated_evidence_architecture", "plot_integrated_evidence_architecture",
                            "Evidence architecture", "How do the studies contribute to each evidence layer?",
                            ["publication_q1/tables/T01-T10", "h1_validation/tables/H1-T07.csv"], cap,
                            ver="cell text summarises verified table values"), out)


def _xstudy(d):
    r = d["res"].set_index("channel")
    q = d["quant"].set_index("channel")
    rows = [("MHC P-2 (0.2 barg)", r.loc["P-2", "ridge_mae_increments"] - r.loc["P-2", "persistence_mae_increments"],
             r.loc["P-2", "ridge_rmse_increments"] - r.loc["P-2", "persistence_rmse_increments"],
             r.loc["P-2", "persistence_exact_match"]),
            ("MHC MFC-3 (0.01 ln/min)", r.loc["MFC-3", "ridge_mae_increments"] - r.loc["MFC-3", "persistence_mae_increments"],
             r.loc["MFC-3", "ridge_rmse_increments"] - r.loc["MFC-3", "persistence_rmse_increments"],
             r.loc["MFC-3", "persistence_exact_match"]),
            ("HY2RES buffer (0.1 bar)", q.loc["pres_buf", "ridge_mae_incr"] - q.loc["pres_buf", "persistence_mae_incr"],
             q.loc["pres_buf", "ridge_rmse_incr"] - q.loc["pres_buf", "persistence_rmse_incr"], q.loc["pres_buf", "persistence_exact_rate"]),
            ("HY2RES tank (0.1 bar)", q.loc["pres_comp", "ridge_mae_incr"] - q.loc["pres_comp", "persistence_mae_incr"],
             q.loc["pres_comp", "ridge_rmse_incr"] - q.loc["pres_comp", "persistence_rmse_incr"], q.loc["pres_comp", "persistence_exact_rate"])]
    return pd.DataFrame(rows, columns=["channel", "dmae", "drmse", "exact"])


def plot_integrated_reference_comparison(d, out):
    x = _xstudy(d)
    fig = figure()
    title(fig, "Across studies, Ridge's advantage over persistence is a fraction of one recorded step")
    axs = fig.subplots(1, 2, sharey=True)
    y = np.arange(len(x))
    for ax, col, lab in [(axs[0], "dmae", "ΔMAE, Ridge − persistence"), (axs[1], "drmse", "ΔRMSE, Ridge − persistence")]:
        ax.barh(y, x[col], color=[C["burgundy"] if v > 0 else C["teal"] for v in x[col]], height=0.5, zorder=3,
                hatch=None if col == "dmae" else "//", edgecolor=C["white"])
        ax.axvline(0, color=C["text"], lw=0.8)
        ax.set_xlabel(f"{lab}\n(recording increments; positive favours persistence)")
        xgrid(ax)
    axs[0].set_yticks(y, x.channel)
    axs[0].invert_yaxis()
    cap = ("Pooled held-out differences between the frozen Ridge and persistence references, divided by each channel's "
           "observed recording increment so the studies can be read on one dimensionless scale (values are not pooled). "
           + "; ".join(f"{r.channel}: ΔMAE {r.dmae:+.3f}, ΔRMSE {r.drmse:+.3f}" for r in x.itertuples())
           + ". Ridge is worse on MAE except for HY2RES tank pressure and better on RMSE by small amounts; MHC per-run "
           "values are in Q1_B05/B06.")
    return finish(fig, meta("Q1_I02", "integrated_reference_comparison", "plot_integrated_reference_comparison",
                            "Cross-study reference comparison",
                            "Is the learned reference better than persistence when errors are expressed on the recording grid?",
                            ["study_b/evidence_enhancement/results/analysis/resolution.csv",
                             "hy2res .../evidence_enhancement/results/analysis/quantization_comparison.csv"], cap), out)


def plot_integrated_exact_hits(d, out):
    x = _xstudy(d)
    fig = figure()
    title(fig, "Recorded signals are mostly unchanged step to step, so persistence is often exact")
    ax = fig.add_subplot()
    y = np.arange(len(x))
    ax.barh(y, x.exact, color=C["navy"], height=0.45, zorder=3, label=MODEL["persistence"]["label"])
    ax.scatter(np.zeros(len(x)), y, marker="s", s=60, color=C["ochre"], edgecolor=C["text"], zorder=4, label="Ridge (continuous output)")
    for i, v in enumerate(x.exact):
        ax.text(v + 0.01, i, f"{v:.3f}", va="center", fontsize=10)
    ax.set_yticks(y, x.channel)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("Share of held-out rows predicted exactly (on the recording grid)")
    xgrid(ax)
    fig.legend(loc="outside lower center", ncol=2)
    cap = ("Exact-hit share of the persistence reference on the held-out rows of each channel (MHC: 15,885 rows per channel; "
           "HY2RES: 43,168 rows). Ridge never predicts a recorded value exactly. Because most recorded values repeat, MAE "
           "rewards persistence, while RMSE is decided by the few rows with recorded changes. This is a property of the "
           "recording grid, not of instrument accuracy.")
    return finish(fig, meta("Q1_I03", "integrated_exact_hits", "plot_integrated_exact_hits", "Measurement-grid limitation",
                            "Why do MAE and RMSE disagree across the experimental and operational studies?",
                            ["study_b/.../analysis/resolution.csv", "hy2res .../analysis/quantization_comparison.csv"], cap), out)


def plot_integrated_mechanism_recognition(d, out):
    c = d["c07"]
    rows = [("Frozen library\n(own template present)", c.iloc[0]), ("Own template excluded", c.iloc[1]),
            ("Own excluded +\nindependent replicate", c.iloc[2])]
    fig = figure()
    title(fig, "Mechanism recognition depends on self-templates and near-duplicates")
    ax = fig.add_subplot()
    for i, (lab, r) in enumerate(rows):
        n = int(str(r.evaluated).split()[0])
        agree = int(str(r.agreement).split("/")[0])
        sup = int(r.supported)
        uns = int(r.unsupported)
        parts = [(agree, "Agrees with configured mechanism", C["teal"], None),
                 (sup - agree, "Disagrees", C["burgundy"], "xx"), (uns, "Unsupported (own mechanism absent)", C["white"], "////")]
        left = 0
        for v, name, col, h in parts:
            if v:
                ax.barh(i, v, left=left, color=col, hatch=h, edgecolor=C["text"], lw=0.6, height=0.5, zorder=3,
                        label=name if name not in ax.get_legend_handles_labels()[1] else None)
                ax.text(left + v / 2, i, str(v), ha="center", va="center", fontsize=11,
                        bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.2))
                left += v
        assert left == n
    ax.set_yticks(range(3), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 7.2)
    ax.set_xlabel("Controlled Center queries (counts, one simulation family)")
    xgrid(ax)
    fig.legend(loc="outside lower center", ncol=3)
    cap = ("Nearest-mechanism recognition for the 7 controlled Center queries (normalized B3 RMS, all sensors). With the "
           "frozen library every query matches a self (5) or near-duplicate (2) template. Excluding the own template leaves "
           "5 supported queries, of which 3 agree; adding the alternate-profile SID 213 capture as a replicate raises "
           "agreement to 4/5. Counts from one source family, not rates; details in Q1_C07.")
    return finish(fig, meta("Q1_I04", "integrated_mechanism_recognition", "plot_integrated_mechanism_recognition",
                            "Mechanism-recognition potential", "How much of the apparent recognition survives independent templates?",
                            ["03_results/validation/center_evidence_enhancement/tables/TAB_C07.csv"], cap,
                            lim="Seven queries from one controlled simulation family; not a classification accuracy."), out)


def plot_integrated_r2_confusion(d, out):
    cf = d["conf"]
    fig = figure()
    title(fig, "Registered R2 classification: errors concentrate in two topologies")
    axs = fig.subplots(1, 3)
    for ax, t in zip(axs, ["Center", "Downstream", "Upstream"]):
        m = cf[cf.scope == t].pivot(index="true_class", columns="predicted_class", values="n").loc[CLS, CLS]
        v = m.to_numpy(float)
        rown = v / np.maximum(v.sum(1, keepdims=True), 1)
        from matplotlib.colors import to_rgb
        from matplotlib.patches import Rectangle
        nv, wh = np.array(to_rgb(C["navy"])), np.array(to_rgb(C["white"]))
        for i in range(4):
            for j in range(4):
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=tuple(wh + (nv - wh) * rown[i, j]),
                                       edgecolor=C["grid"], lw=0.6))
        ax.set_xlim(-0.5, 3.5)
        ax.set_ylim(3.5, -0.5)
        ax.set_aspect("equal")
        for i in range(4):
            for j in range(4):
                if v[i, j]:
                    ax.text(j, i, f"{int(v[i, j]):,}", ha="center", va="center", fontsize=9.5,
                            color=C["white"] if rown[i, j] > 0.55 else C["text"])
        ax.set_xticks(range(4), [SHORT[c] for c in CLS], rotation=35, ha="right")
        ax.set_yticks(range(4), [SHORT[c] for c in CLS] if t == "Center" else [""] * 4)
        ax.set_title(f"{t} held out ({int(v.sum()):,} windows)", fontsize=12)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
    axs[0].set_ylabel("True class")
    axs[1].set_xlabel("Predicted class")
    c = cf[cf.scope == "Center"].set_index(["true_class", "predicted_class"]).n
    dn = cf[cf.scope == "Downstream"].set_index(["true_class", "predicted_class"]).n
    cap = (f"Window-count confusion matrices of the registered R2 classifier per held-out topology (shading: row share). "
           f"Center LEAK → NORMAL ({int(c[('LEAK', 'NORMAL')]):,} windows) and Downstream NORMAL → LEAK "
           f"({int(dn[('NORMAL', 'LEAK')]):,}) are the dominant errors; both trace to the source-folder attribution defect "
           "(D1 pending). Upstream is error-free. Windows are serially dependent; independent units are scenario families "
           "and ancestors (Q1_I06).")
    return finish(fig, meta("Q1_I05", "integrated_r2_confusion", "plot_integrated_r2_confusion",
                            "R2 classification by topology", "Where does the registered classifier err?",
                            ["03_results/primary_protocol/PRIMARY/confusion_matrix.csv"], cap,
                            lim="Simulated topologies; inspected outer test; counts of dependent windows."), out)


def plot_integrated_independence_units(d, out):
    u = d["iu"].set_index("y_true").loc[CLS]
    fig = figure()
    title(fig, "Thousands of windows, but few independent scenario templates per class")
    ax = fig.add_subplot()
    lv = [("windows", "Windows", C["slate"], None), ("runs", "Runs", C["blue"], "//"), ("families", "Scenario families", C["teal"], None),
          ("ancestors", "Scenario ancestors (templates)", C["burgundy"], "xx")]
    for j, (col, lab, c, h) in enumerate(lv):
        ax.bar(np.arange(4) + (j - 1.5) * 0.2, u[col], width=0.19, color=c, hatch=h, edgecolor=C["white"], zorder=3, label=lab)
        for i, v in enumerate(u[col]):
            ax.text(i + (j - 1.5) * 0.2, v * 1.12, f"{int(v):,}", ha="center", fontsize=8.5)
    ax.set_yscale("log")
    ax.set_ylim(0.8, 1e5)
    ax.set_xticks(range(4), [SHORT[c] for c in CLS])
    ax.set_ylabel("Count (logarithmic)")
    ygrid(ax)
    fig.legend(loc="outside lower center", ncol=4)
    cap = (f"Units of the registered R2 dataset per class (all three topologies). {int(u.windows.sum()):,} windows come "
           f"from {int(u.runs.sum())} runs, {int(u.families.sum())} scenario families and only {int(u.ancestors.sum())} scenario "
           "ancestors, because every template is simulated in all three topologies. Compressor delay and normal operation "
           "each rest on one ancestor. Recomputed from the frozen predictions; identical to the forensic independence table.")
    return finish(fig, meta("Q1_I06", "integrated_independence_units", "plot_integrated_independence_units",
                            "Dataset composition and independence", "How many independent units support the classification evidence?",
                            ["h1_validation/analysis/h1_02_independence_units_check.csv",
                             "03_results/diagnostics/forensics/independence_units.csv"], cap), out)


def plot_integrated_dy_qualification(d, out):
    reqs = ["Qualified observation bounds", "Qualified model bounds", "Hypothesis library with adapters",
            "Independent event labels", "Event locations", "Formal D(Y) decision"]
    st = {"Center": ["hypothetical", "hypothetical", "partial (6 of 9)", "controlled", "configured", "conditional"],
          "R2 / H2-SimNet": ["absent", "absent", "absent", "disputed (D1)", "absent", "not applicable"],
          "MHC": ["absent", "absent", "absent", "absent", "absent", "blocked"],
          "HY2RES": ["absent", "absent", "absent", "absent", "absent", "blocked"]}
    sty = {"hypothetical": ("D", C["ochre"]), "partial (6 of 9)": ("D", C["ochre"]), "controlled": ("o", C["teal"]),
           "configured": ("o", C["teal"]), "conditional": ("D", C["ochre"]), "absent": ("X", C["burgundy"]),
           "disputed (D1)": ("^", C["ochre"]), "not applicable": ("s", C["slate"]), "blocked": ("X", C["burgundy"])}
    fig = figure()
    title(fig, "Formal D(Y) requires inputs that only the controlled study partly provides")
    ax = fig.add_subplot()
    for j, (s, vals) in enumerate(st.items()):
        for i, v in enumerate(vals):
            m, c = sty[v]
            ax.scatter(j, i, marker=m, s=120, color=c, edgecolor=C["text"], lw=0.6, zorder=3)
            ax.text(j + 0.12, i, v, va="center", fontsize=9.5)
    ax.set_xticks(range(4), list(st))
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(reqs)), reqs)
    ax.set_xlim(-0.4, 3.9)
    ax.set_ylim(len(reqs) - 0.5, -0.6)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    for j in range(4):
        ax.axvline(j, color=C["grid"], lw=0.8, zorder=1)
    hs = [Line2D([], [], marker="o", ls="", color=C["teal"], ms=9, label="Available"),
          Line2D([], [], marker="D", ls="", color=C["ochre"], ms=8, label="Hypothetical / partial / conditional"),
          Line2D([], [], marker="X", ls="", color=C["burgundy"], ms=9, label="Absent or blocked")]
    fig.legend(handles=hs, loc="outside lower center", ncol=3)
    cap = ("Inputs required by the formal set-membership decision D(Y) = (H_consistent, H_excluded, H_indeterminate), per "
           "evidence source. Only Center provides configured events and locations, and its bounds are declared hypothetically "
           "(conditional hypothetical bounds — not calibrated uncertainty); three of nine declared Center hypotheses have no "
           "adapter. R2 used the empirical D(x), not D(Y). MHC and HY2RES have no event labels or locations, so D(Y) is "
           "blocked by evidence (TAB_B08, TAB_H09).")
    return finish(fig, meta("Q1_I07", "integrated_dy_qualification", "plot_integrated_dy_qualification",
                            "Formal D(Y) qualification across studies", "Where can formal D(Y) be evaluated at all?",
                            ["center TAB_C08", "study_b TAB_B08", "hy2res TAB_H09"], cap,
                            ver="qualitative status taken from the accepted claim tables"), out)


def plot_integrated_rq3_outcomes(d, out):
    r = d["rq2"]
    r = r[(r.variant == "primary") & np.isclose(r.target, 0.6)].set_index("class").loc[CLS]
    fig = figure()
    title(fig, "Registered three-outcome policy: decision shares by class (RQ3)")
    ax = fig.add_subplot()
    parts = [("specific", "SPECIFIC", DECISION["SPECIFIC"]), ("ambiguity_set", "AMBIGUITY SET", DECISION["AMBIGUOUS"]),
             ("unresolved", "UNRESOLVED", DECISION["UNRESOLVED"])]
    for i, (cl, row) in enumerate(r.iterrows()):
        left = 0
        for col, lab, s in parts:
            v = row[col]
            if v > 0:
                ax.barh(i, v, left=left, color=s["color"], hatch=s["hatch"], edgecolor=C["white"], height=0.55, zorder=3,
                        label=lab if lab not in ax.get_legend_handles_labels()[1] else None)
                if v > 0.06:
                    ax.text(left + v / 2, i, f"{v:.2f}", ha="center", va="center", fontsize=10,
                            bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.2))
                left += v
    ax.set_yticks(range(4), [f"{SHORT[c]}\n({int(r.loc[c, 'n']):,} windows, {int(r.loc[c, 'n_families'])} families)" for c in CLS])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of the class's windows (Downstream and Upstream held out; target 0.60)")
    xgrid(ax)
    fig.legend(loc="outside lower center", ncol=3)
    cap = ("Registered RQ3 outcome shares of the s_C policy at rank-matched coverage 0.60, pooled over the two outer folds "
           "where 0.60 is attainable (Center absent). Every SPECIFIC decision is correct (0 of 11,198 wrong) and all 31 "
           "ambiguity sets (size 2) contain the true class; compressor-fault windows are never decided because the support "
           "flags block them. LEAK is reported as 'restricted', the other classes as descriptive only (registered rule).")
    return finish(fig, meta("Q1_I08", "integrated_rq3_outcomes", "plot_integrated_rq3_outcomes", "Three-outcome decision shares",
                            "Does the policy produce specific, ambiguous and unresolved outcomes in a class-interpretable way?",
                            ["03_results/primary_protocol/PRIMARY/rq2.csv", "h1_validation/analysis/h1_06_three_outcome_validity_r2.csv"],
                            cap, lim="Two topologies, one or two families per thin class; inspected outer test."), out)


def plot_integrated_capability_matrix(d, out):
    caps = ["Source / data qualification", "Causal reference prediction", "Recording-grid interpretation",
            "Operating-support validity", "Mechanism recognition", "Categorical location ranking",
            "Formal D(Y) decisions", "Three-outcome policy", "H1: incremental decision value",
            "Fault classification / diagnosis", "Localization accuracy", "Industrial / field transfer"]
    S = {  # level codes: V verified, D descriptive, C conditional, X exploratory, N not estimable, B blocked, - not applicable
        "Center": ["V", "-", "-", "-", "D", "D", "C", "C", "-", "B", "B", "B"],
        "R2 / H2-SimNet": ["D", "-", "-", "D", "-", "-", "-", "D", "N", "B", "B", "B"],
        "MHC": ["V", "V", "V", "-", "-", "-", "B", "-", "-", "B", "B", "B"],
        "HY2RES": ["V", "V", "V", "D", "-", "-", "B", "D", "-", "B", "B", "B"]}
    lev = {"V": ("Verified / validated within scope", "o", C["teal"]), "D": ("Descriptively supported", "o", C["blue"]),
           "C": ("Conditionally demonstrated", "D", C["ochre"]), "N": ("Not estimable (registered)", "X", C["burgundy"]),
           "B": ("Blocked by evidence", "s", C["slate"]), "-": None}
    fig = figure(h=6.2)
    title(fig, "What the integrated evidence establishes")
    ax = fig.add_subplot()
    for j, (s, v) in enumerate(S.items()):
        for i, code in enumerate(v):
            if lev[code]:
                _, m, c = lev[code]
                ax.scatter(j, i, marker=m, s=110, color=c, edgecolor=C["text"], lw=0.5, zorder=3)
            else:
                ax.text(j, i, "–", ha="center", va="center", color=C["slate"], fontsize=11)
    ax.set_xticks(range(4), list(S))
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(caps)), caps)
    ax.set_ylim(len(caps) - 0.5, -0.7)
    ax.set_xlim(-0.5, 3.5)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    for j in range(4):
        ax.axvline(j, color=C["grid"], lw=0.8, zorder=1)
    hs = [Line2D([], [], marker=m, ls="", color=c, ms=8, label=lab) for lab, m, c in [x for k, x in lev.items() if x]]
    fig.legend(handles=hs, loc="outside right center", fontsize=9.5)
    cap = ("Claim-to-evidence qualification per capability (rows) and evidence source (columns), in the project vocabulary; "
           "'–' = not addressed by that source. Every cell is traced in T10. Fault classification, localization accuracy "
           "and industrial transfer are blocked everywhere; H1 is not estimable under the registered protocol.")
    return finish(fig, meta("Q1_I09", "integrated_capability_matrix", "plot_integrated_capability_matrix",
                            "Claim-to-evidence qualification", "Which capabilities are established, and by which evidence?",
                            ["publication_q1/tables/T10_claim_evidence.csv"], cap,
                            ver="codes mirror T10, which cites each source"), out)


FIGURES = [plot_integrated_evidence_architecture, plot_integrated_reference_comparison, plot_integrated_exact_hits,
           plot_integrated_mechanism_recognition, plot_integrated_r2_confusion, plot_integrated_independence_units,
           plot_integrated_dy_qualification, plot_integrated_rq3_outcomes, plot_integrated_capability_matrix]
