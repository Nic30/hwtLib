#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch
from hwt.hdl.types.enum import HEnum
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr


def ComplexConditions():
    n = RtlNetlist()
    stT = HEnum('t_state', ["idle", "tsWait", "ts0Wait", "ts1Wait", "lenExtr"])
    clk = n.sig('clk')
    rst = n.sig("rst")

    st = n.sig('st', stT, clk=clk, syncRst=rst, def_val=stT.idle)
    s_idle = n.sig('s_idle')
    sd0 = n.sig('sd0')
    sd1 = n.sig('sd1')
    cntrlFifoVld = n.sig('ctrlFifoVld')
    cntrlFifoLast = n.sig('ctrlFifoLast')

    def tsWaitLogic(ifNoTsRd):
        return If(sd0 & sd1,
                   st(stT.lenExtr)
               ).Elif(sd0,
                   st(stT.ts1Wait)
               ).Elif(sd1,
                   st(stT.ts0Wait)
               ).Else(
                   ifNoTsRd
               )
    Switch(st)\
    .Case(stT.idle,
        tsWaitLogic(
            If(cntrlFifoVld,
               st(stT.tsWait)
            )
        )
    ).Case(stT.tsWait,
        tsWaitLogic(st(st))
    ).Case(stT.ts0Wait,
        If(sd0,
           st(stT.lenExtr)
        )
    ).Case(stT.ts1Wait,
        If(sd1,
           st(stT.lenExtr)
        )
    ).Case(stT.lenExtr,
        If(cntrlFifoVld & cntrlFifoLast,
           st(stT.idle)
        )
    )
    s_idle(st._eq(stT.idle))

    return n, [rst, clk, sd0, sd1, cntrlFifoVld, cntrlFifoLast, s_idle]


complexConditionsExpected = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY ComplexConditions IS
    PORT (clk: IN STD_LOGIC;
        ctrlFifoLast: IN STD_LOGIC;
        ctrlFifoVld: IN STD_LOGIC;
        rst: IN STD_LOGIC;
        s_idle: OUT STD_LOGIC;
        sd0: IN STD_LOGIC;
        sd1: IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF ComplexConditions IS
    TYPE T_STATE IS (idle, tsWait, ts0Wait, ts1Wait, lenExtr);
    SIGNAL st: t_state := idle;
    SIGNAL st_next: t_state;
BEGIN
    s_idle <= '1' WHEN st = idle ELSE '0';
    assig_process_st: PROCESS (clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                st <= idle;
            ELSE
                st <= st_next;
            END IF;
        END IF;
    END PROCESS;

    assig_process_st_next: PROCESS (ctrlFifoLast, ctrlFifoVld, sd0, sd1, st)
    BEGIN
        CASE st IS
        WHEN idle =>
            IF (sd0 AND sd1) = '1' THEN
                st_next <= lenExtr;
            ELSIF sd0 = '1' THEN
                st_next <= ts1Wait;
            ELSIF sd1 = '1' THEN
                st_next <= ts0Wait;
            ELSIF ctrlFifoVld = '1' THEN
                st_next <= tsWait;
            ELSE
                st_next <= st;
            END IF;
        WHEN tsWait =>
            IF (sd0 AND sd1) = '1' THEN
                st_next <= lenExtr;
            ELSIF sd0 = '1' THEN
                st_next <= ts1Wait;
            ELSIF sd1 = '1' THEN
                st_next <= ts0Wait;
            ELSE
                st_next <= st;
            END IF;
        WHEN ts0Wait =>
            IF sd0 = '1' THEN
                st_next <= lenExtr;
            ELSE
                st_next <= st;
            END IF;
        WHEN ts1Wait =>
            IF sd1 = '1' THEN
                st_next <= lenExtr;
            ELSE
                st_next <= st;
            END IF;
        WHEN OTHERS =>
            IF (ctrlFifoVld AND ctrlFifoLast) = '1' THEN
                st_next <= idle;
            ELSE
                st_next <= st;
            END IF;
        END CASE;
    END PROCESS;

END ARCHITECTURE;"""

if __name__ == "__main__":
    netlist, interfaces = ComplexConditions()
    print(netlistToVhdlStr("ComplexConditions", netlist, interfaces))
