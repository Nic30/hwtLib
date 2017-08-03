#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.simulator.agentConnector import agInts
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.shortcuts import toRtl
from hwtLib.samples.statements.switchStm import SwitchStmUnit


switchStm_vhdl = """--
--    Example which is using switch statement to create multiplexer
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SwitchStmUnit IS
    PORT (a: IN STD_LOGIC;
        b: IN STD_LOGIC;
        c: IN STD_LOGIC;
        out_0: OUT STD_LOGIC;
        sel: IN STD_LOGIC_VECTOR(2 DOWNTO 0)
    );
END SwitchStmUnit;

ARCHITECTURE rtl OF SwitchStmUnit IS
BEGIN
    assig_process_out: PROCESS (a, b, c, sel)
    BEGIN
        CASE sel IS
        WHEN "000" =>
            out_0 <= a;
        WHEN "001" =>
            out_0 <= b;
        WHEN "010" =>
            out_0 <= c;
        WHEN OTHERS =>
            out_0 <= '0';
        END CASE;
    END PROCESS;

END ARCHITECTURE rtl;"""

switchStm_verilog = """/*

    Example which is using switch statement to create multiplexer
    
*/
module SwitchStmUnit(input a,
        input b,
        input c,
        output reg out,
        input [2:0] sel
    );

    always @(a or b or c or sel) begin: assig_process_out
        case(sel)
        3'b000:
            out <= a;
        3'b001:
            out <= b;
        3'b010:
            out <= c;
        default:
            out <= 1'b0;
        endcase
    end

endmodule"""

switchStm_systemc = """/*

    Example which is using switch statement to create multiplexer
    
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
            out.write('0');
            break;
        }
    }

    SC_CTOR(SwitchStmUnit) {
        SC_METHOD(assig_process_out);
        sensitive << a << b << c << sel;
    }
};"""


class SwitchStmTC(SimTestCase):
    def test_allCases(self):
        self.u = SwitchStmUnit()
        self.prepareUnit(self.u)

        u = self.u
        u.sel._ag.data.extend([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 1])
        u.a._ag.data.extend([0, 1, 0, 0, 0, 0, 0, 0, 1, None, 0])
        u.b._ag.data.extend([0, 0, 0, 1, 0, 0, 0, 0, 1, None, 0])
        u.c._ag.data.extend([0, 0, 0, 0, 0, 1, 0, 0, 1, None, 0])

        self.doSim(200 * Time.ns)

        self.assertSequenceEqual([0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0], agInts(u.out))

    def test_vhdlSerialization(self):
        u = SwitchStmUnit()
        s = toRtl(u, serializer=VhdlSerializer)
        self.assertEqual(s, switchStm_vhdl)

    def test_verilogSerialization(self):
        u = SwitchStmUnit()
        s = toRtl(u, serializer=VerilogSerializer)
        self.assertEqual(s, switchStm_verilog)

    def test_systemcSerialization(self):
        u = SwitchStmUnit()
        s = toRtl(u, serializer=SystemCSerializer)
        self.assertEqual(s, switchStm_systemc)

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TwoCntrsTC('test_nothingEnable'))
    suite.addTest(unittest.makeSuite(SwitchStmTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
