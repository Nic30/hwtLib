#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, List

from hwt.code import If, Or, SwitchLogic
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIODataVld, HwIOVectSignal
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.vectorUtils import iterBits


@serializeParamsUniq
class OneHotToBin(HwModule):
    """
    Converts one hot signal to binary, bin.vld is high when oneHot != 0

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.ONE_HOT_WIDTH = HwParam(8)

    @override
    def hwDeclr(self):
        self.oneHot = HwIOVectSignal(self.ONE_HOT_WIDTH)
        self.bin = HwIODataVld()._m()
        self.bin.DATA_WIDTH = log2ceil(self.ONE_HOT_WIDTH)

    @override
    def hwImpl(self):
        self.bin.data(oneHotToBin(self, self.oneHot))
        self.bin.vld(Or(*[bit for bit in iterBits(self.oneHot)]))


def oneHotToBin(parent, signals: Union[RtlSignal, HwIOSignal, List[Union[RtlSignal, HwIOSignal]]], resName="oneHotToBin"):
    if isinstance(signals, (RtlSignal, HwIOSignal)):
        signals = [signals[i] for i in range(signals._dtype.bit_length())]
    else:
        signals = list(signals)

    res = parent._sig(resName, HBits(log2ceil(len(signals))))
    SwitchLogic([(c, (res(i))) for i, c in enumerate(signals[:-1])],
                default=(res(len(signals) - 1)))

    return res


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = OneHotToBin()
    print(to_rtl_str(m))
