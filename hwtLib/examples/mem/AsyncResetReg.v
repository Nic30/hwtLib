//
//    .. hwt-autodoc::
//    
module AsyncResetReg (
    input wire clk,
    input wire din,
    output wire dout,
    input wire rst
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
