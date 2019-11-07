#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from _collections import deque
import unittest

from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwtLib.peripheral.i2c.intf import I2cAgent
from hwtLib.peripheral.i2c.masterBitCntrl import I2cMasterBitCtrl, \
    NOP, START, READ, WRITE
from pyMathBitPrecise.bit_utils import selectBit
from pycocotb.constants import CLK_PERIOD


class I2CMasterBitCntrlTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        cls.u = I2cMasterBitCtrl()
        return cls.u

    def test_nop(self):
        u = self.u
        u.cntrl._ag.data.append((NOP, 0))
        u.clk_cnt_initVal._ag.data.append(4)
        self.runSim(20 * CLK_PERIOD)

        self.assertFalse(u.i2c._ag.hasTransactionPending())

    def test_startbit(self):
        u = self.u
        u.cntrl._ag.data.extend([(START, 0), (NOP, 0)])
        u.clk_cnt_initVal._ag.data.append(4)
        self.runSim(60 * CLK_PERIOD)

        self.assertEqual(u.i2c._ag.bit_cntrl_rx, deque([I2cAgent.START]))

    def test_7bitAddr(self):
        u = self.u
        addr = 13
        mode = I2cAgent.READ
        u.cntrl._ag.data.extend(
            [(START, 0), ] +
            [(WRITE, selectBit(addr, 7 - i - 1)) for i in range(7)] +
            [(WRITE, mode),
             (READ, 0),
             (NOP, 0)
            ])
        u.clk_cnt_initVal._ag.data.append(4)
        self.runSim(70 * CLK_PERIOD)

        self.assertValSequenceEqual(
            u.i2c._ag.bit_cntrl_rx,
            [I2cAgent.START] + 
            [selectBit(addr, 7 - i - 1)
             for i in range(7)] +
            [mode])


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(I2CMasterBitCntrlTC('test_nop'))
    suite.addTest(unittest.makeSuite(I2CMasterBitCntrlTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
