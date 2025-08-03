#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.code import If
from hwt.doc_markers import hwt_expr_producer
from hwt.hdl.commonConstants import b1
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.mathAutoExt import addAutoExt
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.avalon.st import AvalonST
from hwtLib.clocking.clkBuilder import ClkBuilder
from hwtLib.handshaked.fifo import HandshakedFifo


class AvalonST_latencyAdapter(HwModule):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self) -> None:
        AvalonST.hwConfig(self)
        self.OUT_readyLatency:int = HwParam(0)
        self.OUT_readyAllowance: Optional[int] = HwParam(None)

    @override
    def hwDeclr(self) -> None:
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = AvalonST()
            self.dataOut: AvalonST = AvalonST()._m()
            self.dataOut.readyLatency = self.OUT_readyLatency
            self.dataOut.readyAllowance = self.OUT_readyAllowance

    @hwt_expr_producer
    def _constructAllowanceCreditCounter(self, ready: RtlSignal, valid: RtlSignal, maxVal):
        dstCreditT = HBits(log2ceil(maxVal + 1))
        # :note: the dstCredit guards the maximum number beats send to dst
        #  it is necessary becase we can not rely only on dst.rd or its delayed value because
        #  readyAllowance specifies that the data may be transfered even if rd==0
        dstCredit = self._reg(f"dst_credit", dstCreditT, def_val=0)
        If(ready,
            dstCredit(maxVal)  # restart credit counter if ready=1
        ).Elif(~ready & valid,
            # decrement dstCredit if we did not ceceive rd=1 but dst.readyAllowance specifies that we can send data anyway
            # :note: should never underflow because dst.vld can not be set if there is no dstCredit or dstRdDelayed
            dstCredit(dstCredit - 1)
        )
        return dstCredit

    @override
    def hwImpl(self) -> None:
        """
        https://cdrdv2.intel.com/v1/dl/getContent/667068?fileName=mnl_avalon_spec-683091-667068.pdf
        Based on Avalon Interface Specifications Updated for Intel Quartus Prime Design Suite: 20.1
        Table 19. Source/Sink Adaptation Requirement
        
        Functionality equivalent to Quartus avst_latency_adapter
        
        :note: ready cycle is a cycle during which the sink can accept a transfer
        :note: ready is asserted by the sink on cycle <n> to mark cycle <n + readyLatency>
            as a ready cycle.
            If readyLatency=0 and readyAllowance=0, data transfers occur only
            when both ready and valid are asserted.
            If readyLatency>0 or readyAllowance>0 the source may only assert valid and
            during ready cycles.
        :note: The sink samples data and on ready cycles where valid is asserted 1.
        :note: if readyLatency==0 the interface works as a typical (AXI4 Stream) ready/valid handshake.
            if >0 the ready signaling is delayed (inside of the source). The ready cycle is when source received delayed
            ready=1 from the sink, The source may assert valid only in ready cycle (when it is receiving delayed ready=1)
        :note: if readyLatency > the ready is delayed inside of the source and Avalon-ST itself will use non-delayed value
        :note: readyAllowance defines how many data can sink capture with ready=False, if it is set to None then readyAllowance=readyLatency
        :note: readyLatency/readyAllowance are parameters of FIFO implemented on sink side
            the "ready" represents "almost-full" of this FIFO,
            readyLatency=almost-full-remaining-size - 1,
            readyAllowance=FIFO total size-1. 
            e.g. readyLatency=0, readyAllowance=1 can buffer 1 item with ready=0
        
        :note: When readyLatency=1 and readyAllowance=2 the dst can accept data 1 cycle after rd=1,
               and 2 more cycles of transfers are allowed after rd=0.
        """
        src: AvalonST = self.dataIn
        dst = self.dataOut
        assert src.__class__ is dst.__class__, (src, dst)

        # srcExpectsLargerBuff = src.readyAllowance > dst.readyAllowance
        srcCanSendBeforeDstCanAccept = src.readyLatency < dst.readyLatency
        srcExpectedBuffSize = src.readyAllowance
        if srcCanSendBeforeDstCanAccept:
            # must be able to store additional items before dst can accept them
            # because src ready is sampled in later time han dst expects
            srcExpectedBuffSize += dst.readyLatency - src.readyLatency
        dstProvidedBuffSize = dst.readyAllowance

        if srcExpectedBuffSize > dstProvidedBuffSize:
            # :note: fifo is used to accomodate extra items which we have to buffer
            #   in the case that the dst will stall but we already confirmed to src that we will be able
            #   to receive the data using rd (and because readyLatency we had to assume the optimistic case that
            #   the dst will not stall because otherwise we would severeli limit the troughput)
            fifo = HandshakedFifo(dst.__class__)
            fifo._updateHwParamsFrom(src)
            fifo.readyAllowance = 0
            fifo.readyLatency = 0
            fifo.EXPORT_SPACE = True
            # :note: +1 is there to compensate for the fact that 1 item is output register
            #           thus minimal fill during fifo continuous operation is 2
            # :note: 2* +1 to compensate for latency of in/out
            # :note: +1 because for latency of credit logic
            fifo.DEPTH = srcExpectedBuffSize - dstProvidedBuffSize + src.readyLatency + 4
            self.latencyMatchFifo = fifo
            propagateClkRstn(self)

            dst(fifo.dataOut, exclude=(dst.vld, dst.rd))

            # :note: the fifo may be read on ready cycle (defined by dst readyAllowance,readyLatency),
            # which is when delayed dst.ready==1
            if dst.readyLatency:
                dstRdDelayed = ClkBuilder(self, dst.rd).regPipe(
                    dst.rd, dst.readyLatency - 1,
                    "rd_delay",
                    def_val=[0 for _ in range(dst.readyLatency - 1)])[-1]
                dstCredit = self._constructAllowanceCreditCounter(dstRdDelayed, dst.vld, dst.readyAllowance)
                isReadyCycle = dstCredit != 0
                # :note: fifo.space defines how many empty slots in fifo are currently available,
                #   while dstCredit specifies how many slots are available inside of dst
                actualSpace = addAutoExt(fifo.space, dstCredit)
            else:
                actualSpace = fifo.space
                isReadyCycle = b1

            # connect fifo.dataOut -> dst ready/valid handshake
            fifo.dataOut.rd(isReadyCycle & dst.rd)
            dst.vld(isReadyCycle & fifo.dataOut.vld)

            # :note: src.vld should never be 1 if it is not possible to store the beat
            fifo.dataIn(src, exclude=(src.rd,))
            # src.rd=1 if there is a enough space in fifo or in dst buffer
            # enough means that in the case of dst stall it will be still possile to store the data
            src.rd(actualSpace > (src.readyAllowance + 1))

        else:
            if srcCanSendBeforeDstCanAccept:
                dst(src, exclude=(dst.rd, dst.vld))

                if dst.readyAllowance:
                    # add delay regs for ready to extend src.readyLatency to dst.readyLatency
                    dstRdDelayed = ClkBuilder(self, dst.rd).regPipe(
                        dst.rd, dst.readyLatency - 1, "rd_delayForDst",
                        def_val=[0 for _ in range(dst.readyLatency - 1)])

                    dstCredit = self._constructAllowanceCreditCounter(
                        dstRdDelayed[-1], dst.vld, dst.readyAllowance)
                    # there is a ready
                    enable = dstCredit != 0
                else:
                    enable = ClkBuilder(self, dst.rd).regPipe(
                        dst.rd, dst.readyLatency - src.readyLatency, "rd_delayForDst",
                        def_val=[0 for _ in range(dst.readyLatency)])[-1]

                src.rd(enable)
                if dst.readyLatency == 0:
                    # in this case vld is allowed to be 1 if this is not ready cycle
                    dst.vld(src.vld)
                else:
                    # dst.vld must be 0 if this is not ready cycle
                    dst.vld(src.vld & enable)

            elif src.readyAllowance == 0 and dst.readyAllowance != 0:
                # special case where src can set vld with rd=0 and dst disallows that
                dst(src, exclude=(src.vld,))
                dst.vld(src.vld & dst.rd)
            else:
                dst(src)

        # if src.readyLatency >= dst.readyLatency:
        #    if src.readyAllowance > dst.readyAllowance:
        #        # After ready is deasserted, the source can send more transfers
        #        # than the sink can capture.
        # else:
        #    # src.readyLatency < dst.readyLatency
        #    if src.readyAllowance <= dst.readyAllowance:
        #        # The source can start sending
        #        # transfers before sink can capture.
        #        raise NotImplementedError()
        # dst(src)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = AvalonST_latencyAdapter()
    m.OUT_readyAllowance = 1
    m.OUT_readyLatency = 1
    print(to_rtl_str(m))
