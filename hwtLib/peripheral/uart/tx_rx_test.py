#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hwIOs.std import HwIODataRdVld, HwIODataVld
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.utils import Bits3valToInt
from hwtLib.peripheral.uart.rx import UartRx
from hwtLib.peripheral.uart.tx import UartTx
from hwtSimApi.utils import freq_to_period


class TestHwModule_uart(HwModule):

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(8)
        self.CLK_FREQ = HwParam(115200 * 16)
        self.BAUD = HwParam(115200)
        self.OVERSAMPLING = HwParam(16)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.din = HwIODataRdVld()
            self.dout = HwIODataVld()._m()

            self.tx = UartTx()
            self.rx = UartRx()

    @override
    def hwImpl(self):
        propagateClkRstn(self)
        self.rx.rxd(self.tx.txd)
        self.tx.dataIn(self.din)
        self.dout(self.rx.dataOut)


class UartTxRxTC(SimTestCase):

    @classmethod
    @override
    def setUpClass(cls):
        dut = cls.dut = TestHwModule_uart()
        dut.BAUD = 115200
        dut.CLK_FREQ = 115200 * 16
        dut.OVERSAMPLING = 16
        cls.CLK_PERIOD = int(freq_to_period(dut.CLK_FREQ))
        cls.compileSim(dut)

    def getStr(self):
        return "".join([chr(Bits3valToInt(d)) for d in self.dut.dout._ag.data])

    def sendStr(self, string):
        for s in string:
            self.dut.din._ag.data.append(ord(s))

    def test_nop(self):
        self.runSim(20 * self.CLK_PERIOD)
        self.assertEqual(self.getStr(), "")

    def test_simple(self):
        t = "simple"
        self.sendStr(t)
        self.runSim(10 * (len(t) * 16 + 10) * self.CLK_PERIOD)
        self.assertEqual(self.getStr(), t)


if __name__ == "__main__":
    import unittest
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([UartTxRxTC("test_multiple_randomized2")])
    suite = testLoader.loadTestsFromTestCase(UartTxRxTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
