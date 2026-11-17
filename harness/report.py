#!/usr/bin/env python3
"""Build results/leaderboard.md from results/*.json, one section per synthesis tool."""
import json, glob, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "results", "*.json"))):
    r = json.load(open(f))
    rows.append((r["candidate"], r["status"], r, r.get("points", {}).get("area")))
def pct(v, b): return f"{(v / b - 1) * 100:+.0f}%"
out = []
SECTIONS = [("Yosys 0.71 (current release; Booth multiplier mapping enabled for the baselines)", lambda n: "yosys071" in n and n[0] != "x"),
            ("Yosys 0.33 (Ubuntu 24.04 package; no Booth option)", lambda n: "yosys071" not in n and n[0] != "x")]
for title, sel in SECTIONS:
    sec = [x for x in rows if sel(x[0])]
    if not sec: continue
    out += [f"### {title}", "",
            "| Design | Verdict | Cells | Area (um2) | Min period (ns) | Fmax (MHz) | Power @100 MHz (mW) | Energy/op (pJ) |",
            "|---|---|---|---|---|---|---|---|"]
    for n, s, r, p in sec:
        if s != "PASS" or not p:
            out.append(f"| {n} | {s} | | | | | | |"); continue
        sy, st = p["synth"], p["sta"]
        out.append(f"| {n} | PASS | {sy['cells']} | {sy['area_um2']:.0f} | {st['min_period_ns']:.2f} | "
                   f"{1000 / st['min_period_ns']:.0f} | {st['power_mw']:.2f} | {p['energy_per_op_pj']:.1f} |")
    out.append("")
    base = [(n, p) for n, s, r, p in sec if n.startswith("b") and s == "PASS" and p]
    if base:
        bn, bp = min(base, key=lambda x: x[1]["synth"]["area_um2"])       # strongest baseline in this section
        out += [f"Relative to the strongest baseline here, `{bn}`:", ""]
        for n, s, r, p in sec:
            if s == "PASS" and p and n.startswith("c"):
                out.append(f"- {n}: {pct(p['synth']['area_um2'], bp['synth']['area_um2'])} area, "
                           f"{pct(p['sta']['min_period_ns'], bp['sta']['min_period_ns'])} delay, "
                           f"{pct(p['sta']['power_mw'], bp['sta']['power_mw'])} power")
        out.append("")
ctl = [x for x in rows if x[0][0] == "x"]
if ctl:
    out += ["### Negative controls (deliberately broken designs)", "", "| Design | Verdict | RTL sim mismatches | Formal N=1 |", "|---|---|---|---|"]
    for n, s, r, p in ctl:
        st = r["stages"]; f = st.get("formal") or []
        out.append(f"| {n} | {s} | {st.get('rtl_sim', {}).get('errors', '-')} of {st.get('rtl_sim', {}).get('checked', '-')} | "
                   f"{'not reached' if not f else ('proved' if f[0]['proved'] else 'counterexample found')} |")
    out.append("")
open(os.path.join(ROOT, "results", "leaderboard.md"), "w").write("\n".join(out))
print("\n".join(out))
