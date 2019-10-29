#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, rol, SwitchLogic
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import VldSynced
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.handshaked.joinPrioritized import HsJoinPrioritized


class HsJoinFairShare(HsJoinPrioritized):
    """
    Join multiple input streams into single output stream.
    Priority is changing every clock period.
    If prioritized input is not sending valid data,
    input with lowest index and valid is used.

    :note: combinational

    .. hwt-schematic: _example_HsJoinFairShare
    """

    def _config(self):
        HsJoinPrioritized._config(self)
        self.EXPORT_SELECTED = Param(True)

    def _declr(self):
        HsJoinPrioritized._declr(self)
        addClkRstn(self)
        if self.EXPORT_SELECTED:
            s = self.selectedOneHot = VldSynced()._m()
            s.DATA_WIDTH = self.INPUTS

    @staticmethod
    def priorityAck(priorityReg, vldSignals, index):
        """
        Generate ack logic for selected input

        :param priorityReg: priority register with one hot encoding,
            1 means input of this index should have be prioritized.
        :param vldSignals: list of vld signals of input
        :param index: index of input for which you wont get ack logic
        :return: ack signal for this input
        """
        priorityOverdrives = []
        vldWithHigherPriority = list(vldSignals[:index])

        for i, (p, vld) in enumerate(zip(iterBits(priorityReg), vldSignals)):
            if i > index:
                priorityOverdrives.append(p & vld)

        # ack when no one with higher priority has vld or this input have the
        # priority
        ack = ~Or(*priorityOverdrives, *
                  vldWithHigherPriority) | priorityReg[index]
        return ack

    def isSelectedLogic(self):
        """
        Resolve isSelected signal flags for each input, when isSelected flag signal is 1 it means
        input has clearance to make transaction
        """
        vld = self.get_valid_signal
        rd = self.get_ready_signal
        dout = self.dataOut

        priority = self._reg("priority", Bits(self.INPUTS), def_val=1)
        priority(rol(priority, 1))

        vldSignals = list(map(vld, self.dataIn))

        isSelectedFlags = []
        for i, din in enumerate(self.dataIn):
            isSelected = self._sig("isSelected_%d" % i)
            isSelected(self.priorityAck(priority, vldSignals, i))
            isSelectedFlags.append(isSelected)

            rd(din)(isSelected & rd(dout))

            if self.EXPORT_SELECTED:
                self.selectedOneHot.data[i](isSelected & vld(din))

        if self.EXPORT_SELECTED:
            self.selectedOneHot.vld(Or(*vldSignals) & rd(dout))

        return isSelectedFlags, vldSignals

    def inputMuxLogic(self, isSelectedFlags, vldSignals):
        vld = self.get_valid_signal
        dout = self.dataOut

        # data out mux
        dataCases = []
        for isSelected, din in zip(isSelectedFlags, self.dataIn):
            dataConnectExpr = self.dataConnectionExpr(din, dout)
            cond = vld(din) & isSelected
            dataCases.append((cond, dataConnectExpr))

        dataDefault = self.dataConnectionExpr(None, dout)
        SwitchLogic(dataCases, dataDefault)
        vld(dout)(Or(*vldSignals))

    def _impl(self):
        isSelectedFlags, vldSignals = self.isSelectedLogic()
        self.inputMuxLogic(isSelectedFlags, vldSignals)


def _example_HsJoinFairShare():
    from hwt.interfaces.std import Handshaked
    u = HsJoinFairShare(Handshaked)
    u.INPUTS = 3
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_HsJoinFairShare()
    print(toRtl(u))
