#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from typing import Optional

from hwt.code import If, Switch
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class HandshakedStoredBurst(Unit):
    """
    This units send data stored in property DATA over axi-stream interface

    .. hwt-autodoc::
    """
    def __init__(self, intfCls=Handshaked, hdl_name_override:Optional[str]=None):
        self.intfCls = intfCls
        super(HandshakedStoredBurst, self).__init__(hdl_name_override=hdl_name_override)

    def _config(self):
        self.intfCls._config(self)
        self.INTF_CLS = Param(self.intfCls)
        self.REPEAT = Param(False)
        self.DATA = Param(tuple(ord(c) for c in "Hello world"))

    def dataRd(self):
        return self.dataOut.rd

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataOut = self.INTF_CLS()._m()

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

    def set_data(self, intf, d):
        return [intf.data(d), ]

    def _impl(self):
        self.DATA_WIDTH = int(self.DATA_WIDTH)
        dout = self.dataOut
        DATA_LEN = len(self.DATA)

        wordIndex_w = int(math.log2(DATA_LEN) + 1)
        wordIndex = self._reg("wordIndex", Bits(wordIndex_w), def_val=0)

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
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(HandshakedStoredBurst()))
