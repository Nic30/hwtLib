from hwt.code import If, Concat
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode


class HandshakedToAxiStream(HandshakedCompBase):
    """
    Pack raw input data from :class:`hwt.interfaces.std.Handshaked` interface
    into AxiStream frames according to an input timeout or max frame size specification

    :ivar IN_TIMEOUT: number of clk ticks until the actual frame is closed with the last word when
        if there are not input data
    :ivar MAX_FRAME_WORDS: maximum number of words in frame

    .. hwt-autodoc:: _example_HandshakedToAxiStream
    """

    def _config(self) -> None:
        self.IN_TIMEOUT = Param(None)
        self.MAX_FRAME_WORDS = Param(None)
        self.DATA_WIDTH = Param(64)

    def _declr(self) -> None:
        assert self.IN_TIMEOUT or self.MAX_FRAME_WORDS, "Need to have some specification how to resolve frame end"
        addClkRstn(self)

        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut: AxiStream = AxiStream()._m()

    def construct_timeout_cntr_and_in_reg(self):
        TIME_MAX = self.IN_TIMEOUT - 1
        timeout_cntr = self._reg("timeout_cntr", Bits(log2ceil(self.IN_TIMEOUT)), def_val=TIME_MAX)
        last = timeout_cntr._eq(0)
        r = HandshakedReg(self.intfCls)
        r.DATA_WIDTH = self.DATA_WIDTH
        self.r = r
        r.dataIn(self.dataIn)
        return timeout_cntr, TIME_MAX, last, r.dataOut

    def _impl(self) -> None:
        din = self.dataIn
        dout = self.dataOut

        if self.IN_TIMEOUT is not None and self.MAX_FRAME_WORDS:
            timeout_cntr, TIME_MAX, last_timeout, r_out = self.construct_timeout_cntr_and_in_reg()

            WORD_MAX = self.MAX_FRAME_WORDS - 1
            frame_word = self._reg("frame_word", Bits(log2ceil(WORD_MAX)), def_val=0)
            last_size = frame_word._eq(WORD_MAX)

            last = (last_timeout | last_size)
            If(~r_out.vld | (last & dout.ready),
               timeout_cntr(TIME_MAX),
            ).Elif(~self.dataIn.vld & r_out.vld & ~last,
               timeout_cntr(timeout_cntr - 1),
            )
            sn = StreamNode(
                [r_out],
                [dout],
                extraConds={
                    r_out: (last_timeout | (din.vld & r_out.vld)),
                    dout: (last_timeout | (din.vld & r_out.vld)),
                }
            )
            sn.sync()
            dout.data(Concat(*self.get_data(r_out)))
            dout.last(last)

            If(sn.ack(),
                If(last,
                   frame_word(0),
                ).Else(
                   frame_word(frame_word + 1),
                )
            )

        elif self.IN_TIMEOUT:
            # we have to delay last data and send it only
            # in the case of timeout in order to be able to mark it with last flag
            timeout_cntr, TIME_MAX, last, r_out = self.construct_timeout_cntr_and_in_reg()

            If(last & dout.ready,
               timeout_cntr(TIME_MAX),
            ).Elif(~din.vld & r_out.vld & ~last,
               timeout_cntr(timeout_cntr - 1),
            )
            dout.data(Concat(*self.get_data(r_out)))
            dout.last(last)
            sn = StreamNode(
                [r_out],
                [dout],
            ).sync(last | din.vld)

        elif self.MAX_FRAME_WORDS:
            dout.data(Concat(*self.get_data(din)))

            WORD_MAX = self.MAX_FRAME_WORDS - 1
            frame_word = self._reg("frame_word", Bits(log2ceil(self.MAX_FRAME_WORDS)), def_val=0)
            last = frame_word._eq(WORD_MAX)
            dout.last(last)

            sn = StreamNode([din], [dout])
            sn.sync()

            If(sn.ack(),
                If(last,
                   frame_word(0),
                ).Else(
                   frame_word(frame_word + 1),
                )
            )

        propagateClkRstn(self)


def _example_HandshakedToAxiStream():
    u = HandshakedToAxiStream(Handshaked)
    u.IN_TIMEOUT = 10
    # u.MAX_FRAME_WORDS = 8
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_HandshakedToAxiStream()
    print(to_rtl_str(u))
