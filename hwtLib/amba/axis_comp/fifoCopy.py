#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple, Optional, Union

from hwt.code import If
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Signal, Rst_n, Rst, Clk, VectSignal
from hwt.interfaces.utils import propagateClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import packIntf, \
    connectPacked
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.reg import AxiSReg
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.mem.fifoCopy import FifoCopy


@serializeParamsUniq
class AxiSRegCopy(AxiSCompBase, HandshakedFifo):
    """
    Same thing as a :class:`~.AxiSFifoCopy`
    just uses registers without fifo pointers

    .. hwt-autodoc::
    """

    def _declr(self):
        AxiSFifoCopy._declr_io(self)
        with self._paramsShared():
            self.reg = AxiSReg(self.intfCls)

    def _impl(self):
        reg = self.reg
        copy_en = self.dataOut_copy_frame & self.dataOut.valid
        non_data_signals = [reg.dataIn.ready, reg.dataIn.valid]
        if self.ID_WIDTH > 0:
            non_data_signals.append(reg.dataIn.id)
            If(self.dataOut_copy_frame,
               reg.dataIn.id(self.dataOut_replacement_id),
            ).Else(
              reg.dataIn.id(self.dataIn.id)
            )
        If(copy_en,
            reg.dataIn(reg.dataOut, exclude=non_data_signals)
        ).Else(
            reg.dataIn(self.dataIn, exclude=non_data_signals)
        )

        reg.dataIn.valid(copy_en | self.dataIn.valid)
        self.dataIn.ready(reg.dataIn.ready & ~copy_en)

        #self.dataOut(reg.dataOut, exclude=[reg.dataOut.ready, reg.dataOut.valid])
        self.dataOut(reg.dataOut)

        propagateClkRstn(self)


@serializeParamsUniq
class AxiSFifoCopy(AxiSCompBase, HandshakedFifo):
    """
    Synchronous fifo for axi-stream interface which can copy last frame or work
    as a regular fifo.

    :note: DEPTH > axis.MAX_FRAME_LEN

    :see: :class:`hwtLib.handshaked.fifo_copy.HandshakedFifoCopy`

    .. hwt-autodoc:: _example_AxiSFifoCopy
    """
    FIFO_CLS = FifoCopy

    def _declr_io(self):
        HandshakedFifo._declr_io(self)
        # these signals are used sorely in dataOut beat which has last=1
        self.dataOut_copy_frame = Signal()
        if self.ID_WIDTH > 0:
            self.dataOut_replacement_id = VectSignal(self.ID_WIDTH)

    def _declr(self)->None:
        assert self.DEPTH > 1 ,\
            "Fifo is too small, fifo pointers would not work correctly, use register(s) instead"
        HandshakedFifo._declr(self)

    def _impl(self, clk_rst: Optional[Tuple[
            Tuple[Clk, Union[Rst, Rst_n]],
            Tuple[Clk, Union[Rst, Rst_n]]]]=None):
        HandshakedFifo._impl(self, clk_rst=clk_rst)

    def _connect_fifo_in(self):
        rd = self.get_ready_signal
        vld = self.get_valid_signal
        din = self.dataIn
        fIn = self.fifo.dataIn
        wr_en = ~fIn.wait

        rd(din)(wr_en)
        fIn.data(packIntf(din, exclude=[vld(din), rd(din)]))
        fIn.en(vld(din) & wr_en)

    def _connect_fifo_out(self, out_clk, out_rst):
        rd = self.get_ready_signal
        vld = self.get_valid_signal

        fOut = self.fifo.dataOut
        dout = self.dataOut

        out_vld = self._reg("out_vld", def_val=0, clk=out_clk, rst=out_rst)
        vld(dout)(out_vld)
        non_data = [vld(dout), rd(dout),]
        data_connections = connectPacked(fOut.data,
                      dout,
                      exclude=non_data)
        if self.ID_WIDTH > 0:
            replace_id = self._reg("replace_id",
                HStruct(
                    (dout.id._dtype, "val"),
                    (BIT, "vld")
                ),
                def_val={"vld": 0}
            )
            id_from_fifo = [a for a in data_connections if a.dst is dout.id._sig]
            assert id_from_fifo
            If(replace_id.vld,
               dout.id(replace_id.val)
            ).Else(
                *id_from_fifo
            )
            If(dout.last & rd(dout) & vld(dout),
               replace_id.vld(self.dataOut_copy_frame),
               replace_id.val(self.dataOut_replacement_id),
            )

        fOut.en((rd(dout) | ~out_vld) & ~fOut.wait)
        If(rd(dout) | ~out_vld,
           out_vld(~fOut.wait)
        )
        self.fifo.dataOut_copy_frame.vld(out_vld & dout.last & rd(dout))
        self.fifo.dataOut_copy_frame.data(self.dataOut_copy_frame)

        return out_vld


def _example_AxiSFifoCopy():
    u = AxiSFifoCopy()
    u.DEPTH = 4
    u.ID_WIDTH = 2
    # u.EXPORT_SIZE = True
    # u.EXPORT_SPACE = True
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AxiSFifoCopy()

    print(to_rtl_str(u))
