#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import And, If, Or, iterBits, rol, ror
from hwt.hdlObjects.typeShortcuts import vecT
from hwtLib.handshaked.join import HandshakedJoin
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param, evalParam
from hwt.interfaces.std import VectSignal, VldSynced


def priorityAck(priorityReg, vldSignals, index):
    priorityOverdrives = []
    vldWithHigherPriority = list(vldSignals[:index])

    for i, (p, vld) in enumerate(zip(iterBits(priorityReg), vldSignals)):
        if i > index:
            priorityOverdrives.append(p & vld)


    ack = ~Or(*priorityOverdrives, *vldWithHigherPriority) | priorityReg[index]

    return ack


class HsJoinFairShare(HandshakedJoin):
    """
    Join input stream to single output stream
    inputs with lower number has higher priority

    Priority is changing every clock 
    If prioritized input is not sending valid data, 
    input with lowest index and valid is used

    combinational
    """
    def _config(self):
        HandshakedJoin._config(self)
        self.EXPORT_SELECTED = Param(True)

    def _declr(self):
        HandshakedJoin._declr(self)
        addClkRstn(self)
        if evalParam(self.EXPORT_SELECTED).val:
            self.selectedOneHot = VldSynced()
            self.selectedOneHot._replaceParam("DATA_WIDTH", self.INPUTS)

    def _impl(self):
        rd = self.getRd
        vld = self.getVld
        data = self.getData
        dout = self.dataOut
        EXPORT_SELECTED = evalParam(self.EXPORT_SELECTED).val

        priority = self._reg("priority", vecT(self.INPUTS), defVal=1)

        vldSignals = list(map(vld, self.dataIn))

        isSelected_tmp = []
        for i, din in enumerate(self.dataIn):
            isSelected = self._sig("isSelected_%d" % i)
            isSelected ** priorityAck(priority, vldSignals, i)
            isSelected_tmp.append(isSelected)

            rd(din) ** (isSelected & rd(dout))

            if EXPORT_SELECTED:
                self.selectedOneHot.data[i] ** (isSelected & vld(din))

        # data out mux
        outMuxTop = []
        for d in data(dout):
            outMuxTop.extend(d ** None)
        for isSelected, din in zip(reversed(isSelected_tmp), reversed(list(self.dataIn))):
            dataConnectExpr = []
            for _din, _dout in zip(data(din), data(dout)):
                dataConnectExpr.extend(_dout ** _din)

            outMuxTop = If(vld(din) & isSelected,
                dataConnectExpr
            ).Else(
                outMuxTop
            )

        priority ** rol(priority, 1)
        vld(dout) ** Or(*vldSignals)
        if EXPORT_SELECTED:
            self.selectedOneHot.vld ** (Or(*vldSignals) & rd(dout))

if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HsJoinFairShare(Handshaked)
    u.INPUTS.set(3)
    print(toRtl(u))
