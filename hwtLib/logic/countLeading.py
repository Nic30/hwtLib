#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.doc_markers import hwt_expr_producer
from hwt.hdl.commonConstants import b0
from hwt.hdl.types.bitConstFunctions import AnyHBitsValue
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.mainBases import RtlSignalBase
from hwt.math import isPow2, log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from pyMathBitPrecise.bit_utils import mask, next_power_of_2


# https://electronics.stackexchange.com/questions/196914/verilog-synthesize-high-speed-leading-zero-count
# https://content.sciendo.com/view/journals/jee/66/6/article-p329.xml?language=en
# [1]. Nebojša Z. Milenković and Vladimir V. Stanković and Miljana Lj. Milić, “MODULAR DESIGN OF FAST LEADING ZEROS COUNTING CIRCUIT”, Journal of ELECTRICAL ENGINEERING, VOL. 66, NO. 6, 2015, 329–333
# https://github.com/tomverbeure/math?tab=readme-ov-file#leading-zero-counter-lzc-and-leading-zero-anticipor-lza
@hwt_expr_producer
def _countLeadingRecurse(dataIn: RtlSignalBase[HBits], bitValToCount: int) -> AnyHBitsValue:
    """
    Construct a balanced tree for counter of leading 0/1

    :attention: result is not final result, it is only for 0 to width-1 values

    """
    assert bitValToCount in (0, 1), bitValToCount
    inWidth = dataIn._dtype.bit_length()
    if inWidth == 2:
        if bitValToCount == 0:
            return ~dataIn[1]
        else:
            return dataIn[1]
    else:
        assert inWidth > 2, inWidth
        assert inWidth % 2 == 0, inWidth
        lhs = dataIn[:inWidth // 2]
        rhs = dataIn[inWidth // 2:]
        if bitValToCount == 0:
            leftFull = lhs._eq(0)
        else:
            leftFull = lhs._eq(mask(lhs._dtype.bit_length()))

        in_ = leftFull._ternary(rhs, lhs)

        halfCount = _countLeadingRecurse(in_, bitValToCount)
        return Concat(leftFull, halfCount)


@hwt_expr_producer
def _countTrailingRecurse(dataIn: RtlSignalBase[HBits], bitValToCount: int) -> AnyHBitsValue:
    """
    Version of :func:`~._countLeadingRecurse` which counts from the back of the vector (upper bits first)
    """
    assert bitValToCount in (0, 1), bitValToCount
    inWidth = dataIn._dtype.bit_length()
    if inWidth == 2:
        if bitValToCount == 0:
            return ~dataIn[0]
        else:
            return dataIn[0]
    else:
        assert inWidth > 2, inWidth
        assert inWidth % 2 == 0, inWidth
        lhs = dataIn[:inWidth // 2]
        rhs = dataIn[inWidth // 2:]
        if bitValToCount == 0:
            leftFull = rhs._eq(0)
        else:
            leftFull = rhs._eq(mask(rhs._dtype.bit_length()))

        in_ = leftFull._ternary(lhs, rhs)
        halfCount = _countTrailingRecurse(in_, bitValToCount)
        return Concat(leftFull, halfCount)


@hwt_expr_producer
def countBits(dataIn: RtlSignalBase[HBits], bitValToCount: int, leading: bool) -> AnyHBitsValue:
    """
    :param bitValToCount: parameter to switch between count of zeros and ones
    :param leading: flag which switches between leading (from MSB side) and trailing (from LSB side) count
    :returns: number of bits set to bitValToCount value
    """
    origInWidth = inWidth = dataIn._dtype.bit_length()
    isExactlyPow2width = isPow2(inWidth)
    if isExactlyPow2width:
        pass
    else:
        nextPow2 = next_power_of_2(inWidth, 64)
        paddingTy = HBits(nextPow2 - inWidth)
        if bitValToCount == 0 and leading:
            # add padding from LSB, 1 is neutral element
            dataIn = Concat(dataIn, paddingTy.getAllOnesValue())
        elif bitValToCount == 0 and not leading:
            # add padding from MSB, 1 is neutral element
            dataIn = Concat(paddingTy.getAllOnesValue(), dataIn)
        elif bitValToCount == 1 and leading:
            # add padding from LSB, 0 is neutral element
            dataIn = Concat(dataIn, paddingTy.from_py(0))
        elif bitValToCount == 1 and not leading:
            # add padding from MSB, 0 is neutral element
            dataIn = Concat(paddingTy.from_py(0), dataIn)

        inWidth = nextPow2

    assert isPow2(inWidth), inWidth
    assert bitValToCount in (0, 1), bitValToCount
    assert isinstance(leading, bool), leading

    if bitValToCount == 0:
        full = dataIn._eq(0)
    else:
        full = dataIn._eq(mask(inWidth))

    countFn = _countLeadingRecurse if leading else _countTrailingRecurse
    halfCount = countFn(dataIn, bitValToCount)
    inWidthMax = HBits(log2ceil(inWidth + 1)).from_py(inWidth)

    result = full._ternary(inWidthMax,  # all bits are of counted value -> return max value
                            Concat(b0, halfCount)
                            )

    if isExactlyPow2width:
        return result
    else:
        # Trim result in the case that input had to be extended
        # to work correctly with bit count algorithm
        return result._trunc(log2ceil(origInWidth + 1))


# https://electronics.stackexchange.com/questions/196914/verilog-synthesize-high-speed-leading-zero-count
# https://content.sciendo.com/view/journals/jee/66/6/article-p329.xml?language=en
class _CountLeading(HwModule):
    """
    Count leading zeros/ones in bit vector
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(2)

    @override
    def hwDeclr(self):
        assert isPow2(self.DATA_WIDTH), self.DATA_WIDTH
        self.data_in = HwIOVectSignal(self.DATA_WIDTH)
        self.data_out = HwIOVectSignal(log2ceil(self.DATA_WIDTH + 1))._m()

    @override
    def hwImpl(self):
        raise NotImplementedError("This is an abstract method and should be overridden")


@serializeParamsUniq
class CountLeadingZeros(_CountLeading):
    """
    Count leading zeros in bit vector (leading means from MSB side)

    .. hwt-autodoc::
    """

    @override
    def hwImpl(self):
        self.data_out(countBits(self.data_in, 0, True))


@serializeParamsUniq
class CountLeadingOnes(_CountLeading):
    """
    Count leading zeros in bit vector (leading means from MSB side)

    .. hwt-autodoc::
    """

    @override
    def hwImpl(self):
        self.data_out(countBits(self.data_in, 1, True))


@serializeParamsUniq
class CountTrailingZeros(_CountLeading):
    """
    Count trailing zeros in bit vector (trailing means from LSB side)

    .. hwt-autodoc::
    """

    @override
    def hwImpl(self):
        self.data_out(countBits(self.data_in, 0, False))


@serializeParamsUniq
class CountTrailingOnes(_CountLeading):
    """
    Count trailing zeros in bit vector (trailing means from LSB side)

    .. hwt-autodoc::
    """

    @override
    def hwImpl(self):
        self.data_out(countBits(self.data_in, 1, False))


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(CountLeadingZeros()))
