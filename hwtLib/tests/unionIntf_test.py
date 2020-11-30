#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.union import HUnion
from hwt.interfaces.std import Handshaked
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSink, UnionSource
from hwt.interfaces.utils import addClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.emptyUnit import EmptyUnit
from hwtLib.types.ctypes import uint16_t, uint8_t, int16_t


union0 = HUnion(
        (uint16_t, "b16"),
        (HStruct(
            (uint8_t, "b16to8"),
            (uint8_t, "b8to0")
            ), "struct16"),
        (HUnion(
            (Bits(16), "b16"),
            (uint16_t, "b16u"),
            (int16_t, "b16s"),
            ), "union")
    )


class SimpleUnionSlave(EmptyUnit):

    def __init__(self, intfCls, dtype):
        self.dtype = dtype
        self.intfCls = intfCls
        super(SimpleUnionSlave, self).__init__()

    def mkFieldIntf(self, structIntf: Union[StructIntf, UnionSink, UnionSource], field):
        t = field.dtype
        path = structIntf._field_path / field.name
        if isinstance(t, HUnion):
            p = self.intfCls(t, path, structIntf._instantiateFieldFn)
            p._fieldsToInterfaces = structIntf._fieldsToInterfaces
            return p
        elif isinstance(t, HStruct):
            p = StructIntf(t, path, structIntf._instantiateFieldFn)
            p._fieldsToInterfaces = structIntf._fieldsToInterfaces
            return p
        else:
            p = Handshaked()

        p.DATA_WIDTH = field.dtype.bit_length()
        return p

    def _declr(self):
        addClkRstn(self)
        self.a = UnionSink(self.dtype, tuple(), self.mkFieldIntf)


class SimpleUnionMaster(SimpleUnionSlave):

    def _declr(self):
        addClkRstn(self)
        self.a = UnionSink(self.dtype, tuple(), self.mkFieldIntf)._m()


class UnionIntfTC(SimTestCase):

    def checkIntf(self, u):
        d = u.a._fieldsToInterfaces

        self.assertIs(d[("b16", )], u.a.b16)
        self.assertIs(d[("struct16",)], u.a.struct16)
        self.assertIs(d[("struct16", "b16to8")],
                      u.a.struct16.b16to8)
        self.assertIs(d[("union", "b16")],
                      u.a.union.b16)

    def test_instantiationSinkSlave(self):
        u = SimpleUnionSlave(UnionSink, union0)
        self.compileSimAndStart(u)
        self.checkIntf(u)

    def test_instantiationSinkMaster(self):
        u = SimpleUnionMaster(UnionSink, union0)
        self.compileSimAndStart(u)
        self.checkIntf(u)

    def test_instantiationSourceSlave(self):
        u = SimpleUnionSlave(UnionSource, union0)
        self.compileSimAndStart(u)
        self.checkIntf(u)

    def test_instantiationSourceMaster(self):
        u = SimpleUnionMaster(UnionSource, union0)
        self.compileSimAndStart(u)
        self.checkIntf(u)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(BitsSlicingTC('test_slice_bits_sig'))
    suite.addTest(unittest.makeSuite(UnionIntfTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
