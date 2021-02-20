#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import valToInt
from hwtLib.peripheral.uart.rx import UartRx
from hwtSimApi.constants import CLK_PERIOD
from pyMathBitPrecise.bit_utils import get_bit


class UartRxBasicTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = UartRx()
        u.OVERSAMPLING = cls.OVERSAMPLING = 16
        u.FREQ = cls.FREQ = 115200 * cls.OVERSAMPLING
        u.BAUD = cls.BAUD = 115200
        cls.compileSim(u)

    def getStr(self):
        s = ""
        for d in self.u.dataOut._ag.data:
            ch = valToInt(d)
            s += chr(ch)

        return s

    def sendStr(self, string):
        START_BIT = 0
        STOP_BIT = 1

        rx = self.u.rxd._ag.data
        os = self.FREQ // self.BAUD
        for ch in string:
            rx.extend([START_BIT for _ in range(os)])
            for i in range(8):
                d = get_bit(ord(ch), i)
                rx.extend([d for _ in range(os)])
            rx.extend([STOP_BIT for _ in range(os)])

    def test_nop(self):
        self.u.rxd._ag.data.append(1)
        self.runSim(200 * Time.ns,)
        self.assertEqual(self.getStr(), "")

    def test_simple(self):
        t = "simple"
        self.sendStr(t)
        self.runSim(self.OVERSAMPLING *
                    (self.FREQ // self.BAUD) * (len(t) + 5) * CLK_PERIOD)
        self.assertEqual(self.getStr(), t)


class UartRxTC(UartRxBasicTC):

    @classmethod
    def setUpClass(cls):
        cls.OVERSAMPLING = 16
        cls.FREQ = 115200 * cls.OVERSAMPLING * 4
        cls.BAUD = 115200

        u = cls.u = UartRx()
        u.BAUD = cls.BAUD
        u.FREQ = cls.FREQ
        u.OVERSAMPLING = cls.OVERSAMPLING
        cls.compileSim(u)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(UartRxTC('test_simple'))
    suite.addTest(unittest.makeSuite(UartRxBasicTC))
    suite.addTest(unittest.makeSuite(UartRxTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
