//
//    Every HW component class has to be derived from :class:`hwt.synthesizer.unit.Unit` class
//
//    .. hwt-autodoc::
//    
module Showcase0 (
    input wire[31:0] a,
    input wire signed[31:0] b,
    output reg[31:0] c,
    input wire clk,
    output reg cmp_0,
    output reg cmp_1,
    output reg cmp_2,
    output reg cmp_3,
    output reg cmp_4,
    output reg cmp_5,
    output reg[31:0] contOut,
    input wire[31:0] d,
    input wire e,
    output wire f,
    output reg[15:0] fitted,
    output reg[7:0] g,
    output reg[7:0] h,
    input wire[1:0] i,
    output reg[7:0] j,
    output reg[31:0] k,
    output wire out,
    output wire output_0,
    input wire rst_n,
    output reg[7:0] sc_signal
);
    localparam [31:0] const_private_signal = 32'h0000007b;
    reg signed[7:0] fallingEdgeRam[0:3];
    reg r = 1'b0;
    reg[1:0] r_0 = 2'b00;
    reg[1:0] r_1 = 2'b00;
    reg r_next;
    wire[1:0] r_next_0;
    wire[1:0] r_next_1;
    reg[7:0] rom[0:3];
    always @(a, b) begin: assig_process_c
        c = a + $signed(b);
    end

    always @(a) begin: assig_process_cmp_0
        cmp_0 = a < 32'h00000004;
    end

    always @(a) begin: assig_process_cmp_1
        cmp_1 = a > 32'h00000004;
    end

    always @(b) begin: assig_process_cmp_2
        cmp_2 = b <= $signed(32'h00000004);
    end

    always @(b) begin: assig_process_cmp_3
        cmp_3 = b >= $signed(32'h00000004);
    end

    always @(b) begin: assig_process_cmp_4
        cmp_4 = b != $signed(32'h00000004);
    end

    always @(b) begin: assig_process_cmp_5
        cmp_5 = b == $signed(32'h00000004);
    end

    always @(*) begin: assig_process_contOut
        contOut = const_private_signal;
    end

    assign f = r;
    always @(negedge clk) begin: assig_process_fallingEdgeRam
        fallingEdgeRam[r_1] <= $unsigned(a[7:0]);
        k <= {24'h000000, $signed(fallingEdgeRam[r_1])};
    end

    always @(a) begin: assig_process_fitted
        fitted = a[15:0];
    end

    always @(a, b) begin: assig_process_g
        g = {{a[1] & b[1], a[0] ^ b[0] | a[1]}, a[5:0]};
    end

    always @(a, r) begin: assig_process_h
        if (a[2])
            if (r)
                h = 8'h00;
            else if (a[1])
                h = 8'h01;
            else
                h = 8'h02;
    end

    always @(posedge clk) begin: assig_process_j
        j <= rom[r_1];
    end

    assign out = 1'b0;
    assign output_0 = 1'bx;
    always @(posedge clk) begin: assig_process_r
        if (rst_n == 1'b0) begin
            r_1 <= 2'b00;
            r_0 <= 2'b00;
            r <= 1'b0;
        end else begin
            r_1 <= r_next_1;
            r_0 <= r_next_0;
            r <= r_next;
        end
    end

    assign r_next_0 = i;
    assign r_next_1 = r_0;
    always @(e, r) begin: assig_process_r_next_1
        if (~r)
            r_next = e;
        else
            r_next = r;
    end

    always @(a) begin: assig_process_sc_signal
        case(a)
            32'h00000001:
                sc_signal = 8'h00;
            32'h00000002:
                sc_signal = 8'h01;
            32'h00000003:
                sc_signal = 8'h03;
            default:
                sc_signal = 8'h04;
        endcase
    end

    initial begin
        rom[0] = 0;
        rom[1] = 1;
        rom[2] = 2;
        rom[3] = 3;
    end

endmodule
