#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.code import Switch
from hwt.hdl.ifContainter import IfContainer
from hwt.hdl.switchContainer import SwitchContainer
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

    def test_SwitchContainer_isSame(self):
        nl = RtlNetlist()
        a = nl.sig("a", BIT)
        b = nl.sig("b", BIT)

        s0 = SwitchContainer(switchOn=a, cases=[
            (hBit(0), [b(0), ])
        ])
        
        s1 = SwitchContainer(switchOn=a, cases=[
            (hBit(0), [b(0), ])
        ])
        self.assertTrue(s0.isSame(s1))
        self.assertTrue(s1.isSame(s0))
        
        s2 = SwitchContainer(switchOn=a, cases=[
            (hBit(0), [b(0), ]),
            (hBit(1), [b(0), ]),
        ])
        self.assertFalse(s0.isSame(s2))
        self.assertFalse(s2.isSame(s0))

        s2b = SwitchContainer(switchOn=a, cases=[
            (hBit(0), [b(0), ]),
            (hBit(1), [b(0), ]),
        ])
        self.assertTrue(s2.isSame(s2b))
        self.assertTrue(s2b.isSame(s2))

        s3 = SwitchContainer(switchOn=a, cases=[
            (hBit(1), [b(0), ]),
        ])
        self.assertFalse(s0.isSame(s3))
        self.assertFalse(s3.isSame(s0))

        s4 = SwitchContainer(switchOn=a, cases=[
            (hBit(0), [b(0), ])
        ], default=[b(0), ])
        self.assertFalse(s0.isSame(s4))
        self.assertFalse(s4.isSame(s0))

        s5 = SwitchContainer(switchOn=a, cases=[
            (hBit(0), [b(0), ])
        ], default=[b(1), ])
        self.assertFalse(s4.isSame(s5))
        self.assertFalse(s5.isSame(s4))

    def test_SwitchContainer_try_reduce__all(self):
        nl = RtlNetlist()
        a = nl.sig("a", BIT)
        b = nl.sig("b", BIT)
        s0 = Switch(a).add_cases([
            (hBit(0), [b(0), ]),
            (hBit(1), [b(0), ])
        ])
        s0_red, io_change = s0._try_reduce()
        self.assertFalse(io_change)
        self.assertEqual(len(s0_red), 1)
        self.assertTrue(s0_red[0].isSame(b(0)))

    def test_SwitchContainer_try_reduce__none(self):
        nl = RtlNetlist()
        a = nl.sig("a", BIT)
        b = nl.sig("b", BIT)
        s0 = Switch(a).add_cases([
            (hBit(0), [b(0), ]),
            (hBit(1), [b(1), ])
        ])
        s0_red, io_change = s0._try_reduce()
        self.assertFalse(io_change)
        self.assertEqual(len(s0_red), 1)
        s0_orig = Switch(a).add_cases([
            (hBit(0), [b(0), ]),
            (hBit(1), [b(1), ])
        ])
        self.assertTrue(s0_red[0].isSame(s0_orig))

    def test_SwitchContainer_try_reduce__empty(self):
        nl = RtlNetlist()
        a = nl.sig("a", BIT)
        s0 = Switch(a).add_cases([
            (hBit(0), []),
            (hBit(1), [])
        ])
        s0_red, io_change = s0._try_reduce()
        self.assertFalse(io_change)
        self.assertEqual(s0_red, [])
               
    def test_SwitchContainer_cut_off_drivers_of(self):
        nl = RtlNetlist()
        a = nl.sig("a", BIT)
        b = nl.sig("b", BIT)
        c = nl.sig("c", BIT)

        # reduce everything
        s0 = Switch(a).add_cases([
            (hBit(0), [b(0), ])
        ])
        s0_0 = s0._cut_off_drivers_of(b)
        self.assertIs(s0, s0_0)
        s0_1 = Switch(a).add_cases([
            (hBit(0), [b(0), ])
        ])
        self.assertTrue(s0.isSame(s0_1))
        
        # reduce nothing
        s0 = Switch(a).add_cases([
            (hBit(0), [b(0), ])
        ])
        s0_0 = s0._cut_off_drivers_of(a)
        self.assertIsNone(s0_0)
        self.assertTrue(s0.isSame(s0_1))

        # reduce a single case
        s1 = Switch(a).add_cases([
            (hBit(0), [b(0), ]),
            (hBit(1), [c(0), ]),
        ])
        s1_0 = s1._cut_off_drivers_of(c)
        s1_cut = Switch(a).add_cases([
            (hBit(1), [c(0), ]),
        ])
        self.assertTrue(s1_0.isSame(s1_cut))
        self.assertSetEqual(set(s1._outputs), {b})
        self.assertSetEqual(set(s1_0._outputs), {c})

        self.assertTrue(s1.isSame(s0))

        # reduce default
        s2 = Switch(a).add_cases([
            (hBit(0), [b(1), ]),
            (hBit(1), [b(0), ]),
        ]).Default(c(1))
        s2_0 = s2._cut_off_drivers_of(c)
        s2_rem = Switch(a).add_cases([
            (hBit(0), [b(1), ]),
            (hBit(1), [b(0), ]),
        ])
        s2_cut = Switch(a).add_cases([
            (hBit(0), []),
            (hBit(1), []),
        ]).Default(c(1))
        self.assertTrue(s2.isSame(s2_rem))
        self.assertTrue(s2_0.isSame(s2_cut))


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StatementsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
