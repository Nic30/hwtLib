#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch
from hwt.hdl.types.bits import Bits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr


def SwitchStatement():
    t = Bits(8)
    n = RtlNetlist()

    In = n.sig("input", t, def_val=8)
    Out = n.sig("output", t)

    Switch(In).addCases(
        [(i, Out(i + 1)) for i in range(8)]
    )

    interf = [In, Out]
    return n, interf

switchStatementExpected = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SwitchStatement IS
    PORT (input: IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        output: OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SwitchStatement IS
BEGIN

    assig_process_output: PROCESS (input)
    BEGIN
        CASE input IS
        WHEN X"00" =>
            output <= X"01";
        WHEN X"01" =>
            output <= X"02";
        WHEN X"02" =>
            output <= X"03";
        WHEN X"03" =>
            output <= X"04";
        WHEN X"04" =>
            output <= X"05";
        WHEN X"05" =>
            output <= X"06";
        WHEN X"06" =>
            output <= X"07";
        WHEN X"07" =>
            output <= X"08";
        END CASE;
    END PROCESS;

END ARCHITECTURE;"""

if __name__ == "__main__":
    netlist, interfaces = SwitchStatement()
    print(netlistToVhdlStr("SwitchStatement", netlist, interfaces))
