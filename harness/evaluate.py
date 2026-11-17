#!/usr/bin/env python3
"""Validator harness: one candidate in, one JSON verdict out.

Stages (a candidate is rejected at the first failing gate):
  1 lint      verilator --lint-only -Wall
  2 rtl_sim   self-checking sim vs python golden model (corner + uniform + conv stimulus)
  3 formal    SAT equivalence vs reference model at reduced tap counts (temporal induction)
  4 synth     yosys -> IHP SG13G2 standard cells (abc, per timing target)
  5 gate_sim  mapped netlist + foundry cell models vs the same vectors; dumps switching activity
  6 sta       OpenSTA: critical path, and power from the gate-level activity

Candidate contract: directory with design.v (module dot_s8, parameter N) or gen.py
(`python3 gen.py N` prints Verilog for module dot_s8 with N taps).
Ports: clk, rst_n, a[N*8-1:0], w[N*8-1:0], y[16+clog2(N)-1:0]. Latency exactly 2.
"""
import argparse, json, os, re, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import golden

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(ROOT, "harness")
LIB = os.path.join(ROOT, "pdk", "sg13g2_stdcell_typ_1p20V_25C.lib")
CELLS = os.path.join(ROOT, "pdk", "sg13g2_func.v")   # generated from the Liberty file by lib2v.py
STA = os.environ.get("OPENSTA") or shutil.which("sta") or "/home/claude/ext/OpenSTA/build/sta"
YOSYS_SYN = os.environ.get("YOSYS_SYN", "yosys")          # synthesis binary (formal always uses system yosys)
SYNTH_FLAGS = os.environ.get("SYNTH_FLAGS", "")           # e.g. -booth on newer Yosys
TAG = os.environ.get("RESULT_TAG", "")

def run(cmd, cwd, timeout=1800, log=None):
    t = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout)
        out, rc = p.stdout + p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        out, rc = (e.stdout or b"").decode(errors="ignore") + "\nTIMEOUT", 124
    if log:
        open(os.path.join(cwd, log), "w").write(out)
    return rc, out, round(time.time() - t, 1)

def emit_design(cand, n, dst):
    """Return (path, is_parameterised)."""
    g = os.path.join(cand, "gen.py")
    if os.path.exists(g):
        rc, out, _ = run([sys.executable, g, str(n)], cand)
        if rc != 0:
            raise RuntimeError("gen.py failed: " + out[-400:])
        open(dst, "w").write(out)
        return dst, False
    shutil.copy(os.path.join(cand, "design.v"), dst)
    return dst, True

def vectors(n, wd, sets):
    vecs = []
    for mode, count, seed in sets:
        vecs += golden.gen(n, mode, count, seed)
    return golden.write(n, vecs, os.path.join(wd, "vec"))

def _verdict(rc, out, nvec, t):
    m = re.search(r"RESULT checked=\s*(\d+) errors=\s*(\d+)", out)
    ok = rc == 0 and m is not None and int(m.group(2)) == 0 and int(m.group(1)) == nvec
    return ok, {"checked": int(m.group(1)) if m else 0, "errors": int(m.group(2)) if m else -1, "sec": t,
                "detail": "" if ok else out[-300:]}

def sim(wd, files, n, nvec, param, tag):
    """RTL simulation with Icarus Verilog."""
    yw = golden.ywidth(n)
    defs = "-DDUT_PARAM " if param else ""
    cmd = (f"iverilog -g2012 {defs}-Ptb.N={n} -Ptb.YW={yw} -o {tag}.vvp {H}/tb.v {' '.join(files)} "
           f"&& vvp -n {tag}.vvp +nvec={nvec}")
    rc, out, t = run(cmd, wd, log=f"{tag}.log")
    return _verdict(rc, out, nvec, t)

def gate_build(wd, netlist, n, tag, half):
    """Compile mapped netlist + Liberty-derived cell models with Verilator (once per netlist)."""
    yw = golden.ywidth(n)
    cmd = (f"verilator --binary --timing --trace --trace-underscore -Wno-fatal -Wno-WIDTH -Wno-PINMISSING "
           f"-Wno-TIMESCALEMOD --top-module tb -GN={n} -GYW={yw} -GHALF={half} -O1 -CFLAGS -O0 "
           f"--Mdir obj_{tag} -o sim {H}/tb.v {netlist} {CELLS}")
    rc, out, t = run(cmd, wd, log=f"{tag}_build.log")
    return rc == 0, t

def gate_run(wd, tag, nvec, dump=False):
    rc, out, t = run(f"./obj_{tag}/sim +nvec={nvec}" + (" +dump" if dump else ""), wd, log=f"{tag}_run.log")
    return _verdict(rc, out, nvec, t)

