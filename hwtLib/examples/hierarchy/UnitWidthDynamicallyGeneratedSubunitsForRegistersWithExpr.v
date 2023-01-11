//
//    An unit which will extract selected circuit from parent on instantiation.
//    
module ExtractedUnit (
    input wire clk,
    input wire[7:0] i,
    output wire[7:0] r0,
    input wire sig_0
);
    reg[7:0] r0_0 = 8'h00;
    reg[7:0] r0_next;
    always @(posedge clk) begin: assig_process_r0
        if (sig_0)
            r0_0 <= 8'h00;
        else
            r0_0 <= r0_next;
    end

    assign r0 = r0_0;
    always @(i) begin: assig_process_r0_next
        r0_next = i + 8'h01;
    end

endmodule
//
//    An unit which will extract selected circuit from parent on instantiation.
//    
module ExtractedUnit_0 (
    input wire clk,
    output wire[7:0] r1,
    input wire sig_0,
    input wire[7:0] sig_uForR0_r0
);
    reg[7:0] r1_0 = 8'h00;
    reg[7:0] r1_next;
    always @(posedge clk) begin: assig_process_r1
        if (sig_0)
            r1_0 <= 8'h00;
        else
            r1_0 <= r1_next;
    end

    assign r1 = r1_0;
    always @(sig_uForR0_r0) begin: assig_process_r1_next
        r1_next = (sig_uForR0_r0 ^ 8'h01) + 8'h01 + sig_uForR0_r0;
    end

endmodule
module UnitWidthDynamicallyGeneratedSubunitsForRegistersWithExpr (
    input wire clk,
    input wire[7:0] i,
    output wire[7:0] o,
    input wire rst_n
);
    wire sig_uForR0_clk;
    wire[7:0] sig_uForR0_i;
    wire[7:0] sig_uForR0_r0;
    reg sig_uForR0_sig_0;
    wire sig_uForR1_clk;
    wire[7:0] sig_uForR1_r1;
    reg sig_uForR1_sig_0;
    wire[7:0] sig_uForR1_sig_uForR0_r0;
    ExtractedUnit uForR0_inst (
        .clk(sig_uForR0_clk),
        .i(sig_uForR0_i),
        .r0(sig_uForR0_r0),
        .sig_0(sig_uForR0_sig_0)
    );

    ExtractedUnit_0 uForR1_inst (
        .clk(sig_uForR1_clk),
        .r1(sig_uForR1_r1),
        .sig_0(sig_uForR1_sig_0),
        .sig_uForR0_r0(sig_uForR1_sig_uForR0_r0)
    );

    assign o = sig_uForR1_r1;
    assign sig_uForR0_clk = clk;
    assign sig_uForR0_i = i;
    always @(rst_n) begin: assig_process_sig_uForR0_sig_0
        sig_uForR0_sig_0 = rst_n == 1'b0;
    end

    assign sig_uForR1_clk = clk;
    always @(rst_n) begin: assig_process_sig_uForR1_sig_0
        sig_uForR1_sig_0 = rst_n == 1'b0;
    end

    assign sig_uForR1_sig_uForR0_r0 = sig_uForR0_r0;
endmodule
