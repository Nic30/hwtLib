#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, If
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIOClk
from hwt.serializer.mode import serializeExclude
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwt.hdl.types.defs import BIT


def mkLutRamCls(DATA_WIDTH):
    """
    Lut ram generator,
    hdl code will be excluded from serialization because we expect vendor library to contains it
    """

    class RAMnX1S(HwModule):

        def _config(self):
            self.INIT = HwParam(HBits(DATA_WIDTH).from_py(0))
            self.IS_WCLK_INVERTED = HwParam(BIT.from_py(0))

        def _declr(self):
            self.a0 = HwIOSignal()
            self.a1 = HwIOSignal()
            self.a2 = HwIOSignal()
            self.a3 = HwIOSignal()
            self.a4 = HwIOSignal()
            self.a5 = HwIOSignal()
            self.d = HwIOSignal()  # in

            self.wclk = HwIOClk()
            self.o = HwIOSignal()._m()  # out
            self.we = HwIOSignal()

        def _impl(self):
            s = self._sig
            wclk_in = s("wclk_in")
            mem = self._ctx.sig("mem", HBits(DATA_WIDTH),
                                def_val=self.INIT)
            a_in = s("a_in", HBits(6))
            d_in = s("d_in")
            we_in = s("we_in")

            wclk_in(self.wclk ^ self.IS_WCLK_INVERTED)
            we_in(self.we)
            a_in(Concat(self.a5, self.a4, self.a3, self.a2, self.a1, self.a0))
            d_in(self.d)

            # ReadBehavior
            self.o(mem[a_in])

            # WriteBehavior
            If(wclk_in._onRisingEdge() & we_in,
               mem[a_in](d_in)
            )

    RAMnX1S.__name__ = f"RAM{DATA_WIDTH:d}X1S"
    return RAMnX1S


# exclude from serialization because it is part of sources provided from FPGA vendor
RAM64X1S = serializeExclude(mkLutRamCls(64))


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = RAM64X1S()
    # note that this will not produce any code as the serialization
    # is disabled using serializeExclude
    print(to_rtl_str(m))
