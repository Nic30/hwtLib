#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, If, Switch
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.constants import BURST_INCR, CACHE_DEFAULT, LOCK_DEFAULT, \
    PROT_DEFAULT, BYTES_IN_TRANS, QOS_DEFAULT
from hwtLib.types.ctypes import uint32_t
from pyMathBitPrecise.bit_utils import mask


class Axi4streamToMem(Unit):
    """
    Most simple DMA for AXI4 interface.

    * 0x0 control reg.
        * bit 0, rw - on/off (1 means on)
        * bit 1, r  - idle (1 if no transaction in progress)

    0x4 baseAddr

    Length of written data is specified by DATA_LEN.
    Input data is splited on smaller frames to fit MAX_BUTST_LEN.

    If there is transaction pending idle flag is 0,
    if on/off is set to 0 in this state
    unit continues until all data are send and then stays off.
    This could be use as synchronization with the software.

    1) driver enables this unit, then tests while not idle.
    2) then waits while idle.
    3) then reads the data and back to 1

    or unit is enabled and driver disables it only for the time of reading.

    .. hwt-autodoc::
    """
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)
        self.CNTRL_AW = Param(5)

        # size of data which should be transfered in worlds
        self.DATA_LEN = Param(33)
        self.MAX_BUTST_LEN = Param(16)
        self.REGISTER_MAP = HStruct(
                             (uint32_t, "control"),
                             (uint32_t, "baseAddr")
                             )

    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.axi = Axi4()._m()
            self.axi.HAS_R = False
            self.dataIn = Handshaked()
        cntrl = self.cntrlBus = Axi4Lite()
        regs = self.regsConventor = AxiLiteEndpoint(self.REGISTER_MAP)

        cntrl.ADDR_WIDTH = self.CNTRL_AW
        cntrl.DATA_WIDTH = self.DATA_WIDTH

        regs.ADDR_WIDTH = self.CNTRL_AW
        regs.DATA_WIDTH = self.DATA_WIDTH

    def axiWAddrHandler(self, st, baseAddr, actualAddr, lenRem):
        """
        AXI write addr logic
        """
        axi = self.axi
        st_t = st._dtype

        axi.aw.valid(st._eq(st_t.writeAddr))
        axi.aw.addr(actualAddr)
        axi.aw.id(0)
        axi.aw.burst(BURST_INCR)
        axi.aw.cache(CACHE_DEFAULT)

        If(lenRem > self.MAX_BUTST_LEN,
            axi.aw.len(self.MAX_BUTST_LEN - 1)
        ).Else(
            axi.aw.len(lenRem - 1, fit=True)
        )
        axi.aw.lock(LOCK_DEFAULT)
        axi.aw.prot(PROT_DEFAULT)
        axi.aw.size(BYTES_IN_TRANS(self.DATA_WIDTH // 8))
        axi.aw.qos(QOS_DEFAULT)

        # lenRem, actualAddr logic
        Switch(st)\
        .Case(st_t.fullIdle,
            lenRem(self.DATA_LEN),
            actualAddr(baseAddr)
        ).Case(st_t.writeAddr,
            If(axi.aw.ready,
                If(lenRem > self.MAX_BUTST_LEN,
                   actualAddr(actualAddr + (self.MAX_BUTST_LEN * self.DATA_WIDTH // 8)),
                   lenRem(lenRem - self.MAX_BUTST_LEN)
                ).Else(
                   actualAddr(actualAddr + fitTo(lenRem, actualAddr)),
                   lenRem(0)
                )
            )
        )

    def connectRegisters(self, st, onoff, baseAddr):
        """
        connection of AXI-lite registers
        """
        idle = st._eq(st._dtype.fullIdle)
        regs = self.regsConventor.decoded
        regs.control.din(Concat(onoff, idle,
                                Bits(self.DATA_WIDTH - 2).from_py(0)))

        If(regs.control.dout.vld,
           onoff(regs.control.dout.data[0])
        )

        regs.baseAddr.din(baseAddr)
        If(regs.baseAddr.dout.vld,
           baseAddr(regs.baseAddr.dout.data)
        )

    def mainFsm(self, st, onoff, lenRem, actualLenRem):
        axi = self.axi
        st_t = st._dtype

        w_ackAll = self.w_allAck(st)

        Switch(st)\
        .Case(st_t.fullIdle,
            If(onoff,
                st(st_t.writeAddr)
            )
        ).Case(st_t.writeAddr,
            If(axi.aw.ready,
                If(lenRem._eq(1),
                   st(st_t.writeDataLast)
                ).Else(
                   st(st_t.writeData)
                )
            )
        ).Case(st_t.writeData,
            If(w_ackAll & (actualLenRem._eq(2)),
               st(st_t.writeDataLast)
            )
        ).Case(st_t.writeDataLast,
            If(w_ackAll,
                If(lenRem != 0,
                   st(st_t.writeAddr)
                ).Else(
                   st(st_t.fullIdle)
                )
            )
        )

    def w_allAck(self, st):
        """
        In this clk data word will be transfered
        """
        st_t = st._dtype
        w_en = st._eq(st_t.writeData) | st._eq(st_t.writeDataLast)
        return w_en & self.dataIn.vld & self.axi.w.ready

    def dataWFeed(self, st, lenRem, actualLenRem):
        """
        Connection between din and axi.w channel
        """
        w = self.axi.w
        din = self.dataIn
        st_t = st._dtype

        last = st._eq(st_t.writeDataLast)
        w_en = st._eq(st_t.writeData) | last

        w.valid(din.vld & w_en)
        w.data(din.data)

        w.strb(mask(w.strb._dtype.bit_length()))
        w.last(last)

        din.rd(w_en & w.ready)

        w_allAck = self.w_allAck(st)

        # actualLenRem driver
        Switch(st)\
        .Case(st_t.writeData,
            If(w_allAck,
                actualLenRem(actualLenRem - 1)
            )
        ).Case(st_t.writeDataLast,
            If(w_allAck,
               actualLenRem(0)
            )
        ).Default(
            If(lenRem > self.MAX_BUTST_LEN,
               actualLenRem(self.MAX_BUTST_LEN)
            ).Else(
               actualLenRem(lenRem, fit=True)
            )
        )

    def _impl(self):
        propagateClkRstn(self)
        self.regsConventor.bus(self.cntrlBus)
        axi = self.axi

        axi.b.ready(1)  # we do ignore write confirmations

        st_t = HEnum("state_type", ["fullIdle", "writeAddr", "writeData",
                                    "writeDataLast"])

        onoff = self._reg("on_off_reg", def_val=0)
        baseAddr = self._reg("baseAddr_reg", Bits(self.ADDR_WIDTH), 0)
        st = self._reg("state_reg", st_t, st_t.fullIdle)
        actualAddr = self._reg("actualAddr_reg", Bits(self.ADDR_WIDTH))
        lenRem = self._reg("lenRem_reg",
                           Bits(int(self.DATA_LEN).bit_length() + 1),
                           self.DATA_LEN)
        actualLenRem = self._reg("actualLenRem_reg", axi.aw.len._dtype)

        self.connectRegisters(st, onoff, baseAddr)
        self.axiWAddrHandler(st, baseAddr, actualAddr, lenRem)
        self.mainFsm(st, onoff, lenRem, actualLenRem)
        self.dataWFeed(st, lenRem, actualLenRem)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Axi4streamToMem()
    # u = AxiLiteRegs(Axi4streamToMem().REGISTER_MAP)
    print(to_rtl_str(u))
