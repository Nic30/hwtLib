#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.constants import DIRECTION
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.agents.universalComposite import UniversalCompositeAgent
from hwt.interfaces.std import Handshaked, BramPort_withoutClk
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.common_nonstd_interfaces.addr_data_hs import AddrDataHs
from hwtSimApi.hdlSimulator import HdlSimulator


class RamHsR(Interface):
    """
    Handshaked RAM port

    .. hwt-autodoc::
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
        self._ag = UniversalCompositeAgent(sim, self)


@serializeParamsUniq
class RamAsHs(Unit):
    """
    Converter from a single ram port to handshaked interfaces

    .. hwt-autodoc::
    """

    def _config(self):
        BramPort_withoutClk._config(self)

    def _declr(self):
        assert self.HAS_R or self.HAS_W
        addClkRstn(self)
        with self._paramsShared():
            if self.HAS_R:
                self.r = RamHsR()
            if self.HAS_W:
                self.w = AddrDataHs()
                self.w.HAS_MASK = self.HAS_BE

            self.ram = BramPort_withoutClk()._m()

    def read_logic(self, r: RamHsR, ram: BramPort_withoutClk):
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

        return rEn, readData

    def _impl(self):
        ram = self.ram
        if self.HAS_R:
            r = self.r
            rEn, readData = self.read_logic(r, ram)

            if self.HAS_W:
                # read/write
                w = self.w
                if self.HAS_BE:
                    ram.be(w.mask)
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
            else:
                # read only
                ram.addr(r.addr.data)
                ram.en(rEn & r.addr.vld)
                r.data.data(readData.data)
                r.data.vld(readData.vld)

        elif self.HAS_W:
            # write only
            w = self.w
            w.rd(1)
            if self.HAS_BE:
                ram.we(w.mask)
            ram.addr(w.addr)
            ram.din(w.data)
            ram.en(w.vld)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = RamAsHs()
    print(to_rtl_str(u))
