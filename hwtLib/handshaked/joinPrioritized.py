#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import And, Or, SwitchLogic
from hwt.synthesizer.param import Param
from hwtLib.handshaked.compBase import HandshakedCompBase


class HsJoinPrioritized(HandshakedCompBase):
    """
    Join input stream to single output stream
    inputs with lower number has higher priority

    combinational
    """
    def _config(self):
        self.INPUTS = Param(2)
        super()._config()

    def _declr(self):
        with self._paramsShared():
            self.dataIn = self.intfCls(asArraySize=self.INPUTS)
            self.dataOut = self.intfCls()

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

    def _impl(self):
        rd = self.getRd
        vld = self.getVld
        dout = self.dataOut

        vldSignals = list(map(vld, self.dataIn))

        # data out mux
        dataCases = []
        for i, din in enumerate(self.dataIn):
            allLowerPriorNotReady = map(lambda x: ~x, vldSignals[:i])
            rd(din) ** (And(rd(dout), *allLowerPriorNotReady))

            cond = vld(din)
            dataConnectExpr = self.dataConnectionExpr(din, dout)
            dataCases.append((cond, dataConnectExpr))

        dataDefault = self.dataConnectionExpr(None, dout)
        SwitchLogic(dataCases, dataDefault)

        vld(dout) ** Or(*vldSignals)


if __name__ == "__main__":
    from hwt.interfaces.std import Handshaked
    from hwt.synthesizer.shortcuts import toRtl
    u = HandshakedJoinPrioritized(Handshaked)
    print(toRtl(u))
