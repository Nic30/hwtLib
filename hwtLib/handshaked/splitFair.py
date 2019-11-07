#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, rol, connect
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


    :ivar selectedOneHot: handshaked interface with one hot encoded
        index of selected output
    
    .. hwt-schematic:: _example_HsSplitFair
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

    def isSelectedLogic(self):
        """
        Resolve isSelected signal flags for each input, when isSelected flag
        signal is 1 it means input has clearance to make transaction
        """
        vld = self.get_valid_signal
        rd = self.get_ready_signal
        din = self.dataIn
        EXPORT_SELECTED = bool(self.EXPORT_SELECTED)

        priority = self._reg("priority", Bits(self.OUTPUTS), def_val=1)
        priority(rol(priority, 1))

        rdSignals = list(map(rd, self.dataOut))

        for i, dout in enumerate(self.dataOut):
            isSelected = self._sig("isSelected_%d" % i)
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
        rdSignals = self.isSelectedLogic()

        for dout in self.dataOut:
            connect(self.dataIn, dout, exclude={self.get_ready_signal(dout),
                                                self.get_valid_signal(dout)})

        if self.EXPORT_SELECTED:
            self.get_ready_signal(self.dataIn)(Or(*rdSignals) & self.selectedOneHot.rd)
        else:
            self.get_ready_signal(self.dataIn)(Or(*rdSignals))


def _example_HsSplitFair():
    return HsSplitFair(Handshaked)

if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_HsSplitFair()
    print(toRtl(u))
