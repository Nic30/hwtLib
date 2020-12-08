#include <systemc.h>

//
//    Every HW component class has to be derived from Unit class
//
//    .. hwt-autodoc::
//    
SC_MODULE(Showcase0) {
    // ports
    sc_in<sc_uint<32>> a;
    sc_in<sc_int<32>> b;
    sc_out<sc_uint<32>> c;
    sc_in_clk clk;
    sc_out<sc_uint<1>> cmp_0;
    sc_out<sc_uint<1>> cmp_1;
    sc_out<sc_uint<1>> cmp_2;
    sc_out<sc_uint<1>> cmp_3;
    sc_out<sc_uint<1>> cmp_4;
    sc_out<sc_uint<1>> cmp_5;
    sc_out<sc_uint<32>> contOut;
    sc_in<sc_uint<32>> d;
    sc_in<sc_uint<1>> e;
    sc_out<sc_uint<1>> f;
    sc_out<sc_uint<16>> fitted;
    sc_out<sc_uint<8>> g;
    sc_out<sc_uint<8>> h;
    sc_in<sc_uint<2>> i;
    sc_out<sc_uint<8>> j;
    sc_out<sc_uint<32>> k;
    sc_out<sc_uint<1>> out;
    sc_out<sc_uint<1>> output;
    sc_in<sc_uint<1>> rst_n;
    sc_out<sc_uint<8>> sc_signal_0;
    // component instances
    // internal signals
    sc_uint<32> const_private_signal = sc_uint<32>("0x0000007B");
    sc_int<8> fallingEdgeRam[4];
    sc_uint<1> r = sc_uint<1>("0b0");
    sc_uint<2> r_0 = sc_uint<2>("0b00");
    sc_uint<2> r_1 = sc_uint<2>("0b00");
    sc_signal<sc_uint<1>> r_next;
    sc_signal<sc_uint<2>> r_next_0;
    sc_signal<sc_uint<2>> r_next_1;
    sc_uint<8> rom[4] = {sc_uint<8>("0x00"), 
        sc_uint<8>("0x01"), 
        sc_uint<8>("0x02"), 
        sc_uint<8>("0x03"), 
        };
    void assig_process_c() {
        c.write(static_cast<sc_uint<32>>(a.read() + static_cast<sc_uint<32>>(b.read())));
    }

    void assig_process_cmp_0() {
        cmp_0.write(a.read() < sc_uint<32>("0x00000004"));
    }

    void assig_process_cmp_1() {
        cmp_1.write(a.read() > sc_uint<32>("0x00000004"));
    }

    void assig_process_cmp_2() {
        cmp_2.write(b.read() <= sc_int<32>("0x00000004"));
    }

    void assig_process_cmp_3() {
        cmp_3.write(b.read() >= sc_int<32>("0x00000004"));
    }

    void assig_process_cmp_4() {
        cmp_4.write(b.read() != sc_int<32>("0x00000004"));
    }

    void assig_process_cmp_5() {
        cmp_5.write(b.read() == sc_int<32>("0x00000004"));
    }

    void assig_process_contOut() {
        contOut.write(static_cast<sc_uint<32>>(const_private_signal));
    }

    void assig_process_f() {
        f.write(r);
    }

    void assig_process_fallingEdgeRam() {
        sc_signal<sc_uint<32>> tmpConcat_0;
        tmpConcat_0.write((sc_uint<24>("0x000000"), static_cast<sc_uint<8>>(static_cast<sc_uint<8>>(fallingEdgeRam[r_1])), ));
        {
            (fallingEdgeRam[r_1]).write(static_cast<sc_int<8>>(a.read().range(sc_int<32>("0x00000008"), sc_int<32>("0x00000000"))));
            k = tmpConcat_0.read();
        }
    }

    void assig_process_fitted() {
        fitted.write(static_cast<sc_uint<16>>(a.read().range(sc_int<32>("0x00000010"), sc_int<32>("0x00000000"))));
    }

    void assig_process_g() {
        sc_signal<sc_uint<8>> tmpConcat_0;
        sc_signal<sc_uint<2>> tmpConcat_1;
        tmpConcat_0.write((tmpConcat_1.read(), static_cast<sc_uint<6>>(a.read().range(sc_int<32>("0x00000006"), sc_int<32>("0x00000000"))), ));
        tmpConcat_1.write((a.read()[sc_int<32>("0x00000001")] & b.read()[sc_int<32>("0x00000001")], a.read()[sc_int<32>("0x00000000")] ^ b.read()[sc_int<32>("0x00000000")] | a.read()[sc_int<32>("0x00000001")], ));
        g.write(tmpConcat_0.read());
    }

    void assig_process_h() {
        if (a.read()[sc_int<32>("0x00000002")] == sc_uint<1>("0b1"))
            if (r == sc_uint<1>("0b1"))
                h.write(sc_uint<8>("0x00"));
            else if (a.read()[sc_int<32>("0x00000001")] == sc_uint<1>("0b1"))
                h.write(sc_uint<8>("0x01"));
            else
                h.write(sc_uint<8>("0x02"));
    }

    void assig_process_j() {
        j = static_cast<sc_uint<8>>(rom[r_1]);
    }

    void assig_process_out() {
        out.write(sc_uint<1>("0b0"));
    }

    void assig_process_output() {
        output.write(sc_uint<1>("0bX"));
    }

    void assig_process_r() {
        if (rst_n.read() == sc_uint<1>("0b0")) {
            r_1 = sc_uint<2>("0b00");
            r_0 = sc_uint<2>("0b00");
            r = sc_uint<1>("0b0");
        } else {
            r_1 = r_next_1.read();
            r_0 = r_next_0.read();
            r = r_next.read();
        }
    }

    void assig_process_r_next() {
        r_next_0.write(i.read());
    }

    void assig_process_r_next_0() {
        r_next_1.write(r_0);
    }

    void assig_process_r_next_1() {
        if (~r == sc_uint<1>("0b1"))
            r_next.write(e.read());
        else
            r_next.write(r);
    }

    void assig_process_sc_signal_0() {
        switch(a.read()) {
        case sc_uint<32>("0x00000001"): {
                sc_signal_0.write(sc_uint<8>("0x00"));
                break;
            }
        case sc_uint<32>("0x00000002"): {
                sc_signal_0.write(sc_uint<8>("0x01"));
                break;
            }
        case sc_uint<32>("0x00000003"): {
                sc_signal_0.write(sc_uint<8>("0x03"));
                break;
            }
        default:
                sc_signal_0.write(sc_uint<8>("0x04"));
        }
    }

    SC_CTOR(Showcase0) {
        SC_METHOD(assig_process_c);
        sensitive << a << b;
        SC_METHOD(assig_process_cmp_0);
        sensitive << a;
        SC_METHOD(assig_process_cmp_1);
        sensitive << a;
        SC_METHOD(assig_process_cmp_2);
        sensitive << b;
        SC_METHOD(assig_process_cmp_3);
        sensitive << b;
        SC_METHOD(assig_process_cmp_4);
        sensitive << b;
        SC_METHOD(assig_process_cmp_5);
        sensitive << b;
        assig_process_contOut();
        SC_METHOD(assig_process_f);
        sensitive << r;
        SC_METHOD(assig_process_fallingEdgeRam);
        sensitive << clk.neg();
        SC_METHOD(assig_process_fitted);
        sensitive << a;
        SC_METHOD(assig_process_g);
        sensitive << a << b;
        SC_METHOD(assig_process_h);
        sensitive << a << r;
        SC_METHOD(assig_process_j);
        sensitive << clk.pos();
        assig_process_out();
        assig_process_output();
        SC_METHOD(assig_process_r);
        sensitive << clk.pos();
        SC_METHOD(assig_process_r_next);
        sensitive << i;
        SC_METHOD(assig_process_r_next_0);
        sensitive << r_0;
        SC_METHOD(assig_process_r_next_1);
        sensitive << e << r;
        SC_METHOD(assig_process_sc_signal_0);
        sensitive << a;
        // connect ports
    }
};
