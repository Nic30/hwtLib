#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import log2ceil, connect, Switch, If
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.utils import addClkRstn
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.streamNode import streamSync, streamAck


class AxiS_append(AxiSCompBase):
    """
    AXI-Stream Append

    Behind frame from dataIn0 is appended data from dataIn1.
    No data alignment is performed.
    """
    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn0 = self.intfCls()
            self.dataIn1 = self.intfCls()
            self.dataOut = self.intfCls()

    def _impl(self):
        In0 = self.dataIn0
        In1 = self.dataIn1
        out = self.dataOut

        selected = self._reg("selected", vecT(log2ceil(2), False), defVal=0)

        If(selected,
              connect(In1, out, exclude={out.valid, out.ready}),
              In0.ready ** 0,
              streamSync(masters=[In1], slaves=[out]),
              If(streamAck(masters=[In1], slaves=[out]) & In1.last,
                 selected ** 0
              )
        ).Else(
              connect(In0, out, exclude={out.valid, out.ready}),
              streamSync(masters=[In0], slaves=[out]),
              In1.ready ** 0,
              If(streamAck(masters=[In0], slaves=[out]) & In0.last,
                 selected ** 1
              )
        )

if __name__ == "__main__":
    from hwtLib.amba.axis import AxiStream_withoutSTRB
    from hwt.synthesizer.shortcuts import toRtl
    u = AxiS_append(AxiStream_withoutSTRB)
    print(toRtl(u))
