#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.agentConnector import valToInt
from hwt.simulator.simTestCase import SingleUnitSimTestCase

from hwtLib.peripheral.uart.tx import UartTx
from pycocotb.constants import CLK_PERIOD


class UartTxTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = UartTx()
        u.BAUD = 115200
        u.FREQ = 115200
        return u

    def setUp(self):
        SingleUnitSimTestCase.setUp(self)
        self.randomize(self.u.dataIn)

    def getStr(self):
        START_BIT = 0
        STOP_BIT = 1
        s = ""
        d = iter(self.u.txd._ag.data)
        for bit in d:
            self.assertEqual(bit.vld_mask, 0b1)
            _bit = valToInt(bit)

            if _bit == START_BIT:
                ch = 0
                for i in range(10 - 1):
                    b = next(d)
                    self.assertEqual(b.vld_mask, 0b1)
                    _b = valToInt(b)
                    if i == 8:
                        self.assertEqual(_b, STOP_BIT)
                    else:
                        ch |= _b << i

                s = s + chr(ch)

        return s

    def sendStr(self, string):
        for ch in string:
            self.u.dataIn._ag.data.append(ord(ch))

    def test_nop(self):
        self.runSim(20 * CLK_PERIOD)
        self.assertEqual(self.getStr(), "")

    def test_simple(self):
        t = "simple"
        self.sendStr(t)
        self.runSim(10 * (len(t) + 10) * CLK_PERIOD)
        self.assertEqual(self.getStr(), t)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(UartTxTC('test_multiple_randomized2'))
    suite.addTest(unittest.makeSuite(UartTxTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
