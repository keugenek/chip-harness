
read_liberty /home/claude/forge/pdk/sg13g2_stdcell_typ_1p20V_25C.lib
read_verilog syn_area.v
link_design dot_s8
create_clock -name clk -period 10.0 [get_ports clk]
set_input_delay 0 -clock clk [get_ports {a* w*}]
set_output_delay 0 -clock clk [get_ports y*]
set_false_path -from [get_ports rst_n]
puts "WS [sta::worst_slack -max]"
report_checks -path_delay max -format summary
read_vcd -scope TOP/tb/dut act_area.vcd
report_power
