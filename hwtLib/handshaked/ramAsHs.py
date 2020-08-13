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
from pycocotb.agents.base import AgentBase
from pycocotb.hdlSimulator import HdlSimulator

from hwtLib.interfaces.addr_data_hs import AddrDataHs
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.defs import BIT


class RamHsRAgent(AgentBase):
    """
    Composite agent with agent for addr and data channel
    enable is shared
    """

    def getEnable(self):
        return self.__enable

    def setEnable(self, v):
        """
        Distribute change of enable on child agents
        """
        self.__enable = v
        for o in (self.addr, self.data):
            o.setEnable(v)

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

        readDataPending = self._reg("readDataPending", def_val=0)
        readData = self._reg("readData",
                             HStruct((r.data.data._dtype, "data"),
                                     (BIT, "vld")),
                             def_val={"vld": 0}
                             )
        readDataOverflow = self._reg("readDataOverflow",
                                     readData._dtype, def_val={"vld": 0})

        rEn = ~readDataOverflow.vld & (~readData.vld | r.data.rd)
        readDataPending(r.addr.vld & rEn)
        If(readDataPending,
            If(~readData.vld | r.data.rd,
                # can store directly to readData register
                readData.data(ram.dout),
                readData.vld(1),
                readDataOverflow.vld(0),
            ).Else(
                # need to store to overflow register
                readDataOverflow.data(ram.dout),
                readDataOverflow.vld(1),
            ),
        ).Else(
            If(r.data.rd,
               readData.data(readDataOverflow.data),
               readData.vld(readDataOverflow.vld),
               readDataOverflow.vld(0)
            )
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
        r.data.data(readData.data)
        r.data.vld(readData.vld)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = RamAsHs()
    print(to_rtl_str(u))
