#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from typing import Tuple, Union

from hwt.code import If, Switch
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.bitsVal import BitsVal
from hwt.interfaces.utils import addClkRstn
from hwt.pyUtils.arrayQuery import grouper
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from pyMathBitPrecise.bit_utils import mask, byte_list_to_be_int


class AxiSStoredBurst(Unit):
    """
    This unit send data stored in property :obj:`~.DATA` over axi-stream interface

    :ivar ~.DATA: bytes or integer values for each word
    :ivar ~.REPEAT: if False this component works in one-shot mode

    .. hwt-autodoc::
    """

    def _config(self):
        AxiStream._config(self)
        self.REPEAT:bool = Param(False)
        self.DATA:Union[bytes, Tuple[Union[int, BitsVal]]] = Param("Hello world".encode())

    def dataRd(self):
        return self.dataOut.ready

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataOut: AxiStream = AxiStream()._m()

    def nextWordIndexLogic(self, wordIndex: RtlSignal, DATA_LEN:int):
        if self.REPEAT:
            return If(wordIndex < DATA_LEN,
                       wordIndex(wordIndex + 1)
                   ).Else(
                       wordIndex(0)
                   )
        else:
            return If(wordIndex < DATA_LEN,
                       wordIndex(wordIndex + 1)
                   )

    def _impl(self):
        dout = self.dataOut
        all_mask = mask(self.DATA_WIDTH // 8)
        DATA = self.DATA
        if isinstance(DATA, bytes):
            # convert bytes to integer for words
            DATA_SIZE = len(DATA)
            if not self.USE_STRB and not self.USE_KEEP:
                assert DATA_SIZE % (self.DATA_WIDTH // 8) == 0, (
                    "Not using any kind of mask and the data does not exactly fit into words", DATA)
            last_mask = mask((DATA_SIZE % (self.DATA_WIDTH // 8) // 8))
            if last_mask == 0:
                last_mask = all_mask

            words = []
            for word_bytes in grouper(self.DATA_WIDTH // 8, DATA, 0):
                word = byte_list_to_be_int(word_bytes)
                words.append(word)
            words.append(word)
            DATA = words
        else:
            last_mask = all_mask

        DATA_LEN = len(DATA)

        wordIndex_w = int(math.log2(DATA_LEN) + 1)
        wordIndex = self._reg("wordIndex", Bits(wordIndex_w), def_val=0)

        Switch(wordIndex)\
            .add_cases([(i, dout.data(d))
                       for i, d in enumerate(DATA)])\
            .Default(dout.data(None))

        dout.last(wordIndex._eq(DATA_LEN - 1))
        if self.USE_STRB or self.USE_KEEP:
            if last_mask == all_mask:
                out_mask = all_mask
            else:
                out_mask = dout.last._ternary(last_mask, all_mask)
        If(wordIndex < DATA_LEN,
            dout.strb(out_mask) if self.USE_STRB else [],
            dout.keep(out_mask) if self.USE_KEEP else [],
            dout.valid(1)
        ).Else(
            dout.strb(None) if self.USE_STRB else [],
            dout.keep(None) if self.USE_KEEP else [],
            dout.valid(0)
        )

        If(self.dataRd(),
            self.nextWordIndexLogic(wordIndex, DATA_LEN)
        )


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    print(to_rtl_str(AxiSStoredBurst()))
