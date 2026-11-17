// Baseline B0: what a human writes first. Behavioural multiply-accumulate,
// left to the synthesis tool. Registered inputs and output.
module dot_s8 #(parameter N = 27, parameter YW = 16 + $clog2(N)) (
  input  wire             clk,
  input  wire             rst_n,
  input  wire [N*8-1:0]   a,
  input  wire [N*8-1:0]   w,
  output reg  [YW-1:0]    y
);
  reg [N*8-1:0] a_q, w_q;
  reg signed [YW-1:0] acc;
  integer i;
  always @* begin
    acc = 0;
    for (i = 0; i < N; i = i + 1)
      acc = acc + $signed(a_q[i*8 +: 8]) * $signed(w_q[i*8 +: 8]);
  end
  always @(posedge clk or negedge rst_n)
    if (!rst_n) begin a_q <= 0; w_q <= 0; y <= 0; end
    else begin a_q <= a; w_q <= w; y <= acc; end
endmodule
