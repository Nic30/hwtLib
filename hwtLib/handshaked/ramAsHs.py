#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import Handshaked, BramPort_withoutClk
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.interfaces.addrDataHs import AddrDataHs
from pycocotb.agents.base import AgentBase
from pycocotb.hdlSimulator import HdlSimulator


class RamHsRAgent(AgentBase):
    """
    Composite agent with agent for addr and data channel
    enable is shared
    """

    @property
    def enable(self):
        return self.__enable

    @enable.setter
    def enable(self, v):
        """
        Distribute change of enable on child agents
        """
        self.__enable = v

        for o in [self.req, self.r]:
            o.enable = v

    def __init__(self, sim: HdlSimulator, intf):
        self.__enable = True
        self.intf = intf

        intf.addr._initSimAgent(sim)
        self.addr = intf.addr._ag

        intf.data._initSimAgent(sim)
        self.data = intf.data._ag

    def getDrivers(self):
        return (self.addr.getDrivers() +
                self.data.getMonitors()
                )

    def getMonitors(self):
        return (self.addr.getMonitors() +
                self.data.getDrivers()
                )


class RamHsR(Interface):
    """
    Handshaked RAM port
    """
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        a = self.addr = Handshaked()
        a.DATA_WIDTH = self.ADDR_WIDTH
        with self._paramsShared():
            self.data = Handshaked(masterDir=DIRECTION.IN)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = RamHsRAgent(sim, self)


@serializeParamsUniq
class RamAsHs(Unit):
    """
    Converter from ram port to handshaked interfaces

    .. hwt-schematic::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.r = RamHsR()
            self.w = AddrDataHs()
            self.ram = BramPort_withoutClk()._m()

    def _impl(self):
        r = self.r
        w = self.w
        ram = self.ram

        readRegEmpty = self._reg("readRegEmpty", def_val=1)
        readDataPending = self._reg("readDataPending", def_val=0)
        readData = self._reg("readData", r.data.data._dtype)

        rEn = readRegEmpty | r.data.rd
        readDataPending(r.addr.vld & rEn)
        If(readDataPending,
           readData(ram.dout)
        )

        If(r.data.rd,
            readRegEmpty(~readDataPending)
        ).Else(
            readRegEmpty(~(readDataPending | ~readRegEmpty))

        )

        r.addr.rd(rEn)

        If(rEn & r.addr.vld,
           ram.we(0),
           ram.addr(r.addr.data) 
        ).Else(
           ram.we(1),
           ram.addr(w.addr)
        )
        wEn = ~rEn | ~r.addr.vld
        w.rd(wEn)

        ram.din(w.data)
        ram.en((rEn & r.addr.vld) | w.vld)
        r.data.data(readData)
        r.data.vld(~readRegEmpty)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = RamAsHs()
    print(toRtl(u))
