/*

    .. hwt-schematic::
    
*/
module FsmExample(input a,
        input b,
        input clk,
        output reg [2:0] dout,
        input rst_n
    );

    reg [1:0] st = 0;
    reg [1:0] st_next;
    always @(st) begin: assig_process_dout
        case(st)
        0: begin
            dout = 3'b001;
        end
        1: begin
            dout = 3'b010;
        end
        default: begin
            dout = 3'b011;
        end
        endcase
    end

    always @(posedge clk) begin: assig_process_st
        if (rst_n == 1'b0) begin
            st <= 0;
        end else begin
            st <= st_next;
        end
    end

    always @(a or b or st) begin: assig_process_st_next
        case(st)
        0: begin
            if (a & b) begin
                st_next = 2;
            end else if (b) begin
                st_next = 1;
            end else begin
                st_next = st;
            end
        end
        1: begin
            if (a & b) begin
                st_next = 2;
            end else if (a) begin
                st_next = 0;
            end else begin
                st_next = st;
            end
        end
        default: begin
            if (a & ~b) begin
                st_next = 0;
            end else if (~a & b) begin
                st_next = 1;
            end else begin
                st_next = st;
            end
        end
        endcase
    end

endmodule
