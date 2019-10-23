/*

    Double Data Rate register

    .. hwt-schematic::
    
*/
module DDR_Reg(input clk,
        input din,
        output reg [1:0] dout,
        input rst
    );

    reg internReg = 1'b0;
    reg internReg_0 = 1'b0;
    always @(internReg or internReg_0) begin: assig_process_dout
        dout = {internReg, internReg_0};
    end

    always @(posedge clk) begin: assig_process_internReg
        internReg <= din;
    end

    always @(negedge clk) begin: assig_process_internReg_0
        internReg_0 <= din;
    end

endmodule