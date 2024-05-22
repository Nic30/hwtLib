#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIORegCntrl
from hwt.hwIOs.utils import addClkRstn
from hwt.serializer.mode import serializeOnce
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


@serializeOnce
class FlipRegister(HwModule):
    """
    Switchable register, there are two registers and two sets of ports,
    Each set of ports is every time connected to opposite reg.
    By select you can choose between regs.

    This component is meant to be form of synchronization.
    Example first reg is connected to first set of ports, writer performs actualizations
    on first reg and reader reads data from second ram by second set of ports.

    Then select is set and access is flipped. Reader now has access to reg 0 and writer to reg 1.

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(32)
        self.DEFAULT_VAL = HwParam(0)

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            addClkRstn(self)
            self.first = HwIORegCntrl()
            self.second = HwIORegCntrl()

            self.select_sig = HwIOSignal()

    def connectWriteHwIO(self, regA, regB):
        return [
            If(self.first.dout.vld,
                regA(self.first.dout.data)
            ),
            If(self.second.dout.vld,
               regB(self.second.dout.data)
            )
        ]

    def connectReadHwIO(self, regA, regB):
        return [
            self.first.din(regA),
            self.second.din(regB)
        ]

    @override
    def hwImpl(self):
        first = self._reg("first_reg", HBits(self.DATA_WIDTH), def_val=self.DEFAULT_VAL)
        second = self._reg("second_reg", HBits(self.DATA_WIDTH), def_val=self.DEFAULT_VAL)

        If(self.select_sig,
           self.connectReadHwIO(second, first),
           self.connectWriteHwIO(second, first)
        ).Else(
           self.connectReadHwIO(first, second),
           self.connectWriteHwIO(first, second)
        )


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = FlipRegister()
    print(to_rtl_str(m))
