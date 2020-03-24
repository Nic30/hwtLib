#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil
from typing import Tuple, List

from hwt.code import If, SwitchLogic
from hwt.hdl.typeShortcuts import hBit
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axis_comp.base import AxiSCompBase
from pyMathBitPrecise.bit_utils import mask, setBitRange, selectBitRange
from hwt.code_utils import rename_signal

# Examples of configurations and states which may apperar
#
#     DW = 2*8, footer= 2 * 8
#     1. the footer is alligned in the way it appears on minimal number of words
#        and the dataOut[0] and [1] are always in separate words
#        +------------------+----+----+
#        | word_i           | B0 | B1 |
#        +------------------+----+----+
#        | last -1 (dataIn) | f  | f  |
#        +------------------+----+----+
#        | last    (reg[0]) | d  | d  |
#        +------------------+----+----+
#     2. the footer is not alligned in the way it takes +1 words
#        +------------------+----+----+
#        | word_i           | B0 | B1 |
#        +------------------+----+----+
#        | last -1 (dataIn) | f  | X  |
#        +------------------+----+----+
#        | last    (reg[0]) | d  | f  |
#        +------------------+----+----+
#     DW = 2*8, footer=1*8
#     1. footer, data in separate words
#        +------------------+----+----+
#        | word_i           | B0 | B1 |
#        +------------------+----+----+
#        | last -1 (dataIn) | f  | X  |
#        +------------------+----+----+
#        | last    (reg[0]) | d  | d  |
#        +------------------+----+----+
#
#     2. footer and data on minimal number of words
#        +------------------+----+----+
#        | word_i           | B0 | B1 |
#        +------------------+----+----+
#        | last -1 (dataIn) | d  | f  |
#        +------------------+----+----+
#        | last    (reg[0]) | X  | X  |
#        +------------------+----+----+
#     3. same as 2. but the last word in reg[0] does belongs to this input frame
#        +------------------+----+----+
#        | word_i           | B0 | B1 |
#        +------------------+----+----+
#        | last -1 (dataIn) | d  | f  |
#        +------------------+----+----+
#        | last    (reg[0]) | d  | d  |
#        +------------------+----+----+
#     DW = 3*8, footer=2*8
#        +------------------+----+----+----+
#        | word_i           | B0 | B1 | B2 |
#        +------------------+----+----+----+
#        | last -1 (dataIn) | d  | f  | f  |
#        +------------------+----+----+----+
#        | last    (reg[0]) | X  | X  | X  |
#        +------------------+----+----+----+
#
#        +------------------+----+----+----+
#        | word_i           | B0 | B1 | B2 |
#        +------------------+----+----+----+
#        | last -1 (dataIn) | f  | f  | X  |
#        +------------------+----+----+----+
#        | last    (reg[0]) | d  | d  | d  |
#        +------------------+----+----+----+
#        +------------------+----+----+----+
#        | word_i           | B0 | B1 | B2 |
#        +------------------+----+----+----+
#        | last -1 (dataIn) | f  | X  | X  |
#        +------------------+----+----+----+
#        | last    (reg[0]) | d  | d  | f  |
#        +------------------+----+----+----+


