//
//    .. hwt-autodoc::
//    
module FullAdder (
    input wire a,
    input wire b,
    input wire ci,
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
module RippleAdder0 #(
    parameter p_wordlength = 4
) (
    input wire[3:0] a,
    input wire[3:0] b,
    input wire ci,
    output reg co,
    output reg[3:0] s
);
    reg[4:0] c;
    reg sig_fa0_a;
    reg sig_fa0_b;
    reg sig_fa0_ci;
    wire sig_fa0_co;
    wire sig_fa0_s;
    reg sig_fa1_a;
    reg sig_fa1_b;
    reg sig_fa1_ci;
    wire sig_fa1_co;
    wire sig_fa1_s;
    reg sig_fa2_a;
    reg sig_fa2_b;
    reg sig_fa2_ci;
    wire sig_fa2_co;
    wire sig_fa2_s;
    reg sig_fa3_a;
    reg sig_fa3_b;
    reg sig_fa3_ci;
    wire sig_fa3_co;
    wire sig_fa3_s;
    FullAdder fa0_inst (
        .a(sig_fa0_a),
        .b(sig_fa0_b),
        .ci(sig_fa0_ci),
        .co(sig_fa0_co),
        .s(sig_fa0_s)
    );

    FullAdder fa1_inst (
        .a(sig_fa1_a),
        .b(sig_fa1_b),
        .ci(sig_fa1_ci),
        .co(sig_fa1_co),
        .s(sig_fa1_s)
    );

    FullAdder fa2_inst (
        .a(sig_fa2_a),
        .b(sig_fa2_b),
        .ci(sig_fa2_ci),
        .co(sig_fa2_co),
        .s(sig_fa2_s)
    );

    FullAdder fa3_inst (
        .a(sig_fa3_a),
        .b(sig_fa3_b),
        .ci(sig_fa3_ci),
        .co(sig_fa3_co),
        .s(sig_fa3_s)
    );

    always @(ci, sig_fa0_co) begin: assig_process_c
        c = {{{{sig_fa0_co, sig_fa0_co}, sig_fa0_co}, sig_fa0_co}, ci};
    end

    always @(c) begin: assig_process_co
        co = c[4];
    end

    always @(sig_fa0_s, sig_fa1_s, sig_fa2_s, sig_fa3_s) begin: assig_process_s
        s = {{{sig_fa3_s, sig_fa2_s}, sig_fa1_s}, sig_fa0_s};
    end

    always @(a) begin: assig_process_sig_fa0_a
        sig_fa0_a = a[0];
    end

    always @(a) begin: assig_process_sig_fa0_b
        sig_fa0_b = a[0];
    end

    always @(c) begin: assig_process_sig_fa0_ci
        sig_fa0_ci = c[0];
    end

    always @(a) begin: assig_process_sig_fa1_a
        sig_fa1_a = a[1];
    end

    always @(a) begin: assig_process_sig_fa1_b
        sig_fa1_b = a[1];
    end

    always @(c) begin: assig_process_sig_fa1_ci
        sig_fa1_ci = c[1];
    end

    always @(a) begin: assig_process_sig_fa2_a
        sig_fa2_a = a[2];
    end

    always @(a) begin: assig_process_sig_fa2_b
        sig_fa2_b = a[2];
    end

    always @(c) begin: assig_process_sig_fa2_ci
        sig_fa2_ci = c[2];
    end

    always @(a) begin: assig_process_sig_fa3_a
        sig_fa3_a = a[3];
    end

    always @(a) begin: assig_process_sig_fa3_b
        sig_fa3_b = a[3];
    end

    always @(c) begin: assig_process_sig_fa3_ci
        sig_fa3_ci = c[3];
    end

    generate if (p_wordlength != 4)
        $error("%m Generated only for this param value");
    endgenerate

endmodule
