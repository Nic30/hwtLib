#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr


def SimpleEnum():
    t = Bits(8)
    fsmT = HEnum('fsmT', ['send0', 'send1'])

    n = RtlNetlist()

    s_out = n.sig("s_out", t)
    s_in0 = n.sig("s_in0", t)
    s_in1 = n.sig("s_in1", t)
    clk = n.sig("clk")
    syncRst = n.sig("rst")

    fsmSt = n.sig("fsmSt", fsmT, clk, syncRst, fsmT.send0)
    If(fsmSt._eq(fsmT.send0),
        s_out(s_in0),
        fsmSt(fsmT.send1),
    ).Else(
        s_out(s_in1),
        fsmSt(fsmT.send0)
    )

    interf = [clk, syncRst, s_in0, s_in1, s_out]
    return n, interf


simpleEnumExpected = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleEnum IS
    PORT (clk: IN STD_LOGIC;
        rst: IN STD_LOGIC;
        s_in0: IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_in1: IN STD_LOGIC_VECTOR(7 DOWNTO 0);
        s_out: OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleEnum IS
    TYPE FSMT IS (send0, send1);
    SIGNAL fsmSt: fsmT := send0;
    SIGNAL fsmSt_next: fsmT;
BEGIN
    assig_process_fsmSt: PROCESS (clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                fsmSt <= send0;
            ELSE
                fsmSt <= fsmSt_next;
            END IF;
        END IF;
    END PROCESS;

    assig_process_fsmSt_next: PROCESS (fsmSt, s_in0, s_in1)
    BEGIN
        IF fsmSt = send0 THEN
            s_out <= s_in0;
            fsmSt_next <= send1;
        ELSE
            s_out <= s_in1;
            fsmSt_next <= send0;
        END IF;
    END PROCESS;

END ARCHITECTURE;"""


if __name__ == "__main__":
    netlist, interfaces = SimpleEnum()
    print(netlistToVhdlStr("SimpleEnum", netlist, interfaces))
