#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

from hwt.bitmask import mask
from hwt.code import If, Switch
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.amba.axis import AxiStream


class AxiSStoredBurst(Unit):
    """
    This units send data stored in property DATA over axi-stream interface
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.DATA = [ord(c) for c in "Hello world"]
        self.REPEAT = Param(False)

    def dataRd(self):
        return self.dataOut.ready

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataOut = AxiStream()

    def nextWordIndexLogic(self, wordIndex):
        if evalParam(self.REPEAT).val:
            return If(wordIndex < len(self.DATA),
                       wordIndex ** (wordIndex + 1)
                   ).Else(
                       wordIndex ** 0
                   )
        else:
            return If(wordIndex < len(self.DATA),
                       wordIndex ** (wordIndex + 1)
                   )

    def _impl(self):
        self.DATA_WIDTH = evalParam(self.DATA_WIDTH).val
        vldAll = mask(self.DATA_WIDTH // 8)
        dout = self.dataOut
        DATA_LEN = len(self.DATA)

        wordIndex_w = int(math.log2(DATA_LEN) + 1)
        wordIndex = self._reg("wordIndex", vecT(wordIndex_w), defVal=0)

        Switch(wordIndex)\
        .addCases([(i, dout.data ** d)
                    for i, d in enumerate(self.DATA)])\
        .Default(dout.data ** None)

        dout.last ** wordIndex._eq(DATA_LEN - 1)
        If(wordIndex < DATA_LEN,
            dout.strb ** vldAll,
            dout.valid ** 1
        ).Else(
            dout.strb ** None,
            dout.valid ** 0
        )

        If(self.dataRd(),
            self.nextWordIndexLogic(wordIndex)
        )

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(AxiSStoredBurst))
