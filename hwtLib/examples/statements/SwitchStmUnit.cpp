#include <systemc.h>

//
//    Example which is using switch statement to create multiplexer
//
//    .. hwt-autodoc::
//    
SC_MODULE(SwitchStmUnit) {
    // ports
    sc_in<sc_uint<1>> a;
    sc_in<sc_uint<1>> b;
    sc_in<sc_uint<1>> c;
    sc_out<sc_uint<1>> out;
    sc_in<sc_uint<3>> sel;
    // component instances
    // internal signals
    void assig_process_out() {
        switch(sel.read()) {
        case sc_uint<3>("0b000"): {
                out.write(a.read());
                break;
            }
        case sc_uint<3>("0b001"): {
                out.write(b.read());
                break;
            }
        case sc_uint<3>("0b010"): {
                out.write(c.read());
                break;
            }
        default:
                out.write(sc_uint<1>("0b0"));
        }
    }

    SC_CTOR(SwitchStmUnit) {
        SC_METHOD(assig_process_out);
        sensitive << a << b << c << sel;
        // connect ports
    }
};
