#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

from hwt.code import If, Switch
from hwt.hdl.types.bits import Bits
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from pyMathBitPrecise.bit_utils import mask


class AxiSStoredBurst(Unit):
    """
    This units send data stored in property DATA over axi-stream interface

    .. hwt-schematic::
    """
    def __init__(self, data=[ord(c) for c in "Hello world"]):
        super(AxiSStoredBurst, self).__init__()
        self.DATA = data

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USE_STRB = Param(True)
        self.REPEAT = Param(False)

    def dataRd(self):
        return self.dataOut.ready

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataOut = AxiStream()._m()

    def nextWordIndexLogic(self, wordIndex):
        if self.REPEAT:
            return If(wordIndex < len(self.DATA),
                       wordIndex(wordIndex + 1)
                   ).Else(
                       wordIndex(0)
                   )
        else:
            return If(wordIndex < len(self.DATA),
                       wordIndex(wordIndex + 1)
                   )

    def _impl(self):
        self.DATA_WIDTH = int(self.DATA_WIDTH)
        vldAll = mask(self.DATA_WIDTH // 8)
        dout = self.dataOut
        DATA_LEN = len(self.DATA)

        wordIndex_w = int(math.log2(DATA_LEN) + 1)
        wordIndex = self._reg("wordIndex", Bits(wordIndex_w), def_val=0)

        Switch(wordIndex)\
            .addCases([(i, dout.data(d))
                       for i, d in enumerate(self.DATA)])\
            .Default(dout.data(None))

        dout.last(wordIndex._eq(DATA_LEN - 1))
        If(wordIndex < DATA_LEN,
            dout.strb(vldAll),
            dout.valid(1)
        ).Else(
            dout.strb(None),
            dout.valid(0)
        )

        If(self.dataRd(),
            self.nextWordIndexLogic(wordIndex)
        )


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    print(toRtl(AxiSStoredBurst))
