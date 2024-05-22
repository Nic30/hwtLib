#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, If
from hwt.hdl.types.defs import BIT
from hwt.hwIOs.std import HwIOVectSignal
from hwt.math import log2ceil, isPow2
from hwt.hwParam import HwParam
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.hwModule import HwModule
from pyMathBitPrecise.bit_utils import mask


# https://electronics.stackexchange.com/questions/196914/verilog-synthesize-high-speed-leading-zero-count
# https://content.sciendo.com/view/journals/jee/66/6/article-p329.xml?language=en
class _CountLeading(HwModule):
    """
    Count leading zeros/ones in bit vector
    """

    def _config(self):
        self.DATA_WIDTH = HwParam(2)

    def _declr(self):
        assert isPow2(self.DATA_WIDTH), self.DATA_WIDTH
        self.data_in = HwIOVectSignal(self.DATA_WIDTH)
        self.data_out = HwIOVectSignal(log2ceil(self.DATA_WIDTH + 1))._m()

    @classmethod
    def _count_leading_recurse(cls, data_in: RtlSignal, bit_to_count: int):
        """
        Construct a balanced tree for counter of leading 0/1
        :attention: result is not final result

        """
        assert bit_to_count in (0, 1), bit_to_count
        in_width = data_in._dtype.bit_length()
        if in_width == 2:
            if bit_to_count == 0:
                return ~data_in[1]
            else:
                return data_in[1]
        else:
            assert in_width > 2, in_width
            lhs = data_in[:in_width // 2]
            rhs = data_in[in_width // 2:]
            if bit_to_count == 0:
                left_full = lhs._eq(0)
            else:
                left_full = lhs._eq(mask(lhs._dtype.bit_length()))

            in_ = left_full._ternary(rhs, lhs)
            half_count = cls._count_leading_recurse(in_, bit_to_count)
        return Concat(left_full, half_count)

    @classmethod
    def count_leading(cls, data_in: RtlSignal, data_out: RtlSignal, bit_to_count: int):
        in_width = data_in._dtype.bit_length()
        assert bit_to_count in (0, 1), bit_to_count

        if bit_to_count == 0:
            full = data_in._eq(0)
        else:
            full = data_in._eq(mask(in_width))

        half_count = cls._count_leading_recurse(data_in, bit_to_count)
        If(full,
           data_out(in_width),
        ).Else(
           data_out(Concat(BIT.from_py(0), half_count))
        )

    def _impl(self):
        raise NotImplementedError("This is an abstract method and should be overridden")


class CountLeadingZeros(_CountLeading):
    """
    Count leading zeros in bit vector

    .. hwt-autodoc::
    """

    def _impl(self):
        self.count_leading(self.data_in, self.data_out, 0)


class CountLeadingOnes(_CountLeading):
    """
    Count leading zeros in bit vector

    .. hwt-autodoc::
    """

    def _impl(self):
        self.count_leading(self.data_in, self.data_out, 1)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(CountLeadingZeros()))
