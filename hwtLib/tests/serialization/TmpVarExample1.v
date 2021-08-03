module TmpVarExample1 (
    input wire[31:0] a,
    output reg[31:0] b
);
    always @(a) begin: assig_process_b
        reg tmp_index_0;
        reg tmp_index_1;
        tmp_index_0 = a[15:0] == 16'h0001;
        tmp_index_1 = a[31:16] == 16'h0001;
        if (tmp_index_0 == 1'b0 & tmp_index_1 == 1'b0)
            b = 32'h00000000;
        else
            b = 32'h00000001;
    end

endmodule
