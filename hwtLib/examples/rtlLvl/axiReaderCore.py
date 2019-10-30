#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.enum import HEnum
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr


def AxiReaderCore():
    n = RtlNetlist()
    rSt_t = HEnum('rSt_t', ['rdIdle', 'rdData'])

    rSt = n.sig('rSt', rSt_t)
    arRd = n.sig('arRd')
    arVld = n.sig('arVld')
    rVld = n.sig('rVld')
    rRd = n.sig('rRd')

    # ar fsm next
    If(arRd,
       # rdIdle
        If(arVld,
           rSt(rSt_t.rdData)
        ).Else(
           rSt(rSt_t.rdIdle)
        )
    ).Else(
        # rdData
        If(rRd & rVld,
           rSt(rSt_t.rdIdle)
        ).Else(
           rSt(rSt_t.rdData)
        )
    )

    return n, [rSt, arRd, arVld, rVld, rRd]

axiReaderCoreExpected = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY AxiReaderCore IS
    PORT (arRd: IN STD_LOGIC;
        arVld: IN STD_LOGIC;
        rRd: IN STD_LOGIC;
        rSt: OUT rSt_t;
        rVld: IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF AxiReaderCore IS
BEGIN
    assig_process_rSt: PROCESS (arRd, arVld, rRd, rVld)
    BEGIN
        IF arRd = '1' THEN
            IF arVld = '1' THEN
                rSt <= rdData;
            ELSE
                rSt <= rdIdle;
            END IF;
        ELSIF (rRd AND rVld) = '1' THEN
            rSt <= rdIdle;
        ELSE
            rSt <= rdData;
        END IF;
    END PROCESS;

END ARCHITECTURE;"""

if __name__ == "__main__":
    netlist, interfaces = AxiReaderCore()
    print(netlistToVhdlStr("AxiReaderCore", netlist, interfaces))
