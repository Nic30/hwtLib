#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, connect
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.streamNode import StreamNode


class AxiS_en(AxiSCompBase):
    """
    This component is like on-off switch for axi stream interface
    which does care about frames.
    If en signal is 0 current frame is finished
    and next frame is started only when en is 1
    
    :note: interface is configurable and schematic is example with AxiStream
    
    .. hwt-schematic:: _example_AxiS_en
    """
    def _declr(self):
        addClkRstn(self)
        self.en = Signal()
        self.dataIn = self.intfCls()
        self.dataOut = self.intfCls()._m()

    def _impl(self):
        din = self.dataIn
        dout = self.dataOut

        framePending = self._reg("framePending", defVal=False)
        ack = StreamNode([din], [dout]).ack()

        If(framePending & ack,
           framePending(~din.last)
        )

        dataEn = self.en | framePending
        StreamNode(masters=[din],
                   slaves=[dout]).sync(dataEn)

        connect(din, dout, exclude=[din.ready, din.valid])

def _example_AxiS_en():
    from hwtLib.amba.axis import AxiStream
    u = AxiS_en(AxiStream)
    return u

if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiS_en()

    print(toRtl(u))
