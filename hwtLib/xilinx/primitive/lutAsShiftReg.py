#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOClk, HwIOVectSignal, HwIOSignal, HwIODataVld
from hwt.math import log2ceil
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule


class LutAsShiftReg(HwModule):
    """
    This components generates SRL16E and other shift registers.

    In order to allow Xilinx Vivado 2020.2 (and possibly any other version)
    to map this component into SRL16E and equivalents we need to satisfy several conditions:
    1. the memory must not have reset
    2. the shift expressions must be performed on a single signal
    3. whole memory must be single signal
    4. the output must be read only by index operator (switch on address does not work)
    5. we can not merge memories of individual data bits
    """

    def hwConfig(self) -> None:
        self.DATA_WIDTH = HwParam(1)
        self.ITEMS = HwParam(16)
        self.INIT = HwParam(None)

    def hwDeclr(self) -> None:
        self.clk = HwIOClk()
        self.d_in = HwIODataVld()
        self.d_in.DATA_WIDTH = self.DATA_WIDTH

        self.d_out_addr = HwIOVectSignal(log2ceil(self.ITEMS))
        self.d_out = HwIOSignal(HBits(self.DATA_WIDTH))._m()

    def hwImpl(self) -> None:
        out = []
        for i in range(self.DATA_WIDTH):
            mem = self._sig(f"mem{i:d}", HBits(self.ITEMS), def_val=self.INIT)
            If(self.clk._onRisingEdge(),
                If(self.d_in.vld,
                    mem(Concat(mem[mem._dtype.bit_length() - 1:], self.d_in.data[i],))
                )
            )
            out.append(mem[self.d_out_addr])

        self.d_out(Concat(*reversed(out)))

if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = LutAsShiftReg()
    m.DATA_WIDTH = 4
    print(to_rtl_str(m))