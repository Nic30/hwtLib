/*

    Every HW component class has to be derived from Unit class

    .. hwt-schematic::
    
*/
module Showcase0(input [31:0] a,
        input signed [31:0] b,
        output [31:0] c,
        input clk,
        output cmp_0,
        output cmp_1,
        output cmp_2,
        output cmp_3,
        output cmp_4,
        output cmp_5,
        output [31:0] contOut,
        input [31:0] d,
        input e,
        output f,
        output [15:0] fitted,
        output [7:0] g,
        output reg [7:0] h,
        input [1:0] i,
        output reg [7:0] j,
        output reg [31:0] k,
        output out,
        output output_0,
        input rst_n,
        output reg [7:0] sc_signal
    );

    reg [31:0] const_private_signal = 123;
    reg signed [7:0] fallingEdgeRam [4-1:0];
    reg r = 1'b0;
    reg [1:0] r_0 = 2'b00;
    reg [1:0] r_1 = 2'b00;
    reg r_next;
    wire [1:0] r_next_0;
    wire [1:0] r_next_1;
    reg [7:0] rom;
    assign c = a + $unsigned(b);
    assign cmp_0 = a < 4;
    assign cmp_1 = a > 4;
    assign cmp_2 = b <= $signed(4);
    assign cmp_3 = b >= $signed(4);
    assign cmp_4 = b != $signed(4);
    assign cmp_5 = b == $signed(4);
    assign contOut = const_private_signal;
    assign f = r;
    always @(negedge clk) begin: assig_process_fallingEdgeRam
        fallingEdgeRam[r_1] <= $signed(a[7:0]);
        k <= {24'h000000, $unsigned(fallingEdgeRam[r_1])};
    end

    assign fitted = a[15:0];
    assign g = {{(a[1]) & (b[1]), ((a[0]) ^ (b[0])) | (a[1])}, a[5:0]};
    always @(a or r) begin: assig_process_h
        if((a[2])==1'b1) begin
            if((r)==1'b1) begin
                h <= 8'h00;
            end else if((a[1])==1'b1) begin
                h <= 8'h01;
            end else begin
                h <= 8'h02;
            end
        end
    end

    always @(posedge clk) begin: assig_process_j
        j <= rom;
    end

    assign out = 1'b0;
    assign output_0 = 1'bx;
    always @(posedge clk) begin: assig_process_r
        if(rst_n == 1'b0) begin
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
    always @(e or r) begin: assig_process_r_next
        if((~r)==1'b1) begin
            r_next <= e;
        end else begin
            r_next <= r;
        end
    end

    always @(a) begin: assig_process_sc_signal
        case(a)
        1:
            sc_signal <= 8'h00;
        2:
            sc_signal <= 8'h01;
        3:
            sc_signal <= 8'h03;
        default:
            sc_signal <= 8'h04;
        endcase
    end

    always @(r_1) begin: rom_0
        case(r_1)
        0:
            rom <= 0;
        1:
            rom <= 1;
        2:
            rom <= 2;
        3:
            rom <= 3;
        endcase
    end

endmodule