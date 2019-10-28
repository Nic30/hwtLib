#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr


def LeadingZero():
    t = Bits(64)
    resT = Bits(8)
    n = RtlNetlist()

    s_in = n.sig("s_in", t)
    index = n.sig("s_indexOfFirstZero", resT)

    leadingZeroTop = None  # index is index of first empty record or last one
    for i in reversed(range(8)):
        connections = index(i)
        if leadingZeroTop is None:
            leadingZeroTop = connections 
        else:
            leadingZeroTop = If(s_in[i]._eq(0),
               connections
            ).Else(
               leadingZeroTop
            )

    interf = [s_in, index]

    return n, interf

leadingZeroExpected = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY LeadingZero IS
    PORT (s_in: IN STD_LOGIC_VECTOR(63 DOWNTO 0);
        s_indexOfFirstZero: OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF LeadingZero IS
BEGIN
    assig_process_s_indexOfFirstZero: PROCESS (s_in)
    BEGIN
        IF s_in(0) = '0' THEN
            s_indexOfFirstZero <= X"00";
        ELSIF s_in(1) = '0' THEN
            s_indexOfFirstZero <= X"01";
        ELSIF s_in(2) = '0' THEN
            s_indexOfFirstZero <= X"02";
        ELSIF s_in(3) = '0' THEN
            s_indexOfFirstZero <= X"03";
        ELSIF s_in(4) = '0' THEN
            s_indexOfFirstZero <= X"04";
        ELSIF s_in(5) = '0' THEN
            s_indexOfFirstZero <= X"05";
        ELSIF s_in(6) = '0' THEN
            s_indexOfFirstZero <= X"06";
        ELSE
            s_indexOfFirstZero <= X"07";
        END IF;
    END PROCESS;

END ARCHITECTURE;"""

if __name__ == "__main__":
    netlist, interfaces = LeadingZero()
    print(netlistToVhdlStr("LeadingZero", netlist, interfaces))
