module TmpVarZExtBool (
    input wire[7:0] a,
    input wire[7:0] b,
    output reg o0,
    output reg[1:0] o0_2b,
    output reg signed[1:0] o0_2b_s,
    output reg[1:0] o0_2b_u,
    output reg[2:0] o0_3b,
    output reg signed[2:0] o0_3b_s,
    output reg[2:0] o0_3b_u
);
    always @(a, b) begin: assig_process_o0
        o0 = a < b;
    end

    always @(a, b) begin: assig_process_o0_2b
        o0_2b = {1'b0, a < b};
    end

    always @(a, b) begin: assig_process_o0_2b_s
        o0_2b_s = $signed({1'b0, a < b});
    end

    always @(a, b) begin: assig_process_o0_2b_u
        o0_2b_u = {1'b0, a < b};
    end

    always @(a, b) begin: assig_process_o0_3b
        o0_3b = {2'b00, a < b};
    end

    always @(a, b) begin: assig_process_o0_3b_s
        o0_3b_s = $signed({2'b00, a < b});
    end

    always @(a, b) begin: assig_process_o0_3b_u
        o0_3b_u = {2'b00, a < b};
    end

endmodule
