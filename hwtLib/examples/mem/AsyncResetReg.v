/*

    .. hwt-schematic::
    
*/
module AsyncResetReg(input clk,
        input din,
        output dout,
        input rst
    );

    reg internReg = 1'b0;
    assign dout = internReg;
    always @(posedge clk or posedge rst) begin: assig_process_internReg
        if(rst == 1'b1) begin
            internReg = 1'b0;
        end else begin
            internReg <= din;
        end
    end

endmodule