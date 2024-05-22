#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hwIOs.std import HwIOSignal, HwIORdVldSync, \
    HwIORegCntrl
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeOnce
from hwtLib.mem.atomic.flipReg import FlipRegister


@serializeOnce
class FlipCntr(HwModule):
    """
    Counter with FlipRegister which is form memory with atomic access

    interface doFilip drives switching of memories in flip register
    dataIn has higher priority than doIncr

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(18)

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            addClkRstn(self)
            self.doIncr = HwIOSignal()
            self.doFlip = HwIORdVldSync()
            self.data = HwIORegCntrl()
            self.cntr = FlipRegister()

    def flipHandler(self):
        self.doFlip.rd(1)

        flipSt = self._reg("flipState", def_val=0)
        If(self.doFlip.vld,
            flipSt(~flipSt)
        )
        self.cntr.select_sig(flipSt)

    def dataHanldler(self):
        cntr = self.cntr
        cntr.first.dout.data(cntr.first.din + 1)
        cntr.first.dout.vld(self.doIncr)

        cntr.second(self.data)

    @override
    def hwImpl(self):
        propagateClkRstn(self)
        self.flipHandler()
        self.dataHanldler()


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = FlipCntr()
    print(to_rtl_str(m))
