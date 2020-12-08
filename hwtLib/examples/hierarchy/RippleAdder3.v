//
//    .. hwt-autodoc::
//    
module FullAdder (
    input  a,
    input  b,
    input  ci,
    output reg co,
    output reg s
);
    always @(a, b, ci) begin: assig_process_co
        co = a & b | (a & ci) | (b & ci);
    end

    always @(a, b, ci) begin: assig_process_s
        s = a ^ b ^ ci;
    end

endmodule
//
//    .. hwt-autodoc::
//    
module RippleAdder3 #(
    parameter p_wordlength = 4
) (
    input [3:0] a,
    input [3:0] b,
    input  ci,
    output  co,
    output reg[3:0] s
);
    reg sig_fa_0_a = 1'bx;
    reg sig_fa_0_b = 1'bx;
    wire sig_fa_0_ci = 1'bx;
    wire sig_fa_0_co = 1'bx;
    wire sig_fa_0_s = 1'bx;
    reg sig_fa_1_a = 1'bx;
    reg sig_fa_1_b = 1'bx;
    wire sig_fa_1_ci = 1'bx;
    wire sig_fa_1_co = 1'bx;
    wire sig_fa_1_s = 1'bx;
    reg sig_fa_2_a = 1'bx;
    reg sig_fa_2_b = 1'bx;
    wire sig_fa_2_ci = 1'bx;
    wire sig_fa_2_co = 1'bx;
    wire sig_fa_2_s = 1'bx;
    reg sig_fa_3_a = 1'bx;
    reg sig_fa_3_b = 1'bx;
    wire sig_fa_3_ci = 1'bx;
    wire sig_fa_3_co = 1'bx;
    wire sig_fa_3_s = 1'bx;
    FullAdder fa_0_inst (
        .a(sig_fa_0_a),
        .b(sig_fa_0_b),
        .ci(sig_fa_0_ci),
        .co(sig_fa_0_co),
        .s(sig_fa_0_s)
    );

    FullAdder fa_1_inst (
        .a(sig_fa_1_a),
        .b(sig_fa_1_b),
        .ci(sig_fa_1_ci),
        .co(sig_fa_1_co),
        .s(sig_fa_1_s)
    );

    FullAdder fa_2_inst (
        .a(sig_fa_2_a),
        .b(sig_fa_2_b),
        .ci(sig_fa_2_ci),
        .co(sig_fa_2_co),
        .s(sig_fa_2_s)
    );

    FullAdder fa_3_inst (
        .a(sig_fa_3_a),
        .b(sig_fa_3_b),
        .ci(sig_fa_3_ci),
        .co(sig_fa_3_co),
        .s(sig_fa_3_s)
    );

    assign co = sig_fa_3_co;
    always @(sig_fa_0_s, sig_fa_1_s, sig_fa_2_s, sig_fa_3_s) begin: assig_process_s
        s = {{{sig_fa_3_s, sig_fa_2_s}, sig_fa_1_s}, sig_fa_0_s};
    end

    always @(a) begin: assig_process_sig_fa_0_a
        sig_fa_0_a = a[0];
    end

    always @(b) begin: assig_process_sig_fa_0_b
        sig_fa_0_b = b[0];
    end

    assign sig_fa_0_ci = ci;
    always @(a) begin: assig_process_sig_fa_1_a
        sig_fa_1_a = a[1];
    end

    always @(b) begin: assig_process_sig_fa_1_b
        sig_fa_1_b = b[1];
    end

    assign sig_fa_1_ci = sig_fa_0_co;
    always @(a) begin: assig_process_sig_fa_2_a
        sig_fa_2_a = a[2];
    end

    always @(b) begin: assig_process_sig_fa_2_b
        sig_fa_2_b = b[2];
    end

    assign sig_fa_2_ci = sig_fa_1_co;
    always @(a) begin: assig_process_sig_fa_3_a
        sig_fa_3_a = a[3];
    end

    always @(b) begin: assig_process_sig_fa_3_b
        sig_fa_3_b = b[3];
    end

    assign sig_fa_3_ci = sig_fa_2_co;
endmodule
