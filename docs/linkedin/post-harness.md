# LinkedIn post: the demo harness

One image: `explainer.png`. Optional second image: `layout.png`.

## Post text

I open-sourced a small demo: a validator harness that lets an AI agent design a chip block and decides,
automatically, whether each design is allowed to count.

The agent writes the circuit. The harness runs six gates, in order, and rejects at the first failure:

1. Lint
2. Simulation against a golden model (5,330 test vectors)
3. Formal equivalence proof
4. Synthesis to an open 130 nm process (IHP SG13G2)
5. Simulation of the synthesised netlist
6. Timing and power

Only a design that passes all six gets a score. One command per candidate, one JSON verdict out.

Three things I learned building it:

- Simulation is not enough. I planted a bug that passed all 5,330 vectors. Only the formal proof caught it.
- The harness needs checking too. It had three bugs of its own, and each one produced a plausible wrong
  number, not a crash.
- Baselines lie. The agent's design looked 34% smaller than hand-written code until I gave the baseline a
  current synthesis tool. The real gain is 10% area and 19% clock period before layout, at 3% more power.

It is a demo, not a product: one 27-tap dot product, about 8,000 cells, one design placed and routed, no
signoff. Everything runs on open tools (Yosys, Verilator, Icarus, OpenSTA, OpenROAD).

Apache 2.0. Code, results and the routed layout: https://github.com/keugenek/chip-harness
