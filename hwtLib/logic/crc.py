#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from hwt.code import If, Concat, Switch
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BIT
from hwt.hwIOs.std import HwIODataVld, HwIOVectSignal, HwIOSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.commonHwIO.data_mask_last_hs import HwIODataMaskLastRdVld
from hwtLib.logic.crcComb import CrcComb
from hwtLib.logic.crcPoly import CRC_32
from pyMathBitPrecise.bit_utils import get_bit, bit_list_reversed_endianity, \
    mask


# http://www.rightxlight.co.jp/technical/crc-verilog-hdl
# http://outputlogic.com/my-stuff/parallel_crc_generator_whitepaper.pdf
# https://is.muni.cz/th/b7glm/crc.pdf
@serializeParamsUniq
class Crc(HwModule):
    """
    Crc generator for any crc,
    polynome can be string in usual format or integer ("x^3+x+1" or 0b1011)

    :note: See :class:`hwtLib.logic.crcComb.CrcComb`
    :ivar LATENCY: number of cycles from data in to data out
    :ivar DATA_WIDTH: number of bits of data in
    :ivar MASK_GRANULARITY: if None, there is no mask for data in,
        else it must be an int which represents number of bits per 1 bit of mask signal,
        this allows this component to compute crc for smaller bitwidth than data_in width
    :ivar CONTAINS_STATE_REG: if True the state register is present in this component
        otherwise the stateIn io is used as a value of current sate

    .. hwt-autodoc:: _example_Crc
    """

    @override
    def hwConfig(self):
        CrcComb.hwConfig(self)
        self.setConfig(CRC_32)
        self.LATENCY = HwParam(1)
        self.DATA_WIDTH = 32
        self.MASK_GRANULARITY = HwParam(None)
        self.CONTAINS_STATE_REG = HwParam(True)

    @override
    def hwDeclr(self):
        if self.CONTAINS_STATE_REG:
            addClkRstn(self)
        else:
            assert self.LATENCY == 0

        with self._hwParamsShared():
            if self.MASK_GRANULARITY is None:
                self.dataIn = HwIODataVld()
            else:
                self.dataIn = HwIODataMaskLastRdVld()
            self.dataOut = HwIOVectSignal(self.POLY_WIDTH)._m()

            if not self.CONTAINS_STATE_REG:
                self.stateIn = HwIOSignal(HBits(self.POLY_WIDTH))

    def setConfig(self, crcConfigCls):
        """
        Apply configuration from CRC configuration class
        """
        CrcComb.setConfig(self, crcConfigCls)

    def build_crc_xor_matrix(self,
                             state_in_bits: List[RtlSignal],
                             poly_bits: List[int], data_in_bits: List[RtlSignal])\
            ->List[RtlSignal]:
        """
        build xor tree for CRC computation
        """
        crcMatrix = CrcComb.buildCrcXorMatrix(len(data_in_bits), poly_bits)
        res = CrcComb.applyCrcXorMatrix(
            crcMatrix, data_in_bits,
            state_in_bits, self.REFIN)

        # next state logic
        # wrap crc next signals to separate signal to have nice code
        stateNext = []
        for i, crcbit in enumerate(res):
            b = rename_signal(self, crcbit, f"crc_{i:d}")
            stateNext.append(b)
        return stateNext

    @override
    def hwImpl(self):
        # prepare constants and bit arrays for inputs
        poly_bits, _ = CrcComb.parsePoly(self.POLY, self.POLY_WIDTH)
        din = self.dataIn
        # rename "dataIn_data" to "d" to make code shorter
        _d = rename_signal(self, din.data, "d")
        data_in_bits = list(iterBits(_d))

        if not self.IN_IS_BIGENDIAN:
            data_in_bits = bit_list_reversed_endianity(data_in_bits)

        if self.MASK_GRANULARITY:
            din.rd(1)

        if self.CONTAINS_STATE_REG:
            if self.MASK_GRANULARITY:
                rst = self.rst_n._isOn() | (din.vld & din.last)
            else:
                rst = self.rst_n
    
            state = self._reg("c",
                              HBits(self.POLY_WIDTH),
                              self.INIT,
                              rst=rst)
            stateOut = state
        else:
            # rename "dataIn_data" to "d" to make code shorter
            state = rename_signal(self, self.stateIn, "c")
            stateOut = self.dataOut

        state_in_bits = list(iterBits(state))

        if self.MASK_GRANULARITY is None or self.MASK_GRANULARITY == self.DATA_WIDTH:
            state_next = self.build_crc_xor_matrix(
                state_in_bits, poly_bits, data_in_bits)

            if self.CONTAINS_STATE_REG:
                If(din.vld,
                   # state_next is in format 0 ... N,
                   # we need to reverse it to litle-endian
                   stateOut(Concat(*reversed(state_next)))
                )
            else:
                stateOut(Concat(*reversed(state_next)))

        else:
            mask_in = din.mask
            mask_width = mask_in._dtype.bit_length()
            state_next_cases = []
            for vld_byte_cnt in range(1, mask_width + 1):
                # because bytes are already reversed in bit vector of input bits
                _data_in_bits = data_in_bits[
                     (mask_width - vld_byte_cnt) * self.MASK_GRANULARITY:
                ]
                state_next = self.build_crc_xor_matrix(
                    state_in_bits, poly_bits, _data_in_bits)
                # reversed because of because of MSB..LSB
                state_next_cases.append((
                    mask(vld_byte_cnt), stateOut(Concat(*reversed(state_next)))
                ))
            stNext = If(din.vld,
                Switch(mask_in).add_cases(
                   state_next_cases
                ).Default(
                    stateOut(None)
                )
            )
            if not self.CONTAINS_STATE_REG:
                stNext.Else(
                    stateOut(None)
                )
        # output connection
        if self.LATENCY == 0:
            if self.CONTAINS_STATE_REG:
                state = state._rtlNextSig
        elif self.LATENCY == 1:
            if self.MASK_GRANULARITY is not None:
                # to avoid the case where the state is restarted by dataIn.last
                if self.CONTAINS_STATE_REG:
                    state_tmp = self._reg("state_tmp", state._dtype)
                    state_tmp(state._rtlNextSig)
                    state = state_tmp
                else:
                    raise NotImplementedError()
        else:
            raise NotImplementedError(self.LATENCY)

        if self.CONTAINS_STATE_REG:
            dataOut = self._aply_REFOUT_and_XOROUT(state, self.POLY_WIDTH, self.REFOUT, self.XOROUT)
            self.dataOut(dataOut)
        else:
            assert not self.REFOUT
            assert int(self.XOROUT) == 0
            assert self.dataOut is stateOut, stateOut

    def _aply_REFOUT_and_XOROUT(self, state: RtlSignal, POLY_WIDTH:int, REFOUT:bool, XOROUT:int):
        XOROUT = int(XOROUT)
        if REFOUT:
            state_reversed = rename_signal(
                self,
                Concat(*iterBits(state)),
                "state_revered")
            state = state_reversed

        if XOROUT != 0:
            # reverse bit order in XOROUT
            fin_bits = [BIT.from_py(get_bit(XOROUT, i))
                        for i in range(POLY_WIDTH)]
            fin_bits = Concat(*fin_bits)
            return state ^ fin_bits
        else:
            return state


def _example_Crc():
    m = Crc()
    m.MASK_GRANULARITY = 8
    m.setConfig(CRC_32)
    m.DATA_WIDTH = 24
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_Crc()
    print(to_rtl_str(m))
