#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch, SwitchLogic
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.hdl.value import HValue
from hwt.interfaces.std import Signal, HandshakeSync, VectSignal
from hwt.interfaces.utils import propagateClkRstn
from hwt.math import log2ceil
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axis_comp.frame_join import AxiS_FrameJoin
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.amba.datapump.base import AxiDatapumpBase
from hwtLib.amba.datapump.intf import AxiRDatapumpIntf
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from pyMathBitPrecise.bit_utils import mask
from hwt.hdl.types.defs import BIT


class TransEndInfo(HandshakeSync):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = Param(0)
        self.DATA_WIDTH = Param(64)
        self.HAS_PROPAGATE_LAST = Param(True)
        self.SHIFT_OPTIONS = Param((0,))

    def _declr(self):
        if self.ID_WIDTH:
            self.id = VectSignal(self.ID_WIDTH)
        # rem is number of bits in last word which is valid - 1,
        # if rem == 0 it means all bytes are valid
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))
        if self.SHIFT_OPTIONS != (0,):
            self.shift = VectSignal(log2ceil(len(self.SHIFT_OPTIONS)))
        if self.HAS_PROPAGATE_LAST:
            self.propagateLast = Signal()
        HandshakeSync._declr(self)


@serializeParamsUniq
class Axi_rDatapump(AxiDatapumpBase):
    """
    Forward request to axi address read channel
    and collect data to data channel form axi read data channel

    * Blocks data channel when there is no request pending.

    * If req len is wider transaction is internally split to multiple axi
      transactions, but returned read data is a single packet as originally requested.

    * errorRead stays high when there was error on axi read channel
      it will not affect unit functionality

    * id of driver is a different id than is used on AXI
      this is because the id on driver side is used to distinguish between
      transactions and on AXI side it has to be same to assert that the transactions
      will be finished in-order.

    :see: :class:`hwtLib.amba.datapump.base.AxiDatapumpBase`

    .. hwt-autodoc::
    """

    def _declr(self):
        super()._declr()  # add clk, rst, axi addr channel and req channel

        self.errorRead = Signal()._m()
        if self.ALIGNAS != 8:
            self.errorAlignment = Signal()._m()

        with self._paramsShared():
            self.axi.HAS_W = False
            d = self.driver = AxiRDatapumpIntf()
            d.ID_WIDTH = 0
            d.MAX_BYTES = self.MAX_CHUNKS * (self.CHUNK_WIDTH // 8)

            f = self.sizeRmFifo = HandshakedFifo(TransEndInfo)
            f.ID_WIDTH = 0
            f.DEPTH = self.MAX_TRANS_OVERLAP
            f.SHIFT_OPTIONS = self.getShiftOptions()

    def storeTransInfo(self, transInfo: TransEndInfo, isLast: bool):
        if isLast:
            rem = self.driver.req.rem
        else:
            rem = 0

        offset = self.driver.req.addr[self.getSizeAlignBits():]
        return [
            transInfo.rem(rem),
            transInfo.propagateLast(int(isLast)),
            *([]
              if self.isAlwaysAligned() else
              [self.encodeShiftValue(transInfo.SHIFT_OPTIONS, offset, transInfo.shift), ]),
        ]

    def remSizeToStrb(self, remSize: RtlSignal, strb: RtlSignal, isFirstWord, isLastWord):
        sizeRm = self.sizeRmFifo.dataOut
        STRB_W = strb._dtype.bit_length()
        if self.isAlwaysAligned():
            STRB_ALL = mask(STRB_W)
            strbSwitch = Switch(remSize)\
                .Case(0,
                      strb(STRB_ALL)
                ).add_cases(
                    [(i + 1, strb(mask(i + 1)))
                     for i in range(STRB_W - 1)]
                ).Default(
                    strb(None)
                )
            if isinstance(isLastWord, (bool, int, HValue)):
                if isLastWord:
                    return strbSwitch
                else:
                    return strb(STRB_ALL)
            else:
                return If(isLastWord,
                    strbSwitch
                ).Else(
                    strb(STRB_ALL)
                )
        else:
            CHUNK = self.CHUNK_WIDTH // 8
            MAX_BYTES = CHUNK * self.MAX_CHUNKS
            STRB_ALL = mask(min(STRB_W, MAX_BYTES))
            ALIGNAS = self.ALIGNAS
            possibleBytesInLastWord = set()
            assert self.DATA_WIDTH % ALIGNAS == 0, ("Required to resolve number of bytes in last word", self.DATA_WIDTH, ALIGNAS)
            for CHUNK_CNT in range(1, min(self.MAX_CHUNKS, max(3, self.DATA_WIDTH // CHUNK * 3)) + 1):
                for o in range(0, STRB_W, ALIGNAS // 8):
                    bytesInLastWord = (o + CHUNK * CHUNK_CNT) % (self.DATA_WIDTH // 8)
                    if bytesInLastWord in possibleBytesInLastWord:
                        break
                    possibleBytesInLastWord.add(bytesInLastWord)
            possibleBytesInLastWord = sorted(possibleBytesInLastWord)

            offsetsAlignmentCombinations = set([
                # bytesInLastWord, offset value of value in last word, index of shift option
                (min(bytesInLastWord, MAX_BYTES), sh // 8, sh_i)
                 for bytesInLastWord in possibleBytesInLastWord
                 for sh_i, sh in enumerate(sizeRm.SHIFT_OPTIONS)
                 if bytesInLastWord <= MAX_BYTES
            ])
            offsetsAlignmentCombinations = sorted(offsetsAlignmentCombinations)

            t = strb._dtype.from_py
            # :attention: last word can be first word as well
            MASK_ALL = mask(STRB_W)
            WORD_W = strb._dtype.bit_length()
            return \
                SwitchLogic([
                    (remSize._eq(0 if bytesInLastWord == STRB_W else bytesInLastWord) & sizeRm.shift._eq(shift_i),
                        strb(
                             # dissable prefix bytes if this is first word
                             isFirstWord._ternary(t((MASK_ALL << shift) & MASK_ALL), t(MASK_ALL)) &
                             # dissable suffix bytes if this last word
                             isLastWord._ternary(t(MASK_ALL >> ((WORD_W - bytesInLastWord - shift) % WORD_W)), t(MASK_ALL))
                        )
                    )
                    for bytesInLastWord, shift, shift_i in offsetsAlignmentCombinations
                    ],
                    default=strb(None)
                )

    def dataHandler(self, rErrFlag: RtlSignal, rmSizeOut: TransEndInfo):
        rIn = self.axi.r
        rOut = self.driver.r

        if self.axi.LEN_WIDTH:
            last = rIn.last
        else:
            last = BIT.from_py(1)

        rInLast = last

        if self.useTransSplitting():
            last = rmSizeOut.propagateLast & last

        if self.isAlwaysAligned():
            # without shift logic
            * ([self.remSizeToStrb(rmSizeOut.rem, rOut.strb, False, rIn.valid & last), ] if self.USE_STRB else []),
            rOut.data(rIn.data)
            rOut.last(last)
            StreamNode(
                masters=[rIn, rmSizeOut],
                slaves=[rOut],
                extraConds={
                    rmSizeOut: rInLast,
                    rOut:~rErrFlag
                }
            ).sync()

        else:
            # align shifted incoming read data and optionally merge frames
            aligner = AxiS_FrameJoin()
            aligner.T = HStruct(
                (HStream(Bits(self.CHUNK_WIDTH),
                         start_offsets=[i // 8 for i in self.getShiftOptions()],
                         frame_len=(1, self.MAX_CHUNKS)
                         ), "f0"),
            )
            aligner.USE_STRB = False
            aligner.DATA_WIDTH = self.DATA_WIDTH
            self.aligner = aligner

            isSingleWordOnly = self.CHUNK_WIDTH * self.MAX_CHUNKS <= self.DATA_WIDTH and self.ALIGNAS % (self.CHUNK_WIDTH * self.MAX_CHUNKS) == 0
            if isSingleWordOnly:
                first = BIT.from_py(1)
            else:
                # first beat of output frame (not necessary input frame, as multiple input
                # frames could be merged in to a single output frame)
                first = self._reg(f"first", def_val=1)

                If(StreamNode([rIn, rmSizeOut], [aligner.dataIn[0], ]).ack(),
                    first(last),
                )

            aligner.dataIn[0].data(rIn.data)
            aligner.dataIn[0].last(last)
            self.remSizeToStrb(rmSizeOut.rem, aligner.dataIn[0].keep, first, last)

            StreamNode(
                [rIn, rmSizeOut],
                [aligner.dataIn[0], ],
                extraConds={
                    rmSizeOut:~rErrFlag & rInLast,
                }
            ).sync()

            if self.USE_STRB:
                rOut.strb(aligner.dataOut.keep)
            rOut.data(aligner.dataOut.data)
            rOut.last(aligner.dataOut.last)

            StreamNode(
                masters=[aligner.dataOut, ],
                slaves=[rOut],
                extraConds={
                    rOut:~rErrFlag
                }
            ).sync()

    def _impl(self):
        r = self.axi.r
        errorRead = self._reg("errorRead", def_val=0)
        If(r.valid & (r.resp != RESP_OKAY),
           errorRead(1)
        )
        self.errorRead(errorRead)
        err = errorRead

        if self.ALIGNAS != 8:
            req = self.driver.req
            errorAlignment = self._reg("errorAlignment", def_val=0)
            If(req.vld & (req.addr[log2ceil(self.ALIGNAS // 8):] != 0),
               errorAlignment(1)
            )
            self.errorAlignment(errorAlignment)
            err = err | errorAlignment

        self.addrHandler(self.driver.req, self.axi.ar, self.sizeRmFifo.dataIn, err)
        self.dataHandler(err, self.sizeRmFifo.dataOut)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # import sys
    # sys.setrecursionlimit(5000)
    u = Axi_rDatapump()
    u.DATA_WIDTH = 512
    u.MAX_CHUNKS = 1
    u.CHUNK_WIDTH = 32
    u.ALIGNAS = 32
    print(to_rtl_str(u))
