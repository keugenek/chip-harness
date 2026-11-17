# Task given to the agent: `dot_s8`

**Function.** `y = sum_{i<N} a[i] * w[i]`, signed 8-bit operands, exact (no rounding, no saturation).
N = 27 is the target: one 3x3x3 window of a causal 3D convolution, the inner loop of a video VAE
decoder, with int8 activations and weights. It is also the mantissa datapath of a block-floating-point
(shared exponent, 8-bit mantissa) convolution.

**Interface.** `clk`, `rst_n` (async, active low), `a[N*8-1:0]`, `w[N*8-1:0]` (element 0 in the low byte),
`y[16+clog2(N)-1:0]`. Inputs are registered, output is registered: latency exactly 2 clock edges.
Extra registers are allowed only if latency and interface are unchanged.

**Deliverable.** `design.v` (parameter N) or `gen.py N` that prints Verilog for N taps.

**Gates, in order.** lint -> RTL simulation against the Python golden model -> formal equivalence at N=1
-> synthesis to IHP SG13G2 -> gate-level simulation of the mapped netlist -> static timing and power.
A candidate that fails any gate is rejected with the failing stage and a short reason; it is never scored.

**Score.** Standard-cell area, minimum clock period, power at 100 MHz under conv-like switching activity.
Same synthesis script, same library corner, same stimulus for every design.
