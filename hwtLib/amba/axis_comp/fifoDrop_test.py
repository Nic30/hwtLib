#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axis_comp.fifoDrop import Axi4SFifoDrop
from hwtSimApi.constants import CLK_PERIOD


class Axi4SFifoDropTC(SimTestCase):
    ITEMS = 4
    DATA_WIDTH = 8

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = Axi4SFifoDrop()
        dut.DATA_WIDTH = cls.DATA_WIDTH
        dut.DEPTH = cls.ITEMS
        dut.EXPORT_SIZE = True
        dut.EXPORT_SPACE = True
        cls.compileSim(dut)

    def test_nop(self):
        dut = self.dut
        dut.dataIn_discard._ag.data.append(0)
        self.runSim(20 * CLK_PERIOD)

        self.assertEqual(len(dut.dataOut._ag.data), 0)

    def test_singleWordPacket_commited(self):
        dut = self.dut

        dut.dataIn_discard._ag.data.append(0)
        ref_data = [
            (1, 1),
        ]
        dut.dataIn._ag.data.extend(ref_data)

        self.runSim(20 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.dataOut._ag.data, ref_data)

    def test_twoWordPacket_commited(self):
        dut = self.dut

        dut.dataIn_discard._ag.data.append(0)
        ref_data = [
            (1, 0),
            (2, 1),
        ]
        dut.dataIn._ag.data.extend(ref_data)

        self.runSim(20 * CLK_PERIOD)
        self.assertValSequenceEqual(dut.dataOut._ag.data, ref_data)

    def test_commited_on_end(self):
        dut = self.dut

        dut.dataIn_discard._ag.data.append(0)
        N = self.ITEMS - 1
        # N = 60
        ref_data = [
            (i + 1, int(last))
            for last, i in iter_with_last(range(N))
        ]
        dut.dataIn._ag.data.extend(ref_data)

        self.runSim((2 * N + 10) * CLK_PERIOD)
        self.assertValSequenceEqual(dut.dataOut._ag.data, ref_data)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([Axi4SFifoDropTC("test_singleWordPacket")])
    suite = testLoader.loadTestsFromTestCase(Axi4SFifoDropTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
