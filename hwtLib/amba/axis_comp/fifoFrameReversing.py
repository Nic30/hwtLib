#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.constants import READ, WRITE
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIORdVldSync
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.interfaceLevel.utils import HwIO_connectPacked, HwIO_pack
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.fifoPtrLogic import FifoPtrLogic
from hwtLib.mem.ram import RamSingleClock


class HwIoFifoIndexTuple(HwIORdVldSync):

    @override
    def hwConfig(self) -> None:
        self.INDEX_WIDTH = HwParam(16)

    @override
    def hwDeclr(self):
        t = HBits(self.INDEX_WIDTH, signed=False)
        # for example  begin=0, end=0, size=1
        # begin/end represent fifo pointers and begin may be <= end and end <= begin
        # if size of fifo is not power of 2 the substraction will need saturation
        self.begin = HwIOSignal(t)
        self.end = HwIOSignal(t)
        self.size = HwIOSignal(t)
        super().hwDeclr()


class Axi4S_fifoFrameReversing(HwModule):
    """
    FIFO which returns the word of the frame in reversal order

    .. code-block::text
        begin            end
        <------------r  w -----------> 
        f0.0 f0.1 f0.2  f1.0 f1.1 f1.2
        
        input  f0.0 f0.1 f0.3  f1.0 f1.1 f1.2
        output f0.2 f0.1 f0.0  f1.2 f1.1 f1.0

    :ivar MAX_PKT_WORDS: max number of words per packet
    :ivar MAX_PKT_CNT: max number of packets in storable in this FIFO
    :ivar DEPTH: max number of packet words storable in this FIFO
    :attention: does not support ZLP (Zero-length-packets)

    .. hwt-autodoc:: _example_Axi4S_fifoFrameReversing
    """
    REG_CLS = NotImplementedError

    @override
    def hwConfig(self):
        Axi4Stream.hwConfig(self)
        self.MAX_PKT_WORDS = HwParam((2048 // 8) - 1)
        self.MAX_PKT_CNT = HwParam(2)
        self.DEPTH = HwParam(self.MAX_PKT_WORDS * self.MAX_PKT_CNT)
        self.INIT_DATA: tuple = HwParam(())

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = Axi4Stream()
            self.dataOut = Axi4Stream()._m()

        self.index_t = HBits(log2ceil(self.DEPTH), signed=False)
        ram = RamSingleClock()
        ram.ADDR_WIDTH = log2ceil(self.DEPTH)
        ram.DATA_WIDTH = self.dataIn._bit_length() - 3  # exclude ready, valid, last
        ram.PORT_CNT = (WRITE, READ)
        self.ram = ram

        framePosFifo = HandshakedFifo(HwIoFifoIndexTuple)
        framePosFifo.DEPTH = self.MAX_PKT_CNT
        framePosFifo.INDEX_WIDTH = self.index_t.bit_length()
        self.framePosFifo = framePosFifo

    @override
    def hwImpl(self):
        propagateClkRstn(self)

        ram = self.ram
        framePosFifo = self.framePosFifo

        # write logic
        write_en = self._sig("write_en")
        write_wait = self._sig("write_wait")

        read_en = self._sig("read_en")
        read_wait = self._sig("read_wait")
        fifoPtrs = FifoPtrLogic(self, self.DEPTH, INIT_SIZE=len(self.INIT_DATA))
        read_increment = self._sig("read_increment", fifoPtrs.index_t)

        (_, write_index), (_, _) = fifoPtrs.fifo_pointers((write_en, write_wait),
                                                          [(read_en, read_wait, read_increment)])

        dIn = self.dataIn
        ramIn = ram.port[0]
        inSNode = StreamNode(
            masters=[
                dIn,
            ],
            slaves=[
                framePosFifo.dataIn,
                (ramIn.en, 1),
            ],
            extraConds={
                framePosFifo.dataIn: dIn.valid & dIn.last,
            },
            skipWhen={
                framePosFifo.dataIn: dIn.valid & ~dIn.last,
            })
        inAck = inSNode.ack()
        write_en(inAck)
        inSNode.sync(~write_wait)
        inAck = inAck & ~write_wait
        
        ramIn.addr(write_index)
        ramIn.din(HwIO_pack(dIn, exclude=(dIn.ready, dIn.valid, dIn.last)))

        assert self.MAX_PKT_WORDS <= self.DEPTH // 2, (self.MAX_PKT_WORDS, self.DEPTH, "It is necessary for fifoPtrs.index_t to hold max size of packet")
        in_frame_begin_size = self._reg("in_frame_begin_size", fifoPtrs.index_t, def_val=1)
        frame_begin_index = self._reg("frame_begin_index", write_index._dtype)
        sof = self._reg("sof", def_val=1)
        If(inAck,
           If(sof,
              frame_begin_index(write_index),
           ),
           sof(dIn.last),
           If(dIn.last,
              # reset in_frame_begin_size
              in_frame_begin_size(1),
           ).Else(
              in_frame_begin_size(in_frame_begin_size + 1),
           )
        )
        If(sof,
            framePosFifo.dataIn.begin(write_index),
        ).Else(
            framePosFifo.dataIn.begin(frame_begin_index),
        )
        framePosFifo.dataIn.size(in_frame_begin_size)
        framePosFifo.dataIn.end(write_index)

        dOut = self.dataOut

        fRegsValid = self._reg("out_frame_regs_valid", def_val=0)
        # :note: outWord itself is latched at the output of the ram
        # :note: outWordValid has to be 1 clk delayed for data to load from ram
        outWordValid = self._reg("outWordValid", def_val=0)

        fBegin = self._reg("out_frame_begin_index", fifoPtrs.index_t)
        fEnd = self._reg("out_frame_end_index", fifoPtrs.index_t)
        fSize = self._reg("out_frameSize", fifoPtrs.index_t)
        outLast = fBegin._eq(fEnd)
        outWordLast = self._reg("out_word_last")

        # while begin != end: end -=1
        outWordAck = ~outWordValid | dOut.ready
        loadNewFramePtrs = rename_signal(self,
            (~fRegsValid | (fRegsValid & outLast)) & (~outWordValid | outWordAck),
            "loadNewFramePtrs")
        framePosFifo.dataOut.rd(loadNewFramePtrs)
        read_increment(fSize)
        # consume previous frame from fifo
        read_en(loadNewFramePtrs & fRegsValid)
        If(loadNewFramePtrs,
           # load new record from framePosFifo
           fBegin(framePosFifo.dataOut.begin),
           fEnd(framePosFifo.dataOut.end),
           fSize(framePosFifo.dataOut.size),

           outWordValid(fRegsValid),
           fRegsValid(framePosFifo.dataOut.vld),

        ).Elif(outWordAck,
            fEnd(fifoPtrs._usub_with_modulo(fEnd, 1)),
            outWordValid(~outLast),
        )
        ramOut = ram.port[1]
        # If(loadNewFramePtrs,
        #   ramOut.addr(framePosFifo.dataOut.begin),
        #   outWordLast(framePosFifo.dataOut.end._eq(framePosFifo.dataOut.begin))
        # ).Else(
        #   ramOut.addr(fEnd),
        #   outWordLast(outLast),
        # )
        ramOut.addr(fEnd)
        ramOut.en(fRegsValid & outWordAck)
        If(fRegsValid & outWordAck,
           outWordLast(outLast)
        )

        dOut.valid(outWordValid)

        HwIO_connectPacked(ram.port[1].dout, dOut, exclude=(dOut.ready, dOut.valid, dOut.last))
        dOut.last(outWordLast)


def _example_Axi4S_fifoFrameReversing():
    m = Axi4S_fifoFrameReversing()
    m.USE_STRB = True
    # u.EXPORT_ALIGNMENT_ERROR = True
    m.MAX_LEN = 15
    m.SIZES_BUFF_DEPTH = 4
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_Axi4S_fifoFrameReversing()
    print(to_rtl_str(m))
