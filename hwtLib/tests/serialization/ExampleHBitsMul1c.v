module ExampleHBitsMul1c (
    input wire signed[7:0] a,
    input wire signed[7:0] b,
    input wire signed[15:0] c,
    output reg signed[15:0] res
);
    always @(a, b, c) begin: assig_process_res
        reg signed[15:0] tmp_mul_0;
        tmp_mul_0 = $unsigned(a) * $unsigned(b);
        res = tmp_mul_0 + c;
    end

endmodule