def formal(cand, wd, n):
    d, param = emit_design(cand, n, os.path.join(wd, f"formal_dut_{n}.v"))
    chp = f"chparam -set N {n} dot_s8;" if param else ""
    ys = f"""
read_verilog {H}/ref.v; chparam -set N {n} dot_s8; hierarchy -top dot_s8; proc; flatten; async2sync; opt_clean; rename dot_s8 gold; design -stash gold
read_verilog {d}; {chp} hierarchy -top dot_s8; proc; flatten; async2sync; opt_clean; rename dot_s8 gate; design -stash gate
design -copy-from gold -as gold gold; design -copy-from gate -as gate gate
miter -equiv -flatten -make_outputs gold gate miter; hierarchy -top miter; opt -full
sat -verify -tempinduct -prove trigger 0 -set-init-zero -seq 1 -maxsteps 8 -timeout 900 miter
"""
    open(os.path.join(wd, f"formal_{n}.ys"), "w").write(ys)
    rc, out, t = run(f"yosys formal_{n}.ys", wd, timeout=1000, log=f"formal_{n}.log")
    proved = rc == 0 and "Induction step proven: SUCCESS!" in out
    return proved, {"taps": n, "proved": proved, "sec": t, "detail": "" if proved else out[-300:]}

def synth(wd, design, param, n, targets):
    """One yosys run: generic synthesis once, then technology mapping per timing target."""
    chp = f"chparam -set N {n} dot_s8;" if param else ""
    ys = f"""
read_verilog {design}; {chp} hierarchy -top dot_s8
synth -top dot_s8 -flatten {SYNTH_FLAGS}
opt -purge
dfflibmap -liberty {LIB}
design -save premap
"""
    for t in targets:
        tgt = "" if t == "area" else f"-D {int(t)}"
        ys += f"""
design -load premap
abc -liberty {LIB} {tgt}
opt_clean -purge
hilomap -hicell sg13g2_tiehi L_HI -locell sg13g2_tielo L_LO
tee -o syn_{t}.stat stat -liberty {LIB}
write_verilog -noattr -noexpr -nohex -nodec syn_{t}.v
"""
    open(os.path.join(wd, "syn.ys"), "w").write(ys)
    rc, out, sec = run(f"{YOSYS_SYN} -q syn.ys", wd, timeout=9000, log="syn.log")
    res = {}
    for t in targets:
        f = os.path.join(wd, f"syn_{t}.stat")
        if rc != 0 or not os.path.exists(f):
            return False, {"detail": out[-400:], "sec": sec}
        st = open(f).read()
        area = float(re.search(r"Chip area for module.*?:\s*([\d.]+)", st).group(1))
        m = re.search(r"Number of cells:\s*(\d+)", st) or re.search(r"^\s*(\d+)\s+\S+\s+cells\s*$", st, re.M)
        cells = int(m.group(1))
        flops = sum(int(x) for x in re.findall(r"sg13g2_(?:s?df\w+)[ \t]+(\d+)", st)) or \
                sum(int(x) for x in re.findall(r"^\s*(\d+)\s+\S+\s+sg13g2_s?df\w+", st, re.M))
        res[t] = {"area_um2": round(area, 1), "cells": cells, "flops": flops, "netlist": f"syn_{t}.v"}
    res["_sec"] = sec
    return True, res

def sta(wd, netlist, tag, period, vcd=None):
    act = f"read_vcd -scope TOP/tb/dut {vcd}" if vcd else "set_power_activity -input -activity 0.2"
    tcl = f"""
read_liberty {LIB}
read_verilog {netlist}
link_design dot_s8
create_clock -name clk -period {period} [get_ports clk]
set_input_delay 0 -clock clk [get_ports {{a* w*}}]
set_output_delay 0 -clock clk [get_ports y*]
set_false_path -from [get_ports rst_n]
puts "WS [sta::worst_slack -max]"
report_checks -path_delay max -format summary
{act}
report_power
"""
    open(os.path.join(wd, tag + ".tcl"), "w").write(tcl)
    rc, out, t = run(f"{STA} -no_init -no_splash -exit {tag}.tcl", wd, log=tag + ".log")
    m = re.search(r"WS (-?[\d.eE+-]+)", out)
    pw = re.search(r"^Total\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", out, re.M)
    if rc != 0 or not m or not pw:
        return False, {"detail": out[-400:]}
    ws = float(m.group(1))
    return True, {"period_ns": period, "worst_slack_ns": round(ws, 3), "min_period_ns": round(period - ws, 3),
                  "power_mw": round(float(pw.group(4)) * 1e3, 4),
                  "power_internal_mw": round(float(pw.group(1)) * 1e3, 4),
                  "power_switching_mw": round(float(pw.group(2)) * 1e3, 4),
                  "power_leakage_mw": round(float(pw.group(3)) * 1e3, 6),
                  "activity": "gate-level VCD (conv stimulus)" if vcd else "default 0.2"}

