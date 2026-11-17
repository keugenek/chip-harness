#!/usr/bin/env python3
"""Golden model + stimulus for dot_s8: y = sum_i a[i]*w[i], signed 8-bit operands.

Stimulus modes
  corner : extremes that break sign handling
  uniform: uniform random int8 on both operands
  conv   : conv-like activity -- weights held for 256 samples, activations ~N(0,20) clipped
           (synthetic stand-in for a quantised video-VAE conv layer; NOT a real model trace)
"""
import random, sys, math

def clog2(n): return (n - 1).bit_length()
def ywidth(n): return 16 + clog2(n)
def dot(a, w): return sum(x * y for x, y in zip(a, w))

def gen(n, mode, count, seed):
    r = random.Random(seed)
    out = []
    if mode == "corner":
        ext = [-128, 127, -1, 0, 1]
        for x in ext:
            for y in ext:
                out.append(([x] * n, [y] * n))
        for _ in range(count):
            out.append(([r.choice(ext) for _ in range(n)], [r.choice(ext) for _ in range(n)]))
        for i in range(n):  # one-hot taps: catches tap wiring / ordering bugs
            a = [0] * n; w = [0] * n; a[i] = -128; w[i] = -128; out.append((a, w))
            a = [0] * n; w = [0] * n; a[i] = 127; w[i] = -128; out.append((a, w))
            a = [0] * n; w = [0] * n; a[i] = r.randint(-128, 127); w[i] = r.randint(-128, 127); out.append((a, w))
    elif mode == "uniform":
        for _ in range(count):
            out.append(([r.randint(-128, 127) for _ in range(n)], [r.randint(-128, 127) for _ in range(n)]))
    elif mode == "conv":
        w = None
        for k in range(count):
            if k % 256 == 0:
                w = [max(-128, min(127, round(r.gauss(0, 40)))) for _ in range(n)]
            a = [max(-128, min(127, round(r.gauss(0, 20)))) for _ in range(n)]
            out.append((a, list(w)))
    else:
        raise SystemExit("bad mode")
    return out

def pack(v):  # element 0 in the low byte
    return "".join("%02x" % (x & 0xFF) for x in reversed(v))

def write(n, vecs, prefix):
    yw = ywidth(n)
    with open(prefix + "_a.hex", "w") as fa, open(prefix + "_w.hex", "w") as fw, open(prefix + "_y.hex", "w") as fy:
        for a, w in vecs:
            fa.write(pack(a) + "\n"); fw.write(pack(w) + "\n")
            fy.write("%x\n" % (dot(a, w) & ((1 << yw) - 1)))
    return len(vecs)

if __name__ == "__main__":
    n = int(sys.argv[1]); mode = sys.argv[2]; count = int(sys.argv[3]); seed = int(sys.argv[4]); prefix = sys.argv[5]
    print(write(n, gen(n, mode, count, seed), prefix))
