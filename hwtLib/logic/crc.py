#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat
from hwt.hdl.typeShortcuts import hBit
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import VldSynced, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.logic.crcComb import CrcComb
from pyMathBitPrecise.bit_utils import selectBit, bitListReversedEndianity


# http://www.rightxlight.co.jp/technical/crc-verilog-hdl
# http://outputlogic.com/my-stuff/parallel_crc_generator_whitepaper.pdf
class Crc(Unit):
    """
    Crc generator for any crc,
    polynome can be string in usual format or integer ("x^3+x+1" or 0b1011)

    .. hwt-schematic::
    """

    def _config(self):
        CrcComb._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = VldSynced()
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

    def _impl(self):
        # prepare constants and bit arrays for inputs
        DW = int(self.DATA_WIDTH)
        polyBits, PW = CrcComb.parsePoly(self.POLY, self.POLY_WIDTH)

        XOROUT = int(self.XOROUT)
        finBits = [hBit(selectBit(XOROUT, i))
                   for i in range(PW)]

        # rename "dataIn_data" to "d" to make code shorter
        _d = self.wrapWithName(self.dataIn.data, "d")
        inBits = list(iterBits(_d))
        if not self.IN_IS_BIGENDIAN:
            inBits = bitListReversedEndianity(inBits)

        state = self._reg("c",
                          Bits(self.POLY_WIDTH),
                          self.INIT)
        stateBits = list(iterBits(state))

        # build xor tree for CRC computation
        crcMatrix = CrcComb.buildCrcXorMatrix(DW, polyBits)
        res = CrcComb.applyCrcXorMatrix(
            crcMatrix, inBits,
            stateBits, bool(self.REFIN))

        # next state logic
        # wrap crc next signals to separate signal to have nice code
        stateNext = []
        for i, crcbit in enumerate(res):
            b = self.wrapWithName(crcbit, "crc_%d" % i)
            stateNext.append(b)

        If(self.dataIn.vld,
           # regNext is in format 0 ... N, we need to reverse it to litle
           # endian
           state(Concat(*reversed(stateNext)))
           )

        # output connection
        if self.REFOUT:
            finBits = reversed(finBits)
            self.dataOut(
                Concat(*[rb ^ fb
                         for rb, fb in zip(iterBits(state), finBits)]
                       )
            )
        else:
            self.dataOut(state ^ Concat(*finBits))


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    # from hwtLib.logic.crcPoly import CRC_32
    u = Crc()
    # CrcComb.setConfig(u, CRC_32)
    # u.DATA_WIDTH = 8

    print(toRtl(u))
