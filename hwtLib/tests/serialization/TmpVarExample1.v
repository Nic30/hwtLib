module TmpVarExample1 (
    input wire[31:0] a,
    output reg[31:0] b
);
    always @(a) begin: assig_process_b
        if (a[15:0] == 16'h0001 == 0 & a[31:16] == 16'h0001 == 0)
            b = 32'h00000000;
        else
            b = 32'h00000001;
    end

endmodule
