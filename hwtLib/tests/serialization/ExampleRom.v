module ExampleRom (
    output reg[7:0] data,
    input wire[1:0] idx
);
    reg[7:0] rom[0:3];
    always @(idx) begin: assig_process_data
        data = rom[idx];
    end

    initial begin
        rom[0] = 3;
        rom[1] = 10;
        rom[2] = 12;
        rom[3] = 99;
    end

endmodule
