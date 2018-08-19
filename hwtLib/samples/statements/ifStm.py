#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal, Clk
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit


class SimpleIfStatement(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()._m()

    def _impl(self):
        If(self.a,
           self.d(self.b),
        ).Elif(self.b,
           self.d(self.c)
        ).Else(
           self.d(0)
        )


class SimpleIfStatement2(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()._m()

    def _impl(self):
        r = self._reg("reg_d", defVal=0)

        If(self.a,
            If(self.b & self.c,
               r(1),
            ).Else(
               r(0)
            )
        )
        self.d(r)


class SimpleIfStatement2b(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = Signal()._m()

    def _impl(self):
        r = self._reg("reg_d", defVal=0)

        If(self.a & self.b,
            If(self.c,
               r(1),
            )
        ).Elif(self.c,
            r(0)
        )
        self.d(r)


class SimpleIfStatement2c(Unit):
    def _declr(self):
        addClkRstn(self)
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()
        self.d = VectSignal(2)._m()

    def _impl(self):
        r = self._reg("reg_d", Bits(2), defVal=0)

        If(self.a & self.b,
            If(self.c,
               r(0),
            )
        ).Elif(self.c,
            r(1)
        ).Else(
            r(2)
        )
        self.d(r)


class SimpleIfStatement3(SimpleIfStatement):
    def _impl(self):
        If(self.a,
           self.d(0),
        ).Elif(self.b,
           self.d(0)
        ).Else(
           self.d(0)
        )


class SimpleIfStatementMergable(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()

        self.c = Signal()._m()
        self.d = Signal()._m()

    def _impl(self):
        If(self.a,
           self.d(self.b),
        ).Else(
           self.d(0)
        )

        If(self.a,
            self.c(self.b),
        ).Else(
           self.c(0)
        )


SimpleIfStatementMergable_vhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleIfStatementMergable IS
    PORT (a: IN STD_LOGIC;
        b: IN STD_LOGIC;
        c: OUT STD_LOGIC;
        d: OUT STD_LOGIC
    );
END SimpleIfStatementMergable;

ARCHITECTURE rtl OF SimpleIfStatementMergable IS
BEGIN
    assig_process_d: PROCESS (a, b)
    BEGIN
        IF a = '1' THEN
            d <= b;
            c <= b;
        ELSE
            d <= '0';
            c <= '0';
        END IF;
    END PROCESS;

END ARCHITECTURE rtl;"""


class SimpleIfStatementMergable1(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()

        self.c = Signal()._m()
        self.d = Signal()._m()
        self.e = Signal()

    def _impl(self):
        If(self.e,
            If(self.a,
                self.d(self.b),
            ),
            If(self.a,
                self.c(self.b),
            )
        )


SimpleIfStatementMergable1_vhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleIfStatementMergable1 IS
    PORT (a: IN STD_LOGIC;
        b: IN STD_LOGIC;
        c: OUT STD_LOGIC;
        d: OUT STD_LOGIC;
        e: IN STD_LOGIC
    );
END SimpleIfStatementMergable1;

ARCHITECTURE rtl OF SimpleIfStatementMergable1 IS
BEGIN
    assig_process_c: PROCESS (a, b, e)
    BEGIN
        IF e = '1' THEN
            IF a = '1' THEN
                d <= b;
                c <= b;
            END IF;
        END IF;
    END PROCESS;

END ARCHITECTURE rtl;"""


class SimpleIfStatementMergable2(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()

        self.c = Signal()
        self.d = Signal()._m()
        self.e = Signal()._m()
        self.f = Signal()._m()

    def _impl(self):
        If(self.a,
            self.d(self.b),
            # this two if statements will be merged together
            If(self.b,
               self.e(self.c)
            ),
            If(self.b,
               self.f(0)
            )
        ).Else(
           self.d(0)
        )


SimpleIfStatementMergable2_vhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleIfStatementMergable2 IS
    PORT (a: IN STD_LOGIC;
        b: IN STD_LOGIC;
        c: IN STD_LOGIC;
        d: OUT STD_LOGIC;
        e: OUT STD_LOGIC;
        f: OUT STD_LOGIC
    );
END SimpleIfStatementMergable2;

ARCHITECTURE rtl OF SimpleIfStatementMergable2 IS
BEGIN
    assig_process_d: PROCESS (a, b, c)
    BEGIN
        IF a = '1' THEN
            d <= b;
            IF b = '1' THEN
                e <= c;
                f <= '0';
            END IF;
        ELSE
            d <= '0';
        END IF;
    END PROCESS;

END ARCHITECTURE rtl;"""


class IfStatementPartiallyEnclosed(Unit):
    def _declr(self):
        self.clk = Clk()
        self.a = Signal()._m()
        self.b = Signal()._m()

        self.c = Signal()
        self.d = Signal()

    def _impl(self):
        a = self._reg("a_reg")
        b = self._reg("b_reg")

        If(self.c,
            a(1),
            b(1),
        ).Elif(self.d,
            a(0)
        ).Else(
            a(1),
            b(1),
        )
        self.a(a)
        self.b(b)


IfStatementPartiallyEnclosed_vhdl = """library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY IfStatementPartiallyEnclosed IS
    PORT (a: OUT STD_LOGIC;
        b: OUT STD_LOGIC;
        c: IN STD_LOGIC;
        clk: IN STD_LOGIC;
        d: IN STD_LOGIC
    );
END IfStatementPartiallyEnclosed;

ARCHITECTURE rtl OF IfStatementPartiallyEnclosed IS
    SIGNAL a_reg: STD_LOGIC;
    SIGNAL a_reg_next: STD_LOGIC;
    SIGNAL b_reg: STD_LOGIC;
    SIGNAL b_reg_next: STD_LOGIC;
BEGIN
    a <= a_reg;
    assig_process_a_reg_next: PROCESS (c, d)
    BEGIN
        IF c = '1' THEN
            a_reg_next <= '1';
            b_reg_next <= '1';
        ELSIF d = '1' THEN
            a_reg_next <= '0';
            b_reg_next <= b_reg;
        ELSE
            a_reg_next <= '1';
            b_reg_next <= '1';
        END IF;
    END PROCESS;

    b <= b_reg;
    assig_process_b_reg: PROCESS (clk)
    BEGIN
        IF RISING_EDGE(clk) THEN
            b_reg <= b_reg_next;
            a_reg <= a_reg_next;
        END IF;
    END PROCESS;

END ARCHITECTURE rtl;"""


if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.utils import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = IfStatementPartiallyEnclosed()
    print(toRtl(u))
