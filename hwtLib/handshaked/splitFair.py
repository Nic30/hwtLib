#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, rol, connect
from hwt.hdlObjects.typeShortcuts import vecT
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

    combinational


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
    """
    def _config(self):
        HsSplitCopy._config(self)
        self.EXPORT_SELECTED = Param(True)

    def _declr(self):
        HsSplitCopy._declr(self)
        addClkRstn(self)
        if self.EXPORT_SELECTED:
            self.selectedOneHot = Handshaked()
            self.selectedOneHot._replaceParam("DATA_WIDTH", self.OUTPUTS)

    def isSelectedLogic(self):
        """
        Resolve isSelected signal flags for each input, when isSelected flag
        signal is 1 it means input has clearance to make transaction
        """
        vld = self.getVld
        rd = self.getRd
        din = self.dataIn
        EXPORT_SELECTED = bool(self.EXPORT_SELECTED)

        priority = self._reg("priority", vecT(self.OUTPUTS), defVal=1)
        priority ** rol(priority, 1)

        rdSignals = list(map(rd, self.dataOut))

        for i, dout in enumerate(self.dataOut):
            isSelected = self._sig("isSelected_%d" % i)
            isSelected ** HsJoinFairShare.priorityAck(priority, rdSignals, i)

            if EXPORT_SELECTED:
                self.selectedOneHot.data[i] ** (isSelected & vld(din))
                vld(dout) ** (isSelected & vld(din) & self.selectedOneHot.rd)
            else:
                vld(dout) ** (isSelected & vld(din))

        if EXPORT_SELECTED:
            self.selectedOneHot.vld ** (Or(*rdSignals) & vld(din))

        return rdSignals

    def _impl(self):
        rdSignals = self.isSelectedLogic()

        for dout in self.dataOut:
            connect(self.dataIn, dout, exclude={self.getRd(dout), self.getVld(dout)})

        if self.EXPORT_SELECTED:
            self.getRd(self.dataIn) ** (Or(*rdSignals) & self.selectedOneHot.rd)
        else:
            self.getRd(self.dataIn) ** Or(*rdSignals)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = HsSplitFair(Handshaked)
    print(toRtl(u))
