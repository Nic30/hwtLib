#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import BramPort, Clk, BramPort_withoutClk
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit


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
        self.R_PORT_CNT = Param(None)
        self.W_PORT_CNT = Param(None)

    def _declr(self):
        PORTS = self.PORT_CNT
        R_PORTS = self.R_PORT_CNT 
        W_PORTS = self.W_PORT_CNT 
        if PORTS is not None:
            assert R_PORTS is None, "Do not spefify PORT_CNT if you want to use R/W_PORT_CNT"
            assert W_PORTS is None, "Do not spefify PORT_CNT if you want to use R/W_PORT_CNT"
            R_PORTS = W_PORTS = PORTS
        else:
            if R_PORTS is None:
                R_PORTS = 0
            if W_PORTS is None:
                W_PORTS = 0
            PORTS = max(R_PORTS, W_PORTS)

        self.clk = Clk()
        with self._paramsShared():
            ports = HObjList()
            for i in range(PORTS):
                p = BramPort_withoutClk()
                p.HAS_R = i < R_PORTS
                p.HAS_W = i < W_PORTS
                ports.append(p)

            self.port = ports

    @staticmethod
    def connectPort(clk: RtlSignal, port: BramPort_withoutClk, mem: RtlSignal):
        if port.HAS_R and port.HAS_W:
            If(clk._onRisingEdge() & port.en,
               If(port.we,
                  mem[port.addr](port.din)
               ),
               port.dout(mem[port.addr])
            )
        elif port.HAS_R:
            If(clk._onRisingEdge() & port.en,
               port.dout(mem[port.addr])
            )
        elif port.HAS_W:
            If(clk._onRisingEdge() & port.en,
                mem[port.addr](port.din)
            )
        else:
            raise AssertionError("Bram port has to have at least write or read part")

    def _impl(self):
        dt = Bits(self.DATA_WIDTH)[2 ** self.ADDR_WIDTH]
        self._mem = self._sig("ram_memory", dt)

        for p in self.port:
            self.connectPort(self.clk, p, self._mem)


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

    def _impl(self):
        dt = Bits(self.DATA_WIDTH)[2 ** self.ADDR_WIDTH]
        self._mem = self._sig("ram_memory", dt)

        RamSingleClock.connectPort(self.a.clk, self.a, self._mem)


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
        RamSingleClock.connectPort(self.b.clk, self.b, self._mem)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(Ram_sp()))
