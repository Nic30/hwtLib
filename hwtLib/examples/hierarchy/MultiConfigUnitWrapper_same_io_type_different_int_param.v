//
//    Simple parametrized unit.
//
//    .. hwt-autodoc::
//    
module SimpleUnitWithParam_0 #(
    parameter DATA_WIDTH = 2
) (
    input wire[1:0] a,
    output wire[1:0] b
);
    assign b = a;
    generate if (DATA_WIDTH != 2)
        $error("%m Generated only for this param value");
    endgenerate

endmodule
//
//    Simple parametrized unit.
//
//    .. hwt-autodoc::
//    
module SimpleUnitWithParam_1 #(
    parameter DATA_WIDTH = 3
) (
    input wire[2:0] a,
    output wire[2:0] b
);
    assign b = a;
    generate if (DATA_WIDTH != 3)
        $error("%m Generated only for this param value");
    endgenerate

endmodule
//
//    Simple parametrized unit.
//
//    .. hwt-autodoc::
//    
module SimpleUnitWithParam #(
    parameter DATA_WIDTH = 2
) (
    input wire[DATA_WIDTH - 1:0] a,
    output wire[DATA_WIDTH - 1:0] b
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
    else
        $error("%m The component was generated for this generic/params combination");
    endgenerate

endmodule
