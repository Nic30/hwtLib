from hwt.bitmask import selectBit, mask
from hwt.code import If, Concat
from hwt.hdlObjects.typeShortcuts import vecT, vec
from hwt.interfaces.std import VldSynced, VectSignal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.logic.crcPoly import CRC_5_USB, CRC_32
from hwtLib.logic.crcUtils import parsePolyStr, buildCrcMatrix
from hwt.synthesizer.byteOrder import reversedBits


# http://stackoverflow.com/questions/41734560/parallel-crc-32-calculation-ethernet-10ge-mac
class Crc(Unit):
    """
    Crc generator for any crc
    polynom can be string in usual format or integer f.e."x^3+x+1" or 0b1011
    """
    def _config(self):
        self.DATA_WIDTH = Param(5)

        self.POLY = Param(CRC_5_USB)
        self.POLY_WIDTH = Param(5)
        # also  refin, reference in
        self.REVERSE_IN = Param(False)
        self.REVERSE_OUT = Param(False)

        # also xorout
        # output = this ^ value in reg
        # for example ethernet has 0xffffffff
        # (0 or mask(POLY_WIDTH) is automatically reduced)
        self.FINAL_XOR_VAL = Param(0)
        self.SEED = Param(0)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = VldSynced()
            self.dataOut = VectSignal(self.POLY_WIDTH)

    def wrapWithName(self, sig, name):
        _sig = self._sig(name, sig._dtype)
        _sig ** sig
        return _sig

    def parsePoly(self, POLY_WIDTH):
        poly = int(self.POLY)
        if isinstance(poly, str):
            return parsePolyStr(poly, POLY_WIDTH)
        elif isinstance(poly, int):
            return [selectBit(poly, i) for i in range(POLY_WIDTH)]
        else:
            raise TypeError()

    def build_CRC_XOR(self, inputBits, xorMatrix):
        inputBits = list(inputBits)
        crcBits = []
        for regMask in xorMatrix:
            bit = None
            for m, b in zip(regMask, inputBits):
                if m:
                    if bit is None:
                        bit = b
                    else:
                        bit = bit ^ b
            crcBits.append(bit)

        return crcBits

    def _impl(self):
        PW = int(self.POLY_WIDTH)
        DW = int(self.DATA_WIDTH)
        polyCoefs = self.parsePoly(PW)

        regXorMatrix, dataXorMatrix = buildCrcMatrix(polyCoefs, PW, DW)

        reg = self._reg("r",
                        vecT(self.POLY_WIDTH),
                        self.SEED)

        # just rename to make code shorter
        d = self.wrapWithName(self.dataIn.data, "d")
        dataXorMatrix = iter(dataXorMatrix)
        regCrcBits = self.build_CRC_XOR(iterBits(reg), regXorMatrix)

        _dataBits = iterBits(d)
        if self.REVERSE_IN:
            _dataBits = reversed(list(_dataBits))

        dataCrcBits = self.build_CRC_XOR(_dataBits, dataXorMatrix)

        regNext = []
        assert len(regCrcBits) == len(dataCrcBits)
        for i, (dbit, rbit) in enumerate(zip(regCrcBits, dataCrcBits)):
            if dbit is not None:
                # just rename to make code shorter
                dbit = self.wrapWithName(dbit, "d_%d" % i)

            if rbit is not None:
                # just rename to make code shorter
                rbit = self.wrapWithName(rbit, "r_%d" % i)

            if dbit is None:
                bit = rbit
            elif rbit is None:
                bit = dbit
            else:
                bit = dbit ^ rbit

            regNext.append(bit)

        If(self.dataIn.vld,
           # regNext is in format 0 ... N, we need to reverse it to litle endian
           reg ** Concat(*reversed(regNext))
        )

        outXor = int(self.FINAL_XOR_VAL)
        if self.REVERSE_OUT:
            _reg = reversedBits(reg)
        else:
            _reg = reg

        if outXor == 0:
            self.dataOut ** _reg
        elif outXor == mask(int(self.POLY_WIDTH)):
            self.dataOut ** ~_reg
        else:
            self.dataOut ** (_reg ^ self.FINAL_XOR_VAL)

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = Crc()
    u.POLY.set(CRC_32)
    u.DATA_WIDTH.set(8)
    u.POLY_WIDTH.set(32)
    u.REVERSE_IN.set(True)
    u.REVERSE_OUT.set(True)
    u.FINAL_XOR_VAL.set(vec(mask(32), 32))
    u.SEED.set(vec(mask(32), 32))
    print(toRtl(u))
