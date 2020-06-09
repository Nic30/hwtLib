#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, isPow2, Concat
from hwt.interfaces.std import VectSignal
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit

# https://electronics.stackexchange.com/questions/196914/verilog-synthesize-high-speed-leading-zero-count
class _CountLeading(Unit):
    """
    Count leading zeros/ones in bit vector
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        assert isPow2(self.DATA_WIDTH), self.DATA_WIDTH 
        self.data_in = VectSignal(self.DATA_WIDTH)
        self.data_out = VectSignal(log2ceil(self.DATA_WIDTH))._m()

    @classmethod
    def count_leading_recurse(cls, data_in: RtlSignal, bit_to_count: int):
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
            left_empty = lhs._eq(0)

            half_count = cls.count_leading_recurse(left_empty._ternary(rhs, lhs), bit_to_count)
            return Concat(left_empty, half_count)

    def _impl(self):
        raise NotImplementedError("This is an abstract method and should be overriden")


class CountLeadingZeros(_CountLeading):
    """
    Count leading zeros in bit vector

    .. hwt-schematic::
    """

    def _impl(self):
        self.data_out(self.count_leading_recurse(self.data_in, 0))


class CountLeadingOnes(_CountLeading):
    """
    Count leading zeros in bit vector

    .. hwt-schematic::
    """

    def _impl(self):
        self.data_out(self.count_leading_recurse(self.data_in, 1))


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(CountLeadingZeros()))
