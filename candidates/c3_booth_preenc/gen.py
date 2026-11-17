#!/usr/bin/env python3
"""C3: as C2, but the Booth recoder sits BEFORE the weight register. In a convolution the weights
are quasi-static, so recoding them on the way in takes the encoder off the critical path and
stops it toggling. Costs 4 extra flops per tap; interface and latency are unchanged."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from tree import *; from booth import *
n = int(sys.argv[1]); yw = 16 + clog2(n)
net = Net(); cols = {}; K = 0; enc = []
for t in range(n):
    digs = []
    for k, (one, two, neg) in enumerate(encode_exprs(lambda j: f"w[{t*8+j}]")):
        base = t * 12 + k * 3
        enc.append(f"  assign w_d[{base}] = {one};\n  assign w_d[{base+1}] = {two};\n  assign w_d[{base+2}] = {neg};")
        digs.append((f"w_q[{base}]", f"w_q[{base+1}]", f"w_q[{base+2}]"))
    K += tap_bits(net, cols, lambda b: f"a_q[{t*8+b}]", digs)
add_const(cols, K % (1 << yw), yw)
print(finish(net, cols, n, yw, n * 12, "\n".join(enc), "C3 pre-encoded Booth weights + merged Dadda tree"))
