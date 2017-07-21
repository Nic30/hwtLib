#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch
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
        self.OUTPUTS = Param(3)
        super()._config()

    def _declr(self):
        outputs = int(self.OUTPUTS)
        assert outputs > 1, outputs

        self.sel = Handshaked()
        self.sel.DATA_WIDTH.set(outputs.bit_length())

        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls(asArraySize=self.OUTPUTS)

    def _impl(self):
        In = self.dataIn
        rd = self.getRd
        sel = self.sel

        for index, outIntf in enumerate(self.dataOut):
            for ini, outi in zip(In._interfaces, outIntf._interfaces):
                if ini == self.getVld(In):
                    outi ** (sel.vld & ini & sel.data._eq(index))
                elif ini == rd(In):
                    pass
                else:  # data
                    outi ** ini

        Switch(self.sel.data).addCases(
            [(index, [rd(In) ** rd(out),
                      sel.rd ** (rd(out) & self.getVld(out))])
             for index, out in enumerate(self.dataOut)]
        ).Default(
                  sel.rd ** None,
                  rd(In) ** None
                  )


if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HsSplitSelect(Handshaked)
    print(toRtl(u))
