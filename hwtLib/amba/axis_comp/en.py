#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.streamNode import StreamNode


class AxiS_en(AxiSCompBase):
    """
    This component is like on-off switch for axi stream interface
    which does care about frames.
    If en signal is 0 current frame is finished
    and next frame is started only when en is 1

    .. hwt-autodoc::
    """
    def _declr(self):
        addClkRstn(self)
        self.en = Signal()
        with self._paramsShared():
            self.dataIn = AxiStream()
            self.dataOut = AxiStream()._m()

    def _impl(self):
        din = self.dataIn
        dout = self.dataOut

        framePending = self._reg("framePending", def_val=False)
        ack = StreamNode([din], [dout]).ack()

        If(framePending & ack,
           framePending(~din.last)
        )

        dataEn = self.en | framePending
        StreamNode(masters=[din],
                   slaves=[dout]).sync(dataEn)

        dout(din, exclude=[din.ready, din.valid])


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = AxiS_en()

    print(to_rtl_str(u))
