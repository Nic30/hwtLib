#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.interfaces.std import Signal, VectSignal
from hwt.serializer.mode import serializeExclude, serializeOnce, \
    serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class SimpeUnit(Unit):
    def _declr(self):
        self.a = Signal()._m()

    def _impl(self):
        self.a(1)


@serializeExclude
class ExcludedUnit(SimpeUnit):
    pass


@serializeOnce
class OnceUnit(SimpeUnit):
    pass


@serializeParamsUniq
class ParamsUniqUnit(SimpeUnit):
    def _config(self):
        self.A = Param(0)
        self.B = Param(1)


class ExampleA(Unit):
    def _declr(self):
        self.a = VectSignal(7)._m()
        self.u0 = ExcludedUnit()
        self.u1 = ExcludedUnit()
        self.u2 = OnceUnit()
        self.u3 = OnceUnit()
        self.u4 = OnceUnit()
        self.u5 = ParamsUniqUnit()
        self.u6 = ParamsUniqUnit()
        self.u7 = ParamsUniqUnit()
        self.u7.B = 12

    def _impl(self):
        self.a(Concat(*[getattr(self, f"u{i:d}").a for i in range(7)]))


class SerializerModes_TC(BaseSerializationTC):
    __FILE__ = __file__

    def test_all(self):
        self.assert_serializes_as_file(ExampleA(), "ExampleA.vhd")


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(TransTmpl_TC('test_walkFlatten_arr'))
    suite.addTest(unittest.makeSuite(SerializerModes_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)