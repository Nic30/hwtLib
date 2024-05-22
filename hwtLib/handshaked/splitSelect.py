#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import SwitchLogic
from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwIOs.utils import propagateClkRstn, addClkRstn
from hwt.hObjList import HObjList
from hwt.hwParam import HwParam
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.handshaked.reg import HandshakedReg
from hwt.pyUtils.typingFuture import override


class HsSplitSelect(HandshakedCompBase):
    """
    Split data from input interface to N output interfaces based on explicit
    output index provided by select interface.

    .. figure:: ./_static/HsSplitSelect.png

    .. hwt-autodoc:: _example_HsSplitSelect
    """
    @override
    def hwConfig(self):
        self.OUTPUTS = HwParam(3)
        super().hwConfig()

    @override
    def hwDeclr(self):
        addClkRstn(self)

        outputs = int(self.OUTPUTS)
        assert outputs > 1, outputs

        self.selectOneHot = HwIODataRdVld()
        self.selectOneHot.DATA_WIDTH = outputs

        with self._hwParamsShared():
            self.dataIn = self.hwIOCls()
            self.dataOut = HObjList(
                self.hwIOCls()._m() for _ in range(int(self.OUTPUTS))
            )

    def _select_consume_en(self):
        return True

    @override
    def hwImpl(self):
        In = self.dataIn
        rd = self.get_ready_signal

        sel = self.selectOneHot
        r = HandshakedReg(HwIODataRdVld)
        r.DATA_WIDTH = sel.data._dtype.bit_length()
        self.selReg = r
        r.dataIn(sel)
        propagateClkRstn(self)
        sel = r.dataOut

        for index, outHwIO in enumerate(self.dataOut):
            for inIO, outIO in zip(In._hwIOs, outHwIO._hwIOs):
                if inIO == self.get_valid_signal(In):
                    # out.vld
                    outIO(sel.vld & inIO & sel.data[index])
                elif inIO == rd(In):
                    pass
                else:  # data
                    outIO(inIO)

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
    return  HsSplitSelect(HwIODataRdVld)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = _example_HsSplitSelect()
    print(to_rtl_str(m))
