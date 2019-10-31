#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.peripheral.spi.master import SpiMaster
from pycocotb.constants import CLK_PERIOD


class SpiMasterTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = SpiMaster()
        u.SPI_FREQ_PESCALER = 8
        return u

    def test_readAndWrite8bits(self):
        u = self.u

        # slave, d, last
        u.data._ag.data.append([0, 7, 1])
        u.spi._ag.txData.append(11)

        self.runSim(150 * CLK_PERIOD)
        aeq = self.assertValSequenceEqual
        aeq(u.data._ag.dinData, [11])
        aeq(u.spi._ag.rxData, [7])
        aeq(u.spi._ag.chipSelects, [0])

    def test_readAndWrite16bits(self):
        u = self.u

        # slave, d, last
        u.data._ag.data.extend(([0, 7, 0], [0, 99, 1]))
        u.spi._ag.txData.extend([11, 48])

        self.runSim(200 * CLK_PERIOD)
        aeq = self.assertValSequenceEqual
        aeq(u.data._ag.dinData, [11, 48])
        aeq(u.spi._ag.rxData, [7, 99])
        aeq(u.spi._ag.chipSelects, [0, 0])

    def test_readAndWrite2x8bits(self):
        u = self.u

        # slave, d, last
        u.data._ag.data.extend(([0, 7, 1], [0, 99, 1]))
        u.spi._ag.txData.extend([11, 48])

        self.runSim(200 * CLK_PERIOD)

        aeq = self.assertValSequenceEqual
        aeq(u.data._ag.dinData, [11, 48])
        aeq(u.spi._ag.rxData, [7, 99])
        aeq(u.spi._ag.chipSelects, [0, 0])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(SpiMasterTC('test_readAndWrite8bits'))
    suite.addTest(unittest.makeSuite(SpiMasterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
