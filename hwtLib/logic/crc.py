#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from hwt.code import If, Concat, Switch
from hwt.hdl.typeShortcuts import hBit
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import VldSynced, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.interfaces.data_mask_last_hs import DataMaskLastHs
from hwtLib.logic.crcComb import CrcComb
from pyMathBitPrecise.bit_utils import selectBit, bitListReversedEndianity,\
    mask


# http://www.rightxlight.co.jp/technical/crc-verilog-hdl
# http://outputlogic.com/my-stuff/parallel_crc_generator_whitepaper.pdf
# https://is.muni.cz/th/b7glm/crc.pdf
class Crc(Unit):
    """
    Crc generator for any crc,
    polynome can be string in usual format or integer ("x^3+x+1" or 0b1011)

    :note: See :class:`hwtLib.logic.crcComb.CrcComb`

    .. hwt-schematic::
    """

    def _config(self):
        CrcComb._config(self)
        self.LATENCY = Param(1)
        self.MASK_GRANULARITY = Param(None)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            if self.MASK_GRANULARITY is None:
                self.dataIn = VldSynced()
            else:
                self.dataIn = DataMaskLastHs()
            self.dataOut = VectSignal(self.POLY_WIDTH)._m()

    def setConfig(self, crcConfigCls):
        """
        Apply configuration from CRC configuration class
        """
        CrcComb.setConfig(self, crcConfigCls)

    def wrapWithName(self, sig, name):
        _sig = self._sig(name, sig._dtype)
        _sig(sig)
        return _sig

    def build_crc_xor_matrix(self, state_in_bits, poly_bits, data_in_bits)\
            -> List[RtlSignal]:
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
            b = self.wrapWithName(crcbit, "crc_%d" % i)
            stateNext.append(b)
        return stateNext

    def _impl(self):
        # prepare constants and bit arrays for inputs
        poly_bits, PW = CrcComb.parsePoly(self.POLY, self.POLY_WIDTH)
        din = self.dataIn
        # rename "dataIn_data" to "d" to make code shorter
        _d = self.wrapWithName(din.data, "d")
        data_in_bits = list(iterBits(_d))
        if not self.IN_IS_BIGENDIAN:
            data_in_bits = bitListReversedEndianity(data_in_bits)
        if self.MASK_GRANULARITY:
            din.rd(1)
            rst = self.rst_n._isOn() | (din.vld & din.last)
        else:
            rst = self.rst_n
        state = self._reg("c",
                          Bits(self.POLY_WIDTH),
                          self.INIT,
                          rst=rst)
        state_in_bits = list(iterBits(state))

        if self.MASK_GRANULARITY is None or self.MASK_GRANULARITY == self.DATA_WIDTH:
            state_next = self.build_crc_xor_matrix(
                state_in_bits, poly_bits, data_in_bits)

            If(din.vld,
               # state_next is in format 0 ... N,
               # we need to reverse it to litle-endian
               state(Concat(*reversed(state_next)))
            )
        else:
            mask_in = din.mask
            mask_width = mask_in._dtype.bit_length()
            state_next_cases = []
            for vld_byte_cnt in range(1, mask_width + 1):
                m = mask(vld_byte_cnt)
                # because of MSB..LSB
                _data_in_bits = data_in_bits[
                    (mask_width - vld_byte_cnt)*self.MASK_GRANULARITY:
                ]
                state_next = self.build_crc_xor_matrix(
                    state_in_bits, poly_bits, _data_in_bits)
                state_next_cases.append((
                    m, state(Concat(*reversed(state_next)))
                ))
            If(din.vld,
                Switch(mask_in).add_cases(
                   state_next_cases
                ).Default(state(None))
            )
        # output connection
        if self.LATENCY == 0:
            state = state.next
        elif self.LATENCY == 1:
            if self.MASK_GRANULARITY is not None:
                # to avoid the case where the state is restarted by dataIn.last
                state_tmp = self._reg("state_tmp", state._dtype)
                state_tmp(state.next)
                state = state_tmp
        else:
            raise NotImplementedError(self.LATENCY)

        XOROUT = int(self.XOROUT)
        fin_bits = [hBit(selectBit(XOROUT, i))
                    for i in range(PW)]
        fin_bits = self.wrapWithName(Concat(*fin_bits), "fin_bits")

        if self.REFOUT:
            state_reversed = self.wrapWithName(
                Concat(*iterBits(state)), "state_revered")
            state = state_reversed
        self.dataOut(state ^ fin_bits)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # from hwtLib.logic.crcPoly import CRC_32
    u = Crc()
    u.MASK_GRANULARITY = 8
    # CrcComb.setConfig(u, CRC_32)
    # u.DATA_WIDTH = 8

    print(to_rtl_str(u))
