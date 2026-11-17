#!/usr/bin/env python3
"""Place and route a mapped netlist on IHP SG13G2 with OpenROAD (Python wheel: pip install openroad).
Usage: pnr.py <netlist.v> <outdir> <sites_per_row> <rows>
Flow: floorplan -> pin placement -> global/detailed placement -> clock tree -> global route -> detailed route.
Not included: power grid, fill, antenna repair, signoff DRC/LVS."""
import os, sys, time, faulthandler; faulthandler.enable()
from openroad import Tech, Design, odb
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
net, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); sites, rows = int(sys.argv[3]), int(sys.argv[4])
os.makedirs(out, exist_ok=True); os.chdir(out)
P = os.path.join(ROOT, "pdk")
tech = Tech()
tech.readLiberty(f"{P}/sg13g2_stdcell_typ_1p20V_25C.lib")
tech.readLef(f"{P}/lef/sg13g2_tech.lef"); tech.readLef(f"{P}/lef/sg13g2_stdcell.lef")
d = Design(tech); d.readVerilog(net); d.link("dot_s8")
fp = d.getFloorplan(); site = fp.findSite("CoreSite"); u = d.micronToDBU
cw, ch = sites * 0.48, rows * 3.78                       # CoreSite is 0.48 x 3.78 um
fp.initFloorplan(odb.Rect(0, 0, u(cw + 12.48), u(ch + 15.12)), odb.Rect(u(6.24), u(7.56), u(6.24 + cw), u(7.56 + ch)), site)
fp.makeTracks()
def tcl(s):
    t = time.time(); d.evalTclString(s); print(f"[{time.time()-t:6.1f}s] STEP {s.splitlines()[0][:90]}", flush=True)
tcl("set_thread_count 2")
tcl("create_clock -name clk -period 10 [get_ports clk]")
tcl(f"source {P}/lef/orfs/setRC.tcl")
tcl("place_pins -hor_layers Metal3 -ver_layers Metal2")
tcl("global_placement -density 0.65")
tcl("detailed_placement")
tcl("write_def placed.def")
tcl("clock_tree_synthesis -buf_list {sg13g2_buf_2 sg13g2_buf_4 sg13g2_buf_8} -root_buf sg13g2_buf_8 -sink_clustering_enable")
tcl("set_propagated_clock [all_clocks]")
tcl("detailed_placement")
tcl("check_placement -verbose")
tcl("set_routing_layers -signal Metal2-Metal5 -clock Metal2-Metal5")
tcl("global_route -congestion_iterations 50 -verbose")
tcl("estimate_parasitics -global_routing")
tcl("report_worst_slack -max")
tcl("report_power")
tcl("write_def groute.def")
tcl("detailed_route -output_drc drc.rpt -verbose 1")
tcl("write_def routed.def")
tcl("write_db routed.odb")
tcl("report_design_area")
print("DONE", flush=True)
