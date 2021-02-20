#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import VectSignal
from hwt.synthesizer.unit import Unit
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class TmpVarExample(Unit):
    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(32)._m()

    def _impl(self):
        a = self.a[8:] + 4
        self.b(a[4:], fit=True)


class Serializer_tmpVar_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_add_to_slice_vhdl(self):
        self.assert_serializes_as_file(TmpVarExample(), "TmpVarExample.vhd")


if __name__ == '__main__':
    import unittest

    suite = unittest.TestSuite()
    # suite.addTest(RdSyncedPipe('test_basic_data_pass'))
    suite.addTest(unittest.makeSuite(Serializer_tmpVar_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
