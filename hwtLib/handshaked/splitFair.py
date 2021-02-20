#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, rol
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwtLib.handshaked.joinFair import HsJoinFairShare
from hwtLib.handshaked.splitCopy import HsSplitCopy


class HsSplitFair(HsSplitCopy):
    """
    Split input stream to outputs, select single output for every
    input data based on priority.

    Priority is changing every clock
    If prioritized output is not ready,
    input with lowest index and ready is used

    :note: combinational


    .. aafig::
                                     +-------+
                              +------> out0  |
                              |      +-------+
                      +-------+
         input stream |       |      +-------+
        +-------------> split +------> out1  |
                      |       |      +-------+
                      +-------+
                              |      +-------+
                              +------> out2  |
                                     +-------+


    :ivar ~.selectedOneHot: handshaked interface with one hot encoded
        index of selected output

    .. hwt-autodoc:: _example_HsSplitFair
    """

    def _config(self):
        HsSplitCopy._config(self)
        self.EXPORT_SELECTED = Param(True)

    def _declr(self):
        HsSplitCopy._declr(self)
        addClkRstn(self)
        if self.EXPORT_SELECTED:
            s = self.selectedOneHot = Handshaked()._m()
            s.DATA_WIDTH = self.OUTPUTS

    def isSelectedLogic(self, din):
        """
        Resolve isSelected signal flags for each input, when isSelected flag
        signal is 1 it means input has clearance to make transaction
        """
        vld = self.get_valid_signal
        rd = self.get_ready_signal
        EXPORT_SELECTED = bool(self.EXPORT_SELECTED)

        priority = self._reg("priority", Bits(self.OUTPUTS), def_val=1)
        priority(rol(priority, 1))

        rdSignals = [rd(d) for d in self.dataOut]

        for i, dout in enumerate(self.dataOut):
            isSelected = self._sig(f"isSelected_{i:d}")
            isSelected(HsJoinFairShare.priorityAck(priority, rdSignals, i))

            if EXPORT_SELECTED:
                self.selectedOneHot.data[i](isSelected & vld(din))
                vld(dout)(isSelected & vld(din) & self.selectedOneHot.rd)
            else:
                vld(dout)(isSelected & vld(din))

        if EXPORT_SELECTED:
            self.selectedOneHot.vld(Or(*rdSignals) & vld(din))

        return rdSignals

    def _impl(self):
        din = self.dataIn
        rdSignals = self.isSelectedLogic(din)

        for dout in self.dataOut:
            dout(din, exclude={self.get_ready_signal(dout),
                               self.get_valid_signal(dout)})

        if self.EXPORT_SELECTED:
            self.get_ready_signal(din)(Or(*rdSignals) & self.selectedOneHot.rd)
        else:
            self.get_ready_signal(din)(Or(*rdSignals))


def _example_HsSplitFair():
    return HsSplitFair(Handshaked)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_HsSplitFair()
    print(to_rtl_str(u))
