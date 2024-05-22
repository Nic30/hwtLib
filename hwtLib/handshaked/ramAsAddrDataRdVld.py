#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.constants import DIRECTION
from hwt.hwIO import HwIO
from hwt.hwIOs.agents.universalComposite import UniversalCompositeAgent
from hwt.hwIOs.std import HwIODataRdVld, HwIOBramPort_noClk
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.serializer.mode import serializeParamsUniq
from hwtLib.commonHwIO.addr_data import HwIOAddrDataRdVld
from hwtSimApi.hdlSimulator import HdlSimulator
from hwt.pyUtils.typingFuture import override


class HwIORamRdVldR(HwIO):
    """
    HwIODataRdVld RAM port

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(8)
        self.DATA_WIDTH = HwParam(8)

    @override
    def hwDeclr(self):
        a = self.addr = HwIODataRdVld()
        a.DATA_WIDTH = self.ADDR_WIDTH
        with self._hwParamsShared():
            self.data = HwIODataRdVld(masterDir=DIRECTION.IN)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = UniversalCompositeAgent(sim, self)


@serializeParamsUniq
class RamAsAddrDataRdVld(HwModule):
    """
    Converter from a single ram port to handshaked interfaces

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        HwIOBramPort_noClk.hwConfig(self)

    @override
    def hwDeclr(self):
        assert self.HAS_R or self.HAS_W
        addClkRstn(self)
        with self._hwParamsShared():
            if self.HAS_R:
                self.r = HwIORamRdVldR()
            if self.HAS_W:
                self.w = HwIOAddrDataRdVld()
                self.w.HAS_MASK = self.HAS_BE

            self.ram = HwIOBramPort_noClk()._m()

    def read_logic(self, r: HwIORamRdVldR, ram: HwIOBramPort_noClk):
        readDataPending = self._reg("readDataPending", def_val=0)
        readData = self._reg("readData",
                             HStruct((r.data.data._dtype, "data"),
                                     (BIT, "vld")),
                             def_val={"vld": 0}
                             )
        readDataOverflow = self._reg("readDataOverflow",
                                     readData._dtype, def_val={"vld": 0})

        rEn = (~readDataOverflow.vld | r.data.rd) & (~readData.vld | r.data.rd)
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
               # pop data from readDataOverflow register
               readData.data(readDataOverflow.data),
               readData.vld(readDataOverflow.vld),
               readDataOverflow.vld(0)
            )
        )

        r.addr.rd(rEn)

        return rEn, readData

    @override
    def hwImpl(self):
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
    from hwt.synth import to_rtl_str
    
    m = RamAsAddrDataRdVld()
    print(to_rtl_str(m))
