#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import Bits3valToInt
from hwtLib.peripheral.uart.rx import UartRx
from hwtSimApi.utils import freq_to_period
from pyMathBitPrecise.bit_utils import get_bit


class UartRxBasicTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = UartRx()
        dut.OVERSAMPLING = cls.OVERSAMPLING = 16
        dut.FREQ = cls.FREQ = 115200 * cls.OVERSAMPLING
        dut.BAUD = cls.BAUD = 115200
        cls.CLK_PERIOD = int(freq_to_period(dut.FREQ))
        cls.compileSim(dut)

    def getStr(self):
        s = ""
        for d in self.dut.dataOut._ag.data:
            ch = Bits3valToInt(d)
            s += chr(ch)

        return s

    def sendStr(self, string):
        START_BIT = 0
        STOP_BIT = 1

        rx = self.dut.rxd._ag.data
        os = self.FREQ // self.BAUD
        for ch in string:
            rx.extend([START_BIT for _ in range(os)])
            for i in range(8):
                d = get_bit(ord(ch), i)
                rx.extend([d for _ in range(os)])
            rx.extend([STOP_BIT for _ in range(os)])

    def test_nop(self):
        self.dut.rxd._ag.data.append(1)
        self.runSim(20 * self.CLK_PERIOD)
        self.assertEqual(self.getStr(), "")

    def test_simple(self):
        t = "simple"
        self.sendStr(t)
        self.runSim(self.OVERSAMPLING *
                    (self.FREQ // self.BAUD) * (len(t) + 5) * self.CLK_PERIOD)
        self.assertEqual(self.getStr(), t)


class UartRxTC(UartRxBasicTC):

    @classmethod
    def setUpClass(cls):
        cls.OVERSAMPLING = 16
        cls.FREQ = 115200 * cls.OVERSAMPLING * 4
        cls.BAUD = 115200

        dut = cls.dut = UartRx()
        dut.BAUD = cls.BAUD
        dut.FREQ = cls.FREQ
        dut.OVERSAMPLING = cls.OVERSAMPLING
        cls.CLK_PERIOD = int(freq_to_period(dut.FREQ))
        cls.compileSim(dut)


if __name__ == "__main__":
    import unittest
    _ALL_TCs = [UartRxBasicTC, UartRxTC]
    testLoader = unittest.TestLoader()
    loadedTcs = [testLoader.loadTestsFromTestCase(tc) for tc in _ALL_TCs]
    suite = unittest.TestSuite(loadedTcs)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