class AxiS_footerSplit(AxiSCompBase):
    """
    Split a constant size footer and prefix data from a input frame.

    :attention: this component does not solve an alignment of output streams

    .. code-block:: python

        HStruct(
            (HStream(uint8_t, frame_len=(1, inf)), "dataIn[0]"),
            (HStream(Bits(self.FOOTER_SIZE), , frame_len=1), "dataIn[1]"),
        )

    Functionality:

        First the data is loaded to internal registers,
        if this data overflows it is passed to dataOut[0].
        Once last word is fond the mask of boundary word is resolved
        and data is send to dataOut[0] and [1].
        Then the rest of data in registers is send on dataOut[1].

    :note: The design is pipelined and the data can loaded
        in to internal registers imediadetely as soon as there is some space.
        There is no inter-frame delay.
    """

    def _config(self):
        AxiSCompBase._config(self)
        self.FOOTER_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = self.intfCls()
            self.dataOut = HObjList([
                self.intfCls()._m(),
                self.intfCls()._m()
            ])

    def generate_regs(self, LOOK_AHEAD) -> List[Tuple[RtlSignal, RtlSignal,
                                                      RtlSignal, RtlSignal,
                                                      RtlSignal]]:
        din = self.dataIn
        mask_t = Bits(self.DATA_WIDTH // 8, force_vector=True)
        data_fieds = [
            (din.data._dtype, "data"),
            # flag for end of input frame
            (BIT, "last"),
            (BIT, "valid"),
        ]
        if self.USE_KEEP:
            data_fieds.append((mask_t, "keep"))
        if self.USE_STRB:
            data_fieds.append((mask_t, "strb"))

        reg_t = HStruct(*data_fieds)
        regs = []
        # 0 is dataIn, 1 is connected to dataIn, ..., n connected to dataOut
        for last, i in iter_with_last(range(LOOK_AHEAD + 1 + 1)):
            if i == 0:
                r = din
                ready = din.ready
                can_flush = hBit(0)
                is_footer = self._sig("dataIn_is_footer", mask_t)
                is_footer_set_val = is_footer  # because it is always set
            elif last:
                r = self._reg("out_reg", reg_t, def_val={"valid": 0})
                ready = self._sig("out_reg_ready")
                can_flush = self._sig("out_reg_can_flush")
                is_footer = self._reg("out_reg_is_footer", mask_t, def_val=0)
                is_footer_set_val = self._sig("out_reg_is_footer_set_val", mask_t)
            else:
                r = self._reg("r%d" % i, reg_t, def_val={"valid": 0})
                ready = self._sig("r%d_ready" % i)
                can_flush = self._sig("r%d_can_flush" % i)
                is_footer = self._reg("r%d_is_footer" % i, mask_t, def_val=0)
                is_footer_set_val = self._sig("r%d_is_footer_set_val" % i, mask_t)
            # :var ready: signal which is 1 if this register can accept data
            # :var can_flush: tells if this register can pass it's value to next
            #     even if prev does not contain valid data
            #     and the hole in data may be created
            # :var is_footer: mask with 1 for footer bytes
            # :var is_footer_set_val: value of is_footer which will be set if end
            #     of frame is detected
            regs.append((r, is_footer, is_footer_set_val, can_flush, ready))

        return regs

    def flush_en_logic(self, regs):
        for i, (r, _, _, can_flush, _) in enumerate(regs):
            if i > 0:
                _, _, _, prev_can_flush, _ = regs[i - 1]
                can_flush((r.valid & r.last) | prev_can_flush)

    def is_footer_mask_set_values(self, LOOK_AHEAD, regs):
        D_W = self.DATA_WIDTH
        BYTE_CNT = D_W // 8
        FOOTER_WIDTH = self.FOOTER_WIDTH
        din = self.dataIn
        in_mask = din.strb
        set_is_footer = self._sig("set_is_footer")
        set_is_footer(din.valid & din.last)
        mask_cases = []
        for last_B_valid, bytes_in_last_input_word in iter_with_last(
                range(1, BYTE_CNT + 1)):
            footer_end = (LOOK_AHEAD * BYTE_CNT
                          + bytes_in_last_input_word) * 8
            footer_start = footer_end - FOOTER_WIDTH
            assert footer_start > 0, (
                "otherwise we would not be able to send last for previous frame",
                footer_start)
            assert footer_start < D_W * 3, (
                "footer start can appear only in last-1 or last-2 regster,"
                " last register is output register",
                footer_start, D_W)
            _is_footer = setBitRange(
                0,
                footer_start // 8,
                FOOTER_WIDTH // 8,
                mask(FOOTER_WIDTH // 8))
            set_flags = []
            for i, (_, _, is_footer_set_val, _, _) in enumerate(regs):
                if i == 0:
                    is_footer_val = 0
                    is_footer_val_last_word = selectBitRange(
                        _is_footer,
                        (LOOK_AHEAD - i) * BYTE_CNT,
                        BYTE_CNT)
                    set_flags.append(
                        If(set_is_footer,
                            is_footer_set_val(is_footer_val_last_word)
                        ).Else(
                            is_footer_set_val(is_footer_val)
                        )
                    )
                else:
                    is_footer_val = selectBitRange(_is_footer,
                                                   (LOOK_AHEAD - i + 1) * BYTE_CNT,
                                                   BYTE_CNT)
                    set_flags.append(is_footer_set_val(is_footer_val))

            if last_B_valid:
                # last byte also valid
                mask_default = set_flags
            else:
                # last 0 from the end of the validity mask
                mask_cases.append(
                    (~in_mask[bytes_in_last_input_word], set_flags)
                )

        SwitchLogic(mask_cases, mask_default)
        return set_is_footer

    def _impl(self):
        USE_KEEP = self.USE_KEEP
        USE_STRB = self.USE_STRB
        FOOTER_WIDTH = self.FOOTER_WIDTH
        D_W = self.DATA_WIDTH
        LOOK_AHEAD = ceil(FOOTER_WIDTH / D_W)
        if FOOTER_WIDTH % 8 != 0:
            raise NotImplementedError()
        if not (self.USE_KEEP or self.USE_STRB):
            assert D_W == 8, ("AxiStream is configured not to use KEEP/STRB"
                              " but is required to resolve frame end", D_W)
        dout = self.dataOut
        regs = self.generate_regs(LOOK_AHEAD)
        self.flush_en_logic(regs)
        # resolve footer flags
        if USE_KEEP or USE_STRB:
            set_is_footer = self.is_footer_mask_set_values(LOOK_AHEAD, regs)
        else:
            raise NotImplementedError()
        din = self.dataIn
        # connect inputs/outputs of registers, dataIn, dataOut
        for is_last, (i, (r, is_footer, is_footer_set_val, can_flush, ready)) in\
                iter_with_last(enumerate(regs)):
            # :note: reg[0] is dataIn, reg[-1] is out_reg
            if is_last:
                # connect last register to outputs
                prev_r, prev_is_footer, _, _, _ = regs[i - 1]
                en = rename_signal(self, din.valid | can_flush, "out_en")
                # at least starts with non footer data
                d0_en = rename_signal(self, ~is_footer[0], "d0_en")
                # contains at least some footer data
                d1_en = rename_signal(self, is_footer != 0, "d1_en")

                # connect prefix data
                dout[0].data(r.data)
                # last if this word contains footer, or next word does not contains data
                d0_last_word_in_last_r = prev_r.valid & prev_is_footer[0]
                dout[0].last((is_footer != 0) | d0_last_word_in_last_r)
                dout[0].valid(r.valid & d0_en & en & (~d1_en | dout[1].ready))

                # connect footer
                dout[1].data(r.data)
                dout[1].last(r.last)
                dout[1].valid(r.valid & d1_en & en & (~d0_en | dout[0].ready))

                mask0 = ~is_footer
                mask1 = is_footer
                if USE_KEEP:
                    dout[0].keep(r.keep & mask0)
                    dout[1].keep(r.keep & mask1)
                if USE_STRB:
                    dout[0].strb(r.strb & mask0)
                    dout[1].strb(r.strb & mask1)

                ready(
                    ~r.valid | (
                        (dout[0].ready | ~d0_en) &
                        (dout[1].ready | ~d1_en)
                    )
                )
            else:
                # connect only ready, because inputs of next register
                # are connected by next register
                next_ready = regs[i + 1][-1]
                if i == 0:
                    # dataIn is actually not a register
                    # and we do not need any extra check
                    ready(next_ready)
                else:
                    ready(~r.valid | next_ready)

            if i > 0:
                # connect register inputs, skip 0 because it is dataIn itself
                prev_r, prev_is_footer, _, prev_can_flush, _ = regs[i - 1]

                data_feed = []
                if USE_KEEP:
                    data_feed.append(r.keep(prev_r.keep))
                if USE_STRB:
                    data_feed.append(r.strb(prev_r.strb))

                prev_r_vld = prev_r.valid & (din.valid | prev_can_flush)
                If(ready,
                    If(prev_r_vld | can_flush,
                       r.data(prev_r.data),
                       r.last(prev_r.last),
                       *data_feed,
                    ),
                    If(set_is_footer & ~(prev_r.valid & prev_r.last),
                       is_footer(is_footer_set_val),
                       r.valid(prev_r.valid),
                    ).Elif(prev_r_vld,
                       is_footer(prev_is_footer),
                       r.valid(prev_r.valid),
                    ).Elif(can_flush,
                       is_footer(0),
                       r.valid(0),
                    )
               )


if __name__ == '__main__':
    from hwt.synthesizer.utils import toRtl
    u = AxiS_footerSplit()
    u.DATA_WIDTH = 8
    u.FOOTER_WIDTH = 8
    u.USE_STRB = True
    print(toRtl(u))
