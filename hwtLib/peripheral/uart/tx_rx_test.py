#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Handshaked, VldSynced
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.agentConnector import valToInt
from hwt.simulator.simTestCase import SingleUnitSimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit

from hwtLib.peripheral.uart.rx import UartRx
from hwtLib.peripheral.uart.tx import UartTx
from pycocotb.constants import CLK_PERIOD


class TestUnit_uart(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.FREQ = Param(115200*16)
        self.BAUD = Param(115200)
        self.OVERSAMPLING = Param(16)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.din = Handshaked()
            self.dout = VldSynced()._m()

            self.tx = UartTx()
            self.rx = UartRx()

    def _impl(self):
        propagateClkRstn(self)
        self.rx.rxd(self.tx.txd)
        self.tx.dataIn(self.din)
        self.dout(self.rx.dataOut)


class UartTxRxTC(SingleUnitSimTestCase):

    @classmethod
    def getUnit(cls):
        u = cls.u = TestUnit_uart()
        u.BAUD = 115200
        u.FREQ = 115200 * 16
        u.OVERSAMPLING = 16
        return u

    def getStr(self):
        return "".join([chr(valToInt(d)) for d in self.u.dout._ag.data])

    def sendStr(self, string):
        for s in string:
            self.u.din._ag.data.append(ord(s))

    def test_nop(self):
        self.runSim(20 * CLK_PERIOD)
        self.assertEqual(self.getStr(), "")

    def test_simple(self):
        t = "simple"
        self.sendStr(t)
        self.runSim(10 * (len(t) * 16 + 10) * CLK_PERIOD)
        self.assertEqual(self.getStr(), t)


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(UartTxTC('test_multiple_randomized2'))
    suite.addTest(unittest.makeSuite(UartTxRxTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
