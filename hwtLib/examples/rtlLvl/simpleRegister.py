#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.bits import Bits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr


def SimpleRegister():
    t = Bits(8)

    n = RtlNetlist()

    s_out = n.sig("s_out", t)
    s_in = n.sig("s_in", t)
    clk = n.sig("clk")
    syncRst = n.sig("rst")

    val = n.sig("val", t, clk, syncRst, 0)
    val(s_in)
    s_out(val)

    interf = [clk, syncRst, s_in, s_out]
    return n, interf


simpleRegisterExpected = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleRegister IS
    PORT (clk: IN STD_LOGIC;
        rst: IN STD_LOGIC;
        s_in: IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out: OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleRegister IS
    SIGNAL val: STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL val_next: STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    s_out <= val;
    assig_process_val: PROCESS (clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                val <= X"00";
            ELSE
                val <= val_next;
            END IF;
        END IF;
    END PROCESS;

    val_next <= s_in;
END ARCHITECTURE;"""

if __name__ == "__main__":
    netlist, interfaces = SimpleRegister()
    print(netlistToVhdlStr("SimpleRegister", netlist, interfaces))
