#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwt.synth import to_rtl_str
from hwt.synthesizer.exceptions import TypeConversionErr
from hwt.synthesizer.rtlLevel.exceptions import \
    SignalDriverErr
from hwtLib.examples.errors.accessingSubunitInternalIntf import \
    AccessingSubunitInternalIntf
from hwtLib.examples.errors.inconsistentIntfDirection import \
    InconsistentIntfDirection
from hwtLib.examples.errors.invalidTypeConnetion import InvalidTypeConnetion
from hwtLib.examples.errors.multipleDriversOfChildNet import \
    MultipleDriversOfChildNet, MultipleDriversOfChildNet2
from hwtLib.examples.errors.unusedSubunit import UnusedSubunit, UnusedSubunit2
from hwtLib.types.ctypes import uint8_t


class ExampleRomWithTooLargeArrayInit(HwModule):

    @override
    def hwDeclr(self):
        self.idx = HwIOSignal(HBits(2))
        self.data = HwIOSignal(HBits(8, signed=False))._m()

    @override
    def hwImpl(self):

        lut = self._sig(name="rom", dtype=uint8_t[1],
                                    def_val=[3, 10, 12, 99])

        self.data(lut[self.idx])


class ErrorsTC(unittest.TestCase):

    def test_invalidTypeConnetion(self):
        dut = InvalidTypeConnetion()
        with self.assertRaises(TypeConversionErr):
            to_rtl_str(dut)

    def test_inconsistentIntfDirection(self):
        dut = InconsistentIntfDirection()
        with self.assertRaises(SignalDriverErr):
            to_rtl_str(dut)

    def test_multipleDriversOfChildNet(self):
        dut = MultipleDriversOfChildNet()
        with self.assertRaises((SignalDriverErr, AssertionError)):
            to_rtl_str(dut)

    def test_multipleDriversOfChildNet2(self):
        dut = MultipleDriversOfChildNet2()
        with self.assertRaises(SignalDriverErr):
            to_rtl_str(dut)

    def test_unusedSubunit(self):
        dut = UnusedSubunit()
        with self.assertRaises(SignalDriverErr):
            to_rtl_str(dut)

    def test_unusedSubunit2(self):
        dut = UnusedSubunit2()
        with self.assertRaises(SignalDriverErr):
            to_rtl_str(dut)

    def test_accessingSubunitInternalIntf(self):
        dut = AccessingSubunitInternalIntf()
        with self.assertRaises(AssertionError):
            to_rtl_str(dut)

    def test_ExampleRomWithTooLargeArrayInit(self):
        dut = ExampleRomWithTooLargeArrayInit()
        with self.assertRaises(ValueError):
            to_rtl_str(dut)


if __name__ == '__main__':
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ErrorsTC("testBitAnd")])
    suite = testLoader.loadTestsFromTestCase(ErrorsTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
