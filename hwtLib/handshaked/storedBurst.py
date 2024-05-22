#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from typing import Optional

from hwt.code import If, Switch
from hwt.hdl.types.bits import HBits
from hwt.hwParam import HwParam
from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


class HandshakedStoredBurst(HwModule):
    """
    This units send data stored in property DATA over axi-stream interface

    .. hwt-autodoc::
    """
    def __init__(self, hwIOCls=HwIODataRdVld, hdlName:Optional[str]=None):
        self.hwIOCls = hwIOCls
        super(HandshakedStoredBurst, self).__init__(hdlName=hdlName)

    def _config(self):
        self.hwIOCls._config(self)
        self.HWIO_CLS = HwParam(self.hwIOCls)
        self.REPEAT = HwParam(False)
        self.DATA = HwParam(tuple(ord(c) for c in "Hello world"))

    def dataRd(self):
        return self.dataOut.rd

    def _declr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataOut = self.HWIO_CLS()._m()

    def nextWordIndexLogic(self, wordIndex: RtlSignal):
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

    def set_data(self, hwIO: HwIODataRdVld, d):
        return [hwIO.data(d), ]

    def _impl(self):
        self.DATA_WIDTH = int(self.DATA_WIDTH)
        dout = self.dataOut
        DATA_LEN = len(self.DATA)

        wordIndex_w = int(math.log2(DATA_LEN) + 1)
        wordIndex = self._reg("wordIndex", HBits(wordIndex_w), def_val=0)

        def set_data(d):
            return self.set_data(dout, d)

        Switch(wordIndex)\
            .add_cases([(i, set_data(d))
                       for i, d in enumerate(self.DATA)])\
            .Default(*set_data(None))

        If(wordIndex < DATA_LEN,
            dout.vld(1)
        ).Else(
            dout.vld(0)
        )

        If(self.dataRd(),
            self.nextWordIndexLogic(wordIndex)
        )


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    print(to_rtl_str(HandshakedStoredBurst()))
