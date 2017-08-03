#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, power
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import BramPort, Clk, BramPort_withoutClk
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param


@serializeParamsUniq
class RamSingleClock(Unit):

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.ADDR_WIDTH = Param(4)
        self.PORT_CNT = Param(1)

    def _declr(self):
        PORTS = int(self.PORT_CNT)

        self.clk = Clk()
        with self._paramsShared():
            self.a = BramPort_withoutClk()
            for i in range(PORTS - 1):
                name = self.genPortName(i + 1)
                setattr(self, name, BramPort_withoutClk())

    @staticmethod
    def genPortName(index):
        return chr(ord('a') + index)

    def getPortByIndx(self, index):
        return getattr(self, self.genPortName(index))

    def connectPort(self, port, mem):
        If(self.clk._onRisingEdge() & port.en,
           If(port.we,
              mem[port.addr] ** port.din
           ),
           port.dout ** mem[port.addr]
        )

    def _impl(self):
        PORTS = int(self.PORT_CNT)
        dt = vecT(self.DATA_WIDTH)[power(2, self.ADDR_WIDTH)]
        self._mem = self._sig("ram_memory", dt)

        for i in range(PORTS):
            self.connectPort(getattr(self, self.genPortName(i)), self._mem)


@serializeParamsUniq
class Ram_sp(Unit):
    """
    Write first variant
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.ADDR_WIDTH = Param(4)

    def _declr(self):
        with self._paramsShared():
            self.a = BramPort()

    def connectPort(self, port, mem):
        If(port.clk._onRisingEdge() & port.en,
           If(port.we,
              mem[port.addr] ** port.din
           ),
           port.dout ** mem[port.addr]
        )

    def _impl(self):
        dt = vecT(self.DATA_WIDTH)[power(2, self.ADDR_WIDTH)]
        self._mem = self._sig("ram_memory", dt)

        self.connectPort(self.a, self._mem)


class Ram_dp(Ram_sp):
    def _declr(self):
        super()._declr()
        with self._paramsShared():
            self.b = BramPort()

    def _impl(self):
        super()._impl()
        self.connectPort(self.b, self._mem)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(Ram_dp()))
