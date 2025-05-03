module ExampleHBitsMul0b (
    input wire[15:0] a,
    input wire[15:0] b,
    input wire[15:0] c,
    output reg[15:0] res
);
    always @(a, b, c) begin: assig_process_res
        reg[15:0] tmp_mul_0;
        tmp_mul_0 = a * b;
        res = tmp_mul_0 + c;
    end

endmodule
