#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Tuple, Union

from hwt.code import If
from hwt.constants import NOT_SPECIFIED
from hwt.hwIOs.utils import addClkRstn
from hwt.hwParam import HwParam
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interfaceLevel.hwModuleImplHelpers import getSignalName
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.handshaked.compBase import HandshakedCompBase


@serializeParamsUniq
class HandshakedReg(HandshakedCompBase):
    """
    Register for HwIODataRdVld interfaces

    :note: latency and delay can be specified as well as HwIO class
    :note: if LATENCY == (1, 2) the ready chain is broken.
        That there is an extra register for potential data overflow and
        no combinational path between input ready, valid and output ready/valid exists.

    :ivar INIT_DATA: a reset value of register (data is transfered from this register after reset)
        (an item for each stage of register, typically just 1 item)
        e.g. if register has latency=1 and interface has just data:uint8_t signal
        the INIT_DATA will be in format ((0,),)

    .. hwt-autodoc:: _example_HandshakedReg
    """

    @override
    def hwConfig(self):
        HandshakedCompBase.hwConfig(self)
        self.LATENCY: Union[int, Tuple[int, int]] = HwParam(1)
        self.DELAY = HwParam(0)
        self.INIT_DATA: tuple = HwParam(())

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = self.hwIOCls()
            self.dataOut = self.hwIOCls()._m()

    def _impl_latency(self, inVld: RtlSignal, inRd: RtlSignal, inData: List[RtlSignal],
                      outVld: RtlSignal, outRd: RtlSignal, prefix:str, initData: list,
                      hasInit:bool):
        """
        Create a normal handshaked register

        :param inVld: input valid signal (1 if producer is sending data)
        :param inRd: input ready signal (send 1 if we are ready to receive the data)
        :param inData: list of input data signals
        :param outVld: output valid signal (1 if we are sending valid data)
        :param outRd: output ready signal (1 if consummer is ready to receive the data)
        :param prefix: name prefix used for internal signals
        :param initData: list of init data for each data signal on iterface
        """
        isOccupied = self._reg(prefix + "isOccupied", def_val=hasInit)
        regs_we = self._sig(prefix + 'reg_we')

        outData = []
        assert len(initData) == len(inData)
        for iin, init in zip(inData, initData):
            r = self._reg(prefix + 'reg_' + getSignalName(iin), iin._dtype,
                          def_val=None if init is NOT_SPECIFIED else init)

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
                             outVld: RtlSignal, outRd: RtlSignal, prefix: str, initData: list, hasInit:bool):
        """
        Create a register pipe

        :see: For param description see :meth:`HandshakedReg._impl_latency`
        """
        wordLoaded = self._reg(prefix + "wordLoaded", def_val=hasInit)
        If(wordLoaded,
            wordLoaded(~outRd)
        ).Else(
            wordLoaded(inVld)
        )

        outData = []
        # construct delay register for each signal
        assert len(initData) == len(inData)
        for iin, init in zip(inData, initData):
            r = self._reg('reg_' + getSignalName(iin), iin._dtype,
                          def_val=None if init is NOT_SPECIFIED else init)
            If(~wordLoaded,
               r(iin)
            )
            outData.append(r)

        inRd(~wordLoaded)
        outVld(wordLoaded)

        return outData

    def _implReadyChainBreak(self, in_vld: RtlSignal, in_rd: RtlSignal, in_data: List[RtlSignal],
                             out_vld: RtlSignal, out_rd: RtlSignal, prefix: str, initData: list, hasInit:bool):
        """
        Two sets of registers 0. is prioritized 1. is used as a backup
        The in_rd is not combinationally connected to out_rd
        The out_vld is not combinationally connected to in_vld

        :see: For param description see :meth:`HandshakedReg._impl_latency`
        """
        occupied = [self._reg(f"{prefix}occupied_{i:d}", def_val=hasInit if i == 0 else 0) for i in range(2)]
        reader_prio = self._reg(f"{prefix}reader_prio", def_val=0)

        consume_0 = (reader_prio._eq(0) & occupied[0]) | ~occupied[1]
        consume_1 = (reader_prio._eq(1) & occupied[1]) | ~occupied[0]

        outData = []
        assert len(initData) == len(in_data), (initData, in_data)
        for iin, init in zip(in_data, initData):
            r0 = self._reg(prefix + 'reg0_' + getSignalName(iin), iin._dtype,
                           def_val=None if init is NOT_SPECIFIED else init)
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

    @override
    def hwImpl(self):
        LATENCY = self.LATENCY
        DELAY = self.DELAY

        vld = self.get_valid_signal
        rd = self.get_ready_signal
        data = self.get_data

        Out = self.dataOut
        In = self.dataIn

        no_init = [NOT_SPECIFIED for _ in data(In)]
        hasInit = False
        if LATENCY == (1, 2):
            # ready chain break
            if DELAY != 0:
                raise NotImplementedError()

            in_vld, in_rd, in_data = vld(In), rd(In), data(In)
            out_vld, out_rd = vld(Out), rd(Out)
            if self.INIT_DATA:
                if len(self.INIT_DATA) > 1:
                    raise NotImplementedError()
                else:
                    init = self.INIT_DATA[0]
                    hasInit = True
            else:
                init = no_init

            outData = self._implReadyChainBreak(in_vld, in_rd, in_data, out_vld, out_rd,
                                                "ready_chain_break_", init, hasInit)

        elif DELAY == 0:
            assert len(self.INIT_DATA) <= self.LATENCY
            in_vld, in_rd, in_data = vld(In), rd(In), data(In)
            for last, i in iter_with_last(range(LATENCY)):
                if last:
                    out_vld, out_rd = vld(Out), rd(Out)
                else:
                    out_vld = self._sig("latency%d_vld" % (i + 1))
                    out_rd = self._sig("latency%d_rd" % (i + 1))
                try:
                    init = self.INIT_DATA[i]
                    hasInit = True
                except IndexError:
                    init = no_init

                outData = self._impl_latency(in_vld, in_rd, in_data,
                                             out_vld, out_rd,
                                             f"latency{i:d}_", init, hasInit)
                in_vld, in_rd, in_data = out_vld, out_rd, outData

        elif LATENCY == 2 and DELAY == 1:
            latency1_vld = self._sig("latency1_vld")
            latency1_rd = self._sig("latency1_rd")
            if self.INIT_DATA:
                if len(self.INIT_DATA) == 1:
                    init0 = self.INIT_DATA[0]
                    hasInit = True
                else:
                    init0, init1 = self.INIT_DATA
                    hasInit = True

            else:
                init0 = init1 = no_init
            outData = self._impl_latency(vld(In), rd(In), data(In),
                                         latency1_vld, latency1_rd,
                                         "latency1_", init0, hasInit)
            outData = self._implLatencyAndDelay(latency1_vld, latency1_rd,
                                                outData, vld(Out), rd(Out),
                                                "latency2_delay1_", init1, hasInit)
        else:
            raise NotImplementedError(LATENCY, DELAY)

        for ds, dm in zip(data(Out), outData):
            ds(dm)


def _example_HandshakedReg():
    from hwt.hwIOs.std import HwIODataRdVld

    m = HandshakedReg(HwIODataRdVld)
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_HandshakedReg()
    print(to_rtl_str(m))
