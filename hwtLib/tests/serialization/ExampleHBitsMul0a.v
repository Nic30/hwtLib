module ExampleHBitsMul0a (
    input wire[15:0] a,
    input wire[15:0] b,
    output reg[15:0] res
);
    always @(a, b) begin: assig_process_res
        reg[15:0] tmp_mul_0;
        tmp_mul_0 = a * b;
        res = tmp_mul_0;
    end

endmodule
