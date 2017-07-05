#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.synthesizer.param import Param
from hwtLib.handshaked.compBase import HandshakedCompBase


class HsSplitSelect(HandshakedCompBase):
    """
    Split data from input interface to output interface based on explicit output index
    provided by select interface

    .. aafig::
                *----+ output0
               *     +-------->
         input |     |
        +------>     | output1
               |     +-------->
               *     |
                *-^--+
                  |
                  +
                select
    """
    def _config(self):
        self.OUTPUTS = Param(2)
        super()._config()

    def _declr(self):
        outputs = int(self.OUTPUTS)

        self.sel = Signal(dtype=vecT(outputs.bit_length()))

        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls(asArraySize=self.OUTPUTS)

    def _impl(self):
        In = self.dataIn
        rd = self.getRd

        for index, outIntf in enumerate(self.dataOut):
            for ini, outi in zip(In._interfaces, outIntf._interfaces):
                if ini == self.getVld(In):
                    outi ** (ini & self.sel._eq(index))
                elif ini == rd(In):
                    pass
                else:  # data
                    outi ** ini

        Switch(self.sel).addCases(
            [(index, rd(In) ** rd(out))
             for index, out in enumerate(self.dataOut)]
        )


if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HandshakedDemux(Handshaked)
    print(toRtl(u))