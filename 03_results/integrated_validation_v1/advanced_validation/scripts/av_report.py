"""Assemble ADVANCED_VALIDATION_RESULTS.md (the single authoritative Results narrative) from tables and captions.

Usage (repository root): python 03_results/integrated_validation_v1/advanced_validation/scripts/av_report.py
"""
import re
from pathlib import Path

AV = Path(__file__).resolve().parents[1]

SECTIONS = [
    ("R1. H1 at matched coverage", "Does the evidence policy reduce wrong-specific risk at matched coverage on the frozen R2 predictions?",
     "Frozen R2 predictions (27,993 windows, 17 templates); registered rank-matched selection; fixed grid 0.05–0.25.",
     "Classifier without abstention; conventional confidence abstention; guarded confidence, margin, −entropy, D(x) only; s_C−D.",
     "The registered test remains NOT_ESTIMABLE. Inside the shared region the evidence policy has the lowest point risk, but every "
     "interval for the registered contrast includes 0 and no policy errs outside the disputed runs, so the apparent benefit cannot be "
     "separated from the attribution defect.",
     "Inspected windows; 17 templates; label defect.", ["AV-F01", "AV-F02"], ["A01"]),
    ("R2. Wrong-specific accounting and error attribution", "Which wrong SPECIFIC decisions does each policy make, where, and with what confidence?",
     "Same population; per-class, per-attribution, per-confidence and per-template counts.", "As R1.",
     "Without abstention 28.6 % of windows are wrong and 2,991 errors carry confidence ≥ 0.9. At coverage 0.25 every wrong SPECIFIC "
     "decision of s_C is low-confidence (< 0.9) and lies in a disputed run; the guarded conventional scores add 650 confident errors "
     "from the single undisputed Downstream NORMAL run. At coverage 0.25 the wrong decisions come from 3 templates (s_C, s_C−D), "
     "4 (guarded scores) and 7 (conventional abstention) of 17.",
     "One NORMAL template; inspected data.", ["AV-F03"], ["A02a", "A02b"]),
    ("R3. Negative controls", "Do the policies mistake normal operation or command interventions for leaks?",
     "R2 NORMAL windows (one template); Center pressure-command and timing interventions.", "Classifier without abstention; nearest-mechanism rule.",
     "Conventional abstention keeps 655 false LEAK calls among 680 NORMAL SPECIFIC decisions at 0.25; the evidence policies issue none. "
     "On Center the nearest-mechanism rule routes the timing intervention to withdrawal once its own template is removed; formal D(Y) "
     "issues no withdrawal decision for either intervention.",
     "One NORMAL template; two Center interventions.", ["AV-F11"], ["A11a", "A11b"]),
    ("R4. Formal D(Y): mathematical integrity", "Does the engine respect evidence monotonicity, and are its certificates valid?",
     "2,376 new decisions on the hash-verified Center captures plus the 672 frozen decisions.",
     "Paired runs with frozen bounds: sensor removal, clock widening, bound widening; independent certificate re-verification.",
     "Zero forbidden transitions in 25,024 paired hypothesis checks; all 11,061 exclusion certificates and 1,552 feasibility witnesses "
     "re-verify. The engine is mathematically sound on these inputs.",
     "Mathematical property only; bounds hypothetical.", ["AV-F05"], ["A04a", "A04b"]),
    ("R5. Hypothesis-library completeness", "What happens when the true mechanism or an operating rival is missing?",
     "E4: four libraries × 6 queries × 7 bound scenarios.", "Full declared universe.",
     "The full declared universe never decides (42/42 UNRESOLVED). Removing the true hypothesis converts abstention into wrong SPECIFIC "
     "decisions and ambiguity sets without the truth; removing the normal-operation rival removes the two wrong decisions because they "
     "had selected it. False specificity is unavoidable whenever the truth is absent and one rival stays consistent.",
     "Conditional bounds; six captures.", ["AV-F04"], ["A05"]),
    ("R6. Missing sensors and evidence availability", "Does losing sensors lead to abstention or to false certainty?",
     "E1: 79 predeclared sensor configurations.", "All 13 channels.",
     "It depends on which channels are lost. Losing MFS3 (SID 213 branch meter) turns correct SPECIFIC decisions into ambiguity; losing "
     "pressure sensing (flow only) doubles wrong SPECIFIC decisions (2 → 4 of 24) because pressure is what excludes normal operation "
     "for the flow-blind SID 215 withdrawal. Random removals reduce both correct and wrong SPECIFIC decisions.",
     "Conditional bounds; counts.", ["AV-F08", "AV-F10"], ["A08", "A10"]),
    ("R7. Timing uncertainty", "How do clock uncertainty and observation delay affect formal decisions?",
     "E2 (τ 0–10 s) and E3 (delay 0–10 s, τ = 1 s or τ = delay).", "τ = 1 s, no delay.",
     "Widening τ changes nothing (no new exclusions). A delay of 2 s or more beyond τ removes all correct SPECIFIC decisions in favour "
     "of MODEL_MISMATCH abstention; declaring τ = delay restores them. The two wrong decisions are delay-invariant.",
     "Fixed-step simulation clock; jitter not tested.", ["AV-F09"], ["A09"]),
    ("R8. Pairwise isolability and minimum sensor sets", "Which hypothesis pairs are formally separable with which sensors?",
     "Template-level isolability over admissible shifts; exhaustive search over 8,191 channel subsets.", "All 13 channels.",
     "At REF bounds 14 of 15 pairs are separable with all channels and with flow only; pressure only separates 9. Normal operation vs "
     "the SID 215 withdrawal is never separable at REF bounds. Two channels (MFS1 + MFS3) preserve every separable pair at REF bounds.",
     "Template-level, conditional bounds; not a field sensor design.", ["AV-F07", "AV-F13"], ["A16a", "A16b"]),
    ("R9. Localization", "Which localization level is demonstrated, on how many independent locations?",
     "TAB_C03 rankings; formal decisions of the withdrawal queries.", "Nearest template with and without abstention.",
     "Level 2 (correct categorical outlet) for one outlet (SID 213, two near-duplicate captures). At matched coverage 0.5 neither the "
     "margin-ranked nearest template nor formal D(Y) names a wrong outlet; without abstention the nearest template is wrong for both "
     "unsupported outlets.", "One supported location; H-Loc exploratory.", ["AV-F06"], ["A06a", "A06b", "A07"]),
    ("R10. Leakage and generalization", "Which leakage pathways are confirmed, and how strong is out-of-template generalization?",
     "Forensic attribution, hash audits, template-sharing analysis, train/test gap.", "—",
     "Confirmed: label attribution defect, near-duplicate SID 213 captures, template sharing between every held-out topology and its "
     "training topologies (17/17 templates), source-model sensor signatures in features, self-template matching on Center. Out-of-template "
     "generalization has never been tested.", "Some risks unverifiable (HY2RES training code not tracked).", [], ["A03"]),
    ("R11. Portability and gas transfer", "Is the engine portable across studies and gas compositions?",
     "Import inspection; H2Net v1 property assets; gas-composition interface.", "—",
     "The formal engine has been executed only on Center; MHC and HY2RES use independent code. Pure-H2 property tables exist; no "
     "gas-specific transient model exists, so no diagnostic transfer to pure H2 or blends is demonstrated.",
     "Status assessment.", ["AV-F14", "AV-F15"], ["A12", "A13"]),
    ("R12. Computational performance and cost", "How does runtime scale, and can a cost saving be quantified?",
     "Measured benchmarks (one dimension at a time); parametric cost model.", "—",
     "Formal D(Y) runtime grows roughly proportionally with channels, hypotheses and window length and is insensitive to the shift "
     "count; D(x) grows sub-linearly with the reference size over 1k–20k windows. No monetary saving can be quantified: no sensor "
     "prices are documented.", "One CPU; no prices.", ["AV-F12"], ["A14a", "A14b", "A14c", "A15"]),
    ("R13. Literature and claims", "How does H₂-PRISM relate to published work, and what is established?",
     "Nine verified-DOI studies; claim matrix.", "Published methods (contextual only).",
     "No published result passes the comparability gate; all comparisons are contextual. The defensible distinctive element is "
     "auditable, monotone formal evidence qualification that refuses to decide under an incomplete library — demonstrated "
     "conditionally on one simulation family.", "No head-to-head benchmark exists.", ["AV-F16"], ["A17", "A19", "A20"]),
]


