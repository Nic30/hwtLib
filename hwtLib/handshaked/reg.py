#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from hwt.code import If
from hwt.interfaces.utils import addClkRstn
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.handshaked.compBase import HandshakedCompBase


@serializeParamsUniq
class HandshakedReg(HandshakedCompBase):
    """
    Register for Handshaked interfaces

    :note: latency and delay can be specified as well as interface class
    :note: if LATENCY == (1, 2) the ready chain is broken.
        That there is an extra register for potential data overflow and
        no combinational path between input ready, valid and output ready/valid exists.

    .. hwt-autodoc:: _example_HandshakedReg
    """

    def _config(self):
        HandshakedCompBase._config(self)
        self.LATENCY = Param(1)
        self.DELAY = Param(0)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = self.intfCls()._m()

    def _impl_latency(self, inVld, inRd, inData, outVld, outRd, prefix):
        """
        Create a normal handshaked register
        """
        isOccupied = self._reg(prefix + "isOccupied", def_val=0)
        regs_we = self._sig(prefix + 'reg_we')

        outData = []
        for iin in inData:
            r = self._reg(prefix + 'reg_' + getSignalName(iin), iin._dtype)

            If(regs_we,
                r(iin)
            )
            outData.append(r)

        If(isOccupied,
            inRd(outRd),
            regs_we(inVld & outRd),
            If(outRd & ~inVld,
                isOccupied(0)
            )
        ).Else(
            inRd(1),
            regs_we(inVld),
            isOccupied(inVld)
        )
        outVld(isOccupied)
        return outData

    def _implLatencyAndDelay(self, inVld: RtlSignal, inRd: RtlSignal, inData: List[RtlSignal],
                             outVld: RtlSignal, outRd: RtlSignal, prefix: str):
        """
        Create a register pipe
        """
        wordLoaded = self._reg(prefix + "wordLoaded", def_val=0)
        If(wordLoaded,
           wordLoaded(~outRd)
        ).Else(
            wordLoaded(inVld)
        )

        outData = []
        for iin in inData:
            r = self._reg('reg_' + getSignalName(iin), iin._dtype)
            If(~wordLoaded,
               r(iin)
            )
            outData.append(r)

        inRd(~wordLoaded)
        outVld(wordLoaded)

        return outData

    def _implReadyChainBreak(self, in_vld: RtlSignal, in_rd: RtlSignal, in_data: List[RtlSignal],
                             out_vld: RtlSignal, out_rd: RtlSignal, prefix: str):
        """
        Two sets of registers 0. is prioritized 1. is used as a backup
        The in_rd is not combinationally connected to out_rd
        The out_vld is not combinationally connected to in_vld
        """

        occupied = [self._reg(f"{prefix}occupied_{i:d}", def_val=0) for i in range(2)]
        reader_prio = self._reg(f"{prefix}reader_prio", def_val=0)

        consume_0 = (reader_prio._eq(0) & occupied[0]) | ~occupied[1]
        consume_1 = (reader_prio._eq(1) & occupied[1]) | ~occupied[0]

        outData = []
        for iin in in_data:
            r0 = self._reg(prefix + 'reg0_' + getSignalName(iin), iin._dtype)
            If(in_vld & ~occupied[0],
               r0(iin)
            )

            r1 = self._reg(prefix + 'reg1_' + getSignalName(iin), iin._dtype)
            If(in_vld & ~occupied[1],
               r1(iin)
            )

            o = self._sig(prefix + 'out_tmp_' + getSignalName(iin), iin._dtype)

            If(consume_0 & occupied[0],
               o(r0)
            ).Elif(consume_1 & occupied[1],
               o(r1)
            ).Else(
               o(None)
            )
            outData.append(o)

        If(in_vld & (~occupied[0] | ~occupied[1]),
            If(occupied[0],
               reader_prio(0),
            ).Elif(occupied[1],
               reader_prio(1),
            )
        )

        oc0_set = in_vld & ~occupied[0]
        oc0_clr = out_rd & occupied[0] & consume_0

        oc1_set = in_vld & occupied[0] & ~occupied[1]
        oc1_clr = out_rd & occupied[1] & consume_1

        occupied[0]((occupied[0] | oc0_set) & ~oc0_clr)
        occupied[1]((occupied[1] | oc1_set) & ~oc1_clr)

        in_rd(~occupied[0] | ~occupied[1])
        out_vld(occupied[0] | occupied[1])

        return outData

    def _impl(self):
        LATENCY = self.LATENCY
        DELAY = self.DELAY

        vld = self.get_valid_signal
        rd = self.get_ready_signal
        data = self.get_data

        Out = self.dataOut
        In = self.dataIn

        if LATENCY == (1, 2):
            # ready chain break
            if DELAY != 0:
                raise NotImplementedError()

            in_vld, in_rd, in_data = vld(In), rd(In), data(In)
            out_vld, out_rd = vld(Out), rd(Out)
            outData = self._implReadyChainBreak(in_vld, in_rd, in_data, out_vld, out_rd, "ready_chain_break_")

        elif DELAY == 0:
            in_vld, in_rd, in_data = vld(In), rd(In), data(In)
            for last, i in iter_with_last(range(LATENCY)):
                if last:
                    out_vld, out_rd = vld(Out), rd(Out)
                else:
                    out_vld = self._sig("latency%d_vld" % (i+1))
                    out_rd = self._sig("latency%d_rd" % (i+1))

                outData = self._impl_latency(in_vld, in_rd, in_data,
                                             out_vld, out_rd,
                                             f"latency{i:d}_")
                in_vld, in_rd, in_data = out_vld, out_rd, outData

        elif LATENCY == 2 and DELAY == 1:
            latency1_vld = self._sig("latency1_vld")
            latency1_rd = self._sig("latency1_rd")
            outData = self._impl_latency(vld(In), rd(In), data(In),
                                         latency1_vld, latency1_rd,
                                         "latency1_")
            outData = self._implLatencyAndDelay(latency1_vld, latency1_rd,
                                                outData, vld(Out), rd(Out),
                                                "latency2_delay1_")
        else:
            raise NotImplementedError(LATENCY, DELAY)

        for ds, dm in zip(data(Out), outData):
            ds(dm)


def _example_HandshakedReg():
    from hwt.interfaces.std import Handshaked
    u = HandshakedReg(Handshaked)
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_HandshakedReg()
    print(to_rtl_str(u))
