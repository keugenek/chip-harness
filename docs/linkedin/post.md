# LinkedIn post

Two images, in this order: `layout.png` (the routed layout), then `explainer.png` (how it was made).
Both are 4:5 portrait. Sources for every number are in the repository README and `results/`.

## Post text

One evening, open tools only: I let an AI agent design a small chip block for video generation, and built a
six-gate harness to decide what survives.

The block is a 27-tap dot product, one window of the 3D convolution inside a video decoder. The first image is
the real thing after place and route on an open 130 nm process: 7,787 cells, 0.39 m of wire, 58,267 vias,
zero routing violations.

Against a fair hand-written baseline, before layout: 10% less area, 19% shorter clock period, 3% more power.
With an older synthesis tool the area gain looked like 34%. Giving the baseline a current tool erased most of it.

What I trust is the harness, not the agent. It rejected two planted bugs, one of which passed 5,330 test
vectors and was caught only by the formal proof. It also exposed three bugs in itself, each of which produced
a plausible wrong number.

Limits: one small block, the comparison is before layout, no power grid or signoff, synthetic test activity.
Next: route the baseline, use real workload traces, and point the same loop at kernels on real AI hardware.

Code, results and the routed design: https://github.com/keugenek/chip-harness

## How the explainer reads

1. Headline: the agent designed the block, the checks did the work.
2. Diagram: the agent proposes a design; six gates (lint, simulate, prove, synthesise, gate-level simulation,
   timing and power) check it; a rejection goes back with the failing gate and reason; a pass gets scored.
3. The block, and what the checks caught.
4. Results against the baseline, including the power regression.
5. The lesson about the baseline, and the limits.

## Regenerating the images

The images were rendered from the design canvas artboards with headless Chrome at 2x. The layout picture inside
`layout.png` comes from `harness/render.py` run on `results/layout/routed.def.gz` (unpack first).
