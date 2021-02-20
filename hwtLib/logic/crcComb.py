#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from typing import List, Tuple, Union

from hwt.interfaces.std import VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.logic.crcPoly import CRC_5_USB
from hwtLib.logic.crcUtils import parsePolyStr
from pyMathBitPrecise.bit_utils import get_bit, bit_list_reversed_bits_in_bytes, \
    bit_list_reversed_endianity
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.hdl.types.bitsVal import BitsVal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT


# http://www.sunshine2k.de/coding/javascript/crc/crc_js.html
# http://www.easics.be/webtools/crctool
# http://www.ijsret.org/pdf/121757.pdf
class CrcComb(Unit):
    """
    CRC generator,
    polynomial can be string in usual format or integer ("x^3+x+1" or 0b1011)

    :ivar ~.DATA_WIDTH: width of data in signal
    :ivar ~.POLY: specified CRC polynome, str, int or Bits value
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

    def _config(self):
        self.DATA_WIDTH = Param(7 + 4)
        self.IN_IS_BIGENDIAN = Param(False)
        self.setConfig(CRC_5_USB)

    def setConfig(self, crcConfigCls):
        """
        Apply configuration from CRC configuration class
        """
        word_t = Bits(crcConfigCls.WIDTH)
        self.POLY = word_t.from_py(crcConfigCls.POLY)
        self.POLY_WIDTH = crcConfigCls.WIDTH
        self.REFIN = crcConfigCls.REFIN
        self.REFOUT = crcConfigCls.REFOUT
        self.XOROUT = word_t.from_py(crcConfigCls.XOROUT)
        self.INIT = word_t.from_py(crcConfigCls.INIT)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = VectSignal(self.DATA_WIDTH)
            self.dataOut = VectSignal(self.POLY_WIDTH)._m()

    @staticmethod
    def parsePoly(POLY, POLY_WIDTH) -> List[int]:
        """
        :return: list of bits from polynome, extra MSB 1 is added
            len of this list is POLY_WIDTH + 1
        """
        PW = int(POLY_WIDTH)
        poly = int(POLY)  # [TODO] poly in str
        if isinstance(poly, str):
            polyCoefs = parsePolyStr(poly, PW)
        elif isinstance(poly, int):
            polyCoefs = [get_bit(poly, i)
                         for i in range(PW)]
        else:
            raise NotImplementedError()

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
            should be XORed to get bit of resut
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
                          inBits: List[RtlSignal], stateBits: List[Union[RtlSignal, BitsVal]],
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

    def _impl(self):
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
    from hwt.synthesizer.utils import to_rtl_str
    # from hwtLib.logic.crcPoly import CRC_32
    # https://github.com/hdl4fpga/hdl4fpga/blob/2a18e546cfcd1f1c38e19705842243e776e019d1/library/usb/usbhost/usbh_crc5.v
    # https://superjameszou.wordpress.com/2010/09/06/a-real-example-for-usb-packets-transferring/
    # https://www.usb.org/sites/default/files/crcdes.pdf
    # http://www.rayslogic.com/Propeller/USB.htm
    # http://outputlogic.com/?page_id=321
    # https://github.com/boostorg/crc/blob/develop/include/boost/crc.hpp
    u = CrcComb()
    # https://github.com/hdl4fpga/hdl4fpga/blob/2a18e546cfcd1f1c38e19705842243e776e019d1/library/usb/usbhost/usbh_crc5.v
    u.setConfig(CRC_5_USB)
    u.DATA_WIDTH = 7 + 4
    # u.REFIN = u.REFOUT = False
    # u.IN_IS_BIGENDIAN = True
    # https://github.com/nandland/nandland/blob/master/CRC/Verilog/source/CRC_16_CCITT_Parallel.v
    #from hwtLib.logic.crcPoly import CRC_16_CCITT
    #u.setConfig(CRC_16_CCITT)
    #u.DATA_WIDTH = 16

    print(to_rtl_str(u))
