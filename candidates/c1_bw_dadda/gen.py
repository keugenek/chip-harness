#!/usr/bin/env python3
"""C1: Baugh-Wooley partial products for all taps merged into ONE Dadda tree, one final adder.
Removes the 27 separate multiplier carry chains and the sign-extension waste of the baselines."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from tree import *
n = int(sys.argv[1]); yw = 16 + clog2(n)
net = Net(); cols = {}; K = 0
for t in range(n):
    for i in range(8):
        for j in range(8):
            ai, wj = f"a_q[{t*8+i}]", f"w_q[{t*8+j}]"
            neg = (i == 7) != (j == 7)                       # exactly one sign bit -> negative weight
            nm = net.wire(f"~({ai} & {wj})" if neg else f"{ai} & {wj}", "pp")
            cols.setdefault(i + j, []).append((nm, 1))
    K += (1 << 8) - (1 << 15)                                # per-tap Baugh-Wooley correction
add_const(cols, K % (1 << yw), yw)
print(finish(net, cols, n, yw, n * 8, "  assign w_d = w;", "C1 Baugh-Wooley + merged Dadda tree"))
