#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, Clk
from hwt.serializer.mode import serializeExclude
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.hdl.types.defs import BIT


def mkLutRamCls(DATA_WIDTH):
    """
    Lut ram generator,
    hdl code will be excluded from serialization because we expect vendor library to contains it
    """

    class RAMnX1S(Unit):

        def _config(self):
            self.INIT = Param(Bits(DATA_WIDTH).from_py(0))
            self.IS_WCLK_INVERTED = Param(BIT.from_py(0))

        def _declr(self):
            self.a0 = Signal()
            self.a1 = Signal()
            self.a2 = Signal()
            self.a3 = Signal()
            self.a4 = Signal()
            self.a5 = Signal()
            self.d = Signal()  # in

            self.wclk = Clk()
            self.o = Signal()._m()  # out
            self.we = Signal()

        def _impl(self):
            s = self._sig
            wclk_in = s("wclk_in")
            mem = self._ctx.sig("mem", Bits(DATA_WIDTH),
                                def_val=self.INIT)
            a_in = s("a_in", Bits(6))
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
    from hwt.synthesizer.utils import to_rtl_str
    u = RAM64X1S()
    # note that this will not produce any code as the serialization
    # is dissabled using serializeExclude
    print(to_rtl_str(u))
