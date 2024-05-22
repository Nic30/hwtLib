#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.examples.base_serialization_TC import BaseSerializationTC
from hwtLib.examples.statements.codeBlockStm import BlockStm_complete_override0, \
    BlockStm_complete_override1, BlockStm_complete_override2, \
    BlockStm_nop_val_optimized_out, BlockStm_nop_val
from hwtSimApi.constants import CLK_PERIOD


class CodeBlokStmTC(BaseSerializationTC):
    __FILE__ = __file__

    def test_BlockStm_complete_override0(self):
        dut = BlockStm_complete_override0()
        self.compileSimAndStart(dut)

        a = dut.a._ag.data
        b = dut.b._ag.data
        c = []
        for _a in [0, 1, None]:
            for _b in [0, 1, None]:
                _c = _b
                a.append(_a)
                b.append(_b)
                c.append(_c)

        self.runSim(len(c) * CLK_PERIOD)

        self.assertValSequenceEqual(dut.c._ag.data, c)

    def test_BlockStm_complete_override1(self):
        dut = BlockStm_complete_override1()
        self.compileSimAndStart(dut)

        a = dut.a._ag.data
        b = dut.b._ag.data
        c = []
        for _a in [0, 1, None]:
            for _b in [0, 1, None]:
                _c = _a
                if _b is None:
                    _c = None
                elif _b:
                    _c = 0
                a.append(_a)
                b.append(_b)
                c.append(_c)

        self.runSim(len(c) * CLK_PERIOD)

        self.assertValSequenceEqual(dut.c._ag.data, c)

    def test_BlockStm_complete_override2(self):
        dut = BlockStm_complete_override2()
        self.compileSimAndStart(dut)

        a = dut.a._ag.data
        b = dut.b._ag.data
        c = []
        for _a in [0, 1, None]:
            for _b in [0, 1, None]:
                _c = _a
                a.append(_a)
                b.append(_b)
                c.append(_c)

        self.runSim(len(c) * CLK_PERIOD)

        self.assertValSequenceEqual(dut.c._ag.data, c)

    def test_BlockStm_nop_val_optimized_out(self):
        dut = BlockStm_nop_val_optimized_out()
        self.compileSimAndStart(dut)

        a = dut.a._ag.data
        b = dut.b._ag.data
        c = []
        for _a in [0, 1, None]:
            for _b in [0, 1, None]:
                _c = _a
                a.append(_a)
                b.append(_b)
                c.append(_c)

        self.runSim((len(c) + 1) * CLK_PERIOD)

        self.assertValSequenceEqual(dut.c._ag.data, c)

    def test_BlockStm_nop(self):
        dut = BlockStm_nop_val()
        self.compileSimAndStart(dut)

        a = dut.a._ag.data
        b = dut.b._ag.data
        c = []
        c1 = []
        _c1 = None
        for _a in [1, 1, 0, 1, 0, 1, 1, None]:
            for _b in [0, 1, None]:
                _c = _a
                a.append(_a)
                b.append(_b)
                c.append(_c)
                c1.append(_c1)
                if _b:
                    _c1 = _a
                elif _b is None:
                    _c1 = None

        self.runSim((len(c) + 1) * CLK_PERIOD)

        self.assertValSequenceEqual(dut.c._ag.data, c)
        self.assertValSequenceEqual(dut.c1._ag.data, c1)

    def test_BlockStm_complete_override1_vhdl(self):
        self.assert_serializes_as_file(BlockStm_complete_override1,
                                       "BlockStm_complete_override1.vhd")


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([CodeBlokStmTC("test_resources_SimpleIfStatement2c")])
    suite = testLoader.loadTestsFromTestCase(CodeBlokStmTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
