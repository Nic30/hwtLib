#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat
from hwt.hdl.typeShortcuts import hBit
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit

from hwtLib.clocking.clkBuilder import ClkBuilder


# http://ece-research.unm.edu/jimp/vhdl_fpgas/slides/UART.pdf
class UartTx(Unit):
    """
    UART Tx channel controller

    .. hwt-schematic::
    """
    def _config(self):
        self.FREQ = Param(int(100e6))
        # number of bits per second
        self.BAUD = Param(115200)
        # self.PARITY = Param(None)

    def _declr(self):
        addClkRstn(self)
        self.dataIn = Handshaked()
        self.dataIn.DATA_WIDTH = 8
        self.txd = Signal()._m()

    def _impl(self):
        propagateClkRstn(self)
        r = self._reg

        START_BIT = hBit(0)
        STOP_BIT = hBit(1)
        BITS_TO_SEND = 1 + 8 + 1
        BIT_RATE = self.FREQ // self.BAUD

        assert BIT_RATE >= 1

        din = self.dataIn

        data = r("data", Bits(BITS_TO_SEND))  # data + start bit + stop bit
        en = r("en", def_val=False)
        tick, last = ClkBuilder(self, self.clk).timers(
                                                       [BIT_RATE, BIT_RATE * BITS_TO_SEND],
                                                       en)

        If(~en & din.vld,
           data(Concat(STOP_BIT, din.data, START_BIT)),
           en(1)
        ).Elif(tick & en,
            # srl where 1 is shifted from left
            data(hBit(1)._concat(data[:1])),
            If(last,
               en(0),
            )
        )
        din.rd(~en)

        txd = r("reg_txd", def_val=1)
        If(tick & en,
           txd(data[0])
        )
        self.txd(txd)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = UartTx()
    print(toRtl(u))
