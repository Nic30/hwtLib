//
//An unit which will extract selected circuit from parent on instantiation.
module ExtractedHwModule (
    input wire clk,
    input wire[7:0] i0,
    input wire[7:0] i1,
    output wire[7:0] r0_0,
    output wire[7:0] r0_1,
    input wire sig_0
);
    reg[7:0] r0_0_0 = 8'h00;
    wire[7:0] r0_0_next;
    reg[7:0] r0_1_0 = 8'h00;
    wire[7:0] r0_1_next;
    assign r0_0 = r0_0_0;
    assign r0_0_next = i0;
    always @(posedge clk) begin: assig_process_r0_1
        if (sig_0) begin
            r0_1_0 <= 8'h00;
            r0_0_0 <= 8'h00;
        end else begin
            r0_1_0 <= r0_1_next;
            r0_0_0 <= r0_0_next;
        end
    end

    assign r0_1 = r0_1_0;
    assign r0_1_next = i1;
endmodule
//
//An unit which will extract selected circuit from parent on instantiation.
module ExtractedHwModule_0 (
    input wire clk,
    output wire[7:0] r1_0,
    output wire[7:0] r1_1,
    input wire sig_0,
    input wire[7:0] sig_uForR0_r0_0,
    input wire[7:0] sig_uForR0_r0_1
);
    reg[7:0] r1_0_0 = 8'h00;
    wire[7:0] r1_0_next;
    reg[7:0] r1_1_0 = 8'h00;
    wire[7:0] r1_1_next;
    assign r1_0 = r1_0_0;
    assign r1_0_next = sig_uForR0_r0_0;
    always @(posedge clk) begin: assig_process_r1_1
        if (sig_0) begin
            r1_1_0 <= 8'h00;
            r1_0_0 <= 8'h00;
        end else begin
            r1_1_0 <= r1_1_next;
            r1_0_0 <= r1_0_next;
        end
    end

    assign r1_1 = r1_1_0;
    assign r1_1_next = sig_uForR0_r0_1;
endmodule
module HwModuleWidthDynamicallyGeneratedSubunitsForManyRegisters (
    input wire clk,
    input wire[7:0] i0,
    input wire[7:0] i1,
    output reg[7:0] o,
    input wire rst_n
);
    wire sig_uForR0_clk;
    wire[7:0] sig_uForR0_i0;
    wire[7:0] sig_uForR0_i1;
    wire[7:0] sig_uForR0_r0_0;
    wire[7:0] sig_uForR0_r0_1;
    reg sig_uForR0_sig_0;
    wire sig_uForR1_clk;
    wire[7:0] sig_uForR1_r1_0;
    wire[7:0] sig_uForR1_r1_1;
    reg sig_uForR1_sig_0;
    wire[7:0] sig_uForR1_sig_uForR0_r0_0;
    wire[7:0] sig_uForR1_sig_uForR0_r0_1;
    ExtractedHwModule uForR0_inst (
        .clk(sig_uForR0_clk),
        .i0(sig_uForR0_i0),
        .i1(sig_uForR0_i1),
        .r0_0(sig_uForR0_r0_0),
        .r0_1(sig_uForR0_r0_1),
        .sig_0(sig_uForR0_sig_0)
    );

    ExtractedHwModule_0 uForR1_inst (
        .clk(sig_uForR1_clk),
        .r1_0(sig_uForR1_r1_0),
        .r1_1(sig_uForR1_r1_1),
        .sig_0(sig_uForR1_sig_0),
        .sig_uForR0_r0_0(sig_uForR1_sig_uForR0_r0_0),
        .sig_uForR0_r0_1(sig_uForR1_sig_uForR0_r0_1)
    );

    always @(sig_uForR1_r1_0, sig_uForR1_r1_1) begin: assig_process_o
        o = sig_uForR1_r1_0 + sig_uForR1_r1_1;
    end

    assign sig_uForR0_clk = clk;
    assign sig_uForR0_i0 = i0;
    assign sig_uForR0_i1 = i1;
    always @(rst_n) begin: assig_process_sig_uForR0_sig_0
        sig_uForR0_sig_0 = rst_n == 1'b0;
    end

    assign sig_uForR1_clk = clk;
    always @(rst_n) begin: assig_process_sig_uForR1_sig_0
        sig_uForR1_sig_0 = rst_n == 1'b0;
    end

    assign sig_uForR1_sig_uForR0_r0_0 = sig_uForR0_r0_0;
    assign sig_uForR1_sig_uForR0_r0_1 = sig_uForR0_r0_1;
endmodule
