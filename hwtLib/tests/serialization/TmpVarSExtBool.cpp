#include <systemc.h>

SC_MODULE(TmpVarSExtBool) {
    // ports
    sc_in<sc_uint<8>> a;
    sc_in<sc_uint<8>> b;
    sc_out<sc_uint<1>> o0;
    sc_out<sc_uint<2>> o0_2b;
    sc_out<sc_int<2>> o0_2b_s;
    sc_out<sc_uint<2>> o0_2b_u;
    sc_out<sc_uint<3>> o0_3b;
    sc_out<sc_int<3>> o0_3b_s;
    sc_out<sc_uint<3>> o0_3b_u;
    // component instances
    // internal signals
    void assig_process_o0() {
        o0.write(a.read() < b.read());
    }

    void assig_process_o0_2b() {
        o0_2b.write(static_cast<sc_uint<2>>(static_cast<sc_int<1>>(a.read() < b.read())));
    }

    void assig_process_o0_2b_s() {
        o0_2b_s.write(static_cast<sc_int<2>>(static_cast<sc_uint<2>>(static_cast<sc_int<1>>(a.read() < b.read()))));
    }

    void assig_process_o0_2b_u() {
        o0_2b_u.write(static_cast<sc_uint<2>>(static_cast<sc_uint<2>>(static_cast<sc_int<1>>(a.read() < b.read()))));
    }

    void assig_process_o0_3b() {
        o0_3b.write(static_cast<sc_uint<3>>(static_cast<sc_int<1>>(a.read() < b.read())));
    }

    void assig_process_o0_3b_s() {
        o0_3b_s.write(static_cast<sc_int<3>>(static_cast<sc_uint<3>>(static_cast<sc_int<1>>(a.read() < b.read()))));
    }

    void assig_process_o0_3b_u() {
        o0_3b_u.write(static_cast<sc_uint<3>>(static_cast<sc_uint<3>>(static_cast<sc_int<1>>(a.read() < b.read()))));
    }

    SC_CTOR(TmpVarSExtBool) {
        SC_METHOD(assig_process_o0);
        sensitive << a << b;
        SC_METHOD(assig_process_o0_2b);
        sensitive << a << b;
        SC_METHOD(assig_process_o0_2b_s);
        sensitive << a << b;
        SC_METHOD(assig_process_o0_2b_u);
        sensitive << a << b;
        SC_METHOD(assig_process_o0_3b);
        sensitive << a << b;
        SC_METHOD(assig_process_o0_3b_s);
        sensitive << a << b;
        SC_METHOD(assig_process_o0_3b_u);
        sensitive << a << b;
        // connect ports
    }
};
