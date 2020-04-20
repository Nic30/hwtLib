/*

    Example which is using switch statement to create multiplexer

    .. hwt-schematic::

*/

#include <systemc.h>


SC_MODULE(SwitchStmUnit) {
    //interfaces
    sc_in<sc_uint<1>> a;
    sc_in<sc_uint<1>> b;
    sc_in<sc_uint<1>> c;
    sc_out<sc_uint<1>> out;
    sc_in<sc_uint<3>> sel;

    //processes inside this component
    void assig_process_out() {
        switch(sel.read()) {
        case sc_uint<3>("000"):
            out.write(a.read());
            break;
        case sc_uint<3>("001"):
            out.write(b.read());
            break;
        case sc_uint<3>("010"):
            out.write(c.read());
            break;
        default:
            out.write(0);
            break;
        }
    }

    SC_CTOR(SwitchStmUnit) {
        SC_METHOD(assig_process_out);
        sensitive << a << b << c << sel;
    }
};
