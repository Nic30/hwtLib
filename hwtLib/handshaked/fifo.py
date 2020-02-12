#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Tuple, Union

from hwt.code import If, connect, log2ceil
from hwt.interfaces.std import VectSignal, Clk, Rst_n, Rst
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import packIntf, \
    connectPacked
from hwt.synthesizer.param import Param
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.mem.fifo import Fifo


@serializeParamsUniq
class HandshakedFifo(HandshakedCompBase):
    """
    Synchronous FIFO for handshaked interfaces

    .. aafig::
                 +-+-+-+-+-+
         input   | | | | | | output
       +-stream--> | | | | +-stream->
                 | | | | | |
                 +-+-+-+-+-+

    .. hwt-schematic:: _example_HandshakedFifo
    """

    def _config(self):
        self.DEPTH = Param(0)
        self.EXPORT_SIZE = Param(False)
        super()._config()

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls()._m()

        f = self.fifo = Fifo()
        DW = self.dataIn._bit_length() - 2  # 2 for control (valid, ready)
        f.DATA_WIDTH = DW
        f.DEPTH = self.DEPTH - 1  # because there is an extra register
        f.EXPORT_SIZE = self.EXPORT_SIZE

        if self.EXPORT_SIZE:
            self.size = VectSignal(
                log2ceil(self.DEPTH + 1 + 1), signed=False)._m()

    def _impl(self,
              clk_rst: Optional[Tuple[
                  Tuple[Clk, Union[Rst, Rst_n]],
                  Tuple[Clk, Union[Rst, Rst_n]]]]=None):
        """
        :param clk_rst: optional tuple ((inClk, inRst), (outClk, outRst))
        """
        rd = self.get_ready_signal
        vld = self.get_valid_signal

        # connect clock and resets
        if clk_rst is None:
            propagateClkRstn(self)
            outClk = None
            outRst = None
        else:
            (inClk, inRst), (outClk, outRst) = clk_rst
            f = self.fifo
            f.dataIn_clk(inClk)
            f.dataIn_rst_n(inRst)
            f.dataOut_clk(outClk)
            f.dataOut_rst_n(outRst)

        # to fifo
        fIn = self.fifo.dataIn
        din = self.dataIn
        wr_en = ~fIn.wait
        rd(din)(wr_en)
        fIn.data(packIntf(din, exclude=[vld(din), rd(din)]))
        fIn.en(vld(din) & wr_en)

        # from fifo
        fOut = self.fifo.dataOut
        dout = self.dataOut
        out_vld = self._reg("out_vld", def_val=0, clk=outClk, rst=outRst)
        vld(dout)(out_vld)
        connectPacked(fOut.data,
                      dout,
                      exclude=[vld(dout), rd(dout)])
        fOut.en((rd(dout) | ~out_vld) & ~fOut.wait)
        If(rd(dout) | ~out_vld,
           out_vld(~fOut.wait)
        )

        if self.EXPORT_SIZE:
            sizeTmp = self._sig("sizeTmp", self.size._dtype)
            connect(self.fifo.size, sizeTmp, fit=True)

            If(out_vld,
               self.size(sizeTmp + 1)
            ).Else(
                connect(self.fifo.size, self.size, fit=True)
            )


def _example_HandshakedFifo():
    from hwt.interfaces.std import Handshaked
    u = HandshakedFifo(Handshaked)
    u.DEPTH = 8
    u.DATA_WIDTH = 4
    u.EXPORT_SIZE = True
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_HandshakedFifo()
    print(toRtl(u))
