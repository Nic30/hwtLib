//
//    .. hwt-autodoc::
//    
module FsmExample (
    input wire a,
    input wire b,
    input wire clk,
    output reg[2:0] dout,
    input wire rst_n
);
    reg[1:0] st = 0;
    reg[1:0] st_next;
    always @(st) begin: assig_process_dout
        case(st)
            0:
                dout = 3'b001;
            1:
                dout = 3'b010;
            default:
                dout = 3'b011;
        endcase
    end

    always @(posedge clk) begin: assig_process_st
        if (rst_n == 1'b0)
            st <= 0;
        else
            st <= st_next;
    end

    always @(a, b, st) begin: assig_process_st_next
        case(st)
            0:
                if (a & b)
                    st_next = 2;
                else if (b)
                    st_next = 1;
                else
                    st_next = st;
            1:
                if (a & b)
                    st_next = 2;
                else if (a)
                    st_next = 0;
                else
                    st_next = st;
            default:
                if (a & ~b)
                    st_next = 0;
                else if (~a & b)
                    st_next = 1;
                else
                    st_next = st;
        endcase
    end

endmodule
