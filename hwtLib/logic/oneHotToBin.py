#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Or, log2ceil
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VldSynced, VectSignal
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.vectorUtils import iterBits


@serializeParamsUniq
class OneHotToBin(Unit):
    """
    Converts one hot signal to binary, bin.vld is high when oneHot != 0

    .. hwt-schematic::
    """

    def _config(self):
        self.ONE_HOT_WIDTH = Param(8)

    def _declr(self):
        self.oneHot = VectSignal(self.ONE_HOT_WIDTH)
        self.bin = VldSynced()._m()
        self.bin.DATA_WIDTH = log2ceil(self.ONE_HOT_WIDTH)

    def _impl(self):
        self.bin.data(oneHotToBin(self, self.oneHot))
        self.bin.vld(Or(*[bit for bit in iterBits(self.oneHot)]))


def oneHotToBin(parent, signals, resName="oneHotToBin"):
    if isinstance(signals, (RtlSignal, Signal)):
        signals = [signals[i] for i in range(signals._dtype.bit_length())]
    else:
        signals = list(signals)

    res = parent._sig(resName, Bits(log2ceil(len(signals))))
    leadingZeroTop = None
    for i, s in enumerate(reversed(signals)):
        connections = res(len(signals) - i - 1)

        if leadingZeroTop is None:
            leadingZeroTop = connections
        else:
            leadingZeroTop = If(s,
                                connections
                             ).Else(
                                leadingZeroTop
                             )

    return res


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = OneHotToBin()
    print(toRtl(u))
