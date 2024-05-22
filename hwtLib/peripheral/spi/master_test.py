#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.spi.master import SpiMaster
from hwtSimApi.constants import CLK_PERIOD


class SpiMasterTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = SpiMaster()
        dut.SPI_FREQ_PESCALER = 8
        cls.compileSim(dut)

    def test_readAndWrite8bits(self):
        dut = self.dut

        # slave, d, last
        dut.data._ag.data.append([0, 7, 1])
        dut.spi._ag.txData.append(11)

        self.runSim(150 * CLK_PERIOD)
        aeq = self.assertValSequenceEqual
        aeq(dut.data._ag.dinData, [11])
        aeq(dut.spi._ag.rxData, [7])
        aeq(dut.spi._ag.chipSelects, [0])

    def test_readAndWrite16bits(self):
        dut = self.dut

        # slave, d, last
        dut.data._ag.data.extend(([0, 7, 0], [0, 99, 1]))
        dut.spi._ag.txData.extend([11, 48])

        self.runSim(200 * CLK_PERIOD)
        aeq = self.assertValSequenceEqual
        aeq(dut.data._ag.dinData, [11, 48])
        aeq(dut.spi._ag.rxData, [7, 99])
        aeq(dut.spi._ag.chipSelects, [0, 0])

    def test_readAndWrite2x8bits(self):
        dut = self.dut

        # slave, d, last
        dut.data._ag.data.extend(([0, 7, 1], [0, 99, 1]))
        dut.spi._ag.txData.extend([11, 48])

        self.runSim(200 * CLK_PERIOD)

        aeq = self.assertValSequenceEqual
        aeq(dut.data._ag.dinData, [11, 48])
        aeq(dut.spi._ag.rxData, [7, 99])
        aeq(dut.spi._ag.chipSelects, [0, 0])


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([SpiMasterTC("test_readAndWrite8bits")])
    suite = testLoader.loadTestsFromTestCase(SpiMasterTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
