module ExampleRom (
    output reg[7:0] data,
    input wire[1:0] idx
);
    reg[7:0] rom[0:3];
    always @(idx) begin: assig_process_data
        data = rom[idx];
    end

    initial begin
        rom[0] = 8'h03;
        rom[1] = 8'h0a;
        rom[2] = 8'h0c;
        rom[3] = 8'h63;
    end

endmodule
