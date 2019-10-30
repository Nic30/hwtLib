#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.interfaces.std import Signal, HandshakeSync, \
    RegCntrl
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.mode import serializeOnce
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.mem.atomic.flipReg import FlipRegister


@serializeOnce
class FlipCntr(Unit):
    """
    Counter with FlipRegister which is form memory with atomic access

    interface doFilip drives switching of memories in flip register
    dataIn has higher priority than doIncr
    
    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(18)

    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.doIncr = Signal()
            self.doFlip = HandshakeSync()
            self.data = RegCntrl()
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

    def _impl(self):
        propagateClkRstn(self)
        self.flipHandler()
        self.dataHanldler()


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = FlipCntr()
    print(toRtl(u))
