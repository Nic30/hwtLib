#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import SwitchLogic
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import propagateClkRstn, addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param

from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.handshaked.reg import HandshakedReg


class HsSplitSelect(HandshakedCompBase):
    """
    Split data from input interface to N output interfaces based on explicit
    output index provided by select interface.

    .. aafig::
                 *----+ dataOut_0
                *     +-------->
         dataIn |     |
        +------->     | dataOut_1
                |     +-------->
                *     |
                 *-^--+
                   |
                   +
                 select
    
    .. hwt-schematic:: _example_HsSplitSelect
    
    """
    def _config(self):
        self.OUTPUTS = Param(3)
        super()._config()

    def _declr(self):
        addClkRstn(self)

        outputs = int(self.OUTPUTS)
        assert outputs > 1, outputs

        self.selectOneHot = Handshaked()
        self.selectOneHot.DATA_WIDTH = outputs

        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = HObjList(
                self.intfCls()._m() for _ in range(int(self.OUTPUTS))
            )

    def _select_consume_en(self):
        return True

    def _impl(self):
        In = self.dataIn
        rd = self.get_ready_signal

        sel = self.selectOneHot
        r = HandshakedReg(Handshaked)
        r.DATA_WIDTH = sel.data._dtype.bit_length()
        self.selReg = r
        r.dataIn(sel)
        propagateClkRstn(self)
        sel = r.dataOut

        for index, outIntf in enumerate(self.dataOut):
            for ini, outi in zip(In._interfaces, outIntf._interfaces):
                if ini == self.get_valid_signal(In):
                    # out.vld
                    outi(sel.vld & ini & sel.data[index])
                elif ini == rd(In):
                    pass
                else:  # data
                    outi(ini)

        din = self.dataIn
        SwitchLogic(
            cases=[(~sel.vld, [sel.rd(0),
                                rd(In)(0)])
                  ] +
                  [(sel.data[index],
                    [rd(In)(rd(out)),
                     sel.rd(rd(out) & self.get_valid_signal(din) & sel.vld & self._select_consume_en())])
                   for index, out in enumerate(self.dataOut)],
            default=[
                     sel.rd(None),
                     rd(In)(None)
            ]
        )


def _example_HsSplitSelect():
    return  HsSplitSelect(Handshaked)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_HsSplitSelect()
    print(toRtl(u))
