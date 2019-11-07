#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import BramPort, Clk, BramPort_withoutClk
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


@serializeParamsUniq
class RamSingleClock(Unit):
    """
    RAM with only one clock signal

    .. hwt-schematic::
    """
    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.ADDR_WIDTH = Param(4)
        self.PORT_CNT = Param(1)

    def _declr(self):
        PORTS = int(self.PORT_CNT)

        self.clk = Clk()
        with self._paramsShared():
            # to let IDEs resolve type of port
            self.a = BramPort_withoutClk()

            for i in range(PORTS - 1):
                self._sportPort(i + 1)

    def _sportPort(self, index) -> None:
        name = self.genPortName(index)
        setattr(self, name, BramPort_withoutClk())

    @staticmethod
    def genPortName(index) -> str:
        return chr(ord('a') + index)

    def getPortByIndx(self, index) -> BramPort_withoutClk:
        return getattr(self, self.genPortName(index))

    def connectPort(self, port: BramPort_withoutClk, mem: RtlSignal):
        If(self.clk._onRisingEdge() & port.en,
           If(port.we,
              mem[port.addr](port.din)
           ),
           port.dout(mem[port.addr])
        )

    def _impl(self):
        PORTS = int(self.PORT_CNT)
        dt = Bits(self.DATA_WIDTH)[2 ** self.ADDR_WIDTH]
        self._mem = self._sig("ram_memory", dt)

        for i in range(PORTS):
            self.connectPort(getattr(self, self.genPortName(i)), self._mem)


@serializeParamsUniq
class Ram_sp(Unit):
    """
    Single port RAM, write-first variant

    .. hwt-schematic::
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
              mem[port.addr](port.din)
           ),
           port.dout(mem[port.addr])
        )

    def _impl(self):
        dt = Bits(self.DATA_WIDTH)[2 ** self.ADDR_WIDTH]
        self._mem = self._sig("ram_memory", dt)

        self.connectPort(self.a, self._mem)


class Ram_dp(Ram_sp):
    """
    True dual port RAM.
    :note: write-first variant 

    .. hwt-schematic::
    """
    def _declr(self):
        super()._declr()
        with self._paramsShared():
            self.b = BramPort()

    def _impl(self):
        super()._impl()
        self.connectPort(self.b, self._mem)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(Ram_sp()))
