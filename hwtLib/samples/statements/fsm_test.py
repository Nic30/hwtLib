#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from hwt.hdlObjects.constants import Time
from hwt.simulator.agentConnector import agInts
from hwtLib.samples.statements.fsm import FsmExample, HadrcodedFsmExample
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.shortcuts import toRtl
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.systemC.serializer import SystemCSerializer

fsmExample_verilog = """module FsmExample(input a,
        input b,
        input clk,
        output reg [2:0] dout,
        input rst_n
    );

    reg [1:0] st = 0;
    reg [1:0] st_next;
    always @(st) begin: assig_process_dout
        case(st)
        0:
            dout <= 3'b001;
        1:
            dout <= 3'b010;
        default:
            dout <= 3'b011;
        endcase
    end

    always @(posedge clk) begin: assig_process_st
        if(rst_n == 1'b0) begin
            st <= 0;
        end else begin
            st <= st_next;
        end
    end

    always @(a or b or st) begin: assig_process_st_next
        st_next <= st;
        case(st)
        0:
            if((a & b)==1'b1) begin
                st_next <= 2;
            end else if((b)==1'b1) begin
                st_next <= 1;
            end
        1:
            if((a & b)==1'b1) begin
                st_next <= 2;
            end else if((a)==1'b1) begin
                st_next <= 0;
            end
        default:
            if((a & (~b))==1'b1) begin
                st_next <= 0;
            end else if(((~a) & b)==1'b1) begin
                st_next <= 1;
            end
        endcase
    end

endmodule"""

fsmExample_systemc= """#include <systemc.h>


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
        if(rst_n.read() == '0') {
            st = 0;
        } else {
            st = st_next.read();
        }
    }
    void assig_process_st_next() {
        st_next.write(st);
        switch(st) {
        case 0:
            if(a.read() & b.read() == '1') {
                st_next.write(2);
            } else if(b.read() == '1') {
                st_next.write(1);
            }
            break;
        case 1:
            if(a.read() & b.read() == '1') {
                st_next.write(2);
            } else if(a.read() == '1') {
                st_next.write(0);
            }
            break;
        default:
            if(a.read() & (~b.read()) == '1') {
                st_next.write(0);
            } else if((~a.read()) & b.read() == '1') {
                st_next.write(1);
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
};"""


class FsmExampleTC(SimTestCase):
    def setUp(self):
        super(FsmExampleTC, self).setUp()
        self.u = FsmExample()
        self.prepareUnit(self.u)

    def test_allCases(self):
        u = self.u

        u.a._ag.data.extend([1, 1, 1, 0, 0, 0, 0, 0])
        u.b._ag.data.extend([0, 1, 0, 0, 1, 0, 1, 0])

        self.doSim(80 * Time.ns)

        self.assertSequenceEqual([1, 1, 3, 1, 1, 2, 2, 2], agInts(u.dout))

    def test_verilog(self):
        s = toRtl(FsmExample(), serializer=VerilogSerializer)
        self.assertEqual(s, fsmExample_verilog)

    def test_systemc(self):
        s = toRtl(FsmExample(), serializer=SystemCSerializer)
        self.assertEqual(s, fsmExample_systemc)


class HadrcodedFsmExampleTC(FsmExampleTC):
    def setUp(self):
        SimTestCase.setUp(self)
        self.u = HadrcodedFsmExample()
        self.prepareUnit(self.u)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(FsmExampleTC))
    suite.addTest(unittest.makeSuite(HadrcodedFsmExampleTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
