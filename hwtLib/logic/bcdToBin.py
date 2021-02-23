#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch, If, Concat
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class BcdToBin(Unit):
    """
    Convert a BCD number to binary encoding
    This uses the double-dabble algorithm in reverse. The conversion of a BCD
    number to an n-bit binary number will take n+3 cycles to complete.

    based on: https://github.com/kevinpt/vhdl-extras/blob/master/rtl/extras/bcd_conversion.vhdl

    .. hwt-autodoc::
    """

    def _config(self):
        self.BCD_DIGITS = Param(3)

    def _declr(self):
        addClkRstn(self)
        BCD_DIGITS = self.BCD_DIGITS
        bcd = self.din = Handshaked()  # BCD data to convert
        bcd.DATA_WIDTH = 4 * BCD_DIGITS
        bin_ = self.dout = Handshaked()._m()
        bin_.DATA_WIDTH = log2ceil(10 ** BCD_DIGITS - 1)  # Converted output. Retained until next conversion

    def _impl(self):
        st_t = HEnum("state_t", ["IDLE", "LOAD_SR", "CONVERTING", "DONE"])
        st = self._reg("st", st_t, def_val=st_t.IDLE)
        sr_shift = st.next._eq(st_t.CONVERTING)

        bcd = self.din
        bin_ = self.dout
        bcd_sr = self._reg("bcd_sr", bcd.data._dtype, def_val=0)
        binary_sr = self._reg("binary_sr", bin_.data._dtype, def_val=0)
        next_bcd = rename_signal(self, bcd_sr >> 1, "next_bcd")

        MAX_COUNT = binary_sr._dtype.bit_length()
        bit_count = self._reg("bit_count", Bits(log2ceil(MAX_COUNT), signed=False), def_val=MAX_COUNT)
        If(sr_shift,
           bit_count(bit_count - 1),
        ).Else(
           bit_count(MAX_COUNT),
        )
        # dabble the digits
        digits = []
        for i in range(self.BCD_DIGITS):
            d = next_bcd[(i + 1) * 4:i * 4]._unsigned()
            d_sig = (d < 7)._ternary(d, d - 3)
            digits.append(d_sig)

        If(st.next._eq(st_t.LOAD_SR),
           bcd_sr(bcd.data),
           binary_sr(0),
        ).Elif(sr_shift,
           # shift right
           binary_sr(Concat(bcd_sr[0], binary_sr[:1])),
           bcd_sr(Concat(*reversed(digits))),
        )

        bin_.data(binary_sr)

        Switch(st)\
        .Case(st_t.IDLE,
            If(bcd.vld,
                st(st_t.LOAD_SR),  # load the shift registers
            ))\
        .Case(st_t.LOAD_SR,
            # shift right each cycle
            st(st_t.CONVERTING),
        )\
        .Case(st_t.CONVERTING,
            If(bit_count._eq(0),
                # indicate completion
                st(st_t.DONE),
            )
        )\
        .Case(st_t.DONE,
            If(bcd.vld & bin_.rd,
                st(st_t.LOAD_SR),
            ).Elif(bin_.rd,
                st(st_t.IDLE),
            )
        )
        bcd.rd(st._eq(st_t.IDLE) | (st._eq(st_t.DONE) & bin_.rd))
        bin_.vld(st._eq(st_t.DONE))


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = BcdToBin()
    print(to_rtl_str(u))
