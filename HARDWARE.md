# Hardware assessment for the chip-design bid

Scope: what each machine you own can do for an "agent designs a video-generation accelerator block" programme.
Specs marked (web) were checked on 16 Nov 2026; the rest comes from what you have told me.

## Summary

| Machine | Role in this project | Fit |
|---|---|---|
| Tenstorrent Blackhole p150 | Target and reference silicon: profile real video-generation kernels on an open RISC-V AI chip | Strong, and the most distinctive asset |
| Threadripper Pro + 3x RTX 3090 | Agent model host and video-model tracing on a current software stack | Strong |
| Minisforum MS-01 | Always-on EDA runner and orchestrator | Good |
| V100 SXM2 | Batch workers on a frozen software stack | Marginal |
| Missing: FPGA board | Run generated blocks on real hardware | Gap, about £100-250 |
| Missing: place-and-route | Post-layout numbers | Gap, software only |

## Tenstorrent Blackhole p150 (you wrote "b150"; I assume the Blackhole p150)

- (web) 32 GB GDDR6, 16 SiFive X280 "big" RISC-V cores, up to 300 W. Tensix core count was cut from 140 to 120
  by a February 2026 firmware update.
- (web) Tenstorrent's own video demos: Wan 2.2 14B needs four Blackhole chips (QuietBox 2, about six minutes per
  5-second clip). On one card the documented path is AnimateDiff on Stable Diffusion 1.4, about 7.7 s per frame.
- Why it matters here:
  1. It is the measurement target. Run a video pipeline on it, record which operations dominate, and pick the next
     block from data instead of from my guess (3D convolution).
  2. The software stack is open down to the kernels that run on the on-chip RISC-V cores, so an agent can change
     kernel and hardware block together. A GPU does not allow that.
  3. Its block-floating-point 8-bit format has an integer mantissa datapath. The `dot_s8` block in this repo is that
     datapath for a 3x3x3 convolution window. Treat this mapping as my reading of the format; confirm against tt-metal.
  4. For a European jury it is a credible "we measure against real open AI silicon" story.
- Limits: one card cannot run the 14B video model; Blackhole software is still under active development.

## Threadripper Pro 3945WX, 512 GB RAM, 3x RTX 3090

- Best host for the agent model (72 GB VRAM) and for tracing a current video model (Wan 2.2 5B class) with
  current PyTorch to capture real int8 activation statistics. That replaces the synthetic stimulus used here.
- 512 GB RAM is what large formal and place-and-route jobs need. The multi-tap equivalence proof that timed out
  on the 2-core cloud box used for this run belongs here.
- 12 cores is the limit: synthesis of one candidate is single-threaded, so throughput is about 12 candidates at once.

## Minisforum MS-01 (assumed; say if you meant the MS-S1 Max)

- (web) PCIe 4.0 x16 slot wired x8, half-height single-slot cards only; three M.2 slots; 10 GbE.
- Role: always-on harness runner. The whole flow here is CPU-bound and mostly single-threaded per job, so the
  mobile i9 runs many candidates in parallel. This run took about 10-30 minutes per candidate on 2 cloud cores;
  my estimate is a few minutes each there with native Yosys (not measured).
- It cannot house the p150 or a 3090 internally (300 W, dual-slot). A riser and an external PSU might work on the
  x8 slot, but I have not verified that.
- If you meant the MS-S1 Max (Ryzen AI Max+ 395, up to 128 GB unified memory, x16 slot wired x4): it would also
  host a mid-size agent model, which makes it a self-contained agent-plus-EDA node.

## V100 SXM2

- (web) Volta is on NVIDIA's legacy 580 driver branch; 590 and later ignore the card. PyTorch 2.14 is the last
  release with prebuilt wheels that support it (CUDA 12.6); from 2.15 it is build-from-source only.
- Useful as extra llama.cpp agent workers or for pinned-version tracing jobs. Not a platform to build on, and SXM2
  cards need carrier boards and cooling. Do not put it in the proposal as a capability.

## Gaps

1. FPGA board. A generated block that runs on an FPGA next to the Blackhole card is a far stronger demo than
   synthesis numbers. A low-cost Lattice ECP5 board is supported by the same open toolchain.
2. Place-and-route. OpenROAD would not install in the cloud box (prebuilt download blocked, source build too heavy).
   On the MS-01 it gives post-layout area, timing and power, which is what a chip jury expects.
3. Tape-out path. IHP has run free open-source shuttle runs on SG13G2, the process used here. Check the current
   schedule; a tiny fabricated block would answer the "no silicon track record" objection directly.
4. People. None of the above replaces a physical-design partner.
