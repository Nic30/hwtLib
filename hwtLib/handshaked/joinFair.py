#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, rol, SwitchLogic
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
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

    .. hwt-autodoc: _example_HsJoinFairShare
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
        ack = ~Or(*priorityOverdrives, *vldWithHigherPriority) | priorityReg[index]
        return ack

    def isSelectedLogic(self, din_vlds, dout_rd, selectedOneHot):
        """
        Resolve isSelected signal flags for each input, when isSelected flag
        signal is 1 it means input has clearance to make transaction
        """
        assert din_vlds
        if len(din_vlds) == 1:
            isSelectedFlags = [BIT.from_py(1), ]
            if selectedOneHot is not None:
                selectedOneHot.data(1)
        else:
            priority = self._reg("priority", Bits(len(din_vlds)), def_val=1)
            priority(rol(priority, 1))

            isSelectedFlags = []
            for i, din_vld in enumerate(din_vlds):
                isSelected = self._sig(f"isSelected_{i:d}")
                isSelected(self.priorityAck(priority, din_vlds, i))
                isSelectedFlags.append(isSelected)

                if selectedOneHot is not None:
                    selectedOneHot.data[i](isSelected & din_vld)

        if selectedOneHot is not None:
            selectedOneHot.vld(Or(*din_vlds) & dout_rd)

        return isSelectedFlags

    def inputMuxLogic(self, isSelectedFlags):
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

    def _impl(self):
        if self.EXPORT_SELECTED:
            selectedOneHot = self.selectedOneHot
        else:
            selectedOneHot = None

        rd = self.get_ready_signal
        vld = self.get_valid_signal
        dout = self.dataOut
        din_vlds = [vld(d) for d in self.dataIn]
        # round-robin
        isSelectedFlags = self.isSelectedLogic(
            din_vlds, rd(dout), selectedOneHot)

        self.inputMuxLogic(isSelectedFlags)

        # handshake logic with injected round-robin
        for din, isSelected in zip(self.dataIn, isSelectedFlags):
            rd(din)(isSelected & rd(dout))
        vld(dout)(Or(*din_vlds))


def _example_HsJoinFairShare():
    from hwt.interfaces.std import Handshaked
    u = HsJoinFairShare(Handshaked)
    u.INPUTS = 3
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_HsJoinFairShare()
    print(to_rtl_str(u))
