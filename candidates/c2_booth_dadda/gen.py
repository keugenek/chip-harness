#!/usr/bin/env python3
"""C2: radix-4 Booth recoding of the weights (4 partial products per tap instead of 8),
all taps merged into one Dadda tree."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from tree import *; from booth import *
n = int(sys.argv[1]); yw = 16 + clog2(n)
net = Net(); cols = {}; K = 0
for t in range(n):
    digs = []
    for (one, two, neg) in encode_exprs(lambda j: f"w_q[{t*8+j}]"):
        digs.append((net.wire(one, "one"), net.wire(two, "two"), neg))
    K += tap_bits(net, cols, lambda b: f"a_q[{t*8+b}]", digs)
add_const(cols, K % (1 << yw), yw)
print(finish(net, cols, n, yw, n * 8, "  assign w_d = w;", "C2 radix-4 Booth + merged Dadda tree"))
