#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdlObjects.constants import Time
from hwt.serializer.systemC.serializer import SystemCSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.simulator.agentConnector import agInts
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.shortcuts import toRtl
from hwtLib.samples.mem.reg import DReg, DoubleDReg, OptimizedOutReg,\
    AsyncResetReg, DDR_Reg


dreg_vhdl = """--
--    Basic d flip flop
--
--    :attention: using this unit is pointless because HWToolkit can automatically
--        generate such a register for any interface and datatype
--    
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY DReg IS
    PORT (clk: IN STD_LOGIC;
        din: IN STD_LOGIC;
        dout: OUT STD_LOGIC;
        rst: IN STD_LOGIC
    );
END DReg;

ARCHITECTURE rtl OF DReg IS
    SIGNAL internReg: STD_LOGIC := '0';
    SIGNAL internReg_next: STD_LOGIC;
BEGIN
    dout <= internReg;
    assig_process_internReg: PROCESS (clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                internReg <= '0';
            ELSE
                internReg <= internReg_next;
            END IF;
        END IF;
    END PROCESS;

    internReg_next <= din;
END ARCHITECTURE rtl;"""

dreg_verilog = """/*

    Basic d flip flop

    :attention: using this unit is pointless because HWToolkit can automatically
        generate such a register for any interface and datatype
    
*/
module DReg(input clk,
        input din,
        output dout,
        input rst
    );

    reg internReg = 1'b0;
    wire internReg_next;
    assign dout = internReg;
    always @(posedge clk) begin: assig_process_internReg
        if(rst == 1'b1) begin
            internReg <= 1'b0;
        end else begin
            internReg <= internReg_next;
        end
    end

    assign internReg_next = din;
endmodule"""


dreg_systemc = """/*

    Basic d flip flop

    :attention: using this unit is pointless because HWToolkit can automatically
        generate such a register for any interface and datatype
    
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
};"""

asyncResetReg_verilog = """module AsyncResetReg(input clk,
        input din,
        output dout,
        input rst
    );

    reg internReg = 1'b0;
    assign dout = internReg;
    always @(posedge clk or posedge rst) begin: assig_process_internReg
        if(rst == 1'b1) begin
            internReg <= 1'b0;
        end else begin
            internReg <= din;
        end
    end

endmodule"""

asyncResetReg_vhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY AsyncResetReg IS
    PORT (clk: IN STD_LOGIC;
        din: IN STD_LOGIC;
        dout: OUT STD_LOGIC;
        rst: IN STD_LOGIC
    );
END AsyncResetReg;

ARCHITECTURE rtl OF AsyncResetReg IS
    SIGNAL internReg: STD_LOGIC := '0';
BEGIN
    dout <= internReg;
    assig_process_internReg: PROCESS (clk, rst)
    BEGIN
        IF rst = '1' THEN
            internReg <= '0';
        ELSIF RISING_EDGE(clk) THEN
            internReg <= din;
        END IF;
    END PROCESS;

END ARCHITECTURE rtl;"""


ddr_reg_vhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY DDR_Reg IS
    PORT (clk: IN STD_LOGIC;
        din: IN STD_LOGIC;
        dout: OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
        rst: IN STD_LOGIC
    );
END DDR_Reg;

ARCHITECTURE rtl OF DDR_Reg IS
    SIGNAL internReg: STD_LOGIC := '0';
    SIGNAL internReg_0: STD_LOGIC := '0';
BEGIN
    dout <= internReg & internReg_0;
    assig_process_internReg: PROCESS (clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            internReg <= din;
        END IF;
    END PROCESS;

    assig_process_internReg_0: PROCESS (clk)
    BEGIN
        IF FALLING_EDGE(clk) THEN
            internReg_0 <= din;
        END IF;
    END PROCESS;

END ARCHITECTURE rtl;"""

ddr_reg_verilog = """module DDR_Reg(input clk,
        input din,
        output [1:0] dout,
        input rst
    );

    reg internReg = 1'b0;
    reg internReg_0 = 1'b0;
    assign dout = {internReg, internReg_0};
    always @(posedge clk) begin: assig_process_internReg
        internReg <= din;
    end

    always @(negedge clk) begin: assig_process_internReg_0
        internReg_0 <= din;
    end

endmodule"""


class DRegTC(SimTestCase):
    def setUpUnit(self, u):
        self.u, self.model, self.procs = simPrepare(u)

    def test_simple(self):
        self.setUpUnit(DReg())

        self.u.din._ag.data.extend([i % 2 for i in range(6)] + [None, None, 0, 1])
        expected = [0, 0, 1, 0, 1, 0, 1, None, None, 0]

        self.doSim(100 * Time.ns)
        recieved = agInts(self.u.dout)
        # check simulation results
        self.assertSequenceEqual(expected, recieved)

    def test_double(self):
        self.setUpUnit(DoubleDReg())

        self.u.din._ag.data.extend([i % 2 for i in range(6)] + [None, None, 0, 1])
        expected = [0, 0, 0, 1, 0, 1, 0, 1, None, None]

        self.doSim(100 * Time.ns)

        recieved = agInts(self.u.dout)

        # check simulation results
        self.assertSequenceEqual(expected, recieved)

    def test_optimizedOutReg(self):
        u = OptimizedOutReg()
        self.assertNotIn("unconnected", toRtl(u))

    def test_dreg_vhdl(self):
        s = toRtl(DReg(), serializer=VhdlSerializer)
        self.assertEqual(s, dreg_vhdl)

    def test_dreg_verilog(self):
        s = toRtl(DReg(), serializer=VerilogSerializer)
        self.assertEqual(s, dreg_verilog)

    def test_dreg_systemc(self):
        s = toRtl(DReg(), serializer=SystemCSerializer)
        self.assertEqual(s, dreg_systemc)

    def test_AsyncResetReg_vhdl(self):
        s = toRtl(AsyncResetReg(), serializer=VhdlSerializer)
        self.assertEqual(s, asyncResetReg_vhdl)

    def test_AsyncResetReg_verilog(self):
        s = toRtl(AsyncResetReg(), serializer=VerilogSerializer)
        self.assertEqual(s, asyncResetReg_verilog)

    def test_DDR_Reg_vhdl(self):
        s = toRtl(DDR_Reg(), serializer=VhdlSerializer)
        self.assertEqual(s, ddr_reg_vhdl)

    def test_DDR_Reg_verilog(self):
        s = toRtl(DDR_Reg(), serializer=VerilogSerializer)
        self.assertEqual(s, ddr_reg_verilog)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(DRegTC('test_optimizedOutReg'))
    suite.addTest(unittest.makeSuite(DRegTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
