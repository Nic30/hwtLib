#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from typing import List, Tuple, Union

from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.defs import BIT
from hwt.hwIOs.std import HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.logic.crcPoly import CRC_5_USB, CRC_POLY
from hwtLib.logic.crcUtils import parsePolyStr
from pyMathBitPrecise.bit_utils import get_bit, bit_list_reversed_bits_in_bytes, \
    bit_list_reversed_endianity


# http://www.sunshine2k.de/coding/javascript/crc/crc_js.html
# http://www.easics.be/webtools/crctool
# http://www.ijsret.org/pdf/121757.pdf
class CrcComb(HwModule):
    """
    CRC generator,
    polynomial can be string in usual format or integer ("x^3+x+1" or 0b1011)

    :note: Padding of data with 0 bits may be used to compute crc for smaller bitwidths.
        If the CRC is reflected, then pad from LSB side. If the CRC is not reflected, then pad from MSB side.

    :ivar ~.DATA_WIDTH: width of data in signal
    :ivar ~.POLY: specified CRC polynome, str, int or HBits value
    :ivar ~.POLY_WIDTH: width of POLY
    :ivar ~.REFIN: This is a boolean parameter. If it is FALSE,
        input bytes are processed with bit 7 being treated
        as the most significant bit (MSB) and bit 0 being treated
        as the least significant bit. If this parameter is FALSE,
        each byte is reflected before being processed.
    :ivar ~.REFOUT: Same as REFIN except for output
    :ivar ~.XOROUT: value to xor result with

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(7 + 4)
        self.IN_IS_BIGENDIAN = HwParam(False)
        self.POLY_TY = HwParam(CRC_5_USB)
        self.setConfig(CRC_5_USB)

    def setConfig(self, crcConfigCls: Tuple[CRC_POLY]):
        """
        Apply configuration from CRC configuration class
        """
        self.POLY_TY = crcConfigCls
        word_t = HBits(crcConfigCls.WIDTH)
        self.POLY = word_t.from_py(crcConfigCls.POLY)
        self.POLY_WIDTH = crcConfigCls.WIDTH
        self.REFIN = crcConfigCls.REFIN
        self.REFOUT = crcConfigCls.REFOUT
        self.XOROUT = word_t.from_py(crcConfigCls.XOROUT)
        self.INIT = word_t.from_py(crcConfigCls.INIT)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.dataIn = HwIOVectSignal(self.DATA_WIDTH)
            self.dataOut = HwIOVectSignal(self.POLY_WIDTH)._m()

    @staticmethod
    def parsePoly(POLY: int, POLY_WIDTH: int) -> List[int]:
        """
        :return: list of bits from polynome, extra MSB 1 is added
            len of this list is POLY_WIDTH + 1
        """
        PW = int(POLY_WIDTH)
        if isinstance(POLY, str):
            polyCoefs = parsePolyStr(POLY, PW)
        else:
            poly = int(POLY)
            polyCoefs = [get_bit(poly, i)
                         for i in range(PW)]

        # LSB is usuaaly 1
        return polyCoefs, PW

    # based on
    # hhttps://github.com/alexforencich/fpga-utils/blob/master/crcgen.py
    @staticmethod
    def buildCrcXorMatrix(data_width: int,
                          polyBits: List[bool]) -> List[Tuple[List[bool],
                                                              List[bool]]]:
        """
        :param data_width: number of bits in input
            (excluding bits of signal wit current crc state)
        :param polyBits: list of bits in specified polynome
        :note: all bits are in format LSB downto MSB
        :return: crc_mask contains rows where each row describes which bits
            should be XORed to get bit of result
            row is [mask_for_state_reg, mask_for_data]
        """
        DW = data_width
        PW = len(polyBits)
        # list index is output bit index
        # initial state is 1:1 mapping from previous state to next state
        crc_mask = deque([
            [[int(x == y) for y in range(PW)], [0] * DW]
            for x in range(PW)
        ])

        for i in range(DW - 1, -1, -1):
            # determine shift in value
            # current value in last FF, XOR with input data bit (MSB first)
            val = crc_mask[-1]
            val[1][i] = int(not val[1][i])

            # shift
            crc_mask.appendleft(val)
            crc_mask.pop()

            # add XOR inputs at correct indicies
            first = True
            val_s, val_d = val
            for cm, pb in zip(crc_mask, polyBits):
                if first:
                    first = False
                elif pb:
                    cm[0] = [a ^ b for a, b in zip(cm[0], val_s)]
                    cm[1] = [a ^ b for a, b in zip(cm[1], val_d)]

        return crc_mask

    @classmethod
    def applyCrcXorMatrix(cls, crcMatrix: List[List[List[int]]],
                          inBits: List[RtlSignal], stateBits: List[Union[RtlSignal, HBitsConst]],
                          refin: bool) -> List:
        if refin:
            inBits = bit_list_reversed_bits_in_bytes(inBits, extend=False)
        outBits = []
        for (stateMask, dataMask) in crcMatrix:
            v = BIT.from_py(0)  # neutral value for XOR
            assert len(stateMask) == len(stateBits)
            for useBit, b in zip(stateMask, stateBits):
                if useBit:
                    v = v ^ b

            assert len(dataMask) == len(inBits), (len(dataMask), len(inBits))
            for useBit, b in zip(dataMask, inBits):
                if useBit:
                    v = v ^ b

            outBits.append(v)

        assert len(outBits) == len(stateBits)
        return outBits

    @override
    def hwImpl(self):
        DW = int(self.DATA_WIDTH)
        polyBits, PW = self.parsePoly(self.POLY, self.POLY_WIDTH)
        XOROUT = int(self.XOROUT)
        _INIT = int(self.INIT)
        initBits = [BIT.from_py(get_bit(_INIT, i))
                    for i in range(PW)]
        finBits = [BIT.from_py(get_bit(XOROUT, i))
                   for i in range(PW)]

        # rename to have shorter code
        _inD = self._sig("d", self.dataIn._dtype)
        _inD(self.dataIn)
        inBits = list(iterBits(_inD))

        if not self.IN_IS_BIGENDIAN:
            # we need to process lower byte first
            inBits = bit_list_reversed_endianity(inBits, extend=False)

        crcMatrix = self.buildCrcXorMatrix(DW, polyBits)
        res = self.applyCrcXorMatrix(
            crcMatrix, inBits,
            initBits, bool(self.REFIN))

        if self.REFOUT:
            res = list(reversed(res))
            finBits = bit_list_reversed_bits_in_bytes(finBits, extend=False)

        outBits = iterBits(self.dataOut)
        for ob, b, fb in zip(outBits, res, finBits):
            ob(b ^ fb)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    # from hwtLib.logic.crcPoly import CRC_32
    # https://github.com/hdl4fpga/hdl4fpga/blob/2a18e546cfcd1f1c38e19705842243e776e019d1/library/usb/usbhost/usbh_crc5.v
    # https://superjameszou.wordpress.com/2010/09/06/a-real-example-for-usb-packets-transferring/
    # https://www.usb.org/sites/default/files/crcdes.pdf
    # http://www.rayslogic.com/Propeller/USB.htm
    # http://outputlogic.com/?page_id=321
    # https://github.com/boostorg/crc/blob/develop/include/boost/crc.hpp
    m = CrcComb()
    # https://github.com/hdl4fpga/hdl4fpga/blob/2a18e546cfcd1f1c38e19705842243e776e019d1/library/usb/usbhost/usbh_crc5.v
    m.setConfig(CRC_5_USB)
    m.DATA_WIDTH = 7 + 4
    # m.REFIN = m.REFOUT = False
    # m.IN_IS_BIGENDIAN = True
    # https://github.com/nandland/nandland/blob/master/CRC/Verilog/source/CRC_16_CCITT_Parallel.v
    # from hwtLib.logic.crcPoly import CRC_16_CCITT
    # m.setConfig(CRC_16_CCITT)
    # m.DATA_WIDTH = 16

    print(to_rtl_str(m))
