#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import And, If, Or, iterBits, rol, ror, SwitchLogic
from hwt.hdlObjects.typeShortcuts import vecT
from hwtLib.handshaked.join import HandshakedJoin
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param, evalParam
from hwt.interfaces.std import VldSynced


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

    def dataConnectionExpr(self, dIn, dOut):
        """Create connection between input and output interface"""
        data = self.getData
        dataConnectExpr = []
        outDataSignals = list(data(dOut))
        
        if dIn is None:
            dIn = [None for _ in outDataSignals]
        else:
            dIn = data(dIn)
        
        for _din, _dout in zip(dIn, outDataSignals):
            dataConnectExpr.extend(_dout ** _din)

        return dataConnectExpr

    def isSelectedLogic(self, EXPORT_SELECTED):
        vld = self.getVld
        rd = self.getRd
        dout = self.dataOut
        
        priority = self._reg("priority", vecT(self.INPUTS), defVal=1)
        priority ** rol(priority, 1)

        vldSignals = list(map(vld, self.dataIn))

        isSelectedFlags = []
        for i, din in enumerate(self.dataIn):
            isSelected = self._sig("isSelected_%d" % i)
            isSelected ** priorityAck(priority, vldSignals, i)
            isSelectedFlags.append(isSelected)

            rd(din) ** (isSelected & rd(dout))

            if EXPORT_SELECTED:
                self.selectedOneHot.data[i] ** (isSelected & vld(din))
        
        if EXPORT_SELECTED:
            self.selectedOneHot.vld ** (Or(*vldSignals) & rd(dout))
        
        return isSelectedFlags, vldSignals
    
    def inputMuxLogic(self, isSelectedFlags, vldSignals):
        vld = self.getVld
        dout = self.dataOut

        # data out mux
        dataCases = []
        for isSelected, din in zip(isSelectedFlags, self.dataIn):
            dataConnectExpr = self.dataConnectionExpr(din, dout)
            cond = vld(din) & isSelected
            dataCases.append((cond, dataConnectExpr))

        dataDefault = self.dataConnectionExpr(None, dout)
        SwitchLogic(dataCases, dataDefault)
        vld(dout) ** Or(*vldSignals)

    def _impl(self):
        EXPORT_SELECTED = evalParam(self.EXPORT_SELECTED).val

        isSelectedFlags, vldSignals = self.isSelectedLogic(EXPORT_SELECTED)
        self.inputMuxLogic(isSelectedFlags, vldSignals)



if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HsJoinFairShare(Handshaked)
    u.INPUTS.set(3)
    print(toRtl(u))
