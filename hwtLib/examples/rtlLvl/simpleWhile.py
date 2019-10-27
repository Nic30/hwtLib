#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.rtlLvl.netlistToRtl import netlistToVhdlStr


def SimpleWhile():
    t = Bits(8)
    n = RtlNetlist()

    boundary = n.sig("boundary", t, def_val=8)
    s_out = n.sig("s_out", t)

    start = n.sig("start")
    en = n.sig("en")

    clk = n.sig("clk")
    syncRst = n.sig("rst")

    counter = n.sig("counter", t, clk, syncRst, 0)
    If(start,
        counter(boundary)
    ).Elif(en,
        counter(counter - 1)
    )

    s_out(counter)

    interf = [clk, syncRst, start, en, s_out]
    return n, interf


simpleWhileExpected = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleWhile IS
    PORT (clk: IN STD_LOGIC;
        en: IN STD_LOGIC;
        rst: IN STD_LOGIC;
        s_out: OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
        start: IN STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleWhile IS
    CONSTANT boundary: STD_LOGIC_VECTOR(7 DOWNTO 0) := X"08";
    SIGNAL counter: STD_LOGIC_VECTOR(7 DOWNTO 0) := X"00";
    SIGNAL counter_next: STD_LOGIC_VECTOR(7 DOWNTO 0);
BEGIN
    assig_process_counter: PROCESS (clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            IF rst = '1' THEN
                counter <= X"00";
            ELSE
                counter <= counter_next;
            END IF;
        END IF;
    END PROCESS;

    assig_process_counter_next: PROCESS (counter, en, start)
    BEGIN
        IF start = '1' THEN
            counter_next <= boundary;
        ELSIF en = '1' THEN
            counter_next <= STD_LOGIC_VECTOR(UNSIGNED(counter) - TO_UNSIGNED(1, 8));
        ELSE
            counter_next <= counter;
        END IF;
    END PROCESS;

    s_out <= counter;
END ARCHITECTURE;"""

if __name__ == "__main__":
    netlist, interfaces = SimpleWhile()
    print(netlistToVhdlStr("SimpleWhile", netlist, interfaces))