def caption(fid):
    f = next((AV / "captions").glob(f"{fid}_*.md"))
    t = f.read_text(encoding="utf-8")
    ttl = t.splitlines()[0].split("— ", 1)[1]
    cap = re.search(r"\*\*Caption\.\*\* (.*?)\n\n", t, re.S).group(1)
    return f"![{fid}](figures/{f.stem}.png)\n\n*{fid} — {ttl}.* {cap} ([caption](captions/{f.name}))\n"


def table(tid):
    return (AV / "tables" / f"{tid}.md").read_text(encoding="utf-8").replace("### ", "#### ")


def main():
    out = ["# H₂-PRISM advanced validation — Results\n",
           "Authoritative Results narrative. Each section: question → evidence → method → numeric result (figure captions and "
           "tables, generated from verified outputs) → comparator → interpretation → limitation. Protocol: "
           "`protocols/AV_PROTOCOL.md`; decisions on scope: `ADVANCED_VALIDATION_EXECUTION_DECISION.md`.\n"]
    for head, q, ev, comp, interp, lim, figs, tabs in SECTIONS:
        out.append(f"## {head}\n\n- **Question.** {q}\n- **Evidence / method.** {ev}\n- **Comparator.** {comp}\n\n**Results.**\n")
        out += [caption(f) for f in figs]
        out += [table(t) for t in tabs]
        out.append(f"**Interpretation.** {interp}\n\n**Limitation.** {lim}\n")
    (AV / "ADVANCED_VALIDATION_RESULTS.md").write_text("\n".join(out), encoding="utf-8", newline="\n")
    print("written")


if __name__ == "__main__":
    main()