def evaluate(cand_in, n=27, targets=("area",), period=10.0, keep=True, formal_taps=(1,), stop_after=None):
    cand = os.path.abspath(cand_in)
    name = os.path.basename(cand) + TAG
    wd = os.path.join(ROOT, "work", name)
    shutil.rmtree(wd, ignore_errors=True); os.makedirs(wd)
    R = {"candidate": name, "taps": n, "pdk": "IHP SG13G2 (typ 1.2V 25C)", "synth_tool": YOSYS_SYN + (" " + SYNTH_FLAGS if SYNTH_FLAGS else ""), "stages": {}, "status": "running"}
    def fail(stage):
        R["status"] = "REJECTED@" + stage
        return R
    try:
        design, param = emit_design(cand, n, os.path.join(wd, "design.v"))
    except Exception as e:
        R["stages"]["emit"] = {"detail": str(e)}; return fail("emit")
    R["rtl_lines"] = sum(1 for _ in open(design))
    # 1 lint
    g = f"-GN={n}" if param else ""
    rc, out, t = run(f"verilator --lint-only -Wall -Wno-fatal -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL -Wno-UNUSEDPARAM {g} --top-module dot_s8 {design}", wd, log="lint.log")
    errs = len(re.findall(r"%Error", out)); warns = len(re.findall(r"%Warning", out))
    R["stages"]["lint"] = {"errors": errs, "warnings": warns, "sec": t, "detail": out[-300:] if errs else ""}
    if errs or rc != 0: return fail("lint")
    # 2 rtl sim
    nvec = vectors(n, wd, [("corner", 200, 1), ("uniform", 4000, 2), ("conv", 1024, 3)])
    ok, info = sim(wd, [design], n, nvec, param, "rtl_sim")
    R["stages"]["rtl_sim"] = info
    if not ok: return fail("rtl_sim")
    # 3 formal
    R["stages"]["formal"] = []
    for k in formal_taps:
        ok, info = formal(cand, wd, k)
        R["stages"]["formal"].append(info)
        if not ok: return fail("formal")
    if stop_after == "formal":
        R["status"] = "PASS(pre-synthesis gates only)"; return R
    # 4-6 per synthesis target
    R["points"] = {}
    ok, syn = synth(wd, design, param, n, targets)
    if not ok: R["stages"]["synth"] = syn; return fail("synth")
    R["synth_sec"] = syn["_sec"]
    for tgt in targets:
        P = {"synth": syn[tgt]}; info = syn[tgt]
        net = info["netlist"]
        okb, tb_sec = gate_build(wd, net, n, f"gate_{tgt}", period / 2)
        if not okb: P["gate_sim"] = {"detail": "verilator build failed"}; R["points"][tgt] = P; return fail("gate_sim")
        nvec = vectors(n, wd, [("corner", 200, 1), ("uniform", 4000, 2)])
        ok, info = gate_run(wd, f"gate_{tgt}", nvec); info["build_sec"] = tb_sec; P["gate_sim"] = info
        if not ok: R["points"][tgt] = P; return fail("gate_sim")
        nvec = vectors(n, wd, [("conv", 4096, 7)])
        ok, info = gate_run(wd, f"gate_{tgt}", nvec, dump=True)
        if ok: os.replace(os.path.join(wd, "dump.vcd"), os.path.join(wd, f"act_{tgt}.vcd"))
        ok2, info2 = sta(wd, net, f"sta_{tgt}", period, f"act_{tgt}.vcd" if ok else None); P["sta"] = info2
        if not ok2: R["points"][tgt] = P; return fail("sta")
        P["energy_per_op_pj"] = round(info2["power_mw"] * period, 2)   # mW * ns = pJ
        if not keep and os.path.exists(os.path.join(wd, f"act_{tgt}.vcd")): os.remove(os.path.join(wd, f"act_{tgt}.vcd"))
        R["points"][tgt] = P
    R["status"] = "PASS"
    return R

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate"); ap.add_argument("--taps", type=int, default=27)
    ap.add_argument("--targets", default="area"); ap.add_argument("--period", type=float, default=10.0)
    ap.add_argument("--formal-taps", default="1"); ap.add_argument("--stop-after", default=None)
    a = ap.parse_args()
    r = evaluate(a.candidate, a.taps, tuple(a.targets.split(",")), a.period, keep=False,
                 formal_taps=tuple(int(x) for x in a.formal_taps.split(",")), stop_after=a.stop_after)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    if not a.stop_after: json.dump(r, open(os.path.join(ROOT, "results", r["candidate"] + ".json"), "w"), indent=1)
    print(json.dumps(r, indent=1))
    sys.exit(0 if r["status"] == "PASS" else 1)
