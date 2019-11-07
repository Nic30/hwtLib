#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import And, Or, SwitchLogic
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.handshaked.compBase import HandshakedCompBase


class HsJoinPrioritized(HandshakedCompBase):
    """
    Join input stream to single output stream
    inputs with lower number has higher priority

    :note: combinational

    .. hwt-schematic:: _example_HsJoinPrioritized
    """

    def _config(self):
        self.INPUTS = Param(2)
        super()._config()

    def _declr(self):
        with self._paramsShared():
            self.dataIn = HObjList(
                self.intfCls() for _ in range(int(self.INPUTS))
            )
            self.dataOut = self.intfCls()._m()

    def dataConnectionExpr(self, dIn, dOut):
        """Create connection between input and output interface"""
        data = self.get_data
        dataConnectExpr = []
        outDataSignals = list(data(dOut))

        if dIn is None:
            dIn = [None for _ in outDataSignals]
        else:
            dIn = data(dIn)

        for _din, _dout in zip(dIn, outDataSignals):
            dataConnectExpr.append(_dout(_din))

        return dataConnectExpr

    def _impl(self):
        rd = self.get_ready_signal
        vld = self.get_valid_signal
        dout = self.dataOut

        vldSignals = list(map(vld, self.dataIn))

        # data out mux
        dataCases = []
        for i, din in enumerate(self.dataIn):
            allLowerPriorNotReady = map(lambda x: ~x, vldSignals[:i])
            rd(din)(And(rd(dout), *allLowerPriorNotReady))

            cond = vld(din)
            dataConnectExpr = self.dataConnectionExpr(din, dout)
            dataCases.append((cond, dataConnectExpr))

        dataDefault = self.dataConnectionExpr(None, dout)
        SwitchLogic(dataCases, dataDefault)

        vld(dout)(Or(*vldSignals))


def _example_HsJoinPrioritized():
    from hwt.interfaces.std import Handshaked
    u = HsJoinPrioritized(Handshaked)
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_HsJoinPrioritized()
    print(toRtl(u))
