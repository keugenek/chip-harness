// Self-checking testbench shared by RTL and gate-level runs.
// Contract: dot_s8 has latency exactly 2 clock edges (input register + output register).
`timescale 1ns/1ps
module tb;
  parameter N = 27;
  parameter YW = 21;
  parameter NVEC = 8192;   // capacity; actual count comes from +nvec=
  parameter real HALF = 5.0;
  reg clk = 0, rst_n = 0;
  reg  [N*8-1:0] a, w;
  wire [YW-1:0] y;
  reg [N*8-1:0] va [0:NVEC-1];
  reg [N*8-1:0] vw [0:NVEC-1];
  reg [YW-1:0]  vy [0:NVEC-1];
  integer i, errors, nvec;
  dot_s8
`ifdef DUT_PARAM
    #(.N(N))
`endif
    dut (.clk(clk), .rst_n(rst_n), .a(a), .w(w), .y(y));
  always #(HALF) clk = ~clk;
  initial begin
    $readmemh("vec_a.hex", va); $readmemh("vec_w.hex", vw); $readmemh("vec_y.hex", vy);
    errors = 0; a = 0; w = 0;
    if (!$value$plusargs("nvec=%d", nvec)) nvec = NVEC;
    if ($test$plusargs("dump")) begin $dumpfile("dump.vcd"); $dumpvars(0, tb.dut); end
    repeat (3) @(negedge clk); rst_n = 1;
    for (i = 0; i < nvec + 2; i = i + 1) begin
      @(negedge clk);
      if (i >= 2 && y !== vy[i-2]) begin
        errors = errors + 1;
        if (errors <= 5) $display("MISMATCH vec %0d: got %h exp %h", i-2, y, vy[i-2]);
      end
      if (i < nvec) begin a = va[i]; w = vw[i]; end
    end
    $display("RESULT checked=%0d errors=%0d", nvec, errors);
    $finish;
  end
endmodule
