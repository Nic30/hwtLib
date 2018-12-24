/*

    Basic d flip flop

    :attention: using this unit is pointless because HWToolkit can automatically
        generate such a register for any interface and datatype

    .. hwt-schematic::

*/

#include <systemc.h>


SC_MODULE(DReg) {
    //interfaces
    sc_in_clk clk;
    sc_in<sc_uint<1>> din;
    sc_out<sc_uint<1>> dout;
    sc_in<sc_uint<1>> rst;

    //internal signals
    sc_uint<1> internReg = '0';
    sc_signal<sc_uint<1>> internReg_next;

    //processes inside this component
    void assig_process_dout() {
        dout.write(internReg);
    }
    void assig_process_internReg() {
        if(rst.read() == '1') {
            internReg = '0';
        } else {
            internReg = internReg_next.read();
        }
    }
    void assig_process_internReg_next() {
        internReg_next.write(din.read());
    }

    SC_CTOR(DReg) {
        SC_METHOD(assig_process_dout);
        sensitive << internReg;
        SC_METHOD(assig_process_internReg);
        sensitive << clk.pos();
        SC_METHOD(assig_process_internReg_next);
        sensitive << din;
    }
};
