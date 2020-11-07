//
//    Simple parametrized unit.
//
//    .. hwt-schematic::
//    
module SimpleUnitWithParam_0 #(
    parameter DATA_WIDTH = 2
) (
    input [1:0] a,
    output [1:0] b
);
    assign b = a;
endmodule
//
//    Simple parametrized unit.
//
//    .. hwt-schematic::
//    
module SimpleUnitWithParam_1 #(
    parameter DATA_WIDTH = 3
) (
    input [2:0] a,
    output [2:0] b
);
    assign b = a;
endmodule
//
//    Simple parametrized unit.
//
//    .. hwt-schematic::
//    
module SimpleUnitWithParam #(
    parameter DATA_WIDTH = 2
) (
    input [DATA_WIDTH - 1:0] a,
    output [DATA_WIDTH - 1:0] b
);
    generate if (DATA_WIDTH == 32'h2)
        SimpleUnitWithParam_0 #(
            .DATA_WIDTH(2)
        ) possible_variants_0_inst (
            .a(a),
            .b(b)
        );
    else if (DATA_WIDTH == 32'h3)
        SimpleUnitWithParam_1 #(
            .DATA_WIDTH(3)
        ) possible_variants_1_inst (
            .a(a),
            .b(b)
        );
    endgenerate

endmodule
