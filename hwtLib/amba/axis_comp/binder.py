#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, c
from hwt.interfaces.utils import addClkRstn
from hwt.intfLvl import Unit, Param
from hwtLib.amba.axis import AxiStream, AxiStream_withoutSTRB


def axiStreamDec(sel, in0, in1, out):
    If(sel,
       c(in0, out),
       in1.ready ** 0
    ).Else(
       c(in1, out),
       in0.ready ** 0 
    )

class AxiSBinder(Unit):
    """
    This unit merges two axi stream inputs into one output
    Round-Robin like scheduling 
    Latency : 0
    Delay   : 0
    """
    def __init__(self, axiIntfCls=AxiStream):
        """
        @param axiIntfCls: class of interface which should be used as interface of this unit
        """
        assert(issubclass(axiIntfCls, AxiStream_withoutSTRB))
        self.axiIntfCls = axiIntfCls
        super().__init__()
        
    def _config(self):
        self.DATA_WIDTH = Param(64)
    
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn0 = self.axiIntfCls()
            self.dataIn1 = self.axiIntfCls()
            self.dataOut = self.axiIntfCls()
        
    def _impl(self):
        transInProgress = self._reg('transInProgress', defVal=0)
        prefer0 = self._reg('prefer0', defVal=0)
        
        outRd = self.dataOut.ready
        in0vld = self.dataIn0.valid
        in0last = self.dataIn0.last
        
        in1vld = self.dataIn1.valid
        in1last = self.dataIn1.last
        
        axiStreamDec(prefer0, self.dataIn0, self.dataIn1, self.dataOut)
        
        If(transInProgress,
            If(prefer0 & in1vld & outRd & in1last,
               prefer0 ** False,
               transInProgress ** 0,
            ).Else(
                If(~prefer0 & in0vld & outRd & in0last,
                   prefer0 ** True,
                   transInProgress ** False,
                )
            )
        ).Else(
            transInProgress ** (outRd & (in0vld | in1vld))
        )
        
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiSBinder()
    print(toRtl(u))
    
    
