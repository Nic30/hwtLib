#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.constants import DIRECTION
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.utils import addClkRstn
from hwt.code import If, FsmBuilder
from hwt.synthesizer.param import Param, evalParam
from hwtLib.amba.axis_comp.base import AxiSCompBase


class AxiSAppend(AxiSCompBase):
    """
    AXI-Stream Append
    
    Behind frame from dataIn0 is appended data from dataIn1.
    If JOIN is set frames are merged. 
    No data alignment is performed.
    """
    def _config(self):
        super()._config()
        self.JOIN = Param(True)
        
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn0 = self.intfCls()
            self.dataIn1 = self.intfCls()
            self.dataOut = self.intfCls()
        
    def _impl(self):
        stT = Enum('t_state', ["sendDataIn0", "sendDataIn1"])
        In0 = self.dataIn0
        In1 = self.dataIn1
        out = self.dataOut
        vld = self.getVld 
        rd = self.getRd
        
        st = FsmBuilder(self, stT)\
        .Trans(stT.sendDataIn0,
            (vld(In0) & In0.last & rd(out), stT.sendDataIn1)               
        ).Trans(stT.sendDataIn1,
            (vld(In1) & In1.last & rd(out), stT.sendDataIn0)
        ).stateReg

        doJoin = evalParam(self.JOIN).val
        i = lambda intf: intf._interfaces
        for i0, i1, oi in zip(i(self.dataIn0),
                              i(self.dataIn1),
                              i(self.dataOut)):
            if oi._masterDir == DIRECTION.IN:
                # swap because direction is opposite
                i0 ** (oi & st._eq(stT.sendDataIn0))
                i1 ** (oi & st._eq(stT.sendDataIn1))
            else:
                if oi._name == "last" and doJoin:
                    i0 = 0
                If(st._eq(stT.sendDataIn0),
                    oi ** i0,
                ).Else(
                    oi ** i1 
                )

if __name__ == "__main__":
    from hwtLib.amba.axis import AxiStream_withoutSTRB
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSAppend(AxiStream_withoutSTRB)
    print(toRtl(u))
