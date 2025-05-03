module ExampleHBitsMulS1a (
    input wire[7:0] a,
    input wire[7:0] b,
    output reg[15:0] res
);
    always @(a, b) begin: assig_process_res
        reg[15:0] tmp_mul_0;
        tmp_mul_0 = $signed(a) * $signed(b);
        res = tmp_mul_0;
    end

endmodule
