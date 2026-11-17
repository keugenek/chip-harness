// Baseline B1: careful hand-written structure. One signed 8x8 multiplier per tap,
// products summed in a balanced binary adder tree with minimal bit growth per level.
module dot_s8 #(parameter N = 27, parameter YW = 16 + $clog2(N)) (
  input  wire             clk,
  input  wire             rst_n,
  input  wire [N*8-1:0]   a,
  input  wire [N*8-1:0]   w,
  output reg  [YW-1:0]    y
);
  localparam L  = $clog2(N);
  localparam P2 = 1 << L;
  reg [N*8-1:0] a_q, w_q;
  // node storage: level l has P2>>l nodes, each stored YW bits wide (sign-extended)
  wire signed [YW-1:0] node [0:2*P2-2];
  genvar g, l;
  generate
    for (g = 0; g < P2; g = g + 1) begin : leaf
      if (g < N) begin : m
        wire signed [15:0] p = $signed(a_q[g*8 +: 8]) * $signed(w_q[g*8 +: 8]);
        assign node[g] = p;
      end else begin : z
        assign node[g] = {YW{1'b0}};
      end
    end
    for (l = 0; l < L; l = l + 1) begin : lvl
      for (g = 0; g < (P2 >> (l+1)); g = g + 1) begin : add
        // offset of level l = 2*P2 - 2*(P2>>l) ; level l+1 = 2*P2 - 2*(P2>>(l+1))
        localparam SRC = 2*P2 - 2*(P2 >> l);
        localparam DST = 2*P2 - 2*(P2 >> (l+1));
        localparam WD  = 16 + l + 1;             // width needed at this level
        wire signed [WD-1:0] s = $signed(node[SRC + 2*g][WD-2:0]) + $signed(node[SRC + 2*g + 1][WD-2:0]);
        assign node[DST + g] = s;
      end
    end
  endgenerate
  always @(posedge clk or negedge rst_n)
    if (!rst_n) begin a_q <= 0; w_q <= 0; y <= 0; end
    else begin a_q <= a; w_q <= w; y <= node[2*P2-2][YW-1:0]; end
endmodule
