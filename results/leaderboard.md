### Yosys 0.71 (current release; Booth multiplier mapping enabled for the baselines)

| Design | Verdict | Cells | Area (um2) | Min period (ns) | Fmax (MHz) | Power @100 MHz (mW) | Energy/op (pJ) |
|---|---|---|---|---|---|---|---|
| b0_behavioral_yosys071_booth | PASS | 9722 | 121175 | 6.28 | 159 | 6.51 | 65.1 |
| b1_hand_tree_yosys071_booth | PASS | 9722 | 121175 | 6.28 | 159 | 6.51 | 65.1 |
| c1_bw_dadda_yosys071 | PASS | 9781 | 121631 | 5.19 | 193 | 6.73 | 67.3 |
| c2_booth_dadda_yosys071 | PASS | 8978 | 112740 | 5.38 | 186 | 6.10 | 61.0 |
| c3_booth_preenc_yosys071 | PASS | 7707 | 109475 | 5.30 | 189 | 6.71 | 67.1 |
| c4_booth_preenc_prefix_yosys071 | PASS | 7686 | 109379 | 5.07 | 197 | 6.71 | 67.1 |

Relative to the strongest baseline here, `b0_behavioral_yosys071_booth`:

- c1_bw_dadda_yosys071: +0% area, -17% delay, +3% power
- c2_booth_dadda_yosys071: -7% area, -14% delay, -6% power
- c3_booth_preenc_yosys071: -10% area, -16% delay, +3% power
- c4_booth_preenc_prefix_yosys071: -10% area, -19% delay, +3% power

### Yosys 0.33 (Ubuntu 24.04 package; no Booth option)

| Design | Verdict | Cells | Area (um2) | Min period (ns) | Fmax (MHz) | Power @100 MHz (mW) | Energy/op (pJ) |
|---|---|---|---|---|---|---|---|
| b0_behavioral | PASS | 13895 | 165710 | 6.60 | 152 | 8.04 | 80.4 |
| b1_hand_tree | PASS | 13900 | 165790 | 6.57 | 152 | 8.09 | 80.9 |
| c1_bw_dadda | PASS | 9691 | 120995 | 5.24 | 191 | 6.71 | 67.1 |
| c2_booth_dadda | PASS | 8480 | 110561 | 5.53 | 181 | 6.07 | 60.7 |
| c3_booth_preenc | PASS | 7754 | 109191 | 5.21 | 192 | 6.69 | 66.9 |
| c4_booth_preenc_prefix | PASS | 7755 | 109205 | 5.12 | 195 | 6.69 | 66.9 |

Relative to the strongest baseline here, `b0_behavioral`:

- c1_bw_dadda: -27% area, -21% delay, -17% power
- c2_booth_dadda: -33% area, -16% delay, -25% power
- c3_booth_preenc: -34% area, -21% delay, -17% power
- c4_booth_preenc_prefix: -34% area, -22% delay, -17% power

### Negative controls (deliberately broken designs)

| Design | Verdict | RTL sim mismatches | Formal N=1 |
|---|---|---|---|
| x1_rare_value_bug | REJECTED@formal | 0 of 5330 | counterexample found |
| x2_swapped_taps | REJECTED@rtl_sim | 5116 of 5330 | not reached |
