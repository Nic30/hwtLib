/*

    .. hwt-schematic::

*/

#include <systemc.h>


SC_MODULE(FsmExample) {
    //interfaces
    sc_in<sc_uint<1>> a;
    sc_in<sc_uint<1>> b;
    sc_in_clk clk;
    sc_out<sc_uint<3>> dout;
    sc_in<sc_uint<1>> rst_n;

    //internal signals
    sc_uint<2> st = 0;
    sc_signal<sc_uint<2>> st_next;

    //processes inside this component
    void assig_process_dout() {
        switch(st) {
        case 0:
            dout.write(sc_uint<3>("001"));
            break;
        case 1:
            dout.write(sc_uint<3>("010"));
            break;
        default:
            dout.write(sc_uint<3>("011"));
            break;
        }
    }
    void assig_process_st() {
        if (rst_n.read() == 0) {
            st = 0;
        } else {
            st = st_next.read();
        }
    }
    void assig_process_st_next() {
        switch(st) {
        case 0:
            if ((a.read() & b.read()) == 1) {
                st_next.write(2);
            } else if (b.read() == 1) {
                st_next.write(1);
            } else {
                st_next.write(st);
            }
            break;
        case 1:
            if ((a.read() & b.read()) == 1) {
                st_next.write(2);
            } else if (a.read() == 1) {
                st_next.write(0);
            } else {
                st_next.write(st);
            }
            break;
        default:
            if ((a.read() & ~b.read()) == 1) {
                st_next.write(0);
            } else if ((~a.read() & b.read()) == 1) {
                st_next.write(1);
            } else {
                st_next.write(st);
            }
            break;
        }
    }

    SC_CTOR(FsmExample) {
        SC_METHOD(assig_process_dout);
        sensitive << st;
        SC_METHOD(assig_process_st);
        sensitive << clk.pos();
        SC_METHOD(assig_process_st_next);
        sensitive << a << b << st;
    }
};
