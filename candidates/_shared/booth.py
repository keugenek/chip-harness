"""Radix-4 Booth partial products for a signed 8x8 tap. Digit k of w gives (one, two, neg)."""
def encode_exprs(wbit):
    """wbit(j) -> expression for weight bit j (j=-1 is constant 0). Returns list of 4 (one,two,neg) expression triples."""
    out = []
    for k in range(4):
        lo, mid, hi = ("1'b0" if k == 0 else wbit(2 * k - 1)), wbit(2 * k), wbit(2 * k + 1)
        one = f"({lo} ^ {mid})"
        two = f"(({hi} & ~{mid} & ~{lo}) | (~{hi} & {mid} & {lo}))"
        out.append((one, two, hi))
    return out

def tap_bits(net, cols, abit, digits):
    """digits: 4 triples of net names (one,two,neg). Adds bits to cols; returns integer constant to add."""
    K = 0
    for k, (one, two, neg) in enumerate(digits):
        for b in range(9):
            a1 = abit(min(b, 7))                              # sign-extended a
            a2 = abit(b - 1) if b >= 1 else "1'b0"
            x = net.wire(f"(({a1} & {one}) | ({a2} & {two})) ^ {neg}", "bx")
            if b == 8:                                        # sign bit: -x*2^m == ~x*2^m - 2^m
                x = net.wire(f"~{x}", "bn"); K -= 1 << (2 * k + 8)
            cols.setdefault(2 * k + b, []).append((x, 2))
        cols.setdefault(2 * k, []).append((neg, 0))           # +1 completing the two's complement
    return K
