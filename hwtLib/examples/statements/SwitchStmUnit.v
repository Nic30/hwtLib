//
//    Example which is using switch statement to create multiplexer
//
//    .. hwt-schematic::
//    
module SwitchStmUnit (
    input  a,
    input  b,
    input  c,
    output reg out,
    input [2:0] sel
);
    always @(a, b, c, sel) begin: assig_process_out
        case(sel)
            3'b000:
                out = a;
            3'b001:
                out = b;
            3'b010:
                out = c;
            default:
                out = 1'b0;
        endcase
    end

endmodule
