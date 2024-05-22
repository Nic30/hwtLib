#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union

from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.hwIOs.hwIOUnion import HwIOUnionSink, HwIOUnionSource
from hwt.hwIOs.utils import addClkRstn
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.union import HUnion
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.emptyHwModule import EmptyHwModule
from hwtLib.types.ctypes import uint16_t, uint8_t, int16_t


union0 = HUnion(
        (uint16_t, "b16"),
        (HStruct(
            (uint8_t, "b16to8"),
            (uint8_t, "b8to0")
            ), "struct16"),
        (HUnion(
            (HBits(16), "b16"),
            (uint16_t, "b16u"),
            (int16_t, "b16s"),
            ), "union")
    )


class SimpleUnionSlave(EmptyHwModule):

    def __init__(self, hwIOCls, dtype):
        self.dtype = dtype
        self.hwIOCls = hwIOCls
        super(SimpleUnionSlave, self).__init__()

    def mkFieldHwIO(self, structHwIO: Union[HwIOStruct, HwIOUnionSink, HwIOUnionSource], field):
        t = field.dtype
        path = structHwIO._field_path / field.name
        if isinstance(t, HUnion):
            p = self.hwIOCls(t, path, structHwIO._instantiateFieldFn)
            p._fieldsToHwIOs = structHwIO._fieldsToHwIOs
            return p
        elif isinstance(t, HStruct):
            p = HwIOStruct(t, path, structHwIO._instantiateFieldFn)
            p._fieldsToHwIOs = structHwIO._fieldsToHwIOs
            return p
        else:
            p = HwIODataRdVld()

        p.DATA_WIDTH = field.dtype.bit_length()
        return p

    def _declr(self):
        addClkRstn(self)
        self.a = HwIOUnionSink(self.dtype, tuple(), self.mkFieldHwIO)


class SimpleUnionMaster(SimpleUnionSlave):

    def _declr(self):
        addClkRstn(self)
        self.a = HwIOUnionSink(self.dtype, tuple(), self.mkFieldHwIO)._m()


class HwIOUnionTC(SimTestCase):

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def checkHwIO(self, dut):
        d = dut.a._fieldsToHwIOs

        self.assertIs(d[("b16",)], dut.a.b16)
        self.assertIs(d[("struct16",)], dut.a.struct16)
        self.assertIs(d[("struct16", "b16to8")],
                      dut.a.struct16.b16to8)
        self.assertIs(d[("union", "b16")],
                      dut.a.union.b16)

    def test_instantiationSinkSlave(self):
        dut = SimpleUnionSlave(HwIOUnionSink, union0)
        self.compileSimAndStart(dut)
        self.checkHwIO(dut)

    def test_instantiationSinkMaster(self):
        dut = SimpleUnionMaster(HwIOUnionSink, union0)
        self.compileSimAndStart(dut)
        self.checkHwIO(dut)

    def test_instantiationSourceSlave(self):
        dut = SimpleUnionSlave(HwIOUnionSource, union0)
        self.compileSimAndStart(dut)
        self.checkHwIO(dut)

    def test_instantiationSourceMaster(self):
        dut = SimpleUnionMaster(HwIOUnionSource, union0)
        self.compileSimAndStart(dut)
        self.checkHwIO(dut)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([HwIOUnionTC("test_slice_bits_sig")])
    suite = testLoader.loadTestsFromTestCase(HwIOUnionTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
