/*

    Example which is using switch statement to create multiplexer

    .. hwt-schematic::
    
*/
module SwitchStmUnit(input a,
        input b,
        input c,
        output reg out,
        input [2:0] sel
    );

    always @(a or b or c or sel) begin: assig_process_out
        case(sel)
        3'b000: begin
            out = a;
        end
        3'b001: begin
            out = b;
        end
        3'b010: begin
            out = c;
        end
        default: begin
            out = 1'b0;
        end
        endcase
    end

endmodule
