// func adder(chan A, B, S) {
// 	while {
// 		S.send(A.recv() + B.recv())
// 	}
// }

`timescale 1ns/1ps

module adder #(
	parameter WIDTH = 8
) (
	input wire clk,
	input wire reset,
	input wire A_valid,
	output wire A_ready,
	input wire [WIDTH-1:0] A_data,
	input wire B_valid,
	output wire B_ready,
	input wire [WIDTH-1:0] B_data,
	output wire S_valid,
	input wire S_ready,
	output wire [WIDTH:0] S_data
);
	wire branch_0_valid;
	wire branch_0_ready;

	reg S_valid_reg;
	reg [WIDTH:0] S_state;
	assign S_valid = S_valid_reg;
	assign S_data = S_state;

	assign branch_0_valid = A_valid&&B_valid;
	assign branch_0_ready = branch_0_valid&&(S_ready||!S_valid_reg);
	assign B_ready = branch_0_ready;
	assign A_ready = branch_0_ready;

	always @(posedge clk) begin
		if (reset) begin
			S_valid_reg <= 0;
			S_state <= 0;
		end else if (branch_0_valid&&(S_ready||!S_valid_reg)) begin
			S_valid_reg <= 1;
			S_state <= A_data+B_data;
		end else begin
			if (S_ready) begin
				S_valid_reg <= 0;
			end
		end
	end

`ifndef SYNTHESIS
	initial begin
		$dumpfile("dump.vcd");
		$dumpvars(0, adder); // dump all signals in this module and below
	end
`endif
endmodule


