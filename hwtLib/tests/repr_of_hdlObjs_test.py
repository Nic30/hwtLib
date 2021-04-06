#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.code import If, Switch
from hwt.hdl.types.bits import Bits
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.types.ctypes import uint8_t, int8_t


class ReprOfHdlObjsTC(unittest.TestCase):

    def ae(self, x, y):
        self.assertEqual((x).__repr__(), y)

    def test_RtlSignal(self):
        ctx = RtlNetlist()
        a = ctx.sig("a", uint8_t)
        b = ctx.sig("b", uint8_t)
        ae = self.ae
        ae(a, "a")
        ae(b, "b")
        ae(~a, "~a")
        c = ctx.sig("c", int8_t)
        ae(-c, "-c")
        ae(a + b, "a + b")
        ae(a - b, "a - b")
        ae(a // b, "a // b")
        ae(a * b, "a * b")
        ae(a._eq(b), "a._eq(b)")
        ae(a != b, "a != b")
        ae(a > b, "a > b")
        ae(a >= b, "a >= b")
        ae(a <= b, "a <= b")
        ae(a < b, "a < b")

        d = ctx.sig("d", Bits(8))
        ae(d[1:0], "d[1:0]")
        ae(d << 1, "Concat(d[7:0], Bits(1).from_py(0))")
        ae(d >> 1, "Concat(Bits(1).from_py(0), d[8:1])")

    def test_HdlAssignmentContainer(self):
        ctx = RtlNetlist()
        a = ctx.sig("a", uint8_t)
        b = ctx.sig("b", uint8_t)
        stm = a(b)
        self.ae(stm, "a(b)")

    def test_If(self):
        ctx = RtlNetlist()
        a = ctx.sig("a", uint8_t)
        b = ctx.sig("b", uint8_t)
        stm = If(a != 0,
                 a(b)
                 ).Else(
            a(b + 1)
        )
        self.ae(stm, """\
If(a != 0,
    a(b)
).Else(
    a(b + 1)
)""")
        stm = If(a != 2,
                 a(b)
                 ).Elif(b != 3,
                        a(b - 1)
                        ).Else(
            a(b + 2)
        )
        self.ae(stm, """\
If(a != 2,
    a(b)
).Elif(b != 3,
    a(b - 1)
).Else(
    a(b + 2)
)""")

        stm = If(a != 2,
                 a(b)
                 ).Elif(b != 3,
                        a(b - 1)
                        ).Elif(b != 4,
                               a(b - 2)
                               )
        self.ae(stm, """\
If(a != 2,
    a(b)
).Elif(b != 3,
    a(b - 1)
).Elif(b != 4,
    a(b - 2)
)""")

    def test_Switch(self):
        ctx = RtlNetlist()
        a = ctx.sig("a", uint8_t)
        b = ctx.sig("b", uint8_t)
        stm = Switch(a)\
            .Case(0, b(0))\
            .Case(1, b(1))\
            .Case(2, b(2))\
            .Default(b(3))
        self.ae(stm, """\
Switch(a)\\
    .Case(0,
        b(0))\\
    .Case(1,
        b(1))\\
    .Case(2,
        b(2))\\
    .Default(
        b(3))""")


if __name__ == '__main__':
    unittest.main()
