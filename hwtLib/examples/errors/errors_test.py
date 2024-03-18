#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.synthesizer.exceptions import TypeConversionErr
from hwt.synthesizer.rtlLevel.signalUtils.exceptions import \
    SignalDriverErr
from hwt.synthesizer.utils import to_rtl_str
from hwtLib.examples.errors.accessingSubunitInternalIntf import \
    AccessingSubunitInternalIntf
from hwtLib.examples.errors.inconsistentIntfDirection import \
    InconsistentIntfDirection
from hwtLib.examples.errors.invalidTypeConnetion import InvalidTypeConnetion
from hwtLib.examples.errors.multipleDriversOfChildNet import \
    MultipleDriversOfChildNet, MultipleDriversOfChildNet2
from hwtLib.examples.errors.unusedSubunit import UnusedSubunit, UnusedSubunit2
from hwt.synthesizer.unit import Unit
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal
from hwtLib.types.ctypes import uint8_t


class ExampleRomWithTooLargeArrayInit(Unit):

    def _declr(self):
        self.idx = Signal(Bits(2))
        self.data = Signal(Bits(8, signed=False))._m()

    def _impl(self):

        lut = self._sig(name="rom", dtype=uint8_t[1],
                                    def_val=[3, 10, 12, 99])

        self.data(lut[self.idx])


class ErrorsTC(unittest.TestCase):

    def test_invalidTypeConnetion(self):
        u = InvalidTypeConnetion()
        with self.assertRaises(TypeConversionErr):
            to_rtl_str(u)

    def test_inconsistentIntfDirection(self):
        u = InconsistentIntfDirection()
        with self.assertRaises(SignalDriverErr):
            to_rtl_str(u)

    def test_multipleDriversOfChildNet(self):
        u = MultipleDriversOfChildNet()
        with self.assertRaises((SignalDriverErr, AssertionError)):
            to_rtl_str(u)

    def test_multipleDriversOfChildNet2(self):
        u = MultipleDriversOfChildNet2()
        with self.assertRaises(SignalDriverErr):
            to_rtl_str(u)

    def test_unusedSubunit(self):
        u = UnusedSubunit()
        with self.assertRaises(SignalDriverErr):
            to_rtl_str(u)

    def test_unusedSubunit2(self):
        u = UnusedSubunit2()
        with self.assertRaises(SignalDriverErr):
            to_rtl_str(u)

    def test_accessingSubunitInternalIntf(self):
        u = AccessingSubunitInternalIntf()
        with self.assertRaises(AssertionError):
            to_rtl_str(u)

    def test_ExampleRomWithTooLargeArrayInit(self):
        u = ExampleRomWithTooLargeArrayInit()
        with self.assertRaises(ValueError):
            to_rtl_str(u)


if __name__ == '__main__':
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([ErrorsTC("testBitAnd")])
    suite = testLoader.loadTestsFromTestCase(ErrorsTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
