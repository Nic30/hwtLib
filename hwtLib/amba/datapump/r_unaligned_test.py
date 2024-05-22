#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.amba.axi3 import Axi3
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.datapump.r import Axi_rDatapump
from hwtLib.amba.datapump.r_aligned_test import Axi3Lite_rDatapumpTC, \
    Axi3_rDatapumpTC


class Axi4Lite_rDatapump_alignas8TC(Axi3Lite_rDatapumpTC):
    CHUNK_WIDTH = 8
    ALIGNAS = 8

    @classmethod
    def setUpClass(cls):
        dut = Axi_rDatapump(axiCls=Axi4Lite)
        dut.DATA_WIDTH = cls.DATA_WIDTH
        dut.CHUNK_WIDTH = cls.CHUNK_WIDTH
        dut.MAX_CHUNKS = (cls.DATA_WIDTH // cls.CHUNK_WIDTH) * (cls.LEN_MAX_VAL + 1)
        dut.ALIGNAS = cls.ALIGNAS
        cls.compileSim(dut)


class Axi4Lite_rDatapump_16b_from_64bTC(Axi4Lite_rDatapump_alignas8TC):
    LEN_MAX_VAL = 0
    CHUNK_WIDTH = 16
    ALIGNAS = 16


class Axi3_rDatapump_alignas8_TC(Axi3_rDatapumpTC):
    ALIGNAS = 8
    CHUNK_WIDTH = 8

    @classmethod
    def setUpClass(cls):
        dut = Axi_rDatapump(axiCls=Axi3)
        dut.ALIGNAS = cls.ALIGNAS
        dut.DATA_WIDTH = cls.DATA_WIDTH
        dut.CHUNK_WIDTH = cls.CHUNK_WIDTH
        dut.MAX_CHUNKS = (cls.DATA_WIDTH // cls.CHUNK_WIDTH) * (cls.LEN_MAX_VAL + 1)
        dut.ALIGNAS = cls.ALIGNAS
        cls.compileSim(dut)


Axi_rDatapump_unalignedTCs = [
    Axi3_rDatapump_alignas8_TC,
    Axi4Lite_rDatapump_alignas8TC,
    Axi4Lite_rDatapump_16b_from_64bTC,
]

if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4Lite_rDatapump_16b_from_64bTC("test_notSplitedReqWithData")])
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in Axi_rDatapump_unalignedTCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
