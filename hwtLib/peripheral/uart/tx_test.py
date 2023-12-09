#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import valToInt
from hwtLib.peripheral.uart.tx import UartTx
from hwtSimApi.utils import freq_to_period


class UartTxTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = UartTx()
        u.BAUD = 115200
        u.FREQ = 115200
        cls.CLK_PERIOD = int(freq_to_period(u.FREQ))
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
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
        self.runSim(20 * self.CLK_PERIOD)
        self.assertEqual(self.getStr(), "")

    def test_simple(self):
        t = "simple"
        self.sendStr(t)
        self.runSim((len(t) + 10) * self.CLK_PERIOD * self.u.BAUD)
        self.assertEqual(self.getStr(), t)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([UartTxTC("test_multiple_randomized2")])
    suite = testLoader.loadTestsFromTestCase(UartTxTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
