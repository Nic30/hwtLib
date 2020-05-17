#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest

from hwt.hdl.ifContainter import IfContainer
from hwt.hdl.typeShortcuts import hBit
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist


class StatementsTC(unittest.TestCase):
    def test_ifContSeqEval(self):
        for a_in, b_in in [(0, 0),
                           (0, 1),
                           (1, 0),
                           (1, 1)]:
            resT = Bits(2)
            nl = RtlNetlist()

            res = nl.sig("res", resT)
            a = nl.sig("a", BIT)
            b = nl.sig("b", BIT)

            def w(val):
                return res(val)

            a.def_val = hBit(a_in)
            b.def_val = hBit(b_in)

            stm = IfContainer(a & b,
                              ifTrue=[res(0), ],
                              elIfs=[(a, [res(1)]), ],
                              ifFalse=[res(2), ]
                              )

            if a_in and b_in:
                expected = 0
            elif a_in:
                expected = 1
            else:
                expected = 2

            stm.seqEval()

            newVal = res._val

            self.assertEqual(newVal.val, expected)
            self.assertEqual(newVal.vld_mask, 3)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StatementsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
