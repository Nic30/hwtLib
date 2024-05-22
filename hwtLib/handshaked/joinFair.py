#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, rol, SwitchLogic
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BIT
from hwt.hwIOs.std import HwIODataVld
from hwt.hwIOs.utils import addClkRstn
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
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

    @override
    def hwConfig(self):
        HsJoinPrioritized.hwConfig(self)
        self.EXPORT_SELECTED = HwParam(True)

    @override
    def hwDeclr(self):
        HsJoinPrioritized.hwDeclr(self)
        addClkRstn(self)
        if self.EXPORT_SELECTED:
            s = self.selectedOneHot = HwIODataVld()._m()
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
            priority = self._reg("priority", HBits(len(din_vlds)), def_val=1)
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

    @override
    def hwImpl(self):
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
    from hwt.hwIOs.std import HwIODataRdVld

    m = HsJoinFairShare(HwIODataRdVld)
    m.INPUTS = 3
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_HsJoinFairShare()
    print(to_rtl_str(m))
