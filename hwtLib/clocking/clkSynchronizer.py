#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.defs import BIT
from hwt.interfaces.std import Rst, Signal, Clk
from hwt.synthesizer.unit import Unit


# http://www.sunburst-design.com/papers/CummingsSNUG2008Boston_CDC.pdf
class ClkSynchronizer(Unit):
    """
    Signal synchronization between two clock domains

    :attention: multibits signals should not be sychronized using this sychronizer
        instead handshake or req-ack sychronization should be used for controll signals
        and main data should be passed over couble of registers

    .. hwt-schematic::
    """

    def _config(self):
        self.DATA_TYP = BIT

    def _declr(self):
        self.rst = Rst()

        self.inClk = Clk()
        with self._associated(clk=self.inClk):
            self.inData = Signal(dtype=self.DATA_TYP)

        self.outClk = Clk()
        with self._associated(clk=self.outClk):
            self.outData = Signal(dtype=self.DATA_TYP)._m()

    def _impl(self):
        def reg(name, clk):
            return self._reg(name,
                             self.DATA_TYP,
                             clk=clk,
                             rst=self.rst,
                             def_val=0)
        inReg = reg("inReg", self.inClk)
        outReg0 = reg("outReg0", self.outClk)
        outReg1 = reg("outReg1", self.outClk)

        inReg(self.inData)

        outReg0(inReg)
        outReg1(outReg0)
        self.outData(outReg1)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(ClkSynchronizer))
