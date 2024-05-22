#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeExclude, serializeOnce, \
    serializeParamsUniq
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class SimpleHwModule(HwModule):
    @override
    def hwDeclr(self):
        self.a = HwIOSignal()._m()

    @override
    def hwImpl(self):
        self.a(1)


@serializeExclude
class ExcludedHwModule(SimpleHwModule):
    pass


@serializeOnce
class OnceHwModule(SimpleHwModule):
    pass


@serializeParamsUniq
class ParamsUniqHwModule(SimpleHwModule):
    @override
    def hwConfig(self):
        self.A = HwParam(0)
        self.B = HwParam(1)


class ExampleA(HwModule):
    @override
    def hwDeclr(self):
        self.a = HwIOVectSignal(7)._m()
        self.m0 = ExcludedHwModule()
        self.m1 = ExcludedHwModule()
        self.m2 = OnceHwModule()
        self.m3 = OnceHwModule()
        self.m4 = OnceHwModule()
        self.m5 = ParamsUniqHwModule()
        self.m6 = ParamsUniqHwModule()
        self.m7 = ParamsUniqHwModule()
        self.m7.B = 12

    @override
    def hwImpl(self):
        self.a(Concat(*[getattr(self, f"m{i:d}").a for i in range(7)]))


class SerializerModes_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_all(self):
        self.assert_serializes_as_file(ExampleA(), "ExampleA.vhd")


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SerializerModes_TC("test_walkFlatten_arr")])
    suite = testLoader.loadTestsFromTestCase(SerializerModes_TC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)