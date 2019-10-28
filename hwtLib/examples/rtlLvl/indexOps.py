#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.typeShortcuts import vec
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr
from hwt.hdl.types.bits import Bits


def IndexOps():
    t = Bits(8)
    n = RtlNetlist()

    s_in = n.sig("s_in", t)
    s_out = n.sig("s_out", t)

    s_in2 = n.sig("s_in2", t)
    s_out2 = n.sig("s_out2", t)

    s_in3 = n.sig("s_in3", Bits(16))
    s_out3 = n.sig("s_out3", t)

    s_in4a = n.sig("s_in4a", t)
    s_in4b = n.sig("s_in4b", t)

    s_out4 = n.sig("s_out4", Bits(16))

    s_out(s_in[4:]._concat(vec(2, 4)))

    s_out2[4:](s_in2[4:])
    s_out2[:4](s_in2[:4])

    s_out3(s_in3[8:])

    s_out4[8:](s_in4a)
    s_out4[(8 + 8):8](s_in4b)

    interf = [s_in, s_out, s_in2, s_out2, s_in3, s_out3, s_in4a, s_in4b, s_out4]

    return n, interf

indexOpsExpected = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY IndexOps IS
    PORT (s_in: IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_in2: IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_in3: IN STD_LOGIC_VECTOR(15 DOWNTO 0);
        s_in4a: IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_in4b: IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out: OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out2: OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out3: OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out4: OUT STD_LOGIC_VECTOR(15 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF IndexOps IS
BEGIN
    s_out <= s_in(3 DOWNTO 0) & X"2";
    s_out2(3 DOWNTO 0) <= s_in2(3 DOWNTO 0);
    s_out2(7 DOWNTO 4) <= s_in2(7 DOWNTO 4);
    s_out3 <= s_in3(7 DOWNTO 0);
    s_out4(7 DOWNTO 0) <= s_in4a;
    s_out4(15 DOWNTO 8) <= s_in4b;
END ARCHITECTURE;"""

if __name__ == "__main__":
    netlist, interfaces = IndexOps()
    print(netlistToVhdlStr("IndexOps", netlist, interfaces))