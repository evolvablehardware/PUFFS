// func adder(chan A, B, S) {
// 	while {
// 		S.send(A.recv() + B.recv())
// 	}
// }

`timescale 1ns/1ps

module adder #(parameter WIDTH = 8)
(
	input wire clk,
	input wire reset,
	input wire B_valid,
	output wire B_ready,
	input wire [WIDTH-1:0] B_data,
	input wire A_valid,
	output wire A_ready,
	input wire [WIDTH-1:0] A_data,
	output wire S_valid,
	input wire S_ready,
	output wire [WIDTH-1:0] S_data
);
	wire branch_0_ready;
	reg S_valid_reg;
	reg [WIDTH-1:0] S_state;
	wire __S_ok;
	reg branch_id;
	assign S_valid = S_valid_reg;
	assign S_data = S_state;
	assign __S_ok = (!S_valid_reg||S_ready);
	assign branch_0_ready = B_valid&&A_valid&&(S_ready||!S_valid_reg)&&branch_id==0;
	assign B_ready = branch_0_ready;
	assign A_ready = branch_0_ready;
	always @(posedge clk)
		if (reset) begin
			S_valid_reg <= 0;
			S_state <= 0;
			branch_id <= 0;
		end else if (B_valid&&A_valid&&(S_ready||!S_valid_reg)) begin
			branch_id <= 0;
			S_state <= (A_data)+(B_data);
			S_valid_reg <= 1;
		end else
			if (S_ready)
				S_valid_reg <= 0;

initial begin
        $dumpfile("dump.vcd");
        $dumpvars(0, adder); // dump all signals in this module and below
    end

endmodule


