#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import SwitchLogic
from hwt.interfaces.std import Handshaked
from hwt.synthesizer.param import Param
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.handshaked.reg import HandshakedReg
from hwt.interfaces.utils import propagateClkRstn, addClkRstn


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
        addClkRstn(self)

        outputs = int(self.OUTPUTS)
        assert outputs > 1, outputs

        self.selectOneHot = Handshaked()
        self.selectOneHot.DATA_WIDTH.set(outputs)

        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls(asArraySize=self.OUTPUTS)

    def _impl(self):
        In = self.dataIn
        rd = self.getRd

        sel = self.selectOneHot
        r = HandshakedReg(Handshaked)
        r.DATA_WIDTH.set(sel.data._dtype.bit_length())
        self.selReg = r
        r.dataIn ** sel
        propagateClkRstn(self)
        sel = r.dataOut

        for index, outIntf in enumerate(self.dataOut):
            for ini, outi in zip(In._interfaces, outIntf._interfaces):
                if ini == self.getVld(In):
                    # out.vld
                    outi ** (sel.vld & ini & sel.data[index])
                elif ini == rd(In):
                    pass
                else:  # data
                    outi ** ini

        din = self.dataIn
        SwitchLogic(
            cases=[(~sel.vld, [sel.rd ** 0,
                                rd(In) ** 0])
                  ] +
                  [(sel.data[index],
                    [rd(In) ** rd(out),
                     sel.rd ** (rd(out) & self.getVld(din) & sel.vld)])
                   for index, out in enumerate(self.dataOut)],
            default=[
                     sel.rd ** None,
                     rd(In) ** None
                     ])


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = HsSplitSelect(Handshaked)
    print(toRtl(u))
