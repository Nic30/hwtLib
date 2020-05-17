//
//    .. hwt-schematic::
//    
module AsyncResetReg (
    input  clk,
    input  din,
    output  dout,
    input  rst
);
    reg internReg = 1'b0;
    assign dout = internReg;
    always @(posedge clk, posedge rst) begin: assig_process_internReg
        if (rst == 1'b1)
            internReg <= 1'b0;
        else
            internReg <= din;
    end

endmodule
