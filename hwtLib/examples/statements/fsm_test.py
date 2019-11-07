#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from hwt.hdl.constants import Time
from hwtLib.examples.statements.fsm import FsmExample, HadrcodedFsmExample
from hwt.simulator.simTestCase import SimTestCase, SingleUnitSimTestCase
from hwt.synthesizer.utils import toRtl
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer

fsmExample_vhdl = """--
--    .. hwt-schematic::
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY FsmExample IS
    PORT (a: IN STD_LOGIC;
        b: IN STD_LOGIC;
        clk: IN STD_LOGIC;
        dout: OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
        rst_n: IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF FsmExample IS
    TYPE ST_T IS (a_0, b_0, aAndB);
    SIGNAL st: st_t := a_0;
    SIGNAL st_next: st_t;
BEGIN
    assig_process_dout: PROCESS (st)
    BEGIN
        CASE st IS
        WHEN a_0 =>
            dout <= "001";
        WHEN b_0 =>
            dout <= "010";
        WHEN OTHERS =>
            dout <= "011";
        END CASE;
    END PROCESS;

    assig_process_st: PROCESS (clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst_n = '0' THEN
                st <= a_0;
            ELSE
                st <= st_next;
            END IF;
        END IF;
    END PROCESS;

    assig_process_st_next: PROCESS (a, b, st)
    BEGIN
        CASE st IS
        WHEN a_0 =>
            IF (a AND b) = '1' THEN
                st_next <= aAndB;
            ELSIF b = '1' THEN
                st_next <= b_0;
            ELSE
                st_next <= st;
            END IF;
        WHEN b_0 =>
            IF (a AND b) = '1' THEN
                st_next <= aAndB;
            ELSIF a = '1' THEN
                st_next <= a_0;
            ELSE
                st_next <= st;
            END IF;
        WHEN OTHERS =>
            IF (a AND NOT b) = '1' THEN
                st_next <= a_0;
            ELSIF (NOT a AND b) = '1' THEN
                st_next <= b_0;
            ELSE
                st_next <= st;
            END IF;
        END CASE;
    END PROCESS;

END ARCHITECTURE;"""

fsmExample_verilog = """/*

    .. hwt-schematic::
    
*/
module FsmExample(input a,
        input b,
        input clk,
        output reg [2:0] dout,
        input rst_n
    );

    reg [1:0] st = 0;
    reg [1:0] st_next;
    always @(st) begin: assig_process_dout
        case(st)
        0: begin
            dout = 3'b001;
        end
        1: begin
            dout = 3'b010;
        end
        default: begin
            dout = 3'b011;
        end
        endcase
    end

    always @(posedge clk) begin: assig_process_st
        if (rst_n == 1'b0) begin
            st <= 0;
        end else begin
            st <= st_next;
        end
    end

    always @(a or b or st) begin: assig_process_st_next
        case(st)
        0: begin
            if (a & b) begin
                st_next = 2;
            end else if (b) begin
                st_next = 1;
            end else begin
                st_next = st;
            end
        end
        1: begin
            if (a & b) begin
                st_next = 2;
            end else if (a) begin
                st_next = 0;
            end else begin
                st_next = st;
            end
        end
        default: begin
            if (a & ~b) begin
                st_next = 0;
            end else if (~a & b) begin
                st_next = 1;
            end else begin
                st_next = st;
            end
        end
        endcase
    end

endmodule"""

fsmExample_systemc = """/*

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
};"""


class FsmExampleTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = FsmExample()
        return cls.u

    def test_allCases(self):
        u = self.u

        u.a._ag.data.extend([1, 1, 1, 0, 0, 0, 0, 0])
        u.b._ag.data.extend([0, 1, 0, 0, 1, 0, 1, 0])

        self.runSim(90 * Time.ns)

        self.assertValSequenceEqual(u.dout._ag.data,
                                    [1, 1, 3, 1, 1, 2, 2, 2])


class HadrcodedFsmExampleTC(FsmExampleTC):

    @classmethod
    def getUnit(cls):
        cls.u = HadrcodedFsmExample()
        return cls.u


class FsmSerializationTC(unittest.TestCase):

    def test_vhdl(self):
        s = toRtl(FsmExample(), serializer=VhdlSerializer)
        self.assertEqual(s, fsmExample_vhdl)

    def test_verilog(self):
        s = toRtl(FsmExample(), serializer=VerilogSerializer)
        self.assertEqual(s, fsmExample_verilog)

    def test_systemc(self):
        s = toRtl(FsmExample(), serializer=SystemCSerializer)
        self.assertEqual(s, fsmExample_systemc)


if __name__ == "__main__":

    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(FsmExampleTC))
    suite.addTest(unittest.makeSuite(HadrcodedFsmExampleTC))
    suite.addTest(unittest.makeSuite(FsmSerializationTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
