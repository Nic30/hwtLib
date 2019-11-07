#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, RegCntrl
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.mode import serializeOnce
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param


@serializeOnce
class FlipRegister(Unit):
    """
    Switchable register, there are two registers and two sets of ports,
    Each set of ports is every time connected to opposite reg.
    By select you can choose between regs.

    This component is meant to be form of synchronization.
    Example first reg is connected to first set of ports, writer performs actualizations
    on first reg and reader reads data from second ram by second set of ports.

    Then select is set and access is flipped. Reader now has access to reg 0 and writer to reg 1.
    
    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.DEFAULT_VAL = Param(0)

    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.first = RegCntrl()
            self.second = RegCntrl()

            self.select_sig = Signal()

    def connectWriteIntf(self, regA, regB):
        return [
            If(self.first.dout.vld,
                regA(self.first.dout.data)
            ),
            If(self.second.dout.vld,
               regB(self.second.dout.data)
            )
        ]

    def connectReadIntf(self, regA, regB):
        return [
            self.first.din(regA),
            self.second.din(regB)
        ]

    def _impl(self):
        first = self._reg("first_reg", Bits(self.DATA_WIDTH), def_val=self.DEFAULT_VAL)
        second = self._reg("second_reg", Bits(self.DATA_WIDTH), def_val=self.DEFAULT_VAL)

        If(self.select_sig,
           self.connectReadIntf(second, first),
           self.connectWriteIntf(second, first)
        ).Else(
           self.connectReadIntf(first, second),
           self.connectWriteIntf(first, second)
        )


if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.utils import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    u = FlipRegister()
    print(toRtl(u))
