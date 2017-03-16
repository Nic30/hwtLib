from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.streamNode import streamAck, streamSync
from hwt.code import If, connect
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn


class AxiS_en(AxiSCompBase):
    """
    If en signal is 0 current frame is finished
    and next frame is started only when en is 1
    """
    def _declr(self):
        addClkRstn(self)
        self.en = Signal()
        self.dataIn = self.intfCls()
        self.dataOut = self.intfCls()

    def _impl(self):
        din = self.dataIn
        dout = self.dataOut

        framePending = self._reg("framePending", defVal=False)
        ack = streamAck([din], [dout])

        If(framePending & ack,
           framePending ** ~din.last
        )

        dataEn = self.en | framePending
        streamSync(masters=[din],
                   slaves=[dout],
                   extraConds={din: dataEn,
                               dout: dataEn,
                               })

        connect(din, dout, exclude=[din.ready, din.valid])

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.amba.axis import AxiStream_withoutSTRB
    u = AxiS_en(AxiStream_withoutSTRB)

    print(toRtl(u))
