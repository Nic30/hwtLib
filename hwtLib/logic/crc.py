from copy import copy
import re

from hwt.bitmask import mask, selectBit
from hwt.code import iterBits
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import VldSynced, Signal, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.logic.crcPoly import CRC_5_USB


def parsePolyStr_parse_n(string):
    "Parse the number part of a polynomial string term"
    if not string:
        return 1
    elif string == '-':
        return -1
    elif string == '+':
        return 1
    else:
        return int(string)


def parsePolyStr_parse_p(string):
    "Parse the power part of a polynomial string term"
    pat = re.compile('x\^?(\d)?')
    if not string:
        return 0
    res = pat.findall(string)[0]
    if not res:
        return 1
    return int(res)


def parsePolyStr(polyStr, width):
    coefs = [0 for _ in range(width)]
    """\
    Do very, very primitive polynom parsing of a string into a list of coeficients.
    'x' is the only term considered for the polynomial, and this
    routine can only handle terms of the form:
    7x^2 + 6x - 5
    and will choke on seemingly simple forms such as
    x^2*7 - 1
    or
    x**2 - 1
    @return: list of coeficients
    """
    termpat = re.compile('([-+]?\s*\d*\.?\d*)(x?\^?\d?)')
    res_dict = {}
    for n, p in termpat.findall(polyStr):
        n, p = n.strip(), p.strip()
        if not n and not p:
            continue
        n, p = parsePolyStr_parse_n(n), parsePolyStr_parse_p(p)
        if p in res_dict:
            res_dict[p] += n
        else:
            res_dict[p] = n

    for key, value in res_dict.items():
        coefs[key] = value
    return coefs


def crc_serial_shift(num_bits_to_shift,
                     polySize,
                     coefs,
                     lfsr_cur,
                     dataWidth,
                     data_cur):

    assert num_bits_to_shift <= dataWidth

    lfsr_next = copy(lfsr_cur)
    lfsr_poly_size = len(coefs)

    for j in range(num_bits_to_shift):
        # shift the entire LFSR
        lfsr_upper_bit = lfsr_next[lfsr_poly_size - 1]

        for i in range(lfsr_poly_size - 1, 0, -1):
            if coefs[i]:
                lfsr_next[i] = lfsr_next[i - 1] ^ lfsr_upper_bit ^ data_cur[j]
            else:
                lfsr_next[i] = lfsr_next[i - 1]

        lfsr_next[0] = lfsr_upper_bit ^ data_cur[j]
    return lfsr_next


def buildCrcMatrix_dataMatrix(coefs, polyWidth, dataWidth):
    # Data to lfsr reg,  matrix[MxN]
    reg_cur = [0 for _ in range(polyWidth)]
    data_cur = [0 for _ in range(dataWidth)]
    data_matrix = [[0 for _ in range(dataWidth)]
                   for _ in range(polyWidth)]

    for m1 in range(dataWidth):
        data_cur[m1] = 1
        if m1:
            data_cur[m1 - 1] = 0

        reg_next = crc_serial_shift(dataWidth,
                                    polyWidth,
                                    coefs,
                                    reg_cur,
                                    dataWidth,
                                    data_cur)

        for n2, b in enumerate(reg_next):
            if b:
                data_matrix[n2][dataWidth - m1 - 1] = 1
    return data_matrix


def buildCrcMatrix_reg0Matrix(coefs, polyWidth, dataWidth):
    reg_cur = [0 for _ in range(polyWidth)]
    data_cur = [0 for _ in range(dataWidth)]
    reg_matrix = [[0 for _ in range(polyWidth)]
                  for _ in range(polyWidth)]

    # lfsr reg to lfsr reg connections
    for n1 in range(polyWidth):
        reg_cur[n1] = 1
        if n1:
            reg_cur[n1 - 1] = 0
        reg_next = crc_serial_shift(dataWidth,
                                    polyWidth,
                                    coefs,
                                    reg_cur,
                                    dataWidth,
                                    data_cur)
        for n2, b in enumerate(reg_next):
            if b:
                reg_matrix[n2][n1] = 1

    return reg_matrix


def buildCrcMatrix(coefs, polyWidth, dataWidth):
    regMatrix = buildCrcMatrix_reg0Matrix(coefs, polyWidth, dataWidth)
    dataMatrix = buildCrcMatrix_dataMatrix(coefs, polyWidth, dataWidth)

    return regMatrix, dataMatrix


class CrcComb(Unit):
    """
    Crc generator for any crc
    polynom can be string in usual format or integer f.e."x^3+x+1" or 0x1
    """
    def _config(self):
        self.DATA_WIDTH = Param(6)

        self.POLY = Param(CRC_5_USB)
        self.POLY_WIDTH = Param(6)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = VectSignal(self.DATA_WIDTH)
            self.dataOut = VectSignal(self.POLY_WIDTH)

    def _impl(self):
        PW = evalParam(self.POLY_WIDTH).val
        DW = evalParam(self.DATA_WIDTH).val
        assert PW == DW
        poly = evalParam(self.POLY).val
        if isinstance(poly, str):
            polyCoefs = parsePolyStr(poly, PW)
        elif isinstance(poly, int):
            polyCoefs = [selectBit(poly, i) for i in range(PW)]
        else:
            raise NotImplementedError()
        xorMatrix = buildCrcMatrix_dataMatrix(polyCoefs, PW, DW)

        for outBit, inMask in zip(iterBits(self.dataOut),
                                  xorMatrix):
            bit = None
            for m, b in zip(inMask, iterBits(self.dataIn)):
                if m:
                    if bit is None:
                        bit = b
                    else:
                        bit = bit ^ b
            assert bit is not None
            outBit ** bit


class Crc(Unit):
    """
    Crc generator for any crc
    polynom can be string in usual format or integer f.e."x^3+x+1" or 0x1
    """
    def _config(self):
        self.DATA_WIDTH = Param(4)

        self.POLY = Param(CRC_5_USB)
        self.POLY_WIDTH = Param(5)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = VldSynced()
            self.dataOut = Signal(dtype=vecT(self.POLY_WIDTH))

    def _impl(self):
        PW = evalParam(self.POLY_WIDTH).val
        DW = evalParam(self.DATA_WIDTH).val
        poly = evalParam(self.POLY).val
        if isinstance(poly, str):
            polyCoefs = parsePolyStr(poly, PW)
        elif isinstance(poly, int):
            polyCoefs = [selectBit(poly, i) for i in range(PW)]
        else:
            raise NotImplementedError()
        regXorMatrix, dataXorMatrix = buildCrcMatrix(polyCoefs, PW, DW)

        reg = self._reg("crcReg",
                        vecT(self.POLY_WIDTH),
                        mask(PW))

        dataXorMatrix = iter(dataXorMatrix)
        for regBit, regMask in zip(iterBits(reg),
                                   regXorMatrix):
            bit = None
            for m, b in zip(regMask, iterBits(reg)):
                if m:
                    if bit is None:
                        bit = b
                    else:
                        bit = bit ^ b

            try:
                dataMask = next(dataXorMatrix)
            except StopIteration:
                dataMask = []

            for m, b in zip(dataMask, iterBits(self.dataIn.data)):
                if m:
                    if bit is None:
                        bit = b
                    else:
                        bit = bit ^ b
            assert bit is not None
            regBit ** bit


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = CrcComb()
    print(toRtl(u))
