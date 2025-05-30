#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.code import Switch, If
from hwt.hdl.statements.switchContainer import SwitchContainer
from hwt.hdl.types.defs import BIT
from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.synth import synthesised
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.tests.types.hConst_test import hBit


class If_solvable_comb_loop(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIOSignal()
        self.c = HwIOSignal()._m()

    @override
    def hwImpl(self):
        b = self.b = self._sig("b")

        return If(self.a,
           # b is input and output of this if statement,
           # the statement has to be split in to two to remove this dependency
            b(self.a),
            self.c(b),
        )


class If_solvable_comb_loop_nested(If_solvable_comb_loop):

    @override
    def hwDeclr(self):
        super(If_solvable_comb_loop_nested, self).hwDeclr()
        self.d = HwIOSignal()

    @override
    def hwImpl(self):
        If(self.d,
           super(If_solvable_comb_loop_nested, self).hwImpl()
        )


class StatementsTC(unittest.TestCase):

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

    def test_If_solvable_comb_loop(self):
        dut = If_solvable_comb_loop()
        synthesised(dut)
        b_d = dut.b._rtlDrivers
        c_d = dut.c._sigInside._rtlDrivers
        self.assertEqual(len(b_d), 1)
        self.assertEqual(len(c_d), 1)
        self.assertIsNot(b_d[0], c_d[0])

        self.assertIsNone(b_d[0].parentStm)
        self.assertSequenceEqual(b_d[0]._inputs, [dut.a._sigInside])
        self.assertSequenceEqual(b_d[0]._outputs, [dut.b])
        self.assertSequenceEqual(b_d[0]._sensitivity, [dut.a._sigInside])

        self.assertIsNone(c_d[0].parentStm)
        self.assertSequenceEqual(c_d[0]._inputs, [dut.a._sigInside, dut.b])
        self.assertSequenceEqual(c_d[0]._outputs, [dut.c._sigInside])
        self.assertSequenceEqual(c_d[0]._sensitivity, [dut.a._sigInside, dut.b])

    def test_If_solvable_comb_loop_nested(self):
        dut = If_solvable_comb_loop_nested()
        synthesised(dut)
        b_d = dut.b._rtlDrivers
        c_d = dut.c._sigInside._rtlDrivers
        self.assertEqual(len(b_d), 1)
        self.assertEqual(len(c_d), 1)
        self.assertIsNot(b_d[0], c_d[0])

        d = dut.d._sigInside
        self.assertIsNone(b_d[0].parentStm)
        self.assertSequenceEqual(b_d[0]._inputs, [d, dut.a._sigInside])
        self.assertSequenceEqual(b_d[0]._outputs, [dut.b])
        self.assertSequenceEqual(b_d[0]._sensitivity, [d, dut.a._sigInside])

        self.assertIsNone(c_d[0].parentStm)
        self.assertSequenceEqual(c_d[0]._inputs, [d, dut.a._sigInside, dut.b])
        self.assertSequenceEqual(c_d[0]._outputs, [dut.c._sigInside])
        self.assertSequenceEqual(c_d[0]._sensitivity, [d, dut.a._sigInside, dut.b])


if __name__ == '__main__':
    testLoader = unittest.TestLoader()
    suite = testLoader.loadTestsFromTestCase(StatementsTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
