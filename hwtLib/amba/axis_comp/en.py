#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hwIOs.std import HwIOSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axis_comp.base import Axi4SCompBase
from hwtLib.handshaked.streamNode import StreamNode


class Axi4S_en(Axi4SCompBase):
    """
    This component is like on-off switch for axi stream interface
    which does care about frames.
    If en signal is 0 current frame is finished
    and next frame is started only when en is 1

    .. hwt-autodoc::
    """
    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.en = HwIOSignal()
        with self._hwParamsShared():
            self.dataIn = Axi4Stream()
            self.dataOut = Axi4Stream()._m()

    @override
    def hwImpl(self):
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
    from hwt.synth import to_rtl_str
    m = Axi4S_en()

    print(to_rtl_str(m))
