#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil, log10

from hwt.code import If, Switch, Concat
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.hdl.types.defs import BIT


class BinToBcd(Unit):
    """
    Convert binary to BCD (Binary coded decimal) format
    (BCD is a format where each 4 bites represents a single decimal digit 0-9)

    based on https://github.com/kb000/bin2bcd/blob/master/rtl/bin2bcd32.v

    .. hwt-autodoc::
    """

    def _config(self):
        self.INPUT_WIDTH = Param(64)

    def _declr(self):
        addClkRstn(self)
        assert self.INPUT_WIDTH > 0, self.INPUT_WIDTH
        self.DECIMAL_DIGITS = self.decadic_deciamls_for_bin(self.INPUT_WIDTH)
        self.din = Handshaked()
        self.din.DATA_WIDTH = self.INPUT_WIDTH
        self.dout = Handshaked()._m()
        self.dout.DATA_WIDTH = self.DECIMAL_DIGITS * 4

    @staticmethod
    def decadic_deciamls_for_bin(bin_width: int):
        return ceil(log10(2 ** bin_width))

    def _impl(self):
        INPUT_WIDTH, DECIMAL_DIGITS, din, dout = \
        self.INPUT_WIDTH, self.DECIMAL_DIGITS, self.din, self.dout

        bin_r = self._reg("bin_r", Bits(INPUT_WIDTH, signed=False))
        bitcount = self._reg("bitcount", Bits(log2ceil(INPUT_WIDTH), signed=False), def_val=0)

        st_t = HEnum("st_t", ["idle", "busy", "fin"])
        state = self._reg("state", st_t, def_val=st_t.idle)

        din.rd(state._eq(st_t.idle))

        dout.vld(state._eq(st_t.fin))

        Switch(state)\
            .Case(st_t.idle,
                If(din.vld,
                    state(st_t.busy)
                ))\
            .Case(st_t.busy,
                If(bitcount._eq(INPUT_WIDTH - 1),
                    state(st_t.fin)
                ))\
            .Case(st_t.fin,
                If(dout.rd,
                   state(st_t.idle),
                )
            )

        Switch(state)\
            .Case(st_t.idle,
                If(din.vld,
                    bin_r(din.data)
                ))\
            .Case(st_t.busy,
                bin_r(bin_r[INPUT_WIDTH - 1:]._concat(BIT.from_py(0))))

        Switch(state)\
            .Case(st_t.busy,
                bitcount(bitcount + 1))\
            .Default(
                bitcount(0))

        bcdp = [self._sig(f"bcdp{i:d}", Bits(4, signed=False)) for i in range(DECIMAL_DIGITS)]
        bcd_digits = []
        for g in range(DECIMAL_DIGITS):
            bcd = self._reg(f"bcd_{g:d}", Bits(4, signed=False), def_val=0)
            bcdp[g]((bcd >= 5)._ternary(bcd + 3, bcd)),
            prev = self._sig(f"prev_{g:d}", Bits(4))
            if g != 0:
                prev(bcdp[g - 1])
            else:
                prev(bin_r[INPUT_WIDTH-1]._concat(Bits(3).from_py(0)))

            s = self._sig(f"s_{g:d}", Bits(4))
            s(bcdp[g] << 1 | prev >> 3),
            Switch(state)\
                .Case(st_t.idle,
                    bcd(0))\
                .Case(st_t.busy,
                    bcd(s))
            bcd_digits.append(bcd)

        dout.data(Concat(*reversed(bcd_digits)))


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = BinToBcd()
    print(to_rtl_str(u))
